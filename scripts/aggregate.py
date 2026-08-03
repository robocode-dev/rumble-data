#!/usr/bin/env python3
"""Derive deterministic Rumble leaderboard and matchmaking projections from raw facts."""

from __future__ import annotations

import argparse
from collections import defaultdict
from itertools import combinations
from pathlib import Path
from typing import Any

from common import content_hash, read_json, repository_files, write_json

TARGET_SAMPLES_PER_PAIRING = 6


def registered_clients(root: Path) -> dict[str, set[str]]:
    """Return current client registrations indexed by forge account."""
    registrations: dict[str, set[str]] = {}
    for path in repository_files(root, "clients"):
        registration = read_json(path)
        account, client_ids = registration.get("account"), registration.get("clientIds")
        if isinstance(account, str) and isinstance(client_ids, list) and all(isinstance(client_id, str) and client_id for client_id in client_ids):
            registrations[account] = set(client_ids)
    return registrations


def record_client_id(record: dict[str, Any]) -> str | None:
    """Return a record's V1 nested client identifier."""
    client = record.get("client")
    return client.get("id") if isinstance(client, dict) and isinstance(client.get("id"), str) else None


def eligible_fact(record: dict[str, Any], *, registrations: dict[str, set[str]], banned_accounts: set[str], disqualified_bots: set[tuple[str, str]], exclusions: set[str]) -> bool:
    """Select a fact against every current moderation and registration input."""
    account = record.get("submittedBy")
    if not isinstance(account, str) or account in banned_accounts or record.get("battleId") in exclusions:
        return False
    client_id = record_client_id(record)
    if client_id not in registrations.get(account, set()):
        return False
    return not any(identity(participant) in disqualified_bots for participant in record.get("participants", []) if isinstance(participant, dict))


def facts(root: Path) -> list[dict[str, Any]]:
    """Load raw facts and compacted rollups in a deterministic order."""
    records: list[dict[str, Any]] = []
    for path in repository_files(root, "results/raw"):
        records.append(read_json(path))
    for path in repository_files(root, "results/rollups"):
        rollup = read_json(path)
        records.extend(rollup.get("results", []))
    exclusions = set(read_json(root / "exclusions.json").get("battleIds", []))
    bans = read_json(root / "bans.json")
    banned_accounts = set(bans.get("bannedAccounts", []))
    disqualified_bots = {(str(item.get("name")), str(item.get("version"))) for item in bans.get("disqualifiedBots", [])}
    registrations = registered_clients(root)
    return sorted((record for record in records if eligible_fact(record, registrations=registrations, banned_accounts=banned_accounts, disqualified_bots=disqualified_bots, exclusions=exclusions)), key=lambda item: (str(item.get("completedAt")), str(item.get("payloadHash"))))


def active_catalog(root: Path) -> list[dict[str, Any]]:
    """Return active bot versions in stable identity order."""
    return sorted((bot for bot in read_json(root / "catalog.json").get("bots", []) if bot.get("status") == "active"), key=lambda item: (str(item.get("name")).casefold(), str(item.get("version"))))


def identity(participant: dict[str, Any]) -> tuple[str, str]:
    """Return a bot's immutable name-and-version identity."""
    return str(participant["name"]), str(participant["version"])


def aggregate_game_type(records: list[dict[str, Any]], catalog: list[dict[str, Any]], game_type: str, behavior_version: int) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    """Produce leaderboard, pairings, and matchmaking advice for one game type."""
    eligible = {(str(bot["name"]), str(bot["version"])): bot for bot in catalog}
    relevant = [record for record in records if record.get("gameType") == game_type and record.get("engine", {}).get("behaviorVersion") == behavior_version]
    shares: dict[tuple[str, str], dict[tuple[tuple[str, str], ...], list[float]]] = defaultdict(lambda: defaultdict(list))
    pairing_counts: dict[tuple[tuple[str, str], ...], int] = defaultdict(int)
    pair_sample_counts: dict[tuple[tuple[str, str], tuple[str, str]], int] = defaultdict(int)
    for record in relevant:
        participants = record["participants"]
        total = sum(float(participant["totalScore"]) for participant in participants)
        bots = tuple(sorted(identity(participant) for participant in participants))
        pairing_counts[bots] += 1
        for pair in combinations(bots, 2):
            pair_sample_counts[pair] += 1
        for participant in participants:
            bot = identity(participant)
            if bot in eligible:
                shares[bot][bots].append(float(participant["totalScore"]) / total if total else 0.0)
    entries = []
    for bot, catalog_entry in eligible.items():
        bot_pairings = shares.get(bot, {})
        per_pairing = [sum(values) / len(values) for values in bot_pairings.values()]
        entries.append({
            "bot": f"{bot[0]} {bot[1]}", "name": bot[0], "version": bot[1], "platform": catalog_entry.get("platform"), "owner": catalog_entry.get("owner"),
            "aps": round((sum(per_pairing) / len(per_pairing) * 100) if per_pairing else 0.0, 4), "battles": sum(len(values) for values in bot_pairings.values()),
            "pairings": len(bot_pairings), "epoch": behavior_version,
        })
    entries.sort(key=lambda item: (-float(item["aps"]), str(item["bot"]).casefold()))
    projection_id = content_hash({"gameType": game_type, "behaviorVersion": behavior_version, "records": relevant, "catalog": catalog})
    leaderboard = {"schemaVersion": 1, "projectionId": projection_id, "gameType": game_type, "behaviorVersion": behavior_version, "entries": entries}
    pairs = [{"bots": [f"{name} {version}" for name, version in pair], "battles": count} for pair, count in sorted(pairing_counts.items())]
    pairings = {"schemaVersion": 1, "projectionId": projection_id, "gameType": game_type, "pairings": pairs}
    priority_pairs = []
    for pair in combinations(sorted(eligible), 2):
        count = pair_sample_counts.get(pair, 0)
        if count < TARGET_SAMPLES_PER_PAIRING:
            priority_pairs.append({"bots": [f"{name} {version}" for name, version in pair], "have": count, "reason": "new-bot" if count == 0 else "under-sampled"})
    needed = {"schemaVersion": 1, "projectionId": projection_id, "gameType": game_type, "targetSamplesPerPairing": TARGET_SAMPLES_PER_PAIRING, "priorityPairs": priority_pairs}
    return leaderboard, pairings, needed


def aggregate(root: Path) -> None:
    """Regenerate every projection from repository inputs."""
    engine = read_json(root / "engine.json")
    behavior_version = int(engine["behaviorVersion"])
    records, catalog = facts(root), active_catalog(root)
    for game_type in sorted(engine["gameTypes"]):
        leaderboard, pairings, needed = aggregate_game_type(records, catalog, game_type, behavior_version)
        write_json(root / "leaderboard" / f"{game_type}.json", leaderboard)
        write_json(root / "matchmaking" / f"pairings-{game_type}.json", pairings)
        write_json(root / "matchmaking" / f"matches_needed-{game_type}.json", needed)
        write_json(root / "site" / "data" / "leaderboard" / f"{game_type}.json", leaderboard)
        for entry in leaderboard["entries"]:
            write_json(root / "leaderboard" / "bots" / f"{entry['name']}-{entry['version']}.json", {"schemaVersion": 1, "projectionId": leaderboard["projectionId"], "gameType": game_type, "entry": entry})
            write_json(root / "site" / "data" / "bots" / f"{entry['name']}-{entry['version']}.json", {"schemaVersion": 1, "projectionId": leaderboard["projectionId"], "gameType": game_type, "entry": entry})
    client_totals: dict[str, int] = defaultdict(int)
    for record in records:
        client_id = record_client_id(record)
        if client_id is not None:
            client_totals[client_id] += 1
    write_json(root / "clients.json", {"schemaVersion": 1, "clients": [{"clientId": client_id, "battles": battles} for client_id, battles in sorted(client_totals.items())]})
    write_json(root / "site" / "data" / "clients.json", {"schemaVersion": 1, "clients": [{"clientId": client_id, "battles": battles} for client_id, battles in sorted(client_totals.items())]})


def main() -> int:
    """Run aggregation from the command line."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    arguments = parser.parse_args()
    aggregate(arguments.root.resolve())
    print("regenerated projections")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
