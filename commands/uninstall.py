import shutil
import subprocess
import sys
import tomllib
from pathlib import Path

WRAPPER_PATH  = Path.home() / ".local" / "bin" / "wallflux"
EXTENSION_DST = Path.home() / ".local/share/gnome-shell/extensions/wallflux@wallflux"
PROGRAM_DIR   = Path(__file__).parent.parent.resolve()
CONFIG_FILE   = PROGRAM_DIR / "config.toml"


def run():
    print("WallFlux Uninstaller")
    print()

    install_path, data_path = _read_paths()

    print("The following will be removed:")
    print(f"  {install_path}   (program files)")
    print(f"  {WRAPPER_PATH}   (wrapper)")
    print(f"  {EXTENSION_DST}   (GNOME extension)")
    print()

    remove_data = input(f"Remove profiles and data too? ({data_path}) [y/N]: ").strip().lower() == "y"
    if remove_data:
        print(f"  {data_path}   (profiles, config)")

    print()
    confirm = input("Are you sure? This cannot be undone. [y/N]: ").strip().lower()
    if confirm != "y":
        print("Aborted.")
        return

    subprocess.run(["gnome-extensions", "disable", "wallflux@wallflux"], capture_output=True)
    print("Extension disabled")

    if EXTENSION_DST.exists():
        shutil.rmtree(EXTENSION_DST)
        print("Extension files removed")

    if WRAPPER_PATH.exists():
        WRAPPER_PATH.unlink()
        print("Wrapper removed")

    if remove_data and data_path.exists():
        shutil.rmtree(data_path)
        print("Profiles and data removed")

    if install_path.exists():
        subprocess.run(["rm", "-rf", str(install_path)])
        print("Program files removed")

    print()
    print("WallFlux has been uninstalled.")


def _read_paths() -> tuple[Path, Path]:
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "rb") as f:
                config = tomllib.load(f)
            wf = config.get("wallflux", {})
            install = Path(wf.get("install_path", str(PROGRAM_DIR)))
            data    = Path(wf.get("data_path",    str(PROGRAM_DIR)))
            return install, data
        except Exception:
            pass
    return PROGRAM_DIR, PROGRAM_DIR
