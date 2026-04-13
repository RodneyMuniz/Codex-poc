from __future__ import annotations

from pathlib import Path

import pytest

from intake.compiler import compile_task_packet
from intake.gateway import classify_operator_request
from intake.interpreter import compile_interpreter_summary
from intake.models import InterpreterSummary, TaskPacket
from workspace_root import (
    AUTHORITATIVE_ROOT_ENV,
    KNOWN_DUPLICATE_ROOT_ENV,
    WorkspaceRootAuthorityError,
    write_workspace_authority_marker,
)


def _prepare_repo(tmp_path: Path) -> None:
    (tmp_path / "projects" / "program-kanban" / "governance").mkdir(parents=True)
    (tmp_path / "projects" / "program-kanban" / "execution").mkdir(parents=True)
    (tmp_path / "sessions").mkdir(parents=True)
    (tmp_path / "governance").mkdir(parents=True)
    (tmp_path / "memory").mkdir(parents=True)
    (tmp_path / "agents").mkdir(parents=True)
    for name in ["FRAMEWORK.md", "GOVERNANCE_RULES.md", "VISION.md", "MODEL_REASONING_MATRIX.md", "MEMORY_MAP.md"]:
        (tmp_path / "governance" / name).write_text(f"# {name}\n", encoding="utf-8")
    (tmp_path / "governance" / "CONTROL_INVARIANTS.md").write_text("# Controls\n", encoding="utf-8")
    (tmp_path / "governance" / "ARCHITECTURE_BASELINE.md").write_text("# Architecture\n", encoding="utf-8")
    (tmp_path / "governance" / "KNOWN_GAPS.md").write_text("# Gaps\n", encoding="utf-8")
    (tmp_path / "projects" / "program-kanban" / "governance" / "PROJECT_BRIEF.md").write_text("# Brief\n", encoding="utf-8")
    (tmp_path / "memory" / "framework_health.json").write_text("{}\n", encoding="utf-8")
    (tmp_path / "memory" / "session_summaries.json").write_text("[]\n", encoding="utf-8")


def test_safe_task_decision_produces_valid_interpreter_summary(tmp_path):
    _prepare_repo(tmp_path)
    decision = classify_operator_request("Implement the gateway")

    summary = compile_interpreter_summary(tmp_path, decision, project_name="program-kanban")

    assert isinstance(summary, InterpreterSummary)
    assert summary.schema_version == "interpreter_summary_v1"
    assert summary.source_intent == "TASK"
    assert summary.task_kind == "IMPLEMENTATION"
    assert summary.safe_for_execution_path is False
    assert "governance/CONTROL_INVARIANTS.md" in summary.relevant_refs
    assert "workspace_root_authority" in summary.constraints


def test_non_task_decisions_do_not_enter_interpreter_flow(tmp_path):
    _prepare_repo(tmp_path)
    decision = classify_operator_request("What is the current status of the orchestrator control work?")

    with pytest.raises(ValueError, match="Only safe ROUTE_TASK decisions compile to InterpreterSummary"):
        compile_interpreter_summary(tmp_path, decision, project_name="program-kanban")


def test_interpreter_remains_read_only(tmp_path):
    _prepare_repo(tmp_path)
    decision = classify_operator_request("Review the gateway implementation plan")

    summary = compile_interpreter_summary(tmp_path, decision, project_name="program-kanban")

    assert summary.task_kind == "REVIEW"
    assert (tmp_path / "sessions" / "studio.db").exists() is False
    assert (tmp_path / "governance" / "policy_proposals").exists() is False


def test_task_packet_compiles_from_interpreter_summary(tmp_path):
    _prepare_repo(tmp_path)
    summary = compile_interpreter_summary(
        tmp_path,
        classify_operator_request("Implement the gateway"),
        project_name="program-kanban",
    )

    packet = compile_task_packet(summary)

    assert isinstance(packet, TaskPacket)
    assert packet.task_type == "IMPLEMENTATION"
    assert "write_project_artifact" in packet.allowed_tools


def test_unknown_task_kind_is_handled_safely():
    summary = InterpreterSummary(
        summary_id="interp_deadbeefcafe",
        source_intent="TASK",
        normalized_request="Coordinate the gateway next steps",
        task_kind="UNKNOWN",
        relevant_refs=["governance/CONTROL_INVARIANTS.md"],
        constraints=["workspace_root_authority", "task_path_only"],
        open_questions=["task_kind_unclear"],
        safe_for_execution_path=False,
    )

    packet = compile_task_packet(summary)

    assert packet.task_type == "UNKNOWN"
    assert "write_project_artifact" not in packet.allowed_tools
    assert packet.token_budget.max_retries == 0


def test_interpreter_workspace_root_enforcement_still_applies(tmp_path, monkeypatch):
    authoritative_root = tmp_path / "authoritative"
    duplicate_root = tmp_path / "duplicate"
    authoritative_root.mkdir()
    duplicate_root.mkdir()
    _prepare_repo(authoritative_root)
    write_workspace_authority_marker(authoritative_root, repo_name="authoritative-test-root")
    monkeypatch.setenv(AUTHORITATIVE_ROOT_ENV, str(authoritative_root))
    monkeypatch.setenv(KNOWN_DUPLICATE_ROOT_ENV, str(duplicate_root))
    decision = classify_operator_request("Implement the gateway")

    with pytest.raises(WorkspaceRootAuthorityError, match="known non-authoritative duplicate workspace root"):
        compile_interpreter_summary(duplicate_root, decision, project_name="program-kanban")
