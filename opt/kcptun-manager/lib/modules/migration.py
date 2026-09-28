"""Migrate old connections."""
from lib.ui import hr, info, ok, warn, pause, confirm, C
from lib.state import State
from lib.services import write_instance_env_iran_test, enable_start_unit, fw_allow_tcp


def migrate_iran(state: State):
    hr(); print(f"  {C.BOLD}Migrate connection-ha{C.NC}"); hr()
    warn("Baraye connection-ha-i ke test fields nadaran.")
    names = [n for n, c in state.list_connections().items()
             if any("test_local_port" not in t for t in c.get("tunnels", []))]
    if not names:
        ok("Hame connection-ha migrate shodand."); pause(); return
    info("In connection-ha niaz be migrate darand:")
    for n in names: print(" ", n)
    if not confirm("Migrate konim?", "y"): pause(); return

    for name in names:
        info(f"Migrate: {name}")
        c = state.get_connection(name)
        fip = c.get("foreign_ip", "")
        k = c["kcp"]
        for t in c["tunnels"]:
            if "test_local_port" in t: continue
            tlp = state.next_free(32000, "any", "tcp")
            tup = state.next_free(39900, "any", "udp")
            ipf = state.next_free(5201, "any", "tcp")
            t["test_local_port"] = tlp
            t["test_iran_udp_port"] = tup
            t["test_foreign_udp_port"] = tup
            t["iperf_port"] = ipf
            write_instance_env_iran_test(name, t["id"], fip, tup, tlp,
                                         k["key"], k["crypt"], k["mode"], k["mtu"],
                                         k["sndwnd"], k["rcvwnd"], k["sockbuf"],
                                         k["nocomp"], k["smuxver"], k["fec"])
            enable_start_unit("kcptun-client", f"{name}-{t['id']}-test")
            fw_allow_tcp(tlp, f"kcptun-mgr {name} t{t['id']} test")
        state.update_connection(name, {"tunnels": c["tunnels"]})
    hr(); ok("Migrate tamam shod."); pause()
