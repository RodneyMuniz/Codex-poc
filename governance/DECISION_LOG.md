# Decision Log

## 2026-03-19

- Adopt AutoGen as the first multi-agent framework because the active environment is Python 3.14 and must support persistent team state.
- Treat `projects/tactics-game/execution/KANBAN.md` as a human-readable execution view that will later be synchronized from the persistent session store.
- Archive the manual markdown-first prototype under `archive/legacy-manual-studio/` before replacing active paths.
- Use SQLite at `sessions/studio.db` as the Phase 1 source of truth for tasks, runs, approvals, messages, delegation edges, and artifacts.
- Make the Project PO the only role allowed to request approval or mark work complete, with Architect and Developer consulted through a real AutoGen team workflow.

## 2026-03-24

- Add automatic pre-dispatch backups of `sessions/studio.db` under `sessions/backups/` before the Orchestrator starts a new run.
- Treat `projects/<project>/artifacts/` as the only valid worker write boundary for framework-generated specialist outputs.
