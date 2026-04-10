from __future__ import annotations

import hashlib
import json
import sqlite3
import subprocess
from pathlib import Path

from intake.models import IntentDecision, StatusResponse
from workspace_root import ensure_authoritative_workspace_path, ensure_authoritative_workspace_root

_SYSTEM_TOKENS = ("system", "repo", "repository", "branch", "runtime", "environment")
_TASK_TOKENS = ("task", "tasks", "work", "backlog", "run", "runs", "approval", "approvals", "kanban", "review")
_GOVERNANCE_TOKENS = ("policy", "policies", "governance", "proposal", "proposals", "rules")


def _bounded_text(value: str, *, limit: int) -> str:
    collapsed = " ".join((value or "").split())
    if len(collapsed) <= limit:
        return collapsed
    return collapsed[: limit - 3].rstrip() + "..."


def _bounded_refs(items: list[str]) -> list[str]:
    normalized = [_bounded_text(str(item), limit=160) for item in items if str(item).strip()]
    return normalized[:5]


def _status_kind(normalized_request: str) -> str:
    lowered = normalized_request.lower()
    if any(token in lowered for token in _GOVERNANCE_TOKENS):
        return "GOVERNANCE"
    if any(token in lowered for token in _TASK_TOKENS):
        return "TASK"
    if any(token in lowered for token in _SYSTEM_TOKENS):
        return "SYSTEM"
    return "UNKNOWN"


def _git_summary(repo_root: Path) -> tuple[str, list[str]]:
    git_dir = ensure_authoritative_workspace_path(repo_root / ".git", label="status git path")
    if not git_dir.exists():
        return ("System status is limited in v1 because git metadata is unavailable.", ["repo:.git missing"])
    branch = subprocess.run(
        ["git", "branch", "--show-current"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    ).stdout.strip() or "unknown"
    dirty = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    ).stdout.strip()
    dirty_state = "dirty" if dirty else "clean"
    return (
        f"System branch {branch} has a {dirty_state} working tree.",
        ["git:branch", "git:status"],
    )


def _task_summary(repo_root: Path, project_name: str | None) -> tuple[str, list[str]]:
    db_path = ensure_authoritative_workspace_path(repo_root / "sessions" / "studio.db", label="status task db path")
    if not db_path.exists():
        return ("Task status is limited in v1 because sessions/studio.db is unavailable.", ["sessions/studio.db"])
    query = "SELECT status, COUNT(*) AS count FROM tasks"
    latest_query = "SELECT id, status FROM tasks"
    params: tuple[str, ...] = ()
    if project_name:
        query += " WHERE project_name = ?"
        latest_query += " WHERE project_name = ?"
        params = (project_name,)
    query += " GROUP BY status ORDER BY status"
    latest_query += " ORDER BY updated_at DESC LIMIT 1"
    try:
        connection = sqlite3.connect(f"file:{db_path.as_posix()}?mode=ro", uri=True)
        connection.row_factory = sqlite3.Row
        try:
            counts = connection.execute(query, params).fetchall()
            latest = connection.execute(latest_query, params).fetchone()
        finally:
            connection.close()
    except sqlite3.Error:
        return ("Task status is limited in v1 because the task store is unreadable.", ["sessions/studio.db"])
    if not counts:
        target = project_name or "all tracked projects"
        return (f"No tracked tasks are available for {target}.", ["sessions/studio.db"])
    count_bits = [f"{row['count']} {row['status']}" for row in counts]
    latest_bit = ""
    if latest is not None:
        latest_bit = f" Latest task {latest['id']} is {latest['status']}."
    target = project_name or "all tracked projects"
    return (
        _bounded_text(
            f"Task status for {target}: " + ", ".join(count_bits) + "." + latest_bit,
            limit=240,
        ),
        _bounded_refs(["sessions/studio.db", f"project:{target}"]),
    )


def _governance_summary(repo_root: Path) -> tuple[str, list[str]]:
    proposals_dir = ensure_authoritative_workspace_path(
        repo_root / "governance" / "policy_proposals",
        label="status governance proposals path",
    )
    if not proposals_dir.exists():
        return (
            "Governance status is limited in v1 because no policy proposals have been recorded.",
            ["governance/policy_proposals"],
        )
    proposal_files = sorted(proposals_dir.glob("*.json"))
    if not proposal_files:
        return (
            "Governance status is limited in v1 because no policy proposals have been recorded.",
            ["governance/policy_proposals"],
        )
    latest = proposal_files[-1]
    latest_payload = json.loads(latest.read_text(encoding="utf-8"))
    latest_id = str(latest_payload.get("proposal_id") or latest.stem)
    latest_status = str(latest_payload.get("status") or "UNKNOWN")
    return (
        _bounded_text(
            f"Governance has {len(proposal_files)} recorded policy proposal(s). Latest proposal {latest_id} is {latest_status}.",
            limit=240,
        ),
        _bounded_refs(["governance/policy_proposals", f"proposal:{latest_id}"]),
    )


def _unknown_summary() -> tuple[str, list[str]]:
    return (
        "Status query is outside the supported v1 status scope.",
        ["status:v1-limited-scope"],
    )


def compile_status_response(
    repo_root: str | Path,
    decision: IntentDecision,
    *,
    project_name: str | None = None,
) -> StatusResponse:
    validated = IntentDecision.model_validate(decision.model_dump())
    if validated.decision != "ROUTE_STATUS" or validated.intent != "STATUS_QUERY" or not validated.safe_to_route:
        raise ValueError("Only safe STATUS_QUERY decisions compile to StatusResponse.")

    normalized_request = validated.normalized_request
    status_kind = _status_kind(normalized_request)
    root = ensure_authoritative_workspace_root(repo_root, label="status repo_root")
    if status_kind == "SYSTEM":
        summary, evidence_refs = _git_summary(root)
    elif status_kind == "TASK":
        summary, evidence_refs = _task_summary(root, project_name)
    elif status_kind == "GOVERNANCE":
        summary, evidence_refs = _governance_summary(root)
    else:
        summary, evidence_refs = _unknown_summary()

    response_id = "status_" + hashlib.sha256(normalized_request.encode("utf-8")).hexdigest()[:12]
    return StatusResponse(
        response_id=response_id,
        source_intent="STATUS_QUERY",
        normalized_request=normalized_request,
        status_kind=status_kind,  # type: ignore[arg-type]
        summary=_bounded_text(summary, limit=240),
        evidence_refs=_bounded_refs(evidence_refs),
        safe_for_execution_path=False,
    )
