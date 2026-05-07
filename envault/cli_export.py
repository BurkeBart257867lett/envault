"""CLI commands for exporting and importing secrets."""

import click

from envault.cli import get_password
from envault.export import export_secrets, import_secrets


@click.group("export")
def export_group():
    """Export and import secrets."""


@export_group.command("dump")
@click.argument("project")
@click.argument("output")
@click.option(
    "--format",
    "fmt",
    type=click.Choice(["env", "json"]),
    default="env",
    show_default=True,
    help="Output format.",
)
@click.option("--export-password", default=None, help="Password for JSON encryption.")
def cmd_dump(project: str, output: str, fmt: str, export_password: str):
    """Export all secrets for PROJECT to OUTPUT file."""
    password = get_password(confirm=False)
    if fmt == "json" and not export_password:
        export_password = click.prompt(
            "Export file password", hide_input=True, confirmation_prompt=True
        )
    try:
        export_secrets(project, password, output, export_password=export_password, fmt=fmt)
        click.echo(f"Secrets exported to {output} ({fmt} format).")
    except ValueError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@export_group.command("load")
@click.argument("input_file")
@click.argument("project")
@click.option(
    "--overwrite",
    is_flag=True,
    default=False,
    help="Overwrite existing keys.",
)
@click.option("--export-password", default=None, help="Password used when file was exported.")
def cmd_load(input_file: str, project: str, overwrite: bool, export_password: str):
    """Import secrets from INPUT_FILE into PROJECT."""
    password = get_password(confirm=False)
    if input_file.endswith(".json") and not export_password:
        export_password = click.prompt("Export file password", hide_input=True)
    try:
        imported = import_secrets(
            input_file, project, password, export_password=export_password, overwrite=overwrite
        )
        if imported:
            click.echo(f"Imported {len(imported)} secret(s): {', '.join(imported)}")
        else:
            click.echo("No new secrets imported (use --overwrite to replace existing keys).")
    except (ValueError, FileNotFoundError) as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)
