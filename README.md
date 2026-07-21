# WallFlux

A terminal-based wallpaper transition player for GNOME on Wayland.

Play a video fullscreen, then seamlessly transition it into a live wallpaper — all from a single command.

```
wallflux ghostedit
```

---

## How It Works

```
wallflux play <profile>
        ↓
Highlight segment plays fullscreen (with audio)
        ↓
Desktop minimizes → wallpaper segment plays as live wallpaper (with audio)
        ↓
Live wallpaper finishes → original wallpaper restored
```

WallFlux splits your video into two parts at a cut point you choose:
- `.highlight_<name>.mp4` — the fullscreen part
- `.wp_<name>.mp4` — the wallpaper part

Both are cut losslessly via ffmpeg (-c copy), so there is zero quality loss.

---

## Requirements

- GNOME 45+ on Wayland
- mpv
- ffmpeg
- python3
- Hanabi Extension (live wallpaper engine for GNOME)
  https://extensions.gnome.org/extension/6441/hanabi/

---

## Installation

```bash
git clone https://github.com/ForsanCry/WallFlux ~/wallflux
cd ~/wallflux
python3 wallflux.py install
```

Then install the Hanabi extension from GNOME Extensions and enable it:

```bash
gnome-extensions enable hanabi-extension@jeffshee.github.io
```

---

## Usage

### Create a profile

```bash
wallflux new ghostedit ~/Videos/ghost.mp4
# or if you are already in the video directory:
wallflux new ghostedit ghost.mp4
```

WallFlux will analyse the video, detect a cut point automatically (based on audio peaks and scene changes), show a preview, then cut losslessly.

### Play a profile

```bash
wallflux play ghostedit
# shortcut:
wallflux ghostedit
```

### Other commands

```bash
wallflux list                       # list all profiles
wallflux info ghostedit             # show profile details
wallflux rm ghostedit               # delete a profile
wallflux edit ghostedit --time      # change the cut point
wallflux edit ghostedit --name      # rename a profile
wallflux help                       # show all commands
```

### Time format

```
32             ->  0 min 32 sec
32.450         ->  0 min 32 sec 450 ms
1:32           ->  1 min 32 sec
1:32.450       ->  1 min 32 sec 450 ms
1:04:32.450    ->  1 hr  4 min 32 sec 450 ms
```

---

## File Structure

```
~/wallflux/               <- program files (git clone here)
~/.WallFlux/
├── config.toml
├── wporigin/             <- original wallpaper backup
└── profiles/
    └── ghostedit/
        ├── profile.toml
        ├── .COPIED_ghost.mp4
        ├── .highlight_ghostedit.mp4
        └── .wp_ghostedit.mp4
```

Profile files are prefixed with . so they stay hidden from media browsers.

---

## About This Project

WallFlux is a personal learning project built to explore:

- Python as a system orchestration tool (subprocess, threading, pathlib)
- GNOME Shell Extensions and the DBus API
- Wayland compositor constraints and why X11 tools do not work
- Lossless video processing with ffmpeg
- Inter-process communication between Python and GNOME Shell via gdbus
- Linux PATH, wrapper scripts, and how terminal commands are resolved

The project intentionally avoids heavy frameworks. Everything runs from the terminal. A UI may be added in the future, but the CLI comes first.

---

## Known Limitations

- GNOME Wayland only (no X11, no KDE)
- Requires Hanabi extension for live wallpaper rendering
- Hanabi may cause a brief GNOME Shell freeze on first load (this is a Hanabi/GStreamer issue, not WallFlux)
- Timing between highlight end and wallpaper start may vary slightly by hardware

---

## License

MIT
