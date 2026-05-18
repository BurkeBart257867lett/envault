"""Tests for envault.cli_diff Click commands."""
import pytest
from click.testing import CliRunner
from unittest.mock import patch

from envault.cli_diff import diff_group
from envault.diff import SecretDiff
from envault.snapshot import SnapshotError


@pytest.fixture
from click.testing import CliRunner


@pytest.fixture
def runner():
    return CliRunner()


_NO_DIFF = SecretDiff(project="myapp")
_WITH_DIFF = SecretDiff(
    project="myapp",
    added=["NEW_KEY"],
    removed=["OLD_KEY"],
    changed=["CHANGED_KEY"],
)


# ---------------------------------------------------------------------------
# diff snapshots
# ---------------------------------------------------------------------------

def test_diff_snapshots_no_changes(runner):
    with patch("envault.cli_diff.diff_snapshots", return_value=_NO_DIFF):
        result = runner.invoke(
            diff_group,
            ["snapshots", "myapp", "snap1", "snap2", "--password", "secret"],
        )
    assert result.exit_code == 0
    assert "No differences" in result.output


def test_diff_snapshots_with_changes(runner):
    with patch("envault.cli_diff.diff_snapshots", return_value=_WITH_DIFF):
        result = runner.invoke(
            diff_group,
            ["snapshots", "myapp", "snap1", "snap2", "--password", "secret"],
        )
    assert result.exit_code == 0
    assert "+ NEW_KEY" in result.output
    assert "- OLD_KEY" in result.output
    assert "~ CHANGED_KEY" in result.output


def test_diff_snapshots_missing_snapshot_exits_nonzero(runner):
    with patch(
        "envault.cli_diff.diff_snapshots",
        side_effect=SnapshotError("Snapshot not found: snap1"),
    ):
        result = runner.invoke(
            diff_group,
            ["snapshots", "myapp", "snap1", "snap2", "--password", "secret"],
        )
    assert result.exit_code == 1
    assert "Error" in result.output


# ---------------------------------------------------------------------------
# diff live
# ---------------------------------------------------------------------------

def test_diff_live_no_changes(runner):
    with patch("envault.cli_diff.diff_snapshot_live", return_value=_NO_DIFF):
        result = runner.invoke(
            diff_group,
            ["live", "myapp", "snap1", "--password", "secret"],
        )
    assert result.exit_code == 0
    assert "No differences" in result.output


def test_diff_live_with_changes(runner):
    with patch("envault.cli_diff.diff_snapshot_live", return_value=_WITH_DIFF):
        result = runner.invoke(
            diff_group,
            ["live", "myapp", "snap1", "--password", "secret"],
        )
    assert result.exit_code == 0
    assert "+ NEW_KEY" in result.output
    assert "- OLD_KEY" in result.output


def test_diff_live_snapshot_error_exits_nonzero(runner):
    with patch(
        "envault.cli_diff.diff_snapshot_live",
        side_effect=SnapshotError("Snapshot not found: snap99"),
    ):
        result = runner.invoke(
            diff_group,
            ["live", "myapp", "snap99", "--password", "secret"],
        )
    assert result.exit_code == 1
