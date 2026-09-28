"""Uninstall menu."""

import shutil
import subprocess
import sys

from kcptun_manager import constants as C
from kcptun_manager.ui.prompts import confirm


def run_uninstall() -> None:
    print("\n=== Uninstall ===", file=sys.stderr)
    if not confirm("Stop and remove all kcptun systemd units?", default=False):
        return

    subprocess.run("systemctl stop 'kcptun-server-*' 'kcptun-client-*' "
                   f"{C.UNIT_HAPROXY} 2>/dev/null || true", shell=True)
    subprocess.run("systemctl disable 'kcptun-server-*' 'kcptun-client-*' "
                   f"{C.UNIT_HAPROXY} 2>/dev/null || true", shell=True)

    for p in C.SYSTEMD_DIR.glob("kcptun-*.service"):
        try:
            p.unlink()
        except OSError:
            pass
    hp = C.SYSTEMD_DIR / C.UNIT_HAPROXY
    if hp.exists():
        hp.unlink()
    subprocess.run(["systemctl", "daemon-reload"], check=False)

    if confirm("Delete /opt/kcptun-manager entirely?", default=False):
        shutil.rmtree(C.BASE_DIR, ignore_errors=True)
        print("[OK] Removed.", file=sys.stderr)