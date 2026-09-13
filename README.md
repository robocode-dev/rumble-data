# Tank Royale Rumble data

`rumble-data` is the public result store and ranking dashboard for the Tank Royale Rumble. It accepts ranked battle batches from registered clients, keeps accepted results as immutable Git-tracked facts, and rebuilds the leaderboard from those facts.

- [Open the live rankings](https://robocode-dev.github.io/rumble-data/)
- [Learn what the Rumble is](https://robocode.dev/rumble/)
- [Register and run a battle client](https://robocode.dev/rumble/client-guide)

Most battle contributors should use the Rumble Client rather than create result issues by hand. This README describes the data repository for maintainers, auditors, and coding agents.

## When the dashboard updates

A result issue normally starts ingestion as soon as GitHub applies the `result-submission` label. A scheduled fallback runs at 17 and 47 minutes past every UTC hour. Each successful drain commits accepted facts, regenerates the projections, and triggers a Pages deployment when dashboard data changed.

The reviewed bot catalog synchronizes at 23 minutes past every UTC hour. A newly merged bot appears after that synchronization and starts with no ranked samples.

GitHub Actions schedules may run late, so these times describe the automation cadence rather than a delivery guarantee.

## How results become rankings

Submitted issue bodies are transport, not durable storage. The ingestion workflow validates each result independently and writes accepted records under `results/raw/` using content-addressed filenames. It publishes a receipt only after the accepted fact has been pushed.

`scripts/aggregate.py` derives the leaderboard, pairing statistics, matchmaking advice, client totals, and dashboard data from repository-tracked inputs. The generated projections are disposable; accepted facts are the source of truth.

The current dashboard ranks each game type by APS, or Average Percentage Score. It also shows how many battles and distinct matchups contribute to each entry.

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
