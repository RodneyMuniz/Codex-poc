from __future__ import annotations

import asyncio
import sqlite3
from pathlib import Path

import pytest

from intake.compiler import compile_policy_proposal, compile_task_packet
from intake.gateway import classify_operator_request
from intake.ingress import dispatch_operator_request, intake_operator_request
from intake.models import PolicyProposal, StatusResponse, TaskPacket
from intake.status import compile_status_response


def _prepare_repo(tmp_path: Path) -> None:
    (tmp_path / "projects" / "program-kanban" / "governance").mkdir(parents=True)
    (tmp_path / "projects" / "program-kanban" / "execution").mkdir(parents=True)
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


def _create_read_only_task_db(tmp_path: Path) -> None:
    db_path = tmp_path / "sessions" / "studio.db"
    connection = sqlite3.connect(db_path)
    try:
        connection.execute(
            """
            CREATE TABLE tasks (
                id TEXT,
                project_name TEXT,
                status TEXT,
                updated_at TEXT
            )
            """
        )
        connection.execute(
            "INSERT INTO tasks (id, project_name, status, updated_at) VALUES (?, ?, ?, ?)",
            ("PK-001", "program-kanban", "in_review", "2026-04-10T00:00:00"),
        )
        connection.execute(
            "INSERT INTO tasks (id, project_name, status, updated_at) VALUES (?, ?, ?, ?)",
            ("PK-002", "program-kanban", "completed", "2026-04-10T01:00:00"),
        )
        connection.commit()
    finally:
        connection.close()


class _DummyStatusIngressOrchestrator:
    def __init__(self, repo_root: Path) -> None:
        self.repo_root = repo_root

    async def intake_request(self, *args, **kwargs):
        raise AssertionError("Status ingress must not route into task intake.")

    async def dispatch_request(self, *args, **kwargs):
        raise AssertionError("Status ingress must not route into task dispatch.")


def test_status_query_decision_produces_valid_status_response(tmp_path):
    _prepare_repo(tmp_path)
    _create_read_only_task_db(tmp_path)
    decision = classify_operator_request("What is the current status of the current task work?")

    response = compile_status_response(tmp_path, decision, project_name="program-kanban")

    assert response.schema_version == "status_response_v1"
    assert response.source_intent == "STATUS_QUERY"
    assert response.status_kind == "TASK"
    assert response.safe_for_execution_path is False
    assert "program-kanban" in response.summary


def test_status_query_does_not_compile_to_task_packet():
    decision = classify_operator_request("What is the current status of the orchestrator control work?")

    with pytest.raises(ValueError, match="Only safe ROUTE_TASK decisions"):
        compile_task_packet(decision)


def test_status_query_does_not_compile_to_policy_proposal():
    decision = classify_operator_request("What is the current status of governance proposals?")

    with pytest.raises(ValueError, match="Only POLICY_UPDATE admin decisions"):
        compile_policy_proposal(decision)


def test_status_handling_is_read_only(tmp_path):
    _prepare_repo(tmp_path)
    orchestrator = _DummyStatusIngressOrchestrator(tmp_path)

    result = asyncio.run(
        intake_operator_request(
            orchestrator,
            "program-kanban",
            "What is the current status of the orchestrator control work?",
        )
    )

    assert result["status"] == "status_only"
    assert result["task"] is None
    assert result["packet"] is None
    assert "policy_proposal" not in result
    assert (tmp_path / "sessions" / "studio.db").exists() is False
    assert (tmp_path / "governance" / "policy_proposals").exists() is False


def test_task_and_policy_update_still_follow_their_own_paths(tmp_path):
    _prepare_repo(tmp_path)
    captured: dict[str, object] = {}

    class _DummyTaskOrchestrator:
        repo_root = tmp_path

        async def dispatch_request(self, project_name: str, *, task_packet: TaskPacket):
            captured["task_project"] = project_name
            captured["task_packet"] = task_packet
            return {"task": {"id": "TASK-1"}, "run_result": {"run_status": "queued"}}

    task_result = asyncio.run(
        dispatch_operator_request(
            _DummyTaskOrchestrator(),
            "program-kanban",
            "Implement the gateway",
        )
    )
    policy_result = asyncio.run(
        intake_operator_request(
            _DummyStatusIngressOrchestrator(tmp_path),
            "program-kanban",
            "Allow the architect agent to edit governance rules directly",
        )
    )

    assert task_result["run_result"]["run_status"] == "queued"
    assert isinstance(captured["task_packet"], TaskPacket)
    assert policy_result["status"] == "proposal_recorded"
    assert "status_response" not in policy_result


def test_unsupported_status_query_is_handled_safely(tmp_path):
    _prepare_repo(tmp_path)
    decision = classify_operator_request("What is the current status of the dragon economy simulation?")

    response = compile_status_response(tmp_path, decision, project_name="program-kanban")

    assert isinstance(response, StatusResponse)
    assert response.status_kind == "UNKNOWN"
    assert "supported v1 status scope" in response.summary


def test_governance_status_query_routes_as_status_not_policy_update(tmp_path):
    _prepare_repo(tmp_path)
    decision = classify_operator_request("What is the current status of governance proposals?")

    response = compile_status_response(tmp_path, decision, project_name="program-kanban")

    assert decision.decision == "ROUTE_STATUS"
    assert decision.intent == "STATUS_QUERY"
    assert response.status_kind == "GOVERNANCE"


def test_status_response_cannot_be_misused_as_task_or_policy_contract():
    status_response = StatusResponse(
        response_id="status_deadbeefcafe",
        source_intent="STATUS_QUERY",
        normalized_request="What is the current status of the orchestrator control work?",
        status_kind="SYSTEM",
        summary="System status is limited in v1 because git metadata is unavailable.",
        evidence_refs=["repo:.git missing"],
        safe_for_execution_path=False,
    )

    assert isinstance(status_response, StatusResponse)
    assert not isinstance(status_response, TaskPacket)
    assert not isinstance(status_response, PolicyProposal)
