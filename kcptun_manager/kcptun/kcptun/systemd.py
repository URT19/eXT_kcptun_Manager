"""Generate and install systemd units for kcptun-server / kcptun-client."""

import subprocess
import sys
from pathlib import Path

from kcptun_manager import constants as C
from kcptun_manager.models import KcptunNode, KcptunChannel

SERVER_UNIT_TEMPLATE = """\
[Unit]
Description=kcptun-server for {node_name} (port {kcp_port})
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
EnvironmentFile=-/opt/kcptun-manager/data/env/{node_name}.env
ExecStart=/opt/kcptun-manager/bin/kcptun-server \\
  -l :{kcp_port} \\
  -t {target_host}:{target_port} \\
  --key ${{KCPTUN_KEY}} \\
  --crypt {crypt} \\
  --mode {mode} \\
  --mtu {mtu} \\
  --sndwnd {sndwnd} --rcvwnd {rcvwnd} \\
  --sockbuf {sockbuf} \\
  {nocomp_flag}--smuxver {smuxver} {fec_flags}{conn_flag}
Restart=always
RestartSec=3
LimitNOFILE=1048576

[Install]
WantedBy=multi-user.target
"""

CLIENT_UNIT_TEMPLATE = """\
[Unit]
Description=kcptun-client channel {channel_id} -> {node_name}
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
EnvironmentFile=-/opt/kcptun-manager/data/env/{node_name}.env
ExecStart=/opt/kcptun-manager/bin/kcptun-client \\
  -r {remote_ip}:{kcp_port} \\
  -l :{local_tcp_port} \\
  --key ${{KCPTUN_KEY}} \\
  --crypt {crypt} \\
  --mode {mode} \\
  --mtu {mtu} \\
  --sndwnd {sndwnd} --rcvwnd {rcvwnd} \\
  --sockbuf {sockbuf} \\
  {nocomp_flag}--smuxver {smuxver} {fec_flags}{conn_flag}
Restart=always
RestartSec=3
LimitNOFILE=1048576

[Install]
WantedBy=multi-user.target
"""


def _flags(node: KcptunNode) -> dict:
    nocomp = "--nocomp " if node.nocomp else ""
    fec = ""
    if node.fec_ds > 0 or node.fec_ps > 0:
        fec = f"--datashard {node.fec_ds} --parityshard {node.fec_ps} "
    conn = f"--conn {node.conn}" if node.conn > 1 else ""
    return {
        "nocomp_flag": nocomp,
        "fec_flags": fec,
        "conn_flag": conn,
    }


def render_server_unit(node: KcptunNode) -> str:
    flags = _flags(node)
    return SERVER_UNIT_TEMPLATE.format(
        node_name=node.name,
        kcp_port=node.kcp_port,
        target_host=node.target_host,
        target_port=node.target_port,
        crypt=node.crypt,
        mode=node.mode,
        mtu=node.mtu,
        sndwnd=node.sndwnd,
        rcvwnd=node.rcvwnd,
        sockbuf=node.sockbuf,
        smuxver=node.smuxver,
        **flags,
    )


def render_client_unit(node: KcptunNode, channel: KcptunChannel) -> str:
    flags = _flags(node)
    return CLIENT_UNIT_TEMPLATE.format(
        channel_id=channel.channel_id,
        node_name=node.name,
        remote_ip=node.address,
        kcp_port=channel.kcp_port,
        local_tcp_port=channel.local_tcp_port,
        crypt=node.crypt,
        mode=node.mode,
        mtu=node.mtu,
        sndwnd=node.sndwnd,
        rcvwnd=node.rcvwnd,
        sockbuf=node.sockbuf,
        smuxver=node.smuxver,
        **flags,
    )


def _env_file(node: KcptunNode) -> Path:
    env_dir = C.DATA_DIR / "env"
    env_dir.mkdir(parents=True, exist_ok=True)
    f = env_dir / f"{node.name}.env"
    f.write_text(f"KCPTUN_KEY={node.key}\n", encoding="utf-8")
    f.chmod(0o600)
    return f


def install_units(nodes: dict[str, KcptunNode],
                  routes: dict[str, "KcptunRoute"]) -> None:
    """Write per-channel client units + per-node server units, reload systemd."""
    C.SYSTEMD_DIR.mkdir(parents=True, exist_ok=True)

    # Server units (one per node) — only used when location == "kharej"
    for node in nodes.values():
        _env_file(node)
        unit_path = C.SYSTEMD_DIR / f"kcptun-server-{node.name}.service"
        unit_path.write_text(render_server_unit(node), encoding="utf-8")
        print(f"[OK] Wrote {unit_path}", file=sys.stderr)

    # Client units (one per channel)
    seen_channels: set[str] = set()
    for route in routes.values():
        for ch in route.channels:
            if ch.channel_id in seen_channels:
                continue
            seen_channels.add(ch.channel_id)
            node = nodes.get(ch.node_name)
            if not node:
                print(f"[WARN] Channel {ch.channel_id} references unknown node {ch.node_name}",
                      file=sys.stderr)
                continue
            unit_path = C.SYSTEMD_DIR / f"kcptun-client-{ch.channel_id}.service"
            unit_path.write_text(render_client_unit(node, ch), encoding="utf-8")
            print(f"[OK] Wrote {unit_path}", file=sys.stderr)

    subprocess.run(["systemctl", "daemon-reload"], check=False)


def start_channel(channel_id: str) -> None:
    subprocess.run(["systemctl", "enable", "--now",
                    f"kcptun-client-{channel_id}.service"], check=False)


def stop_channel(channel_id: str) -> None:
    subprocess.run(["systemctl", "disable", "--now",
                    f"kcptun-client-{channel_id}.service"], check=False)