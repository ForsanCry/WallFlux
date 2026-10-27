import os
import shutil
import sys
from pathlib import Path

from core.profile import (
    profile_exists,
    save_profile,
    delete_profile,
    get_profile_dir,
    get_copied_video_path,
    get_highlight_path,
    get_wp_path,
    is_reserved_name,
    is_idle,
    set_idle,
)
from core.video import (
    get_duration,
    detect_cut_point,
    parse_timestamp,
    seconds_to_timestamp,
    cut_video,
    preview_cut,
)


def run(profile_name: str, video_arg: str):
    # ── 0. Reserved name check ─────────────────────────────────────────────
    _check_name(profile_name)

    # ── 1. Resolve video path ──────────────────────────────────────────────
    video_path = _resolve_video(video_arg)

    # ── 2. Profile name check ──────────────────────────────────────────────
    if profile_exists(profile_name):
        print(f"Profile '{profile_name}' already exists.")
        overwrite = input("Overwrite? [y/N] ").strip().lower()
        if overwrite != "y":
            print("Aborted.")
            sys.exit(0)

    profile_dir = get_profile_dir(profile_name)
    profile_dir.mkdir(parents=True, exist_ok=True)

    # ── 3. Copy video into profile ────────────────────────────────────────
    copied_path = get_copied_video_path(profile_name, video_path.name)
    print(f"\nCopying video → {copied_path.name} ...")
    shutil.copy2(video_path, copied_path)
    print("✓ Done")

    # ── 4. Duration info ──────────────────────────────────────────────────
    duration = get_duration(copied_path)
    print(f"  Duration : {seconds_to_timestamp(duration)}")

    # ── 5. Cut mode ───────────────────────────────────────────────────────
    print("\nCut point detection:")
    print("  [a] Auto  (audio + scene analysis)")
    print("  [m] Manual (enter timestamp)")

    while True:
        mode = input("Selection: ").strip().lower()
        if mode in ("a", "m"):
            break
        print("  Please enter 'a' or 'm'.")

    # ── 6. Determine cut point ────────────────────────────────────────────
    if mode == "a":
        print("\nAnalysing video ...")
        try:
            cut_point = detect_cut_point(copied_path)
        except RuntimeError as e:
            print(f"\n✗ Auto-detection failed: {e}")
            print("Falling back to manual entry.")
            cut_point = _ask_timestamp(duration)
        else:
            print(f"  Detected cut point : {seconds_to_timestamp(cut_point)}")
    else:
        cut_point = _ask_timestamp(duration)

    # ── 7. Preview ────────────────────────────────────────────────────────
    while True:
        preview = input("\nPreview cut point? [y/n] ").strip().lower()
        if preview == "y":
            preview_cut(copied_path, cut_point)
            confirm = input("Accept this cut point? [y/n] ").strip().lower()
            if confirm == "y":
                break
            # Let user re-enter manually
            print("Enter a new cut point:")
            cut_point = _ask_timestamp(duration)
        elif preview == "n":
            break
        else:
            print("  Please enter 'y' or 'n'.")

    # ── 8. Lossless cut ───────────────────────────────────────────────────
    highlight_path = get_highlight_path(profile_name)
    wp_path        = get_wp_path(profile_name)

    print("\nCutting video (lossless) ...")
    try:
        cut_video(copied_path, highlight_path, wp_path, cut_point)
    except RuntimeError as e:
        print(f"✗ Cut failed: {e}")
        sys.exit(1)

    print(f"  ✓ .highlight_{profile_name}.mp4  ({seconds_to_timestamp(cut_point)})")
    print(f"  ✓ .wp_{profile_name}.mp4         ({seconds_to_timestamp(duration - cut_point)})")

    # ── 9. Save profile.toml ──────────────────────────────────────────────
    save_profile(profile_name, {
        "name":             profile_name,
        "original_file":    video_path.name,
        "cut_point":        cut_point,
        "duration":         duration,
    })

    print(f"\n✓ Profile '{profile_name}' ready.")
    print(f"  Run: wallflux play {profile_name}")


def run_idle(profile_name: str, video_arg: str | None = None):
    """
    wallflux new idle <name>           -> add an existing profile to idle
    wallflux new idle <name> <video>   -> create a new idle-only profile (no cut)
    """
    _check_name(profile_name)

    # ── Case 1: no video given -> mark an existing profile as idle ────────
    if video_arg is None:
        if not profile_exists(profile_name):
            print(f"Profile '{profile_name}' not found.")
            print("To create an idle profile from a video:")
            print("  wallflux new idle <name> <video>")
            sys.exit(1)
        if is_idle(profile_name):
            print(f"'{profile_name}' is already in idle.")
            return
        set_idle(profile_name, True)
        print(f"✓ '{profile_name}' added to idle.")
        # TODO (step 2): run the idle setup wizard if idle.toml does not exist yet
        return

    # ── Case 2: video given -> new idle-only profile ──────────────────────
    video_path = _resolve_video(video_arg)

    if profile_exists(profile_name):
        print(f"Profile '{profile_name}' already exists.")
        overwrite = input("Overwrite? [y/N] ").strip().lower()
        if overwrite != "y":
            print("Aborted.")
            sys.exit(0)
        delete_profile(profile_name)   # drop old files so nothing stale is left behind

    get_profile_dir(profile_name).mkdir(parents=True, exist_ok=True)

    copied_path = get_copied_video_path(profile_name, video_path.name)
    print(f"\nCopying video → {copied_path.name} ...")
    shutil.copy2(video_path, copied_path)
    print("✓ Done")

    duration = get_duration(copied_path)
    print(f"  Duration : {seconds_to_timestamp(duration)}")

    # No cut point: idle plays the whole video, so no highlight/wp files are made
    save_profile(profile_name, {
        "name":             profile_name,
        "original_file":    video_path.name,
        "duration":         duration,
        "idle":             True,
    })

    print(f"\n✓ Idle profile '{profile_name}' ready (no cut needed).")
    # TODO (step 2): run the idle setup wizard if idle.toml does not exist yet


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _check_name(profile_name: str):
    if is_reserved_name(profile_name):
        print(f"✗ '{profile_name}' is a command name and cannot be used as a profile name.")
        sys.exit(1)


def _resolve_video(video_arg: str) -> Path:
    """Accept absolute path or filename relative to cwd."""
    p = Path(video_arg)

    if p.is_absolute() and p.exists():
        return p

    cwd_path = Path.cwd() / p
    if cwd_path.exists():
        return cwd_path.resolve()

    print(f"✗ Video not found: '{video_arg}'")
    sys.exit(1)


def _ask_timestamp(duration: float) -> float:
    """Prompt the user for a valid timestamp within the video duration."""
    print("  Format: 32 / 32.450 / 1:32 / 1:32.450 / 1:04:32.450")
    while True:
        raw = input("  Cut point: ").strip()
        try:
            t = parse_timestamp(raw)
        except ValueError as e:
            print(f"  ✗ {e}")
            continue
        if t <= 0 or t >= duration:
            print(f"  ✗ Must be between 0 and {seconds_to_timestamp(duration)}")
            continue
        return t
