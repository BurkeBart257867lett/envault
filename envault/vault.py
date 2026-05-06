"""Core vault operations: store and retrieve encrypted .env files."""

import json
import os
from pathlib import Path
from typing import Dict

from envault.crypto import decrypt, encode_token, decode_token, encrypt

VAULT_DIR = Path.home() / ".envault" / "vaults"
META_FILENAME = "meta.json"


def _vault_path(project: str) -> Path:
    return VAULT_DIR / project


def _ensure_vault_dir(project: str) -> Path:
    path = _vault_path(project)
    path.mkdir(parents=True, exist_ok=True)
    return path


def store_secret(project: str, env_name: str, plaintext: str, password: str) -> None:
    """Encrypt and store a secret for the given project and env name."""
    vault = _ensure_vault_dir(project)
    token = encrypt(plaintext, password)
    secret_file = vault / f"{env_name}.enc"
    secret_file.write_text(encode_token(token))


def load_secret(project: str, env_name: str, password: str) -> str:
    """Load and decrypt a secret for the given project and env name."""
    vault = _vault_path(project)
    secret_file = vault / f"{env_name}.enc"
    if not secret_file.exists():
        raise FileNotFoundError(f"No secret '{env_name}' found for project '{project}'.")
    encoded = secret_file.read_text().strip()
    return decrypt(decode_token(encoded), password)


def list_secrets(project: str) -> list[str]:
    """Return a list of stored secret names for the given project."""
    vault = _vault_path(project)
    if not vault.exists():
        return []
    return [f.stem for f in vault.glob("*.enc")]


def delete_secret(project: str, env_name: str) -> bool:
    """Delete a stored secret. Returns True if deleted, False if not found."""
    secret_file = _vault_path(project) / f"{env_name}.enc"
    if secret_file.exists():
        secret_file.unlink()
        return True
    return False


def list_projects() -> list[str]:
    """Return all known project names in the vault directory."""
    if not VAULT_DIR.exists():
        return []
    return [d.name for d in VAULT_DIR.iterdir() if d.is_dir()]
