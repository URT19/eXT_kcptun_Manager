from dataclasses import dataclass, field
from typing import Optional, List

@dataclass
class KcptunNode:
    """یک سرور خارج که kcptun-server روی آن اجرا می‌شود."""
    name: str
    address: str          # IP سرور خارج
    kcp_port: int         # پورت UDP که kcptun-server گوش می‌دهد
    target_host: str = "127.0.0.1"
    target_port: int = 443
    location: str = ""
    note: str = ""
    ssh_port: int = 22
    ssh_user: str = "root"
    # پارامترهای بهینه‌شده (از tuner)
    mode: str = "fast3"
    mtu: int = 1350
    sndwnd: int = 1024
    rcvwnd: int = 1024
    sockbuf: int = 16777216
    nocomp: bool = True
    smuxver: int = 2
    fec_ds: int = 0
    fec_ps: int = 0
    conn: int = 1
    key: str = ""
    crypt: str = "aes-128"

@dataclass
class KcptunChannel:
    """یک تونل kcptun تکی بین Hub و یک Node."""
    channel_id: str
    node_name: str
    local_tcp_port: int   # پورتی که kcptun-client روی ایران گوش می‌دهد
    kcp_port: int         # پورت UDP روی خارج
    kcptun_params: dict = field(default_factory=dict)

@dataclass
class KcptunRoute:
    """یک پورت عمومی روی Hub که به چند کانال نگاشت می‌شود."""
    route_id: str
    entry_port: int
    mode: str = "balanced"  # simple | balanced
    channels: List[KcptunChannel] = field(default_factory=list)
    balance_algo: str = "roundrobin"
    haproxy_enabled: bool = False