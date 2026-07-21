#!/usr/bin/env python3

import sys
from commands import install, new, play, edit, rm, list_profiles, info, help_cmd
from core.profile import profile_exists

def main():
    args = sys.argv[1:]

    if not args:
        help_cmd.run()
        return

    cmd = args[0]

    match cmd:
        case "install":
            install.run()
        case "new":
            if len(args) < 3:
                print("Usage: wallflux new <profile> <video>")
                sys.exit(1)
            new.run(args[1], args[2])
        case "play":
            if len(args) < 2:
                print("Usage: wallflux play <profile>")
                sys.exit(1)
            play.run(args[1])
        case "list":
            list_profiles.run()
        case "rm":
            if len(args) < 2:
                print("Usage: wallflux rm <profile>")
                sys.exit(1)
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
        case "help":
            help_cmd.run()
        case _:
            # wallflux ghostedit → play shortcut
            if profile_exists(cmd):
                play.run(cmd)
            else:
                print(f"Unknown command or profile not found: '{cmd}'")
                print("Run 'wallflux help' for usage.")
                sys.exit(1)

if __name__ == "__main__":
    main()
