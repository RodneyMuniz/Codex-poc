# Architecture Baseline

This document describes the current actual repository architecture at baseline time. It does not describe a target future architecture.

## Top-Level Structure Summary

- `agents/`
  - orchestration, PM, specialist agents, API router, config, cost tracking, telemetry
- `governance/`
  - role/state/tool policies, governance docs, execution log
- `kanban/`
  - board adapter and transition enforcement
- `memory/`
  - memory database and framework snapshots
- `projects/`
  - project workspaces such as `program-kanban/` and `tactics-game/`
- `scripts/`
  - CLI, operator API, worker process, control-room snapshot utilities
- `sessions/`
  - canonical SQLite store, approvals, backups, restore receipts
- `skills/`
  - manifest-controlled file and command tools
- `tests/`
  - runtime, governance, store, router, operator-surface, and state-machine tests
- `wrappers/`
  - LLM governance wrapper and logging
- repository root files:
  - `runtime.py`
  - `state_machine.py`
  - `hooks.py`
  - `README.md`
  - `pyproject.toml`

## Key Runtime Components

- Entry surfaces
  - `scripts/cli.py`
  - `scripts/operator_api.py`
  - `scripts/worker.py`
- Control layer
  - `agents/orchestrator.py::Orchestrator`
  - `agents/prompt_specialist.py::PromptSpecialistAgent`
  - `agents/pm.py::ProjectManagerAgent`
- Specialist execution layer
  - `agents/role_base.py::StudioRoleAgent`
  - `agents/architect.py`
  - `agents/developer.py`
  - `agents/design.py`
  - `agents/qa.py`
- LLM routing/runtime layer
  - `wrappers/llm_wrapper.py`
  - `agents/api_router.py`
  - `runtime.py`
- Governance/control layer
  - `governance/rules.py`
  - `governance/rules.yml`
  - `kanban/board.py`
  - `state_machine.py`
  - `skills/tools.py`
- Persistence layer
  - `sessions/store.py`
  - `memory/memory_store.py`
  - `wrappers/logging.py`
  - `agents/cost_tracker.py`

## Real Execution Path

### Intake path

1. User enters a request through `scripts/cli.py` or `scripts/operator_api.py`.
2. The script constructs `Orchestrator(ROOT)`.
3. `agents/orchestrator.py` loads environment, resolves runtime mode, and initializes:
   - `SessionStore`
   - `KanbanBoard`
   - `TelemetryRecorder`
   - `PromptSpecialistAgent`
4. Intake uses `PromptSpecialistAgent.process_input(...)`.
5. `PromptSpecialistAgent` calls `StudioRoleAgent.generate_json(...)`.
6. `StudioRoleAgent.generate_json(...)` uses `wrappers/llm_wrapper.py::llm_call_async(...)`.
7. The wrapper checks:
   - role/state permission
   - forbidden prompt content
   - allowed tool name
8. If checks pass, the model client is invoked and the result is logged to:
   - `logs/llm_calls.jsonl`
   - `memory/memory.db`
9. The orchestrator creates or updates a task in `sessions/studio.db` and keeps board state in sync through task acceptance/task_state fields.

### Execution path

1. The orchestrator dispatches work through `dispatch_request(...)` or `run_next_task(...)`.
2. The orchestrator creates a run record and team state in `SessionStore`.
3. `Orchestrator._execute_run(...)` instantiates `ProjectManagerAgent`.
4. `ProjectManagerAgent.execute_request(...)` builds a plan, creates subtasks, and advances review/build state through `KanbanBoard`.
5. PM issues a sealed worker manifest and updates run team state/context receipts.
6. `scripts/worker.py` validates the active worker manifest before specialist artifact work.
7. The worker runs a governed specialist agent or QA agent.
8. Specialist model calls use either:
   - `StudioRoleAgent.generate_text(...)` / `generate_json(...)` -> `llm_call_async(...)`, or
   - delegated API execution -> `agents/api_router.py::APIRouter.invoke_text(...)` -> `wrappers/llm_wrapper.py::llm_call(...)` -> `runtime.py::OpenAIResponsesRuntime.invoke(...)`
9. Artifact writes go through `skills/tools.py::write_project_artifact(...)` and are constrained to manifest-approved project artifact paths.
10. `SessionStore` records:
    - tasks
    - runs
    - approvals
    - messages
    - usage
    - execution packets/reservations
    - trace events
    - artifacts
    - visual artifacts

### Visual artifact path

1. PM receives a worker result.
2. `ProjectManagerAgent._register_media_outputs(...)` detects design artifact outputs.
3. `SessionStore.sync_visual_artifact(...)` writes canonical visual artifact records.
4. PM records `media_service_visual_registered` trace evidence.
5. Operator surfaces read canonical run evidence and wall snapshots from the store.

## Current Enforcement Points

- Wrapper enforcement
  - `wrappers/llm_wrapper.py`
  - `agents/api_router.py`
  - `agents/role_base.py`
- Fail-closed runtime selection
  - `agents/config.py`
  - `agents/sdk_runtime.py`
  - `scripts/sdk_runtime_bridge.py`
- Kanban/state enforcement
  - `governance/rules.py::check_transition(...)`
  - `state_machine.py::ensure_transition(...)`
  - `kanban/board.py::move_task(...)`
  - `sessions/store.py::update_task(...)`
- Manifest/file enforcement
  - `skills/tools.py`
  - `scripts/worker.py`
  - `sessions/store.py`
  - `wrappers/logging.py`
  - `memory/memory_store.py`
  - `agents/cost_tracker.py`

## Current Governance Points

- Role and state allowlists
  - `governance/rules.yml`
  - `governance/rules.py::check_role(...)`
- Forbidden prompt patterns
  - `governance/rules.yml`
  - `governance/rules.py::check_prompt(...)`
- Tool allowlists
  - `governance/rules.yml`
  - `governance/rules.py::check_tool_access(...)`
- Board transitions and review consensus
  - `governance/rules.yml`
  - `governance/rules.py::check_transition(...)`
  - `state_machine.py`
  - `kanban/board.py`

## Current State, Kanban, and Session Locations

- Canonical session database
  - `sessions/studio.db`
- Rendered board visibility file
  - `projects/program-kanban/execution/KANBAN.md`
- Approval legacy file path
  - `sessions/approvals.json`
- Backup/restore receipts
  - `sessions/backups/`
  - `sessions/backups/receipts/`
- Memory snapshots
  - `memory/framework_health.json`
  - `memory/session_summaries.json`
- Memory database
  - `memory/memory.db`
- LLM call log
  - `logs/llm_calls.jsonl`
- Execution usage log
  - `governance/execution_logs.md`

## Current Test Locations

- Governance/wrapper tests
  - `tests/test_llm_wrapper.py`
  - `tests/test_sdk_runtime.py`
- Board/state tests
  - `tests/test_state_machine.py`
  - `tests/test_kanban_board.py`
- Store/session tests
  - `tests/test_store.py`
- Router/orchestrator/PM tests
  - `tests/test_api_router.py`
  - `tests/test_orchestrator.py`
  - `tests/test_pm_flow.py`
- Operator/CLI surfaces
  - `tests/test_cli.py`
  - `tests/test_operator_api.py`
