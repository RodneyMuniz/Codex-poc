from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from sessions import SessionStore


def _prepare_repo(tmp_path):
    (tmp_path / "projects" / "tactics-game" / "execution").mkdir(parents=True)
    (tmp_path / "projects" / "tactics-game" / "governance").mkdir(parents=True)
    (tmp_path / "sessions").mkdir(parents=True)
    (tmp_path / "governance").mkdir(parents=True)
    (tmp_path / "projects" / "tactics-game" / "governance" / "PROJECT_BRIEF.md").write_text(
        "# Brief\n\nTest project.\n",
        encoding="utf-8",
    )
    (tmp_path / "sessions" / "approvals.json").write_text("", encoding="utf-8")
    return tmp_path


def test_store_persists_queue_states_subtasks_and_kanban(tmp_path):
    repo_root = _prepare_repo(tmp_path)
    store = SessionStore(repo_root)

    task = store.create_task("tactics-game", "Mage request", "Design and implement the mage class", requires_approval=True)
    assert task["status"] == "backlog"

    subtask = store.create_subtask(
        "tactics-game",
        task["id"],
        "Mage design",
        "Write the design doc",
        objective="Create the mage design doc",
        owner_role="Architect",
        priority="medium",
        expected_artifact_path="projects/tactics-game/artifacts/mage_design.md",
        acceptance={"required_headings": ["Overview", "Attributes"]},
    )
    assert subtask["task_kind"] == "subtask"
    assert subtask["parent_task_id"] == task["id"]

    run = store.create_run("tactics-game", task["id"])
    approval = store.create_approval(run["id"], task["id"], "Orchestrator", "High impact request")
    assert approval["status"] == "pending"

    decided = store.decide_approval(approval["id"], "approve", "Looks good")
    assert decided["status"] == "approved"

    store.update_task(subtask["id"], status="completed", owner_role="QA", result_summary="Approved")
    store.update_task(task["id"], status="completed", owner_role="QA", result_summary="Complete")

    kanban = (repo_root / "projects" / "tactics-game" / "execution" / "KANBAN.md").read_text(encoding="utf-8")
    assert "Backlog" in kanban
    assert "Ready for Build" in kanban
    assert "Complete" in kanban
    assert "Mage request" in kanban


def test_store_records_messages_and_usage(tmp_path):
    repo_root = _prepare_repo(tmp_path)
    store = SessionStore(repo_root)
    task = store.create_task("tactics-game", "Telemetry Task", "Verify message logging")
    run = store.create_run("tactics-game", task["id"])

    store.record_message(
        run["id"],
        task["id"],
        "agent_text",
        {"content": "hello"},
        source="PM",
        prompt_tokens=11,
        completion_tokens=7,
    )

    connection = sqlite3.connect(store.paths.db_path)
    try:
        messages = connection.execute("SELECT payload_json FROM messages").fetchall()
        usage = connection.execute("SELECT prompt_tokens, completion_tokens FROM usage_events").fetchall()
    finally:
        connection.close()

    assert json.loads(messages[0][0])["content"] == "hello"
    assert usage[0] == (11, 7)


def test_store_run_evidence_includes_trace_events(tmp_path):
    repo_root = _prepare_repo(tmp_path)
    store = SessionStore(repo_root)
    task = store.create_task("tactics-game", "Trace Task", "Verify trace ledger recording")
    run = store.create_run("tactics-game", task["id"])

    store.record_trace_event(
        run["id"],
        task["id"],
        "operator_request_confirmed",
        source="Orchestrator",
        summary="Operator confirmed the request.",
        packet={"objective": "Verify trace ledger recording"},
        route={"runtime_role": "Orchestrator", "model": "gpt-test"},
        raw_json={"request_text": "Verify trace ledger recording"},
    )

    evidence = store.get_run_evidence(run["id"])

    assert evidence["trace_events"][0]["event_type"] == "operator_request_confirmed"
    assert evidence["trace_events"][0]["payload"]["summary"] == "Operator confirmed the request."


def test_store_run_evidence_includes_sdk_runtime_summary(tmp_path):
    repo_root = _prepare_repo(tmp_path)
    store = SessionStore(repo_root)
    task = store.create_task("tactics-game", "SDK Task", "Verify SDK runtime evidence")
    run = store.create_run(
        "tactics-game",
        task["id"],
        team_state={
            "runtime_mode": "sdk",
            "specialist_runtime": {
                "mode": "sdk",
                "orchestrator_source": "chat_or_control_room",
                "planning_layer": "deterministic_internal_helper",
                "specialist_roles": ["Architect", "Developer", "Design"],
            },
        },
    )
    agent_run = store.create_agent_run(run["id"], task["id"], "Architect")
    store.record_trace_event(
        run["id"],
        task["id"],
        "sdk_specialist_result_received",
        source="Architect",
        summary="Architect session completed.",
        packet={
            "session_id": f"studio-specialist-architect-{run['id']}",
            "response_id": "resp_test",
            "trace_id": "trace_test",
            "model": "gpt-4.1-mini",
        },
        route={"runtime_role": "Architect", "runtime_mode": "sdk"},
        raw_json={"role": "Architect"},
    )
    store.record_trace_event(
        run["id"],
        task["id"],
        "sdk_approval_bridge_requested",
        source="PM",
        summary="Paused for SDK specialist approval.",
        packet={
            "approval_id": "approval_test",
            "target_role": "Developer",
            "session_id": f"studio-specialist-developer-{run['id']}",
            "expected_artifact_path": "projects/tactics-game/artifacts/sdk.py",
            "runtime_mode": "sdk",
        },
        route={"runtime_role": "Developer", "runtime_mode": "sdk"},
        raw_json={"approval_id": "approval_test"},
    )

    evidence = store.get_run_evidence(run["id"])

    assert evidence["sdk_runtime"]["mode"] == "sdk"
    assert evidence["sdk_runtime"]["sessions"][0]["session_id"] == f"studio-specialist-architect-{run['id']}"
    assert evidence["sdk_runtime"]["approval_bridge_events"][0]["approval_id"] == "approval_test"
    assert evidence["sdk_runtime"]["specialist_run_count"] == 1


def test_create_dispatch_backup_writes_backup_and_manifest(tmp_path):
    repo_root = _prepare_repo(tmp_path)
    store = SessionStore(repo_root)
    task = store.create_task("tactics-game", "Backup Task", "Verify pre-dispatch backups")

    backup = store.create_dispatch_backup(
        project_name="tactics-game",
        trigger="dispatch_request",
        task_id=task["id"],
        note="Verify pre-dispatch backups",
    )

    assert Path(backup["path"]).exists()
    assert Path(backup["manifest_path"]).exists()
    assert backup["sha256"]

    connection = sqlite3.connect(backup["path"])
    try:
        tables = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type = 'table'")}
    finally:
        connection.close()
    assert "tasks" in tables

    manifest = json.loads(Path(backup["manifest_path"]).read_text(encoding="utf-8"))
    assert manifest["project_name"] == "tactics-game"
    assert manifest["task_id"] == task["id"]


def test_restore_dispatch_backup_restores_db_and_creates_receipt(tmp_path):
    repo_root = _prepare_repo(tmp_path)
    store = SessionStore(repo_root)
    task = store.create_task("tactics-game", "Restore Task", "Verify control-room restore flow")

    backup = store.create_dispatch_backup(
        project_name="tactics-game",
        trigger="restore_test",
        task_id=task["id"],
        note="Create a snapshot before changing task state.",
    )

    store.update_task(task["id"], status="in_progress", owner_role="Developer", result_summary="State changed")
    changed = store.get_task(task["id"])
    assert changed is not None
    assert changed["status"] == "in_progress"

    restore = store.restore_dispatch_backup(backup_id=backup["backup_id"], requested_by="Test Runner")

    restored_store = SessionStore(repo_root)
    restored_task = restored_store.get_task(task["id"])

    assert restored_task is not None
    assert restored_task["status"] == "backlog"
    assert Path(restore["receipt_path"]).exists()
    assert Path(restore["pre_restore_backup"]["path"]).exists()
    assert restore["store_health"]["ok"] is True


def test_program_kanban_ready_gate_requires_milestone_and_expected_output(tmp_path):
    repo_root = _prepare_repo(tmp_path)
    (repo_root / "projects" / "program-kanban" / "execution").mkdir(parents=True)
    (repo_root / "projects" / "program-kanban" / "governance").mkdir(parents=True)
    (repo_root / "projects" / "program-kanban" / "governance" / "PROJECT_BRIEF.md").write_text(
        "# Brief\n\nProgram Kanban.\n",
        encoding="utf-8",
    )
    store = SessionStore(repo_root)

    task = store.create_task(
        "program-kanban",
        "Restore milestone view",
        "Implement the milestone wall.",
        objective="Implement the milestone wall.",
        owner_role="Dashboard Implementer",
        assigned_role="Dashboard Implementer",
        acceptance={
            "proposed_milestone": "M1 - Basic Operation Level",
            "entry_goal": "The board is missing milestone review.",
            "exit_goal": "Milestones are visible again.",
            "approved_decisions": {"progress_formula": "completed/total"},
        },
    )

    try:
        store.update_task(task["id"], status="ready")
        assert False, "Expected the Ready for Build gate to reject missing expected output."
    except ValueError as error:
        assert "Missing expected artifact or output." in str(error)

    updated = store.update_task(
        task["id"],
        expected_artifact_path="projects/program-kanban/app/app.js",
        status="ready",
    )
    assert updated["status"] == "ready"
    assert updated["milestone_id"] is not None
    milestone = store.get_milestone(updated["milestone_id"])
    assert milestone is not None
    assert milestone["title"] == "M1 - Basic Operation Level"


def test_program_kanban_complete_requires_explicit_acceptance(tmp_path):
    repo_root = _prepare_repo(tmp_path)
    (repo_root / "projects" / "program-kanban" / "execution").mkdir(parents=True)
    (repo_root / "projects" / "program-kanban" / "governance").mkdir(parents=True)
    (repo_root / "projects" / "program-kanban" / "governance" / "PROJECT_BRIEF.md").write_text(
        "# Brief\n\nProgram Kanban.\n",
        encoding="utf-8",
    )
    store = SessionStore(repo_root)

    task = store.create_task(
        "program-kanban",
        "Define workflow columns",
        "Capture the workflow model.",
        objective="Capture the workflow model.",
        owner_role="Project Orchestrator",
        assigned_role="Project Orchestrator",
        expected_artifact_path="projects/program-kanban/governance/spec.md",
        acceptance={
            "proposed_milestone": "M1 - Basic Operation Level",
            "entry_goal": "Columns are undefined.",
            "exit_goal": "Columns are approved.",
            "approved_decisions": {"columns": ["Backlog", "Ready for Build"]},
        },
    )
    store.update_task(task["id"], status="ready")

    try:
        store.update_task(task["id"], status="completed")
        assert False, "Expected Complete to require Accepted review state."
    except ValueError as error:
        assert "Complete requires review_state 'Accepted'." in str(error)

    completed = store.update_task(task["id"], status="completed", review_state="Accepted")
    assert completed["status"] == "completed"
    assert completed["review_state"] == "Accepted"
