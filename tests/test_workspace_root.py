from __future__ import annotations

import asyncio
import sqlite3
from pathlib import Path

import pytest

from agents.orchestrator import Orchestrator
from intake.gateway import classify_operator_request
from intake.ingress import dispatch_operator_request, intake_operator_request
from intake.models import TaskPacket
from intake.policy_store import record_policy_proposal
from intake.compiler import compile_policy_proposal
from intake.status import compile_status_response
from skills.tools import write_project_artifact
from workspace_root import (
    AUTHORITATIVE_ROOT_ENV,
    KNOWN_DUPLICATE_ROOT_ENV,
    WorkspaceRootAuthorityError,
    ensure_authoritative_workspace_path,
    ensure_authoritative_workspace_root,
)


def _prepare_repo(tmp_path: Path) -> None:
    (tmp_path / "projects" / "program-kanban" / "governance").mkdir(parents=True)
    (tmp_path / "projects" / "program-kanban" / "execution").mkdir(parents=True)
    (tmp_path / "projects" / "tactics-game" / "artifacts").mkdir(parents=True)
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


def _create_task_db(tmp_path: Path) -> None:
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
            ("PK-100", "program-kanban", "in_review", "2026-04-10T00:00:00"),
        )
        connection.commit()
    finally:
        connection.close()


class _DummyTaskIngressOrchestrator:
    def __init__(self, repo_root: Path) -> None:
        self.repo_root = repo_root

    async def dispatch_request(self, project_name: str, *, task_packet: TaskPacket):
        return {
            "task": {"id": "TASK-1", "project_name": project_name},
            "run_result": {"run_status": "queued"},
            "packet": task_packet.model_dump(),
        }


class _ReadOnlyIngressOrchestrator:
    def __init__(self, repo_root: Path) -> None:
        self.repo_root = repo_root

    async def intake_request(self, *args, **kwargs):
        raise AssertionError("Read-only ingress must not enter task intake.")

    async def dispatch_request(self, *args, **kwargs):
        raise AssertionError("Read-only ingress must not enter task dispatch.")


def test_in_root_workspace_path_succeeds(tmp_path):
    _prepare_repo(tmp_path)

    assert ensure_authoritative_workspace_root(tmp_path) == tmp_path.resolve()
    assert ensure_authoritative_workspace_path(tmp_path / "governance") == (tmp_path / "governance").resolve()


def test_out_of_root_workspace_path_fails_closed(tmp_path):
    _prepare_repo(tmp_path)
    outside_root = tmp_path.parent / f"{tmp_path.name}_outside"
    outside_root.mkdir()

    with pytest.raises(WorkspaceRootAuthorityError, match="outside the authoritative workspace root"):
        ensure_authoritative_workspace_path(outside_root, label="external path")


def test_known_duplicate_root_is_rejected(tmp_path, monkeypatch):
    authoritative_root = tmp_path / "authoritative"
    duplicate_root = tmp_path / "duplicate"
    authoritative_root.mkdir()
    duplicate_root.mkdir()
    monkeypatch.setenv(AUTHORITATIVE_ROOT_ENV, str(authoritative_root))
    monkeypatch.setenv(KNOWN_DUPLICATE_ROOT_ENV, str(duplicate_root))

    with pytest.raises(WorkspaceRootAuthorityError, match="known non-authoritative duplicate workspace root"):
        ensure_authoritative_workspace_root(duplicate_root, label="duplicate repo_root")


def test_governance_storage_refuses_out_of_root_path(tmp_path, monkeypatch):
    _prepare_repo(tmp_path)
    duplicate_root = tmp_path.parent / f"{tmp_path.name}_duplicate"
    duplicate_root.mkdir()
    monkeypatch.setenv(KNOWN_DUPLICATE_ROOT_ENV, str(duplicate_root))
    proposal = compile_policy_proposal(
        classify_operator_request("Allow the architect agent to edit governance rules directly")
    )

    with pytest.raises(WorkspaceRootAuthorityError, match="known non-authoritative duplicate workspace root"):
        record_policy_proposal(duplicate_root, proposal)


def test_status_inspection_refuses_non_authoritative_path(tmp_path, monkeypatch):
    _prepare_repo(tmp_path)
    outside_root = tmp_path.parent / f"{tmp_path.name}_outside"
    outside_root.mkdir()
    monkeypatch.delenv(KNOWN_DUPLICATE_ROOT_ENV, raising=False)
    decision = classify_operator_request("What is the current status of the orchestrator control work?")

    with pytest.raises(WorkspaceRootAuthorityError, match="must equal the authoritative workspace root"):
        compile_status_response(outside_root, decision, project_name="program-kanban")


def test_tool_layer_rejects_known_duplicate_workspace_root(tmp_path, monkeypatch):
    authoritative_root = tmp_path / "authoritative"
    duplicate_root = tmp_path / "duplicate"
    (authoritative_root / "projects" / "tactics-game" / "artifacts").mkdir(parents=True)
    (duplicate_root / "projects" / "tactics-game" / "artifacts").mkdir(parents=True)
    monkeypatch.setenv(AUTHORITATIVE_ROOT_ENV, str(authoritative_root))
    monkeypatch.setenv(KNOWN_DUPLICATE_ROOT_ENV, str(duplicate_root))
    monkeypatch.chdir(duplicate_root)

    with pytest.raises(WorkspaceRootAuthorityError, match="known non-authoritative duplicate workspace root"):
        write_project_artifact("projects/tactics-game/artifacts/blocked.txt", "blocked\n")


def test_orchestrator_rejects_known_duplicate_repo_root(tmp_path, monkeypatch):
    authoritative_root = tmp_path / "authoritative"
    duplicate_root = tmp_path / "duplicate"
    authoritative_root.mkdir()
    duplicate_root.mkdir()
    monkeypatch.setenv(AUTHORITATIVE_ROOT_ENV, str(authoritative_root))
    monkeypatch.setenv(KNOWN_DUPLICATE_ROOT_ENV, str(duplicate_root))

    with pytest.raises(WorkspaceRootAuthorityError, match="known non-authoritative duplicate workspace root"):
        Orchestrator(duplicate_root)


def test_normal_in_root_task_policy_and_status_paths_still_work(tmp_path):
    _prepare_repo(tmp_path)
    _create_task_db(tmp_path)

    task_result = asyncio.run(
        dispatch_operator_request(
            _DummyTaskIngressOrchestrator(tmp_path),
            "program-kanban",
            "Implement the workspace root authority guard",
        )
    )
    policy_result = asyncio.run(
        intake_operator_request(
            _ReadOnlyIngressOrchestrator(tmp_path),
            "program-kanban",
            "Allow the architect agent to edit governance rules directly",
        )
    )
    status_result = asyncio.run(
        intake_operator_request(
            _ReadOnlyIngressOrchestrator(tmp_path),
            "program-kanban",
            "What is the current status of task work?",
        )
    )

    assert task_result["run_result"]["run_status"] == "queued"
    assert task_result["packet"]["schema_version"] == "task_packet_v1"
    assert policy_result["status"] == "proposal_recorded"
    assert policy_result["proposal_record"]["path"].endswith(".json")
    assert status_result["status"] == "status_only"
    assert status_result["status_response"]["schema_version"] == "status_response_v1"
    assert status_result["status_response"]["status_kind"] == "TASK"
