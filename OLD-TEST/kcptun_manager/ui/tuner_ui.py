"""Interactive Auto-Tuner UI."""

import json
import sys
from datetime import datetime
from pathlib import Path

from kcptun_manager import constants as C
from kcptun_manager.config import SSHInfo, TunerConfig
from kcptun_manager.state import load_state, save_state
from kcptun_manager.kcptun.tuner import KcptunTuner
from kcptun_manager.ui.prompts import ask, ask_bool, confirm
from kcptun_manager.ui.tables import render_tuner_report


def _write_report(result, node_name: str, key: str) -> Path:
    C.LOG_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
    out = C.LOG_DIR / f"tuner-{node_name}-{ts}.json"
    out.write_text(
        json.dumps({
            "node": node_name,
            "key": key,
            "baseline_speed": result.baseline_speed,
            "best_speed": result.best_speed,
            "params": {
                "mode": result.mode, "mtu": result.mtu,
                "sndwnd": result.sndwnd, "rcvwnd": result.rcvwnd,
                "sockbuf": result.sockbuf, "nocomp": result.nocomp,
                "smuxver": result.smuxver, "fec_ds": result.fec_ds,
                "fec_ps": result.fec_ps, "conn": result.conn,
            },
            "cpu_diag": result.cpu_diag,
            "elapsed_sec": result.elapsed_sec,
        }, indent=2),
        encoding="utf-8",
    )
    return out


def run_tuner_ui() -> None:
    state = load_state()
    if not state.nodes:
        print("[!] No nodes defined. Add a node first.", file=sys.stderr)
        return

    print("\n=== Auto-Tuner ===", file=sys.stderr)
    print("Nodes:", ", ".join(state.nodes.keys()), file=sys.stderr)
    node_name = ask("Node name")
    node = state.nodes.get(node_name)
    if not node:
        print(f"[!] Unknown node: {node_name}", file=sys.stderr)
        return

    kharej_ip = ask("Kharej SSH IP", node.address)
    kharej_user = ask("Kharej SSH user", node.ssh_user)
    kharej_port = int(ask("Kharej SSH port", str(node.ssh_port)))
    kharej_pass = ask("Kharej SSH password", secret=True)

    iran_ip = ask("Iran SSH IP")
    iran_user = ask("Iran SSH user", "root")
    iran_port = int(ask("Iran SSH port", "22"))
    iran_pass = ask("Iran SSH password", secret=True)

    fec = ask_bool("Enable FEC sweep?", default=False)
    conn = ask_bool("Enable --conn sweep?", default=False)

    cfg = TunerConfig.from_env()
    cfg.fec_sweep = fec
    cfg.conn_sweep = conn

    kharej = SSHInfo(host=kharej_ip, port=kharej_port, user=kharej_user, password=kharej_pass)
    iran = SSHInfo(host=iran_ip, port=iran_port, user=iran_user, password=iran_pass)

    key = node.key or ask("Shared key (leave blank to auto-generate)")
    if not key:
        import secrets, string
        alphabet = string.ascii_letters + string.digits
        key = "kcptun-rs-" + "".join(secrets.choice(alphabet) for _ in range(16))
    node.key = key

    tuner = KcptunTuner(kharej=kharej, iran=iran, cfg=cfg, key=key)

    try:
        result = tuner.run_full()
    except Exception as e:
        print(f"[!] Tuner failed: {e}", file=sys.stderr)
        return

    print(render_tuner_report(result, node.name, key), file=sys.stderr)

    # Persist best params
    node.mode = result.mode
    node.mtu = result.mtu
    node.sndwnd = result.sndwnd
    node.rcvwnd = result.rcvwnd
    node.sockbuf = result.sockbuf
    node.nocomp = result.nocomp
    node.smuxver = result.smuxver
    node.fec_ds = result.fec_ds
    node.fec_ps = result.fec_ps
    node.conn = result.conn
    node.baseline_speed = result.baseline_speed
    node.best_speed = result.best_speed
    node.tuned_at = datetime.utcnow().isoformat(timespec="seconds") + "Z"

    if confirm("Save these parameters to node?", default=True):
        save_state(state)
        report_path = _write_report(result, node.name, key)
        print(f"[OK] Saved. Report: {report_path}", file=sys.stderr)