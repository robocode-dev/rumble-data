"""Shared deterministic JSON and repository helpers for Rumble data tooling."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


def read_json(path: Path) -> Any:
    """Read a UTF-8 JSON value from path."""
    return json.loads(path.read_text(encoding="utf-8"))


def canonical_json(value: Any) -> str:
    """Return the stable JSON representation used for content addressing."""
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def write_json(path: Path, value: Any) -> None:
    """Write an indented canonical JSON document terminated by one newline."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def content_hash(value: Any) -> str:
    """Return a SHA-256 content address for a JSON value."""
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def repository_files(root: Path, relative: str) -> list[Path]:
    """Return sorted JSON files below a repository-relative directory."""
    directory = root / relative
    return sorted(path for path in directory.rglob("*.json") if path.is_file()) if directory.exists() else []
