# Contributing result data

## Register a contributor client

Open a pull request that adds `clients/<your-forge-account>.json`. Its `account` must equal the filename, and `clientIds` must be a non-empty list of stable client identifiers you control. A moderator reviews this once before any issue submission is accepted.

## Submit a ranked batch

Create an issue titled `[result] <client-id> <UTC timestamp>`, apply the `result-submission` label, and place exactly one JSON envelope in a fenced `json` block. The envelope has `schemaVersion: 1`, `clientId`, `clientVersion`, and 1–60 `results`. Each result supplies a UUID `battleId`, `completedAt`, the pinned `behaviorVersion`, a supported game type, and one participant record per required bot with `name`, `version`, and non-negative `totalScore`.

The submitting issue account and `clientId` must be registered. Every bot must be active in `catalog.json`; the catalog is synchronized from the reviewed Rumble bot catalog by maintainers. The drain workflow closes every processed issue with accepted and rejected record diagnostics.

## Rules

Do not edit raw facts, generated projections, or the static dashboard data in a pull request. Do not submit replays; retain replay evidence locally. Duplicate battle IDs, engine mismatches, unknown bots, unregistered clients, banned accounts, malformed batches, and implausible score sets are rejected.

All contributions are made under Apache-2.0 and must follow the project code of conduct and governance process.
