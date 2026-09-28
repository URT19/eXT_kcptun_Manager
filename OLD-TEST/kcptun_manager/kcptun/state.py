"""Persistent state management (state.json)."""

import json
import os
from datetime import datetime
from pathlib import Path

from kcptun_manager import constants as C
from kcptun_manager.models import ManagerState


def _ensure_dirs() -> None:
    for d in (C.BASE_DIR, C.DATA_DIR, C.CONFIG_DIR, C.HAPROXY_DIR,
              C.EXPORT_DIR, C.BACKUP_DIR, C.LOG_DIR, C.BIN_DIR):
        d.mkdir(parents=True, exist_ok=True)


def load_state() -> ManagerState:
    _ensure_dirs()
    if not C.STATE_FILE.exists():
        return ManagerState()
    try:
        with C.STATE_FILE.open("r", encoding="utf-8") as f:
            return ManagerState.from_dict(json.load(f))
    except (json.JSONDecodeError, OSError):
        # Corrupt state -> back it up and start fresh
        backup = C.STATE_FILE.with_suffix(".json.corrupt")
        try:
            C.STATE_FILE.rename(backup)
        except OSError:
            pass
        return ManagerState()


def save_state(state: ManagerState) -> None:
    _ensure_dirs()
    state.last_updated = datetime.utcnow().isoformat(timespec="seconds") + "Z"
    tmp = C.STATE_FILE.with_suffix(".json.tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(state.to_dict(), f, indent=2, ensure_ascii=False)
    os.replace(tmp, C.STATE_FILE)
    os.chmod(C.STATE_FILE, 0o600)