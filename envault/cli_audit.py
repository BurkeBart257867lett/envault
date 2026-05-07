"""CLI sub-commands for viewing the envault audit log."""

import sys

import click

from envault.audit import clear_log, read_log


@click.group("audit", help="View and manage the audit log.")
def audit_group() -> None:  # pragma: no cover
    pass


@audit_group.command("show")
@click.argument("project")
@click.option("--action", default=None, help="Filter by action (set/get/delete/…).")
@click.option("--key", default=None, help="Filter by secret key name.")
@click.option("--tail", default=0, type=int, help="Show only the last N entries.")
def cmd_show(project: str, action: str, key: str, tail: int) -> None:
    """Print audit log entries for PROJECT."""
    records = read_log(project)

    if action:
        records = [r for r in records if r.get("action") == action]
    if key:
        records = [r for r in records if r.get("key") == key]
    if tail > 0:
        records = records[-tail:]

    if not records:
        click.echo("No audit log entries found.")
        return

    for r in records:
        status = "OK" if r.get("success", True) else "FAIL"
        directory = f" [{r['directory']}]" if "directory" in r else ""
        detail = f" — {r['detail']}" if r.get("detail") else ""
        click.echo(
            f"{r['ts']}  {status:4s}  {r['action']:10s}  {r['key']}{directory}{detail}"
        )


@audit_group.command("clear")
@click.argument("project")
@click.confirmation_option(prompt="Delete the entire audit log for this project?")
def cmd_clear(project: str) -> None:
    """Delete the audit log for PROJECT."""
    clear_log(project)
    click.echo(f"Audit log cleared for project '{project}'.")
