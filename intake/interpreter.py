from __future__ import annotations

import hashlib
from pathlib import Path

from intake.models import IntentDecision, InterpreterSummary
from workspace_root import ensure_authoritative_workspace_path, ensure_authoritative_workspace_root


_IMPLEMENTATION_TOKENS = ("implement", "build", "add", "fix", "update", "create", "write", "refactor", "restore", "design")
_ANALYSIS_TOKENS = ("analyze", "analysis", "assess", "diagnose", "investigate", "summarize", "document")
_REVIEW_TOKENS = ("review", "audit", "validate", "verify", "inspect", "check")


def _task_kind(normalized_request: str) -> str:
    lowered = normalized_request.lower()
    if any(token in lowered for token in _REVIEW_TOKENS):
        return "REVIEW"
    if any(token in lowered for token in _ANALYSIS_TOKENS):
        return "ANALYSIS"
    if any(token in lowered for token in _IMPLEMENTATION_TOKENS):
        return "IMPLEMENTATION"
    return "UNKNOWN"


def _bounded_refs(repo_root: Path, *, project_name: str | None, task_kind: str) -> list[str]:
    candidates = [
        repo_root / "governance" / "CONTROL_INVARIANTS.md",
        repo_root / "governance" / "ARCHITECTURE_BASELINE.md",
    ]
    if task_kind in {"ANALYSIS", "REVIEW", "UNKNOWN"}:
        candidates.append(repo_root / "governance" / "KNOWN_GAPS.md")
    if project_name:
        candidates.append(repo_root / "projects" / project_name / "governance" / "PROJECT_BRIEF.md")

    refs: list[str] = []
    for candidate in candidates:
        checked = ensure_authoritative_workspace_path(candidate, label="interpreter ref path")
        if checked.exists():
            refs.append(checked.relative_to(repo_root).as_posix())
        if len(refs) >= 5:
            break
    if not refs:
        refs.append("workspace:authoritative_root")
    return refs


def _constraints(task_kind: str) -> list[str]:
    constraints = [
        "workspace_root_authority",
        "task_path_only",
        "policy_updates_separate",
        "read_only_interpreter",
    ]
    if task_kind in {"ANALYSIS", "REVIEW", "UNKNOWN"}:
        constraints.append("prefer_non_mutating_defaults")
    return constraints[:5]


def _open_questions(repo_root: Path, *, project_name: str | None, task_kind: str) -> list[str]:
    questions: list[str] = []
    if project_name:
        brief_path = ensure_authoritative_workspace_path(
            repo_root / "projects" / project_name / "governance" / "PROJECT_BRIEF.md",
            label="interpreter project brief path",
        )
        if not brief_path.exists():
            questions.append("project_brief_unavailable")
    if task_kind == "UNKNOWN":
        questions.append("task_kind_unclear")
    return questions[:5]


def compile_interpreter_summary(
    repo_root: str | Path,
    decision: IntentDecision,
    *,
    project_name: str | None = None,
) -> InterpreterSummary:
    validated = IntentDecision.model_validate(decision.model_dump())
    if validated.decision != "ROUTE_TASK" or validated.intent != "TASK" or not validated.safe_to_route:
        raise ValueError("Only safe ROUTE_TASK decisions compile to InterpreterSummary.")

    root = ensure_authoritative_workspace_root(repo_root, label="interpreter repo_root")
    normalized_request = validated.normalized_request
    task_kind = _task_kind(normalized_request)
    summary_id = "interp_" + hashlib.sha256(normalized_request.encode("utf-8")).hexdigest()[:12]
    return InterpreterSummary(
        summary_id=summary_id,
        source_intent="TASK",
        normalized_request=normalized_request,
        task_kind=task_kind,  # type: ignore[arg-type]
        relevant_refs=_bounded_refs(root, project_name=project_name, task_kind=task_kind),
        constraints=_constraints(task_kind),
        open_questions=_open_questions(root, project_name=project_name, task_kind=task_kind),
        safe_for_execution_path=False,
    )
