"""Pretty-print helpers (plain ANSI, no external deps)."""

from kcptun_manager.models import KcptunNode, KcptunRoute, KcptunChannel
from kcptun_manager.kcptun.tuner import TunerResult

RESET = "\033[0m"
BOLD = "\033[1m"
CYAN = "\033[36m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
RED = "\033[31m"
MAGENTA = "\033[35m"


def render_main_banner(state, haproxy_online: bool) -> str:
    online_channels = sum(1 for c in state.channels.values() if c.enabled)
    lines = [
        f"{CYAN}╭─ ● HUB — {state.hub.location.upper()} ─────────────────────────────╮{RESET}",
        f"{CYAN}│{RESET}   ✓  {online_channels} channel(s) online",
        f"{CYAN}│{RESET}   ✓  {len(state.routes)} route(s) defined",
        f"{CYAN}│{RESET}   ✓  HAProxy: {'ONLINE' if haproxy_online else 'OFFLINE'}",
        f"{CYAN}╰───────────────────────────────────────────────────────────╯{RESET}",
    ]
    return "\n".join(lines)


def render_nodes_table(nodes: dict[str, KcptunNode]) -> str:
    if not nodes:
        return "(no nodes)"
    rows = ["NAME                 ADDRESS              KCP_PORT  TARGET           MODE"]
    for n in nodes.values():
        rows.append(
            f"{n.name:<20} {n.address:<20} {n.kcp_port:<9} "
            f"{n.target_host}:{n.target_port:<6} {n.mode}"
        )
    return "\n".join(rows)


def render_routes_table(routes: dict[str, KcptunRoute]) -> str:
    if not routes:
        return "(no routes)"
    rows = ["ROUTE_ID   ENTRY   MODE       HAProxy  CHANNELS"]
    for r in routes.values():
        rows.append(
            f"{r.route_id:<10} {r.entry_port:<7} {r.mode:<10} "
            f"{'yes' if r.haproxy_enabled else 'no':<8} {len(r.channels)}"
        )
    return "\n".join(rows)


def render_channels_table(channels: dict[str, KcptunChannel]) -> str:
    if not channels:
        return "(no channels)"
    rows = ["CHANNEL_ID   NODE            LOCAL_TCP   KCP_PORT   ENABLED"]
    for c in channels.values():
        rows.append(
            f"{c.channel_id:<12} {c.node_name:<15} {c.local_tcp_port:<11} "
            f"{c.kcp_port:<10} {'yes' if c.enabled else 'no'}"
        )
    return "\n".join(rows)


def render_tuner_report(result: TunerResult, node_name: str, key: str) -> str:
    lines = [
        f"{BOLD}=== TUNER REPORT — {node_name} ==={RESET}",
        f"Baseline (no tunnel): {result.baseline_speed} Mbit/s",
        f"Best through tunnel:  {result.best_speed} Mbit/s",
        f"Elapsed:              {result.elapsed_sec}s",
        "",
        f"{BOLD}CPU diagnostic:{RESET}",
        f"  conn1 speed: {result.cpu_diag.get('conn1_speed', 'n/a')} Mbit/s",
        f"  conn4 speed: {result.cpu_diag.get('conn4_speed', 'n/a')} Mbit/s",
        f"  improvement: {result.cpu_diag.get('improvement_pct', 'n/a')}%",
        f"  cpu_bound:   {result.cpu_diag.get('cpu_bound', 'n/a')}",
        "",
        f"{BOLD}Best params:{RESET}",
        f"  mode={result.mode} mtu={result.mtu} "
        f"win={result.sndwnd}/{result.rcvwnd} sockbuf={result.sockbuf}",
        f"  nocomp={result.nocomp} smuxver={result.smuxver} "
        f"fec={result.fec_ds}/{result.fec_ps} conn={result.conn}",
        "",
        f"{BOLD}Shared key:{RESET} {key}",
    ]
    return "\n".join(lines)