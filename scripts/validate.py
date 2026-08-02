#!/usr/bin/env python3
"""Validate Tank Royale Rumble result envelopes using only the standard library."""

from __future__ import annotations

import argparse
import uuid
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from common import content_hash, read_json

SCHEMA_VERSION = 1
GAME_TYPE_PARTICIPANTS = {"1v1": 2, "twinduel": 4, "melee": 10}


class ValidationError(ValueError):
    """A submission error that is safe to show to its contributor."""


@dataclass(frozen=True)
class AcceptedResult:
    """A validated record with its deterministic content address."""

    record: dict[str, Any]
    digest: str


def require(condition: bool, message: str) -> None:
    """Raise a diagnostic validation error when condition is false."""
    if not condition:
        raise ValidationError(message)


def registered_client_ids(root: Path, account: str) -> set[str]:
    """Return registered client IDs for one forge account."""
    registration = root / "clients" / f"{account}.json"
    require(registration.is_file(), f"account `{account}` is not registered")
    data = read_json(registration)
    require(data.get("account") == account, f"registration for `{account}` has an invalid account field")
    client_ids = data.get("clientIds")
    require(isinstance(client_ids, list) and all(isinstance(item, str) and item for item in client_ids), "registration has invalid clientIds")
    return set(client_ids)


def active_bots(root: Path) -> dict[tuple[str, str], dict[str, Any]]:
    """Return the active catalog entries indexed by immutable bot identity."""
    catalog = read_json(root / "catalog.json")
    bots = catalog.get("bots")
    require(catalog.get("schemaVersion") == SCHEMA_VERSION and isinstance(bots, list), "catalog.json is invalid")
    return {(str(bot.get("name")), str(bot.get("version"))): bot for bot in bots if bot.get("status") == "active"}


def validate_result(root: Path, record: Any, *, account: str, client_ids: set[str], known_bots: dict[tuple[str, str], dict[str, Any]]) -> AcceptedResult:
    """Validate one result record and return its content-addressed representation."""
    require(isinstance(record, dict), "result must be a JSON object")
    required = ("battleId", "completedAt", "clientId", "behaviorVersion", "gameType", "participants")
    require(all(field in record for field in required), f"result is missing one of: {', '.join(required)}")
    try:
        uuid.UUID(str(record["battleId"]))
    except ValueError as error:
        raise ValidationError("battleId must be a UUID") from error
    try:
        datetime.fromisoformat(str(record["completedAt"]).replace("Z", "+00:00"))
    except ValueError as error:
        raise ValidationError("completedAt must be an ISO-8601 timestamp") from error
    require(record["clientId"] in client_ids, f"clientId `{record['clientId']}` is not registered to `{account}`")
    engine = read_json(root / "engine.json")
    require(record["behaviorVersion"] == engine.get("behaviorVersion"), "behaviorVersion does not match engine.json")
    game_type = record["gameType"]
    require(game_type in GAME_TYPE_PARTICIPANTS, f"unsupported gameType `{game_type}`")
    participants = record["participants"]
    require(isinstance(participants, list) and len(participants) == GAME_TYPE_PARTICIPANTS[game_type], f"{game_type} requires {GAME_TYPE_PARTICIPANTS[game_type]} participants")
    identities: set[tuple[str, str]] = set()
    total_score = 0.0
    for participant in participants:
        require(isinstance(participant, dict), "each participant must be an object")
        identity = (str(participant.get("name")), str(participant.get("version")))
        require(identity in known_bots, f"unknown or inactive bot `{identity[0]} {identity[1]}`")
        require(identity not in identities, f"bot `{identity[0]} {identity[1]}` appears more than once")
        identities.add(identity)
        score = participant.get("totalScore")
        require(isinstance(score, (int, float)) and not isinstance(score, bool) and score >= 0, "totalScore must be a non-negative number")
        total_score += float(score)
    require(total_score > 0, "at least one participant must have a positive totalScore")
    banned = read_json(root / "bans.json")
    require(account not in set(banned.get("bannedAccounts", [])), f"account `{account}` is banned")
    disqualified = {(str(item.get("name")), str(item.get("version"))) for item in banned.get("disqualifiedBots", [])}
    require(not identities.intersection(disqualified), "result contains a disqualified bot")
    normalized = record | {"submittedBy": account, "payloadHash": content_hash(record)}
    return AcceptedResult(normalized, content_hash(normalized))


def validate_envelope(root: Path, envelope: Any, *, account: str) -> list[AcceptedResult]:
    """Validate a batch envelope and return every accepted result."""
    require(isinstance(envelope, dict), "submission must be a JSON object")
    require(envelope.get("schemaVersion") == SCHEMA_VERSION, "unsupported submission schemaVersion")
    client_id = envelope.get("clientId")
    require(isinstance(client_id, str) and client_id, "submission has no clientId")
    records = envelope.get("results")
    require(isinstance(records, list) and records, "submission must contain at least one result")
    require(len(records) <= 60, "submission exceeds the 60-result batch limit")
    client_ids = registered_client_ids(root, account)
    require(client_id in client_ids, f"clientId `{client_id}` is not registered to `{account}`")
    known_bots = active_bots(root)
    accepted = [validate_result(root, record, account=account, client_ids=client_ids, known_bots=known_bots) for record in records]
    battle_ids = [item.record["battleId"] for item in accepted]
    require(len(set(battle_ids)) == len(battle_ids), "submission repeats a battleId")
    return accepted


def main() -> int:
    """Run envelope validation from the command line."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--account", required=True)
    parser.add_argument("--input", type=Path, required=True)
    arguments = parser.parse_args()
    try:
        results = validate_envelope(arguments.root.resolve(), read_json(arguments.input), account=arguments.account)
    except (OSError, ValueError, ValidationError) as error:
        print(f"validation failed: {error}")
        return 1
    print(f"validated {len(results)} result(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
