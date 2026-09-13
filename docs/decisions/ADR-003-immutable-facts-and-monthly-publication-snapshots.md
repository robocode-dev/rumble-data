---
id: ADR-003
type: decision
status: inferred
author: agent
accepted-by: []
links: [CAP-001, CAP-002]
supersedes: [ADR-001]
title: Keep immutable facts and cumulative rankings with immutable monthly publication snapshots
---

# ADR-003 — Keep immutable facts and cumulative rankings with immutable monthly publication snapshots

Accepted battle results remain content-addressed immutable facts. The current leaderboard, matchmaking advice, client totals, and current dashboard JSON remain disposable projections fully regenerated from tracked facts plus current catalog, registration, engine, and moderation state.

The live ranking is cumulative and does not reset at month boundaries. Before the first serialized writer accepts new input in a new UTC month, it copies the previous current leaderboard and bot details byte for byte into an immutable snapshot for each completed month. Late accepted results can change the current projection but never rewrite a snapshot.

`site/data/history.json` separates operational publication metadata from deterministic aggregation. Its `lastUpdatedAt` changes only when current ranking-visible JSON changes; polling, aggregation with identical output, deployment, and snapshot creation alone do not make the ranking appear fresher.

This distinction keeps rankings reproducible while preserving what viewers actually saw at month end. It also constrains every writer to the shared serialization boundary and every future migration to treat existing snapshot paths as append-only records. The system structure and shared rollover flow are described in [the architecture overview](../architecture/README.md) and [the design overview](../design/README.md).
