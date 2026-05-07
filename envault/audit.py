"""Audit log: records secret access and mutation events to a per-vault log file."""

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from envault.vault import _vault_path

AUDIT_FILE = "audit.log"


def _audit_path(project: str) -> Path:
    return _vault_path(project).parent / AUDIT_FILE


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def log_event(
    project: str,
    action: str,
    key: str,
    *,
    directory: Optional[str] = None,
    success: bool = True,
    detail: Optional[str] = None,
) -> None:
    """Append a single audit event as a JSON line."""
    record = {
        "ts": _now_iso(),
        "project": project,
        "action": action,
        "key": key,
        "success": success,
    }
    if directory is not None:
        record["directory"] = directory
    if detail is not None:
        record["detail"] = detail

    audit_file = _audit_path(project)
    audit_file.parent.mkdir(parents=True, exist_ok=True)
    with audit_file.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record) + "\n")


def read_log(project: str) -> list[dict]:
    """Return all audit records for *project* as a list of dicts."""
    audit_file = _audit_path(project)
    if not audit_file.exists():
        return []
    records = []
    with audit_file.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    pass  # skip corrupt lines
    return records


def clear_log(project: str) -> None:
    """Delete the audit log for *project*."""
    audit_file = _audit_path(project)
    if audit_file.exists():
        audit_file.unlink()
