#!/usr/bin/env python3
"""kcptun-manager CLI. Entry point for non-interactive commands."""
import sys
import os
import argparse

BASE = "/opt/kcptun-manager"
sys.path.insert(0, BASE)


def cmd_export(args):
    from lib.exporter import export, print_instructions
    path = export(prefix=args.name, out_dir=args.out)
    if not args.quiet:
        print_instructions(path)


def cmd_version(args):
    from lib.backup import get_version
    print(get_version())


def cmd_help(args):
    print("""\
kcptun-manager CLI

Usage:
  kcptun-manager export [--name NAME] [--out DIR] [--quiet]
  kcptun-manager version
  kcptun-manager help
  kcptun-manager               (interactive menu)
""")


def main():
    parser = argparse.ArgumentParser(prog="kcptun-manager", add_help=False)
    sub = parser.add_subparsers(dest="cmd")

    p_exp = sub.add_parser("export", help="Create a portable tar.gz")
    p_exp.add_argument("--name", default="export",
                       help="suffix for the file name (default: export)")
    p_exp.add_argument("--out", default="/root",
                       help="output directory (default: /root)")
    p_exp.add_argument("--quiet", action="store_true",
                       help="do not print install instructions")
    p_exp.set_defaults(func=cmd_export)

    p_ver = sub.add_parser("version")
    p_ver.set_defaults(func=cmd_version)

    p_help = sub.add_parser("help")
    p_help.set_defaults(func=cmd_help)

    if len(sys.argv) == 1:
        # no args → launch interactive
        os.execv(sys.executable,
                 [sys.executable, "-u", f"{BASE}/kcptun_manager.py"])
        return

    args = parser.parse_args()
    if not hasattr(args, "func"):
        parser.print_help()
        sys.exit(1)
    args.func(args)


if __name__ == "__main__":
    main()
