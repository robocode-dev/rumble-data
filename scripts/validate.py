#!/usr/bin/env python3
"""Validate Tank Royale Rumble result envelopes using only the standard library."""

from __future__ import annotations

import argparse
import re
import uuid
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from common import TEAM_SIZE, content_hash, normalized_catalog_bots, read_json

SCHEMA_VERSION = 1
INT32_MIN = -(2**31)
INT32_MAX = 2**31 - 1
SCORE_FIELDS = (
    "totalScore",
    "survival",
    "lastSurvivorBonus",
    "bulletDamage",
    "bulletKillBonus",
    "ramDamage",
    "ramKillBonus",
    "firstPlaces",
    "secondPlaces",
    "thirdPlaces",
)
PLACE_FIELDS = ("firstPlaces", "secondPlaces", "thirdPlaces")
CLIENT_IMAGE = re.compile(r"ghcr\.io/[a-z0-9._/-]+@sha256:[0-9a-f]{64}")


class ValidationError(ValueError):
    """A submission error that is safe to show to its contributor."""


@dataclass(frozen=True)
class AcceptedResult:
    """A validated record with its deterministic content address."""

    record: dict[str, Any]
    digest: str


@dataclass(frozen=True)
class ValidationOutcome:
    """The accepted or rejected outcome for one submitted record."""

    index: int
    battle_id: str | None
    accepted: AcceptedResult | None = None
    error: str | None = None


def require(condition: bool, message: str) -> None:
    """Raise a diagnostic validation error when condition is false."""
    if not condition:
        raise ValidationError(message)


def require_string(value: Any, message: str) -> str:
    """Require a non-empty string value."""
    require(isinstance(value, str) and value, message)
    return value


def require_int32(value: Any, message: str, *, minimum: int = 0) -> int:
    """Require a signed 32-bit integer at or above the supplied minimum."""
    require(type(value) is int and INT32_MIN <= value <= INT32_MAX and value >= minimum, message)
    return value


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
    require(catalog.get("schemaVersion") == SCHEMA_VERSION, "catalog.json is invalid")
    try:
        bots = normalized_catalog_bots(catalog.get("bots"))
    except ValueError as error:
        raise ValidationError(f"catalog.json is invalid: {error}") from error
    return {(str(bot.get("name")), str(bot.get("version"))): bot for bot in bots if bot.get("status") == "active"}


def engine_pin(root: Path) -> dict[str, Any]:
    """Return the engine pin after validating its additive client image guidance."""
    engine = read_json(root / "engine.json")
    require(engine.get("schemaVersion") == SCHEMA_VERSION, "engine.json has an unsupported schemaVersion")
    client_image = engine.get("clientImage")
    require(client_image is None or (isinstance(client_image, str) and CLIENT_IMAGE.fullmatch(client_image) is not None),
            "engine.json.clientImage must be an immutable GHCR SHA-256 reference")
    return engine


def game_settings(root: Path, game_type: str) -> tuple[dict[str, Any], int]:
    """Return validated V1 settings and the number of bots represented by each result entry."""
    engine = engine_pin(root)
    games = engine.get("gameTypes")
    require(isinstance(games, dict) and game_type in games, f"unsupported gameType `{game_type}`")
    settings = games[game_type]
    require(isinstance(settings, dict), f"engine.json has invalid settings for `{game_type}`")
    team_size = TEAM_SIZE.get(game_type)
    require(team_size is not None, f"unsupported gameType `{game_type}`")
    expanded_participants = require_int32(settings.get("participants"), f"engine.json has invalid participants for `{game_type}`", minimum=1)
    require(expanded_participants % team_size == 0, f"engine.json has incompatible team size for `{game_type}`")
    require_int32(settings.get("rounds"), f"engine.json has invalid rounds for `{game_type}`", minimum=1)
    battlefield = settings.get("battlefield")
    require(isinstance(battlefield, list) and len(battlefield) == 2, f"engine.json has invalid battlefield for `{game_type}`")
    require_int32(battlefield[0], f"engine.json has invalid battlefield for `{game_type}`", minimum=1)
    require_int32(battlefield[1], f"engine.json has invalid battlefield for `{game_type}`", minimum=1)
    return settings, team_size


def validate_ranks(participants: list[dict[str, Any]]) -> None:
    """Require the engine's shared 1224 placement rank multiset."""
    ranks = [require_int32(participant.get("rank"), "rank must be a positive signed 32-bit integer", minimum=1) for participant in participants]
    distinct = sorted(set(ranks))
    require(distinct and distinct[0] == 1, "the lowest rank must be 1")
    for rank in distinct:
        lower_count = sum(candidate < rank for candidate in ranks)
        require(rank == lower_count + 1, "ranks must use the 1224 placement system")


def validate_result(root: Path, record: Any, *, account: str, client_ids: set[str], known_bots: dict[tuple[str, str], dict[str, Any]], envelope_client_id: str, envelope_client_version: str) -> AcceptedResult:
    """Validate one result record and return its content-addressed representation."""
    require(isinstance(record, dict), "result must be a JSON object")
    required = ("battleId", "completedAt", "client", "engine", "gameType", "rounds", "arenaWidth", "arenaHeight", "participants")
    require(all(field in record for field in required), f"result is missing one of: {', '.join(required)}")
    try:
        uuid.UUID(str(record["battleId"]))
    except ValueError as error:
        raise ValidationError("battleId must be a UUID") from error
    try:
        datetime.fromisoformat(str(record["completedAt"]).replace("Z", "+00:00"))
    except ValueError as error:
        raise ValidationError("completedAt must be an ISO-8601 timestamp") from error

    client = record["client"]
    require(isinstance(client, dict), "client must be an object")
    client_id = require_string(client.get("id"), "client.id must be a non-empty string")
    client_version = require_string(client.get("version"), "client.version must be a non-empty string")
    require(client_id == envelope_client_id and client_version == envelope_client_version, "record client identity must match the envelope")
    require(client_id in client_ids, f"client.id `{client_id}` is not registered to `{account}`")

    engine = record["engine"]
    require(isinstance(engine, dict), "engine must be an object")
    behavior_version = require_int32(engine.get("behaviorVersion"), "engine.behaviorVersion must be a positive signed 32-bit integer", minimum=1)
    configured_engine = engine_pin(root)
    require(behavior_version == configured_engine.get("behaviorVersion"), "engine.behaviorVersion does not match engine.json")

    game_type = require_string(record["gameType"], "gameType must be a non-empty string")
    settings, team_size = game_settings(root, game_type)
    require(record["rounds"] == settings["rounds"], f"rounds does not match the `{game_type}` engine pin")
    require(record["arenaWidth"] == settings["battlefield"][0] and record["arenaHeight"] == settings["battlefield"][1], f"arena dimensions do not match the `{game_type}` engine pin")

    participants = record["participants"]
    expected_entries = settings["participants"] // team_size
    require(isinstance(participants, list) and len(participants) == expected_entries, f"{game_type} requires {expected_entries} result entries")
    identities: set[tuple[str, str]] = set()
    expected_is_team = team_size > 1
    completed_rounds = settings["rounds"] * team_size
    for participant in participants:
        require(isinstance(participant, dict), "each participant must be an object")
        name = require_string(participant.get("name"), "participant name must be a non-empty string")
        version = require_string(participant.get("version"), "participant version must be a non-empty string")
        identity = name, version
        require(identity in known_bots, f"unknown or inactive bot `{name} {version}`")
        require(identity not in identities, f"bot `{name} {version}` appears more than once")
        identities.add(identity)
        require(type(participant.get("isTeam")) is bool and participant["isTeam"] is expected_is_team, f"isTeam must be {str(expected_is_team).lower()} for `{game_type}`")
        catalog_is_team = bool(known_bots[identity]["teamMembers"])
        require(catalog_is_team is expected_is_team, f"catalog identity `{name} {version}` is not eligible for `{game_type}`")
        for field in SCORE_FIELDS:
            require_int32(participant.get(field), f"{field} must be a non-negative signed 32-bit integer")
        for field in PLACE_FIELDS:
            require(participant[field] <= completed_rounds, f"{field} exceeds completed rounds")

    validate_ranks(participants)
    for participant in participants:
        require(sum(participant[field] for field in PLACE_FIELDS) <= completed_rounds, "participant place counts exceed completed rounds")
    for field in PLACE_FIELDS:
        total = sum(participant[field] for participant in participants)
        require(total <= completed_rounds, f"{field} total exceeds completed rounds")

    banned = read_json(root / "bans.json")
    require(account not in set(banned.get("bannedAccounts", [])), f"account `{account}` is banned")
    disqualified = {(str(item.get("name")), str(item.get("version"))) for item in banned.get("disqualifiedBots", [])}
    require(not identities.intersection(disqualified), "result contains a disqualified bot")
    normalized = record | {"submittedBy": account, "payloadHash": content_hash(record)}
    return AcceptedResult(normalized, content_hash(normalized))


def validate_envelope(root: Path, envelope: Any, *, account: str) -> list[ValidationOutcome]:
    """Validate each record independently and return one outcome for each."""
    require(isinstance(envelope, dict), "submission must be a JSON object")
    require(envelope.get("schemaVersion") == SCHEMA_VERSION, "unsupported submission schemaVersion")
    client_id = require_string(envelope.get("clientId"), "submission has no clientId")
    client_version = require_string(envelope.get("clientVersion"), "submission has no clientVersion")
    records = envelope.get("results")
    require(isinstance(records, list) and records, "submission must contain at least one result")
    require(len(records) <= 60, "submission exceeds the 60-result batch limit")
    client_ids = registered_client_ids(root, account)
    require(client_id in client_ids, f"clientId `{client_id}` is not registered to `{account}`")
    known_bots = active_bots(root)
    outcomes: list[ValidationOutcome] = []
    for index, record in enumerate(records):
        battle_id = str(record.get("battleId")) if isinstance(record, dict) and record.get("battleId") is not None else None
        try:
            accepted = validate_result(root, record, account=account, client_ids=client_ids, known_bots=known_bots, envelope_client_id=client_id, envelope_client_version=client_version)
            outcomes.append(ValidationOutcome(index=index, battle_id=battle_id, accepted=accepted))
        except ValidationError as error:
            outcomes.append(ValidationOutcome(index=index, battle_id=battle_id, error=str(error)))
    return outcomes


def main() -> int:
    """Run envelope validation from the command line."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--account", required=True)
    parser.add_argument("--input", type=Path, required=True)
    arguments = parser.parse_args()
    try:
        outcomes = validate_envelope(arguments.root.resolve(), read_json(arguments.input), account=arguments.account)
    except (OSError, ValueError, ValidationError) as error:
        print(f"validation failed: {error}")
        return 1
    for outcome in outcomes:
        label = outcome.battle_id or f"result[{outcome.index}]"
        print(f"{label}: {'accepted' if outcome.accepted else f'rejected: {outcome.error}'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
