import sys
from pathlib import Path

from core.profile import (
    load_profile, save_profile, profile_exists,
    get_profile_dir, get_highlight_path, get_wp_path,
    get_copied_video_path, PROFILES_DIR, is_reserved_name,
)
from core.video import (
    parse_timestamp, seconds_to_timestamp,
    get_duration, cut_video, preview_cut,
)


def run(profile_name: str, params: list[str]):
    if not profile_exists(profile_name):
        print(f"✗ Profile '{profile_name}' not found.")
        sys.exit(1)

    if not params:
        print("Usage: wallflux edit <profile> --name/--p | --time/--t")
        sys.exit(1)

    flag = params[0].lower()

    if flag in ("--name", "--p"):
        _edit_name(profile_name)
    elif flag in ("--time", "--t"):
        _edit_time(profile_name)
    else:
        print(f"✗ Unknown parameter: '{flag}'")
        print("  Use --name/--p  or  --time/--t")
        sys.exit(1)


# ─── Edit name ────────────────────────────────────────────────────────────────

def _edit_name(profile_name: str):
    import shutil

    new_name = input(f"New name for '{profile_name}': ").strip()

    if not new_name:
        print("Aborted — name cannot be empty.")
        return

    if new_name == profile_name:
        print("Name unchanged.")
        return

    if is_reserved_name(new_name):
        print(f"✗ '{new_name}' is a command name and cannot be used as a profile name.")
        sys.exit(1)

    if profile_exists(new_name):
        print(f"✗ A profile named '{new_name}' already exists.")
        sys.exit(1)

    old_dir = get_profile_dir(profile_name)
    new_dir = PROFILES_DIR / new_name

    # Rename only the two files that are named after the profile.
    # The source copy (.COPIED_*) is named after the original video and profile.toml
    # remembers that name, so it must keep its name (renaming it broke re-cutting
    # and idle whenever the profile name appeared inside the video's file name).
    for prefix in (".highlight_", ".wp_"):
        old_file = old_dir / f"{prefix}{profile_name}.mp4"
        if old_file.exists():
            old_file.rename(old_dir / f"{prefix}{new_name}.mp4")

    # Rename the directory itself
    old_dir.rename(new_dir)

    # Update profile.toml
    data = load_profile(new_name)
    data["name"] = new_name
    save_profile(new_name, data)

    print(f"✓ Profile renamed: '{profile_name}' → '{new_name}'")


# ─── Edit cut time ────────────────────────────────────────────────────────────

def _edit_time(profile_name: str):
    profile = load_profile(profile_name)
    had_cut = "cut_point" in profile          # idle-only profiles have no cut yet
    old_cut = profile.get("cut_point", 0)
    duration = profile.get("duration", 0)

    if had_cut:
        print(f"\n  Current cut point : {seconds_to_timestamp(old_cut)}")
    else:
        print("\n  This is an idle-only profile (no cut point yet).")
        print("  Setting one turns it into a normal WallFlux profile (it stays in idle).")
    print(f"  Video duration    : {seconds_to_timestamp(duration)}")
    print(f"  Format: 32 / 32.450 / 1:32 / 1:32.450 / 1:04:32.450\n")

    # Find the copied source video
    original_file = profile.get("original_file", "")
    source = get_copied_video_path(profile_name, original_file)

    if not source.exists():
        print(f"✗ Source file not found: {source.name}")
        print("  Cannot re-cut without the original copy.")
        sys.exit(1)

    # Ask for new cut point
    new_cut = _ask_timestamp(duration)

    # Preview loop
    while True:
        preview = input("Preview new cut point? [y/n] ").strip().lower()
        if preview == "y":
            preview_cut(source, new_cut)
            confirm = input("Accept this cut point? [y/n] ").strip().lower()
            if confirm == "y":
                break
            new_cut = _ask_timestamp(duration)
        elif preview == "n":
            break

    # Remove old cut files
    for old_file in [get_highlight_path(profile_name), get_wp_path(profile_name)]:
        if old_file.exists():
            old_file.unlink()

    # Re-cut losslessly
    print("\nRe-cutting (lossless) ..." if had_cut else "\nCutting (lossless) ...")
    try:
        cut_video(source, get_highlight_path(profile_name), get_wp_path(profile_name), new_cut)
    except RuntimeError as e:
        print(f"✗ Cut failed: {e}")
        sys.exit(1)

    # Update profile.toml
    profile["cut_point"] = new_cut
    save_profile(profile_name, profile)

    verb = "updated" if had_cut else "created"
    print(f"  ✓ .highlight_{profile_name}.mp4  {verb}")
    print(f"  ✓ .wp_{profile_name}.mp4         {verb}")
    if had_cut:
        print(f"  ✓ Cut point: {seconds_to_timestamp(old_cut)} → {seconds_to_timestamp(new_cut)}")
    else:
        print(f"  ✓ Cut point: {seconds_to_timestamp(new_cut)}")


def _ask_timestamp(duration: float) -> float:
    while True:
        raw = input("  New cut point: ").strip()
        try:
            t = parse_timestamp(raw)
        except ValueError as e:
            print(f"  ✗ {e}")
            continue
        if t <= 0 or t >= duration:
            print(f"  ✗ Must be between 0 and {seconds_to_timestamp(duration)}")
            continue
        return t
