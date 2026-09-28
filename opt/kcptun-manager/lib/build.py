"""Build / install / systemd templates."""
import os
import subprocess
import tempfile
import shutil
from pathlib import Path

from lib.ui import info, ok, warn, err, die, prompt
from lib.state import State


BASE_DIR = "/opt/kcptun-manager"
BIN_DIR = f"{BASE_DIR}/bin"
HELPER_DIR = f"{BASE_DIR}/helpers"
SYSTEMD_DIR = "/etc/systemd/system"

RUNNER_CLIENT = """#!/usr/bin/env bash
set -euo pipefail

: "${FOREIGN_IP:?}"
: "${FOREIGN_UDP_PORT:?}"
: "${LOCAL_PORT:?}"
: "${KCP_KEY:?}"
: "${KCP_CRYPT:?}"
: "${KCP_MODE:?}"
: "${KCP_MTU:?}"
: "${KCP_SNDWND:?}"
: "${KCP_RCVWND:?}"
: "${KCP_SOCKBUF:?}"
: "${KCP_SMUXVER:?}"

ARGS=(
  -r "${FOREIGN_IP}:${FOREIGN_UDP_PORT}"
  -l "127.0.0.1:${LOCAL_PORT}"
  --key "${KCP_KEY}"
  --crypt "${KCP_CRYPT}"
  --mode "${KCP_MODE}"
  --mtu "${KCP_MTU}"
  --sndwnd "${KCP_SNDWND}"
  --rcvwnd "${KCP_RCVWND}"
  --sockbuf "${KCP_SOCKBUF}"
  --smuxver "${KCP_SMUXVER}"
)
[[ -n "${KCP_NOCOMP_FLAG:-}" ]] && ARGS+=( ${KCP_NOCOMP_FLAG} )
[[ -n "${KCP_FEC_FLAGS:-}"  ]] && ARGS+=( ${KCP_FEC_FLAGS} )
exec /opt/kcptun-manager/bin/kcptun-client "${ARGS[@]}"
"""

RUNNER_SERVER = """#!/usr/bin/env bash
set -euo pipefail

: "${FOREIGN_UDP_PORT:?}"
: "${FOREIGN_TARGET_PORT:?}"
: "${KCP_KEY:?}"
: "${KCP_CRYPT:?}"
: "${KCP_MODE:?}"
: "${KCP_MTU:?}"
: "${KCP_SNDWND:?}"
: "${KCP_RCVWND:?}"
: "${KCP_SOCKBUF:?}"
: "${KCP_SMUXVER:?}"

ARGS=(
  -l ":${FOREIGN_UDP_PORT}"
  -t "127.0.0.1:${FOREIGN_TARGET_PORT}"
  --key "${KCP_KEY}"
  --crypt "${KCP_CRYPT}"
  --mode "${KCP_MODE}"
  --mtu "${KCP_MTU}"
  --sndwnd "${KCP_SNDWND}"
  --rcvwnd "${KCP_RCVWND}"
  --sockbuf "${KCP_SOCKBUF}"
  --smuxver "${KCP_SMUXVER}"
)
[[ -n "${KCP_NOCOMP_FLAG:-}" ]] && ARGS+=( ${KCP_NOCOMP_FLAG} )
[[ -n "${KCP_FEC_FLAGS:-}"  ]] && ARGS+=( ${KCP_FEC_FLAGS} )
exec /opt/kcptun-manager/bin/kcptun-server "${ARGS[@]}"
"""

CLIENT_UNIT = """[Unit]
Description=kcptun-client tunnel %i
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
EnvironmentFile=/etc/kcptun-manager/instances/%i.env
ExecStart=/opt/kcptun-manager/run-client.sh
Restart=always
RestartSec=3
LimitNOFILE=1048576
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
"""

SERVER_UNIT = """[Unit]
Description=kcptun-server tunnel %i
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
EnvironmentFile=/etc/kcptun-manager/instances/%i.env
ExecStart=/opt/kcptun-manager/run-server.sh
Restart=always
RestartSec=3
LimitNOFILE=1048576
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
"""


def install_deps_common():
    info("Nasb pish-niaz-ha...")
    env = os.environ.copy()
    env["DEBIAN_FRONTEND"] = "noninteractive"
    subprocess.run(["apt-get", "update", "-qq"], check=True)
    subprocess.run(
        ["apt-get", "install", "-y", "-qq",
         "python3", "curl", "wget", "unzip", "ufw", "iperf3", "psmisc"],
        env=env, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    ok("Pish-niaz-ha nasb shod.")


def extract_kcptun():
    os.makedirs(BIN_DIR, exist_ok=True)
    cli = os.path.join(BIN_DIR, "kcptun-client")
    srv = os.path.join(BIN_DIR, "kcptun-server")
    if os.path.isfile(cli) and os.access(cli, os.X_OK) and \
       os.path.isfile(srv) and os.access(srv, os.X_OK):
        ok("Binary-ha az ghabl mojoodand.")
        return

    # 1) local candidates
    candidates = [
        f"{BASE_DIR}/kcptun.zip",
        "./kcptun.zip",
    ]
    zipfile = next((c for c in candidates if os.path.isfile(c)), None)

    # 2) remote URL
    REMOTE_URL = "https://github.com/user-attachments/files/32697848/kcptun.zip"

    if not zipfile:
        info("kcptun.zip peyda nashod, downloading ...")
        dest = f"{BASE_DIR}/kcptun.zip"
        try:
            r = subprocess.run(
                ["curl", "-fsSL", "--max-time", "120", "-o", dest, REMOTE_URL],
                capture_output=True, text=True, timeout=130
            )
        except Exception as e:
            die(f"Download failed: {e}")
        if r.returncode != 0 or not os.path.isfile(dest) or os.path.getsize(dest) < 1000:
            die(f"Download failed (rc={r.returncode}). stderr: {r.stderr.strip()}")
        zipfile = dest
        ok(f"Downloaded: {zipfile} ({os.path.getsize(zipfile)} bytes)")

    if not os.path.isfile(zipfile):
        die(f"File zip peyda nashod: {zipfile}")

    # extract
    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run(["unzip", "-q", zipfile, "-d", tmp], check=True)
        c = s = None
        for root, _, files in os.walk(tmp):
            for f in files:
                if f == "kcptun-client" and not c:
                    c = os.path.join(root, f)
                if f == "kcptun-server" and not s:
                    s = os.path.join(root, f)
        if not c: die("kcptun-client dar zip peyda nashod.")
        if not s: die("kcptun-server dar zip peyda nashod.")
        shutil.copy2(c, cli)
        shutil.copy2(s, srv)
        os.chmod(cli, 0o755)
        os.chmod(srv, 0o755)
    ok(f"Binary-ha nasb shodand dar {BIN_DIR}")

def install_helpers():
    os.makedirs(HELPER_DIR, exist_ok=True)
    # Python helpers are no longer needed; state.py handles JSON directly.


def install_kcptun_only():
    install_deps_common()
    extract_kcptun()
    install_helpers()


def install_iran_full():
    install_deps_common()
    info("Nasb HAProxy...")
    env = os.environ.copy()
    env["DEBIAN_FRONTEND"] = "noninteractive"
    subprocess.run(["apt-get", "install", "-y", "-qq", "haproxy"],
                   env=env, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    extract_kcptun()
    install_helpers()
    info("Nasb systemd template baraye kcptun-client...")
    install_client_template()
    ok("Nasb iran kamel shod.")


def install_runner_scripts():
    os.makedirs(BASE_DIR, exist_ok=True)
    with open(f"{BASE_DIR}/run-client.sh", "w") as f:
        f.write(RUNNER_CLIENT)
    with open(f"{BASE_DIR}/run-server.sh", "w") as f:
        f.write(RUNNER_SERVER)
    os.chmod(f"{BASE_DIR}/run-client.sh", 0o755)
    os.chmod(f"{BASE_DIR}/run-server.sh", 0o755)


def install_client_template():
    install_runner_scripts()
    with open(f"{SYSTEMD_DIR}/kcptun-client@.service", "w") as f:
        f.write(CLIENT_UNIT)
    subprocess.run(["systemctl", "daemon-reload"], check=False)


def install_server_template():
    install_runner_scripts()
    with open(f"{SYSTEMD_DIR}/kcptun-server@.service", "w") as f:
        f.write(SERVER_UNIT)
    subprocess.run(["systemctl", "daemon-reload"], check=False)
