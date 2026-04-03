from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from wrappers.llm_wrapper import llm_call


def _fake_response(text: str = "ok"):
    return SimpleNamespace(
        output_text=text,
        usage={
            "input_tokens": 12,
            "input_tokens_details": {"cached_tokens": 2},
            "output_tokens": 4,
            "output_tokens_details": {"reasoning_tokens": 1},
        },
    )


def test_llm_wrapper_logs_call_and_writes_memory(tmp_path):
    response = llm_call(
        "Architect",
        "In Progress",
        [{"role": "user", "content": "Summarize the architecture note."}],
        tool_name="model_client.create",
        repo_root=tmp_path,
        invoke=lambda prepared_messages: _fake_response(prepared_messages[-1]["content"]),
    )

    assert response.output_text == "Summarize the architecture note."
    assert (tmp_path / "logs" / "llm_calls.jsonl").exists()
    assert (tmp_path / "memory" / "memory.db").exists()


def test_llm_wrapper_rejects_prompt_specialist_outside_spec(tmp_path):
    with pytest.raises(PermissionError):
        llm_call(
            "PromptSpecialist",
            "In Progress",
            [{"role": "user", "content": "Create a spec packet."}],
            tool_name="model_client.create",
            repo_root=tmp_path,
            invoke=lambda prepared_messages: _fake_response(),
        )
