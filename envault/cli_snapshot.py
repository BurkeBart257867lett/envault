"""CLI commands for snapshot management."""

from __future__ import annotations

import sys
import click

from envault.cli import get_password
from envault.snapshot import SnapshotError, create_snapshot, list_snapshots, restore_snapshot


@click.group(name="snapshot")
def snapshot_group() -> None:
    """Create and restore secret snapshots."""


@snapshot_group.command("create")
@click.argument("project")
@click.option("--label", "-l", default=None, help="Human-readable label for the snapshot.")
@click.option("--snapshot-password", envvar="ENVAULT_SNAP_PASSWORD", default=None,
              help="Separate password to encrypt the snapshot (defaults to vault password).")
def cmd_create(project: str, label: str | None, snapshot_password: str | None) -> None:
    """Snapshot all secrets for PROJECT."""
    password = get_password(confirm=False)
    try:
        path = create_snapshot(project, password, label=label, snapshot_password=snapshot_password)
        click.echo(f"Snapshot saved: {path.name}")
    except SnapshotError as exc:
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)


@snapshot_group.command("list")
@click.argument("project")
@click.option("--verbose", "-v", is_flag=True, default=False,
              help="Show additional snapshot metadata.")
def cmd_list(project: str, verbose: bool) -> None:
    """List available snapshots for PROJECT."""
    snaps = list_snapshots(project)
    if not snaps:
        click.echo("No snapshots found.")
        return
    for s in snaps:
        label = s.get("label") or "(no label)"
        line = f"{s['file']}  ts={s['ts']}  label={label}"
        if verbose:
            key_count = s.get("key_count")
            if key_count is not None:
                line += f"  keys={key_count}"
        click.echo(line)


@snapshot_group.command("restore")
@click.argument("project")
@click.argument("snapshot_file")
@click.option("--overwrite", is_flag=True, default=False,
              help="Overwrite existing secrets with snapshot values.")
@click.option("--snapshot-password", envvar="ENVAULT_SNAP_PASSWORD", default=None,
              help="Password used when the snapshot was created.")
def cmd_restore(
    project: str,
    snapshot_file: str,
    overwrite: bool,
    snapshot_password: str | None,
) -> None:
    """Restore secrets from SNAPSHOT_FILE into PROJECT."""
    password = get_password(confirm=False)
    try:
        restored = restore_snapshot(
            project, snapshot_file, password,
            snapshot_password=snapshot_password,
            overwrite=overwrite,
        )
    except SnapshotError as exc:
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)

    if not restored:
        click.echo("Nothing restored (all keys already exist; use --overwrite to force).")
    else:
        click.echo(f"Restored {len(restored)} secret(s): {', '.join(restored)}")
