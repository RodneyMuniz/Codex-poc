from __future__ import annotations

import json
import sqlite3
import uuid
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Iterator


PROJECT_NAME = "tactics-game"
TASK_STATUSES = ("backlog", "ready", "in_progress", "in_review", "completed", "blocked")
REQUIRED_TABLES = (
    "projects",
    "tasks",
    "runs",
    "approvals",
    "delegation_edges",
    "messages",
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


@dataclass(frozen=True)
class StorePaths:
    repo_root: Path
    db_path: Path
    kanban_path: Path
    memory_dir: Path
    health_path: Path
    summary_path: Path
    legacy_approvals_path: Path


class SessionStore:
    def __init__(self, repo_root: str | Path | None = None, db_path: str | Path | None = None) -> None:
        root = Path(repo_root or Path.cwd()).resolve()
        database_path = Path(db_path) if db_path else root / "sessions" / "studio.db"
        memory_dir = root / "memory"
        self.paths = StorePaths(
            repo_root=root,
            db_path=database_path.resolve(),
            kanban_path=root / "projects" / PROJECT_NAME / "execution" / "KANBAN.md",
            memory_dir=memory_dir,
            health_path=memory_dir / "framework_health.json",
            summary_path=memory_dir / "session_summaries.json",
            legacy_approvals_path=root / "sessions" / "approvals.json",
        )
        self.paths.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.paths.memory_dir.mkdir(parents=True, exist_ok=True)
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
                    FOREIGN KEY(project_name) REFERENCES projects(name),
                    FOREIGN KEY(parent_task_id) REFERENCES tasks(id)
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
                    FOREIGN KEY(run_id) REFERENCES runs(id),
                    FOREIGN KEY(task_id) REFERENCES tasks(id)
                );
                """
            )
            connection.execute(
                """
                INSERT OR IGNORE INTO projects (id, name, root_path, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (_new_id("project"), PROJECT_NAME, str(self.paths.repo_root / "projects" / PROJECT_NAME), _utc_now()),
            )
        self._ensure_task_columns()
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
        }
        with self._connect() as connection:
            existing = {row["name"] for row in connection.execute("PRAGMA table_info(tasks)").fetchall()}
            for column_name, definition in task_columns.items():
                if column_name not in existing:
                    connection.execute(f"ALTER TABLE tasks ADD COLUMN {column_name} {definition}")

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
            rows = connection.execute("SELECT id, status, owner_role FROM tasks").fetchall()
            for row in rows:
                new_status = mappings.get(row["status"], row["status"])
                owner_role = "PM" if row["owner_role"] == "ProjectPO" else row["owner_role"]
                connection.execute(
                    "UPDATE tasks SET status = ?, owner_role = ? WHERE id = ?",
                    (new_status, owner_role, row["id"]),
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
    ) -> dict[str, Any]:
        if status not in TASK_STATUSES:
            raise ValueError(f"Invalid task status: {status}")
        task_id = _new_id("task")
        now = _utc_now()
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO tasks (
                    id, project_name, parent_task_id, task_kind, title, objective, details, description, status,
                    priority, requires_approval, owner_role, expected_artifact_path, acceptance_json, raw_request,
                    result_summary, review_notes, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                ),
            )
        self.render_kanban(project_name)
        task = self.get_task(task_id)
        if task is None:
            raise ValueError(f"Failed to create task: {task_id}")
        return task

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
        task["updated_at"] = _utc_now()
        with self._connect() as connection:
            connection.execute(
                """
                UPDATE tasks
                SET status = ?, owner_role = ?, result_summary = ?, review_notes = ?,
                    expected_artifact_path = ?, acceptance_json = ?, updated_at = ?
                WHERE id = ?
                """,
                (
                    task["status"],
                    task["owner_role"],
                    task["result_summary"],
                    task["review_notes"],
                    task["expected_artifact_path"],
                    _json_dumps(task["acceptance"]),
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

    def create_approval(self, run_id: str, task_id: str, requested_by: str, reason: str) -> dict[str, Any]:
        latest = self.latest_approval_for_task(task_id)
        if latest and latest["status"] == "pending":
            return latest
        approval_id = _new_id("approval")
        now = _utc_now()
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO approvals (id, run_id, task_id, requested_by, reason, status, created_at, decided_at, decision_note)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (approval_id, run_id, task_id, requested_by, reason, "pending", now, None, None),
            )
        approval = self.get_approval(approval_id)
        if approval is None:
            raise ValueError(f"Failed to create approval: {approval_id}")
        return approval

    def get_approval(self, approval_id: str) -> dict[str, Any] | None:
        with self._connect() as connection:
            row = connection.execute("SELECT * FROM approvals WHERE id = ?", (approval_id,)).fetchone()
        return dict(row) if row else None

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
        return dict(row) if row else None

    def list_approvals(self, status: str | None = None) -> list[dict[str, Any]]:
        query = "SELECT * FROM approvals"
        params: tuple[Any, ...] = ()
        if status:
            query += " WHERE status = ?"
            params = (status,)
        query += " ORDER BY created_at ASC"
        with self._connect() as connection:
            rows = connection.execute(query, params).fetchall()
        return [dict(row) for row in rows]

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

    def record_artifact(self, run_id: str, task_id: str, kind: str, content: str) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO artifacts (id, run_id, task_id, kind, content, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (_new_id("artifact"), run_id, task_id, kind, content, _utc_now()),
            )

    def list_artifacts(self, run_id: str) -> list[dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT * FROM artifacts WHERE run_id = ? ORDER BY created_at ASC",
                (run_id,),
            ).fetchall()
        return [dict(row) for row in rows]

    def append_session_summary(self, summary: dict[str, Any]) -> None:
        current = _json_loads(self.paths.summary_path.read_text(encoding="utf-8"), default=[])
        current.append(summary)
        self.paths.summary_path.write_text(_json_dumps(current) + "\n", encoding="utf-8")

    def write_health_snapshot(self, payload: dict[str, Any]) -> None:
        self.paths.health_path.write_text(_json_dumps(payload) + "\n", encoding="utf-8")

    def render_kanban(self, project_name: str) -> None:
        tasks = self.list_tasks(project_name)
        columns: dict[str, list[dict[str, Any]]] = {
            "Backlog": [],
            "Ready": [],
            "In Progress": [],
            "Review": [],
            "Done": [],
            "Blocked": [],
        }
        for task in tasks:
            match task["status"]:
                case "backlog":
                    columns["Backlog"].append(task)
                case "ready":
                    columns["Ready"].append(task)
                case "in_progress":
                    columns["In Progress"].append(task)
                case "in_review":
                    columns["Review"].append(task)
                case "completed":
                    columns["Done"].append(task)
                case _:
                    columns["Blocked"].append(task)
        lines = [
            "# Tactics Game Kanban",
            "",
            "This file is rendered from `sessions/studio.db`. Do not use it as the source of truth.",
            "",
        ]
        for column_name, column_tasks in columns.items():
            lines.append(f"## {column_name}")
            lines.append("")
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
                        f"- Priority: {task['priority']}",
                        f"- Requires Approval: {'yes' if task['requires_approval'] else 'no'}",
                    ]
                )
                if task["parent_task_id"]:
                    lines.append(f"- Parent Task: {task['parent_task_id']}")
                if task["expected_artifact_path"]:
                    lines.append(f"- Expected Artifact: {task['expected_artifact_path']}")
                lines.append(f"- Details: {task['details']}")
                if task["result_summary"]:
                    lines.append(f"- Result: {task['result_summary']}")
                if task["review_notes"]:
                    lines.append(f"- Review Notes: {task['review_notes']}")
                lines.append("")
        self.paths.kanban_path.parent.mkdir(parents=True, exist_ok=True)
        self.paths.kanban_path.write_text("\n".join(lines).strip() + "\n", encoding="utf-8")

    def _deserialize_task(self, row: sqlite3.Row) -> dict[str, Any]:
        task = dict(row)
        task["requires_approval"] = bool(task["requires_approval"])
        task["acceptance"] = _json_loads(task.get("acceptance_json"), default={})
        return task
