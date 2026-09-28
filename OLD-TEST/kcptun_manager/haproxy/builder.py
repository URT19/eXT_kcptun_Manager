"""Generate HAProxy config aggregating multiple kcptun-client channels."""

from kcptun_manager.models import KcptunRoute, KcptunNode


def build_config(routes: dict[str, KcptunRoute],
                 nodes: dict[str, KcptunNode]) -> str:
    lines = [
        "global",
        "    daemon",
        "    maxconn 200000",
        "    log /dev/log local0",
        "    stats socket /run/haproxy-kcptun.sock mode 660 level admin",
        "",
        "defaults",
        "    mode tcp",
        "    timeout connect 5s",
        "    timeout client 300s",
        "    timeout server 300s",
        "    option tcplog",
        "",
    ]

    any_balanced = False
    for route in routes.values():
        if not route.haproxy_enabled or route.mode != "balanced":
            continue
        if not route.channels:
            continue
        any_balanced = True

        lines.append(f"# ---- Route {route.route_id} (entry :{route.entry_port}) ----")
        lines.append(f"frontend fe_{route.route_id}")
        lines.append(f"    bind 0.0.0.0:{route.entry_port}")
        lines.append(f"    default_backend be_{route.route_id}")
        lines.append("")

        lines.append(f"backend be_{route.route_id}")
        lines.append(f"    balance {route.balance_algo}")
        for ch in route.channels:
            if not ch.enabled:
                continue
            node = nodes.get(ch.node_name)
            label = f"{ch.channel_id}_{ch.node_name}"
            lines.append(
                f"    server {label} 127.0.0.1:{ch.local_tcp_port} "
                f"check inter 3s fall 2 rise 2"
            )
        lines.append("")

    if not any_balanced:
        lines.append("# No balanced routes configured yet.")
        lines.append("")

    return "\n".join(lines)