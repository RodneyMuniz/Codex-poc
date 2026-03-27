from __future__ import annotations

import hashlib
import json
import re
import shutil
import sqlite3
import uuid
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Iterator


PROJECT_NAME = "tactics-game"
TASK_STATUSES = ("backlog", "ready", "in_progress", "in_review", "completed", "blocked")
PRIMARY_BOARD_COLUMNS = (
    ("backlog", "Backlog"),
    ("ready", "Ready for Build"),
    ("in_progress", "In Progress"),
    ("in_review", "In Review"),
    ("completed", "Complete"),
)
REQUIRED_TABLES = (
    "projects",
    "milestones",
    "tasks",
    "runs",
    "agent_runs",
    "approvals",
    "delegation_edges",
    "messages",
    "trace_events",
    "validation_results",
    "usage_events",
    "artifacts",
)


def _utc_now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def _new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


def _json_dumps(value: Any) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True, default=str)


def _json_loads(value: str | None, default: Any) -> Any:
    if not value:
        return default
    return json.loads(value)


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "milestone"


def _sha256_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


@dataclass(frozen=True)
class StorePaths:
    repo_root: Path
    db_path: Path
    kanban_path: Path
    memory_dir: Path
    backups_dir: Path
    restore_receipts_dir: Path
    health_path: Path
    summary_path: Path
    legacy_approvals_path: Path


class SessionStore:
    def __init__(self, repo_root: str | Path | None = None, db_path: str | Path | None = None) -> None:
        root = Path(repo_root or Path.cwd()).resolve()
        database_path = Path(db_path) if db_path else root / "sessions" / "studio.db"
        memory_dir = root / "memory"
        backups_dir = root / "sessions" / "backups"
        self.paths = StorePaths(
            repo_root=root,
            db_path=database_path.resolve(),
            kanban_path=root / "projects" / PROJECT_NAME / "execution" / "KANBAN.md",
            memory_dir=memory_dir,
            backups_dir=backups_dir,
            restore_receipts_dir=backups_dir / "receipts",
            health_path=memory_dir / "framework_health.json",
            summary_path=memory_dir / "session_summaries.json",
            legacy_approvals_path=root / "sessions" / "approvals.json",
        )
        self.paths.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.paths.memory_dir.mkdir(parents=True, exist_ok=True)
        self.paths.backups_dir.mkdir(parents=True, exist_ok=True)
        self.paths.restore_receipts_dir.mkdir(parents=True, exist_ok=True)
        self.ensure_memory_files()
        self.initialize()

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self.paths.db_path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        try:
            yield connection
            connection.commit()
        finally:
            connection.close()

    def ensure_memory_files(self) -> None:
        if not self.paths.health_path.exists():
            self.paths.health_path.write_text("{}\n", encoding="utf-8")
        if not self.paths.summary_path.exists():
            self.paths.summary_path.write_text("[]\n", encoding="utf-8")

    def initialize(self) -> None:
        with self._connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS projects (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL UNIQUE,
                    root_path TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS milestones (
                    id TEXT PRIMARY KEY,
                    project_name TEXT NOT NULL,
                    slug TEXT NOT NULL,
                    title TEXT NOT NULL,
                    entry_goal TEXT NOT NULL,
                    exit_goal TEXT NOT NULL,
                    status TEXT NOT NULL,
                    milestone_order INTEGER NOT NULL DEFAULT 0,
                    owner_role TEXT NOT NULL DEFAULT 'Project Orchestrator',
                    details TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY(project_name) REFERENCES projects(name),
                    UNIQUE(project_name, slug),
                    UNIQUE(project_name, title)
                );

                CREATE TABLE IF NOT EXISTS tasks (
                    id TEXT PRIMARY KEY,
                    project_name TEXT NOT NULL,
                    parent_task_id TEXT,
                    task_kind TEXT NOT NULL DEFAULT 'request',
                    title TEXT NOT NULL,
                    objective TEXT,
                    details TEXT,
                    description TEXT NOT NULL,
                    status TEXT NOT NULL,
                    priority TEXT NOT NULL DEFAULT 'medium',
                    requires_approval INTEGER NOT NULL DEFAULT 0,
                    owner_role TEXT NOT NULL,
                    expected_artifact_path TEXT,
                    acceptance_json TEXT,
                    raw_request TEXT,
                    result_summary TEXT,
                    review_notes TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    layer TEXT NOT NULL DEFAULT 'Execution',
                    category TEXT NOT NULL DEFAULT 'Implementation',
                    review_state TEXT NOT NULL DEFAULT 'None',
                    completed_at TEXT,
                    assigned_role TEXT,
                    milestone_id TEXT,
                    FOREIGN KEY(project_name) REFERENCES projects(name),
                    FOREIGN KEY(parent_task_id) REFERENCES tasks(id),
                    FOREIGN KEY(milestone_id) REFERENCES milestones(id)
                );

                CREATE TABLE IF NOT EXISTS runs (
                    id TEXT PRIMARY KEY,
                    project_name TEXT NOT NULL,
                    task_id TEXT NOT NULL,
                    status TEXT NOT NULL,
                    stop_reason TEXT,
                    last_error TEXT,
                    team_state_json TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    started_at TEXT,
                    completed_at TEXT,
                    FOREIGN KEY(project_name) REFERENCES projects(name),
                    FOREIGN KEY(task_id) REFERENCES tasks(id)
                );

                CREATE TABLE IF NOT EXISTS agent_runs (
                    id TEXT PRIMARY KEY,
                    run_id TEXT NOT NULL,
                    task_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    status TEXT NOT NULL,
                    pid INTEGER,
                    input_artifact_path TEXT,
                    input_artifact_sha256 TEXT,
                    output_artifact_path TEXT,
                    output_artifact_sha256 TEXT,
                    notes TEXT,
                    started_at TEXT NOT NULL,
                    completed_at TEXT,
                    error TEXT,
                    FOREIGN KEY(run_id) REFERENCES runs(id),
                    FOREIGN KEY(task_id) REFERENCES tasks(id)
                );

                CREATE TABLE IF NOT EXISTS approvals (
                    id TEXT PRIMARY KEY,
                    run_id TEXT NOT NULL,
                    task_id TEXT NOT NULL,
                    requested_by TEXT NOT NULL,
                    reason TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    decided_at TEXT,
                    decision_note TEXT,
                    approval_scope TEXT NOT NULL DEFAULT 'program',
                    target_role TEXT,
                    exact_task TEXT,
                    expected_output TEXT,
                    why_now TEXT,
                    risks_json TEXT,
                    FOREIGN KEY(run_id) REFERENCES runs(id),
                    FOREIGN KEY(task_id) REFERENCES tasks(id)
                );

                CREATE TABLE IF NOT EXISTS delegation_edges (
                    id TEXT PRIMARY KEY,
                    run_id TEXT NOT NULL,
                    task_id TEXT NOT NULL,
                    from_role TEXT NOT NULL,
                    to_role TEXT NOT NULL,
                    note TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(run_id) REFERENCES runs(id),
                    FOREIGN KEY(task_id) REFERENCES tasks(id)
                );

                CREATE TABLE IF NOT EXISTS messages (
                    id TEXT PRIMARY KEY,
                    run_id TEXT NOT NULL,
                    task_id TEXT NOT NULL,
                    source TEXT,
                    event_type TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    prompt_tokens INTEGER,
                    completion_tokens INTEGER,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(run_id) REFERENCES runs(id),
                    FOREIGN KEY(task_id) REFERENCES tasks(id)
                );

                CREATE TABLE IF NOT EXISTS trace_events (
                    id TEXT PRIMARY KEY,
                    run_id TEXT NOT NULL,
                    task_id TEXT NOT NULL,
                    source TEXT,
                    event_type TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(run_id) REFERENCES runs(id),
                    FOREIGN KEY(task_id) REFERENCES tasks(id)
                );

                CREATE TABLE IF NOT EXISTS validation_results (
                    id TEXT PRIMARY KEY,
                    run_id TEXT NOT NULL,
                    task_id TEXT NOT NULL,
                    agent_run_id TEXT,
                    validator_role TEXT NOT NULL,
                    artifact_path TEXT NOT NULL,
                    artifact_sha256 TEXT,
                    status TEXT NOT NULL,
                    checks_json TEXT NOT NULL,
                    summary TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(run_id) REFERENCES runs(id),
                    FOREIGN KEY(task_id) REFERENCES tasks(id),
                    FOREIGN KEY(agent_run_id) REFERENCES agent_runs(id)
                );

                CREATE TABLE IF NOT EXISTS usage_events (
                    id TEXT PRIMARY KEY,
                    run_id TEXT NOT NULL,
                    task_id TEXT NOT NULL,
                    source TEXT,
                    prompt_tokens INTEGER NOT NULL,
                    completion_tokens INTEGER NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(run_id) REFERENCES runs(id),
                    FOREIGN KEY(task_id) REFERENCES tasks(id)
                );

                CREATE TABLE IF NOT EXISTS artifacts (
                    id TEXT PRIMARY KEY,
                    run_id TEXT NOT NULL,
                    task_id TEXT NOT NULL,
                    kind TEXT NOT NULL,
                    content TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    artifact_path TEXT,
                    artifact_sha256 TEXT,
                    bytes_written INTEGER,
                    produced_by TEXT,
                    source_agent_run_id TEXT,
                    input_artifact_paths_json TEXT,
                    FOREIGN KEY(run_id) REFERENCES runs(id),
                    FOREIGN KEY(task_id) REFERENCES tasks(id),
                    FOREIGN KEY(source_agent_run_id) REFERENCES agent_runs(id)
                );
                """
            )
        self._ensure_project(PROJECT_NAME)
        self._ensure_task_columns()
        self._ensure_milestone_columns()
        self._ensure_approval_columns()
        self._ensure_artifact_columns()
        self.migrate_legacy_approvals_file()
        self.normalize_legacy_statuses()
        self.render_kanban(PROJECT_NAME)

    def _ensure_task_columns(self) -> None:
        task_columns = {
            "parent_task_id": "TEXT",
            "task_kind": "TEXT NOT NULL DEFAULT 'request'",
            "objective": "TEXT",
            "details": "TEXT",
            "priority": "TEXT NOT NULL DEFAULT 'medium'",
            "expected_artifact_path": "TEXT",
            "acceptance_json": "TEXT",
            "raw_request": "TEXT",
            "review_notes": "TEXT",
            "layer": "TEXT NOT NULL DEFAULT 'Execution'",
            "category": "TEXT NOT NULL DEFAULT 'Implementation'",
            "review_state": "TEXT NOT NULL DEFAULT 'None'",
            "completed_at": "TEXT",
            "assigned_role": "TEXT",
            "milestone_id": "TEXT",
        }
        with self._connect() as connection:
            existing = {row["name"] for row in connection.execute("PRAGMA table_info(tasks)").fetchall()}
            for column_name, definition in task_columns.items():
                if column_name not in existing:
                    connection.execute(f"ALTER TABLE tasks ADD COLUMN {column_name} {definition}")

    def _ensure_milestone_columns(self) -> None:
        milestone_columns = {
            "slug": "TEXT NOT NULL DEFAULT 'milestone'",
            "title": "TEXT NOT NULL DEFAULT ''",
            "entry_goal": "TEXT NOT NULL DEFAULT ''",
            "exit_goal": "TEXT NOT NULL DEFAULT ''",
            "status": "TEXT NOT NULL DEFAULT 'planned'",
            "milestone_order": "INTEGER NOT NULL DEFAULT 0",
            "owner_role": "TEXT NOT NULL DEFAULT 'Project Orchestrator'",
            "details": "TEXT",
            "updated_at": "TEXT NOT NULL DEFAULT ''",
        }
        with self._connect() as connection:
            existing = {row["name"] for row in connection.execute("PRAGMA table_info(milestones)").fetchall()}
            for column_name, definition in milestone_columns.items():
                if column_name not in existing:
                    connection.execute(f"ALTER TABLE milestones ADD COLUMN {column_name} {definition}")

    def _ensure_approval_columns(self) -> None:
        approval_columns = {
            "approval_scope": "TEXT NOT NULL DEFAULT 'program'",
            "target_role": "TEXT",
            "exact_task": "TEXT",
            "expected_output": "TEXT",
            "why_now": "TEXT",
            "risks_json": "TEXT",
        }
        with self._connect() as connection:
            existing = {row["name"] for row in connection.execute("PRAGMA table_info(approvals)").fetchall()}
            for column_name, definition in approval_columns.items():
                if column_name not in existing:
                    connection.execute(f"ALTER TABLE approvals ADD COLUMN {column_name} {definition}")

    def _ensure_artifact_columns(self) -> None:
        artifact_columns = {
            "artifact_path": "TEXT",
            "artifact_sha256": "TEXT",
            "bytes_written": "INTEGER",
            "produced_by": "TEXT",
            "source_agent_run_id": "TEXT",
            "input_artifact_paths_json": "TEXT",
        }
        with self._connect() as connection:
            existing = {row["name"] for row in connection.execute("PRAGMA table_info(artifacts)").fetchall()}
            for column_name, definition in artifact_columns.items():
                if column_name not in existing:
                    connection.execute(f"ALTER TABLE artifacts ADD COLUMN {column_name} {definition}")

    def normalize_legacy_statuses(self) -> None:
        mappings = {
            "queued": "backlog",
            "delegated": "in_progress",
            "in_progress": "in_progress",
            "awaiting_approval": "ready",
            "approved": "ready",
            "completed": "completed",
            "failed": "blocked",
            "rejected": "blocked",
            "cancelled": "blocked",
        }
        with self._connect() as connection:
            rows = connection.execute("SELECT id, status, owner_role, assigned_role FROM tasks").fetchall()
            for row in rows:
                new_status = mappings.get(row["status"], row["status"])
                owner_role = "PM" if row["owner_role"] == "ProjectPO" else row["owner_role"]
                assigned_role = row["assigned_role"] or owner_role
                connection.execute(
                    "UPDATE tasks SET status = ?, owner_role = ?, assigned_role = ? WHERE id = ?",
                    (new_status, owner_role, assigned_role, row["id"]),
                )

    def migrate_legacy_approvals_file(self) -> None:
        path = self.paths.legacy_approvals_path
        if not path.exists():
            return
        content = path.read_text(encoding="utf-8").strip()
        if not content:
            path.unlink()
            return
        try:
            payload = json.loads(content)
        except json.JSONDecodeError:
            path.rename(path.with_suffix(".legacy.invalid"))
            return
        if isinstance(payload, list):
            with self._connect() as connection:
                for item in payload:
                    if not isinstance(item, dict):
                        continue
                    connection.execute(
                        """
                        INSERT OR IGNORE INTO approvals (
                            id, run_id, task_id, requested_by, reason, status, created_at, decided_at, decision_note
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            item.get("id") or _new_id("approval"),
                            item.get("run_id", "legacy_run"),
                            item.get("task_id", "legacy_task"),
                            item.get("requested_by", "legacy"),
                            item.get("reason", "Migrated from legacy approvals.json"),
                            item.get("status", "pending"),
                            item.get("created_at", _utc_now()),
                            item.get("decided_at"),
                            item.get("decision_note"),
                        ),
                    )
        path.rename(path.with_suffix(".legacy.migrated"))

    def list_tables(self) -> list[str]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table' ORDER BY name"
            ).fetchall()
        return [row["name"] for row in rows]

    def schema_health(self) -> dict[str, Any]:
        tables = self.list_tables()
        issues = [table for table in REQUIRED_TABLES if table not in tables]
        return {"ok": not issues, "tables": tables, "issues": issues}

    def _ensure_project(self, project_name: str) -> dict[str, Any]:
        root_path = self.paths.repo_root / "projects" / project_name
        root_path.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.execute(
                """
                INSERT OR IGNORE INTO projects (id, name, root_path, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (_new_id("project"), project_name, str(root_path), _utc_now()),
            )
        return self.get_project(project_name) or {"name": project_name, "root_path": str(root_path)}

    def get_project(self, project_name: str) -> dict[str, Any] | None:
        with self._connect() as connection:
            row = connection.execute("SELECT * FROM projects WHERE name = ?", (project_name,)).fetchone()
        return dict(row) if row else None

    def upsert_project(self, project_name: str, root_path: str | None = None) -> dict[str, Any]:
        now = _utc_now()
        resolved_root = root_path or str(self.paths.repo_root / "projects" / project_name)
        with self._connect() as connection:
            existing = connection.execute("SELECT id, created_at FROM projects WHERE name = ?", (project_name,)).fetchone()
            if existing:
                connection.execute(
                    "UPDATE projects SET root_path = ? WHERE name = ?",
                    (resolved_root, project_name),
                )
                project_id = existing["id"]
                created_at = existing["created_at"]
            else:
                project_id = _new_id("project")
                created_at = now
                connection.execute(
                    "INSERT INTO projects (id, name, root_path, created_at) VALUES (?, ?, ?, ?)",
                    (project_id, project_name, resolved_root, created_at),
                )
        project = self.get_project(project_name)
        if project is None:
            return {"id": project_id, "name": project_name, "root_path": resolved_root, "created_at": created_at}
        return project

    def list_projects(self) -> list[dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute("SELECT * FROM projects ORDER BY created_at ASC").fetchall()
        return [dict(row) for row in rows]

    def purge_project(self, project_name: str) -> dict[str, int]:
        counts: dict[str, int] = {}
        task_ids = [task["id"] for task in self.list_tasks(project_name)]
        run_ids = [run["id"] for run in self.list_runs(project_name)]
        task_scoped_tables = (
            "validation_results",
            "artifacts",
            "trace_events",
            "messages",
            "delegation_edges",
            "approvals",
            "usage_events",
        )
        with self._connect() as connection:
            if task_ids:
                task_placeholders = ",".join("?" for _ in task_ids)
                task_params = tuple(task_ids)
                for table in task_scoped_tables:
                    row = connection.execute(
                        f"SELECT COUNT(*) AS count FROM {table} WHERE task_id IN ({task_placeholders})",
                        task_params,
                    ).fetchone()
                    counts[table] = int(row["count"]) if row else 0
                    connection.execute(
                        f"DELETE FROM {table} WHERE task_id IN ({task_placeholders})",
                        task_params,
                    )
                row = connection.execute(
                    f"SELECT COUNT(*) AS count FROM agent_runs WHERE task_id IN ({task_placeholders})",
                    task_params,
                ).fetchone()
                counts["agent_runs"] = int(row["count"]) if row else 0
                connection.execute(
                    f"DELETE FROM agent_runs WHERE task_id IN ({task_placeholders})",
                    task_params,
                )
            else:
                counts["agent_runs"] = 0
            if run_ids:
                run_placeholders = ",".join("?" for _ in run_ids)
                run_params = tuple(run_ids)
                row = connection.execute(
                    f"SELECT COUNT(*) AS count FROM runs WHERE id IN ({run_placeholders})",
                    run_params,
                ).fetchone()
                counts["runs"] = int(row["count"]) if row else 0
                connection.execute(
                    f"DELETE FROM runs WHERE id IN ({run_placeholders})",
                    run_params,
                )
            else:
                counts["runs"] = 0
            if task_ids:
                row = connection.execute(
                    f"SELECT COUNT(*) AS count FROM tasks WHERE id IN ({task_placeholders})",
                    task_params,
                ).fetchone()
                counts["tasks"] = int(row["count"]) if row else 0
                connection.execute(
                    f"DELETE FROM tasks WHERE id IN ({task_placeholders})",
                    task_params,
                )
                row = connection.execute(
                    "SELECT COUNT(*) AS count FROM milestones WHERE project_name = ?",
                    (project_name,),
                ).fetchone()
                counts["milestones"] = int(row["count"]) if row else 0
                connection.execute("DELETE FROM milestones WHERE project_name = ?", (project_name,))
            else:
                counts["tasks"] = 0
                counts["milestones"] = 0
        self.render_kanban(project_name)
        return counts

    def board_columns(self) -> list[tuple[str, str]]:
        return list(PRIMARY_BOARD_COLUMNS)

    def task_board_column_key(self, task: dict[str, Any]) -> str:
        status = str(task.get("status") or "backlog")
        if status in {"blocked", "deferred"}:
            return "backlog"
        if status in {key for key, _ in PRIMARY_BOARD_COLUMNS}:
            return status
        return "backlog"

    def _task_acceptance(self, task: dict[str, Any]) -> dict[str, Any]:
        acceptance = task.get("acceptance")
        return acceptance if isinstance(acceptance, dict) else {}

    def _milestone_payload(
        self,
        project_name: str,
        title: str,
        *,
        entry_goal: str | None = None,
        exit_goal: str | None = None,
        status: str = "planned",
        milestone_order: int | None = None,
        owner_role: str = "Project Orchestrator",
        details: str | None = None,
        slug: str | None = None,
    ) -> dict[str, Any]:
        milestone = self.get_milestone_by_title(project_name, title)
        if milestone:
            return milestone
        if milestone_order is None:
            with self._connect() as connection:
                row = connection.execute(
                    "SELECT COALESCE(MAX(milestone_order), 0) AS next_order FROM milestones WHERE project_name = ?",
                    (project_name,),
                ).fetchone()
            milestone_order = int(row["next_order"]) + 1 if row else 1
        milestone_id = _new_id("milestone")
        now = _utc_now()
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO milestones (
                    id, project_name, slug, title, entry_goal, exit_goal, status, milestone_order, owner_role, details,
                    created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    milestone_id,
                    project_name,
                    slug or _slugify(title),
                    title,
                    entry_goal or title,
                    exit_goal or title,
                    status,
                    milestone_order,
                    owner_role,
                    details,
                    now,
                    now,
                ),
            )
        return self.get_milestone(milestone_id) or {
            "id": milestone_id,
            "project_name": project_name,
            "title": title,
        }

    def create_milestone(
        self,
        project_name: str,
        title: str,
        entry_goal: str,
        exit_goal: str,
        *,
        status: str = "planned",
        milestone_order: int | None = None,
        owner_role: str = "Project Orchestrator",
        details: str | None = None,
        slug: str | None = None,
    ) -> dict[str, Any]:
        self._ensure_project(project_name)
        return self._milestone_payload(
            project_name,
            title,
            entry_goal=entry_goal,
            exit_goal=exit_goal,
            status=status,
            milestone_order=milestone_order,
            owner_role=owner_role,
            details=details,
            slug=slug,
        )

    def get_milestone(self, milestone_id: str) -> dict[str, Any] | None:
        with self._connect() as connection:
            row = connection.execute("SELECT * FROM milestones WHERE id = ?", (milestone_id,)).fetchone()
        return dict(row) if row else None

    def get_milestone_by_title(self, project_name: str, title: str) -> dict[str, Any] | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM milestones WHERE project_name = ? AND title = ?",
                (project_name, title),
            ).fetchone()
        return dict(row) if row else None

    def list_milestones(self, project_name: str | None = None) -> list[dict[str, Any]]:
        query = "SELECT * FROM milestones WHERE 1 = 1"
        params: list[Any] = []
        if project_name:
            query += " AND project_name = ?"
            params.append(project_name)
        query += " ORDER BY milestone_order ASC, created_at ASC"
        with self._connect() as connection:
            rows = connection.execute(query, tuple(params)).fetchall()
        return [dict(row) for row in rows]

    def _resolve_milestone_id(
        self,
        project_name: str,
        acceptance: dict[str, Any] | None,
        *,
        title: str,
        details: str,
        owner_role: str,
    ) -> str | None:
        if not acceptance:
            return None
        proposed = acceptance.get("proposed_milestone")
        if not proposed:
            return None
        milestone = self._milestone_payload(
            project_name,
            proposed,
            entry_goal=acceptance.get("entry_goal") or details or title,
            exit_goal=acceptance.get("exit_goal") or details or title,
            status=acceptance.get("milestone_status", "planned"),
            owner_role=acceptance.get("milestone_owner_role") or owner_role,
            details=acceptance.get("milestone_details") or details,
            slug=acceptance.get("milestone_slug"),
        )
        return milestone["id"]

    def _task_gate_issues(self, task: dict[str, Any], *, target_status: str) -> list[str]:
        if task.get("project_name") != "program-kanban":
            return []
        issues: list[str] = []
        acceptance = self._task_acceptance(task)
        if target_status in {"ready", "completed"} and not task.get("milestone_id"):
            issues.append("Missing milestone assignment.")
        if target_status in {"ready", "completed"} and not acceptance:
            issues.append("Missing acceptance criteria.")
        if target_status in {"ready", "completed"} and not task.get("expected_artifact_path"):
            issues.append("Missing expected artifact or output.")
        if target_status in {"ready", "completed"} and not (task.get("assigned_role") or task.get("owner_role")):
            issues.append("Missing responsible owner assignment.")
        if target_status == "completed" and task.get("review_state") != "Accepted":
            issues.append("Complete requires review_state 'Accepted'.")
        return issues

    def task_gate_issues(self, task: dict[str, Any], *, target_status: str | None = None) -> list[str]:
        return self._task_gate_issues(task, target_status=target_status or str(task.get("status") or "backlog"))

    def create_task(
        self,
        project_name: str,
        title: str,
        details: str,
        *,
        objective: str | None = None,
        status: str = "backlog",
        requires_approval: bool = False,
        owner_role: str = "Orchestrator",
        task_kind: str = "request",
        parent_task_id: str | None = None,
        priority: str = "medium",
        expected_artifact_path: str | None = None,
        acceptance: dict[str, Any] | None = None,
        raw_request: str | None = None,
        assigned_role: str | None = None,
        review_state: str = "None",
        milestone_id: str | None = None,
        layer: str = "Execution",
        category: str = "Implementation",
        completed_at: str | None = None,
    ) -> dict[str, Any]:
        if status not in TASK_STATUSES:
            raise ValueError(f"Invalid task status: {status}")
        self._ensure_project(project_name)
        resolved_milestone_id = milestone_id or self._resolve_milestone_id(
            project_name,
            acceptance,
            title=title,
            details=details,
            owner_role=owner_role,
        )
        task_id = _new_id("task")
        now = _utc_now()
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO tasks (
                    id, project_name, parent_task_id, task_kind, title, objective, details, description, status,
                    priority, requires_approval, owner_role, expected_artifact_path, acceptance_json, raw_request,
                    result_summary, review_notes, created_at, updated_at, layer, category, review_state,
                    completed_at, assigned_role, milestone_id
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    task_id,
                    project_name,
                    parent_task_id,
                    task_kind,
                    title,
                    objective or title,
                    details,
                    details,
                    status,
                    priority,
                    int(requires_approval),
                    owner_role,
                    expected_artifact_path,
                    _json_dumps(acceptance or {}),
                    raw_request,
                    None,
                    None,
                    now,
                    now,
                    layer,
                    category,
                    review_state,
                    completed_at,
                    assigned_role or owner_role,
                    resolved_milestone_id,
                ),
            )
        task = self.get_task(task_id)
        if task is None:
            raise ValueError(f"Failed to create task: {task_id}")
        if status in {"ready", "completed"}:
            issues = self.task_gate_issues(task, target_status=status)
            if issues:
                raise ValueError("; ".join(issues))
        self.render_kanban(project_name)
        return task

    def import_task(
        self,
        *,
        task_id: str,
        project_name: str,
        title: str,
        details: str,
        objective: str | None = None,
        status: str = "backlog",
        requires_approval: bool = False,
        owner_role: str = "Orchestrator",
        task_kind: str = "request",
        parent_task_id: str | None = None,
        priority: str = "medium",
        expected_artifact_path: str | None = None,
        acceptance: dict[str, Any] | None = None,
        raw_request: str | None = None,
        assigned_role: str | None = None,
        review_state: str = "None",
        milestone_id: str | None = None,
        layer: str = "Execution",
        category: str = "Implementation",
        result_summary: str | None = None,
        review_notes: str | None = None,
        created_at: str | None = None,
        updated_at: str | None = None,
        completed_at: str | None = None,
    ) -> dict[str, Any]:
        if status not in TASK_STATUSES:
            raise ValueError(f"Invalid task status: {status}")
        self._ensure_project(project_name)
        resolved_milestone_id = milestone_id or self._resolve_milestone_id(
            project_name,
            acceptance,
            title=title,
            details=details,
            owner_role=owner_role,
        )
        created_at_value = created_at or _utc_now()
        updated_at_value = updated_at or created_at_value
        with self._connect() as connection:
            connection.execute(
                """
                INSERT OR REPLACE INTO tasks (
                    id, project_name, parent_task_id, task_kind, title, objective, details, description, status,
                    priority, requires_approval, owner_role, expected_artifact_path, acceptance_json, raw_request,
                    result_summary, review_notes, created_at, updated_at, layer, category, review_state,
                    completed_at, assigned_role, milestone_id
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    task_id,
                    project_name,
                    parent_task_id,
                    task_kind,
                    title,
                    objective or title,
                    details,
                    details,
                    status,
                    priority,
                    int(requires_approval),
                    owner_role,
                    expected_artifact_path,
                    _json_dumps(acceptance or {}),
                    raw_request,
                    result_summary,
                    review_notes,
                    created_at_value,
                    updated_at_value,
                    layer,
                    category,
                    review_state,
                    completed_at,
                    assigned_role or owner_role,
                    resolved_milestone_id,
                ),
            )
        imported = self.get_task(task_id)
        if imported is None:
            raise ValueError(f"Failed to import task: {task_id}")
        self.render_kanban(project_name)
        return imported

    def create_subtask(
        self,
        project_name: str,
        parent_task_id: str,
        title: str,
        details: str,
        *,
        objective: str,
        owner_role: str,
        priority: str,
        expected_artifact_path: str,
        acceptance: dict[str, Any],
    ) -> dict[str, Any]:
        return self.create_task(
            project_name,
            title,
            details,
            objective=objective,
            status="backlog",
            requires_approval=False,
            owner_role=owner_role,
            task_kind="subtask",
            parent_task_id=parent_task_id,
            priority=priority,
            expected_artifact_path=expected_artifact_path,
            acceptance=acceptance,
            assigned_role=owner_role,
        )

    def get_task(self, task_id: str) -> dict[str, Any] | None:
        with self._connect() as connection:
            row = connection.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
        return self._deserialize_task(row) if row else None

    def list_tasks(
        self,
        project_name: str | None = None,
        *,
        status: str | None = None,
        task_kind: str | None = None,
        parent_task_id: str | None = None,
    ) -> list[dict[str, Any]]:
        query = "SELECT * FROM tasks WHERE 1 = 1"
        params: list[Any] = []
        if project_name:
            query += " AND project_name = ?"
            params.append(project_name)
        if status:
            query += " AND status = ?"
            params.append(status)
        if task_kind:
            query += " AND task_kind = ?"
            params.append(task_kind)
        if parent_task_id is not None:
            if parent_task_id == "":
                query += " AND parent_task_id IS NULL"
            else:
                query += " AND parent_task_id = ?"
                params.append(parent_task_id)
        query += " ORDER BY created_at ASC"
        with self._connect() as connection:
            rows = connection.execute(query, tuple(params)).fetchall()
        return [self._deserialize_task(row) for row in rows]

    def get_subtasks(self, parent_task_id: str) -> list[dict[str, Any]]:
        return self.list_tasks(task_kind="subtask", parent_task_id=parent_task_id)

    def get_next_runnable_task(self, project_name: str) -> dict[str, Any] | None:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT * FROM tasks
                WHERE project_name = ?
                  AND task_kind = 'request'
                  AND parent_task_id IS NULL
                  AND status IN ('backlog', 'ready')
                ORDER BY created_at ASC
                LIMIT 1
                """,
                (project_name,),
            ).fetchone()
        return self._deserialize_task(row) if row else None

    def update_task(
        self,
        task_id: str,
        *,
        status: str | None = None,
        owner_role: str | None = None,
        result_summary: str | None = None,
        review_notes: str | None = None,
        expected_artifact_path: str | None = None,
        acceptance: dict[str, Any] | None = None,
        assigned_role: str | None = None,
        review_state: str | None = None,
        milestone_id: str | None = None,
        layer: str | None = None,
        category: str | None = None,
        completed_at: str | None = None,
    ) -> dict[str, Any]:
        task = self.get_task(task_id)
        if task is None:
            raise ValueError(f"Task not found: {task_id}")
        if status is not None:
            if status not in TASK_STATUSES:
                raise ValueError(f"Invalid task status: {status}")
            task["status"] = status
        if owner_role is not None:
            task["owner_role"] = owner_role
        if result_summary is not None:
            task["result_summary"] = result_summary
        if review_notes is not None:
            task["review_notes"] = review_notes
        if expected_artifact_path is not None:
            task["expected_artifact_path"] = expected_artifact_path
        if acceptance is not None:
            task["acceptance"] = acceptance
        if assigned_role is not None:
            task["assigned_role"] = assigned_role
        if review_state is not None:
            task["review_state"] = review_state
        if milestone_id is not None:
            task["milestone_id"] = milestone_id
        if layer is not None:
            task["layer"] = layer
        if category is not None:
            task["category"] = category
        if completed_at is not None:
            task["completed_at"] = completed_at

        if not task.get("milestone_id"):
            resolved_milestone_id = self._resolve_milestone_id(
                task["project_name"],
                task.get("acceptance"),
                title=task["title"],
                details=task["details"],
                owner_role=task["owner_role"],
            )
            if resolved_milestone_id:
                task["milestone_id"] = resolved_milestone_id

        if task["status"] in {"ready", "completed"}:
            issues = self.task_gate_issues(task, target_status=task["status"])
            if issues:
                raise ValueError("; ".join(issues))
            if task["status"] == "completed" and not task.get("completed_at"):
                task["completed_at"] = _utc_now()
        task["updated_at"] = _utc_now()
        with self._connect() as connection:
            connection.execute(
                """
                UPDATE tasks
                SET status = ?, owner_role = ?, result_summary = ?, review_notes = ?,
                    expected_artifact_path = ?, acceptance_json = ?, assigned_role = ?, review_state = ?,
                    milestone_id = ?, layer = ?, category = ?, completed_at = ?, updated_at = ?
                WHERE id = ?
                """,
                (
                    task["status"],
                    task["owner_role"],
                    task["result_summary"],
                    task["review_notes"],
                    task["expected_artifact_path"],
                    _json_dumps(task["acceptance"]),
                    task.get("assigned_role"),
                    task.get("review_state"),
                    task.get("milestone_id"),
                    task.get("layer"),
                    task.get("category"),
                    task.get("completed_at"),
                    task["updated_at"],
                    task_id,
                ),
            )
        self.render_kanban(task["project_name"])
        updated = self.get_task(task_id)
        if updated is None:
            raise ValueError(f"Task vanished after update: {task_id}")
        return updated

    def create_run(self, project_name: str, task_id: str, team_state: dict[str, Any] | None = None) -> dict[str, Any]:
        self._ensure_project(project_name)
        run_id = _new_id("run")
        now = _utc_now()
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO runs (id, project_name, task_id, status, stop_reason, last_error, team_state_json, created_at, updated_at, started_at, completed_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (run_id, project_name, task_id, "running", None, None, _json_dumps(team_state) if team_state else None, now, now, now, None),
            )
        return self.get_run(run_id)

    def get_run(self, run_id: str) -> dict[str, Any] | None:
        with self._connect() as connection:
            row = connection.execute("SELECT * FROM runs WHERE id = ?", (run_id,)).fetchone()
        return dict(row) if row else None

    def list_runs(self, project_name: str | None = None) -> list[dict[str, Any]]:
        query = "SELECT * FROM runs WHERE 1 = 1"
        params: list[Any] = []
        if project_name:
            query += " AND project_name = ?"
            params.append(project_name)
        query += " ORDER BY created_at DESC"
        with self._connect() as connection:
            rows = connection.execute(query, tuple(params)).fetchall()
        return [dict(row) for row in rows]

    def update_run(
        self,
        run_id: str,
        *,
        status: str | None = None,
        stop_reason: str | None = None,
        last_error: str | None = None,
        team_state: dict[str, Any] | None = None,
        completed: bool = False,
    ) -> dict[str, Any]:
        run = self.get_run(run_id)
        if run is None:
            raise ValueError(f"Run not found: {run_id}")
        run["status"] = status or run["status"]
        if stop_reason is not None:
            run["stop_reason"] = stop_reason
        if last_error is not None:
            run["last_error"] = last_error
        if team_state is not None:
            run["team_state_json"] = _json_dumps(team_state)
        run["updated_at"] = _utc_now()
        if completed:
            run["completed_at"] = _utc_now()
        with self._connect() as connection:
            connection.execute(
                """
                UPDATE runs
                SET status = ?, stop_reason = ?, last_error = ?, team_state_json = ?, updated_at = ?, completed_at = ?
                WHERE id = ?
                """,
                (
                    run["status"],
                    run["stop_reason"],
                    run["last_error"],
                    run["team_state_json"],
                    run["updated_at"],
                    run["completed_at"],
                    run_id,
                ),
            )
        return self.get_run(run_id) or run

    def save_team_state(self, run_id: str, team_state: dict[str, Any]) -> None:
        self.update_run(run_id, team_state=team_state)

    def load_team_state(self, run_id: str) -> dict[str, Any] | None:
        run = self.get_run(run_id)
        if not run or not run.get("team_state_json"):
            return None
        return _json_loads(run["team_state_json"], default=None)

    def create_approval(
        self,
        run_id: str,
        task_id: str,
        requested_by: str,
        reason: str,
        *,
        approval_scope: str = "program",
        target_role: str | None = None,
        exact_task: str | None = None,
        expected_output: str | None = None,
        why_now: str | None = None,
        risks: list[str] | None = None,
    ) -> dict[str, Any]:
        latest = self.latest_approval_for_task(task_id)
        if latest and latest["status"] == "pending":
            return latest
        approval_id = _new_id("approval")
        now = _utc_now()
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO approvals (
                    id, run_id, task_id, requested_by, reason, status, created_at, decided_at, decision_note,
                    approval_scope, target_role, exact_task, expected_output, why_now, risks_json
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    approval_id,
                    run_id,
                    task_id,
                    requested_by,
                    reason,
                    "pending",
                    now,
                    None,
                    None,
                    approval_scope,
                    target_role,
                    exact_task,
                    expected_output,
                    why_now,
                    _json_dumps(risks or []),
                ),
            )
        approval = self.get_approval(approval_id)
        if approval is None:
            raise ValueError(f"Failed to create approval: {approval_id}")
        return approval

    def get_approval(self, approval_id: str) -> dict[str, Any] | None:
        with self._connect() as connection:
            row = connection.execute("SELECT * FROM approvals WHERE id = ?", (approval_id,)).fetchone()
        return self._deserialize_approval(row) if row else None

    def latest_approval_for_task(self, task_id: str) -> dict[str, Any] | None:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT * FROM approvals
                WHERE task_id = ?
                ORDER BY created_at DESC
                LIMIT 1
                """,
                (task_id,),
            ).fetchone()
        return self._deserialize_approval(row) if row else None

    def list_approvals(self, status: str | None = None) -> list[dict[str, Any]]:
        query = "SELECT * FROM approvals"
        params: tuple[Any, ...] = ()
        if status:
            query += " WHERE status = ?"
            params = (status,)
        query += " ORDER BY created_at ASC"
        with self._connect() as connection:
            rows = connection.execute(query, params).fetchall()
        return [self._deserialize_approval(row) for row in rows]

    def decide_approval(self, approval_id: str, decision: str, note: str | None = None) -> dict[str, Any]:
        approval = self.get_approval(approval_id)
        if approval is None:
            raise ValueError(f"Approval not found: {approval_id}")
        if approval["status"] != "pending":
            return approval
        status = "approved" if decision == "approve" else "rejected"
        decided_at = _utc_now()
        with self._connect() as connection:
            connection.execute(
                """
                UPDATE approvals
                SET status = ?, decided_at = ?, decision_note = ?
                WHERE id = ?
                """,
                (status, decided_at, note, approval_id),
            )
        if status == "rejected":
            self.update_task(approval["task_id"], status="blocked", owner_role="Orchestrator", review_notes=note or "Approval rejected")
        decided = self.get_approval(approval_id)
        if decided is None:
            raise ValueError(f"Approval vanished after decision: {approval_id}")
        return decided

    def approval_required_and_missing(self, task_id: str) -> bool:
        task = self.get_task(task_id)
        if task is None or not task["requires_approval"]:
            return False
        approval = self.latest_approval_for_task(task_id)
        return approval is None or approval["status"] != "approved"

    def record_delegation(self, run_id: str, task_id: str, from_role: str, to_role: str, note: str) -> dict[str, Any]:
        delegation_id = _new_id("edge")
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO delegation_edges (id, run_id, task_id, from_role, to_role, note, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (delegation_id, run_id, task_id, from_role, to_role, note, _utc_now()),
            )
        return {
            "id": delegation_id,
            "run_id": run_id,
            "task_id": task_id,
            "from_role": from_role,
            "to_role": to_role,
            "note": note,
        }

    def list_delegations(self, run_id: str) -> list[dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT * FROM delegation_edges WHERE run_id = ? ORDER BY created_at ASC",
                (run_id,),
            ).fetchall()
        return [dict(row) for row in rows]

    def create_agent_run(
        self,
        run_id: str,
        task_id: str,
        role: str,
        *,
        pid: int | None = None,
        input_artifact_path: str | None = None,
        input_artifact_sha256: str | None = None,
        notes: str | None = None,
    ) -> dict[str, Any]:
        agent_run_id = _new_id("agent_run")
        now = _utc_now()
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO agent_runs (
                    id, run_id, task_id, role, status, pid, input_artifact_path, input_artifact_sha256,
                    output_artifact_path, output_artifact_sha256, notes, started_at, completed_at, error
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    agent_run_id,
                    run_id,
                    task_id,
                    role,
                    "running",
                    pid,
                    input_artifact_path,
                    input_artifact_sha256,
                    None,
                    None,
                    notes,
                    now,
                    None,
                    None,
                ),
            )
        agent_run = self.get_agent_run(agent_run_id)
        if agent_run is None:
            raise ValueError(f"Failed to create agent run: {agent_run_id}")
        return agent_run

    def get_agent_run(self, agent_run_id: str) -> dict[str, Any] | None:
        with self._connect() as connection:
            row = connection.execute("SELECT * FROM agent_runs WHERE id = ?", (agent_run_id,)).fetchone()
        return self._deserialize_agent_run(row) if row else None

    def update_agent_run(
        self,
        agent_run_id: str,
        *,
        status: str | None = None,
        output_artifact_path: str | None = None,
        output_artifact_sha256: str | None = None,
        input_artifact_path: str | None = None,
        input_artifact_sha256: str | None = None,
        notes: str | None = None,
        error: str | None = None,
        pid: int | None = None,
        completed_at: str | None = None,
    ) -> dict[str, Any]:
        agent_run = self.get_agent_run(agent_run_id)
        if agent_run is None:
            raise ValueError(f"Agent run not found: {agent_run_id}")
        if status is not None:
            agent_run["status"] = status
        if output_artifact_path is not None:
            agent_run["output_artifact_path"] = output_artifact_path
        if output_artifact_sha256 is not None:
            agent_run["output_artifact_sha256"] = output_artifact_sha256
        if input_artifact_path is not None:
            agent_run["input_artifact_path"] = input_artifact_path
        if input_artifact_sha256 is not None:
            agent_run["input_artifact_sha256"] = input_artifact_sha256
        if notes is not None:
            agent_run["notes"] = notes
        if error is not None:
            agent_run["error"] = error
        if pid is not None:
            agent_run["pid"] = pid
        if completed_at is not None:
            agent_run["completed_at"] = completed_at
        elif agent_run["status"] == "completed" and not agent_run.get("completed_at"):
            agent_run["completed_at"] = _utc_now()
        with self._connect() as connection:
            connection.execute(
                """
                UPDATE agent_runs
                SET status = ?, pid = ?, input_artifact_path = ?, input_artifact_sha256 = ?,
                    output_artifact_path = ?, output_artifact_sha256 = ?, notes = ?, completed_at = ?, error = ?
                WHERE id = ?
                """,
                (
                    agent_run["status"],
                    agent_run.get("pid"),
                    agent_run.get("input_artifact_path"),
                    agent_run.get("input_artifact_sha256"),
                    agent_run.get("output_artifact_path"),
                    agent_run.get("output_artifact_sha256"),
                    agent_run.get("notes"),
                    agent_run.get("completed_at"),
                    agent_run.get("error"),
                    agent_run_id,
                ),
            )
        updated = self.get_agent_run(agent_run_id)
        if updated is None:
            raise ValueError(f"Agent run vanished after update: {agent_run_id}")
        return updated

    def latest_agent_run(self, run_id: str, task_id: str, role: str | None = None) -> dict[str, Any] | None:
        query = "SELECT * FROM agent_runs WHERE run_id = ? AND task_id = ?"
        params: list[Any] = [run_id, task_id]
        if role:
            query += " AND role = ?"
            params.append(role)
        query += " ORDER BY started_at DESC LIMIT 1"
        with self._connect() as connection:
            row = connection.execute(query, tuple(params)).fetchone()
        return self._deserialize_agent_run(row) if row else None

    def list_agent_runs(self, run_id: str) -> list[dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT * FROM agent_runs WHERE run_id = ? ORDER BY started_at DESC",
                (run_id,),
            ).fetchall()
        return [self._deserialize_agent_run(row) for row in rows]

    def record_message(
        self,
        run_id: str,
        task_id: str,
        event_type: str,
        payload: dict[str, Any],
        *,
        source: str | None = None,
        prompt_tokens: int | None = None,
        completion_tokens: int | None = None,
    ) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO messages (id, run_id, task_id, source, event_type, payload_json, prompt_tokens, completion_tokens, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    _new_id("msg"),
                    run_id,
                    task_id,
                    source,
                    event_type,
                    _json_dumps(payload),
                    prompt_tokens,
                    completion_tokens,
                    _utc_now(),
                ),
            )
        if prompt_tokens is not None or completion_tokens is not None:
            self.record_usage(
                run_id,
                task_id,
                source=source,
                prompt_tokens=prompt_tokens or 0,
                completion_tokens=completion_tokens or 0,
            )

    def record_usage(self, run_id: str, task_id: str, *, source: str | None, prompt_tokens: int, completion_tokens: int) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO usage_events (id, run_id, task_id, source, prompt_tokens, completion_tokens, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (_new_id("usage"), run_id, task_id, source, prompt_tokens, completion_tokens, _utc_now()),
            )

    def file_metadata(self, relative_path: str) -> dict[str, Any]:
        path = (self.paths.repo_root / relative_path).resolve()
        if not path.exists():
            raise FileNotFoundError(relative_path)
        content = path.read_bytes()
        stat = path.stat()
        return {
            "artifact_path": relative_path,
            "artifact_sha256": _sha256_bytes(content),
            "bytes_written": len(content),
            "size_bytes": len(content),
            "modified_at": datetime.fromtimestamp(stat.st_mtime, tz=UTC).isoformat(timespec="seconds"),
        }

    def _artifact_metadata(self, relative_path: str | None, content: str) -> dict[str, Any]:
        metadata: dict[str, Any] = {}
        if relative_path:
            artifact_info = self.file_metadata(relative_path)
            metadata["artifact_path"] = artifact_info["artifact_path"]
            metadata["artifact_sha256"] = artifact_info["artifact_sha256"]
            metadata["bytes_written"] = artifact_info["bytes_written"]
        else:
            content_bytes = content.encode("utf-8")
            metadata["artifact_sha256"] = _sha256_bytes(content_bytes)
            metadata["bytes_written"] = len(content_bytes)
        return metadata

    def record_artifact(
        self,
        run_id: str,
        task_id: str,
        kind: str,
        content: str,
        *,
        artifact_path: str | None = None,
        artifact_sha256: str | None = None,
        bytes_written: int | None = None,
        produced_by: str | None = None,
        source_agent_run_id: str | None = None,
        input_artifact_paths: list[str] | None = None,
    ) -> dict[str, Any]:
        metadata = self._artifact_metadata(artifact_path, content) if artifact_path else {}
        final_artifact_sha256 = artifact_sha256 or metadata.get("artifact_sha256")
        final_bytes_written = bytes_written or metadata.get("bytes_written") or len(content.encode("utf-8"))
        artifact_id = _new_id("artifact")
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO artifacts (
                    id, run_id, task_id, kind, content, created_at, artifact_path, artifact_sha256, bytes_written,
                    produced_by, source_agent_run_id, input_artifact_paths_json
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    artifact_id,
                    run_id,
                    task_id,
                    kind,
                    content,
                    _utc_now(),
                    artifact_path,
                    final_artifact_sha256,
                    final_bytes_written,
                    produced_by,
                    source_agent_run_id,
                    _json_dumps(input_artifact_paths or []),
                ),
            )
        artifact = self.get_artifact(artifact_id)
        if artifact is None:
            raise ValueError(f"Failed to create artifact: {artifact_id}")
        return artifact

    def get_artifact(self, artifact_id: str) -> dict[str, Any] | None:
        with self._connect() as connection:
            row = connection.execute("SELECT * FROM artifacts WHERE id = ?", (artifact_id,)).fetchone()
        return self._deserialize_artifact(row) if row else None

    def list_artifacts(self, run_id: str) -> list[dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT * FROM artifacts WHERE run_id = ? ORDER BY created_at ASC",
                (run_id,),
            ).fetchall()
        return [self._deserialize_artifact(row) for row in rows]

    def record_validation_result(
        self,
        run_id: str,
        task_id: str,
        *,
        agent_run_id: str | None = None,
        validator_role: str,
        artifact_path: str,
        status: str,
        checks: dict[str, Any],
        summary: str,
    ) -> dict[str, Any]:
        artifact_sha256 = None
        if artifact_path:
            try:
                artifact_sha256 = self.file_metadata(artifact_path)["artifact_sha256"]
            except FileNotFoundError:
                artifact_sha256 = None
        validation_id = _new_id("validation")
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO validation_results (
                    id, run_id, task_id, agent_run_id, validator_role, artifact_path, artifact_sha256, status,
                    checks_json, summary, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    validation_id,
                    run_id,
                    task_id,
                    agent_run_id,
                    validator_role,
                    artifact_path,
                    artifact_sha256,
                    status,
                    _json_dumps(checks),
                    summary,
                    _utc_now(),
                ),
            )
        validation = self.get_validation_result(validation_id)
        if validation is None:
            raise ValueError(f"Failed to create validation result: {validation_id}")
        return validation

    def get_validation_result(self, validation_id: str) -> dict[str, Any] | None:
        with self._connect() as connection:
            row = connection.execute("SELECT * FROM validation_results WHERE id = ?", (validation_id,)).fetchone()
        return self._deserialize_validation_result(row) if row else None

    def list_validation_results(self, run_id: str) -> list[dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT * FROM validation_results WHERE run_id = ? ORDER BY created_at ASC",
                (run_id,),
            ).fetchall()
        return [self._deserialize_validation_result(row) for row in rows]

    def record_trace_event(
        self,
        run_id: str,
        task_id: str,
        event_type: str,
        *,
        source: str | None = None,
        summary: str | None = None,
        packet: dict[str, Any] | None = None,
        route: dict[str, Any] | None = None,
        raw_json: dict[str, Any] | None = None,
    ) -> None:
        payload = {"summary": summary, "packet": packet or {}, "route": route or {}, "raw_json": raw_json or {}}
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO trace_events (id, run_id, task_id, source, event_type, payload_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (_new_id("trace"), run_id, task_id, source, event_type, _json_dumps(payload), _utc_now()),
            )

    def list_messages(self, run_id: str, *, task_id: str | None = None) -> list[dict[str, Any]]:
        with self._connect() as connection:
            message_rows = connection.execute(
                "SELECT * FROM messages WHERE run_id = ? ORDER BY created_at ASC",
                (run_id,),
            ).fetchall()
            trace_rows = connection.execute(
                "SELECT * FROM trace_events WHERE run_id = ? ORDER BY created_at ASC",
                (run_id,),
            ).fetchall()
        items = [self._deserialize_message(row, record_type="message") for row in message_rows]
        items.extend(self._deserialize_trace_event(row) for row in trace_rows)
        if task_id is not None:
            items = [item for item in items if item["task_id"] == task_id]
        items.sort(key=lambda item: item["created_at"])
        return items

    def append_session_summary(self, summary: dict[str, Any]) -> None:
        current = _json_loads(self.paths.summary_path.read_text(encoding="utf-8"), default=[])
        current.append(summary)
        self.paths.summary_path.write_text(_json_dumps(current) + "\n", encoding="utf-8")

    def load_health_snapshot(self) -> dict[str, Any]:
        if not self.paths.health_path.exists():
            return {"ok": None, "issues": [], "checked_tables": []}
        return _json_loads(self.paths.health_path.read_text(encoding="utf-8"), default={}) or {}

    def write_health_snapshot(self, payload: dict[str, Any]) -> None:
        self.paths.health_path.write_text(_json_dumps(payload) + "\n", encoding="utf-8")

    def _backup_manifest_path(self, backup_path: Path) -> Path:
        return backup_path.with_suffix(".json")

    def create_dispatch_backup(
        self,
        *,
        project_name: str,
        trigger: str,
        task_id: str,
        note: str,
    ) -> dict[str, Any]:
        self._ensure_project(project_name)
        backup_id = _new_id("backup")
        timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
        backup_path = self.paths.backups_dir / f"{timestamp}_{project_name}_{trigger}_{backup_id}.db"
        manifest_path = self._backup_manifest_path(backup_path)
        shutil.copy2(self.paths.db_path, backup_path)
        sha256 = _sha256_bytes(backup_path.read_bytes())
        manifest = {
            "backup_id": backup_id,
            "project_name": project_name,
            "trigger": trigger,
            "task_id": task_id,
            "note": note,
            "created_at": _utc_now(),
            "path": str(backup_path),
            "manifest_path": str(manifest_path),
            "sha256": sha256,
            "source_db_path": str(self.paths.db_path),
        }
        manifest_path.write_text(_json_dumps(manifest) + "\n", encoding="utf-8")
        return manifest

    def list_dispatch_backups(self, project_name: str | None = None, limit: int = 8) -> list[dict[str, Any]]:
        backups: list[dict[str, Any]] = []
        for manifest_path in sorted(self.paths.backups_dir.glob("*.json")):
            try:
                backup = json.loads(manifest_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                continue
            if project_name and backup.get("project_name") != project_name:
                continue
            backups.append(backup)
        backups.sort(key=lambda item: item.get("created_at") or "", reverse=True)
        return backups[:limit]

    def _find_dispatch_backup(self, backup_id: str) -> dict[str, Any] | None:
        for backup in self.list_dispatch_backups(limit=10_000):
            if backup.get("backup_id") == backup_id:
                return backup
        return None

    def restore_dispatch_backup(self, *, backup_id: str, requested_by: str) -> dict[str, Any]:
        backup = self._find_dispatch_backup(backup_id)
        if backup is None:
            raise ValueError(f"Backup not found: {backup_id}")
        pre_restore_backup = self.create_dispatch_backup(
            project_name=backup["project_name"],
            trigger="pre_restore",
            task_id=backup["task_id"],
            note=f"Pre-restore backup before restoring {backup_id} requested by {requested_by}.",
        )
        shutil.copy2(Path(backup["path"]), self.paths.db_path)
        self.initialize()
        receipt = {
            "restore_id": _new_id("restore"),
            "backup_id": backup_id,
            "requested_by": requested_by,
            "restored_at": _utc_now(),
            "pre_restore_backup": pre_restore_backup,
            "store_health": self.schema_health(),
        }
        receipt_path = self.paths.restore_receipts_dir / f"{receipt['restore_id']}.json"
        receipt["receipt_path"] = str(receipt_path)
        receipt_path.write_text(_json_dumps(receipt) + "\n", encoding="utf-8")
        return receipt

    def get_run_evidence(self, run_id: str) -> dict[str, Any]:
        run = self.get_run(run_id)
        if run is None:
            raise ValueError(f"Run not found: {run_id}")
        task = self.get_task(run["task_id"])
        messages = self.list_messages(run_id)
        trace_events = [item for item in messages if item.get("record_type") == "trace"]
        message_events = [item for item in messages if item.get("record_type") == "message"]
        approvals = [approval for approval in self.list_approvals() if approval.get("run_id") == run_id]
        agent_runs = self.list_agent_runs(run_id)
        artifacts = self.list_artifacts(run_id)
        validation_results = self.list_validation_results(run_id)
        delegations = self.list_delegations(run_id)
        sdk_runtime = self._sdk_runtime_summary(run, trace_events, agent_runs)
        return {
            "run": run,
            "task": task,
            "project_name": run["project_name"],
            "delegations": delegations,
            "approvals": approvals,
            "messages": message_events,
            "trace_events": trace_events,
            "agent_runs": agent_runs,
            "artifacts": artifacts,
            "validation_results": validation_results,
            "sdk_runtime": sdk_runtime,
        }

    def _sdk_runtime_summary(
        self,
        run: dict[str, Any],
        trace_events: list[dict[str, Any]],
        agent_runs: list[dict[str, Any]],
    ) -> dict[str, Any] | None:
        team_state = self.load_team_state(run["id"]) or {}
        specialist_runtime = team_state.get("specialist_runtime") or {}
        mode = team_state.get("runtime_mode") or specialist_runtime.get("mode") or "custom"
        sessions: list[dict[str, Any]] = []
        approval_bridge_events: list[dict[str, Any]] = []
        for event in trace_events:
            payload = event.get("payload") or {}
            packet = payload.get("packet") or {}
            if event["event_type"] == "sdk_specialist_result_received":
                sessions.append(
                    {
                        "session_id": packet.get("session_id"),
                        "response_id": packet.get("response_id"),
                        "trace_id": packet.get("trace_id"),
                        "model": packet.get("model"),
                        "role": event.get("source"),
                        "created_at": event.get("created_at"),
                    }
                )
            if event["event_type"] == "sdk_approval_bridge_requested":
                approval_bridge_events.append(
                    {
                        "approval_id": packet.get("approval_id"),
                        "target_role": packet.get("target_role"),
                        "session_id": packet.get("session_id"),
                        "expected_artifact_path": packet.get("expected_artifact_path"),
                        "created_at": event.get("created_at"),
                    }
                )
        if not (sessions or approval_bridge_events or team_state):
            return None
        return {
            "mode": mode,
            "orchestrator_source": specialist_runtime.get("orchestrator_source"),
            "planning_layer": specialist_runtime.get("planning_layer"),
            "specialist_roles": specialist_runtime.get("specialist_roles", []),
            "sessions": sessions,
            "approval_bridge_events": approval_bridge_events,
            "specialist_run_count": len(agent_runs),
        }

    def render_kanban(self, project_name: str) -> None:
        tasks = self.list_tasks(project_name)
        columns: dict[str, list[dict[str, Any]]] = {key: [] for key, _ in self.board_columns()}
        blocked_tasks: list[dict[str, Any]] = []
        board_title = project_name.replace("-", " ").title()
        if not board_title.lower().endswith("kanban"):
            board_title = f"{board_title} Kanban"
        for task in tasks:
            if task["status"] in {"blocked", "deferred"}:
                blocked_tasks.append(task)
            else:
                columns[self.task_board_column_key(task)].append(task)
        lines = [
            f"# {board_title}",
            "",
            "This file is rendered from `sessions/studio.db`. Do not use it as the source of truth.",
            "",
        ]
        for column_key, column_name in self.board_columns():
            lines.append(f"## {column_name}")
            lines.append("")
            column_tasks = columns[column_key]
            if not column_tasks:
                lines.append("_No items_")
                lines.append("")
                continue
            for task in column_tasks:
                lines.extend(
                    [
                        f"### {task['title']}",
                        f"- ID: {task['id']}",
                        f"- Kind: {task['task_kind']}",
                        f"- Status: {task['status']}",
                        f"- Owner: {task['owner_role']}",
                        f"- Assigned Role: {task.get('assigned_role') or task['owner_role']}",
                        f"- Priority: {task['priority']}",
                        f"- Requires Approval: {'yes' if task['requires_approval'] else 'no'}",
                        f"- Review State: {task.get('review_state') or 'None'}",
                    ]
                )
                if task["parent_task_id"]:
                    lines.append(f"- Parent Task: {task['parent_task_id']}")
                if task.get("milestone_id"):
                    milestone = self.get_milestone(task["milestone_id"])
                    if milestone:
                        lines.append(f"- Milestone: {milestone['title']}")
                if task["expected_artifact_path"]:
                    lines.append(f"- Expected Artifact: {task['expected_artifact_path']}")
                lines.append(f"- Details: {task['details']}")
                if task["result_summary"]:
                    lines.append(f"- Result: {task['result_summary']}")
                if task["review_notes"]:
                    lines.append(f"- Review Notes: {task['review_notes']}")
                lines.append("")
        if blocked_tasks:
            lines.extend(["## Blocked", ""])
            for task in blocked_tasks:
                lines.extend(
                    [
                        f"### {task['title']}",
                        f"- ID: {task['id']}",
                        f"- Status: {task['status']}",
                        f"- Secondary State: {task['status']}",
                        f"- Owner: {task['owner_role']}",
                        f"- Details: {task['details']}",
                        "",
                    ]
                )
        kanban_path = self.paths.repo_root / "projects" / project_name / "execution" / "KANBAN.md"
        kanban_path.parent.mkdir(parents=True, exist_ok=True)
        kanban_path.write_text("\n".join(lines).strip() + "\n", encoding="utf-8")

    def _deserialize_task(self, row: sqlite3.Row) -> dict[str, Any]:
        task = dict(row)
        task["requires_approval"] = bool(task["requires_approval"])
        task["acceptance"] = _json_loads(task.get("acceptance_json"), default={})
        return task

    def _deserialize_approval(self, row: sqlite3.Row) -> dict[str, Any]:
        approval = dict(row)
        approval["risks"] = _json_loads(approval.get("risks_json"), default=[])
        return approval

    def _deserialize_agent_run(self, row: sqlite3.Row) -> dict[str, Any]:
        return dict(row)

    def _deserialize_message(self, row: sqlite3.Row, *, record_type: str) -> dict[str, Any]:
        message = dict(row)
        message["payload"] = _json_loads(message.pop("payload_json"), default={})
        message["record_type"] = record_type
        return message

    def _deserialize_trace_event(self, row: sqlite3.Row) -> dict[str, Any]:
        event = dict(row)
        event["payload"] = _json_loads(event.pop("payload_json"), default={})
        event["record_type"] = "trace"
        return event

    def _deserialize_artifact(self, row: sqlite3.Row) -> dict[str, Any]:
        artifact = dict(row)
        artifact["input_artifact_paths"] = _json_loads(artifact.get("input_artifact_paths_json"), default=[])
        return artifact

    def _deserialize_validation_result(self, row: sqlite3.Row) -> dict[str, Any]:
        validation = dict(row)
        validation["checks"] = _json_loads(validation.get("checks_json"), default={})
        return validation
