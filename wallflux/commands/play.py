import sys
import time
from pathlib import Path

from core.profile import (
    load_profile,
    profile_exists,
    get_highlight_path,
    get_wp_path,
    WPORIGIN_DIR,
)
from core.wallpaper import (
    get_current_wallpaper,
    save_wallpaper_to_wporigin,
    set_wallpaper,
    play_fullscreen,
    start_mpvpaper,
    stop_mpvpaper,
)
from core.gnome import ping_extension, minimize_all, restore_all


def run(profile_name: str):

    # ── 1. Profile check ──────────────────────────────────────────────────
    if not profile_exists(profile_name):
        print(f"✗ Profile '{profile_name}' not found.")
        print("  Run 'wallflux list' to see available profiles.")
        sys.exit(1)

    profile = load_profile(profile_name)

    highlight_path = get_highlight_path(profile_name)
    wp_path        = get_wp_path(profile_name)

    for p in [highlight_path, wp_path]:
        if not p.exists():
            print(f"✗ Missing file: {p.name}")
            print(f"  Re-run: wallflux new {profile_name} <video>")
            sys.exit(1)

    # ── 2. Extension check ────────────────────────────────────────────────
    if not ping_extension():
        print("✗ WallFlux GNOME extension is not running.")
        print("  Run: gnome-extensions enable wallflux@wallflux")
        print("  Then log out and back in, or restart GNOME Shell.")
        sys.exit(1)

    # ── 3. Save current wallpaper ─────────────────────────────────────────
    current_uri  = get_current_wallpaper()
    saved_path   = save_wallpaper_to_wporigin(current_uri, WPORIGIN_DIR)

    # ── 4. Play highlight fullscreen ──────────────────────────────────────
    #    ~200ms before mpv closes → minimize all windows
    window_ids = []

    def _pre_end():
        nonlocal window_ids
        window_ids = minimize_all()

    play_fullscreen(highlight_path, on_near_end=_pre_end, pre_end_ms=200)

    # ── 5. Small safety gap ───────────────────────────────────────────────
    #    If _pre_end fired but minimize hasn't fully settled yet
    time.sleep(0.05)

    # ── 6. Start mpvpaper ─────────────────────────────────────────────────
    mpvpaper_proc = start_mpvpaper(wp_path)

    # ── 7. Wait for mpvpaper to finish ────────────────────────────────────
    mpvpaper_proc.wait()

    # ── 8. Restore windows + wallpaper ───────────────────────────────────
    restore_all(window_ids)

    original_uri = saved_path.as_uri()   # file:///home/...
    set_wallpaper(original_uri)
