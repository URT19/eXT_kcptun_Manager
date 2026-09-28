"""Install / validate / restart HAProxy aggregation service."""

import subprocess
import sys
from pathlib import Path

from kcptun_manager import constants as C


def write_config(content: str) -> Path:
    C.HAPROXY_DIR.mkdir(parents=True, exist_ok=True)
    C.HAPROXY_CFG.write_text(content, encoding="utf-8")
    print(f"[OK] Wrote {C.HAPROXY_CFG}", file=sys.stderr)
    return C.HAPROXY_CFG


def validate_config() -> bool:
    r = subprocess.run(
        ["haproxy", "-c", "-f", str(C.HAPROXY_CFG)],
        capture_output=True, text=True,
    )
    if r.returncode != 0:
        print(r.stdout, file=sys.stderr)
        print(r.stderr, file=sys.stderr)
    return r.returncode == 0


HAPROXY_UNIT = """\
[Unit]
Description=HAProxy KCPTun aggregation
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
ExecStart=/usr/sbin/haproxy -Ws -f /opt/kcptun-manager/data/haproxy/haproxy-agg.cfg -p /run/haproxy-kcptun.pid
ExecReload=/bin/kill -USR2 $MAINPID
Restart=always
RestartSec=3
LimitNOFILE=1048576

[Install]
WantedBy=multi-user.target
"""


def install_haproxy_unit() -> None:
    C.SYSTEMD_DIR.mkdir(parents=True, exist_ok=True)
    unit_path = C.SYSTEMD_DIR / C.UNIT_HAPROXY
    unit_path.write_text(HAPROXY_UNIT, encoding="utf-8")
    subprocess.run(["systemctl", "daemon-reload"], check=False)
    print(f"[OK] Wrote {unit_path}", file=sys.stderr)


def restart_haproxy() -> None:
    subprocess.run(["systemctl", "enable", "--now", C.UNIT_HAPROXY], check=False)
    subprocess.run(["systemctl", "restart", C.UNIT_HAPROXY], check=False)