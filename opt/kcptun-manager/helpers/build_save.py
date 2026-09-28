#!/usr/bin/env python3
import json, sys, datetime
conn_file = sys.argv[1]
name, fip, fport, lport = sys.argv[2], sys.argv[3], int(sys.argv[4]), int(sys.argv[5])
key, crypt, mode, mtu = sys.argv[6], sys.argv[7], sys.argv[8], int(sys.argv[9])
snd, rcv, sb = int(sys.argv[10]), int(sys.argv[11]), int(sys.argv[12])
nc, sv, fec = sys.argv[13], int(sys.argv[14]), sys.argv[15]
tunnels_file = sys.argv[16]

d = json.load(open(conn_file))
tunnels = json.load(open(tunnels_file))

d["connections"][name] = {
    "name": name,
    "iran_listen_port": lport,
    "foreign_ip": fip,
    "foreign_target_port": fport,
    "tunnels": tunnels,
    "kcp": {
        "key": key, "crypt": crypt, "mode": mode,
        "mtu": mtu, "sndwnd": snd, "rcvwnd": rcv,
        "sockbuf": sb, "nocomp": nc, "smuxver": sv,
        "fec": fec, "conn": 1
    },
    "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat()
}

max_l = max((t["local_port"] for t in tunnels), default=31000)
max_u = max((t["iran_udp_port"] for t in tunnels), default=29900)
d["next_local_port"] = max(d.get("next_local_port", 31000), max_l + 1)
d["next_udp_port"]   = max(d.get("next_udp_port",   29900), max_u + 1)
json.dump(d, open(conn_file, "w"), indent=2)
print("OK")
