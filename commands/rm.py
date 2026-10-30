import sys
from core.profile import (
    profile_exists, delete_profile, load_profile,
    is_idle, set_idle, has_cut,
)

def run(profile_name: str):
    if not profile_exists(profile_name):
        print(f"✗ Profile '{profile_name}' not found.")
        sys.exit(1)

    confirm = input(f"Delete profile '{profile_name}' and all its files? [y/N] ").strip().lower()
    if confirm != "y":
        print("Aborted.")
        return

    delete_profile(profile_name)
    print(f"✓ Profile '{profile_name}' deleted.")


def run_idle(profile_name: str):
    """wallflux rm idle <name> — take a profile out of idle."""
    if not profile_exists(profile_name):
        print(f"✗ Profile '{profile_name}' not found.")
        sys.exit(1)

    if not is_idle(profile_name):
        print(f"'{profile_name}' is not in idle.")
        return

    # An idle-only profile (no cut) is useless outside idle, so removing it deletes it
    if not has_cut(profile_name):
        print(f"'{profile_name}' is an idle-only profile (no cut point).")
        confirm = input("Removing it from idle deletes it. Delete? [y/N] ").strip().lower()
        if confirm != "y":
            print("Aborted.")
            return
        delete_profile(profile_name)
        print(f"✓ Idle profile '{profile_name}' deleted.")
        return

    set_idle(profile_name, False)
    print(f"✓ '{profile_name}' removed from idle (the profile is kept).")
