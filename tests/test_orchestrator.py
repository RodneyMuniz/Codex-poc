from __future__ import annotations

import asyncio
from pathlib import Path

from agents.orchestrator import Orchestrator
from agents.schemas import DelegationPacket


def _prepare_repo(tmp_path):
    (tmp_path / "projects" / "tactics-game" / "execution").mkdir(parents=True)
    (tmp_path / "projects" / "tactics-game" / "governance").mkdir(parents=True)
    (tmp_path / "sessions").mkdir(parents=True)
    (tmp_path / "governance").mkdir(parents=True)
    (tmp_path / "memory").mkdir(parents=True)
    (tmp_path / "agents").mkdir(parents=True)
    for name in ["FRAMEWORK.md", "GOVERNANCE_RULES.md", "VISION.md", "MODEL_REASONING_MATRIX.md", "MEMORY_MAP.md"]:
        (tmp_path / "governance" / name).write_text(f"# {name}\n", encoding="utf-8")
    (tmp_path / "projects" / "tactics-game" / "governance" / "PROJECT_BRIEF.md").write_text("# Brief\n", encoding="utf-8")
    (tmp_path / "memory" / "framework_health.json").write_text("{}\n", encoding="utf-8")
    (tmp_path / "memory" / "session_summaries.json").write_text("[]\n", encoding="utf-8")
    for name in ["prompt_specialist.py", "orchestrator.py", "pm.py", "architect.py", "developer.py", "design.py", "qa.py"]:
        (tmp_path / "agents" / name).write_text("# placeholder\n", encoding="utf-8")


def test_health_check_reports_required_assets(tmp_path, monkeypatch):
    _prepare_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    orchestrator = Orchestrator(tmp_path)
    report = orchestrator.health_check()

    assert report["ok"] is True
    assert "tasks" in report["checked_tables"]
    assert "agents/qa.py" in report["checked_agents"]


class _DummyClient:
    async def close(self) -> None:
        return None


def test_preview_request_returns_route_preview_and_operator_brief(tmp_path, monkeypatch):
    _prepare_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setattr("agents.role_base.create_model_client", lambda role: _DummyClient())

    orchestrator = Orchestrator(tmp_path)

    async def _fake_process_input(user_text: str, *, run_id=None, task_id=None):
        return DelegationPacket(
            objective="Restore the operator intake flow",
            details="Build a preview-driven operator intake flow with explicit evidence.",
            priority="high",
            requires_approval=True,
            assumptions=["The current project is correct."],
            risks=["Operator review is required before downstream dispatch."],
        )

    orchestrator.prompt_specialist.process_input = _fake_process_input

    preview = asyncio.run(orchestrator.preview_request("program-kanban", "Restore the operator intake flow"))

    assert preview["packet"]["objective"] == "Restore the operator intake flow"
    assert preview["route_preview"][0]["runtime_role"] == "PromptSpecialist"
    assert preview["route_preview"][1]["runtime_role"] == "Orchestrator"
    assert any(chip["label"] == "Need Proof" for chip in preview["operator_brief"]["response_chips"])


def test_dispatch_request_creates_pre_dispatch_backup(tmp_path, monkeypatch):
    _prepare_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setattr("agents.role_base.create_model_client", lambda role: _DummyClient())

    orchestrator = Orchestrator(tmp_path)

    async def _fake_process_input(user_text: str, *, run_id=None, task_id=None):
        return DelegationPacket(
            objective="Build a safe operator dispatch",
            details="Verify the runtime creates a backup before dispatching work.",
            priority="high",
            requires_approval=True,
            assumptions=["The current project is correct."],
            risks=["A pre-dispatch backup should exist before the run starts."],
        )

    captured: dict[str, object] = {}
    real_backup = orchestrator.store.create_dispatch_backup

    def _capture_backup(**kwargs):
        backup = real_backup(**kwargs)
        captured["backup"] = backup
        return backup

    async def _fake_start_task(task_id: str, *, preview_payload=None, backup_info=None):
        captured["task_id"] = task_id
        captured["start_backup"] = backup_info
        return {"status": "paused_approval", "run_id": "run_test", "task_id": task_id, "dispatch_backup": backup_info}

    orchestrator.prompt_specialist.process_input = _fake_process_input
    monkeypatch.setattr(orchestrator.store, "create_dispatch_backup", _capture_backup)
    monkeypatch.setattr(orchestrator, "start_task", _fake_start_task)

    result = asyncio.run(orchestrator.dispatch_request("tactics-game", "Build a safe operator dispatch"))

    backup = captured["backup"]
    assert isinstance(backup, dict)
    assert Path(backup["path"]).exists()
    assert result["dispatch_backup"]["path"] == backup["path"]
    assert captured["start_backup"]["path"] == backup["path"]


def test_resume_run_returns_status_when_run_already_progressed(tmp_path, monkeypatch):
    _prepare_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setattr("agents.role_base.create_model_client", lambda role: _DummyClient())

    orchestrator = Orchestrator(tmp_path)
    task = orchestrator.store.create_task("tactics-game", "Safe resume", "Verify noop resume handling")
    run = orchestrator.store.create_run("tactics-game", task["id"])
    orchestrator.store.update_run(run["id"], status="completed", stop_reason="completed", completed=True)

    payload = asyncio.run(orchestrator.resume_run(run["id"]))

    assert payload["status"] == "already_progressed"
    assert payload["run_status"] == "completed"
    assert payload["run_id"] == run["id"]


def test_approve_and_resume_returns_graceful_status_when_run_already_progressed(tmp_path, monkeypatch):
    _prepare_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setattr("agents.role_base.create_model_client", lambda role: _DummyClient())

    orchestrator = Orchestrator(tmp_path)
    task = orchestrator.store.create_task("tactics-game", "Safe approve", "Verify graceful approve/continue handling")
    run = orchestrator.store.create_run("tactics-game", task["id"])
    approval = orchestrator.store.create_approval(run["id"], task["id"], "PM", "Dispatch developer work")
    orchestrator.store.update_run(run["id"], status="completed", stop_reason="completed", completed=True)

    payload = asyncio.run(orchestrator.approve_and_resume(approval["id"]))

    assert payload["status"] == "already_progressed"
    assert payload["run_id"] == run["id"]
    assert payload["run_status"] == "completed"


def test_dispatch_request_executes_direct_task_move_for_referenced_board_item(tmp_path, monkeypatch):
    _prepare_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setattr("agents.role_base.create_model_client", lambda role: _DummyClient())

    orchestrator = Orchestrator(tmp_path)
    orchestrator.store.import_task(
        task_id="TG-098",
        project_name="tactics-game",
        title="Define the first battle visual identity packet for the playable prototype",
        details="Imported tactics-game backlog item.",
        objective="Define the first battle visual identity packet for the playable prototype",
        status="in_review",
        owner_role="Art Director / Visual Identity Planner",
        assigned_role="Art Director / Visual Identity Planner",
        review_state="In Review",
    )

    result = asyncio.run(
        orchestrator.dispatch_request(
            "program-kanban",
            "hi, please move back TG-098 to in progress, as i cant really see the outcome of the task from the build.",
        )
    )

    moved_task = orchestrator.store.get_task("TG-098")

    assert result["preview"]["project_name"] == "tactics-game"
    assert result["preview"]["operator_action"]["action_type"] == "move_task_status"
    assert len(result["preview"]["route_preview"]) == 1
    assert result["task"]["project_name"] == "tactics-game"
    assert result["run_result"]["run_status"] == "completed"
    assert result["run_result"]["target_task_id"] == "TG-098"
    assert moved_task is not None
    assert moved_task["status"] == "in_progress"
    assert moved_task["review_state"] == "Revision Needed"


def test_preview_request_bypasses_prompt_specialist_for_direct_board_actions(tmp_path, monkeypatch):
    _prepare_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setattr("agents.role_base.create_model_client", lambda role: _DummyClient())

    orchestrator = Orchestrator(tmp_path)
    orchestrator.store.import_task(
        task_id="TGD-999",
        project_name="program-kanban",
        title="Temporary review item",
        details="Imported board item for deterministic routing test.",
        objective="Temporary review item",
        status="in_review",
        owner_role="Project Orchestrator",
        assigned_role="Project Orchestrator",
        review_state="In Review",
    )

    async def _unexpected(*args, **kwargs):
        raise AssertionError("Prompt specialist should not run for deterministic board actions.")

    orchestrator.prompt_specialist.process_input = _unexpected

    preview = asyncio.run(orchestrator.preview_request("program-kanban", "please move TGD-999 back to in progress"))

    assert preview["operator_action"]["target_task_id"] == "TGD-999"
    assert preview["execution_runtime"]["mode"] == "deterministic"
    assert preview["route_preview"][0]["runtime_role"] == "Orchestrator"


def test_execute_run_selects_sdk_specialist_runtime_without_second_orchestrator(tmp_path, monkeypatch):
    _prepare_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("AISTUDIO_RUNTIME_MODE", "sdk")
    monkeypatch.setattr("agents.role_base.create_model_client", lambda role: _DummyClient())

    orchestrator = Orchestrator(tmp_path)
    task = orchestrator.store.create_task(
        "tactics-game",
        "SDK runtime path",
        "Verify the SDK specialist runtime is selected without a second orchestrator.",
        objective="Use SDK specialists while keeping orchestration deterministic.",
        requires_approval=False,
    )
    run = orchestrator.store.create_run("tactics-game", task["id"])
    captured: dict[str, str] = {}

    async def _fake_pm_execute(self, *, run_id: str, task: dict):
        captured["objective"] = task["objective"]
        captured["details"] = task["details"]
        captured["runtime_mode"] = task["runtime_mode"]
        captured["planning_layer"] = task["sdk_runtime_context"]["planning_layer"]
        return {"completed": True, "summary": "Planning layer completed the migrated run.", "task_id": task["id"]}

    monkeypatch.setattr("agents.pm.ProjectManagerAgent.execute_request", _fake_pm_execute)

    result = asyncio.run(orchestrator._execute_run(run["id"], task))
    team_state = orchestrator.store.load_team_state(run["id"])
    evidence = orchestrator.get_run_evidence(run["id"])

    assert result["run_status"] == "completed"
    assert captured["objective"] == "Use SDK specialists while keeping orchestration deterministic."
    assert captured["details"] == "Verify the SDK specialist runtime is selected without a second orchestrator."
    assert captured["runtime_mode"] == "sdk"
    assert captured["planning_layer"] == "deterministic_internal_helper"
    assert team_state is not None
    assert team_state["runtime_mode"] == "sdk"
    assert team_state["execution_mode"] == "worker_only"
    assert any(event["event_type"] == "sdk_specialist_runtime_selected" for event in evidence["trace_events"])
