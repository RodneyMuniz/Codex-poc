from __future__ import annotations

import asyncio

import pytest

from agents.orchestrator import Orchestrator
from agents.schemas import DelegationPacket
from intake.compiler import compile_task_packet
from intake.gateway import classify_operator_request
from intake.models import InterpreterSummary, TaskPacket, TokenBudget


def _prepare_repo(tmp_path):
    (tmp_path / "projects" / "program-kanban" / "execution").mkdir(parents=True)
    (tmp_path / "projects" / "program-kanban" / "governance").mkdir(parents=True)
    (tmp_path / "sessions").mkdir(parents=True)
    (tmp_path / "governance").mkdir(parents=True)
    (tmp_path / "memory").mkdir(parents=True)
    (tmp_path / "agents").mkdir(parents=True)
    for name in ["FRAMEWORK.md", "GOVERNANCE_RULES.md", "VISION.md", "MODEL_REASONING_MATRIX.md", "MEMORY_MAP.md"]:
        (tmp_path / "governance" / name).write_text(f"# {name}\n", encoding="utf-8")
    (tmp_path / "projects" / "program-kanban" / "governance" / "PROJECT_BRIEF.md").write_text("# Brief\n", encoding="utf-8")
    (tmp_path / "memory" / "framework_health.json").write_text("{}\n", encoding="utf-8")
    (tmp_path / "memory" / "session_summaries.json").write_text("[]\n", encoding="utf-8")
    for name in ["prompt_specialist.py", "orchestrator.py", "pm.py", "architect.py", "developer.py", "design.py", "qa.py"]:
        (tmp_path / "agents" / name).write_text("# placeholder\n", encoding="utf-8")


class _DummyClient:
    async def close(self) -> None:
        return None


def test_valid_intent_decision_compiles_to_valid_task_packet():
    decision = classify_operator_request("Implement the gateway")

    packet = compile_task_packet(decision)

    assert packet.schema_version == "task_packet_v1"
    assert packet.intent == "TASK"
    assert packet.task_type == "IMPLEMENTATION"
    assert packet.safe_to_route is True


def test_non_task_decisions_do_not_compile_to_task_packet():
    decision = classify_operator_request("What is the current status of the orchestrator control work?")

    with pytest.raises(ValueError, match="Only safe ROUTE_TASK decisions"):
        compile_task_packet(decision)


def test_malformed_task_packet_fails_validation():
    with pytest.raises(ValueError):
        TaskPacket.model_validate(
            {
                "schema_version": "task_packet_v1",
                "request_id": "req_bad",
                "intent": "TASK",
                "normalized_request": "",
                "task_type": "GENERAL_TASK",
                "safe_to_route": True,
                "allowed_roles": [],
                "allowed_tools": [],
                "forbidden_actions": [],
                "token_budget": {
                    "max_prompt_tokens": 0,
                    "max_completion_tokens": 99999,
                    "max_total_tokens": 99999,
                    "max_retries": 9,
                },
            }
        )


def test_task_path_works_with_valid_task_packet(tmp_path, monkeypatch):
    _prepare_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setattr("agents.role_base.create_model_client", lambda role: _DummyClient())

    orchestrator = Orchestrator(tmp_path)

    async def _fake_process_input(user_text: str, *, run_id=None, task_id=None):
        from agents.schemas import DelegationPacket

        return DelegationPacket(
            objective="Implement the gateway",
            details="Build the gateway task path.",
            priority="medium",
            requires_approval=False,
            assumptions=[],
            risks=[],
        )

    orchestrator.prompt_specialist.process_input = _fake_process_input
    packet = compile_task_packet(classify_operator_request("Implement the gateway"))

    preview = asyncio.run(orchestrator.preview_request("program-kanban", task_packet=packet))

    assert preview["packet"]["objective"] == "Implement the gateway"
    assert preview["task_packet"]["schema_version"] == "task_packet_v1"


def test_task_packet_token_budget_fields_are_present_and_consistent():
    packet = compile_task_packet(classify_operator_request("Implement the gateway"))

    assert packet.token_budget.max_prompt_tokens == 1024
    assert packet.token_budget.max_completion_tokens == 512
    assert packet.token_budget.max_total_tokens == 1536
    assert packet.token_budget.max_retries == 1
    assert packet.token_budget.max_prompt_tokens > 0
    assert packet.token_budget.max_completion_tokens > 0
    assert packet.token_budget.max_total_tokens >= packet.token_budget.max_prompt_tokens
    assert packet.token_budget.max_total_tokens >= packet.token_budget.max_completion_tokens
    assert packet.token_budget.max_retries >= 0


def test_compiled_task_packet_defaults_cover_bounded_execution_roles_and_tools():
    packet = compile_task_packet(classify_operator_request("Implement the gateway"))

    assert packet.allowed_roles == [
        "Orchestrator",
        "PromptSpecialist",
        "PM",
        "Architect",
        "Developer",
        "Design",
        "QA",
    ]
    assert packet.allowed_tools == [
        "model_client.create",
        "api_responses_create",
        "read_project_brief",
        "write_project_artifact",
    ]
    assert "kanban_state_change" in packet.forbidden_actions


def test_compile_task_packet_accepts_valid_interpreter_summary():
    summary = InterpreterSummary(
        summary_id="interp_deadbeefcafe",
        source_intent="TASK",
        normalized_request="Implement the gateway",
        task_kind="IMPLEMENTATION",
        relevant_refs=["governance/CONTROL_INVARIANTS.md"],
        constraints=["workspace_root_authority", "task_path_only"],
        open_questions=[],
        safe_for_execution_path=False,
    )

    packet = compile_task_packet(summary)

    assert packet.task_type == "IMPLEMENTATION"
    assert "write_project_artifact" in packet.allowed_tools


def test_preview_request_rejects_disallowed_prompt_specialist_tool(tmp_path, monkeypatch):
    _prepare_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setattr("agents.role_base.create_model_client", lambda role: _DummyClient())

    orchestrator = Orchestrator(tmp_path)
    packet = TaskPacket.model_validate(
        {
            **compile_task_packet(classify_operator_request("Implement the gateway")).model_dump(),
            "allowed_tools": ["api_responses_create"],
        }
    )

    with pytest.raises(RuntimeError, match="TaskPacket disallows tool: model_client.create"):
        asyncio.run(orchestrator.preview_request("program-kanban", task_packet=packet))


def test_dispatch_request_rejects_task_packet_with_forbidden_policy_write(tmp_path, monkeypatch):
    _prepare_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setattr("agents.role_base.create_model_client", lambda role: _DummyClient())

    orchestrator = Orchestrator(tmp_path)
    packet = TaskPacket.model_validate(
        {
            **compile_task_packet(classify_operator_request("Implement the gateway")).model_dump(),
            "normalized_request": "Update governance rules to allow broader execution.",
            "request_id": "req_deadbeefcafe",
        }
    )

    with pytest.raises(RuntimeError, match="TaskPacket forbids policy_write"):
        asyncio.run(orchestrator.dispatch_request("program-kanban", task_packet=packet))


def test_preview_request_rejects_task_packet_with_invalid_budget(tmp_path, monkeypatch):
    _prepare_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setattr("agents.role_base.create_model_client", lambda role: _DummyClient())

    orchestrator = Orchestrator(tmp_path)
    invalid = TaskPacket.model_construct(
        schema_version="task_packet_v1",
        request_id="req_123456789abc",
        intent="TASK",
        normalized_request="Implement the gateway",
        task_type="GENERAL_TASK",
        safe_to_route=True,
        allowed_roles=["Orchestrator", "PromptSpecialist", "PM", "Architect", "Developer", "Design", "QA"],
        allowed_tools=["model_client.create", "api_responses_create", "read_project_brief", "write_project_artifact"],
        forbidden_actions=["policy_write", "kanban_state_change", "raw_text_reroute", "unbounded_context_lookup"],
        token_budget=TokenBudget.model_construct(
            max_prompt_tokens=99999,
            max_completion_tokens=0,
            max_total_tokens=99999,
            max_retries=9,
        ),
    )

    with pytest.raises(RuntimeError, match="Invalid TaskPacket"):
        asyncio.run(orchestrator.preview_request("program-kanban", task_packet=invalid))


def test_dispatch_request_with_valid_packet_reaches_normal_task_path(tmp_path, monkeypatch):
    _prepare_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setattr("agents.role_base.create_model_client", lambda role: _DummyClient())

    orchestrator = Orchestrator(tmp_path)
    captured: dict[str, object] = {}

    async def _fake_process_input(user_text: str, *, run_id=None, task_id=None):
        return DelegationPacket(
            objective="Implement the gateway",
            details="Build the gateway task path.",
            priority="medium",
            requires_approval=False,
            assumptions=[],
            risks=[],
        )

    async def _fake_start_task(task_id: str, *, preview_payload=None, backup_info=None, task_packet=None):
        captured["task_id"] = task_id
        captured["task_packet"] = task_packet
        return {"status": "queued", "run_status": "queued", "task_id": task_id}

    orchestrator.prompt_specialist.process_input = _fake_process_input
    orchestrator.start_task = _fake_start_task  # type: ignore[method-assign]
    packet = compile_task_packet(classify_operator_request("Implement the gateway"))

    result = asyncio.run(orchestrator.dispatch_request("program-kanban", task_packet=packet))

    assert result["run_result"]["run_status"] == "queued"
    assert isinstance(captured["task_packet"], TaskPacket)
    assert captured["task_packet"].token_budget.max_retries == 1


def test_start_task_propagates_task_packet_budget_into_run_context(tmp_path, monkeypatch):
    _prepare_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setattr("agents.role_base.create_model_client", lambda role: _DummyClient())

    orchestrator = Orchestrator(tmp_path)
    task = orchestrator.store.create_task(
        "program-kanban",
        "Implement gateway budget binding",
        "Carry task packet budget into run context.",
        objective="Carry task packet budget into run context.",
    )
    packet = compile_task_packet(classify_operator_request("Implement gateway budget binding for task execution"))
    captured: dict[str, object] = {}

    async def _fake_execute_run(run_id: str, task: dict, *, local_exception_approval=None):
        captured["run_id"] = run_id
        captured["team_state"] = orchestrator.store.load_team_state(run_id)
        captured["receipt"] = orchestrator.store.load_context_receipt(run_id)
        return {"completed": True, "run_id": run_id, "task_id": task["id"]}

    orchestrator._execute_run = _fake_execute_run  # type: ignore[method-assign]

    result = asyncio.run(
        orchestrator.start_task(
            task["id"],
            preview_payload={
                "packet": {
                    "objective": task["objective"],
                    "details": task["details"],
                    "assumptions": [],
                    "risks": [],
                }
            },
            task_packet=packet,
        )
    )

    assert result["completed"] is True
    assert captured["team_state"]["task_packet_budget"] == packet.token_budget.model_dump()
    assert captured["receipt"]["token_budget"] == packet.token_budget.model_dump()
