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

```gherkin
@RDA-001
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
@RDA-002
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
@RDA-003
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
@RDA-004
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
@RDA-005
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
