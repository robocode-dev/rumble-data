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

What the system can do: keep a local, read-only copy of the reviewed Rumble bot catalog (`catalog.json`) synchronized from its declared external HTTPS source, normalizing and validating team membership so that only bots and teams eligible for ranked play can ever reach `CAP-001`'s validation and matchmaking.

This capability exists so `CAP-001` never has to trust unvalidated team data: `scripts/sync_catalog.py` is the sole writer of `catalog.json`, and `scripts/common.py::normalized_catalog_bots` is the shared team-membership contract both this capability and `CAP-001` rely on.

Structure and cross-capability flow live in `../../architecture/README.md` and `../../design/README.md`; this folder covers only this capability's own behavior and design.
