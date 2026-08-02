#!/usr/bin/env python3
"""Append independently validated Rumble result records as immutable raw facts."""

from __future__ import annotations

import argparse
from pathlib import Path

from common import read_json, write_json
from validate import AcceptedResult, ValidationError, validate_batch


def raw_path(root: Path, completed_at: str, digest: str) -> Path:
    date = completed_at[:10].split("-")
    if len(date) != 3 or not all(part.isdigit() for part in date):
        raise ValidationError("completedAt must start with an ISO-8601 date")
    return root / "results" / "raw" / date[0] / date[1] / f"{digest}.json"


def existing_battle_ids(root: Path) -> set[str]:
    result: set[str] = set()
    for relative in ("results/raw", "results/rollups"):
        for path in (root / relative).rglob("*.json") if (root / relative).exists() else []:
            value = read_json(path)
            records = value.get("results", []) if relative.endswith("rollups") else [value]
            result.update(str(record.get("battleId")) for record in records)
    return result


def ingest(root: Path, envelope: object, *, account: str) -> tuple[list[str], list[str]]:
    """Persist valid records while reporting every rejected record."""
    accepted, rejected = validate_batch(root, envelope, account=account)
    seen = existing_battle_ids(root)
    paths: list[str] = []
    for item in accepted:
        if item.record["battleId"] in seen:
            rejected.append(f"battleId {item.record['battleId']}: rejected: duplicate battleId already retained")
            continue
        path = raw_path(root, str(item.record["completedAt"]), item.digest)
        if path.exists():
            rejected.append(f"battleId {item.record['battleId']}: rejected: duplicate payload hash")
            continue
        write_json(path, item.record)
        paths.append(path.relative_to(root).as_posix())
        seen.add(item.record["battleId"])
    return paths, rejected


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--account", required=True)
    parser.add_argument("--input", type=Path, required=True)
    arguments = parser.parse_args()
    try:
        paths, rejected = ingest(arguments.root.resolve(), read_json(arguments.input), account=arguments.account)
    except (OSError, ValueError, ValidationError) as error:
        print(f"submission rejected: {error}")
        return 1
    print("\n".join([f"accepted: {path}" for path in paths] + rejected))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
