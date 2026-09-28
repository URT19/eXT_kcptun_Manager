"""State management: JSON file, role, ports, connections."""
import os
import json
import subprocess
import tempfile
import datetime

CONF_DIR = "/etc/kcptun-manager"
INSTANCES_DIR = f"{CONF_DIR}/instances"
HAPROXY_DIR = f"{CONF_DIR}/haproxy"
ROLE_FILE = f"{CONF_DIR}/role"
CONN_FILE = f"{CONF_DIR}/connections.json"
LOCK_FILE = "/var/lock/kcptun-manager.lock"


class State:
    def __init__(self):
        os.makedirs(CONF_DIR, exist_ok=True)
        os.makedirs(INSTANCES_DIR, exist_ok=True)
        os.makedirs(HAPROXY_DIR, exist_ok=True)
        self._init_json()
        self._lock_fh = None

    # --- JSON ---
    def _init_json(self):
        if not os.path.exists(CONN_FILE):
            self._write_json({"connections": {}, "next_local_port": 31000, "next_udp_port": 29900})
        os.chmod(CONN_FILE, 0o600)

    def _read_json(self):
        with open(CONN_FILE) as f:
            return json.load(f)

    def _write_json(self, data):
        fd, tmp = tempfile.mkstemp(dir=os.path.dirname(CONN_FILE))
        with os.fdopen(fd, "w") as f:
            json.dump(data, f, indent=2)
        os.replace(tmp, CONN_FILE)
        os.chmod(CONN_FILE, 0o600)

    # --- Role ---
    def get_role(self):
        if os.path.exists(ROLE_FILE):
            with open(ROLE_FILE) as f:
                return f.read().strip()
        return ""

    def set_role(self, role):
        os.makedirs(CONF_DIR, exist_ok=True)
        with open(ROLE_FILE, "w") as f:
            f.write(role)
        os.chmod(ROLE_FILE, 0o600)

    # --- Lock ---
    def acquire_lock(self):
        import fcntl
        self._lock_fh = open(LOCK_FILE, "w")
        try:
            fcntl.flock(self._lock_fh, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise RuntimeError("Ye nushe dige az script dar hale ejrast.")

    # --- Connections ---
    def list_connections(self):
        d = self._read_json()
        return d.get("connections", {})

    def get_connection(self, name):
        return self.list_connections().get(name)

    def exists(self, name):
        return name in self.list_connections()

    def save_connection(self, name, data):
        d = self._read_json()
        d["connections"][name] = data
        self._write_json(d)

    def delete_connection(self, name):
        d = self._read_json()
        d["connections"].pop(name, None)
        self._write_json(d)

    def update_connection(self, name, updates):
        d = self._read_json()
        if name not in d["connections"]:
            raise KeyError(name)
        d["connections"][name].update(updates)
        self._write_json(d)

    def dump(self):
        return self._read_json()

    # --- Port allocation ---
    def port_in_use(self, port, kind):
        """kind in {frontend, local, udp, any}"""
        for c in self.list_connections().values():
            if kind in ("frontend", "any") and c.get("iran_listen_port") == port:
                return True
            for t in c.get("tunnels", []):
                if kind in ("local", "any"):
                    if t.get("local_port") == port: return True
                    if t.get("test_local_port") == port: return True
                    if t.get("iperf_port") == port: return True
                if kind in ("udp", "any"):
                    if t.get("iran_udp_port") == port: return True
                    if t.get("foreign_udp_port") == port: return True
                    if t.get("test_iran_udp_port") == port: return True
                    if t.get("test_foreign_udp_port") == port: return True
        return False

    def port_is_free_os(self, port, proto):
        if proto == "tcp":
            r = subprocess.run(
                ["ss", "-Hltn"], capture_output=True, text=True, timeout=5
            )
            for line in r.stdout.splitlines():
                parts = line.split()
                if len(parts) >= 4:
                    addr = parts[3]
                    if addr.endswith(f":{port}"):
                        return False
        else:
            r = subprocess.run(
                ["ss", "-Hlun"], capture_output=True, text=True, timeout=5
            )
            for line in r.stdout.splitlines():
                parts = line.split()
                if len(parts) >= 5:
                    addr = parts[4]
                    if addr.endswith(f":{port}"):
                        return False
        return True

    def next_free(self, start, kind, proto):
        for p in range(start, start + 2000):
            if not self.port_in_use(p, kind) and self.port_is_free_os(p, proto):
                return p
        raise RuntimeError(f"Port azad peyda nashod (start={start})")


def utc_now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()
