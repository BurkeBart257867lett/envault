"""Tests for envault.audit and the cli_audit commands."""

import pytest
from click.testing import CliRunner

from envault.audit import clear_log, log_event, read_log
from envault.cli_audit import audit_group


@pytest.fixture()
def isolated_vault(tmp_path, monkeypatch):
    """Redirect the vault base directory to a temp folder."""
    monkeypatch.setenv("ENVAULT_HOME", str(tmp_path))
    import envault.vault as vmod
    import envault.audit as amod
    monkeypatch.setattr(vmod, "VAULT_HOME", tmp_path)
    return tmp_path


def test_empty_log_returns_empty_list(isolated_vault):
    assert read_log("myproject") == []


def test_log_event_creates_file(isolated_vault):
    log_event("myproject", "set", "DB_URL")
    records = read_log("myproject")
    assert len(records) == 1
    r = records[0]
    assert r["action"] == "set"
    assert r["key"] == "DB_URL"
    assert r["success"] is True
    assert "ts" in r


def test_log_event_optional_fields(isolated_vault):
    log_event("proj", "get", "SECRET", directory="/app", success=False, detail="denied")
    r = read_log("proj")[0]
    assert r["directory"] == "/app"
    assert r["success"] is False
    assert r["detail"] == "denied"


def test_multiple_events_appended(isolated_vault):
    for i in range(5):
        log_event("proj", "get", f"KEY_{i}")
    assert len(read_log("proj")) == 5


def test_clear_log_removes_entries(isolated_vault):
    log_event("proj", "set", "X")
    clear_log("proj")
    assert read_log("proj") == []


def test_clear_log_no_file_is_noop(isolated_vault):
    clear_log("nonexistent")  # should not raise


# ── CLI tests ────────────────────────────────────────────────────────────────


def test_cli_show_empty(isolated_vault):
    runner = CliRunner()
    result = runner.invoke(audit_group, ["show", "proj"])
    assert result.exit_code == 0
    assert "No audit log entries" in result.output


def test_cli_show_lists_events(isolated_vault):
    log_event("proj", "set", "API_KEY")
    log_event("proj", "get", "API_KEY")
    runner = CliRunner()
    result = runner.invoke(audit_group, ["show", "proj"])
    assert result.exit_code == 0
    assert "set" in result.output
    assert "get" in result.output
    assert "API_KEY" in result.output


def test_cli_show_filter_action(isolated_vault):
    log_event("proj", "set", "X")
    log_event("proj", "delete", "X")
    runner = CliRunner()
    result = runner.invoke(audit_group, ["show", "proj", "--action", "delete"])
    assert "delete" in result.output
    assert "set" not in result.output


def test_cli_show_tail(isolated_vault):
    for i in range(10):
        log_event("proj", "get", f"K{i}")
    runner = CliRunner()
    result = runner.invoke(audit_group, ["show", "proj", "--tail", "3"])
    lines = [l for l in result.output.splitlines() if l.strip()]
    assert len(lines) == 3


def test_cli_clear(isolated_vault):
    log_event("proj", "set", "Y")
    runner = CliRunner()
    result = runner.invoke(audit_group, ["clear", "proj"], input="y\n")
    assert result.exit_code == 0
    assert read_log("proj") == []
