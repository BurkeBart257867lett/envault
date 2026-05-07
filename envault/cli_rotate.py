"""CLI command group for secret rotation."""

from __future__ import annotations

import click

from .cli import get_password
from .rotate import RotationError, rotate_secrets


@click.group("rotate")
def rotate_group() -> None:
    """Rotate encryption passwords for a project's secrets."""


@rotate_group.command("run")
@click.argument("project")
@click.option(
    "--dry-run",
    is_flag=True,
    default=False,
    help="Show which secrets would be rotated without modifying the vault.",
)
def cmd_rotate(project: str, dry_run: bool) -> None:
    """Re-encrypt all secrets in PROJECT with a new master password."""
    click.echo(f"Rotating secrets for project '{project}'.")

    old_password = get_password(prompt="Current master password")
    if dry_run:
        new_password = old_password  # not used for writes
    else:
        new_password = get_password(prompt="New master password", confirm=True)
        if new_password == old_password:
            click.echo("New password is identical to the old one — nothing to do.")
            raise SystemExit(0)

    try:
        rotated = rotate_secrets(
            project, old_password, new_password, dry_run=dry_run
        )
    except RotationError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1) from exc

    if not rotated:
        click.echo("No secrets found — nothing to rotate.")
        raise SystemExit(0)

    prefix = "Would rotate" if dry_run else "Rotated"
    click.echo(f"{prefix} {len(rotated)} secret(s):")
    for name in rotated:
        click.echo(f"  • {name}")

    if dry_run:
        click.echo("(Dry run — vault was not modified.)")
