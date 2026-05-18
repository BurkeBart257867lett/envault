"""CLI integration tests for the tags sub-commands."""

from __future__ import annotations

import pytest
from click.testing import CliRunner

from envault.cli_tags import tags_group
import envault.vault as vault_mod
import envault.tags as tags_mod


@pytest.fixture()
def runner():
    return CliRunner(mix_stderr=False)


@pytest.fixture()
def isolated_vault(tmp_path, monkeypatch):
    monkeypatch.setattr(vault_mod, "_VAULT_ROOT", tmp_path)
    monkeypatch.setattr(tags_mod, "_vault_path", vault_mod._vault_path)
    return tmp_path


def test_add_and_list_tags(runner, isolated_vault):
    result = runner.invoke(tags_group, ["add", "proj", "DB_PASS", "database"])
    assert result.exit_code == 0
    assert "Tagged" in result.output

    result = runner.invoke(tags_group, ["list", "proj", "DB_PASS"])
    assert result.exit_code == 0
    assert "database" in result.output


def test_list_no_tags_exits_zero(runner, isolated_vault):
    result = runner.invoke(tags_group, ["list", "proj", "MISSING"])
    assert result.exit_code == 0
    assert "No tags" in result.output


def test_remove_tag(runner, isolated_vault):
    runner.invoke(tags_group, ["add", "proj", "KEY", "mytag"])
    result = runner.invoke(tags_group, ["remove", "proj", "KEY", "mytag"])
    assert result.exit_code == 0
    assert "Removed" in result.output

    result = runner.invoke(tags_group, ["list", "proj", "KEY"])
    assert "No tags" in result.output


def test_find_tagged_keys(runner, isolated_vault):
    runner.invoke(tags_group, ["add", "proj", "DB_PASS", "db"])
    runner.invoke(tags_group, ["add", "proj", "DB_HOST", "db"])
    result = runner.invoke(tags_group, ["find", "proj", "db"])
    assert result.exit_code == 0
    assert "DB_PASS" in result.output
    assert "DB_HOST" in result.output


def test_find_no_match_exits_zero(runner, isolated_vault):
    result = runner.invoke(tags_group, ["find", "proj", "ghost"])
    assert result.exit_code == 0
    assert "No secrets" in result.output


def test_show_all_tags(runner, isolated_vault):
    runner.invoke(tags_group, ["add", "proj", "K1", "t1"])
    runner.invoke(tags_group, ["add", "proj", "K2", "t2"])
    result = runner.invoke(tags_group, ["show", "proj"])
    assert result.exit_code == 0
    assert "K1" in result.output
    assert "K2" in result.output


def test_show_empty_project_exits_zero(runner, isolated_vault):
    result = runner.invoke(tags_group, ["show", "empty_proj"])
    assert result.exit_code == 0
    assert "No tags" in result.output


def test_clear_all_tags(runner, isolated_vault):
    runner.invoke(tags_group, ["add", "proj", "K1", "t1"])
    result = runner.invoke(tags_group, ["clear", "proj"])
    assert result.exit_code == 0
    assert "Cleared" in result.output

    result = runner.invoke(tags_group, ["show", "proj"])
    assert "No tags" in result.output


def test_clear_single_key_tags(runner, isolated_vault):
    runner.invoke(tags_group, ["add", "proj", "K1", "t1"])
    runner.invoke(tags_group, ["add", "proj", "K2", "t2"])
    result = runner.invoke(tags_group, ["clear", "proj", "--key", "K1"])
    assert result.exit_code == 0

    result = runner.invoke(tags_group, ["show", "proj"])
    assert "K1" not in result.output
    assert "K2" in result.output
