"""CLI commands for managing per-directory access control."""

import os
import click
from pathlib import Path

from envault.access import grant_access, revoke_access, list_access, is_allowed


@click.group("access")
def access_group():
    """Manage per-directory access control for secrets."""


@access_group.command("grant")
@click.argument("secret_name")
@click.argument("allowed_dir", default=None, required=False)
@click.option("--vault-dir", default=None, help="Override vault access control directory.")
def cmd_grant(secret_name: str, allowed_dir: str, vault_dir: str):
    """Grant a directory access to SECRET_NAME.

    ALLOWED_DIR defaults to the current working directory.
    """
    target = allowed_dir or os.getcwd()
    resolved = str(Path(target).resolve())
    grant_access(secret_name, resolved, directory=vault_dir)
    click.echo(f"Granted access to '{secret_name}' for directory: {resolved}")


@access_group.command("revoke")
@click.argument("secret_name")
@click.argument("allowed_dir", default=None, required=False)
@click.option("--vault-dir", default=None, help="Override vault access control directory.")
def cmd_revoke(secret_name: str, allowed_dir: str, vault_dir: str):
    """Revoke a directory's access to SECRET_NAME.

    ALLOWED_DIR defaults to the current working directory.
    """
    target = allowed_dir or os.getcwd()
    resolved = str(Path(target).resolve())
    revoke_access(secret_name, resolved, directory=vault_dir)
    click.echo(f"Revoked access to '{secret_name}' for directory: {resolved}")


@access_group.command("list")
@click.argument("secret_name")
@click.option("--vault-dir", default=None, help="Override vault access control directory.")
def cmd_list_access(secret_name: str, vault_dir: str):
    """List all directories allowed to access SECRET_NAME."""
    dirs = list_access(secret_name, directory=vault_dir)
    if not dirs:
        click.echo(f"No access restrictions set for '{secret_name}' (open access).")
    else:
        click.echo(f"Directories with access to '{secret_name}':")
        for d in dirs:
            click.echo(f"  {d}")


@access_group.command("check")
@click.argument("secret_name")
@click.option("--dir", "check_dir", default=None, help="Directory to check (default: cwd).")
@click.option("--vault-dir", default=None, help="Override vault access control directory.")
def cmd_check(secret_name: str, check_dir: str, vault_dir: str):
    """Check whether a directory is allowed to access SECRET_NAME."""
    target = check_dir or os.getcwd()
    resolved = str(Path(target).resolve())
    allowed = is_allowed(secret_name, requesting_dir=resolved, directory=vault_dir)
    status = click.style("ALLOWED", fg="green") if allowed else click.style("DENIED", fg="red")
    click.echo(f"Access for '{resolved}' to '{secret_name}': {status}")
    raise SystemExit(0 if allowed else 1)
