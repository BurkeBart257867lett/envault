"""Tests for per-directory access control."""

import json
import os
import pytest
from pathlib import Path

from envault.access import (
    grant_access,
    revoke_access,
    is_allowed,
    list_access,
    ACCESS_FILE,
)


@pytest.fixture
def access_dir(tmp_path):
    """Provide a temporary directory as the access control base."""
    return str(tmp_path)


def test_no_rules_allows_all(access_dir):
    assert is_allowed("MY_SECRET", requesting_dir=access_dir, directory=access_dir) is True


def test_grant_creates_access_file(access_dir):
    grant_access("MY_SECRET", access_dir, directory=access_dir)
    access_file = Path(access_dir) / ACCESS_FILE
    assert access_file.exists()


def test_grant_and_check_allowed(access_dir, tmp_path):
    allowed = str(tmp_path / "project_a")
    Path(allowed).mkdir()
    grant_access("DB_PASS", allowed, directory=access_dir)
    assert is_allowed("DB_PASS", requesting_dir=allowed, directory=access_dir) is True


def test_unlisted_dir_denied_after_grant(access_dir, tmp_path):
    allowed = str(tmp_path / "project_a")
    denied = str(tmp_path / "project_b")
    Path(allowed).mkdir()
    Path(denied).mkdir()
    grant_access("DB_PASS", allowed, directory=access_dir)
    assert is_allowed("DB_PASS", requesting_dir=denied, directory=access_dir) is False


def test_revoke_removes_access(access_dir, tmp_path):
    allowed = str(tmp_path / "project_a")
    Path(allowed).mkdir()
    grant_access("API_KEY", allowed, directory=access_dir)
    revoke_access("API_KEY", allowed, directory=access_dir)
    # After revoke, list is empty → open access again
    assert is_allowed("API_KEY", requesting_dir=allowed, directory=access_dir) is True


def test_list_access_returns_dirs(access_dir, tmp_path):
    dir_a = str(tmp_path / "a")
    dir_b = str(tmp_path / "b")
    Path(dir_a).mkdir()
    Path(dir_b).mkdir()
    grant_access("TOKEN", dir_a, directory=access_dir)
    grant_access("TOKEN", dir_b, directory=access_dir)
    dirs = list_access("TOKEN", directory=access_dir)
    assert str(Path(dir_a).resolve()) in dirs
    assert str(Path(dir_b).resolve()) in dirs


def test_duplicate_grant_not_duplicated(access_dir, tmp_path):
    allowed = str(tmp_path / "project_a")
    Path(allowed).mkdir()
    grant_access("SECRET", allowed, directory=access_dir)
    grant_access("SECRET", allowed, directory=access_dir)
    dirs = list_access("SECRET", directory=access_dir)
    assert dirs.count(str(Path(allowed).resolve())) == 1


def test_access_file_permissions(access_dir, tmp_path):
    allowed = str(tmp_path / "proj")
    Path(allowed).mkdir()
    grant_access("KEY", allowed, directory=access_dir)
    access_file = Path(access_dir) / ACCESS_FILE
    mode = oct(os.stat(access_file).st_mode)[-3:]
    assert mode == "600"
