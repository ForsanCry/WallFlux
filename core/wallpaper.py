import subprocess
import sys
import time
from pathlib import Path

def get_current_wallpaper() -> str:
    for key in ["picture-uri-dark", "picture-uri"]:
        result = subprocess.run(
            ["gsettings", "get", "org.gnome.desktop.background", key],
            capture_output=True, text=True
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip().strip("'")
    print("Could not read current wallpaper.")
    sys.exit(1)

def set_wallpaper(uri: str):
    for key in ["picture-uri", "picture-uri-dark"]:
        subprocess.run(["gsettings", "set", "org.gnome.desktop.background", key, uri], check=True)

def save_wallpaper_to_wporigin(uri: str, wporigin_dir: Path) -> Path:
    import shutil
    file_path = Path(uri.replace("file://", ""))
    if not file_path.exists():
        print(f"Wallpaper file not found: {file_path}")
        sys.exit(1)
    dest = wporigin_dir / file_path.name
    if file_path.resolve() != dest.resolve():
        shutil.copy2(file_path, dest)
    return dest

HANABI_UUID   = "hanabi-extension@jeffshee.github.io"
HANABI_SCHEMA = "io.github.jeffshee.hanabi-extension"
HANABI_DBUS   = "io.github.jeffshee.HanabiRenderer"
HANABI_PATH   = "/io/github/jeffshee/HanabiRenderer"

def hanabi_set_video(video_path: Path):
    subprocess.run(["gsettings", "set", HANABI_SCHEMA, "video-path", str(video_path)], check=True)

def hanabi_enable():
    # Check if already running
    result = subprocess.run(
        ["gdbus", "call", "--session", "--dest", "org.freedesktop.DBus",
         "--object-path", "/org/freedesktop/DBus", "--method", "org.freedesktop.DBus.ListNames"],
        capture_output=True, text=True
    )
    already_running = HANABI_DBUS in result.stdout

    subprocess.run(["gsettings", "set", HANABI_SCHEMA, "mute", "true"], capture_output=True)

    if not already_running:
        # First time — need to enable
        subprocess.run(["gnome-extensions", "disable", HANABI_UUID], capture_output=True)
        time.sleep(0.5)
        subprocess.run(["gnome-extensions", "enable", HANABI_UUID], check=True)

def hanabi_disable():
    subprocess.run(["gsettings", "set", HANABI_SCHEMA, "mute", "true"], capture_output=True)
    subprocess.run(["gnome-extensions", "disable", HANABI_UUID], capture_output=True)

def hanabi_set_play():
    # Unmute before playing
    subprocess.run(["gsettings", "set", HANABI_SCHEMA, "mute", "false"], capture_output=True)
    result = subprocess.run(
        ["gdbus", "call", "--session", "--dest", HANABI_DBUS,
         "--object-path", HANABI_PATH, "--method", f"{HANABI_DBUS}.setPlay"],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        print(f"  setPlay warning: {result.stderr.strip()}")

def hanabi_wait_for_renderer(timeout: float = 15.0) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        result = subprocess.run(
            ["gdbus", "call", "--session", "--dest", "org.freedesktop.DBus",
             "--object-path", "/org/freedesktop/DBus", "--method", "org.freedesktop.DBus.ListNames"],
            capture_output=True, text=True
        )
        if HANABI_DBUS in result.stdout:
            return True
        time.sleep(0.2)
    return False

def play_fullscreen(video_path: Path, on_near_end=None, pre_end_ms: int = 200):
    import threading
    if on_near_end is None:
        subprocess.run(["mpv", "--fullscreen", str(video_path)])
        return
    from core.video import get_duration
    duration   = get_duration(video_path)
    trigger_at = max(0.0, duration - (pre_end_ms / 1000.0))
    proc = subprocess.Popen(["mpv", "--fullscreen", str(video_path)])
    def _watcher():
        start = time.monotonic()
        fired = False
        while proc.poll() is None:
            if not fired and (time.monotonic() - start) >= trigger_at:
                on_near_end()
                fired = True
            time.sleep(0.05)
    t = threading.Thread(target=_watcher, daemon=True)
    t.start()
    proc.wait()
    t.join(timeout=1)

def hanabi_is_playing() -> bool:
    result = subprocess.run(
        [
            "gdbus", "call", "--session",
            "--dest",        HANABI_DBUS,
            "--object-path", HANABI_PATH,
            "--method",      "org.freedesktop.DBus.Properties.Get",
            "io.github.jeffshee.HanabiRenderer", "isPlaying",
        ],
        capture_output=True, text=True
    )
    return result.returncode == 0 and "true" in result.stdout

def hanabi_set_pause():
    subprocess.run(
        [
            "gdbus", "call", "--session",
            "--dest",        HANABI_DBUS,
            "--object-path", HANABI_PATH,
            "--method",      f"{HANABI_DBUS}.setPause",
        ],
        capture_output=True, text=True
    )
