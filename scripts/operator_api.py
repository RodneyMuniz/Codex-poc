from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agents.orchestrator import Orchestrator, run_async
from intake.ingress import dispatch_operator_request, preview_operator_request
from sessions import SessionStore
from state_machine import ensure_first_slice_stage_completion, ensure_first_slice_stage_start
from workspace_root import ensure_authoritative_workspace_path, ensure_authoritative_workspace_root


AIOFFICE_SUPERVISED_REHEARSAL_TASK = (
    "Prepare an architect-stage decision for a one-paragraph authoritative-root reminder note."
)
AIOFFICE_SUPERVISED_REHEARSAL_ROOT = (
    "projects/aioffice/artifacts/m5_supervised_operator_cli_rehearsal/workspace"
)
AIOFFICE_FIRST_SLICE = ("intake", "pm", "context_audit", "architect")


def _orchestrator() -> Orchestrator:
    ensure_authoritative_workspace_root(ROOT, label="operator_api root")
    return Orchestrator(ROOT)


def _routing_catalog() -> dict[str, Any]:
    try:
        from agents.config import routing_catalog
    except ImportError:
        return {}
    return routing_catalog()


def _resolve_control_kernel_packet_context(store: Any, packet: dict[str, Any]) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    stage_run = None
    workflow_run = None
    stage_run_id = packet.get("stage_run_id")
    workflow_run_id = packet.get("workflow_run_id")
    if stage_run_id:
        stage_run = store.get_stage_run(stage_run_id)
        if stage_run is None:
            raise ValueError(f"Packet references unknown stage_run_id: {stage_run_id}")
        workflow_run_id = workflow_run_id or stage_run.get("workflow_run_id")
    if workflow_run_id:
        workflow_run = store.get_workflow_run(workflow_run_id)
        if workflow_run is None:
            raise ValueError(f"Packet references unknown workflow_run_id: {workflow_run_id}")
    if stage_run is not None and workflow_run is not None and stage_run.get("workflow_run_id") != workflow_run["id"]:
        raise ValueError("Packet stage/workflow context is inconsistent.")
    return workflow_run, stage_run


def _require_matching_context(
    *,
    selected_id: str | None,
    actual_id: str | None,
    label: str,
) -> None:
    if selected_id is not None and actual_id != selected_id:
        raise ValueError(f"{label} does not match the requested inspection context.")


def _load_required_records(store: Any, ids: list[str], getter_name: str, label: str) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    getter = getattr(store, getter_name)
    for record_id in ids:
        record = getter(record_id)
        if record is None:
            raise ValueError(f"{label} not found: {record_id}")
        records.append(record)
    return records


def _control_kernel_details(
    store: Any,
    *,
    workflow_run_id: str | None = None,
    stage_run_id: str | None = None,
    packet_id: str | None = None,
    bundle_id: str | None = None,
) -> dict[str, Any]:
    if not any([workflow_run_id, stage_run_id, packet_id, bundle_id]):
        raise ValueError("At least one control-kernel identifier is required.")

    workflow_run = store.get_workflow_run(workflow_run_id) if workflow_run_id else None
    if workflow_run_id and workflow_run is None:
        raise ValueError(f"Workflow run not found: {workflow_run_id}")

    stage_run = store.get_stage_run(stage_run_id) if stage_run_id else None
    if stage_run_id and stage_run is None:
        raise ValueError(f"Stage run not found: {stage_run_id}")
    if stage_run is not None:
        _require_matching_context(
            selected_id=workflow_run_id,
            actual_id=stage_run.get("workflow_run_id"),
            label="stage_run_id",
        )
        if workflow_run is None:
            workflow_run = store.get_workflow_run(stage_run["workflow_run_id"])
            if workflow_run is None:
                raise ValueError(f"Workflow run not found: {stage_run['workflow_run_id']}")

    packet = store.get_control_execution_packet(packet_id) if packet_id else None
    if packet_id and packet is None:
        raise ValueError(f"Control execution packet not found: {packet_id}")

    bundle = store.get_execution_bundle(bundle_id) if bundle_id else None
    if bundle_id and bundle is None:
        raise ValueError(f"Execution bundle not found: {bundle_id}")
    if bundle is not None:
        if packet is None:
            packet = store.get_control_execution_packet(bundle["packet_id"])
            if packet is None:
                raise ValueError(f"Execution bundle references unknown packet_id: {bundle['packet_id']}")
        elif bundle["packet_id"] != packet["packet_id"]:
            raise ValueError("bundle_id does not belong to the requested packet_id.")

    if packet is not None:
        packet_workflow_run, packet_stage_run = _resolve_control_kernel_packet_context(store, packet)
        if packet_stage_run is not None:
            _require_matching_context(
                selected_id=stage_run_id,
                actual_id=packet_stage_run["id"],
                label="packet_id",
            )
            if stage_run is None:
                stage_run = packet_stage_run
        elif stage_run_id is not None:
            raise ValueError("packet_id does not declare the requested stage_run_id.")
        if packet_workflow_run is not None:
            _require_matching_context(
                selected_id=workflow_run_id,
                actual_id=packet_workflow_run["id"],
                label="packet_id",
            )
            if workflow_run is None:
                workflow_run = packet_workflow_run
        elif workflow_run_id is not None:
            raise ValueError("packet_id does not declare the requested workflow_run_id.")

    if bundle is not None:
        bundle_workflow_run_id = bundle.get("workflow_run_id")
        bundle_stage_run_id = bundle.get("stage_run_id")
        if bundle_workflow_run_id is not None:
            _require_matching_context(
                selected_id=workflow_run["id"] if workflow_run else workflow_run_id,
                actual_id=bundle_workflow_run_id,
                label="bundle_id",
            )
        if bundle_stage_run_id is not None:
            _require_matching_context(
                selected_id=stage_run["id"] if stage_run else stage_run_id,
                actual_id=bundle_stage_run_id,
                label="bundle_id",
            )

    payload: dict[str, Any] = {}
    if workflow_run is not None:
        payload["workflow_run"] = workflow_run
        payload["stage_runs"] = store.list_stage_runs(workflow_run["id"])
        payload["workflow_artifacts"] = store.list_workflow_artifacts(workflow_run["id"])
        payload["handoffs"] = store.list_handoffs(workflow_run["id"])
        payload["blockers"] = store.list_blockers(workflow_run["id"])
        payload["question_or_assumptions"] = store.list_question_or_assumptions(workflow_run["id"])
        payload["orchestration_traces"] = store.list_orchestration_traces(workflow_run["id"])
        payload["control_execution_packets"] = store.list_control_execution_packets(workflow_run_id=workflow_run["id"])
        payload["execution_bundles"] = store.list_execution_bundles(workflow_run_id=workflow_run["id"])
    if stage_run is not None:
        payload["stage_run"] = stage_run
        if workflow_run is not None:
            payload["stage_workflow_artifacts"] = store.list_workflow_artifacts(
                workflow_run["id"],
                stage_run_id=stage_run["id"],
            )
            payload["stage_orchestration_traces"] = store.list_orchestration_traces(
                workflow_run["id"],
                stage_run_id=stage_run["id"],
            )
            payload["stage_control_execution_packets"] = store.list_control_execution_packets(
                workflow_run_id=workflow_run["id"],
                stage_run_id=stage_run["id"],
            )
            payload["stage_blockers"] = [
                item for item in payload["blockers"] if item.get("stage_run_id") == stage_run["id"]
            ]
            payload["stage_questions_or_assumptions"] = [
                item for item in payload["question_or_assumptions"] if item.get("stage_run_id") == stage_run["id"]
            ]
            payload["stage_handoffs"] = [
                item for item in payload["handoffs"] if item.get("stage_run_id") == stage_run["id"]
            ]
            payload["stage_execution_bundles"] = [
                item for item in payload["execution_bundles"] if item.get("stage_run_id") == stage_run["id"]
            ]
    if packet is not None:
        payload["control_execution_packet"] = packet
        payload["packet_execution_bundles"] = store.list_execution_bundles(packet_id=packet["packet_id"])
    if bundle is not None:
        payload["execution_bundle"] = bundle
        payload["bundle_workflow_artifacts"] = _load_required_records(
            store,
            bundle.get("produced_artifact_ids", []),
            "get_workflow_artifact",
            "Bundle artifact",
        )
        payload["bundle_blockers"] = _load_required_records(
            store,
            bundle.get("blocker_ids", []),
            "get_blocker",
            "Bundle blocker",
        )
        payload["bundle_questions"] = _load_required_records(
            store,
            bundle.get("question_ids", []),
            "get_question_or_assumption",
            "Bundle question",
        )
        payload["bundle_assumptions"] = _load_required_records(
            store,
            bundle.get("assumption_ids", []),
            "get_question_or_assumption",
            "Bundle assumption",
        )
    return payload


def _resolve_control_kernel_workspace_root(repo_root: Path, workspace_root: str | None) -> Path | None:
    normalized = " ".join(str(workspace_root or "").split())
    if not normalized:
        return None
    candidate = Path(normalized)
    if not candidate.is_absolute():
        candidate = repo_root / candidate
    return ensure_authoritative_workspace_path(candidate, label="control-kernel-details workspace")


def _inspection_store_for_control_kernel(repo_root: Path, workspace_root: str | None) -> tuple[Any, Path | None]:
    inspection_workspace_root = _resolve_control_kernel_workspace_root(repo_root, workspace_root)
    if inspection_workspace_root is None:
        return _orchestrator().store, None
    database_path = inspection_workspace_root / "sessions" / "studio.db"
    if not database_path.exists():
        raise ValueError(
            "control-kernel-details workspace must already contain a sanctioned persisted store at sessions/studio.db."
    )
    return SessionStore(inspection_workspace_root, bootstrap_legacy_defaults=False), inspection_workspace_root


def _require_cli_non_empty_text(field_name: str, value: str | None) -> str:
    text = str(value or "").strip()
    if not text:
        raise ValueError(f"{field_name} is required.")
    return text


def _normalize_bundle_decision_action(action: str | None) -> str:
    normalized = _require_cli_non_empty_text("action", action)
    if normalized not in {"apply", "promote"}:
        raise ValueError("action must be either 'apply' or 'promote'.")
    return normalized


def _parse_destination_mappings_payload(raw_value: str, *, field_name: str) -> list[dict[str, Any]]:
    normalized = str(raw_value).strip()
    if not normalized:
        raise ValueError(f"{field_name} must not be empty.")
    try:
        decoded = json.loads(normalized)
    except json.JSONDecodeError as exc:
        raise ValueError(f"{field_name} must contain valid JSON.") from exc
    if not isinstance(decoded, list):
        raise ValueError(f"{field_name} must decode to a JSON array.")
    if not decoded:
        raise ValueError(f"{field_name} must not be empty.")
    return decoded


def _load_destination_mappings_file(repo_root: Path, raw_path: str | None) -> tuple[str, list[dict[str, Any]]]:
    normalized = _require_cli_non_empty_text("destination_mappings_file", raw_path)
    candidate = Path(normalized)
    if not candidate.is_absolute():
        candidate = repo_root / candidate
    resolved = candidate.resolve()
    if not resolved.exists():
        raise ValueError(f"destination_mappings_file does not exist: {normalized}")
    if resolved.is_dir():
        raise ValueError("destination_mappings_file must point to a file.")
    try:
        raw_payload = resolved.read_text(encoding="utf-8")
    except OSError as exc:
        raise ValueError(f"destination_mappings_file is not readable: {resolved}") from exc
    decoded = _parse_destination_mappings_payload(
        raw_payload,
        field_name="destination_mappings_file",
    )
    return str(resolved), decoded


def _bundle_decision_snapshot(inspection: dict[str, Any]) -> dict[str, Any]:
    workflow_run = inspection.get("workflow_run") or {}
    stage_run = inspection.get("stage_run") or {}
    packet = inspection.get("control_execution_packet") or {}
    bundle = inspection.get("execution_bundle") or {}
    return {
        "workflow_run_id": workflow_run.get("id"),
        "stage_run_id": stage_run.get("id"),
        "packet_id": packet.get("packet_id"),
        "bundle_id": bundle.get("bundle_id"),
        "task_id": packet.get("task_id"),
        "bundle_acceptance_state": bundle.get("acceptance_state"),
        "authoritative_workspace_root": packet.get("authoritative_workspace_root"),
        "produced_artifact_ids": bundle.get("produced_artifact_ids", []),
        "evidence_receipt_kinds": [
            receipt.get("kind")
            for receipt in bundle.get("evidence_receipts", [])
            if isinstance(receipt, dict)
        ],
    }


def _execute_control_kernel_bundle_decision(
    repo_root: Path,
    *,
    bundle_id: str,
    action: str,
    approved_by: str,
    destination_mappings_file: str,
    decision_note: str | None = None,
    workspace_root: str | None = None,
) -> dict[str, Any]:
    normalized_bundle_id = _require_cli_non_empty_text("bundle_id", bundle_id)
    normalized_action = _normalize_bundle_decision_action(action)
    normalized_approved_by = _require_cli_non_empty_text("approved_by", approved_by)
    resolved_destination_mappings_file, normalized_destination_mappings = _load_destination_mappings_file(
        repo_root,
        destination_mappings_file,
    )

    normalized_decision_note = None
    if decision_note is not None:
        normalized_decision_note = str(decision_note).strip()
        if not normalized_decision_note:
            raise ValueError("decision_note must not be blank.")

    decision_store, inspection_workspace_root = _inspection_store_for_control_kernel(repo_root, workspace_root)
    inspection_before = _control_kernel_details(
        decision_store,
        bundle_id=normalized_bundle_id,
    )
    approved_decision = {
        "decision": "approved",
        "action": normalized_action,
        "approved_by": normalized_approved_by,
    }
    if normalized_decision_note is not None:
        approved_decision["decision_note"] = normalized_decision_note

    updated_bundle = decision_store.execute_apply_promotion_decision(
        normalized_bundle_id,
        approved_decision=approved_decision,
        destination_mappings=normalized_destination_mappings,
    )
    inspection_after = _control_kernel_details(
        decision_store,
        bundle_id=normalized_bundle_id,
    )

    payload: dict[str, Any] = {
        "command": "bundle-decision",
        "bundle_id": normalized_bundle_id,
        "approved_decision": approved_decision,
        "destination_mappings_file": resolved_destination_mappings_file,
        "destination_mappings": normalized_destination_mappings,
        "updated_bundle": updated_bundle,
        "inspection_before": _bundle_decision_snapshot(inspection_before),
        "inspection_after": _bundle_decision_snapshot(inspection_after),
    }
    if inspection_workspace_root is not None:
        payload["inspection_workspace_root"] = str(inspection_workspace_root)
    return payload


def _utc_now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")


def _relative_path(root: Path, path: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def _artifact_metadata_receipt(store: SessionStore, artifact_path: str, *, kind: str) -> dict[str, Any]:
    metadata = store.file_metadata(artifact_path)
    return {
        "kind": kind,
        "artifact_path": metadata["artifact_path"],
        "artifact_sha256": metadata["artifact_sha256"],
        "bytes_written": metadata["bytes_written"],
        "modified_at": metadata["modified_at"],
    }


def _aioffice_supervised_rehearsal_store(
    repo_root: Path,
    *,
    rehearsal_root: str,
) -> tuple[SessionStore, Path]:
    ensure_authoritative_workspace_root(repo_root, label="operator_api root")
    workspace_root = ensure_authoritative_workspace_path(
        repo_root / rehearsal_root,
        label="AIOffice supervised rehearsal workspace",
    )
    workspace_root.mkdir(parents=True, exist_ok=True)
    (workspace_root / "sessions").mkdir(parents=True, exist_ok=True)
    (workspace_root / "sessions" / "approvals.json").write_text("", encoding="utf-8")
    store = SessionStore(workspace_root, bootstrap_legacy_defaults=False)
    return store, workspace_root


def _ensure_unambiguous_aioffice_rehearsal_context(store: SessionStore, *, task_id: str) -> None:
    active = store.list_workflow_runs(project_name="aioffice", task_id=task_id, status="active")
    if active:
        raise ValueError(
            "Ambiguous run/stage state: an active AIOffice supervised rehearsal workflow already exists for this task."
        )


def _stage_artifact_paths(base_dir: Path) -> dict[str, Path]:
    return {
        "intake_request_v1": base_dir / "intake" / "intake_request_v1.md",
        "pm_plan_v1": base_dir / "pm" / "pm_plan_v1.md",
        "pm_assumption_register_v1": base_dir / "pm" / "pm_assumption_register_v1.md",
        "context_audit_report_v1": base_dir / "context_audit" / "context_audit_report_v1.md",
        "architecture_decision_v1": base_dir / "architect" / "architecture_decision_v1.md",
        "provider_external_proof_v1": base_dir / "architect" / "provider_external_proof_v1.json",
        "architect_reconciliation_v1": base_dir / "architect" / "architect_reconciliation_v1.json",
    }


def _create_stage_artifact(
    store: SessionStore,
    *,
    workflow_run_id: str,
    stage_run_id: str,
    task_id: str,
    contract_name: str,
    artifact_path: Path,
    content: str,
    kind: str = "document",
    proof_value: str = "stage_output",
    source_packet_id: str | None = None,
    input_artifact_paths: list[str] | None = None,
) -> dict[str, Any]:
    _write_text(artifact_path, content)
    return store.create_workflow_artifact(
        "aioffice",
        workflow_run_id=workflow_run_id,
        stage_run_id=stage_run_id,
        task_id=task_id,
        contract_name=contract_name,
        kind=kind,
        content=content,
        proof_value=proof_value,
        artifact_path=_relative_path(store.paths.repo_root, artifact_path),
        produced_by="operator_api supervised rehearsal",
        source_packet_id=source_packet_id,
        input_artifact_paths=input_artifact_paths,
    )


def _validate_rehearsal_reconciliation(
    *,
    store: SessionStore,
    workflow_run_id: str,
    architect_stage_run_id: str,
    packet: dict[str, Any],
    bundle: dict[str, Any],
    inspection: dict[str, Any],
    produced_artifacts: list[dict[str, Any]],
    provider_proof_receipt: dict[str, Any] | None,
    stop_after: str,
) -> dict[str, Any]:
    if stop_after != "architect":
        raise ValueError("AIOffice supervised rehearsal is bounded to architect-stage only.")
    if provider_proof_receipt is None or not str(provider_proof_receipt.get("provider_request_id") or "").strip():
        raise ValueError("Provider/external proof is required for the supervised architect rehearsal.")
    if bundle.get("acceptance_state") != "pending_review":
        raise ValueError("Execution bundle must remain pending_review.")
    if inspection.get("execution_bundle", {}).get("acceptance_state") != "pending_review":
        raise ValueError("Inspection must confirm that the execution bundle remains pending_review.")

    required_output_paths = set(packet.get("required_artifact_outputs") or [])
    observed_output_paths = {
        str(artifact.get("artifact_path") or "")
        for artifact in produced_artifacts
        if str(artifact.get("artifact_path") or "").strip()
    }
    missing_outputs = sorted(required_output_paths - observed_output_paths)
    if missing_outputs:
        raise ValueError(f"Missing required packet outputs: {', '.join(missing_outputs)}")

    architect_artifact = next(
        (artifact for artifact in produced_artifacts if artifact.get("contract_name") == "architecture_decision_v1"),
        None,
    )
    if architect_artifact is None:
        raise ValueError("architect-stage artifact missing: architecture_decision_v1")
    if architect_artifact.get("stage_run_id") != architect_stage_run_id:
        raise ValueError("architect-stage artifact does not belong to the requested architect attempt.")

    architect_completion = ensure_first_slice_stage_completion(
        store,
        workflow_run_id,
        stage_name="architect",
        stage_run_id=architect_stage_run_id,
    )
    if not architect_completion["allowed"]:
        raise ValueError("architect completion could not be proven from persisted artifact state.")

    stage_runs = inspection.get("stage_runs") or []
    unexpected_stages = [
        stage_run.get("stage_name")
        for stage_run in stage_runs
        if str(stage_run.get("stage_name") or "") not in AIOFFICE_FIRST_SLICE
    ]
    if unexpected_stages:
        raise ValueError(
            "Later-stage continuation is not allowed in the supervised architect rehearsal: "
            + ", ".join(sorted({str(item) for item in unexpected_stages}))
        )

    return {
        "status": "reconciled",
        "matched_required_outputs": True,
        "architect_stage_complete": architect_completion["allowed"],
        "bundle_pending_review": True,
        "provider_external_proof_present": True,
        "continued_beyond_architect": False,
        "observed_output_paths": sorted(observed_output_paths),
    }


def _run_aioffice_supervised_architect_rehearsal(
    repo_root: Path,
    *,
    task_id: str,
    operator_name: str,
    provider_request_id: str,
    reconciliation_evidence_source: str,
    rehearsal_root: str = AIOFFICE_SUPERVISED_REHEARSAL_ROOT,
    rehearsal_task: str = AIOFFICE_SUPERVISED_REHEARSAL_TASK,
    stop_after: str = "architect",
    confirm_supervised: bool,
    create_architecture_artifact: bool = True,
    create_provider_proof: bool = True,
) -> dict[str, Any]:
    if not confirm_supervised:
        raise ValueError("Supervised rehearsal requires explicit operator confirmation.")
    normalized_operator = " ".join(str(operator_name or "").split())
    if not normalized_operator:
        raise ValueError("operator_name is required.")
    normalized_provider_request_id = " ".join(str(provider_request_id or "").split())
    if not normalized_provider_request_id:
        raise ValueError("provider_request_id is required.")
    normalized_reconciliation_source = " ".join(str(reconciliation_evidence_source or "").split())
    if not normalized_reconciliation_source:
        raise ValueError("reconciliation_evidence_source is required.")
    if stop_after != "architect":
        raise ValueError("AIOffice supervised rehearsal must stop after architect.")

    store, workspace_root = _aioffice_supervised_rehearsal_store(repo_root, rehearsal_root=rehearsal_root)
    _ensure_unambiguous_aioffice_rehearsal_context(store, task_id=task_id)

    workflow = store.create_workflow_run(
        "aioffice",
        task_id=task_id,
        objective=rehearsal_task,
        authoritative_workspace_root="projects/aioffice",
        current_stage="architect",
        scope={
            "non_trivial": True,
            "rehearsal": "M5 supervised operator CLI",
            "stop_after": stop_after,
            "operator": normalized_operator,
        },
    )
    stage_runs = {
        "intake": store.create_stage_run(workflow["id"], stage_name="intake", attempt_number=1, status="completed"),
        "pm": store.create_stage_run(workflow["id"], stage_name="pm", attempt_number=1, status="completed"),
        "context_audit": store.create_stage_run(
            workflow["id"],
            stage_name="context_audit",
            attempt_number=1,
            status="completed",
        ),
        "architect": store.create_stage_run(
            workflow["id"],
            stage_name="architect",
            attempt_number=1,
            status="in_progress",
        ),
    }
    stage_base_dir = (
        workspace_root
        / "projects"
        / "aioffice"
        / "artifacts"
        / "m5_supervised_operator_cli_rehearsal"
        / workflow["id"]
    )
    artifact_paths = _stage_artifact_paths(stage_base_dir)

    intake_artifact = _create_stage_artifact(
        store,
        workflow_run_id=workflow["id"],
        stage_run_id=stage_runs["intake"]["id"],
        task_id=task_id,
        contract_name="intake_request_v1",
        artifact_path=artifact_paths["intake_request_v1"],
        content=(
            "# Intake Request\n\n"
            f"- original_request: {rehearsal_task}\n"
            "- explicit_objective: prove one supervised operator CLI architect-stop rehearsal\n"
            "- authoritative_workspace_path: projects/aioffice\n"
            "- duplicate_workspace_note: Documents duplicate root remains non-authoritative\n"
        ),
        proof_value="intake_output",
    )
    pm_plan_artifact = _create_stage_artifact(
        store,
        workflow_run_id=workflow["id"],
        stage_run_id=stage_runs["pm"]["id"],
        task_id=task_id,
        contract_name="pm_plan_v1",
        artifact_path=artifact_paths["pm_plan_v1"],
        content=(
            "# PM Plan\n\n"
            "- problem_framing: prove operator CLI invocation against sanctioned persisted state\n"
            "- scope: first slice through architect only\n"
            "- out_of_scope: apply/promotion, later stages, unattended execution\n"
            "- decomposition: intake -> pm -> context_audit -> architect\n"
            "- intended_stage_path: intake, pm, context_audit, architect\n"
        ),
        proof_value="stage_output",
    )
    pm_assumption_artifact = _create_stage_artifact(
        store,
        workflow_run_id=workflow["id"],
        stage_run_id=stage_runs["pm"]["id"],
        task_id=task_id,
        contract_name="pm_assumption_register_v1",
        artifact_path=artifact_paths["pm_assumption_register_v1"],
        content=(
            "# PM Assumption Register\n\n"
            "- assumption: one supervised architect-stop rehearsal is sufficient for this bounded increment\n"
            "- impact_or_risk: broader multi-run behavior remains unproven\n"
            "- open_implication: no autonomy claim can be made from this rehearsal alone\n"
        ),
        proof_value="stage_output",
    )
    context_artifact = _create_stage_artifact(
        store,
        workflow_run_id=workflow["id"],
        stage_run_id=stage_runs["context_audit"]["id"],
        task_id=task_id,
        contract_name="context_audit_report_v1",
        artifact_path=artifact_paths["context_audit_report_v1"],
        content=(
            "# Context Audit Report\n\n"
            "- sources_checked: sessions/store.py, scripts/operator_api.py, state_machine.py\n"
            "- relevant_context_found: persisted workflow entities, packet/bundle path, read-only inspection path\n"
            "- gaps: no apply/promotion, no unattended scheduling, no later-stage proof\n"
            "- risks: missing provider proof or stale stage evidence must fail closed\n"
        ),
        proof_value="audit_output",
    )

    handoffs = {
        "intake_to_pm": store.create_handoff(
            workflow["id"],
            from_stage_name="intake",
            to_stage_name="pm",
            summary="Intake request is ready for PM review.",
            stage_run_id=stage_runs["intake"]["id"],
            upstream_artifact_ids=[intake_artifact["id"]],
        ),
        "pm_to_context_audit": store.create_handoff(
            workflow["id"],
            from_stage_name="pm",
            to_stage_name="context_audit",
            summary="PM plan and assumption branch are ready for context audit.",
            stage_run_id=stage_runs["pm"]["id"],
            upstream_artifact_ids=[pm_plan_artifact["id"], pm_assumption_artifact["id"]],
        ),
        "context_audit_to_architect": store.create_handoff(
            workflow["id"],
            from_stage_name="context_audit",
            to_stage_name="architect",
            summary="Context audit is ready for architect-stage review.",
            stage_run_id=stage_runs["context_audit"]["id"],
            upstream_artifact_ids=[context_artifact["id"]],
        ),
    }
    question = store.create_question_or_assumption(
        workflow["id"],
        record_type="question",
        summary="Should the operator CLI rehearsal keep using an isolated workspace root?",
        stage_run_id=stage_runs["architect"]["id"],
        why_it_matters="Isolation must stay explicit while proof remains supervised.",
    )
    assumption = store.create_question_or_assumption(
        workflow["id"],
        record_type="assumption",
        summary="Architect-stop remains the hard boundary for this rehearsal command.",
        stage_run_id=stage_runs["architect"]["id"],
        impact_or_risk="Any later-stage continuation would violate the bounded task.",
    )
    review_blocker = store.create_blocker(
        workflow["id"],
        blocker_kind="review_pending",
        summary="Bundle review is still required after supervised rehearsal completion.",
        stage_run_id=stage_runs["architect"]["id"],
    )
    store.record_orchestration_trace(
        workflow["id"],
        stage_run_id=stage_runs["architect"]["id"],
        source="operator_api",
        event_type="supervised_rehearsal_started",
        payload={"operator": normalized_operator, "stop_after": stop_after},
    )

    gate_checks = {
        "intake_completion": ensure_first_slice_stage_completion(
            store,
            workflow["id"],
            stage_name="intake",
            stage_run_id=stage_runs["intake"]["id"],
        ),
        "pm_start": ensure_first_slice_stage_start(
            store,
            workflow["id"],
            stage_name="pm",
            stage_run_id=stage_runs["pm"]["id"],
        ),
        "pm_completion": ensure_first_slice_stage_completion(
            store,
            workflow["id"],
            stage_name="pm",
            stage_run_id=stage_runs["pm"]["id"],
        ),
        "context_audit_start": ensure_first_slice_stage_start(
            store,
            workflow["id"],
            stage_name="context_audit",
            stage_run_id=stage_runs["context_audit"]["id"],
        ),
        "context_audit_completion": ensure_first_slice_stage_completion(
            store,
            workflow["id"],
            stage_name="context_audit",
            stage_run_id=stage_runs["context_audit"]["id"],
        ),
        "architect_start": ensure_first_slice_stage_start(
            store,
            workflow["id"],
            stage_name="architect",
            stage_run_id=stage_runs["architect"]["id"],
        ),
    }

    packet = store.issue_control_execution_packet(
        "aioffice",
        task_id,
        objective="Produce the architect-stage decision, provider proof artifact, and bounded evidence bundle.",
        authoritative_workspace_root="projects/aioffice",
        allowed_write_paths=[
            _relative_path(workspace_root, artifact_paths["architecture_decision_v1"]),
            _relative_path(workspace_root, artifact_paths["provider_external_proof_v1"]),
            _relative_path(workspace_root, artifact_paths["architect_reconciliation_v1"]),
        ],
        scratch_path="tmp/aioffice/m5_supervised_operator_cli",
        forbidden_paths=["projects/aioffice/governance", "scripts", "app"],
        forbidden_actions=["self_accept", "self_promote", "publish", "continue_beyond_architect"],
        required_artifact_outputs=[
            _relative_path(workspace_root, artifact_paths["architecture_decision_v1"]),
            _relative_path(workspace_root, artifact_paths["provider_external_proof_v1"]),
        ],
        required_validations=[
            "first-slice gate checks remain fail-closed",
            "operator_api control-kernel details read sanctioned persisted state",
        ],
        expected_return_bundle_contents=[
            "produced artifacts",
            "provider/external proof receipts",
            "open risks",
            "self-report summary",
        ],
        failure_reporting_expectations=[
            "report blockers",
            "report questions",
            "report assumptions",
            "report proof gaps",
        ],
        workflow_run_id=workflow["id"],
        stage_run_id=stage_runs["architect"]["id"],
        issued_by=normalized_operator,
        provenance_note=f"{task_id} supervised operator CLI architect rehearsal",
    )

    produced_artifacts: list[dict[str, Any]] = []
    if create_architecture_artifact:
        produced_artifacts.append(
            _create_stage_artifact(
                store,
                workflow_run_id=workflow["id"],
                stage_run_id=stage_runs["architect"]["id"],
                task_id=task_id,
                contract_name="architecture_decision_v1",
                artifact_path=artifact_paths["architecture_decision_v1"],
                content=(
                    "# Architecture Decision\n\n"
                    "- chosen_approach: run one explicit supervised operator CLI rehearsal in an isolated workspace\n"
                    "- rationale: prove sanctioned packet/bundle, inspection, and gate flow without broadening authority\n"
                    "- tradeoffs: later-stage execution, apply/promotion, and unattended behavior remain out of scope\n"
                    "- dependencies: first-slice stage artifacts, provider proof, pending bundle review\n"
                    "- downstream_implications: next work should harden end-to-end CLI invocation and apply/promotion under supervision\n"
                ),
                proof_value="architecture_output",
                source_packet_id=packet["packet_id"],
                input_artifact_paths=[
                    intake_artifact["artifact_path"],
                    pm_plan_artifact["artifact_path"],
                    pm_assumption_artifact["artifact_path"],
                    context_artifact["artifact_path"],
                ],
            )
        )

    provider_proof_receipt: dict[str, Any] | None = None
    if create_provider_proof:
        provider_proof_payload = {
            "provider": "supervised_operator_cli",
            "model": "architect_stop_rehearsal",
            "provider_request_id": normalized_provider_request_id,
            "execution_path": "operator_api.aioffice-supervised-architect-rehearsal",
            "workspace_root": str(workspace_root),
            "captured_at": _utc_now(),
            "operator": normalized_operator,
            "stop_after": stop_after,
        }
        _write_json(artifact_paths["provider_external_proof_v1"], provider_proof_payload)
        produced_artifacts.append(
            store.create_workflow_artifact(
                "aioffice",
                workflow_run_id=workflow["id"],
                stage_run_id=stage_runs["architect"]["id"],
                task_id=task_id,
                contract_name="provider_external_proof_v1",
                kind="json",
                content=json.dumps(provider_proof_payload, ensure_ascii=True, indent=2),
                proof_value="external_proof",
                artifact_path=_relative_path(workspace_root, artifact_paths["provider_external_proof_v1"]),
                produced_by="operator_api supervised rehearsal",
                source_packet_id=packet["packet_id"],
                input_artifact_paths=[
                    artifact.get("artifact_path")
                    for artifact in produced_artifacts
                    if str(artifact.get("artifact_path") or "").strip()
                ],
            )
        )
        provider_proof_receipt = {
            "kind": "provider_metadata",
            "provider": provider_proof_payload["provider"],
            "model": provider_proof_payload["model"],
            "provider_request_id": provider_proof_payload["provider_request_id"],
            "execution_path": provider_proof_payload["execution_path"],
            "captured_at": provider_proof_payload["captured_at"],
        }

    architect_output = next(
        (artifact for artifact in produced_artifacts if artifact.get("contract_name") == "architecture_decision_v1"),
        None,
    )
    if architect_output is None:
        raise ValueError("architect-stage artifact missing for supervised rehearsal.")
    if provider_proof_receipt is None:
        raise ValueError("provider/external proof missing for supervised rehearsal.")
    gate_checks["architect_completion"] = ensure_first_slice_stage_completion(
        store,
        workflow["id"],
        stage_name="architect",
        stage_run_id=stage_runs["architect"]["id"],
    )

    command_preview = " ".join(
        [
            Path(sys.executable).name,
            "scripts/operator_api.py",
            "aioffice-supervised-architect-rehearsal",
            f'--task-id "{task_id}"',
            "--confirm-supervised",
            f'--operator "{normalized_operator}"',
            f'--provider-request-id "{normalized_provider_request_id}"',
            f'--reconciliation-evidence-source "{normalized_reconciliation_source}"',
        ]
    )
    evidence_receipts = [provider_proof_receipt]
    for artifact in produced_artifacts:
        artifact_path = str(artifact.get("artifact_path") or "").strip()
        if artifact_path:
            evidence_receipts.append(
                _artifact_metadata_receipt(
                    store,
                    artifact_path,
                    kind="external_file_observation",
                )
            )

    bundle = store.ingest_execution_bundle(
        packet["packet_id"],
        produced_artifact_ids=[artifact["id"] for artifact in produced_artifacts],
        diff_refs=[artifact["artifact_path"] for artifact in produced_artifacts if artifact.get("artifact_path")],
        commands_run=[command_preview],
        test_results=[
            {"check": "architect_start", "status": "passed"},
            {"check": "architect_completion", "status": "passed"},
        ],
        blocker_ids=[review_blocker["id"]],
        question_ids=[question["id"]],
        assumption_ids=[assumption["id"]],
        self_report_summary="Supervised operator CLI architect rehearsal completed with pending_review bundle state.",
        open_risks=[
            "Apply/promotion remains out of scope.",
            "No unattended or later-stage behavior was exercised.",
        ],
        evidence_receipts=evidence_receipts,
    )

    inspection = _control_kernel_details(
        store,
        workflow_run_id=workflow["id"],
        stage_run_id=stage_runs["architect"]["id"],
        packet_id=packet["packet_id"],
        bundle_id=bundle["bundle_id"],
    )
    reconciliation_result = _validate_rehearsal_reconciliation(
        store=store,
        workflow_run_id=workflow["id"],
        architect_stage_run_id=stage_runs["architect"]["id"],
        packet=packet,
        bundle=bundle,
        inspection=inspection,
        produced_artifacts=produced_artifacts,
        provider_proof_receipt=provider_proof_receipt,
        stop_after=stop_after,
    )

    reconciliation_payload = {
        "execution_claims": {
            "workflow_run_id": workflow["id"],
            "packet_id": packet["packet_id"],
            "bundle_id": bundle["bundle_id"],
            "objective": packet["objective"],
            "self_report_summary": bundle["self_report_summary"],
            "commands_run": bundle["commands_run"],
            "stop_after": stop_after,
        },
        "stage_artifacts": [
            {
                "artifact_id": artifact["id"],
                "contract_name": artifact["contract_name"],
                "stage_run_id": artifact.get("stage_run_id"),
                "artifact_path": artifact.get("artifact_path"),
                "proof_value": artifact.get("proof_value"),
            }
            for artifact in produced_artifacts
        ],
        "provider_external_proof": {
            "provider_receipt": provider_proof_receipt,
            "evidence_receipts": evidence_receipts,
            "inspection_bundle_state": inspection["execution_bundle"]["acceptance_state"],
            "reconciliation_evidence_source": normalized_reconciliation_source,
        },
        "reconciliation_result": reconciliation_result,
    }
    _write_json(artifact_paths["architect_reconciliation_v1"], reconciliation_payload)
    reconciliation_artifact = store.create_workflow_artifact(
        "aioffice",
        workflow_run_id=workflow["id"],
        stage_run_id=stage_runs["architect"]["id"],
        task_id=task_id,
        contract_name="architect_reconciliation_v1",
        kind="json",
        content=json.dumps(reconciliation_payload, ensure_ascii=True, indent=2),
        proof_value="reconciliation_output",
        artifact_path=_relative_path(workspace_root, artifact_paths["architect_reconciliation_v1"]),
        produced_by="operator_api supervised rehearsal",
        source_packet_id=packet["packet_id"],
        input_artifact_paths=[
            artifact["artifact_path"]
            for artifact in produced_artifacts
            if str(artifact.get("artifact_path") or "").strip()
        ],
    )
    store.record_orchestration_trace(
        workflow["id"],
        stage_run_id=stage_runs["architect"]["id"],
        source="operator_api",
        event_type="supervised_rehearsal_reconciled",
        payload={"reconciliation_artifact_id": reconciliation_artifact["id"]},
    )

    return {
        "command": "aioffice-supervised-architect-rehearsal",
        "task_id": task_id,
        "workspace_root": str(workspace_root),
        "workflow_run": workflow,
        "stage_runs": stage_runs,
        "handoffs": handoffs,
        "packet": packet,
        "bundle": bundle,
        "inspection": {
            "workflow_run_id": inspection["workflow_run"]["id"],
            "stage_run_id": inspection["stage_run"]["id"],
            "packet_id": inspection["control_execution_packet"]["packet_id"],
            "bundle_id": inspection["execution_bundle"]["bundle_id"],
            "bundle_acceptance_state": inspection["execution_bundle"]["acceptance_state"],
        },
        "gate_checks": gate_checks,
        "produced_artifacts": produced_artifacts + [reconciliation_artifact],
        "reconciliation_artifact": reconciliation_artifact,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Program Kanban operator-client service wrapper.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    preview = subparsers.add_parser("preview")
    preview.add_argument("--project", required=True)
    preview.add_argument("--text", required=True)
    preview.add_argument("--clarification", default=None)

    dispatch = subparsers.add_parser("dispatch")
    dispatch.add_argument("--project", required=True)
    dispatch.add_argument("--text", required=True)
    dispatch.add_argument("--clarification", default=None)

    approve = subparsers.add_parser("approve")
    approve.add_argument("--approval-id", required=True)
    approve.add_argument("--note", default=None)

    approve_resume = subparsers.add_parser("approve-resume")
    approve_resume.add_argument("--approval-id", required=True)
    approve_resume.add_argument("--note", default=None)

    reject = subparsers.add_parser("reject")
    reject.add_argument("--approval-id", required=True)
    reject.add_argument("--note", default=None)

    resume = subparsers.add_parser("resume")
    resume.add_argument("--run-id", required=True)

    run_details = subparsers.add_parser("run-details")
    run_details.add_argument("--run-id", required=True)

    task_details = subparsers.add_parser("task-details")
    task_details.add_argument("--task-id", required=True)

    control_kernel_details = subparsers.add_parser("control-kernel-details")
    control_kernel_details.add_argument("--workflow-run-id", default=None)
    control_kernel_details.add_argument("--stage-run-id", default=None)
    control_kernel_details.add_argument("--packet-id", default=None)
    control_kernel_details.add_argument("--bundle-id", default=None)
    control_kernel_details.add_argument("--workspace-root", default=None)

    bundle_decision = subparsers.add_parser("bundle-decision")
    bundle_decision.add_argument("--bundle-id", required=True)
    bundle_decision.add_argument("--action", required=True)
    bundle_decision.add_argument("--approved-by", required=True)
    bundle_decision.add_argument("--destination-mappings-file", required=True)
    bundle_decision.add_argument("--decision-note", default=None)
    bundle_decision.add_argument("--workspace-root", default=None)

    aioffice_rehearsal = subparsers.add_parser("aioffice-supervised-architect-rehearsal")
    aioffice_rehearsal.add_argument("--task-id", default="AIO-029")
    aioffice_rehearsal.add_argument("--operator", required=True)
    aioffice_rehearsal.add_argument("--provider-request-id", required=True)
    aioffice_rehearsal.add_argument("--reconciliation-evidence-source", required=True)
    aioffice_rehearsal.add_argument("--rehearsal-root", default=AIOFFICE_SUPERVISED_REHEARSAL_ROOT)
    aioffice_rehearsal.add_argument("--rehearsal-task", default=AIOFFICE_SUPERVISED_REHEARSAL_TASK)
    aioffice_rehearsal.add_argument("--stop-after", default="architect")
    aioffice_rehearsal.add_argument("--confirm-supervised", action="store_true")

    trust_worklist = subparsers.add_parser("trust-worklist")
    trust_worklist.add_argument("--include-trusted", action="store_true")

    record_reconciliation = subparsers.add_parser("record-reconciliation")
    record_reconciliation.add_argument("--external-call-id", required=True)
    record_reconciliation.add_argument("--provider-request-id", required=True)
    record_reconciliation.add_argument(
        "--reconciliation-state",
        required=True,
        choices=["reconciliation_pending", "reconciled", "reconciliation_failed"],
    )
    record_reconciliation.add_argument("--reconciliation-evidence-source", required=True)
    record_reconciliation.add_argument("--checked-at", default=None)
    record_reconciliation.add_argument("--reason-code", default=None)

    subparsers.add_parser("routing-catalog")

    try:
        args = parser.parse_args()
        orchestrator = None

        def _get_orchestrator() -> Orchestrator:
            nonlocal orchestrator
            if orchestrator is None:
                orchestrator = _orchestrator()
            return orchestrator

        if args.command == "preview":
            payload = run_async(preview_operator_request(_get_orchestrator(), args.project, args.text, args.clarification))
        elif args.command == "dispatch":
            payload = run_async(dispatch_operator_request(_get_orchestrator(), args.project, args.text, args.clarification))
            run_result = payload.get("run_result", {})
            run_id = run_result.get("run_id")
            if run_id:
                payload["run_evidence"] = _get_orchestrator().store.get_run_evidence(run_id)
            payload["routing_catalog"] = _routing_catalog()
        elif args.command == "approve":
            payload = _get_orchestrator().approve(args.approval_id, args.note)
        elif args.command == "approve-resume":
            payload = run_async(_get_orchestrator().approve_and_resume(args.approval_id, args.note))
            run_id = payload.get("run_id")
            if run_id:
                payload["run_evidence"] = _get_orchestrator().store.get_run_evidence(run_id)
            payload["routing_catalog"] = _routing_catalog()
        elif args.command == "reject":
            payload = _get_orchestrator().reject(args.approval_id, args.note)
        elif args.command == "resume":
            payload = run_async(_get_orchestrator().resume_run(args.run_id))
            run_id = payload.get("run_id") or args.run_id
            payload["run_evidence"] = _get_orchestrator().store.get_run_evidence(run_id)
            payload["routing_catalog"] = _routing_catalog()
        elif args.command == "run-details":
            payload = _get_orchestrator().store.get_run_evidence(args.run_id)
            payload["routing_catalog"] = _routing_catalog()
        elif args.command == "task-details":
            payload = _get_orchestrator().store.get_task_work_graph(args.task_id)
            payload["routing_catalog"] = _routing_catalog()
        elif args.command == "control-kernel-details":
            inspection_store, inspection_workspace_root = _inspection_store_for_control_kernel(ROOT, args.workspace_root)
            payload = _control_kernel_details(
                inspection_store,
                workflow_run_id=args.workflow_run_id,
                stage_run_id=args.stage_run_id,
                packet_id=args.packet_id,
                bundle_id=args.bundle_id,
            )
            if inspection_workspace_root is not None:
                payload["inspection_workspace_root"] = str(inspection_workspace_root)
            payload["routing_catalog"] = _routing_catalog()
        elif args.command == "bundle-decision":
            payload = _execute_control_kernel_bundle_decision(
                ROOT,
                bundle_id=args.bundle_id,
                action=args.action,
                approved_by=args.approved_by,
                destination_mappings_file=args.destination_mappings_file,
                decision_note=args.decision_note,
                workspace_root=args.workspace_root,
            )
            payload["routing_catalog"] = _routing_catalog()
        elif args.command == "aioffice-supervised-architect-rehearsal":
            payload = _run_aioffice_supervised_architect_rehearsal(
                ROOT,
                task_id=args.task_id,
                operator_name=args.operator,
                provider_request_id=args.provider_request_id,
                reconciliation_evidence_source=args.reconciliation_evidence_source,
                rehearsal_root=args.rehearsal_root,
                rehearsal_task=args.rehearsal_task,
                stop_after=args.stop_after,
                confirm_supervised=bool(args.confirm_supervised),
            )
        elif args.command == "trust-worklist":
            worklist = _get_orchestrator().store.list_governed_external_trust_worklist(
                include_trusted=bool(args.include_trusted)
            )
            payload = {
                "trust_worklist": worklist,
                "trust_worklist_count": len(worklist),
                "include_trusted_reconciled": bool(args.include_trusted),
            }
        elif args.command == "record-reconciliation":
            payload = _get_orchestrator().store.record_governed_external_reconciliation(
                external_call_id=args.external_call_id,
                provider_request_id=args.provider_request_id,
                reconciliation_state=args.reconciliation_state,
                reconciliation_evidence_source=args.reconciliation_evidence_source,
                reconciliation_checked_at=args.checked_at,
                reconciliation_reason_code=args.reason_code,
            )
        else:
            payload = {"routes": _routing_catalog()}
    except Exception as exc:
        print(
            json.dumps(
                {
                    "error": str(exc),
                    "error_type": exc.__class__.__name__,
                },
                ensure_ascii=True,
            )
        )
        raise SystemExit(1) from exc

    print(json.dumps(payload, ensure_ascii=True))


if __name__ == "__main__":
    main()
