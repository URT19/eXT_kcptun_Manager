#!/usr/bin/env python3
import json, sys, datetime
conn_file, blob_file = sys.argv[1], sys.argv[2]
d = json.load(open(conn_file))
p = json.load(open(blob_file))
d["connections"][p["connection_name"]] = {
    "name": p["connection_name"],
    "foreign_target_port": p["foreign_target_port"],
    "tunnels": p["tunnels"],
    "kcp": p["kcp"],
    "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat()
}
json.dump(d, open(conn_file, "w"), indent=2)
print("OK")
