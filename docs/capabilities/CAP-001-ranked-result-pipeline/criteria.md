---
id: CAP-001-criteria
type: criteria
status: active
links: [CAP-001]
title: Ranked result pipeline — acceptance criteria
ac-prefix: RDA
---

# CAP-001 — acceptance criteria

Each test method in `tests/test_rumble_data.py` embeds its criterion ID, declared type, and direction in its name (`test<PREFIX><digits>_<Type><Direction>_<description>`); this file's IDs canonicalize that embedded number with a hyphen (`RDA001` → `RDA-001`).

`clue validate` auto-classifies test evidence only in Go, JVM, or Cucumber, so it cannot verify these Python references directly; each scenario cites its test methods below as a direct reference instead.

Every criterion remains tagged `@draft` only because the repository's executable evidence is Python, which the current Cliewen evidence classifier cannot recognize. Its focused tests run in `verify.yml`; the tag records the unsupported formal proof carrier rather than an unimplemented behavior.

```gherkin
@RDA-001 @draft
Scenario: A valid submission from a registered client becomes an immutable ranked fact
Test-type: Integration
  Given a battle result from a registered client and client ID, for a supported game type, matching the pinned engine and an active catalog entry
  When the batch is ingested
  Then the record is written exactly once as a content-addressed immutable fact under results/raw
  And regenerating projections reflects it in the leaderboard and in matchmaking advice
```

Evidence (all positive-direction facets of this one criterion):

- `testRDA001_IntegrationPositive_valid_batch_becomes_immutable_fact_and_projections`
- `testRDA001_IntegrationPositive_issue_inbox_uses_GitHub_submitter_account` — the submitting account is read from the issue author, never from batch content
- `testRDA001_IntegrationPositive_valid_records_survive_invalid_batch_neighbors` — one batch's records are validated and persisted independently
- `testRDA001_IntegrationPositive_identical_retry_is_idempotently_accepted` — retrying an identical retained result is idempotent, not a duplicate
- `testRDA001_IntegrationPositive_identical_retry_survives_current_pin_change` — an idempotent retry succeeds even after the engine pin has since changed
- `testRDA001_IntegrationPositive_twinduel_requires_team_result_entries` — a team game type's result shape is accepted when it matches its game type
- `testRDA001_IntegrationPositive_every_ranked_type_advises_under_sampled_pairs` — every ranked game type produces under-sampled matchmaking advice
- `testRDA001_IntegrationPositive_catalog_sync_admits_published_bot_results` — a bot newly admitted by `CAP-002` can immediately submit results

```gherkin
@RDA-002 @draft
Scenario: A structurally invalid record is rejected and never persisted
Test-type: Integration
  Given a batch containing a record that fails schema, identity, engine-pin, or score-consistency validation
  When the batch is ingested
  Then that record is rejected with a diagnostic error and no fact is written for it
  And a rejected record never prevents its valid neighbors in the same batch from being accepted
```

Evidence (negative direction):

- `testRDA002_IntegrationNegative_structural_records_never_persist`
- `testRDA002_IntegrationNegative_conflicting_battle_id_is_rejected` — reusing a battle ID for different content is rejected, not silently overwritten
- `testRDA002_IntegrationNegative_duplicate_within_one_batch_is_rejected`
- `testRDA002_IntegrationNegative_rejects_each_documented_structural_violation` — table-driven coverage of client identity, engine pin, arena dimensions, isTeam, score typing, 1224 rank system, and place-count bounds

```gherkin
@RDA-003 @draft
Scenario: Projections stay deterministic and reflect current moderation, independent of when facts were recorded
Test-type: Integration
  Given accepted facts recorded under registrations, bans, and exclusions that have since changed, and facts that have since been compacted into monthly rollups
  When projections are regenerated
  Then the result is identical whether the underlying facts are read from results/raw or from results/rollups
  And the projection reflects only accounts and bots that are currently registered, unbanned, and not excluded
```

Evidence:

- `testRDA003_IntegrationPositive_compaction_preserves_deterministic_projection`
- `testRDA003_IntegrationPositive_current_bans_and_registration_filter_existing_facts`

```gherkin
@RDA-004 @draft
Scenario: The dashboard reads generated projections rather than embedding data of its own
Test-type: E2E
  Given the published static site
  When a viewer selects a game type
  Then the page fetches that game type's versioned leaderboard projection and per-bot detail files
  And renders and sorts entries from that fetched data
```

Evidence:

- `testRDA004_E2EPositive_dashboard_references_versioned_projection_and_bot_details`

```gherkin
@RDA-005 @draft
Scenario: Catalog membership and eligibility gate both validation and matchmaking
Test-type: Integration
  Given the current active bot catalog, including which entries are individual bots and which are teams
  When results are validated and projections are regenerated
  Then only catalog-eligible bots and teams can be accepted for their matching game type
  And matchmaking advice is scoped to exactly the currently eligible bots and teams
```

Evidence (positive):

- `testRDA005_IntegrationPositive_catalog_membership_controls_result_validation_and_matchmaking`

Evidence (negative):

- `testRDA005_IntegrationNegative_rejects_ineligible_or_overlapping_team_entries` — an individual entered as a team, a team entered as an individual, and two teams sharing a member are each rejected; an unknown or inactive team member fails engine-pin validation outright

```gherkin
@RDA-006 @draft
Scenario: APS gives each distinct pairing equal weight within the active ranking epoch
Test-type: Integration
  Given eligible facts for the current behavior version and the catalog's active bot versions
  When a game type's leaderboard is generated
  Then each battle contributes the participant's share of that battle's total score, repeated battles are averaged within their exact participant pairing, and APS is 100 times the mean of those pairing averages
  And each distinct pairing has equal weight regardless of its battle count
  And superseded versions and facts from another behavior version do not contribute, while an active version with no samples has APS zero
```

Evidence:

- `testRDA006_IntegrationPositive_aps_weights_each_distinct_pairing_equally`
- `testRDA006_IntegrationNegative_live_ranking_excludes_superseded_and_wrong_epoch_results`

```gherkin
@RDA-007 @draft
Scenario: Publication freshness changes only when current ranking data changes
Test-type: Integration
  Given a current leaderboard and its publication timestamp
  When publication regenerates the current leaderboard
  Then a visible ranking change advances lastUpdatedAt to the publication time
  And identical ranking output preserves the previous lastUpdatedAt
  And creating a history snapshot alone does not advance lastUpdatedAt
```

Evidence:

- `testRDA007_IntegrationPositive_visible_ranking_change_advances_publication_time`
- `testRDA007_IntegrationPositive_changed_writers_explicitly_dispatch_pages`
- `testRDA007_IntegrationPositive_detects_ranking_regenerated_outside_publication`
- `testRDA007_IntegrationNegative_unchanged_ranking_preserves_publication_time`
- `testRDA007_IntegrationNegative_snapshot_alone_preserves_publication_time`

```gherkin
@RDA-008 @draft
Scenario: The first writer after a UTC month boundary preserves immutable cumulative history
Test-type: Integration
  Given the current cumulative leaderboard and the month in which it was last rolled over
  When a serialized writer first runs in a later UTC month
  Then it copies the current leaderboard and bot detail JSON byte for byte into a snapshot for every completed month before accepting new input
  And its first run initializes the current month without inventing earlier snapshots
  And it adds each snapshot to the history manifest without resetting the live cumulative ranking
  And it refuses to alter, delete, or overwrite an existing snapshot
```

Evidence:

- `testRDA008_IntegrationPositive_rollover_copies_each_missing_month_byte_for_byte`
- `testRDA008_IntegrationPositive_first_rollover_initializes_without_backfill`
- `testRDA008_IntegrationPositive_rollover_recovers_an_identical_partial_copy`
- `testRDA008_IntegrationNegative_rollover_refuses_to_overwrite_a_snapshot`

```gherkin
@RDA-009 @draft
Scenario: A dashboard viewer can distinguish current rankings from read-only monthly history
Test-type: E2E
  Given the publication history manifest and current and archived leaderboard data
  When a viewer selects Current or a completed month and a game type
  Then the dashboard loads the corresponding leaderboard and bot details
  And it shows when that ranking data last changed
  And an archived month is clearly identified as a read-only month-end snapshot
```

Evidence:

- `testRDA009_E2EPositive_dashboard_selects_current_or_archived_data`
- `testRDA009_E2ENegative_dashboard_marks_archived_rankings_read_only`
