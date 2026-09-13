---
id: CH-001
type: change
status: open
links: [G-001, G-002, CAP-001, CAP-002]
title: Reliable Rumble ranking publication and history
---

# CH-001 — Reliable Rumble ranking publication and history

## Why

The generated repository data already includes reviewed bots beyond Orbit, but the public dashboard can remain stale because commits made by the catalog workflow do not trigger the Pages workflow. The current publication path also rebuilds on unchanged catalog polls, does not expose when ranking data last changed, and has no immutable month-end history.

## What

Make catalog and result writers share a serialized publication path that rolls over any missing UTC month snapshots before accepting new input, updates current ranking data only when its visible content changes, and explicitly requests a Pages deployment after a changed generated-site commit. Add a scheduled Pages reconciliation fallback that deploys only when the published site differs from the current `site/` tree.

Publish immutable cumulative month-end snapshots and a history manifest, add current/month selection and ranking freshness to the dashboard, document the exact APS and active-version rules, and add focused automated evidence for change detection, rollover immutability, history selection, timestamps, uneven APS samples, and active bot versions.

This is a plan-less change serving `G-001` and `G-002`; no campaign plan or use case is warranted because the behavior belongs within the two existing capabilities.

## Decisions

Add `ADR-003` to supersede `ADR-001`: accepted raw results remain immutable facts, current rankings remain disposable projections, and month-end dashboard snapshots become immutable publication records. Rankings remain cumulative rather than resetting each month; late accepted results update only the current projection and never rewrite historical snapshots.

## Documentation impact

Update the architecture and cross-cutting design overviews, both affected capability documents and criteria, repository operations guidance, dashboard copy, and the public README. The separate `tank-royale` documentation change will follow only after this change is accepted.
