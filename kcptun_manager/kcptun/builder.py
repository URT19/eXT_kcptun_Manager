def build_kcptun_server_cmd(node: KcptunNode) -> list[str]:
    """ساخت دستور kcptun-server برای خارج."""
    cmd = [
        "/opt/kcptun-manager/bin/kcptun-server",
        "-l", f":{node.kcp_port}",
        "-t", f"{node.target_host}:{node.target_port}",
        "--key", node.key,
        "--crypt", node.crypt,
        "--mode", node.mode,
        "--mtu", str(node.mtu),
        "--sndwnd", str(node.sndwnd),
        "--rcvwnd", str(node.rcvwnd),
        "--sockbuf", str(node.sockbuf),
        "--smuxver", str(node.smuxver),
    ]
    if node.nocomp:
        cmd.append("--nocomp")
    if node.fec_ds > 0 or node.fec_ps > 0:
        cmd += ["--datashard", str(node.fec_ds), "--parityshard", str(node.fec_ps)]
    if node.conn > 1:
        cmd += ["--conn", str(node.conn)]
    return cmd


def build_kcptun_client_cmd(channel: KcptunChannel, node: KcptunNode) -> list[str]:
    """ساخت دستور kcptun-client برای ایران."""
    cmd = [
        "/opt/kcptun-manager/bin/kcptun-client",
        "-r", f"{node.address}:{node.kcp_port}",
        "-l", f":{channel.local_tcp_port}",
        "--key", node.key,
        "--crypt", node.crypt,
        "--mode", node.mode,
        "--mtu", str(node.mtu),
        "--sndwnd", str(node.sndwnd),
        "--rcvwnd", str(node.rcvwnd),
        "--sockbuf", str(node.sockbuf),
        "--smuxver", str(node.smuxver),
    ]
    if node.nocomp:
        cmd.append("--nocomp")
    if node.fec_ds > 0 or node.fec_ps > 0:
        cmd += ["--datashard", str(node.fec_ds), "--parityshard", str(node.fec_ps)]
    if node.conn > 1:
        cmd += ["--conn", str(node.conn)]
    return cmd