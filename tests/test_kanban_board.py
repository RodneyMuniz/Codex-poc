from __future__ import annotations

from kanban.board import KanbanBoard
from sessions import SessionStore


def _prepare_repo(tmp_path):
    (tmp_path / "projects" / "program-kanban" / "execution").mkdir(parents=True)
    (tmp_path / "projects" / "program-kanban" / "governance").mkdir(parents=True)
    (tmp_path / "sessions").mkdir(parents=True)
    (tmp_path / "governance").mkdir(parents=True)
    (tmp_path / "memory").mkdir(parents=True)
    (tmp_path / "memory" / "framework_health.json").write_text("{}\n", encoding="utf-8")
    (tmp_path / "memory" / "session_summaries.json").write_text("[]\n", encoding="utf-8")
    (tmp_path / "projects" / "program-kanban" / "governance" / "PROJECT_BRIEF.md").write_text("# Brief\n", encoding="utf-8")
    return tmp_path


def test_local_kanban_board_tracks_task_state(tmp_path):
    repo_root = _prepare_repo(tmp_path)
    store = SessionStore(repo_root)
    board = KanbanBoard(repo_root, store=store)

    task = board.create_issue(
        project_name="program-kanban",
        title="Board task",
        details="Track board state locally.",
        objective="Track board state locally.",
    )
    assert task["task_state"] == "Idea"

    task = board.move_task(task["id"], "Spec")
    task = board.move_task(task["id"], "Todo")

    fetched = board.fetch_next_task("Todo", project_name="program-kanban")
    assert fetched is not None
    assert fetched["id"] == task["id"]
    assert fetched["task_state"] == "Todo"


def test_local_kanban_board_requires_two_review_votes_before_done(tmp_path):
    repo_root = _prepare_repo(tmp_path)
    store = SessionStore(repo_root)
    board = KanbanBoard(repo_root, store=store)

    task = board.create_issue(
        project_name="program-kanban",
        title="Consensus task",
        details="Require two review approvals.",
        objective="Require two review approvals.",
    )
    task = board.move_task(task["id"], "Spec")
    task = board.move_task(task["id"], "Todo")
    task = board.move_task(task["id"], "In Progress")
    task = board.move_task(task["id"], "Review")

    board.record_review_vote(task["id"], "Architect", True)
    try:
        board.move_task(task["id"], "Done")
    except Exception as exc:
        assert "two agents" in str(exc)
    else:
        raise AssertionError("Expected review-to-done transition to require two approvals.")

    board.record_review_vote(task["id"], "QA", True)
    task = board.move_task(task["id"], "Done")
    assert task["task_state"] == "Done"
