---
id: CAP-001-design
type: design
status: active
links: [CAP-001]
title: Ranked result pipeline — design
---

# CAP-001 — design

## Transport and extraction

A client submits by opening a GitHub issue titled `[result] <client-id> <UTC timestamp>` with the `result-submission` label and exactly one fenced `json` batch envelope in the body (`CONTRIBUTING.md`). `scripts/extract_envelope.py` pulls that one fenced block out of the raw issue body; more or fewer than one fenced JSON block is rejected before any record-level validation runs.

The submitting identity is always the GitHub account that owns the issue (`.github/workflows/ingest.yml` reads `user.login`, not any field inside the body), so a batch's content can never claim a different submitter than the one GitHub recorded.

## Validation (`scripts/validate.py`)

Each record is validated independently and completely before any of it is trusted:

- Structural shape: required fields present, `battleId` a UUID, `completedAt` ISO-8601, all score fields non-negative signed 32-bit integers.
- Identity: `client.id`/`client.version` match the envelope and the account's registration (`clients/<account>.json`); every participant is an active catalog entry (`CAP-002`); no duplicate identity within one record.
- Engine pin: `engine.behaviorVersion` matches `engine.json`; `rounds` and arena dimensions match the pinned settings for the record's `gameType`; `engine.json.clientImage`, when present, must be an immutable `ghcr.io/...@sha256:...` reference, never a mutable tag.
- Game-type shape: the participant count and `isTeam` flag match the game type's configured team size (`common.TEAM_SIZE`); a team's catalog entry must itself be a team, and two teams in one record must not share a member (enforced through `CAP-002`'s validated `teamMembers`).
- Placement: ranks must follow the shared 1224 placement system; place-count fields must not exceed completed rounds, individually or summed per participant or per field.
- Moderation: the submitting account must not be banned, and no participant may be a disqualified bot (`bans.json`).

A record that fails any check is rejected with a diagnostic message; a batch's other, independently valid records are unaffected (`AC-RDA-002`, `AC-RDA-001`).

## Persistence (`scripts/ingest.py`)

An accepted record is normalized with `submittedBy` (the account) and a `payloadHash` (a SHA-256 content hash of the raw record, via `common.content_hash`'s canonical JSON), then written once under `results/raw/<year>/<month>/<digest>.json`, where `<digest>` is the content hash of the normalized record — deterministic, collision-free, and inherently deduplicating.

Idempotency: retaining state is checked by `battleId` before insertion. An identical retry (same account, same `payloadHash`, same client identity) recovers the original accepted outcome without writing a second fact — this holds even if the engine pin has since changed, because the retry is judged against the already-accepted record, not re-validated from scratch. A battle ID reused for different content, or a payload hash or raw-fact path collision from a different record, is rejected rather than silently accepted or overwritten.

## Projection (`scripts/aggregate.py`)

Projections are always fully regenerated from repository-tracked inputs, never incrementally updated — this is what keeps `AC-RDA-003` true (identical output whether facts come from `results/raw` or archived `results/rollups`, and always reflecting only currently-registered, unbanned, non-excluded, non-disqualified data):

1. Load every raw fact and rollup record; filter to those whose submitting account is currently registered for that client ID and not banned, whose `battleId` is not in `exclusions.json`, and whose participants are not disqualified.
2. For each configured game type, compute each eligible bot's APS (mean, across its distinct pairings, of the mean per-pairing score share) and battle/pairing counts, and matchmaking advice (pairings below `TARGET_SAMPLES_PER_PAIRING`, tagged `new-bot` at zero samples or `under-sampled` otherwise) — team pairs that would share a member (`CAP-002`) are never proposed.
3. Write `leaderboard/<gameType>.json`, `leaderboard/bots/<name>-<version>.json`, `matchmaking/pairings-<gameType>.json`, `matchmaking/matches_needed-<gameType>.json`, mirrored copies of the leaderboard and bot-detail files under `site/data/`, and `clients.json` (battle totals per client ID).

Every projection carries a `projectionId` — a content hash of the game type, behavior version, contributing records, and catalog — so a consumer can tell whether two projections were derived from the same inputs.

`scripts/compact.py` moves facts older than three full months into monthly rollups on a separate `archive` branch checkout, but only after confirming aggregation output is byte-identical before and after the move; any mismatch rolls the move back entirely (`AC-RDA-003`).

## Ordering guarantee

`.github/workflows/ingest.yml` always pushes accepted facts and regenerated projections before it publishes per-record receipt comments and closes the issue, so a contributor is never told "accepted" for a fact that is not yet durably committed.

## Dashboard (`site/`)

The static site has no server component: `site/app.js` fetches `data/leaderboard/${gameType}.json` and `data/bots/...json` directly and renders/sorts entries client-side (`AC-RDA-004`). `.github/workflows/pages.yml` redeploys whenever a push changes anything under `site/`.
