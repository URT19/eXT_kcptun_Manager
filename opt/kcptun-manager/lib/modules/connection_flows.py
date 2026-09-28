"""Connection lifecycle: build, export, import, edit, delete, list, view."""
import base64
import json
import os
import re
import subprocess
import time
from lib.ui import (
    info, ok, warn, err, hr, prompt, confirm, pause, C, select_from_list,
    banner, show_server_ip,
)
from lib.state import State, utc_now
from lib.services import (
    write_instance_env_iran, write_instance_env_iran_test,
    write_instance_env_foreign, write_instance_env_foreign_test,
    enable_start_unit, stop_disable_unit, rebuild_haproxy,
    fw_allow_tcp, fw_allow_udp, fw_delete_tcp, fw_delete_udp,
)
from lib.state import INSTANCES_DIR


def _valid_name(s):  return bool(re.fullmatch(r"[A-Za-z0-9_-]+", s))
def _valid_port(s):  return bool(re.fullmatch(r"\d+", s)) and 1 <= int(s) <= 65535
def _valid_ip(s):    return bool(re.fullmatch(r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}", s))


def _svc_state(name):
    r = subprocess.run(["systemctl", "is-active", name],
                       capture_output=True, text=True)
    return r.stdout.strip() or "inactive"


def _color_state(st):
    return f"{C.G}{st}{C.NC}" if st == "active" else f"{C.R}{st}{C.NC}"


# ============================================================
#  LIST
# ============================================================
def _list_compact(state):
    conns = state.list_connections()
    if not conns:
        print("  (hich connection-i vojood nadarad)")
        return
    # header
    print(f"  {C.BOLD}{'NAME':<20} {'FRONT':<7} {'TUN':<5} {'FOREIGN':<22} {'TARGET':<7}{C.NC}")
    print(f"  {C.DIM}{'─'*20} {'─'*7} {'─'*5} {'─'*22} {'─'*7}{C.NC}")
    for n, c in sorted(conns.items()):
        fe = c.get("iran_listen_port", "-")
        nt = len(c.get("tunnels", []))
        fip = c.get("foreign_ip", "-")
        tp = c.get("foreign_target_port", "-")
        print(f"  {n:<20} {str(fe):<7} {str(nt):<5} {str(fip):<22} {str(tp):<7}")


def _list_detailed(state):
    conns = state.list_connections()
    role = state.get_role()
    for n, c in sorted(conns.items()):
        k = c["kcp"]
        tunnels = c.get("tunnels", [])

        # header box
        print()
        print(f"  {C.CY}{C.BOLD}┌─ Connection: {n}{C.NC}")

        if role == "iran":
            fe = c.get("iran_listen_port", "-")
            fip = c.get("foreign_ip", "-")
            tp = c.get("foreign_target_port", "-")
            print(f"  {C.CY}│{C.NC}  Frontend  :  {C.G}127.0.0.1:{fe}{C.NC}   {C.DIM}(HAProxy){C.NC}")
            print(f"  {C.CY}│{C.NC}  Foreign   :  {fip}:{tp}")
        else:
            tp = c.get("foreign_target_port", "-")
            print(f"  {C.CY}│{C.NC}  Role      :  {C.M}KHAREJ (server){C.NC}")
            print(f"  {C.CY}│{C.NC}  Target    :  127.0.0.1:{tp}")

        print(f"  {C.CY}│{C.NC}  KCP       :  crypt={k['crypt']}  mode={k['mode']}  mtu={k['mtu']}")
        print(f"  {C.CY}│{C.NC}               snd={k['sndwnd']}  rcv={k['rcvwnd']}  "
              f"sockbuf={k['sockbuf']}  nocomp={k['nocomp']}  smux={k['smuxver']}  fec={k['fec']}")
        print(f"  {C.CY}│{C.NC}")
        print(f"  {C.CY}│{C.NC}  {C.BOLD}Channels ({len(tunnels)}):{C.NC}")

        if role == "iran":
            print(f"  {C.CY}│{C.NC}    {C.BOLD}{'#':<3} {'MAIN PORT':<11} {'TEST PORT':<11} "
                  f"{'UDP MAIN':<10} {'UDP TEST':<10} {'SERVICE':<10}{C.NC}")
            print(f"  {C.CY}│{C.NC}    {C.DIM}{'─'*3} {'─'*11} {'─'*11} "
                  f"{'─'*10} {'─'*10} {'─'*10}{C.NC}")
            for t in tunnels:
                tid = t["id"]
                main_port = t.get("local_port", "-")
                test_port = t.get("test_local_port", "-")
                main_udp = t.get("iran_udp_port", "-")
                test_udp = t.get("test_iran_udp_port", "-")
                svc_main = _svc_state(f"kcptun-client@{n}-{tid}")
                svc_test = _svc_state(f"kcptun-client@{n}-{tid}-test")
                main_st = _color_state(svc_main)
                test_st = _color_state(svc_test)
                both_ok = (svc_main == "active" and svc_test == "active")
                mark = f"{C.G}✓{C.NC}" if both_ok else f"{C.Y}⚠{C.NC}"
                print(f"  {C.CY}│{C.NC}    {mark} {tid:<2} {main_port:<11} {test_port:<11} "
                      f"{main_udp:<10} {test_udp:<10} {main_st}")
                print(f"  {C.CY}│{C.NC}       {C.DIM}{'':11} {test_st:<11}{C.NC}")
        else:
            print(f"  {C.CY}│{C.NC}    {C.BOLD}{'#':<3} {'UDP MAIN':<11} "
                  f"{'UDP TEST':<11} {'SERVICE':<20}{C.NC}")
            print(f"  {C.CY}│{C.NC}    {C.DIM}{'─'*3} {'─'*11} "
                  f"{'─'*11} {'─'*20}{C.NC}")
            for t in tunnels:
                tid = t["id"]
                main_udp = t.get("foreign_udp_port", "-")
                test_udp = t.get("test_foreign_udp_port", "-")
                svc_main = _svc_state(f"kcptun-server@{n}-{tid}")
                svc_test = _svc_state(f"kcptun-server@{n}-{tid}-test")
                main_st = _color_state(svc_main)
                test_st = _color_state(svc_test)
                both_ok = (svc_main == "active" and svc_test == "active")
                mark = f"{C.G}✓{C.NC}" if both_ok else f"{C.Y}⚠{C.NC}"
                print(f"  {C.CY}│{C.NC}    {mark} {tid:<2} {main_udp:<11} "
                      f"{test_udp:<11} main={main_st}")
                print(f"  {C.CY}│{C.NC}       {C.DIM}{'':11} {'':11} test={test_st}{C.NC}")

        print(f"  {C.CY}└{'─'*50}{C.NC}")


def list_full(state):
    banner(state.get_role())
    print(f"  {C.BOLD}List connection-ha{C.NC}")
    hr()
    _list_compact(state)
    print()
    _list_detailed(state)
    print()
    pause()


# ============================================================
#  VIEW configs
# ============================================================
def view_configs(state):
    banner(state.get_role())
    hr()
    print(f"  {C.BOLD}connections.json{C.NC}")
    hr()
    with open("/etc/kcptun-manager/connections.json") as f:
        print(f.read())
    if state.get_role() == "iran" and os.path.isfile("/etc/haproxy/haproxy.cfg"):
        hr()
        print(f"  {C.BOLD}haproxy.cfg{C.NC}")
        hr()
        with open("/etc/haproxy/haproxy.cfg") as f:
            print(f.read())
    pause()


# ============================================================
#  helpers
# ============================================================
def _conn_items(state):
    items = []
    for name, c in sorted(state.list_connections().items()):
        fe = c.get("iran_listen_port", "-")
        nt = len(c.get("tunnels", []))
        fip = c.get("foreign_ip", "-")
        tp = c.get("foreign_target_port", "-")
        disp = f"{name:<22}  tunnels={nt}  frontend={fe}  foreign={fip}:{tp}"
        items.append((disp, name))
    return items


def _choose_conn(state, label="Shomare connection"):
    items = _conn_items(state)
    if not items:
        err("Hich connection-i vojood nadarad.")
        return None
    return select_from_list(items, label)


def view_one(state: State, name: str):
    banner(state.get_role())
    c = state.get_connection(name)
    if not c:
        print("  peyda nashod."); pause(); return
    k = c["kcp"]
    print(f"  {C.CY}{C.BOLD}┌─ Connection: {name}{C.NC}")
    fe = c.get("iran_listen_port", "-")
    fip = c.get("foreign_ip", "-")
    tp = c.get("foreign_target_port", "-")
    print(f"  {C.CY}│{C.NC}  Frontend   :  {C.G}127.0.0.1:{fe}{C.NC}")
    print(f"  {C.CY}│{C.NC}  Foreign    :  {fip}:{tp}")
    print(f"  {C.CY}│{C.NC}  KCP        :  crypt={k['crypt']}  mode={k['mode']}  mtu={k['mtu']}")
    print(f"  {C.CY}│{C.NC}                snd={k['sndwnd']}  rcv={k['rcvwnd']}  "
          f"sockbuf={k['sockbuf']}  nocomp={k['nocomp']}  smux={k['smuxver']}  fec={k['fec']}")
    print(f"  {C.CY}│{C.NC}")
    print(f"  {C.CY}│{C.NC}  {C.BOLD}Channels:{C.NC}")
    for t in c.get("tunnels", []):
        tid = t["id"]
        print(f"  {C.CY}│{C.NC}    #{tid}  main={t.get('local_port','-')}  "
              f"test={t.get('test_local_port','-')}  "
              f"udp-main={t.get('iran_udp_port','-')}  "
              f"udp-test={t.get('test_iran_udp_port','-')}  "
              f"iperf={t.get('iperf_port','-')}")
    print(f"  {C.CY}└{'─'*50}{C.NC}")
    pause()


# ============================================================
#  BUILD (IRAN)
# ============================================================
def build_iran(state: State):
    hr()
    print(f"  {C.BOLD}Sakht connection jadid (IRAN){C.NC}")
    hr()

    while True:
        name = prompt("Esme connection (a-z 0-9 _ -)")
        if not _valid_name(name):
            err("Esme na-mojaz."); continue
        if state.exists(name):
            err("In esm vojood dare."); continue
        break

    while True:
        fip = prompt("IP server kharej")
        if _valid_ip(fip): break
        err("IP na-mojaz.")

    while True:
        fport = prompt("Port target rooye kharej (mesl 443)", "443")
        if _valid_port(fport): break
        err("Port na-mojaz.")

    while True:
        lport = prompt("Port voroodi rooye IRAN (frontend HAProxy)", "443")
        if not _valid_port(lport):
            err("Port na-mojaz."); continue
        if state.port_in_use(int(lport), "frontend"):
            err("In port estefade shode."); continue
        if not state.port_is_free_os(int(lport), "tcp"):
            err("In port rooye system masroof ast."); continue
        break

    while True:
        nt = prompt("Tedad tunnel-ha", "4")
        try: nt = int(nt)
        except ValueError: err("Adad na-mojaz."); continue
        if 1 <= nt <= 32: break
        err("Tedad na-mojaz.")

    print(); info("Tanzimate kcptun (Enter = default):")
    crypt = prompt("  crypt", "aes-128")
    mode  = prompt("  mode",  "fast3")
    mtu   = prompt("  mtu",   "1350")
    snd   = prompt("  sndwnd","1024")
    rcv   = prompt("  rcvwnd","1024")
    sb    = prompt("  sockbuf","16777216")
    nc    = prompt("  nocomp (on/off)", "on")
    sv    = prompt("  smuxver (1/2)", "2")
    fec   = prompt("  fec (datashard/parityshard)", "0/0")

    try:
        mtu = int(mtu); snd = int(snd); rcv = int(rcv); sb = int(sb); sv = int(sv)
    except ValueError:
        err("Yeki az meghdar-ha adad nist."); return
    if nc not in ("on", "off"):
        err("nocomp bayad on ya off bashe."); return
    if not re.fullmatch(r"\d+/\d+", fec):
        err("fec format na-mojaz."); return

    key = "kcptun-rs-" + base64.b32encode(os.urandom(10)).decode().rstrip("=")[:16]

    hr(); print(f"  {C.BOLD}Khollase:{C.NC}")
    print(f"  Name         : {name}")
    print(f"  Foreign      : {fip}:{fport}")
    print(f"  Iran frontend: :{lport}  (HAProxy roundrobin)")
    print(f"  Tunnels      : {nt}")
    print(f"  kcptun       : crypt={crypt} mode={mode} mtu={mtu} snd={snd} rcv={rcv} "
          f"sb={sb} nocomp={nc} smux={sv} fec={fec}")
    print(f"  Key          : {key}")
    hr()
    if not confirm("Taeed mishe?", "y"):
        warn("Cancel shod."); return

    info("Allocate port-ha...")
    tunnels = []
    cur_local  = state.next_free(31000, "local", "tcp")
    cur_udp    = state.next_free(29900, "udp",   "udp")
    cur_tlocal = state.next_free(32000, "any",   "tcp")
    cur_tudp   = state.next_free(39900, "any",   "udp")
    cur_iperf  = state.next_free(5201,  "any",   "tcp")
    for i in range(1, nt + 1):
        while state.port_in_use(cur_local, "local") or not state.port_is_free_os(cur_local, "tcp"):
            cur_local += 1
        while state.port_in_use(cur_udp, "udp"):
            cur_udp += 1
        while state.port_in_use(cur_tlocal, "any") or not state.port_is_free_os(cur_tlocal, "tcp"):
            cur_tlocal += 1
        while state.port_in_use(cur_tudp, "any"):
            cur_tudp += 1
        while state.port_in_use(cur_iperf, "any"):
            cur_iperf += 1
        tunnels.append({
            "id": i,
            "local_port": cur_local,
            "iran_udp_port": cur_udp,
            "foreign_udp_port": cur_udp,
            "test_local_port": cur_tlocal,
            "test_iran_udp_port": cur_tudp,
            "test_foreign_udp_port": cur_tudp,
            "iperf_port": cur_iperf,
        })
        cur_local += 1; cur_udp += 1; cur_tlocal += 1; cur_tudp += 1; cur_iperf += 1

    state.save_connection(name, {
        "name": name,
        "iran_listen_port": int(lport),
        "foreign_ip": fip,
        "foreign_target_port": int(fport),
        "tunnels": tunnels,
        "kcp": {
            "key": key, "crypt": crypt, "mode": mode,
            "mtu": mtu, "sndwnd": snd, "rcvwnd": rcv,
            "sockbuf": sb, "nocomp": nc, "smuxver": sv,
            "fec": fec, "conn": 1,
        },
        "created_at": utc_now(),
    })
    ok(f"Connection '{name}' zakhire shod.")

    info("Sakht systemd unit-ha va env file-ha...")
    for t in tunnels:
        tid = t["id"]
        write_instance_env_iran(name, tid, fip, t["iran_udp_port"], t["local_port"],
                                key, crypt, mode, mtu, snd, rcv, sb, nc, sv, fec)
        enable_start_unit("kcptun-client", f"{name}-{tid}")
        write_instance_env_iran_test(name, tid, fip, t["test_iran_udp_port"], t["test_local_port"],
                                     key, crypt, mode, mtu, snd, rcv, sb, nc, sv, fec)
        enable_start_unit("kcptun-client", f"{name}-{tid}-test")
        fw_allow_tcp(t["test_local_port"], f"kcptun-mgr {name} t{tid} test")

    info(f"Firewall: baz kardan {lport}/tcp")
    fw_allow_tcp(lport, f"kcptun-mgr {name} frontend")

    info("Rebuild HAProxy...")
    rebuild_haproxy(state) or warn("HAProxy rebuild fail shod.")

    hr(); ok(f"Connection '{name}' rooye IRAN sakhte shod."); hr()
    info("Baraye enteghal be KHAREJ, az menu gozine 'Export' ra bezanid.")
    pause()


# ============================================================
#  EXPORT / IMPORT
# ============================================================
def export(state: State):
    hr(); print(f"  {C.BOLD}Export data baraye KHAREJ{C.NC}"); hr()
    name = _choose_conn(state, "Shomare connection baraye EXPORT")
    if not name: pause(); return
    c = state.get_connection(name)
    payload = {
        "manager_version": "2.1",
        "role_source": "iran",
        "connection_name": c["name"],
        "foreign_target_port": c["foreign_target_port"],
        "tunnels": [],
        "kcp": c["kcp"],
    }
    for t in c["tunnels"]:
        payload["tunnels"].append({
            "id": t["id"],
            "foreign_udp_port": t["foreign_udp_port"],
            "test_foreign_udp_port": t.get("test_foreign_udp_port", ""),
            "iperf_port": t.get("iperf_port", ""),
        })
    raw = json.dumps(payload, separators=(",", ":")).encode()
    blob = base64.b64encode(raw).decode()

    hr(); print(f"  {C.BOLD}Base64 blob (kolle khat ra copy konid):{C.NC}"); print()
    print(blob); print(); hr()
    warn("In blob ra rooye KHAREJ dar menu gozine 'Import' paste konid."); print()
    with open(f"/root/kcptun-export-{name}.b64", "w") as f:
        f.write(blob)
    ok(f"Zakhire shod: /root/kcptun-export-{name}.b64")
    pause()


def import_from_iran(state: State):
    hr(); print(f"  {C.BOLD}Import data az IRAN{C.NC}"); hr()
    print("  Base64 blob ra paste konid va Enter bezanid:")
    blob = input().strip()
    if not blob:
        err("Khali."); pause(); return
    try:
        raw = base64.b64decode(blob)
        payload = json.loads(raw)
    except Exception as e:
        err(f"Base64/JSON na-mojaz: {e}"); pause(); return

    name = payload["connection_name"]
    has_test = all("test_foreign_udp_port" in t and "iperf_port" in t
                   for t in payload["tunnels"])

    if state.exists(name):
        warn(f"Connection '{name}' vojood darad.")
        if not has_test:
            err("Blob fielde test nadarad."); pause(); return
        info("Update test fields...")
        existing = state.get_connection(name)
        by_id = {t["id"]: t for t in payload["tunnels"]}
        for t in existing["tunnels"]:
            b = by_id.get(t["id"], {})
            if b.get("test_foreign_udp_port"):
                t["test_foreign_udp_port"] = b["test_foreign_udp_port"]
            if b.get("iperf_port"):
                t["iperf_port"] = b["iperf_port"]
        state.update_connection(name, {"tunnels": existing["tunnels"]})
        ok("Test fields update shodand.")
        _create_test_instances_foreign(state, name, payload)
        hr(); ok("Import tamam shod."); pause()
        return

    if not has_test:
        warn("Blob fielde test nadarad. Faghat main.")

    state.save_connection(name, {
        "name": name,
        "foreign_target_port": payload["foreign_target_port"],
        "tunnels": payload["tunnels"],
        "kcp": payload["kcp"],
        "created_at": utc_now(),
    })
    ok("Zakhire shod dar json.")

    info("Sakht systemd unit-ha-ye main...")
    k = payload["kcp"]
    target = payload["foreign_target_port"]
    for t in payload["tunnels"]:
        tid = t["id"]
        write_instance_env_foreign(name, tid, t["foreign_udp_port"], target,
                                   k["key"], k["crypt"], k["mode"], k["mtu"],
                                   k["sndwnd"], k["rcvwnd"], k["sockbuf"],
                                   k["nocomp"], k["smuxver"], k["fec"])
        enable_start_unit("kcptun-server", f"{name}-{tid}")
        fw_allow_udp(t["foreign_udp_port"], f"kcptun-mgr {name} t{tid}")

    if has_test:
        _create_test_instances_foreign(state, name, payload)

    hr(); ok(f"Connection '{name}' import va faal shod."); pause()


def _create_test_instances_foreign(state, name, payload):
    info("Sakht instance-haye test...")
    k = payload["kcp"]
    for t in payload["tunnels"]:
        tid = t["id"]
        tfudp = t.get("test_foreign_udp_port")
        ipf = t.get("iperf_port")
        if not tfudp or not ipf:
            continue
        write_instance_env_foreign_test(name, tid, tfudp, ipf,
                                        k["key"], k["crypt"], k["mode"], k["mtu"],
                                        k["sndwnd"], k["rcvwnd"], k["sockbuf"],
                                        k["nocomp"], k["smuxver"], k["fec"])
        enable_start_unit("kcptun-server", f"{name}-{tid}-test")
        fw_allow_udp(tfudp, f"kcptun-mgr {name} t{tid} test")
    ok("Instance-haye test sakhte shodand.")


# ============================================================
#  DELETE
# ============================================================
def delete(state: State, role: str):
    hr(); print(f"  {C.BOLD}Hazf connection{C.NC}"); hr()
    name = _choose_conn(state, "Shomare connection baraye HAZF")
    if not name: pause(); return
    c = state.get_connection(name)
    if not c:
        err("Peyda nashod."); pause(); return

    print()
    print(f"  Name         : {c['name']}")
    if "iran_listen_port" in c:
        print(f"  Iran frontend: :{c['iran_listen_port']}")
    if "foreign_ip" in c:
        print(f"  Foreign IP   : {c['foreign_ip']}")
    print(f"  Target port  : {c['foreign_target_port']}")
    print(f"  Tunnels      : {len(c.get('tunnels', []))}")
    print()
    warn("Non-reversible.")
    if not confirm(f"Hazf '{name}'?", "n"):
        info("Cancel."); pause(); return

    fe_port = c.get("iran_listen_port", "")
    udp_ports = []
    tunnel_ids = []
    for t in c.get("tunnels", []):
        tunnel_ids.append(t["id"])
        for k in ("foreign_udp_port", "test_foreign_udp_port"):
            if t.get(k): udp_ports.append(t[k])

    info("Hazf systemd unit-ha...")
    for tid in tunnel_ids:
        if role == "iran":
            stop_disable_unit("kcptun-client", f"{name}-{tid}")
            stop_disable_unit("kcptun-client", f"{name}-{tid}-test")
        else:
            stop_disable_unit("kcptun-server", f"{name}-{tid}")
            stop_disable_unit("kcptun-server", f"{name}-{tid}-test")
        for suffix in ("", "-test"):
            p = os.path.join(INSTANCES_DIR, f"{name}-{tid}{suffix}.env")
            if os.path.isfile(p):
                try: os.remove(p)
                except Exception: pass

    if role == "iran" and fe_port:
        fw_delete_tcp(fe_port)
    for p in udp_ports:
        fw_delete_udp(p)

    state.delete_connection(name)
    ok(f"Connection '{name}' az json hazf shod.")

    if role == "iran":
        info("Rebuild HAProxy...")
        rebuild_haproxy(state) or warn("Rebuild fail shod.")

    hr(); ok(f"Connection '{name}' kamelan hazf shod."); hr()
    pause()


# ============================================================
#  EDIT
# ============================================================
def edit_iran(state: State):
    hr(); print(f"  {C.BOLD}Edit connection (IRAN){C.NC}"); hr()
    name = _choose_conn(state, "Shomare connection baraye EDIT")
    if not name: pause(); return

    while True:
        banner(state.get_role())
        c = state.get_connection(name)
        print(f"  {C.BOLD}Edit: {name}{C.NC}")
        hr()
        print("  1) Taghir-e foreign IP")
        print("  2) Taghir-e foreign target port")
        print("  3) Taghir-e frontend port")
        print("  4) Taghir-e kcptun params")
        print("  5) Namayesh tafsilat")
        print("  0) Bazgasht")
        hr()
        ch = prompt("Entekhab")
        if ch == "1": _edit_iran_foreign_ip(state, name)
        elif ch == "2": _edit_iran_target_port(state, name)
        elif ch == "3": _edit_iran_frontend_port(state, name)
        elif ch == "4": _edit_iran_kcp(state, name)
        elif ch == "5": view_one(state, name)
        elif ch == "0": return
        else: err("Na-mojaz."); time.sleep(1)


def _edit_iran_foreign_ip(state, name):
    while True:
        new_ip = prompt("IP jadid")
        if _valid_ip(new_ip): break
        err("IP na-mojaz.")
    state.update_connection(name, {"foreign_ip": new_ip})
    ok("IP update shod.")
    _restart_iran_tunnels(state, name)
    rebuild_haproxy(state)


def _edit_iran_target_port(state, name):
    while True:
        t = prompt("Target port jadid")
        if _valid_port(t): break
        err("Port na-mojaz.")
    state.update_connection(name, {"foreign_target_port": int(t)})
    ok("Target port update shod.")


def _edit_iran_frontend_port(state, name):
    c = state.get_connection(name)
    cur = c["iran_listen_port"]
    while True:
        new = prompt("Frontend port jadid")
        if not _valid_port(new):
            err("Port na-mojaz."); continue
        if int(new) != cur:
            if state.port_in_use(int(new), "frontend"):
                err("In port estefade shode."); continue
            if not state.port_is_free_os(int(new), "tcp"):
                err("In port rooye system masroof ast."); continue
        break
    state.update_connection(name, {"iran_listen_port": int(new)})
    fw_delete_tcp(cur)
    fw_allow_tcp(new, f"kcptun-mgr {name} frontend")
    rebuild_haproxy(state)
    ok(f"Frontend avaz shod: {cur} -> {new}")


def _edit_iran_kcp(state, name):
    c = state.get_connection(name)
    k = c["kcp"]
    hr(); print(f"  {C.BOLD}Edit kcptun params (IRAN): {name}{C.NC}"); hr()
    print("  (Enter = negah dashtan)")
    n_crypt = prompt("  crypt", k["crypt"])
    n_mode  = prompt("  mode",  k["mode"])
    n_mtu   = prompt("  mtu",   str(k["mtu"]))
    n_snd   = prompt("  sndwnd", str(k["sndwnd"]))
    n_rcv   = prompt("  rcvwnd", str(k["rcvwnd"]))
    n_sb    = prompt("  sockbuf", str(k["sockbuf"]))
    n_nc    = prompt("  nocomp", k["nocomp"])
    n_sv    = prompt("  smuxver", str(k["smuxver"]))
    n_fec   = prompt("  fec", k["fec"])
    try:
        new_k = {
            "key": k["key"], "crypt": n_crypt, "mode": n_mode,
            "mtu": int(n_mtu), "sndwnd": int(n_snd), "rcvwnd": int(n_rcv),
            "sockbuf": int(n_sb), "nocomp": n_nc, "smuxver": int(n_sv),
            "fec": n_fec, "conn": k.get("conn", 1),
        }
    except ValueError:
        err("Adad na-mojaz."); return
    state.update_connection(name, {"kcp": new_k})
    ok("KCP params update shod.")
    _restart_iran_tunnels(state, name)
    rebuild_haproxy(state)
    pause()


def _restart_iran_tunnels(state, name):
    c = state.get_connection(name)
    fip = c.get("foreign_ip", "")
    k = c["kcp"]
    for t in c["tunnels"]:
        tid = t["id"]
        write_instance_env_iran(name, tid, fip, t["iran_udp_port"], t["local_port"],
                                k["key"], k["crypt"], k["mode"], k["mtu"],
                                k["sndwnd"], k["rcvwnd"], k["sockbuf"],
                                k["nocomp"], k["smuxver"], k["fec"])
        subprocess.run(["systemctl", "restart", f"kcptun-client@{name}-{tid}.service"],
                       check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if t.get("test_local_port") and t.get("test_iran_udp_port"):
            write_instance_env_iran_test(name, tid, fip,
                                         t["test_iran_udp_port"], t["test_local_port"],
                                         k["key"], k["crypt"], k["mode"], k["mtu"],
                                         k["sndwnd"], k["rcvwnd"], k["sockbuf"],
                                         k["nocomp"], k["smuxver"], k["fec"])
            subprocess.run(["systemctl", "restart", f"kcptun-client@{name}-{tid}-test.service"],
                           check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    ok("Tunnels restart shodand.")


def edit_foreign(state: State):
    hr(); print(f"  {C.BOLD}Edit connection (FOREIGN){C.NC}"); hr()
    name = _choose_conn(state, "Shomare connection baraye EDIT")
    if not name: pause(); return

    while True:
        banner(state.get_role())
        print(f"  {C.BOLD}Edit: {name}{C.NC}")
        hr()
        print("  1) Taghir-e foreign target port")
        print("  2) Taghir-e kcptun params")
        print("  3) Namayesh tafsilat")
        print("  0) Bazgasht")
        hr()
        ch = prompt("Entekhab")
        if ch == "1": _edit_foreign_target_port(state, name)
        elif ch == "2": _edit_foreign_kcp(state, name)
        elif ch == "3": view_one(state, name)
        elif ch == "0": return
        else: err("Na-mojaz."); time.sleep(1)


def _edit_foreign_target_port(state, name):
    while True:
        t = prompt("Target port jadid")
        if _valid_port(t): break
        err("Port na-mojaz.")
    state.update_connection(name, {"foreign_target_port": int(t)})
    ok("Target port update shod.")


def _edit_foreign_kcp(state, name):
    c = state.get_connection(name)
    k = c["kcp"]
    target = c["foreign_target_port"]
    hr(); print(f"  {C.BOLD}Edit kcptun params (FOREIGN): {name}{C.NC}"); hr()
    print("  (Enter = negah dashtan)")
    n_crypt = prompt("  crypt", k["crypt"])
    n_mode  = prompt("  mode",  k["mode"])
    n_mtu   = prompt("  mtu",   str(k["mtu"]))
    n_snd   = prompt("  sndwnd", str(k["sndwnd"]))
    n_rcv   = prompt("  rcvwnd", str(k["rcvwnd"]))
    n_sb    = prompt("  sockbuf", str(k["sockbuf"]))
    n_nc    = prompt("  nocomp", k["nocomp"])
    n_sv    = prompt("  smuxver", str(k["smuxver"]))
    n_fec   = prompt("  fec", k["fec"])
    try:
        new_k = {
            "key": k["key"], "crypt": n_crypt, "mode": n_mode,
            "mtu": int(n_mtu), "sndwnd": int(n_snd), "rcvwnd": int(n_rcv),
            "sockbuf": int(n_sb), "nocomp": n_nc, "smuxver": int(n_sv),
            "fec": n_fec, "conn": k.get("conn", 1),
        }
    except ValueError:
        err("Adad na-mojaz."); return
    state.update_connection(name, {"kcp": new_k})
    ok("KCP params update shod.")
    for t in c["tunnels"]:
        tid = t["id"]
        write_instance_env_foreign(name, tid, t["foreign_udp_port"], target,
                                   n_crypt, n_mode, new_k["mtu"],
                                   new_k["sndwnd"], new_k["rcvwnd"], new_k["sockbuf"],
                                   n_nc, new_k["smuxver"], n_fec)
        subprocess.run(["systemctl", "restart", f"kcptun-server@{name}-{tid}.service"],
                       check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if t.get("test_foreign_udp_port") and t.get("iperf_port"):
            write_instance_env_foreign_test(name, tid,
                                            t["test_foreign_udp_port"], t["iperf_port"],
                                            n_crypt, n_mode, new_k["mtu"],
                                            new_k["sndwnd"], new_k["rcvwnd"], new_k["sockbuf"],
                                            n_nc, new_k["smuxver"], n_fec)
            subprocess.run(["systemctl", "restart", f"kcptun-server@{name}-{tid}-test.service"],
                           check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    pause()


# ============================================================
#  Role change
# ============================================================
def change_role(state: State):
    hr(); print(f"  {C.BOLD}Taghir-e Role{C.NC}"); hr()
    cur = state.get_role()
    print(f"  Current Role: {C.G}{cur}{C.NC}"); print()
    target = "foreign" if cur == "iran" else "iran"
    print(f"  New Role    : {C.Y}{target}{C.NC}")
    print()
    ans = input(f"  {C.BOLD}Confirm?{C.NC} (y/n): ").strip().lower()
    if not ans.startswith("y"):
        info("Cancelled.")
        pause()
        return
    state.set_role(target)
    verify = state.get_role()
    if verify != target:
        err(f"Role zakhire nashod! (file says: {verify})")
        pause()
        return
    ok(f"Role avaz shod be '{target}'.")
    print()
    info("Restarting script...")
    import time; time.sleep(1.0)

    # release lock قبل از exec
    try:
        import fcntl
        if state._lock_fh:
            fcntl.flock(state._lock_fh, fcntl.LOCK_UN)
            state._lock_fh.close()
    except Exception:
        pass

    # re-exec خود اسکریپت
    import os, sys
    script = "/opt/kcptun-manager/kcptun_manager.py"
    os.execv(sys.executable, [sys.executable, "-u", script])
