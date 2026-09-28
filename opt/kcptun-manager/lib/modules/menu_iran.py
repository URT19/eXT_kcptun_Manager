"""Iran main menu."""
import time
from lib.ui import logo_banner, menu_two_cols, hr, prompt, pause, err, C
from lib.state import State
from lib.build import install_iran_full
from lib.speedtest import menu_iran as speedtest_menu_iran
from lib.modules import connection_flows, services_menu, haproxy_menu, firewall_menu, backup_menu, migration


def _stats(state):
    conns = state.list_connections()
    nt = sum(len(c.get("tunnels", [])) for c in conns.values())
    return len(conns), nt


def menu_iran(state: State):
    while True:
        nc, nt = _stats(state)
        logo_banner("iran", connections=nc, tunnels=nt)

        items = [
            ("__section__", "Setup"),
            ("1",  "Nasb / Initialize",           C.BRIGHT_BLUE, True),
            ("2",  "Sakht connection jadid",      C.G,           True),
            ("3",  "Export baraye KHAREJ",        C.G,           True),

            ("__section__", "Management"),
            ("4",  "List connection-ha",          C.BOLD,        True),
            ("5",  "Edit connection",             "",            True),
            ("6",  "Namayesh config-ha",          "",            True),
            ("7",  "Hazf connection",             C.R,           True),

            ("__section__", "Services"),
            ("8",  "kcptun-client services",      "",            True),
            ("9",  "HAProxy",                     "",            True),
            ("10", "Firewall",                    "",            True),

            ("__section__", "Tools"),
            ("11", "Speedtest",                   C.BRIGHT_ORANGE, True),
            ("12", "Migrate connection-ha",       "",            True),
            ("13", "Backup / Restore",            "",            True),
            ("14", "Taghir-e Role be KHAREJ",     C.R,           True),
        ]
        menu_two_cols(items)
        print()
        hr()
        print(f"  {C.R}[0]{C.NC}  Exit")
        print()
        ch = prompt("Entekhab")
        if   ch == "1":  install_iran_full(); pause()
        elif ch == "2":  connection_flows.build_iran(state)
        elif ch == "3":  connection_flows.export(state)
        elif ch == "4":  connection_flows.list_full(state)
        elif ch == "5":  connection_flows.edit_iran(state)
        elif ch == "6":  connection_flows.view_configs(state)
        elif ch == "7":  connection_flows.delete(state, "iran")
        elif ch == "8":  services_menu.iran(state)
        elif ch == "9":  haproxy_menu.menu(state)
        elif ch == "10": firewall_menu.menu(state)
        elif ch == "11": speedtest_menu_iran(state)
        elif ch == "12": migration.migrate_iran(state)
        elif ch == "13": backup_menu.menu(state)
        elif ch == "14": connection_flows.change_role(state)
        elif ch == "0":  return
        else:
            err("Na-mojaz."); time.sleep(1)
