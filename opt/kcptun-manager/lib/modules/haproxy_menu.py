"""HAProxy menu."""
import subprocess, time
from lib.ui import banner, hr, prompt, pause, err, ok
from lib.services import rebuild_haproxy


def menu(state):
    while True:
        banner("iran")
        print("  Modiriat HAProxy"); hr()
        print("  1) Rebuild config")
        print("  2) Test config")
        print("  3) Reload HAProxy")
        print("  4) Restart HAProxy")
        print("  5) Status")
        print("  6) Logs")
        print("  7) Namayesh config")
        print("  8) Stats URL")
        print("  0) Bazgasht"); hr()
        ch = prompt("Entekhab")
        if ch == "1": rebuild_haproxy(state); pause()
        elif ch == "2":
            r = subprocess.run(["haproxy", "-c", "-f", "/etc/haproxy/haproxy.cfg"])
            (ok if r.returncode == 0 else err)("check"); pause()
        elif ch == "3":
            subprocess.run(["systemctl", "reload", "haproxy"]); ok("reload shod"); pause()
        elif ch == "4":
            subprocess.run(["systemctl", "restart", "haproxy"]); ok("restart shod"); pause()
        elif ch == "5":
            subprocess.run(["systemctl", "status", "haproxy", "--no-pager"]); pause()
        elif ch == "6":
            subprocess.run(["journalctl", "-u", "haproxy", "-n", "100", "--no-pager"]); pause()
        elif ch == "7":
            print(open("/etc/haproxy/haproxy.cfg").read()); pause()
        elif ch == "8":
            print("  http://127.0.0.1:8404/stats"); pause()
        elif ch == "0": return
        else:
            err("Na-mojaz."); time.sleep(1)
