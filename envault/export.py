"""Export and import functionality for envault secrets."""

import json
import os
from pathlib import Path
from typing import Optional

from envault.vault import list_secrets, load_secret, store_secret
from envault.crypto import derive_key, encrypt, decrypt, encode_token, decode_token


def export_secrets(
    project: str,
    password: str,
    output_path: str,
    export_password: Optional[str] = None,
    fmt: str = "env",
) -> None:
    """Export all secrets for a project to a file.

    Args:
        project: Project name to export secrets from.
        password: Master vault password.
        output_path: Destination file path.
        export_password: Optional separate password to encrypt the export file.
        fmt: Export format — 'env' (plain .env) or 'json' (encrypted bundle).
    """
    keys = list_secrets(project)
    if not keys:
        raise ValueError(f"No secrets found for project '{project}'.")

    secrets = {}
    for key in keys:
        value = load_secret(project, key, password)
        secrets[key] = value

    if fmt == "env":
        lines = [f"{k}={v}\n" for k, v in secrets.items()]
        Path(output_path).write_text("".join(lines), encoding="utf-8")

    elif fmt == "json":
        if not export_password:
            raise ValueError("export_password is required for JSON format.")
        plaintext = json.dumps(secrets).encode("utf-8")
        exp_key = derive_key(export_password)
        token = encode_token(encrypt(plaintext, exp_key))
        bundle = {"project": project, "data": token}
        Path(output_path).write_text(json.dumps(bundle, indent=2), encoding="utf-8")

    else:
        raise ValueError(f"Unknown format '{fmt}'. Use 'env' or 'json'.")


def import_secrets(
    input_path: str,
    project: str,
    password: str,
    export_password: Optional[str] = None,
    overwrite: bool = False,
) -> list:
    """Import secrets from a file into the vault.

    Returns list of imported key names.
    """
    path = Path(input_path)
    if not path.exists():
        raise FileNotFoundError(f"Import file not found: {input_path}")

    suffix = path.suffix.lower()

    if suffix == ".env":
        secrets = {}
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, _, v = line.partition("=")
            secrets[k.strip()] = v.strip()

    elif suffix == ".json":
        if not export_password:
            raise ValueError("export_password is required for JSON import.")
        bundle = json.loads(path.read_text(encoding="utf-8"))
        exp_key = derive_key(export_password)
        plaintext = decrypt(decode_token(bundle["data"]), exp_key)
        secrets = json.loads(plaintext.decode("utf-8"))

    else:
        raise ValueError(f"Unsupported file extension '{suffix}'. Use .env or .json.")

    existing = set(list_secrets(project))
    imported = []
    for k, v in secrets.items():
        if k in existing and not overwrite:
            continue
        store_secret(project, k, v, password)
        imported.append(k)

    return imported
