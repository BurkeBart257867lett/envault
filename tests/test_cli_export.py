"""CLI integration tests for export/import commands."""

import json
import pytest
from click.testing import CliRunner
from pathlib import Path

from envault.cli_export import export_group
from envault.vault import store_secret


PASSWORD = "cli-export-pass"
PROJECT = "cli_export_proj"


@pytest.fixture(autouse=True)
def isolated_vault(tmp_path, monkeypatch):
    monkeypatch.setenv("ENVAULT_HOME", str(tmp_path))
    yield tmp_path


@pytest.fixture()
def seeded_project():
    store_secret(PROJECT, "HOST", "127.0.0.1", PASSWORD)
    store_secret(PROJECT, "PORT", "8080", PASSWORD)


def test_dump_env_format(seeded_project, tmp_path):
    runner = CliRunner()
    out = str(tmp_path / "out.env")
    result = runner.invoke(
        export_group,
        ["dump", PROJECT, out, "--format", "env"],
        input=f"{PASSWORD}\n",
    )
    assert result.exit_code == 0, result.output
    assert "exported" in result.output
    content = Path(out).read_text()
    assert "HOST=127.0.0.1" in content


def test_dump_json_format(seeded_project, tmp_path):
    runner = CliRunner()
    out = str(tmp_path / "out.json")
    result = runner.invoke(
        export_group,
        ["dump", PROJECT, out, "--format", "json", "--export-password", "xpass"],
        input=f"{PASSWORD}\n",
    )
    assert result.exit_code == 0, result.output
    bundle = json.loads(Path(out).read_text())
    assert bundle["project"] == PROJECT


def test_dump_empty_project_exits_nonzero(tmp_path):
    runner = CliRunner()
    result = runner.invoke(
        export_group,
        ["dump", "ghost_project", str(tmp_path / "out.env")],
        input=f"{PASSWORD}\n",
    )
    assert result.exit_code != 0


def test_load_env_file(seeded_project, tmp_path):
    env_file = tmp_path / "import.env"
    env_file.write_text("NEW_VAR=hello\nANOTHER=world\n")
    runner = CliRunner()
    result = runner.invoke(
        export_group,
        ["load", str(env_file), PROJECT],
        input=f"{PASSWORD}\n",
    )
    assert result.exit_code == 0, result.output
    assert "Imported 2" in result.output


def test_load_no_new_secrets_message(seeded_project, tmp_path):
    env_file = tmp_path / "existing.env"
    env_file.write_text("HOST=other\n")
    runner = CliRunner()
    result = runner.invoke(
        export_group,
        ["load", str(env_file), PROJECT],
        input=f"{PASSWORD}\n",
    )
    assert result.exit_code == 0
    assert "No new secrets" in result.output


def test_load_missing_file_exits_nonzero(tmp_path):
    runner = CliRunner()
    result = runner.invoke(
        export_group,
        ["load", str(tmp_path / "ghost.env"), PROJECT],
        input=f"{PASSWORD}\n",
    )
    assert result.exit_code != 0
