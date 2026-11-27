def run():
    print("""
WallFlux — Wallpaper transition player for GNOME on Wayland

COMMANDS:
  install                      Check dependencies and install WallFlux
  uninstall                    Remove WallFlux from your system
  new <profile> <video>        Create a new profile from a video file
  new idle <name>              Add an existing profile to idle
  new idle <name> <video>      Create an idle-only profile (no cut needed)
  play <profile>               Play a profile (fullscreen → wallpaper)
  <profile>                    Shortcut for 'play'
  list                         List all profiles
  rm <profile>                 Delete a profile and its files
  rm idle <profile>            Remove a profile from idle
  edit <profile> --name/--p    Rename a profile
  edit <profile> --time/--t    Change the cut point of a profile
                               (on an idle-only profile: add a cut point)
  info <profile>               Show profile details
  idle                         Show the idle settings
  idle setup                   Run the idle setup again
  idle set time <time>         Idle time before the video starts (10, 30s, 10m, 1h)
  idle set after <what>        After the video: dim | screen_off | hold | loop
  idle set lock <yes|no>       Lock the screen when you come back
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
  wallflux new idle ghostedit               # add an existing profile to idle
  wallflux new idle calm ~/Videos/calm.mp4  # idle-only profile, no cut
  wallflux rm idle ghostedit                # take it out of idle again

FILES:
  ~/wallflux/profiles/<name>/
    .COPIED_<original>.mp4     source copy (idle plays this one)
    .highlight_<name>.mp4      fullscreen segment
    .wp_<name>.mp4             wallpaper segment
  ~/wallflux/wporigin/        original wallpaper backup
  ~/wallflux/config.toml      configuration
  ~/wallflux/idle.toml        idle settings (shared by all idle profiles)
""")
