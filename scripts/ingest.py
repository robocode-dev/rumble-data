#!/usr/bin/env python3
"""Validate a result envelope and append each new record as an immutable raw fact."""

from __future__ import annotations

import argparse
from pathlib import Path

from common import content_hash, read_json, write_json
from validate import SCHEMA_VERSION, AcceptedResult, ValidationError, ValidationOutcome, validate_envelope


def raw_path(root: Path, completed_at: str, digest: str) -> Path:
    """Return the deterministic raw-fact path for a result record."""
    date = completed_at[:10].split("-")
    if len(date) != 3 or not all(part.isdigit() for part in date):
        raise ValidationError("completedAt must start with an ISO-8601 date")
    return root / "results" / "raw" / date[0] / date[1] / f"{digest}.json"


def retained_results(root: Path) -> dict[str, dict]:
    """Return retained facts indexed by battle ID."""
    result: dict[str, dict] = {}
    for path in (root / "results" / "raw").rglob("*.json") if (root / "results" / "raw").exists() else []:
        record = read_json(path)
        result[str(record.get("battleId"))] = record
    for path in (root / "results" / "rollups").rglob("*.json") if (root / "results" / "rollups").exists() else []:
        for record in read_json(path).get("results", []):
            result[str(record.get("battleId"))] = record
    return result


def validate_with_idempotent_retries(root: Path, envelope: object, *, account: str,
                                     retained: dict[str, dict]) -> list[ValidationOutcome]:
    """Validate new records while recovering successes for identical retained facts."""
    if not isinstance(envelope, dict) or not isinstance(envelope.get("results"), list):
        return validate_envelope(root, envelope, account=account)
    recovered: dict[int, ValidationOutcome] = {}
    pending_records: list[object] = []
    pending_indexes: list[int] = []
    recoverable_envelope = envelope.get("schemaVersion") == SCHEMA_VERSION and 0 < len(envelope["results"]) <= 60
    for index, record in enumerate(envelope["results"]):
        battle_id = str(record.get("battleId")) if isinstance(record, dict) and record.get("battleId") is not None else None
        existing = retained.get(battle_id) if battle_id is not None else None
        client = record.get("client") if isinstance(record, dict) else None
        identical = (
            recoverable_envelope
            and existing is not None
            and existing.get("submittedBy") == account
            and content_hash(record) == existing.get("payloadHash")
            and isinstance(client, dict)
            and envelope.get("clientId") == client.get("id")
            and envelope.get("clientVersion") == client.get("version")
        )
        if identical:
            accepted = AcceptedResult(existing, content_hash(existing))
            recovered[index] = ValidationOutcome(index=index, battle_id=battle_id, accepted=accepted)
        else:
            pending_indexes.append(index)
            pending_records.append(record)
    if pending_records:
        pending_envelope = envelope | {"results": pending_records}
        for index, outcome in zip(pending_indexes, validate_envelope(root, pending_envelope, account=account)):
            recovered[index] = ValidationOutcome(index=index, battle_id=outcome.battle_id, accepted=outcome.accepted, error=outcome.error)
    return [recovered[index] for index in range(len(envelope["results"]))]


def format_outcome(outcome: ValidationOutcome) -> str:
    """Render one stable receipt line for a submitted record."""
    label = outcome.battle_id or f"result[{outcome.index}]"
    return f"{label}: {'accepted' if outcome.accepted else f'rejected: {outcome.error}'}"


def ingest(root: Path, envelope: object, *, account: str) -> list[ValidationOutcome]:
    """Append every independently accepted record and return all receipt outcomes."""
    retained = retained_results(root)
    outcomes = validate_with_idempotent_retries(root, envelope, account=account, retained=retained)
    payload_hashes = {str(record.get("payloadHash")) for record in retained.values()}
    persisted: list[ValidationOutcome] = []
    for outcome in outcomes:
        if outcome.accepted is None:
            persisted.append(outcome)
            continue
        item: AcceptedResult = outcome.accepted
        battle_id = str(item.record["battleId"])
        payload_hash = str(item.record["payloadHash"])
        existing = retained.get(battle_id)
        if existing is item.record:
            persisted.append(outcome)
            continue
        if battle_id in retained:
            persisted.append(ValidationOutcome(index=outcome.index, battle_id=battle_id, error="duplicate battleId already retained"))
            continue
        if payload_hash in payload_hashes:
            persisted.append(ValidationOutcome(index=outcome.index, battle_id=battle_id, error="duplicate payload hash already retained"))
            continue
        path = raw_path(root, str(item.record["completedAt"]), item.digest)
        if path.exists():
            persisted.append(ValidationOutcome(index=outcome.index, battle_id=battle_id, error="duplicate payload hash already retained"))
            continue
        write_json(path, item.record)
        retained[battle_id] = item.record
        payload_hashes.add(payload_hash)
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
