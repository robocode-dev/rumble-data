#!/usr/bin/env python3
"""Publish changed current rankings and immutable cumulative month snapshots."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from aggregate import aggregate
from common import read_json, write_json

CURRENT_DATA_DIRECTORIES = ("leaderboard", "bots")


def utc_now() -> datetime:
    """Return the current aware UTC time."""
    return datetime.now(timezone.utc)


def parse_instant(value: str | None) -> datetime:
    """Parse an optional ISO-8601 instant, defaulting to now."""
    if value is None:
        return utc_now()
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("publication time must include a UTC offset")
    return parsed.astimezone(timezone.utc)


def instant_text(value: datetime) -> str:
    """Return the canonical second-precision UTC timestamp."""
    return value.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def month_text(value: datetime) -> str:
    """Return the UTC calendar month for an instant."""
    return value.astimezone(timezone.utc).strftime("%Y-%m")


def next_month(value: str) -> str:
    """Advance a canonical YYYY-MM value by one month."""
    year, month = (int(part) for part in value.split("-"))
    return f"{year + (month == 12):04d}-{1 if month == 12 else month + 1:02d}"


def current_files(root: Path) -> dict[str, bytes]:
    """Return current public ranking files by data-relative path."""
    data_root = root / "site" / "data"
    files: dict[str, bytes] = {}
    for directory_name in CURRENT_DATA_DIRECTORIES:
        directory = data_root / directory_name
        if directory.exists():
            for path in sorted(directory.glob("*.json")):
                files[path.relative_to(data_root).as_posix()] = path.read_bytes()
    return files


def history(root: Path) -> dict[str, Any]:
    """Read publication history or return its initial state."""
    path = root / "site" / "data" / "history.json"
    if not path.exists():
        return {"schemaVersion": 1, "currentMonth": None, "lastUpdatedAt": None, "snapshots": []}
    value = read_json(path)
    if not isinstance(value, dict) or value.get("schemaVersion") != 1 or not isinstance(value.get("snapshots"), list):
        raise ValueError("site/data/history.json has an unsupported schema")
    return value


def write_history(root: Path, value: dict[str, Any]) -> None:
    """Write the public history manifest."""
    write_json(root / "site" / "data" / "history.json", value)


def rollover(root: Path, at: datetime) -> bool:
    """Snapshot each completed UTC month without ever rewriting an archive."""
    manifest = history(root)
    target_month = month_text(at)
    current_month = manifest.get("currentMonth")
    if current_month is None:
        manifest["currentMonth"] = target_month
        write_history(root, manifest)
        return True
    if not isinstance(current_month, str) or len(current_month) != 7:
        raise ValueError("history currentMonth must be YYYY-MM or null")
    if current_month > target_month:
        raise ValueError("publication time precedes history currentMonth")

    changed = False
    while current_month < target_month:
        relative_files = current_files(root)
        snapshot_root = root / "site" / "data" / "snapshots" / current_month
        expected_paths = {snapshot_root / relative for relative in relative_files}
        existing_paths = set(snapshot_root.rglob("*.json")) if snapshot_root.exists() else set()
        if not existing_paths.issubset(expected_paths):
            raise ValueError(f"snapshot {current_month} is immutable: unexpected files exist")
        for relative, content in relative_files.items():
            destination = snapshot_root / relative
            if destination.exists() and destination.read_bytes() != content:
                raise ValueError(f"snapshot {current_month} is immutable: {relative} differs")
            if not destination.exists():
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_bytes(content)

        entry = {"month": current_month, "updatedAt": manifest.get("lastUpdatedAt"), "path": f"data/snapshots/{current_month}"}
        entries = [item for item in manifest["snapshots"] if isinstance(item, dict) and item.get("month") == current_month]
        if entries and entries[0] != entry:
            raise ValueError(f"snapshot manifest entry for {current_month} is immutable")
        if not entries:
            manifest["snapshots"].append(entry)
        current_month = next_month(current_month)
        changed = True

    if manifest.get("currentMonth") != target_month:
        manifest["currentMonth"] = target_month
        changed = True
    if changed:
        manifest["snapshots"] = sorted(manifest["snapshots"], key=lambda item: item["month"])
        write_history(root, manifest)
    return changed


def publish_current(root: Path, at: datetime) -> bool:
    """Regenerate current projections and timestamp only visible ranking changes."""
    before = current_files(root)
    aggregate(root)
    changed = current_files(root) != before
    if changed:
        manifest = history(root)
        manifest["lastUpdatedAt"] = instant_text(at)
        write_history(root, manifest)
    return changed


def main() -> int:
    """Run rollover and optionally regenerate current rankings."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--at", help="ISO-8601 publication time; defaults to the current UTC time")
    parser.add_argument("--rollover-only", action="store_true")
    arguments = parser.parse_args()
    root = arguments.root.resolve()
    at = parse_instant(arguments.at)
    rolled_over = rollover(root, at)
    ranking_changed = False if arguments.rollover_only else publish_current(root, at)
    print(f"rollover_changed={str(rolled_over).lower()}")
    print(f"ranking_changed={str(ranking_changed).lower()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
