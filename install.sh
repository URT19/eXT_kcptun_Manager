#!/usr/bin/env bash
# kcptun-rs Manager — نصب‌کننده از روی آرشیو export
# استفاده:
#   chmod +x install.sh
#   sudo ./install.sh [/path/to/kcptun-manager-export-vX.Y.Z-*.tar.gz]
#
# اگر آرگومان ندهید، آخرین فایل matching در /root جستجو می‌شود.

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

info()  { echo -e "${CYAN}[*]${NC} $*"; }
ok()    { echo -e "${GREEN}[+]${NC} $*"; }
warn()  { echo -e "${YELLOW}[!]${NC} $*"; }
err()   { echo -e "${RED}[-]${NC} $*" >&2; }
die()   { err "$*"; exit 1; }

need_root() {
  if [[ $EUID -ne 0 ]]; then
    die "این اسکریپت باید با root اجرا شود (sudo ./install.sh)."
  fi
}

find_archive() {
  local given="${1:-}"
  if [[ -n "$given" ]]; then
    if [[ -f "$given" ]]; then
      echo "$given"
      return
    fi
    die "فایل پیدا نشد: $given"
  fi

  # جستجوی آخرین export در /root
  local latest
  latest=$(ls -1t /root/kcptun-manager-export-v*.tar.gz 2>/dev/null | head -1 || true)
  if [[ -n "$latest" && -f "$latest" ]]; then
    echo "$latest"
    return
  fi
  die "هیچ آرشیو kcptun-manager-export-v*.tar.gz در /root پیدا نشد. مسیر را به‌صورت آرگومان بدهید."
}

extract_archive() {
  local archive="$1"
  info "استخراج: $archive"
  tar -xzf "$archive" -C /
  ok "استخراج انجام شد."
}

install_deps() {
  info "نصب وابستگی‌ها..."
  export DEBIAN_FRONTEND=noninteractive
  apt-get update -qq
  apt-get install -y -qq python3 curl wget unzip iperf3 haproxy iproute2
  ok "وابستگی‌ها نصب شدند."
}

create_dirs() {
  info "ساخت پوشه‌های اجرایی..."
  mkdir -p /etc/kcptun-manager/instances
  mkdir -p /etc/kcptun-manager/haproxy
  mkdir -p /opt/kcptun-manager/bin
  mkdir -p /var/lock
  mkdir -p /var/backups/kcptun-manager
  ok "پوشه‌ها آماده شدند."
}

reload_systemd() {
  info "بارگذاری مجدد systemd..."
  systemctl daemon-reload
  ok "systemd به‌روز شد."
}

install_wrappers() {
  info "ساخت دستورات سراسری..."

  cat > /usr/local/bin/kcptun << 'EOF'
#!/usr/bin/env bash
exec python3 -u /opt/kcptun-manager/kcptun_manager.py "$@"
EOF
  chmod +x /usr/local/bin/kcptun

  if [[ -f /opt/kcptun-manager/cli.py ]]; then
    cat > /usr/local/bin/kcptun-manager << 'EOF'
#!/usr/bin/env bash
exec python3 -u /opt/kcptun-manager/cli.py "$@"
EOF
    chmod +x /usr/local/bin/kcptun-manager
  fi

  ok "دستورات سراسری: kcptun  و  kcptun-manager"
}

print_next_steps() {
  echo
  echo -e "${GREEN}══════════════════════════════════════════════════${NC}"
  echo -e "${GREEN}  نصب با موفقیت انجام شد.${NC}"
  echo -e "${GREEN}══════════════════════════════════════════════════${NC}"
  echo
  echo "مراحل بعدی:"
  echo "  1) اجرا کنید:"
  echo "       kcptun"
  echo "     یا:"
  echo "       python3 -u /opt/kcptun-manager/kcptun_manager.py"
  echo
  echo "  2) در اولین اجرا نقش را انتخاب کنید:"
  echo "       IRAN   → رله + HAProxy + kcptun-client"
  echo "       KHAREJ → خروجی + kcptun-server"
  echo
  echo "  3) سپس گزینه 1 (نصب / Initialize) را بزنید"
  echo "     تا باینری‌های kcptun دریافت شوند."
  echo
  echo "CLI:"
  echo "  kcptun-manager version"
  echo "  kcptun-manager export [--name NAME] [--out DIR]"
  echo
}

main() {
  need_root

  local archive
  archive=$(find_archive "${1:-}")
  info "آرشیو انتخاب‌شده: $archive"

  extract_archive "$archive"
  install_deps
  create_dirs
  reload_systemd
  install_wrappers
  print_next_steps
}

main "$@"
