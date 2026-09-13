---
id: C-004
type: constraint
status: active
provenance: inferred
reversal-cost: low
links: [CAP-001]
title: Accepted raw facts and rollups are never edited or deleted
source: CONTRIBUTING.md ("Protected data"), GOVERNANCE.md ("Moderation")
enforcement: agent
---

# C-004 — Accepted raw facts and rollups are never edited or deleted

Once a result is accepted under `results/raw/` (or archived into `results/rollups/`), no pull request or workflow may edit or delete it. To exclude a disputed result, add its `battleId` to `exclusions.json` so aggregation omits it while the fact itself, and the audit trail, remain intact.

**Promotion trigger:** this becomes `machine`-enforced when CI gains a check that fails a pull request touching any path under `results/raw/` or `results/rollups/` outside the ingestion and compaction workflows themselves (for example, a CI job that diffs a PR's changed paths against those two writer workflows). Until then it is held by moderator review of every pull request (`GOVERNANCE.md`), the same residual `C-002` already names for the broader CI-only-writer boundary.
