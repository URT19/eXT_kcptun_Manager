"""Global constants for the KCPTun Manager."""

from pathlib import Path

# ---- Paths ----
BASE_DIR = Path("/opt/kcptun-manager")
DATA_DIR = BASE_DIR / "data"
CONFIG_DIR = DATA_DIR / "configs"
HAPROXY_DIR = DATA_DIR / "haproxy"
EXPORT_DIR = DATA_DIR / "exports"
BACKUP_DIR = DATA_DIR / "backups"
LOG_DIR = DATA_DIR / "logs"
STATE_FILE = DATA_DIR / "state.json"

BIN_DIR = BASE_DIR / "bin"
KCPTUN_SERVER_BIN = BIN_DIR / "kcptun-server"
KCPTUN_CLIENT_BIN = BIN_DIR / "kcptun-client"

SYSTEMD_DIR = Path("/etc/systemd/system")
HAPROXY_CFG = HAPROXY_DIR / "haproxy-agg.cfg"

# ---- Network defaults ----
DEFAULT_KCP_PORT = 29900
DEFAULT_KCP_PORT_RANGE = 100          # scan KCP_PORT..KCP_PORT+100
DEFAULT_TCP_PORT_RANGE = (20000, 45000)
DEFAULT_IPERF_PORT_RANGE = (55000, 59999)

# ---- KCPTun defaults (used as initial values before tuning) ----
DEFAULT_MODE = "fast3"
DEFAULT_MTU = 1350
DEFAULT_SNDWND = 1024
DEFAULT_RCVWND = 1024
DEFAULT_SOCKBUF = 16777216
DEFAULT_NOCOMP = True
DEFAULT_SMUXVER = 2
DEFAULT_FEC_DS = 0
DEFAULT_FEC_PS = 0
DEFAULT_CONN = 1
DEFAULT_CRYPT = "aes-128"

# ---- Sweep tables (mirrors kcptun-rs-optimizer-v4.1.sh) ----
SWEEP_MODES = ["fast", "fast2", "fast3", "normal"]
SWEEP_MTUS = [1500, 1450, 1400, 1350, 1300, 1250, 1200, 1150]
SWEEP_WINDOWS = [
    (512, 512),
    (1024, 1024),
    (2048, 2048),
    (1024, 2048),
    (2048, 1024),
    (4096, 4096),
]
SWEEP_SOCKBUFS = [
    1048576,
    4194304,
    8388608,
    16777216,
    33554432,
    67108864,
    134217728,
]
SWEEP_NOCOMP_SMUX = [
    (True, 1),
    (True, 2),
    (False, 1),
    (False, 2),
]
SWEEP_FEC = [
    (0, 0),
    (10, 3),
    (10, 2),
    (3, 1),
]
SWEEP_CONNS = [1, 2, 4, 8]

# ---- KCPTun binary release ----
KCPTUN_REPO = "https://github.com/xsean2020/kcptun-rs.git"
KCPTUN_BUILD_TIMEOUT = 1200  # seconds

# ---- Systemd unit templates ----
UNIT_SERVER = "kcptun-server@.service"
UNIT_CLIENT = "kcptun-client@.service"
UNIT_HAPROXY = "haproxy-kcptun-agg.service"