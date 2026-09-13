---
id: VIS-001
type: vision
status: draft
provenance: inferred
reversal-cost: low
links: []
title: Public, verifiable Tank Royale Rumble rankings
---

# VIS-001 — Public, verifiable Tank Royale Rumble rankings

`rumble-data` is the public result store and ranking dashboard for the Tank Royale Rumble: a continuous, community-run bot tournament for the Robocode Tank Royale engine. It serves battle contributors who run ranked battles against a registered client, bot authors and owners who want to see how their bots rank, and moderators and auditors who need to trust and, if necessary, correct what is published.

The problem it addresses: a ranked leaderboard that many independent, untrusted parties contribute battle results to needs a record of what happened that nobody can quietly rewrite, and a ranking that anyone can regenerate from that record rather than take on faith. The value it creates is a transparent, audit-friendly leaderboard (ranked by Average Percentage Score, or APS) plus matchmaking advice that tells contributors which bot pairings are under-sampled.

**In scope:** accepting battle-result submissions from registered clients over GitHub Issues, validating each result independently against the pinned engine and reviewed bot catalog, keeping accepted results as immutable Git-tracked facts, deriving the leaderboard and matchmaking projections from those facts, publishing a static dashboard, and giving moderators a way to exclude disputed results or ban abusive accounts without rewriting history.

**Deliberately out of scope (V1):** running battles itself (that is the separate Rumble Client and Tank Royale engine), hosting the reviewed bot catalog (this repository only synchronizes a read-only copy), accepting submissions from forked repositories or unregistered clients, and any authenticated write path other than GitHub's own PR/issue review flow.

**Principles that constrain its direction, evidenced in `GOVERNANCE.md` and `CONTRIBUTING.md`:**

- Accepted facts are immutable; moderation acts by excluding or re-deriving, never by editing history.
- CI is the only writer of accepted facts and generated projections on `main` — humans change policy or source through reviewed pull requests, not by hand-editing results.
- Everything needed to reproduce ingestion and the dashboard must be public: the quarterly fork drill (`GOVERNANCE.md`) exists specifically to prove the project does not secretly depend on private credentials or services.
- Generated projections are disposable and must always be re-derivable from repository-tracked inputs (`scripts/aggregate.py`); the raw facts are the only source of truth.

**Recognizing success:** contributors can submit results and see them ranked within one ingestion cycle; a disputed result can be excluded and the leaderboard recomputed without any accepted fact being altered; a fresh fork can rebuild the same dashboard from public inputs alone.

**Assumptions still uncertain (ask a human to confirm or correct):**

- Whether the "V1" qualifiers throughout `CONTRIBUTING.md`/`GOVERNANCE.md` (no fork-PR submissions, no dedicated writer-identity mechanism) describe a deliberately staged rollout with a known V2 direction, or just the current limits of what GitHub permissions allow.
- Whether bot authors/owners are meant to be a primary audience of the dashboard itself, or whether the dashboard's main audience is contributors and moderators, with public bot authors being an incidental beneficiary.
