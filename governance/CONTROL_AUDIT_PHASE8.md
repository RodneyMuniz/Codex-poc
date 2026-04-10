# Control Audit Phase 8

Authoritative repository root audited: `C:\Users\rodne\OneDrive\Desktop\_AIStudio_POC`

Known non-authoritative duplicate intentionally not touched: `C:\Users\rodne\OneDrive\Documentos\_AIStudio_POC`

## Summary

This audit found that the Phase 8 control stack is materially stronger than the pre-gateway runtime, but the core invariants are not yet fully universal.

- Ingress separation is real on the primary natural-language entrypoints.
- TaskPacket validation is real on `preview_request`, `dispatch_request`, and `intake_request`.
- Policy proposal routing, status routing, workspace-root enforcement, and interpreter read-only behavior all have direct code and passing test evidence.
- The strongest remaining hardening gap is that execution can still begin without a TaskPacket through legacy task/run paths such as `Orchestrator.start_task`, `Orchestrator.run_next_task`, and `scripts/cli.py task create`.
- The policy lifecycle exists in code, but the currently supported apply target is not reachable through ingress: `classify_operator_request("Change governance review votes required to 3")` currently returns `NEEDS_SPLIT`, which causes the supported lifecycle tests to fail before proposal approval/apply can run.

## Evidence Snapshot

- Code inspected:
  - `intake/`
  - `agents/orchestrator.py`
  - `agents/pm.py`
  - `agents/role_base.py`
  - `governance/policy_lifecycle.py`
  - `workspace_root.py`
  - `scripts/cli.py`
  - `scripts/operator_api.py`
  - `skills/tools.py`

- Focused test runs:
  - `venv\Scripts\python.exe -m pytest tests/test_intent_gateway.py tests/test_task_packet.py tests/test_policy_proposal.py tests/test_status_response.py tests/test_workspace_root.py tests/test_interpreter_summary.py tests/test_cli.py tests/test_operator_api.py tests/test_role_base_usage.py tests/test_tools.py -q`
    - Result: `63 passed`
  - `venv\Scripts\python.exe -m pytest tests/test_pm_flow.py::test_pm_rejects_subtask_role_not_allowed_by_task_packet tests/test_pm_flow.py::test_pm_rejects_subtask_tool_not_allowed_by_task_packet -q`
    - Result: `2 passed`
  - `venv\Scripts\python.exe -m pytest tests/test_pm_flow.py::test_pm_launches_worker_with_sealed_manifest_for_architect_subtask tests/test_pm_flow.py::test_pm_worker_manifest_matches_tools_consumer_contract -q`
    - Result: `2 passed`
  - `venv\Scripts\python.exe -m pytest tests/test_orchestrator.py::test_start_task_seeds_context_receipt_from_preview_packet -q`
    - Result: `1 passed`
  - `venv\Scripts\python.exe -m pytest tests/test_policy_lifecycle.py -q`
    - Result: `1 passed, 5 failed`

- Direct classifier probe:
  - Input: `Change governance review votes required to 3`
  - Actual decision: `NEEDS_SPLIT`, `AMBIGUOUS`, `mixed_unsafe_intent`
  - Significance: the supported `CONSENSUS_REVIEW_VOTES_REQUIRED` lifecycle exists in `intake/compiler.py`, but its intended ingress phrase is not currently reachable through `intake/gateway.py`.

## A. Implemented Control Boundaries

### 1. Public ingress gating

- Boundary name: public ingress gating
- Intended invariant: operator natural-language input is classified before execution routing.
- Actual enforcement points:
  - `intake.gateway.classify_operator_request`
  - `intake.ingress.decide_operator_request`
  - `intake.ingress.preview_operator_request`
  - `intake.ingress.dispatch_operator_request`
  - `intake.ingress.intake_operator_request`
  - `scripts.operator_api.main` preview/dispatch branches route through ingress helpers
  - `scripts.cli.request` routes through `intake_operator_request`
- Test evidence:
  - `tests/test_intent_gateway.py::test_intent_gateway_routes_plain_task_request`
  - `tests/test_intent_gateway.py::test_dispatch_request_does_not_proceed_on_reject`
  - `tests/test_intent_gateway.py::test_dispatch_request_does_not_proceed_on_needs_split`
  - `tests/test_cli.py::test_cli_request_routes_through_ingress_first`
  - `tests/test_operator_api.py::test_operator_api_preview_routes_through_ingress_first`
  - `tests/test_operator_api.py::test_operator_api_dispatch_mixed_request_does_not_reach_execution`
- Assessment:
  - The primary public text-entry wrappers are gated correctly.
  - This is not yet universal across all public commands because `scripts/cli.py task create` and `scripts/cli.py run` bypass natural-language classification entirely.
- Confidence: MEDIUM

### 2. Orchestrator packet-only execution boundary

- Boundary name: orchestrator packet-only execution boundary
- Intended invariant: no orchestrator execution without a valid `TaskPacket v1`.
- Actual enforcement points:
  - `agents.orchestrator.Orchestrator._require_valid_task_packet`
  - `agents.orchestrator.Orchestrator._require_routable_task_packet`
  - `agents.orchestrator.Orchestrator.preview_request`
  - `agents.orchestrator.Orchestrator.dispatch_request`
  - `agents.orchestrator.Orchestrator.intake_request`
  - Internal raw-text helpers `_preview_request_from_text`, `_dispatch_request_from_text`, and `_intake_request_from_text` require `explicitly_internal=True` and compile a packet before calling packet-only entrypoints
- Test evidence:
  - `tests/test_intent_gateway.py::test_gateway_validation_rejects_malformed_output_shape`
  - `tests/test_intent_gateway.py::test_gateway_validation_rejects_wrong_schema_version`
  - `tests/test_intent_gateway.py::test_orchestrator_rejects_unsafe_task_packet`
  - `tests/test_intent_gateway.py::test_orchestrator_raw_text_entry_requires_explicit_internal_flag`
  - `tests/test_task_packet.py::test_task_path_works_with_valid_task_packet`
- Assessment:
  - The boundary is enforced on the ingress-facing orchestrator methods.
  - It is not yet enforced on all execution starts. `Orchestrator.start_task`, `Orchestrator.run_next_task`, `Orchestrator.resume_run`, and `_execute_run` all continue when no packet is present.
- Confidence: LOW

### 3. Task packet enforcement binding

- Boundary name: task packet enforcement binding
- Intended invariant: once a task is packetized, execution must stay bounded by packet roles, tools, forbidden actions, and budget.
- Actual enforcement points:
  - `intake.compiler.compile_task_packet`
  - `agents.orchestrator.Orchestrator._ensure_task_packet_allows_role`
  - `agents.orchestrator.Orchestrator._ensure_task_packet_allows_tool`
  - `agents.orchestrator.Orchestrator._enforce_task_packet_forbidden_actions`
  - `agents.orchestrator.Orchestrator._merge_task_packet_acceptance`
  - `agents.orchestrator.Orchestrator._bind_task_packet_to_team_state`
  - `agents.pm.ProjectManagerAgent._task_packet_for_task`
  - `agents.pm.ProjectManagerAgent._task_packet_for_subtask`
  - `agents.pm.ProjectManagerAgent._require_task_packet_role`
  - `agents.pm.ProjectManagerAgent._resolve_manifest_allowed_tools`
  - `agents.pm.ProjectManagerAgent._build_write_manifest`
  - `agents.role_base.StudioRoleAgent._enforce_task_packet_contract`
  - `skills.tools.validate_project_artifact_path`
  - `skills.tools.validate_tool_access_from_manifest`
- Test evidence:
  - `tests/test_task_packet.py::test_preview_request_rejects_disallowed_prompt_specialist_tool`
  - `tests/test_task_packet.py::test_dispatch_request_rejects_task_packet_with_forbidden_policy_write`
  - `tests/test_task_packet.py::test_start_task_propagates_task_packet_budget_into_run_context`
  - `tests/test_pm_flow.py::test_pm_rejects_subtask_role_not_allowed_by_task_packet`
  - `tests/test_pm_flow.py::test_pm_rejects_subtask_tool_not_allowed_by_task_packet`
  - `tests/test_pm_flow.py::test_pm_launches_worker_with_sealed_manifest_for_architect_subtask`
  - `tests/test_pm_flow.py::test_pm_worker_manifest_matches_tools_consumer_contract`
  - `tests/test_tools.py::test_write_project_artifact_rejects_sibling_path_under_active_manifest`
- Assessment:
  - Packet binding is strong once a packet exists and reaches execution.
  - The limitation is upstream: packetless tasks still exist, so this binding is conditional rather than universal.
- Confidence: MEDIUM

### 4. Policy proposal separation

- Boundary name: policy proposal separation
- Intended invariant: policy updates become `PolicyProposal` records, not task execution.
- Actual enforcement points:
  - `intake.gateway.classify_operator_request` routes policy-only text to `ROUTE_ADMIN`
  - `intake.compiler.compile_policy_proposal`
  - `intake.compiler.compile_task_packet` rejects non-task decisions
  - `intake.ingress.preview_operator_request` returns proposal preview for policy input
  - `intake.ingress.dispatch_operator_request` records proposals through `record_policy_proposal`
  - `intake.ingress.intake_operator_request` records proposals through `record_policy_proposal`
  - `intake.policy_store.record_policy_proposal`
  - `agents.orchestrator.preview_request` rejects non-TaskPacket payloads
- Test evidence:
  - `tests/test_policy_proposal.py::test_policy_update_decision_compiles_to_valid_policy_proposal`
  - `tests/test_policy_proposal.py::test_policy_update_does_not_compile_to_task_packet`
  - `tests/test_policy_proposal.py::test_task_execution_path_rejects_policy_proposal_misuse`
  - `tests/test_policy_proposal.py::test_policy_proposal_is_recorded_in_governance_storage_path`
  - `tests/test_policy_proposal.py::test_mixed_request_creates_neither_proposal_nor_task`
- Assessment:
  - Separation between policy proposals and task execution is implemented and passing for unsupported and generic policy requests.
  - The supported apply target is currently unreachable through the gateway due to classifier overlap, but the separation itself holds.
- Confidence: HIGH

### 5. Policy approval/apply separation from task execution

- Boundary name: policy approval/apply separation from task execution
- Intended invariant: approving and applying policy is outside task execution and cannot occur through the task path.
- Actual enforcement points:
  - `governance.policy_lifecycle.approve_policy_proposal`
  - `governance.policy_lifecycle.reject_policy_proposal`
  - `governance.policy_lifecycle.apply_policy_proposal`
  - `governance.policy_lifecycle._apply_supported_policy_change`
  - No call sites from `intake/`, `agents/orchestrator.py`, `scripts/operator_api.py`, or `scripts/cli.py`
  - `apply_policy_proposal` requires `APPROVED` state and a supported target before writing `governance/rules.yml`
- Test evidence:
  - Passing: `tests/test_policy_lifecycle.py::test_unsupported_policy_target_fails_closed`
  - Failing: `tests/test_policy_lifecycle.py` currently reports `5 failed, 1 passed` because the supported proposal phrase is classified as `NEEDS_SPLIT` before lifecycle approval/apply begins
  - Supporting separation evidence:
    - `tests/test_policy_proposal.py::test_task_execution_path_rejects_policy_proposal_misuse`
    - `tests/test_status_response.py::test_task_and_policy_update_still_follow_their_own_paths`
- Assessment:
  - Separation is structurally present: task execution does not call policy apply.
  - End-to-end confidence is reduced because the supported policy apply flow is not ingress-reachable and has failing tests.
- Confidence: MEDIUM

### 6. Status read-only separation

- Boundary name: status read-only separation
- Intended invariant: status requests are read-only and cannot mutate task or governance state.
- Actual enforcement points:
  - `intake.gateway.classify_operator_request` routes status text to `ROUTE_STATUS`
  - `intake.status.compile_status_response`
  - `intake.status._git_summary`
  - `intake.status._task_summary` opens SQLite with `mode=ro`
  - `intake.status._governance_summary`
  - `intake.ingress.preview_operator_request`
  - `intake.ingress.dispatch_operator_request`
  - `intake.ingress.intake_operator_request`
- Test evidence:
  - `tests/test_status_response.py::test_status_query_decision_produces_valid_status_response`
  - `tests/test_status_response.py::test_status_handling_is_read_only`
  - `tests/test_status_response.py::test_status_query_does_not_compile_to_task_packet`
  - `tests/test_status_response.py::test_status_query_does_not_compile_to_policy_proposal`
  - `tests/test_status_response.py::test_governance_status_query_routes_as_status_not_policy_update`
- Assessment:
  - Status is correctly separated from both task and policy execution.
  - The plane is intentionally limited in scope, but the v1 implementation is read-only.
- Confidence: HIGH

### 7. Workspace-root authority

- Boundary name: workspace-root authority
- Intended invariant: governed operations must fail closed outside the authoritative workspace root and must reject the known duplicate root.
- Actual enforcement points:
  - `workspace_root.classify_workspace_path`
  - `workspace_root.ensure_authoritative_workspace_root`
  - `workspace_root.ensure_authoritative_workspace_path`
  - `agents.orchestrator.Orchestrator.__init__`
  - `intake.interpreter.compile_interpreter_summary`
  - `intake.status.compile_status_response`
  - `intake.policy_store.policy_proposals_dir`
  - `governance.policy_lifecycle._rules_path`
  - `skills.tools._repo_root`
- Test evidence:
  - `tests/test_workspace_root.py::test_in_root_workspace_path_succeeds`
  - `tests/test_workspace_root.py::test_out_of_root_workspace_path_fails_closed`
  - `tests/test_workspace_root.py::test_known_duplicate_root_is_rejected`
  - `tests/test_workspace_root.py::test_tool_layer_rejects_known_duplicate_workspace_root`
  - `tests/test_workspace_root.py::test_orchestrator_rejects_known_duplicate_repo_root`
  - `tests/test_interpreter_summary.py::test_interpreter_workspace_root_enforcement_still_applies`
- Assessment:
  - Root authority is strongly enforced at the governed entrypoints audited here.
  - Lower-level data modules still rely on callers to pass authoritative roots, so this is not yet a fully pushed-down invariant.
- Confidence: HIGH

### 8. Interpreter read-only boundary

- Boundary name: interpreter read-only boundary
- Intended invariant: task intent is translated into a bounded read-only `InterpreterSummary`, not direct execution.
- Actual enforcement points:
  - `intake.interpreter.compile_interpreter_summary`
  - `intake.interpreter._bounded_refs`
  - `intake.interpreter._constraints`
  - `intake.interpreter._open_questions`
  - `intake.models.InterpreterSummary` validates `safe_for_execution_path=False`
  - `intake.compiler._load_interpreter_summary` accepts `IntentDecision` or prevalidated `InterpreterSummary`
- Test evidence:
  - `tests/test_interpreter_summary.py::test_safe_task_decision_produces_valid_interpreter_summary`
  - `tests/test_interpreter_summary.py::test_non_task_decisions_do_not_enter_interpreter_flow`
  - `tests/test_interpreter_summary.py::test_interpreter_remains_read_only`
  - `tests/test_interpreter_summary.py::test_task_packet_compiles_from_interpreter_summary`
  - `tests/test_interpreter_summary.py::test_unknown_task_kind_is_handled_safely`
- Assessment:
  - The interpreter is bounded to safe `ROUTE_TASK` input, root-checked references, and read-only summary generation.
  - No mutation path was found in the interpreter implementation.
- Confidence: HIGH

## B. Transitional / Residual Paths

| Description | Why it exists | Risk level | Recommendation |
| --- | --- | --- | --- |
| Internal raw-text helpers remain in `agents/orchestrator.py`: `_preview_request_from_text`, `_dispatch_request_from_text`, `_intake_request_from_text` | Backward/internal compatibility and test coverage for the old raw-text path | LOW | Keep for now, but remove later or isolate behind a test-only/internal adapter once packet-only starts are universal |
| Packetless execution is still possible through `Orchestrator.start_task`, `Orchestrator.run_next_task`, `Orchestrator.resume_run`, and `_execute_run` when no packet is stored | Legacy task-board execution predates TaskPacket and still supports existing task records | HIGH | Harden next: require a validated stored TaskPacket before any execution start or resume |
| `scripts/cli.py task create` creates tasks directly through `store.create_task`, and `scripts/cli.py run` can execute them later | Legacy operational CLI remains alongside the governed ingress path | HIGH | Harden or retire; if kept, force TaskPacket creation and attach it before the task is runnable |
| Supported policy apply intent is blocked by classifier overlap: `Change governance review votes required to 3` becomes `NEEDS_SPLIT` | The v1 gateway is keyword-based and the phrase matches both policy and task heuristics | HIGH | Harden classifier semantics for supported policy-admin requests and add an end-to-end passing lifecycle test |
| Policy approval/apply plane exists only as module functions plus tests; there is no audited operator-facing admin entrypoint for it | Lifecycle was implemented as a separate control plane before being exposed publicly | MEDIUM | Keep the separation, but add a governed admin entrypoint only after ingress classification is corrected |
| Workspace-root checks are concentrated at governed entrypoints; lower layers such as `SessionStore`, `MemoryStore`, and `KanbanBoard` are caller-trusting | Incremental hardening focused on entry surfaces first | MEDIUM | Harden constructors/factories so root authority is enforced deeper in the stack |
| Forbidden action enforcement for `policy_write` and `unbounded_context_lookup` is heuristic over normalized request text | Lightweight v1 guard intended to complement stronger role/tool/path controls | MEDIUM | Keep short term, then replace or supplement with action-plan and artifact-path level enforcement |

## C. Residual Risk Register

| Risk | Impact | Current mitigation | Recommended next action |
| --- | --- | --- | --- |
| Packetless execution start | Violates the core invariant `No execution without valid TaskPacket`; legacy tasks can still execute outside the packet contract | `preview_request`, `dispatch_request`, and `intake_request` enforce packets; downstream PM/tool checks bind packets when present | Make `start_task`, `run_next_task`, and `resume_run` fail closed unless a valid stored packet exists |
| Supported governance apply path is unreachable | The one implemented supported policy target cannot complete its intended ingress -> proposal -> approve/apply path; direct lifecycle tests fail | Proposal storage and lifecycle code exist; unsupported targets fail closed; generic policy proposals route to proposal-only storage | Fix intent classification for supported governance phrases and make `tests/test_policy_lifecycle.py` green end to end |
| Public compatibility CLI bypasses ingress | Operator or automation usage can still create and run legacy tasks without classification or packetization | The `request` command is gated; raw-text internal helpers are blocked unless explicitly internal | Retire or govern `task create` and `run` so every runnable task is born from ingress + packet compilation |
| Root authority is not pushed into all lower layers | Future direct imports could accidentally bypass root discipline if they skip the governed entrypoints | Orchestrator, intake, governance, and tool-layer entrypoints root-check now | Push root validation into store/board/memory constructors or expose only authoritative factories |
| Heuristic forbidden-action checks can miss novel wording | A risky request might avoid text triggers even though it should be blocked | Roles, tools, exact-path manifests, API router authority, and workspace-root constraints still bound execution | Move forbidden-action checks closer to actual planned actions, manifests, and artifact targets |

## D. Recommended Next Phase Options

1. Universal TaskPacket enforcement at execution start
   - Rationale: this closes the highest-severity invariant gap and removes the largest bypass class in one move.

2. End-to-end governed policy admin path repair
   - Rationale: the supported policy lifecycle already exists but is not ingress-reachable; fixing that yields a true proposal -> approve -> apply control story with passing evidence.

3. Compatibility surface retirement and lower-layer root hardening
   - Rationale: once packet starts and policy ingress are fixed, the next best hardening move is to remove or lock down the remaining trust-based legacy surfaces rather than layering more policy around them.

## E. Explicit Non-Goals

The current system does not yet do the following:

- It does not universally require a `TaskPacket` for every task/run execution start.
- It does not expose a governed operator-facing approval/apply API for policy proposals.
- It does not support arbitrary policy mutation through the lifecycle; v1 apply only supports `consensus.review_votes_required` in `governance/rules.yml`.
- It does not provide a rich status plane beyond limited v1 `SYSTEM`, `TASK`, `GOVERNANCE`, and `UNKNOWN` summaries.
- It does not eliminate every internal or legacy compatibility helper.
- It does not rely on semantic action inspection alone; some protections still depend on request-text heuristics plus role/tool/path boundaries.

## Audit Conclusion

The governed control architecture is real and test-backed in the ingress, policy-proposal, status, workspace-root, interpreter, and packet-binding layers. The system is not yet fully fail-closed against packetless execution, and the supported policy apply lifecycle is currently blocked by the gateway classifier. Those two items are the highest-priority next hardening targets.
