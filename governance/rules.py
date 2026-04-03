from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

from state_machine import normalize_role_name, normalize_task_state


def _rules_path(path: str | Path | None = None) -> Path:
    if path is not None:
        return Path(path).resolve()
    return Path(__file__).resolve().parent / "rules.yml"


@lru_cache(maxsize=4)
def load_policies(path: str | Path | None = None) -> dict[str, Any]:
    with _rules_path(path).open("r", encoding="utf-8") as handle:
        policies = yaml.safe_load(handle) or {}
    return policies if isinstance(policies, dict) else {}


def check_role(role: str, task_state: str, policies: dict[str, Any] | None = None) -> None:
    policies = policies or load_policies()
    normalized_role = normalize_role_name(role)
    normalized_state = normalize_task_state(task_state)
    roles = policies.get("roles") or {}
    role_policy = roles.get(normalized_role) or roles.get(normalized_role.replace("_", ""))
    if not isinstance(role_policy, dict):
        raise PermissionError(f"Role {role} is not registered in governance rules.")
    allowed_states = [normalize_task_state(item) for item in role_policy.get("allowed_states") or []]
    if normalized_state not in allowed_states:
        raise PermissionError(f"Role {role} cannot operate in {normalized_state} stage.")


def check_prompt(text: str, policies: dict[str, Any] | None = None) -> None:
    policies = policies or load_policies()
    lowered = text.lower()
    for forbidden in policies.get("forbidden_patterns") or []:
        token = str(forbidden).strip().lower()
        if token and token in lowered:
            raise ValueError(f"Prompt contains forbidden pattern: {token}")


def check_tool_access(role: str, tool_name: str, policies: dict[str, Any] | None = None) -> None:
    policies = policies or load_policies()
    normalized_role = normalize_role_name(role)
    roles = policies.get("roles") or {}
    role_policy = roles.get(normalized_role) or roles.get(normalized_role.replace("_", ""))
    if not isinstance(role_policy, dict):
        raise PermissionError(f"Role {role} is not registered in governance rules.")
    allowed_tools = {str(item).strip() for item in role_policy.get("tools") or []}
    if tool_name not in allowed_tools:
        raise PermissionError(f"Role {role} may not call tool {tool_name}.")


def check_transition(current_state: str, next_state: str, policies: dict[str, Any] | None = None) -> None:
    policies = policies or load_policies()
    current = normalize_task_state(current_state)
    target = normalize_task_state(next_state)
    allowed = {normalize_task_state(item) for item in (policies.get("transitions") or {}).get(current, [])}
    if current != target and target not in allowed:
        raise ValueError(f"Invalid state transition: {current} -> {target}")
