import sys
from core.profile import profile_exists, delete_profile, load_profile

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
