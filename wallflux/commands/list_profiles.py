from core.profile import list_profiles
from core.video import seconds_to_timestamp

def run():
    profiles = list_profiles()

    if not profiles:
        print("No profiles found.")
        print("Create one with: wallflux new <profile> <video>")
        return

    print(f"{'PROFILE':<20} {'CUT POINT':<12} {'DURATION':<12}")
    print("─" * 46)

    for name in sorted(profiles):
        try:
            from core.profile import load_profile
            p = load_profile(name)
            cut  = seconds_to_timestamp(p.get("cut_point", 0))
            dur  = seconds_to_timestamp(p.get("duration", 0))
        except Exception:
            cut, dur = "?", "?"
        print(f"{name:<20} {cut:<12} {dur:<12}")
