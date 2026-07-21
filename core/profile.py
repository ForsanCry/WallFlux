import tomllib
import tomli_w
from pathlib import Path

# Program directory — works regardless of where wallflux is installed
PROGRAM_DIR = Path(__file__).parent.parent.resolve()
CONFIG_FILE = PROGRAM_DIR / "config.toml"

def _load_config() -> dict:
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, "rb") as f:
            return tomllib.load(f)
    return {}

def _get_data_dir() -> Path:
    config = _load_config()
    data = config.get("wallflux", {}).get("data_path")
    if data:
        return Path(data)
    return PROGRAM_DIR

WALLFLUX_DIR = _get_data_dir()
PROFILES_DIR = WALLFLUX_DIR / "profiles"
WPORIGIN_DIR = WALLFLUX_DIR / "wporigin"

def get_profile_dir(name: str) -> Path:
    return PROFILES_DIR / name

def get_profile_toml(name: str) -> Path:
    return get_profile_dir(name) / "profile.toml"

def profile_exists(name: str) -> bool:
    return get_profile_toml(name).exists()

def load_profile(name: str) -> dict:
    toml_path = get_profile_toml(name)
    if not toml_path.exists():
        raise FileNotFoundError(f"Profile not found: {name}")
    with open(toml_path, "rb") as f:
        return tomllib.load(f)

def save_profile(name: str, data: dict):
    toml_path = get_profile_toml(name)
    toml_path.parent.mkdir(parents=True, exist_ok=True)
    with open(toml_path, "wb") as f:
        tomli_w.dump(data, f)

def list_profiles() -> list[str]:
    if not PROFILES_DIR.exists():
        return []
    return [
        d.name for d in PROFILES_DIR.iterdir()
        if d.is_dir() and (d / "profile.toml").exists()
    ]

def delete_profile(name: str):
    import shutil
    profile_dir = get_profile_dir(name)
    if not profile_dir.exists():
        raise FileNotFoundError(f"Profile not found: {name}")
    shutil.rmtree(profile_dir)

def get_copied_video_path(name: str, original_filename: str) -> Path:
    stem = Path(original_filename).stem
    return get_profile_dir(name) / f".COPIED_{stem}.mp4"

def get_highlight_path(name: str) -> Path:
    return get_profile_dir(name) / f".highlight_{name}.mp4"

def get_wp_path(name: str) -> Path:
    return get_profile_dir(name) / f".wp_{name}.mp4"
