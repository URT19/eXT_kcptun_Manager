"""Runtime configuration (defaults + user overrides)."""

import os
from dataclasses import dataclass

from kcptun_manager import constants as C


@dataclass
class TunerConfig:
    test_duration: int = 10
    warmup_duration: int = 2
    runs_per_profile: int = 1
    streams: int = 1
    fec_sweep: bool = False
    conn_sweep: bool = False
    cpu_diag: bool = True
    debug: bool = False
    crypt: str = C.DEFAULT_CRYPT

    @classmethod
    def from_env(cls) -> "TunerConfig":
        return cls(
            test_duration=int(os.environ.get("TEST_DURATION", 10)),
            warmup_duration=int(os.environ.get("WARMUP_DURATION", 2)),
            runs_per_profile=int(os.environ.get("RUNS_PER_PROFILE", 1)),
            streams=int(os.environ.get("STREAMS", 1)),
            fec_sweep=os.environ.get("FEC_SWEEP", "0") == "1",
            conn_sweep=os.environ.get("CONN_SWEEP", "0") == "1",
            cpu_diag=os.environ.get("CPU_DIAG", "1") == "1",
            debug=os.environ.get("DEBUG", "0") == "1",
            crypt=os.environ.get("CRYPT", C.DEFAULT_CRYPT),
        )


@dataclass
class SSHInfo:
    host: str
    port: int = 22
    user: str = "root"
    password: str = ""

    @property
    def target(self) -> str:
        return f"{self.user}@{self.host}"