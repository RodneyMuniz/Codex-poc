from __future__ import annotations

import argparse
import json
import re
import shutil
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from sessions import SessionStore


@dataclass(frozen=True)
class LegacySource:
    project_name: str
    display_name: str
    source_root: Path
    project_file: Path
    kanban_file: Path


DEFAULT_SOURCES = (
    LegacySource(
        project_name="program-kanban",
        display_name="Program Kanban",
        source_root=Path(r"C:\Users\rodne\OneDrive\Documentos\_Codex Projects\Program Kanban"),
        project_file=Path(r"C:\Users\rodne\OneDrive\Documentos\_Codex Projects\Program Kanban\PROJECT.md"),
        kanban_file=Path(r"C:\Users\rodne\OneDrive\Documentos\_Codex Projects\Program Kanban\KANBAN.md"),
    ),
    LegacySource(
        project_name="tactics-game",
        display_name="TacticsGame",
        source_root=Path(r"C:\Users\rodne\OneDrive\Documentos\_Codex Projects\TacticsGame"),
        project_file=Path(r"C:\Users\rodne\OneDrive\Documentos\_Codex Projects\TacticsGame\PROJECT.md"),
        kanban_file=Path(r"C:\Users\rodne\OneDrive\Documentos\_Codex Projects\TacticsGame\KANBAN.md"),
    ),
)

STATUS_TO_COLUMN = {
    "Backlog": "backlog",
    "Ready": "ready",
    "In Progress": "in_progress",
    "Review": "in_review",
    "Blocked": "blocked",
    "Done": "completed",
    "Deferred": "deferred",
}

CATEGORY_MAP = {
    "UI/UX": "UX",
    "UX / Player Experience": "UX",
    "Technical/Architecture": "Architecture",
}

DEMO_ARTIFACTS = (
    "healer.py",
    "healer_design.md",
    "healer_ui_notes.md",
    "healer_run_evidence.json",
    "mage.py",
    "mage_design.md",
    "mage_ui_notes.md",
    "tactics_game_wall_snapshot.json",
    "test_warrior.py",
    "warrior.py",
    "warrior_design.md",
)

FIELD_LINE = re.compile(r"^([A-Za-z0-9 /`'()._-]+):\s*(.*)$")
TASK_BULLET = re.compile(r"^- ([A-Z]+-\d+)\s+(.*)$")


def _slug_label(value: str) -> str:
    return " ".join(part.capitalize() for part in value.split("-"))


def _legacy_to_store_status(value: str) -> str:
    return STATUS_TO_COLUMN.get(value.strip(), "backlog")


def _priority(value: str | None) -> str:
    normalized = (value or "medium").strip().lower()
    if normalized not in {"low", "medium", "high"}:
        return "medium"
    return normalized


def _normalize_category(value: str | None) -> str:
    if not value:
        return "Implementation"
    return CATEGORY_MAP.get(value.strip(), value.strip())


def _extract_section(markdown: str, heading: str) -> str:
    pattern = re.compile(rf"^## {re.escape(heading)}\s*$", re.MULTILINE)
    match = pattern.search(markdown)
    if not match:
        return ""
    start = match.end()
    next_heading = re.search(r"^## ", markdown[start:], re.MULTILINE)
    end = start + next_heading.start() if next_heading else len(markdown)
    return markdown[start:end].strip()


def _compact(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _write_project_brief(repo_root: Path, source: LegacySource, imported_count: int) -> Path:
    markdown = source.project_file.read_text(encoding="utf-8")
    one_liner = _compact(_extract_section(markdown, "One-Sentence Description"))
    status = _compact(_extract_section(markdown, "Status"))
    next_step = _compact(_extract_section(markdown, "Next Step") or _extract_section(markdown, "Smallest Next Implementation Step"))
    runtime_root = repo_root / "projects" / source.project_name
    brief_path = runtime_root / "governance" / "PROJECT_BRIEF.md"
    brief_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        f"# {source.display_name} Project Brief",
        "",
        f"- Imported project slug: `{source.project_name}`",
        f"- Runtime project root: `{runtime_root}`",
        f"- Runtime app root: `{runtime_root / 'app'}`",
        f"- Legacy source root: `{source.source_root}`",
        f"- Legacy project doc: `{source.project_file}`",
        f"- Legacy kanban doc: `{source.kanban_file}`",
        f"- Imported task count: `{imported_count}`",
        "",
        "## One-Sentence Description",
        one_liner or "Imported from the legacy project source.",
        "",
        "## Current Status",
        status or "Imported from legacy markdown. Review the board in the operator wall before dispatching new runtime work.",
        "",
        "## Next Step",
        next_step or "Use the imported board state as the starting point for new framework-managed execution.",
        "",
        "## Operating Notes",
        "- Legacy markdown was used as the source for import provenance.",
        "- The canonical operator-facing board in this repo is now derived from `sessions/studio.db`.",
        "- New runtime work should be dispatched through the framework, not by editing the imported legacy markdown directly.",
        "",
    ]
    brief_path.write_text("\n".join(lines), encoding="utf-8")
    return brief_path


def _parse_column_index(markdown: str) -> tuple[list[str], dict[str, dict[str, Any]]]:
    order: list[str] = []
    tasks: dict[str, dict[str, Any]] = {}
    current_column: str | None = None
    for line in markdown.splitlines():
        if line.strip() == "---":
            break
        if line.startswith("## "):
            heading = line[3:].strip()
            current_column = heading if heading in STATUS_TO_COLUMN else None
            continue
        if current_column and line.startswith("- "):
            match = TASK_BULLET.match(line.strip())
            if not match:
                continue
            legacy_id, title = match.groups()
            if legacy_id not in tasks:
                order.append(legacy_id)
                tasks[legacy_id] = {"column": current_column, "title": title.strip()}
            else:
                tasks[legacy_id]["column"] = current_column
    return order, tasks


def _parse_task_details(markdown: str) -> dict[str, dict[str, str]]:
    details: dict[str, dict[str, str]] = {}
    blocks = markdown.split("\n### ID:")
    for block in blocks[1:]:
        lines = block.splitlines()
        legacy_id = lines[0].strip()
        fields: dict[str, str] = {}
        current_field: str | None = None
        for raw_line in lines[1:]:
            line = raw_line.rstrip()
            if not line.strip():
                continue
            match = FIELD_LINE.match(line.strip())
            if match and not line.strip().startswith("- "):
                current_field = match.group(1).strip()
                fields[current_field] = match.group(2).strip()
                continue
            if current_field:
                extra = line.strip()
                fields[current_field] = f"{fields[current_field]}\n{extra}".strip()
        details[legacy_id] = fields
    return details


def parse_legacy_kanban(source: LegacySource) -> list[dict[str, Any]]:
    markdown = source.kanban_file.read_text(encoding="utf-8")
    order, column_entries = _parse_column_index(markdown)
    detail_entries = _parse_task_details(markdown)
    imported: list[dict[str, Any]] = []
    for index, legacy_id in enumerate(order):
        fields = detail_entries.get(legacy_id, {})
        title = fields.get("Title") or column_entries.get(legacy_id, {}).get("title") or legacy_id
        status = _legacy_to_store_status(fields.get("Status") or column_entries.get(legacy_id, {}).get("column", "Backlog"))
        review_state = fields.get("Review State") or ("Accepted" if status == "completed" else "None")
        objective = fields.get("Objective") or title
        details_parts = [objective]
        if fields.get("Scope In"):
            details_parts.append(f"Scope In:\n{fields['Scope In']}")
        if fields.get("Scope Out"):
            details_parts.append(f"Scope Out:\n{fields['Scope Out']}")
        if fields.get("Acceptance Criteria"):
            details_parts.append(f"Acceptance Criteria:\n{fields['Acceptance Criteria']}")
        details_text = "\n\n".join(part.strip() for part in details_parts if part.strip()) or title
        owner_role = fields.get("Owner") or fields.get("Role/Skill", "Imported Legacy Board").split("/")[0].strip()
        acceptance_criteria = [item[2:].strip() for item in fields.get("Acceptance Criteria", "").splitlines() if item.strip().startswith("- ")]
        created_at = (datetime(2026, 1, 1, tzinfo=UTC) + timedelta(seconds=index)).isoformat(timespec="seconds")
        updated_at = created_at
        completed_at = fields.get("Completed At") or None
        if completed_at:
            updated_at = completed_at
        imported.append(
            {
                "id": legacy_id,
                "project_name": source.project_name,
                "title": title,
                "objective": objective,
                "details": details_text,
                "status": status,
                "priority": _priority(fields.get("Priority")),
                "owner_role": owner_role or "Imported Legacy Board",
                "assigned_role": owner_role or "Imported Legacy Board",
                "layer": fields.get("Layer", "Execution"),
                "category": _normalize_category(fields.get("Category")),
                "review_state": review_state,
                "review_notes": fields.get("Notes / Handoff"),
                "result_summary": fields.get("Notes / Handoff") if status == "completed" else None,
                "expected_artifact_path": None,
                "acceptance": {
                    "legacy_acceptance_criteria": acceptance_criteria,
                    "legacy_depends_on": fields.get("Depends on"),
                    "legacy_estimate": fields.get("Estimate"),
                    "legacy_artifacts_affected": fields.get("Artifacts Affected"),
                },
                "raw_request": json.dumps(
                    {
                        "source_root": str(source.source_root),
                        "source_kanban": str(source.kanban_file),
                        "legacy_fields": fields,
                    },
                    ensure_ascii=True,
                ),
                "created_at": created_at,
                "updated_at": updated_at,
                "completed_at": completed_at,
                "requires_approval": status in {"backlog", "ready"},
            }
        )
    return imported


def _backup_database(repo_root: Path) -> Path:
    backups_dir = repo_root / "sessions" / "backups"
    backups_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    backup_path = backups_dir / f"pre_legacy_import_{timestamp}.db"
    shutil.copy2(repo_root / "sessions" / "studio.db", backup_path)
    return backup_path


def _archive_demo_artifacts(repo_root: Path) -> list[str]:
    artifacts_dir = repo_root / "projects" / "tactics-game" / "artifacts"
    if not artifacts_dir.exists():
        return []
    archived: list[str] = []
    archive_root = repo_root / "sessions" / "backups" / f"runtime_demo_artifacts_{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}"
    archive_root.mkdir(parents=True, exist_ok=True)
    for name in DEMO_ARTIFACTS:
        source_path = artifacts_dir / name
        if source_path.exists():
            shutil.move(str(source_path), archive_root / name)
            archived.append(name)
    pycache_dir = artifacts_dir / "__pycache__"
    if pycache_dir.exists():
        shutil.rmtree(pycache_dir)
    return archived


def import_legacy_sources(repo_root: str | Path, sources: tuple[LegacySource, ...] = DEFAULT_SOURCES) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    store = SessionStore(root)
    backup_path = _backup_database(root)
    archived_artifacts = _archive_demo_artifacts(root)

    summary: dict[str, Any] = {
        "backup_db": str(backup_path),
        "archived_demo_artifacts": archived_artifacts,
        "projects": [],
    }

    for source in sources:
        imported_tasks = parse_legacy_kanban(source)
        runtime_root = root / "projects" / source.project_name
        store.upsert_project(source.project_name, str(runtime_root))
        purged = store.purge_project(source.project_name)
        for task in imported_tasks:
            store.import_task(
                task_id=task["id"],
                project_name=task["project_name"],
                title=task["title"],
                details=task["details"],
                objective=task["objective"],
                status=task["status"],
                requires_approval=task["requires_approval"],
                owner_role=task["owner_role"],
                assigned_role=task["assigned_role"],
                priority=task["priority"],
                layer=task["layer"],
                category=task["category"],
                review_state=task["review_state"],
                review_notes=task["review_notes"],
                result_summary=task["result_summary"],
                expected_artifact_path=task["expected_artifact_path"],
                acceptance=task["acceptance"],
                raw_request=task["raw_request"],
                created_at=task["created_at"],
                updated_at=task["updated_at"],
                completed_at=task["completed_at"],
            )
        store.render_kanban(source.project_name)
        brief_path = _write_project_brief(root, source, len(imported_tasks))
        counts: dict[str, int] = {}
        for item in imported_tasks:
            counts[item["status"]] = counts.get(item["status"], 0) + 1
        summary["projects"].append(
            {
                "project_name": source.project_name,
                "display_name": source.display_name,
                "runtime_root": str(runtime_root),
                "source_root": str(source.source_root),
                "kanban_source": str(source.kanban_file),
                "task_count": len(imported_tasks),
                "status_counts": counts,
                "purged": purged,
                "project_brief": str(brief_path),
                "derived_kanban": str(root / "projects" / source.project_name / "execution" / "KANBAN.md"),
            }
        )

    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Import legacy Program Kanban and TacticsGame progress into the current framework store.")
    parser.add_argument("--repo-root", default=Path.cwd())
    args = parser.parse_args()
    result = import_legacy_sources(args.repo_root)
    print(json.dumps(result, ensure_ascii=True, indent=2))


if __name__ == "__main__":
    main()
