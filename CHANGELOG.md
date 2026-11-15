# Changelog

## Unreleased

- Rank each bot only in the game types its catalog entry declares (`gameTypes`), in leaderboards, matchmaking advice and result validation; an entry without declared game types still plays every game type of its kind.

- Show a public Beta notice with a feedback link at the top of the rankings dashboard.
- Make catalog-driven ranking publication change-aware, explicitly deploy changed generated site data, expose ranking freshness, and add immutable cumulative month-end snapshots selectable from the dashboard.
