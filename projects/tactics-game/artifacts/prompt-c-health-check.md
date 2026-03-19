# Prompt C Health Check

## Audit Basis

- Audit date: 2026-03-20
- Audit target: current `_AIStudio_POC` implementation after Phase 0 and Phase 1 plus the Prompt B scenario run
- Reference baseline: the phase 0-2 build plan derived from the "AI Studio System Audit & Redesign Proposal" constraints
- Scope note: this audit treats the active repository as the compliance target; archived materials and external legacy source folders are called out separately and are not counted as active duplicates

## Runtime Snapshot

- Canonical runtime DB: `sessions/studio.db`
- Current row counts at audit time:
  - `tasks`: 6
  - `runs`: 6
  - `approvals`: 1
  - `delegation_edges`: 15
  - `messages`: 240
  - `usage_events`: 115
  - `artifacts`: 20
- Current task distribution:
  - `completed`: 4
  - `delegated`: 2
- Current run distribution:
  - `completed`: 4
  - `running`: 2

## Compliance Checklist

| Criterion | Status | Evidence | Remediation |
| --- | --- | --- | --- |
| Canonical governance documents are normalized and active duplicates are removed | compliant | Active repo has a single studio decision log at `governance/DECISION_LOG.md`, a single studio vision at `governance/VISION.md`, one project brief at `projects/tactics-game/governance/PROJECT_BRIEF.md`, and one rendered kanban at `projects/tactics-game/execution/KANBAN.md`. The old `PROJECT.md` lives only under `archive/legacy-manual-studio/`. | Keep future legacy imports in `archive/` until each file is mapped to a canonical destination. |
| Persistent session store exists | compliant | `sessions/store.py` initializes SQLite at `sessions/studio.db` and creates the `projects`, `tasks`, `runs`, `approvals`, `delegation_edges`, `messages`, `usage_events`, and `artifacts` tables. | No structural remediation needed for Phase 1. |
| Session store records pending approvals, current ticket, run state, and delegation chain | partially compliant | Approvals, run state, and delegation edges are first-class tables. The active task is inferable through `runs.task_id`, but there is no explicit project cursor or current-ticket pointer. | Add a project-level state table or explicit `current_task_id` field, and support resumable non-approval interruptions. |
| Model-reasoning matrix is documented | compliant | `governance/MODEL_REASONING_MATRIX.md` defines per-role runtime defaults, upgrade paths, reasoning depth, and cost posture. `agents/config.py` also contains role policies and env-var overrides. | Keep the doc and runtime policy in sync during Phase 2 upgrades. |
| Memory strategy is documented | compliant | `governance/MEMORY_MAP.md` clearly names SQLite as the runtime source of truth and maps policy, approvals, delegation, kanban rendering, and logs to canonical locations. | Expand the memory map once long-term retrieval or summarization services are added. |
| Tasks flow through a canonical queue with `Backlog -> Ready -> In Progress -> Review -> Done` | partially compliant | A queue exists, but the runtime statuses are `queued`, `delegated`, `in_progress`, `awaiting_approval`, `approved`, `completed`, `rejected`, and `failed`. The rendered board shows `Backlog`, `In Progress`, `Awaiting Approval`, `Done`, and `Blocked`, so `Ready` and `Review` are not first-class states. | Normalize the task state machine to the proposal's queue model and map approvals and delegation as flags or substates instead of extra top-level statuses. |
| Operator approvals pause and resume work correctly | partially compliant | `ProjectPO` is the only role that can request approval or mark completion. `resume_run` works when a run is in `paused_approval` and the approval is marked approved. | Add resume support for runs stopped by turn limits or recoverable errors, not just approval pauses. |
| Observability logs token usage, errors, and approvals | compliant | `agents/telemetry.py` writes `logs/app.log` and `logs/agent_events.jsonl`; `sessions/store.py` persists `usage_events`, `messages`, and `approvals`; `ProgramOrchestrator` records `run_finished`, `run_failed`, model usage totals, and approval decisions. | Add operator-facing rollups and per-run summaries so audits do not require direct DB inspection. |
| Skill system has been started with explicit schemas | compliant | `skills/schemas.py` defines typed inputs and outputs, `skills/registry.py` registers `FunctionTool` instances, and `skills/tools.py` implements file search, summarization, code diff, unit tests, and artifact writing. | Add a restricted patch/edit skill and richer file-read tooling for multi-step repair work. |
| Long-term memory integration has been started | partially compliant | Durable session history exists in SQLite, and governance documents provide stable non-ephemeral context. There is no retrieval layer, memory compaction, semantic search, or cross-run project memory synthesis yet. | Add a long-term memory service with retrieval tools, run summaries, and project-level memory compaction. |
| Model routing has been started | partially compliant | `agents/config.py` resolves models by role through env vars such as `AISTUDIO_MODEL_ARCHITECT` and `AISTUDIO_MODEL_DEVELOPER`. In practice, all defaults still collapse to `gpt-4.1-mini`. | Enforce role-specific policy from the matrix, add budget-aware fallbacks, and surface the resolved model per run in telemetry. |
| Completion is verified against task acceptance criteria | not compliant | Prompt B exposed a real gap: `Warrior Architecture Plan` and `Warrior Architecture Artifact Recovery` were marked completed even though `projects/tactics-game/artifacts/warrior_architecture_plan.md` does not exist. | Add task-level validators such as `required_files_exist`, `pytest_passed`, and `artifact_contains_sections` before `ProjectPO` can complete a task. |

## Key Findings

1. The framework is structurally on track.
   SQLite persistence, governance normalization, approvals, delegation tracking, typed skills, and basic telemetry are all real and working.

2. The biggest gaps are workflow semantics, not missing scaffolding.
   The system still needs the proposal's canonical queue states, stronger completion gates, and broader resume behavior.

3. The highest-risk issue is false completion.
   The current Project PO can close work based on conversation flow before acceptance criteria are machine-checked.

4. Long-term memory and model routing are present only in a first-cut form.
   Durable history exists, but not richer retrieval, summarization, or policy enforcement.

## Recommended Remediation Order

1. Add acceptance validators to task completion.
   This closes the most important reliability gap immediately.

2. Normalize the task status model to `Backlog`, `Ready`, `In Progress`, `Review`, and `Done`.
   Store approvals and delegation as supporting state instead of replacing queue semantics.

3. Add generic run resume for `max_turns` and recoverable failure states.
   Prompt B showed that this is needed for realistic repair loops.

4. Add a project/run cursor.
   Make the active ticket explicit instead of inferring it from open runs.

5. Extend memory beyond raw persistence.
   Add project summaries, retrieval helpers, and carry-forward memory between runs.

6. Improve observability ergonomics.
   Create a CLI or report command for run summaries, approval history, token usage totals, and failure analysis.
