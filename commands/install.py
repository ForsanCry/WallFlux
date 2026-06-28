import os
import shutil
import subprocess
import sys
from pathlib import Path

from core.profile import WALLFLUX_DIR, PROFILES_DIR, WPORIGIN_DIR, CONFIG_FILE

REQUIRED_BINARIES = ["mpv", "ffmpeg", "mpvpaper"]
LOCAL_BIN         = Path.home() / ".local" / "bin"
WRAPPER_PATH      = LOCAL_BIN / "wallflux"
EXTENSION_SRC     = Path(__file__).parent.parent / "extension"
EXTENSION_DST     = (
    Path.home()
    / ".local/share/gnome-shell/extensions/wallflux@wallflux"
)


def run():
    print("WallFlux Installer\n")

    _check_wayland()
    _check_gnome()
    missing = _check_dependencies()
    if missing:
        _print_install_hint(missing)
        sys.exit(1)
    _create_directories()
    _write_default_config()
    _install_extension()
    _install_wrapper()

    print("\n✓ WallFlux installed successfully.")
    print("  Run 'wallflux help' to get started.")


# ─── Checks ───────────────────────────────────────────────────────────────────

def _check_wayland():
    if not os.environ.get("WAYLAND_DISPLAY"):
        print("✗ Wayland session not detected.")
        print("  WallFlux requires a Wayland session (GNOME on Wayland).")
        sys.exit(1)
    print("✓ Wayland session detected")


def _check_gnome():
    result = subprocess.run(
        ["gnome-shell", "--version"],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        print("✗ GNOME Shell not found.")
        sys.exit(1)

    try:
        version_str = result.stdout.strip().split()[-1]
        major = int(version_str.split(".")[0])
    except (IndexError, ValueError):
        print("✗ Could not parse GNOME Shell version.")
        sys.exit(1)

    if major < 45:
        print(f"✗ GNOME Shell {major} detected. WallFlux requires GNOME 45+.")
        sys.exit(1)

    print(f"✓ GNOME Shell {major} detected")
    return major


def _check_dependencies() -> list[str]:
    missing = []
    for binary in REQUIRED_BINARIES:
        if shutil.which(binary) is None:
            missing.append(binary)
            print(f"✗ {binary} not found")
        else:
            print(f"✓ {binary} found")
    return missing


def _print_install_hint(missing: list[str]):
    """Detect the system package manager and print the right install command."""
    print(f"\n  Missing: {', '.join(missing)}")

    pm = _detect_package_manager()

    if pm == "dnf":
        print(f"  Run: sudo dnf install {' '.join(missing)}")
    elif pm == "apt":
        print(f"  Run: sudo apt install {' '.join(missing)}")
    elif pm == "pacman":
        print(f"  Run: sudo pacman -S {' '.join(missing)}")
    elif pm == "zypper":
        print(f"  Run: sudo zypper install {' '.join(missing)}")
    elif pm == "apk":
        print(f"  Run: sudo apk add {' '.join(missing)}")
    else:
        print(f"  Please install the missing packages using your system package manager.")

    print("  Then run 'wallflux install' again.")


def _detect_package_manager() -> str | None:
    """Return the name of the available package manager, or None."""
    for pm in ["dnf", "apt", "pacman", "zypper", "apk"]:
        if shutil.which(pm):
            return pm
    return None


# ─── Setup ────────────────────────────────────────────────────────────────────

def _create_directories():
    for d in [WALLFLUX_DIR, PROFILES_DIR, WPORIGIN_DIR]:
        d.mkdir(parents=True, exist_ok=True)
    print("✓ ~/.WallFlux/ directory structure created")


def _write_default_config():
    if CONFIG_FILE.exists():
        print("✓ config.toml already exists, skipping")
        return
    CONFIG_FILE.write_text('[wallflux]\nversion = "0.1.0"\n')
    print("✓ config.toml written")


def _install_extension():
    if not EXTENSION_SRC.exists():
        print("✗ Extension source not found. Is the wallflux repo intact?")
        sys.exit(1)

    if EXTENSION_DST.exists():
        shutil.rmtree(EXTENSION_DST)

    shutil.copytree(EXTENSION_SRC, EXTENSION_DST)
    print("✓ GNOME Shell extension installed")

    result = subprocess.run(
        ["gnome-extensions", "enable", "wallflux@wallflux"],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        print("  ⚠ Could not auto-enable extension.")
        print("    Run: gnome-extensions enable wallflux@wallflux")
    else:
        print("✓ Extension enabled")


def _install_wrapper():
    LOCAL_BIN.mkdir(parents=True, exist_ok=True)

    repo_dir    = Path(__file__).parent.parent.resolve()
    entry_point = repo_dir / "wallflux.py"

    WRAPPER_PATH.write_text(
        f'#!/bin/bash\nexec python3 "{entry_point}" "$@"\n'
    )
    WRAPPER_PATH.chmod(0o755)
    print(f"✓ Wrapper installed → {WRAPPER_PATH}")

    if str(LOCAL_BIN) not in os.environ.get("PATH", ""):
        print("\n  ⚠ ~/.local/bin is not in your PATH.")
        print("  Add this to your ~/.bashrc or ~/.zshrc:")
        print('    export PATH="$HOME/.local/bin:$PATH"')
        print("  Then run: source ~/.bashrc")
