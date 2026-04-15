from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

from scripts import operator_api
from sessions import SessionStore
from workspace_root import write_workspace_authority_marker


def _prepare_control_kernel_repo(tmp_path: Path) -> Path:
    (tmp_path / "projects" / "aioffice" / "execution").mkdir(parents=True)
    (tmp_path / "projects" / "aioffice" / "governance").mkdir(parents=True)
    (tmp_path / "sessions").mkdir(parents=True)
    (tmp_path / "governance").mkdir(parents=True)
    (tmp_path / "projects" / "aioffice" / "governance" / "PROJECT_BRIEF.md").write_text(
        "# Brief\n\nAIOffice test project.\n",
        encoding="utf-8",
    )
    (tmp_path / "sessions" / "approvals.json").write_text("", encoding="utf-8")
    return tmp_path


def _prepare_authoritative_operator_repo(tmp_path: Path) -> Path:
    repo_root = _prepare_control_kernel_repo(tmp_path)
    write_workspace_authority_marker(
        repo_root,
        repo_name="_AIStudio_POC",
        canonical_root_hint=repo_root,
    )
    return repo_root


def _build_control_kernel_fixture(tmp_path: Path) -> dict[str, object]:
    repo_root = _prepare_control_kernel_repo(tmp_path)
    store = SessionStore(repo_root)
    workflow = store.create_workflow_run(
        "aioffice",
        task_id="AIO-025",
        objective="Inspect persisted control-kernel state.",
        authoritative_workspace_root="projects/aioffice",
        current_stage="architect",
    )
    stage = store.create_stage_run(
        workflow["id"],
        stage_name="architect",
        status="in_progress",
    )
    artifact = store.create_workflow_artifact(
        "aioffice",
        workflow_run_id=workflow["id"],
        stage_run_id=stage["id"],
        task_id="AIO-025",
        contract_name="architecture_decision_v1",
        kind="document",
        content="# Architecture\n\nInspection-ready output.\n",
        proof_value="architecture_output",
    )
    handoff = store.create_handoff(
        workflow["id"],
        from_stage_name="context_audit",
        to_stage_name="architect",
        summary="Audit context and architecture input are ready.",
        stage_run_id=stage["id"],
        upstream_artifact_ids=[artifact["id"]],
    )
    blocker = store.create_blocker(
        workflow["id"],
        blocker_kind="review_pending",
        summary="Bundle review is still required.",
        stage_run_id=stage["id"],
    )
    question = store.create_question_or_assumption(
        workflow["id"],
        record_type="question",
        summary="Should inspection expose packet scope details?",
        stage_run_id=stage["id"],
    )
    assumption = store.create_question_or_assumption(
        workflow["id"],
        record_type="assumption",
        summary="Inspection remains read-only.",
        stage_run_id=stage["id"],
    )
    trace = store.record_orchestration_trace(
        workflow["id"],
        stage_run_id=stage["id"],
        event_type="inspection_requested",
        source="Project Orchestrator",
        payload={"surface": "operator_api"},
    )
    packet = store.issue_control_execution_packet(
        "aioffice",
        "AIO-025",
        objective="Expose persisted control-kernel state read-only.",
        authoritative_workspace_root="projects/aioffice",
        allowed_write_paths=["scripts/operator_api.py", "tests/test_operator_api.py"],
        scratch_path="tmp/aioffice/operator-inspection",
        forbidden_paths=["projects/aioffice/governance"],
        forbidden_actions=["self_accept", "self_promote"],
        required_artifact_outputs=["scripts/operator_api.py"],
        required_validations=["pytest tests/test_operator_api.py"],
        expected_return_bundle_contents=["produced artifacts", "evidence receipts"],
        failure_reporting_expectations=["report blockers", "report open risks"],
        workflow_run_id=workflow["id"],
        stage_run_id=stage["id"],
        issued_by="Project Orchestrator",
        provenance_note="AIO-025 bounded implementation bundle",
    )
    bundle = store.ingest_execution_bundle(
        packet["packet_id"],
        produced_artifact_ids=[artifact["id"]],
        diff_refs=["scripts/operator_api.py"],
        commands_run=["pytest tests/test_operator_api.py"],
        test_results=[{"command": "pytest", "status": "passed"}],
        blocker_ids=[blocker["id"]],
        question_ids=[question["id"]],
        assumption_ids=[assumption["id"]],
        self_report_summary="Added a read-only inspection path for persisted control-kernel state.",
        open_risks=["No writable inspection surface is allowed."],
        evidence_receipts=[{"kind": "pytest", "status": "passed"}],
    )
    return {
        "store": store,
        "workflow": workflow,
        "stage": stage,
        "artifact": artifact,
        "handoff": handoff,
        "blocker": blocker,
        "question": question,
        "assumption": assumption,
        "trace": trace,
        "packet": packet,
        "bundle": bundle,
    }


def _build_bundle_decision_fixture(tmp_path: Path) -> dict[str, object]:
    repo_root = _prepare_authoritative_operator_repo(tmp_path)
    store = SessionStore(repo_root)
    workflow = store.create_workflow_run(
        "aioffice",
        task_id="AIO-041",
        objective="Prepare a bounded pending-review bundle for operator bundle decision.",
        authoritative_workspace_root="projects/aioffice",
        current_stage="architect",
    )
    stage = store.create_stage_run(
        workflow["id"],
        stage_name="architect",
        status="in_progress",
    )
    source_artifact_path = (
        "projects/aioffice/artifacts/m7_operator_bundle_decision/workflow_review/architect/architecture_decision_v1.md"
    )
    source_artifact_file = (
        repo_root
        / "projects"
        / "aioffice"
        / "artifacts"
        / "m7_operator_bundle_decision"
        / "workflow_review"
        / "architect"
        / "architecture_decision_v1.md"
    )
    source_artifact_file.parent.mkdir(parents=True, exist_ok=True)
    source_artifact_file.write_text("# Architecture Decision\n\nApply this reviewed output.\n", encoding="utf-8")
    artifact = store.create_workflow_artifact(
        "aioffice",
        workflow_run_id=workflow["id"],
        stage_run_id=stage["id"],
        task_id="AIO-041",
        contract_name="architecture_decision_v1",
        kind="document",
        content=source_artifact_file.read_text(encoding="utf-8"),
        proof_value="architecture_output",
        artifact_path=source_artifact_path,
        produced_by="Architect",
    )
    packet = store.issue_control_execution_packet(
        "aioffice",
        "AIO-041",
        objective="Issue one explicit approved bundle decision through the sanctioned operator API wrapper.",
        authoritative_workspace_root="projects/aioffice",
        allowed_write_paths=[source_artifact_path],
        scratch_path="tmp/aioffice/operator-bundle-decision",
        forbidden_paths=["projects/aioffice/governance", "projects/aioffice/execution/protected"],
        forbidden_actions=["self_accept", "self_promote"],
        required_artifact_outputs=[source_artifact_path],
        required_validations=["pytest tests/test_operator_api.py -k bundle_decision"],
        expected_return_bundle_contents=["produced artifacts", "evidence receipts"],
        failure_reporting_expectations=["report blockers", "report open risks"],
        workflow_run_id=workflow["id"],
        stage_run_id=stage["id"],
        issued_by="Project Orchestrator",
        provenance_note="AIO-041 bounded operator bundle decision packet",
    )
    bundle = store.ingest_execution_bundle(
        packet["packet_id"],
        produced_artifact_ids=[artifact["id"]],
        diff_refs=[source_artifact_path],
        commands_run=["pytest tests/test_operator_api.py -k bundle_decision"],
        test_results=[{"command": "pytest", "status": "passed"}],
        self_report_summary="Pending review bundle is ready for one operator bundle decision.",
        open_risks=["AIO-042 rehearsal remains out of scope."],
        evidence_receipts=[{"kind": "provider_metadata", "provider": "manual_harness", "status": "captured"}],
    )
    destination_path = "projects/aioffice/execution/approved/operator_bundle_decision.md"
    destination_file = (
        repo_root / "projects" / "aioffice" / "execution" / "approved" / "operator_bundle_decision.md"
    )
    return {
        "repo_root": repo_root,
        "store": store,
        "workflow": workflow,
        "stage": stage,
        "artifact": artifact,
        "packet": packet,
        "bundle": bundle,
        "source_artifact_file": source_artifact_file,
        "source_artifact_path": source_artifact_path,
        "destination_path": destination_path,
        "destination_file": destination_file,
    }


def test_operator_api_preview_routes_through_ingress_first(monkeypatch, capsys):
    captured: dict[str, object] = {}

    class _DummyStore:
        def get_run_evidence(self, run_id: str) -> dict[str, str]:
            raise AssertionError("No run evidence should be requested for preview.")

    class _DummyOrchestrator:
        store = _DummyStore()

        async def preview_request(self, *args, **kwargs):
            raise AssertionError("Operator API should not bypass ingress with raw-text preview calls.")

    async def _fake_preview_operator_request(orchestrator, project_name: str, user_text: str, clarification: str | None = None):
        captured["project_name"] = project_name
        captured["user_text"] = user_text
        captured["clarification"] = clarification
        return {
            "gateway_decision": {
                "schema_version": "intent_decision_v1",
                "decision": "ROUTE_TASK",
                "intent": "TASK",
                "contains_task_request": True,
                "contains_policy_request": False,
                "contains_status_request": False,
                "safe_to_route": True,
                "reason_codes": ["task_request_detected"],
                "normalized_request": "Implement the gateway",
            }
        }

    monkeypatch.setattr(operator_api, "_orchestrator", lambda: _DummyOrchestrator())
    monkeypatch.setattr(operator_api, "preview_operator_request", _fake_preview_operator_request)
    monkeypatch.setattr(operator_api, "_routing_catalog", lambda: {})
    monkeypatch.setattr(
        sys,
        "argv",
        ["operator_api.py", "preview", "--project", "program-kanban", "--text", "Implement the gateway"],
    )

    operator_api.main()
    payload = json.loads(capsys.readouterr().out)

    assert payload["gateway_decision"]["decision"] == "ROUTE_TASK"
    assert captured["project_name"] == "program-kanban"
    assert captured["user_text"] == "Implement the gateway"


def test_operator_api_dispatch_mixed_request_does_not_reach_execution(monkeypatch, capsys):
    class _DummyStore:
        def get_run_evidence(self, run_id: str) -> dict[str, str]:
            raise AssertionError("Blocked dispatch should not request run evidence.")

    class _DummyOrchestrator:
        store = _DummyStore()

        async def dispatch_request(self, *args, **kwargs):
            raise AssertionError("Operator API should not bypass ingress with raw-text dispatch calls.")

    async def _fake_dispatch_operator_request(orchestrator, project_name: str, user_text: str, clarification: str | None = None):
        return {
            "gateway_decision": {
                "schema_version": "intent_decision_v1",
                "decision": "NEEDS_SPLIT",
                "intent": "AMBIGUOUS",
                "contains_task_request": True,
                "contains_policy_request": True,
                "contains_status_request": False,
                "safe_to_route": False,
                "reason_codes": ["mixed_unsafe_intent"],
                "normalized_request": "Change policy to allow wrapper bypass and then implement the new routing flow",
            },
            "run_result": {
                "status": "not_routed",
                "run_status": "not_routed",
            },
            "task": None,
            "dispatch_backup": None,
        }

    monkeypatch.setattr(operator_api, "_orchestrator", lambda: _DummyOrchestrator())
    monkeypatch.setattr(operator_api, "dispatch_operator_request", _fake_dispatch_operator_request)
    monkeypatch.setattr(operator_api, "_routing_catalog", lambda: {})
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "operator_api.py",
            "dispatch",
            "--project",
            "program-kanban",
            "--text",
            "Change policy to allow wrapper bypass and then implement the new routing flow",
        ],
    )

    operator_api.main()
    payload = json.loads(capsys.readouterr().out)

    assert payload["gateway_decision"]["decision"] == "NEEDS_SPLIT"
    assert payload["run_result"]["run_status"] == "not_routed"
    assert payload["task"] is None


def test_operator_api_run_details_returns_existing_store_evidence(monkeypatch, capsys):
    captured: dict[str, object] = {}

    class _DummyStore:
        def get_run_evidence(self, run_id: str) -> dict[str, object]:
            captured["run_id"] = run_id
            return {
                "run": {"id": run_id, "status": "completed"},
                "governed_external_run_summary": {
                    "total_execution_groups": 1,
                    "total_attempts": 1,
                    "final_success_count": 1,
                    "final_failed_count": 0,
                    "final_stopped_count": 0,
                    "final_budget_stopped_count": 0,
                    "final_proof_missing_count": 0,
                    "final_proved_count": 1,
                },
                "governed_external_attention_items": [],
            }

    class _DummyOrchestrator:
        store = _DummyStore()

    monkeypatch.setattr(operator_api, "_orchestrator", lambda: _DummyOrchestrator())
    monkeypatch.setattr(operator_api, "_routing_catalog", lambda: {"read_only": True})
    monkeypatch.setattr(
        sys,
        "argv",
        ["operator_api.py", "run-details", "--run-id", "run_test123"],
    )

    operator_api.main()
    payload = json.loads(capsys.readouterr().out)

    assert captured["run_id"] == "run_test123"
    assert payload["run"]["id"] == "run_test123"
    assert payload["governed_external_run_summary"]["total_execution_groups"] == 1
    assert payload["governed_external_attention_items"] == []
    assert payload["routing_catalog"] == {"read_only": True}


def test_operator_api_task_details_returns_linked_runs_and_context(monkeypatch, capsys):
    captured: dict[str, object] = {}

    class _DummyStore:
        def get_task_work_graph(self, task_id: str) -> dict[str, object]:
            captured["task_id"] = task_id
            return {
                "project": {"id": "project_test123", "name": "program-kanban"},
                "milestone": {"id": "milestone_test123", "title": "M1 - Unified Work Graph"},
                "task": {"id": task_id, "project_name": "program-kanban", "milestone_id": "milestone_test123"},
                "linked_run_count": 1,
                "linked_runs": [
                    {
                        "id": "run_test123",
                        "task_id": task_id,
                        "project_id": "project_test123",
                        "project_name": "program-kanban",
                        "milestone_id": "milestone_test123",
                        "governed_external_run_summary": {
                            "governed_api_execution_count": 1,
                            "final_proof_missing_count": 0,
                        },
                        "execution_summary": {
                            "latest_execution_path_classification": "governed_api_executed",
                            "latest_proof_status": "proved",
                        },
                    }
                ],
                "latest_run_summary": {"id": "run_test123"},
                "latest_attention_summary": {"attention_count": 0},
                "latest_health_summary": {"has_attention": False},
                "latest_execution_summary": {
                    "latest_execution_path_classification": "governed_api_executed",
                    "latest_proof_status": "proved",
                },
            }

    class _DummyOrchestrator:
        store = _DummyStore()

    monkeypatch.setattr(operator_api, "_orchestrator", lambda: _DummyOrchestrator())
    monkeypatch.setattr(operator_api, "_routing_catalog", lambda: {"read_only": True})
    monkeypatch.setattr(
        sys,
        "argv",
        ["operator_api.py", "task-details", "--task-id", "PK-101"],
    )

    operator_api.main()
    payload = json.loads(capsys.readouterr().out)

    assert captured["task_id"] == "PK-101"
    assert payload["project"]["id"] == "project_test123"
    assert payload["milestone"]["id"] == "milestone_test123"
    assert payload["linked_run_count"] == 1
    assert payload["linked_runs"][0]["id"] == "run_test123"
    assert payload["linked_runs"][0]["project_id"] == "project_test123"
    assert payload["latest_execution_summary"]["latest_execution_path_classification"] == "governed_api_executed"
    assert payload["routing_catalog"] == {"read_only": True}


def test_operator_api_trust_worklist_routes_to_store(monkeypatch, capsys):
    captured: dict[str, object] = {}

    class _DummyStore:
        def list_governed_external_trust_worklist(self, *, include_trusted: bool = False) -> list[dict[str, object]]:
            captured["include_trusted"] = include_trusted
            return [
                {
                    "worklist_category": "reconciliation_failed",
                    "external_call_id": "external_call_test123",
                    "run_id": "run_test123",
                    "task_id": "PK-101",
                    "provider_request_id": "resp_test123",
                    "proof_status": "proved",
                    "reconciliation_state": "reconciliation_failed",
                    "trust_status": "reconciliation_failed",
                    "reconciliation_reason_code": "provider_record_not_found",
                    "reconciliation_checked_at": "2026-04-12T12:00:00+00:00",
                }
            ]

    class _DummyOrchestrator:
        store = _DummyStore()

    monkeypatch.setattr(operator_api, "_orchestrator", lambda: _DummyOrchestrator())
    monkeypatch.setattr(
        sys,
        "argv",
        ["operator_api.py", "trust-worklist", "--include-trusted"],
    )

    operator_api.main()
    payload = json.loads(capsys.readouterr().out)

    assert captured == {"include_trusted": True}
    assert payload["trust_worklist_count"] == 1
    assert payload["include_trusted_reconciled"] is True
    assert payload["trust_worklist"][0]["external_call_id"] == "external_call_test123"
    assert payload["trust_worklist"][0]["trust_status"] == "reconciliation_failed"


def test_operator_api_record_reconciliation_routes_to_store(monkeypatch, capsys):
    captured: dict[str, object] = {}

    class _DummyStore:
        def record_governed_external_reconciliation(self, **kwargs) -> dict[str, object]:
            captured.update(kwargs)
            return {
                "reconciliation_record": {
                    "reconciliation_id": "recon_test123",
                    "external_call_id": kwargs["external_call_id"],
                    "provider_request_id": kwargs["provider_request_id"],
                    "reconciliation_state": kwargs["reconciliation_state"],
                },
                "governed_external_call": {
                    "external_call_id": kwargs["external_call_id"],
                    "trust_status": "trusted_reconciled",
                },
            }

    class _DummyOrchestrator:
        store = _DummyStore()

    monkeypatch.setattr(operator_api, "_orchestrator", lambda: _DummyOrchestrator())
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "operator_api.py",
            "record-reconciliation",
            "--external-call-id",
            "external_call_test123",
            "--provider-request-id",
            "resp_test123",
            "--reconciliation-state",
            "reconciled",
            "--reconciliation-evidence-source",
            "provider_ledger",
            "--checked-at",
            "2026-04-12T12:00:00+00:00",
        ],
    )

    operator_api.main()
    payload = json.loads(capsys.readouterr().out)

    assert captured == {
        "external_call_id": "external_call_test123",
        "provider_request_id": "resp_test123",
        "reconciliation_state": "reconciled",
        "reconciliation_evidence_source": "provider_ledger",
        "reconciliation_checked_at": "2026-04-12T12:00:00+00:00",
        "reconciliation_reason_code": None,
    }
    assert payload["reconciliation_record"]["reconciliation_id"] == "recon_test123"
    assert payload["governed_external_call"]["trust_status"] == "trusted_reconciled"


def test_operator_api_rejects_missing_authority_marker(tmp_path, monkeypatch, capsys):
    marker_path = tmp_path / ".workspace_authority.json"
    if marker_path.exists():
        marker_path.unlink()
    monkeypatch.setattr(operator_api, "ROOT", tmp_path)
    monkeypatch.setattr(
        sys,
        "argv",
        ["operator_api.py", "run-details", "--run-id", "run_test123"],
    )

    with pytest.raises(SystemExit) as exc_info:
        operator_api.main()

    assert exc_info.value.code == 1
    payload = json.loads(capsys.readouterr().out)
    assert payload["error_type"] == "WorkspaceRootAuthorityError"
    assert "authoritative workspace root marker required" in payload["error"]


def test_operator_api_control_kernel_details_returns_persisted_state(monkeypatch, capsys, tmp_path):
    fixture = _build_control_kernel_fixture(tmp_path)

    class _DummyOrchestrator:
        store = fixture["store"]

    monkeypatch.setattr(operator_api, "_orchestrator", lambda: _DummyOrchestrator())
    monkeypatch.setattr(operator_api, "_routing_catalog", lambda: {"read_only": True})
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "operator_api.py",
            "control-kernel-details",
            "--bundle-id",
            fixture["bundle"]["bundle_id"],
        ],
    )

    operator_api.main()
    payload = json.loads(capsys.readouterr().out)

    assert payload["workflow_run"]["id"] == fixture["workflow"]["id"]
    assert payload["stage_run"]["id"] == fixture["stage"]["id"]
    assert payload["control_execution_packet"]["packet_id"] == fixture["packet"]["packet_id"]
    assert payload["execution_bundle"]["bundle_id"] == fixture["bundle"]["bundle_id"]
    assert payload["workflow_artifacts"][0]["id"] == fixture["artifact"]["id"]
    assert payload["bundle_workflow_artifacts"][0]["id"] == fixture["artifact"]["id"]
    assert payload["handoffs"][0]["id"] == fixture["handoff"]["id"]
    assert payload["blockers"][0]["id"] == fixture["blocker"]["id"]
    assert {item["record_type"] for item in payload["question_or_assumptions"]} == {"question", "assumption"}
    assert payload["orchestration_traces"][0]["id"] == fixture["trace"]["id"]
    assert payload["packet_execution_bundles"][0]["bundle_id"] == fixture["bundle"]["bundle_id"]
    assert payload["routing_catalog"] == {"read_only": True}


def test_operator_api_control_kernel_details_rejects_missing_identifiers(monkeypatch, capsys):
    class _DummyStore:
        pass

    class _DummyOrchestrator:
        store = _DummyStore()

    monkeypatch.setattr(operator_api, "_orchestrator", lambda: _DummyOrchestrator())
    monkeypatch.setattr(
        sys,
        "argv",
        ["operator_api.py", "control-kernel-details"],
    )

    with pytest.raises(SystemExit) as exc_info:
        operator_api.main()

    assert exc_info.value.code == 1
    payload = json.loads(capsys.readouterr().out)
    assert payload["error_type"] == "ValueError"
    assert "At least one control-kernel identifier is required" in payload["error"]


def test_operator_api_control_kernel_details_rejects_unknown_bundle_lookup(monkeypatch, capsys):
    class _DummyStore:
        def get_execution_bundle(self, bundle_id: str):
            return None

    class _DummyOrchestrator:
        store = _DummyStore()

    monkeypatch.setattr(operator_api, "_orchestrator", lambda: _DummyOrchestrator())
    monkeypatch.setattr(
        sys,
        "argv",
        ["operator_api.py", "control-kernel-details", "--bundle-id", "bundle_missing"],
    )

    with pytest.raises(SystemExit) as exc_info:
        operator_api.main()

    assert exc_info.value.code == 1
    payload = json.loads(capsys.readouterr().out)
    assert payload["error_type"] == "ValueError"
    assert "Execution bundle not found: bundle_missing" in payload["error"]


def test_operator_api_control_kernel_details_rejects_duplicate_workspace_root(monkeypatch, capsys, tmp_path):
    repo_root = _prepare_authoritative_operator_repo(tmp_path / "authoritative")
    duplicate_root = tmp_path / "duplicate"
    duplicate_root.mkdir(parents=True)
    monkeypatch.setenv("AISTUDIO_AUTHORITATIVE_ROOT", str(repo_root))
    monkeypatch.setenv("AISTUDIO_NON_AUTHORITATIVE_DUPLICATE_ROOT", str(duplicate_root))
    monkeypatch.setattr(operator_api, "ROOT", repo_root)
    monkeypatch.setattr(operator_api, "_routing_catalog", lambda: {})
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "operator_api.py",
            "control-kernel-details",
            "--workspace-root",
            str(duplicate_root),
            "--bundle-id",
            "bundle_test",
        ],
    )

    with pytest.raises(SystemExit) as exc_info:
        operator_api.main()

    assert exc_info.value.code == 1
    payload = json.loads(capsys.readouterr().out)
    assert payload["error_type"] == "WorkspaceRootAuthorityError"
    assert "non-authoritative duplicate workspace root" in payload["error"]


def test_operator_api_control_kernel_details_rejects_missing_workspace_store(monkeypatch, capsys, tmp_path):
    repo_root = _prepare_authoritative_operator_repo(tmp_path / "authoritative")
    duplicate_root = tmp_path / "duplicate"
    duplicate_root.mkdir(parents=True)
    inspection_workspace = repo_root / "projects" / "aioffice" / "artifacts" / "fresh_inspection_workspace"
    inspection_workspace.mkdir(parents=True)
    database_path = inspection_workspace / "sessions" / "studio.db"
    monkeypatch.setenv("AISTUDIO_AUTHORITATIVE_ROOT", str(repo_root))
    monkeypatch.setenv("AISTUDIO_NON_AUTHORITATIVE_DUPLICATE_ROOT", str(duplicate_root))
    monkeypatch.setattr(operator_api, "ROOT", repo_root)
    monkeypatch.setattr(operator_api, "_routing_catalog", lambda: {})
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "operator_api.py",
            "control-kernel-details",
            "--workspace-root",
            str(inspection_workspace),
            "--bundle-id",
            "bundle_test",
        ],
    )

    with pytest.raises(SystemExit) as exc_info:
        operator_api.main()

    assert exc_info.value.code == 1
    payload = json.loads(capsys.readouterr().out)
    assert payload["error_type"] == "ValueError"
    assert "must already contain a sanctioned persisted store at sessions/studio.db" in payload["error"]
    assert not database_path.exists()


def test_operator_api_control_kernel_details_reads_without_mutation(monkeypatch, capsys, tmp_path):
    fixture = _build_control_kernel_fixture(tmp_path)

    class _ReadOnlyStoreProxy:
        def __init__(self, store):
            self._store = store

        def __getattr__(self, name: str):
            if name.startswith(("create_", "update_", "issue_", "ingest_", "record_")):
                raise AssertionError(f"Inspection must not call mutating store method: {name}")
            return getattr(self._store, name)

    class _DummyOrchestrator:
        store = _ReadOnlyStoreProxy(fixture["store"])

    monkeypatch.setattr(operator_api, "_orchestrator", lambda: _DummyOrchestrator())
    monkeypatch.setattr(operator_api, "_routing_catalog", lambda: {})
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "operator_api.py",
            "control-kernel-details",
            "--packet-id",
            fixture["packet"]["packet_id"],
        ],
    )

    operator_api.main()
    payload = json.loads(capsys.readouterr().out)

    assert payload["control_execution_packet"]["packet_id"] == fixture["packet"]["packet_id"]
    assert payload["packet_execution_bundles"][0]["bundle_id"] == fixture["bundle"]["bundle_id"]


def test_operator_api_bundle_decision_executes_controlled_apply(monkeypatch, capsys, tmp_path):
    fixture = _build_bundle_decision_fixture(tmp_path)
    captured: dict[str, object] = {"call_count": 0}

    class _DecisionStoreProxy:
        def __init__(self, store):
            self._store = store

        def __getattr__(self, name: str):
            return getattr(self._store, name)

        def execute_apply_promotion_decision(
            self,
            bundle_id: str,
            *,
            approved_decision: dict[str, object],
            destination_mappings: list[dict[str, object]],
        ) -> dict[str, object]:
            captured["call_count"] = int(captured["call_count"]) + 1
            captured["bundle_id"] = bundle_id
            captured["approved_decision"] = dict(approved_decision)
            captured["destination_mappings"] = [dict(item) for item in destination_mappings]
            return self._store.execute_apply_promotion_decision(
                bundle_id,
                approved_decision=approved_decision,
                destination_mappings=destination_mappings,
            )

    class _DummyOrchestrator:
        store = _DecisionStoreProxy(fixture["store"])

    monkeypatch.setattr(operator_api, "_orchestrator", lambda: _DummyOrchestrator())
    monkeypatch.setattr(operator_api, "_routing_catalog", lambda: {"decision_surface": True})
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "operator_api.py",
            "bundle-decision",
            "--bundle-id",
            fixture["bundle"]["bundle_id"],
            "--action",
            "apply",
            "--approved-by",
            "Project Orchestrator",
            "--destination-mappings",
            json.dumps(
                [
                    {
                        "source_artifact_id": fixture["artifact"]["id"],
                        "destination_path": fixture["destination_path"],
                    }
                ]
            ),
            "--decision-note",
            "Approved bounded apply into the authoritative workspace.",
        ],
    )

    operator_api.main()
    payload = json.loads(capsys.readouterr().out)

    assert payload["command"] == "bundle-decision"
    assert payload["bundle_id"] == fixture["bundle"]["bundle_id"]
    assert captured["call_count"] == 1
    assert captured["bundle_id"] == fixture["bundle"]["bundle_id"]
    assert captured["approved_decision"] == {
        "decision": "approved",
        "action": "apply",
        "approved_by": "Project Orchestrator",
        "decision_note": "Approved bounded apply into the authoritative workspace.",
    }
    assert captured["destination_mappings"] == [
        {
            "source_artifact_id": fixture["artifact"]["id"],
            "destination_path": fixture["destination_path"],
        }
    ]
    assert payload["inspection_before"]["bundle_acceptance_state"] == "pending_review"
    assert payload["inspection_after"]["bundle_acceptance_state"] == "applied"
    assert payload["updated_bundle"]["acceptance_state"] == "applied"
    assert "apply_promotion_decision" in payload["inspection_after"]["evidence_receipt_kinds"]
    assert fixture["destination_file"].read_text(encoding="utf-8") == fixture["source_artifact_file"].read_text(
        encoding="utf-8"
    )
    assert fixture["store"].get_execution_bundle(fixture["bundle"]["bundle_id"])["acceptance_state"] == "applied"
    assert payload["routing_catalog"] == {"decision_surface": True}


def test_operator_api_bundle_decision_rejects_blank_approved_by(monkeypatch, capsys, tmp_path):
    fixture = _build_bundle_decision_fixture(tmp_path)
    captured: dict[str, object] = {"call_count": 0}

    class _DecisionStoreProxy:
        def __init__(self, store):
            self._store = store

        def __getattr__(self, name: str):
            return getattr(self._store, name)

        def execute_apply_promotion_decision(self, *args, **kwargs):
            captured["call_count"] = int(captured["call_count"]) + 1
            return self._store.execute_apply_promotion_decision(*args, **kwargs)

    class _DummyOrchestrator:
        store = _DecisionStoreProxy(fixture["store"])

    monkeypatch.setattr(operator_api, "_orchestrator", lambda: _DummyOrchestrator())
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "operator_api.py",
            "bundle-decision",
            "--bundle-id",
            fixture["bundle"]["bundle_id"],
            "--action",
            "apply",
            "--approved-by",
            "   ",
            "--destination-mappings",
            json.dumps(
                [
                    {
                        "source_artifact_id": fixture["artifact"]["id"],
                        "destination_path": fixture["destination_path"],
                    }
                ]
            ),
        ],
    )

    with pytest.raises(SystemExit) as exc_info:
        operator_api.main()

    assert exc_info.value.code == 1
    payload = json.loads(capsys.readouterr().out)
    assert payload["error_type"] == "ValueError"
    assert "approved_by is required" in payload["error"]
    assert captured["call_count"] == 0
    assert fixture["store"].get_execution_bundle(fixture["bundle"]["bundle_id"])["acceptance_state"] == "pending_review"
    assert not fixture["destination_file"].exists()


def test_operator_api_bundle_decision_rejects_destination_outside_authoritative_workspace(
    monkeypatch,
    capsys,
    tmp_path,
):
    fixture = _build_bundle_decision_fixture(tmp_path)
    captured: dict[str, object] = {"call_count": 0}
    outside_destination = fixture["repo_root"] / "sessions" / "not_allowed.md"

    class _DecisionStoreProxy:
        def __init__(self, store):
            self._store = store

        def __getattr__(self, name: str):
            return getattr(self._store, name)

        def execute_apply_promotion_decision(self, *args, **kwargs):
            captured["call_count"] = int(captured["call_count"]) + 1
            return self._store.execute_apply_promotion_decision(*args, **kwargs)

    class _DummyOrchestrator:
        store = _DecisionStoreProxy(fixture["store"])

    monkeypatch.setattr(operator_api, "_orchestrator", lambda: _DummyOrchestrator())
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "operator_api.py",
            "bundle-decision",
            "--bundle-id",
            fixture["bundle"]["bundle_id"],
            "--action",
            "apply",
            "--approved-by",
            "Project Orchestrator",
            "--destination-mappings",
            json.dumps(
                [
                    {
                        "source_artifact_id": fixture["artifact"]["id"],
                        "destination_path": "sessions/not_allowed.md",
                    }
                ]
            ),
        ],
    )

    with pytest.raises(SystemExit) as exc_info:
        operator_api.main()

    assert exc_info.value.code == 1
    payload = json.loads(capsys.readouterr().out)
    assert payload["error_type"] == "ValueError"
    assert "authoritative_workspace_root" in payload["error"]
    assert captured["call_count"] == 1
    assert fixture["store"].get_execution_bundle(fixture["bundle"]["bundle_id"])["acceptance_state"] == "pending_review"
    assert not outside_destination.exists()


def test_operator_api_aioffice_supervised_architect_rehearsal_succeeds(monkeypatch, capsys, tmp_path):
    repo_root = _prepare_authoritative_operator_repo(tmp_path)
    duplicate_root = tmp_path / "duplicate"
    duplicate_root.mkdir(parents=True)
    monkeypatch.setenv("AISTUDIO_AUTHORITATIVE_ROOT", str(repo_root))
    monkeypatch.setenv("AISTUDIO_NON_AUTHORITATIVE_DUPLICATE_ROOT", str(duplicate_root))
    monkeypatch.setattr(operator_api, "ROOT", repo_root)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "operator_api.py",
            "aioffice-supervised-architect-rehearsal",
            "--confirm-supervised",
            "--operator",
            "Project Orchestrator",
            "--provider-request-id",
            "prov_test_029",
            "--reconciliation-evidence-source",
            "operator_cli_test",
        ],
    )

    operator_api.main()
    payload = json.loads(capsys.readouterr().out)

    assert payload["command"] == "aioffice-supervised-architect-rehearsal"
    assert payload["workflow_run"]["task_id"] == "AIO-029"
    assert payload["bundle"]["acceptance_state"] == "pending_review"
    assert payload["gate_checks"]["architect_completion"]["allowed"] is True
    assert payload["inspection"]["bundle_acceptance_state"] == "pending_review"
    contracts = {item["contract_name"] for item in payload["produced_artifacts"]}
    assert {"architecture_decision_v1", "provider_external_proof_v1", "architect_reconciliation_v1"} <= contracts
    rehearsal_root = Path(payload["workspace_root"])
    workflow_id = payload["workflow_run"]["id"]
    expected_files = {
        "sessions/studio.db",
        f"projects/aioffice/artifacts/m5_supervised_operator_cli_rehearsal/{workflow_id}/intake/intake_request_v1.md",
        f"projects/aioffice/artifacts/m5_supervised_operator_cli_rehearsal/{workflow_id}/pm/pm_plan_v1.md",
        f"projects/aioffice/artifacts/m5_supervised_operator_cli_rehearsal/{workflow_id}/pm/pm_assumption_register_v1.md",
        f"projects/aioffice/artifacts/m5_supervised_operator_cli_rehearsal/{workflow_id}/context_audit/context_audit_report_v1.md",
        f"projects/aioffice/artifacts/m5_supervised_operator_cli_rehearsal/{workflow_id}/architect/architecture_decision_v1.md",
        f"projects/aioffice/artifacts/m5_supervised_operator_cli_rehearsal/{workflow_id}/architect/provider_external_proof_v1.json",
        f"projects/aioffice/artifacts/m5_supervised_operator_cli_rehearsal/{workflow_id}/architect/architect_reconciliation_v1.json",
    }
    actual_files = {
        str(path.relative_to(rehearsal_root)).replace("\\", "/")
        for path in rehearsal_root.rglob("*")
        if path.is_file()
    }
    assert actual_files == expected_files
    assert "projects/tactics-game/execution/KANBAN.md" not in actual_files
    assert "memory/framework_health.json" not in actual_files
    assert "memory/session_summaries.json" not in actual_files


def test_operator_api_aio030_supervised_rehearsal_round_trips_persisted_state_via_cli(
    monkeypatch,
    capsys,
    tmp_path,
):
    repo_root = _prepare_authoritative_operator_repo(tmp_path)
    duplicate_root = tmp_path / "duplicate"
    duplicate_root.mkdir(parents=True)
    monkeypatch.setenv("AISTUDIO_AUTHORITATIVE_ROOT", str(repo_root))
    monkeypatch.setenv("AISTUDIO_NON_AUTHORITATIVE_DUPLICATE_ROOT", str(duplicate_root))
    monkeypatch.setattr(operator_api, "ROOT", repo_root)
    monkeypatch.setattr(operator_api, "_routing_catalog", lambda: {})

    rehearsal_root = "projects/aioffice/artifacts/m5_aio030_operator_cli_test/workspace"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "operator_api.py",
            "aioffice-supervised-architect-rehearsal",
            "--task-id",
            "AIO-030",
            "--confirm-supervised",
            "--operator",
            "Project Orchestrator",
            "--provider-request-id",
            "prov_test_030",
            "--reconciliation-evidence-source",
            "operator_cli_test",
            "--rehearsal-root",
            rehearsal_root,
            "--rehearsal-task",
            "Prove one supervised AIO-030 operator CLI architect-stop invocation against sanctioned persisted state.",
        ],
    )

    operator_api.main()
    rehearsal_payload = json.loads(capsys.readouterr().out)

    architect_stage = rehearsal_payload["stage_runs"]["architect"]
    assert rehearsal_payload["command"] == "aioffice-supervised-architect-rehearsal"
    assert rehearsal_payload["task_id"] == "AIO-030"
    assert rehearsal_payload["workflow_run"]["task_id"] == "AIO-030"
    assert rehearsal_payload["packet"]["workflow_run_id"] == rehearsal_payload["workflow_run"]["id"]
    assert rehearsal_payload["packet"]["stage_run_id"] == architect_stage["id"]
    assert rehearsal_payload["packet"]["provenance_note"] == "AIO-030 supervised operator CLI architect rehearsal"
    assert rehearsal_payload["bundle"]["packet_id"] == rehearsal_payload["packet"]["packet_id"]
    assert rehearsal_payload["bundle"]["acceptance_state"] == "pending_review"
    assert '--task-id "AIO-030"' in rehearsal_payload["bundle"]["commands_run"][0]

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "operator_api.py",
            "control-kernel-details",
            "--workspace-root",
            rehearsal_root,
            "--workflow-run-id",
            rehearsal_payload["workflow_run"]["id"],
            "--stage-run-id",
            architect_stage["id"],
            "--packet-id",
            rehearsal_payload["packet"]["packet_id"],
            "--bundle-id",
            rehearsal_payload["bundle"]["bundle_id"],
        ],
    )

    operator_api.main()
    inspection_payload = json.loads(capsys.readouterr().out)

    assert inspection_payload["inspection_workspace_root"] == str((repo_root / rehearsal_root).resolve())
    assert inspection_payload["workflow_run"]["id"] == rehearsal_payload["workflow_run"]["id"]
    assert inspection_payload["workflow_run"]["task_id"] == "AIO-030"
    assert inspection_payload["stage_run"]["id"] == architect_stage["id"]
    assert inspection_payload["control_execution_packet"]["packet_id"] == rehearsal_payload["packet"]["packet_id"]
    assert inspection_payload["execution_bundle"]["bundle_id"] == rehearsal_payload["bundle"]["bundle_id"]
    assert inspection_payload["execution_bundle"]["acceptance_state"] == "pending_review"
    contracts = {item["contract_name"] for item in inspection_payload["workflow_artifacts"]}
    assert {"architecture_decision_v1", "provider_external_proof_v1", "architect_reconciliation_v1"} <= contracts


def test_operator_api_aioffice_supervised_architect_rehearsal_rejects_wrong_workspace(monkeypatch, tmp_path):
    repo_root = _prepare_authoritative_operator_repo(tmp_path / "authoritative")
    duplicate_root = tmp_path / "duplicate"
    duplicate_root.mkdir(parents=True)
    write_workspace_authority_marker(
        duplicate_root,
        repo_name="_AIStudio_POC",
        canonical_root_hint=duplicate_root,
    )
    monkeypatch.setenv("AISTUDIO_AUTHORITATIVE_ROOT", str(repo_root))
    monkeypatch.setenv("AISTUDIO_NON_AUTHORITATIVE_DUPLICATE_ROOT", str(duplicate_root))

    with pytest.raises(Exception) as exc_info:
        operator_api._run_aioffice_supervised_architect_rehearsal(
            duplicate_root,
            task_id="AIO-029",
            operator_name="Project Orchestrator",
            provider_request_id="prov_test_wrong_root",
            reconciliation_evidence_source="operator_cli_test",
            confirm_supervised=True,
        )

    assert "non-authoritative duplicate workspace root" in str(exc_info.value)


def test_operator_api_aioffice_supervised_architect_rehearsal_rejects_missing_architect_artifact(
    monkeypatch,
    tmp_path,
):
    repo_root = _prepare_authoritative_operator_repo(tmp_path)
    duplicate_root = tmp_path / "duplicate"
    duplicate_root.mkdir(parents=True)
    monkeypatch.setenv("AISTUDIO_AUTHORITATIVE_ROOT", str(repo_root))
    monkeypatch.setenv("AISTUDIO_NON_AUTHORITATIVE_DUPLICATE_ROOT", str(duplicate_root))

    with pytest.raises(ValueError) as exc_info:
        operator_api._run_aioffice_supervised_architect_rehearsal(
            repo_root,
            task_id="AIO-029",
            operator_name="Project Orchestrator",
            provider_request_id="prov_test_missing_arch",
            reconciliation_evidence_source="operator_cli_test",
            confirm_supervised=True,
            create_architecture_artifact=False,
        )

    assert "architect-stage artifact missing" in str(exc_info.value)


def test_operator_api_aioffice_supervised_architect_rehearsal_rejects_ambiguous_active_workflow(
    monkeypatch,
    tmp_path,
):
    repo_root = _prepare_authoritative_operator_repo(tmp_path)
    duplicate_root = tmp_path / "duplicate"
    duplicate_root.mkdir(parents=True)
    monkeypatch.setenv("AISTUDIO_AUTHORITATIVE_ROOT", str(repo_root))
    monkeypatch.setenv("AISTUDIO_NON_AUTHORITATIVE_DUPLICATE_ROOT", str(duplicate_root))
    store, _workspace_root = operator_api._aioffice_supervised_rehearsal_store(
        repo_root,
        rehearsal_root=operator_api.AIOFFICE_SUPERVISED_REHEARSAL_ROOT,
    )
    store.create_workflow_run(
        "aioffice",
        task_id="AIO-029",
        objective="Existing active workflow.",
        authoritative_workspace_root="projects/aioffice",
        current_stage="architect",
        status="active",
    )

    with pytest.raises(ValueError) as exc_info:
        operator_api._run_aioffice_supervised_architect_rehearsal(
            repo_root,
            task_id="AIO-029",
            operator_name="Project Orchestrator",
            provider_request_id="prov_test_ambiguous",
            reconciliation_evidence_source="operator_cli_test",
            confirm_supervised=True,
        )

    assert "Ambiguous run/stage state" in str(exc_info.value)


def test_operator_api_aioffice_supervised_architect_rehearsal_rejects_missing_provider_proof(
    monkeypatch,
    tmp_path,
):
    repo_root = _prepare_authoritative_operator_repo(tmp_path)
    duplicate_root = tmp_path / "duplicate"
    duplicate_root.mkdir(parents=True)
    monkeypatch.setenv("AISTUDIO_AUTHORITATIVE_ROOT", str(repo_root))
    monkeypatch.setenv("AISTUDIO_NON_AUTHORITATIVE_DUPLICATE_ROOT", str(duplicate_root))

    with pytest.raises(ValueError) as exc_info:
        operator_api._run_aioffice_supervised_architect_rehearsal(
            repo_root,
            task_id="AIO-029",
            operator_name="Project Orchestrator",
            provider_request_id="prov_test_missing_proof",
            reconciliation_evidence_source="operator_cli_test",
            confirm_supervised=True,
            create_provider_proof=False,
        )

    assert "provider/external proof missing" in str(exc_info.value)


def test_operator_api_aioffice_supervised_architect_rehearsal_rejects_later_stage_continuation(
    monkeypatch,
    tmp_path,
):
    repo_root = _prepare_authoritative_operator_repo(tmp_path)
    duplicate_root = tmp_path / "duplicate"
    duplicate_root.mkdir(parents=True)
    monkeypatch.setenv("AISTUDIO_AUTHORITATIVE_ROOT", str(repo_root))
    monkeypatch.setenv("AISTUDIO_NON_AUTHORITATIVE_DUPLICATE_ROOT", str(duplicate_root))

    with pytest.raises(ValueError) as exc_info:
        operator_api._run_aioffice_supervised_architect_rehearsal(
            repo_root,
            task_id="AIO-029",
            operator_name="Project Orchestrator",
            provider_request_id="prov_test_later_stage",
            reconciliation_evidence_source="operator_cli_test",
            confirm_supervised=True,
            stop_after="publish",
        )

    assert "must stop after architect" in str(exc_info.value)
