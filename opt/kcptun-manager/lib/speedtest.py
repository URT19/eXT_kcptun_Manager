"""Speedtest: iperf3 server on foreign, client on iran. Unified menus."""
import os, re, json, time, subprocess, sys, socket

from lib.ui import info, ok, warn, err, hr, prompt, confirm, pause, C, select_from_list, banner
from lib.state import State

PID_DIR = "/run/kcptun-iperf"
DEF_DURATION = 10


def _p(*a):
    print(*a, flush=True)


# ============================================================
#  common helpers
# ============================================================
def _kill_servers():
    for pat in ("iperf3 -s -B 127.0.0.1", "iperf3 -s -p", "iperf3 -s"):
        subprocess.run(["pkill", "-9", "-f", pat],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if os.path.isdir(PID_DIR):
        for f in os.listdir(PID_DIR):
            if f.endswith(".pid"):
                try: os.remove(os.path.join(PID_DIR, f))
                except Exception: pass
    time.sleep(0.4)


def _kill_clients():
    subprocess.run(["pkill", "-9", "-f", "iperf3 -c"],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(0.2)


def _preflight(port, timeout=2):
    """Check if port is LISTENING (does not open a socket! iperf3 server 
    would count any TCP connect as an attempted session and block)."""
    try:
        r = subprocess.run(
            ["ss", "-Hltn"],
            capture_output=True, text=True, timeout=5
        )
        for line in r.stdout.splitlines():
            parts = line.split()
            if len(parts) >= 4 and parts[3].endswith(f":{port}"):
                return True
        return False
    except Exception:
        return False


# ============================================================
#  FOREIGN (KHAREJ) menu 12
# ============================================================
def _menu_foreign(state):
    _kill_servers()
    while True:
        banner("foreign")
        _p(f"  {C.BOLD}Speedtest Server (KHAREJ)  |  menu 12{C.NC}")
        hr()
        _p("  1) Start server            (vared shodan be halat server)")
        _p("  2) Stop server")
        _p("  3) Server status")
        _p("  0) Bazgasht")
        hr()
        ch = prompt("Entekhab")
        if ch == "1": _foreign_start(state)
        elif ch == "2": _foreign_stop()
        elif ch == "3": _foreign_status()
        elif ch == "0": return
        else:
            err("Na-mojaz."); time.sleep(1)


def _foreign_start(state):
    _kill_servers()
    hr()
    _p(f"  {C.BOLD}Start iperf3 server rooye KHAREJ{C.NC}")
    hr()

    items = []
    for name, c in sorted(state.list_connections().items()):
        nt = len(c.get("tunnels", []))
        fip = c.get("foreign_ip", "-")
        tp = c.get("foreign_target_port", "-")
        disp = f"{name:<22}  tunnels={nt}  target={fip}:{tp}"
        items.append((disp, name))
    if not items:
        err("Hich connection-i vojood nadarad.")
        err("Avval az IRAN yek connection besazid va import konid.")
        pause(); return

    _p("  Kodoom connection ra be onvane server estefade konim?")
    _p()
    name = select_from_list(items, "Shomare connection")
    if not name:
        return
    c = state.get_connection(name)
    target = c.get("foreign_target_port", 443)

    _p()
    _p(f"  Connection  : {name}")
    _p(f"  Target port : {target}")
    _p(f"  Tunnels     : {len(c.get('tunnels', []))}")
    _p()

    _p("  Mode-e server:")
    _p(f"   1) Port hamoon target ({target})")
    _p("   2) Port custom")
    _p("   0) Cancel")
    mode = prompt("Entekhab", "1")
    if mode == "0": return

    if mode == "1":
        port = int(target)
    elif mode == "2":
        port = prompt("Port")
        if not re.fullmatch(r"\d+", port) or not (1 <= int(port) <= 65535):
            err("Port na-mojaz."); pause(); return
        port = int(port)
    else:
        err("Na-mojaz."); pause(); return

    os.makedirs(PID_DIR, exist_ok=True)
    subprocess.run(["fuser", "-k", "-n", "tcp", str(port)],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(0.3)

    info(f"Start: iperf3 -s -B 127.0.0.1 -p {port}")
    log = open(f"/tmp/iperf-server-{port}.log", "w")
    p = subprocess.Popen(
        ["iperf3", "-s", "-B", "127.0.0.1", "-p", str(port), "--idle-timeout", "86400"],
        stdout=log, stderr=subprocess.STDOUT,
    )
    with open(f"{PID_DIR}/iperf-{port}.pid", "w") as f:
        f.write(str(p.pid))
    time.sleep(0.6)

    if p.poll() is None:
        ok(f"Speedtest server rooye :{port} faal ast (PID {p.pid})")
        _p(f"  {C.DIM}Log: /tmp/iperf-server-{port}.log{C.NC}")
        _p()
        _p(f"  {C.Y}ALAN beravid rooye IRAN va menuye 12 (Speedtest) ra baz konid.{C.NC}")
    else:
        err("Server start nashod. Log:")
        with open(f"/tmp/iperf-server-{port}.log") as f:
            _p(f.read())
    pause()


def _foreign_stop():
    hr()
    _p(f"  {C.BOLD}Stop iperf3 server-ha{C.NC}")
    hr()
    r = subprocess.run(["pgrep", "-af", "iperf3 -s"], capture_output=True, text=True)
    if r.stdout.strip():
        _p("  Process-ha-ye faal:")
        for line in r.stdout.strip().splitlines():
            _p(f"    {line}")
        _p()
        _kill_servers()
        ok("Hame server-ha khamoosh shodand.")
    else:
        info("Hich server-i faal nabood.")
    pause()


def _foreign_status():
    hr()
    _p(f"  {C.BOLD}Server status{C.NC}")
    hr()
    r = subprocess.run(["pgrep", "-af", "iperf3 -s"], capture_output=True, text=True)
    if r.stdout.strip():
        _p("  Process-ha:")
        for line in r.stdout.strip().splitlines():
            _p(f"    {line}")
        _p()
        _p("  Port-ha:")
        s = subprocess.run(["ss", "-tlnp"], capture_output=True, text=True)
        for line in s.stdout.splitlines():
            if "iperf3" in line:
                _p(f"    {line}")
    else:
        info("Hich server-i faal nist.")
    pause()


# ============================================================
#  IRAN menu 12
# ============================================================
def _menu_iran(state):
    _kill_clients()
    while True:
        banner("iran")
        _p(f"  {C.BOLD}Speedtest Client (IRAN)  |  menu 12{C.NC}")
        hr()
        _p("  1) Run test")
        _p("  2) Show status")
        _p("  0) Bazgasht")
        hr()
        ch = prompt("Entekhab")
        if ch == "1": _iran_run(state)
        elif ch == "2": _iran_status(state)
        elif ch == "0": return
        else:
            err("Na-mojaz."); time.sleep(1)


def _iran_run(state):
    hr()
    _p(f"  {C.BOLD}Speedtest (IRAN -> KHAREJ){C.NC}")
    hr()
    _p(f"  {C.Y}AGAHI: Ghabl az test, ROOYE KHAREJ bayad iperf3 server bala bashe.{C.NC}")
    _p(f"  {C.Y}Rooye KHAREJ: menu 12 -> 1 (Start server){C.NC}")
    _p()

    if not confirm("Server rooye KHAREJ bala ast?", "y"):
        info("Avval rooye KHAREJ server ra bala biyarid.")
        pause(); return

    items = []
    for name, c in sorted(state.list_connections().items()):
        nt = len(c.get("tunnels", []))
        fe = c.get("iran_listen_port", "-")
        fip = c.get("foreign_ip", "-")
        tp = c.get("foreign_target_port", "-")
        disp = f"{name:<22}  channels={nt}  frontend={fe}  foreign={fip}:{tp}"
        items.append((disp, name))
    if not items:
        err("Hich connection-i vojood nadarad.")
        pause(); return

    _p("  Kodoom connection ra mikhahid test konid?")
    _p()
    name = select_from_list(items, "Shomare connection")
    if not name:
        return

    c = state.get_connection(name)
    fe = c.get("iran_listen_port")
    tunnels = c.get("tunnels", [])

    _p()
    _p(f"  {C.BOLD}Status-e connection '{name}':{C.NC}")
    _p(f"    Frontend (HAProxy)   : 127.0.0.1:{fe}")
    _p(f"    Tedad-e channel-ha   : {len(tunnels)}")
    _p()
    _p(f"  {C.BOLD}Channel-ha:{C.NC}")
    _p(f"    {'#':<4} {'MAIN PORT':<12} {'TEST PORT':<12} {'UDP MAIN':<10} {'UDP TEST':<10}")
    for t in tunnels:
        _p(f"    {t['id']:<4} {t.get('local_port','-'):<12} "
           f"{t.get('test_local_port','-'):<12} "
           f"{t.get('iran_udp_port','-'):<10} "
           f"{t.get('test_iran_udp_port','-'):<10}")

    _p()
    _p(f"  {C.BOLD}Noe-e test:{C.NC}")
    _p(f"    1) Test-e HAProxy   (hame channel-ha az tarigh 127.0.0.1:{fe})")
    _p(f"    2) Test-e channel-e tak (yek channel-e entekhabi)")
    _p(f"    0) Cancel")
    mode = prompt("Entekhab", "1")
    if mode == "0":
        return

    if mode == "1":
        _test_haproxy(state, name, fe)
    elif mode == "2":
        _test_single(state, name, tunnels)
    else:
        err("Na-mojaz."); pause()


def _test_haproxy(state, name, fe):
    _p()
    _p(f"  {C.Y}Nokte: -P 1 baraye HAProxy pisnahad mishe.{C.NC}")
    _p()
    dur = prompt("Moddat (saniye)", str(DEF_DURATION))
    try: dur = int(dur)
    except ValueError: dur = DEF_DURATION
    strm = prompt("Tedad stream (-P)", "1")
    try: strm = int(strm)
    except ValueError: strm = 1

    _p()
    info(f"Test: HAProxy 127.0.0.1:{fe}  ({strm} streams, {dur}s)")
    _p()
    _run_iperf_client(fe, dur, strm,
                      label=f"HAProxy (port {fe})  |  {name}")
    pause()


def _test_single(state, name, tunnels):
    _p()
    _p(f"  Noe-e channel:")
    _p(f"    1) Main channel  (target = main port rooye kharej)")
    _p(f"    2) Test channel  (target = test port rooye kharej)")
    _p(f"    0) Cancel")
    kind = prompt("Entekhab", "1")
    if kind == "0": return
    if kind not in ("1", "2"):
        err("Na-mojaz."); pause(); return

    items = []
    for t in tunnels:
        if kind == "1":
            port = t.get("local_port"); typ = "main"
        else:
            port = t.get("test_local_port"); typ = "test"
        if not port: continue
        disp = f"{typ:<5} channel #{t['id']}  ->  127.0.0.1:{port}"
        items.append((disp, (t["id"], port, typ)))
    if not items:
        err("Channel-i peyda nashod.")
        pause(); return

    chosen = select_from_list(items, "Kodoom channel")
    if not chosen:
        return
    tid, port, typ = chosen

    _p()
    dur = prompt("Moddat (saniye)", str(DEF_DURATION))
    try: dur = int(dur)
    except ValueError: dur = DEF_DURATION
    strm = prompt("Tedad stream (-P)", "4")
    try: strm = int(strm)
    except ValueError: strm = 4

    _p()
    info(f"Test: {typ} channel #{tid}  127.0.0.1:{port}  ({strm} streams, {dur}s)")
    _p()
    _run_iperf_client(port, dur, strm,
                      label=f"{typ.capitalize()} channel #{tid} (port {port})  |  {name}")
    pause()


def _iran_status(state):
    hr()
    _p(f"  {C.BOLD}Status-e connection-ha va channel-ha{C.NC}")
    hr()

    r = subprocess.run(["systemctl", "is-active", "haproxy"],
                       capture_output=True, text=True)
    ha = r.stdout.strip()
    _p(f"  HAProxy: {C.G if ha == 'active' else C.R}{ha}{C.NC}")
    _p()

    for name, c in sorted(state.list_connections().items()):
        fe = c.get("iran_listen_port", "-")
        fip = c.get("foreign_ip", "-")
        tp = c.get("foreign_target_port", "-")
        tunnels = c.get("tunnels", [])
        _p(f"  {C.BOLD}Connection: {name}{C.NC}")
        _p(f"    Frontend: 127.0.0.1:{fe}   Foreign: {fip}:{tp}")
        _p(f"    Channels: {len(tunnels)}")
        for t in tunnels:
            tid = t["id"]
            main_port = t.get("local_port")
            main_svc = f"kcptun-client@{name}-{tid}"
            main_state = subprocess.run(
                ["systemctl", "is-active", main_svc],
                capture_output=True, text=True
            ).stdout.strip()
            main_color = C.G if main_state == "active" else C.R

            test_port = t.get("test_local_port")
            test_svc = f"kcptun-client@{name}-{tid}-test"
            test_state = subprocess.run(
                ["systemctl", "is-active", test_svc],
                capture_output=True, text=True
            ).stdout.strip()
            test_color = C.G if test_state == "active" else C.R

            _p(f"      channel #{tid}:")
            _p(f"        main  port {main_port:<6}  {main_color}{main_state}{C.NC}")
            _p(f"        test  port {test_port:<6}  {test_color}{test_state}{C.NC}")
        _p()

    pause()


# ============================================================
#  iperf3 client runner — TEXT MODE (no -J, no --connect-timeout)
#  This mirrors the exact command that works when run by hand.
# ============================================================
def _run_iperf_client(port, dur, strm, label):
    _kill_clients()
    out = f"/tmp/speedtest-{port}-{int(time.time())}.txt"

    # NOTE: preflight hatof shod. iperf3 server har TCP connect ro ye 
    # "attempted session" mishomare va montazere cookie mimune. Pas 
    # preflight ba TCP connect khatarnake. iperf3 khodesh error mide.
    _p(f"  {C.DIM}[1/2] Ejra (text mode, mesl dasti) ...{C.NC}")
    info(f"iperf3 -c 127.0.0.1 -p {port} -t {dur} -P {strm}")
    cmd = ["iperf3", "-c", "127.0.0.1", "-p", str(port),
           "-t", str(dur), "-P", str(strm)]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=dur + 30)
    except subprocess.TimeoutExpired:
        err(f"Timeout ba'd az {dur + 30}s")
        return False

    with open(out, "w") as f:
        f.write(r.stdout or "")
        f.write("\n--- STDERR ---\n")
        f.write(r.stderr or "")

    if r.returncode != 0:
        err(f"iperf3 exit {r.returncode}")
        if r.stderr.strip():
            _p(f"  {C.Y}STDERR:{C.NC}")
            for line in r.stderr.splitlines()[:10]:
                _p(f"    {line}")
        if r.stdout.strip():
            _p(f"  {C.Y}STDOUT (15 line):{C.NC}")
            for line in r.stdout.splitlines()[:15]:
                _p(f"    {line}")
        _p(f"  {C.DIM}Full output: {out}{C.NC}")
        return False

    _p(f"  {C.DIM}[2/2] Parse natije ...{C.NC}")
    txt = r.stdout

    speed_mbps = None
    bytes_total = None

    # [SUM] line first (multi-stream)
    for line in txt.splitlines():
        if "[SUM]" in line and "receiver" in line:
            parts = line.split()
            try:
                idx = parts.index("Mbits/sec")
                speed_mbps = float(parts[idx - 1])
                if idx >= 4 and parts[idx - 3] == "MBytes":
                    bytes_total = float(parts[idx - 4])
            except (ValueError, IndexError):
                pass
            if speed_mbps is not None:
                break

    # fallback: single stream receiver line
    if speed_mbps is None:
        for line in txt.splitlines():
            if "receiver" in line and "Mbits/sec" in line:
                parts = line.split()
                try:
                    idx = parts.index("Mbits/sec")
                    speed_mbps = float(parts[idx - 1])
                    if idx >= 4 and parts[idx - 3] == "MBytes":
                        bytes_total = float(parts[idx - 4])
                except (ValueError, IndexError):
                    pass
                if speed_mbps is not None:
                    break

    hr()
    _p(f"  {C.BOLD}{label}{C.NC}")
    hr()
    if speed_mbps is not None:
        _p(f"  {C.G}Result   : {speed_mbps:>9.2f} Mbit/s{C.NC}")
        if bytes_total is not None:
            _p(f"  Bytes    : {bytes_total:>9.1f} MB")
    else:
        err("Natunestim az text output parse konim.")
        _p(f"  {C.Y}Akharin 30 line:{C.NC}")
        for line in txt.splitlines()[-30:]:
            _p(f"    {line}")
        return False

    _p(f"  {C.DIM}Full output: {out}{C.NC}")
    return True


# ============================================================
#  Public entry points
# ============================================================
def menu_iran(state: State):
    _menu_iran(state)


def menu_foreign(state: State):
    _menu_foreign(state)
