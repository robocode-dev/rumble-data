# Goals

G-xxx: who wants the system and why — the reason anything else in this corpus exists.

A goal artifact answers three questions: who wants it, what they want, and why it matters. New wishes enter as `status: proposed` — the proposed goals **are** the inbox; a human promotes a goal to `accepted` when the project commits to it. Retiring a goal means deleting its file and naming its ID in a successor's `supersedes:` field. Plans link the goals they serve, so every milestone traces back to someone who wanted it.

<!-- clue:index:start -->
- [G-001 — Bot authors and contributors want a trustworthy, auditable ranked leaderboard](G-001-trustworthy-public-rankings.md) · `accepted` — Battle contributors run ranked battles and bot authors want to see how their bots compare, but neither will trust a leaderboard that anyone could quietly edit.
- [G-002 — Maintainers want ingestion and ranking to run automatically with minimal manual toil](G-002-low-toil-automated-operation.md) · `accepted` — `GOVERNANCE.md` describes label-triggered ingestion with a scheduled fallback every 30 minutes, catalog synchronization on its own schedule, and automatic monthly compaction — moderators review…
- [G-003 — The project wants to keep running from public information alone, without private dependencies](G-003-fork-recoverable-operation.md) · `accepted` — `GOVERNANCE.md`'s "Fork drill" requires forking the repository once each quarter, enabling its workflows and Pages, running aggregation locally, and recording the result — explicitly "to show that…
<!-- clue:index:end -->
