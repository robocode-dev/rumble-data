# Contributing result data

## Register a contributor client

Open a pull request that adds `clients/<your-forge-account>.json`. Its `account` must equal the filename, and `clientIds` must be a non-empty list of stable client identifiers you control. A moderator reviews this once before any issue submission is accepted.

## Submit a ranked batch

Create an issue titled `[result] <client-id> <UTC timestamp>`, apply the `result-submission` label, and place exactly one JSON envelope in a fenced `json` block. The envelope has `schemaVersion: 1`, `clientId`, `clientVersion`, and 1–60 whole-battle `results`. Each result supplies a UUID `battleId`, `completedAt`, the pinned `behaviorVersion`, game type, preset rounds and battlefield, and one Battle Runner result per required participant: immutable `name`, `version`, and `isTeam`, rank, total score, six score components, and first/second/third-place counts.

The submitting issue account and `clientId` must be registered. Every bot must be active in `catalog.json`; the catalog is synchronized from the reviewed Rumble bot catalog by maintainers. The drain workflow closes every processed issue with accepted and rejected record diagnostics.

## Rules

Do not edit raw facts, generated projections, or the static dashboard data in a pull request. Do not submit replays; retain replay evidence locally. Duplicate battle IDs, engine mismatches, preset mismatches, unknown bots, unregistered clients, banned accounts, malformed batches, and inconsistent score components are rejected. Fork-pull-request result submission is not supported in V1.

All contributions are made under Apache-2.0 and must follow the project code of conduct and governance process.
