"""Build kcptun-server / kcptun-client command lines and compact exports."""

import base64
import json
from typing import Iterable

from kcptun_manager import constants as C
from kcptun_manager.models import KcptunNode, KcptunChannel


def _node_flags(node: KcptunNode) -> list[str]:
    flags = [
        "--key", node.key,
        "--crypt", node.crypt,
        "--mode", node.mode,
        "--mtu", str(node.mtu),
        "--sndwnd", str(node.sndwnd),
        "--rcvwnd", str(node.rcvwnd),
        "--sockbuf", str(node.sockbuf),
        "--smuxver", str(node.smuxver),
    ]
    if node.nocomp:
        flags.append("--nocomp")
    if node.fec_ds > 0 or node.fec_ps > 0:
        flags += ["--datashard", str(node.fec_ds), "--parityshard", str(node.fec_ps)]
    if node.conn > 1:
        flags += ["--conn", str(node.conn)]
    return flags


def build_server_cmd(node: KcptunNode) -> list[str]:
    """kcptun-server command (runs on Kharej)."""
    return [
        str(C.KCPTUN_SERVER_BIN),
        "-l", f":{node.kcp_port}",
        "-t", f"{node.target_host}:{node.target_port}",
        *_node_flags(node),
    ]


def build_client_cmd(node: KcptunNode, channel: KcptunChannel) -> list[str]:
    """kcptun-client command (runs on Iran, one per channel)."""
    return [
        str(C.KCPTUN_CLIENT_BIN),
        "-r", f"{node.address}:{node.kcp_port}",
        "-l", f":{channel.local_tcp_port}",
        *_node_flags(node),
    ]


def build_server_cmd_str(node: KcptunNode) -> str:
    return " ".join(build_server_cmd(node))


def build_client_cmd_str(node: KcptunNode, channel: KcptunChannel) -> str:
    return " ".join(build_client_cmd(node, channel))


# ---------------------------------------------------------------------------
# Compact export / import (for moving a node's config to the Kharej server)
# ---------------------------------------------------------------------------

def build_compact_export(node: KcptunNode) -> str:
    """Base64-encoded JSON blob with everything the Kharej side needs."""
    payload = {
        "type": "kcptun-node",
        "version": 1,
        "node": node.to_dict(),
    }
    raw = json.dumps(payload, separators=(",", ":"), ensure_ascii=False)
    return base64.urlsafe_b64encode(raw.encode("utf-8")).decode("ascii")


def parse_compact_export(blob: str) -> KcptunNode:
    """Decode a compact export and return the embedded KcptunNode."""
    blob = "".join(blob.split())  # strip whitespace/newlines
    raw = base64.urlsafe_b64decode(blob.encode("ascii"))
    payload = json.loads(raw.decode("utf-8"))
    if payload.get("type") != "kcptun-node":
        raise ValueError("Not a kcptun-node compact export")
    return KcptunNode.from_dict(payload["node"])


def build_ready_to_use_commands(
    node: KcptunNode,
    channels: Iterable[KcptunChannel],
) -> dict[str, list[str]]:
    """Return ready-to-use server + per-channel client command strings."""
    return {
        "server": build_server_cmd_str(node),
        "clients": [
            f"# channel {ch.channel_id} (local tcp :{ch.local_tcp_port})"
            for ch in channels
        ],
    }