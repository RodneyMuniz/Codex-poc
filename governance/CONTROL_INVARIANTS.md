# Control Invariants

This document freezes the currently enforced control behavior in the Desktop repository baseline at `feature/governance-wrapper-kanban`. It is based on direct inspection of the current working tree, not on intended future architecture.

## 1. Wrapper-Required LLM Calls

- Invariant name: Wrapper-required LLM execution
- Description: Governed model execution must pass through `wrappers/llm_wrapper.py` so that role, state, prompt, and tool checks happen before provider invocation.
- Enforcement locations:
  - `wrappers/llm_wrapper.py`
    - `llm_call(...)`
    - `llm_call_async(...)`
  - `agents/api_router.py`
    - `APIRouter.invoke_text(...)`
    - `APIRouter.invoke_json(...)`
  - `agents/role_base.py`
    - `StudioRoleAgent.generate_text(...)`
    - `StudioRoleAgent.generate_json(...)`
- Failure behavior when violated:
  - `PermissionError` for invalid role/state or tool use
  - `ValueError` for forbidden prompt content
  - delegated execution raises `DelegatedExecutionBypassError` if it tries to skip `api_router`
- Current evidence/tests:
  - `tests/test_llm_wrapper.py::test_llm_wrapper_rejects_prompt_specialist_outside_spec`
  - `tests/test_api_router.py::test_api_router_rejects_delegated_packet_missing_authority_field`
  - `tests/test_orchestrator.py::test_start_task_fails_closed_when_prompt_specialist_tracked_request_lacks_api_router_authority`

## 2. Fail-Closed Runtime Selection

- Invariant name: Fail-closed runtime mode
- Description: The runtime may not switch into the legacy SDK path. The repository currently treats `sdk` mode as disabled because it bypasses the governance wrapper.
- Enforcement locations:
  - `agents/config.py`
    - `resolve_runtime_mode(...)`
  - `agents/sdk_runtime.py`
    - `SDKRuntimeAdapter.__init__(...)`
  - `scripts/sdk_runtime_bridge.py`
- Failure behavior when violated:
  - `RuntimeError` or `SDKRuntimeError` is raised immediately
- Current evidence/tests:
  - `tests/test_sdk_runtime.py::test_sdk_runtime_adapter_is_disabled_fail_closed`
  - `tests/test_sdk_runtime.py::test_resolve_runtime_mode_rejects_sdk`
  - `tests/test_sdk_runtime.py::test_sdk_runtime_bridge_is_disabled_fail_closed`

## 3. No-Fallback Specialist Intake

- Invariant name: No-fallback prompt-specialist path
- Description: Prompt-specialist intake no longer falls back to locally generated packets. If governance or model execution fails, the request fails.
- Enforcement locations:
  - `agents/prompt_specialist.py`
    - `PromptSpecialistAgent.process_input(...)`
  - `hooks.py`
    - `@pre_task("Spec")`
    - `@post_task("Spec")`
  - `agents/role_base.py`
    - `StudioRoleAgent.generate_json(...)`
- Failure behavior when violated:
  - underlying wrapper or model exception is raised to caller
  - no fallback packet is generated
- Current evidence/tests:
  - `tests/test_llm_wrapper.py::test_llm_wrapper_rejects_prompt_specialist_outside_spec`
  - `tests/test_orchestrator.py::test_start_task_fails_closed_when_prompt_specialist_tracked_request_lacks_api_router_authority`

## 4. Manifest and File-Write Restrictions

- Invariant name: Manifest/file write restriction
- Description: Delegated artifact writes must stay inside manifest-approved exact paths, and framework-owned internal writes must stay inside narrow canonical allowlists.
- Enforcement locations:
  - `skills/tools.py`
    - `require_worker_write_manifest(...)`
    - `validate_worker_write_manifest(...)`
    - `validate_project_artifact_path(...)`
    - `write_project_artifact(...)`
    - `validate_tool_access_from_manifest(...)`
    - `enforce_command_policy(...)`
  - `scripts/worker.py`
    - `_load_write_manifest(...)`
  - `sessions/store.py`
    - `_assert_internal_repo_path(...)`
    - `_assert_canonical_db_path(...)`
    - `_assert_framework_memory_path(...)`
    - `_assert_legacy_approval_path(...)`
    - `_assert_dispatch_backup_path(...)`
    - `_assert_restore_receipt_path(...)`
    - `_assert_kanban_render_path(...)`
  - `wrappers/logging.py`
    - `_assert_internal_log_path(...)`
  - `memory/memory_store.py`
    - `_assert_internal_memory_db_path(...)`
  - `agents/cost_tracker.py`
    - `_assert_internal_execution_log_path(...)`
- Failure behavior when violated:
  - `ValueError` for noncanonical artifact, command, database, memory, log, approval, backup, or KANBAN paths
- Current evidence/tests:
  - `tests/test_store.py::test_store_rejects_noncanonical_internal_db_path`
  - `tests/test_store.py::test_visual_artifact_requires_design_artifact_path`
  - `tests/test_llm_wrapper.py::test_llm_logging_rejects_noncanonical_internal_path`
  - `tests/test_api_router.py::test_cost_tracker_rejects_noncanonical_internal_log_path`

## 5. Kanban/State-Machine Authority

- Invariant name: Kanban/state-machine authority
- Description: Runtime task-state progression must follow the board/state machine rather than ad hoc status jumps.
- Enforcement locations:
  - `governance/rules.py`
    - `check_transition(...)`
  - `state_machine.py`
    - `can_transition(...)`
    - `ensure_transition(...)`
    - `determine_task_state(...)`
    - `state_to_store_status(...)`
  - `kanban/board.py`
    - `KanbanBoard.move_task(...)`
    - `KanbanBoard.record_review_vote(...)`
  - `sessions/store.py`
    - `SessionStore.update_task(...)`
  - `agents/orchestrator.py`
    - `_move_task_through_board(...)`
    - `move_task_to_board_state(...)`
- Failure behavior when violated:
  - `ValueError("Invalid state transition ...")`
  - `ValueError("Task state changes must go through KanbanBoard.move_task.")`
  - `KanbanBoardError` when review consensus is missing before `Done`
- Current evidence/tests:
  - `tests/test_state_machine.py::test_ensure_transition_rejects_skips`
  - `tests/test_kanban_board.py::test_local_kanban_board_tracks_task_state`
  - `tests/test_kanban_board.py::test_local_kanban_board_requires_two_review_votes_before_done`
  - `tests/test_store.py::test_program_kanban_ready_gate_requires_milestone_and_expected_output`
  - `tests/test_store.py::test_program_kanban_complete_requires_explicit_acceptance`

## 6. Tool Restriction Invariant

- Invariant name: Role and manifest tool restriction
- Description: Tool usage is restricted both by governance role policy and, for worker execution, by manifest-scoped allowed tools.
- Enforcement locations:
  - `governance/rules.py`
    - `check_tool_access(...)`
  - `governance/rules.yml`
    - role tool allowlists
  - `wrappers/llm_wrapper.py`
    - `tool_name=` checks before invoke
  - `skills/tools.py`
    - `validate_tool_access_from_manifest(...)`
- Failure behavior when violated:
  - `PermissionError` for role policy violation
  - `ValueError` for manifest-scoped tool violation
- Current evidence/tests:
  - `tests/test_llm_wrapper.py::test_llm_wrapper_rejects_prompt_specialist_outside_spec`
  - `tests/test_pm_flow.py::test_pm_worker_manifest_matches_tools_consumer_contract`

## 7. Single Approved Delegated Execution Path

- Invariant name: Single approved delegated execution path
- Description: Delegated specialist execution is intended to flow through orchestrator -> PM -> worker manifest -> governed role agent/API router. SDK bypass paths are disabled.
- Enforcement locations:
  - `agents/orchestrator.py`
    - `_execute_run(...)`
  - `agents/pm.py`
    - `_update_worker_team_state(...)`
    - `_register_media_outputs(...)`
  - `scripts/worker.py`
    - `_load_write_manifest(...)`
    - `_run(...)`
  - `agents/role_base.py`
    - `_assert_api_router_authority(...)`
  - `agents/api_router.py`
    - delegated authority validation and packet synchronization
- Failure behavior when violated:
  - `DelegatedExecutionBypassError` if delegated agent work attempts direct execution
  - `APIRouterError` or validation failure if delegated authority contract is incomplete
  - runtime-selection failure if `sdk` is requested
- Current evidence/tests:
  - `tests/test_api_router.py::test_api_router_allows_delegated_packet_with_complete_authority_contract`
  - `tests/test_api_router.py::test_api_router_rejects_delegated_packet_without_active_reservation`
  - `tests/test_pm_flow.py::test_pm_launches_worker_with_sealed_manifest_for_architect_subtask`
  - `tests/test_pm_flow.py::test_pm_runs_approved_developer_subtask_via_worker_manifest`

## 8. Workspace-Root Authority Assessment

- Assessment name: Workspace-root authority gap
- Description: The repository enforces internal repo-relative paths once the correct root is chosen, but it does not mechanically stop an operator or tool from opening a different duplicate folder outside the repo. This was observed during Phase 0 with a second `_AIStudio_POC` tree under `OneDrive\\Documentos`.
- Current evidence:
  - authoritative repo root contains `.git`, runtime code, governance code, and tests
  - duplicate path under `OneDrive\\Documentos` contains no `.git`, no runtime code, and only partial mirror content
  - the duplicate wiki file hash differs from the authoritative wiki file hash
- Why this is listed here:
  - it affects control authority and operator trust, but it is not currently enforced by in-repo runtime code
- Phase 0 status:
  - documented only
  - not changed in this baseline
