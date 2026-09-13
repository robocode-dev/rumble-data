---
id: CAP-002-design
type: design
status: active
links: [CAP-002]
title: Bot catalog synchronization — design
---

# CAP-002 — design

`scripts/sync_catalog.py` reads the currently stored `catalog.json`, requires it to declare an `https://` `source` URL, fetches that source with an explicit `User-Agent`, and requires the source to declare `schemaVersion: 1`. It replaces the local file with `schemaVersion`, `source`, `sourceCommit`, `sourceGeneratedAt` (both passed through from the source, unvalidated beyond presence), and `bots` — the source's bot list run through the same `common.normalized_catalog_bots` team-membership contract that `CAP-001`'s validation and aggregation use.

`normalized_catalog_bots` is the single shared rule both capabilities depend on:

- every entry's `teamMembers` must be an empty list, or a list of exactly two non-empty string identities;
- among entries with `status: active`, no two may share the same `name`+`version` identity;
- every member named in an active team's `teamMembers` must itself be an active, non-team catalog entry.

Any violation raises before the write happens, so `catalog.json` can never hold an internally inconsistent catalog (`AC-RBC-004`, negative direction). Because `CAP-001`'s validation and aggregation re-read `catalog.json` fresh on every run, a newly synchronized, eligible bot can submit and be ranked immediately — there is no separate activation step (`AC-RDA-001`'s `catalog_sync_admits_published_bot_results` facet).

`.github/workflows/sync-catalog.yml` runs synchronization on its own schedule (23 minutes past every UTC hour, per `GOVERNANCE.md`), then immediately regenerates projections in the same run, so a catalog change and its effect on eligibility and matchmaking land in the same commit.
