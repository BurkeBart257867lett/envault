"""CLI commands for diffing snapshots."""
import sys
import click

from envault.diff import diff_snapshots, diff_snapshot_live
from envault.cli import get_password
from envault.snapshot import list_snapshots, SnapshotError


@click.group(name="diff")
def diff_group():
    """Compare secrets between snapshots or live vault."""


@diff_group.command("snapshots")
@click.argument("project")
@click.argument("snapshot_a")
@click.argument("snapshot_b")
@click.option("--password", envvar="ENVAULT_PASSWORD", default=None, help="Vault password.")
def cmd_diff_snapshots(project: str, snapshot_a: str, snapshot_b: str, password: str):
    """Compare two snapshots for a PROJECT."""
    if not password:
        password = get_password(confirm=False)
    try:
        result = diff_snapshots(project, snapshot_a, snapshot_b, password)
    except SnapshotError as exc:
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)

    if not result.has_changes:
        click.echo("No differences found.")
        return

    _print_diff(result)


@diff_group.command("live")
@click.argument("project")
@click.argument("snapshot_id")
@click.option("--password", envvar="ENVAULT_PASSWORD", default=None, help="Vault password.")
def cmd_diff_live(project: str, snapshot_id: str, password: str):
    """Compare SNAPSHOT_ID against the live vault for PROJECT."""
    if not password:
        password = get_password(confirm=False)
    try:
        result = diff_snapshot_live(project, snapshot_id, password)
    except SnapshotError as exc:
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)

    if not result.has_changes:
        click.echo("No differences found between snapshot and live vault.")
        return

    _print_diff(result)


def _print_diff(result):
    click.echo(f"Project: {result.project}")
    for key in result.added:
        click.echo(click.style(f"  + {key}", fg="green"))
    for key in result.removed:
        click.echo(click.style(f"  - {key}", fg="red"))
    for key in result.changed:
        click.echo(click.style(f"  ~ {key}", fg="yellow"))
