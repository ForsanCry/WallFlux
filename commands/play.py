import sys
import time
from pathlib import Path

from core.profile import (
    load_profile, profile_exists,
    get_highlight_path, get_wp_path,
    WPORIGIN_DIR,
)
from core.wallpaper import (
    get_current_wallpaper,
    save_wallpaper_to_wporigin,
    set_wallpaper,
    play_fullscreen,
    hanabi_set_video,
    hanabi_enable,
    hanabi_disable,
    hanabi_set_play,
    hanabi_set_pause,
    hanabi_wait_for_renderer,
    hanabi_is_playing,
)
from core.gnome import ping_extension, minimize_all, restore_all

''' Playtime lag incase of bad performance '''
SETPLAY_LAG = 0.0

def run(profile_name: str):

    # 1. Profile check
    if not profile_exists(profile_name):
        print(f"Profile not found: {profile_name}")
        sys.exit(1)

    profile        = load_profile(profile_name)
    highlight_path = get_highlight_path(profile_name)
    wp_path        = get_wp_path(profile_name)

    for p in [highlight_path, wp_path]:
        if not p.exists():
            print(f"Missing file: {p.name}")
            sys.exit(1)

    # 2. Extension check
    if not ping_extension():
        print("WallFlux GNOME extension is not running.")
        print("  Run: gnome-extensions enable wallflux@wallflux")
        sys.exit(1)

    # 3. Save current wallpaper
    current_uri = get_current_wallpaper()
    saved_path  = save_wallpaper_to_wporigin(current_uri, WPORIGIN_DIR)

    # 4. Pre-load hanabi BEFORE highlight starts
    hanabi_set_video(wp_path)
    hanabi_enable()

    # 4a. Wait for renderer to appear on dbus
    if not hanabi_wait_for_renderer(timeout=10.0):
        print("  Warning: Hanabi renderer did not appear.")

    # 4b. Wait until isPlaying = false (renderer ready but not playing yet)
    deadline = time.monotonic() + 10.0
    while time.monotonic() < deadline:
        if hanabi_is_playing():
            hanabi_set_pause()  # pause spam
            break  # stop , ready

        time.sleep(0.001)

    # 5. Play highlight fullscreen, minimize on end
    window_ids = []

    def _on_end():
        nonlocal window_ids
        try:
            window_ids = minimize_all()
        except Exception as e:
            print(f"  Warning: minimize failed: {e}")

    # ------------------------------------------------------------------------
    #    play_fullscreen(highlight_path, on_near_end=_on_end, pre_end_ms=100)
    # ------------------------------------------------------------------------
    play_fullscreen(highlight_path)
    # mpv finished
    try:
        window_ids = minimize_all()
    except Exception as e:
        print(f"  Warning: minimize failed: {e}")
    # ------------------------------------------------------------------------
    # 6. Highlight done → setPlay immediately
    hanabi_set_play()

    # 7. Wait for wp video to finish
    wp_duration = profile.get("duration", 0) - profile.get("cut_point", 0)
    time.sleep(wp_duration + SETPLAY_LAG)

    # 8. Cleanup
    hanabi_disable()
    restore_all(window_ids)
    set_wallpaper(saved_path.as_uri())