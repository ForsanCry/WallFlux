import subprocess
import sys


DBUS_DEST   = "org.wallflux.Shell"
DBUS_PATH   = "/org/wallflux/Shell"
DBUS_IFACE  = "org.wallflux.Shell"


def _gdbus_call(method: str, args: str = "") -> subprocess.CompletedProcess:
    cmd = [
        "gdbus", "call",
        "--session",
        "--dest",        DBUS_DEST,
        "--object-path", DBUS_PATH,
        "--method",      f"{DBUS_IFACE}.{method}",
    ]
    if args:
        cmd.append(args)
    return subprocess.run(cmd, capture_output=True, text=True)


def ping_extension() -> bool:
    """Returns True if the WallFlux GNOME extension is running and reachable."""
    result = _gdbus_call("Ping")
    return result.returncode == 0 and "pong" in result.stdout


def minimize_all() -> list[str]:
    """
    Minimizes all normal windows on the active workspace.
    Returns a list of window IDs so we can restore them later.
    """
    result = _gdbus_call("MinimizeAll")
    if result.returncode != 0:
        _extension_error("MinimizeAll")
        return []

    # gdbus returns: (['id1', 'id2', ...],)
    # Parse it simply — we just need the ids back for RestoreAll
    raw = result.stdout.strip()
    ids = _parse_string_array(raw)
    return ids


def restore_all(window_ids: list[str]):
    """Restores windows that WallFlux previously minimized."""
    if not window_ids:
        return

    # Format ids as a dbus array of strings: "['id1', 'id2']"
    array_arg = "['" + "', '".join(window_ids) + "']"
    result = _gdbus_call("RestoreAll", array_arg)
    if result.returncode != 0:
        _extension_error("RestoreAll")


def _parse_string_array(raw: str) -> list[str]:
    """Parse gdbus output like (['123', '456'],) into ['123', '456']"""
    try:
        import ast
        # gdbus wraps the return in a tuple: (['a', 'b'],)
        # ast.literal_eval handles this safely
        parsed = ast.literal_eval(raw)
        if isinstance(parsed, tuple) and parsed:
            inner = parsed[0]
            if isinstance(inner, list):
                return [str(i) for i in inner]
    except Exception:
        pass
    return []


def _extension_error(method: str):
    raise RuntimeError(
        f"WallFlux extension did not respond to {method}. "
        "Run: gnome-extensions enable wallflux@wallflux"
    )
