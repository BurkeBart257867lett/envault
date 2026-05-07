"""Tests for envault.search — key and value search across projects."""

from __future__ import annotations

import pytest

import envault.vault as vault_mod
from envault.search import SearchResult, search_keys, search_values
from envault.vault import store_secret


PASSWORD = "hunter2"


@pytest.fixture()
def isolated_vault(tmp_path, monkeypatch):
    """Redirect vault storage to a temporary directory."""
    vault_root = tmp_path / ".envault"
    vault_root.mkdir()
    monkeypatch.setattr(
        vault_mod,
        "_vault_path",
        lambda project: vault_root / project,
    )
    return vault_root


@pytest.fixture()
def seeded(isolated_vault):
    """Populate two projects with a handful of secrets."""
    store_secret("alpha", "DB_HOST", "localhost", PASSWORD)
    store_secret("alpha", "DB_PASS", "s3cr3t", PASSWORD)
    store_secret("alpha", "API_KEY", "abc123", PASSWORD)
    store_secret("beta", "DB_HOST", "prod.db", PASSWORD)
    store_secret("beta", "REDIS_URL", "redis://localhost", PASSWORD)
    return isolated_vault


# ---------------------------------------------------------------------------
# search_keys — glob
# ---------------------------------------------------------------------------

def test_search_keys_glob_all_projects(seeded):
    results = search_keys("DB_*")
    keys = {(r.project, r.key) for r in results}
    assert ("alpha", "DB_HOST") in keys
    assert ("alpha", "DB_PASS") in keys
    assert ("beta", "DB_HOST") in keys


def test_search_keys_glob_single_project(seeded):
    results = search_keys("DB_*", project="alpha")
    assert all(r.project == "alpha" for r in results)
    assert len(results) == 2


def test_search_keys_no_match_returns_empty(seeded):
    results = search_keys("NONEXISTENT_*")
    assert results == []


def test_search_keys_exact_match(seeded):
    results = search_keys("API_KEY")
    assert len(results) == 1
    assert results[0].key == "API_KEY"
    assert results[0].project == "alpha"


# ---------------------------------------------------------------------------
# search_keys — regex
# ---------------------------------------------------------------------------

def test_search_keys_regex(seeded):
    results = search_keys(r"^DB_", use_regex=True)
    assert len(results) == 3  # DB_HOST x2, DB_PASS x1


def test_search_keys_regex_no_match(seeded):
    results = search_keys(r"^ZZZNOPE", use_regex=True)
    assert results == []


# ---------------------------------------------------------------------------
# search_values
# ---------------------------------------------------------------------------

def test_search_values_finds_substring(seeded):
    results = search_values("localhost", PASSWORD)
    keys = {(r.project, r.key) for r in results}
    assert ("alpha", "DB_HOST") in keys
    assert ("beta", "REDIS_URL") in keys


def test_search_values_populates_value_field(seeded):
    results = search_values("s3cr3t", PASSWORD)
    assert len(results) == 1
    assert results[0].value == "s3cr3t"


def test_search_values_case_insensitive(seeded):
    results = search_values("LOCALHOST", PASSWORD, case_sensitive=False)
    assert len(results) >= 2


def test_search_values_wrong_password_skips_silently(seeded):
    # Should not raise; secrets simply won't be returned.
    results = search_values("localhost", "wrongpassword")
    assert results == []


def test_search_values_single_project(seeded):
    results = search_values("localhost", PASSWORD, project="beta")
    assert all(r.project == "beta" for r in results)


def test_search_result_repr():
    r = SearchResult(project="alpha", key="DB_HOST")
    assert "alpha" in repr(r)
    assert "DB_HOST" in repr(r)
