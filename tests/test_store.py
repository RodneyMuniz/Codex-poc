from __future__ import annotations

import json

from sessions import SessionStore


def _prepare_repo(tmp_path):
    (tmp_path / "projects" / "tactics-game" / "execution").mkdir(parents=True)
    (tmp_path / "projects" / "tactics-game" / "governance").mkdir(parents=True)
    (tmp_path / "sessions").mkdir(parents=True)
    (tmp_path / "projects" / "tactics-game" / "governance" / "PROJECT_BRIEF.md").write_text(
        "# Brief\n\nTest project.\n",
        encoding="utf-8",
    )
    (tmp_path / "sessions" / "approvals.json").write_text("", encoding="utf-8")
    return tmp_path


def test_store_persists_tasks_approvals_and_kanban(tmp_path):
    repo_root = _prepare_repo(tmp_path)
    store = SessionStore(repo_root)

    task = store.create_task("tactics-game", "Test Task", "Exercise the queue", requires_approval=True)
    assert task["status"] == "queued"

    run = store.create_run("tactics-game", task["id"])
    approval = store.create_approval(run["id"], task["id"], "ProjectPO", "Need operator confirmation")
    updated_task = store.get_task(task["id"])
    assert updated_task is not None
    assert updated_task["status"] == "awaiting_approval"

    decided = store.decide_approval(approval["id"], "approve", "Looks good")
    assert decided["status"] == "approved"

    state = {"turn": 1, "messages": ["hello"]}
    store.save_team_state(run["id"], state)
    loaded = store.load_team_state(run["id"])
    assert loaded == state

    store.update_task(task["id"], status="completed", owner_role="ProjectPO", result_summary="Done")
    kanban = (repo_root / "projects" / "tactics-game" / "execution" / "KANBAN.md").read_text(encoding="utf-8")
    assert "Test Task" in kanban
    assert "Done" in kanban


def test_store_records_messages_and_usage(tmp_path):
    repo_root = _prepare_repo(tmp_path)
    store = SessionStore(repo_root)
    task = store.create_task("tactics-game", "Telemetry Task", "Verify message logging")
    run = store.create_run("tactics-game", task["id"])

    store.record_message(
        run["id"],
        task["id"],
        "TextMessage",
        {"content": "hello"},
        source="ProjectPO",
        prompt_tokens=11,
        completion_tokens=7,
    )

    usage_db = store.paths.db_path
    import sqlite3

    connection = sqlite3.connect(usage_db)
    try:
        messages = connection.execute("SELECT payload_json FROM messages").fetchall()
        usage = connection.execute("SELECT prompt_tokens, completion_tokens FROM usage_events").fetchall()
    finally:
        connection.close()

    assert json.loads(messages[0][0])["content"] == "hello"
    assert usage[0] == (11, 7)
