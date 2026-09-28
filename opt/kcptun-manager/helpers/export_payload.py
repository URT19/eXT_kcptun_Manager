#!/usr/bin/env python3
import json, sys, base64
conn_file, name = sys.argv[1], sys.argv[2]
d = json.load(open(conn_file))
c = d["connections"][name]
payload = {
    "manager_version": "2.0",
    "role_source": "iran",
    "connection_name": c["name"],
    "foreign_target_port": c["foreign_target_port"],
    "tunnels": [],
    "kcp": c["kcp"]
}
for t in c["tunnels"]:
    payload["tunnels"].append({
        "id": t["id"],
        "foreign_udp_port": t["foreign_udp_port"],
        "test_foreign_udp_port": t.get("test_foreign_udp_port", ""),
        "iperf_port": t.get("iperf_port", ""),
    })
raw = json.dumps(payload, separators=(",", ":")).encode()
print(base64.b64encode(raw).decode())
