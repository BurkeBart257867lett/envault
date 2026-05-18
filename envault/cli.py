"""Main CLI entry-point for envault.

Registers all sub-command groups and top-level commands.
"""

from __future__ import annotations

import click

from envault.vault import store_secret, load_secret, list_secrets
from envault.cli_access import access_group
from envault.cli_export import export_group
from envault.cli_rotate import rotate_group
from envault.cli_audit import audit_group
from envault.cli_snapshot import snapshot_group
from envault.cli_diff import diff_group
from envault.cli_tags import tags_group


def get_password(prompt: str = "Vault password") -> str:
    return click.prompt(prompt, hide_input=True)


@click.group()
def cli() -> None:
    """envault — local secrets manager."""


@cli.command("set")
@click.argument("project")
@click.argument("key")
@click.argument("value")
def cmd_set(project: str, key: str, value: str) -> None:
    """Store a secret VALUE for KEY in PROJECT."""
    password = get_password()
    store_secret(project, key, value, password)
    click.echo(f"Stored '{key}' in project '{project}'.")


@cli.command("get")
@click.argument("project")
@click.argument("key")
def cmd_get(project: str, key: str) -> None:
    """Retrieve a secret by KEY from PROJECT."""
    password = get_password()
    value = load_secret(project, key, password)
    if value is None:
        click.echo(f"Key '{key}' not found in project '{project}'.", err=True)
        raise SystemExit(1)
    click.echo(value)


@cli.command("list")
@click.argument("project")
def cmd_list(project: str) -> None:
    """List all secret keys stored in PROJECT."""
    keys = list_secrets(project)
    if not keys:
        click.echo(f"No secrets found in project '{project}'.")
        return
    for key in keys:
        click.echo(key)


cli.add_command(access_group)
cli.add_command(export_group)
cli.add_command(rotate_group)
cli.add_command(audit_group)
cli.add_command(snapshot_group)
cli.add_command(diff_group)
cli.add_command(tags_group)


if __name__ == "__main__":
    cli()
