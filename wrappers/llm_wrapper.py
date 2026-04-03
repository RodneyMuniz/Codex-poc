from __future__ import annotations

import time
from pathlib import Path
from typing import Any, Awaitable, Callable

from governance.rules import check_prompt, check_role, check_tool_access, load_policies
from memory.memory_store import query_memory, record_metric
from state_machine import default_state_for_role, normalize_task_state
from wrappers.logging import log_call


POLICIES = load_policies()


def _normalized_messages(messages: list[dict[str, Any]]) -> list[dict[str, str]]:
    normalized: list[dict[str, str]] = []
    for message in messages:
        content = str(message.get("content") or "").strip()
        if not content:
            continue
        normalized.append({"role": str(message.get("role") or "user"), "content": content})
    return normalized


def _memory_messages(messages: list[dict[str, str]], *, repo_root: str | Path | None = None) -> list[dict[str, str]]:
    joined = "\n".join(message["content"] for message in messages)
    memories = query_memory(joined, top_k=3, repo_root=repo_root)
    if not memories:
        return messages
    memory_lines = [f"- [{item['role']}/{item['state']}] {item['message'][:240]}" for item in memories]
    memory_context = "Relevant memory context:\n" + "\n".join(memory_lines)
    return [{"role": "system", "content": memory_context}, *messages]


def llm_call(
    role: str,
    task_state: str | None,
    messages: list[dict[str, Any]],
    *,
    invoke: Callable[[list[dict[str, str]]], Any],
    tool_name: str | None = None,
    repo_root: str | Path | None = None,
    metadata: dict[str, Any] | None = None,
) -> Any:
    resolved_state = normalize_task_state(task_state or default_state_for_role(role))
    normalized_messages = _normalized_messages(messages)
    check_role(role, resolved_state, POLICIES)
    for message in normalized_messages:
        check_prompt(message["content"], POLICIES)
    if tool_name:
        check_tool_access(role, tool_name, POLICIES)
    prepared_messages = _memory_messages(normalized_messages, repo_root=repo_root)
    started = time.perf_counter()
    try:
        response = invoke(prepared_messages)
    except Exception as exc:
        latency_ms = round((time.perf_counter() - started) * 1000, 3)
        record_metric(
            role=role,
            state=resolved_state,
            event_type="llm_call",
            latency_ms=latency_ms,
            success=False,
            token_usage=None,
            metadata={"tool_name": tool_name, "error": str(exc), **(metadata or {})},
            repo_root=repo_root,
        )
        raise
    latency_ms = round((time.perf_counter() - started) * 1000, 3)
    log_call(
        role=role,
        task_state=resolved_state,
        messages=prepared_messages,
        response=response,
        repo_root=repo_root,
        latency_ms=latency_ms,
        metadata={"tool_name": tool_name, **(metadata or {})},
    )
    return response


async def llm_call_async(
    role: str,
    task_state: str | None,
    messages: list[dict[str, Any]],
    *,
    invoke_async: Callable[[list[dict[str, str]]], Awaitable[Any]],
    tool_name: str | None = None,
    repo_root: str | Path | None = None,
    metadata: dict[str, Any] | None = None,
) -> Any:
    resolved_state = normalize_task_state(task_state or default_state_for_role(role))
    normalized_messages = _normalized_messages(messages)
    check_role(role, resolved_state, POLICIES)
    for message in normalized_messages:
        check_prompt(message["content"], POLICIES)
    if tool_name:
        check_tool_access(role, tool_name, POLICIES)
    prepared_messages = _memory_messages(normalized_messages, repo_root=repo_root)
    started = time.perf_counter()
    try:
        response = await invoke_async(prepared_messages)
    except Exception as exc:
        latency_ms = round((time.perf_counter() - started) * 1000, 3)
        record_metric(
            role=role,
            state=resolved_state,
            event_type="llm_call_async",
            latency_ms=latency_ms,
            success=False,
            token_usage=None,
            metadata={"tool_name": tool_name, "error": str(exc), **(metadata or {})},
            repo_root=repo_root,
        )
        raise
    latency_ms = round((time.perf_counter() - started) * 1000, 3)
    log_call(
        role=role,
        task_state=resolved_state,
        messages=prepared_messages,
        response=response,
        repo_root=repo_root,
        latency_ms=latency_ms,
        metadata={"tool_name": tool_name, **(metadata or {})},
    )
    return response
