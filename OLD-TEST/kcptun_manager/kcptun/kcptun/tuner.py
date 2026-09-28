"""KCPTun auto-tuner — Python port of kcptun-rs-optimizer-v4.1.sh.

Baseline + greedy multi-stage sweep, with pre-flight UDP check and
single-core CPU diagnostic.
"""

import json
import os
import re
import shlex
import signal
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

from kcptun_manager import constants as C
from kcptun_manager.config import SSHInfo, TunerConfig
from kcptun_manager.models import KcptunNode, KcptunChannel
from kcptun_manager.system.net import find_free_udp_port, find_free_tcp_port
from kcptun_manager.system.ssh import SSHClient


# ---------------------------------------------------------------------------
# Result dataclass
# ---------------------------------------------------------------------------

@dataclass
class TunerResult:
    baseline_speed: float = 0.0
    mode: str = C.DEFAULT_MODE
    mtu: int = C.DEFAULT_MTU
    sndwnd: int = C.DEFAULT_SNDWND
    rcvwnd: int = C.DEFAULT_RCVWND
    sockbuf: int = C.DEFAULT_SOCKBUF
    nocomp: bool = C.DEFAULT_NOCOMP
    smuxver: int = C.DEFAULT_SMUXVER
    fec_ds: int = C.DEFAULT_FEC_DS
    fec_ps: int = C.DEFAULT_FEC_PS
    conn: int = C.DEFAULT_CONN
    best_speed: float = 0.0
    elapsed_sec: int = 0
    # Stage-by-stage results (for the report)
    stage_results: dict = field(default_factory=dict)
    cpu_diag: dict = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Tuner
# ---------------------------------------------------------------------------

class KcptunTuner:
    STATE_DIR = Path("/run/kcptun-manager-tuner")

    def __init__(self, kharej: SSHInfo, iran: SSHInfo,
                 cfg: TunerConfig, key: str):
        self.kharej = SSHClient(kharej)
        self.iran = SSHClient(iran)
        self.kharej_info = kharej
        self.iran_info = iran
        self.cfg = cfg
        self.key = key
        self.kharej_ip = kharej.host
        self.STATE_DIR.mkdir(parents=True, exist_ok=True)

    # ---- cleanup ----
    def _cleanup_local(self) -> None:
        for pat in ("kcptun-server", "iperf3 -s -B 127.0.0.1", "iperf3 -s -B 0.0.0.0"):
            subprocess.run(["pkill", "-TERM", "-f", pat], check=False)
        time.sleep(0.3)
        for pat in ("kcptun-server", "iperf3 -s -B 127.0.0.1", "iperf3 -s -B 0.0.0.0"):
            subprocess.run(["pkill", "-KILL", "-f", pat], check=False)

    def _cleanup_remote(self) -> None:
        self.iran.run_script(
            "pkill -TERM -f 'kcptun-client' 2>/dev/null || true\n"
            "pkill -TERM -f 'iperf3 -s' 2>/dev/null || true\n"
            "pkill -TERM -f 'iperf3 -c' 2>/dev/null || true\n"
            "sleep 0.3\n"
            "pkill -KILL -f 'kcptun-client' 2>/dev/null || true\n"
            "pkill -KILL -f 'iperf3 -s' 2>/dev/null || true\n"
            "pkill -KILL -f 'iperf3 -c' 2>/dev/null || true\n"
        )

    # ---- iperf parsing ----
    @staticmethod
    def _parse_iperf_json(path: Path) -> float:
        try:
            d = json.loads(path.read_text(encoding="utf-8"))
            bps = d["end"]["sum_received"]["bits_per_second"]
            return round(bps / 1_000_000, 2)
        except Exception:
            return 0.0

    # ---- baseline ----
    def run_baseline(self) -> float:
        port = find_free_tcp_port()
        json_path = self.STATE_DIR / "baseline.json"

        self._cleanup_local()
        self._cleanup_remote()

        subprocess.Popen(
            ["iperf3", "-s", "-B", "0.0.0.0", "-p", str(port), "--idle-timeout", "60"],
            stdout=open(self.STATE_DIR / "iperf-baseline.log", "w"),
            stderr=subprocess.STDOUT,
        )
        time.sleep(2)

        # reachability check from Iran
        try:
            out = self.iran.run(
                f"timeout 3 bash -c '</dev/tcp/{self.kharej_ip}/{port}' "
                f"&& echo OK || echo FAIL", timeout=10,
            )
            if "OK" not in out:
                self._cleanup_local()
                return 0.0
        except Exception:
            self._cleanup_local()
            return 0.0

        # warmup
        self.iran.run(
            f"timeout {self.cfg.warmup_duration} iperf3 -c {self.kharej_ip} "
            f"-p {port} -t {self.cfg.warmup_duration} -P 1 >/dev/null 2>&1 || true",
            timeout=self.cfg.warmup_duration + 10,
        )

        total, valid = 0.0, 0
        for _ in range(self.cfg.runs_per_profile):
            try:
                out = self.iran.run(
                    f"timeout {self.cfg.test_duration + 5} iperf3 -c {self.kharej_ip} "
                    f"-p {port} -t {self.cfg.test_duration} -P {self.cfg.streams} -J",
                    timeout=self.cfg.test_duration + 15,
                )
                json_path.write_text(out, encoding="utf-8")
                speed = self._parse_iperf_json(json_path)
                if speed > 0:
                    total += speed
                    valid += 1
            except Exception:
                pass

        self._cleanup_local()
        return round(total / valid, 2) if valid else 0.0

    # ---- single measurement ----
    def measure(self, mode: str, mtu: int, snd: int, rcv: int, sockbuf: int,
                nocomp: bool, smuxver: int,
                fec_ds: int = 0, fec_ps: int = 0, conn: int | None = None,
                cpu_sample_out: Path | None = None) -> float:
        kcp_port = find_free_udp_port()
        iperf_port = find_free_tcp_port()

        nocomp_flag = "--nocomp" if nocomp else ""
        fec_flag = f"--datashard {fec_ds} --parityshard {fec_ps}" if (fec_ds or fec_ps) else ""
        conn_flag = f"--conn {conn}" if conn else ""

        # local iperf server
        self._cleanup_local()
        self._cleanup_remote()
        subprocess.Popen(
            ["iperf3", "-s", "-B", "127.0.0.1", "-p", str(iperf_port),
             "--idle-timeout", "30"],
            stdout=open(self.STATE_DIR / f"iperf-{iperf_port}.log", "w"),
            stderr=subprocess.STDOUT,
        )

        # local kcptun-server
        server_cmd = [
            str(C.KCPTUN_SERVER_BIN),
            "-l", f":{kcp_port}",
            "-t", f"127.0.0.1:{iperf_port}",
            "--key", self.key, "--crypt", self.cfg.crypt,
            "--mode", mode, "--mtu", str(mtu),
            "--sndwnd", str(snd), "--rcvwnd", str(rcv),
            "--sockbuf", str(sockbuf), "--smuxver", str(smuxver),
        ]
        if nocomp_flag:
            server_cmd.append(nocomp_flag)
        if fec_flag:
            server_cmd += shlex.split(fec_flag)
        subprocess.Popen(
            server_cmd,
            stdout=open(self.STATE_DIR / f"kcptun-server-{kcp_port}.log", "w"),
            stderr=subprocess.STDOUT,
        )
        time.sleep(2)

        # remote kcptun-client
        client_cmd = (
            f"nohup /opt/kcptun-manager/bin/kcptun-client "
            f"-r {self.kharej_ip}:{kcp_port} "
            f"-l :{iperf_port} "
            f"--key {shlex.quote(self.key)} --crypt {self.cfg.crypt} "
            f"--mode {mode} --mtu {mtu} "
            f"--sndwnd {snd} --rcvwnd {rcv} "
            f"--sockbuf {sockbuf} {nocomp_flag} --smuxver {smuxver} "
            f"{fec_flag} {conn_flag} "
            f"> /tmp/kcptun-client-{iperf_port}.log 2>&1 &"
        )
        self.iran.run_script(client_cmd)
        time.sleep(3)

        # warmup through tunnel
        self.iran.run(
            f"timeout 3 iperf3 -c 127.0.0.1 -p {iperf_port} -t 3 -P 1 >/dev/null 2>&1 || true",
            timeout=10,
        )

        json_path = self.STATE_DIR / f"iperf-{os.getpid()}-{iperf_port}.json"

        mpstat_proc = None
        if cpu_sample_out:
            mpstat_proc = subprocess.Popen(
                ["mpstat", "-P", "ALL", "1", str(self.cfg.test_duration)],
                stdout=open(cpu_sample_out, "w"),
                stderr=subprocess.DEVNULL,
            )

        try:
            out = self.iran.run(
                f"timeout {self.cfg.test_duration + 5} iperf3 -c 127.0.0.1 "
                f"-p {iperf_port} -t {self.cfg.test_duration} "
                f"-P {self.cfg.streams} -J",
                timeout=self.cfg.test_duration + 15,
            )
            json_path.write_text(out, encoding="utf-8")
        except Exception:
            pass
        finally:
            if mpstat_proc:
                mpstat_proc.wait()

        speed = self._parse_iperf_json(json_path)
        self._cleanup_local()
        self._cleanup_remote()
        return speed

    # ---- stages ----
    def _progress(self, i: int, total: int, label: str, speed: float) -> None:
        print(f"  [{i}/{total}] {label} -> {speed:.2f} Mbit/s", file=sys.stderr)

    def sweep_mode(self, best: dict) -> dict:
        results = []
        for i, m in enumerate(C.SWEEP_MODES, 1):
            speed = self.measure(m, best["mtu"], best["sndwnd"], best["rcvwnd"],
                                 best["sockbuf"], best["nocomp"], best["smuxver"])
            self._progress(i, len(C.SWEEP_MODES), f"mode={m}", speed)
            results.append((m, speed))
            if speed > best["speed"]:
                best = {**best, "mode": m, "speed": speed}
        best["_stage_mode"] = results
        return best

    def sweep_mtu(self, best: dict) -> dict:
        results = []
        for i, mtu in enumerate(C.SWEEP_MTUS, 1):
            speed = self.measure(best["mode"], mtu, best["sndwnd"], best["rcvwnd"],
                                 best["sockbuf"], best["nocomp"], best["smuxver"])
            self._progress(i, len(C.SWEEP_MTUS), f"mtu={mtu}", speed)
            results.append((mtu, speed))
            if speed > best["speed"]:
                best = {**best, "mtu": mtu, "speed": speed}
        best["_stage_mtu"] = results
        return best

    def sweep_window(self, best: dict) -> dict:
        results = []
        for i, (s, r) in enumerate(C.SWEEP_WINDOWS, 1):
            speed = self.measure(best["mode"], best["mtu"], s, r,
                                 best["sockbuf"], best["nocomp"], best["smuxver"])
            self._progress(i, len(C.SWEEP_WINDOWS), f"win={s}/{r}", speed)
            results.append(((s, r), speed))
            if speed > best["speed"]:
                best = {**best, "sndwnd": s, "rcvwnd": r, "speed": speed}
        best["_stage_win"] = results
        return best

    def sweep_sockbuf(self, best: dict) -> dict:
        results = []
        for i, sb in enumerate(C.SWEEP_SOCKBUFS, 1):
            speed = self.measure(best["mode"], best["mtu"], best["sndwnd"], best["rcvwnd"],
                                 sb, best["nocomp"], best["smuxver"])
            self._progress(i, len(C.SWEEP_SOCKBUFS), f"sockbuf={sb}", speed)
            results.append((sb, speed))
            if speed > best["speed"]:
                best = {**best, "sockbuf": sb, "speed": speed}
        best["_stage_sockbuf"] = results
        return best

    def sweep_nocomp_smux(self, best: dict) -> dict:
        results = []
        for i, (nc, sv) in enumerate(C.SWEEP_NOCOMP_SMUX, 1):
            speed = self.measure(best["mode"], best["mtu"], best["sndwnd"], best["rcvwnd"],
                                 best["sockbuf"], nc, sv)
            self._progress(i, len(C.SWEEP_NOCOMP_SMUX), f"nocomp={nc} smux={sv}", speed)
            results.append(((nc, sv), speed))
            if speed > best["speed"]:
                best = {**best, "nocomp": nc, "smuxver": sv, "speed": speed}
        best["_stage_ns"] = results
        return best

    def sweep_fec(self, best: dict) -> dict:
        results = []
        for i, (ds, ps) in enumerate(C.SWEEP_FEC, 1):
            speed = self.measure(best["mode"], best["mtu"], best["sndwnd"], best["rcvwnd"],
                                 best["sockbuf"], best["nocomp"], best["smuxver"], ds, ps)
            self._progress(i, len(C.SWEEP_FEC), f"fec={ds}/{ps}", speed)
            results.append(((ds, ps), speed))
            if speed > best["speed"]:
                best = {**best, "fec_ds": ds, "fec_ps": ps, "speed": speed}
        best["_stage_fec"] = results
        return best

    def sweep_conn(self, best: dict) -> dict:
        results = []
        for i, c in enumerate(C.SWEEP_CONNS, 1):
            speed = self.measure(best["mode"], best["mtu"], best["sndwnd"], best["rcvwnd"],
                                 best["sockbuf"], best["nocomp"], best["smuxver"],
                                 best["fec_ds"], best["fec_ps"], c)
            self._progress(i, len(C.SWEEP_CONNS), f"conn={c}", speed)
            results.append((c, speed))
            if speed > best["speed"]:
                best = {**best, "conn": c, "speed": speed}
        best["_stage_conn"] = results
        return best

    # ---- CPU diagnostic ----
    def cpu_diagnostic(self, best: dict) -> dict:
        if not self.cfg.cpu_diag:
            return {"skipped": True}
        if subprocess.run(["which", "mpstat"], capture_output=True).returncode != 0:
            return {"skipped": True, "reason": "mpstat missing"}

        cpu1 = self.STATE_DIR / "cpu-conn1.txt"
        cpu4 = self.STATE_DIR / "cpu-conn4.txt"

        s1 = self.measure(best["mode"], best["mtu"], best["sndwnd"], best["rcvwnd"],
                          best["sockbuf"], best["nocomp"], best["smuxver"],
                          cpu_sample_out=cpu1)
        s4 = self.measure(best["mode"], best["mtu"], best["sndwnd"], best["rcvwnd"],
                          best["sockbuf"], best["nocomp"], best["smuxver"],
                          conn=4, cpu_sample_out=cpu4)

        busy, idle = 0, 0
        if cpu1.exists():
            for line in cpu1.read_text().splitlines():
                if "Average:" in line:
                    parts = line.split()
                    if len(parts) >= 2 and parts[1].isdigit():
                        try:
                            idle_pct = float(parts[-1])
                            if idle_pct < 15:
                                busy += 1
                            elif idle_pct > 50:
                                idle += 1
                        except ValueError:
                            pass

        improvement = ((s4 - s1) / s1 * 100) if s1 > 0 else 0.0
        return {
            "conn1_speed": s1,
            "conn4_speed": s4,
            "busy_cores": busy,
            "idle_cores": idle,
            "improvement_pct": round(improvement, 1),
            "cpu_bound": (busy >= 1 and idle >= 1 and improvement > 15),
        }

    # ---- pre-flight ----
    def preflight(self) -> float:
        speed = self.measure(
            C.DEFAULT_MODE, C.DEFAULT_MTU, C.DEFAULT_SNDWND, C.DEFAULT_RCVWND,
            C.DEFAULT_SOCKBUF, C.DEFAULT_NOCOMP, C.DEFAULT_SMUXVER,
        )
        if speed <= 0:
            print("[WARN] Pre-flight returned 0, retrying once...", file=sys.stderr)
            speed = self.measure(
                C.DEFAULT_MODE, C.DEFAULT_MTU, C.DEFAULT_SNDWND, C.DEFAULT_RCVWND,
                C.DEFAULT_SOCKBUF, C.DEFAULT_NOCOMP, C.DEFAULT_SMUXVER,
            )
        return speed

    # ---- main ----
    def run_full(self) -> TunerResult:
        started = int(time.time())
        self.STATE_DIR.mkdir(parents=True, exist_ok=True)

        print("==> Baseline (direct iperf3, no tunnel)", file=sys.stderr)
        baseline = self.run_baseline()
        print(f"[OK] Baseline: {baseline} Mbit/s", file=sys.stderr)

        print("==> Pre-flight UDP reachability check", file=sys.stderr)
        pre = self.preflight()
        if pre <= 0:
            raise RuntimeError(
                "Pre-flight failed twice. UDP port likely blocked on Kharej "
                "firewall/security group, or NAT/UDP filtering on path."
            )
        print(f"[OK] Pre-flight: {pre} Mbit/s", file=sys.stderr)

        best = {
            "mode": C.DEFAULT_MODE, "mtu": C.DEFAULT_MTU,
            "sndwnd": C.DEFAULT_SNDWND, "rcvwnd": C.DEFAULT_RCVWND,
            "sockbuf": C.DEFAULT_SOCKBUF, "nocomp": C.DEFAULT_NOCOMP,
            "smuxver": C.DEFAULT_SMUXVER, "fec_ds": C.DEFAULT_FEC_DS,
            "fec_ps": C.DEFAULT_FEC_PS, "conn": C.DEFAULT_CONN,
            "speed": pre,
        }

        cpu_diag = self.cpu_diagnostic(best)

        print("==> Stage 1: Mode sweep", file=sys.stderr)
        best = self.sweep_mode(best)
        print("==> Stage 2: MTU sweep", file=sys.stderr)
        best = self.sweep_mtu(best)
        print("==> Stage 3: Window sweep", file=sys.stderr)
        best = self.sweep_window(best)
        print("==> Stage 4: SOCKBUF sweep", file=sys.stderr)
        best = self.sweep_sockbuf(best)
        print("==> Stage 5: nocomp/smuxver sweep", file=sys.stderr)
        best = self.sweep_nocomp_smux(best)

        if self.cfg.fec_sweep:
            print("==> Stage 6: FEC sweep", file=sys.stderr)
            best = self.sweep_fec(best)
        if self.cfg.conn_sweep:
            print("==> Stage 7: --conn sweep", file=sys.stderr)
            best = self.sweep_conn(best)

        self._cleanup_local()
        self._cleanup_remote()

        result = TunerResult(
            baseline_speed=baseline,
            mode=best["mode"], mtu=best["mtu"],
            sndwnd=best["sndwnd"], rcvwnd=best["rcvwnd"],
            sockbuf=best["sockbuf"], nocomp=best["nocomp"],
            smuxver=best["smuxver"], fec_ds=best["fec_ds"],
            fec_ps=best["fec_ps"], conn=best["conn"],
            best_speed=best["speed"],
            elapsed_sec=int(time.time()) - started,
            stage_results={k: v for k, v in best.items() if k.startswith("_stage_")},
            cpu_diag=cpu_diag,
        )
        return result