"""Quick wizard: create Node + Route in one flow."""

import sys

from kcptun_manager.models import KcptunNode, KcptunRoute, KcptunChannel
from kcptun_manager.state import load_state, save_state
from kcptun_manager.system.net import find_free_udp_port, find_free_tcp_port
from kcptun_manager.kcptun.systemd import install_units, start_channel
from kcptun_manager.haproxy import build_config, write_config, validate_config, \
    restart_haproxy, install_haproxy_unit
from kcptun_manager.ui.prompts import ask, ask_int, ask_bool
from kcptun_manager.i18n import t


def _generate_key() -> str:
    import secrets, string
    alphabet = string.ascii_letters + string.digits
    return "kcptun-rs-" + "".join(secrets.choice(alphabet) for _ in range(16))


def run_wizard() -> None:
    print("\n=== Wizard (quick) ===", file=sys.stderr)
    state = load_state()

    name = ask(t("prompt.node_name"))
    addr = ask(t("prompt.node_addr"))
    entry_port = ask_int(t("prompt.entry_port"), default=443)
    target_port = ask_int(t("prompt.target_port"), default=443)
    mode_choice = ask_int(t("prompt.mode"), default=2)
    route_mode = "simple" if mode_choice == 1 else "balanced"

    node = KcptunNode(
        name=name,
        address=addr,
        kcp_port=find_free_udp_port(),
        target_port=target_port,
        key=_generate_key(),
    )

    route = KcptunRoute.create(entry_port=entry_port, mode=route_mode)

    n_channels = 1 if route_mode == "simple" else 3
    for _ in range(n_channels):
        ch = KcptunChannel.create(
            node_name=node.name,
            local_tcp_port=find_free_tcp_port(),
            kcp_port=node.kcp_port,
        )
        route.channels.append(ch)
        state.channels[ch.channel_id] = ch

    state.nodes[node.name] = node
    state.routes[route.route_id] = route
    save_state(state)

    install_units(state.nodes, state.routes)
    for ch in route.channels:
        start_channel(ch.channel_id)

    if route_mode == "balanced":
        cfg = build_config(state.routes, state.nodes)
        write_config(cfg)
        if validate_config():
            install_haproxy_unit()
            restart_haproxy()

    print(f"[OK] Node '{node.name}' + Route '{route.route_id}' created.",
          file=sys.stderr)
    print(f"[OK] Shared key: {node.key}", file=sys.stderr)