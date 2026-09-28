#!/usr/bin/env bash
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
