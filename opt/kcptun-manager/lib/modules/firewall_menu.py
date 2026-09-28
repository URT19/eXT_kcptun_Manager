"""Firewall menu."""
import subprocess, time
from lib.ui import banner, hr, prompt, pause, err
from lib.services import fw_allow_tcp, fw_allow_udp


def menu(state):
    while True:
        banner(state.get_role())
        print("  Modiriat Firewall"); hr()
        print("  1) Status ufw")
        print("  2) Enable ufw")
        print("  3) Disable ufw")
        print("  4) List rules")
        print("  5) Add TCP port")
        print("  6) Add UDP port")
        print("  0) Bazgasht"); hr()
        ch = prompt("Entekhab")
        if ch == "1": subprocess.run(["ufw", "status", "verbose"]); pause()
        elif ch == "2": subprocess.run(["ufw", "--force", "enable"]); pause()
        elif ch == "3": subprocess.run(["ufw", "disable"]); pause()
        elif ch == "4": subprocess.run(["ufw", "status", "numbered"]); pause()
        elif ch == "5": fw_allow_tcp(prompt("TCP port"), "manual"); pause()
        elif ch == "6": fw_allow_udp(prompt("UDP port"), "manual"); pause()
        elif ch == "0": return
        else: err("Na-mojaz."); time.sleep(1)
