---
id: CAP-002-criteria
type: criteria
status: active
links: [CAP-002]
title: Bot catalog synchronization — acceptance criteria
ac-prefix: RBC
---

# CAP-002 — acceptance criteria

This capability's criterion ID canonicalizes its test tag the same way `CAP-001`'s do (`RBC004` → `RBC-004`); see `../CAP-001-ranked-result-pipeline/criteria.md` for the evidence-language note.

The `RBC-001`..`RBC-003` numbers are not used by any current test or corpus artifact — this is a normal gap, not a missing criterion; a future one would mint `RBC-005` next.

```gherkin
@RBC-004
Scenario: Synchronization keeps team membership valid and never advises invalid teams
Test-type: Integration
  Given a source catalog with individual bots and additive team entries
  When the catalog is synchronized
  Then valid team membership (an empty list, or exactly two known, non-team members) is preserved
  And a team naming an unknown or inactive member is rejected outright
  And two teams that would share a member are never advised as an under-sampled pairing
```

Evidence (positive):

- `testRBC004_IntegrationPositive_catalog_sync_preserves_valid_team_membership`

Evidence (negative):

- `testRBC004_IntegrationNegative_catalog_sync_rejects_unknown_team_member`
- `testRBC004_IntegrationNegative_teams_sharing_a_member_are_never_advised`
