---
id: G-002
type: goal
status: accepted
provenance: inferred
reversal-cost: low
links: [VIS-001]
title: Maintainers want ingestion and ranking to run automatically with minimal manual toil
---

# G-002 — Maintainers want ingestion and ranking to run automatically with minimal manual toil

`GOVERNANCE.md` describes label-triggered ingestion with a scheduled fallback every 30 minutes, catalog synchronization on its own schedule, and automatic monthly compaction — moderators review policy changes and disputes, not routine batches. The repository map in `README.md` and the workflows under `.github/workflows/` show every routine step (validate, ingest, aggregate, publish) automated end to end, with humans only reviewing registrations, bans, exclusions, and catalog or policy pull requests.

Accepted since this automation is already live and operating (inferred from `GOVERNANCE.md` and the checked-in workflows).
