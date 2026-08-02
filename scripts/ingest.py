#!/usr/bin/env python3
"""Validate a result envelope and append each new record as an immutable raw fact."""

from __future__ import annotations

import argparse
from pathlib import Path

from common import read_json, write_json
from validate import AcceptedResult, ValidationError, ValidationOutcome, validate_envelope


def raw_path(root: Path, completed_at: str, digest: str) -> Path:
    """Return the deterministic raw-fact path for a result record."""
    date = completed_at[:10].split("-")
    if len(date) != 3 or not all(part.isdigit() for part in date):
        raise ValidationError("completedAt must start with an ISO-8601 date")
    return root / "results" / "raw" / date[0] / date[1] / f"{digest}.json"


def retained_values(root: Path, field: str) -> set[str]:
    """Return one field's values from every retained raw fact and rollup record."""
    result: set[str] = set()
    for path in (root / "results" / "raw").rglob("*.json") if (root / "results" / "raw").exists() else []:
        result.add(str(read_json(path).get(field)))
    for path in (root / "results" / "rollups").rglob("*.json") if (root / "results" / "rollups").exists() else []:
        result.update(str(record.get(field)) for record in read_json(path).get("results", []))
    return result


def format_outcome(outcome: ValidationOutcome) -> str:
    """Render one stable receipt line for a submitted record."""
    label = outcome.battle_id or f"result[{outcome.index}]"
    return f"{label}: {'accepted' if outcome.accepted else f'rejected: {outcome.error}'}"


def ingest(root: Path, envelope: object, *, account: str) -> list[ValidationOutcome]:
    """Append every independently accepted record and return all receipt outcomes."""
    outcomes = validate_envelope(root, envelope, account=account)
    battle_ids = retained_values(root, "battleId")
    payload_hashes = retained_values(root, "payloadHash")
    persisted: list[ValidationOutcome] = []
    for outcome in outcomes:
        if outcome.accepted is None:
            persisted.append(outcome)
            continue
        item: AcceptedResult = outcome.accepted
        battle_id = str(item.record["battleId"])
        if battle_id in battle_ids:
            persisted.append(ValidationOutcome(index=outcome.index, battle_id=battle_id, error="duplicate battleId already retained"))
            continue
        if item.record["payloadHash"] in payload_hashes:
            persisted.append(ValidationOutcome(index=outcome.index, battle_id=battle_id, error="duplicate payload hash already retained"))
            continue
        path = raw_path(root, str(item.record["completedAt"]), item.digest)
        if path.exists():
            persisted.append(ValidationOutcome(index=outcome.index, battle_id=battle_id, error="duplicate payload hash already retained"))
            continue
        write_json(path, item.record)
        battle_ids.add(battle_id)
        payload_hashes.add(str(item.record["payloadHash"]))
        persisted.append(outcome)
    return persisted


def main() -> int:
    """Run result ingestion from the command line."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--account", required=True)
    parser.add_argument("--input", type=Path, required=True)
    arguments = parser.parse_args()
    try:
        outcomes = ingest(arguments.root.resolve(), read_json(arguments.input), account=arguments.account)
    except (OSError, ValueError, ValidationError) as error:
        print(f"ingestion failed: {error}")
        return 1
    print("\n".join(format_outcome(outcome) for outcome in outcomes))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
