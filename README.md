# WallFlux

A terminal-based wallpaper transition player for GNOME on Wayland.

Play a video fullscreen, then seamlessly transition it into a live wallpaper — all from a single command.

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

---

## Requirements

- GNOME 45+ on Wayland
- `mpv` — fullscreen video playback
- `ffmpeg` — video analysis and lossless cutting
- `python3`
- [Hanabi Extension](https://extensions.gnome.org/extension/6441/hanabi/) — live wallpaper engine for GNOME Wayland
- `tomli-w` Python package — `pip install tomli-w`

---

## Installation

```bash
git clone https://github.com/ForsanCry/WallFlux ~/wallflux
cd ~/wallflux
python3 wallflux.py install
```

Install and enable Hanabi from GNOME Extensions, then:

```bash
gnome-extensions enable hanabi-extension@jeffshee.github.io
```

Log out and back in to activate the WallFlux GNOME extension.

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

### Play a profile

```bash
wallflux play ghostedit
# shortcut:
wallflux ghostedit
```

### All commands

```
wallflux install                    Check dependencies and set up WallFlux
wallflux uninstall                  Remove WallFlux from your system
wallflux new <profile> <video>      Create a new profile
wallflux play <profile>             Play a profile
wallflux <profile>                  Shortcut for play
wallflux list                       List all profiles
wallflux rm <profile>               Delete a profile and its files
wallflux edit <profile> --name      Rename a profile
wallflux edit <profile> --time      Change the cut point
wallflux info <profile>             Show profile details
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
    ├── core/video.py       ffmpeg: analyse, detect cut point, lossless cut
    ├── core/profile.py     read/write profile.toml, manage file paths
    ├── core/wallpaper.py   gsettings, Hanabi control via DBus
    ├── core/gnome.py       WallFlux GNOME extension bridge (MinimizeAll etc.)
    │
    └── commands/
        ├── new.py          wallflux new
        ├── play.py         wallflux play — the main orchestrator
        ├── install.py      wallflux install
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
└── README.md
```

Profile files are prefixed with `.` so they are hidden from media browsers:

```
profiles/ghostedit/
    .COPIED_ghost.mp4         source copy
    .highlight_ghostedit.mp4  fullscreen segment
    .wp_ghostedit.mp4         wallpaper segment
    profile.toml              cut point, duration, original filename
```

---

## Known Limitations

- **GNOME Wayland only** — Hanabi and the WallFlux extension are GNOME-specific. KDE and X11 are not supported yet.
- **Hanabi renderer delay** — on first use after login, Hanabi takes a few seconds to start. WallFlux waits up to 10 seconds for the renderer to appear on DBus.
- **Brief GNOME freeze on Hanabi enable** — caused by GStreamer pipeline initialisation inside GNOME Shell. This is a Hanabi/GStreamer issue, not WallFlux. It only happens on the first play after login.
- **Timing variance** — wallpaper end time is calculated from `profile.toml` duration. A small lag constant (`SETPLAY_LAG`) can be adjusted in `play.py` if needed.

---

## Roadmap

- [ ] Multi-monitor support — highlight on primary, wallpaper on all screens
- [ ] KDE/Plasma support
- [ ] GUI (CLI comes first)
- [ ] `wallflux edit --lag` — adjust timing per profile

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
