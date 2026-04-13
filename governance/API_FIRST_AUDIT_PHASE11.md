# API-First Audit Phase 11

## Scope

This audit inspects the current governed v1 execution stack in the authoritative repository only:

- `C:\Users\rodne\OneDrive\Desktop\_AIStudio_POC`

It does not inspect or modify the known duplicate workspace:

- `C:\Users\rodne\OneDrive\Documentos\_AIStudio_POC`

This is an inspection-only audit. No runtime behavior was changed to produce this document.

## Method

Evidence used for this audit:

- Code inspection of:
  - `agents/orchestrator.py`
  - `agents/pm.py`
  - `agents/role_base.py`
  - `agents/api_router.py`
  - `agents/config.py`
  - `agents/prompt_specialist.py`
  - `agents/sdk_specialists.py`
  - `agents/sdk_runtime.py`
  - `scripts/worker.py`
  - `scripts/sdk_runtime_bridge.py`
  - `scripts/operator_api.py`
  - `scripts/cli.py`
  - `agents/cost_tracker.py`
  - `sessions/store.py`
- Focused tests:
  - `tests/test_role_base_usage.py`
  - `tests/test_api_router.py`
  - `tests/test_pm_flow.py::test_pm_runs_approved_developer_subtask_via_worker_manifest`
  - `tests/test_orchestrator.py::test_execute_run_selects_sdk_specialist_runtime_without_second_orchestrator`
  - `tests/test_sdk_runtime.py`
- Two targeted local probes against temporary repos:
  - tracked `PromptSpecialistAgent.process_input(...)`
  - tracked `DeveloperAgent.produce_artifact(...)`

Key verified outcomes from the probes:

- Tracked prompt-specialist execution returned a heuristic packet with `usage_events=0`.
- Tracked developer execution failed with:
  - `APIRouterError: Delegated execution requires an active budget reservation before job start: <run_id>:reservation.`

## A. Execution Path Map

### 1. Orchestrator local path

Actual path:

- `Orchestrator.run_next_task(...)` creates a run with `execution_mode="worker_only"` and calls `_execute_run(...)`.
  - Evidence: `agents/orchestrator.py:1983`, `agents/orchestrator.py:2018`
- `_execute_run(...)` sets `task["authority_delegated_work"] = True`, binds the `TaskPacket`, optionally marks SDK specialist runtime, and then calls `pm.execute_request(...)`.
  - Evidence: `agents/orchestrator.py:2020`, `agents/orchestrator.py:2037`, `agents/orchestrator.py:2073`, `agents/orchestrator.py:2134`

Assessment:

- The orchestrator itself is local, deterministic control code.
- It does not directly perform specialist model work.
- It always enters PM first for governed task execution.

### 2. PM path

Actual path:

- `ProjectManagerAgent.execute_request(...)` is local orchestration logic:
  - builds a plan
  - creates subtasks
  - runs subtasks
  - performs QA review and parent-task review
  - Evidence: `agents/pm.py:108`
- Specialist dispatch is performed by `_launch_worker_subtask(...)`, which shells out to `scripts/worker.py` via `subprocess.run(...)`.
  - Evidence: `agents/pm.py:510`, `agents/pm.py:539`

Assessment:

- PM is not API-first today.
- PM planning and dispatch are local Python logic.
- Specialist execution is wrapped in a local worker subprocess boundary, not a remote/API job boundary.

### 3. Role-agent path

Actual path:

- Specialist agents (`ArchitectAgent`, `DeveloperAgent`, `DesignAgent`) all inherit `StudioRoleAgent`.
- Their `produce_artifact(...)` methods call `generate_text(...)` with `run_id` and `task_id`.
  - Evidence:
    - `agents/architect.py`
    - `agents/developer.py`
    - `agents/design.py`
- In `StudioRoleAgent.generate_text(...)` and `generate_json(...)`:
  - if delegated work is requested (`run_id` and `task_id` present), the code chooses `api_responses_create`
  - it then calls `_assert_api_router_authority(...)`
  - and routes into `APIRouter.invoke_text(...)` / `invoke_json(...)`
  - Evidence:
    - `agents/role_base.py:50-57`
    - `agents/role_base.py:118-125`
    - `agents/role_base.py:232-239`

Local compatibility branch:

- If delegated work is not requested, `StudioRoleAgent` falls back to local `llm_call_async(...)` plus `model_client.create(...)`.
  - Evidence: `agents/role_base.py:81-96`, `agents/role_base.py:148-164`

Assessment:

- For tracked specialist agent model calls, the intended path is API-routed.
- The local direct model-client path still exists as a compatibility path when no governed run context is attached.

### 4. api_router path

Actual path:

- `APIRouter.invoke_text(...)` validates delegated authority, requires an active reservation for delegated work, and then calls `llm_call(...)` with `tool_name="api_responses_create"`.
  - Evidence: `agents/api_router.py:82`, `agents/api_router.py:134`, `agents/api_router.py:179`
- The underlying runtime is `OpenAIResponsesRuntime.invoke(...)`, which calls `client.responses.create(...)`.
  - Evidence:
    - `runtime.py`
    - `agents/api_router.py`
- Successful routed calls record:
  - `usage_events`
  - `execution_packets`
  - `execution_job_reservations`
  - markdown execution logs
  - Evidence: `agents/api_router.py:202`, `agents/cost_tracker.py:91`, `sessions/store.py:3400-3431`

Assessment:

- This is the strongest API-first execution surface in the repository.
- It is the only inspected path with explicit reservation, retry, stop-rule, usage, and cost telemetry.

### 5. Worker path

Actual path:

- PM launches `scripts/worker.py` locally via subprocess.
  - Evidence: `agents/pm.py:510-547`
- `worker.py` loads the runtime mode, validates the worker manifest, creates an agent run, then:
  - uses `SDKSpecialistCoordinator` when `runtime_mode == "sdk"`
  - otherwise instantiates local role-agent classes and calls their `produce_artifact(...)`
  - Evidence: `scripts/worker.py:57`, `scripts/worker.py:136-190`
- QA is also run locally inside `worker.py`.
  - Evidence: `scripts/worker.py:73`

Assessment:

- The worker path is local process execution even when the model call inside the worker may become API-routed.
- This is not API-first at the runtime boundary.

### 6. Wrapper/runtime path

Actual path:

- Public wrappers (`scripts/operator_api.py`, `scripts/cli.py`) are local entry wrappers that call the orchestrator/ingress.
- SDK mode uses a second local subprocess boundary:
  - `SDKRuntimeAdapter` shells out to `scripts/sdk_runtime_bridge.py`
  - the bridge uses the official OpenAI Agents SDK `Runner.run(...)`
  - Evidence:
    - `agents/sdk_runtime.py`
    - `scripts/sdk_runtime_bridge.py:134`

Assessment:

- The wrapper/runtime layer is local-process-first today.
- SDK specialist execution is API-backed at the model layer, but it is still mediated by a local bridge subprocess.

## B. Actual Default Behavior

### Default execution mode

- `resolve_runtime_mode()` defaults to `"custom"` unless `AISTUDIO_RUNTIME_MODE=sdk`.
  - Evidence: `agents/config.py:240-242`
- PM also normalizes to `"custom"` unless the run/team state says `"sdk"`.
  - Evidence: `agents/pm.py:328-329`

Conclusion:

- The actual default execution mode is `custom`.

### Which path is used for normal specialist work

Under the default `custom` runtime:

1. Orchestrator enters `_execute_run(...)`.
2. PM builds subtasks locally.
3. PM launches `scripts/worker.py` locally.
4. `worker.py` instantiates local role-agent objects.
5. Those role agents attempt to route their tracked model calls through `api_router`.

This means:

- The default runtime is not purely local model execution.
- It is also not fully API-first at the execution boundary.
- It is a hybrid:
  - local orchestrator
  - local PM
  - local worker process
  - API router inside the worker for tracked specialist LLM calls

### Under what conditions API delegation happens

API delegation is attempted when all of the following are true:

- a role-agent call has both `run_id` and `task_id`
- the model client is the modern `OpenAIChatCompletionClient`
- `_assert_api_router_authority(...)` passes

Evidence:

- `agents/config.py:328-329`
- `agents/role_base.py:232-239`

### Under what conditions local execution happens

Local execution still happens when:

- orchestrator/PM control logic runs
- PM launches `scripts/worker.py`
- QA review runs inside `worker.py`
- the SDK bridge subprocess runs
- a role-agent call does not have governed run context (`run_id`/`task_id`)
- a legacy/non-OpenAI client is used

Evidence:

- `agents/orchestrator.py:2134`
- `agents/pm.py:108`, `agents/pm.py:510`
- `scripts/worker.py:73`, `scripts/worker.py:136-190`
- `agents/role_base.py:81-96`, `agents/role_base.py:148-164`

## C. Bypass and Fallback Surfaces

### 1. Silent local fallback in Prompt Specialist

`PromptSpecialistAgent.process_input(...)` catches `Exception` and returns a heuristic `DelegationPacket`.

Evidence:

- `agents/prompt_specialist.py:16-40`

Observed probe:

- tracked `process_input(...)` returned:
  - `packet_objective = Implement the routing flow`
  - `usage_events = 0`
  - `messages = 0`

Why this matters:

- Router/reservation failures can silently degrade into a local heuristic packet instead of failing closed.
- This is not compatible with a strict API-first invariant for tracked governed execution.

### 2. Local compatibility path in `StudioRoleAgent`

`StudioRoleAgent` still contains a direct local LLM path through:

- `llm_call_async(...)`
- `model_client.create(...)`

Evidence:

- `agents/role_base.py:81-96`
- `agents/role_base.py:148-164`

Why this exists:

- It supports non-delegated or legacy-client usage.

Risk:

- It is a real compatibility path that bypasses reservation-backed API-first controls.

### 3. Synthesized authority fields that imply delegation but do not enforce it end-to-end

`_resolve_authority_context(...)` synthesizes:

- `authority_packet_id`
- `authority_job_id`
- `authority_token`
- `budget_max_tokens`
- `budget_reservation_id = <job_id>:reservation`
- `retry_limit`
- `early_stop_rule`

Evidence:

- `agents/role_base.py:287-314`

Risk:

- These fields make the path look fully delegated.
- But production code does not create the active reservation that `api_router` later requires.

### 4. Reservation enforcement exists, reservation creation does not

`APIRouter` correctly rejects delegated execution without an active reservation.

Evidence:

- `agents/api_router.py:134`
- `agents/api_router.py:455`
- `tests/test_api_router.py:413`
- `tests/test_api_router.py:458`

But production creation/sync of reservations was not found outside:

- `APIRouter` itself
- tests

Search result:

- production calls to `sync_execution_job_reservation(...)` were not found outside `agents/api_router.py`

Risk:

- The default governed specialist path attempts API routing but is not operational end-to-end unless some external actor creates reservations first.

Observed probe:

- tracked `DeveloperAgent.produce_artifact(...)` failed with:
  - `APIRouterError`
  - `Delegated execution requires an active budget reservation before job start: <run_id>:reservation.`

### 5. SDK path is separate from `api_router`

When `runtime_mode == "sdk"`:

- `worker.py` bypasses `APIRouter`
- `SDKSpecialistCoordinator` calls `SDKRuntimeAdapter`
- `SDKRuntimeAdapter` shells out to `scripts/sdk_runtime_bridge.py`
- the bridge uses `Runner.run(...)`

Evidence:

- `scripts/worker.py:136-190`
- `agents/sdk_specialists.py:36-90`
- `agents/sdk_runtime.py`
- `scripts/sdk_runtime_bridge.py:134`

Risk:

- This path is API-backed, but it is outside the `api_router` reservation/cost contract.

### 6. Compatibility and legacy surfaces

Notable compatibility surfaces:

- `custom` runtime default
- local worker subprocess model
- legacy-client branch in `StudioRoleAgent`
- prompt-specialist heuristic fallback
- legacy import tooling in CLI

These are not necessarily bugs, but they are incompatible with a hard API-first invariant unless explicitly carved out.

## D. Token/Cost Path Analysis

### Current propagation

Token/budget controls are propagated into governed tasks and subtasks through `TaskPacket` handling:

- orchestrator merges:
  - `budget_max_tokens`
  - `retry_limit`
  - `early_stop_rule`
  - Evidence: `agents/orchestrator.py`
- PM inherits those into subtasks:
  - Evidence: `agents/pm.py`
- `StudioRoleAgent._resolve_authority_context(...)` forwards them to `api_router`
  - Evidence: `agents/role_base.py:287-314`

### Delegated API-router path

When `api_router` is actually used:

- it enforces:
  - active reservation
  - `budget_max_tokens` consistency against reservation
  - retry cap
  - stop rule
- it records:
  - `usage_events`
  - `execution_packets`
  - `execution_job_reservations`
  - markdown execution log rows

Evidence:

- `agents/api_router.py:134-224`
- `agents/cost_tracker.py:91-122`
- `sessions/store.py:3400-3431`
- `tests/test_api_router.py:152`
- `tests/test_api_router.py:370`
- `tests/test_api_router.py:413`
- `tests/test_api_router.py:458`

Assessment:

- This is the only fully instrumented token/cost control path inspected in this audit.

### Local non-router path

When `StudioRoleAgent` falls back to local `llm_call_async(...)` / `model_client.create(...)`:

- usage may still be recorded after the call
- cost may still be estimated after the call
- but there is no reservation gate
- and no hard pre-call token reservation control

Evidence:

- `agents/role_base.py:81-96`
- `agents/role_base.py:148-164`
- `agents/role_base.py` `_record(...)`

Assessment:

- This path logs usage, but it bypasses the intended delegated budget-reservation contract.

### SDK path

The SDK specialist path:

- writes artifacts
- emits telemetry (`sdk_specialist_invocation`)
- does not call `CostTracker.record_api_usage(...)`
- no `usage_events`, `execution_packets`, or reservation enforcement were found in the SDK path

Evidence:

- `agents/sdk_specialists.py:57-90`
- `scripts/sdk_runtime_bridge.py:134`
- `agents/cost_tracker.py:91`
- `tests/test_sdk_runtime.py:32`

Assessment:

- The SDK path is currently outside the repository's strongest token/cost control surface.

## E. Recommended Enforcement Plan

This section proposes the minimum changes required to make API-first a real enforced invariant without redesigning the runtime.

### What should remain local

Keep local:

- orchestrator control logic
- PM planning/decomposition
- QA deterministic review/validation
- worker manifest validation
- wrapper scripts (`cli.py`, `operator_api.py`)

Reason:

- These are control-plane and filesystem-governance responsibilities, not specialist model execution.

### What must be delegated

For governed tracked execution, the following should be API-delegated only:

- `PromptSpecialistAgent.process_input(...)` when called with `run_id` and `task_id`
- `ArchitectAgent.produce_artifact(...)`
- `DeveloperAgent.produce_artifact(...)`
- `DesignAgent.produce_artifact(...)`
- any future tracked specialist/subagent LLM generation

### What should fail closed

Fail closed for governed tracked specialist work when any of the following are missing:

- active reservation
- complete authority packet
- supported API-backed execution mode
- usage/cost telemetry sink

For strict API-first, these should also fail closed:

- prompt-specialist heuristic fallback on tracked execution
- local `model_client.create(...)` compatibility path for tracked specialist work
- SDK specialist execution unless it satisfies the same reservation/usage contract as `api_router`

### Minimum change set

1. Create the execution-job reservation before specialist dispatch.
   - This is the smallest missing link between current role-agent routing and current router enforcement.
   - Without it, the default custom specialist path cannot satisfy `api_router`.

2. Remove the silent fallback for tracked prompt-specialist execution.
   - Keep the heuristic fallback only for explicitly untracked/local use, if needed.
   - For governed tracked execution, router failure should be visible and blocking.

3. Pick one governed specialist API path and enforce it.
   - Minimal option:
     - keep `api_router` as the required governed path for tracked specialist execution
     - treat SDK mode as unsupported for governed delegated specialist work until it emits equivalent usage/reservation evidence
   - Alternate option:
     - keep SDK mode, but only after adding equivalent reservation, retry, stop-rule, and usage/cost recording

4. Remove or hard-gate the local compatibility path for tracked specialist work.
   - The direct `llm_call_async(...)` path should remain available only when no governed delegated execution contract is active.

## F. Ranked Next Actions

### 1. Wire reservation creation into governed specialist dispatch

Why first:

- `api_router` already enforces reservation-backed execution.
- Production dispatch currently does not provide the reservation it requires.
- This is the smallest change that turns the current tracked specialist path from "intended" to "operational."

### 2. Make tracked prompt-specialist routing fail closed

Why second:

- It is the clearest silent local fallback in the governed path.
- It can hide router/control failures while still letting execution continue.
- This undermines any API-first auditability claim.

### 3. Decide the governed status of SDK specialist execution

Why third:

- SDK mode is selectable and has tests, but it is outside the router reservation/cost contract.
- Either:
  - hard-disable it for governed runs until parity exists, or
  - add equivalent reservation, retry, stop-rule, and cost telemetry before continuing to treat it as a supported governed execution path.

## Bottom Line

Specialist/subagent execution is not yet a fully enforced API-first invariant.

What is true today:

- tracked specialist role-agent model calls are designed to use `api_router`
- `api_router` has strong authority and budget controls
- SDK specialist execution exists as a separate API-backed path

What is also true today:

- the default runtime is still `custom`
- worker/process execution is still local
- production reservation creation for delegated API calls was not found
- tracked prompt-specialist execution can silently fall back to a local heuristic packet
- the SDK path does not appear to emit the same usage/reservation evidence as `api_router`

Therefore:

- the system is currently hybrid
- partially API-routed
- not yet provably API-first as an enforced end-to-end invariant

## Confidence

- Execution path map: HIGH
- Default runtime behavior: HIGH
- `api_router` delegated enforcement behavior: HIGH
- Silent prompt-specialist fallback finding: HIGH
- Missing production reservation-creation finding: MEDIUM-HIGH
- End-to-end success of the default specialist API path today: LOW
  - no passing production-like end-to-end test was found for PM -> real worker -> real role-agent -> successful routed API call with an active reservation
