"""Tests for envault.export module."""

import json
import os
import pytest
from pathlib import Path

from envault.export import export_secrets, import_secrets
from envault.vault import store_secret, list_secrets


PASSWORD = "test-master-pass"
EXPORT_PASSWORD = "export-secret-42"
PROJECT = "export_test_proj"


@pytest.fixture(autouse=True)
def isolated_vault(tmp_path, monkeypatch):
    """Redirect vault storage to a temp directory."""
    monkeypatch.setenv("ENVAULT_HOME", str(tmp_path))
    yield tmp_path


@pytest.fixture()
def populated_project():
    store_secret(PROJECT, "DB_HOST", "localhost", PASSWORD)
    store_secret(PROJECT, "DB_PORT", "5432", PASSWORD)
    store_secret(PROJECT, "API_KEY", "abc123", PASSWORD)


def test_export_env_format(populated_project, tmp_path):
    out = tmp_path / "secrets.env"
    export_secrets(PROJECT, PASSWORD, str(out), fmt="env")
    content = out.read_text()
    assert "DB_HOST=localhost" in content
    assert "DB_PORT=5432" in content
    assert "API_KEY=abc123" in content


def test_export_json_format(populated_project, tmp_path):
    out = tmp_path / "secrets.json"
    export_secrets(PROJECT, PASSWORD, str(out), export_password=EXPORT_PASSWORD, fmt="json")
    bundle = json.loads(out.read_text())
    assert bundle["project"] == PROJECT
    assert "data" in bundle


def test_export_json_requires_export_password(populated_project, tmp_path):
    out = tmp_path / "secrets.json"
    with pytest.raises(ValueError, match="export_password"):
        export_secrets(PROJECT, PASSWORD, str(out), fmt="json")


def test_export_unknown_format_raises(populated_project, tmp_path):
    with pytest.raises(ValueError, match="Unknown format"):
        export_secrets(PROJECT, PASSWORD, str(tmp_path / "x.txt"), fmt="xml")


def test_export_empty_project_raises(tmp_path):
    with pytest.raises(ValueError, match="No secrets found"):
        export_secrets("nonexistent", PASSWORD, str(tmp_path / "out.env"), fmt="env")


def test_import_env_file(tmp_path):
    env_file = tmp_path / "import.env"
    env_file.write_text("FOO=bar\nBAZ=qux\n")
    imported = import_secrets(str(env_file), "new_proj", PASSWORD)
    assert set(imported) == {"FOO", "BAZ"}
    assert list_secrets("new_proj") is not None


def test_import_json_roundtrip(populated_project, tmp_path):
    out = tmp_path / "bundle.json"
    export_secrets(PROJECT, PASSWORD, str(out), export_password=EXPORT_PASSWORD, fmt="json")
    imported = import_secrets(str(out), "restored_proj", PASSWORD, export_password=EXPORT_PASSWORD)
    assert set(imported) == {"DB_HOST", "DB_PORT", "API_KEY"}


def test_import_no_overwrite_skips_existing(populated_project, tmp_path):
    env_file = tmp_path / "partial.env"
    env_file.write_text("DB_HOST=newvalue\nNEW_KEY=hello\n")
    imported = import_secrets(str(env_file), PROJECT, PASSWORD, overwrite=False)
    assert "NEW_KEY" in imported
    assert "DB_HOST" not in imported


def test_import_with_overwrite_replaces(populated_project, tmp_path):
    env_file = tmp_path / "override.env"
    env_file.write_text("DB_HOST=newvalue\n")
    imported = import_secrets(str(env_file), PROJECT, PASSWORD, overwrite=True)
    assert "DB_HOST" in imported


def test_import_missing_file_raises():
    with pytest.raises(FileNotFoundError):
        import_secrets("/nonexistent/path.env", PROJECT, PASSWORD)


def test_import_unsupported_extension_raises(tmp_path):
    bad = tmp_path / "data.csv"
    bad.write_text("key,value\n")
    with pytest.raises(ValueError, match="Unsupported file extension"):
        import_secrets(str(bad), PROJECT, PASSWORD)
