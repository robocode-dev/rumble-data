# Governance and operations

The `robocode-dev` organization owns this repository. Moderators review client registrations, catalog updates, bans, exclusions, and ordinary code or policy changes through pull requests. The Verify Rumble data workflow must pass, and one moderator approval is required.

For the day-to-day review checklist, see [Moderate the Rumble](https://robocode.dev/rumble/moderator-guide).

## Automated writer boundary

CI is the only writer of accepted raw facts and generated projections on `main`. Clients submit through issues, and humans change policy or source through pull requests. Neither clients nor moderators manually add or rewrite result facts.

GitHub cannot distinguish the built-in Actions writer from human collaborators in a repository ruleset without a secret-bearing organization app. The CI-only writer rule is therefore a documented governance boundary for V1.

## Moderation

Keep accepted facts immutable. To exclude a disputed result, add its `battleId` to `exclusions.json`; aggregation then omits it while preserving the audit trail. To block abuse, add the GitHub account to `bans.json`. Explain each moderation change in its pull request.

Aggregation reapplies current registrations, bans, bot disqualifications, and exclusions whenever it rebuilds projections. A later moderation decision therefore changes what counts without rewriting history.

## Ingestion and dashboard operations

A newly labelled result issue normally triggers ingestion immediately. The scheduled fallback runs at 17 and 47 minutes past every UTC hour. Runs are serialized, and each drain processes the complete labelled inbox, commits accepted facts and projections together, publishes receipts, and closes processed issues.

Catalog synchronization runs at 23 minutes past every UTC hour. Dashboard deployment runs after a push changes `site/`.

If GitHub disables scheduled workflows after inactivity, re-enable them. An incoming labelled issue can wake ingestion, but it does not replace routine operational checks.

## Compaction

On the first drain of each month, compact individual facts older than three full months into monthly rollups. Use `scripts/compact.py` with a separate checkout of the `archive` branch. The script verifies that projections are unchanged before the operational change is accepted.

Move the selected individual facts to the archive branch in the same operation. Keep rejected transport receipts there for 30 days, then prune them.

## Fork drill

Once each quarter, fork the repository, enable its workflows and Pages, run aggregation locally, and record the result in a governance issue. The drill must show that public source and documentation are enough to recover result ingestion and the dashboard without personal credentials or external services.
