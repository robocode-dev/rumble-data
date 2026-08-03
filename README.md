# Tank Royale Rumble data

`rumble-data` is the immutable result store and static ranking dashboard for Tank Royale Rumble. Contributors submit ranked-battle batches through labelled issues; the serialized ingestion workflow validates them, commits only accepted JSON facts, and regenerates every projection from Git-tracked input.

## Local verification

Run the focused suite with `python -m unittest discover -s tests -v`. It uses only Python's standard library. Run `python scripts/aggregate.py --root .` to regenerate projections from the current facts.

`catalog.json` is a local, reviewed copy of the generated Rumble bot catalog. Run `python scripts/sync_catalog.py --root .` to refresh it from its declared HTTPS source; the scheduled workflow performs the same synchronization hourly.

## Submit results

Before a client can submit ranked results, its forge account must be registered through a reviewed pull request adding `clients/<account>.json`. The client then creates an issue labelled `result-submission`, with a `[result]` title and exactly one fenced JSON batch envelope. See [CONTRIBUTING.md](CONTRIBUTING.md) for the contract and limits.

Issue bodies are transport receipts, never durable storage. The only authoritative accepted result is a content-addressed JSON fact under `results/raw/`; projections are disposable and reproducible.

## Forking and operations

There are no secrets or external services. `scripts/` contains the portable implementation and GitHub Actions is a thin wrapper. `wellknown/rumble.json` identifies the canonical repository and allows an eventual move. Governance, moderation, compaction, and the quarterly fork drill are recorded in [GOVERNANCE.md](GOVERNANCE.md).
