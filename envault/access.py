"""Per-directory access control for envault."""

import json
import os
from pathlib import Path
from typing import Optional

ACCESS_FILE = ".envault_access"


def _access_path(directory: Optional[str] = None) -> Path:
    """Return the path to the access control file for a given directory."""
    base = Path(directory) if directory else Path.cwd()
    return base / ACCESS_FILE


def _load_access(directory: Optional[str] = None) -> dict:
    """Load access rules from the access control file."""
    path = _access_path(directory)
    if not path.exists():
        return {}
    with open(path, "r") as f:
        return json.load(f)


def _save_access(rules: dict, directory: Optional[str] = None) -> None:
    """Persist access rules to the access control file."""
    path = _access_path(directory)
    with open(path, "w") as f:
        json.dump(rules, f, indent=2)
    os.chmod(path, 0o600)


def grant_access(secret_name: str, allowed_dir: str, directory: Optional[str] = None) -> None:
    """Grant access to a secret for a specific directory path."""
    rules = _load_access(directory)
    allowed_dirs = rules.get(secret_name, [])
    resolved = str(Path(allowed_dir).resolve())
    if resolved not in allowed_dirs:
        allowed_dirs.append(resolved)
    rules[secret_name] = allowed_dirs
    _save_access(rules, directory)


def revoke_access(secret_name: str, allowed_dir: str, directory: Optional[str] = None) -> None:
    """Revoke access to a secret for a specific directory path."""
    rules = _load_access(directory)
    allowed_dirs = rules.get(secret_name, [])
    resolved = str(Path(allowed_dir).resolve())
    rules[secret_name] = [d for d in allowed_dirs if d != resolved]
    _save_access(rules, directory)


def is_allowed(secret_name: str, requesting_dir: Optional[str] = None, directory: Optional[str] = None) -> bool:
    """Check whether a requesting directory is allowed to access a secret."""
    rules = _load_access(directory)
    allowed_dirs = rules.get(secret_name, [])
    # If no rules defined, access is open
    if not allowed_dirs:
        return True
    resolved = str(Path(requesting_dir or os.getcwd()).resolve())
    return resolved in allowed_dirs


def list_access(secret_name: str, directory: Optional[str] = None) -> list:
    """List all directories allowed to access a secret."""
    rules = _load_access(directory)
    return rules.get(secret_name, [])
