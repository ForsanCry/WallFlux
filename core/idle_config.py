import re
import tomllib
import tomli_w

from core.profile import WALLFLUX_DIR

# ─── Time parsing ─────────────────────────────────────────────────────────────

# A bare number means minutes: "10" -> 10 minutes, "10s" -> 10 seconds.
_UNITS = {
    "s": 1, "sec": 1, "secs": 1, "second": 1, "seconds": 1,
    "m": 60, "min": 60, "mins": 60, "minute": 60, "minutes": 60,
    "h": 3600, "hr": 3600, "hrs": 3600, "hour": 3600, "hours": 3600,
}
_PATTERN = re.compile(r"^\s*(\d+(?:\.\d+)?)\s*([a-z]*)\s*$", re.IGNORECASE)

MIN_SECONDS = 5


def parse_duration(text: str) -> float:
    """Convert '10', '10s', '10m', '1.5h', '10 minutes' to seconds."""
    match = _PATTERN.match(text)
    if not match:
        raise ValueError(f"Invalid time: '{text}'")

    number, unit = match.groups()
    unit = unit.lower() or "m"          # no unit -> minutes
    if unit not in _UNITS:
        raise ValueError(f"Unknown time unit: '{unit}' (use s, m or h)")

    seconds = float(number) * _UNITS[unit]
    if seconds < MIN_SECONDS:
        raise ValueError(f"Time must be at least {MIN_SECONDS} seconds")
    return seconds


def looks_like_duration(text: str) -> bool:
    """True if text can be parsed as a duration (used to tell it from a profile name)."""
    try:
        parse_duration(text)
        return True
    except ValueError:
        return False


def format_duration(seconds: float) -> str:
    """600 -> '10m', 90 -> '1m 30s', 45 -> '45s', 3600 -> '1h'."""
    total = int(round(seconds))
    hours, rest = divmod(total, 3600)
    minutes, secs = divmod(rest, 60)
    parts = []
    if hours:
        parts.append(f"{hours}h")
    if minutes:
        parts.append(f"{minutes}m")
    if secs or not parts:
        parts.append(f"{secs}s")
    return " ".join(parts)


def duration_to_text(seconds: float) -> str:
    """600 -> '10m', 7200 -> '2h', 90 -> '90s'. parse_duration can always read it back."""
    total = int(round(seconds))
    if total % 3600 == 0:
        return f"{total // 3600}h"
    if total % 60 == 0:
        return f"{total // 60}m"
    return f"{total}s"


# ─── idle.toml ────────────────────────────────────────────────────────────────

# One settings file for ALL idle profiles, next to profiles/ in the data directory
IDLE_FILE = WALLFLUX_DIR / "idle.toml"

# What happens after the video has played once
AFTER_CHOICES = ("dim", "screen_off", "hold", "loop")

DEFAULTS = {
    "timeout": "10m",    # how long the computer must be idle before the video starts
    "after":   "dim",    # one of AFTER_CHOICES
    "lock":    True,     # lock the screen when the user comes back
}


def idle_config_exists() -> bool:
    return IDLE_FILE.exists()


def load_idle_config() -> dict:
    """Settings from idle.toml. Missing or invalid values fall back to the defaults."""
    cfg = dict(DEFAULTS)
    if not IDLE_FILE.exists():
        return cfg

    with open(IDLE_FILE, "rb") as f:
        saved = tomllib.load(f).get("idle", {})

    for key in DEFAULTS:
        if key in saved:
            cfg[key] = saved[key]

    if not (isinstance(cfg["timeout"], str) and looks_like_duration(cfg["timeout"])):
        print(f"  Warning: invalid 'timeout' in idle.toml, using {DEFAULTS['timeout']}")
        cfg["timeout"] = DEFAULTS["timeout"]
    if cfg["after"] not in AFTER_CHOICES:
        print(f"  Warning: invalid 'after' in idle.toml, using {DEFAULTS['after']}")
        cfg["after"] = DEFAULTS["after"]
    if not isinstance(cfg["lock"], bool):
        print("  Warning: invalid 'lock' in idle.toml, using the default")
        cfg["lock"] = DEFAULTS["lock"]

    return cfg


def save_idle_config(cfg: dict):
    IDLE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(IDLE_FILE, "wb") as f:
        tomli_w.dump({"idle": cfg}, f)
