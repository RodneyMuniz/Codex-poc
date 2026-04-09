# Repository Diagnostic

This diagnostic is grounded in direct inspection of the authoritative Desktop repository.

## Concise Tree

```text
_AIStudio_POC/
├── agents/
├── governance/
├── kanban/
├── logs/
├── memory/
├── projects/
│   ├── program-kanban/
│   └── tactics-game/
├── scripts/
├── sessions/
├── skills/
├── tests/
├── wrappers/
├── hooks.py
├── runtime.py
└── state_machine.py
```

## Key Subdirectories and Purpose

- `agents/`
  - control runtime, PM sequencing, specialist agents, API routing, config, cost tracking
- `governance/`
  - policy rules, governance docs, execution log
- `kanban/`
  - task-state transition authority
- `memory/`
  - memory database and framework snapshots
- `projects/program-kanban/`
  - current governed program board, artifacts, app, and project governance
- `scripts/`
  - operator/CLI entrypoints and worker runtime
- `sessions/`
  - SQLite store, approvals, backups, restore receipts
- `skills/`
  - file and command tools constrained by worker manifests
- `tests/`
  - control, router, store, PM, and operator-surface test coverage
- `wrappers/`
  - LLM wrapper and logging

## Runtime Entrypoints

- `scripts/cli.py`
  - human-facing CLI
- `scripts/operator_api.py`
  - operator service wrapper / structured JSON interface
- `scripts/worker.py`
  - specialist worker subprocess entrypoint

## Key Execution Files and Functions

- `agents/orchestrator.py`
  - `Orchestrator.__init__(...)`
  - `intake_request(...)`
  - `dispatch_request(...)`
  - `run_next_task(...)`
  - `_execute_run(...)`
  - `_move_task_through_board(...)`
- `agents/prompt_specialist.py`
  - `PromptSpecialistAgent.process_input(...)`
- `agents/pm.py`
  - `ProjectManagerAgent.execute_request(...)`
  - `_update_worker_team_state(...)`
  - `_register_media_outputs(...)`
- `agents/role_base.py`
  - `StudioRoleAgent.generate_text(...)`
  - `StudioRoleAgent.generate_json(...)`
  - `_assert_api_router_authority(...)`
- `agents/api_router.py`
  - `APIRouter.invoke_text(...)`
  - `APIRouter.invoke_json(...)`
- `runtime.py`
  - `OpenAIResponsesRuntime.invoke(...)`
- `skills/tools.py`
  - `write_project_artifact(...)`
  - `run_unit_tests(...)`
  - `code_diff(...)`
- `sessions/store.py`
  - `SessionStore.create_task(...)`
  - `SessionStore.update_task(...)`
  - `SessionStore.create_run(...)`
  - `SessionStore.update_run(...)`
  - `SessionStore.record_trace_event(...)`
  - `SessionStore.sync_visual_artifact(...)`
  - `SessionStore.get_run_evidence(...)`

## Key Enforcement Files and Functions

- `governance/rules.py`
  - `check_role(...)`
  - `check_prompt(...)`
  - `check_tool_access(...)`
  - `check_transition(...)`
- `wrappers/llm_wrapper.py`
  - `llm_call(...)`
  - `llm_call_async(...)`
- `kanban/board.py`
  - `KanbanBoard.move_task(...)`
  - `KanbanBoard.record_review_vote(...)`
- `state_machine.py`
  - `can_transition(...)`
  - `ensure_transition(...)`
  - `determine_task_state(...)`
- `sessions/store.py`
  - `_assert_internal_repo_path(...)`
  - `_assert_canonical_db_path(...)`
  - `_assert_framework_memory_path(...)`
  - `_assert_legacy_approval_path(...)`
  - `update_task(...)`
- `skills/tools.py`
  - `require_worker_write_manifest(...)`
  - `validate_worker_write_manifest(...)`
  - `validate_tool_access_from_manifest(...)`
  - `enforce_command_policy(...)`
  - `validate_project_artifact_path(...)`
- `agents/config.py`
  - `resolve_runtime_mode(...)`
- `agents/sdk_runtime.py`
  - `SDKRuntimeAdapter.__init__(...)`
- `scripts/sdk_runtime_bridge.py`
  - module-level fail-closed runtime error
- `wrappers/logging.py`
  - `_assert_internal_log_path(...)`
- `memory/memory_store.py`
  - `_assert_internal_memory_db_path(...)`
- `agents/cost_tracker.py`
  - `_assert_internal_execution_log_path(...)`

## Key Control-Related Tests

- `tests/test_llm_wrapper.py`
  - wrapper role enforcement
  - logging path restriction
  - memory/log creation
- `tests/test_sdk_runtime.py`
  - sdk fail-closed behavior
- `tests/test_state_machine.py`
  - legal/illegal transition behavior
- `tests/test_kanban_board.py`
  - board tracking
  - two-vote review consensus before `Done`
- `tests/test_store.py`
  - canonical store path enforcement
  - program-kanban ready gate
  - explicit acceptance gate for completion
  - visual artifact restrictions and provenance
- `tests/test_api_router.py`
  - delegated authority contract
  - retry/stop rules
  - budget reservation enforcement
- `tests/test_orchestrator.py`
  - prompt-specialist authority checks
  - delegated completion/breach behavior
  - deterministic direct board action path
- `tests/test_pm_flow.py`
  - worker manifest issuance
  - visual artifact registration before QA
  - tools/manifest contract alignment
- `tests/test_cli.py`
  - compliance state visibility
  - governance-blocked CLI failure
- `tests/test_operator_api.py`
  - structured error output
  - compliance state visibility
