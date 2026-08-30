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


def normalized_catalog_bots(value: Any) -> list[dict[str, Any]]:
    """Return catalog entries with validated additive team membership."""
    if not isinstance(value, list):
        raise ValueError("catalog bots must be a list")
    bots: list[dict[str, Any]] = []
    for entry in value:
        if not isinstance(entry, dict):
            raise ValueError("each catalog entry must be an object")
        team_members = entry.get("teamMembers", [])
        if not isinstance(team_members, list) or len(team_members) not in (0, 2) or not all(isinstance(member, str) and member for member in team_members):
            raise ValueError("catalog teamMembers must be empty or contain exactly two identities")
        bots.append(entry | {"teamMembers": list(team_members)})

    active: dict[str, dict[str, Any]] = {}
    for entry in bots:
        if entry.get("status") != "active":
            continue
        identity = f"{entry.get('name')} {entry.get('version')}"
        if identity in active:
            raise ValueError(f"duplicate active catalog identity `{identity}`")
        active[identity] = entry
    for team in (entry for entry in active.values() if entry["teamMembers"]):
        for member_identity in team["teamMembers"]:
            member = active.get(member_identity)
            if member is None:
                raise ValueError(f"unknown or inactive team member `{member_identity}`")
            if member["teamMembers"]:
                raise ValueError(f"team member `{member_identity}` cannot be another team")
    return bots
