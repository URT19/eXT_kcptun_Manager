"""Main CLI menu."""

import subprocess
import sys

from kcptun_manager import __version__, APP_DISPLAY_NAME
from kcptun_manager import constants as C
from kcptun_manager.i18n import t, set_lang, get_lang
from kcptun_manager.state import load_state, save_state
from kcptun_manager.ui import (
    render_main_banner, render_nodes_table, render_routes_table,
    render_channels_table, run_wizard, run_tuner_ui, run_uninstall,
    ask, ask_int, confirm,
)
from kcptun_manager.kcptun import (
    ensure_binaries, build_compact_export, parse_compact_export,
    install_units, start_channel, stop_channel,
)
from kcptun_manager.kcptun.deployer import deploy_to_node
from kcptun_manager.haproxy import (
    build_config, write_config, validate_config,
    restart_haproxy, install_haproxy_unit,
)
from kcptun_manager.system.optimize import apply_sysctl_tweaks


def _haproxy_online() -> bool:
    r = subprocess.run(["systemctl", "is-active", C.UNIT_HAPROXY],
                       capture_output=True, text=True)
    return r.stdout.strip() == "active"


def _menu() -> None:
    state = load_state()
    print(render_main_banner(state, _haproxy_online()), file=sys.stderr)
    print(f"""
  [ 1] {t('menu.install')}                [10] {t('menu.tuner')}
  [ 2] {t('menu.wizard')}                 [11] {t('menu.speedtest')}
  [ 3] {t('menu.nodes')}                  [12] {t('menu.optimize')}
  [ 4] {t('menu.simple_route')}           [13] {t('menu.backup')}
  [ 5] {t('menu.balanced_route')}         [14] {t('menu.reset')}
  [ 6] {t('menu.routes')}                 [15] {t('menu.lang')}
  [ 7] {t('menu.export')}                 [16] {t('menu.help')}
  [ 8] {t('menu.import')}                 [17] {t('menu.uninstall')}
  [ 9] {t('menu.channels')}               [ 0] {t('menu.exit')}
""", file=sys.stderr)


def _do_install() -> None:
    ensure_binaries()


def _do_nodes() -> None:
    state = load_state()
    print(render_nodes_table(state.nodes), file=sys.stderr)
    print("\n[1] Add  [2] Remove  [0] Back", file=sys.stderr)
    c = ask("Choice")
    if c == "1":
        from kcptun_manager.ui.wizard import _generate_key
        from kcptun_manager.models import KcptunNode
        from kcptun_manager.system.net import find_free_udp_port
        name = ask(t("prompt.node_name"))
        addr = ask(t("prompt.node_addr"))
        target_port = ask_int(t("prompt.target_port"), 443)
        node = KcptunNode(
            name=name, address=addr, target_port=target_port,
            kcp_port=find_free_udp_port(), key=_generate_key(),
        )
        state.nodes[name] = node
        save_state(state)
        print(f"[OK] Node {name} added.", file=sys.stderr)
    elif c == "2":
        name = ask("Node name to remove")
        if name in state.nodes:
            del state.nodes[name]
            save_state(state)
            print(f"[OK] Removed {name}.", file=sys.stderr)


def _do_routes() -> None:
    state = load_state()
    print(render_routes_table(state.routes), file=sys.stderr)


def _do_channels() -> None:
    state = load_state()
    print(render_channels_table(state.channels), file=sys.stderr)
    print("\n[1] Start  [2] Stop  [0] Back", file=sys.stderr)
    c = ask("Choice")
    cid = ask("Channel ID")
    if c == "1":
        start_channel(cid)
    elif c == "2":
        stop_channel(cid)


def _do_export() -> None:
    state = load_state()
    if not state.nodes:
        print("[!] No nodes.", file=sys.stderr)
        return
    name = ask("Node name")
    node = state.nodes.get(name)
    if not node:
        print("[!] Unknown node.", file=sys.stderr)
        return
    blob = build_compact_export(node)
    print("\n--- Compact export (paste on Kharej) ---", file=sys.stderr)
    print(blob)
    print("--- end ---", file=sys.stderr)


def _do_import() -> None:
    print("Paste compact export (blank line to finish):", file=sys.stderr)
    lines = []
    while True:
        line = sys.stdin.readline()
        if not line.strip():
            break
        lines.append(line.strip())
    blob = "".join(lines)
    try:
        node = parse_compact_export(blob)
    except Exception as e:
        print(f"[!] Parse error: {e}", file=sys.stderr)
        return
    state = load_state()
    state.nodes[node.name] = node
    save_state(state)
    print(f"[OK] Node {node.name} imported.", file=sys.stderr)


def _do_optimize() -> None:
    apply_sysctl_tweaks()


def _do_backup() -> None:
    import shutil, time
    C.BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    ts = time.strftime("%Y%m%d-%H%M%S")
    dst = C.BACKUP_DIR / f"state-{ts}.json"
    shutil.copy2(C.STATE_FILE, dst)
    print(f"[OK] Backup: {dst}", file=sys.stderr)


def _do_reset() -> None:
    if not confirm("Delete state.json and all configs?", default=False):
        return
    from kcptun_manager.models import ManagerState
    save_state(ManagerState())
    print("[OK] Reset.", file=sys.stderr)


def _do_lang() -> None:
    print(f"Current: {get_lang()}", file=sys.stderr)
    c = ask("Language (fa/en)")
    set_lang(c)


def _do_help() -> None:
    print("""
KCPTun Manager Help
-------------------
1. Install KCPTun binaries (requires Rust toolchain).
2. Use the Wizard for a quick Node + Route setup.
3. Use Auto-Tuner to find best mode/mtu/window/sockbuf.
4. Export a compact blob from Iran, paste on Kharej with [8].
5. HAProxy aggregates channels of Balanced routes on :entry_port.
""", file=sys.stderr)


HANDLERS = {
    "1": _do_install,
    "2": run_wizard,
    "3": _do_nodes,
    "6": _do_routes,
    "7": _do_export,
    "8": _do_import,
    "9": _do_channels,
    "10": run_tuner_ui,
    "12": _do_optimize,
    "13": _do_backup,
    "14": _do_reset,
    "15": _do_lang,
    "16": _do_help,
    "17": run_uninstall,
}


def main() -> int:
    if len(sys.argv) > 1 and sys.argv[1] in ("-v", "--version"):
        print(f"{APP_DISPLAY_NAME} v{__version__}")
        return 0

    while True:
        _menu()
        try:
            choice = ask(t("prompt.choice"))
        except (EOFError, KeyboardInterrupt):
            print()
            return 0
        if choice == "0":
            return 0
        handler = HANDLERS.get(choice)
        if not handler:
            print("[!] Unknown option.", file=sys.stderr)
            continue
        try:
            handler()
        except KeyboardInterrupt:
            print("\n[!] Interrupted.", file=sys.stderr)
        except Exception as e:
            print(f"[!] Error: {e}", file=sys.stderr)