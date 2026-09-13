# Tank Royale Rumble data

`rumble-data` is the public result store and ranking dashboard for the Tank Royale Rumble. It accepts ranked battle batches from registered clients, keeps accepted results as immutable Git-tracked facts, and rebuilds the leaderboard from those facts.

- [Open the live rankings](https://robocode-dev.github.io/rumble-data/)
- [Learn what the Rumble is](https://robocode.dev/rumble/)
- [Register and run a battle client](https://robocode.dev/rumble/client-guide)

Most battle contributors should use the Rumble Client rather than create result issues by hand. This README describes the data repository for maintainers, auditors, and coding agents.

## When the dashboard updates

A result issue normally starts ingestion as soon as GitHub applies the `result-submission` label. A scheduled fallback runs at 17 and 47 minutes past every UTC hour. Each drain regenerates the projections, but it commits and requests a Pages deployment only when accepted facts, current ranking data, or month history changed.

The reviewed bot catalog is checked at 23 minutes past every UTC hour. Identical source content stops without aggregation, a commit, or a deployment. A newly merged bot or bot version changes the catalog, triggers ranking regeneration and publication, and starts with no ranked samples.

The Pages workflow also checks at 41 minutes past each UTC hour whether the current `site/` tree differs from the latest successful deployment. This reconciliation recovers a missed deployment without republishing an unchanged site. GitHub Actions schedules may run late, so these times describe the automation cadence rather than a delivery guarantee.

The dashboard's “ranking data last updated” value advances only when current leaderboard or bot-detail JSON changes. A workflow run, unchanged regeneration, deployment, or monthly snapshot by itself does not advance it.

## How results become rankings

Submitted issue bodies are transport, not durable storage. The ingestion workflow validates each result independently and writes accepted records under `results/raw/` using content-addressed filenames. It publishes a receipt only after the accepted fact has been pushed.

`scripts/aggregate.py` derives the leaderboard, pairing statistics, matchmaking advice, client totals, and dashboard data from repository-tracked inputs. The generated projections are disposable; accepted facts are the source of truth.

The current dashboard ranks each game type by APS, or Average Percentage Score. For each accepted battle, a participant's score share is its `totalScore` divided by the sum of all participants' `totalScore` values; a zero total produces a zero share. Battles are grouped by the exact sorted set of participating bot name-and-version identities. Repeated battles are averaged within each distinct pairing, then APS is 100 times the mean of those pairing averages, so every distinct pairing has equal weight regardless of how many samples it has. Stored APS is rounded to four decimal places and the dashboard displays two.

Only accepted facts matching the current `engine.json` `behaviorVersion` and matchups whose complete participant set consists of currently active, game-type-eligible identities contribute. The live leaderboard contains only catalog entries whose exact name and version are currently `active`. When a new version becomes active, it is a separate identity that starts at APS 0 with no samples; its superseded version disappears, and matchups containing that old version stop affecting every participant's live APS. Entries sort by descending APS with a stable bot-identity tie break.

The live ranking remains cumulative rather than resetting each month. Before the first result or catalog writer proceeds in a new UTC month, it saves the previous current leaderboard and bot details as an immutable month-end snapshot. The dashboard period selector exposes these read-only snapshots; late results affect the current ranking only and never rewrite past months. The first snapshot is created at the first month boundary after this feature is deployed, with no synthetic backfill.

## Repository map

| Path | Purpose |
|------|---------|
| `results/raw/` | Immutable accepted battle facts. |
| `leaderboard/` | Generated rankings and per-entry details. |
| `matchmaking/` | Generated pairing counts and under-sampled matchup advice. |
| `clients/` | Reviewed battle-contributor registrations. |
| `catalog.json` | Synchronized copy of the reviewed Rumble bot catalog. |
| `engine.json` | Pinned game behavior and ranked presets. |
| `site/` | Static dashboard published through GitHub Pages. |
| `site/data/history.json` | Current publication freshness and available monthly snapshots. |
| `site/data/snapshots/YYYY-MM/` | Immutable cumulative month-end leaderboard and bot-detail JSON. |
| `wellknown/rumble.json` | Canonical repository pointer used by clients. |

`engine.json.clientImage` is optional while no production Rumble Client image is published. When added, it must use an immutable image digest. Ranked compatibility is determined by `behaviorVersion`, not by the presence of an image.

## Verify locally

Run the test suite:

```shell
python -m unittest discover -s tests -v
```

Regenerate projections:

```shell
python scripts/aggregate.py --root .
```

Refresh `catalog.json` from its declared HTTPS source:

```shell
python scripts/sync_catalog.py --root .
```

The scripts use only Python's standard library. Read [CONTRIBUTING.md](CONTRIBUTING.md) for registration and result-envelope contracts, and [GOVERNANCE.md](GOVERNANCE.md) for moderation, compaction, and recovery procedures.
