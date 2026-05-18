"""Tag management for envault secrets.

Allows secrets to be annotated with arbitrary string tags,
enabling filtering and organisation across projects.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional

from envault.vault import _vault_path


def _tags_path(project: str) -> Path:
    """Return path to the tags metadata file for *project*."""
    return _vault_path(project).parent / "tags.json"


def _load_tags(project: str) -> Dict[str, List[str]]:
    """Load tag mapping ``{key: [tag, ...]`` for *project*."""
    path = _tags_path(project)
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _save_tags(project: str, data: Dict[str, List[str]]) -> None:
    path = _tags_path(project)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def add_tag(project: str, key: str, tag: str) -> None:
    """Add *tag* to *key* in *project*.  Duplicate tags are ignored."""
    data = _load_tags(project)
    tags = data.setdefault(key, [])
    if tag not in tags:
        tags.append(tag)
    _save_tags(project, data)


def remove_tag(project: str, key: str, tag: str) -> None:
    """Remove *tag* from *key* in *project*.  No-op if absent."""
    data = _load_tags(project)
    if key in data and tag in data[key]:
        data[key].remove(tag)
        if not data[key]:
            del data[key]
    _save_tags(project, data)


def get_tags(project: str, key: str) -> List[str]:
    """Return all tags for *key* in *project*."""
    return list(_load_tags(project).get(key, []))


def list_tagged(project: str, tag: str) -> List[str]:
    """Return all secret keys in *project* that carry *tag*."""
    return [k for k, tags in _load_tags(project).items() if tag in tags]


def all_tags(project: str) -> Dict[str, List[str]]:
    """Return the full tag mapping for *project*."""
    return dict(_load_tags(project))


def clear_tags(project: str, key: Optional[str] = None) -> None:
    """Remove all tags for *key*, or wipe the entire tag store if *key* is None."""
    if key is None:
        _save_tags(project, {})
    else:
        data = _load_tags(project)
        data.pop(key, None)
        _save_tags(project, data)
