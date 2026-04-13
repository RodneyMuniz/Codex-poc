from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from click.testing import CliRunner

from scripts import cli
from sessions import SessionStore
from workspace_root import AUTHORITATIVE_ROOT_ENV, KNOWN_DUPLICATE_ROOT_ENV, write_workspace_authority_marker


def _prepare_repo(tmp_path: Path) -> Path:
    (tmp_path / "projects" / "program-kanban" / "execution").mkdir(parents=True)
    (tmp_path / "projects" / "tactics-game" / "execution").mkdir(parents=True)
    (tmp_path / "sessions").mkdir(parents=True)
    (tmp_path / "projects" / "program-kanban" / "execution" / "KANBAN.md").write_text(
        "# Program Kanban\n\nSentinel board.\n",
        encoding="utf-8",
    )
    (tmp_path / "projects" / "tactics-game" / "execution" / "KANBAN.md").write_text(
        "# Tactics Game Kanban\n\nSentinel board.\n",
        encoding="utf-8",
    )
    return tmp_path


def test_session_store_ensure_project_registered_is_idempotent_without_kanban_side_effects(tmp_path):
    repo_root = _prepare_repo(tmp_path)
    program_kanban_path = repo_root / "projects" / "program-kanban" / "execution" / "KANBAN.md"
    tactics_kanban_path = repo_root / "projects" / "tactics-game" / "execution" / "KANBAN.md"
    original_program_kanban = program_kanban_path.read_text(encoding="utf-8")
    original_tactics_kanban = tactics_kanban_path.read_text(encoding="utf-8")

    first = SessionStore.ensure_project_registered(repo_root, "aioffice")
    second = SessionStore.ensure_project_registered(repo_root, "aioffice")

    connection = sqlite3.connect(repo_root / "sessions" / "studio.db")
    try:
        rows = connection.execute(
            "SELECT id, name, root_path, created_at FROM projects WHERE name = ?",
            ("aioffice",),
        ).fetchall()
    finally:
        connection.close()

    assert len(rows) == 1
    assert rows[0][1] == "aioffice"
    assert rows[0][2] == str((repo_root / "projects" / "aioffice").resolve())
    assert first["id"] == second["id"] == rows[0][0]
    assert first["created_at"] == second["created_at"] == rows[0][3]
    assert program_kanban_path.read_text(encoding="utf-8") == original_program_kanban
    assert tactics_kanban_path.read_text(encoding="utf-8") == original_tactics_kanban


def test_cli_projects_ensure_registers_project_from_authoritative_root(tmp_path, monkeypatch):
    repo_root = _prepare_repo(tmp_path)
    write_workspace_authority_marker(repo_root, repo_name="test-ai-studio")
    duplicate_root = tmp_path.parent / f"{tmp_path.name}_duplicate"
    duplicate_root.mkdir()

    monkeypatch.setenv(AUTHORITATIVE_ROOT_ENV, str(repo_root))
    monkeypatch.setenv(KNOWN_DUPLICATE_ROOT_ENV, str(duplicate_root))
    monkeypatch.setattr(cli, "ROOT", repo_root)

    runner = CliRunner()
    first_result = runner.invoke(cli.cli, ["projects", "ensure", "aioffice"])
    second_result = runner.invoke(cli.cli, ["projects", "ensure", "aioffice"])

    assert first_result.exit_code == 0
    assert second_result.exit_code == 0

    first_payload = json.loads(first_result.output)
    second_payload = json.loads(second_result.output)

    assert first_payload["name"] == "aioffice"
    assert second_payload["name"] == "aioffice"
    assert first_payload["id"] == second_payload["id"]
    assert first_payload["root_path"] == str((repo_root / "projects" / "aioffice").resolve())


def test_cli_projects_ensure_rejects_missing_authority_marker(tmp_path, monkeypatch):
    _prepare_repo(tmp_path)
    marker_path = tmp_path / ".workspace_authority.json"
    if marker_path.exists():
        marker_path.unlink()

    monkeypatch.setenv(AUTHORITATIVE_ROOT_ENV, str(tmp_path))
    monkeypatch.delenv(KNOWN_DUPLICATE_ROOT_ENV, raising=False)
    monkeypatch.setattr(cli, "ROOT", tmp_path)

    runner = CliRunner()
    result = runner.invoke(cli.cli, ["projects", "ensure", "aioffice"])

    assert result.exit_code != 0
    assert "authoritative workspace root marker required" in result.output
