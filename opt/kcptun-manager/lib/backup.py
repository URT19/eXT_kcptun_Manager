"""Backup helper: before editing any file, save a numbered .bak.
Also tracks the app version."""
import os
import shutil
import glob
import re
from datetime import datetime

BACKUP_DIR = "/var/backups/kcptun-manager"
VERSION_FILE = "/opt/kcptun-manager/VERSION"


def ensure_dirs():
    os.makedirs(BACKUP_DIR, exist_ok=True)


def _next_index(basename):
    """Find highest existing .NNNN.bak for basename; return next index."""
    pattern = os.path.join(BACKUP_DIR, f"{basename}.*.bak")
    existing = glob.glob(pattern)
    max_idx = 0
    for path in existing:
        m = re.search(r"\.(\d{4})\.bak$", path)
        if m:
            max_idx = max(max_idx, int(m.group(1)))
    return max_idx + 1


def snapshot(filepath):
    """Copy filepath to BACKUP_DIR with a numbered suffix. Returns backup path."""
    ensure_dirs()
    if not os.path.isfile(filepath):
        return None
    basename = os.path.basename(filepath)
    idx = _next_index(basename)
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    dest = os.path.join(BACKUP_DIR, f"{basename}.{idx:04d}.{ts}.bak")
    shutil.copy2(filepath, dest)
    # prune: keep last 20 per basename
    _prune(basename, keep=20)
    return dest


def _prune(basename, keep=20):
    pattern = os.path.join(BACKUP_DIR, f"{basename}.*.bak")
    files = sorted(glob.glob(pattern))
    if len(files) > keep:
        for old in files[:-keep]:
            try: os.remove(old)
            except Exception: pass


def list_backups(basename=None):
    """Return list of (path, size, mtime) sorted by mtime desc."""
    ensure_dirs()
    if basename:
        files = glob.glob(os.path.join(BACKUP_DIR, f"{basename}.*.bak"))
    else:
        files = glob.glob(os.path.join(BACKUP_DIR, "*.bak"))
    out = []
    for f in files:
        try:
            st = os.stat(f)
            out.append((f, st.st_size, st.st_mtime))
        except Exception:
            pass
    return sorted(out, key=lambda x: -x[2])


def restore(backup_path, target_path=None):
    """Restore a backup. If target_path None, infer from basename."""
    if not os.path.isfile(backup_path):
        raise FileNotFoundError(backup_path)
    if target_path is None:
        basename = os.path.basename(backup_path)
        # strip ".NNNN.TIMESTAMP.bak"
        real = re.sub(r"\.\d{4}\.\d{8}-\d{6}\.bak$", "", basename)
        if not real:
            raise ValueError("Cannot infer target name from backup filename")
        # Find it under common roots
        candidates = [
            f"/opt/kcptun-manager/{real}",
            f"/opt/kcptun-manager/lib/{real}",
            f"/opt/kcptun-manager/lib/modules/{real}",
        ]
        for c in candidates:
            if os.path.isfile(c):
                target_path = c
                break
        if target_path is None:
            raise ValueError(f"Cannot locate original file for {basename}")
    shutil.copy2(backup_path, target_path)
    return target_path


# ---------- version ----------
def get_version():
    if os.path.isfile(VERSION_FILE):
        with open(VERSION_FILE) as f:
            return f.read().strip()
    return "0.0.0"


def bump_version(part="patch"):
    """part in {'major','minor','patch'}"""
    cur = get_version()
    try:
        major, minor, patch = (int(x) for x in cur.split("."))
    except Exception:
        major, minor, patch = 0, 0, 0
    if part == "major":
        major += 1; minor = 0; patch = 0
    elif part == "minor":
        minor += 1; patch = 0
    else:
        patch += 1
    new = f"{major}.{minor}.{patch}"
    with open(VERSION_FILE, "w") as f:
        f.write(new)
    return new


def set_version(v):
    with open(VERSION_FILE, "w") as f:
        f.write(v)
    return v
