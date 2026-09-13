---
id: C-002
type: constraint
status: active
provenance: inferred
reversal-cost: low
links: [CAP-001]
title: CI is the only writer of accepted facts and generated projections on main
source: GOVERNANCE.md, "Automated writer boundary"
enforcement: partial
---

# C-002 — CI is the only writer of accepted facts and generated projections on main

Clients submit only through issues; humans change policy or source only through pull requests. Neither clients nor moderators manually add or rewrite `results/`, `leaderboard/`, `matchmaking/`, `clients.json`, or `site/data/`.

**Checked by:** `.github/workflows/verify.yml`'s regenerate-and-diff step catches a hand-edited projection that drifted from what the tracked inputs would produce, on every pull request and push to `main`.

**Residual:** GitHub cannot distinguish the built-in Actions writer from a human collaborator in a repository ruleset without a secret-bearing organization app (`GOVERNANCE.md`), so nothing technically stops a moderator with write access from hand-editing `results/raw/` in a way that still regenerates consistent projections (for example, editing a fact and its dependent projections together). This is a documented governance boundary for V1, held by reviewer judgment on every pull request, not by a machine check.
