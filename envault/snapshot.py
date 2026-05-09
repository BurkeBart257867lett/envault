"""Snapshot support: capture and restore the full state of a project's secrets."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import List, Optional

from envault.vault import _vault_path, list_secrets, load_secret, store_secret
from envault.crypto import encrypt, decrypt, derive_key, encode_token, decode_token


class SnapshotError(Exception):
    """Raised when a snapshot operation fails."""


def _snapshots_dir(project: str) -> Path:
    base = _vault_path(project).parent
    d = base / "snapshots"
    d.mkdir(parents=True, exist_ok=True)
    return d


def create_snapshot(
    project: str,
    password: str,
    label: Optional[str] = None,
    snapshot_password: Optional[str] = None,
) -> Path:
    """Capture all secrets for *project* and write a snapshot file.

    If *snapshot_password* is given the snapshot blob is re-encrypted with
    that password; otherwise the vault password is reused.
    """
    keys = list_secrets(project)
    if not keys:
        raise SnapshotError(f"No secrets found for project '{project}'")

    secrets = {k: load_secret(project, k, password) for k in keys}

    snap_pass = snapshot_password or password
    salt = derive_key.__module__  # just a stable import; real salt generated inside
    key, _ = derive_key(snap_pass)  # derive_key returns (key, salt)
    blob = json.dumps(secrets).encode()
    token = encrypt(blob, key)

    ts = int(time.time())
    name = f"{label or 'snap'}_{ts}.snap"
    path = _snapshots_dir(project) / name

    payload = {"ts": ts, "label": label, "token": encode_token(token)}
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def list_snapshots(project: str) -> List[dict]:
    """Return metadata for all snapshots of *project*, newest first."""
    d = _snapshots_dir(project)
    results = []
    for f in sorted(d.glob("*.snap"), reverse=True):
        try:
            meta = json.loads(f.read_text(encoding="utf-8"))
            meta["file"] = f.name
            results.append(meta)
        except (json.JSONDecodeError, OSError):
            continue
    return results


def restore_snapshot(
    project: str,
    snapshot_file: str,
    password: str,
    snapshot_password: Optional[str] = None,
    overwrite: bool = False,
) -> List[str]:
    """Restore secrets from a snapshot file.  Returns list of restored keys."""
    path = _snapshots_dir(project) / snapshot_file
    if not path.exists():
        raise SnapshotError(f"Snapshot not found: {snapshot_file}")

    payload = json.loads(path.read_text(encoding="utf-8"))
    token = decode_token(payload["token"])

    snap_pass = snapshot_password or password
    key, _ = derive_key(snap_pass)
    try:
        blob = decrypt(token, key)
    except Exception as exc:
        raise SnapshotError("Failed to decrypt snapshot — wrong password?") from exc

    secrets: dict = json.loads(blob.decode())
    existing = set(list_secrets(project))
    restored = []
    for k, v in secrets.items():
        if k in existing and not overwrite:
            continue
        store_secret(project, k, v, password)
        restored.append(k)
    return restored
