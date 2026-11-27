# WallFlux

A terminal-based wallpaper transition player for GNOME on Wayland.

Play a video fullscreen, then seamlessly transition it into a live wallpaper — all from a single command.
When you step away from the computer, WallFlux can also play one of your videos like a screensaver.

```bash
wallflux ghostedit
```

---

## What It Does

WallFlux splits a video into two segments at a cut point you define:

- **Highlight** — plays fullscreen with audio (the "edit" part)
- **Wallpaper** — plays as a live wallpaper after the highlight ends

```
wallflux play <profile>
        ↓
Highlight plays fullscreen (mpv, with audio)
        ↓
Windows minimize → live wallpaper starts (Hanabi, with audio)
        ↓
Wallpaper segment ends → original wallpaper restored
```

Both segments are cut **losslessly** via ffmpeg (`-c copy`). Zero quality loss.

**Idle mode** (in progress): after a set time without keyboard or mouse input, a random idle profile
plays fullscreen once. Then the screen dims, turns off, holds the last frame or loops — your choice.
It never starts while a video is playing in your browser. See [Idle](#idle).

---

## Requirements

- GNOME 45+ on Wayland
- `mpv` — fullscreen video playback
- `ffmpeg` — video analysis and lossless cutting
- `python3` with PyGObject (`gi`, preinstalled on Fedora)
- `tomli-w` Python package — `pip install tomli-w`
- [Hanabi](https://github.com/jeffshee/gnome-ext-hanabi) — live wallpaper engine for GNOME Wayland

### Which Hanabi for which GNOME

Hanabi ships different versions for different GNOME releases. Check yours with `gnome-shell --version`:

| GNOME   | Hanabi                                                                                              |
|---------|-----------------------------------------------------------------------------------------------------|
| 45 – 49 | `javascript` branch                                                                                 |
| 50      | `main` branch                                                                                       |
| 51      | `main` branch + [PR #264](https://github.com/jeffshee/gnome-ext-hanabi/pull/264) (not merged yet)   |

GNOME 51 removed an API that Hanabi's `main` branch still uses, so it fails to load without that PR.

---

## Installation

```bash
git clone https://github.com/ForsanCry/WallFlux ~/wallflux
cd ~/wallflux
python3 wallflux.py install
```

The install wizard:

1. Checks dependencies (`mpv`, `ffmpeg`, `tomli-w`, Hanabi)
2. Asks where to keep your profiles (data directory) and writes `config.toml`
3. Installs the `wallflux` command into `~/.local/bin`
4. Installs the WallFlux GNOME extension

Then log out and back in to activate the WallFlux GNOME extension, and make sure Hanabi is enabled:

```bash
gnome-extensions enable hanabi-extension@jeffshee.github.io
```

Installing never sets up anything in the background. Idle settings are only asked the first time
you add an idle profile.

---

## Usage

### Create a profile

```bash
wallflux new ghostedit ~/Videos/ghost.mp4
# or from the video's directory:
wallflux new ghostedit ghost.mp4
```

WallFlux will:
1. Copy the video into the profile directory
2. Analyse audio peaks and scene changes to detect a cut point
3. Show a preview so you can confirm or adjust
4. Cut losslessly into `.highlight_<name>.mp4` and `.wp_<name>.mp4`

Command names (`new`, `play`, `list`, `idle`, …) cannot be used as profile names.

### Play a profile

```bash
wallflux play ghostedit
# shortcut:
wallflux ghostedit
```

### Manage profiles

```bash
wallflux list                  # all profiles, cut points and idle status
wallflux info ghostedit        # details of one profile
wallflux edit ghostedit --p    # rename (--name)
wallflux edit ghostedit --t    # change the cut point (--time)
wallflux rm ghostedit          # delete a profile and its files
```

---

## Idle

> **Status:** idle profiles and settings are done. The background player that actually starts the
> video when you are away is being built.

### Idle profiles

Any profile can join idle. Idle plays the **whole source video** fullscreen, not the cut segments.

```bash
wallflux new idle ghostedit               # add an existing profile to idle
wallflux new idle calm ~/Videos/calm.mp4  # idle-only profile, no cut needed
wallflux rm idle ghostedit                # take it out of idle again
```

An idle-only profile has no cut point (`list` shows `--:--.---`). You can still turn it into a normal
profile later with `wallflux edit calm --t`. It stays in idle.

When several profiles are in idle, a random one is picked each time.

### Idle settings

The first time a profile joins idle, a short setup asks three questions. One set of settings applies
to all idle profiles:

1. **How long until idle starts** — `10` (minutes), `30s`, `10m`, `1h`
2. **What happens after the video has played once**
   - `dim` — dim the screen to minimum (default)
   - `screen_off` — turn the screen off
   - `hold` — stay on the last frame
   - `loop` — play again
3. **Lock when you come back** — show the lock screen, or go straight to the desktop

```bash
wallflux idle                      # show settings and what will happen
wallflux idle setup                # run the setup again
wallflux idle set time 15m
wallflux idle set after screen_off
wallflux idle set lock no
```

Settings live in `idle.toml`:

```toml
[idle]
timeout = "10m"
after = "dim"
lock = true
```

### When idle does not start

Idle respects GNOME's own "don't go idle" signal. Browsers send it while a video is playing
(for example YouTube in Firefox or Zen), so idle waits until playback stops.

Keep the idle time shorter than GNOME's automatic suspend (Settings → Power), otherwise the
computer goes to sleep first.

---

## All commands

```
wallflux install                    Check dependencies and set up WallFlux
wallflux uninstall                  Remove WallFlux from your system
wallflux new <profile> <video>      Create a new profile
wallflux new idle <name>            Add an existing profile to idle
wallflux new idle <name> <video>    Create an idle-only profile (no cut needed)
wallflux play <profile>             Play a profile
wallflux <profile>                  Shortcut for play
wallflux list                       List all profiles
wallflux rm <profile>               Delete a profile and its files
wallflux rm idle <profile>          Remove a profile from idle
wallflux edit <profile> --name/--p  Rename a profile
wallflux edit <profile> --time/--t  Change the cut point (adds one to idle-only profiles)
wallflux info <profile>             Show profile details
wallflux idle                       Show the idle settings
wallflux idle setup                 Run the idle setup again
wallflux idle set <key> <value>     Change one idle setting (time, after, lock)
wallflux help                       Show this message
```

### Time format

```
32             →  0 min 32 sec
32.450         →  0 min 32 sec 450 ms
1:32           →  1 min 32 sec
1:32.450       →  1 min 32 sec 450 ms
1:04:32.450    →  1 hr  4 min 32 sec 450 ms
```

---

## How It Works

### Architecture

```
wallflux (Python)
    │
    ├── core/video.py         ffmpeg: analyse, detect cut point, lossless cut
    ├── core/profile.py       read/write profile.toml, manage file paths, idle flag
    ├── core/wallpaper.py     gsettings, Hanabi control via DBus
    ├── core/gnome.py         WallFlux GNOME extension bridge (MinimizeAll etc.)
    ├── core/idle_config.py   idle.toml load/save, duration parsing
    ├── core/idle_system.py   idle time, blockers, brightness, screen off, lock (DBus)
    │
    └── commands/
        ├── new.py            wallflux new / new idle
        ├── play.py           wallflux play — the main orchestrator
        ├── idle.py           wallflux idle — setup wizard, status, set
        ├── install.py        wallflux install
        └── ...
```

### Play flow in detail

```
1. Read profile.toml → get highlight path, wp path, duration
2. Set Hanabi video path via gsettings
3. Enable Hanabi → wait for renderer on DBus → send setPause
   (Hanabi loads the video silently in the background)
4. Play highlight fullscreen via mpv
5. mpv exits → call MinimizeAll on WallFlux GNOME extension
6. Send setPlay to Hanabi → unmute
7. Sleep for wp_duration seconds
8. Disable Hanabi → restore windows → restore original wallpaper
```

### Idle building blocks

Everything goes through GNOME's own DBus services, so nothing is hardcoded to one machine:

| What                     | How                                                                 |
|--------------------------|---------------------------------------------------------------------|
| Time since last input    | `org.gnome.Mutter.IdleMonitor`                                      |
| "Video is playing" check | `org.gnome.SessionManager.IsInhibited` (idle flag)                  |
| Dim the screen           | `org.gnome.Mutter.DisplayConfig.SetBacklight`, logind as a fallback |
| Turn the screen off      | `DisplayConfig.PowerSaveMode`                                       |
| Lock                     | `org.gnome.ScreenSaver.Lock`                                        |

On a desktop without a built-in panel there is no backlight to dim, so `dim` falls back gracefully.

### GNOME Extension (wallflux@wallflux)

A small GNOME Shell extension written in JavaScript. It exposes three DBus methods:

- `Ping` → returns `"pong"` (health check)
- `MinimizeAll` → minimizes all normal windows on the active workspace, returns their IDs
- `RestoreAll(ids)` → restores only the windows WallFlux minimized

Python talks to the extension via `gdbus call`.

### Hanabi

[Hanabi](https://github.com/jeffshee/gnome-ext-hanabi) is a GNOME Shell extension that renders video as a live wallpaper using GStreamer. WallFlux controls it via:

- `gsettings` → set video path, mute/unmute, volume
- DBus → `setPlay` / `setPause` on `io.github.jeffshee.HanabiRenderer`

These names are the same in every Hanabi version, so WallFlux works with all of them unchanged.
WallFlux pre-loads Hanabi while the highlight is playing so the transition is instant.

---

## File Structure

```
~/wallflux/
├── wallflux.py          entry point
├── commands/            one file per command
├── core/                shared logic
├── extension/           GNOME Shell extension source
├── profiles/            created by wallflux new (git-ignored)
├── wporigin/            original wallpaper backup (git-ignored)
├── config.toml          install paths (git-ignored)
├── idle.toml            idle settings (git-ignored)
└── README.md
```

Profile files are prefixed with `.` so they are hidden from media browsers:

```
profiles/ghostedit/
    .COPIED_ghost.mp4         source copy (idle plays this one)
    .highlight_ghostedit.mp4  fullscreen segment
    .wp_ghostedit.mp4         wallpaper segment
    profile.toml              cut point, duration, original filename, idle flag
```

---

## Known Limitations

- **GNOME on Wayland only, by design** — WallFlux is built around GNOME Shell, Mutter and Hanabi.
- **New GNOME releases** — GNOME ships every six months (March and September) and refuses extensions
  that do not list the new version. Both the WallFlux extension and Hanabi need an update each time.
- **Hanabi renderer delay** — on first use after login, Hanabi takes a few seconds to start. WallFlux waits up to 10 seconds for the renderer to appear on DBus.
- **Brief GNOME freeze on Hanabi enable** — caused by GStreamer pipeline initialisation inside GNOME Shell. This is a Hanabi/GStreamer issue, not WallFlux. It only happens on the first play after login.
- **Timing variance** — wallpaper end time is calculated from `profile.toml` duration. A small lag constant (`SETPLAY_LAG`) can be adjusted in `play.py` if needed.
- **Single monitor** — multi-monitor setups are not handled yet.

---

## Roadmap

- [x] Idle profiles and settings (`new idle`, `rm idle`, `wallflux idle`)
- [ ] Idle player — start on idle, dim / screen off / hold / loop, restore on input, lock
- [ ] Optional background service for idle (asked once, never installed by `install`)
- [ ] Multi-monitor support — highlight on primary, wallpaper on all screens
- [ ] `wallflux edit --lag` — adjust timing per profile
- [ ] GUI (CLI comes first)

---

## About This Project

WallFlux is a personal learning project. The goal was to explore:

- Python as a system orchestration tool (`subprocess`, `threading`, `pathlib`, `tomllib`)
- GNOME Shell Extensions and the DBus API
- Wayland compositor constraints and why X11 tools do not work
- Lossless video processing with ffmpeg
- Inter-process communication between Python and GNOME Shell via `gdbus`
- Linux PATH, wrapper scripts, and how terminal commands are resolved
- Git and project structure

The project intentionally avoids heavy frameworks. Everything runs from the terminal.

---

## License

MIT
