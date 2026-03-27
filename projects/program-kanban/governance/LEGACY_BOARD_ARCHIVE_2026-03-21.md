# Program Kanban Legacy Board Archive

This note records the decision to retire the imported legacy `Program Kanban` task set from the active board while preserving it as historical reference.

Archive payload:
- Full task export: `LEGACY_BOARD_ARCHIVE_2026-03-21.json`
- Archived task count: `24`
- Archived completed tasks: `15`
- Archived backlog tasks: `9`
- Archive date: `2026-03-21`

Why this archive exists:
- The current framework is now SQLite-first and operator-facing.
- The imported legacy board mixed historical completions, markdown-era assumptions, and a few freshly added reset tasks.
- Keeping those tasks live in the active board would make the new implementation queue look more complete than it really is.
- We want a clean implementation surface for the new Program Kanban while preserving prior thinking and accepted legacy capabilities.

What remains true from the archived work:
- The old board proved demand for a lightweight operator wall.
- The old board proved that milestone grouping, task-id copy, and compact operator-friendly task presentation were useful.
- The old board also surfaced helpful supporting ideas such as recent updates, lightweight hierarchy cues, scoped project filters, and consistency checks.

How to use this archive:
- Treat the JSON export as the source for historical Program Kanban task memory.
- Treat the new active board as the implementation queue for the new framework-backed board.
- If we need to revisit a legacy decision, map the old `TGD-*` item to the fresh backlog item created during the `2026-03-21` reset instead of reopening the archived board directly.
