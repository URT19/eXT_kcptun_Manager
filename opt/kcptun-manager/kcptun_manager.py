#!/usr/bin/env python3
"""kcptun-rs Manager - Python modular edition. Entry point."""
import sys, os, fcntl, time
BASE = "/opt/kcptun-manager"
sys.path.insert(0, BASE)

from lib.ui import banner, info, ok, warn, err, step, hr, pause, prompt, confirm, die, C
from lib.state import State
from lib.build import install_helpers
from lib.modules import menu_iran as menu_iran_mod
from lib.modules import menu_foreign as menu_foreign_mod


LOCK_PATH = "/var/lock/kcptun-manager.lock"


def need_root():
    if os.geteuid() != 0:
        die("In script bayad ba root ejra beshe.")


def acquire_lock_smart():
    """Try to acquire lock. If stale, clean it and retry."""
    for attempt in range(1, 4):
        try:
            fh = open(LOCK_PATH, "a+")
            fcntl.flock(fh, fcntl.LOCK_EX | fcntl.LOCK_NB)
            fh.seek(0)
            fh.truncate()
            fh.write(str(os.getpid()))
            fh.flush()
            return fh
        except BlockingIOError:
            # lock is held by someone
            if attempt == 1:
                warn(f"Lock file dar hale estefade ast: {LOCK_PATH}")
                # read holder PID
                try:
                    with open(LOCK_PATH) as f:
                        holder = f.read().strip()
                except Exception:
                    holder = "?"
                info(f"PID-e saheb: {holder}")
                # check if holder still alive
                if holder.isdigit():
                    alive = os.path.exists(f"/proc/{holder}")
                    if not alive:
                        warn(f"PID {holder} morde — lock ghadimi ast. Pak mikonam...")
                        try: os.remove(LOCK_PATH)
                        except Exception: pass
                        time.sleep(0.3)
                        continue
                    else:
                        die(f"Script dar PID {holder} dar hale ejrast. "
                            f"Agar motmaen nisti: kill -9 {holder} && rm -f {LOCK_PATH}")
                else:
                    warn("PID-e saheb na-mojaz — lock pak mikonam.")
                    try: os.remove(LOCK_PATH)
                    except Exception: pass
                    time.sleep(0.3)
                    continue
            else:
                die("Natunestim lock begirim. "
                    f"Ye bar dige emtehan kon ya dasti: rm -f {LOCK_PATH}")
    die("Lock acquire fail shod.")


def first_run(state: State):
    banner("setup")
    print("  In server chiye?")
    print("  1) IRAN   (relay + HAProxy + kcptun-client)")
    print("  2) KHAREJ (exit + kcptun-server)")
    print("  0) Exit")
    hr()
    ch = prompt("Entekhab")
    if ch == "1":
        state.set_role("iran"); ok("Role = iran")
    elif ch == "2":
        state.set_role("foreign"); ok("Role = foreign")
    elif ch == "0":
        sys.exit(0)
    else:
        err("Na-mojaz."); time.sleep(1); first_run(state)


def main():
    need_root()
    lock_fh = acquire_lock_smart()
    try:
        state = State()
        install_helpers()

        role = state.get_role()
        if not role:
            first_run(state)
            role = state.get_role()

        if role == "iran":
            menu_iran_mod.menu_iran(state)
        elif role == "foreign":
            menu_foreign_mod.menu_foreign(state)
        else:
            die(f"Role invalid: {role}")
    finally:
        try:
            fcntl.flock(lock_fh, fcntl.LOCK_UN)
            lock_fh.close()
        except Exception:
            pass


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[!] Interrupted.")
        sys.exit(130)
