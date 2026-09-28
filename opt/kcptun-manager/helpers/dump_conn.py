#!/usr/bin/env python3
import json, sys
conn_file, name = sys.argv[1], sys.argv[2]
d = json.load(open(conn_file))
c = d["connections"].get(name)
if not c:
    sys.exit(1)
for k, v in c.items():
    if k == "tunnels":
        for t in v:
            print("TUNNEL\t" + "\t".join(f"{kk}={vv}" for kk, vv in t.items()))
    elif k == "kcp":
        print("KCP\t" + "\t".join(f"{kk}={vv}" for kk, vv in v.items()))
    else:
        print(f"{k}={v}")
