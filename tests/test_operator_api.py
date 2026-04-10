from __future__ import annotations

import json
import sys

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
