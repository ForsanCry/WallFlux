from core.profile import list_profiles
from core.video import seconds_to_timestamp

def run():
    profiles = list_profiles()

    if not profiles:
        print("No profiles found.")
        print("Create one with: wallflux new <profile> <video>")
        return

    print(f"{'PROFILE':<20} {'CUT POINT':<12} {'DURATION':<12} {'IDLE'}")
    print("─" * 52)

    for name in sorted(profiles):
        try:
            from core.profile import load_profile
            p = load_profile(name)
            # Idle-only profiles are never cut, so they have no cut point
            if "cut_point" in p:
                cut = seconds_to_timestamp(p["cut_point"])
            else:
                cut = "--:--.---"
            dur  = seconds_to_timestamp(p.get("duration", 0))
            idle = str(bool(p.get("idle", False)))
        except Exception:
            cut, dur, idle = "?", "?", "?"
        print(f"{name:<20} {cut:<12} {dur:<12} {idle}")
