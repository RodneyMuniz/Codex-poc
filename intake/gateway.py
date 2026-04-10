from __future__ import annotations

import re

from intake.models import IntentDecision


_TASK_VERBS = (
    "implement",
    "build",
    "add",
    "fix",
    "update",
    "create",
    "write",
    "refactor",
    "restore",
    "design",
    "summarize",
    "analyze",
    "assess",
    "diagnose",
    "investigate",
    "review",
    "audit",
    "validate",
    "verify",
    "inspect",
)
_POLICY_SUBJECTS = (
    "policy",
    "governance",
    "rule",
    "rules",
    "permission",
    "permissions",
)
_POLICY_UPDATE_VERBS = (
    "allow",
    "edit",
    "change",
    "update",
    "modify",
    "write",
    "bypass",
)
_STATUS_PATTERNS = (
    r"\bwhat(?:'s| is)\b.*\bstatus\b",
    r"\bcurrent status\b",
    r"\bstatus of\b",
    r"\bprogress on\b",
    r"\bhow far along\b",
    r"\bwhere does\b.*\bstand\b",
    r"\bshow\b.*\bstatus\b",
)
_INJECTION_PATTERNS = (
    "ignore previous",
    "ignore governance",
    "bypass router",
    "bypass the wrapper",
    "skip kanban",
    "directly execute this change",
    "write directly to",
)
_TASK_REFERENCE_PATTERN = re.compile(r"\b[A-Z]+-\d+\b", re.IGNORECASE)
_BOARD_ACTION_PATTERNS = (
    "move ",
    "mark ",
    "set ",
    "back to ",
    "change status",
)
_SUPPORTED_POLICY_TARGET_PATTERNS = (
    re.compile(r"\breview votes required to \d+\b", re.IGNORECASE),
    re.compile(r"\brequire \d+ review votes\b", re.IGNORECASE),
    re.compile(r"\bset review vote requirement to \d+\b", re.IGNORECASE),
)


def normalize_operator_request(raw_text: str) -> str:
    collapsed = " ".join((raw_text or "").split())
    if not collapsed:
        return ""
    return collapsed[:160]


def _contains_status_request(lowered: str) -> bool:
    return any(re.search(pattern, lowered) for pattern in _STATUS_PATTERNS)


def _contains_policy_request(lowered: str) -> bool:
    has_subject = any(token in lowered for token in _POLICY_SUBJECTS)
    has_update_verb = any(re.search(r"\b" + re.escape(token) + r"\b", lowered) for token in _POLICY_UPDATE_VERBS)
    return has_subject and has_update_verb


def _scrub_supported_policy_target_phrases(lowered: str) -> str:
    scrubbed = lowered
    for pattern in _SUPPORTED_POLICY_TARGET_PATTERNS:
        scrubbed = pattern.sub(" ", scrubbed)
    return " ".join(scrubbed.split())


def _contains_task_request(lowered: str) -> bool:
    scrubbed = _scrub_supported_policy_target_phrases(lowered)
    return any(re.search(r"\b" + re.escape(token) + r"\b", scrubbed) for token in _TASK_VERBS)


def _contains_board_action_request(lowered: str) -> bool:
    if _TASK_REFERENCE_PATTERN.search(lowered) is None:
        return False
    if not any(token in lowered for token in _BOARD_ACTION_PATTERNS):
        return False
    return any(state in lowered for state in ("in progress", "in review", "complete", "completed", "todo", "backlog"))


def _reject(*, normalized_request: str, reason_codes: list[str]) -> IntentDecision:
    return IntentDecision(
        decision="REJECT",
        intent="AMBIGUOUS",
        contains_task_request=False,
        contains_policy_request=False,
        contains_status_request=False,
        safe_to_route=False,
        reason_codes=reason_codes,
        normalized_request=normalized_request or "empty request",
    )


def classify_operator_request(raw_text: str) -> IntentDecision:
    normalized_request = normalize_operator_request(raw_text)
    if not normalized_request:
        return _reject(normalized_request="empty request", reason_codes=["empty_request"])

    lowered = normalized_request.lower()

    if any(pattern in lowered for pattern in _INJECTION_PATTERNS):
        return _reject(
            normalized_request=normalized_request,
            reason_codes=["policy_bypass_attempt"],
        )

    if _contains_board_action_request(lowered):
        return _reject(
            normalized_request=normalized_request,
            reason_codes=["unsupported_board_control_request"],
        )

    contains_task_request = _contains_task_request(lowered)
    contains_policy_request = _contains_policy_request(lowered)
    contains_status_request = _contains_status_request(lowered)

    active_categories = sum(
        (
            contains_task_request,
            contains_policy_request,
            contains_status_request,
        )
    )

    if active_categories > 1:
        return IntentDecision(
            decision="NEEDS_SPLIT",
            intent="AMBIGUOUS",
            contains_task_request=contains_task_request,
            contains_policy_request=contains_policy_request,
            contains_status_request=contains_status_request,
            safe_to_route=False,
            reason_codes=["mixed_unsafe_intent"],
            normalized_request=normalized_request,
        )

    if contains_policy_request:
        return IntentDecision(
            decision="ROUTE_ADMIN",
            intent="POLICY_UPDATE",
            contains_task_request=False,
            contains_policy_request=True,
            contains_status_request=False,
            safe_to_route=False,
            reason_codes=["policy_update_detected"],
            normalized_request=normalized_request,
        )

    if contains_status_request:
        return IntentDecision(
            decision="ROUTE_STATUS",
            intent="STATUS_QUERY",
            contains_task_request=False,
            contains_policy_request=False,
            contains_status_request=True,
            safe_to_route=True,
            reason_codes=["status_query_detected"],
            normalized_request=normalized_request,
        )

    if contains_task_request:
        return IntentDecision(
            decision="ROUTE_TASK",
            intent="TASK",
            contains_task_request=True,
            contains_policy_request=False,
            contains_status_request=False,
            safe_to_route=True,
            reason_codes=["task_request_detected"],
            normalized_request=normalized_request,
        )

    return _reject(
        normalized_request=normalized_request,
        reason_codes=["ambiguous_intent"],
    )
