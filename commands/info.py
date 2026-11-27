import sys
from pathlib import Path
from core.profile import (
    load_profile, profile_exists, get_profile_dir,
    get_highlight_path, get_wp_path, get_full_video_path,
)
from core.video import seconds_to_timestamp

def run(profile_name: str):
    if not profile_exists(profile_name):
        print(f"✗ Profile '{profile_name}' not found.")
        sys.exit(1)

    p   = load_profile(profile_name)
    dir = get_profile_dir(profile_name)

    def _size(path: Path) -> str:
        if not path.exists():
            return "missing"
        mb = path.stat().st_size / 1_048_576
        return f"{mb:.1f} MB"

    highlight = get_highlight_path(profile_name)
    wp        = get_wp_path(profile_name)

    duration = p.get("duration", 0)

    print(f"\n  Profile   : {profile_name}")
    print(f"  Source    : {p.get('original_file', '?')}")
    print(f"  Duration  : {seconds_to_timestamp(duration)}")

    if "cut_point" in p:
        cut = p["cut_point"]
        print(f"  Cut point : {seconds_to_timestamp(cut)}")
        print(f"  Highlight : {seconds_to_timestamp(cut)}  ({_size(highlight)})")
        print(f"  WP loop   : {seconds_to_timestamp(duration - cut)}  ({_size(wp)})")
    else:
        # idle-only profile: the whole video is used, nothing is cut
        print("  Cut point : none (idle-only profile)")
        print(f"  Video     : {seconds_to_timestamp(duration)}  ({_size(get_full_video_path(profile_name))})")

    print(f"  Idle      : {bool(p.get('idle', False))}")
    print(f"  Directory : {dir}\n")
