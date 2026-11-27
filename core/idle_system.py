"""Low-level system helpers for the idle feature (GNOME / Mutter, Wayland).

Everything here only talks to the desktop over D-Bus (or loginctl).
No polling, no state: the idle player decides *when* to call these.
"""
import subprocess
from pathlib import Path

from gi.repository import Gio, GLib

MUTTER = "org.gnome.Mutter.DisplayConfig"
MUTTER_PATH = "/org/gnome/Mutter/DisplayConfig"


# ---------- tiny D-Bus helper ----------

def _call(bus, name, path, iface, method, params=None, reply=None):
    """One synchronous D-Bus call. Returns the unpacked reply (tuple) or None on error."""
    try:
        conn = Gio.bus_get_sync(bus, None)
        res = conn.call_sync(
            name, path, iface, method, params,
            GLib.VariantType(reply) if reply else None,
            Gio.DBusCallFlags.NONE, 2000, None,
        )
        return res.unpack() if res is not None else ()
    except GLib.Error:
        return None


def _session(*args, **kw):
    return _call(Gio.BusType.SESSION, *args, **kw)


def _get_property(name, path, iface, prop):
    res = _session(name, path, "org.freedesktop.DBus.Properties", "Get",
                   GLib.Variant("(ss)", (iface, prop)), "(v)")
    return res[0] if res else None


# ---------- idle time ----------

def get_idle_ms():
    """Milliseconds since the last keyboard/mouse input, or None."""
    res = _session("org.gnome.Mutter.IdleMonitor", "/org/gnome/Mutter/IdleMonitor/Core",
                   "org.gnome.Mutter.IdleMonitor", "GetIdletime", None, "(t)")
    return res[0] if res else None


# ---------- blockers: something asked the session not to go idle ----------

def get_inhibitors():
    """Apps that asked to prevent idle (flag 8): list of (app_id, reason).

    Browsers set this while a video plays ("Playing video" / "Playing audio").
    """
    sm = "org.gnome.SessionManager"
    res = _session(sm, "/org/gnome/SessionManager", sm, "GetInhibitors", None, "(ao)")
    found = []
    for path in (res[0] if res else []):
        flags = _session(sm, path, "org.gnome.SessionManager.Inhibitor", "GetFlags", None, "(u)")
        if not flags or not (flags[0] & 8):
            continue
        app = _session(sm, path, "org.gnome.SessionManager.Inhibitor", "GetAppId", None, "(s)")
        why = _session(sm, path, "org.gnome.SessionManager.Inhibitor", "GetReason", None, "(s)")
        found.append((app[0] if app else "?", why[0] if why else ""))
    return found


def is_idle_inhibited():
    sm = "org.gnome.SessionManager"
    res = _session(sm, "/org/gnome/SessionManager", sm, "IsInhibited",
                   GLib.Variant("(u)", (8,)), "(b)")
    return bool(res and res[0])


# ---------- brightness ----------

def _mutter_backlight():
    """Panel backlight as GNOME sees it: dict(serial, connector, min, max, value) or None."""
    val = _get_property(MUTTER, MUTTER_PATH, MUTTER, "Backlight")
    if not val:
        return None
    serial, monitors = val
    for m in monitors:
        if m.get("active"):
            return {"serial": serial, "connector": m["connector"],
                    "min": m["min"], "max": m["max"], "value": m["value"]}
    return None


def _sysfs_backlight():
    """Fallback: first /sys/class/backlight device as (name, value, max) or None."""
    for d in sorted(Path("/sys/class/backlight").glob("*")):
        try:
            return d.name, int((d / "brightness").read_text()), int((d / "max_brightness").read_text())
        except (OSError, ValueError):
            continue
    return None


def get_brightness():
    """Current raw brightness value, or None if there is no controllable panel."""
    info = _mutter_backlight()
    if info:
        return info["value"]
    sysfs = _sysfs_backlight()
    return sysfs[1] if sysfs else None


def min_brightness():
    """Lowest value that still shows an image (Mutter's own minimum, else 1% of max)."""
    info = _mutter_backlight()
    if info:
        return info["min"]
    sysfs = _sysfs_backlight()
    return max(1, sysfs[2] // 100) if sysfs else None


def set_brightness(value):
    """Set raw brightness. Tries GNOME (Mutter) first, then logind. Returns True on success."""
    info = _mutter_backlight()
    if info:
        res = _session(MUTTER, MUTTER_PATH, MUTTER, "SetBacklight",
                       GLib.Variant("(usi)", (info["serial"], info["connector"], int(value))))
        if res is not None:
            return True
    sysfs = _sysfs_backlight()
    if sysfs:
        res = _call(Gio.BusType.SYSTEM, "org.freedesktop.login1",
                    "/org/freedesktop/login1/session/auto", "org.freedesktop.login1.Session",
                    "SetBrightness", GLib.Variant("(ssu)", ("backlight", sysfs[0], int(value))))
        return res is not None
    return False


# ---------- screen off / lock ----------

def set_screen_off(off):
    """Turn the display off (True) or back on (False) via PowerSaveMode."""
    res = _session("org.gnome.Mutter.DisplayConfig", MUTTER_PATH,
                   "org.freedesktop.DBus.Properties", "Set",
                   GLib.Variant("(ssv)", (MUTTER, "PowerSaveMode", GLib.Variant("i", 1 if off else 0))))
    return res is not None


def lock_screen():
    """Show the GNOME lock screen."""
    res = _session("org.gnome.ScreenSaver", "/org/gnome/ScreenSaver",
                   "org.gnome.ScreenSaver", "Lock")
    if res is None:
        subprocess.run(["loginctl", "lock-session"], check=False)


def is_locked():
    res = _session("org.gnome.ScreenSaver", "/org/gnome/ScreenSaver",
                   "org.gnome.ScreenSaver", "GetActive", None, "(b)")
    return bool(res and res[0])


# ---------- quick manual check:  python3 core/idle_system.py [--dim] ----------

if __name__ == "__main__":
    import sys, time

    print("idle (ms)   :", get_idle_ms())
    print("inhibited   :", is_idle_inhibited(), get_inhibitors())
    print("brightness  :", get_brightness(), "(min", min_brightness(), ")")
    print("locked      :", is_locked())

    if "--dim" in sys.argv:
        old = get_brightness()
        print("dimming for 4 s ...")
        print("set min     :", set_brightness(min_brightness()))
        time.sleep(4)
        print("restore     :", set_brightness(old))
