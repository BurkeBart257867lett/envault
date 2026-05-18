"""Main CLI entry-point for envault."""
import sys
import click

from envault.vault import store_secret, load_secret, list_secrets, delete_secret
from envault.access import check_access
from envault.audit import log_event


def get_password(confirm: bool = False) -> str:
    """Prompt for a vault password, optionally asking twice for confirmation."""
    password = click.prompt("Vault password", hide_input=True)
    if confirm:
        password2 = click.prompt("Confirm password", hide_input=True)
        if password != password2:
            click.echo("Passwords do not match.", err=True)
            sys.exit(1)
    return password


@click.group()
def cli():
    """envault — local encrypted secrets manager."""


@cli.command("set")
@click.argument("project")
@click.argument("key")
@click.argument("value")
@click.option("--password", envvar="ENVAULT_PASSWORD", default=None)
def cmd_set(project: str, key: str, value: str, password: str):
    """Store a secret KEY=VALUE for PROJECT."""
    if not check_access(project):
        click.echo(f"Access denied for project '{project}'.", err=True)
        sys.exit(1)
    if not password:
        password = get_password(confirm=False)
    store_secret(project, key, value.encode(), password)
    log_event("set", project=project, key=key)
    click.echo(f"Stored {key} for {project}.")


@cli.command("get")
@click.argument("project")
@click.argument("key")
@click.option("--password", envvar="ENVAULT_PASSWORD", default=None)
def cmd_get(project: str, key: str, password: str):
    """Retrieve secret KEY for PROJECT."""
    if not check_access(project):
        click.echo(f"Access denied for project '{project}'.", err=True)
        sys.exit(1)
    if not password:
        password = get_password(confirm=False)
    try:
        value = load_secret(project, key, password)
    except FileNotFoundError:
        click.echo(f"Secret '{key}' not found in project '{project}'.", err=True)
        sys.exit(1)
    log_event("get", project=project, key=key)
    click.echo(value.decode())


@cli.command("list")
@click.argument("project")
def cmd_list(project: str):
    """List secret keys stored for PROJECT."""
    if not check_access(project):
        click.echo(f"Access denied for project '{project}'.", err=True)
        sys.exit(1)
    keys = list_secrets(project)
    if not keys:
        click.echo(f"No secrets stored for '{project}'.")
        return
    for k in keys:
        click.echo(k)


@cli.command("delete")
@click.argument("project")
@click.argument("key")
@click.option("--yes", is_flag=True, help="Skip confirmation.")
def cmd_delete(project: str, key: str, yes: bool):
    """Delete secret KEY from PROJECT."""
    if not check_access(project):
        click.echo(f"Access denied for project '{project}'.", err=True)
        sys.exit(1)
    if not yes:
        click.confirm(f"Delete '{key}' from '{project}'?", abort=True)
    try:
        delete_secret(project, key)
    except FileNotFoundError:
        click.echo(f"Secret '{key}' not found.", err=True)
        sys.exit(1)
    log_event("delete", project=project, key=key)
    click.echo(f"Deleted {key} from {project}.")


# Register sub-command groups
from envault.cli_access import access_group
from envault.cli_export import export_group
from envault.cli_rotate import rotate_group
from envault.cli_audit import audit_group
from envault.cli_snapshot import snapshot_group
from envault.cli_diff import diff_group

cli.add_command(access_group)
cli.add_command(export_group)
cli.add_command(rotate_group)
cli.add_command(audit_group)
cli.add_command(snapshot_group)
cli.add_command(diff_group)

if __name__ == "__main__":
    cli()
