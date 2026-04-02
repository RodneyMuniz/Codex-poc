from __future__ import annotations

import asyncio
from pathlib import Path

import pytest

from agents.orchestrator import Orchestrator
from agents.role_base import DelegatedExecutionBypassError
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


class _UsageClient:
    async def create(self, messages, json_output=None):
        return type(
            "UsageResult",
            (),
            {
                "content": '{"objective":"Design the first control-room gallery screen","details":"Create a reviewable gallery layout with clear filters and selected-direction state.","priority":"high","requires_approval":false,"assumptions":["Keep the first pass review-first."],"risks":["Style direction may still need clarification."]}',
                "usage": type("Usage", (), {"prompt_tokens": 91, "completion_tokens": 27})(),
            },
        )()

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


def test_preview_request_adds_design_request_preview_for_visual_requests(tmp_path, monkeypatch):
    _prepare_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setattr("agents.role_base.create_model_client", lambda role: _DummyClient())

    orchestrator = Orchestrator(tmp_path)

    async def _fake_process_input(user_text: str, *, run_id=None, task_id=None):
        return DelegationPacket(
            objective="Design the first battle board concept",
            details="Create a reviewable board concept for the tactics map. Keep the first pass clean and readable.",
            priority="high",
            requires_approval=False,
            assumptions=["Preserve tactical readability."],
            risks=["Style direction is still open."],
        )

    orchestrator.prompt_specialist.process_input = _fake_process_input

    preview = asyncio.run(orchestrator.preview_request("program-kanban", "Design the first battle board concept"))

    assert preview["design_request_preview"] is not None
    assert preview["clarification_gate"]["questions"] == preview["design_request_preview"]["open_questions"]
    assert preview["clarification_gate"]["ready_to_execute"] == (len(preview["clarification_gate"]["questions"]) == 0)
    assert preview["design_request_preview"]["target_surface"] == "board or map concept"
    assert "board or map concept review packet" in preview["design_request_preview"]["deliverables"]
    assert preview["packet"]["blocked_questions"] == preview["design_request_preview"]["open_questions"]
    assert preview["media_service_contracts"]
    assert preview["media_service_contracts"][0]["family"] == "visual"
    assert any(chip["label"] == "Design Packet" for chip in preview["operator_brief"]["response_chips"])
    assert any(chip["label"] == "Media Services" for chip in preview["operator_brief"]["response_chips"])
    assert any(step["runtime_role"] == "MediaService" for step in preview["route_preview"])
    if preview["clarification_gate"]["active"]:
        assert any(chip["label"] == "Clarification" for chip in preview["operator_brief"]["response_chips"])


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

    async def _fake_start_task(task_id: str, *, preview_payload=None, backup_info=None):
        return {"status": "paused_approval", "run_id": "run_test", "task_id": task_id, "dispatch_backup": backup_info}

    orchestrator.prompt_specialist.process_input = _fake_process_input
    monkeypatch.setattr(orchestrator, "start_task", _fake_start_task)

    result = asyncio.run(orchestrator.dispatch_request("tactics-game", "Build a safe operator dispatch"))

    backup = result["dispatch_backup"]
    assert isinstance(backup, dict)
    assert Path(backup["path"]).exists()
    assert result["run_result"]["dispatch_backup"]["path"] == backup["path"]


def test_dispatch_request_persists_design_request_preview_in_acceptance(tmp_path, monkeypatch):
    _prepare_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setattr("agents.role_base.create_model_client", lambda role: _DummyClient())

    orchestrator = Orchestrator(tmp_path)

    async def _fake_process_input(user_text: str, *, run_id=None, task_id=None):
        return DelegationPacket(
            objective="Design the first control-room gallery screen",
            details="Create a UI layout concept for the control-room gallery. Avoid visual clutter.",
            priority="medium",
            requires_approval=False,
            assumptions=["Focus on reviewability first."],
            risks=[],
        )

    async def _unexpected_start(*args, **kwargs):
        raise AssertionError("Dispatch should pause for clarification before execution starts.")

    orchestrator.prompt_specialist.process_input = _fake_process_input
    monkeypatch.setattr(orchestrator, "start_task", _unexpected_start)

    result = asyncio.run(orchestrator.dispatch_request("program-kanban", "Design the first control-room gallery screen"))
    task = orchestrator.store.get_task(result["task"]["id"])

    assert task is not None
    assert result["run_result"]["status"] == "needs_clarification"
    assert result["dispatch_backup"] is None
    assert task["acceptance"]["design_request_preview"]["target_surface"] == "control-room review gallery"
    assert task["acceptance"]["design_request_preview"]["deliverables"][0] == "design request preview"
    assert task["acceptance"]["clarification_gate"]["active"] is True
    assert task["acceptance"]["media_service_contracts"][0]["family"] == "visual"
    assert task["review_notes"].startswith("Awaiting design clarification:")


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


def test_resume_run_preserves_context_receipt_after_standard_approval(tmp_path, monkeypatch):
    _prepare_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setattr("agents.role_base.create_model_client", lambda role: _DummyClient())

    orchestrator = Orchestrator(tmp_path)
    task = orchestrator.store.create_task(
        "tactics-game",
        "Receipt resume",
        "Verify a paused approval run keeps its context receipt through resume.",
        objective="Verify a paused approval run keeps its context receipt through resume.",
        requires_approval=True,
        expected_artifact_path="projects/tactics-game/artifacts/receipt_resume.md",
    )

    async def _fake_execute_request(self, *, run_id: str, task: dict):
        return {"completed": True, "summary": "Approval-gated run completed."}

    monkeypatch.setattr("agents.pm.ProjectManagerAgent.execute_request", _fake_execute_request)

    paused = asyncio.run(
        orchestrator.start_task(
            task["id"],
            preview_payload={
                "packet": {
                    "objective": task["objective"],
                    "details": task["details"],
                    "assumptions": ["Keep the original continuity frame."],
                }
            },
        )
    )

    orchestrator.approve(paused["approval_id"], "Proceed.")
    resumed = asyncio.run(orchestrator.resume_run(paused["run_id"]))
    receipt = orchestrator.store.load_context_receipt(paused["run_id"])

    assert resumed["run_status"] == "completed"
    assert receipt is not None
    assert receipt["task_id"] == task["id"]
    assert receipt["accepted_assumptions"] == ["Keep the original continuity frame."]
    assert receipt["next_reviewer"] == "Operator"
    assert receipt["current_owner_role"] == "QA"
    assert receipt["resume_conditions"] == ["Review the recorded run evidence before opening the next lane."]


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


def test_direct_board_action_run_evidence_stays_deterministic_without_approval_pause(tmp_path, monkeypatch):
    _prepare_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setattr("agents.role_base.create_model_client", lambda role: _DummyClient())

    orchestrator = Orchestrator(tmp_path)
    orchestrator.store.import_task(
        task_id="TG-099",
        project_name="tactics-game",
        title="Temporary deterministic move",
        details="Imported board item for deterministic evidence coverage.",
        objective="Temporary deterministic move",
        status="in_review",
        owner_role="Project Orchestrator",
        assigned_role="Project Orchestrator",
        review_state="In Review",
    )

    result = asyncio.run(
        orchestrator.dispatch_request(
            "program-kanban",
            "please move TG-099 back to in progress because the deterministic board action should stay local",
        )
    )

    evidence = orchestrator.get_run_evidence(result["run_result"]["run_id"])

    assert result["run_result"]["run_status"] == "completed"
    assert evidence["run"]["stop_reason"] == "direct_board_action"
    assert evidence["approvals"] == []
    assert evidence["worker_dispatch"] is None
    assert evidence["context_receipt"]["resume_conditions"] == ["Direct board action completed locally."]
    assert evidence["context_receipt"]["next_reviewer"] == "Operator"


def test_preview_request_bypasses_prompt_specialist_for_direct_board_actions(tmp_path, monkeypatch):
    _prepare_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setattr("agents.role_base.create_model_client", lambda role: _DummyClient())

    orchestrator = Orchestrator(tmp_path)
    orchestrator.store.import_task(
        task_id="PK-999",
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

    preview = asyncio.run(orchestrator.preview_request("program-kanban", "please move PK-999 back to in progress"))

    assert preview["operator_action"]["target_task_id"] == "PK-999"
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
        captured["authority_delegated_work"] = task["authority_delegated_work"]
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
    assert captured["authority_delegated_work"] is True
    assert captured["planning_layer"] == "deterministic_internal_helper"
    assert team_state is not None
    assert team_state["runtime_mode"] == "sdk"
    assert team_state["execution_mode"] == "worker_only"
    assert any(event["event_type"] == "sdk_specialist_runtime_selected" for event in evidence["trace_events"])


def test_start_task_seeds_context_receipt_from_preview_packet(tmp_path, monkeypatch):
    _prepare_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setattr("agents.role_base.create_model_client", lambda role: _DummyClient())

    orchestrator = Orchestrator(tmp_path)
    task = orchestrator.store.create_task(
        "tactics-game",
        "Receipt kickoff",
        "Verify the orchestrator seeds continuity receipts before PM execution.",
        objective="Seed continuity receipts from the approved preview packet.",
        expected_artifact_path="projects/tactics-game/artifacts/receipt.md",
    )

    async def _fake_pm_execute(self, *, run_id: str, task: dict):
        return {"completed": True, "summary": "Continuity kickoff completed."}

    monkeypatch.setattr("agents.pm.ProjectManagerAgent.execute_request", _fake_pm_execute)

    payload = asyncio.run(
        orchestrator.start_task(
            task["id"],
            preview_payload={
                "packet": {
                    "objective": task["objective"],
                    "details": task["details"],
                    "assumptions": ["Keep continuity in the canonical run state."],
                }
            },
        )
    )

    receipt = orchestrator.store.load_context_receipt(payload["run_id"])
    evidence = orchestrator.get_run_evidence(payload["run_id"])

    assert receipt is not None
    assert receipt["task_id"] == task["id"]
    assert receipt["approved_objective"] == "Seed continuity receipts from the approved preview packet."
    assert receipt["accepted_assumptions"] == ["Keep continuity in the canonical run state."]
    assert receipt["allowed_paths"] == ["projects/tactics-game/artifacts/receipt.md"]
    assert evidence["context_receipt"]["task_id"] == task["id"]


def test_start_task_fails_closed_when_prompt_specialist_tracked_request_lacks_api_router_authority(tmp_path, monkeypatch):
    _prepare_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setattr("agents.role_base.create_model_client", lambda role: _UsageClient())

    orchestrator = Orchestrator(tmp_path)
    task = orchestrator.store.create_task(
        "program-kanban",
        "Tracked design preview usage",
        "Verify tracked prompt-specialist intake usage is recorded for a started request.",
        objective="Track prompt-specialist API usage for a design request preview.",
        raw_request="Design the first control-room gallery screen. Keep it review-first and avoid clutter.",
        expected_artifact_path="projects/program-kanban/artifacts/tracked_preview_usage.md",
    )

    async def _fake_execute_run(run_id: str, task: dict, *, local_exception_approval=None):
        return {"status": "completed", "run_status": "completed", "run_id": run_id, "task_id": task["id"]}

    monkeypatch.setattr(orchestrator, "_execute_run", _fake_execute_run)

    with pytest.raises(DelegatedExecutionBypassError, match="api_router"):
        asyncio.run(
            orchestrator.start_task(
                task["id"],
                preview_payload={
                    "packet": {
                        "objective": task["objective"],
                        "details": task["details"],
                        "assumptions": ["Keep the first pass review-first."],
                    },
                    "design_request_preview": {
                        "goal": task["objective"],
                        "target_surface": "control-room review gallery",
                        "style_direction": None,
                        "deliverables": ["design request preview", "screen or UI review packet"],
                        "constraints": ["Keep it review-first and avoid clutter."],
                        "open_questions": ["What visual direction or references should guide the first pass?"],
                    },
                },
            )
        )


def test_start_task_resolves_program_milestone_before_execution(tmp_path, monkeypatch):
    _prepare_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setattr("agents.role_base.create_model_client", lambda role: _DummyClient())

    orchestrator = Orchestrator(tmp_path)
    task = orchestrator.store.create_task(
        "program-kanban",
        "Preview gate milestone normalization",
        "Ensure design preview execution resolves its milestone before delegated work starts.",
        objective="Ensure design preview execution resolves its milestone before delegated work starts.",
        expected_artifact_path="projects/program-kanban/artifacts/pk075_preview_gate.md",
        acceptance={
            "proposed_milestone": "M8 - Visual Production And Digital Asset Management",
            "entry_goal": "Capture visual requests through a reviewable preview packet.",
            "exit_goal": "Preview-driven design requests can start with clear evidence and review gates.",
        },
        milestone_id=None,
    )
    orchestrator.store.update_task(task["id"], milestone_id=None)
    captured: dict[str, str | None] = {}

    async def _fake_execute_run(run_id: str, task: dict, *, local_exception_approval=None):
        captured["milestone_id"] = task.get("milestone_id")
        return {"status": "completed", "run_status": "completed", "run_id": run_id, "task_id": task["id"]}

    monkeypatch.setattr(orchestrator, "_execute_run", _fake_execute_run)

    result = asyncio.run(
        orchestrator.start_task(
            task["id"],
            preview_payload={
                "packet": {
                    "objective": task["objective"],
                    "details": task["details"],
                    "assumptions": [],
                },
                "proposed_milestone": "M8 - Visual Production And Digital Asset Management",
                "entry_goal": "Capture visual requests through a reviewable preview packet.",
                "exit_goal": "Preview-driven design requests can start with clear evidence and review gates.",
            },
        )
    )

    assert result["run_status"] == "completed"
    assert captured["milestone_id"] is not None
    refreshed = orchestrator.store.get_task(task["id"])
    assert refreshed is not None
    assert refreshed["milestone_id"] is not None


def test_execute_run_records_compliant_delegated_completion_once(tmp_path, monkeypatch):
    _prepare_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setattr("agents.role_base.create_model_client", lambda role: _DummyClient())

    orchestrator = Orchestrator(tmp_path)
    task = orchestrator.store.create_task(
        "tactics-game",
        "Delegated completion",
        "Verify a successful delegated run writes one compliance ledger row.",
        objective="Verify a successful delegated run writes one compliance ledger row.",
    )
    run = orchestrator.store.create_run("tactics-game", task["id"])

    async def _fake_execute_request(self, *, run_id: str, task: dict):
        return {"completed": True, "summary": "Delegated work completed successfully."}

    monkeypatch.setattr("agents.pm.ProjectManagerAgent.execute_request", _fake_execute_request)

    result = asyncio.run(orchestrator._execute_run(run["id"], task))
    records = orchestrator.store.list_compliance_records(run["id"])

    assert result["run_status"] == "completed"
    assert [record["record_kind"] for record in records] == ["compliant_delegated_run"]
    assert records[0]["compliance_state"] == "compliant"


def test_execute_run_pauses_immediately_on_budget_breach(tmp_path, monkeypatch):
    _prepare_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setattr("agents.role_base.create_model_client", lambda role: _DummyClient())

    orchestrator = Orchestrator(tmp_path)
    task = orchestrator.store.create_task(
        "tactics-game",
        "Budget breach",
        "Verify the orchestrator pauses on a budget violation.",
        objective="Verify the orchestrator pauses on a budget violation.",
    )
    run = orchestrator.store.create_run("tactics-game", task["id"])

    async def _fake_execute_request(self, *, run_id: str, task: dict):
        return {
            "paused": True,
            "completed": False,
            "summary": "Token budget exceeded during delegated work.",
            "breach": {
                "kind": "budget",
                "summary": "Token budget exceeded during delegated work.",
                "violations": ["token budget overage"],
                "local_exception_allowed": True,
            },
        }

    monkeypatch.setattr("agents.pm.ProjectManagerAgent.execute_request", _fake_execute_request)

    result = asyncio.run(orchestrator._execute_run(run["id"], task))
    updated_run = orchestrator.store.get_run(run["id"])
    approval = orchestrator.store.latest_approval_for_task(task["id"])
    evidence = orchestrator.get_run_evidence(run["id"])

    assert result["status"] == "paused_breach"
    assert result["approval_id"] == approval["id"]
    assert updated_run is not None
    assert updated_run["status"] == "paused_breach"
    assert updated_run["stop_reason"] == "awaiting_operator_exception"
    assert approval is not None
    assert approval["approval_scope"] == "program"
    assert approval["target_role"] == "Orchestrator"
    assert any(event["event_type"] == "compliance_breach_paused" for event in evidence["trace_events"])
    assert [record["record_kind"] for record in orchestrator.store.list_compliance_records(run["id"])] == ["breach"]


def test_approve_and_resume_records_local_exception_separately(tmp_path, monkeypatch):
    _prepare_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setattr("agents.role_base.create_model_client", lambda role: _DummyClient())

    orchestrator = Orchestrator(tmp_path)
    task = orchestrator.store.create_task(
        "tactics-game",
        "Local exception",
        "Verify local exception approvals resume distinctly from delegated runs.",
        objective="Verify local exception approvals resume distinctly from delegated runs.",
    )
    run = orchestrator.store.create_run("tactics-game", task["id"])
    approval = orchestrator.store.create_approval(
        run["id"],
        task["id"],
        "Orchestrator",
        "Token budget overage needs a one-shot local repair.",
        approval_scope="program",
        target_role="Orchestrator",
        exact_task=task["title"],
        expected_output=task.get("expected_artifact_path"),
        why_now="A local exception is needed to repair the framework once.",
        risks=["The repair should be approved only for this run."],
    )
    orchestrator.store.update_run(
        run["id"],
        status="paused_breach",
        stop_reason="awaiting_operator_exception",
        team_state={
            "phase": "awaiting_operator_exception",
            "runtime_mode": orchestrator.runtime_mode,
            "execution_mode": "local_exception",
            "compliance_state": {
                "mode": "local_exception_pending",
                "approval_id": approval["id"],
            },
        },
    )

    async def _fake_execute_request(self, *, run_id: str, task: dict):
        return {"completed": True, "summary": "Local exception repair completed."}

    monkeypatch.setattr("agents.pm.ProjectManagerAgent.execute_request", _fake_execute_request)

    receipt = orchestrator.store.save_context_receipt(
        run["id"],
        {
            "active_lane": task["id"],
            "approved_objective": task["objective"],
            "accepted_assumptions": ["Use a one-shot local exception only for this repair."],
            "next_reviewer": "Operator",
            "resume_conditions": ["Local exception approval is required before the same run can continue."],
        },
    )

    payload = asyncio.run(orchestrator.approve_and_resume(approval["id"], "Approve once for the repair."))
    updated_run = orchestrator.store.get_run(run["id"])
    updated_approval = orchestrator.store.get_approval(approval["id"])
    team_state = orchestrator.store.load_team_state(run["id"])
    resumed_receipt = orchestrator.store.load_context_receipt(run["id"])

    assert payload["run_status"] == "completed"
    assert updated_run is not None
    assert updated_run["status"] == "completed"
    assert updated_approval is not None
    assert updated_approval["status"] == "approved"
    assert team_state is not None
    assert team_state["execution_mode"] == "local_exception"
    assert team_state["compliance_state"]["mode"] == "local_exception_approved"
    assert receipt["accepted_assumptions"] == ["Use a one-shot local exception only for this repair."]
    assert resumed_receipt is not None
    assert resumed_receipt["accepted_assumptions"] == ["Use a one-shot local exception only for this repair."]
    assert resumed_receipt["next_reviewer"] == "Operator"
    assert resumed_receipt["resume_conditions"] == ["Review the recorded run evidence before opening the next lane."]
    assert [record["record_kind"] for record in orchestrator.store.list_compliance_records(run["id"])] == [
        "local_exception_approved"
    ]


def test_repeated_breach_after_resume_records_a_second_breach_immutably(tmp_path, monkeypatch):
    _prepare_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setattr("agents.role_base.create_model_client", lambda role: _DummyClient())

    orchestrator = Orchestrator(tmp_path)
    task = orchestrator.store.create_task(
        "tactics-game",
        "Repeated breach",
        "Verify a resumed breached run can record another independent breach.",
        objective="Verify a resumed breached run can record another independent breach.",
    )
    run = orchestrator.store.create_run("tactics-game", task["id"])
    breach_results = iter(
        [
            {
                "paused": True,
                "completed": False,
                "summary": "First breach detected during delegated work.",
                "breach": {
                    "kind": "budget",
                    "summary": "First breach detected during delegated work.",
                    "violations": ["first budget overage"],
                    "local_exception_allowed": True,
                },
            },
            {
                "paused": True,
                "completed": False,
                "summary": "Second breach detected after resume.",
                "breach": {
                    "kind": "budget",
                    "summary": "Second breach detected after resume.",
                    "violations": ["second budget overage"],
                    "local_exception_allowed": True,
                },
            },
        ]
    )

    async def _fake_execute_request(self, *, run_id: str, task: dict):
        return next(breach_results)

    monkeypatch.setattr("agents.pm.ProjectManagerAgent.execute_request", _fake_execute_request)

    first_pause = asyncio.run(orchestrator._execute_run(run["id"], task))
    resumed_pause = asyncio.run(orchestrator.approve_and_resume(first_pause["approval_id"], "Approve the first pause."))

    breach_records = orchestrator.store.list_compliance_records(run["id"], record_kind="breach")
    local_exception_approvals = orchestrator.store.list_local_exception_approvals(run["id"])

    assert first_pause["status"] == "paused_breach"
    assert resumed_pause["status"] == "paused_breach"
    assert resumed_pause["approval_id"] != first_pause["approval_id"]
    assert [record["evidence"]["summary"] for record in breach_records] == [
        "First breach detected during delegated work.",
        "Second breach detected after resume.",
    ]
    assert [record["record_kind"] for record in breach_records] == ["breach", "breach"]
    assert len(local_exception_approvals) == 1
    assert local_exception_approvals[0]["status"] == "approved"


def test_rejecting_breach_pause_cancels_run_without_local_exception_record(tmp_path, monkeypatch):
    _prepare_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setattr("agents.role_base.create_model_client", lambda role: _DummyClient())

    orchestrator = Orchestrator(tmp_path)
    task = orchestrator.store.create_task(
        "tactics-game",
        "Rejected breach",
        "Verify rejecting the breach pause cancels the run cleanly.",
        objective="Verify rejecting the breach pause cancels the run cleanly.",
    )
    run = orchestrator.store.create_run("tactics-game", task["id"])

    async def _fake_execute_request(self, *, run_id: str, task: dict):
        return {
            "paused": True,
            "completed": False,
            "summary": "Policy breach requires operator review.",
            "breach": {
                "kind": "policy",
                "summary": "Policy breach requires operator review.",
                "violations": ["policy guardrail"],
                "local_exception_allowed": True,
            },
        }

    monkeypatch.setattr("agents.pm.ProjectManagerAgent.execute_request", _fake_execute_request)

    first_pause = asyncio.run(orchestrator._execute_run(run["id"], task))
    rejection = orchestrator.reject(first_pause["approval_id"], "Reject the exception.")
    updated_run = orchestrator.store.get_run(run["id"])

    assert first_pause["status"] == "paused_breach"
    assert rejection["status"] == "rejected"
    assert updated_run is not None
    assert updated_run["status"] == "cancelled"
    assert updated_run["stop_reason"] == "approval_rejected"
    assert [record["record_kind"] for record in orchestrator.store.list_compliance_records(run["id"])] == ["breach"]
    assert orchestrator.store.list_local_exception_approvals(run["id"]) == []


def test_execute_run_escalates_worker_boundary_failures_to_blocked_parent_state(tmp_path, monkeypatch):
    _prepare_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setattr("agents.role_base.create_model_client", lambda role: _DummyClient())

    orchestrator = Orchestrator(tmp_path)
    task = orchestrator.store.create_task(
        "tactics-game",
        "Boundary violation",
        "Verify worker boundary failures block the parent run with preserved evidence.",
        objective="Verify worker boundary failures block the parent run with preserved evidence.",
    )
    run = orchestrator.store.create_run("tactics-game", task["id"])

    async def _fake_launch_worker_subtask(self, *, run_id: str, subtask: dict, correction_notes: str | None):
        manifest = self._build_write_manifest(run_id=run_id, subtask=subtask, correction_notes=correction_notes)
        self._update_worker_team_state(run_id=run_id, subtask=subtask, manifest=manifest)
        raise RuntimeError("Artifacts may only be written to the exact manifest-approved path.")

    monkeypatch.setattr("agents.pm.ProjectManagerAgent._launch_worker_subtask", _fake_launch_worker_subtask)

    try:
        asyncio.run(orchestrator._execute_run(run["id"], task))
    except RuntimeError as exc:
        assert "manifest-approved path" in str(exc)
    else:
        raise AssertionError("Worker boundary failures should propagate to the orchestrator.")

    updated_run = orchestrator.store.get_run(run["id"])
    updated_task = orchestrator.store.get_task(task["id"])
    subtask = orchestrator.store.get_subtasks(task["id"])[0]
    evidence = orchestrator.get_run_evidence(run["id"])

    assert updated_run is not None
    assert updated_run["status"] == "failed"
    assert "manifest-approved path" in updated_run["last_error"]
    assert updated_task is not None
    assert updated_task["status"] == "blocked"
    assert "manifest-approved path" in updated_task["review_notes"]
    assert subtask["status"] == "in_progress"
    assert evidence["worker_manifest"]["expected_output_path"] == subtask["expected_artifact_path"]
    assert evidence["context_receipt"]["active_lane"] == subtask["id"]
    assert evidence["context_receipt"]["allowed_paths"] == [subtask["expected_artifact_path"]]
    assert orchestrator.store.list_compliance_records(run["id"]) == []


def test_restore_then_resume_preserves_context_receipt_continuity(tmp_path, monkeypatch):
    _prepare_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setattr("agents.role_base.create_model_client", lambda role: _DummyClient())

    orchestrator = Orchestrator(tmp_path)
    task = orchestrator.store.create_task(
        "tactics-game",
        "Restore resume continuity",
        "Verify restore-safe approvals keep continuity receipts through resume.",
        objective="Verify restore-safe approvals keep continuity receipts through resume.",
        requires_approval=True,
        expected_artifact_path="projects/tactics-game/artifacts/restore_resume.md",
    )

    async def _fake_execute_request(self, *, run_id: str, task: dict):
        return {"completed": True, "summary": "Restore-safe approval run completed."}

    monkeypatch.setattr("agents.pm.ProjectManagerAgent.execute_request", _fake_execute_request)

    paused = asyncio.run(
        orchestrator.start_task(
            task["id"],
            preview_payload={
                "packet": {
                    "objective": task["objective"],
                    "details": task["details"],
                    "assumptions": ["Keep the original restore-safe continuity frame."],
                }
            },
        )
    )
    original_receipt = orchestrator.store.load_context_receipt(paused["run_id"])
    backup = orchestrator.store.create_dispatch_backup(
        project_name="tactics-game",
        trigger="pk099_restore_resume",
        task_id=task["id"],
        note="Capture the paused approval run before mutating continuity state.",
    )
    orchestrator.store.save_context_receipt(
        paused["run_id"],
        {
            "next_reviewer": "Architect",
            "resume_conditions": ["This mutated receipt should be replaced by restore."],
            "current_owner_role": "Developer",
        },
    )

    restore = orchestrator.store.restore_dispatch_backup(
        backup_id=backup["backup_id"],
        requested_by="PK-099 Test Runner",
    )
    restored_orchestrator = Orchestrator(tmp_path)
    restored_approval = restored_orchestrator.store.latest_approval_for_task(task["id"])

    assert restored_approval is not None

    restored_orchestrator.approve(restored_approval["id"], "Resume the restored run.")
    resumed = asyncio.run(restored_orchestrator.resume_run(paused["run_id"]))
    receipt = restored_orchestrator.store.load_context_receipt(paused["run_id"])
    evidence = restored_orchestrator.get_run_evidence(paused["run_id"])

    assert original_receipt is not None
    assert restore["source_run_id"] == paused["run_id"]
    assert restore["source_context_receipt"]["accepted_assumptions"] == [
        "Keep the original restore-safe continuity frame."
    ]
    assert resumed["run_status"] == "completed"
    assert receipt is not None
    assert receipt["accepted_assumptions"] == ["Keep the original restore-safe continuity frame."]
    assert receipt["next_reviewer"] == "Operator"
    assert receipt["current_owner_role"] == "QA"
    assert evidence["restore_history"][0]["restore_id"] == restore["restore_id"]
    assert evidence["restore_history"][0]["restored_run_id"] == paused["run_id"]
    assert evidence["context_receipt"]["accepted_assumptions"] == [
        "Keep the original restore-safe continuity frame."
    ]
