#!/usr/bin/env python3
"""Validate versioned, whole-battle Rumble result envelopes."""

from __future__ import annotations

import argparse
import uuid
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from common import content_hash, read_json

SCHEMA_VERSION = 1
SCORE_FIELDS = ("survival", "lastSurvivorBonus", "bulletDamage", "bulletKillBonus", "ramDamage", "ramKillBonus")
PLACE_FIELDS = ("firstPlaces", "secondPlaces", "thirdPlaces")


class ValidationError(ValueError):
    """A submission error that can safely be returned to a contributor."""


@dataclass(frozen=True)
class AcceptedResult:
    """A valid record with its stable content address."""

    record: dict[str, Any]
    digest: str


def require(condition: bool, message: str) -> None:
    """Raise a concise validation error when condition is false."""
    if not condition:
        raise ValidationError(message)


def registered_client_ids(root: Path, account: str) -> set[str]:
    registration = root / "clients" / f"{account}.json"
    require(registration.is_file(), f"account `{account}` is not registered")
    data = read_json(registration)
    client_ids = data.get("clientIds")
    require(data.get("account") == account and isinstance(client_ids, list), f"registration for `{account}` is invalid")
    return {item for item in client_ids if isinstance(item, str) and item}


def active_bots(root: Path) -> dict[tuple[str, str], dict[str, Any]]:
    catalog = read_json(root / "catalog.json")
    require(catalog.get("schemaVersion") == SCHEMA_VERSION and isinstance(catalog.get("bots"), list), "catalog.json is invalid")
    return {(str(bot.get("name")), str(bot.get("version"))): bot for bot in catalog["bots"] if bot.get("status") == "active"}


def validate_header(root: Path, envelope: Any, account: str) -> tuple[list[Any], set[str], dict[tuple[str, str], dict[str, Any]]]:
    require(isinstance(envelope, dict), "submission must be a JSON object")
    require(envelope.get("schemaVersion") == SCHEMA_VERSION, "unsupported submission schemaVersion")
    require(isinstance(envelope.get("clientId"), str) and envelope["clientId"], "submission has no clientId")
    require(isinstance(envelope.get("clientVersion"), str) and envelope["clientVersion"], "submission has no clientVersion")
    records = envelope.get("results")
    require(isinstance(records, list) and records, "submission must contain at least one result")
    require(len(records) <= 60, "submission exceeds the 60-result batch limit")
    client_ids = registered_client_ids(root, account)
    require(envelope["clientId"] in client_ids, f"clientId `{envelope['clientId']}` is not registered to `{account}`")
    return records, client_ids, active_bots(root)


def validate_result(root: Path, record: Any, *, account: str, client_ids: set[str], known_bots: dict[tuple[str, str], dict[str, Any]]) -> AcceptedResult:
    require(isinstance(record, dict), "result must be a JSON object")
    required = ("battleId", "completedAt", "clientId", "behaviorVersion", "gameType", "numberOfRounds", "battlefield", "participants")
    require(all(field in record for field in required), f"result is missing one of: {', '.join(required)}")
    try:
        uuid.UUID(str(record["battleId"]))
        datetime.fromisoformat(str(record["completedAt"]).replace("Z", "+00:00"))
    except ValueError as error:
        raise ValidationError("battleId or completedAt is invalid") from error
    require(record["clientId"] in client_ids, f"clientId `{record['clientId']}` is not registered to `{account}`")
    engine = read_json(root / "engine.json")
    game_type = str(record["gameType"])
    preset = engine.get("gameTypes", {}).get(game_type)
    require(record["behaviorVersion"] == engine.get("behaviorVersion"), "behaviorVersion does not match engine.json")
    require(isinstance(preset, dict), f"unsupported gameType `{game_type}`")
    require(record["numberOfRounds"] == preset.get("rounds"), "numberOfRounds does not match the ranked preset")
    require(record["battlefield"] == preset.get("battlefield"), "battlefield does not match the ranked preset")
    participants = record["participants"]
    require(isinstance(participants, list) and len(participants) == preset.get("participants"), f"{game_type} requires {preset.get('participants')} participants")
    identities: set[tuple[str, str]] = set()
    ranks: set[int] = set()
    for participant in participants:
        require(isinstance(participant, dict), "each participant must be an object")
        identity = (str(participant.get("name")), str(participant.get("version")))
        require(identity in known_bots, f"unknown or inactive bot `{identity[0]} {identity[1]}`")
        require(identity not in identities, f"bot `{identity[0]} {identity[1]}` appears more than once")
        identities.add(identity)
        rank = participant.get("rank")
        require(isinstance(rank, int) and 1 <= rank <= len(participants) and rank not in ranks, "ranks must be unique ranked positions")
        ranks.add(rank)
        values = [participant.get(field) for field in SCORE_FIELDS + PLACE_FIELDS]
        require(all(isinstance(value, int) and not isinstance(value, bool) and value >= 0 for value in values), "score components and place counts must be non-negative integers")
        require(participant.get("totalScore") == sum(participant[field] for field in SCORE_FIELDS), "totalScore must equal the score component sum")
        require(all(participant[field] <= record["numberOfRounds"] for field in PLACE_FIELDS), "place count exceeds numberOfRounds")
    banned = read_json(root / "bans.json")
    require(account not in set(banned.get("bannedAccounts", [])), f"account `{account}` is banned")
    disqualified = {(str(item.get("name")), str(item.get("version"))) for item in banned.get("disqualifiedBots", [])}
    require(not identities.intersection(disqualified), "result contains a disqualified bot")
    normalized = record | {"submittedBy": account, "payloadHash": content_hash(record)}
    return AcceptedResult(normalized, content_hash(normalized))


def validate_batch(root: Path, envelope: Any, *, account: str) -> tuple[list[AcceptedResult], list[str]]:
    """Validate independently, preserving valid records in a mixed batch."""
    records, client_ids, known_bots = validate_header(root, envelope, account)
    accepted: list[AcceptedResult] = []
    rejected: list[str] = []
    seen: set[str] = set()
    for index, record in enumerate(records, start=1):
        try:
            item = validate_result(root, record, account=account, client_ids=client_ids, known_bots=known_bots)
            if item.record["battleId"] in seen:
                raise ValidationError("submission repeats a battleId")
            seen.add(item.record["battleId"])
            accepted.append(item)
        except ValidationError as error:
            rejected.append(f"result {index}: rejected: {error}")
    return accepted, rejected


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--account", required=True)
    parser.add_argument("--input", type=Path, required=True)
    arguments = parser.parse_args()
    try:
        accepted, rejected = validate_batch(arguments.root.resolve(), read_json(arguments.input), account=arguments.account)
    except (OSError, ValueError, ValidationError) as error:
        print(f"submission rejected: {error}")
        return 1
    print("\n".join([f"accepted: {item.record['battleId']}" for item in accepted] + rejected))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
