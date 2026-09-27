"""Deploy kcptun binaries to a Kharej node."""

import sys
from pathlib import Path

from kcptun_manager import constants as C
from kcptun_manager.config import SSHInfo
from kcptun_manager.models import KcptunNode
from kcptun_manager.system.ssh import SSHClient


def deploy_to_node(node: KcptunNode, ssh_password: str) -> None:
    """Upload kcptun-server + kcptun-client to the Kharej node."""
    info = SSHInfo(
        host=node.address,
        port=node.ssh_port,
        user=node.ssh_user,
        password=ssh_password,
    )
    ssh = SSHClient(info)
    if not ssh.check():
        raise RuntimeError(f"SSH to {node.address} failed")

    remote_bin_dir = "/opt/kcptun-manager/bin"
    ssh.run(f"mkdir -p {remote_bin_dir}")

    for name in ("kcptun-server", "kcptun-client"):
        local = C.BIN_DIR / name
        if not local.exists():
            raise FileNotFoundError(f"Local binary missing: {local}")
        print(f"[INFO] Deploying {name}...", file=sys.stderr)
        ssh.copy_atomic(local, f"{remote_bin_dir}/{name}")

    print(f"[OK] Deployed kcptun binaries to {node.address}", file=sys.stderr)