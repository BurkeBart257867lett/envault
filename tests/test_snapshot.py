"""Tests for envault.snapshot and envault.cli_snapshot."""

from __future__ import annotations

import json
import pytest
from pathlib import Path
from unittest.mock import patch
from click.testing import CliRunner

from envault import snapshot as snap_mod
from envault.snapshot import SnapshotError, create_snapshot, list_snapshots, restore_snapshot
from envault.vault import store_secret, list_secrets
from envault.cli_snapshot import snapshot_group


PROJECT = "snap_test_proj"
PASSWORD = "hunter2"


@pytest.fixture(autouse=True)
def isolated_vault(tmp_path, monkeypatch):
    """Redirect vault storage to a temp directory."""
    monkeypatch.setattr("envault.vault.VAULT_DIR", str(tmp_path / "vault"))
    monkeypatch.setattr("envault.snapshot._vault_path",
                        lambda p: Path(str(tmp_path / "vault" / p / "secrets.db")))
    # Also patch _snapshots_dir to use tmp_path
    def _fake_snapshots_dir(project):
        d = tmp_path / "vault" / project / "snapshots"
        d.mkdir(parents=True, exist_ok=True)
        return d
    monkeypatch.setattr(snap_mod, "_snapshots_dir", _fake_snapshots_dir)
    yield tmp_path


@pytest.fixture()
def seeded(isolated_vault):
    store_secret(PROJECT, "DB_URL", "postgres://localhost/db", PASSWORD)
    store_secret(PROJECT, "API_KEY", "abc123", PASSWORD)
    return isolated_vault


# ---------------------------------------------------------------------------
# Unit tests
# ---------------------------------------------------------------------------

def test_create_snapshot_empty_project_raises(isolated_vault):
    with pytest.raises(SnapshotError, match="No secrets"):
        create_snapshot(PROJECT, PASSWORD)


def test_create_snapshot_returns_path(seeded):
    path = create_snapshot(PROJECT, PASSWORD, label="v1")
    assert path.exists()
    assert path.suffix == ".snap"
    assert "v1" in path.name


def test_snapshot_file_is_valid_json(seeded):
    path = create_snapshot(PROJECT, PASSWORD)
    payload = json.loads(path.read_text())
    assert "ts" in payload
    assert "token" in payload


def test_list_snapshots_empty(isolated_vault):
    assert list_snapshots(PROJECT) == []


def test_list_snapshots_returns_metadata(seeded):
    create_snapshot(PROJECT, PASSWORD, label="first")
    create_snapshot(PROJECT, PASSWORD, label="second")
    snaps = list_snapshots(PROJECT)
    assert len(snaps) == 2
    labels = [s["label"] for s in snaps]
    assert "first" in labels and "second" in labels


def test_restore_snapshot_repopulates_secrets(seeded):
    path = create_snapshot(PROJECT, PASSWORD)
    # wipe secrets
    store_secret(PROJECT, "DB_URL", "OVERWRITTEN", PASSWORD)
    restored = restore_snapshot(PROJECT, path.name, PASSWORD, overwrite=True)
    assert "DB_URL" in restored
    assert "API_KEY" in restored


def test_restore_wrong_password_raises(seeded):
    path = create_snapshot(PROJECT, PASSWORD, snapshot_password="secret")
    with pytest.raises(SnapshotError, match="decrypt"):
        restore_snapshot(PROJECT, path.name, PASSWORD, snapshot_password="wrong")


def test_restore_missing_file_raises(isolated_vault):
    with pytest.raises(SnapshotError, match="not found"):
        restore_snapshot(PROJECT, "nonexistent.snap", PASSWORD)


def test_restore_no_overwrite_skips_existing(seeded):
    path = create_snapshot(PROJECT, PASSWORD)
    restored = restore_snapshot(PROJECT, path.name, PASSWORD, overwrite=False)
    # All keys already exist — nothing should be restored
    assert restored == []


# ---------------------------------------------------------------------------
# CLI tests
# ---------------------------------------------------------------------------

def _runner_invoke(args, password=PASSWORD):
    runner = CliRunner(mix_stderr=False)
    with patch("envault.cli_snapshot.get_password", return_value=password):
        return runner.invoke(snapshot_group, args, catch_exceptions=False)


def test_cli_create_success(seeded):
    result = _runner_invoke(["create", PROJECT, "--label", "cli-test"])
    assert result.exit_code == 0
    assert "Snapshot saved" in result.output


def test_cli_create_empty_project_exits_nonzero(isolated_vault):
    result = _runner_invoke(["create", PROJECT])
    assert result.exit_code != 0


def test_cli_list_shows_snapshots(seeded):
    create_snapshot(PROJECT, PASSWORD, label="mysnap")
    result = _runner_invoke(["list", PROJECT])
    assert result.exit_code == 0
    assert "mysnap" in result.output


def test_cli_restore_success(seeded):
    path = create_snapshot(PROJECT, PASSWORD)
    result = _runner_invoke(["restore", PROJECT, path.name, "--overwrite"])
    assert result.exit_code == 0
    assert "Restored" in result.output
