---
id: CAP-001
type: capability
status: active
provenance: inferred
reversal-cost: low
links: [G-001, G-002]
goal: G-001
title: Ranked result pipeline
---

# CAP-001 — Ranked result pipeline

What the system can do: accept a battle-result batch from a registered client, validate every record independently against the pinned engine and reviewed bot catalog, persist each accepted record once as an immutable, content-addressed fact, and derive the leaderboard, matchmaking advice, and dashboard data from the accepted facts plus current moderation state.

This is the capability `G-001` (a trustworthy, auditable leaderboard) and `G-002` (low-toil automated operation) both depend on: it is the whole path from `scripts/extract_envelope.py` and `scripts/validate.py` through `scripts/ingest.py`, `scripts/aggregate.py`, and `scripts/compact.py` to `leaderboard/`, `matchmaking/`, `clients.json`, and `site/data/`.

Structure and cross-capability flow live in `../../architecture/README.md` and `../../design/README.md`; this folder covers only this capability's own behavior and design.
