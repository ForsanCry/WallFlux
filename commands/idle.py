import sys

from core.idle_config import (
    IDLE_FILE, AFTER_CHOICES, idle_config_exists,
    load_idle_config, save_idle_config,
    parse_duration, duration_to_text,
)
from core.profile import list_idle_profiles


# ─── Texts ────────────────────────────────────────────────────────────────────

# (setting, menu text) in the order shown by the wizard
_AFTER_MENU = [
    ("dim",        "Dim the screen to minimum (comes back when you touch keyboard/mouse)"),
    ("screen_off", "Turn the screen off"),
    ("hold",       "Stay on the last frame"),
    ("loop",       "Play again (loop)"),
]

# setting -> (what happens when the video has played, what happens on keyboard/mouse)
_AFTER_TEXT = {
    "dim":        ("screen dims to minimum",                     "brightness restored"),
    "screen_off": ("screen turns off",                           "screen turns back on"),
    "hold":       ("stays on the last frame",                    "video closes"),
    "loop":       ("plays again until you touch keyboard/mouse", "video closes"),
}

_TRUE_WORDS  = ("true", "yes", "y", "on", "1")
_FALSE_WORDS = ("false", "no", "n", "off", "0")


# ─── Entry ────────────────────────────────────────────────────────────────────

def run(args: list[str]):
    sub = args[0].lower() if args else "status"

    match sub:
        case "status":
            status()
        case "setup":
            setup()
        case "set":
            if len(args) < 3:
                _print_set_usage()
                sys.exit(1)
            set_value(args[1], " ".join(args[2:]))   # "10 minutes" arrives as two words
        case _:
            print(f"✗ Unknown idle command: '{sub}'")
            print("  Use: wallflux idle [status | setup | set <key> <value>]")
            sys.exit(1)


def ensure_setup():
    """Called after a profile joins idle. Runs the wizard the first time only."""
    if not idle_config_exists():
        setup()


# ─── Wizard ───────────────────────────────────────────────────────────────────

def setup():
    cfg = load_idle_config()          # defaults the first time, current values later

    print("\nWallFlux Idle — setup")
    print("These settings apply to all idle profiles.")
    print("Change them later with: wallflux idle set <key> <value>\n")

    try:
        cfg["timeout"] = _ask_timeout(cfg["timeout"])
        print()
        cfg["after"]   = _ask_after(cfg["after"])
        print()
        cfg["lock"]    = _ask_lock(cfg["lock"])
    except (KeyboardInterrupt, EOFError):
        print("\nAborted — nothing saved. Run: wallflux idle setup")
        return

    save_idle_config(cfg)
    print(f"\n✓ Saved: {IDLE_FILE}\n")
    _print_summary(cfg)


def _ask_timeout(current: str) -> str:
    print("1) How long should the computer be idle before the video starts?")
    print("   Examples: 10 (minutes), 30s, 10m, 1h")
    while True:
        raw = input(f"   Idle after [{current}]: ").strip()
        if not raw:
            return current
        try:
            return duration_to_text(parse_duration(raw))
        except ValueError as e:
            print(f"   ✗ {e}")


def _ask_after(current: str) -> str:
    print("2) When the video has played once:")
    for i, (_, text) in enumerate(_AFTER_MENU, start=1):
        print(f"   [{i}] {text}")
    default = [name for name, _ in _AFTER_MENU].index(current) + 1
    number = _ask_number(default, len(_AFTER_MENU))
    return _AFTER_MENU[number - 1][0]


def _ask_lock(current: bool) -> bool:
    print("3) What happens when you come back (touch keyboard/mouse)?")
    print("   [1] Lock screen asks for your password")
    print("   [2] Straight to your desktop  (screen stays unlocked)")
    number = _ask_number(1 if current else 2, 2)
    return number == 1


def _ask_number(default: int, count: int) -> int:
    while True:
        raw = input(f"   Choice [{default}]: ").strip()
        if not raw:
            return default
        if raw.isdigit() and 1 <= int(raw) <= count:
            return int(raw)
        print(f"   ✗ Please enter a number from 1 to {count}.")


# ─── Status / set ─────────────────────────────────────────────────────────────

def status():
    if not idle_config_exists():
        print("Idle is not set up yet.")
        print("  Add a profile:  wallflux new idle <name>")
        print("  Or run:         wallflux idle setup")
        return

    cfg = load_idle_config()
    print(f"\nIdle settings  ({IDLE_FILE})")
    print(f"  Idle after : {cfg['timeout']}")
    print(f"  After video: {cfg['after']}")
    print(f"  Lock       : {'yes' if cfg['lock'] else 'no'}\n")
    _print_summary(cfg)


def set_value(key: str, value: str):
    if not idle_config_exists():
        print("✗ Idle is not set up yet. Run: wallflux idle setup")
        sys.exit(1)

    cfg = load_idle_config()
    key = key.lower()

    if key in ("time", "timeout"):
        try:
            cfg["timeout"] = duration_to_text(parse_duration(value))
        except ValueError as e:
            print(f"✗ {e}")
            sys.exit(1)
    elif key == "after":
        if value.lower() not in AFTER_CHOICES:
            print(f"✗ Unknown value '{value}'. Use: {' | '.join(AFTER_CHOICES)}")
            sys.exit(1)
        cfg["after"] = value.lower()
    elif key == "lock":
        word = value.lower()
        if word in _TRUE_WORDS:
            cfg["lock"] = True
        elif word in _FALSE_WORDS:
            cfg["lock"] = False
        else:
            print("✗ Use: yes | no")
            sys.exit(1)
    else:
        print(f"✗ Unknown setting '{key}'.")
        _print_set_usage()
        sys.exit(1)

    save_idle_config(cfg)
    print("✓ Saved.\n")
    _print_summary(cfg)


def _print_set_usage():
    print("Usage: wallflux idle set <key> <value>")
    print("  time  <time>                    10 (minutes), 30s, 10m, 1h")
    print(f"  after <{' | '.join(AFTER_CHOICES)}>")
    print("  lock  <yes | no>")


# ─── Summary ──────────────────────────────────────────────────────────────────

def _print_summary(cfg: dict):
    pool = list_idle_profiles()
    if pool:
        who = f"a random idle profile plays fullscreen ({', '.join(pool)})"
    else:
        who = "a random idle profile plays fullscreen (none yet: wallflux new idle <name>)"

    ended, back = _AFTER_TEXT[cfg["after"]]
    lock = "lock screen appears" if cfg["lock"] else "desktop stays unlocked"

    print("What will happen:")
    print(f"  {'After ' + cfg['timeout'] + ' idle':<20}→ {who}")
    print(f"  {'When it has played':<20}→ {ended}")
    print(f"  {'On keyboard/mouse':<20}→ {back}, {lock}")
    # TODO (step 3): remove this note once the idle player exists
    print("\n  Note: the idle player itself is not built yet. Your settings are saved for it.\n")
