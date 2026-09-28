#!/usr/bin/env bash
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
