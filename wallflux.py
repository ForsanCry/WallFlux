#!/usr/bin/env python3

import subprocess
import sys
from commands import install, uninstall, new, play, edit, rm, list_profiles, info, help_cmd, idle
from core.profile import profile_exists, has_cut, get_full_video_path


def _play(name: str):
    """Play a profile. Idle-only profiles have no cut, so just preview the whole video."""
    if profile_exists(name) and not has_cut(name):
        print(f"'{name}' is an idle-only profile. Previewing the whole video (press q to quit) ...")
        subprocess.run(["mpv", "--fullscreen", str(get_full_video_path(name))])
        return
    play.run(name)


def main():
    args = sys.argv[1:]

    if not args:
        help_cmd.run()
        return

    cmd = args[0]

    match cmd:
        case "install":
            install.run()
        case "uninstall":
            uninstall.run()
        case "new":
            if len(args) >= 2 and args[1] == "idle":
                # wallflux new idle <name> [video]
                if len(args) < 3:
                    print("Usage: wallflux new idle <name>           (add an existing profile)")
                    print("       wallflux new idle <name> <video>   (create a new idle profile)")
                    sys.exit(1)
                new.run_idle(args[2], args[3] if len(args) > 3 else None)
            elif len(args) < 3:
                print("Usage: wallflux new <profile> <video>")
                print("       wallflux new idle <name> [video]")
                sys.exit(1)
            else:
                new.run(args[1], args[2])
        case "play":
            if len(args) < 2:
                print("Usage: wallflux play <profile>")
                sys.exit(1)
            _play(args[1])
        case "list":
            list_profiles.run()
        case "rm":
            if len(args) >= 2 and args[1] == "idle":
                # wallflux rm idle <name>
                if len(args) < 3:
                    print("Usage: wallflux rm idle <profile>")
                    sys.exit(1)
                rm.run_idle(args[2])
            elif len(args) < 2:
                print("Usage: wallflux rm <profile>")
                print("       wallflux rm idle <profile>")
                sys.exit(1)
            else:
                rm.run(args[1])
        case "edit":
            if len(args) < 3:
                print("Usage: wallflux edit <profile> --name/--p | --time/--t")
                sys.exit(1)
            edit.run(args[1], args[2:])
        case "info":
            if len(args) < 2:
                print("Usage: wallflux info <profile>")
                sys.exit(1)
            info.run(args[1])
        case "idle":
            idle.run(args[1:])
        case "help":
            help_cmd.run()
        case _:
            # wallflux ghostedit -> play shortcut
            if profile_exists(cmd):
                _play(cmd)
            else:
                print(f"Unknown command or profile not found: '{cmd}'")
                print("Run 'wallflux help' for usage.")
                sys.exit(1)


if __name__ == "__main__":
    main()
