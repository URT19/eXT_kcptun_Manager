"""Foreign (Kharej) main menu."""
import time
from lib.ui import logo_banner, menu_two_cols, hr, prompt, pause, err, C
from lib.state import State
from lib.build import install_kcptun_only, install_server_template
from lib.speedtest import menu_foreign as speedtest_menu_foreign
from lib.modules import connection_flows, services_menu, firewall_menu, backup_menu


def _stats(state):
    conns = state.list_connections()
    nt = sum(len(c.get("tunnels", [])) for c in conns.values())
    return len(conns), nt


def menu_foreign(state: State):
    while True:
        nc, nt = _stats(state)
        logo_banner("foreign", connections=nc, tunnels=nt)

        items = [
            ("__section__", "Setup"),
            ("1",  "Nasb / Initialize",           C.BRIGHT_BLUE, True),

            ("__section__", "Management"),
            ("2",  "Import data az IRAN",         C.G,           True),
            ("3",  "List connection-ha",          C.BOLD,        True),
            ("4",  "Edit connection",             "",            True),
            ("5",  "Hazf connection",             C.R,           True),
            ("6",  "Namayesh config-ha",          "",            True),

            ("__section__", "Services"),
            ("7",  "kcptun-server services",      "",            True),

            ("__section__", "Tools"),
            ("8",  "Firewall",                    "",            True),
            ("9",  "Backup / Restore",            "",            True),
            ("10", "Speedtest",                   C.BRIGHT_ORANGE, True),
            ("11", "Taghir-e Role be IRAN",       C.G,           True),
        ]
        menu_two_cols(items)
        print()
        hr()
        print(f"  {C.R}[0]{C.NC}  Exit")
        print()
        ch = prompt("Entekhab")
        if   ch == "1":  install_kcptun_only(); install_server_template(); pause()
        elif ch == "2":  connection_flows.import_from_iran(state)
        elif ch == "3":  connection_flows.list_full(state)
        elif ch == "4":  connection_flows.edit_foreign(state)
        elif ch == "5":  connection_flows.delete(state, "foreign")
        elif ch == "6":  connection_flows.view_configs(state)
        elif ch == "7":  services_menu.foreign(state)
        elif ch == "8":  firewall_menu.menu(state)
        elif ch == "9":  backup_menu.menu(state)
        elif ch == "10": speedtest_menu_foreign(state)
        elif ch == "11": connection_flows.change_role(state)
        elif ch == "0":  return
        else:
            err("Na-mojaz."); time.sleep(1)
