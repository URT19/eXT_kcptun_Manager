"""Data models: Node, Channel, Route."""

import uuid
from dataclasses import dataclass, field, asdict
from typing import Optional

from kcptun_manager import constants as C


def _new_id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:8]}"


@dataclass
class KcptunNode:
    """A remote (Kharej) server running kcptun-server."""
    name: str
    address: str                                # public IP of Kharej
    kcp_port: int = C.DEFAULT_KCP_PORT
    target_host: str = "127.0.0.1"
    target_port: int = 443
    location: str = ""
    note: str = ""
    ssh_port: int = 22
    ssh_user: str = "root"

    # Tuned parameters
    key: str = ""
    crypt: str = C.DEFAULT_CRYPT
    mode: str = C.DEFAULT_MODE
    mtu: int = C.DEFAULT_MTU
    sndwnd: int = C.DEFAULT_SNDWND
    rcvwnd: int = C.DEFAULT_RCVWND
    sockbuf: int = C.DEFAULT_SOCKBUF
    nocomp: bool = C.DEFAULT_NOCOMP
    smuxver: int = C.DEFAULT_SMUXVER
    fec_ds: int = C.DEFAULT_FEC_DS
    fec_ps: int = C.DEFAULT_FEC_PS
    conn: int = C.DEFAULT_CONN

    # Tuner metadata
    baseline_speed: float = 0.0
    best_speed: float = 0.0
    tuned_at: str = ""

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "KcptunNode":
        allowed = {f for f in cls.__dataclass_fields__}
        return cls(**{k: v for k, v in d.items() if k in allowed})


@dataclass
class KcptunChannel:
    """A single KCP tunnel between Hub (Iran) and one Node (Kharej)."""
    channel_id: str
    node_name: str
    local_tcp_port: int                # kcptun-client listens here on Iran
    kcp_port: int                      # kcptun-server listens here on Kharej
    protocol_label: str = "kcp"        # for UI / future multi-transport
    enabled: bool = True

    @classmethod
    def create(cls, node_name: str, local_tcp_port: int, kcp_port: int) -> "KcptunChannel":
        return cls(
            channel_id=_new_id("ch"),
            node_name=node_name,
            local_tcp_port=local_tcp_port,
            kcp_port=kcp_port,
        )

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "KcptunChannel":
        allowed = {f for f in cls.__dataclass_fields__}
        return cls(**{k: v for k, v in d.items() if k in allowed})


@dataclass
class KcptunRoute:
    """A public port on Hub mapped to one or more channels."""
    route_id: str
    entry_port: int
    mode: str = "balanced"              # simple | balanced
    channels: list[KcptunChannel] = field(default_factory=list)
    balance_algo: str = "roundrobin"    # roundrobin | leastconn | source
    haproxy_enabled: bool = False
    note: str = ""

    @classmethod
    def create(cls, entry_port: int, mode: str = "balanced") -> "KcptunRoute":
        return cls(
            route_id=_new_id("rt"),
            entry_port=entry_port,
            mode=mode,
            haproxy_enabled=(mode == "balanced"),
        )

    def to_dict(self) -> dict:
        d = asdict(self)
        d["channels"] = [c.to_dict() for c in self.channels]
        return d

    @classmethod
    def from_dict(cls, d: dict) -> "KcptunRoute":
        d = dict(d)
        d["channels"] = [KcptunChannel.from_dict(c) for c in d.get("channels", [])]
        allowed = {f for f in cls.__dataclass_fields__}
        return cls(**{k: v for k, v in d.items() if k in allowed})


@dataclass
class HubConfig:
    """Configuration of the Hub (Iran) side."""
    location: str = "iran"              # iran | kharej
    public_ip: str = ""
    haproxy_enabled: bool = True


@dataclass
class ManagerState:
    """Top-level persistent state."""
    version: str = "4.0.0"
    hub: HubConfig = field(default_factory=HubConfig)
    nodes: dict[str, KcptunNode] = field(default_factory=dict)
    routes: dict[str, KcptunRoute] = field(default_factory=dict)
    channels: dict[str, KcptunChannel] = field(default_factory=dict)
    last_updated: str = ""

    def to_dict(self) -> dict:
        return {
            "version": self.version,
            "hub": asdict(self.hub),
            "nodes": {k: v.to_dict() for k, v in self.nodes.items()},
            "routes": {k: v.to_dict() for k, v in self.routes.items()},
            "channels": {k: v.to_dict() for k, v in self.channels.items()},
            "last_updated": self.last_updated,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "ManagerState":
        return cls(
            version=d.get("version", "4.0.0"),
            hub=HubConfig(**d.get("hub", {})),
            nodes={k: KcptunNode.from_dict(v) for k, v in d.get("nodes", {}).items()},
            routes={k: KcptunRoute.from_dict(v) for k, v in d.get("routes", {}).items()},
            channels={k: KcptunChannel.from_dict(v) for k, v in d.get("channels", {}).items()},
            last_updated=d.get("last_updated", ""),
        )