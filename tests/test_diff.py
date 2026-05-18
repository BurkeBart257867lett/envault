"""Tests for envault.diff (snapshot diffing)."""
import pytest
from unittest.mock import patch

from envault.diff import (
    SecretDiff,
    _compute_diff,
    diff_snapshot_live,
    diff_snapshots,
)
from envault.snapshot import SnapshotError


# ---------------------------------------------------------------------------
# _compute_diff unit tests (no I/O)
# ---------------------------------------------------------------------------

def test_compute_diff_no_changes():
    d = _compute_diff("proj", {"A": b"1", "B": b"2"}, {"A": b"1", "B": b"2"})
    assert not d.has_changes
    assert d.added == []
    assert d.removed == []
    assert d.changed == []


def test_compute_diff_added():
    d = _compute_diff("proj", {"A": b"1"}, {"A": b"1", "B": b"2"})
    assert d.added == ["B"]
    assert d.removed == []
    assert d.changed == []
    assert d.has_changes


def test_compute_diff_removed():
    d = _compute_diff("proj", {"A": b"1", "B": b"2"}, {"A": b"1"})
    assert d.removed == ["B"]
    assert d.added == []
    assert d.changed == []


def test_compute_diff_changed():
    d = _compute_diff("proj", {"A": b"old"}, {"A": b"new"})
    assert d.changed == ["A"]
    assert d.added == []
    assert d.removed == []


def test_compute_diff_sorted_output():
    before = {"Z": b"1", "A": b"1", "M": b"1"}
    after = {"Z": b"2", "B": b"1"}
    d = _compute_diff("proj", before, after)
    assert d.added == ["B"]
    assert d.removed == ["A", "M"]
    assert d.changed == ["Z"]


def test_secret_diff_repr():
    d = SecretDiff(project="myapp", added=["X"], removed=[], changed=["Y"])
    r = repr(d)
    assert "myapp" in r
    assert "X" in r


# ---------------------------------------------------------------------------
# diff_snapshots — mock _load_snapshot_secrets
# ---------------------------------------------------------------------------

_MOCK_A = {"DB_URL": b"postgres://old", "SECRET": b"abc"}
_MOCK_B = {"DB_URL": b"postgres://new", "TOKEN": b"xyz"}


def test_diff_snapshots_delegates_to_compute(tmp_path):
    with patch("envault.diff._load_snapshot_secrets") as mock_load:
        mock_load.side_effect = [_MOCK_A, _MOCK_B]
        result = diff_snapshots("myapp", "snap1", "snap2", "pass")

    assert result.project == "myapp"
    assert result.added == ["TOKEN"]
    assert result.removed == ["SECRET"]
    assert result.changed == ["DB_URL"]


# ---------------------------------------------------------------------------
# diff_snapshot_live — mock _load_snapshot_secrets + list_secrets/load_secret
# ---------------------------------------------------------------------------

def test_diff_snapshot_live_no_changes():
    live_data = {"KEY": b"value"}
    with patch("envault.diff._load_snapshot_secrets", return_value=live_data), \
         patch("envault.diff.list_secrets", return_value=["KEY"]), \
         patch("envault.diff.load_secret", return_value=b"value"):
        result = diff_snapshot_live("proj", "snap1", "pass")

    assert not result.has_changes


def test_diff_snapshot_live_detects_new_live_key():
    snap_data = {"KEY": b"value"}
    with patch("envault.diff._load_snapshot_secrets", return_value=snap_data), \
         patch("envault.diff.list_secrets", return_value=["KEY", "NEW"]), \
         patch("envault.diff.load_secret", side_effect=[b"value", b"fresh"]):
        result = diff_snapshot_live("proj", "snap1", "pass")

    assert result.added == ["NEW"]
    assert result.removed == []


def test_diff_snapshot_live_load_error_marks_unreadable():
    snap_data = {"KEY": b"value"}
    with patch("envault.diff._load_snapshot_secrets", return_value=snap_data), \
         patch("envault.diff.list_secrets", return_value=["KEY"]), \
         patch("envault.diff.load_secret", side_effect=Exception("bad decrypt")):
        result = diff_snapshot_live("proj", "snap1", "pass")
    # unreadable vs value => changed
    assert result.changed == ["KEY"]
