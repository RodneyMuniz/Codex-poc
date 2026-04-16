from __future__ import annotations

import hashlib
import json
import re
import shutil
import sqlite3
import subprocess
import uuid
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Iterator

from sessions.governed_external_observability import (
    GovernedExternalCallRecord,
    GovernedExternalExecutionEvent,
    GovernedPreExecutionBlockRecord,
    GovernedExternalReconciliationRecord,
    determine_trust_status,
)

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
RECOVERY_CLOSEOUT_LABEL = "closeout"
RECOVERY_CHECKPOINT_TAG_PATTERN = re.compile(
    r"^(?P<project>[a-z0-9][a-z0-9-]*)-(?P<milestone>m\d+)-closeout-(?P<date>\d{4}-\d{2}-\d{2})$"
)
RECOVERY_SNAPSHOT_BRANCH_PATTERN = re.compile(
    r"^snapshot/(?P<project>[a-z0-9][a-z0-9-]*)-(?P<milestone>m\d+)-closeout-(?P<date>\d{4}-\d{2}-\d{2})$"
)
AIOFFICE_RECOVERY_AUTHORITATIVE_DOCS = (
    "projects/aioffice/execution/KANBAN.md",
    "projects/aioffice/governance/ACTIVE_STATE.md",
    "projects/aioffice/governance/DECISION_LOG.md",
    "projects/aioffice/governance/RECOVERY_AND_ROLLBACK_CONTRACT.md",
)
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
    "governed_pre_execution_blocks",
    "governed_external_call_records",
    "governed_external_reconciliation_records",
    "governed_external_call_events",
    "artifacts",
    "visual_artifacts",
    "workflow_runs",
    "stage_runs",
    "workflow_artifacts",
    "handoffs",
    "blockers",
    "question_or_assumptions",
    "orchestration_traces",
    "control_execution_packets",
    "execution_bundles",
)
CONTEXT_RECEIPT_LIST_FIELDS = (
    "accepted_assumptions",
    "blocked_questions",
    "allowed_tools",
    "allowed_paths",
    "prior_artifact_paths",
    "resume_conditions",
)
PROJECTS_TABLE_DDL = """
CREATE TABLE IF NOT EXISTS projects (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    root_path TEXT NOT NULL,
    created_at TEXT NOT NULL
);
"""


def _is_aioffice_isolated_rehearsal_workspace_root(root: Path) -> bool:
    parts = [part.lower() for part in root.parts]
    if not parts or parts[-1] != "workspace":
        return False
    for index in range(len(parts) - 3):
        if parts[index : index + 3] == ["projects", "aioffice", "artifacts"]:
            return index + 3 < len(parts) - 1
    return False


def _resolve_bootstrap_legacy_defaults(root: Path, bootstrap_legacy_defaults: bool | None) -> bool:
    if bootstrap_legacy_defaults is not None:
        return bool(bootstrap_legacy_defaults)
    return not _is_aioffice_isolated_rehearsal_workspace_root(root)


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


def _governed_external_trust_status(
    *,
    claim_status: Any,
    proof_status: Any,
    reconciliation_state: Any,
) -> str:
    normalized_claim_status = "claimed" if str(claim_status or "").strip() == "claimed" else "missing"
    normalized_proof_status = "proved" if str(proof_status or "").strip() == "proved" else "missing"
    normalized_reconciliation_state = str(reconciliation_state or "").strip() or "not_reconciled"
    if normalized_reconciliation_state not in {
        "not_reconciled",
        "reconciliation_pending",
        "reconciled",
        "reconciliation_failed",
    }:
        normalized_reconciliation_state = "not_reconciled"
    return determine_trust_status(
        claim_status=normalized_claim_status,
        proof_status=normalized_proof_status,
        reconciliation_state=normalized_reconciliation_state,
    )


def _governed_external_trust_worklist_category(
    *,
    reconciliation_state: Any,
    trust_status: Any,
) -> str | None:
    normalized_reconciliation_state = str(reconciliation_state or "").strip() or "not_reconciled"
    normalized_trust_status = str(trust_status or "").strip()
    if normalized_reconciliation_state == "reconciliation_failed":
        return "reconciliation_failed"
    if normalized_reconciliation_state == "reconciliation_pending":
        return "reconciliation_pending"
    if normalized_trust_status == "proof_captured_not_reconciled":
        return "proof_captured_not_reconciled"
    if normalized_trust_status == "trusted_reconciled":
        return "trusted_reconciled"
    return None


def _governed_external_trust_worklist_rank(category: str | None) -> int:
    if category == "reconciliation_failed":
        return 0
    if category == "reconciliation_pending":
        return 1
    if category == "proof_captured_not_reconciled":
        return 2
    if category == "trusted_reconciled":
        return 3
    return 99


def _governed_external_trust_followup_category(
    *,
    reconciliation_state: Any,
    trust_status: Any,
) -> str | None:
    category = _governed_external_trust_worklist_category(
        reconciliation_state=reconciliation_state,
        trust_status=trust_status,
    )
    return None if category == "trusted_reconciled" else category


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


def _require_non_empty_text(field_name: str, value: Any) -> str:
    text = str(value or "").strip()
    if not text:
        raise ValueError(f"{field_name} is required.")
    return text


def _require_list(field_name: str, value: Any) -> list[Any]:
    if value is None:
        raise ValueError(f"{field_name} is required.")
    if not isinstance(value, list):
        raise ValueError(f"{field_name} must be a list.")
    return list(value)


def _require_non_empty_list(field_name: str, value: Any) -> list[Any]:
    items = _require_list(field_name, value)
    if not items:
        raise ValueError(f"{field_name} must not be empty.")
    return items


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "milestone"


def _normalize_recovery_project_slug(project_name: str) -> str:
    text = _require_non_empty_text("project_name", project_name).lower()
    slug = re.sub(r"[^a-z0-9]+", "-", text).strip("-")
    if not slug:
        raise ValueError("project_name must contain at least one letter or digit.")
    return slug


def _normalize_recovery_milestone_key(milestone_key: str) -> str:
    text = _require_non_empty_text("milestone_key", milestone_key).lower()
    if not re.fullmatch(r"m\d+", text):
        raise ValueError("milestone_key must use the form M10.")
    return text


def _normalize_recovery_closeout_date(closeout_date: str) -> str:
    text = _require_non_empty_text("closeout_date", closeout_date)
    try:
        datetime.strptime(text, "%Y-%m-%d")
    except ValueError as exc:
        raise ValueError("closeout_date must use YYYY-MM-DD.") from exc
    return text


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
    @classmethod
    def ensure_project_registered(
        cls,
        repo_root: str | Path,
        project_name: str,
        *,
        root_path: str | Path | None = None,
        db_path: str | Path | None = None,
    ) -> dict[str, Any]:
        normalized_repo_root = Path(repo_root).resolve()
        database_path = (Path(db_path) if db_path else normalized_repo_root / "sessions" / "studio.db").resolve()
        resolved_root = (Path(root_path) if root_path else normalized_repo_root / "projects" / project_name).resolve()

        database_path.parent.mkdir(parents=True, exist_ok=True)
        resolved_root.mkdir(parents=True, exist_ok=True)

        connection = sqlite3.connect(database_path)
        connection.row_factory = sqlite3.Row
        try:
            connection.execute(PROJECTS_TABLE_DDL)
            existing = connection.execute(
                "SELECT id, created_at FROM projects WHERE name = ?",
                (project_name,),
            ).fetchone()
            if existing:
                connection.execute(
                    "UPDATE projects SET root_path = ? WHERE name = ?",
                    (str(resolved_root), project_name),
                )
            else:
                connection.execute(
                    "INSERT INTO projects (id, name, root_path, created_at) VALUES (?, ?, ?, ?)",
                    (_new_id("project"), project_name, str(resolved_root), _utc_now()),
                )
            connection.commit()
            row = connection.execute("SELECT * FROM projects WHERE name = ?", (project_name,)).fetchone()
        finally:
            connection.close()

        if row is None:
            raise ValueError(f"Failed to register project: {project_name}")
        return dict(row)

    def __init__(
        self,
        repo_root: str | Path | None = None,
        db_path: str | Path | None = None,
        *,
        bootstrap_legacy_defaults: bool | None = None,
    ) -> None:
        root = Path(repo_root or Path.cwd()).resolve()
        database_path = Path(db_path) if db_path else root / "sessions" / "studio.db"
        memory_dir = root / "memory"
        backups_dir = root / "sessions" / "backups"
        self.bootstrap_legacy_defaults = _resolve_bootstrap_legacy_defaults(root, bootstrap_legacy_defaults)
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
        if self.bootstrap_legacy_defaults:
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
            connection.execute(PROJECTS_TABLE_DDL)
            connection.executescript(
                """

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

                CREATE TABLE IF NOT EXISTS governed_pre_execution_blocks (
                    block_id TEXT PRIMARY KEY,
                    occurred_at TEXT NOT NULL,
                    run_id TEXT NOT NULL,
                    task_id TEXT NOT NULL,
                    task_packet_id TEXT,
                    authority_packet_id TEXT,
                    block_stage TEXT NOT NULL,
                    block_reason_code TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(run_id) REFERENCES runs(id),
                    FOREIGN KEY(task_id) REFERENCES tasks(id)
                );

                CREATE TABLE IF NOT EXISTS governed_external_call_records (
                    external_call_id TEXT PRIMARY KEY,
                    execution_group_id TEXT NOT NULL,
                    attempt_number INTEGER NOT NULL DEFAULT 1,
                    run_id TEXT NOT NULL,
                    task_packet_id TEXT NOT NULL,
                    reservation_id TEXT NOT NULL,
                    reservation_linkage_validated INTEGER NOT NULL DEFAULT 0,
                    reservation_status TEXT,
                    provider TEXT NOT NULL,
                    model TEXT NOT NULL,
                    execution_path TEXT NOT NULL,
                    execution_path_classification TEXT,
                    claim_status TEXT NOT NULL,
                    proof_status TEXT NOT NULL,
                    reconciliation_state TEXT NOT NULL DEFAULT 'not_reconciled',
                    reconciliation_checked_at TEXT,
                    reconciliation_reason_code TEXT,
                    reconciliation_evidence_source TEXT,
                    trust_status TEXT NOT NULL DEFAULT 'claim_missing',
                    budget_authority_validated INTEGER NOT NULL DEFAULT 0,
                    max_prompt_tokens INTEGER,
                    max_completion_tokens INTEGER,
                    max_total_tokens INTEGER,
                    retry_limit INTEGER,
                    observed_prompt_tokens INTEGER,
                    observed_completion_tokens INTEGER,
                    observed_total_tokens INTEGER,
                    observed_reasoning_tokens INTEGER,
                    retry_count INTEGER NOT NULL DEFAULT 0,
                    budget_stop_enforced INTEGER NOT NULL DEFAULT 0,
                    budget_stop_reason_code TEXT,
                    provider_request_id TEXT,
                    started_at TEXT NOT NULL,
                    finished_at TEXT,
                    outcome_status TEXT NOT NULL,
                    reason_code TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY(run_id) REFERENCES runs(id)
                );

                CREATE TABLE IF NOT EXISTS governed_external_reconciliation_records (
                    reconciliation_id TEXT PRIMARY KEY,
                    external_call_id TEXT NOT NULL,
                    execution_group_id TEXT NOT NULL,
                    run_id TEXT NOT NULL,
                    provider_request_id TEXT,
                    reconciliation_state TEXT NOT NULL,
                    reconciliation_checked_at TEXT NOT NULL,
                    reconciliation_reason_code TEXT,
                    reconciliation_evidence_source TEXT,
                    details_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(run_id) REFERENCES runs(id),
                    FOREIGN KEY(external_call_id) REFERENCES governed_external_call_records(external_call_id)
                );

                CREATE TABLE IF NOT EXISTS governed_external_call_events (
                    event_id TEXT PRIMARY KEY,
                    event_type TEXT NOT NULL,
                    occurred_at TEXT NOT NULL,
                    run_id TEXT NOT NULL,
                    task_packet_id TEXT NOT NULL,
                    reservation_id TEXT NOT NULL,
                    external_call_id TEXT NOT NULL,
                    source_component TEXT NOT NULL,
                    status TEXT NOT NULL,
                    reason_code TEXT,
                    data_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(run_id) REFERENCES runs(id),
                    FOREIGN KEY(external_call_id) REFERENCES governed_external_call_records(external_call_id)
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

                CREATE TABLE IF NOT EXISTS workflow_runs (
                    id TEXT PRIMARY KEY,
                    project_name TEXT NOT NULL,
                    task_id TEXT,
                    objective TEXT NOT NULL,
                    scope_json TEXT NOT NULL DEFAULT '{}',
                    authoritative_workspace_root TEXT NOT NULL,
                    current_stage TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'active',
                    review_state TEXT NOT NULL DEFAULT 'pending',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS stage_runs (
                    id TEXT PRIMARY KEY,
                    workflow_run_id TEXT NOT NULL,
                    project_name TEXT NOT NULL,
                    task_id TEXT,
                    stage_name TEXT NOT NULL,
                    attempt_number INTEGER NOT NULL DEFAULT 1,
                    status TEXT NOT NULL DEFAULT 'pending',
                    started_at TEXT,
                    completed_at TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY(workflow_run_id) REFERENCES workflow_runs(id)
                );

                CREATE TABLE IF NOT EXISTS workflow_artifacts (
                    id TEXT PRIMARY KEY,
                    workflow_run_id TEXT NOT NULL,
                    stage_run_id TEXT,
                    project_name TEXT NOT NULL,
                    task_id TEXT,
                    contract_name TEXT NOT NULL,
                    kind TEXT NOT NULL,
                    content TEXT NOT NULL,
                    proof_value TEXT NOT NULL,
                    artifact_path TEXT,
                    artifact_sha256 TEXT,
                    bytes_written INTEGER,
                    produced_by TEXT,
                    source_packet_id TEXT,
                    input_artifact_paths_json TEXT NOT NULL DEFAULT '[]',
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(workflow_run_id) REFERENCES workflow_runs(id),
                    FOREIGN KEY(stage_run_id) REFERENCES stage_runs(id)
                );

                CREATE TABLE IF NOT EXISTS handoffs (
                    id TEXT PRIMARY KEY,
                    workflow_run_id TEXT NOT NULL,
                    stage_run_id TEXT,
                    project_name TEXT NOT NULL,
                    task_id TEXT,
                    from_stage_name TEXT NOT NULL,
                    to_stage_name TEXT NOT NULL,
                    summary TEXT NOT NULL,
                    upstream_artifact_ids_json TEXT NOT NULL DEFAULT '[]',
                    status TEXT NOT NULL DEFAULT 'recorded',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY(workflow_run_id) REFERENCES workflow_runs(id),
                    FOREIGN KEY(stage_run_id) REFERENCES stage_runs(id)
                );

                CREATE TABLE IF NOT EXISTS blockers (
                    id TEXT PRIMARY KEY,
                    workflow_run_id TEXT NOT NULL,
                    stage_run_id TEXT,
                    project_name TEXT NOT NULL,
                    task_id TEXT,
                    blocker_kind TEXT NOT NULL,
                    summary TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'open',
                    resolution_note TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY(workflow_run_id) REFERENCES workflow_runs(id),
                    FOREIGN KEY(stage_run_id) REFERENCES stage_runs(id)
                );

                CREATE TABLE IF NOT EXISTS question_or_assumptions (
                    id TEXT PRIMARY KEY,
                    workflow_run_id TEXT NOT NULL,
                    stage_run_id TEXT,
                    project_name TEXT NOT NULL,
                    task_id TEXT,
                    record_type TEXT NOT NULL,
                    summary TEXT NOT NULL,
                    why_it_matters TEXT,
                    impact_or_risk TEXT,
                    unresolved_implication TEXT,
                    status TEXT NOT NULL DEFAULT 'open',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY(workflow_run_id) REFERENCES workflow_runs(id),
                    FOREIGN KEY(stage_run_id) REFERENCES stage_runs(id)
                );

                CREATE TABLE IF NOT EXISTS orchestration_traces (
                    id TEXT PRIMARY KEY,
                    workflow_run_id TEXT NOT NULL,
                    stage_run_id TEXT,
                    project_name TEXT NOT NULL,
                    task_id TEXT,
                    source TEXT,
                    event_type TEXT NOT NULL,
                    payload_json TEXT NOT NULL DEFAULT '{}',
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(workflow_run_id) REFERENCES workflow_runs(id),
                    FOREIGN KEY(stage_run_id) REFERENCES stage_runs(id)
                );

                CREATE TABLE IF NOT EXISTS control_execution_packets (
                    packet_id TEXT PRIMARY KEY,
                    project_name TEXT NOT NULL,
                    task_id TEXT NOT NULL,
                    workflow_run_id TEXT,
                    stage_run_id TEXT,
                    objective TEXT NOT NULL,
                    authoritative_workspace_root TEXT NOT NULL,
                    allowed_write_paths_json TEXT NOT NULL,
                    scratch_path TEXT,
                    forbidden_paths_json TEXT NOT NULL,
                    forbidden_actions_json TEXT NOT NULL,
                    required_artifact_outputs_json TEXT NOT NULL,
                    required_validations_json TEXT NOT NULL,
                    expected_return_bundle_contents_json TEXT NOT NULL,
                    failure_reporting_expectations_json TEXT NOT NULL,
                    packet_status TEXT NOT NULL DEFAULT 'issued',
                    issued_by TEXT,
                    provenance_note TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY(workflow_run_id) REFERENCES workflow_runs(id),
                    FOREIGN KEY(stage_run_id) REFERENCES stage_runs(id)
                );

                CREATE TABLE IF NOT EXISTS execution_bundles (
                    bundle_id TEXT PRIMARY KEY,
                    packet_id TEXT NOT NULL,
                    project_name TEXT NOT NULL,
                    task_id TEXT NOT NULL,
                    workflow_run_id TEXT,
                    stage_run_id TEXT,
                    produced_artifact_ids_json TEXT NOT NULL,
                    diff_refs_json TEXT NOT NULL,
                    commands_run_json TEXT NOT NULL,
                    test_results_json TEXT NOT NULL,
                    blocker_ids_json TEXT NOT NULL,
                    question_ids_json TEXT NOT NULL,
                    assumption_ids_json TEXT NOT NULL,
                    self_report_summary TEXT NOT NULL,
                    open_risks_json TEXT NOT NULL,
                    evidence_receipts_json TEXT NOT NULL,
                    acceptance_state TEXT NOT NULL DEFAULT 'pending_review',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY(packet_id) REFERENCES control_execution_packets(packet_id),
                    FOREIGN KEY(workflow_run_id) REFERENCES workflow_runs(id),
                    FOREIGN KEY(stage_run_id) REFERENCES stage_runs(id)
                );
                """
            )
        self._ensure_task_columns()
        self._ensure_milestone_columns()
        self._ensure_approval_columns()
        self._ensure_local_exception_approval_columns()
        self._ensure_compliance_record_columns()
        self._ensure_artifact_columns()
        self._ensure_visual_artifact_columns()
        self._ensure_usage_event_columns()
        self._ensure_governed_external_call_record_columns()
        self._ensure_governed_external_reconciliation_record_columns()
        self.migrate_legacy_approvals_file()
        if self.bootstrap_legacy_defaults:
            self._ensure_project(PROJECT_NAME)
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

    def _ensure_governed_external_call_record_columns(self) -> None:
        call_record_columns = {
            "execution_group_id": "TEXT",
            "attempt_number": "INTEGER NOT NULL DEFAULT 1",
            "reservation_linkage_validated": "INTEGER NOT NULL DEFAULT 0",
            "reservation_status": "TEXT",
            "execution_path_classification": "TEXT",
            "reconciliation_state": "TEXT NOT NULL DEFAULT 'not_reconciled'",
            "reconciliation_checked_at": "TEXT",
            "reconciliation_reason_code": "TEXT",
            "reconciliation_evidence_source": "TEXT",
            "trust_status": "TEXT NOT NULL DEFAULT 'claim_missing'",
            "budget_authority_validated": "INTEGER NOT NULL DEFAULT 0",
            "max_prompt_tokens": "INTEGER",
            "max_completion_tokens": "INTEGER",
            "max_total_tokens": "INTEGER",
            "retry_limit": "INTEGER",
            "observed_prompt_tokens": "INTEGER",
            "observed_completion_tokens": "INTEGER",
            "observed_total_tokens": "INTEGER",
            "observed_reasoning_tokens": "INTEGER",
            "retry_count": "INTEGER NOT NULL DEFAULT 0",
            "budget_stop_enforced": "INTEGER NOT NULL DEFAULT 0",
            "budget_stop_reason_code": "TEXT",
        }
        with self._connect() as connection:
            existing = {row["name"] for row in connection.execute("PRAGMA table_info(governed_external_call_records)").fetchall()}
            if not existing:
                return
            for column_name, definition in call_record_columns.items():
                if column_name not in existing:
                    connection.execute(f"ALTER TABLE governed_external_call_records ADD COLUMN {column_name} {definition}")
            connection.execute(
                """
                UPDATE governed_external_call_records
                SET execution_group_id = external_call_id
                WHERE execution_group_id IS NULL OR trim(execution_group_id) = ''
                """
            )
            connection.execute(
                """
                UPDATE governed_external_call_records
                SET attempt_number = 1
                WHERE attempt_number IS NULL OR attempt_number <= 0
                """
            )
            connection.execute(
                """
                UPDATE governed_external_call_records
                SET reconciliation_state = 'not_reconciled'
                WHERE reconciliation_state IS NULL OR trim(reconciliation_state) = ''
                """
            )
            connection.execute(
                """
                UPDATE governed_external_call_records
                SET trust_status =
                    CASE
                        WHEN trim(COALESCE(reconciliation_state, '')) = 'reconciliation_failed' THEN 'reconciliation_failed'
                        WHEN trim(COALESCE(claim_status, '')) != 'claimed' THEN 'claim_missing'
                        WHEN trim(COALESCE(proof_status, '')) = 'proved'
                             AND trim(COALESCE(reconciliation_state, '')) = 'reconciled' THEN 'trusted_reconciled'
                        WHEN trim(COALESCE(proof_status, '')) = 'proved' THEN 'proof_captured_not_reconciled'
                        ELSE 'claimed_only'
                    END
                WHERE trust_status IS NULL OR trim(trust_status) = ''
                """
            )

    def _ensure_governed_external_reconciliation_record_columns(self) -> None:
        reconciliation_columns = {
            "provider_request_id": "TEXT",
        }
        with self._connect() as connection:
            existing = {
                row["name"]
                for row in connection.execute("PRAGMA table_info(governed_external_reconciliation_records)").fetchall()
            }
            if not existing:
                return
            for column_name, definition in reconciliation_columns.items():
                if column_name not in existing:
                    connection.execute(
                        f"ALTER TABLE governed_external_reconciliation_records ADD COLUMN {column_name} {definition}"
                    )

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

    def list_runs_for_task(self, task_id: str) -> list[dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT * FROM runs WHERE task_id = ? ORDER BY created_at DESC",
                (task_id,),
            ).fetchall()
        return [dict(row) for row in rows]

    def _normalize_repo_relative_path(self, path_value: str, *, field_name: str) -> str:
        normalized = _require_non_empty_text(field_name, path_value).replace("\\", "/")
        candidate = Path(normalized)
        resolved = (candidate if candidate.is_absolute() else self.paths.repo_root / candidate).resolve()
        try:
            relative = resolved.relative_to(self.paths.repo_root)
        except ValueError as exc:
            raise ValueError(f"{field_name} must stay within the authoritative repository root.") from exc
        relative_text = relative.as_posix()
        return relative_text or "."

    def _normalize_repo_relative_paths(self, field_name: str, values: list[Any]) -> list[str]:
        normalized: list[str] = []
        seen: set[str] = set()
        for index, value in enumerate(values):
            path_text = self._normalize_repo_relative_path(str(value), field_name=f"{field_name}[{index}]")
            if path_text in seen:
                continue
            seen.add(path_text)
            normalized.append(path_text)
        if not normalized:
            raise ValueError(f"{field_name} must contain at least one path.")
        return normalized

    def _repo_relative_path_is_within(self, candidate_path: str, root_path: str) -> bool:
        try:
            Path(candidate_path).relative_to(Path(root_path))
        except ValueError:
            return False
        return True

    def _effective_packet_workflow_run_id(self, packet: dict[str, Any]) -> str | None:
        workflow_run_id = packet.get("workflow_run_id")
        if workflow_run_id:
            return workflow_run_id
        stage_run_id = packet.get("stage_run_id")
        if not stage_run_id:
            return None
        stage_run = self.get_stage_run(stage_run_id)
        if stage_run is None:
            raise ValueError(f"Packet references unknown stage run: {stage_run_id}")
        return stage_run.get("workflow_run_id")

    def _validate_packet_record_context(
        self,
        packet: dict[str, Any],
        *,
        record: dict[str, Any],
        record_kind: str,
    ) -> None:
        record_project_name = record.get("project_name")
        if record_project_name and record_project_name != packet["project_name"]:
            raise ValueError(f"{record_kind} must belong to the same project_name as the packet.")
        record_task_id = record.get("task_id")
        if record_task_id and record_task_id != packet["task_id"]:
            raise ValueError(f"{record_kind} must belong to the same task_id as the packet.")
        effective_workflow_run_id = self._effective_packet_workflow_run_id(packet)
        if effective_workflow_run_id and record.get("workflow_run_id") != effective_workflow_run_id:
            raise ValueError(f"{record_kind} must belong to the same workflow_run_id as the packet.")
        packet_stage_run_id = packet.get("stage_run_id")
        record_stage_run_id = record.get("stage_run_id")
        if packet_stage_run_id and record_stage_run_id and record_stage_run_id != packet_stage_run_id:
            raise ValueError(f"{record_kind} must not point to another stage_run_id.")

    def get_workflow_run(self, workflow_run_id: str) -> dict[str, Any] | None:
        with self._connect() as connection:
            row = connection.execute("SELECT * FROM workflow_runs WHERE id = ?", (workflow_run_id,)).fetchone()
        return self._deserialize_workflow_run(row) if row else None

    def list_workflow_runs(
        self,
        *,
        project_name: str | None = None,
        task_id: str | None = None,
        status: str | None = None,
    ) -> list[dict[str, Any]]:
        query = "SELECT * FROM workflow_runs WHERE 1 = 1"
        params: list[Any] = []
        if project_name:
            query += " AND project_name = ?"
            params.append(project_name)
        if task_id:
            query += " AND task_id = ?"
            params.append(task_id)
        if status:
            query += " AND status = ?"
            params.append(status)
        query += " ORDER BY created_at ASC"
        with self._connect() as connection:
            rows = connection.execute(query, tuple(params)).fetchall()
        return [self._deserialize_workflow_run(row) for row in rows]

    def create_workflow_run(
        self,
        project_name: str,
        *,
        task_id: str | None,
        objective: str,
        authoritative_workspace_root: str,
        current_stage: str,
        scope: dict[str, Any] | None = None,
        status: str = "active",
        review_state: str = "pending",
    ) -> dict[str, Any]:
        self._ensure_project(project_name)
        workflow_run_id = _new_id("workflow")
        now = _utc_now()
        normalized_root = self._normalize_repo_relative_path(
            authoritative_workspace_root,
            field_name="authoritative_workspace_root",
        )
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO workflow_runs (
                    id, project_name, task_id, objective, scope_json, authoritative_workspace_root,
                    current_stage, status, review_state, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    workflow_run_id,
                    project_name,
                    task_id,
                    _require_non_empty_text("objective", objective),
                    _json_dumps(scope or {}),
                    normalized_root,
                    _require_non_empty_text("current_stage", current_stage),
                    _require_non_empty_text("status", status),
                    _require_non_empty_text("review_state", review_state),
                    now,
                    now,
                ),
            )
        workflow_run = self.get_workflow_run(workflow_run_id)
        if workflow_run is None:
            raise ValueError(f"Failed to create workflow run: {workflow_run_id}")
        return workflow_run

    def get_stage_run(self, stage_run_id: str) -> dict[str, Any] | None:
        with self._connect() as connection:
            row = connection.execute("SELECT * FROM stage_runs WHERE id = ?", (stage_run_id,)).fetchone()
        return self._deserialize_stage_run(row) if row else None

    def list_stage_runs(self, workflow_run_id: str) -> list[dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT * FROM stage_runs WHERE workflow_run_id = ? ORDER BY created_at ASC",
                (workflow_run_id,),
            ).fetchall()
        return [self._deserialize_stage_run(row) for row in rows]

    def create_stage_run(
        self,
        workflow_run_id: str,
        *,
        stage_name: str,
        attempt_number: int = 1,
        status: str = "pending",
        task_id: str | None = None,
        started_at: str | None = None,
        completed_at: str | None = None,
    ) -> dict[str, Any]:
        workflow_run = self.get_workflow_run(workflow_run_id)
        if workflow_run is None:
            raise ValueError(f"Workflow run not found: {workflow_run_id}")
        stage_run_id = _new_id("stage")
        now = _utc_now()
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO stage_runs (
                    id, workflow_run_id, project_name, task_id, stage_name, attempt_number, status,
                    started_at, completed_at, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    stage_run_id,
                    workflow_run_id,
                    workflow_run["project_name"],
                    task_id if task_id is not None else workflow_run.get("task_id"),
                    _require_non_empty_text("stage_name", stage_name),
                    int(attempt_number),
                    _require_non_empty_text("status", status),
                    started_at,
                    completed_at,
                    now,
                    now,
                ),
            )
        stage_run = self.get_stage_run(stage_run_id)
        if stage_run is None:
            raise ValueError(f"Failed to create stage run: {stage_run_id}")
        return stage_run

    def create_workflow_artifact(
        self,
        project_name: str,
        *,
        workflow_run_id: str,
        contract_name: str,
        kind: str,
        content: str,
        proof_value: str,
        stage_run_id: str | None = None,
        task_id: str | None = None,
        artifact_path: str | None = None,
        produced_by: str | None = None,
        source_packet_id: str | None = None,
        input_artifact_paths: list[str] | None = None,
    ) -> dict[str, Any]:
        workflow_run = self.get_workflow_run(workflow_run_id)
        if workflow_run is None:
            raise ValueError(f"Workflow run not found: {workflow_run_id}")
        if workflow_run["project_name"] != project_name:
            raise ValueError("workflow_run project_name does not match artifact project_name.")
        if stage_run_id is not None:
            stage_run = self.get_stage_run(stage_run_id)
            if stage_run is None:
                raise ValueError(f"Stage run not found: {stage_run_id}")
            if stage_run["workflow_run_id"] != workflow_run_id:
                raise ValueError("stage_run_id must belong to the same workflow_run.")
        metadata = self._artifact_metadata(artifact_path, content) if artifact_path else {}
        normalized_artifact_path = (
            self._normalize_repo_relative_path(artifact_path, field_name="artifact_path")
            if artifact_path
            else None
        )
        normalized_inputs = [
            self._normalize_repo_relative_path(path, field_name=f"input_artifact_paths[{index}]")
            for index, path in enumerate(input_artifact_paths or [])
        ]
        artifact_id = _new_id("wf_artifact")
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO workflow_artifacts (
                    id, workflow_run_id, stage_run_id, project_name, task_id, contract_name, kind,
                    content, proof_value, artifact_path, artifact_sha256, bytes_written, produced_by,
                    source_packet_id, input_artifact_paths_json, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    artifact_id,
                    workflow_run_id,
                    stage_run_id,
                    project_name,
                    task_id if task_id is not None else workflow_run.get("task_id"),
                    _require_non_empty_text("contract_name", contract_name),
                    _require_non_empty_text("kind", kind),
                    _require_non_empty_text("content", content),
                    _require_non_empty_text("proof_value", proof_value),
                    normalized_artifact_path,
                    metadata.get("artifact_sha256"),
                    metadata.get("bytes_written") or len(content.encode("utf-8")),
                    produced_by,
                    source_packet_id,
                    _json_dumps(normalized_inputs),
                    _utc_now(),
                ),
            )
        artifact = self.get_workflow_artifact(artifact_id)
        if artifact is None:
            raise ValueError(f"Failed to create workflow artifact: {artifact_id}")
        return artifact

    def get_workflow_artifact(self, artifact_id: str) -> dict[str, Any] | None:
        with self._connect() as connection:
            row = connection.execute("SELECT * FROM workflow_artifacts WHERE id = ?", (artifact_id,)).fetchone()
        return self._deserialize_workflow_artifact(row) if row else None

    def list_workflow_artifacts(
        self,
        workflow_run_id: str,
        *,
        stage_run_id: str | None = None,
    ) -> list[dict[str, Any]]:
        query = "SELECT * FROM workflow_artifacts WHERE workflow_run_id = ?"
        params: list[Any] = [workflow_run_id]
        if stage_run_id is not None:
            query += " AND stage_run_id = ?"
            params.append(stage_run_id)
        query += " ORDER BY created_at ASC"
        with self._connect() as connection:
            rows = connection.execute(query, tuple(params)).fetchall()
        return [self._deserialize_workflow_artifact(row) for row in rows]

    def create_handoff(
        self,
        workflow_run_id: str,
        *,
        from_stage_name: str,
        to_stage_name: str,
        summary: str,
        stage_run_id: str | None = None,
        task_id: str | None = None,
        upstream_artifact_ids: list[str] | None = None,
        status: str = "recorded",
    ) -> dict[str, Any]:
        workflow_run = self.get_workflow_run(workflow_run_id)
        if workflow_run is None:
            raise ValueError(f"Workflow run not found: {workflow_run_id}")
        if stage_run_id is not None:
            stage_run = self.get_stage_run(stage_run_id)
            if stage_run is None:
                raise ValueError(f"Stage run not found: {stage_run_id}")
            if stage_run["workflow_run_id"] != workflow_run_id:
                raise ValueError("stage_run_id must belong to the same workflow_run.")
        upstream_ids = _normalize_string_list(upstream_artifact_ids)
        for artifact_id in upstream_ids:
            if self.get_workflow_artifact(artifact_id) is None:
                raise ValueError(f"Upstream artifact not found: {artifact_id}")
        handoff_id = _new_id("handoff")
        now = _utc_now()
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO handoffs (
                    id, workflow_run_id, stage_run_id, project_name, task_id, from_stage_name, to_stage_name,
                    summary, upstream_artifact_ids_json, status, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    handoff_id,
                    workflow_run_id,
                    stage_run_id,
                    workflow_run["project_name"],
                    task_id if task_id is not None else workflow_run.get("task_id"),
                    _require_non_empty_text("from_stage_name", from_stage_name),
                    _require_non_empty_text("to_stage_name", to_stage_name),
                    _require_non_empty_text("summary", summary),
                    _json_dumps(upstream_ids),
                    _require_non_empty_text("status", status),
                    now,
                    now,
                ),
            )
        handoff = self.get_handoff(handoff_id)
        if handoff is None:
            raise ValueError(f"Failed to create handoff: {handoff_id}")
        return handoff

    def get_handoff(self, handoff_id: str) -> dict[str, Any] | None:
        with self._connect() as connection:
            row = connection.execute("SELECT * FROM handoffs WHERE id = ?", (handoff_id,)).fetchone()
        return self._deserialize_handoff(row) if row else None

    def list_handoffs(self, workflow_run_id: str) -> list[dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT * FROM handoffs WHERE workflow_run_id = ? ORDER BY created_at ASC",
                (workflow_run_id,),
            ).fetchall()
        return [self._deserialize_handoff(row) for row in rows]

    def create_blocker(
        self,
        workflow_run_id: str,
        *,
        blocker_kind: str,
        summary: str,
        stage_run_id: str | None = None,
        task_id: str | None = None,
        status: str = "open",
        resolution_note: str | None = None,
    ) -> dict[str, Any]:
        workflow_run = self.get_workflow_run(workflow_run_id)
        if workflow_run is None:
            raise ValueError(f"Workflow run not found: {workflow_run_id}")
        if stage_run_id is not None:
            stage_run = self.get_stage_run(stage_run_id)
            if stage_run is None:
                raise ValueError(f"Stage run not found: {stage_run_id}")
            if stage_run["workflow_run_id"] != workflow_run_id:
                raise ValueError("stage_run_id must belong to the same workflow_run.")
        blocker_id = _new_id("blocker")
        now = _utc_now()
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO blockers (
                    id, workflow_run_id, stage_run_id, project_name, task_id, blocker_kind, summary,
                    status, resolution_note, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    blocker_id,
                    workflow_run_id,
                    stage_run_id,
                    workflow_run["project_name"],
                    task_id if task_id is not None else workflow_run.get("task_id"),
                    _require_non_empty_text("blocker_kind", blocker_kind),
                    _require_non_empty_text("summary", summary),
                    _require_non_empty_text("status", status),
                    resolution_note,
                    now,
                    now,
                ),
            )
        blocker = self.get_blocker(blocker_id)
        if blocker is None:
            raise ValueError(f"Failed to create blocker: {blocker_id}")
        return blocker

    def get_blocker(self, blocker_id: str) -> dict[str, Any] | None:
        with self._connect() as connection:
            row = connection.execute("SELECT * FROM blockers WHERE id = ?", (blocker_id,)).fetchone()
        return self._deserialize_blocker(row) if row else None

    def list_blockers(self, workflow_run_id: str) -> list[dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT * FROM blockers WHERE workflow_run_id = ? ORDER BY created_at ASC",
                (workflow_run_id,),
            ).fetchall()
        return [self._deserialize_blocker(row) for row in rows]

    def create_question_or_assumption(
        self,
        workflow_run_id: str,
        *,
        record_type: str,
        summary: str,
        stage_run_id: str | None = None,
        task_id: str | None = None,
        why_it_matters: str | None = None,
        impact_or_risk: str | None = None,
        unresolved_implication: str | None = None,
        status: str = "open",
    ) -> dict[str, Any]:
        normalized_type = _require_non_empty_text("record_type", record_type)
        if normalized_type not in {"question", "assumption"}:
            raise ValueError("record_type must be either 'question' or 'assumption'.")
        workflow_run = self.get_workflow_run(workflow_run_id)
        if workflow_run is None:
            raise ValueError(f"Workflow run not found: {workflow_run_id}")
        if stage_run_id is not None:
            stage_run = self.get_stage_run(stage_run_id)
            if stage_run is None:
                raise ValueError(f"Stage run not found: {stage_run_id}")
            if stage_run["workflow_run_id"] != workflow_run_id:
                raise ValueError("stage_run_id must belong to the same workflow_run.")
        record_id = _new_id("qa")
        now = _utc_now()
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO question_or_assumptions (
                    id, workflow_run_id, stage_run_id, project_name, task_id, record_type, summary,
                    why_it_matters, impact_or_risk, unresolved_implication, status, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record_id,
                    workflow_run_id,
                    stage_run_id,
                    workflow_run["project_name"],
                    task_id if task_id is not None else workflow_run.get("task_id"),
                    normalized_type,
                    _require_non_empty_text("summary", summary),
                    why_it_matters,
                    impact_or_risk,
                    unresolved_implication,
                    _require_non_empty_text("status", status),
                    now,
                    now,
                ),
            )
        record = self.get_question_or_assumption(record_id)
        if record is None:
            raise ValueError(f"Failed to create question_or_assumption: {record_id}")
        return record

    def get_question_or_assumption(self, record_id: str) -> dict[str, Any] | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM question_or_assumptions WHERE id = ?",
                (record_id,),
            ).fetchone()
        return self._deserialize_question_or_assumption(row) if row else None

    def list_question_or_assumptions(
        self,
        workflow_run_id: str,
        *,
        record_type: str | None = None,
    ) -> list[dict[str, Any]]:
        query = "SELECT * FROM question_or_assumptions WHERE workflow_run_id = ?"
        params: list[Any] = [workflow_run_id]
        if record_type:
            query += " AND record_type = ?"
            params.append(record_type)
        query += " ORDER BY created_at ASC"
        with self._connect() as connection:
            rows = connection.execute(query, tuple(params)).fetchall()
        return [self._deserialize_question_or_assumption(row) for row in rows]

    def record_orchestration_trace(
        self,
        workflow_run_id: str,
        *,
        event_type: str,
        stage_run_id: str | None = None,
        task_id: str | None = None,
        source: str | None = None,
        payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        workflow_run = self.get_workflow_run(workflow_run_id)
        if workflow_run is None:
            raise ValueError(f"Workflow run not found: {workflow_run_id}")
        if stage_run_id is not None:
            stage_run = self.get_stage_run(stage_run_id)
            if stage_run is None:
                raise ValueError(f"Stage run not found: {stage_run_id}")
            if stage_run["workflow_run_id"] != workflow_run_id:
                raise ValueError("stage_run_id must belong to the same workflow_run.")
        trace_id = _new_id("otrace")
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO orchestration_traces (
                    id, workflow_run_id, stage_run_id, project_name, task_id, source, event_type, payload_json, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    trace_id,
                    workflow_run_id,
                    stage_run_id,
                    workflow_run["project_name"],
                    task_id if task_id is not None else workflow_run.get("task_id"),
                    source,
                    _require_non_empty_text("event_type", event_type),
                    _json_dumps(payload or {}),
                    _utc_now(),
                ),
            )
        trace = self.get_orchestration_trace(trace_id)
        if trace is None:
            raise ValueError(f"Failed to create orchestration_trace: {trace_id}")
        return trace

    def get_orchestration_trace(self, trace_id: str) -> dict[str, Any] | None:
        with self._connect() as connection:
            row = connection.execute("SELECT * FROM orchestration_traces WHERE id = ?", (trace_id,)).fetchone()
        return self._deserialize_orchestration_trace(row) if row else None

    def list_orchestration_traces(
        self,
        workflow_run_id: str,
        *,
        stage_run_id: str | None = None,
    ) -> list[dict[str, Any]]:
        query = "SELECT * FROM orchestration_traces WHERE workflow_run_id = ?"
        params: list[Any] = [workflow_run_id]
        if stage_run_id is not None:
            query += " AND stage_run_id = ?"
            params.append(stage_run_id)
        query += " ORDER BY created_at ASC"
        with self._connect() as connection:
            rows = connection.execute(query, tuple(params)).fetchall()
        return [self._deserialize_orchestration_trace(row) for row in rows]

    def issue_control_execution_packet(
        self,
        project_name: str,
        task_id: str,
        *,
        objective: str,
        authoritative_workspace_root: str,
        allowed_write_paths: list[str],
        required_artifact_outputs: list[str],
        required_validations: list[Any],
        expected_return_bundle_contents: list[Any],
        failure_reporting_expectations: list[Any],
        workflow_run_id: str | None = None,
        stage_run_id: str | None = None,
        scratch_path: str | None = None,
        forbidden_paths: list[str] | None = None,
        forbidden_actions: list[Any] | None = None,
        issued_by: str | None = None,
        provenance_note: str | None = None,
        packet_id: str | None = None,
    ) -> dict[str, Any]:
        normalized_packet_id = packet_id or _new_id("packet")
        normalized_task_id = _require_non_empty_text("task_id", task_id)
        normalized_objective = _require_non_empty_text("objective", objective)
        normalized_root = self._normalize_repo_relative_path(
            authoritative_workspace_root,
            field_name="authoritative_workspace_root",
        )
        allowed_paths = self._normalize_repo_relative_paths(
            "allowed_write_paths",
            _require_list("allowed_write_paths", allowed_write_paths),
        )
        required_output_values = _require_list("required_artifact_outputs", required_artifact_outputs)
        required_outputs = (
            self._normalize_repo_relative_paths("required_artifact_outputs", required_output_values)
            if required_output_values
            else []
        )
        validation_items = _require_list("required_validations", required_validations)
        expected_bundle_items = _require_list(
            "expected_return_bundle_contents",
            expected_return_bundle_contents,
        )
        failure_items = _require_list(
            "failure_reporting_expectations",
            failure_reporting_expectations,
        )
        normalized_forbidden_paths = [
            self._normalize_repo_relative_path(path, field_name=f"forbidden_paths[{index}]")
            for index, path in enumerate(forbidden_paths or [])
        ]
        normalized_scratch_path = (
            self._normalize_repo_relative_path(scratch_path, field_name="scratch_path")
            if scratch_path
            else None
        )
        if workflow_run_id is not None:
            workflow_run = self.get_workflow_run(workflow_run_id)
            if workflow_run is None:
                raise ValueError(f"Workflow run not found: {workflow_run_id}")
            if workflow_run["project_name"] != project_name:
                raise ValueError("workflow_run project_name does not match packet project_name.")
            if workflow_run.get("task_id") and workflow_run["task_id"] != normalized_task_id:
                raise ValueError("workflow_run task_id does not match packet task_id.")
        if stage_run_id is not None:
            stage_run = self.get_stage_run(stage_run_id)
            if stage_run is None:
                raise ValueError(f"Stage run not found: {stage_run_id}")
            if stage_run["project_name"] != project_name:
                raise ValueError("stage_run project_name does not match packet project_name.")
            if stage_run.get("task_id") and stage_run["task_id"] != normalized_task_id:
                raise ValueError("stage_run task_id does not match packet task_id.")
            stage_workflow_run = self.get_workflow_run(stage_run["workflow_run_id"])
            if stage_workflow_run is None:
                raise ValueError(f"Workflow run not found for stage_run_id: {stage_run_id}")
            if stage_workflow_run["project_name"] != project_name:
                raise ValueError("stage_run workflow project_name does not match packet project_name.")
            if stage_workflow_run.get("task_id") and stage_workflow_run["task_id"] != normalized_task_id:
                raise ValueError("stage_run workflow task_id does not match packet task_id.")
            if workflow_run_id is not None and stage_run["workflow_run_id"] != workflow_run_id:
                raise ValueError("stage_run_id must belong to the same workflow_run.")
        now = _utc_now()
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO control_execution_packets (
                    packet_id, project_name, task_id, workflow_run_id, stage_run_id, objective,
                    authoritative_workspace_root, allowed_write_paths_json, scratch_path,
                    forbidden_paths_json, forbidden_actions_json, required_artifact_outputs_json,
                    required_validations_json, expected_return_bundle_contents_json,
                    failure_reporting_expectations_json, packet_status, issued_by, provenance_note,
                    created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    normalized_packet_id,
                    project_name,
                    normalized_task_id,
                    workflow_run_id,
                    stage_run_id,
                    normalized_objective,
                    normalized_root,
                    _json_dumps(allowed_paths),
                    normalized_scratch_path,
                    _json_dumps(normalized_forbidden_paths),
                    _json_dumps(list(forbidden_actions or [])),
                    _json_dumps(required_outputs),
                    _json_dumps(validation_items),
                    _json_dumps(expected_bundle_items),
                    _json_dumps(failure_items),
                    "issued",
                    issued_by,
                    provenance_note,
                    now,
                    now,
                ),
            )
        packet = self.get_control_execution_packet(normalized_packet_id)
        if packet is None:
            raise ValueError(f"Failed to create control execution packet: {normalized_packet_id}")
        return packet

    def get_control_execution_packet(self, packet_id: str) -> dict[str, Any] | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM control_execution_packets WHERE packet_id = ?",
                (packet_id,),
            ).fetchone()
        return self._deserialize_control_execution_packet(row) if row else None

    def list_control_execution_packets(
        self,
        *,
        project_name: str | None = None,
        task_id: str | None = None,
        workflow_run_id: str | None = None,
        stage_run_id: str | None = None,
    ) -> list[dict[str, Any]]:
        query = "SELECT * FROM control_execution_packets WHERE 1 = 1"
        params: list[Any] = []
        if project_name:
            query += " AND project_name = ?"
            params.append(project_name)
        if task_id:
            query += " AND task_id = ?"
            params.append(task_id)
        if workflow_run_id:
            query += " AND workflow_run_id = ?"
            params.append(workflow_run_id)
        if stage_run_id:
            query += " AND stage_run_id = ?"
            params.append(stage_run_id)
        query += " ORDER BY created_at ASC"
        with self._connect() as connection:
            rows = connection.execute(query, tuple(params)).fetchall()
        return [self._deserialize_control_execution_packet(row) for row in rows]

    def ingest_execution_bundle(
        self,
        packet_id: str,
        *,
        produced_artifact_ids: list[str],
        diff_refs: list[Any],
        commands_run: list[Any],
        test_results: list[Any],
        self_report_summary: str,
        open_risks: list[Any],
        evidence_receipts: list[Any],
        blocker_ids: list[str] | None = None,
        question_ids: list[str] | None = None,
        assumption_ids: list[str] | None = None,
        bundle_id: str | None = None,
    ) -> dict[str, Any]:
        packet = self.get_control_execution_packet(packet_id)
        if packet is None:
            raise ValueError(f"Control execution packet not found: {packet_id}")
        artifact_ids = _normalize_string_list(_require_list("produced_artifact_ids", produced_artifact_ids))
        diff_items = _require_list("diff_refs", diff_refs)
        command_items = _require_list("commands_run", commands_run)
        test_items = _require_list("test_results", test_results)
        blocker_id_values = _normalize_string_list(blocker_ids)
        question_id_values = _normalize_string_list(question_ids)
        assumption_id_values = _normalize_string_list(assumption_ids)
        risk_items = _require_list("open_risks", open_risks)
        receipt_items = _require_non_empty_list("evidence_receipts", evidence_receipts)
        normalized_summary = _require_non_empty_text("self_report_summary", self_report_summary)
        if packet["required_artifact_outputs"] and not artifact_ids:
            raise ValueError("produced_artifact_ids must not be empty when the packet requires artifact outputs.")
        for artifact_id in artifact_ids:
            artifact = self.get_workflow_artifact(artifact_id)
            if artifact is None:
                raise ValueError(f"Produced artifact not found: {artifact_id}")
            self._validate_packet_record_context(packet, record=artifact, record_kind="artifact")
        for blocker_id in blocker_id_values:
            blocker = self.get_blocker(blocker_id)
            if blocker is None:
                raise ValueError(f"Blocker not found: {blocker_id}")
            self._validate_packet_record_context(packet, record=blocker, record_kind="blocker")
        for question_id in question_id_values:
            record = self.get_question_or_assumption(question_id)
            if record is None:
                raise ValueError(f"Question record not found: {question_id}")
            if record["record_type"] != "question":
                raise ValueError(f"question_ids must reference question records: {question_id}")
            self._validate_packet_record_context(packet, record=record, record_kind="question")
        for assumption_id in assumption_id_values:
            record = self.get_question_or_assumption(assumption_id)
            if record is None:
                raise ValueError(f"Assumption record not found: {assumption_id}")
            if record["record_type"] != "assumption":
                raise ValueError(f"assumption_ids must reference assumption records: {assumption_id}")
            self._validate_packet_record_context(packet, record=record, record_kind="assumption")
        normalized_bundle_id = bundle_id or _new_id("bundle")
        now = _utc_now()
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO execution_bundles (
                    bundle_id, packet_id, project_name, task_id, workflow_run_id, stage_run_id,
                    produced_artifact_ids_json, diff_refs_json, commands_run_json, test_results_json,
                    blocker_ids_json, question_ids_json, assumption_ids_json, self_report_summary,
                    open_risks_json, evidence_receipts_json, acceptance_state, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    normalized_bundle_id,
                    packet_id,
                    packet["project_name"],
                    packet["task_id"],
                    packet.get("workflow_run_id"),
                    packet.get("stage_run_id"),
                    _json_dumps(artifact_ids),
                    _json_dumps(diff_items),
                    _json_dumps(command_items),
                    _json_dumps(test_items),
                    _json_dumps(blocker_id_values),
                    _json_dumps(question_id_values),
                    _json_dumps(assumption_id_values),
                    normalized_summary,
                    _json_dumps(risk_items),
                    _json_dumps(receipt_items),
                    "pending_review",
                    now,
                    now,
                ),
            )
        bundle = self.get_execution_bundle(normalized_bundle_id)
        if bundle is None:
            raise ValueError(f"Failed to ingest execution bundle: {normalized_bundle_id}")
        return bundle

    def get_execution_bundle(self, bundle_id: str) -> dict[str, Any] | None:
        with self._connect() as connection:
            row = connection.execute("SELECT * FROM execution_bundles WHERE bundle_id = ?", (bundle_id,)).fetchone()
        return self._deserialize_execution_bundle(row) if row else None

    def list_execution_bundles(
        self,
        *,
        packet_id: str | None = None,
        workflow_run_id: str | None = None,
        task_id: str | None = None,
    ) -> list[dict[str, Any]]:
        query = "SELECT * FROM execution_bundles WHERE 1 = 1"
        params: list[Any] = []
        if packet_id:
            query += " AND packet_id = ?"
            params.append(packet_id)
        if workflow_run_id:
            query += " AND workflow_run_id = ?"
            params.append(workflow_run_id)
        if task_id:
            query += " AND task_id = ?"
            params.append(task_id)
        query += " ORDER BY created_at ASC"
        with self._connect() as connection:
            rows = connection.execute(query, tuple(params)).fetchall()
        return [self._deserialize_execution_bundle(row) for row in rows]

    def execute_apply_promotion_decision(
        self,
        bundle_id: str,
        *,
        approved_decision: dict[str, Any],
        destination_mappings: list[dict[str, Any]],
    ) -> dict[str, Any]:
        bundle = self.get_execution_bundle(bundle_id)
        if bundle is None:
            raise ValueError(f"Execution bundle not found: {bundle_id}")
        if bundle["acceptance_state"] != "pending_review":
            raise ValueError("Only pending_review execution bundles can be applied or promoted.")

        if not isinstance(approved_decision, dict):
            raise ValueError("approved_decision must be a dictionary.")
        decision = _require_non_empty_text(
            "approved_decision.decision",
            str(approved_decision.get("decision") or ""),
        )
        if decision != "approved":
            raise ValueError("Apply/promotion requires an explicit approved decision input.")
        action = _require_non_empty_text(
            "approved_decision.action",
            str(approved_decision.get("action") or ""),
        )
        if action not in {"apply", "promote"}:
            raise ValueError("approved_decision.action must be either 'apply' or 'promote'.")
        approved_by = _require_non_empty_text(
            "approved_decision.approved_by",
            str(approved_decision.get("approved_by") or ""),
        )
        decision_note = approved_decision.get("decision_note")
        if decision_note is not None:
            decision_note = _require_non_empty_text(
                "approved_decision.decision_note",
                str(decision_note),
            )

        packet = self.get_control_execution_packet(bundle["packet_id"])
        if packet is None:
            raise ValueError(f"Control execution packet not found for bundle: {bundle_id}")
        if bundle["project_name"] != packet["project_name"]:
            raise ValueError("Execution bundle project_name must match the source packet.")
        if bundle["task_id"] != packet["task_id"]:
            raise ValueError("Execution bundle task_id must match the source packet.")
        packet_workflow_run_id = self._effective_packet_workflow_run_id(packet)
        if packet_workflow_run_id and bundle.get("workflow_run_id") != packet_workflow_run_id:
            raise ValueError("Execution bundle workflow_run_id must match the source packet.")
        packet_stage_run_id = packet.get("stage_run_id")
        if packet_stage_run_id and bundle.get("stage_run_id") != packet_stage_run_id:
            raise ValueError("Execution bundle stage_run_id must match the source packet.")
        if packet_workflow_run_id:
            workflow_run = self.get_workflow_run(packet_workflow_run_id)
            if workflow_run is None:
                raise ValueError(f"Workflow run not found for execution bundle: {packet_workflow_run_id}")
            if workflow_run["project_name"] != bundle["project_name"]:
                raise ValueError("Workflow run project_name must match the execution bundle.")
            if workflow_run.get("task_id") and workflow_run["task_id"] != bundle["task_id"]:
                raise ValueError("Workflow run task_id must match the execution bundle.")
        if packet_stage_run_id:
            stage_run = self.get_stage_run(packet_stage_run_id)
            if stage_run is None:
                raise ValueError(f"Stage run not found for execution bundle: {packet_stage_run_id}")
            if stage_run["project_name"] != bundle["project_name"]:
                raise ValueError("Stage run project_name must match the execution bundle.")
            if stage_run.get("task_id") and stage_run["task_id"] != bundle["task_id"]:
                raise ValueError("Stage run task_id must match the execution bundle.")
            if packet_workflow_run_id and stage_run["workflow_run_id"] != packet_workflow_run_id:
                raise ValueError("Stage run workflow_run_id must match the execution bundle workflow_run_id.")

        produced_artifact_ids = _normalize_string_list(bundle.get("produced_artifact_ids"))
        if not produced_artifact_ids:
            raise ValueError("Execution bundle must contain produced_artifact_ids before apply/promotion.")

        normalized_mappings = _require_non_empty_list("destination_mappings", destination_mappings)
        authoritative_root = packet["authoritative_workspace_root"]
        project_name = bundle["project_name"]
        artifact_root = f"projects/{project_name}/artifacts"
        governance_roots = ["governance", f"projects/{project_name}/governance"]
        planned_writes: list[dict[str, Any]] = []
        mapped_artifact_ids: set[str] = set()
        destination_paths: set[str] = set()

        for index, mapping in enumerate(normalized_mappings):
            if not isinstance(mapping, dict):
                raise ValueError(f"destination_mappings[{index}] must be a dictionary.")
            source_artifact_id = _require_non_empty_text(
                f"destination_mappings[{index}].source_artifact_id",
                str(mapping.get("source_artifact_id") or ""),
            )
            if source_artifact_id in mapped_artifact_ids:
                raise ValueError("destination_mappings must not contain duplicate source_artifact_id entries.")
            destination_path = self._normalize_repo_relative_path(
                str(mapping.get("destination_path") or ""),
                field_name=f"destination_mappings[{index}].destination_path",
            )
            if destination_path in destination_paths:
                raise ValueError("destination_mappings must not contain duplicate destination_path entries.")

            artifact = self.get_workflow_artifact(source_artifact_id)
            if artifact is None:
                raise ValueError(f"Produced artifact not found for apply/promotion: {source_artifact_id}")
            self._validate_packet_record_context(packet, record=artifact, record_kind="artifact")
            if source_artifact_id not in produced_artifact_ids:
                raise ValueError("destination_mappings must only reference produced_artifact_ids from the bundle.")

            source_artifact_path = artifact.get("artifact_path")
            if not source_artifact_path:
                raise ValueError("Apply/promotion requires produced artifacts with persisted artifact_path values.")
            if not any(
                self._repo_relative_path_is_within(source_artifact_path, allowed_path)
                for allowed_path in packet["allowed_write_paths"]
            ):
                raise ValueError("Produced artifact path must be covered by the packet allowed_write_paths.")
            if source_artifact_path == destination_path:
                raise ValueError("Apply/promotion must not reuse the non-authoritative source artifact path.")
            if not self._repo_relative_path_is_within(destination_path, authoritative_root):
                raise ValueError("destination_path must stay within the packet authoritative_workspace_root.")
            if any(
                destination_path == forbidden_root
                or self._repo_relative_path_is_within(destination_path, forbidden_root)
                for forbidden_root in governance_roots
            ):
                raise ValueError("destination_path must not target governance-controlled paths.")
            if destination_path == artifact_root or self._repo_relative_path_is_within(destination_path, artifact_root):
                raise ValueError("destination_path must not stay within the non-authoritative artifact tree.")
            if any(
                destination_path == forbidden_path
                or self._repo_relative_path_is_within(destination_path, forbidden_path)
                for forbidden_path in packet["forbidden_paths"]
            ):
                raise ValueError("destination_path must not target packet-forbidden paths.")

            source_absolute_path = (self.paths.repo_root / source_artifact_path).resolve()
            if not source_absolute_path.exists():
                raise ValueError(f"Produced artifact path does not exist on disk: {source_artifact_path}")

            mapped_artifact_ids.add(source_artifact_id)
            destination_paths.add(destination_path)
            planned_writes.append(
                {
                    "artifact": artifact,
                    "source_artifact_id": source_artifact_id,
                    "source_artifact_path": source_artifact_path,
                    "source_absolute_path": source_absolute_path,
                    "destination_path": destination_path,
                }
            )

        expected_artifact_ids = set(produced_artifact_ids)
        if mapped_artifact_ids != expected_artifact_ids:
            raise ValueError("destination_mappings must provide one explicit destination_path for each produced_artifact_id.")

        decision_captured_at = _utc_now()
        promotion_receipts: list[dict[str, Any]] = [
            {
                "kind": "apply_promotion_decision",
                "bundle_id": bundle_id,
                "decision": decision,
                "action": action,
                "approved_by": approved_by,
                "decision_note": decision_note,
                "captured_at": decision_captured_at,
            }
        ]
        for write_plan in planned_writes:
            destination_absolute_path = (self.paths.repo_root / write_plan["destination_path"]).resolve()
            destination_absolute_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(write_plan["source_absolute_path"], destination_absolute_path)
            destination_metadata = self.file_metadata(write_plan["destination_path"])
            promotion_receipts.append(
                {
                    "kind": "authoritative_destination_write",
                    "action": action,
                    "source_artifact_id": write_plan["source_artifact_id"],
                    "source_artifact_path": write_plan["source_artifact_path"],
                    "source_artifact_sha256": write_plan["artifact"].get("artifact_sha256"),
                    "destination_path": write_plan["destination_path"],
                    "destination_artifact_sha256": destination_metadata["artifact_sha256"],
                    "bytes_written": destination_metadata["bytes_written"],
                    "modified_at": destination_metadata["modified_at"],
                }
            )

        updated_evidence_receipts = list(bundle["evidence_receipts"]) + promotion_receipts
        updated_acceptance_state = "applied" if action == "apply" else "promoted"
        with self._connect() as connection:
            connection.execute(
                """
                UPDATE execution_bundles
                SET acceptance_state = ?, evidence_receipts_json = ?, updated_at = ?
                WHERE bundle_id = ?
                """,
                (
                    updated_acceptance_state,
                    _json_dumps(updated_evidence_receipts),
                    _utc_now(),
                    bundle_id,
                ),
            )
        updated_bundle = self.get_execution_bundle(bundle_id)
        if updated_bundle is None:
            raise ValueError(f"Execution bundle vanished after apply/promotion: {bundle_id}")
        return updated_bundle

    def _project_context(self, project_name: str | None) -> dict[str, Any] | None:
        if not project_name:
            return None
        project = self.get_project(str(project_name))
        if project is None:
            return None
        return {
            "id": project.get("id"),
            "name": project.get("name"),
            "root_path": project.get("root_path"),
            "created_at": project.get("created_at"),
        }

    def _milestone_context(self, milestone_id: str | None) -> dict[str, Any] | None:
        if not milestone_id:
            return None
        milestone = self.get_milestone(str(milestone_id))
        if milestone is None:
            return None
        return {
            "id": milestone.get("id"),
            "project_name": milestone.get("project_name"),
            "title": milestone.get("title"),
            "slug": milestone.get("slug"),
            "status": milestone.get("status"),
            "milestone_order": milestone.get("milestone_order"),
        }

    def _run_work_graph_context(
        self,
        run: dict[str, Any],
        task: dict[str, Any] | None,
        *,
        project: dict[str, Any] | None = None,
        milestone: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        resolved_project = project or self._project_context(
            task.get("project_name") if isinstance(task, dict) else run.get("project_name")
        )
        resolved_milestone = milestone or self._milestone_context(
            task.get("milestone_id") if isinstance(task, dict) else None
        )
        return {
            "project_id": resolved_project.get("id") if resolved_project else None,
            "project_name": (task.get("project_name") if isinstance(task, dict) else None) or run.get("project_name"),
            "milestone_id": (
                resolved_milestone.get("id")
                if resolved_milestone
                else task.get("milestone_id")
                if isinstance(task, dict)
                else None
            ),
            "milestone_title": resolved_milestone.get("title") if resolved_milestone else None,
            "task_id": run.get("task_id"),
            "task_title": task.get("title") if isinstance(task, dict) else None,
            "run_id": run.get("id"),
            "control_room_path": f"/control-room?run_id={run.get('id')}",
        }

    def _run_attention_summary(self, evidence: dict[str, Any]) -> dict[str, Any]:
        attention_items = evidence.get("governed_external_attention_items")
        pre_execution_blocks = evidence.get("governed_pre_execution_blocks")
        attention_items = attention_items if isinstance(attention_items, list) else []
        pre_execution_blocks = pre_execution_blocks if isinstance(pre_execution_blocks, list) else []
        top_attention_reason = None
        if pre_execution_blocks:
            top_attention_reason = pre_execution_blocks[0].get("block_reason_code")
        elif attention_items:
            top_attention_reason = attention_items[0].get("attention_reason")
        return {
            "attention_item_count": len(attention_items),
            "pre_observation_block_count": len(pre_execution_blocks),
            "attention_count": len(attention_items) + len(pre_execution_blocks),
            "top_attention_reason": top_attention_reason,
        }

    def _run_health_summary(self, evidence: dict[str, Any]) -> dict[str, Any]:
        governed_summary = evidence.get("governed_external_run_summary")
        governed_summary = governed_summary if isinstance(governed_summary, dict) else {}
        attention_summary = self._run_attention_summary(evidence)
        return {
            "has_attention": bool(attention_summary["attention_count"]),
            "final_success_count": int(governed_summary.get("final_success_count") or 0),
            "final_failed_count": int(governed_summary.get("final_failed_count") or 0),
            "final_budget_stopped_count": int(governed_summary.get("final_budget_stopped_count") or 0),
            "final_proof_missing_count": int(governed_summary.get("final_proof_missing_count") or 0),
            "governed_api_execution_count": int(governed_summary.get("governed_api_execution_count") or 0),
            "blocked_execution_count": int(governed_summary.get("blocked_execution_count") or 0),
            "pre_observation_block_count": int(governed_summary.get("pre_observation_block_count") or 0),
        }

    def _run_execution_summary(self, evidence: dict[str, Any]) -> dict[str, Any]:
        governed_summary = evidence.get("governed_external_run_summary")
        governed_summary = governed_summary if isinstance(governed_summary, dict) else {}
        call_records = evidence.get("governed_external_calls")
        call_records = call_records if isinstance(call_records, list) else []
        ordered_call_records = sorted(
            call_records,
            key=lambda item: (
                str(item.get("started_at") or ""),
                int(item.get("attempt_number") or 1),
                str(item.get("external_call_id") or ""),
            ),
            reverse=True,
        )
        latest_call = ordered_call_records[0] if ordered_call_records else None
        pre_execution_blocks = evidence.get("governed_pre_execution_blocks")
        pre_execution_blocks = pre_execution_blocks if isinstance(pre_execution_blocks, list) else []
        ordered_blocks = sorted(
            pre_execution_blocks,
            key=lambda item: (
                str(item.get("occurred_at") or ""),
                str(item.get("block_id") or ""),
            ),
            reverse=True,
        )
        latest_block = ordered_blocks[0] if ordered_blocks else None
        latest_execution_path = None
        latest_proof_status = None
        latest_reconciliation_state = None
        latest_reconciliation_reason_code = None
        latest_trust_status = None
        latest_outcome_status = None
        latest_reference_id = None
        if latest_call is not None:
            latest_execution_path = latest_call.get("execution_path_classification")
            latest_proof_status = latest_call.get("proof_status")
            latest_reconciliation_state = latest_call.get("reconciliation_state")
            latest_reconciliation_reason_code = latest_call.get("reconciliation_reason_code")
            latest_trust_status = latest_call.get("trust_status")
            latest_outcome_status = latest_call.get("outcome_status")
            latest_reference_id = latest_call.get("external_call_id")
        elif latest_block is not None:
            latest_execution_path = "blocked_pre_execution"
            latest_proof_status = "missing"
            latest_reconciliation_state = None
            latest_reconciliation_reason_code = None
            latest_trust_status = None
            latest_outcome_status = "blocked_pre_execution"
            latest_reference_id = latest_block.get("block_id")
        latest_trust_followup_category = _governed_external_trust_followup_category(
            reconciliation_state=latest_reconciliation_state,
            trust_status=latest_trust_status,
        )
        return {
            "execution_group_count": int(governed_summary.get("total_execution_groups") or 0),
            "governed_api_execution_count": int(governed_summary.get("governed_api_execution_count") or 0),
            "blocked_execution_count": int(governed_summary.get("blocked_execution_count") or 0),
            "pre_observation_block_count": int(governed_summary.get("pre_observation_block_count") or 0),
            "latest_execution_path_classification": latest_execution_path,
            "latest_proof_status": latest_proof_status,
            "latest_reconciliation_state": latest_reconciliation_state,
            "latest_reconciliation_reason_code": latest_reconciliation_reason_code,
            "latest_trust_status": latest_trust_status,
            "latest_trust_followup_category": latest_trust_followup_category,
            "latest_outcome_status": latest_outcome_status,
            "latest_reference_id": latest_reference_id,
        }

    def _task_trust_summary_from_linked_runs(self, runs: list[dict[str, Any]]) -> dict[str, Any]:
        latest_run_summary = runs[0] if runs else None
        latest_execution_summary = (
            latest_run_summary.get("execution_summary")
            if isinstance(latest_run_summary, dict)
            else None
        )
        latest_execution_summary = latest_execution_summary if isinstance(latest_execution_summary, dict) else {}

        highest_priority_issue = None
        reconciliation_failed_count = 0
        reconciliation_pending_count = 0
        proof_captured_not_reconciled_count = 0
        for run_summary in runs:
            execution_summary = run_summary.get("execution_summary") if isinstance(run_summary, dict) else None
            execution_summary = execution_summary if isinstance(execution_summary, dict) else {}
            category = _governed_external_trust_followup_category(
                reconciliation_state=execution_summary.get("latest_reconciliation_state"),
                trust_status=execution_summary.get("latest_trust_status"),
            )
            if category is None:
                continue
            if category == "reconciliation_failed":
                reconciliation_failed_count += 1
            elif category == "reconciliation_pending":
                reconciliation_pending_count += 1
            elif category == "proof_captured_not_reconciled":
                proof_captured_not_reconciled_count += 1
            rank = _governed_external_trust_worklist_rank(category)
            if highest_priority_issue is None or rank < highest_priority_issue["rank"]:
                highest_priority_issue = {
                    "category": category,
                    "run_id": run_summary.get("id"),
                    "trust_status": execution_summary.get("latest_trust_status"),
                    "reconciliation_state": execution_summary.get("latest_reconciliation_state"),
                    "reconciliation_reason_code": execution_summary.get("latest_reconciliation_reason_code"),
                    "rank": rank,
                }

        trust_followup_count = (
            reconciliation_failed_count + reconciliation_pending_count + proof_captured_not_reconciled_count
        )

        return {
            "trust_followup_needed": trust_followup_count > 0,
            "trust_followup_count": trust_followup_count,
            "unreconciled_run_count": trust_followup_count,
            "reconciliation_failed_count": reconciliation_failed_count,
            "reconciliation_pending_count": reconciliation_pending_count,
            "proof_captured_not_reconciled_count": proof_captured_not_reconciled_count,
            "latest_trust_status": latest_execution_summary.get("latest_trust_status"),
            "latest_reconciliation_state": latest_execution_summary.get("latest_reconciliation_state"),
            "latest_reconciliation_reason_code": latest_execution_summary.get("latest_reconciliation_reason_code"),
            "highest_priority_trust_issue": highest_priority_issue["category"] if highest_priority_issue else None,
            "highest_priority_run_id": highest_priority_issue["run_id"] if highest_priority_issue else None,
            "highest_priority_trust_status": highest_priority_issue["trust_status"] if highest_priority_issue else None,
            "highest_priority_reconciliation_state": (
                highest_priority_issue["reconciliation_state"] if highest_priority_issue else None
            ),
            "highest_priority_reconciliation_reason_code": (
                highest_priority_issue["reconciliation_reason_code"] if highest_priority_issue else None
            ),
        }

    def summarize_task_trust(self, task_id: str) -> dict[str, Any]:
        runs = [self.summarize_task_linked_run(run["id"]) for run in self.list_runs_for_task(task_id)]
        return self._task_trust_summary_from_linked_runs(runs)

    def summarize_milestone_trust(self, milestone_id: str) -> dict[str, Any]:
        milestone = self.get_milestone(milestone_id)
        if milestone is None:
            raise ValueError(f"Milestone not found: {milestone_id}")
        tasks = [task for task in self.list_tasks(milestone["project_name"]) if task.get("milestone_id") == milestone_id]
        task_trust_summaries = [self.summarize_task_trust(task["id"]) for task in tasks]

        highest_priority_trust_issue = None
        for task, trust_summary in zip(tasks, task_trust_summaries, strict=False):
            issue = trust_summary.get("highest_priority_trust_issue")
            if not issue:
                continue
            rank = _governed_external_trust_worklist_rank(issue)
            if highest_priority_trust_issue is None or rank < highest_priority_trust_issue["rank"]:
                highest_priority_trust_issue = {
                    "issue": issue,
                    "task_id": task["id"],
                    "run_id": trust_summary.get("highest_priority_run_id"),
                    "rank": rank,
                }

        return {
            "task_count": len(tasks),
            "tasks_with_trust_followup": sum(
                1 for summary in task_trust_summaries if bool(summary.get("trust_followup_needed"))
            ),
            "unreconciled_run_count": sum(
                int(summary.get("unreconciled_run_count") or 0) for summary in task_trust_summaries
            ),
            "reconciliation_failed_count": sum(
                int(summary.get("reconciliation_failed_count") or 0) for summary in task_trust_summaries
            ),
            "reconciliation_pending_count": sum(
                int(summary.get("reconciliation_pending_count") or 0) for summary in task_trust_summaries
            ),
            "proof_captured_not_reconciled_count": sum(
                int(summary.get("proof_captured_not_reconciled_count") or 0) for summary in task_trust_summaries
            ),
            "trust_followup_needed": any(bool(summary.get("trust_followup_needed")) for summary in task_trust_summaries),
            "highest_priority_trust_issue": highest_priority_trust_issue["issue"] if highest_priority_trust_issue else None,
            "highest_priority_task_id": highest_priority_trust_issue["task_id"] if highest_priority_trust_issue else None,
            "highest_priority_run_id": highest_priority_trust_issue["run_id"] if highest_priority_trust_issue else None,
        }

    def summarize_project_trust(self, project_name: str) -> dict[str, Any]:
        tasks = self.list_tasks(project_name)
        task_trust_summaries = [self.summarize_task_trust(task["id"]) for task in tasks]

        highest_priority_trust_issue = None
        for task, trust_summary in zip(tasks, task_trust_summaries, strict=False):
            issue = trust_summary.get("highest_priority_trust_issue")
            if not issue:
                continue
            rank = _governed_external_trust_worklist_rank(issue)
            if highest_priority_trust_issue is None or rank < highest_priority_trust_issue["rank"]:
                highest_priority_trust_issue = {
                    "issue": issue,
                    "task_id": task["id"],
                    "run_id": trust_summary.get("highest_priority_run_id"),
                    "rank": rank,
                }

        return {
            "task_count": len(tasks),
            "tasks_with_trust_followup": sum(
                1 for summary in task_trust_summaries if bool(summary.get("trust_followup_needed"))
            ),
            "unreconciled_run_count": sum(
                int(summary.get("unreconciled_run_count") or 0) for summary in task_trust_summaries
            ),
            "reconciliation_failed_count": sum(
                int(summary.get("reconciliation_failed_count") or 0) for summary in task_trust_summaries
            ),
            "reconciliation_pending_count": sum(
                int(summary.get("reconciliation_pending_count") or 0) for summary in task_trust_summaries
            ),
            "proof_captured_not_reconciled_count": sum(
                int(summary.get("proof_captured_not_reconciled_count") or 0) for summary in task_trust_summaries
            ),
            "trust_followup_needed": any(bool(summary.get("trust_followup_needed")) for summary in task_trust_summaries),
            "highest_priority_trust_issue": highest_priority_trust_issue["issue"] if highest_priority_trust_issue else None,
            "highest_priority_task_id": highest_priority_trust_issue["task_id"] if highest_priority_trust_issue else None,
            "highest_priority_run_id": highest_priority_trust_issue["run_id"] if highest_priority_trust_issue else None,
        }

    def summarize_task_linked_run(self, run_id: str) -> dict[str, Any]:
        evidence = self.get_run_evidence(run_id)
        run = evidence["run"]
        task = evidence.get("task")
        project = evidence.get("project")
        milestone = evidence.get("milestone")
        governed_summary = evidence.get("governed_external_run_summary")
        governed_summary = governed_summary if isinstance(governed_summary, dict) else {}
        return {
            "id": run["id"],
            "status": run.get("status"),
            "stop_reason": run.get("stop_reason"),
            "last_error": run.get("last_error"),
            "created_at": run.get("created_at"),
            "updated_at": run.get("updated_at"),
            "started_at": run.get("started_at"),
            "completed_at": run.get("completed_at"),
            **self._run_work_graph_context(run, task, project=project, milestone=milestone),
            "governed_external_run_summary": governed_summary,
            "attention_summary": self._run_attention_summary(evidence),
            "health_summary": self._run_health_summary(evidence),
            "execution_summary": self._run_execution_summary(evidence),
        }

    def get_task_work_graph(self, task_id: str) -> dict[str, Any]:
        task = self.get_task(task_id)
        if task is None:
            raise ValueError(f"Task not found: {task_id}")
        project = self._project_context(task.get("project_name"))
        milestone = self._milestone_context(task.get("milestone_id"))
        runs = [self.summarize_task_linked_run(run["id"]) for run in self.list_runs_for_task(task_id)]
        latest_run_summary = runs[0] if runs else None
        trust_summary = self._task_trust_summary_from_linked_runs(runs)
        return {
            "project": project,
            "milestone": milestone,
            "task": task,
            "linked_run_count": len(runs),
            "linked_runs": runs,
            "latest_run_summary": latest_run_summary,
            "latest_attention_summary": latest_run_summary.get("attention_summary") if latest_run_summary else None,
            "latest_health_summary": latest_run_summary.get("health_summary") if latest_run_summary else None,
            "latest_execution_summary": latest_run_summary.get("execution_summary") if latest_run_summary else None,
            "trust_summary": trust_summary,
        }

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

    def create_governed_pre_execution_block(
        self,
        *,
        run_id: str,
        task_id: str,
        task_packet_id: str | None,
        authority_packet_id: str | None,
        block_stage: str,
        block_reason_code: str,
        occurred_at: str,
        block_id: str | None = None,
    ) -> dict[str, Any]:
        record = GovernedPreExecutionBlockRecord(
            block_id=block_id or _new_id("preblock"),
            occurred_at=occurred_at,
            run_id=run_id,
            task_id=task_id,
            task_packet_id=task_packet_id,
            authority_packet_id=authority_packet_id,
            block_stage=block_stage,
            block_reason_code=block_reason_code,
        )
        payload = record.model_dump()
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO governed_pre_execution_blocks (
                    block_id, occurred_at, run_id, task_id, task_packet_id, authority_packet_id,
                    block_stage, block_reason_code, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    payload["block_id"],
                    payload["occurred_at"],
                    payload["run_id"],
                    payload["task_id"],
                    payload["task_packet_id"],
                    payload["authority_packet_id"],
                    payload["block_stage"],
                    payload["block_reason_code"],
                    _utc_now(),
                ),
            )
        created = self.get_governed_pre_execution_block(payload["block_id"])
        if created is None:
            raise ValueError(f"Failed to create governed pre-execution block: {payload['block_id']}")
        return created

    def get_governed_pre_execution_block(self, block_id: str) -> dict[str, Any] | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM governed_pre_execution_blocks WHERE block_id = ?",
                (block_id,),
            ).fetchone()
        return self._deserialize_governed_pre_execution_block(row) if row else None

    def list_governed_pre_execution_blocks(
        self,
        *,
        run_id: str | None = None,
        task_id: str | None = None,
    ) -> list[dict[str, Any]]:
        query = "SELECT * FROM governed_pre_execution_blocks WHERE 1 = 1"
        params: list[Any] = []
        if run_id:
            query += " AND run_id = ?"
            params.append(run_id)
        if task_id:
            query += " AND task_id = ?"
            params.append(task_id)
        query += " ORDER BY occurred_at ASC, created_at ASC"
        with self._connect() as connection:
            rows = connection.execute(query, tuple(params)).fetchall()
        return [self._deserialize_governed_pre_execution_block(row) for row in rows]

    def _validated_governed_external_call_payload(self, record: dict[str, Any]) -> dict[str, Any]:
        payload = dict(record)
        payload["reconciliation_state"] = str(payload.get("reconciliation_state") or "").strip() or "not_reconciled"
        payload["trust_status"] = _governed_external_trust_status(
            claim_status=payload.get("claim_status"),
            proof_status=payload.get("proof_status"),
            reconciliation_state=payload.get("reconciliation_state"),
        )
        return GovernedExternalCallRecord.model_validate(payload).model_dump()

    def create_governed_external_call_record(
        self,
        *,
        external_call_id: str,
        execution_group_id: str,
        attempt_number: int = 1,
        run_id: str,
        task_packet_id: str,
        reservation_id: str,
        reservation_linkage_validated: bool = False,
        reservation_status: str | None = None,
        provider: str,
        model: str,
        execution_path: str,
        execution_path_classification: str = "blocked_pre_execution",
        claim_status: str,
        proof_status: str,
        reconciliation_state: str = "not_reconciled",
        reconciliation_checked_at: str | None = None,
        reconciliation_reason_code: str | None = None,
        reconciliation_evidence_source: str | None = None,
        budget_authority_validated: bool = False,
        max_prompt_tokens: int | None = None,
        max_completion_tokens: int | None = None,
        max_total_tokens: int | None = None,
        retry_limit: int | None = None,
        observed_prompt_tokens: int | None = None,
        observed_completion_tokens: int | None = None,
        observed_total_tokens: int | None = None,
        observed_reasoning_tokens: int | None = None,
        retry_count: int = 0,
        budget_stop_enforced: bool = False,
        budget_stop_reason_code: str | None = None,
        provider_request_id: str | None = None,
        started_at: str,
        finished_at: str | None = None,
        outcome_status: str,
        reason_code: str | None = None,
    ) -> dict[str, Any]:
        payload = self._validated_governed_external_call_payload(
            {
                "external_call_id": external_call_id,
                "execution_group_id": execution_group_id,
                "attempt_number": attempt_number,
                "run_id": run_id,
                "task_packet_id": task_packet_id,
                "reservation_id": reservation_id,
                "reservation_linkage_validated": reservation_linkage_validated,
                "reservation_status": reservation_status,
                "provider": provider,
                "model": model,
                "execution_path": execution_path,
                "execution_path_classification": execution_path_classification,
                "claim_status": claim_status,
                "proof_status": proof_status,
                "reconciliation_state": reconciliation_state,
                "reconciliation_checked_at": reconciliation_checked_at,
                "reconciliation_reason_code": reconciliation_reason_code,
                "reconciliation_evidence_source": reconciliation_evidence_source,
                "budget_authority_validated": budget_authority_validated,
                "max_prompt_tokens": max_prompt_tokens,
                "max_completion_tokens": max_completion_tokens,
                "max_total_tokens": max_total_tokens,
                "retry_limit": retry_limit,
                "observed_prompt_tokens": observed_prompt_tokens,
                "observed_completion_tokens": observed_completion_tokens,
                "observed_total_tokens": observed_total_tokens,
                "observed_reasoning_tokens": observed_reasoning_tokens,
                "retry_count": retry_count,
                "budget_stop_enforced": budget_stop_enforced,
                "budget_stop_reason_code": budget_stop_reason_code,
                "provider_request_id": provider_request_id,
                "started_at": started_at,
                "finished_at": finished_at,
                "outcome_status": outcome_status,
                "reason_code": reason_code,
            }
        )
        now = _utc_now()
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO governed_external_call_records (
                    external_call_id, execution_group_id, attempt_number, run_id, task_packet_id, reservation_id, reservation_linkage_validated,
                    reservation_status, provider, model, execution_path, execution_path_classification, claim_status, proof_status,
                    reconciliation_state, reconciliation_checked_at, reconciliation_reason_code, reconciliation_evidence_source, trust_status,
                    budget_authority_validated, max_prompt_tokens, max_completion_tokens, max_total_tokens,
                    retry_limit, observed_prompt_tokens, observed_completion_tokens, observed_total_tokens,
                    observed_reasoning_tokens, retry_count, budget_stop_enforced, budget_stop_reason_code,
                    provider_request_id, started_at, finished_at, outcome_status, reason_code, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    payload["external_call_id"],
                    payload["execution_group_id"],
                    payload["attempt_number"],
                    payload["run_id"],
                    payload["task_packet_id"],
                    payload["reservation_id"],
                    payload["reservation_linkage_validated"],
                    payload["reservation_status"],
                    payload["provider"],
                    payload["model"],
                    payload["execution_path"],
                    payload["execution_path_classification"],
                    payload["claim_status"],
                    payload["proof_status"],
                    payload["reconciliation_state"],
                    payload["reconciliation_checked_at"],
                    payload["reconciliation_reason_code"],
                    payload["reconciliation_evidence_source"],
                    payload["trust_status"],
                    payload["budget_authority_validated"],
                    payload["max_prompt_tokens"],
                    payload["max_completion_tokens"],
                    payload["max_total_tokens"],
                    payload["retry_limit"],
                    payload["observed_prompt_tokens"],
                    payload["observed_completion_tokens"],
                    payload["observed_total_tokens"],
                    payload["observed_reasoning_tokens"],
                    payload["retry_count"],
                    payload["budget_stop_enforced"],
                    payload["budget_stop_reason_code"],
                    payload["provider_request_id"],
                    payload["started_at"],
                    payload["finished_at"],
                    payload["outcome_status"],
                    payload["reason_code"],
                    now,
                    now,
                ),
            )
        created = self.get_governed_external_call_record(external_call_id)
        if created is None:
            raise ValueError(f"Failed to create governed external call record: {external_call_id}")
        return created

    def get_governed_external_call_record(self, external_call_id: str) -> dict[str, Any] | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM governed_external_call_records WHERE external_call_id = ?",
                (external_call_id,),
            ).fetchone()
        return self._deserialize_governed_external_call_record(row) if row else None

    def list_governed_external_call_records(
        self,
        *,
        run_id: str | None = None,
        reservation_id: str | None = None,
        task_packet_id: str | None = None,
    ) -> list[dict[str, Any]]:
        query = "SELECT * FROM governed_external_call_records WHERE 1 = 1"
        params: list[Any] = []
        if run_id:
            query += " AND run_id = ?"
            params.append(run_id)
        if reservation_id:
            query += " AND reservation_id = ?"
            params.append(reservation_id)
        if task_packet_id:
            query += " AND task_packet_id = ?"
            params.append(task_packet_id)
        query += " ORDER BY created_at ASC"
        with self._connect() as connection:
            rows = connection.execute(query, tuple(params)).fetchall()
        return [self._deserialize_governed_external_call_record(row) for row in rows]

    def sync_governed_external_call_record(
        self,
        *,
        external_call_id: str,
        execution_group_id: str,
        attempt_number: int = 1,
        run_id: str,
        task_packet_id: str,
        reservation_id: str,
        reservation_linkage_validated: bool = False,
        reservation_status: str | None = None,
        provider: str,
        model: str,
        execution_path: str,
        execution_path_classification: str = "blocked_pre_execution",
        claim_status: str,
        proof_status: str,
        reconciliation_state: str = "not_reconciled",
        reconciliation_checked_at: str | None = None,
        reconciliation_reason_code: str | None = None,
        reconciliation_evidence_source: str | None = None,
        budget_authority_validated: bool = False,
        max_prompt_tokens: int | None = None,
        max_completion_tokens: int | None = None,
        max_total_tokens: int | None = None,
        retry_limit: int | None = None,
        observed_prompt_tokens: int | None = None,
        observed_completion_tokens: int | None = None,
        observed_total_tokens: int | None = None,
        observed_reasoning_tokens: int | None = None,
        retry_count: int = 0,
        budget_stop_enforced: bool = False,
        budget_stop_reason_code: str | None = None,
        provider_request_id: str | None = None,
        started_at: str,
        finished_at: str | None = None,
        outcome_status: str,
        reason_code: str | None = None,
    ) -> dict[str, Any]:
        existing = self.get_governed_external_call_record(external_call_id)
        if existing is not None:
            return self.update_governed_external_call_record(
                external_call_id,
                execution_group_id=execution_group_id,
                attempt_number=attempt_number,
                run_id=run_id,
                task_packet_id=task_packet_id,
                reservation_id=reservation_id,
                reservation_linkage_validated=reservation_linkage_validated,
                reservation_status=reservation_status,
                provider=provider,
                model=model,
                execution_path=execution_path,
                execution_path_classification=execution_path_classification,
                claim_status=claim_status,
                proof_status=proof_status,
                reconciliation_state=reconciliation_state,
                reconciliation_checked_at=reconciliation_checked_at,
                reconciliation_reason_code=reconciliation_reason_code,
                reconciliation_evidence_source=reconciliation_evidence_source,
                budget_authority_validated=budget_authority_validated,
                max_prompt_tokens=max_prompt_tokens,
                max_completion_tokens=max_completion_tokens,
                max_total_tokens=max_total_tokens,
                retry_limit=retry_limit,
                observed_prompt_tokens=observed_prompt_tokens,
                observed_completion_tokens=observed_completion_tokens,
                observed_total_tokens=observed_total_tokens,
                observed_reasoning_tokens=observed_reasoning_tokens,
                retry_count=retry_count,
                budget_stop_enforced=budget_stop_enforced,
                budget_stop_reason_code=budget_stop_reason_code,
                provider_request_id=provider_request_id,
                started_at=started_at,
                finished_at=finished_at,
                outcome_status=outcome_status,
                reason_code=reason_code,
            )
        return self.create_governed_external_call_record(
            external_call_id=external_call_id,
            execution_group_id=execution_group_id,
            attempt_number=attempt_number,
            run_id=run_id,
            task_packet_id=task_packet_id,
            reservation_id=reservation_id,
            reservation_linkage_validated=reservation_linkage_validated,
            reservation_status=reservation_status,
            provider=provider,
            model=model,
            execution_path=execution_path,
            execution_path_classification=execution_path_classification,
            claim_status=claim_status,
            proof_status=proof_status,
            reconciliation_state=reconciliation_state,
            reconciliation_checked_at=reconciliation_checked_at,
            reconciliation_reason_code=reconciliation_reason_code,
            reconciliation_evidence_source=reconciliation_evidence_source,
            budget_authority_validated=budget_authority_validated,
            max_prompt_tokens=max_prompt_tokens,
            max_completion_tokens=max_completion_tokens,
            max_total_tokens=max_total_tokens,
            retry_limit=retry_limit,
            observed_prompt_tokens=observed_prompt_tokens,
            observed_completion_tokens=observed_completion_tokens,
            observed_total_tokens=observed_total_tokens,
            observed_reasoning_tokens=observed_reasoning_tokens,
            retry_count=retry_count,
            budget_stop_enforced=budget_stop_enforced,
            budget_stop_reason_code=budget_stop_reason_code,
            provider_request_id=provider_request_id,
            started_at=started_at,
            finished_at=finished_at,
            outcome_status=outcome_status,
            reason_code=reason_code,
        )

    def update_governed_external_call_record(
        self,
        external_call_id: str,
        *,
        execution_group_id: str | None = None,
        attempt_number: int | None = None,
        run_id: str | None = None,
        task_packet_id: str | None = None,
        reservation_id: str | None = None,
        reservation_linkage_validated: bool | None = None,
        reservation_status: str | None = None,
        provider: str | None = None,
        model: str | None = None,
        execution_path: str | None = None,
        execution_path_classification: str | None = None,
        claim_status: str | None = None,
        proof_status: str | None = None,
        reconciliation_state: str | None = None,
        reconciliation_checked_at: str | None = None,
        reconciliation_reason_code: str | None = None,
        reconciliation_evidence_source: str | None = None,
        budget_authority_validated: bool | None = None,
        max_prompt_tokens: int | None = None,
        max_completion_tokens: int | None = None,
        max_total_tokens: int | None = None,
        retry_limit: int | None = None,
        observed_prompt_tokens: int | None = None,
        observed_completion_tokens: int | None = None,
        observed_total_tokens: int | None = None,
        observed_reasoning_tokens: int | None = None,
        retry_count: int | None = None,
        budget_stop_enforced: bool | None = None,
        budget_stop_reason_code: str | None = None,
        provider_request_id: str | None = None,
        started_at: str | None = None,
        finished_at: str | None = None,
        outcome_status: str | None = None,
        reason_code: str | None = None,
    ) -> dict[str, Any]:
        record = self.get_governed_external_call_record(external_call_id)
        if record is None:
            raise ValueError(f"Governed external call record not found: {external_call_id}")
        if execution_group_id is not None:
            record["execution_group_id"] = execution_group_id
        if attempt_number is not None:
            record["attempt_number"] = attempt_number
        if run_id is not None:
            record["run_id"] = run_id
        if task_packet_id is not None:
            record["task_packet_id"] = task_packet_id
        if reservation_id is not None:
            record["reservation_id"] = reservation_id
        if reservation_linkage_validated is not None:
            record["reservation_linkage_validated"] = reservation_linkage_validated
        if reservation_status is not None:
            record["reservation_status"] = reservation_status
        if provider is not None:
            record["provider"] = provider
        if model is not None:
            record["model"] = model
        if execution_path is not None:
            record["execution_path"] = execution_path
        if execution_path_classification is not None:
            record["execution_path_classification"] = execution_path_classification
        if claim_status is not None:
            record["claim_status"] = claim_status
        if proof_status is not None:
            record["proof_status"] = proof_status
        if reconciliation_state is not None:
            record["reconciliation_state"] = reconciliation_state
        if reconciliation_checked_at is not None:
            record["reconciliation_checked_at"] = reconciliation_checked_at
        if reconciliation_reason_code is not None:
            record["reconciliation_reason_code"] = reconciliation_reason_code
        if reconciliation_evidence_source is not None:
            record["reconciliation_evidence_source"] = reconciliation_evidence_source
        if budget_authority_validated is not None:
            record["budget_authority_validated"] = budget_authority_validated
        if max_prompt_tokens is not None:
            record["max_prompt_tokens"] = max_prompt_tokens
        if max_completion_tokens is not None:
            record["max_completion_tokens"] = max_completion_tokens
        if max_total_tokens is not None:
            record["max_total_tokens"] = max_total_tokens
        if retry_limit is not None:
            record["retry_limit"] = retry_limit
        if observed_prompt_tokens is not None:
            record["observed_prompt_tokens"] = observed_prompt_tokens
        if observed_completion_tokens is not None:
            record["observed_completion_tokens"] = observed_completion_tokens
        if observed_total_tokens is not None:
            record["observed_total_tokens"] = observed_total_tokens
        if observed_reasoning_tokens is not None:
            record["observed_reasoning_tokens"] = observed_reasoning_tokens
        if retry_count is not None:
            record["retry_count"] = retry_count
        if budget_stop_enforced is not None:
            record["budget_stop_enforced"] = budget_stop_enforced
        if budget_stop_reason_code is not None:
            record["budget_stop_reason_code"] = budget_stop_reason_code
        if provider_request_id is not None:
            record["provider_request_id"] = provider_request_id
        if started_at is not None:
            record["started_at"] = started_at
        if finished_at is not None:
            record["finished_at"] = finished_at
        if outcome_status is not None:
            record["outcome_status"] = outcome_status
        if reason_code is not None:
            record["reason_code"] = reason_code
        payload = self._validated_governed_external_call_payload(record)
        updated_at = _utc_now()
        with self._connect() as connection:
            connection.execute(
                """
                UPDATE governed_external_call_records
                SET execution_group_id = ?, attempt_number = ?, run_id = ?, task_packet_id = ?,
                    reservation_id = ?, reservation_linkage_validated = ?, reservation_status = ?, provider = ?,
                    model = ?, execution_path = ?, execution_path_classification = ?, claim_status = ?, proof_status = ?,
                    reconciliation_state = ?, reconciliation_checked_at = ?, reconciliation_reason_code = ?,
                    reconciliation_evidence_source = ?, trust_status = ?,
                    budget_authority_validated = ?, max_prompt_tokens = ?, max_completion_tokens = ?,
                    max_total_tokens = ?, retry_limit = ?, observed_prompt_tokens = ?,
                    observed_completion_tokens = ?, observed_total_tokens = ?, observed_reasoning_tokens = ?,
                    retry_count = ?, budget_stop_enforced = ?, budget_stop_reason_code = ?, provider_request_id = ?,
                    started_at = ?, finished_at = ?, outcome_status = ?, reason_code = ?, updated_at = ?
                WHERE external_call_id = ?
                """,
                (
                    payload["execution_group_id"],
                    payload["attempt_number"],
                    payload["run_id"],
                    payload["task_packet_id"],
                    payload["reservation_id"],
                    payload["reservation_linkage_validated"],
                    payload["reservation_status"],
                    payload["provider"],
                    payload["model"],
                    payload["execution_path"],
                    payload["execution_path_classification"],
                    payload["claim_status"],
                    payload["proof_status"],
                    payload["reconciliation_state"],
                    payload["reconciliation_checked_at"],
                    payload["reconciliation_reason_code"],
                    payload["reconciliation_evidence_source"],
                    payload["trust_status"],
                    payload["budget_authority_validated"],
                    payload["max_prompt_tokens"],
                    payload["max_completion_tokens"],
                    payload["max_total_tokens"],
                    payload["retry_limit"],
                    payload["observed_prompt_tokens"],
                    payload["observed_completion_tokens"],
                    payload["observed_total_tokens"],
                    payload["observed_reasoning_tokens"],
                    payload["retry_count"],
                    payload["budget_stop_enforced"],
                    payload["budget_stop_reason_code"],
                    payload["provider_request_id"],
                    payload["started_at"],
                    payload["finished_at"],
                    payload["outcome_status"],
                    payload["reason_code"],
                    updated_at,
                    external_call_id,
                ),
            )
        updated = self.get_governed_external_call_record(external_call_id)
        if updated is None:
            raise ValueError(f"Governed external call record vanished after update: {external_call_id}")
        return updated

    def create_governed_external_reconciliation_record(
        self,
        *,
        external_call_id: str,
        provider_request_id: str | None = None,
        reconciliation_state: str,
        reconciliation_checked_at: str,
        reconciliation_reason_code: str | None = None,
        reconciliation_evidence_source: str | None = None,
        details: dict[str, Any] | None = None,
        reconciliation_id: str | None = None,
    ) -> dict[str, Any]:
        call_record = self.get_governed_external_call_record(external_call_id)
        if call_record is None:
            raise ValueError(f"Governed external call record not found: {external_call_id}")
        record = GovernedExternalReconciliationRecord(
            reconciliation_id=reconciliation_id or _new_id("recon"),
            external_call_id=external_call_id,
            execution_group_id=str(call_record.get("execution_group_id") or external_call_id),
            run_id=call_record["run_id"],
            provider_request_id=provider_request_id,
            reconciliation_state=reconciliation_state,
            reconciliation_checked_at=reconciliation_checked_at,
            reconciliation_reason_code=reconciliation_reason_code,
            reconciliation_evidence_source=reconciliation_evidence_source,
            details=details or {},
        )
        payload = record.model_dump()
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO governed_external_reconciliation_records (
                    reconciliation_id, external_call_id, execution_group_id, run_id,
                    provider_request_id, reconciliation_state, reconciliation_checked_at, reconciliation_reason_code,
                    reconciliation_evidence_source, details_json, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    payload["reconciliation_id"],
                    payload["external_call_id"],
                    payload["execution_group_id"],
                    payload["run_id"],
                    payload["provider_request_id"],
                    payload["reconciliation_state"],
                    payload["reconciliation_checked_at"],
                    payload["reconciliation_reason_code"],
                    payload["reconciliation_evidence_source"],
                    _json_dumps(payload["details"]),
                    _utc_now(),
                ),
            )
        self.update_governed_external_call_record(
            external_call_id,
            reconciliation_state=payload["reconciliation_state"],
            reconciliation_checked_at=payload["reconciliation_checked_at"],
            reconciliation_reason_code=payload["reconciliation_reason_code"],
            reconciliation_evidence_source=payload["reconciliation_evidence_source"],
        )
        created = self.get_governed_external_reconciliation_record(payload["reconciliation_id"])
        if created is None:
            raise ValueError(
                f"Failed to create governed external reconciliation record: {payload['reconciliation_id']}"
            )
        return created

    def record_governed_external_reconciliation(
        self,
        *,
        external_call_id: str,
        provider_request_id: str,
        reconciliation_state: str,
        reconciliation_evidence_source: str,
        reconciliation_checked_at: str | None = None,
        reconciliation_reason_code: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        call_record = self.get_governed_external_call_record(external_call_id)
        if call_record is None:
            raise ValueError(f"Governed external call record not found: {external_call_id}")

        normalized_provider_request_id = " ".join(str(provider_request_id).split())
        if not normalized_provider_request_id:
            raise ValueError("provider_request_id is required for reconciliation input.")

        normalized_state = " ".join(str(reconciliation_state).split())
        if normalized_state not in {"reconciliation_pending", "reconciled", "reconciliation_failed"}:
            raise ValueError(
                "reconciliation_state must be one of: reconciliation_pending, reconciled, reconciliation_failed."
            )

        normalized_source = " ".join(str(reconciliation_evidence_source).split())
        if not normalized_source:
            raise ValueError("reconciliation_evidence_source is required for reconciliation input.")

        recorded_provider_request_id = str(call_record.get("provider_request_id") or "").strip()
        if not recorded_provider_request_id or str(call_record.get("proof_status") or "") != "proved":
            raise ValueError(
                "Cannot record reconciliation without provider proof captured on the governed external call."
            )
        if normalized_provider_request_id != recorded_provider_request_id:
            raise ValueError("provider_request_id does not match the governed external call proof record.")

        normalized_reason_code = None
        if reconciliation_reason_code is not None:
            normalized_reason_code = " ".join(str(reconciliation_reason_code).split()) or None
        if normalized_state == "reconciliation_failed" and normalized_reason_code is None:
            raise ValueError("reconciliation_reason_code is required when reconciliation_state is reconciliation_failed.")

        checked_at = " ".join(str(reconciliation_checked_at).split()) if reconciliation_checked_at else _utc_now()
        details_payload = dict(details or {})
        details_payload.setdefault("provider_request_id", normalized_provider_request_id)

        reconciliation_record = self.create_governed_external_reconciliation_record(
            external_call_id=external_call_id,
            provider_request_id=normalized_provider_request_id,
            reconciliation_state=normalized_state,
            reconciliation_checked_at=checked_at,
            reconciliation_reason_code=normalized_reason_code,
            reconciliation_evidence_source=normalized_source,
            details=details_payload,
        )
        updated_call_record = self.get_governed_external_call_record(external_call_id)
        if updated_call_record is None:
            raise ValueError(f"Governed external call record vanished after reconciliation: {external_call_id}")
        return {
            "reconciliation_record": reconciliation_record,
            "governed_external_call": updated_call_record,
        }

    def get_governed_external_reconciliation_record(self, reconciliation_id: str) -> dict[str, Any] | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM governed_external_reconciliation_records WHERE reconciliation_id = ?",
                (reconciliation_id,),
            ).fetchone()
        return self._deserialize_governed_external_reconciliation_record(row) if row else None

    def list_governed_external_reconciliation_records(
        self,
        *,
        run_id: str | None = None,
        external_call_id: str | None = None,
        execution_group_id: str | None = None,
    ) -> list[dict[str, Any]]:
        query = "SELECT * FROM governed_external_reconciliation_records WHERE 1 = 1"
        params: list[Any] = []
        if run_id:
            query += " AND run_id = ?"
            params.append(run_id)
        if external_call_id:
            query += " AND external_call_id = ?"
            params.append(external_call_id)
        if execution_group_id:
            query += " AND execution_group_id = ?"
            params.append(execution_group_id)
        query += " ORDER BY reconciliation_checked_at ASC, created_at ASC"
        with self._connect() as connection:
            rows = connection.execute(query, tuple(params)).fetchall()
        return [self._deserialize_governed_external_reconciliation_record(row) for row in rows]

    def list_governed_external_trust_worklist(self, *, include_trusted: bool = False) -> list[dict[str, Any]]:
        run_cache: dict[str, dict[str, Any] | None] = {}
        task_cache: dict[str, dict[str, Any] | None] = {}
        project_cache: dict[str, dict[str, Any] | None] = {}
        milestone_cache: dict[str, dict[str, Any] | None] = {}
        worklist: list[dict[str, Any]] = []

        for call_record in self.list_governed_external_call_records():
            category = _governed_external_trust_worklist_category(
                reconciliation_state=call_record.get("reconciliation_state"),
                trust_status=call_record.get("trust_status"),
            )
            if category is None:
                continue
            if category == "trusted_reconciled" and not include_trusted:
                continue

            run_id = str(call_record.get("run_id") or "").strip()
            task_id = None
            run = None
            if run_id:
                if run_id not in run_cache:
                    run_cache[run_id] = self.get_run(run_id)
                run = run_cache[run_id]
                task_id = str(run.get("task_id") or "").strip() if isinstance(run, dict) else None

            task = None
            if task_id:
                if task_id not in task_cache:
                    task_cache[task_id] = self.get_task(task_id)
                task = task_cache[task_id]

            project_name = (
                task.get("project_name")
                if isinstance(task, dict)
                else run.get("project_name")
                if isinstance(run, dict)
                else None
            )
            milestone_id = task.get("milestone_id") if isinstance(task, dict) else None

            project = None
            if project_name:
                project_key = str(project_name)
                if project_key not in project_cache:
                    project_cache[project_key] = self._project_context(project_key)
                project = project_cache[project_key]

            milestone = None
            if milestone_id:
                milestone_key = str(milestone_id)
                if milestone_key not in milestone_cache:
                    milestone_cache[milestone_key] = self._milestone_context(milestone_key)
                milestone = milestone_cache[milestone_key]

            run_context = (
                self._run_work_graph_context(run, task, project=project, milestone=milestone)
                if isinstance(run, dict)
                else {
                    "project_id": project.get("id") if isinstance(project, dict) else None,
                    "project_name": project_name,
                    "milestone_id": milestone.get("id") if isinstance(milestone, dict) else milestone_id,
                    "milestone_title": milestone.get("title") if isinstance(milestone, dict) else None,
                    "task_id": task_id,
                    "task_title": task.get("title") if isinstance(task, dict) else None,
                    "run_id": run_id or None,
                    "control_room_path": f"/control-room?run_id={run_id}" if run_id else None,
                }
            )

            worklist.append(
                {
                    "worklist_category": category,
                    "external_call_id": call_record.get("external_call_id"),
                    "execution_group_id": call_record.get("execution_group_id"),
                    "attempt_number": call_record.get("attempt_number"),
                    "run_id": run_context.get("run_id"),
                    "run_status": run.get("status") if isinstance(run, dict) else None,
                    "project_id": run_context.get("project_id"),
                    "project_name": run_context.get("project_name"),
                    "milestone_id": run_context.get("milestone_id"),
                    "milestone_title": run_context.get("milestone_title"),
                    "task_id": run_context.get("task_id"),
                    "task_title": run_context.get("task_title"),
                    "control_room_path": run_context.get("control_room_path"),
                    "provider": call_record.get("provider"),
                    "model": call_record.get("model"),
                    "provider_request_id": call_record.get("provider_request_id"),
                    "proof_status": call_record.get("proof_status"),
                    "reconciliation_state": call_record.get("reconciliation_state"),
                    "trust_status": call_record.get("trust_status"),
                    "reconciliation_reason_code": call_record.get("reconciliation_reason_code"),
                    "reconciliation_checked_at": call_record.get("reconciliation_checked_at"),
                    "reconciliation_evidence_source": call_record.get("reconciliation_evidence_source"),
                    "execution_path_classification": call_record.get("execution_path_classification"),
                    "outcome_status": call_record.get("outcome_status"),
                    "started_at": call_record.get("started_at"),
                    "finished_at": call_record.get("finished_at"),
                    "_worklist_rank": _governed_external_trust_worklist_rank(category),
                    "_sort_at": str(
                        call_record.get("reconciliation_checked_at")
                        or call_record.get("finished_at")
                        or call_record.get("started_at")
                        or ""
                    ),
                }
            )

        worklist.sort(key=lambda item: str(item.get("external_call_id") or ""), reverse=True)
        worklist.sort(key=lambda item: str(item.get("_sort_at") or ""), reverse=True)
        worklist.sort(
            key=lambda item: int(item["_worklist_rank"]) if item.get("_worklist_rank") is not None else 99
        )

        for item in worklist:
            item.pop("_worklist_rank", None)
            item.pop("_sort_at", None)
        return worklist

    def append_governed_external_call_event(
        self,
        *,
        event_type: str,
        occurred_at: str,
        run_id: str,
        task_packet_id: str,
        reservation_id: str,
        external_call_id: str,
        source_component: str,
        status: str,
        reason_code: str | None = None,
        data: dict[str, Any] | None = None,
        event_id: str | None = None,
    ) -> dict[str, Any]:
        payload = GovernedExternalExecutionEvent(
            event_id=event_id or _new_id("ext_evt"),
            event_type=event_type,
            occurred_at=occurred_at,
            run_id=run_id,
            task_packet_id=task_packet_id,
            reservation_id=reservation_id,
            external_call_id=external_call_id,
            source_component=source_component,
            status=status,
            reason_code=reason_code,
            data=data or {},
        ).model_dump()
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO governed_external_call_events (
                    event_id, event_type, occurred_at, run_id, task_packet_id, reservation_id,
                    external_call_id, source_component, status, reason_code, data_json, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    payload["event_id"],
                    payload["event_type"],
                    payload["occurred_at"],
                    payload["run_id"],
                    payload["task_packet_id"],
                    payload["reservation_id"],
                    payload["external_call_id"],
                    payload["source_component"],
                    payload["status"],
                    payload["reason_code"],
                    _json_dumps(payload["data"]),
                    _utc_now(),
                ),
            )
        event = self.get_governed_external_call_event(payload["event_id"])
        if event is None:
            raise ValueError(f"Failed to create governed external call event: {payload['event_id']}")
        return event

    def get_governed_external_call_event(self, event_id: str) -> dict[str, Any] | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM governed_external_call_events WHERE event_id = ?",
                (event_id,),
            ).fetchone()
        return self._deserialize_governed_external_call_event(row) if row else None

    def list_governed_external_call_events(
        self,
        *,
        run_id: str | None = None,
        external_call_id: str | None = None,
        event_type: str | None = None,
    ) -> list[dict[str, Any]]:
        query = "SELECT * FROM governed_external_call_events WHERE 1 = 1"
        params: list[Any] = []
        if run_id:
            query += " AND run_id = ?"
            params.append(run_id)
        if external_call_id:
            query += " AND external_call_id = ?"
            params.append(external_call_id)
        if event_type:
            query += " AND event_type = ?"
            params.append(event_type)
        query += " ORDER BY occurred_at ASC, created_at ASC"
        with self._connect() as connection:
            rows = connection.execute(query, tuple(params)).fetchall()
        return [self._deserialize_governed_external_call_event(row) for row in rows]

    def _summarize_governed_external_execution_groups(
        self,
        records: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        grouped: dict[str, list[dict[str, Any]]] = {}
        for record in records:
            group_id = str(record.get("execution_group_id") or record["external_call_id"])
            grouped.setdefault(group_id, []).append(record)
        summaries: list[dict[str, Any]] = []
        for group_id, attempts in grouped.items():
            ordered_attempts = sorted(
                attempts,
                key=lambda item: (
                    int(item.get("attempt_number") or 1),
                    str(item.get("started_at") or ""),
                    str(item.get("external_call_id") or ""),
                ),
            )
            final_attempt = ordered_attempts[-1]
            classifications = {
                str(item.get("execution_path_classification") or "").strip() for item in ordered_attempts
            }
            if "governed_api_executed" in classifications:
                execution_path_classification = "governed_api_executed"
            elif "non_governed_execution" in classifications:
                execution_path_classification = "non_governed_execution"
            elif classifications == {"blocked_pre_execution"}:
                execution_path_classification = "blocked_pre_execution"
            else:
                execution_path_classification = None
            summaries.append(
                {
                    "execution_group_id": group_id,
                    "total_attempts": len(ordered_attempts),
                    "execution_path_classification": execution_path_classification,
                    "final_attempt_number": int(final_attempt.get("attempt_number") or 1),
                    "final_outcome_status": final_attempt.get("outcome_status"),
                    "final_budget_stop_enforced": bool(final_attempt.get("budget_stop_enforced")),
                    "final_budget_stop_reason_code": final_attempt.get("budget_stop_reason_code"),
                    "final_proof_status": final_attempt.get("proof_status"),
                    "final_reconciliation_state": final_attempt.get("reconciliation_state"),
                    "final_reconciliation_checked_at": final_attempt.get("reconciliation_checked_at"),
                    "final_reconciliation_reason_code": final_attempt.get("reconciliation_reason_code"),
                    "final_reconciliation_evidence_source": final_attempt.get("reconciliation_evidence_source"),
                    "final_trust_status": final_attempt.get("trust_status"),
                    "final_external_call_id": final_attempt.get("external_call_id"),
                }
            )
        return summaries

    def _summarize_governed_external_run(
        self,
        execution_groups: list[dict[str, Any]],
        pre_execution_blocks: list[dict[str, Any]] | None = None,
    ) -> dict[str, int]:
        pre_execution_blocks = pre_execution_blocks or []
        final_success_count = sum(1 for item in execution_groups if item.get("final_outcome_status") == "completed")
        final_stopped_count = sum(1 for item in execution_groups if item.get("final_outcome_status") == "stopped")
        final_budget_stopped_count = sum(1 for item in execution_groups if bool(item.get("final_budget_stop_enforced")))
        final_failed_count = sum(
            1
            for item in execution_groups
            if item.get("final_outcome_status") == "failed" and not bool(item.get("final_budget_stop_enforced"))
        )
        final_proof_missing_count = sum(1 for item in execution_groups if item.get("final_proof_status") == "missing")
        final_proved_count = sum(1 for item in execution_groups if item.get("final_proof_status") == "proved")
        final_trusted_reconciled_count = sum(
            1 for item in execution_groups if item.get("final_trust_status") == "trusted_reconciled"
        )
        final_proof_captured_not_reconciled_count = sum(
            1 for item in execution_groups if item.get("final_trust_status") == "proof_captured_not_reconciled"
        )
        final_reconciliation_failed_count = sum(
            1 for item in execution_groups if item.get("final_trust_status") == "reconciliation_failed"
        )
        final_claim_missing_count = sum(1 for item in execution_groups if item.get("final_trust_status") == "claim_missing")
        final_claimed_only_count = sum(1 for item in execution_groups if item.get("final_trust_status") == "claimed_only")
        governed_api_execution_count = sum(
            1 for item in execution_groups if item.get("execution_path_classification") == "governed_api_executed"
        )
        blocked_execution_count = sum(
            1 for item in execution_groups if item.get("execution_path_classification") == "blocked_pre_execution"
        )
        return {
            "total_execution_groups": len(execution_groups),
            "total_attempts": sum(int(item.get("total_attempts") or 0) for item in execution_groups),
            "governed_api_execution_count": governed_api_execution_count,
            "blocked_execution_count": blocked_execution_count,
            "pre_observation_block_count": len(pre_execution_blocks),
            "final_success_count": final_success_count,
            "final_failed_count": final_failed_count,
            "final_stopped_count": final_stopped_count,
            "final_budget_stopped_count": final_budget_stopped_count,
            "final_proof_missing_count": final_proof_missing_count,
            "final_proved_count": final_proved_count,
            "final_trusted_reconciled_count": final_trusted_reconciled_count,
            "final_proof_captured_not_reconciled_count": final_proof_captured_not_reconciled_count,
            "final_reconciliation_failed_count": final_reconciliation_failed_count,
            "final_claim_missing_count": final_claim_missing_count,
            "final_claimed_only_count": final_claimed_only_count,
        }

    def _governed_external_attention_reason(
        self,
        execution_group: dict[str, Any],
    ) -> str | None:
        if bool(execution_group.get("final_budget_stop_enforced")):
            return str(execution_group.get("final_budget_stop_reason_code") or "budget_stop_enforced")
        final_outcome_status = str(execution_group.get("final_outcome_status") or "").strip()
        if final_outcome_status and final_outcome_status != "completed":
            return f"final_{final_outcome_status}"
        if str(execution_group.get("final_proof_status") or "") == "missing":
            return "final_proof_missing"
        return None

    def _governed_external_attention_items(
        self,
        execution_groups: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []
        for execution_group in execution_groups:
            attention_reason = self._governed_external_attention_reason(execution_group)
            if attention_reason is None:
                continue
            items.append(
                {
                    "execution_group_id": execution_group["execution_group_id"],
                    "final_external_call_id": execution_group.get("final_external_call_id"),
                    "final_attempt_number": int(execution_group.get("final_attempt_number") or 1),
                    "execution_path_classification": execution_group.get("execution_path_classification"),
                    "final_outcome_status": execution_group.get("final_outcome_status"),
                    "final_budget_stop_enforced": bool(execution_group.get("final_budget_stop_enforced")),
                    "final_budget_stop_reason_code": execution_group.get("final_budget_stop_reason_code"),
                    "final_proof_status": execution_group.get("final_proof_status"),
                    "final_reconciliation_state": execution_group.get("final_reconciliation_state"),
                    "final_trust_status": execution_group.get("final_trust_status"),
                    "attention_reason": attention_reason,
                }
            )
        items.sort(
            key=lambda item: (
                0
                if bool(item["final_budget_stop_enforced"])
                else 1
                if item.get("final_outcome_status") != "completed"
                else 2,
                -int(item.get("final_attempt_number") or 1),
                str(item.get("execution_group_id") or ""),
            )
        )
        return items

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

    def _run_git_command(self, *args: str) -> str:
        try:
            result = subprocess.run(
                ["git", *args],
                cwd=self.paths.repo_root,
                capture_output=True,
                text=True,
                check=False,
            )
        except OSError as exc:
            command = " ".join(["git", *args])
            raise ValueError(f"Recovery git command failed to start: {command}") from exc
        if result.returncode != 0:
            command = " ".join(["git", *args])
            detail = (result.stderr or result.stdout).strip() or f"git exited with code {result.returncode}"
            raise ValueError(f"Recovery git command failed: {command}: {detail}")
        return result.stdout.strip()

    def _recovery_manifest_dir(self) -> Path:
        return self.paths.backups_dir / "recovery_manifests"

    def _recovery_snapshot_manifest_path(self, *, checkpoint_tag: str, checkpoint_commit_sha: str) -> Path:
        safe_checkpoint_tag = checkpoint_tag.replace("/", "__")
        return self._recovery_manifest_dir() / f"{safe_checkpoint_tag}__{checkpoint_commit_sha[:12]}.json"

    def _recovery_package_dir(self) -> Path:
        return self.paths.backups_dir / "recovery_packages"

    def _recovery_package_path(self, *, recovery_package_id: str) -> Path:
        return self._recovery_package_dir() / f"{recovery_package_id}.json"

    def _recovery_rollback_receipts_dir(self) -> Path:
        return self.paths.backups_dir / "recovery_rollback_receipts"

    def _recovery_rollback_receipt_path(self, *, rollback_id: str) -> Path:
        return self._recovery_rollback_receipts_dir() / f"{rollback_id}.json"

    def _is_recovery_status_artifact_path(self, relative_path: str) -> bool:
        normalized_path = relative_path.replace("\\", "/").strip()
        return normalized_path.startswith("sessions/backups/")

    def _recovery_authoritative_doc_requirements(
        self,
        *,
        project_name: str,
        working_branch: str,
        checkpoint_tag: str,
        snapshot_branch: str,
        authoritative_doc_paths: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        normalized_project_name = _normalize_recovery_project_slug(project_name)
        normalized_paths = (
            _normalize_string_list(authoritative_doc_paths)
            if authoritative_doc_paths is not None
            else list(AIOFFICE_RECOVERY_AUTHORITATIVE_DOCS if normalized_project_name == "aioffice" else [])
        )
        requirements: list[dict[str, Any]] = []
        for relative_path in normalized_paths:
            required_markers: list[str] = []
            if normalized_project_name == "aioffice" and relative_path == "projects/aioffice/governance/ACTIVE_STATE.md":
                required_markers = [working_branch, checkpoint_tag, snapshot_branch]
            requirements.append(
                {
                    "path": relative_path,
                    "required_markers": required_markers,
                }
            )
        return requirements

    def build_recovery_checkpoint_refs(
        self,
        *,
        project_name: str,
        milestone_key: str,
        closeout_date: str,
    ) -> dict[str, str]:
        project_slug = _normalize_recovery_project_slug(project_name)
        normalized_milestone_key = _normalize_recovery_milestone_key(milestone_key)
        normalized_closeout_date = _normalize_recovery_closeout_date(closeout_date)
        checkpoint_tag = f"{project_slug}-{normalized_milestone_key}-{RECOVERY_CLOSEOUT_LABEL}-{normalized_closeout_date}"
        snapshot_branch = f"snapshot/{checkpoint_tag}"
        return {
            "project_name": project_slug,
            "milestone_key": normalized_milestone_key,
            "closeout_date": normalized_closeout_date,
            "checkpoint_tag": checkpoint_tag,
            "snapshot_branch": snapshot_branch,
        }

    def validate_recovery_checkpoint_refs(
        self,
        *,
        project_name: str,
        milestone_key: str,
        closeout_date: str,
        checkpoint_tag: str,
        snapshot_branch: str,
    ) -> dict[str, str]:
        expected = self.build_recovery_checkpoint_refs(
            project_name=project_name,
            milestone_key=milestone_key,
            closeout_date=closeout_date,
        )
        normalized_checkpoint_tag = _require_non_empty_text("checkpoint_tag", checkpoint_tag)
        normalized_snapshot_branch = _require_non_empty_text("snapshot_branch", snapshot_branch)
        if RECOVERY_CHECKPOINT_TAG_PATTERN.fullmatch(normalized_checkpoint_tag) is None:
            raise ValueError("checkpoint_tag must use the form <project>-m<digits>-closeout-YYYY-MM-DD.")
        if RECOVERY_SNAPSHOT_BRANCH_PATTERN.fullmatch(normalized_snapshot_branch) is None:
            raise ValueError("snapshot_branch must use the form snapshot/<project>-m<digits>-closeout-YYYY-MM-DD.")
        if normalized_checkpoint_tag != expected["checkpoint_tag"] or normalized_snapshot_branch != expected["snapshot_branch"]:
            raise ValueError(
                "checkpoint_tag and snapshot_branch must match the expected recovery naming pattern for the declared project, milestone, and closeout_date."
            )
        return {
            **expected,
            "checkpoint_tag": normalized_checkpoint_tag,
            "snapshot_branch": normalized_snapshot_branch,
        }

    def run_recovery_preflight(
        self,
        *,
        project_name: str,
        milestone_key: str,
        closeout_date: str,
        working_branch: str,
        checkpoint_tag: str | None = None,
        snapshot_branch: str | None = None,
        authoritative_doc_paths: list[str] | None = None,
        require_clean_worktree: bool = True,
    ) -> dict[str, Any]:
        normalized_working_branch = _require_non_empty_text("working_branch", working_branch)
        expected_refs = self.build_recovery_checkpoint_refs(
            project_name=project_name,
            milestone_key=milestone_key,
            closeout_date=closeout_date,
        )
        normalized_checkpoint_tag = _require_non_empty_text(
            "checkpoint_tag",
            checkpoint_tag or expected_refs["checkpoint_tag"],
        )
        normalized_snapshot_branch = _require_non_empty_text(
            "snapshot_branch",
            snapshot_branch or expected_refs["snapshot_branch"],
        )
        validated_refs = self.validate_recovery_checkpoint_refs(
            project_name=project_name,
            milestone_key=milestone_key,
            closeout_date=closeout_date,
            checkpoint_tag=normalized_checkpoint_tag,
            snapshot_branch=normalized_snapshot_branch,
        )

        observed_working_branch = self._run_git_command("branch", "--show-current")
        if observed_working_branch != normalized_working_branch:
            raise ValueError(
                f"Recovery preflight requires working_branch {normalized_working_branch!r}, observed {observed_working_branch!r}."
            )

        status_output = self._run_git_command("status", "--short")
        status_lines = status_output.splitlines() if status_output else []
        ignored_recovery_artifact_output: list[str] = []
        blocking_output: list[str] = []
        for line in status_lines:
            relative_path = line[3:].strip() if len(line) > 3 else ""
            if " -> " in relative_path:
                relative_path = relative_path.split(" -> ", 1)[1].strip()
            if relative_path and self._is_recovery_status_artifact_path(relative_path):
                ignored_recovery_artifact_output.append(line)
            else:
                blocking_output.append(line)
        clean_worktree = {
            "command": "git status --short",
            "required": bool(require_clean_worktree),
            "output": status_lines,
            "ignored_recovery_artifact_output": ignored_recovery_artifact_output,
            "blocking_output": blocking_output,
            "is_clean": not blocking_output,
        }
        if require_clean_worktree and blocking_output:
            raise ValueError("Recovery preflight requires a clean worktree.")

        current_head_commit_sha = self._run_git_command("rev-parse", "HEAD")
        checkpoint_commit_sha = self._run_git_command("rev-list", "-n", "1", validated_refs["checkpoint_tag"])
        snapshot_commit_sha = self._run_git_command("rev-parse", validated_refs["snapshot_branch"])
        if checkpoint_commit_sha != snapshot_commit_sha:
            raise ValueError(
                "Recovery preflight requires checkpoint_tag and snapshot_branch to resolve to the same commit."
            )

        document_requirements = self._recovery_authoritative_doc_requirements(
            project_name=validated_refs["project_name"],
            working_branch=normalized_working_branch,
            checkpoint_tag=validated_refs["checkpoint_tag"],
            snapshot_branch=validated_refs["snapshot_branch"],
            authoritative_doc_paths=authoritative_doc_paths,
        )
        authoritative_documents: list[dict[str, Any]] = []
        missing_documents: list[str] = []
        marker_mismatches: list[str] = []
        for requirement in document_requirements:
            relative_path = str(requirement["path"])
            document_path = self.paths.repo_root / relative_path
            required_markers = _normalize_string_list(requirement.get("required_markers"))
            exists = document_path.exists()
            markers_present: list[bool] = []
            if exists:
                content = document_path.read_text(encoding="utf-8")
                markers_present = [marker in content for marker in required_markers]
            document_record = {
                "path": relative_path,
                "exists": exists,
                "required_markers": required_markers,
                "markers_present": markers_present,
                "all_required_markers_present": all(markers_present) if required_markers else True,
            }
            authoritative_documents.append(document_record)
            if not exists:
                missing_documents.append(relative_path)
            elif required_markers and not document_record["all_required_markers_present"]:
                marker_mismatches.append(relative_path)

        if missing_documents:
            raise ValueError(
                "Recovery preflight requires authoritative docs to exist at HEAD: "
                + ", ".join(missing_documents)
            )
        if marker_mismatches:
            raise ValueError(
                "Recovery preflight requires authoritative docs to match the expected recovery anchors: "
                + ", ".join(marker_mismatches)
            )

        return {
            "status": "passed",
            "project_name": validated_refs["project_name"],
            "milestone_key": validated_refs["milestone_key"],
            "closeout_date": validated_refs["closeout_date"],
            "working_branch": {
                "expected": normalized_working_branch,
                "observed": observed_working_branch,
                "matches": observed_working_branch == normalized_working_branch,
            },
            "checkpoint_tag": {
                "name": validated_refs["checkpoint_tag"],
                "commit_sha": checkpoint_commit_sha,
            },
            "snapshot_branch": {
                "name": validated_refs["snapshot_branch"],
                "commit_sha": snapshot_commit_sha,
            },
            "checkpoint_alignment": {
                "refs_match": checkpoint_commit_sha == snapshot_commit_sha,
            },
            "current_head_commit_sha": current_head_commit_sha,
            "clean_worktree": clean_worktree,
            "authoritative_documents": authoritative_documents,
        }

    def create_recovery_snapshot_manifest(
        self,
        *,
        project_name: str,
        milestone_key: str,
        closeout_date: str,
        working_branch: str,
        checkpoint_tag: str | None = None,
        snapshot_branch: str | None = None,
        authoritative_doc_paths: list[str] | None = None,
        require_clean_worktree: bool = True,
    ) -> dict[str, Any]:
        preflight = self.run_recovery_preflight(
            project_name=project_name,
            milestone_key=milestone_key,
            closeout_date=closeout_date,
            working_branch=working_branch,
            checkpoint_tag=checkpoint_tag,
            snapshot_branch=snapshot_branch,
            authoritative_doc_paths=authoritative_doc_paths,
            require_clean_worktree=require_clean_worktree,
        )
        manifest_path = self._recovery_snapshot_manifest_path(
            checkpoint_tag=preflight["checkpoint_tag"]["name"],
            checkpoint_commit_sha=preflight["checkpoint_tag"]["commit_sha"],
        )
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        manifest = {
            "manifest_kind": "recovery_snapshot_manifest",
            "schema_version": "recovery_snapshot_manifest_v1",
            "created_at": _utc_now(),
            "project_name": preflight["project_name"],
            "milestone_key": preflight["milestone_key"],
            "closeout_date": preflight["closeout_date"],
            "working_branch": preflight["working_branch"]["observed"],
            "checkpoint_tag": preflight["checkpoint_tag"]["name"],
            "snapshot_branch": preflight["snapshot_branch"]["name"],
            "current_head_commit_sha": preflight["current_head_commit_sha"],
            "checkpoint_commit_sha": preflight["checkpoint_tag"]["commit_sha"],
            "snapshot_commit_sha": preflight["snapshot_branch"]["commit_sha"],
            "clean_worktree": preflight["clean_worktree"],
            "authoritative_documents": preflight["authoritative_documents"],
            "checkpoint_alignment": preflight["checkpoint_alignment"],
            "manifest_path": str(manifest_path),
        }
        manifest_path.write_text(_json_dumps(manifest) + "\n", encoding="utf-8")
        return manifest

    def _load_verified_dispatch_backup(self, backup_id: str) -> dict[str, Any]:
        backup = self._find_dispatch_backup(backup_id)
        if backup is None:
            raise ValueError(f"Backup not found: {backup_id}")
        manifest_path = Path(_require_non_empty_text("manifest_path", backup.get("manifest_path")))
        if not manifest_path.exists():
            raise ValueError(f"Backup manifest missing for {backup_id}.")
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ValueError(f"Backup manifest is invalid JSON for {backup_id}.") from exc
        if manifest.get("backup_id") != backup_id:
            raise ValueError(f"Backup manifest backup_id mismatch for {backup_id}.")
        backup_path = Path(_require_non_empty_text("path", manifest.get("path")))
        if not backup_path.exists():
            raise ValueError(f"Backup file missing for {backup_id}.")
        if manifest_path.resolve() != self._backup_manifest_path(backup_path).resolve():
            raise ValueError(f"Backup manifest path mismatch for {backup_id}.")
        actual_sha256 = _sha256_bytes(backup_path.read_bytes())
        if manifest.get("sha256") != actual_sha256:
            raise ValueError(f"Backup sha256 mismatch for {backup_id}.")
        source_db_path = Path(_require_non_empty_text("source_db_path", manifest.get("source_db_path")))
        if source_db_path.resolve() != self.paths.db_path.resolve():
            raise ValueError(f"Backup source_db_path mismatch for {backup_id}.")
        return {
            **manifest,
            "backup_file_exists": True,
            "manifest_file_exists": True,
            "sha256_matches": True,
            "verified_at": _utc_now(),
        }

    def _load_recovery_snapshot_package(self, recovery_package_id: str) -> dict[str, Any]:
        package_path = self._recovery_package_path(recovery_package_id=recovery_package_id)
        if not package_path.exists():
            raise ValueError(f"Recovery snapshot package not found: {recovery_package_id}")
        try:
            package = json.loads(package_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ValueError(f"Recovery snapshot package is invalid JSON: {recovery_package_id}") from exc
        if package.get("recovery_package_id") != recovery_package_id:
            raise ValueError(f"Recovery snapshot package id mismatch for {recovery_package_id}.")
        if package.get("package_kind") != "recovery_snapshot_package":
            raise ValueError(f"Recovery package kind mismatch for {recovery_package_id}.")
        manifest_path = Path(_require_non_empty_text("recovery_manifest_path", package.get("recovery_manifest_path")))
        if not manifest_path.exists():
            raise ValueError(f"Recovery manifest missing for {recovery_package_id}.")
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ValueError(f"Recovery manifest is invalid JSON for {recovery_package_id}.") from exc
        for field in (
            "project_name",
            "milestone_key",
            "closeout_date",
            "working_branch",
            "checkpoint_tag",
            "snapshot_branch",
            "checkpoint_commit_sha",
            "snapshot_commit_sha",
            "current_head_commit_sha",
        ):
            if package.get(field) != manifest.get(field):
                raise ValueError(f"Recovery package manifest mismatch for {recovery_package_id}: {field}.")
        verified_backup = self._load_verified_dispatch_backup(
            _require_non_empty_text("dispatch_backup_id", package.get("dispatch_backup_id"))
        )
        if verified_backup["backup_id"] != package["dispatch_backup_id"]:
            raise ValueError(f"Recovery package backup id mismatch for {recovery_package_id}.")
        if verified_backup["path"] != package.get("dispatch_backup_path"):
            raise ValueError(f"Recovery package backup path mismatch for {recovery_package_id}.")
        if verified_backup["manifest_path"] != package.get("dispatch_backup_manifest_path"):
            raise ValueError(f"Recovery package backup manifest path mismatch for {recovery_package_id}.")
        if verified_backup["sha256"] != package.get("dispatch_backup_sha256"):
            raise ValueError(f"Recovery package backup sha mismatch for {recovery_package_id}.")
        return {
            **package,
            "recovery_manifest": manifest,
            "dispatch_backup": verified_backup,
            "package_path": str(package_path),
            "verified_at": _utc_now(),
        }

    def create_recovery_snapshot_package(
        self,
        *,
        project_name: str,
        milestone_key: str,
        closeout_date: str,
        working_branch: str,
        task_id: str,
        trigger: str,
        note: str,
        requested_by: str,
        checkpoint_tag: str | None = None,
        snapshot_branch: str | None = None,
        authoritative_doc_paths: list[str] | None = None,
        require_clean_worktree: bool = True,
    ) -> dict[str, Any]:
        task = self.get_task(task_id)
        if task is None:
            raise ValueError(f"Task not found: {task_id}")
        if task.get("project_name") != project_name:
            raise ValueError("Recovery snapshot package task/project mismatch.")
        manifest = self.create_recovery_snapshot_manifest(
            project_name=project_name,
            milestone_key=milestone_key,
            closeout_date=closeout_date,
            working_branch=working_branch,
            checkpoint_tag=checkpoint_tag,
            snapshot_branch=snapshot_branch,
            authoritative_doc_paths=authoritative_doc_paths,
            require_clean_worktree=require_clean_worktree,
        )
        dispatch_backup = self.create_dispatch_backup(
            project_name=project_name,
            trigger=trigger,
            task_id=task_id,
            note=note,
        )
        verified_backup = self._load_verified_dispatch_backup(dispatch_backup["backup_id"])
        recovery_package_id = _new_id("recovery")
        package_path = self._recovery_package_path(recovery_package_id=recovery_package_id)
        package_path.parent.mkdir(parents=True, exist_ok=True)
        package = {
            "package_kind": "recovery_snapshot_package",
            "receipt_kind": "recovery_snapshot_created",
            "recovery_package_id": recovery_package_id,
            "created_at": _utc_now(),
            "project_name": manifest["project_name"],
            "task_id": task_id,
            "trigger": _require_non_empty_text("trigger", trigger),
            "note": _require_non_empty_text("note", note),
            "requested_by": _require_non_empty_text("requested_by", requested_by),
            "milestone_key": manifest["milestone_key"],
            "closeout_date": manifest["closeout_date"],
            "working_branch": manifest["working_branch"],
            "checkpoint_tag": manifest["checkpoint_tag"],
            "snapshot_branch": manifest["snapshot_branch"],
            "current_head_commit_sha": manifest["current_head_commit_sha"],
            "checkpoint_commit_sha": manifest["checkpoint_commit_sha"],
            "snapshot_commit_sha": manifest["snapshot_commit_sha"],
            "recovery_manifest_path": manifest["manifest_path"],
            "dispatch_backup_id": verified_backup["backup_id"],
            "dispatch_backup_path": verified_backup["path"],
            "dispatch_backup_manifest_path": verified_backup["manifest_path"],
            "dispatch_backup_sha256": verified_backup["sha256"],
            "clean_worktree": manifest["clean_worktree"],
            "checkpoint_alignment": manifest["checkpoint_alignment"],
            "authoritative_documents": manifest["authoritative_documents"],
            "verification": {
                "recovery_preflight_passed": True,
                "backup_manifest_verified": True,
                "backup_sha256_matches": True,
                "checkpoint_alignment_matches": manifest["checkpoint_alignment"]["refs_match"],
            },
            "package_path": str(package_path),
        }
        package_path.write_text(_json_dumps(package) + "\n", encoding="utf-8")
        return package

    def restore_recovery_snapshot_package(
        self,
        *,
        recovery_package_id: str,
        requested_by: str,
        project_name: str,
        milestone_key: str,
        closeout_date: str,
        working_branch: str,
        checkpoint_tag: str | None = None,
        snapshot_branch: str | None = None,
        authoritative_doc_paths: list[str] | None = None,
        require_clean_worktree: bool = True,
    ) -> dict[str, Any]:
        package = self._load_recovery_snapshot_package(recovery_package_id)
        if package["project_name"] != project_name:
            raise ValueError("Recovery restore package project mismatch.")
        current_anchor = self.run_recovery_preflight(
            project_name=project_name,
            milestone_key=milestone_key,
            closeout_date=closeout_date,
            working_branch=working_branch,
            checkpoint_tag=checkpoint_tag or package["checkpoint_tag"],
            snapshot_branch=snapshot_branch or package["snapshot_branch"],
            authoritative_doc_paths=authoritative_doc_paths,
            require_clean_worktree=require_clean_worktree,
        )
        if (
            current_anchor["checkpoint_tag"]["name"] != package["checkpoint_tag"]
            or current_anchor["snapshot_branch"]["name"] != package["snapshot_branch"]
            or current_anchor["checkpoint_tag"]["commit_sha"] != package["checkpoint_commit_sha"]
            or current_anchor["snapshot_branch"]["commit_sha"] != package["snapshot_commit_sha"]
        ):
            raise ValueError("Recovery restore requires target refs to match the accepted recovery anchor.")
        pre_restore_recovery_package = self.create_recovery_snapshot_package(
            project_name=project_name,
            milestone_key=milestone_key,
            closeout_date=closeout_date,
            working_branch=working_branch,
            task_id=package["task_id"],
            trigger="pre_restore",
            note=f"Pre-restore recovery snapshot before restoring package {recovery_package_id} requested by {requested_by}.",
            requested_by=requested_by,
            checkpoint_tag=package["checkpoint_tag"],
            snapshot_branch=package["snapshot_branch"],
            authoritative_doc_paths=authoritative_doc_paths,
            require_clean_worktree=require_clean_worktree,
        )
        verified_backup = self._load_verified_dispatch_backup(package["dispatch_backup_id"])
        shutil.copy2(Path(verified_backup["path"]), self.paths.db_path)
        self.initialize()
        restored_run = self.latest_run_for_task(package["task_id"])
        restored_context_receipt = self.load_context_receipt(restored_run["id"]) if restored_run else None
        receipt = {
            "receipt_kind": "recovery_restore_completed",
            "restore_id": _new_id("restore"),
            "recovery_package_id": recovery_package_id,
            "task_id": package["task_id"],
            "project_name": project_name,
            "requested_by": _require_non_empty_text("requested_by", requested_by),
            "restored_at": _utc_now(),
            "target_checkpoint_tag": package["checkpoint_tag"],
            "target_snapshot_branch": package["snapshot_branch"],
            "target_checkpoint_commit_sha": package["checkpoint_commit_sha"],
            "pre_restore_recovery_package_id": pre_restore_recovery_package["recovery_package_id"],
            "pre_restore_recovery_package_path": pre_restore_recovery_package["package_path"],
            "backup_id": verified_backup["backup_id"],
            "backup_manifest_path": verified_backup["manifest_path"],
            "backup_sha256": verified_backup["sha256"],
            "recovery_preflight": current_anchor,
            "store_health": self.schema_health(),
            "source_run_id": verified_backup.get("source_run_id"),
            "source_context_receipt": verified_backup.get("source_context_receipt"),
            "restored_run_id": restored_run["id"] if restored_run else None,
            "restored_context_receipt": restored_context_receipt,
            "verification": {
                "target_recovery_package_verified": True,
                "target_refs_match_current_anchor": True,
                "backup_manifest_verified": True,
                "backup_sha256_matches": True,
                "pre_action_snapshot_created": True,
                "accepted_current_truth_changed": False,
            },
            "restore_status": "verified_candidate_only",
            "accepted_current_truth_changed": False,
        }
        receipt_path = self.paths.restore_receipts_dir / f"{receipt['restore_id']}.json"
        receipt["receipt_path"] = str(receipt_path)
        receipt_path.write_text(_json_dumps(receipt) + "\n", encoding="utf-8")
        return receipt

    def prepare_recovery_rollback(
        self,
        *,
        recovery_package_id: str,
        requested_by: str,
        project_name: str,
        milestone_key: str,
        closeout_date: str,
        working_branch: str,
        checkpoint_tag: str | None = None,
        snapshot_branch: str | None = None,
        authoritative_doc_paths: list[str] | None = None,
        require_clean_worktree: bool = True,
    ) -> dict[str, Any]:
        package = self._load_recovery_snapshot_package(recovery_package_id)
        if package["project_name"] != project_name:
            raise ValueError("Recovery rollback package project mismatch.")
        current_anchor = self.run_recovery_preflight(
            project_name=project_name,
            milestone_key=milestone_key,
            closeout_date=closeout_date,
            working_branch=working_branch,
            checkpoint_tag=checkpoint_tag or package["checkpoint_tag"],
            snapshot_branch=snapshot_branch or package["snapshot_branch"],
            authoritative_doc_paths=authoritative_doc_paths,
            require_clean_worktree=require_clean_worktree,
        )
        if (
            current_anchor["checkpoint_tag"]["name"] != package["checkpoint_tag"]
            or current_anchor["snapshot_branch"]["name"] != package["snapshot_branch"]
            or current_anchor["checkpoint_tag"]["commit_sha"] != package["checkpoint_commit_sha"]
            or current_anchor["snapshot_branch"]["commit_sha"] != package["snapshot_commit_sha"]
        ):
            raise ValueError("Recovery rollback requires target refs to match the accepted recovery anchor.")
        pre_rollback_recovery_package = self.create_recovery_snapshot_package(
            project_name=project_name,
            milestone_key=milestone_key,
            closeout_date=closeout_date,
            working_branch=working_branch,
            task_id=package["task_id"],
            trigger="pre_rollback",
            note=f"Pre-rollback recovery snapshot before preparing rollback for package {recovery_package_id} requested by {requested_by}.",
            requested_by=requested_by,
            checkpoint_tag=package["checkpoint_tag"],
            snapshot_branch=package["snapshot_branch"],
            authoritative_doc_paths=authoritative_doc_paths,
            require_clean_worktree=require_clean_worktree,
        )
        verified_backup = self._load_verified_dispatch_backup(package["dispatch_backup_id"])
        rollback_id = _new_id("rollback")
        receipt_path = self._recovery_rollback_receipt_path(rollback_id=rollback_id)
        receipt_path.parent.mkdir(parents=True, exist_ok=True)
        receipt = {
            "receipt_kind": "recovery_rollback_prepared",
            "rollback_id": rollback_id,
            "prepared_at": _utc_now(),
            "requested_by": _require_non_empty_text("requested_by", requested_by),
            "project_name": project_name,
            "task_id": package["task_id"],
            "target_recovery_package_id": recovery_package_id,
            "target_checkpoint_tag": package["checkpoint_tag"],
            "target_snapshot_branch": package["snapshot_branch"],
            "target_checkpoint_commit_sha": package["checkpoint_commit_sha"],
            "target_backup_id": verified_backup["backup_id"],
            "target_backup_manifest_path": verified_backup["manifest_path"],
            "target_backup_sha256": verified_backup["sha256"],
            "pre_rollback_recovery_package_id": pre_rollback_recovery_package["recovery_package_id"],
            "pre_rollback_recovery_package_path": pre_rollback_recovery_package["package_path"],
            "recovery_preflight": current_anchor,
            "verification": {
                "target_recovery_package_verified": True,
                "target_refs_match_current_anchor": True,
                "backup_manifest_verified": True,
                "backup_sha256_matches": True,
                "pre_action_snapshot_created": True,
                "rollback_executed": False,
                "accepted_current_truth_changed": False,
            },
            "rollback_ready": True,
            "rollback_executed": False,
            "accepted_current_truth_changed": False,
            "receipt_path": str(receipt_path),
        }
        receipt_path.write_text(_json_dumps(receipt) + "\n", encoding="utf-8")
        return receipt

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
        backup = self._load_verified_dispatch_backup(backup_id)
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
            "receipt_kind": "dispatch_backup_restore_completed",
            "verification": {
                "backup_manifest_verified": True,
                "backup_sha256_matches": True,
                "accepted_current_truth_changed": False,
            },
            "accepted_current_truth_changed": False,
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
        project = self._project_context(run["project_name"])
        milestone = self._milestone_context(task.get("milestone_id")) if task is not None else None
        run_context = self._run_work_graph_context(run, task, project=project, milestone=milestone)
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
        governed_pre_execution_blocks = self.list_governed_pre_execution_blocks(run_id=run_id)
        governed_external_call_records = self.list_governed_external_call_records(run_id=run_id)
        governed_external_reconciliation_records = self.list_governed_external_reconciliation_records(run_id=run_id)
        governed_external_execution_groups = self._summarize_governed_external_execution_groups(
            governed_external_call_records
        )
        governed_external_run_summary = self._summarize_governed_external_run(
            governed_external_execution_groups,
            governed_pre_execution_blocks,
        )
        governed_external_attention_items = self._governed_external_attention_items(
            governed_external_execution_groups
        )
        governed_external_call_events = self.list_governed_external_call_events(run_id=run_id)
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
            "project": project,
            "milestone": milestone,
            "project_name": run["project_name"],
            "run_context": run_context,
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
            "governed_pre_execution_blocks": governed_pre_execution_blocks,
            "governed_external_calls": governed_external_call_records,
            "governed_external_reconciliation_records": governed_external_reconciliation_records,
            "governed_external_execution_groups": governed_external_execution_groups,
            "governed_external_run_summary": governed_external_run_summary,
            "governed_external_attention_items": governed_external_attention_items,
            "governed_external_call_events": governed_external_call_events,
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

    def _deserialize_workflow_run(self, row: sqlite3.Row) -> dict[str, Any]:
        workflow_run = dict(row)
        workflow_run["scope"] = _json_loads(workflow_run.get("scope_json"), default={})
        return workflow_run

    def _deserialize_stage_run(self, row: sqlite3.Row) -> dict[str, Any]:
        return dict(row)

    def _deserialize_workflow_artifact(self, row: sqlite3.Row) -> dict[str, Any]:
        artifact = dict(row)
        artifact["input_artifact_paths"] = _json_loads(artifact.get("input_artifact_paths_json"), default=[])
        return artifact

    def _deserialize_handoff(self, row: sqlite3.Row) -> dict[str, Any]:
        handoff = dict(row)
        handoff["upstream_artifact_ids"] = _json_loads(handoff.get("upstream_artifact_ids_json"), default=[])
        return handoff

    def _deserialize_blocker(self, row: sqlite3.Row) -> dict[str, Any]:
        return dict(row)

    def _deserialize_question_or_assumption(self, row: sqlite3.Row) -> dict[str, Any]:
        return dict(row)

    def _deserialize_orchestration_trace(self, row: sqlite3.Row) -> dict[str, Any]:
        trace = dict(row)
        trace["payload"] = _json_loads(trace.get("payload_json"), default={})
        return trace

    def _deserialize_control_execution_packet(self, row: sqlite3.Row) -> dict[str, Any]:
        packet = dict(row)
        packet["allowed_write_paths"] = _json_loads(packet.get("allowed_write_paths_json"), default=[])
        packet["forbidden_paths"] = _json_loads(packet.get("forbidden_paths_json"), default=[])
        packet["forbidden_actions"] = _json_loads(packet.get("forbidden_actions_json"), default=[])
        packet["required_artifact_outputs"] = _json_loads(
            packet.get("required_artifact_outputs_json"),
            default=[],
        )
        packet["required_validations"] = _json_loads(packet.get("required_validations_json"), default=[])
        packet["expected_return_bundle_contents"] = _json_loads(
            packet.get("expected_return_bundle_contents_json"),
            default=[],
        )
        packet["failure_reporting_expectations"] = _json_loads(
            packet.get("failure_reporting_expectations_json"),
            default=[],
        )
        return packet

    def _deserialize_execution_bundle(self, row: sqlite3.Row) -> dict[str, Any]:
        bundle = dict(row)
        bundle["produced_artifact_ids"] = _json_loads(bundle.get("produced_artifact_ids_json"), default=[])
        bundle["diff_refs"] = _json_loads(bundle.get("diff_refs_json"), default=[])
        bundle["commands_run"] = _json_loads(bundle.get("commands_run_json"), default=[])
        bundle["test_results"] = _json_loads(bundle.get("test_results_json"), default=[])
        bundle["blocker_ids"] = _json_loads(bundle.get("blocker_ids_json"), default=[])
        bundle["question_ids"] = _json_loads(bundle.get("question_ids_json"), default=[])
        bundle["assumption_ids"] = _json_loads(bundle.get("assumption_ids_json"), default=[])
        bundle["open_risks"] = _json_loads(bundle.get("open_risks_json"), default=[])
        bundle["evidence_receipts"] = _json_loads(bundle.get("evidence_receipts_json"), default=[])
        return bundle

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

    def _deserialize_governed_external_call_record(self, row: sqlite3.Row) -> dict[str, Any]:
        record = dict(row)
        if not str(record.get("execution_path_classification") or "").strip():
            record["execution_path_classification"] = self._derived_execution_path_classification(record)
        return self._validated_governed_external_call_payload(record)

    def _deserialize_governed_pre_execution_block(self, row: sqlite3.Row) -> dict[str, Any]:
        record = dict(row)
        return GovernedPreExecutionBlockRecord.model_validate(record).model_dump()

    def _deserialize_governed_external_reconciliation_record(self, row: sqlite3.Row) -> dict[str, Any]:
        record = dict(row)
        record["details"] = _json_loads(record.pop("details_json"), default={})
        return GovernedExternalReconciliationRecord.model_validate(record).model_dump()

    def _derived_execution_path_classification(self, record: dict[str, Any]) -> str | None:
        normalized_execution_path = str(record.get("execution_path") or "").strip()
        if normalized_execution_path and normalized_execution_path != "governed_api":
            return "non_governed_execution"
        provider_request_id = str(record.get("provider_request_id") or "").strip()
        if provider_request_id:
            return "governed_api_executed"
        observed_fields = (
            record.get("observed_prompt_tokens"),
            record.get("observed_completion_tokens"),
            record.get("observed_total_tokens"),
            record.get("observed_reasoning_tokens"),
        )
        if any(value is not None for value in observed_fields):
            return "governed_api_executed"
        return None

    def _deserialize_governed_external_call_event(self, row: sqlite3.Row) -> dict[str, Any]:
        event = dict(row)
        event["data"] = _json_loads(event.pop("data_json"), default={})
        return GovernedExternalExecutionEvent.model_validate(event).model_dump()

    def _deserialize_validation_result(self, row: sqlite3.Row) -> dict[str, Any]:
        validation = dict(row)
        validation["checks"] = _json_loads(validation.get("checks_json"), default={})
        return validation
