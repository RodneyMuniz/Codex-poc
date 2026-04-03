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
TASK_ID_PREFIXES = {
    "program-kanban": "PK",
    "tactics-game": "TG",
}
LEGACY_TASK_ID_PREFIXES = {
    "program-kanban": ("PK", "TGD"),
    "tactics-game": ("TG",),
}
TASK_STATUSES = ("backlog", "ready", "in_progress", "in_review", "completed", "blocked")
PRIMARY_BOARD_COLUMNS = (
    ("backlog", "Backlog"),
    ("ready", "Ready for Build"),
    ("in_progress", "In Progress"),
    ("in_review", "In Review"),
    ("completed", "Complete"),
)
COMPLIANCE_RECORD_KINDS = {
    "breach": "breach",
    "compliant_delegated_run": "compliant",
    "local_exception_approved": "approved_exception",
}
MEDIA_SERVICE_CONTRACT_CATALOG = {
    "visual": (
        {
            "service_key": "artifact_indexing",
            "owner": "Framework",
            "execution_mode": "deterministic",
            "summary": "Indexes visual artifacts and stores canonical provenance in SQLite.",
            "why_not_ai": "Artifact indexing must stay authoritative even when specialist outputs vary.",
            "evidence_surface": "visual_artifacts, artifacts, and run-details",
        },
        {
            "service_key": "import_bookkeeping",
            "owner": "Framework",
            "execution_mode": "deterministic",
            "summary": "Normalizes imported visual assets into the canonical project artifact structure.",
            "why_not_ai": "Import bookkeeping must be repeatable and should not depend on model behavior.",
            "evidence_surface": "visual_artifacts metadata and file manifests",
        },
        {
            "service_key": "review_state_persistence",
            "owner": "Framework",
            "execution_mode": "deterministic",
            "summary": "Persists review state and selected-direction truth for visual artifacts.",
            "why_not_ai": "Approval and review state are control-room truth, not specialist opinion.",
            "evidence_surface": "visual_artifacts.review_state and selected_direction",
        },
        {
            "service_key": "manifest_generation",
            "owner": "Framework",
            "execution_mode": "deterministic",
            "summary": "Builds manifests and deterministic handoff metadata for approved visual outputs.",
            "why_not_ai": "Runtime-facing manifests must be stable and reproducible.",
            "evidence_surface": "artifacts, worker_manifest, and run-details",
        },
    ),
    "audio": (
        {
            "service_key": "artifact_indexing",
            "owner": "Framework",
            "execution_mode": "deterministic",
            "summary": "Indexes audio artifacts and stores canonical provenance in SQLite.",
            "why_not_ai": "Artifact indexing must stay authoritative even when specialist outputs vary.",
            "evidence_surface": "audio artifact metadata, artifacts, and run-details",
        },
        {
            "service_key": "import_bookkeeping",
            "owner": "Framework",
            "execution_mode": "deterministic",
            "summary": "Normalizes imported audio assets into the canonical project artifact structure.",
            "why_not_ai": "Import bookkeeping must be repeatable and should not depend on model behavior.",
            "evidence_surface": "audio artifact metadata and file manifests",
        },
        {
            "service_key": "review_state_persistence",
            "owner": "Framework",
            "execution_mode": "deterministic",
            "summary": "Persists review state and selected-direction truth for audio artifacts.",
            "why_not_ai": "Approval and review state are control-room truth, not specialist opinion.",
            "evidence_surface": "audio review metadata and run-details",
        },
        {
            "service_key": "manifest_generation",
            "owner": "Framework",
            "execution_mode": "deterministic",
            "summary": "Builds manifests and deterministic handoff metadata for approved audio outputs.",
            "why_not_ai": "Runtime-facing manifests must be stable and reproducible.",
            "evidence_surface": "artifacts, worker_manifest, and run-details",
        },
    ),
}
REQUIRED_TABLES = (
    "projects",
    "milestones",
    "tasks",
    "runs",
    "agent_runs",
    "approvals",
    "compliance_records",
    "delegation_edges",
    "local_exception_approvals",
    "messages",
    "trace_events",
    "validation_results",
    "usage_events",
    "execution_packets",
    "execution_job_reservations",
    "artifacts",
    "visual_artifacts",
)
CONTEXT_RECEIPT_LIST_FIELDS = (
    "accepted_assumptions",
    "blocked_questions",
    "allowed_tools",
    "allowed_paths",
    "prior_artifact_paths",
    "resume_conditions",
)


def _utc_now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def _new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


def _task_id_prefix(project_name: str) -> str:
    return TASK_ID_PREFIXES.get(project_name, project_name.replace("-", "")[:2].upper() or "TK")


def _task_id_aliases(project_name: str) -> tuple[str, ...]:
    primary = _task_id_prefix(project_name)
    aliases = list(LEGACY_TASK_ID_PREFIXES.get(project_name, (primary,)))
    if primary not in aliases:
        aliases.insert(0, primary)
    return tuple(aliases)


def _format_task_id(prefix: str, sequence: int) -> str:
    width = max(3, len(str(sequence)))
    return f"{prefix}-{sequence:0{width}d}"


def _task_sequence_from_id(task_id: str, prefixes: tuple[str, ...]) -> int | None:
    for prefix in prefixes:
        match = re.fullmatch(rf"{re.escape(prefix)}-(\d+)", task_id)
        if match:
            return int(match.group(1))
    return None


def _json_dumps(value: Any) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True, default=str)


def _json_loads(value: str | None, default: Any) -> Any:
    if not value:
        return default
    return json.loads(value)


def _normalize_string_list(value: Any) -> list[str]:
    if value is None:
        return []
    items = value if isinstance(value, list) else [value]
    normalized: list[str] = []
    seen: set[str] = set()
    for item in items:
        text = str(item).strip()
        if not text or text in seen:
            continue
        seen.add(text)
        normalized.append(text)
    return normalized


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

                CREATE TABLE IF NOT EXISTS local_exception_approvals (
                    id TEXT PRIMARY KEY,
                    run_id TEXT NOT NULL,
                    task_id TEXT NOT NULL,
                    requested_by TEXT NOT NULL,
                    reason TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    decided_at TEXT,
                    decision_note TEXT,
                    approval_scope TEXT NOT NULL DEFAULT 'local-exception',
                    target_role TEXT,
                    exact_task TEXT,
                    expected_output TEXT,
                    why_now TEXT,
                    risks_json TEXT,
                    one_shot INTEGER NOT NULL DEFAULT 1,
                    expires_at TEXT,
                    consumed_at TEXT,
                    FOREIGN KEY(run_id) REFERENCES runs(id),
                    FOREIGN KEY(task_id) REFERENCES tasks(id)
                );

                CREATE TABLE IF NOT EXISTS compliance_records (
                    id TEXT PRIMARY KEY,
                    run_id TEXT NOT NULL,
                    task_id TEXT NOT NULL,
                    record_kind TEXT NOT NULL,
                    compliance_state TEXT NOT NULL,
                    policy_area TEXT,
                    violation_type TEXT,
                    severity TEXT NOT NULL DEFAULT 'info',
                    local_exception_approval_id TEXT,
                    source_role TEXT,
                    decision_note TEXT,
                    details TEXT NOT NULL,
                    evidence_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(run_id) REFERENCES runs(id),
                    FOREIGN KEY(task_id) REFERENCES tasks(id),
                    FOREIGN KEY(local_exception_approval_id) REFERENCES local_exception_approvals(id)
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
                    model TEXT,
                    tier TEXT,
                    lane TEXT,
                    cached_input_tokens INTEGER NOT NULL DEFAULT 0,
                    reasoning_tokens INTEGER NOT NULL DEFAULT 0,
                    estimated_cost_usd REAL NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(run_id) REFERENCES runs(id),
                    FOREIGN KEY(task_id) REFERENCES tasks(id)
                );

                CREATE TABLE IF NOT EXISTS execution_packets (
                    authority_packet_id TEXT PRIMARY KEY,
                    authority_job_id TEXT NOT NULL,
                    authority_token TEXT NOT NULL,
                    authority_schema_name TEXT NOT NULL,
                    authority_execution_tier TEXT NOT NULL,
                    authority_execution_lane TEXT NOT NULL,
                    authority_delegated_work INTEGER NOT NULL DEFAULT 0,
                    priority_class TEXT NOT NULL,
                    budget_max_tokens INTEGER NOT NULL,
                    budget_reservation_id TEXT,
                    retry_limit INTEGER NOT NULL,
                    early_stop_rule TEXT NOT NULL,
                    packet_id TEXT NOT NULL,
                    job_id TEXT NOT NULL,
                    actual_total_tokens INTEGER NOT NULL DEFAULT 0,
                    retry_count INTEGER NOT NULL DEFAULT 0,
                    escalation_target TEXT,
                    stop_reason TEXT,
                    status TEXT NOT NULL DEFAULT 'queued',
                    run_id TEXT,
                    task_id TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY(run_id) REFERENCES runs(id),
                    FOREIGN KEY(task_id) REFERENCES tasks(id)
                );

                CREATE TABLE IF NOT EXISTS execution_job_reservations (
                    job_id TEXT PRIMARY KEY,
                    priority_class TEXT NOT NULL,
                    reserved_max_tokens INTEGER NOT NULL DEFAULT 0,
                    reservation_status TEXT NOT NULL DEFAULT 'unreserved',
                    run_id TEXT,
                    task_id TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
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

                CREATE TABLE IF NOT EXISTS visual_artifacts (
                    id TEXT PRIMARY KEY,
                    project_name TEXT NOT NULL,
                    task_id TEXT NOT NULL,
                    run_id TEXT,
                    artifact_kind TEXT NOT NULL DEFAULT 'image',
                    provider TEXT,
                    model TEXT,
                    prompt_summary TEXT,
                    revised_prompt TEXT,
                    parent_visual_artifact_id TEXT,
                    lineage_root_visual_artifact_id TEXT,
                    locked_base_visual_artifact_id TEXT,
                    edit_session_id TEXT,
                    edit_intent TEXT,
                    edit_scope_json TEXT NOT NULL DEFAULT '{}',
                    protected_regions_json TEXT NOT NULL DEFAULT '[]',
                    mask_reference_json TEXT NOT NULL DEFAULT '{}',
                    iteration_index INTEGER NOT NULL DEFAULT 0,
                    review_state TEXT NOT NULL DEFAULT 'pending_review',
                    selected_direction INTEGER NOT NULL DEFAULT 0,
                    artifact_path TEXT NOT NULL,
                    artifact_sha256 TEXT,
                    bytes_written INTEGER,
                    metadata_json TEXT NOT NULL DEFAULT '{}',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY(project_name) REFERENCES projects(name),
                    FOREIGN KEY(task_id) REFERENCES tasks(id),
                    FOREIGN KEY(run_id) REFERENCES runs(id),
                    FOREIGN KEY(parent_visual_artifact_id) REFERENCES visual_artifacts(id)
                );
                """
            )
        self._ensure_project(PROJECT_NAME)
        self._ensure_task_columns()
        self._ensure_milestone_columns()
        self._ensure_approval_columns()
        self._ensure_local_exception_approval_columns()
        self._ensure_compliance_record_columns()
        self._ensure_artifact_columns()
        self._ensure_visual_artifact_columns()
        self._ensure_usage_event_columns()
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

    def _ensure_local_exception_approval_columns(self) -> None:
        local_exception_columns = {
            "approval_scope": "TEXT NOT NULL DEFAULT 'local-exception'",
            "target_role": "TEXT",
            "exact_task": "TEXT",
            "expected_output": "TEXT",
            "why_now": "TEXT",
            "risks_json": "TEXT",
            "one_shot": "INTEGER NOT NULL DEFAULT 1",
            "expires_at": "TEXT",
            "consumed_at": "TEXT",
        }
        with self._connect() as connection:
            existing = {row["name"] for row in connection.execute("PRAGMA table_info(local_exception_approvals)").fetchall()}
            if not existing:
                return
            for column_name, definition in local_exception_columns.items():
                if column_name not in existing:
                    connection.execute(f"ALTER TABLE local_exception_approvals ADD COLUMN {column_name} {definition}")

    def _ensure_compliance_record_columns(self) -> None:
        compliance_columns = {
            "record_kind": "TEXT NOT NULL DEFAULT 'breach'",
            "compliance_state": "TEXT NOT NULL DEFAULT 'breach'",
            "policy_area": "TEXT",
            "violation_type": "TEXT",
            "severity": "TEXT NOT NULL DEFAULT 'info'",
            "local_exception_approval_id": "TEXT",
            "source_role": "TEXT",
            "decision_note": "TEXT",
            "details": "TEXT NOT NULL DEFAULT ''",
            "evidence_json": "TEXT NOT NULL DEFAULT '{}'",
        }
        with self._connect() as connection:
            existing = {row["name"] for row in connection.execute("PRAGMA table_info(compliance_records)").fetchall()}
            if not existing:
                return
            for column_name, definition in compliance_columns.items():
                if column_name not in existing:
                    connection.execute(f"ALTER TABLE compliance_records ADD COLUMN {column_name} {definition}")

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

    def _ensure_visual_artifact_columns(self) -> None:
        visual_artifact_columns = {
            "lineage_root_visual_artifact_id": "TEXT",
            "locked_base_visual_artifact_id": "TEXT",
            "edit_session_id": "TEXT",
            "edit_intent": "TEXT",
            "edit_scope_json": "TEXT NOT NULL DEFAULT '{}'",
            "protected_regions_json": "TEXT NOT NULL DEFAULT '[]'",
            "mask_reference_json": "TEXT NOT NULL DEFAULT '{}'",
            "iteration_index": "INTEGER NOT NULL DEFAULT 0",
        }
        with self._connect() as connection:
            existing = {row["name"] for row in connection.execute("PRAGMA table_info(visual_artifacts)").fetchall()}
            if not existing:
                return
            for column_name, definition in visual_artifact_columns.items():
                if column_name not in existing:
                    connection.execute(f"ALTER TABLE visual_artifacts ADD COLUMN {column_name} {definition}")

    def _ensure_usage_event_columns(self) -> None:
        usage_event_columns = {
            "model": "TEXT",
            "tier": "TEXT",
            "lane": "TEXT",
            "cached_input_tokens": "INTEGER NOT NULL DEFAULT 0",
            "reasoning_tokens": "INTEGER NOT NULL DEFAULT 0",
            "estimated_cost_usd": "REAL NOT NULL DEFAULT 0",
        }
        with self._connect() as connection:
            existing = {row["name"] for row in connection.execute("PRAGMA table_info(usage_events)").fetchall()}
            if not existing:
                return
            for column_name, definition in usage_event_columns.items():
                if column_name not in existing:
                    connection.execute(f"ALTER TABLE usage_events ADD COLUMN {column_name} {definition}")

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
            "local_exception_approvals",
            "compliance_records",
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

    def _contains_media_token(self, text: str, tokens: tuple[str, ...]) -> bool:
        lowered = text.lower()
        for token in tokens:
            pattern = r"\b" + re.escape(token.lower()).replace(r"\ ", r"\s+") + r"\b"
            if re.search(pattern, lowered):
                return True
        return False

    def _media_service_families(
        self,
        project_name: str,
        *,
        task: dict[str, Any] | None = None,
        acceptance: dict[str, Any] | None = None,
        raw_request: str | None = None,
    ) -> list[str]:
        task_payload = task or {}
        acceptance_payload = acceptance if isinstance(acceptance, dict) else self._task_acceptance(task_payload)
        milestone_title = None
        milestone_id = task_payload.get("milestone_id")
        if milestone_id:
            milestone = self.get_milestone(str(milestone_id))
            if milestone is not None:
                milestone_title = str(milestone.get("title") or "")
        text = "\n".join(
            [
                str(raw_request or ""),
                str(task_payload.get("title") or ""),
                str(task_payload.get("objective") or ""),
                str(task_payload.get("details") or ""),
                str(milestone_title or ""),
                json.dumps(acceptance_payload, ensure_ascii=True, sort_keys=True),
            ]
        )
        families: list[str] = []
        if acceptance_payload.get("design_request_preview") or self._contains_media_token(
            text,
            ("visual", "design", "image", "gallery", "screen", "layout", "board", "map"),
        ):
            families.append("visual")
        if self._contains_media_token(
            text,
            ("audio", "sound", "music", "voice", "speech", "sfx"),
        ):
            families.append("audio")
        if project_name == "program-kanban" and not families and milestone_title:
            if "visual production" in milestone_title.lower():
                families.append("visual")
            if "audio production" in milestone_title.lower():
                families.append("audio")
        seen: set[str] = set()
        ordered: list[str] = []
        for family in families:
            if family in seen:
                continue
            seen.add(family)
            ordered.append(family)
        return ordered

    def media_service_contracts(
        self,
        project_name: str,
        *,
        task: dict[str, Any] | None = None,
        acceptance: dict[str, Any] | None = None,
        raw_request: str | None = None,
    ) -> list[dict[str, Any]]:
        contracts: list[dict[str, Any]] = []
        for family in self._media_service_families(
            project_name,
            task=task,
            acceptance=acceptance,
            raw_request=raw_request,
        ):
            for contract in MEDIA_SERVICE_CONTRACT_CATALOG[family]:
                contracts.append(
                    {
                        "project_name": project_name,
                        "family": family,
                        **contract,
                    }
                )
        return contracts

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

    def _next_task_id(self, connection: sqlite3.Connection, project_name: str) -> str:
        prefixes = _task_id_aliases(project_name)
        next_sequence = 1
        for row in connection.execute("SELECT id FROM tasks WHERE project_name = ?", (project_name,)).fetchall():
            sequence = _task_sequence_from_id(str(row["id"]), prefixes)
            if sequence is not None and sequence >= next_sequence:
                next_sequence = sequence + 1
        return _format_task_id(_task_id_prefix(project_name), next_sequence)

    def _normalize_imported_task_id(self, project_name: str, task_id: str) -> str:
        sequence = _task_sequence_from_id(task_id, _task_id_aliases(project_name))
        if sequence is None:
            return task_id
        return task_id

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
        now = _utc_now()
        with self._connect() as connection:
            task_id = self._next_task_id(connection, project_name)
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
        task_id = self._normalize_imported_task_id(project_name, task_id)
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
        parent_task = self.get_task(parent_task_id)
        inherited_milestone_id = parent_task.get("milestone_id") if parent_task else None
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
            milestone_id=inherited_milestone_id,
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
        title: str | None = None,
        details: str | None = None,
        objective: str | None = None,
        priority: str | None = None,
        requires_approval: bool | None = None,
        raw_request: str | None = None,
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
        if title is not None:
            task["title"] = title
        if details is not None:
            task["details"] = details
            task["description"] = details
        if objective is not None:
            task["objective"] = objective
        if priority is not None:
            task["priority"] = priority
        if requires_approval is not None:
            task["requires_approval"] = bool(requires_approval)
        if raw_request is not None:
            task["raw_request"] = raw_request
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
                SET title = ?, objective = ?, details = ?, description = ?, priority = ?, requires_approval = ?,
                    raw_request = ?, status = ?, owner_role = ?, result_summary = ?, review_notes = ?,
                    expected_artifact_path = ?, acceptance_json = ?, assigned_role = ?, review_state = ?,
                    milestone_id = ?, layer = ?, category = ?, completed_at = ?, updated_at = ?
                WHERE id = ?
                """,
                (
                    task["title"],
                    task["objective"],
                    task["details"],
                    task["description"],
                    task["priority"],
                    int(task["requires_approval"]),
                    task.get("raw_request"),
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

    def latest_run_for_task(self, task_id: str) -> dict[str, Any] | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM runs WHERE task_id = ? ORDER BY created_at DESC LIMIT 1",
                (task_id,),
            ).fetchone()
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

    def load_context_receipt(self, run_id: str) -> dict[str, Any] | None:
        team_state = self.load_team_state(run_id) or {}
        receipt = team_state.get("context_receipt")
        if not isinstance(receipt, dict):
            return None
        normalized = dict(receipt)
        for field in CONTEXT_RECEIPT_LIST_FIELDS:
            normalized[field] = _normalize_string_list(normalized.get(field))
        return normalized

    def save_context_receipt(self, run_id: str, receipt: dict[str, Any]) -> dict[str, Any]:
        run = self.get_run(run_id)
        if run is None:
            raise ValueError(f"Run not found: {run_id}")
        team_state = self.load_team_state(run_id) or {}
        merged = dict(self.load_context_receipt(run_id) or {})
        for key, value in receipt.items():
            if value is None:
                continue
            if key in CONTEXT_RECEIPT_LIST_FIELDS:
                merged[key] = _normalize_string_list(value)
            else:
                merged[key] = value
        merged.setdefault("task_id", run["task_id"])
        merged["updated_at"] = _utc_now()
        team_state["context_receipt"] = merged
        self.update_run(run_id, team_state=team_state)
        return dict(merged)

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

    def _validate_run_task_pair(self, run_id: str, task_id: str) -> tuple[dict[str, Any], dict[str, Any]]:
        run = self.get_run(run_id)
        if run is None:
            raise ValueError(f"Run not found: {run_id}")
        task = self.get_task(task_id)
        if task is None:
            raise ValueError(f"Task not found: {task_id}")
        if run["task_id"] != task_id:
            raise ValueError(f"Run and task do not align: {run_id} -> {run['task_id']} != {task_id}")
        return run, task

    def create_local_exception_approval(
        self,
        run_id: str,
        task_id: str,
        requested_by: str,
        reason: str,
        *,
        approval_scope: str = "local-exception",
        target_role: str | None = None,
        exact_task: str | None = None,
        expected_output: str | None = None,
        why_now: str | None = None,
        risks: list[str] | None = None,
        one_shot: bool = True,
        expires_at: str | None = None,
    ) -> dict[str, Any]:
        self._validate_run_task_pair(run_id, task_id)
        approval_id = _new_id("local_exception")
        now = _utc_now()
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO local_exception_approvals (
                    id, run_id, task_id, requested_by, reason, status, created_at, decided_at, decision_note,
                    approval_scope, target_role, exact_task, expected_output, why_now, risks_json, one_shot,
                    expires_at, consumed_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                    int(one_shot),
                    expires_at,
                    None,
                ),
            )
        approval = self.get_local_exception_approval(approval_id)
        if approval is None:
            raise ValueError(f"Failed to create local exception approval: {approval_id}")
        return approval

    def get_local_exception_approval(self, approval_id: str) -> dict[str, Any] | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM local_exception_approvals WHERE id = ?",
                (approval_id,),
            ).fetchone()
        return self._deserialize_local_exception_approval(row) if row else None

    def latest_local_exception_approval_for_task(self, task_id: str) -> dict[str, Any] | None:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT * FROM local_exception_approvals
                WHERE task_id = ?
                ORDER BY created_at DESC
                LIMIT 1
                """,
                (task_id,),
            ).fetchone()
        return self._deserialize_local_exception_approval(row) if row else None

    def list_local_exception_approvals(
        self,
        run_id: str | None = None,
        *,
        status: str | None = None,
        task_id: str | None = None,
    ) -> list[dict[str, Any]]:
        query = "SELECT * FROM local_exception_approvals WHERE 1 = 1"
        params: list[Any] = []
        if run_id:
            query += " AND run_id = ?"
            params.append(run_id)
        if task_id:
            query += " AND task_id = ?"
            params.append(task_id)
        if status:
            query += " AND status = ?"
            params.append(status)
        query += " ORDER BY created_at ASC"
        with self._connect() as connection:
            rows = connection.execute(query, tuple(params)).fetchall()
        return [self._deserialize_local_exception_approval(row) for row in rows]

    def decide_local_exception_approval(self, approval_id: str, decision: str, note: str | None = None) -> dict[str, Any]:
        approval = self.get_local_exception_approval(approval_id)
        if approval is None:
            raise ValueError(f"Local exception approval not found: {approval_id}")
        if approval["status"] != "pending":
            return approval
        if decision not in {"approve", "reject"}:
            raise ValueError(f"Invalid local exception decision: {decision}")
        status = "approved" if decision == "approve" else "rejected"
        decided_at = _utc_now()
        with self._connect() as connection:
            connection.execute(
                """
                UPDATE local_exception_approvals
                SET status = ?, decided_at = ?, decision_note = ?
                WHERE id = ?
                """,
                (status, decided_at, note, approval_id),
            )
        decided = self.get_local_exception_approval(approval_id)
        if decided is None:
            raise ValueError(f"Local exception approval vanished after decision: {approval_id}")
        return decided

    def record_compliance_record(
        self,
        run_id: str,
        task_id: str,
        *,
        record_kind: str,
        details: str,
        policy_area: str | None = None,
        violation_type: str | None = None,
        severity: str = "info",
        local_exception_approval_id: str | None = None,
        source_role: str | None = None,
        decision_note: str | None = None,
        evidence: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if record_kind not in COMPLIANCE_RECORD_KINDS:
            raise ValueError(f"Invalid compliance record kind: {record_kind}")
        compliance_state = COMPLIANCE_RECORD_KINDS[record_kind]
        if not details.strip():
            raise ValueError("Compliance record details are required.")
        if record_kind == "breach":
            if not policy_area:
                raise ValueError("Breach records require a policy area.")
            if not violation_type:
                raise ValueError("Breach records require a violation type.")
        if record_kind == "local_exception_approved":
            if not local_exception_approval_id:
                raise ValueError("Local exception records require a local exception approval id.")
            local_exception = self.get_local_exception_approval(local_exception_approval_id)
            if local_exception is None:
                raise ValueError(f"Local exception approval not found: {local_exception_approval_id}")
            if local_exception["status"] != "approved":
                raise ValueError("Local exception records require an approved exception.")
            if local_exception["task_id"] != task_id:
                raise ValueError("Local exception approval does not match task.")
            if local_exception["one_shot"] and local_exception.get("consumed_at"):
                raise ValueError("Local exception approval has already been consumed.")
        self._validate_run_task_pair(run_id, task_id)
        record_id = _new_id("compliance")
        consumed_at = None
        if record_kind == "local_exception_approved":
            consumed_at = _utc_now()
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO compliance_records (
                    id, run_id, task_id, record_kind, compliance_state, policy_area, violation_type, severity,
                    local_exception_approval_id, source_role, decision_note, details, evidence_json, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record_id,
                    run_id,
                    task_id,
                    record_kind,
                    compliance_state,
                    policy_area,
                    violation_type,
                    severity,
                    local_exception_approval_id,
                    source_role,
                    decision_note,
                    details,
                    _json_dumps(evidence or {}),
                    _utc_now(),
                ),
            )
            if record_kind == "local_exception_approved" and local_exception_approval_id:
                connection.execute(
                    """
                    UPDATE local_exception_approvals
                    SET consumed_at = ?
                    WHERE id = ?
                    """,
                    (consumed_at, local_exception_approval_id),
                )
        record = self.get_compliance_record(record_id)
        if record is None:
            raise ValueError(f"Failed to create compliance record: {record_id}")
        return record

    def record_breach_event(
        self,
        run_id: str,
        task_id: str,
        *,
        policy_area: str,
        violation_type: str,
        details: str,
        severity: str = "high",
        source_role: str | None = None,
        decision_note: str | None = None,
        evidence: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return self.record_compliance_record(
            run_id,
            task_id,
            record_kind="breach",
            details=details,
            policy_area=policy_area,
            violation_type=violation_type,
            severity=severity,
            source_role=source_role,
            decision_note=decision_note,
            evidence=evidence,
        )

    def get_compliance_record(self, record_id: str) -> dict[str, Any] | None:
        with self._connect() as connection:
            row = connection.execute("SELECT * FROM compliance_records WHERE id = ?", (record_id,)).fetchone()
        return self._deserialize_compliance_record(row) if row else None

    def list_compliance_records(
        self,
        run_id: str | None = None,
        *,
        task_id: str | None = None,
        record_kind: str | None = None,
    ) -> list[dict[str, Any]]:
        query = "SELECT * FROM compliance_records WHERE 1 = 1"
        params: list[Any] = []
        if run_id:
            query += " AND run_id = ?"
            params.append(run_id)
        if task_id:
            query += " AND task_id = ?"
            params.append(task_id)
        if record_kind:
            if record_kind not in COMPLIANCE_RECORD_KINDS:
                raise ValueError(f"Invalid compliance record kind filter: {record_kind}")
            query += " AND record_kind = ?"
            params.append(record_kind)
        query += " ORDER BY created_at ASC"
        with self._connect() as connection:
            rows = connection.execute(query, tuple(params)).fetchall()
        return [self._deserialize_compliance_record(row) for row in rows]

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

    def record_usage(
        self,
        run_id: str,
        task_id: str,
        *,
        source: str | None,
        prompt_tokens: int,
        completion_tokens: int,
        model: str | None = None,
        tier: str | None = None,
        lane: str | None = None,
        cached_input_tokens: int = 0,
        reasoning_tokens: int = 0,
        estimated_cost_usd: float = 0.0,
    ) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO usage_events (
                    id, run_id, task_id, source, prompt_tokens, completion_tokens,
                    model, tier, lane, cached_input_tokens, reasoning_tokens, estimated_cost_usd, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    _new_id("usage"),
                    run_id,
                    task_id,
                    source,
                    int(prompt_tokens),
                    int(completion_tokens),
                    model,
                    tier,
                    lane,
                    int(cached_input_tokens),
                    int(reasoning_tokens),
                    float(estimated_cost_usd),
                    _utc_now(),
                ),
            )

    def list_usage_events(self, run_id: str | None = None, *, task_id: str | None = None) -> list[dict[str, Any]]:
        query = "SELECT * FROM usage_events WHERE 1 = 1"
        params: list[Any] = []
        if run_id:
            query += " AND run_id = ?"
            params.append(run_id)
        if task_id:
            query += " AND task_id = ?"
            params.append(task_id)
        query += " ORDER BY created_at ASC"
        with self._connect() as connection:
            rows = connection.execute(query, tuple(params)).fetchall()
        return [dict(row) for row in rows]

    def create_execution_packet(
        self,
        *,
        authority_packet_id: str,
        authority_job_id: str,
        authority_token: str,
        authority_schema_name: str,
        authority_execution_tier: str,
        authority_execution_lane: str,
        authority_delegated_work: bool,
        priority_class: str,
        budget_max_tokens: int,
        budget_reservation_id: str | None,
        retry_limit: int,
        early_stop_rule: str,
        run_id: str | None = None,
        task_id: str | None = None,
        actual_total_tokens: int = 0,
        retry_count: int = 0,
        escalation_target: str | None = None,
        stop_reason: str | None = None,
        status: str = "queued",
    ) -> dict[str, Any]:
        now = _utc_now()
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO execution_packets (
                    authority_packet_id, authority_job_id, authority_token, authority_schema_name,
                    authority_execution_tier, authority_execution_lane, authority_delegated_work,
                    priority_class, budget_max_tokens, budget_reservation_id, retry_limit, early_stop_rule,
                    packet_id, job_id, actual_total_tokens, retry_count, escalation_target, stop_reason,
                    status, run_id, task_id, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    authority_packet_id,
                    authority_job_id,
                    authority_token,
                    authority_schema_name,
                    authority_execution_tier,
                    authority_execution_lane,
                    int(bool(authority_delegated_work)),
                    priority_class,
                    int(budget_max_tokens),
                    budget_reservation_id,
                    int(retry_limit),
                    early_stop_rule,
                    authority_packet_id,
                    authority_job_id,
                    int(actual_total_tokens),
                    int(retry_count),
                    escalation_target,
                    stop_reason,
                    status,
                    run_id,
                    task_id,
                    now,
                    now,
                ),
            )
        packet = self.get_execution_packet(authority_packet_id)
        if packet is None:
            raise ValueError(f"Failed to create execution packet: {authority_packet_id}")
        return packet

    def get_execution_packet(self, authority_packet_id: str) -> dict[str, Any] | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM execution_packets WHERE authority_packet_id = ?",
                (authority_packet_id,),
            ).fetchone()
        return self._deserialize_execution_packet(row) if row else None

    def list_execution_packets(
        self,
        *,
        authority_job_id: str | None = None,
        run_id: str | None = None,
        task_id: str | None = None,
        status: str | None = None,
    ) -> list[dict[str, Any]]:
        query = "SELECT * FROM execution_packets WHERE 1 = 1"
        params: list[Any] = []
        if authority_job_id:
            query += " AND authority_job_id = ?"
            params.append(authority_job_id)
        if run_id:
            query += " AND run_id = ?"
            params.append(run_id)
        if task_id:
            query += " AND task_id = ?"
            params.append(task_id)
        if status:
            query += " AND status = ?"
            params.append(status)
        query += " ORDER BY created_at ASC"
        with self._connect() as connection:
            rows = connection.execute(query, tuple(params)).fetchall()
        return [self._deserialize_execution_packet(row) for row in rows]

    def sync_execution_packet(
        self,
        *,
        authority_packet_id: str,
        authority_job_id: str,
        authority_token: str,
        authority_schema_name: str,
        authority_execution_tier: str,
        authority_execution_lane: str,
        authority_delegated_work: bool,
        priority_class: str,
        budget_max_tokens: int,
        budget_reservation_id: str | None,
        retry_limit: int,
        early_stop_rule: str,
        run_id: str | None = None,
        task_id: str | None = None,
        actual_total_tokens: int = 0,
        retry_count: int = 0,
        escalation_target: str | None = None,
        stop_reason: str | None = None,
        status: str = "queued",
    ) -> dict[str, Any]:
        existing = self.get_execution_packet(authority_packet_id)
        if existing is not None:
            return self.update_execution_packet(
                authority_packet_id,
                authority_job_id=authority_job_id,
                authority_token=authority_token,
                authority_schema_name=authority_schema_name,
                authority_execution_tier=authority_execution_tier,
                authority_execution_lane=authority_execution_lane,
                authority_delegated_work=authority_delegated_work,
                priority_class=priority_class,
                budget_max_tokens=budget_max_tokens,
                budget_reservation_id=budget_reservation_id,
                retry_limit=retry_limit,
                early_stop_rule=early_stop_rule,
                run_id=run_id,
                task_id=task_id,
                actual_total_tokens=actual_total_tokens,
                retry_count=retry_count,
                escalation_target=escalation_target,
                stop_reason=stop_reason,
                status=status,
            )
        return self.create_execution_packet(
            authority_packet_id=authority_packet_id,
            authority_job_id=authority_job_id,
            authority_token=authority_token,
            authority_schema_name=authority_schema_name,
            authority_execution_tier=authority_execution_tier,
            authority_execution_lane=authority_execution_lane,
            authority_delegated_work=authority_delegated_work,
            priority_class=priority_class,
            budget_max_tokens=budget_max_tokens,
            budget_reservation_id=budget_reservation_id,
            retry_limit=retry_limit,
            early_stop_rule=early_stop_rule,
            run_id=run_id,
            task_id=task_id,
            actual_total_tokens=actual_total_tokens,
            retry_count=retry_count,
            escalation_target=escalation_target,
            stop_reason=stop_reason,
            status=status,
        )

    def update_execution_packet(
        self,
        authority_packet_id: str,
        *,
        authority_job_id: str | None = None,
        authority_token: str | None = None,
        authority_schema_name: str | None = None,
        authority_execution_tier: str | None = None,
        authority_execution_lane: str | None = None,
        authority_delegated_work: bool | None = None,
        priority_class: str | None = None,
        budget_max_tokens: int | None = None,
        budget_reservation_id: str | None = None,
        retry_limit: int | None = None,
        early_stop_rule: str | None = None,
        run_id: str | None = None,
        task_id: str | None = None,
        actual_total_tokens: int | None = None,
        retry_count: int | None = None,
        escalation_target: str | None = None,
        stop_reason: str | None = None,
        status: str | None = None,
    ) -> dict[str, Any]:
        packet = self.get_execution_packet(authority_packet_id)
        if packet is None:
            raise ValueError(f"Execution packet not found: {authority_packet_id}")
        if authority_job_id is not None:
            packet["authority_job_id"] = authority_job_id
            packet["job_id"] = authority_job_id
        if authority_token is not None:
            packet["authority_token"] = authority_token
        if authority_schema_name is not None:
            packet["authority_schema_name"] = authority_schema_name
        if authority_execution_tier is not None:
            packet["authority_execution_tier"] = authority_execution_tier
        if authority_execution_lane is not None:
            packet["authority_execution_lane"] = authority_execution_lane
        if authority_delegated_work is not None:
            packet["authority_delegated_work"] = int(bool(authority_delegated_work))
        if priority_class is not None:
            packet["priority_class"] = priority_class
        if budget_max_tokens is not None:
            packet["budget_max_tokens"] = int(budget_max_tokens)
        if budget_reservation_id is not None:
            packet["budget_reservation_id"] = budget_reservation_id
        if retry_limit is not None:
            packet["retry_limit"] = int(retry_limit)
        if early_stop_rule is not None:
            packet["early_stop_rule"] = early_stop_rule
        if run_id is not None:
            packet["run_id"] = run_id
        if task_id is not None:
            packet["task_id"] = task_id
        if status is not None:
            packet["status"] = status
        if actual_total_tokens is not None:
            packet["actual_total_tokens"] = int(actual_total_tokens)
        if retry_count is not None:
            packet["retry_count"] = int(retry_count)
        if escalation_target is not None:
            packet["escalation_target"] = escalation_target
        if stop_reason is not None:
            packet["stop_reason"] = stop_reason
        packet["updated_at"] = _utc_now()
        with self._connect() as connection:
            connection.execute(
                """
                UPDATE execution_packets
                SET authority_job_id = ?, authority_token = ?, authority_schema_name = ?,
                    authority_execution_tier = ?, authority_execution_lane = ?, authority_delegated_work = ?,
                    priority_class = ?, budget_max_tokens = ?, budget_reservation_id = ?, retry_limit = ?,
                    early_stop_rule = ?, packet_id = ?, job_id = ?, actual_total_tokens = ?, retry_count = ?,
                    escalation_target = ?, stop_reason = ?, status = ?, run_id = ?, task_id = ?, updated_at = ?
                WHERE authority_packet_id = ?
                """,
                (
                    packet["authority_job_id"],
                    packet["authority_token"],
                    packet["authority_schema_name"],
                    packet["authority_execution_tier"],
                    packet["authority_execution_lane"],
                    packet["authority_delegated_work"],
                    packet["priority_class"],
                    packet["budget_max_tokens"],
                    packet["budget_reservation_id"],
                    packet["retry_limit"],
                    packet["early_stop_rule"],
                    packet["authority_packet_id"],
                    packet["authority_job_id"],
                    packet["actual_total_tokens"],
                    packet["retry_count"],
                    packet["escalation_target"],
                    packet["stop_reason"],
                    packet["status"],
                    packet.get("run_id"),
                    packet.get("task_id"),
                    packet["updated_at"],
                    authority_packet_id,
                ),
            )
        updated = self.get_execution_packet(authority_packet_id)
        if updated is None:
            raise ValueError(f"Execution packet vanished after update: {authority_packet_id}")
        return updated

    def create_execution_job_reservation(
        self,
        *,
        job_id: str,
        priority_class: str,
        reserved_max_tokens: int,
        reservation_status: str,
        run_id: str | None = None,
        task_id: str | None = None,
    ) -> dict[str, Any]:
        now = _utc_now()
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO execution_job_reservations (
                    job_id, priority_class, reserved_max_tokens, reservation_status, run_id, task_id, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    job_id,
                    priority_class,
                    int(reserved_max_tokens),
                    reservation_status,
                    run_id,
                    task_id,
                    now,
                    now,
                ),
            )
        reservation = self.get_execution_job_reservation(job_id)
        if reservation is None:
            raise ValueError(f"Failed to create execution job reservation: {job_id}")
        return reservation

    def get_execution_job_reservation(self, job_id: str) -> dict[str, Any] | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM execution_job_reservations WHERE job_id = ?",
                (job_id,),
            ).fetchone()
        return self._deserialize_execution_job_reservation(row) if row else None

    def list_execution_job_reservations(
        self,
        *,
        run_id: str | None = None,
        task_id: str | None = None,
        reservation_status: str | None = None,
    ) -> list[dict[str, Any]]:
        query = "SELECT * FROM execution_job_reservations WHERE 1 = 1"
        params: list[Any] = []
        if run_id:
            query += " AND run_id = ?"
            params.append(run_id)
        if task_id:
            query += " AND task_id = ?"
            params.append(task_id)
        if reservation_status:
            query += " AND reservation_status = ?"
            params.append(reservation_status)
        query += " ORDER BY created_at ASC"
        with self._connect() as connection:
            rows = connection.execute(query, tuple(params)).fetchall()
        return [self._deserialize_execution_job_reservation(row) for row in rows]

    def sync_execution_job_reservation(
        self,
        *,
        job_id: str,
        priority_class: str,
        reserved_max_tokens: int,
        reservation_status: str,
        run_id: str | None = None,
        task_id: str | None = None,
    ) -> dict[str, Any]:
        existing = self.get_execution_job_reservation(job_id)
        if existing is not None:
            return self.update_execution_job_reservation(
                job_id,
                priority_class=priority_class,
                reserved_max_tokens=reserved_max_tokens,
                reservation_status=reservation_status,
                run_id=run_id,
                task_id=task_id,
            )
        return self.create_execution_job_reservation(
            job_id=job_id,
            priority_class=priority_class,
            reserved_max_tokens=reserved_max_tokens,
            reservation_status=reservation_status,
            run_id=run_id,
            task_id=task_id,
        )

    def update_execution_job_reservation(
        self,
        job_id: str,
        *,
        priority_class: str | None = None,
        reserved_max_tokens: int | None = None,
        reservation_status: str | None = None,
        run_id: str | None = None,
        task_id: str | None = None,
    ) -> dict[str, Any]:
        reservation = self.get_execution_job_reservation(job_id)
        if reservation is None:
            raise ValueError(f"Execution job reservation not found: {job_id}")
        if priority_class is not None:
            reservation["priority_class"] = priority_class
        if reserved_max_tokens is not None:
            reservation["reserved_max_tokens"] = int(reserved_max_tokens)
        if reservation_status is not None:
            reservation["reservation_status"] = reservation_status
        if run_id is not None:
            reservation["run_id"] = run_id
        if task_id is not None:
            reservation["task_id"] = task_id
        reservation["updated_at"] = _utc_now()
        with self._connect() as connection:
            connection.execute(
                """
                UPDATE execution_job_reservations
                SET priority_class = ?, reserved_max_tokens = ?, reservation_status = ?, run_id = ?, task_id = ?, updated_at = ?
                WHERE job_id = ?
                """,
                (
                    reservation["priority_class"],
                    reservation["reserved_max_tokens"],
                    reservation["reservation_status"],
                    reservation.get("run_id"),
                    reservation.get("task_id"),
                    reservation["updated_at"],
                    job_id,
                ),
            )
        updated = self.get_execution_job_reservation(job_id)
        if updated is None:
            raise ValueError(f"Execution job reservation vanished after update: {job_id}")
        return updated

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

    def _normalize_visual_artifact_path(self, project_name: str, artifact_path: str) -> str:
        normalized = artifact_path.replace("\\", "/").strip()
        expected_prefix = f"projects/{project_name}/artifacts/design/"
        if not normalized.startswith(expected_prefix):
            raise ValueError(f"Visual artifacts must live under {expected_prefix}")
        return normalized

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

    def create_visual_artifact(
        self,
        project_name: str,
        task_id: str,
        *,
        artifact_path: str,
        run_id: str | None = None,
        artifact_kind: str = "image",
        provider: str | None = None,
        model: str | None = None,
        prompt_summary: str | None = None,
        revised_prompt: str | None = None,
        parent_visual_artifact_id: str | None = None,
        lineage_root_visual_artifact_id: str | None = None,
        locked_base_visual_artifact_id: str | None = None,
        edit_session_id: str | None = None,
        edit_intent: str | None = None,
        edit_scope: dict[str, Any] | None = None,
        protected_regions: list[Any] | None = None,
        mask_reference: dict[str, Any] | None = None,
        iteration_index: int = 0,
        review_state: str = "pending_review",
        selected_direction: bool = False,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        self._ensure_project(project_name)
        normalized_path = self._normalize_visual_artifact_path(project_name, artifact_path)
        file_info = self.file_metadata(normalized_path)
        visual_artifact_id = _new_id("visual")
        now = _utc_now()
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO visual_artifacts (
                    id, project_name, task_id, run_id, artifact_kind, provider, model,
                    prompt_summary, revised_prompt, parent_visual_artifact_id,
                    lineage_root_visual_artifact_id, locked_base_visual_artifact_id,
                    edit_session_id, edit_intent, edit_scope_json, protected_regions_json,
                    mask_reference_json, iteration_index, review_state, selected_direction,
                    artifact_path, artifact_sha256, bytes_written, metadata_json, created_at,
                    updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    visual_artifact_id,
                    project_name,
                    task_id,
                    run_id,
                    artifact_kind,
                    provider,
                    model,
                    prompt_summary,
                    revised_prompt,
                    parent_visual_artifact_id,
                    lineage_root_visual_artifact_id or parent_visual_artifact_id,
                    locked_base_visual_artifact_id or lineage_root_visual_artifact_id or parent_visual_artifact_id,
                    edit_session_id,
                    edit_intent,
                    _json_dumps(edit_scope or {}),
                    _json_dumps(protected_regions or []),
                    _json_dumps(mask_reference or {}),
                    int(iteration_index),
                    review_state,
                    int(selected_direction),
                    normalized_path,
                    file_info["artifact_sha256"],
                    file_info["bytes_written"],
                    _json_dumps(metadata or {}),
                    now,
                    now,
                ),
            )
        visual_artifact = self.get_visual_artifact(visual_artifact_id)
        if visual_artifact is None:
            raise ValueError(f"Failed to create visual artifact: {visual_artifact_id}")
        return visual_artifact

    def get_visual_artifact_by_path(
        self,
        project_name: str,
        artifact_path: str,
        *,
        task_id: str | None = None,
    ) -> dict[str, Any] | None:
        normalized_path = self._normalize_visual_artifact_path(project_name, artifact_path)
        query = "SELECT * FROM visual_artifacts WHERE project_name = ? AND artifact_path = ?"
        params: list[Any] = [project_name, normalized_path]
        if task_id:
            query += " AND task_id = ?"
            params.append(task_id)
        query += " ORDER BY updated_at DESC LIMIT 1"
        with self._connect() as connection:
            row = connection.execute(query, tuple(params)).fetchone()
        return self._deserialize_visual_artifact(row) if row else None

    def get_visual_artifact(self, visual_artifact_id: str) -> dict[str, Any] | None:
        with self._connect() as connection:
            row = connection.execute("SELECT * FROM visual_artifacts WHERE id = ?", (visual_artifact_id,)).fetchone()
        return self._deserialize_visual_artifact(row) if row else None

    def list_visual_artifacts(
        self,
        project_name: str,
        *,
        task_id: str | None = None,
        review_state: str | None = None,
    ) -> list[dict[str, Any]]:
        query = "SELECT * FROM visual_artifacts WHERE project_name = ?"
        params: list[Any] = [project_name]
        if task_id:
            query += " AND task_id = ?"
            params.append(task_id)
        if review_state:
            query += " AND review_state = ?"
            params.append(review_state)
        query += " ORDER BY created_at ASC"
        with self._connect() as connection:
            rows = connection.execute(query, tuple(params)).fetchall()
        return [self._deserialize_visual_artifact(row) for row in rows]

    def update_visual_artifact(
        self,
        visual_artifact_id: str,
        *,
        run_id: str | None = None,
        artifact_kind: str | None = None,
        provider: str | None = None,
        model: str | None = None,
        prompt_summary: str | None = None,
        revised_prompt: str | None = None,
        parent_visual_artifact_id: str | None = None,
        lineage_root_visual_artifact_id: str | None = None,
        locked_base_visual_artifact_id: str | None = None,
        edit_session_id: str | None = None,
        edit_intent: str | None = None,
        edit_scope: dict[str, Any] | None = None,
        protected_regions: list[Any] | None = None,
        mask_reference: dict[str, Any] | None = None,
        iteration_index: int | None = None,
        review_state: str | None = None,
        selected_direction: bool | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        artifact = self.get_visual_artifact(visual_artifact_id)
        if artifact is None:
            raise ValueError(f"Visual artifact not found: {visual_artifact_id}")
        normalized_path = self._normalize_visual_artifact_path(artifact["project_name"], artifact["artifact_path"])
        file_info = self.file_metadata(normalized_path)
        merged_metadata = dict(artifact.get("metadata") or {})
        if metadata:
            merged_metadata.update(metadata)
        if run_id is not None:
            artifact["run_id"] = run_id
        if artifact_kind is not None:
            artifact["artifact_kind"] = artifact_kind
        if provider is not None:
            artifact["provider"] = provider
        if model is not None:
            artifact["model"] = model
        if prompt_summary is not None:
            artifact["prompt_summary"] = prompt_summary
        if revised_prompt is not None:
            artifact["revised_prompt"] = revised_prompt
        if parent_visual_artifact_id is not None:
            artifact["parent_visual_artifact_id"] = parent_visual_artifact_id
        if lineage_root_visual_artifact_id is not None:
            artifact["lineage_root_visual_artifact_id"] = lineage_root_visual_artifact_id
        if locked_base_visual_artifact_id is not None:
            artifact["locked_base_visual_artifact_id"] = locked_base_visual_artifact_id
        if edit_session_id is not None:
            artifact["edit_session_id"] = edit_session_id
        if edit_intent is not None:
            artifact["edit_intent"] = edit_intent
        if edit_scope is not None:
            artifact["edit_scope_json"] = _json_dumps(edit_scope)
        if protected_regions is not None:
            artifact["protected_regions_json"] = _json_dumps(protected_regions)
        if mask_reference is not None:
            artifact["mask_reference_json"] = _json_dumps(mask_reference)
        if iteration_index is not None:
            artifact["iteration_index"] = int(iteration_index)
        if review_state is not None:
            artifact["review_state"] = review_state
        if selected_direction is not None:
            artifact["selected_direction"] = bool(selected_direction)
        artifact["artifact_sha256"] = file_info["artifact_sha256"]
        artifact["bytes_written"] = file_info["bytes_written"]
        artifact["updated_at"] = _utc_now()
        with self._connect() as connection:
            connection.execute(
                """
                UPDATE visual_artifacts
                SET run_id = ?, artifact_kind = ?, provider = ?, model = ?, prompt_summary = ?, revised_prompt = ?, parent_visual_artifact_id = ?,
                    lineage_root_visual_artifact_id = ?, locked_base_visual_artifact_id = ?, edit_session_id = ?,
                    edit_intent = ?, edit_scope_json = ?, protected_regions_json = ?, mask_reference_json = ?,
                    iteration_index = ?, review_state = ?, selected_direction = ?, artifact_sha256 = ?, bytes_written = ?,
                    metadata_json = ?, updated_at = ?
                WHERE id = ?
                """,
                (
                    artifact.get("run_id"),
                    artifact.get("artifact_kind"),
                    artifact.get("provider"),
                    artifact.get("model"),
                    artifact.get("prompt_summary"),
                    artifact.get("revised_prompt"),
                    artifact.get("parent_visual_artifact_id"),
                    artifact.get("lineage_root_visual_artifact_id"),
                    artifact.get("locked_base_visual_artifact_id"),
                    artifact.get("edit_session_id"),
                    artifact.get("edit_intent"),
                    artifact.get("edit_scope_json") or _json_dumps({}),
                    artifact.get("protected_regions_json") or _json_dumps([]),
                    artifact.get("mask_reference_json") or _json_dumps({}),
                    int(artifact.get("iteration_index") or 0),
                    artifact.get("review_state"),
                    int(artifact.get("selected_direction", False)),
                    artifact["artifact_sha256"],
                    artifact["bytes_written"],
                    _json_dumps(merged_metadata),
                    artifact["updated_at"],
                    visual_artifact_id,
                ),
            )
        updated = self.get_visual_artifact(visual_artifact_id)
        if updated is None:
            raise ValueError(f"Visual artifact vanished after update: {visual_artifact_id}")
        return updated

    def sync_visual_artifact(
        self,
        project_name: str,
        task_id: str,
        *,
        artifact_path: str,
        run_id: str | None = None,
        artifact_kind: str = "image",
        provider: str | None = None,
        model: str | None = None,
        prompt_summary: str | None = None,
        revised_prompt: str | None = None,
        parent_visual_artifact_id: str | None = None,
        lineage_root_visual_artifact_id: str | None = None,
        locked_base_visual_artifact_id: str | None = None,
        edit_session_id: str | None = None,
        edit_intent: str | None = None,
        edit_scope: dict[str, Any] | None = None,
        protected_regions: list[Any] | None = None,
        mask_reference: dict[str, Any] | None = None,
        iteration_index: int = 0,
        review_state: str = "pending_review",
        selected_direction: bool = False,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        existing = self.get_visual_artifact_by_path(project_name, artifact_path, task_id=task_id)
        if existing is not None:
            return self.update_visual_artifact(
                existing["id"],
                run_id=run_id,
                artifact_kind=artifact_kind,
                provider=provider,
                model=model,
                prompt_summary=prompt_summary,
                revised_prompt=revised_prompt,
                parent_visual_artifact_id=parent_visual_artifact_id,
                lineage_root_visual_artifact_id=lineage_root_visual_artifact_id,
                locked_base_visual_artifact_id=locked_base_visual_artifact_id,
                edit_session_id=edit_session_id,
                edit_intent=edit_intent,
                edit_scope=edit_scope,
                protected_regions=protected_regions,
                mask_reference=mask_reference,
                iteration_index=iteration_index,
                review_state=review_state,
                selected_direction=selected_direction,
                metadata=metadata,
            )
        return self.create_visual_artifact(
            project_name,
            task_id,
            artifact_path=artifact_path,
            run_id=run_id,
            artifact_kind=artifact_kind,
            provider=provider,
            model=model,
            prompt_summary=prompt_summary,
            revised_prompt=revised_prompt,
            parent_visual_artifact_id=parent_visual_artifact_id,
            lineage_root_visual_artifact_id=lineage_root_visual_artifact_id,
            locked_base_visual_artifact_id=locked_base_visual_artifact_id,
            edit_session_id=edit_session_id,
            edit_intent=edit_intent,
            edit_scope=edit_scope,
            protected_regions=protected_regions,
            mask_reference=mask_reference,
            iteration_index=iteration_index,
            review_state=review_state,
            selected_direction=selected_direction,
            metadata=metadata,
        )

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
        latest_run = self.latest_run_for_task(task_id)
        source_context_receipt = self.load_context_receipt(latest_run["id"]) if latest_run else None
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
            "source_run_id": latest_run["id"] if latest_run else None,
            "source_context_receipt": source_context_receipt,
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

    def list_restore_receipts(
        self,
        *,
        task_id: str | None = None,
        run_id: str | None = None,
        limit: int = 8,
    ) -> list[dict[str, Any]]:
        receipts: list[dict[str, Any]] = []
        for receipt_path in sorted(self.paths.restore_receipts_dir.glob("*.json")):
            try:
                receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                continue
            restored_context = receipt.get("restored_context_receipt")
            if task_id:
                restored_task_id = restored_context.get("task_id") if isinstance(restored_context, dict) else None
                if receipt.get("task_id") != task_id and restored_task_id != task_id:
                    continue
            if run_id and receipt.get("restored_run_id") != run_id and receipt.get("source_run_id") != run_id:
                continue
            receipts.append(receipt)
        receipts.sort(key=lambda item: item.get("restored_at") or "", reverse=True)
        return receipts[:limit]

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
        restored_run = self.latest_run_for_task(backup["task_id"])
        restored_context_receipt = self.load_context_receipt(restored_run["id"]) if restored_run else None
        receipt = {
            "restore_id": _new_id("restore"),
            "backup_id": backup_id,
            "task_id": backup["task_id"],
            "requested_by": requested_by,
            "restored_at": _utc_now(),
            "pre_restore_backup": pre_restore_backup,
            "store_health": self.schema_health(),
            "source_run_id": backup.get("source_run_id"),
            "source_context_receipt": backup.get("source_context_receipt"),
            "restored_run_id": restored_run["id"] if restored_run else None,
            "restored_context_receipt": restored_context_receipt,
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
        team_state = self.load_team_state(run["id"]) or {}
        context_receipt = self.load_context_receipt(run_id)
        worker_dispatch = team_state.get("worker_dispatch")
        if isinstance(worker_dispatch, dict):
            worker_dispatch = dict(worker_dispatch)
            manifest = worker_dispatch.get("manifest")
            if isinstance(manifest, dict):
                worker_dispatch["manifest"] = dict(manifest)
        else:
            worker_dispatch = None
        messages = self.list_messages(run_id)
        trace_events = [item for item in messages if item.get("record_type") == "trace"]
        message_events = [item for item in messages if item.get("record_type") == "message"]
        approvals = [approval for approval in self.list_approvals() if approval.get("run_id") == run_id]
        local_exception_approvals = [
            approval for approval in self.list_local_exception_approvals() if approval.get("run_id") == run_id
        ]
        compliance_records = self.list_compliance_records(run_id)
        restore_history = self.list_restore_receipts(task_id=run["task_id"], run_id=run_id, limit=16)
        agent_runs = self.list_agent_runs(run_id)
        artifacts = self.list_artifacts(run_id)
        validation_results = self.list_validation_results(run_id)
        usage_events = self.list_usage_events(run_id)
        execution_packets = self.list_execution_packets(run_id=run_id, task_id=run["task_id"])
        execution_job_reservations = self.list_execution_job_reservations(run_id=run_id, task_id=run["task_id"])
        delegations = self.list_delegations(run_id)
        sdk_runtime = self._sdk_runtime_summary(run, trace_events, agent_runs)
        media_service_contracts = self.media_service_contracts(run["project_name"], task=task) if task else []
        related_task_ids = [run["task_id"]]
        if task is not None:
            related_task_ids.extend(subtask["id"] for subtask in self.get_subtasks(run["task_id"]))
        visual_artifacts: list[dict[str, Any]] = []
        for related_task_id in related_task_ids:
            visual_artifacts.extend(self.list_visual_artifacts(run["project_name"], task_id=related_task_id))
        return {
            "run": run,
            "task": task,
            "project_name": run["project_name"],
            "delegations": delegations,
            "approvals": approvals,
            "local_exception_approvals": local_exception_approvals,
            "compliance_records": compliance_records,
            "context_receipt": context_receipt,
            "restore_history": restore_history,
            "worker_dispatch": worker_dispatch,
            "worker_manifest": worker_dispatch.get("manifest") if worker_dispatch else None,
            "messages": message_events,
            "trace_events": trace_events,
            "agent_runs": agent_runs,
            "artifacts": artifacts,
            "validation_results": validation_results,
            "usage_events": usage_events,
            "execution_packets": execution_packets,
            "execution_job_reservations": execution_job_reservations,
            "sdk_runtime": sdk_runtime,
            "media_service_contracts": media_service_contracts,
            "visual_artifacts": visual_artifacts,
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
                if task.get("objective"):
                    lines.append(f"- Objective: {task['objective']}")
                lines.append(f"- Details: {task['details']}")
                if task["result_summary"]:
                    lines.append(f"- Result: {task['result_summary']}")
                if task["review_notes"]:
                    lines.append(f"- Review Notes: {task['review_notes']}")
                lines.append("")
        if blocked_tasks:
            lines.extend(["## Blocked", ""])
            for task in blocked_tasks:
                milestone_title = None
                if task.get("milestone_id"):
                    milestone = self.get_milestone(task["milestone_id"])
                    if milestone:
                        milestone_title = milestone["title"]
                lines.extend(
                    [
                        f"### {task['title']}",
                        f"- ID: {task['id']}",
                        f"- Status: {task['status']}",
                        f"- Secondary State: {task['status']}",
                        f"- Owner: {task['owner_role']}",
                    ]
                )
                if task.get("assigned_role"):
                    lines.append(f"- Assigned Role: {task['assigned_role']}")
                if milestone_title:
                    lines.append(f"- Milestone: {milestone_title}")
                if task["expected_artifact_path"]:
                    lines.append(f"- Expected Artifact: {task['expected_artifact_path']}")
                if task.get("objective"):
                    lines.append(f"- Objective: {task['objective']}")
                lines.extend(
                    [
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

    def _deserialize_local_exception_approval(self, row: sqlite3.Row) -> dict[str, Any]:
        approval = dict(row)
        approval["risks"] = _json_loads(approval.get("risks_json"), default=[])
        approval["one_shot"] = bool(approval["one_shot"])
        return approval

    def _deserialize_compliance_record(self, row: sqlite3.Row) -> dict[str, Any]:
        record = dict(row)
        record["evidence"] = _json_loads(record.get("evidence_json"), default={})
        return record

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

    def _deserialize_visual_artifact(self, row: sqlite3.Row) -> dict[str, Any]:
        artifact = dict(row)
        artifact["selected_direction"] = bool(artifact["selected_direction"])
        artifact["metadata"] = _json_loads(artifact.get("metadata_json"), default={})
        artifact["edit_scope"] = _json_loads(artifact.get("edit_scope_json"), default={})
        artifact["protected_regions"] = _json_loads(artifact.get("protected_regions_json"), default=[])
        artifact["mask_reference"] = _json_loads(artifact.get("mask_reference_json"), default={})
        return artifact

    def _deserialize_execution_packet(self, row: sqlite3.Row) -> dict[str, Any]:
        packet = dict(row)
        packet["authority_delegated_work"] = bool(packet["authority_delegated_work"])
        return packet

    def _deserialize_execution_job_reservation(self, row: sqlite3.Row) -> dict[str, Any]:
        return dict(row)

    def _deserialize_validation_result(self, row: sqlite3.Row) -> dict[str, Any]:
        validation = dict(row)
        validation["checks"] = _json_loads(validation.get("checks_json"), default={})
        return validation
