# Contributing result data

## Register a contributor client

Open a pull request that adds `clients/<your-forge-account>.json`. Its `account` must equal the filename, and `clientIds` must be a non-empty list of stable client identifiers you control. A moderator reviews this once before any issue submission is accepted.

## Submit a ranked batch

Create an issue titled `[result] <client-id> <UTC timestamp>`, apply the `result-submission` label, and place exactly one JSON envelope in a fenced `json` block. The envelope has `schemaVersion: 1`, `clientId`, `clientVersion`, and 1–60 `results`. Each result supplies a UUID `battleId`, `completedAt`, nested `client.id` and `client.version` matching the envelope, nested `engine.behaviorVersion` matching the engine pin, game type, pinned rounds and arena dimensions, and the complete Battle Runner participant result model.

Each participant supplies cataloged `name` and `version`, `isTeam`, a 1224-system `rank`, `totalScore`, `survival`, `lastSurvivorBonus`, `bulletDamage`, `bulletKillBonus`, `ramDamage`, `ramKillBonus`, `firstPlaces`, `secondPlaces`, and `thirdPlaces`. Scores and place counts are non-negative signed 32-bit integers. `isTeam`, result-entry count, rank placement, and place-count totals must match the selected ranked game type.

The submitting issue account and `clientId` must be registered. Every bot must be active in `catalog.json`; the hourly synchronization workflow copies the reviewed Rumble bot catalog declared by that file. The drain workflow validates each record independently, keeps valid records when neighboring records are rejected, and closes every processed issue with a receipt line for every record.

## Rules

Do not edit raw facts, generated projections, or the static dashboard data in a pull request. Do not submit replays; retain replay evidence locally. Duplicate battle IDs, engine mismatches, unknown bots, unregistered clients, banned accounts, malformed batches, and implausible score sets are rejected.

All contributions are made under Apache-2.0 and must follow the project code of conduct and governance process.
