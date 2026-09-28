"""systemd services menu."""
import subprocess, time
from lib.ui import banner, hr, prompt, pause, ok, err
from lib.state import State


def _all_units(tmpl):
    r = subprocess.run(
        ["systemctl", "list-units", "--all", "--plain", "--no-legend", f"{tmpl}@*.service"],
        capture_output=True, text=True,
    )
    return [l.split()[0] for l in r.stdout.splitlines() if l.strip()]


def _menu(state, tmpl, label):
    while True:
        banner(state.get_role())
        print(f"  Modiriat service-ha-ye {label}"); hr()
        print("  1) Status hame")
        print("  2) Start hame")
        print("  3) Stop hame")
        print("  4) Restart hame")
        print("  5) Logs yek service")
        print("  6) Restart yek service")
        print("  0) Bazgasht"); hr()
        ch = prompt("Entekhab")
        if ch == "1":
            subprocess.run(["systemctl", "list-units", "--all", f"{tmpl}@*.service", "--no-pager"])
            pause()
        elif ch in ("2", "3", "4"):
            verb = {"2": "start", "3": "stop", "4": "restart"}[ch]
            for u in _all_units(tmpl):
                subprocess.run(["systemctl", verb, u], check=False)
                ok(f"{verb} {u}")
            pause()
        elif ch == "5":
            inst = prompt("Esme instance")
            subprocess.run(["journalctl", "-u", f"{tmpl}@{inst}.service", "-n", "100", "--no-pager"])
            pause()
        elif ch == "6":
            inst = prompt("Esme instance")
            subprocess.run(["systemctl", "restart", f"{tmpl}@{inst}.service"], check=False)
            ok("restart shod"); pause()
        elif ch == "0":
            return
        else:
            err("Na-mojaz."); time.sleep(1)


def iran(state):    _menu(state, "kcptun-client", "kcptun-client")
def foreign(state): _menu(state, "kcptun-server", "kcptun-server")
