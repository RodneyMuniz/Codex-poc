from __future__ import annotations

import json
import sqlite3

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
    assert "Ready" in kanban
    assert "Done" in kanban
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
