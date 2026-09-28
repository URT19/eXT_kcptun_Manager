"""Build kcptun-rs from source and install binaries."""

import os
import shutil
import subprocess
import sys
from pathlib import Path

from kcptun_manager import constants as C


def _run(cmd: list[str], cwd: Path | None = None, timeout: int | None = None) -> None:
    print(f"  $ {' '.join(cmd)}", file=sys.stderr)
    subprocess.run(cmd, cwd=cwd, timeout=timeout, check=True)


def _ensure_rust() -> None:
    if shutil.which("cargo") and shutil.which("rustc"):
        return
    print("[INFO] Installing Rust toolchain...", file=sys.stderr)
    _run([
        "bash", "-c",
        "curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs "
        "| sh -s -- -y",
    ])
    cargo_env = Path.home() / ".cargo" / "env"
    if cargo_env.exists():
        # Re-exec in a shell that sources cargo env
        _run(["bash", "-c", f"source {cargo_env} && rustc --version"])


def ensure_binaries(force_rebuild: bool = False) -> None:
    """Ensure kcptun-server and kcptun-client exist in BIN_DIR."""
    C.BIN_DIR.mkdir(parents=True, exist_ok=True)

    server_ok = C.KCPTUN_SERVER_BIN.exists() and os.access(C.KCPTUN_SERVER_BIN, os.X_OK)
    client_ok = C.KCPTUN_CLIENT_BIN.exists() and os.access(C.KCPTUN_CLIENT_BIN, os.X_OK)
    if server_ok and client_ok and not force_rebuild:
        print("[OK] kcptun binaries already present.", file=sys.stderr)
        return

    _ensure_rust()

    src_dir = C.BASE_DIR / "kcptun-rs"
    if force_rebuild and src_dir.exists():
        shutil.rmtree(src_dir, ignore_errors=True)

    if not (src_dir / ".git").exists():
        src_dir.parent.mkdir(parents=True, exist_ok=True)
        _run(["git", "clone", "--depth", "1", C.KCPTUN_REPO, str(src_dir)])

    # cargo build in a bash shell that sources cargo env
    build_cmd = (
        f"source {Path.home() / '.cargo' / 'env'} 2>/dev/null || true; "
        f"cd {src_dir} && timeout {C.KCPTUN_BUILD_TIMEOUT} cargo build --release"
    )
    _run(["bash", "-c", build_cmd])

    for name in ("kcptun-server", "kcptun-client"):
        built = src_dir / "target" / "release" / name
        if not built.exists():
            raise RuntimeError(f"Build did not produce {built}")
        dest = C.BIN_DIR / name
        shutil.copy2(built, dest)
        os.chmod(dest, 0o755)
        print(f"[OK] Installed {dest}", file=sys.stderr)