from __future__ import annotations

import asyncio

from agents.orchestrator import Orchestrator
from agents.schemas import DelegationPacket, ExecutionJobReservation, ExecutionPacketAuthority, ExecutionPacketTelemetry


def _prepare_repo(tmp_path):
    (tmp_path / "projects" / "program-kanban" / "execution").mkdir(parents=True)
    (tmp_path / "projects" / "program-kanban" / "governance").mkdir(parents=True)
    (tmp_path / "projects" / "tactics-game" / "execution").mkdir(parents=True)
    (tmp_path / "projects" / "tactics-game" / "governance").mkdir(parents=True)
    (tmp_path / "sessions").mkdir(parents=True)
    (tmp_path / "governance").mkdir(parents=True)
    (tmp_path / "memory").mkdir(parents=True)
    for name in ["FRAMEWORK.md", "GOVERNANCE_RULES.md", "VISION.md", "MODEL_REASONING_MATRIX.md", "MEMORY_MAP.md"]:
        (tmp_path / "governance" / name).write_text(f"# {name}\n", encoding="utf-8")
    (tmp_path / "projects" / "program-kanban" / "governance" / "PROJECT_BRIEF.md").write_text("# Brief\n", encoding="utf-8")
    (tmp_path / "projects" / "tactics-game" / "governance" / "PROJECT_BRIEF.md").write_text("# Brief\n", encoding="utf-8")
    (tmp_path / "memory" / "framework_health.json").write_text("{}\n", encoding="utf-8")
    (tmp_path / "memory" / "session_summaries.json").write_text("[]\n", encoding="utf-8")
    (tmp_path / "agents").mkdir(parents=True)
    for name in ["prompt_specialist.py", "orchestrator.py", "pm.py", "architect.py", "developer.py", "design.py", "qa.py"]:
        (tmp_path / "agents" / name).write_text("# placeholder\n", encoding="utf-8")


class _DummyClient:
    async def close(self) -> None:
        return None


def test_small_task_routes_to_tier_3(tmp_path, monkeypatch):
    _prepare_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setattr("agents.role_base.create_model_client", lambda role: _DummyClient())
    orchestrator = Orchestrator(tmp_path)

    async def _fake_process_input(user_text: str, *, run_id=None, task_id=None):
        return DelegationPacket(
            objective="Summarize the current backlog health",
            details="Produce a short markdown summary of open backlog risk.",
            priority="medium",
            requires_approval=False,
            assumptions=[],
            risks=[],
        )

    orchestrator.prompt_specialist.process_input = _fake_process_input
    preview = asyncio.run(orchestrator.preview_request("program-kanban", "Summarize the current backlog health."))

    assert preview["tier_assignment"]["tier"] == "tier_3_junior"
    assert preview["tier_assignment"]["execution_lane"] == "sync_api"
    assert preview["tier_assignment"]["approval_required"] is False
    assert len(preview["decomposition"]["subtasks"]) == 2


def test_medium_task_routes_to_tier_2(tmp_path, monkeypatch):
    _prepare_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setattr("agents.role_base.create_model_client", lambda role: _DummyClient())
    orchestrator = Orchestrator(tmp_path)

    async def _fake_process_input(user_text: str, *, run_id=None, task_id=None):
        return DelegationPacket(
            objective="Implement a controlled approval packet surface",
            details="Build the markdown packet and runtime fields needed for approval summaries and operator review.",
            priority="high",
            requires_approval=False,
            assumptions=["The existing approval table stays canonical."],
            risks=["Approval UX could drift if the packet is not explicit."],
        )

    orchestrator.prompt_specialist.process_input = _fake_process_input
    preview = asyncio.run(orchestrator.preview_request("program-kanban", "Implement a controlled approval packet surface."))

    assert preview["tier_assignment"]["tier"] == "tier_2_mid"
    assert preview["tier_assignment"]["execution_lane"] == "background_api"
    assert preview["tier_assignment"]["approval_required"] is False
    assert len(preview["decomposition"]["subtasks"]) == 3


def test_ambiguous_task_routes_to_tier_1_and_requires_approval(tmp_path, monkeypatch):
    _prepare_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setattr("agents.role_base.create_model_client", lambda role: _DummyClient())
    orchestrator = Orchestrator(tmp_path)

    async def _fake_process_input(user_text: str, *, run_id=None, task_id=None):
        return DelegationPacket(
            objective="Design the API-first hybrid execution model",
            details="Research the best routing, architecture, and approval model for a new multi-agent API-first system and decide how architecture changes should be governed.",
            priority="high",
            requires_approval=False,
            assumptions=["The Studio should reduce ChatGPT-heavy execution."],
            risks=["Wrong model routing could increase cost or reduce quality."],
        )

    orchestrator.prompt_specialist.process_input = _fake_process_input
    preview = asyncio.run(orchestrator.preview_request("program-kanban", "Design the API-first hybrid execution model."))

    assert preview["tier_assignment"]["tier"] == "tier_1_senior"
    assert preview["tier_assignment"]["execution_lane"] == "background_api"
    assert preview["tier_assignment"]["approval_required"] is True
    assert "architecture_change" in preview["tier_assignment"]["approval_reasons"]
    assert len(preview["decomposition"]["subtasks"]) == 4


def test_execution_schema_field_names_are_explicit():
    authority = ExecutionPacketAuthority(
        authority_packet_id="packet-1",
        authority_job_id="job-1",
        authority_token="token-1",
        authority_schema_name="authority.schema.v1",
        authority_execution_tier="tier_3_junior",
        authority_execution_lane="sync_api",
        authority_delegated_work=True,
        priority_class="medium",
        budget_max_tokens=1000,
        budget_reservation_id="res-1",
        retry_limit=2,
        early_stop_rule="sufficient_output",
    )
    telemetry = ExecutionPacketTelemetry(
        packet_id="packet-1",
        job_id="job-1",
        priority_class="medium",
        budget_reservation_id="res-1",
        budget_max_tokens=1000,
        actual_total_tokens=20,
        retry_count=1,
        escalation_target=None,
        stop_reason=None,
        status="running",
    )
    reservation = ExecutionJobReservation(
        job_id="job-1",
        priority_class="medium",
        reserved_max_tokens=1000,
        reservation_status="reserved",
    )

    assert set(ExecutionPacketAuthority.model_fields) == {
        "authority_packet_id",
        "authority_job_id",
        "authority_token",
        "authority_schema_name",
        "authority_execution_tier",
        "authority_execution_lane",
        "authority_delegated_work",
        "priority_class",
        "budget_max_tokens",
        "budget_reservation_id",
        "retry_limit",
        "early_stop_rule",
    }
    assert set(ExecutionPacketTelemetry.model_fields) == {
        "packet_id",
        "job_id",
        "priority_class",
        "budget_reservation_id",
        "budget_max_tokens",
        "actual_total_tokens",
        "retry_count",
        "escalation_target",
        "stop_reason",
        "status",
    }
    assert set(ExecutionJobReservation.model_fields) == {
        "job_id",
        "priority_class",
        "reserved_max_tokens",
        "reservation_status",
    }
