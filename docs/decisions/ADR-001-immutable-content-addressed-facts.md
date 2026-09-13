---
id: ADR-001
type: decision
status: inferred
author: agent
accepted-by: []
links: [CAP-001]
title: Accepted results are immutable, content-addressed facts; every projection is disposable and fully regenerated
---

# ADR-001 — Accepted results are immutable, content-addressed facts; every projection is disposable and fully regenerated

Accepted battle results are stored as individual JSON files under `results/raw/<year>/<month>/<sha256-of-content>.json`, never edited or deleted once written. The leaderboard, matchmaking advice, per-client totals, and dashboard data are always fully rebuilt from these facts (plus current catalog, registration, and moderation state) rather than incrementally updated, and CI fails a pull request whose regenerated output differs from what is committed (`.github/workflows/verify.yml`).

This constrains future work: a change must never introduce a code path that edits or deletes an accepted fact, and must never let a projection be written by anything other than full regeneration from tracked inputs — both would break the audit guarantee this repository exists to provide (`G-001`).

**Why:** a public, multi-contributor leaderboard needs a record nobody can quietly rewrite, and a ranking anyone can reproduce rather than take on faith. Content-addressed filenames give idempotent, collision-safe writes for free (a retried submission naturally resolves to the same fact) without needing a separate deduplication index. Making projections disposable and CI-verified against drift is what lets moderation (bans, exclusions, catalog changes) take effect by re-deriving the present rather than editing the past.
