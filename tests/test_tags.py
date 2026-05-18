"""Unit tests for envault.tags."""

from __future__ import annotations

import pytest

from envault import tags as tag_lib
from envault.vault import _vault_path


@pytest.fixture()
def isolated_vault(tmp_path, monkeypatch):
    """Redirect vault storage to a temporary directory."""
    import envault.vault as vault_mod
    import envault.tags as tags_mod

    monkeypatch.setattr(vault_mod, "_VAULT_ROOT", tmp_path)
    monkeypatch.setattr(tags_mod, "_vault_path", vault_mod._vault_path)
    return tmp_path


def test_get_tags_empty_returns_empty_list(isolated_vault):
    assert tag_lib.get_tags("myproject", "DB_PASS") == []


def test_add_tag_creates_entry(isolated_vault):
    tag_lib.add_tag("myproject", "DB_PASS", "database")
    assert "database" in tag_lib.get_tags("myproject", "DB_PASS")


def test_add_duplicate_tag_is_idempotent(isolated_vault):
    tag_lib.add_tag("myproject", "DB_PASS", "database")
    tag_lib.add_tag("myproject", "DB_PASS", "database")
    assert tag_lib.get_tags("myproject", "DB_PASS").count("database") == 1


def test_add_multiple_tags(isolated_vault):
    tag_lib.add_tag("myproject", "API_KEY", "external")
    tag_lib.add_tag("myproject", "API_KEY", "sensitive")
    result = tag_lib.get_tags("myproject", "API_KEY")
    assert set(result) == {"external", "sensitive"}


def test_remove_tag(isolated_vault):
    tag_lib.add_tag("myproject", "TOKEN", "auth")
    tag_lib.remove_tag("myproject", "TOKEN", "auth")
    assert tag_lib.get_tags("myproject", "TOKEN") == []


def test_remove_nonexistent_tag_is_noop(isolated_vault):
    tag_lib.add_tag("myproject", "TOKEN", "auth")
    tag_lib.remove_tag("myproject", "TOKEN", "missing")
    assert tag_lib.get_tags("myproject", "TOKEN") == ["auth"]


def test_list_tagged_returns_matching_keys(isolated_vault):
    tag_lib.add_tag("myproject", "DB_PASS", "database")
    tag_lib.add_tag("myproject", "DB_HOST", "database")
    tag_lib.add_tag("myproject", "API_KEY", "external")
    result = tag_lib.list_tagged("myproject", "database")
    assert set(result) == {"DB_PASS", "DB_HOST"}


def test_list_tagged_no_match_returns_empty(isolated_vault):
    assert tag_lib.list_tagged("myproject", "nonexistent") == []


def test_all_tags_returns_full_mapping(isolated_vault):
    tag_lib.add_tag("myproject", "K1", "t1")
    tag_lib.add_tag("myproject", "K2", "t2")
    mapping = tag_lib.all_tags("myproject")
    assert mapping == {"K1": ["t1"], "K2": ["t2"]}


def test_clear_tags_for_key(isolated_vault):
    tag_lib.add_tag("myproject", "K1", "t1")
    tag_lib.add_tag("myproject", "K2", "t2")
    tag_lib.clear_tags("myproject", "K1")
    assert tag_lib.get_tags("myproject", "K1") == []
    assert tag_lib.get_tags("myproject", "K2") == ["t2"]


def test_clear_all_tags(isolated_vault):
    tag_lib.add_tag("myproject", "K1", "t1")
    tag_lib.add_tag("myproject", "K2", "t2")
    tag_lib.clear_tags("myproject")
    assert tag_lib.all_tags("myproject") == {}


def test_tags_isolated_between_projects(isolated_vault):
    tag_lib.add_tag("proj_a", "KEY", "shared")
    assert tag_lib.get_tags("proj_b", "KEY") == []
