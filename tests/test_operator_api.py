from __future__ import annotations

import json
import sys

import pytest

from scripts import operator_api


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
