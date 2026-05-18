"""Diff two snapshots or a snapshot against the live vault."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from envault.snapshot import restore_snapshot, list_snapshots, SnapshotError
from envault.vault import list_secrets, load_secret


@dataclass
class SecretDiff:
    project: str
    added: List[str] = field(default_factory=list)
    removed: List[str] = field(default_factory=list)
    changed: List[str] = field(default_factory=list)

    @property
    def has_changes(self) -> bool:
        return bool(self.added or self.removed or self.changed)

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"SecretDiff(project={self.project!r}, added={self.added}, "
            f"removed={self.removed}, changed={self.changed})"
        )


def _load_snapshot_secrets(
    snapshot_id: str, project: str, password: str
) -> Dict[str, bytes]:
    """Restore a snapshot into a temp structure and read all secrets for project."""
    import tempfile, pathlib
    from envault.snapshot import _snapshots_dir
    import zipfile, json

    snap_dir = _snapshots_dir()
    snap_file = snap_dir / f"{snapshot_id}.zip"
    if not snap_file.exists():
        raise SnapshotError(f"Snapshot not found: {snapshot_id}")

    secrets: Dict[str, bytes] = {}
    with zipfile.ZipFile(snap_file, "r") as zf:
        prefix = f"{project}/"
        for name in zf.namelist():
            if name.startswith(prefix) and name.endswith(".enc"):
                key = name[len(prefix) : -4]
                raw = zf.read(name)
                from envault.crypto import decrypt, derive_key
                from envault.vault import _vault_path
                # derive key same way vault does
                dk = derive_key(password, project.encode())
                try:
                    secrets[key] = decrypt(raw, dk)
                except Exception:
                    secrets[key] = b"<unreadable>"
    return secrets


def diff_snapshots(
    project: str,
    snapshot_a: str,
    snapshot_b: str,
    password: str,
) -> SecretDiff:
    """Compare two snapshots for a project."""
    a = _load_snapshot_secrets(snapshot_a, project, password)
    b = _load_snapshot_secrets(snapshot_b, project, password)
    return _compute_diff(project, a, b)


def diff_snapshot_live(
    project: str,
    snapshot_id: str,
    password: str,
) -> SecretDiff:
    """Compare a snapshot against the current live vault for a project."""
    snap = _load_snapshot_secrets(snapshot_id, project, password)
    live: Dict[str, bytes] = {}
    for key in list_secrets(project):
        try:
            live[key] = load_secret(project, key, password)
        except Exception:
            live[key] = b"<unreadable>"
    return _compute_diff(project, snap, live)


def _compute_diff(
    project: str,
    before: Dict[str, bytes],
    after: Dict[str, bytes],
) -> SecretDiff:
    before_keys = set(before)
    after_keys = set(after)
    added = sorted(after_keys - before_keys)
    removed = sorted(before_keys - after_keys)
    changed = sorted(
        k for k in before_keys & after_keys if before[k] != after[k]
    )
    return SecretDiff(project=project, added=added, removed=removed, changed=changed)
