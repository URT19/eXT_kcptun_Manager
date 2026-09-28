"""Backup / restore menu."""
import os, subprocess, time
from lib.ui import banner, hr, prompt, confirm, pause, ok, err
from lib.state import State


def menu(state: State):
    while True:
        banner(state.get_role())
        print("  Backup / Restore"); hr()
        print("  1) Backup")
        print("  2) Restore")
        print("  0) Bazgasht"); hr()
        ch = prompt("Entekhab")
        if ch == "1":
            out = f"/root/kcptun-backup-{time.strftime('%Y%m%d-%H%M%S')}.tar.gz"
            subprocess.run(["tar", "-czf", out, "-C", "/etc", "kcptun-manager"])
            ok(f"Backup: {out}"); pause()
        elif ch == "2":
            f = prompt("File")
            if not os.path.isfile(f): err("Peyda nashod."); pause(); continue
            if not confirm("Restore?", "n"): continue
            subprocess.run(["tar", "-xzf", f, "-C", "/etc"])
            ok("Restore shod."); pause()
        elif ch == "0": return
        else: err("Na-mojaz."); time.sleep(1)
