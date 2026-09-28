#!/usr/bin/env python3
import json, sys
conn_file, blob_file, name = sys.argv[1], sys.argv[2], sys.argv[3]
d = json.load(open(conn_file))
p = json.load(open(blob_file))
bt = {t["id"]: t for t in p["tunnels"]}
for t in d["connections"][name]["tunnels"]:
    b = bt.get(t["id"], {})
    if b.get("test_foreign_udp_port"):
        t["test_foreign_udp_port"] = b["test_foreign_udp_port"]
    if b.get("iperf_port"):
        t["iperf_port"] = b["iperf_port"]
if "foreign_target_port" not in d["connections"][name] and "foreign_target_port" in p:
    d["connections"][name]["foreign_target_port"] = p["foreign_target_port"]
json.dump(d, open(conn_file, "w"), indent=2)
print("OK")
