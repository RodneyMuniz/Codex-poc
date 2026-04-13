from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sessions import SessionStore


def _project_label(project_name: str) -> str:
    return " ".join(part.capitalize() for part in project_name.split("-"))


def _secondary_state(task: dict[str, Any]) -> str | None:
    if task["status"] in {"blocked", "deferred"}:
        return task["status"]
    return None


def _status_label(value: str | None) -> str:
    return str(value or "unknown").replace("_", " ").title()


def _approval_lane(approval: dict[str, Any]) -> tuple[str, str]:
    if approval.get("approval_scope") == "local-exception" or "one_shot" in approval:
        return "local_exception", "Local Exception"
    return "delegated_work", "Delegated Work"


def _action_mode(*, runtime_role: str | None = None, source: str | None = None, event_type: str | None = None) -> dict[str, str]:
    specialist_roles = {"Architect", "Developer", "Design", "QA"}
    runtime_value = str(runtime_role or "").strip()
    source_value = str(source or "").strip()
    event_value = str(event_type or "").strip().lower()
    if event_value.startswith("sdk_") or runtime_value in specialist_roles or source_value in specialist_roles:
        return {"key": "ai_delegated", "label": "AI Delegated"}
    return {"key": "framework", "label": "Framework Action"}


def _pending_approval_card(
    approval: dict[str, Any],
    *,
    task: dict[str, Any] | None,
) -> dict[str, Any]:
    lane_key, lane_label = _approval_lane(approval)
    return {
        **approval,
        "approval_id": approval["id"],
        "approval_lane": lane_key,
        "approval_lane_label": lane_label,
        "approval_status_label": _status_label(approval["status"]),
        "project_name": task["project_name"] if task else approval.get("project_name"),
        "project_label": _project_label(task["project_name"]) if task else None,
        "task_title": task["title"] if task else None,
        "task_status": task["status"] if task else None,
        "approval_summary": approval.get("reason") or approval.get("decision_note") or "Approval pending.",
    }


def _worker_manifest_summary(team_state: dict[str, Any]) -> dict[str, Any] | None:
    worker_dispatch = team_state.get("worker_dispatch")
    if not isinstance(worker_dispatch, dict):
        return None
    manifest = worker_dispatch.get("manifest")
    if not isinstance(manifest, dict):
        return None
    return dict(manifest)


def _run_compliance_summary(
    *,
    store: SessionStore,
    run: dict[str, Any],
    task: dict[str, Any] | None,
    approvals_by_run: dict[str, list[dict[str, Any]]],
    local_exception_approvals_by_run: dict[str, list[dict[str, Any]]],
) -> dict[str, Any]:
    team_state = store.load_team_state(run["id"]) or {}
    compliance_state = team_state.get("compliance_state")
    if not isinstance(compliance_state, dict):
        compliance_state = {}
    worker_manifest = _worker_manifest_summary(team_state)
    worker_dispatch = team_state.get("worker_dispatch") if isinstance(team_state.get("worker_dispatch"), dict) else None
    compliance_records = store.list_compliance_records(run["id"])
    breach_records = [record for record in compliance_records if record["record_kind"] == "breach"]
    delegated_records = [record for record in compliance_records if record["record_kind"] == "compliant_delegated_run"]
    local_exception_records = [record for record in compliance_records if record["record_kind"] == "local_exception_approved"]
    pending_delegated = [approval for approval in approvals_by_run.get(run["id"], []) if approval["status"] == "pending"]
    pending_local_exception = [
        approval for approval in local_exception_approvals_by_run.get(run["id"], []) if approval["status"] == "pending"
    ]
    latest_local_exception = local_exception_approvals_by_run.get(run["id"], [])
    latest_local_exception_approval = latest_local_exception[-1] if latest_local_exception else None
    compliance_mode = compliance_state.get("mode")
    if not compliance_mode:
        if breach_records:
            compliance_mode = "breached"
        elif local_exception_records:
            compliance_mode = "local_exception_approved"
        elif delegated_records:
            compliance_mode = "delegated"
        else:
            compliance_mode = "unverified"
    return {
        "run_id": run["id"],
        "task_id": run["task_id"],
        "task_title": task["title"] if task else None,
        "run_status": run["status"],
        "pause_reason": run.get("stop_reason"),
        "pause_reason_label": _status_label(run.get("stop_reason")),
        "phase": team_state.get("phase"),
        "execution_mode": team_state.get("execution_mode"),
        "compliance_state": {
            **compliance_state,
            "mode": compliance_mode,
            "breach_count": len(breach_records),
            "delegated_run_count": len(delegated_records),
            "local_exception_count": len(local_exception_records),
            "pause_reason": run.get("stop_reason"),
            "pause_reason_label": _status_label(run.get("stop_reason")),
            "worker_manifest": worker_manifest,
        },
        "breach_count": len(breach_records),
        "pending_delegated_approvals": len(pending_delegated),
        "pending_local_exception_approvals": len(pending_local_exception),
        "local_exception_state": latest_local_exception_approval,
        "worker_dispatch": worker_dispatch,
        "worker_manifest": worker_manifest,
    }


def _decorate_task_compliance(
    task: dict[str, Any],
    *,
    run_compliance_summary: dict[str, Any] | None,
) -> dict[str, Any]:
    if run_compliance_summary is None:
        return {
            "mode": "unverified",
            "breach_count": 0,
            "pause_reason": None,
            "local_exception_state": None,
            "pending_delegated_approvals": 0,
            "pending_local_exception_approvals": 0,
            "worker_manifest": None,
        }
    return {
        "mode": run_compliance_summary["compliance_state"]["mode"],
        "summary": run_compliance_summary["compliance_state"].get("summary"),
        "breach_count": run_compliance_summary["breach_count"],
        "pause_reason": run_compliance_summary["pause_reason"],
        "pause_reason_label": run_compliance_summary["pause_reason_label"],
        "local_exception_state": run_compliance_summary["local_exception_state"],
        "pending_delegated_approvals": run_compliance_summary["pending_delegated_approvals"],
        "pending_local_exception_approvals": run_compliance_summary["pending_local_exception_approvals"],
        "worker_manifest": run_compliance_summary["worker_manifest"],
    }


def build_run_compliance_summary(store: SessionStore, run_id: str) -> dict[str, Any]:
    run = store.get_run(run_id)
    if run is None:
        raise ValueError(f"Run not found: {run_id}")
    task = store.get_task(run["task_id"])
    approvals_by_run: dict[str, list[dict[str, Any]]] = defaultdict(list)
    local_exception_approvals_by_run: dict[str, list[dict[str, Any]]] = defaultdict(list)
    approvals_by_run[run_id] = [approval for approval in store.list_approvals() if approval.get("run_id") == run_id]
    local_exception_approvals_by_run[run_id] = [
        approval for approval in store.list_local_exception_approvals(run_id)
    ]
    return _run_compliance_summary(
        store=store,
        run=run,
        task=task,
        approvals_by_run=approvals_by_run,
        local_exception_approvals_by_run=local_exception_approvals_by_run,
    )


def build_approval_feed(
    store: SessionStore,
    *,
    status: str | None = None,
) -> list[dict[str, Any]]:
    approvals: list[dict[str, Any]] = []
    standard_approvals = store.list_approvals(status)
    local_exception_approvals = store.list_local_exception_approvals(status=status)
    task_lookup = {task["id"]: task for task in store.list_tasks()}
    for approval in standard_approvals:
        task = task_lookup.get(approval.get("task_id")) if approval.get("task_id") else None
        lane_key, lane_label = _approval_lane(approval)
        approvals.append(
            {
                **approval,
                "approval_lane": lane_key,
                "approval_lane_label": lane_label,
                "approval_status_label": _status_label(approval["status"]),
                "project_name": task["project_name"] if task else None,
                "project_label": _project_label(task["project_name"]) if task else None,
                "task_title": task["title"] if task else None,
                "task_status": task["status"] if task else None,
                "approval_summary": approval.get("reason") or approval.get("decision_note") or "Approval pending.",
            }
        )
    for approval in local_exception_approvals:
        task = task_lookup.get(approval.get("task_id")) if approval.get("task_id") else None
        approvals.append(_pending_approval_card(approval, task=task))
    approvals.sort(key=lambda item: item.get("created_at") or "")
    return approvals


def _run_summary(run: dict[str, Any] | None) -> dict[str, Any] | None:
    if run is None:
        return None
    return {
        "id": run["id"],
        "status": run["status"],
        "created_at": run["created_at"],
        "completed_at": run.get("completed_at"),
        "project_name": run["project_name"],
    }


def _governed_external_run_summary(evidence: dict[str, Any] | None) -> dict[str, int]:
    summary = evidence.get("governed_external_run_summary") if isinstance(evidence, dict) else None
    if not isinstance(summary, dict):
        summary = {}
    return {
        "total_execution_groups": int(summary.get("total_execution_groups") or 0),
        "total_attempts": int(summary.get("total_attempts") or 0),
        "governed_api_execution_count": int(summary.get("governed_api_execution_count") or 0),
        "blocked_execution_count": int(summary.get("blocked_execution_count") or 0),
        "pre_observation_block_count": int(summary.get("pre_observation_block_count") or 0),
        "final_success_count": int(summary.get("final_success_count") or 0),
        "final_failed_count": int(summary.get("final_failed_count") or 0),
        "final_stopped_count": int(summary.get("final_stopped_count") or 0),
        "final_budget_stopped_count": int(summary.get("final_budget_stopped_count") or 0),
        "final_proof_missing_count": int(summary.get("final_proof_missing_count") or 0),
        "final_proved_count": int(summary.get("final_proved_count") or 0),
    }


def _artifact_summary(artifact: dict[str, Any] | None) -> dict[str, Any] | None:
    if artifact is None:
        return None
    produced_by = artifact.get("produced_by")
    if produced_by is None:
        produced_by = artifact.get("provider")
    artifact_kind = artifact.get("artifact_kind") or artifact.get("kind")
    return {
        "id": artifact["id"],
        "artifact_kind": artifact_kind,
        "artifact_path": artifact.get("artifact_path"),
        "produced_by": produced_by,
        "created_at": artifact["created_at"],
        "artifact_sha256": artifact.get("artifact_sha256"),
        "run_id": artifact["run_id"],
        "provider": artifact.get("provider"),
        "prompt_summary": artifact.get("prompt_summary"),
        "review_state": artifact.get("review_state"),
        "selected_direction": artifact.get("selected_direction"),
        "parent_visual_artifact_id": artifact.get("parent_visual_artifact_id"),
        "lineage_root_visual_artifact_id": artifact.get("lineage_root_visual_artifact_id"),
        "locked_base_visual_artifact_id": artifact.get("locked_base_visual_artifact_id"),
        "edit_session_id": artifact.get("edit_session_id"),
    }


def _artifact_sort_key(artifact: dict[str, Any]) -> tuple[str, str, str]:
    return (
        str(artifact.get("updated_at") or artifact.get("created_at") or ""),
        str(artifact.get("created_at") or ""),
        str(artifact.get("id") or ""),
    )


def _validation_summary(validation: dict[str, Any] | None) -> dict[str, Any] | None:
    if validation is None:
        return None
    return {
        "id": validation["id"],
        "status": validation["status"],
        "validator_role": validation["validator_role"],
        "artifact_path": validation.get("artifact_path"),
        "created_at": validation["created_at"],
        "summary": validation["summary"],
        "run_id": validation["run_id"],
    }


def _task_card(
    task: dict[str, Any],
    *,
    project_lookup: dict[str, dict[str, Any]],
    milestone_lookup: dict[str, dict[str, Any]],
    board_column_lookup: dict[str, str],
    latest_run_lookup: dict[str, dict[str, Any]],
    latest_run_work_graph_lookup: dict[str, dict[str, Any]],
    task_run_count_lookup: dict[str, int],
    task_trust_summary_lookup: dict[str, dict[str, Any]],
    run_compliance_lookup: dict[str, dict[str, Any] | None],
    latest_artifact_lookup: dict[str, dict[str, Any]],
    latest_validation_lookup: dict[str, dict[str, Any]],
    store: SessionStore,
) -> dict[str, Any]:
    project = project_lookup.get(task["project_name"])
    milestone = milestone_lookup.get(task.get("milestone_id"))
    board_column_key = store.task_board_column_key(task)
    latest_run = latest_run_lookup.get(task["id"])
    latest_run_summary = latest_run_work_graph_lookup.get(task["id"])
    trust_summary = task_trust_summary_lookup.get(task["id"])
    compliance_summary = run_compliance_lookup.get(latest_run["id"]) if latest_run else None
    return {
        "id": task["id"],
        "copy_text": task["id"],
        "project_id": project.get("id") if project else None,
        "project_name": task["project_name"],
        "project_label": _project_label(task["project_name"]),
        "title": task["title"],
        "objective": task["objective"],
        "details": task["details"],
        "status": task["status"],
        "task_kind": task["task_kind"],
        "owner_role": task["owner_role"],
        "assigned_role": task.get("assigned_role"),
        "layer": task.get("layer"),
        "category": task.get("category"),
        "review_state": task.get("review_state"),
        "priority": task.get("priority"),
        "requires_approval": bool(task.get("requires_approval")),
        "expected_artifact_path": task.get("expected_artifact_path"),
        "parent_task_id": task.get("parent_task_id"),
        "updated_at": task.get("updated_at"),
        "completed_at": task.get("completed_at"),
        "milestone_id": task.get("milestone_id"),
        "milestone_title": milestone["title"] if milestone else None,
        "board_column_key": board_column_key,
        "board_column_label": board_column_lookup[board_column_key],
        "secondary_state": _secondary_state(task),
        "gate_issues": store.task_gate_issues(task, target_status=task["status"]) if task["status"] in {"ready", "completed"} else [],
        "linked_run_count": int(task_run_count_lookup.get(task["id"], 0)),
        "latest_run": latest_run_summary or _run_summary(latest_run),
        "latest_attention_summary": latest_run_summary.get("attention_summary") if latest_run_summary else None,
        "latest_health_summary": latest_run_summary.get("health_summary") if latest_run_summary else None,
        "latest_execution_summary": latest_run_summary.get("execution_summary") if latest_run_summary else None,
        "trust_summary": trust_summary,
        "latest_artifact": _artifact_summary(latest_artifact_lookup.get(task["id"])),
        "latest_validation": _validation_summary(latest_validation_lookup.get(task["id"])),
        "compliance_state": _decorate_task_compliance(task, run_compliance_summary=compliance_summary),
    }


def _filter_for_project(
    items: list[dict[str, Any]],
    *,
    task_lookup: dict[str, dict[str, Any]],
    run_lookup: dict[str, dict[str, Any]],
    project_name: str,
) -> list[dict[str, Any]]:
    filtered: list[dict[str, Any]] = []
    for item in items:
        task_id = item.get("task_id")
        run_id = item.get("run_id")
        task = task_lookup.get(task_id) if task_id else None
        run = run_lookup.get(run_id) if run_id else None
        if (task and task["project_name"] == project_name) or (run and run["project_name"] == project_name):
            filtered.append(item)
    return filtered


def _milestone_cards(
    milestones: list[dict[str, Any]],
    *,
    task_cards: list[dict[str, Any]],
    milestone_trust_lookup: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    tasks_by_milestone: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for task in task_cards:
        if task.get("milestone_id"):
            tasks_by_milestone[task["milestone_id"]].append(task)

    cards: list[dict[str, Any]] = []
    for milestone in milestones:
        items = tasks_by_milestone.get(milestone["id"], [])
        completed = sum(1 for item in items if item["status"] == "completed")
        total = len(items)
        cards.append(
            {
                **milestone,
                "project_label": _project_label(milestone["project_name"]),
                "task_count": total,
                "completed_task_count": completed,
                "completion_percent": int((completed / total) * 100) if total else 0,
                "trust_summary": milestone_trust_lookup.get(milestone["id"]),
                "tasks": [
                    {
                        "id": item["id"],
                        "copy_text": item["id"],
                        "title": item["title"],
                        "status": item["status"],
                        "owner_role": item.get("owner_role"),
                        "assigned_role": item.get("assigned_role"),
                        "board_column_key": item["board_column_key"],
                        "board_column_label": item["board_column_label"],
                        "secondary_state": item.get("secondary_state"),
                        "review_state": item.get("review_state"),
                        "latest_run": item.get("latest_run"),
                        "trust_summary": item.get("trust_summary"),
                        "latest_artifact": item.get("latest_artifact"),
                        "compliance_state": item.get("compliance_state"),
                    }
                    for item in items
                ],
            }
        )
    return cards


def _project_rollup(
    store: SessionStore,
    *,
    projects: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    board_column_lookup = dict(store.board_columns())
    rollup: list[dict[str, Any]] = []
    for project in projects:
        tasks = store.list_tasks(project["name"])
        counts = Counter(store.task_board_column_key(task) for task in tasks)
        milestones = store.list_milestones(project["name"])
        latest_update = max((task.get("updated_at") or task.get("created_at") for task in tasks), default=None)
        rollup.append(
            {
                "project_name": project["name"],
                "project_label": _project_label(project["name"]),
                "root_path": project["root_path"],
                "task_count": len(tasks),
                "milestone_count": len(milestones),
                "trust_summary": store.summarize_project_trust(project["name"]),
                "status_counts": {key: counts.get(key, 0) for key, _ in store.board_columns()},
                "status_labels": board_column_lookup,
                "latest_updated_at": latest_update,
            }
        )
    return rollup


def _recent_updates(
    *,
    task_cards: list[dict[str, Any]],
    approvals: list[dict[str, Any]],
    runs: list[dict[str, Any]],
    agent_runs: list[dict[str, Any]],
    validations: list[dict[str, Any]],
    artifacts: list[dict[str, Any]],
    task_lookup: dict[str, dict[str, Any]],
    limit: int,
) -> list[dict[str, Any]]:
    updates: list[dict[str, Any]] = []

    for task in task_cards:
        status_summary = task["board_column_label"]
        if task.get("secondary_state"):
            status_summary = f"{status_summary} ({_status_label(task['secondary_state'])})"
        updates.append(
            {
                "event_type": "task_status",
                "event_label": "Task Updated",
                "event_at": task.get("updated_at") or task.get("completed_at"),
                "task_id": task["id"],
                "task_title": task["title"],
                "project_name": task["project_name"],
                "project_label": task["project_label"],
                "run_id": task.get("latest_run", {}).get("id") if task.get("latest_run") else None,
                "artifact_id": task.get("latest_artifact", {}).get("id") if task.get("latest_artifact") else None,
                "artifact_path": task.get("latest_artifact", {}).get("artifact_path") if task.get("latest_artifact") else None,
                "summary": f"{task['id']} now sits in {status_summary}.",
                "status": task["status"],
            }
        )

    for approval in approvals:
        task = task_lookup.get(approval["task_id"])
        if task is None:
            continue
        updates.append(
            {
                "event_type": "approval",
                "event_label": f"Approval {_status_label(approval['status'])}",
                "event_at": approval.get("decided_at") or approval.get("created_at"),
                "task_id": task["id"],
                "task_title": task["title"],
                "project_name": task["project_name"],
                "project_label": _project_label(task["project_name"]),
                "run_id": approval.get("run_id"),
                "artifact_id": None,
                "artifact_path": approval.get("expected_output"),
                "summary": approval.get("reason") or approval.get("decision_note") or "Approval event recorded.",
                "status": approval["status"],
                "role": approval.get("requested_by"),
            }
        )

    for run in runs:
        updates.append(
            {
                "event_type": "run",
                "event_label": f"Run {_status_label(run['status'])}",
                "event_at": run.get("completed_at") or run.get("updated_at") or run.get("created_at"),
                "task_id": run["task_id"],
                "task_title": run["task_title"],
                "project_name": run["project_name"],
                "project_label": run["project_label"],
                "run_id": run["id"],
                "artifact_id": None,
                "artifact_path": None,
                "summary": f"{run['id']} is {run['status']}.",
                "status": run["status"],
            }
        )

    for item in agent_runs:
        updates.append(
            {
                "event_type": "agent_run",
                "event_label": f"{item['role']} {_status_label(item['status'])}",
                "event_at": item.get("completed_at") or item.get("started_at"),
                "task_id": item["task_id"],
                "task_title": item["task_title"],
                "project_name": item["project_name"],
                "project_label": item["project_label"],
                "run_id": item["run_id"],
                "artifact_id": None,
                "artifact_path": item.get("output_artifact_path"),
                "summary": item.get("notes") or f"{item['role']} recorded a {item['status']} worker run.",
                "status": item["status"],
                "role": item["role"],
            }
        )

    for item in validations:
        updates.append(
            {
                "event_type": "validation",
                "event_label": f"Validation {_status_label(item['status'])}",
                "event_at": item["created_at"],
                "task_id": item["task_id"],
                "task_title": item["task_title"],
                "project_name": item["project_name"],
                "project_label": item["project_label"],
                "run_id": item["run_id"],
                "artifact_id": None,
                "artifact_path": item.get("artifact_path"),
                "summary": item["summary"],
                "status": item["status"],
                "role": item["validator_role"],
            }
        )

    for item in artifacts:
        updates.append(
            {
                "event_type": "artifact",
                "event_label": "Artifact Recorded",
                "event_at": item["created_at"],
                "task_id": item["task_id"],
                "task_title": item["task_title"],
                "project_name": item["project_name"],
                "project_label": item["project_label"],
                "run_id": item["run_id"],
                "artifact_id": item["id"],
                "artifact_path": item.get("artifact_path"),
                "summary": item.get("kind") or "Runtime artifact captured.",
                "status": item.get("produced_by"),
                "role": item.get("produced_by"),
            }
        )

    updates = [item for item in updates if item.get("event_at")]
    updates.sort(key=lambda item: item["event_at"], reverse=True)
    return updates[:limit]


def build_snapshot(repo_root: str | Path, *, project_name: str = "all", limit: int = 25) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    store = SessionStore(root)
    selected_project = project_name.strip() if project_name else "all"
    scoped_project = None if selected_project == "all" else selected_project
    tasks = store.list_tasks(scoped_project)
    task_lookup = {task["id"]: task for task in tasks}
    all_runs = store.list_runs(scoped_project)
    runs = all_runs[:limit]
    run_lookup = {run["id"]: run for run in all_runs}
    milestones = store.list_milestones(scoped_project)
    milestone_lookup = {milestone["id"]: milestone for milestone in milestones}
    board_columns = store.board_columns()
    board_column_lookup = dict(board_columns)

    registered_projects = store.list_projects()
    project_lookup = {project["name"]: project for project in registered_projects}
    available_projects = [
        {
            "name": project["name"],
            "label": _project_label(project["name"]),
            "root_path": project["root_path"],
            "task_count": len(store.list_tasks(project["name"])),
        }
        for project in registered_projects
    ]

    all_approvals = store.list_approvals()
    all_local_exception_approvals = store.list_local_exception_approvals()
    if scoped_project is None:
        scoped_approvals = all_approvals
        scoped_local_exception_approvals = all_local_exception_approvals
    else:
        scoped_approvals = _filter_for_project(
            all_approvals,
            task_lookup=task_lookup,
            run_lookup=run_lookup,
            project_name=scoped_project,
        )
        scoped_local_exception_approvals = _filter_for_project(
            all_local_exception_approvals,
            task_lookup=task_lookup,
            run_lookup=run_lookup,
            project_name=scoped_project,
        )

    all_agent_runs: list[dict[str, Any]] = []
    all_artifacts: list[dict[str, Any]] = []
    all_validations: list[dict[str, Any]] = []
    latest_run_lookup: dict[str, dict[str, Any]] = {}
    latest_run_work_graph_lookup: dict[str, dict[str, Any]] = {}
    task_trust_summary_lookup: dict[str, dict[str, Any]] = {}
    task_run_count_lookup = Counter(run["task_id"] for run in all_runs)
    approvals_by_run: dict[str, list[dict[str, Any]]] = defaultdict(list)
    local_exception_approvals_by_run: dict[str, list[dict[str, Any]]] = defaultdict(list)
    run_compliance_lookup: dict[str, dict[str, Any]] = {}
    compliance_records_by_run: dict[str, list[dict[str, Any]]] = {}

    for approval in scoped_approvals:
        approvals_by_run[approval["run_id"]].append(approval)
    for approval in scoped_local_exception_approvals:
        local_exception_approvals_by_run[approval["run_id"]].append(approval)

    for run in all_runs:
        latest_run_lookup.setdefault(run["task_id"], run)
        latest_run_work_graph_lookup.setdefault(run["task_id"], store.summarize_task_linked_run(run["id"]))
        compliance_records_by_run[run["id"]] = store.list_compliance_records(run["id"])
        run_compliance_lookup[run["id"]] = _run_compliance_summary(
            store=store,
            run=run,
            task=task_lookup.get(run["task_id"]),
            approvals_by_run=approvals_by_run,
            local_exception_approvals_by_run=local_exception_approvals_by_run,
        )

        for agent_run in store.list_agent_runs(run["id"]):
            all_agent_runs.append(agent_run)
            latest_run_lookup.setdefault(agent_run["task_id"], run)

        for artifact in store.list_artifacts(run["id"]):
            all_artifacts.append(artifact)
            latest_run_lookup.setdefault(artifact["task_id"], run)

        for validation in store.list_validation_results(run["id"]):
            all_validations.append(validation)
            latest_run_lookup.setdefault(validation["task_id"], run)

    all_artifacts.sort(key=_artifact_sort_key, reverse=True)
    all_validations.sort(key=lambda item: item["created_at"], reverse=True)
    all_agent_runs.sort(key=lambda item: item["started_at"], reverse=True)

    all_visual_artifacts: list[dict[str, Any]] = []
    latest_visual_artifact_lookup: dict[str, dict[str, Any]] = {}
    for task in tasks:
        task_visual_artifacts = store.list_visual_artifacts(task["project_name"], task_id=task["id"])
        all_visual_artifacts.extend(task_visual_artifacts)
        if task_visual_artifacts:
            latest_visual_artifact_lookup[task["id"]] = task_visual_artifacts[-1]

    all_visual_artifacts.sort(key=_artifact_sort_key, reverse=True)

    latest_artifact_lookup: dict[str, dict[str, Any]] = dict(latest_visual_artifact_lookup)
    for artifact in all_artifacts:
        latest_artifact_lookup.setdefault(artifact["task_id"], artifact)

    latest_validation_lookup: dict[str, dict[str, Any]] = {}
    for validation in all_validations:
        latest_validation_lookup.setdefault(validation["task_id"], validation)

    for task in tasks:
        task_trust_summary_lookup[task["id"]] = store.summarize_task_trust(task["id"])

    milestone_trust_lookup = {
        milestone["id"]: store.summarize_milestone_trust(milestone["id"])
        for milestone in milestones
    }
    project_trust_summary = store.summarize_project_trust(scoped_project) if scoped_project is not None else None

    task_cards = [
        _task_card(
            task,
            project_lookup=project_lookup,
            milestone_lookup=milestone_lookup,
            board_column_lookup=board_column_lookup,
            latest_run_lookup=latest_run_lookup,
            latest_run_work_graph_lookup=latest_run_work_graph_lookup,
            task_run_count_lookup=task_run_count_lookup,
            task_trust_summary_lookup=task_trust_summary_lookup,
            run_compliance_lookup=run_compliance_lookup,
            latest_artifact_lookup=latest_artifact_lookup,
            latest_validation_lookup=latest_validation_lookup,
            store=store,
        )
        for task in tasks
    ]

    board_map = {key: [] for key, _ in board_columns}
    for task in task_cards:
        board_map[store.task_board_column_key(task)].append(task)

    approvals = []
    for approval in scoped_approvals:
        if approval["status"] != "pending":
            continue
        task = task_lookup.get(approval["task_id"]) if approval.get("task_id") else None
        if task:
            bridge_event = None
            task_events: list[dict[str, Any]] = []
            if approval.get("run_id"):
                task_events = store.list_messages(approval["run_id"], task_id=approval["task_id"])
                bridge_event = next(
                    (
                        event
                        for event in reversed(task_events)
                        if event.get("event_type") == "sdk_approval_bridge_requested"
                        and (event.get("payload", {}).get("packet", {}) or {}).get("approval_id") == approval["id"]
                    ),
                    None,
                )
            bridge_packet = ((bridge_event or {}).get("payload") or {}).get("packet") or {}
            upstream_event = next(
                (
                    event
                    for event in reversed(task_events)
                    if event.get("event_type") != "sdk_approval_bridge_requested"
                ),
                None,
            )
            latest_task_artifact = latest_artifact_lookup.get(task["id"])
            latest_task_validation = latest_validation_lookup.get(task["id"])
            action_mode = _action_mode(
                runtime_role=bridge_packet.get("target_role") or approval.get("target_role"),
                source=approval.get("requested_by"),
                event_type=bridge_event.get("event_type") if bridge_event else approval.get("approval_scope"),
            )
            approvals.append(
                {
                    **approval,
                    "approval_id": approval["id"],
                    "approval_lane": "delegated_work",
                    "approval_lane_label": "Delegated Work",
                    "approval_status_label": _status_label(approval["status"]),
                    "task_title": task["title"],
                    "task_status": task["status"],
                    "project_name": task["project_name"],
                    "project_label": _project_label(task["project_name"]),
                    "action_mode": action_mode,
                    "upstream_context": {
                        "requested_by": approval.get("requested_by"),
                        "task_status": task["status"],
                        "exact_task": approval.get("exact_task") or task.get("objective") or task["title"],
                        "why_now": approval.get("why_now") or approval.get("reason"),
                        "latest_signal": ((upstream_event or {}).get("payload") or {}).get("summary")
                        or approval.get("reason"),
                        "latest_artifact_path": latest_task_artifact.get("artifact_path") if latest_task_artifact else None,
                        "latest_validation_summary": latest_task_validation.get("summary") if latest_task_validation else None,
                    },
                    "downstream_context": {
                        "target_role": approval.get("target_role") or bridge_packet.get("target_role"),
                        "expected_output": approval.get("expected_output") or bridge_packet.get("expected_artifact_path"),
                        "continuation_summary": (
                            f"If approved, {(approval.get('target_role') or bridge_packet.get('target_role') or 'the next runtime step')} "
                            f"continues toward {(approval.get('expected_output') or bridge_packet.get('expected_artifact_path') or 'the recorded output')}."
                        ),
                    },
                    "sdk_bridge": {
                        "runtime_mode": bridge_packet.get("runtime_mode"),
                        "session_id": bridge_packet.get("session_id"),
                        "target_role": bridge_packet.get("target_role"),
                        "expected_artifact_path": bridge_packet.get("expected_artifact_path"),
                    }
                    if bridge_packet
                    else None,
                }
            )
        else:
            approvals.append(_pending_approval_card(approval, task=None))

    for approval in scoped_local_exception_approvals:
        if approval["status"] != "pending":
            continue
        task = task_lookup.get(approval["task_id"]) if approval.get("task_id") else None
        approvals.append(_pending_approval_card(approval, task=task))

    approvals.sort(key=lambda item: item.get("created_at") or "")

    all_compliance_records = [record for records in compliance_records_by_run.values() for record in records]
    breach_records = [record for record in all_compliance_records if record["record_kind"] == "breach"]
    local_exception_records = [record for record in all_compliance_records if record["record_kind"] == "local_exception_approved"]
    compliant_records = [record for record in all_compliance_records if record["record_kind"] == "compliant_delegated_run"]
    paused_breach_run_count = sum(1 for run in all_runs if run["status"] == "paused_breach")

    recent_agent_runs = all_agent_runs[:limit]
    for item in recent_agent_runs:
        task = task_lookup.get(item["task_id"])
        item["task_title"] = task["title"] if task else item["task_id"]
        item["project_name"] = task["project_name"] if task else None
        item["project_label"] = _project_label(task["project_name"]) if task else None

    recent_validations = all_validations[:limit]
    for item in recent_validations:
        task = task_lookup.get(item["task_id"])
        item["task_title"] = task["title"] if task else item["task_id"]
        item["project_name"] = task["project_name"] if task else None
        item["project_label"] = _project_label(task["project_name"]) if task else None

    artifacts: list[dict[str, Any]] = []
    visual_artifact_task_ids = {artifact["task_id"] for artifact in all_visual_artifacts}
    for artifact in all_visual_artifacts:
        task = task_lookup.get(artifact["task_id"])
        if task:
            artifacts.append(
                {
                    **artifact,
                    "kind": artifact.get("artifact_kind"),
                    "produced_by": artifact.get("provider"),
                    "task_title": task["title"],
                    "project_name": task["project_name"],
                    "project_label": _project_label(task["project_name"]),
                }
            )
    for artifact in all_artifacts:
        if artifact["task_id"] in visual_artifact_task_ids:
            continue
        task = task_lookup.get(artifact["task_id"])
        if task:
            artifacts.append(
                {
                    **artifact,
                    "task_title": task["title"],
                    "project_name": task["project_name"],
                    "project_label": _project_label(task["project_name"]),
                }
            )
    artifacts.sort(key=_artifact_sort_key, reverse=True)
    recent_artifacts = artifacts[:limit]

    decorated_runs = []
    for run in runs:
        task = task_lookup.get(run["task_id"])
        evidence = store.get_run_evidence(run["id"])
        decorated_runs.append(
            {
                **run,
                "task_title": task["title"] if task else run["task_id"],
                "project_name": task["project_name"] if task else run["project_name"],
                "project_label": _project_label(task["project_name"] if task else run["project_name"]),
                "governed_external_run_summary": _governed_external_run_summary(evidence),
            }
        )

    focus_run = None
    if runs:
        evidence = store.get_run_evidence(runs[0]["id"])
        focus_run = {
            **evidence,
            "task_title": task_lookup.get(runs[0]["task_id"], {}).get("title", runs[0]["task_id"]),
            "compliance": run_compliance_lookup.get(runs[0]["id"]),
        }

    planning_warnings: list[dict[str, Any]] = []
    for task in task_cards:
        issues = task["gate_issues"]
        if issues:
            planning_warnings.append(
                {
                    "task_id": task["id"],
                    "task_title": task["title"],
                    "project_name": task["project_name"],
                    "project_label": task["project_label"],
                    "milestone_title": task.get("milestone_title"),
                    "issues": issues,
                }
            )

    primary_status_counts = {key: len(board_map[key]) for key, _ in board_columns}
    secondary_status_counts = dict(Counter(task["secondary_state"] for task in task_cards if task.get("secondary_state")))
    store_health = store.schema_health()
    health_snapshot = store.load_health_snapshot()
    health_issues = [*store_health.get("issues", []), *(health_snapshot.get("issues") or [])]
    backup_items = store.list_dispatch_backups(project_name=scoped_project, limit=8)
    last_run_summary = decorated_runs[0] if decorated_runs else None
    runtime_mode = (((focus_run or {}).get("sdk_runtime") or {}).get("mode") if focus_run else None) or os.getenv(
        "AISTUDIO_RUNTIME_MODE",
        "custom",
    ).strip().lower()

    summary = {
        "project_name": selected_project,
        "task_count": len(tasks),
        "milestone_count": len(milestones),
        "request_count": sum(1 for task in tasks if task["task_kind"] == "request"),
        "subtask_count": sum(1 for task in tasks if task["task_kind"] == "subtask"),
        "pending_approvals": len(approvals),
        "run_count": len(decorated_runs),
        "agent_run_count": len(recent_agent_runs),
        "validation_count": len(recent_validations),
        "artifact_count": len(recent_artifacts),
        "backup_count": len(backup_items),
        "breach_count": len(breach_records),
        "compliant_run_count": len(compliant_records),
        "local_exception_count": len(local_exception_records),
        "paused_breach_run_count": paused_breach_run_count,
        "pending_delegated_approval_count": sum(1 for approval in approvals if approval["approval_lane"] == "delegated_work"),
        "pending_local_exception_approval_count": sum(1 for approval in approvals if approval["approval_lane"] == "local_exception"),
        "status_counts": primary_status_counts,
        "secondary_state_counts": secondary_status_counts,
        "planning_warning_count": len(planning_warnings),
    }

    project_rollup = _project_rollup(store, projects=registered_projects) if scoped_project is None else []

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "project_name": selected_project,
        "project_label": "All Projects" if scoped_project is None else _project_label(selected_project),
        "canonical_store": str(store.paths.db_path),
        "available_views": ["board", "milestones", "orchestrator"],
        "summary": summary,
        "project_trust_summary": project_trust_summary,
        "compliance": {
            "breach_count": len(breach_records),
            "compliant_run_count": len(compliant_records),
            "local_exception_approved_count": len(local_exception_records),
            "paused_breach_run_count": paused_breach_run_count,
            "pending_delegated_approvals": summary["pending_delegated_approval_count"],
            "pending_local_exception_approvals": summary["pending_local_exception_approval_count"],
        },
        "available_projects": available_projects,
        "project_rollup": project_rollup,
        "system_health": {
            "runtime_mode": runtime_mode,
            "last_backup": backup_items[0] if backup_items else None,
            "available_backups": backup_items,
            "last_run": {
                "id": last_run_summary.get("id"),
                "status": last_run_summary.get("status"),
                "task_title": last_run_summary.get("task_title"),
                "created_at": last_run_summary.get("created_at"),
                "completed_at": last_run_summary.get("completed_at"),
            }
            if last_run_summary
            else None,
            "store": {
                "ok": store_health.get("ok", False) and not health_issues,
                "issue_count": len(health_issues),
                "issues": health_issues,
                "table_count": len(store_health.get("tables", [])),
                "db_size_bytes": store.paths.db_path.stat().st_size if store.paths.db_path.exists() else 0,
            },
            "last_health_check": {
                "ok": health_snapshot.get("ok"),
                "issue_count": len(health_snapshot.get("issues") or []),
                "checked_tables": len(health_snapshot.get("checked_tables") or []),
                "generated_at": datetime.fromtimestamp(
                    store.paths.health_path.stat().st_mtime,
                    tz=timezone.utc,
                ).isoformat(timespec="seconds")
                if store.paths.health_path.exists()
                else None,
            },
        },
        "board": [
            {
                "key": key,
                "name": label,
                "cards": board_map[key],
                "count": len(board_map[key]),
            }
            for key, label in board_columns
        ],
        "milestones": _milestone_cards(
            milestones,
            task_cards=task_cards,
            milestone_trust_lookup=milestone_trust_lookup,
        ),
        "planning_warnings": planning_warnings,
        "pending_approvals": approvals,
        "recent_runs": decorated_runs,
        "recent_agent_runs": recent_agent_runs,
        "recent_validations": recent_validations,
        "recent_artifacts": recent_artifacts,
        "recent_updates": _recent_updates(
            task_cards=task_cards,
            approvals=scoped_approvals,
            runs=decorated_runs,
            agent_runs=recent_agent_runs,
            validations=recent_validations,
            artifacts=recent_artifacts,
            task_lookup=task_lookup,
            limit=limit,
        ),
        "focus_run": focus_run,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Build an operator wall snapshot from the canonical SQLite store.")
    parser.add_argument("--project", default="all")
    args = parser.parse_args()
    snapshot = build_snapshot(ROOT, project_name=args.project)
    print(json.dumps(snapshot, ensure_ascii=True))


if __name__ == "__main__":
    main()
