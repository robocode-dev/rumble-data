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

Any violation raises before the write happens, so `catalog.json` can never hold an internally inconsistent catalog (`AC-RBC-004`, negative direction). Because `CAP-001`'s validation and aggregation re-read `catalog.json` fresh on every changed synchronization, a newly synchronized, eligible bot can submit and be ranked immediately — there is no separate activation step (`AC-RDA-001`'s `catalog_sync_admits_published_bot_results` facet).

`.github/workflows/sync-catalog.yml` checks the source at 23 minutes past every UTC hour. `sync_catalog.sync` compares normalized objects before writing. The workflow uses the resulting tracked-file difference to skip aggregation when nothing changed; a new bot, a new version, or any other reviewed source change immediately regenerates projections so the catalog and its eligibility effect land in one commit. It shares `rumble-publication-writer` concurrency with result ingestion so both paths can safely run month rollover before reading new input.
