"""Search secrets by key pattern or value content across projects."""

from __future__ import annotations

import fnmatch
import re
from typing import Iterator

from envault.vault import _vault_path, list_secrets, load_secret


class SearchResult:
    """Holds a single search hit."""

    def __init__(self, project: str, key: str, value: str | None = None) -> None:
        self.project = project
        self.key = key
        self.value = value  # Only populated when search_values=True

    def __repr__(self) -> str:  # pragma: no cover
        return f"SearchResult(project={self.project!r}, key={self.key!r})"


def _iter_projects() -> Iterator[str]:
    """Yield all project names stored in the vault directory."""
    vault_dir = _vault_path("").parent
    if not vault_dir.exists():
        return
    for child in sorted(vault_dir.iterdir()):
        if child.is_dir():
            yield child.name


def search_keys(
    pattern: str,
    *,
    project: str | None = None,
    use_regex: bool = False,
) -> list[SearchResult]:
    """Return secrets whose *key* matches *pattern*.

    Args:
        pattern: A glob pattern (default) or regex when *use_regex* is True.
        project: Restrict search to a single project directory.
        use_regex: Treat *pattern* as a regular expression.
    """
    projects = [project] if project else list(_iter_projects())
    results: list[SearchResult] = []

    compiled = re.compile(pattern) if use_regex else None

    for proj in projects:
        for key in list_secrets(proj):
            matched = (
                bool(compiled.search(key))
                if compiled
                else fnmatch.fnmatch(key, pattern)
            )
            if matched:
                results.append(SearchResult(project=proj, key=key))

    return results


def search_values(
    substring: str,
    password: str,
    *,
    project: str | None = None,
    case_sensitive: bool = True,
) -> list[SearchResult]:
    """Return secrets whose *decrypted value* contains *substring*.

    Args:
        substring: Plain-text substring to look for in secret values.
        password: Master password used to decrypt secrets.
        project: Restrict search to a single project directory.
        case_sensitive: Whether the substring match is case-sensitive.
    """
    projects = [project] if project else list(_iter_projects())
    results: list[SearchResult] = []
    needle = substring if case_sensitive else substring.lower()

    for proj in projects:
        for key in list_secrets(proj):
            try:
                value = load_secret(proj, key, password)
            except Exception:  # wrong password or corrupted — skip silently
                continue
            haystack = value if case_sensitive else value.lower()
            if needle in haystack:
                results.append(SearchResult(project=proj, key=key, value=value))

    return results
