"""Secret rotation: re-encrypt all secrets in a project with a new password."""

from __future__ import annotations

from typing import Optional

from .vault import _vault_path, list_secrets, load_secret, store_secret


class RotationError(Exception):
    """Raised when rotation fails partway through."""


def rotate_secrets(
    project: str,
    old_password: str,
    new_password: str,
    *,
    dry_run: bool = False,
) -> list[str]:
    """Re-encrypt every secret in *project* from *old_password* to *new_password*.

    Returns a list of secret names that were rotated.
    Raises :class:`RotationError` if any secret cannot be decrypted with the
    old password (rotation is aborted before any writes in that case).
    """
    names = list_secrets(project)
    if not names:
        return []

    # --- validation pass: decrypt everything first so we don't corrupt the vault ---
    plaintext: dict[str, str] = {}
    for name in names:
        try:
            plaintext[name] = load_secret(project, name, old_password)
        except Exception as exc:
            raise RotationError(
                f"Failed to decrypt '{name}' with the old password: {exc}"
            ) from exc

    if dry_run:
        return list(names)

    # --- write pass: re-encrypt with new password ---
    rotated: list[str] = []
    for name, value in plaintext.items():
        store_secret(project, name, value, new_password)
        rotated.append(name)

    return rotated
