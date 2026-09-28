"""systemd, HAProxy, firewall, env writers."""
import os, subprocess, time
from lib.ui import info, ok, warn, err
from lib.state import INSTANCES_DIR

HAPROXY_CFG = "/etc/haproxy/haproxy.cfg"


def _env_nocomp(nc): return "--nocomp" if nc == "on" else ""


def _env_fec(fec):
    if fec == "0/0": return ""
    ds, ps = fec.split("/", 1)
    return f"--datashard {ds} --parityshard {ps}"


def _write_env(name, tid, lines):
    path = os.path.join(INSTANCES_DIR, f"{name}-{tid}.env")
    with open(path, "w") as f:
        for k, v in lines:
            f.write(f"{k}={v}\n")
    os.chmod(path, 0o600)


def write_instance_env_iran(name, tid, fip, fudp, lport,
                            key, crypt, mode, mtu, snd, rcv, sb, nc, sv, fec):
    _write_env(name, tid, [
        ("FOREIGN_IP", fip), ("FOREIGN_UDP_PORT", fudp), ("LOCAL_PORT", lport),
        ("KCP_KEY", key), ("KCP_CRYPT", crypt), ("KCP_MODE", mode),
        ("KCP_MTU", mtu), ("KCP_SNDWND", snd), ("KCP_RCVWND", rcv),
        ("KCP_SOCKBUF", sb), ("KCP_NOCOMP_FLAG", _env_nocomp(nc)),
        ("KCP_SMUXVER", sv), ("KCP_FEC_FLAGS", _env_fec(fec)),
    ])


def write_instance_env_iran_test(name, tid, fip, fudp, lport,
                                 key, crypt, mode, mtu, snd, rcv, sb, nc, sv, fec):
    _write_env(name, f"{tid}-test", [
        ("FOREIGN_IP", fip), ("FOREIGN_UDP_PORT", fudp), ("LOCAL_PORT", lport),
        ("KCP_KEY", key), ("KCP_CRYPT", crypt), ("KCP_MODE", mode),
        ("KCP_MTU", mtu), ("KCP_SNDWND", snd), ("KCP_RCVWND", rcv),
        ("KCP_SOCKBUF", sb), ("KCP_NOCOMP_FLAG", _env_nocomp(nc)),
        ("KCP_SMUXVER", sv), ("KCP_FEC_FLAGS", _env_fec(fec)),
    ])


def write_instance_env_foreign(name, tid, fudp, target,
                               key, crypt, mode, mtu, snd, rcv, sb, nc, sv, fec):
    _write_env(name, tid, [
        ("FOREIGN_UDP_PORT", fudp), ("FOREIGN_TARGET_PORT", target),
        ("KCP_KEY", key), ("KCP_CRYPT", crypt), ("KCP_MODE", mode),
        ("KCP_MTU", mtu), ("KCP_SNDWND", snd), ("KCP_RCVWND", rcv),
        ("KCP_SOCKBUF", sb), ("KCP_NOCOMP_FLAG", _env_nocomp(nc)),
        ("KCP_SMUXVER", sv), ("KCP_FEC_FLAGS", _env_fec(fec)),
    ])


def write_instance_env_foreign_test(name, tid, fudp, target,
                                    key, crypt, mode, mtu, snd, rcv, sb, nc, sv, fec):
    _write_env(name, f"{tid}-test", [
        ("FOREIGN_UDP_PORT", fudp), ("FOREIGN_TARGET_PORT", target),
        ("KCP_KEY", key), ("KCP_CRYPT", crypt), ("KCP_MODE", mode),
        ("KCP_MTU", mtu), ("KCP_SNDWND", snd), ("KCP_RCVWND", rcv),
        ("KCP_SOCKBUF", sb), ("KCP_NOCOMP_FLAG", _env_nocomp(nc)),
        ("KCP_SMUXVER", sv), ("KCP_FEC_FLAGS", _env_fec(fec)),
    ])


def enable_start_unit(tmpl, inst):
    subprocess.run(["systemctl", "daemon-reload"], check=False)
    subprocess.run(["systemctl", "enable", "--now", f"{tmpl}@{inst}.service"],
                   check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(0.3)
    if subprocess.run(["systemctl", "is-active", "--quiet", f"{tmpl}@{inst}.service"]).returncode == 0:
        ok(f"Service {tmpl}@{inst} faal shod.")
    else:
        warn(f"Service {tmpl}@{inst} faal nashod: journalctl -u {tmpl}@{inst}")


def stop_disable_unit(tmpl, inst):
    subprocess.run(["systemctl", "disable", "--now", f"{tmpl}@{inst}.service"],
                   check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    ok(f"Service {tmpl}@{inst} khamoosh shod.")


def _has_ufw():
    return os.path.exists("/usr/sbin/ufw") or os.path.exists("/usr/bin/ufw")


def fw_allow_tcp(port, comment):
    if _has_ufw():
        subprocess.run(["ufw", "allow", f"{port}/tcp", "comment", comment],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    else:
        subprocess.run(["iptables", "-I", "INPUT", "-p", "tcp", "--dport", str(port), "-j", "ACCEPT"],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    ok(f"Firewall: TCP/{port} baz shod ({comment})")


def fw_allow_udp(port, comment):
    if _has_ufw():
        subprocess.run(["ufw", "allow", f"{port}/udp", "comment", comment],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    else:
        subprocess.run(["iptables", "-I", "INPUT", "-p", "udp", "--dport", str(port), "-j", "ACCEPT"],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    ok(f"Firewall: UDP/{port} baz shod ({comment})")


def fw_delete_tcp(port):
    if _has_ufw():
        subprocess.run(["ufw", "--force", "delete", "allow", f"{port}/tcp"],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    else:
        subprocess.run(["iptables", "-D", "INPUT", "-p", "tcp", "--dport", str(port), "-j", "ACCEPT"],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    ok(f"Firewall: TCP/{port} baste shod")


def fw_delete_udp(port):
    if _has_ufw():
        subprocess.run(["ufw", "--force", "delete", "allow", f"{port}/udp"],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    else:
        subprocess.run(["iptables", "-D", "INPUT", "-p", "udp", "--dport", str(port), "-j", "ACCEPT"],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    ok(f"Firewall: UDP/{port} baste shod")


def _build_haproxy_body(state):
    """Build HAProxy body. NOTE: no `check` on backends because iperf3 
    server only handles one connection at a time and health-check probes 
    would consume that slot."""
    lines = []
    conns = state.list_connections()
    if not conns:
        lines.append("# (hich connection-i vojood nadarad)")
    for name, c in sorted(conns.items(), key=lambda kv: kv[1].get("iran_listen_port", 0)):
        port = c.get("iran_listen_port")
        if not port:
            continue
        lines.append(f"frontend fe_{port}")
        lines.append(f"    bind *:{port}")
        lines.append(f"    mode tcp")
        lines.append(f"    default_backend be_{port}")
        lines.append("")
        lines.append(f"backend be_{port}")
        lines.append(f"    mode tcp")
        lines.append("    balance roundrobin")
        for t in c.get("tunnels", []):
            lp = t.get("local_port")
            if lp:
                # NOTE: `check` hatof mishe chon iperf3 server multi-connection
                # ro poshtibani nemikone va health check ha slot-e server ro
                # eshghal mikonan.
                lines.append(f"    server t{t['id']} 127.0.0.1:{lp}")
        lines.append("")
    return "\n".join(lines)


def rebuild_haproxy(state):
    info("Sakht haproxy.cfg az connections.json...")
    os.makedirs(os.path.dirname(HAPROXY_CFG), exist_ok=True)
    body = _build_haproxy_body(state)
    cfg = f"""# Generated by kcptun-manager. DO NOT EDIT.
# Last update: {time.strftime('%Y-%m-%dT%H:%M:%S%z')}
global
    log /dev/log local0 info
    maxconn 65536
    stats socket /run/haproxy/admin.sock mode 660 level admin
    stats timeout 30s
    daemon

defaults
    mode tcp
    log global
    option tcplog
    option dontlognull
    timeout connect 5s
    timeout client  600s
    timeout server  600s

{body}
listen stats
    bind 127.0.0.1:8404
    mode http
    stats enable
    stats uri /stats
    stats refresh 5s
"""
    with open(HAPROXY_CFG, "w") as f:
        f.write(cfg)
    r = subprocess.run(["haproxy", "-c", "-f", HAPROXY_CFG], capture_output=True, text=True)
    if r.returncode != 0:
        err("haproxy.cfg invalid ast!")
        print(r.stdout); print(r.stderr)
        return False
    ok("haproxy.cfg valid ast.")
    if subprocess.run(["systemctl", "is-active", "--quiet", "haproxy"]).returncode == 0:
        if subprocess.run(["systemctl", "reload", "haproxy"]).returncode == 0:
            ok("HAProxy reload shod."); return True
        if subprocess.run(["systemctl", "restart", "haproxy"]).returncode == 0:
            ok("HAProxy restart shod."); return True
        err("Restart ham fail."); return False
    r = subprocess.run(["systemctl", "enable", "--now", "haproxy"], capture_output=True, text=True)
    if r.returncode == 0:
        ok("HAProxy start shod."); return True
    err("Start HAProxy fail."); return False
