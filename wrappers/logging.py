from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from memory.memory_store import add_interaction, record_metric


def _utc_now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def _repo_root(repo_root: str | Path | None = None) -> Path:
    return Path(repo_root or Path.cwd()).resolve()


def extract_token_usage(response: Any) -> dict[str, int]:
    usage = getattr(response, "usage", None)
    if isinstance(usage, dict):
        input_details = usage.get("input_tokens_details") or {}
        output_details = usage.get("output_tokens_details") or {}
        return {
            "input_tokens": int(usage.get("input_tokens") or usage.get("prompt_tokens") or 0),
            "cached_input_tokens": int(input_details.get("cached_tokens") or 0),
            "output_tokens": int(usage.get("output_tokens") or usage.get("completion_tokens") or 0),
            "reasoning_tokens": int(output_details.get("reasoning_tokens") or 0),
        }
    if usage is None:
        return {"input_tokens": 0, "cached_input_tokens": 0, "output_tokens": 0, "reasoning_tokens": 0}
    input_details = getattr(usage, "input_tokens_details", None)
    output_details = getattr(usage, "output_tokens_details", None)
    return {
        "input_tokens": int(getattr(usage, "input_tokens", getattr(usage, "prompt_tokens", 0)) or 0),
        "cached_input_tokens": int(getattr(input_details, "cached_tokens", 0) or 0),
        "output_tokens": int(getattr(usage, "output_tokens", getattr(usage, "completion_tokens", 0)) or 0),
        "reasoning_tokens": int(getattr(output_details, "reasoning_tokens", 0) or 0),
    }


def extract_response_text(response: Any) -> str:
    if isinstance(response, str):
        return response
    output_text = getattr(response, "output_text", None)
    if isinstance(output_text, str):
        return output_text
    content = getattr(response, "content", None)
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return json.dumps(content, ensure_ascii=True, default=str)
    final_output = getattr(response, "final_output", None)
    if isinstance(final_output, str):
        return final_output
    return json.dumps(response, ensure_ascii=True, default=str)


def log_call(
    *,
    role: str,
    task_state: str,
    messages: list[dict[str, str]],
    response: Any,
    repo_root: str | Path | None = None,
    latency_ms: float | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    root = _repo_root(repo_root)
    log_path = root / "logs" / "llm_calls.jsonl"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    usage = extract_token_usage(response)
    response_text = extract_response_text(response)
    record = {
        "created_at": _utc_now(),
        "role": role,
        "state": task_state,
        "messages": messages,
        "response": response_text,
        "usage": usage,
        "latency_ms": latency_ms,
        "metadata": metadata or {},
    }
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=True, default=str) + "\n")
    for message in messages:
        content = str(message.get("content") or "").strip()
        if content:
            add_interaction(role, task_state, content, repo_root=root)
    if response_text.strip():
        add_interaction(role, task_state, response_text, repo_root=root)
    record_metric(
        role=role,
        state=task_state,
        event_type="llm_call",
        latency_ms=latency_ms,
        success=True,
        token_usage=usage,
        metadata=metadata or {},
        repo_root=root,
    )
    return record
