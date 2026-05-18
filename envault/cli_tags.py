"""CLI commands for managing secret tags."""

from __future__ import annotations

import sys

import click

from envault import tags as tag_lib


@click.group(name="tags")
def tags_group() -> None:
    """Manage tags on secrets."""


@tags_group.command("add")
@click.argument("project")
@click.argument("key")
@click.argument("tag")
def cmd_add(project: str, key: str, tag: str) -> None:
    """Add TAG to KEY in PROJECT."""
    tag_lib.add_tag(project, key, tag)
    click.echo(f"Tagged '{key}' with '{tag}' in project '{project}'.")


@tags_group.command("remove")
@click.argument("project")
@click.argument("key")
@click.argument("tag")
def cmd_remove(project: str, key: str, tag: str) -> None:
    """Remove TAG from KEY in PROJECT."""
    tag_lib.remove_tag(project, key, tag)
    click.echo(f"Removed tag '{tag}' from '{key}' in project '{project}'.")


@tags_group.command("list")
@click.argument("project")
@click.argument("key")
def cmd_list(project: str, key: str) -> None:
    """List all tags on KEY in PROJECT."""
    result = tag_lib.get_tags(project, key)
    if not result:
        click.echo(f"No tags on '{key}' in project '{project}'.")
        sys.exit(0)
    for t in result:
        click.echo(t)


@tags_group.command("find")
@click.argument("project")
@click.argument("tag")
def cmd_find(project: str, tag: str) -> None:
    """Find all keys in PROJECT that have TAG."""
    keys = tag_lib.list_tagged(project, tag)
    if not keys:
        click.echo(f"No secrets tagged '{tag}' in project '{project}'.")
        sys.exit(0)
    for k in keys:
        click.echo(k)


@tags_group.command("show")
@click.argument("project")
def cmd_show(project: str) -> None:
    """Show all tag assignments in PROJECT."""
    mapping = tag_lib.all_tags(project)
    if not mapping:
        click.echo(f"No tags defined in project '{project}'.")
        sys.exit(0)
    for key, tag_list in sorted(mapping.items()):
        click.echo(f"{key}: {', '.join(tag_list)}")


@tags_group.command("clear")
@click.argument("project")
@click.option("--key", default=None, help="Clear tags only for this key.")
def cmd_clear(project: str, key: str | None) -> None:
    """Clear tags in PROJECT (optionally scoped to KEY)."""
    tag_lib.clear_tags(project, key)
    scope = f"key '{key}'" if key else "all keys"
    click.echo(f"Cleared tags for {scope} in project '{project}'.")
