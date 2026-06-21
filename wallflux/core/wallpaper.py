import subprocess
import sys
from pathlib import Path


# ─── gsettings ────────────────────────────────────────────────────────────────

def get_current_wallpaper() -> str:
    """Read the current GNOME wallpaper URI from gsettings."""
    result = subprocess.run(
        [
            "gsettings", "get",
            "org.gnome.desktop.background",
            "picture-uri-dark",
        ],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        # Fallback to light wallpaper key
        result = subprocess.run(
            [
                "gsettings", "get",
                "org.gnome.desktop.background",
                "picture-uri",
            ],
            capture_output=True, text=True
        )
    if result.returncode != 0:
        print("✗ Could not read current wallpaper from gsettings.")
        sys.exit(1)

    # gsettings returns the value with single quotes: 'file:///...'
    return result.stdout.strip().strip("'")


def set_wallpaper(uri: str):
    """Set the GNOME wallpaper via gsettings (both light and dark keys)."""
    for key in ["picture-uri", "picture-uri-dark"]:
        subprocess.run(
            [
                "gsettings", "set",
                "org.gnome.desktop.background",
                key, uri,
            ],
            check=True
        )


def save_wallpaper_to_wporigin(uri: str, wporigin_dir: Path) -> Path:
    """
    Copy the current wallpaper file into ~/.WallFlux/wporigin/
    so we can restore it later even if the original moves.
    Returns the path to the saved copy.
    """
    import shutil

    # Strip file:// prefix if present
    file_path = Path(uri.replace("file://", ""))

    if not file_path.exists():
        print(f"✗ Wallpaper file not found: {file_path}")
        sys.exit(1)

    dest = wporigin_dir / file_path.name
    shutil.copy2(file_path, dest)
    return dest


# ─── mpvpaper ─────────────────────────────────────────────────────────────────

def start_mpvpaper(video_path: Path) -> subprocess.Popen:
    """
    Start mpvpaper on all outputs (*) with the given video.
    Audio is enabled, video loops once then exits (no-loop).
    Returns the Popen handle so the caller can wait on it.
    """
    proc = subprocess.Popen(
        [
            "mpvpaper",
            "-o", "no-audio=no loop-file=no",  # audio on, play once
            "*",                                 # all monitors
            str(video_path),
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return proc


def stop_mpvpaper(proc: subprocess.Popen):
    """Gracefully terminate mpvpaper if still running."""
    if proc and proc.poll() is None:
        proc.terminate()
        try:
            proc.wait(timeout=3)
        except subprocess.TimeoutExpired:
            proc.kill()


# ─── mpv fullscreen ───────────────────────────────────────────────────────────

def play_fullscreen(video_path: Path, on_near_end=None, pre_end_ms: int = 200):
    """
    Play video_path fullscreen via mpv.

    on_near_end: optional callback called ~pre_end_ms before the video ends.
                 Used to trigger minimize_all() just before mpv closes.
    """
    import threading
    import time

    if on_near_end is None:
        # Simple blocking play, no callback needed
        subprocess.run(
            [
                "mpv",
                "--fullscreen",
                "--really-fullscreen",
                str(video_path),
            ]
        )
        return

    # Get duration so we can schedule the callback
    from core.video import get_duration
    duration = get_duration(video_path)
    trigger_at = max(0.0, duration - (pre_end_ms / 1000.0))

    proc = subprocess.Popen(
        [
            "mpv",
            "--fullscreen",
            "--really-fullscreen",
            str(video_path),
        ]
    )

    def _watcher():
        start = time.monotonic()
        while proc.poll() is None:
            elapsed = time.monotonic() - start
            if elapsed >= trigger_at:
                on_near_end()
                return
            time.sleep(0.05)

    t = threading.Thread(target=_watcher, daemon=True)
    t.start()

    proc.wait()
    t.join(timeout=1)
