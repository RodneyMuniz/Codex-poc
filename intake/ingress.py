from __future__ import annotations

from typing import Any

from intake.compiler import compile_policy_proposal, compile_task_packet
from intake.gateway import classify_operator_request
from intake.models import IntentDecision, PolicyProposal
from intake.policy_store import record_policy_proposal
from intake.status import compile_status_response


def decide_operator_request(user_text: str, clarification: str | None = None) -> IntentDecision:
    combined_text = user_text if clarification is None else f"{user_text}\n\n{clarification}"
    decision = classify_operator_request(combined_text)
    return IntentDecision.model_validate(decision.model_dump())


def _allows_task_routing(decision: IntentDecision) -> bool:
    return decision.decision == "ROUTE_TASK" and decision.intent == "TASK" and decision.safe_to_route


def _allows_policy_proposal(decision: IntentDecision) -> bool:
    return decision.decision == "ROUTE_ADMIN" and decision.intent == "POLICY_UPDATE" and not decision.safe_to_route


def _allows_status_response(decision: IntentDecision) -> bool:
    return decision.decision == "ROUTE_STATUS" and decision.intent == "STATUS_QUERY" and decision.safe_to_route


def _operator_brief(decision: IntentDecision) -> dict[str, Any]:
    details_map = {
        "ROUTE_STATUS": "The request is a status query, so execution routing is blocked.",
        "ROUTE_ADMIN": "The request targets policy or governance, so execution routing is blocked.",
        "NEEDS_SPLIT": "The request mixes unsafe intent types and must be split before routing.",
        "REJECT": "The request is ambiguous or unsafe to route directly.",
    }
    return {
        "objective": decision.normalized_request,
        "details": details_map.get(decision.decision, "The request is blocked by the intent gateway."),
        "response_chips": [
            {"label": "Gateway", "value": decision.decision.replace("_", " ").title()},
            {"label": "Intent", "value": decision.intent.replace("_", " ").title()},
            {"label": "Reasons", "value": "; ".join(decision.reason_codes[:2])},
        ],
    }


def _blocked_preview_payload(project_name: str, decision: IntentDecision) -> dict[str, Any]:
    return {
        "project_name": project_name,
        "gateway_decision": decision.model_dump(),
        "operator_brief": _operator_brief(decision),
        "route_preview": [],
        "execution_runtime": {"mode": "blocked"},
    }


def _blocked_dispatch_payload(project_name: str, decision: IntentDecision) -> dict[str, Any]:
    preview = _blocked_preview_payload(project_name, decision)
    return {
        "preview": preview,
        "task": None,
        "gateway_decision": decision.model_dump(),
        "run_result": {
            "status": "not_routed",
            "run_status": "not_routed",
            "decision": decision.decision,
            "intent": decision.intent,
        },
        "dispatch_backup": None,
    }


def _blocked_intake_payload(project_name: str, decision: IntentDecision) -> dict[str, Any]:
    return {
        "project_name": project_name,
        "gateway_decision": decision.model_dump(),
        "task": None,
        "packet": None,
        "status": "not_routed",
    }


def _policy_preview_payload(project_name: str, decision: IntentDecision, proposal: PolicyProposal) -> dict[str, Any]:
    preview = _blocked_preview_payload(project_name, decision)
    preview["policy_proposal_preview"] = proposal.model_dump()
    preview["execution_runtime"] = {"mode": "proposal_only"}
    return preview


def _status_preview_payload(project_name: str, decision: IntentDecision, status_response: dict[str, Any]) -> dict[str, Any]:
    return {
        "project_name": project_name,
        "gateway_decision": decision.model_dump(),
        "status_response": status_response,
        "operator_brief": _operator_brief(decision),
        "route_preview": [],
        "execution_runtime": {"mode": "read_only"},
    }


def _proposal_dispatch_payload(
    project_name: str,
    decision: IntentDecision,
    proposal: PolicyProposal,
    record: dict[str, Any],
) -> dict[str, Any]:
    return {
        "preview": _policy_preview_payload(project_name, decision, proposal),
        "task": None,
        "gateway_decision": decision.model_dump(),
        "policy_proposal": proposal.model_dump(),
        "proposal_record": record,
        "run_result": {
            "status": "proposal_recorded",
            "run_status": "not_routed",
            "decision": decision.decision,
            "intent": decision.intent,
            "proposal_id": proposal.proposal_id,
        },
        "dispatch_backup": None,
    }


def _status_dispatch_payload(project_name: str, decision: IntentDecision, status_response: dict[str, Any]) -> dict[str, Any]:
    return {
        "preview": _status_preview_payload(project_name, decision, status_response),
        "task": None,
        "gateway_decision": decision.model_dump(),
        "status_response": status_response,
        "run_result": {
            "status": "status_only",
            "run_status": "not_routed",
            "decision": decision.decision,
            "intent": decision.intent,
        },
        "dispatch_backup": None,
    }


def _proposal_intake_payload(
    project_name: str,
    decision: IntentDecision,
    proposal: PolicyProposal,
    record: dict[str, Any],
) -> dict[str, Any]:
    return {
        "project_name": project_name,
        "gateway_decision": decision.model_dump(),
        "task": None,
        "packet": None,
        "policy_proposal": proposal.model_dump(),
        "proposal_record": record,
        "status": "proposal_recorded",
    }


def _status_intake_payload(project_name: str, decision: IntentDecision, status_response: dict[str, Any]) -> dict[str, Any]:
    return {
        "project_name": project_name,
        "gateway_decision": decision.model_dump(),
        "task": None,
        "packet": None,
        "status_response": status_response,
        "status": "status_only",
    }


async def preview_operator_request(orchestrator: Any, project_name: str, user_text: str, clarification: str | None = None) -> dict[str, Any]:
    decision = decide_operator_request(user_text, clarification)
    if _allows_status_response(decision):
        status_response = compile_status_response(orchestrator.repo_root, decision, project_name=project_name)
        return _status_preview_payload(project_name, decision, status_response.model_dump())
    if _allows_policy_proposal(decision):
        proposal = compile_policy_proposal(decision)
        return _policy_preview_payload(project_name, decision, proposal)
    if not _allows_task_routing(decision):
        return _blocked_preview_payload(project_name, decision)
    task_packet = compile_task_packet(decision, repo_root=orchestrator.repo_root, project_name=project_name)
    return await orchestrator.preview_request(
        project_name,
        task_packet=task_packet,
    )


async def dispatch_operator_request(orchestrator: Any, project_name: str, user_text: str, clarification: str | None = None) -> dict[str, Any]:
    decision = decide_operator_request(user_text, clarification)
    if _allows_status_response(decision):
        status_response = compile_status_response(orchestrator.repo_root, decision, project_name=project_name)
        return _status_dispatch_payload(project_name, decision, status_response.model_dump())
    if _allows_policy_proposal(decision):
        proposal = compile_policy_proposal(decision)
        record = record_policy_proposal(orchestrator.repo_root, proposal)
        return _proposal_dispatch_payload(project_name, decision, proposal, record)
    if not _allows_task_routing(decision):
        return _blocked_dispatch_payload(project_name, decision)
    task_packet = compile_task_packet(decision, repo_root=orchestrator.repo_root, project_name=project_name)
    return await orchestrator.dispatch_request(
        project_name,
        task_packet=task_packet,
    )


async def intake_operator_request(orchestrator: Any, project_name: str, user_text: str) -> dict[str, Any]:
    decision = decide_operator_request(user_text)
    if _allows_status_response(decision):
        status_response = compile_status_response(orchestrator.repo_root, decision, project_name=project_name)
        return _status_intake_payload(project_name, decision, status_response.model_dump())
    if _allows_policy_proposal(decision):
        proposal = compile_policy_proposal(decision)
        record = record_policy_proposal(orchestrator.repo_root, proposal)
        return _proposal_intake_payload(project_name, decision, proposal, record)
    if not _allows_task_routing(decision):
        return _blocked_intake_payload(project_name, decision)
    task_packet = compile_task_packet(decision, repo_root=orchestrator.repo_root, project_name=project_name)
    return await orchestrator.intake_request(
        project_name,
        task_packet=task_packet,
    )
