from __future__ import annotations

import asyncio
import json
from types import SimpleNamespace

import pytest

from agents.pm import ProjectManagerAgent
from agents.schemas import QAReviewResult
from agents.telemetry import TelemetryRecorder
from intake.compiler import compile_task_packet
from intake.gateway import classify_operator_request
from sessions import SessionStore
from skills.tools import WORKER_WRITE_MANIFEST_ENV, require_worker_write_manifest


def _prepare_repo(tmp_path):
    (tmp_path / "projects" / "tactics-game" / "execution").mkdir(parents=True)
    (tmp_path / "projects" / "tactics-game" / "governance").mkdir(parents=True)
    (tmp_path / "projects" / "tactics-game" / "artifacts").mkdir(parents=True)
    (tmp_path / "projects" / "program-kanban" / "execution").mkdir(parents=True)
    (tmp_path / "projects" / "program-kanban" / "governance").mkdir(parents=True)
    (tmp_path / "projects" / "program-kanban" / "artifacts").mkdir(parents=True)
    (tmp_path / "sessions").mkdir(parents=True)
    (tmp_path / "governance").mkdir(parents=True)
    (tmp_path / "logs").mkdir(parents=True)
    (tmp_path / "projects" / "tactics-game" / "governance" / "PROJECT_BRIEF.md").write_text(
        "# Brief\n\nTest project.\n",
        encoding="utf-8",
    )
    (tmp_path / "projects" / "program-kanban" / "governance" / "PROJECT_BRIEF.md").write_text(
        "# Brief\n\nProgram Kanban test project.\n",
        encoding="utf-8",
    )
    return tmp_path


class _DummyClient:
    async def close(self) -> None:
        return None


class _NoInlineProducer:
    async def produce_artifact(self, *args, **kwargs):
        raise AssertionError("Inline producer path should not run once worker delegation is enabled.")


class _QAStub:
    async def review_artifact(self, *, run_id: str, task: dict) -> QAReviewResult:
        return QAReviewResult(approved=True, summary="Approved", issues=[])


def _pm(tmp_path, monkeypatch) -> ProjectManagerAgent:
    monkeypatch.setattr("agents.role_base.create_model_client", lambda role: _DummyClient())
    store = SessionStore(tmp_path)
    telemetry = TelemetryRecorder(tmp_path)
    return ProjectManagerAgent(
        repo_root=tmp_path,
        store=store,
        telemetry=telemetry,
        project_brief="# Brief\n",
    )


def test_pm_pauses_before_dispatching_approved_subtask(tmp_path, monkeypatch):
    repo_root = _prepare_repo(tmp_path)
    pm = _pm(repo_root, monkeypatch)
    store = pm.store

    parent = store.create_task(
        "tactics-game",
        "Mage request",
        "Design and implement the mage class",
        objective="Design and implement the mage class",
    )
    run = store.create_run("tactics-game", parent["id"])
    developer_plan = next(item for item in pm._build_plan(parent).subtasks if item.assignee == "Developer")
    subtask = pm._create_subtask(parent, developer_plan)

    result = asyncio.run(pm._run_subtask(run_id=run["id"], subtask=subtask))
    approval = store.latest_approval_for_task(subtask["id"])

    assert result["paused"] is True
    assert approval is not None
    assert approval["status"] == "pending"
    assert approval["approval_scope"] == "project"
    assert approval["target_role"] == "Developer"


def test_pm_sdk_pause_records_specialist_approval_bridge(tmp_path, monkeypatch):
    repo_root = _prepare_repo(tmp_path)
    monkeypatch.setenv("AISTUDIO_RUNTIME_MODE", "sdk")
    pm = _pm(repo_root, monkeypatch)
    store = pm.store

    parent = store.create_task(
        "tactics-game",
        "Beacon request",
        "Design and implement the beacon class",
        objective="Design and implement the beacon class",
    )
    run = store.create_run("tactics-game", parent["id"], team_state={"runtime_mode": "sdk"})
    developer_plan = next(item for item in pm._build_plan(parent).subtasks if item.assignee == "Developer")
    subtask = pm._create_subtask(parent, developer_plan)

    result = asyncio.run(pm._run_subtask(run_id=run["id"], subtask=subtask))
    evidence = store.get_run_evidence(run["id"])
    bridge_event = next(item for item in evidence["trace_events"] if item["event_type"] == "sdk_approval_bridge_requested")
    receipt = store.load_context_receipt(run["id"])

    assert result["paused"] is True
    assert result["team_state"]["pending_sdk_approval"]["session_id"] == f"studio-specialist-developer-{run['id']}"
    assert bridge_event["payload"]["packet"]["target_role"] == "Developer"
    assert bridge_event["payload"]["packet"]["runtime_mode"] == "sdk"
    assert receipt is not None
    assert receipt["active_lane"] == subtask["id"]
    assert receipt["next_reviewer"] == "Operator"
    assert receipt["specialist_role"] == "Developer"
    assert receipt["expected_output"] == subtask["expected_artifact_path"]
    assert receipt["resume_conditions"] == ["Dispatch approval is required before the specialist lane can continue."]


def test_pm_custom_runtime_pause_does_not_create_sdk_bridge(tmp_path, monkeypatch):
    repo_root = _prepare_repo(tmp_path)
    pm = _pm(repo_root, monkeypatch)
    store = pm.store

    parent = store.create_task(
        "tactics-game",
        "Sentinel request",
        "Design and implement the sentinel class",
        objective="Design and implement the sentinel class",
    )
    run = store.create_run("tactics-game", parent["id"], team_state={"runtime_mode": "custom"})
    developer_plan = next(item for item in pm._build_plan(parent).subtasks if item.assignee == "Developer")
    subtask = pm._create_subtask(parent, developer_plan)

    result = asyncio.run(pm._run_subtask(run_id=run["id"], subtask=subtask))
    team_state = store.load_team_state(run["id"])
    evidence = store.get_run_evidence(run["id"])

    assert result["paused"] is True
    assert result["team_state"] is None
    assert team_state is not None
    assert "pending_sdk_approval" not in team_state
    assert not any(event["event_type"] == "sdk_approval_bridge_requested" for event in evidence["trace_events"])


def test_pm_uses_program_kanban_capability_registry_defaults(tmp_path, monkeypatch):
    repo_root = _prepare_repo(tmp_path)
    pm = _pm(repo_root, monkeypatch)
    store = pm.store

    parent = store.create_task(
        "program-kanban",
        "Capability registry request",
        "Replace hardcoded planning assumptions with a capability registry",
        objective="Replace hardcoded planning assumptions with a capability registry",
        expected_artifact_path="agents/config.py",
    )

    plan = pm._build_plan(parent)
    assert len(plan.subtasks) == 1

    subtask_plan = plan.subtasks[0]
    assert subtask_plan.assignee == "Architect"
    assert subtask_plan.deliverable_type == "architecture_note"
    assert subtask_plan.expected_artifact_path == "projects/program-kanban/artifacts/capability-registry_architecture.md"
    assert subtask_plan.allowed_tools == ["read_project_brief", "write_project_artifact"]
    assert subtask_plan.assigned_tier == "tier_2_mid"
    assert subtask_plan.expected_output_format == "markdown"
    assert subtask_plan.acceptance.deliverable_contract is not None
    assert subtask_plan.acceptance.deliverable_contract.kind == "review"
    assert subtask_plan.acceptance.deliverable_contract.summary.startswith("Review-oriented architecture note")

    subtask = pm._create_subtask(parent, subtask_plan)
    assert subtask["acceptance"]["deliverable_type"] == "architecture_note"
    assert subtask["acceptance"]["allowed_tools"] == ["read_project_brief", "write_project_artifact"]
    assert subtask["acceptance"]["assigned_tier"] == "tier_2_mid"
    assert subtask["acceptance"]["expected_output_format"] == "markdown"
    assert subtask["acceptance"]["deliverable_contract"]["kind"] == "review"
    assert subtask["acceptance"]["deliverable_contract"]["evidence_surface"] == "run-details.artifacts and run-details.trace_events"


def test_pm_attaches_deliverable_contracts_for_ladder_specs(tmp_path, monkeypatch):
    repo_root = _prepare_repo(tmp_path)
    pm = _pm(repo_root, monkeypatch)
    store = pm.store

    parent = store.create_task(
        "tactics-game",
        "Mage request",
        "Design and implement the mage class",
        objective="Design and implement the mage class",
    )

    plan = pm._build_plan(parent)
    plans = {item.deliverable_type: item for item in plan.subtasks}

    assert plans["architecture_note"].acceptance.deliverable_contract is not None
    assert plans["architecture_note"].acceptance.deliverable_contract.kind == "review"
    assert plans["architecture_note"].assigned_tier == "tier_2_mid"
    assert plans["python_module"].acceptance.deliverable_contract is not None
    assert plans["python_module"].acceptance.deliverable_contract.kind == "code"
    assert plans["python_module"].acceptance.deliverable_contract.required_input_role == "Architect"
    assert plans["python_module"].assigned_tier == "tier_3_junior"
    assert plans["python_module"].expected_output_format == "python"
    assert plans["ui_notes"].acceptance.deliverable_contract is not None
    assert plans["ui_notes"].acceptance.deliverable_contract.kind == "review"


def test_pm_parent_review_requires_validation_results(tmp_path, monkeypatch):
    repo_root = _prepare_repo(tmp_path)
    pm = _pm(repo_root, monkeypatch)
    store = pm.store

    parent = store.create_task(
        "tactics-game",
        "Mage request",
        "Design and implement the mage class",
        objective="Design and implement the mage class",
    )
    subtask = store.create_subtask(
        "tactics-game",
        parent["id"],
        "Mage design",
        "Write the design doc",
        objective="Create the mage design doc",
        owner_role="Architect",
        priority="medium",
        expected_artifact_path="projects/tactics-game/artifacts/mage_design.md",
        acceptance={"required_headings": ["Overview", "Attributes"]},
    )
    artifact_path = repo_root / subtask["expected_artifact_path"]
    artifact_path.write_text("# Overview\n\n## Attributes\n", encoding="utf-8")
    store.update_task(subtask["id"], status="completed", owner_role="QA", result_summary="Approved")
    run = store.create_run("tactics-game", parent["id"])

    first_review = asyncio.run(pm._review_parent_task(run_id=run["id"], parent_task=parent))
    assert first_review.approved is False
    assert any("Missing passing validation result" in issue for issue in first_review.issues)

    store.record_validation_result(
        run["id"],
        subtask["id"],
        agent_run_id=None,
        validator_role="QA",
        artifact_path=subtask["expected_artifact_path"],
        status="passed",
        checks={"artifact_exists": True},
        summary="Validated",
    )

    second_review = asyncio.run(pm._review_parent_task(run_id=run["id"], parent_task=parent))
    assert second_review.approved is True


def test_pm_launches_worker_with_sealed_manifest_for_architect_subtask(tmp_path, monkeypatch):
    repo_root = _prepare_repo(tmp_path)
    pm = _pm(repo_root, monkeypatch)
    store = pm.store
    pm.architect = _NoInlineProducer()
    pm.qa = _QAStub()

    parent = store.create_task(
        "tactics-game",
        "Mage request",
        "Design and implement the mage class",
        objective="Design and implement the mage class",
    )
    run = store.create_run("tactics-game", parent["id"])
    architect_plan = next(item for item in pm._build_plan(parent).subtasks if item.assignee == "Architect")
    subtask = pm._create_subtask(parent, architect_plan)
    captured: dict[str, object] = {}

    async def _fake_launch_worker_subtask(*, run_id: str, subtask: dict, correction_notes: str | None):
        manifest = pm._build_write_manifest(run_id=run_id, subtask=subtask, correction_notes=correction_notes)
        captured["manifest"] = json.loads(pm._canonical_manifest_json(manifest))
        pm._update_worker_team_state(run_id=run_id, subtask=subtask, manifest=manifest)
        return {"role": subtask["owner_role"], "task_id": subtask["id"], "artifact_path": subtask["expected_artifact_path"]}

    monkeypatch.setattr(pm, "_launch_worker_subtask", _fake_launch_worker_subtask)

    result = asyncio.run(pm._run_subtask(run_id=run["id"], subtask=subtask))
    team_state = store.load_team_state(run["id"])

    assert result["approved"] is True
    assert captured["manifest"]["execution_mode"] == "worker_only"
    assert captured["manifest"]["role"] == "Architect"
    assert captured["manifest"]["allowed_write_paths"] == [subtask["expected_artifact_path"]]
    assert captured["manifest"]["expected_output_path"] == subtask["expected_artifact_path"]
    assert team_state is not None
    assert team_state["execution_mode"] == "worker_only"
    assert team_state["worker_dispatch"]["task_id"] == subtask["id"]


def test_pm_updates_context_receipt_from_worker_manifest(tmp_path, monkeypatch):
    repo_root = _prepare_repo(tmp_path)
    pm = _pm(repo_root, monkeypatch)
    store = pm.store

    parent = store.create_task(
        "program-kanban",
        "Receipt hardening",
        "Persist continuity receipts during specialist handoff",
        objective="Persist continuity receipts during specialist handoff",
        expected_artifact_path="projects/program-kanban/artifacts/receipt_parent.md",
    )
    run = store.create_run("program-kanban", parent["id"], team_state={"runtime_mode": "sdk"})
    subtask_plan = pm._build_plan(parent).subtasks[0]
    subtask = pm._create_subtask(parent, subtask_plan)
    manifest = pm._build_write_manifest(run_id=run["id"], subtask=subtask, correction_notes=None)

    pm._update_worker_team_state(run_id=run["id"], subtask=subtask, manifest=manifest)

    receipt = store.load_context_receipt(run["id"])

    assert receipt is not None
    assert receipt["task_id"] == parent["id"]
    assert receipt["active_lane"] == subtask["id"]
    assert receipt["allowed_tools"] == ["read_project_brief", "write_project_artifact"]
    assert receipt["allowed_paths"] == [subtask["expected_artifact_path"]]
    assert receipt["expected_output"] == subtask["expected_artifact_path"]
    assert receipt["next_reviewer"] == "QA"
    assert receipt["specialist_role"] == "Architect"


def test_pm_runs_approved_developer_subtask_via_worker_manifest(tmp_path, monkeypatch):
    repo_root = _prepare_repo(tmp_path)
    pm = _pm(repo_root, monkeypatch)
    store = pm.store
    pm.developer = _NoInlineProducer()
    pm.qa = _QAStub()

    parent = store.create_task(
        "tactics-game",
        "Mage request",
        "Design and implement the mage class",
        objective="Design and implement the mage class",
    )
    run = store.create_run("tactics-game", parent["id"], team_state={"runtime_mode": "sdk"})
    developer_plan = next(item for item in pm._build_plan(parent).subtasks if item.assignee == "Developer")
    subtask = pm._create_subtask(parent, developer_plan)
    approval = store.create_approval(run["id"], subtask["id"], "PM", "Dispatch developer work", approval_scope="project", target_role="Developer")
    store.decide_approval(approval["id"], "approve")
    captured: dict[str, object] = {}

    async def _fake_launch_worker_subtask(*, run_id: str, subtask: dict, correction_notes: str | None):
        manifest = pm._build_write_manifest(run_id=run_id, subtask=subtask, correction_notes=correction_notes)
        captured["manifest"] = json.loads(pm._canonical_manifest_json(manifest))
        pm._update_worker_team_state(run_id=run_id, subtask=subtask, manifest=manifest)
        return {"role": subtask["owner_role"], "task_id": subtask["id"], "artifact_path": subtask["expected_artifact_path"]}

    monkeypatch.setattr(pm, "_launch_worker_subtask", _fake_launch_worker_subtask)

    result = asyncio.run(pm._run_subtask(run_id=run["id"], subtask=subtask))
    team_state = store.load_team_state(run["id"])

    assert result["approved"] is True
    assert captured["manifest"]["role"] == "Developer"
    assert captured["manifest"]["runtime_mode"] == "sdk"
    assert captured["manifest"]["write_scope"] == "exact_paths_only"
    assert captured["manifest"]["seal_sha256"]
    assert team_state is not None
    assert team_state["execution_mode"] == "worker_only"
    assert "pending_sdk_approval" not in team_state


def test_pm_registers_visual_artifact_from_worker_output_before_qa(tmp_path, monkeypatch):
    repo_root = _prepare_repo(tmp_path)
    design_dir = repo_root / "projects" / "tactics-game" / "artifacts" / "design"
    design_dir.mkdir(parents=True)
    pm = _pm(repo_root, monkeypatch)
    store = pm.store
    pm.design = _NoInlineProducer()
    pm.qa = _QAStub()

    parent = store.create_task(
        "tactics-game",
        "Concept request",
        "Create a visual concept variant",
        objective="Create a visual concept variant",
    )
    run = store.create_run("tactics-game", parent["id"])
    subtask = store.create_subtask(
        "tactics-game",
        parent["id"],
        "Concept variant",
        "Create a visual concept variant for review",
        objective="Create a visual concept variant for review",
        owner_role="Design",
        priority="medium",
        expected_artifact_path="projects/tactics-game/artifacts/design/concept-variant.txt",
        acceptance={
            "deliverable_type": "image",
            "deliverable_contract": {"kind": "image"},
            "allowed_tools": ["write_project_artifact"],
        },
    )
    base_path = design_dir / "concept-base.txt"
    base_path.write_text("base concept", encoding="utf-8")
    root = store.create_visual_artifact(
        "tactics-game",
        subtask["id"],
        run_id=run["id"],
        artifact_path="projects/tactics-game/artifacts/design/concept-base.txt",
        provider="openai",
        model="gpt-image-1",
        prompt_summary="Base concept.",
        selected_direction=True,
        metadata={"variant": "base"},
    )

    async def _fake_launch_worker_subtask(*, run_id: str, subtask: dict, correction_notes: str | None):
        manifest = pm._build_write_manifest(run_id=run_id, subtask=subtask, correction_notes=correction_notes)
        pm._update_worker_team_state(run_id=run_id, subtask=subtask, manifest=manifest)
        artifact_path = repo_root / subtask["expected_artifact_path"]
        artifact_path.write_text("concept variant", encoding="utf-8")
        return {
            "role": subtask["owner_role"],
            "task_id": subtask["id"],
            "agent_run_id": "agent_run_visual_test",
            "summary": "Generated concept variant",
            "artifact_path": subtask["expected_artifact_path"],
            "parent_visual_artifact_id": root["id"],
            "lineage_root_visual_artifact_id": root["id"],
            "locked_base_visual_artifact_id": root["id"],
            "edit_session_id": "edit-session-002",
            "edit_intent": "localized_edit",
            "edit_scope": {"mode": "localized_edit", "regions": ["armor"]},
            "protected_regions": ["face", "hands", "background"],
            "mask_reference": {"kind": "region_mask", "path": "projects/tactics-game/artifacts/design/mask.json"},
            "iteration_index": 1,
        }

    monkeypatch.setattr(pm, "_launch_worker_subtask", _fake_launch_worker_subtask)

    result = asyncio.run(pm._run_subtask(run_id=run["id"], subtask=subtask))
    registered = store.list_visual_artifacts("tactics-game", task_id=subtask["id"])
    evidence = store.get_run_evidence(run["id"])
    registered_variant = next(
        item for item in registered if item["artifact_path"] == subtask["expected_artifact_path"]
    )

    assert result["approved"] is True
    assert len(registered) == 2
    assert registered_variant["artifact_path"] == subtask["expected_artifact_path"]
    assert registered_variant["provider"] == "openai"
    assert registered_variant["metadata"]["registered_by"] == "Framework"
    assert registered_variant["metadata"]["registration_mode"] == "deterministic"
    assert registered_variant["metadata"]["agent_run_id"] == "agent_run_visual_test"
    assert registered_variant["parent_visual_artifact_id"] == root["id"]
    assert registered_variant["lineage_root_visual_artifact_id"] == root["id"]
    assert registered_variant["locked_base_visual_artifact_id"] == root["id"]
    assert registered_variant["edit_session_id"] == "edit-session-002"
    assert registered_variant["edit_intent"] == "localized_edit"
    assert registered_variant["edit_scope"]["regions"] == ["armor"]
    assert registered_variant["protected_regions"] == ["face", "hands", "background"]
    assert registered_variant["mask_reference"]["kind"] == "region_mask"
    assert registered_variant["iteration_index"] == 1
    assert any(event["event_type"] == "media_service_visual_registered" for event in evidence["trace_events"])
    evidence_artifact = next(item for item in evidence["visual_artifacts"] if item["id"] == registered_variant["id"])
    assert evidence_artifact["id"] == registered_variant["id"]
    assert evidence_artifact["lineage_root_visual_artifact_id"] == root["id"]
    assert evidence_artifact["locked_base_visual_artifact_id"] == root["id"]
    assert evidence_artifact["edit_session_id"] == "edit-session-002"


def test_pm_worker_manifest_matches_tools_consumer_contract(tmp_path, monkeypatch):
    repo_root = _prepare_repo(tmp_path)
    pm = _pm(repo_root, monkeypatch)
    store = pm.store

    parent = store.create_task(
        "tactics-game",
        "Mage request",
        "Design and implement the mage class",
        objective="Design and implement the mage class",
    )
    run = store.create_run("tactics-game", parent["id"])
    architect_plan = next(item for item in pm._build_plan(parent).subtasks if item.assignee == "Architect")
    subtask = pm._create_subtask(parent, architect_plan)
    captured: dict[str, object] = {}

    def _fake_subprocess_run(command, *, cwd, env, capture_output, text, check):
        captured["env"] = env
        return SimpleNamespace(
            returncode=0,
            stdout=json.dumps(
                {
                    "role": subtask["owner_role"],
                    "task_id": subtask["id"],
                    "artifact_path": subtask["expected_artifact_path"],
                    "summary": "ok",
                }
            )
            + "\n",
            stderr="",
        )

    monkeypatch.setattr("agents.pm.subprocess.run", _fake_subprocess_run)

    result = asyncio.run(pm._launch_worker_subtask(run_id=run["id"], subtask=subtask, correction_notes=None))

    manifest_json = captured["env"][WORKER_WRITE_MANIFEST_ENV]
    monkeypatch.setenv(WORKER_WRITE_MANIFEST_ENV, manifest_json)
    validated = require_worker_write_manifest(
        role=subtask["owner_role"],
        run_id=run["id"],
        task_id=subtask["id"],
        project_name=subtask["project_name"],
        runtime_mode=pm._runtime_mode(run["id"]),
        expected_output_path=subtask["expected_artifact_path"],
    )

    assert result["artifact_path"] == subtask["expected_artifact_path"]
    assert validated["expected_output_path"] == subtask["expected_artifact_path"]
    assert validated["allowed_tools"] == ["read_project_brief", "write_project_artifact"]


def test_pm_rejects_subtask_role_not_allowed_by_task_packet(tmp_path, monkeypatch):
    repo_root = _prepare_repo(tmp_path)
    pm = _pm(repo_root, monkeypatch)
    store = pm.store

    packet = compile_task_packet(classify_operator_request("Implement the gateway"))
    narrowed_packet = {
        **packet.model_dump(),
        "allowed_roles": ["Orchestrator", "PromptSpecialist", "PM", "Developer", "Design", "QA"],
    }
    parent = store.create_task(
        "program-kanban",
        "Architecture request",
        "Define the architecture contract",
        objective="Define the architecture contract",
        acceptance={"task_packet": narrowed_packet},
    )
    run = store.create_run("program-kanban", parent["id"])
    architect_plan = pm._build_plan(parent).subtasks[0]
    subtask = pm._create_subtask(parent, architect_plan)

    with pytest.raises(RuntimeError, match="TaskPacket disallows role: Architect"):
        asyncio.run(pm._run_subtask(run_id=run["id"], subtask=subtask))


def test_pm_rejects_subtask_tool_not_allowed_by_task_packet(tmp_path, monkeypatch):
    repo_root = _prepare_repo(tmp_path)
    pm = _pm(repo_root, monkeypatch)
    store = pm.store

    packet = compile_task_packet(classify_operator_request("Implement the gateway"))
    narrowed_packet = {
        **packet.model_dump(),
        "allowed_tools": ["model_client.create", "api_responses_create"],
    }
    parent = store.create_task(
        "program-kanban",
        "Architecture request",
        "Define the architecture contract",
        objective="Define the architecture contract",
        acceptance={"task_packet": narrowed_packet},
    )
    run = store.create_run("program-kanban", parent["id"])
    architect_plan = pm._build_plan(parent).subtasks[0]
    subtask = pm._create_subtask(parent, architect_plan)

    with pytest.raises(RuntimeError, match="TaskPacket disallows tool: read_project_brief"):
        asyncio.run(pm._run_subtask(run_id=run["id"], subtask=subtask))
