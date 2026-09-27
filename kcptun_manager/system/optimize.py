"""Kernel / sysctl tuning for high-throughput KCP."""

import subprocess
import sys
from pathlib import Path

SYSCTL_FILE = Path("/etc/sysctl.d/99-kcptun-manager.conf")

SYSCTL_TWEAKS = {
    # UDP buffers
    "net.core.rmem_max": "134217728",
    "net.core.wmem_max": "134217728",
    "net.core.rmem_default": "16777216",
    "net.core.wmem_default": "16777216",
    "net.core.netdev_max_backlog": "16384",
    # File descriptors
    "fs.file-max": "1048576",
    # Backlog
    "net.core.somaxconn": "4096",
    # TCP (for HAProxy side)
    "net.ipv4.tcp_fastopen": "3",
    "net.ipv4.tcp_congestion_control": "bbr",
    "net.core.default_qdisc": "fq",
}


def apply_sysctl_tweaks() -> None:
    lines = [f"{k} = {v}" for k, v in SYSCTL_TWEAKS.items()]
    SYSCTL_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")
    subprocess.run(["sysctl", "-p", str(SYSCTL_FILE)], check=False)
    print(f"[OK] Applied sysctl tweaks -> {SYSCTL_FILE}", file=sys.stderr)