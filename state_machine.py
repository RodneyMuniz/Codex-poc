from __future__ import annotations

from typing import Any


BOARD_STATE_IDEA = "Idea"
BOARD_STATE_SPEC = "Spec"
BOARD_STATE_TODO = "Todo"
BOARD_STATE_IN_PROGRESS = "In Progress"
BOARD_STATE_REVIEW = "Review"
BOARD_STATE_DONE = "Done"

BOARD_STATES = (
    BOARD_STATE_IDEA,
    BOARD_STATE_SPEC,
    BOARD_STATE_TODO,
    BOARD_STATE_IN_PROGRESS,
    BOARD_STATE_REVIEW,
    BOARD_STATE_DONE,
)

STORE_STATUS_TO_STATE = {
    "backlog": BOARD_STATE_IDEA,
    "ready": BOARD_STATE_TODO,
    "in_progress": BOARD_STATE_IN_PROGRESS,
    "in_review": BOARD_STATE_REVIEW,
    "completed": BOARD_STATE_DONE,
    "blocked": BOARD_STATE_REVIEW,
}

STATE_TO_STORE_STATUS = {
    BOARD_STATE_IDEA: "backlog",
    BOARD_STATE_SPEC: "backlog",
    BOARD_STATE_TODO: "ready",
    BOARD_STATE_IN_PROGRESS: "in_progress",
    BOARD_STATE_REVIEW: "in_review",
    BOARD_STATE_DONE: "completed",
}

ALLOWED_TRANSITIONS = {
    BOARD_STATE_IDEA: {BOARD_STATE_SPEC},
    BOARD_STATE_SPEC: {BOARD_STATE_TODO},
    BOARD_STATE_TODO: {BOARD_STATE_IN_PROGRESS},
    BOARD_STATE_IN_PROGRESS: {BOARD_STATE_REVIEW},
    BOARD_STATE_REVIEW: {BOARD_STATE_DONE},
    BOARD_STATE_DONE: set(),
}

ROLE_ALLOWED_STATES = {
    "orchestrator": {BOARD_STATE_IDEA, BOARD_STATE_SPEC, BOARD_STATE_TODO, BOARD_STATE_REVIEW},
    "prompt_specialist": {BOARD_STATE_SPEC},
    "pm": {BOARD_STATE_TODO, BOARD_STATE_IN_PROGRESS, BOARD_STATE_REVIEW},
    "architect": {BOARD_STATE_IN_PROGRESS, BOARD_STATE_REVIEW},
    "developer": {BOARD_STATE_IN_PROGRESS, BOARD_STATE_REVIEW},
    "design": {BOARD_STATE_IN_PROGRESS, BOARD_STATE_REVIEW},
    "qa": {BOARD_STATE_REVIEW},
}

DEFAULT_ROLE_STATES = {
    "orchestrator": BOARD_STATE_IDEA,
    "prompt_specialist": BOARD_STATE_SPEC,
    "pm": BOARD_STATE_TODO,
    "architect": BOARD_STATE_IN_PROGRESS,
    "developer": BOARD_STATE_IN_PROGRESS,
    "design": BOARD_STATE_IN_PROGRESS,
    "qa": BOARD_STATE_REVIEW,
}

STATE_ALIASES = {
    "idea": BOARD_STATE_IDEA,
    "spec": BOARD_STATE_SPEC,
    "todo": BOARD_STATE_TODO,
    "to_do": BOARD_STATE_TODO,
    "in_progress": BOARD_STATE_IN_PROGRESS,
    "in progress": BOARD_STATE_IN_PROGRESS,
    "review": BOARD_STATE_REVIEW,
    "in_review": BOARD_STATE_REVIEW,
    "done": BOARD_STATE_DONE,
    "complete": BOARD_STATE_DONE,
    "completed": BOARD_STATE_DONE,
    "backlog": BOARD_STATE_IDEA,
    "ready": BOARD_STATE_TODO,
    "blocked": BOARD_STATE_REVIEW,
}

FIRST_SLICE_STAGES = ("intake", "pm", "context_audit", "architect")
FIRST_SLICE_PM_BRANCH_CONTRACTS = (
    "pm_assumption_register_v1",
    "pm_clarification_questions_v1",
)
FIRST_SLICE_COMPLETION_CONTRACTS = {
    "intake": ("intake_request_v1",),
    "pm": ("pm_plan_v1",),
    "context_audit": ("context_audit_report_v1",),
    "architect": ("architecture_decision_v1",),
}
FIRST_SLICE_START_DEPENDENCIES = {
    "intake": (),
    "pm": (
        {
            "handoff": ("intake", "pm"),
            "contracts": ("intake_request_v1",),
        },
    ),
    "context_audit": (
        {
            "handoff": ("pm", "context_audit"),
            "contracts": ("pm_plan_v1",),
            "requires_pm_branch": True,
        },
    ),
    "architect": (
        {
            "stage_name": "pm",
            "contracts": ("pm_plan_v1",),
            "requires_pm_branch": True,
        },
        {
            "handoff": ("context_audit", "architect"),
            "contracts": ("context_audit_report_v1",),
        },
    ),
}


def normalize_task_state(state: str | None) -> str:
    if not state:
        return BOARD_STATE_IDEA
    lookup = str(state).strip().lower()
    return STATE_ALIASES.get(lookup, state)


def normalize_role_name(role: str | None) -> str:
    if not role:
        return "system"
    collapsed: list[str] = []
    previous_lower = False
    for character in role.strip():
        if character.isupper() and previous_lower:
            collapsed.append("_")
        collapsed.append(character)
        previous_lower = character.islower()
    return "".join(collapsed).replace(" ", "_").lower()


def state_from_store_status(status: str | None) -> str:
    if not status:
        return BOARD_STATE_IDEA
    normalized = str(status).strip().lower()
    return STORE_STATUS_TO_STATE.get(normalized, normalize_task_state(status))


def state_to_store_status(state: str) -> str:
    normalized = normalize_task_state(state)
    return STATE_TO_STORE_STATUS.get(normalized, "backlog")


def can_transition(current_state: str, next_state: str) -> bool:
    current = normalize_task_state(current_state)
    target = normalize_task_state(next_state)
    if current == target:
        return True
    return target in ALLOWED_TRANSITIONS.get(current, set())


def ensure_transition(current_state: str, next_state: str) -> None:
    if not can_transition(current_state, next_state):
        raise ValueError(f"Invalid task-state transition: {current_state} -> {next_state}")


def determine_task_state(task: dict[str, Any] | None) -> str:
    if not task:
        return BOARD_STATE_IDEA
    acceptance = task.get("acceptance") or {}
    explicit_state = acceptance.get("task_state")
    if explicit_state:
        return normalize_task_state(str(explicit_state))
    return state_from_store_status(str(task.get("status") or "backlog"))


def apply_task_state(task: dict[str, Any], task_state: str) -> dict[str, Any]:
    acceptance = dict(task.get("acceptance") or {})
    acceptance["task_state"] = normalize_task_state(task_state)
    updated = dict(task)
    updated["acceptance"] = acceptance
    updated["task_state"] = acceptance["task_state"]
    updated["status"] = state_to_store_status(acceptance["task_state"])
    return updated


def default_state_for_role(role: str | None) -> str:
    normalized = normalize_role_name(role)
    return DEFAULT_ROLE_STATES.get(normalized, BOARD_STATE_IN_PROGRESS)


def allowed_states_for_role(role: str | None) -> set[str]:
    normalized = normalize_role_name(role)
    return ROLE_ALLOWED_STATES.get(normalized, set(BOARD_STATES))


def review_votes_required() -> int:
    return 2


def review_consensus_satisfied(approvals: int, rejections: int = 0) -> bool:
    return approvals >= review_votes_required() and approvals > rejections


def _normalize_first_slice_stage_name(stage_name: str) -> str:
    normalized = str(stage_name).strip().lower()
    if normalized not in FIRST_SLICE_STAGES:
        raise ValueError(f"Unsupported first-slice stage: {stage_name}")
    return normalized


def _resolve_first_slice_non_trivial(workflow_run: dict[str, Any], non_trivial: bool | None) -> bool:
    if non_trivial is not None:
        return bool(non_trivial)
    scope = workflow_run.get("scope")
    if isinstance(scope, dict) and "non_trivial" in scope:
        return bool(scope["non_trivial"])
    return True


def _artifacts_by_contract(
    store: Any,
    workflow_run_id: str,
    *,
    stage_run_id: str | None = None,
) -> dict[str, list[dict[str, Any]]]:
    artifacts = store.list_workflow_artifacts(workflow_run_id, stage_run_id=stage_run_id)
    grouped: dict[str, list[dict[str, Any]]] = {}
    for artifact in artifacts:
        grouped.setdefault(str(artifact.get("contract_name") or ""), []).append(artifact)
    return grouped


def _matching_handoffs(
    store: Any,
    workflow_run_id: str,
    *,
    from_stage_name: str,
    to_stage_name: str,
) -> list[dict[str, Any]]:
    return [
        handoff
        for handoff in store.list_handoffs(workflow_run_id)
        if handoff.get("from_stage_name") == from_stage_name and handoff.get("to_stage_name") == to_stage_name
    ]


def _attempt_number(stage_run: dict[str, Any]) -> int:
    return int(stage_run.get("attempt_number") or 1)


def _stage_runs_for_name(store: Any, workflow_run_id: str, stage_name: str) -> list[dict[str, Any]]:
    return [
        stage_run
        for stage_run in store.list_stage_runs(workflow_run_id)
        if stage_run.get("stage_name") == stage_name
    ]


def _select_attempt_matched_stage_run(
    store: Any,
    workflow_run_id: str,
    *,
    source_stage_name: str,
    target_stage_run: dict[str, Any],
) -> tuple[dict[str, Any] | None, str | None]:
    target_attempt = _attempt_number(target_stage_run)
    candidates = [
        stage_run
        for stage_run in _stage_runs_for_name(store, workflow_run_id, source_stage_name)
        if _attempt_number(stage_run) == target_attempt
    ]
    if not candidates:
        return None, (
            f"{target_stage_run['stage_name']} start requires {source_stage_name} attempt {target_attempt}."
        )
    if len(candidates) > 1:
        return None, (
            f"{target_stage_run['stage_name']} start is ambiguous because multiple {source_stage_name} "
            f"attempts match attempt {target_attempt}."
        )
    return candidates[0], None


def _select_attempt_matched_handoff(
    store: Any,
    workflow_run_id: str,
    *,
    from_stage_name: str,
    to_stage_name: str,
    target_stage_run: dict[str, Any],
) -> tuple[dict[str, Any] | None, dict[str, Any] | None, str | None]:
    target_attempt = _attempt_number(target_stage_run)
    candidates: list[tuple[dict[str, Any], dict[str, Any]]] = []
    for handoff in _matching_handoffs(
        store,
        workflow_run_id,
        from_stage_name=from_stage_name,
        to_stage_name=to_stage_name,
    ):
        upstream_stage_run_id = handoff.get("stage_run_id")
        if not upstream_stage_run_id:
            continue
        upstream_stage_run = store.get_stage_run(upstream_stage_run_id)
        if upstream_stage_run is None:
            continue
        if upstream_stage_run.get("workflow_run_id") != workflow_run_id:
            continue
        if upstream_stage_run.get("stage_name") != from_stage_name:
            continue
        if _attempt_number(upstream_stage_run) != target_attempt:
            continue
        candidates.append((handoff, upstream_stage_run))
    if not candidates:
        return None, None, (
            f"{target_stage_run['stage_name']} start requires handoff {from_stage_name}->{to_stage_name} "
            f"for attempt {target_attempt}."
        )
    if len(candidates) > 1:
        return None, None, (
            f"{target_stage_run['stage_name']} start is ambiguous because multiple handoffs "
            f"{from_stage_name}->{to_stage_name} match attempt {target_attempt}."
        )
    handoff, upstream_stage_run = candidates[0]
    return handoff, upstream_stage_run, None


def _required_contract_artifact_ids(
    artifacts_by_contract: dict[str, list[dict[str, Any]]],
    contracts: tuple[str, ...],
) -> tuple[list[str], list[str]]:
    found_ids: list[str] = []
    missing_contracts: list[str] = []
    for contract_name in contracts:
        matching = artifacts_by_contract.get(contract_name, [])
        if not matching:
            missing_contracts.append(contract_name)
            continue
        found_ids.append(str(matching[0]["id"]))
    return found_ids, missing_contracts


def _pm_branch_artifact_id(artifacts_by_contract: dict[str, list[dict[str, Any]]]) -> str | None:
    for contract_name in FIRST_SLICE_PM_BRANCH_CONTRACTS:
        matching = artifacts_by_contract.get(contract_name, [])
        if matching:
            return str(matching[0]["id"])
    return None


def evaluate_first_slice_transition(
    store: Any,
    workflow_run_id: str,
    *,
    stage_name: str,
    transition: str,
    stage_run_id: str | None = None,
    non_trivial: bool | None = None,
) -> dict[str, Any]:
    normalized_stage = _normalize_first_slice_stage_name(stage_name)
    normalized_transition = str(transition).strip().lower()
    if normalized_transition not in {"start", "complete"}:
        raise ValueError(f"Unsupported first-slice transition: {transition}")

    workflow_run = store.get_workflow_run(workflow_run_id)
    if workflow_run is None:
        raise ValueError(f"Workflow run not found: {workflow_run_id}")

    stage_run = None
    if stage_run_id is not None:
        stage_run = store.get_stage_run(stage_run_id)
        if stage_run is None:
            raise ValueError(f"Stage run not found: {stage_run_id}")
        if stage_run.get("workflow_run_id") != workflow_run_id:
            raise ValueError("stage_run_id must belong to the requested workflow_run.")
        if stage_run.get("stage_name") != normalized_stage:
            raise ValueError("stage_run_id does not match the requested first-slice stage.")

    is_non_trivial = _resolve_first_slice_non_trivial(workflow_run, non_trivial)
    failures: list[str] = []
    checks: list[str] = []

    if normalized_transition == "complete":
        artifacts_by_contract = _artifacts_by_contract(
            store,
            workflow_run_id,
            stage_run_id=stage_run_id,
        )
        _, missing_contracts = _required_contract_artifact_ids(
            artifacts_by_contract,
            FIRST_SLICE_COMPLETION_CONTRACTS[normalized_stage],
        )
        for contract_name in missing_contracts:
            failures.append(f"{normalized_stage} completion requires {contract_name}.")
        checks.extend(FIRST_SLICE_COMPLETION_CONTRACTS[normalized_stage])
        if normalized_stage == "pm" and is_non_trivial:
            checks.extend(FIRST_SLICE_PM_BRANCH_CONTRACTS)
            if _pm_branch_artifact_id(artifacts_by_contract) is None:
                failures.append(
                    "pm completion for non-trivial work requires pm_assumption_register_v1 or pm_clarification_questions_v1."
                )
    else:
        for dependency in FIRST_SLICE_START_DEPENDENCIES[normalized_stage]:
            dependency_artifacts = _artifacts_by_contract(store, workflow_run_id)
            selected_handoff: dict[str, Any] | None = None
            if stage_run is not None:
                handoff_pair = dependency.get("handoff")
                if handoff_pair:
                    from_stage_name, to_stage_name = handoff_pair
                    selected_handoff, selected_stage_run, handoff_failure = _select_attempt_matched_handoff(
                        store,
                        workflow_run_id,
                        from_stage_name=from_stage_name,
                        to_stage_name=to_stage_name,
                        target_stage_run=stage_run,
                    )
                    if handoff_failure:
                        failures.append(handoff_failure)
                        selected_stage_run = None
                    if selected_stage_run is not None:
                        dependency_artifacts = _artifacts_by_contract(
                            store,
                            workflow_run_id,
                            stage_run_id=selected_stage_run["id"],
                        )
                else:
                    dependency_stage_name = dependency.get("stage_name")
                    if dependency_stage_name:
                        selected_stage_run, stage_failure = _select_attempt_matched_stage_run(
                            store,
                            workflow_run_id,
                            source_stage_name=str(dependency_stage_name),
                            target_stage_run=stage_run,
                        )
                        if stage_failure:
                            failures.append(stage_failure)
                            selected_stage_run = None
                        if selected_stage_run is not None:
                            dependency_artifacts = _artifacts_by_contract(
                                store,
                                workflow_run_id,
                                stage_run_id=selected_stage_run["id"],
                            )

            required_ids, missing_contracts = _required_contract_artifact_ids(
                dependency_artifacts,
                dependency.get("contracts", ()),
            )
            for contract_name in dependency.get("contracts", ()):
                checks.append(contract_name)
            for contract_name in missing_contracts:
                failures.append(f"{normalized_stage} start requires {contract_name}.")

            if dependency.get("requires_pm_branch") and is_non_trivial:
                checks.extend(FIRST_SLICE_PM_BRANCH_CONTRACTS)
                branch_artifact_id = _pm_branch_artifact_id(dependency_artifacts)
                if branch_artifact_id is None:
                    failures.append(
                        f"{normalized_stage} start for non-trivial work requires pm_assumption_register_v1 or pm_clarification_questions_v1."
                    )
                else:
                    required_ids.append(branch_artifact_id)

            handoff_pair = dependency.get("handoff")
            if handoff_pair:
                from_stage_name, to_stage_name = handoff_pair
                checks.append(f"handoff:{from_stage_name}->{to_stage_name}")
                if stage_run is not None:
                    if selected_handoff is None:
                        continue
                    handoffs = [selected_handoff]
                else:
                    handoffs = _matching_handoffs(
                        store,
                        workflow_run_id,
                        from_stage_name=from_stage_name,
                        to_stage_name=to_stage_name,
                    )
                if not handoffs:
                    failures.append(f"{normalized_stage} start requires handoff {from_stage_name}->{to_stage_name}.")
                    continue
                required_id_set = set(required_ids)
                if required_id_set and not any(
                    required_id_set.issubset(set(handoff.get("upstream_artifact_ids") or [])) for handoff in handoffs
                ):
                    failures.append(
                        f"{normalized_stage} start requires handoff {from_stage_name}->{to_stage_name} to reference required upstream artifacts."
                    )

    return {
        "allowed": not failures,
        "workflow_run_id": workflow_run_id,
        "stage_name": normalized_stage,
        "transition": normalized_transition,
        "stage_run_id": stage_run_id,
        "non_trivial": is_non_trivial,
        "checks": checks,
        "failures": failures,
    }


def ensure_first_slice_transition(
    store: Any,
    workflow_run_id: str,
    *,
    stage_name: str,
    transition: str,
    stage_run_id: str | None = None,
    non_trivial: bool | None = None,
) -> dict[str, Any]:
    evaluation = evaluate_first_slice_transition(
        store,
        workflow_run_id,
        stage_name=stage_name,
        transition=transition,
        stage_run_id=stage_run_id,
        non_trivial=non_trivial,
    )
    if not evaluation["allowed"]:
        raise ValueError(" ".join(evaluation["failures"]))
    return evaluation


def evaluate_first_slice_stage_start(
    store: Any,
    workflow_run_id: str,
    *,
    stage_name: str,
    stage_run_id: str | None = None,
    non_trivial: bool | None = None,
) -> dict[str, Any]:
    return evaluate_first_slice_transition(
        store,
        workflow_run_id,
        stage_name=stage_name,
        transition="start",
        stage_run_id=stage_run_id,
        non_trivial=non_trivial,
    )


def ensure_first_slice_stage_start(
    store: Any,
    workflow_run_id: str,
    *,
    stage_name: str,
    stage_run_id: str | None = None,
    non_trivial: bool | None = None,
) -> dict[str, Any]:
    return ensure_first_slice_transition(
        store,
        workflow_run_id,
        stage_name=stage_name,
        transition="start",
        stage_run_id=stage_run_id,
        non_trivial=non_trivial,
    )


def evaluate_first_slice_stage_completion(
    store: Any,
    workflow_run_id: str,
    *,
    stage_name: str,
    stage_run_id: str | None = None,
    non_trivial: bool | None = None,
) -> dict[str, Any]:
    return evaluate_first_slice_transition(
        store,
        workflow_run_id,
        stage_name=stage_name,
        transition="complete",
        stage_run_id=stage_run_id,
        non_trivial=non_trivial,
    )


def ensure_first_slice_stage_completion(
    store: Any,
    workflow_run_id: str,
    *,
    stage_name: str,
    stage_run_id: str | None = None,
    non_trivial: bool | None = None,
) -> dict[str, Any]:
    return ensure_first_slice_transition(
        store,
        workflow_run_id,
        stage_name=stage_name,
        transition="complete",
        stage_run_id=stage_run_id,
        non_trivial=non_trivial,
    )
