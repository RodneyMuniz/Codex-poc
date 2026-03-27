from __future__ import annotations

from pathlib import Path

from scripts.import_legacy_projects import LegacySource, import_legacy_sources
from sessions import SessionStore


def _prepare_repo(tmp_path: Path) -> Path:
    (tmp_path / "projects" / "tactics-game" / "execution").mkdir(parents=True)
    (tmp_path / "projects" / "tactics-game" / "governance").mkdir(parents=True)
    (tmp_path / "projects" / "tactics-game" / "artifacts").mkdir(parents=True)
    (tmp_path / "sessions").mkdir(parents=True)
    (tmp_path / "governance").mkdir(parents=True)
    (tmp_path / "memory").mkdir(parents=True)
    (tmp_path / "memory" / "framework_health.json").write_text("{}\n", encoding="utf-8")
    (tmp_path / "memory" / "session_summaries.json").write_text("[]\n", encoding="utf-8")
    return tmp_path


def _legacy_source(root: Path, slug: str, display_name: str, task_id: str, title: str) -> LegacySource:
    source_root = root / slug
    source_root.mkdir(parents=True)
    (source_root / "PROJECT.md").write_text(
        f"# PROJECT\n\n## Project\n{display_name}\n\n## One-Sentence Description\nA migrated legacy project.\n\n## Status\nThe project is active.\n\n## Next Step\nContinue using the imported framework board.\n",
        encoding="utf-8",
    )
    (source_root / "KANBAN.md").write_text(
        "\n".join(
            [
                "# KANBAN",
                "",
                "## Backlog",
                f"- {task_id} {title}",
                "",
                "## Ready",
                "- None.",
                "",
                "## In Progress",
                "- None.",
                "",
                "## Review",
                "- None.",
                "",
                "## Blocked",
                "- None.",
                "",
                "## Done",
                "- None.",
                "",
                "## Deferred",
                "- None.",
                "",
                "---",
                "",
                "## Task Details",
                "",
                f"### ID: {task_id}",
                f"Title: {title}",
                "Layer: Execution",
                "Category: Implementation",
                "Owner: Legacy Planner",
                "Priority: High",
                "Status: Backlog",
                "Review State: None",
                "Objective: Carry this legacy work into the new framework.",
                "Scope In: first migrated scope",
                "Acceptance Criteria:",
                "- board entry survives import",
                "- project brief is generated",
                "Notes / Handoff: Imported from the legacy markdown board.",
            ]
        ),
        encoding="utf-8",
    )
    return LegacySource(
        project_name=slug,
        display_name=display_name,
        source_root=source_root,
        project_file=source_root / "PROJECT.md",
        kanban_file=source_root / "KANBAN.md",
    )


def test_import_legacy_sources_replaces_mock_data_and_generates_project_views(tmp_path):
    repo_root = _prepare_repo(tmp_path)
    store = SessionStore(repo_root)
    mock_task = store.create_task("tactics-game", "Mock task", "Temporary runtime data")
    store.create_run("tactics-game", mock_task["id"])
    demo_artifact = repo_root / "projects" / "tactics-game" / "artifacts" / "healer.py"
    demo_artifact.write_text("print('demo')\n", encoding="utf-8")

    legacy_root = tmp_path / "legacy"
    sources = (
        _legacy_source(legacy_root, "program-kanban", "Program Kanban", "TGD-001", "Imported wall task"),
        _legacy_source(legacy_root, "tactics-game", "TacticsGame", "TG-001", "Imported gameplay task"),
    )

    result = import_legacy_sources(repo_root, sources)

    tactics_tasks = store.list_tasks("tactics-game")
    program_tasks = store.list_tasks("program-kanban")

    assert [task["id"] for task in tactics_tasks] == ["TG-001"]
    assert [task["id"] for task in program_tasks] == ["TGD-001"]
    assert store.list_runs("tactics-game") == []
    assert result["archived_demo_artifacts"] == ["healer.py"]
    assert (repo_root / "projects" / "tactics-game" / "governance" / "PROJECT_BRIEF.md").exists()
    assert (repo_root / "projects" / "program-kanban" / "governance" / "PROJECT_BRIEF.md").exists()
    assert (repo_root / "projects" / "tactics-game" / "execution" / "KANBAN.md").exists()
    assert (repo_root / "projects" / "program-kanban" / "execution" / "KANBAN.md").exists()
    assert len(store.list_projects()) == 2
