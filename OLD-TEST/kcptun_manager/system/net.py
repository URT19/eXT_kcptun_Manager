"""Network helpers: free port discovery."""

import random
import socket
import subprocess
import sys

from kcptun_manager import constants as C


def _port_in_use_udp(port: int) -> bool:
    try:
        out = subprocess.run(
            ["ss", "-Hlun"], capture_output=True, text=True, timeout=5,
        ).stdout
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False
    return any(f":{port}" in line.split()[4] for line in out.splitlines() if len(line.split()) > 4)


def _port_in_use_tcp(port: int) -> bool:
    try:
        out = subprocess.run(
            ["ss", "-Hltn"], capture_output=True, text=True, timeout=5,
        ).stdout
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False
    return any(f":{port}" in line.split()[3] for line in out.splitlines() if len(line.split()) > 3)


def find_free_udp_port(start: int = C.DEFAULT_KCP_PORT,
                       span: int = C.DEFAULT_KCP_PORT_RANGE) -> int:
    for p in range(start, start + span):
        if not _port_in_use_udp(p):
            return p
    raise RuntimeError("No free UDP port found")


def find_free_tcp_port(lo: int | None = None, hi: int | None = None,
                       tries: int = 200) -> int:
    lo = lo or C.DEFAULT_TCP_PORT_RANGE[0]
    hi = hi or C.DEFAULT_TCP_PORT_RANGE[1]
    for _ in range(tries):
        p = random.randint(lo, hi)
        if not _port_in_use_tcp(p):
            return p
    raise RuntimeError("No free TCP port found")


def wait_tcp(host: str, port: int, tries: int = 20, delay: float = 0.5) -> bool:
    import time
    for _ in range(tries):
        try:
            with socket.create_connection((host, port), timeout=1):
                return True
        except OSError:
            time.sleep(delay)
    return False