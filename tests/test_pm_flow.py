from __future__ import annotations

import asyncio
import json
from types import SimpleNamespace

from agents.pm import ProjectManagerAgent
from agents.schemas import QAReviewResult
from agents.telemetry import TelemetryRecorder
from sessions import SessionStore
from skills.tools import WORKER_WRITE_MANIFEST_ENV, require_worker_write_manifest


def _prepare_repo(tmp_path):
    (tmp_path / "projects" / "tactics-game" / "execution").mkdir(parents=True)
    (tmp_path / "projects" / "tactics-game" / "governance").mkdir(parents=True)
    (tmp_path / "projects" / "tactics-game" / "artifacts").mkdir(parents=True)
    (tmp_path / "sessions").mkdir(parents=True)
    (tmp_path / "governance").mkdir(parents=True)
    (tmp_path / "logs").mkdir(parents=True)
    (tmp_path / "projects" / "tactics-game" / "governance" / "PROJECT_BRIEF.md").write_text(
        "# Brief\n\nTest project.\n",
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

    assert result["paused"] is True
    assert result["team_state"]["pending_sdk_approval"]["session_id"] == f"studio-specialist-developer-{run['id']}"
    assert bridge_event["payload"]["packet"]["target_role"] == "Developer"
    assert bridge_event["payload"]["packet"]["runtime_mode"] == "sdk"


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
