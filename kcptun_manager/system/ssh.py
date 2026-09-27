"""SSH/SCP wrapper using sshpass -e (password from env, never CLI arg)."""

import hashlib
import os
import shlex
import subprocess
from pathlib import Path

from kcptun_manager.config import SSHInfo


class SSHClient:
    def __init__(self, info: SSHInfo, connect_timeout: int = 15):
        self.info = info
        self.connect_timeout = connect_timeout
        # Export password for sshpass -e (never pass via CLI)
        os.environ["SSHPASS"] = info.password

    # ---- low-level ----
    def _base_opts(self) -> list[str]:
        return [
            "-o", "StrictHostKeyChecking=no",
            "-o", "UserKnownHostsFile=/dev/null",
            "-o", "LogLevel=ERROR",
            "-o", f"ConnectTimeout={self.connect_timeout}",
            "-o", "ServerAliveInterval=5",
            "-o", "ServerAliveCountMax=3",
        ]

    def run(self, remote_cmd: str, timeout: int | None = None) -> str:
        cmd = [
            "sshpass", "-e", "ssh",
            *self._base_opts(),
            "-p", str(self.info.port),
            self.info.target,
            remote_cmd,
        ]
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return r.stdout

    def run_script(self, script: str, timeout: int | None = None) -> str:
        cmd = [
            "sshpass", "-e", "ssh",
            *self._base_opts(),
            "-p", str(self.info.port),
            self.info.target,
            "bash -s",
        ]
        r = subprocess.run(cmd, input=script, capture_output=True, text=True, timeout=timeout)
        return r.stdout

    def scp(self, src: Path, dst: str, timeout: int = 60) -> None:
        cmd = [
            "sshpass", "-e", "scp", "-q",
            "-o", "StrictHostKeyChecking=no",
            "-o", "UserKnownHostsFile=/dev/null",
            "-o", "LogLevel=ERROR",
            "-o", f"ConnectTimeout={self.connect_timeout}",
            "-P", str(self.info.port),
            str(src), f"{self.info.target}:{dst}",
        ]
        subprocess.run(cmd, check=True, timeout=timeout)

    def check(self) -> bool:
        try:
            out = self.run("echo SSH_OK", timeout=20)
            return "SSH_OK" in out
        except Exception:
            return False

    # ---- high-level ----
    def copy_atomic(self, src: Path, dst: str) -> None:
        """Upload with SHA256 verification, then atomic rename."""
        local_sha = hashlib.sha256(src.read_bytes()).hexdigest()
        tmp = f"{dst}.new.{os.getpid()}"
        self.scp(src, tmp)
        remote_sha = self.run(f"sha256sum {shlex.quote(tmp)}").split()[0]
        if remote_sha != local_sha:
            self.run(f"rm -f {shlex.quote(tmp)}")
            raise RuntimeError(f"SHA256 mismatch for {src.name}")
        self.run(f"chmod 0755 {shlex.quote(tmp)} && mv -f {shlex.quote(tmp)} {shlex.quote(dst)}")
        