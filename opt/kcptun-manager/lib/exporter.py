"""Export the manager as a portable tar.gz, scrubbing private data."""
import os
import tarfile
import tempfile
import subprocess
import time
from lib.ui import info, ok, warn, err
from lib.backup import get_version


BASE_DIR = "/opt/kcptun-manager"
SYSTEMD = "/etc/systemd/system"

# مسیرهایی که هرگز export نمی‌شن
BLOCK_PATHS = [
    "etc/kcptun-manager",       # role + connections.json + instances/*.env
    "etc/haproxy/haproxy.cfg",
    "var/backups/kcptun-manager",
    "opt/kcptun-manager/kcptun.zip",
    "opt/kcptun-manager/bin/kcptun-client",
    "opt/kcptun-manager/bin/kcptun-server",
]

# فایل‌هایی که حتماً export می‌شن
INCLUDE_PATHS = [
    ("opt/kcptun-manager",        "/opt/kcptun-manager"),
    ("etc/systemd/system",        "/etc/systemd/system"),   # فقط unit های ما
]


def _matches_block(path):
    p = path.lstrip("/")
    for b in BLOCK_PATHS:
        if p == b or p.startswith(b + "/"):
            return True
    return False


def _add_systemd_units(tar, arc_prefix):
    for fn in os.listdir(SYSTEMD):
        if fn.startswith("kcptun-") and fn.endswith(".service"):
            full = os.path.join(SYSTEMD, fn)
            if os.path.isfile(full):
                arc = f"{arc_prefix}/{fn}"
                tar.add(full, arcname=arc)


def export(prefix: str = None, out_dir: str = "/root") -> str:
    """Create /root/kcptun-manager-<prefix>-<version>-<ts>.tar.gz. Returns path."""
    if prefix is None:
        prefix = "export"

    version = get_version()
    ts = time.strftime("%Y%m%d-%H%M%S")
    filename = f"kcptun-manager-{prefix}-v{version}-{ts}.tar.gz"
    out_path = os.path.join(out_dir, filename)

    info(f"Creating {out_path} ...")

    # بساز tar
    with tarfile.open(out_path, "w:gz") as tar:
        # /opt/kcptun-manager (bجز فایل‌های بلوک‌شده)
        for root, dirs, files in os.walk(BASE_DIR):
            # پاکسازی dirs
            for d in list(dirs):
                full = os.path.join(root, d)
                rel = "/" + os.path.relpath(full, "/")
                if _matches_block(rel):
                    dirs.remove(d)
            for f in files:
                full = os.path.join(root, f)
                rel = "/" + os.path.relpath(full, "/")
                if _matches_block(rel):
                    continue
                # مسیر داخل tar
                arc = rel.lstrip("/")
                tar.add(full, arcname=arc, recursive=False)
        # systemd units
        _add_systemd_units(tar, "etc/systemd/system")

    size = os.path.getsize(out_path)
    ok(f"Exported: {out_path} ({size} bytes)")
    return out_path


def print_instructions(tar_path: str):
    """Print copy + install instructions."""
    from lib.ui import C
    print()
    print(f"{C.CY}{'═' * 76}{C.NC}")
    print(f"{C.BOLD}  Export ready: {os.path.basename(tar_path)}{C.NC}")
    print(f"{C.CY}{'═' * 76}{C.NC}")
    print()
    print(f"  {C.BOLD}1) Copy to new server{C.NC}")
    print()
    print(f"     scp {tar_path} root@NEW_SERVER:/root/")
    print()
    print(f"  {C.BOLD}2) On the NEW server, run these commands{C.NC}")
    print()
    print(f"     # (a) extract")
    print(f"     cd / && tar -xzf /root/{os.path.basename(tar_path)}")
    print()
    print(f"     # (b) install dependencies")
    print(f"     apt-get update")
    print(f"     apt-get install -y python3 curl wget unzip iperf3 haproxy iproute2")
    print()
    print(f"     # (c) create runtime dirs")
    print(f"     mkdir -p /etc/kcptun-manager/instances")
    print(f"     mkdir -p /etc/kcptun-manager/haproxy")
    print(f"     mkdir -p /opt/kcptun-manager/bin")
    print(f"     mkdir -p /var/lock /var/backups/kcptun-manager")
    print()
    print(f"     # (d) systemd reload")
    print(f"     systemctl daemon-reload")
    print()
    print(f"     # (e) launch the manager")
    print(f"     python3 -u /opt/kcptun-manager/kcptun_manager.py")
    print()
    print(f"     # (f) on first run, choose role IRAN or KHAREJ")
    print(f"     #     then use option 1 (Initialize) to fetch kcptun binaries")
    print()
    print(f"  {C.BOLD}3) Optional: create global command{C.NC}")
    print()
    print(f"     cat > /usr/local/bin/kcptun << 'EOF'")
    print(f"     #!/usr/bin/env bash")
    print(f"     exec python3 -u /opt/kcptun-manager/kcptun_manager.py \"$@\"")
    print(f"     EOF")
    print(f"     chmod +x /usr/local/bin/kcptun")
    print()
    print(f"     # then just run:")
    print(f"     kcptun")
    print()
    print(f"{C.CY}{'═' * 76}{C.NC}")
