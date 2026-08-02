#!/usr/bin/env python3
"""Validate a result envelope and append each new record as an immutable raw fact."""

from __future__ import annotations

import argparse
from pathlib import Path

from common import read_json, write_json
from validate import ValidationError, validate_envelope


def raw_path(root: Path, completed_at: str, digest: str) -> Path:
    """Return the deterministic raw-fact path for a result record."""
    date = completed_at[:10].split("-")
    if len(date) != 3 or not all(part.isdigit() for part in date):
        raise ValidationError("completedAt must start with an ISO-8601 date")
    return root / "results" / "raw" / date[0] / date[1] / f"{digest}.json"


def existing_battle_ids(root: Path) -> set[str]:
    """Return battle IDs already retained as raw facts."""
    result: set[str] = set()
    for path in (root / "results" / "raw").rglob("*.json") if (root / "results" / "raw").exists() else []:
        result.add(str(read_json(path).get("battleId")))
    for path in (root / "results" / "rollups").rglob("*.json") if (root / "results" / "rollups").exists() else []:
        result.update(str(record.get("battleId")) for record in read_json(path).get("results", []))
    return result


def ingest(root: Path, envelope: object, *, account: str) -> list[str]:
    """Append accepted records once and return stable outcome messages."""
    accepted = validate_envelope(root, envelope, account=account)
    seen = existing_battle_ids(root)
    duplicates = [item.record["battleId"] for item in accepted if item.record["battleId"] in seen]
    if duplicates:
        raise ValidationError(f"duplicate battleId already retained: {', '.join(sorted(duplicates))}")
    paths: list[str] = []
    for item in accepted:
        path = raw_path(root, str(item.record["completedAt"]), item.digest)
        if path.exists():
            raise ValidationError(f"duplicate payload hash: {item.digest}")
        write_json(path, item.record)
        paths.append(path.relative_to(root).as_posix())
    return paths


def main() -> int:
    """Run result ingestion from the command line."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--account", required=True)
    parser.add_argument("--input", type=Path, required=True)
    arguments = parser.parse_args()
    try:
        paths = ingest(arguments.root.resolve(), read_json(arguments.input), account=arguments.account)
    except (OSError, ValueError, ValidationError) as error:
        print(f"ingestion failed: {error}")
        return 1
    print("accepted:\n" + "\n".join(paths))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
