#!/usr/bin/env bash
# KCPTun Manager installer
set -euo pipefail

BASE_DIR="/opt/kcptun-manager"
VENV="$BASE_DIR/venv"
SRC_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

need_root(){ [[ $EUID -eq 0 ]] || { echo "Run as root."; exit 1; }; }
need_root

echo "==> Installing system dependencies"
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get install -y -qq \
  python3 python3-venv python3-pip \
  curl wget git build-essential pkg-config libssl-dev \
  iperf3 sshpass jq lsof net-tools bc sysstat \
  haproxy unzip

echo "==> Creating $BASE_DIR"
mkdir -p "$BASE_DIR"/{bin,data/{configs,haproxy,exports,backups,logs,env}}

echo "==> Setting up Python venv"
python3 -m venv "$VENV"
"$VENV/bin/pip" install --quiet --upgrade pip
"$VENV/bin/pip" install --quiet "$SRC_DIR"

echo "==> Installing package source"
cp -r "$SRC_DIR/kcptun_manager" "$BASE_DIR/"
cp "$SRC_DIR/pyproject.toml" "$BASE_DIR/"

echo "==> Creating entrypoints"
cat > /usr/local/bin/frp-cli <<EOF
#!/usr/bin/env bash
exec "$VENV/bin/python" -m kcptun_manager "\$@"
EOF
chmod 0755 /usr/local/bin/frp-cli

cat > /usr/local/bin/kcptun-manager <<EOF
#!/usr/bin/env bash
exec "$VENV/bin/python" -m kcptun_manager "\$@"
EOF
chmod 0755 /usr/local/bin/kcptun-manager

cat > /usr/local/bin/kcptun-tuner <<EOF
#!/usr/bin/env bash
exec "$VENV/bin/python" -c 'from kcptun_manager.ui.tuner_ui import run_tuner_ui; run_tuner_ui()'
EOF
chmod 0755 /usr/local/bin/kcptun-tuner

cat > /usr/local/bin/kcptun-uninstall <<EOF
#!/usr/bin/env bash
exec "$VENV/bin/python" -c 'from kcptun_manager.ui.uninstall import run_uninstall; run_uninstall()'
EOF
chmod 0755 /usr/local/bin/kcptun-uninstall

echo "==> Done. Run: sudo frp-cli"