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
