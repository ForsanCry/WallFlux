def run():
    print("""
WallFlux — Wallpaper transition player for GNOME on Wayland

COMMANDS:
  install                      Check dependencies and install WallFlux
  uninstall                    Remove WallFlux from your system
  new <profile> <video>        Create a new profile from a video file
  play <profile>               Play a profile (fullscreen → wallpaper)
  <profile>                    Shortcut for 'play'
  list                         List all profiles
  rm <profile>                 Delete a profile and its files
  edit <profile> --name/--p    Rename a profile
  edit <profile> --time/--t    Change the cut point of a profile
  info <profile>               Show profile details
  help                         Show this help message

TIME FORMAT:
  32             →  0 min 32 sec
  32.450         →  0 min 32 sec 450 ms
  1:32           →  1 min 32 sec
  1:32.450       →  1 min 32 sec 450 ms
  1:04:32.450    →  1 hr  4 min 32 sec 450 ms

EXAMPLES:
  wallflux install
  wallflux new ghostedit ~/Videos/ghost.mp4
  wallflux new ghostedit ghost.mp4          # if already in that directory
  wallflux ghostedit                        # play shortcut
  wallflux play ghostedit
  wallflux edit ghostedit --t
  wallflux edit ghostedit --p
  wallflux info ghostedit
  wallflux rm ghostedit

FILES:
  ~/.WallFlux/profiles/<name>/
    .COPIED_<original>.mp4     source copy
    .highlight_<name>.mp4      fullscreen segment
    .wp_<name>.mp4             wallpaper segment
  ~/.WallFlux/wporigin/        original wallpaper backup
  ~/.WallFlux/config.toml      configuration
""")
