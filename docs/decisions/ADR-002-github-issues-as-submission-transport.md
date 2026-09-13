---
id: ADR-002
type: decision
status: inferred
author: agent
accepted-by: []
links: [CAP-001]
title: GitHub Issues, not a dedicated API, is the result-submission transport
---

# ADR-002 — GitHub Issues, not a dedicated API, is the result-submission transport

A client submits a result batch by opening a GitHub issue with a fixed title shape, the `result-submission` label, and one fenced JSON envelope in the body; ingestion runs as a GitHub Actions workflow triggered by the label (with a scheduled fallback) rather than as a hosted service with its own endpoint and authentication.

This constrains future work: adding a new transport (a webhook receiver, a dedicated API) is a materially different decision than extending the issue-based one, and anything that depends on "no separately hosted, separately secured service exists" (the fork drill, `G-003`) would need to be re-evaluated if that changed.

**Why:** GitHub's own identity (the issue author) and permission model double as the submitter-identity and access-control mechanism, so the project needs no accounts, tokens, or infrastructure of its own — directly serving the fork-recoverable, no-private-dependencies goal (`G-003`) and the CI-only-writer boundary (`C-002`). The tradeoff, documented as a current V1 limit rather than resolved here, is that fork-based pull-request submission is unsupported and GitHub cannot fully distinguish the Actions writer from a human collaborator without a secret-bearing organization app (see `C-002`).
