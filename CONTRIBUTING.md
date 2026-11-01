# Contributing Rumble result data

Battle contributors should register once, then let the Rumble Client create and track result submissions. Follow [Run ranked Rumble battles](https://robocode.dev/rumble/client-guide) for the complete setup. Do not handcraft an issue unless you are testing or developing the transport contract.

## Register a client

Fork this repository and open a pull request that adds `clients/<your-github-account>.json`. When you open the pull request, use the [client registration description](https://github.com/robocode-dev/rumble-data/compare?expand=1&template=client-registration.md) (the same address with `?template=client-registration.md` added). GitHub offers no menu for choosing a template and otherwise fills in a long maintainer checklist that does not apply to a registration.

```json
{
  "schemaVersion": 1,
  "account": "your-github-account",
  "clientIds": ["your-github-account-desktop-01"]
}
```

The filename and `account` must match the submitting GitHub account. `clientIds` must be a non-empty list of stable identifiers you control. A moderator reviews the registration before results from that account and client ID can be accepted. As a first-time contributor, the automated checks on your pull request do not start by themselves: GitHub holds them until a moderator approves the run, so a pull request that shows no finished checks is waiting for a moderator, not broken.

## Result submission contract

The client creates an issue titled `[result] <client-id> <UTC timestamp>`, applies the `result-submission` label, and puts exactly one JSON batch envelope in a fenced `json` block. The envelope contains `schemaVersion: 1`, `clientId`, `clientVersion`, and between 1 and 60 `results`.

Each result contains a UUID `battleId`, `completedAt`, matching nested client identity, the pinned engine behavior version, game type, rounds, arena dimensions, and the complete Battle Runner participant results.

Each participant contains the cataloged `name` and `version`, `isTeam`, 1224-system `rank`, `totalScore`, `survival`, `lastSurvivorBonus`, `bulletDamage`, `bulletKillBonus`, `ramDamage`, `ramKillBonus`, `firstPlaces`, `secondPlaces`, and `thirdPlaces`. Scores and place counts are non-negative signed 32-bit integers. Team flags, entry counts, ranks, and place-count totals must match the selected game type.

The issue author and `clientId` must match a current registration. Every participant must be active in the synchronized catalog, and the result must match the current engine and game-type pin.

## Processing and retries

The drain validates every record independently, so one rejected neighbor does not discard valid records in the same batch. Accepted facts are pushed before the workflow publishes per-record receipts and closes the issue.

Retrying an identical retained result returns the same successful outcome without creating another fact. Reusing a battle ID for different content is rejected.

## Protected data

Do not edit raw facts, generated projections, synchronized catalog data, or dashboard data in a pull request. Do not submit replays; contributors retain replay evidence locally.

Malformed batches, unknown or disqualified bots, unregistered clients, banned accounts, duplicate battle IDs, engine mismatches, preset mismatches, and inconsistent scores are rejected. Fork-pull-request result submission is not supported in V1.

All contributions are made under Apache-2.0 and must follow the project code of conduct and [GOVERNANCE.md](GOVERNANCE.md).
