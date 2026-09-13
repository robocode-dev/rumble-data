---
id: C-003
type: constraint
status: active
provenance: inferred
reversal-cost: low
links: [G-003]
title: Public source and documentation must be enough to recover ingestion and the dashboard, with no private dependencies
source: GOVERNANCE.md, "Fork drill"
enforcement: human
---

# C-003 — Public source and documentation must be enough to recover ingestion and the dashboard, with no private dependencies

A fork of this repository, with only its own workflows and Pages enabled, must be able to run aggregation and reproduce ingestion and the dashboard without personal credentials or external services.

**Residual:** verified only by a quarterly manual drill (fork, enable workflows and Pages, run aggregation locally, record the result in a governance issue) — there is no automated check that a change has not quietly introduced a private dependency (a secret, a non-public service call, an undocumented manual step) between drills.
