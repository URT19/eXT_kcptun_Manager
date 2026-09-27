"""Simple input helpers (no external deps)."""

import sys


def ask(label: str, default: str = "", secret: bool = False) -> str:
    suffix = f" [{default}]" if default else ""
    if secret:
        import getpass
        return getpass.getpass(f"{label}{suffix}: ") or default
    return input(f"{label}{suffix}: ").strip() or default


def ask_int(label: str, default: int | None = None,
            lo: int | None = None, hi: int | None = None) -> int:
    while True:
        raw = ask(label, str(default) if default is not None else "")
        try:
            v = int(raw)
        except ValueError:
            print("[!] Not an integer.", file=sys.stderr)
            continue
        if lo is not None and v < lo:
            print(f"[!] Must be >= {lo}", file=sys.stderr)
            continue
        if hi is not None and v > hi:
            print(f"[!] Must be <= {hi}", file=sys.stderr)
            continue
        return v


def ask_bool(label: str, default: bool = True) -> bool:
    d = "Y/n" if default else "y/N"
    raw = ask(f"{label} ({d})", "").lower()
    if not raw:
        return default
    return raw in ("y", "yes", "1", "true", "bale", "b")


def ask_choice(label: str, choices: list[str], default: str | None = None) -> str:
    for i, c in enumerate(choices, 1):
        print(f"  [{i}] {c}")
    while True:
        raw = ask(label, default or "")
        if raw in choices:
            return raw
        try:
            idx = int(raw)
            if 1 <= idx <= len(choices):
                return choices[idx - 1]
        except ValueError:
            pass
        print("[!] Invalid choice.", file=sys.stderr)


def confirm(label: str, default: bool = False) -> bool:
    return ask_bool(label, default)