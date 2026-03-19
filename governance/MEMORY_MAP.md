# Memory Map

## Canonical State

| Domain | Canonical Location | Notes |
| --- | --- | --- |
| Studio framework | `governance/FRAMEWORK.md` | Global operating model for the studio |
| Studio rules | `governance/GOVERNANCE_RULES.md` | Human and agent policy boundaries |
| Studio vision | `governance/VISION.md` | Strategic direction |
| Studio decisions | `governance/DECISION_LOG.md` | Consolidated decision record |
| Model policy | `governance/MODEL_REASONING_MATRIX.md` | Role-to-model policy and cost posture |
| Project brief | `projects/tactics-game/governance/PROJECT_BRIEF.md` | Project-specific goals and scope |
| Runtime tasks | `sessions/studio.db` table `tasks` | Source of truth for task queue |
| Runtime runs | `sessions/studio.db` table `runs` | Stores orchestration run lifecycle and team state |
| Pending approvals | `sessions/studio.db` table `approvals` | Replaces legacy `sessions/approvals.json` |
| Delegation chain | `sessions/studio.db` table `delegation_edges` | Tracks handoffs between Project PO, Architect, and Developer |
| Agent message history | `sessions/studio.db` table `messages` | Structured stream of framework events and chat messages |
| Token usage | `sessions/studio.db` table `usage_events` | Prompt and completion token usage per event |
| Artifacts | `sessions/studio.db` table `artifacts` | Summaries, notes, and run deliverables |
| Human-readable kanban | `projects/tactics-game/execution/KANBAN.md` | Rendered view derived from SQLite state |
| Runtime logs | `logs/app.log`, `logs/agent_events.jsonl` | Operational and telemetry output |
| Legacy prototype | `archive/legacy-manual-studio/` | Read-only recovery source |

## Update Rules

- Markdown files may describe state, but SQLite is the source of truth for runtime execution.
- Approval decisions must be written to SQLite before a paused run can resume.
- `projects/tactics-game/execution/KANBAN.md` must be regenerated after task state changes.
- Logs are append-only and should never be treated as the canonical source of task status.
