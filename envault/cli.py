"""Command-line interface for envault.

Provides commands to store, retrieve, list, and delete secrets
from the encrypted vault, with per-directory access control.
"""

import os
import sys
import getpass
import argparse

from envault.vault import (
    store_secret,
    load_secret,
    list_secrets,
    delete_secret,
    export_env,
)


def get_password(confirm: bool = False) -> str:
    """Prompt the user for a vault password.

    Args:
        confirm: If True, ask the user to confirm the password.

    Returns:
        The entered password string.

    Raises:
        SystemExit: If passwords do not match when confirm=True.
    """
    password = getpass.getpass("Vault password: ")
    if confirm:
        password2 = getpass.getpass("Confirm password: ")
        if password != password2:
            print("Error: passwords do not match.", file=sys.stderr)
            sys.exit(1)
    return password


def cmd_set(args: argparse.Namespace) -> None:
    """Handle the 'set' subcommand — store a secret in the vault."""
    value = args.value
    if value is None:
        # Read value from stdin if not provided as argument
        value = getpass.getpass(f"Value for '{args.key}': ")

    password = get_password(confirm=args.new)
    directory = args.dir or os.getcwd()

    store_secret(args.key, value, password, directory=directory)
    print(f"Secret '{args.key}' stored successfully.")


def cmd_get(args: argparse.Namespace) -> None:
    """Handle the 'get' subcommand — retrieve and print a secret."""
    password = get_password()
    directory = args.dir or os.getcwd()

    value = load_secret(args.key, password, directory=directory)
    if value is None:
        print(f"Error: secret '{args.key}' not found.", file=sys.stderr)
        sys.exit(1)

    print(value)


def cmd_list(args: argparse.Namespace) -> None:
    """Handle the 'list' subcommand — list all secret keys for a directory."""
    directory = args.dir or os.getcwd()
    secrets = list_secrets(directory=directory)

    if not secrets:
        print("No secrets stored for this directory.")
    else:
        print(f"Secrets for {directory}:")
        for key in sorted(secrets):
            print(f"  {key}")


def cmd_delete(args: argparse.Namespace) -> None:
    """Handle the 'delete' subcommand — remove a secret from the vault."""
    directory = args.dir or os.getcwd()
    removed = delete_secret(args.key, directory=directory)

    if removed:
        print(f"Secret '{args.key}' deleted.")
    else:
        print(f"Error: secret '{args.key}' not found.", file=sys.stderr)
        sys.exit(1)


def cmd_export(args: argparse.Namespace) -> None:
    """Handle the 'export' subcommand — export secrets as shell export statements."""
    password = get_password()
    directory = args.dir or os.getcwd()

    env_vars = export_env(password, directory=directory)
    if not env_vars:
        print("# No secrets found for this directory.", file=sys.stderr)
        return

    for key, value in sorted(env_vars.items()):
        # Escape single quotes in value for safe shell export
        safe_value = value.replace("'", "'\"'\"'")
        print(f"export {key}='{safe_value}'")


def build_parser() -> argparse.ArgumentParser:
    """Construct and return the argument parser for envault."""
    parser = argparse.ArgumentParser(
        prog="envault",
        description="Encrypted .env secrets manager with per-directory access control.",
    )
    parser.add_argument(
        "--dir",
        metavar="PATH",
        help="Target project directory (defaults to current working directory).",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # set
    p_set = subparsers.add_parser("set", help="Store a secret in the vault.")
    p_set.add_argument("key", help="Secret key name (e.g. DATABASE_URL).")
    p_set.add_argument("value", nargs="?", default=None, help="Secret value (prompted if omitted).")
    p_set.add_argument("--new", action="store_true", help="Confirm password (use when setting up a new vault).")
    p_set.set_defaults(func=cmd_set)

    # get
    p_get = subparsers.add_parser("get", help="Retrieve a secret from the vault.")
    p_get.add_argument("key", help="Secret key name.")
    p_get.set_defaults(func=cmd_get)

    # list
    p_list = subparsers.add_parser("list", help="List all secret keys for a directory.")
    p_list.set_defaults(func=cmd_list)

    # delete
    p_del = subparsers.add_parser("delete", help="Delete a secret from the vault.")
    p_del.add_argument("key", help="Secret key name.")
    p_del.set_defaults(func=cmd_delete)

    # export
    p_export = subparsers.add_parser(
        "export",
        help="Print secrets as shell export statements (eval-friendly).",
    )
    p_export.set_defaults(func=cmd_export)

    return parser


def main() -> None:
    """Entry point for the envault CLI."""
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
