import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import tomli_w

from core.profile import PROGRAM_DIR, CONFIG_FILE
from core.wallpaper import HANABI_UUID

VERSION = "0.1.0"
REQUIRED_BINARIES = ["mpv", "ffmpeg"]
MIN_GNOME = 45

EXT_SRC = PROGRAM_DIR / "extension"
EXT_ROOT = Path.home() / ".local" / "share" / "gnome-shell" / "extensions"
WRAPPER = Path.home() / ".local" / "bin" / "wallflux"
HANABI_URL = "https://extensions.gnome.org/extension/6441/hanabi/"


def _fail(msg: str):
    print(f"✗ {msg}")
    sys.exit(1)


def _ok(msg: str):
    print(f"✓ {msg}")


# ── Checks ────────────────────────────────────────────────────────────

def _check_wayland():
    if os.environ.get("XDG_SESSION_TYPE", "").lower() != "wayland":
        _fail("WallFlux needs a Wayland session (X11 is not supported).")
    _ok("Wayland session")


def _check_gnome() -> int:
    result = subprocess.run(["gnome-shell", "--version"], capture_output=True, text=True)
    if result.returncode != 0:
        _fail("GNOME Shell not found.")
    match = re.search(r"(\d+)", result.stdout)
    if not match:
        _fail(f"Could not parse GNOME version: {result.stdout.strip()}")
    major = int(match.group(1))
    if major < MIN_GNOME:
        _fail(f"GNOME {MIN_GNOME}+ required, found {major}.")
    _ok(f"GNOME Shell {major}")
    return major


def _print_install_hint(missing: list[str]):
    pkgs = " ".join(missing)
    managers = [
        ("dnf", f"sudo dnf install {pkgs}"),
        ("apt", f"sudo apt install {pkgs}"),
        ("pacman", f"sudo pacman -S {pkgs}"),
        ("zypper", f"sudo zypper install {pkgs}"),
        ("apk", f"sudo apk add {pkgs}"),
    ]
    for binary, cmd in managers:
        if shutil.which(binary):
            print(f"  Try: {cmd}")
            return
    print(f"  Install these with your package manager: {pkgs}")


def _check_dependencies():
    missing = [b for b in REQUIRED_BINARIES if shutil.which(b) is None]
    for b in REQUIRED_BINARIES:
        if b in missing:
            print(f"✗ {b} not found")
        else:
            _ok(f"{b} found")
    if missing:
        print()
        print("Missing: " + ", ".join(missing))
        _print_install_hint(missing)
        sys.exit(1)


# ── Setup steps ───────────────────────────────────────────────────────

def _ask_data_dir() -> Path:
    print()
    print("Where should WallFlux keep your profiles and data?")
    print(f"  [1] {PROGRAM_DIR}   (program folder, visible)")
    print("  [2] ~/.wallflux        (hidden)")
    print("  [3] Custom path")
    choice = input("Choice [1]: ").strip() or "1"

    if choice == "1":
        return PROGRAM_DIR
    if choice == "2":
        return Path.home() / ".wallflux"
    if choice == "3":
        raw = input("Path: ").strip()
        if not raw:
            _fail("No path given.")
        return Path(raw).expanduser().resolve()
    _fail("Invalid choice.")


def _create_directories(data_dir: Path):
    (data_dir / "profiles").mkdir(parents=True, exist_ok=True)
    (data_dir / "wporigin").mkdir(parents=True, exist_ok=True)
    _ok(f"Data directory: {data_dir}")


def _write_config(data_dir: Path):
    config = {
        "wallflux": {
            "version": VERSION,
            "install_path": str(PROGRAM_DIR),
            "data_path": str(data_dir),
        }
    }
    with open(CONFIG_FILE, "wb") as f:
        tomli_w.dump(config, f)
    _ok(f"Config written: {CONFIG_FILE}")


def _install_extension(gnome_major: int):
    if not EXT_SRC.exists():
        _fail(f"Extension folder missing: {EXT_SRC}")

    meta_path = EXT_SRC / "metadata.json"
    meta = json.loads(meta_path.read_text())
    uuid = meta["uuid"]

    versions = meta.get("shell-version", [])
    if str(gnome_major) not in versions:
        versions.append(str(gnome_major))
        meta["shell-version"] = versions
        meta_path.write_text(json.dumps(meta, indent=2) + "\n")

    dest = EXT_ROOT / uuid
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(EXT_SRC, dest)
    _ok(f"Extension copied: {dest}")

    result = subprocess.run(["gnome-extensions", "enable", uuid], capture_output=True, text=True)
    if result.returncode == 0:
        _ok("Extension enabled")
    else:
        print("! Could not enable the extension yet.")
    print("  Note: a new extension may need a logout/login before GNOME sees it.")


def _install_wrapper(data_dir: Path):
    WRAPPER.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "#!/bin/sh",
        f'export WALLFLUX_INSTALL="{PROGRAM_DIR}"',
        f'export WALLFLUX_DATA="{data_dir}"',
        'exec python3 "$WALLFLUX_INSTALL/wallflux.py" "$@"',
        "",
    ]
    WRAPPER.write_text("\n".join(lines))
    WRAPPER.chmod(0o755)
    _ok(f"Command installed: {WRAPPER}")

    path_dirs = os.environ.get("PATH", "").split(":")
    if str(WRAPPER.parent) not in path_dirs:
        print(f"! {WRAPPER.parent} is not in your PATH. Add this to ~/.bashrc:")
        print('    export PATH="$HOME/.local/bin:$PATH"')


def _check_hanabi():
    result = subprocess.run(["gnome-extensions", "list"], capture_output=True, text=True)
    if HANABI_UUID in result.stdout:
        _ok("Hanabi extension found")
    else:
        print("! Hanabi extension not found (needed for the live wallpaper).")
        print(f"  Install it from: {HANABI_URL}")


# ── Entry ─────────────────────────────────────────────────────────────

def run():
    print("\nWallFlux Installer\n")
    _check_wayland()
    gnome_major = _check_gnome()
    _check_dependencies()

    data_dir = _ask_data_dir()
    print()
    _create_directories(data_dir)
    _write_config(data_dir)
    _install_extension(gnome_major)
    _install_wrapper(data_dir)
    _check_hanabi()

    print("\n✓ WallFlux installed.")
    print("  Try: wallflux help")
