# Governance and operations

The `robocode-dev` organization owns this repository. Moderators review client registrations, catalog updates, bans, and exclusions through ordinary pull requests. CI is the only writer of accepted raw facts and generated projections on `main`.

## Moderation

Keep facts immutable. To exclude a disputed result, add its `battleId` to `exclusions.json`; aggregation will omit it while preserving the audit trail. To block abuse, add the forge account to `bans.json`. Explain each moderation change in its pull request.

## Ingestion

The workflow is triggered by labelled issues and a modest schedule. It serializes runs, validates every record in an issue batch independently, commits all accepted facts in one commit, regenerates projections, comments with one receipt line per record, and closes the issue. Aggregation applies the current registrations, bans, disqualified bots, and exclusions to immutable facts, so later moderation immediately changes projections without rewriting history. If scheduled workflows are disabled after inactivity, re-enable the workflow; an incoming labelled issue also wakes the system.

## Compaction and fork drill

On the first drain of a month, create monthly rollups for facts older than three full months, verify aggregation is unchanged, then move the individual source facts to the `archive` branch in the same operational change. Keep rejected transport receipts for 30 days on that branch. Once each quarter, fork the repository, enable its workflows and Pages, run aggregation locally, and record the result in a governance issue.
