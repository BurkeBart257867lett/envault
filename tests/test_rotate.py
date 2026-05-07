"""Tests for envault.rotate and the CLI rotate command."""

from __future__ import annotations

import pytest
from click.testing import CliRunner

from envault.rotate import RotationError, rotate_secrets
from envault.vault import list_secrets, load_secret, store_secret
from envault.cli_rotate import rotate_group


PROJECT = "test_proj"
OLD_PW = "old-hunter2"
NEW_PW = "new-s3cret!"


@pytest.fixture()
def isolated_vault(tmp_path, monkeypatch):
    monkeypatch.setenv("ENVAULT_DIR", str(tmp_path))
    return tmp_path


@pytest.fixture()
def seeded(isolated_vault):
    store_secret(PROJECT, "DB_URL", "postgres://localhost/db", OLD_PW)
    store_secret(PROJECT, "API_KEY", "abc123", OLD_PW)
    return isolated_vault


# --- unit tests ---

def test_rotate_empty_project_returns_empty(isolated_vault):
    result = rotate_secrets(PROJECT, OLD_PW, NEW_PW)
    assert result == []


def test_rotate_re_encrypts_all_secrets(seeded):
    rotated = rotate_secrets(PROJECT, OLD_PW, NEW_PW)
    assert set(rotated) == {"DB_URL", "API_KEY"}

    # readable with new password
    assert load_secret(PROJECT, "DB_URL", NEW_PW) == "postgres://localhost/db"
    assert load_secret(PROJECT, "API_KEY", NEW_PW) == "abc123"


def test_old_password_rejected_after_rotation(seeded):
    rotate_secrets(PROJECT, OLD_PW, NEW_PW)
    with pytest.raises(Exception):
        load_secret(PROJECT, "DB_URL", OLD_PW)


def test_wrong_old_password_raises_rotation_error(seeded):
    with pytest.raises(RotationError):
        rotate_secrets(PROJECT, "wrong-password", NEW_PW)


def test_dry_run_does_not_modify_vault(seeded):
    rotated = rotate_secrets(PROJECT, OLD_PW, NEW_PW, dry_run=True)
    assert set(rotated) == {"DB_URL", "API_KEY"}
    # vault still readable with OLD password
    assert load_secret(PROJECT, "DB_URL", OLD_PW) == "postgres://localhost/db"


# --- CLI tests ---

def test_cli_rotate_dry_run(seeded, monkeypatch):
    runner = CliRunner()
    result = runner.invoke(
        rotate_group,
        ["run", PROJECT, "--dry-run"],
        input=f"{OLD_PW}\n",
    )
    assert result.exit_code == 0
    assert "Dry run" in result.output
    assert load_secret(PROJECT, "DB_URL", OLD_PW) == "postgres://localhost/db"


def test_cli_rotate_success(seeded):
    runner = CliRunner()
    result = runner.invoke(
        rotate_group,
        ["run", PROJECT],
        input=f"{OLD_PW}\n{NEW_PW}\n{NEW_PW}\n",
    )
    assert result.exit_code == 0
    assert "2 secret(s)" in result.output
    assert load_secret(PROJECT, "API_KEY", NEW_PW) == "abc123"


def test_cli_rotate_wrong_old_password_exits_nonzero(seeded):
    runner = CliRunner()
    result = runner.invoke(
        rotate_group,
        ["run", PROJECT],
        input=f"wrong-pw\n{NEW_PW}\n{NEW_PW}\n",
    )
    assert result.exit_code != 0
    assert "Error" in result.output
