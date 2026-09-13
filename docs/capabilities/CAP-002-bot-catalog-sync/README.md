---
id: CAP-002
type: capability
status: active
provenance: inferred
reversal-cost: low
links: [G-001]
goal: G-001
title: Bot catalog synchronization
---

# CAP-002 — Bot catalog synchronization

What the system can do: check a reviewed external Rumble bot catalog hourly, update the local read-only copy only when normalized content changes, and immediately publish the active bot and version set without doing ranking or deployment work for an identical poll.

This capability exists so `CAP-001` never has to trust unvalidated team data: `scripts/sync_catalog.py` is the sole writer of `catalog.json`, and `scripts/common.py::normalized_catalog_bots` is the shared team-membership contract both this capability and `CAP-001` rely on.

Structure and cross-capability flow live in `../../architecture/README.md` and `../../design/README.md`; this folder covers only this capability's own behavior and design.
