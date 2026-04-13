from __future__ import annotations

import hashlib
import re
from pathlib import Path

from intake.interpreter import compile_interpreter_summary
from intake.models import IntentDecision, InterpreterSummary, PolicyProposal, TaskPacket, TokenBudget
from workspace_root import authoritative_workspace_root


_CONSENSUS_REVIEW_VOTES_PATTERNS = (
    re.compile(r"\breview votes required to (\d+)\b", re.IGNORECASE),
    re.compile(r"\brequire (\d+) review votes\b", re.IGNORECASE),
    re.compile(r"\bset review vote requirement to (\d+)\b", re.IGNORECASE),
)


def _policy_target_details(normalized_request: str) -> tuple[str, str | None, int | None]:
    for pattern in _CONSENSUS_REVIEW_VOTES_PATTERNS:
        match = pattern.search(normalized_request)
        if match:
            return ("CONSENSUS_REVIEW_VOTES_REQUIRED", "governance/rules.yml", int(match.group(1)))
    return ("UNSUPPORTED", None, None)


def _task_packet_defaults(task_kind: str) -> tuple[list[str], list[str], TokenBudget]:
    common_roles = ["Orchestrator", "PromptSpecialist", "PM"]
    if task_kind == "IMPLEMENTATION":
        return (
            common_roles + ["Architect", "Developer", "Design", "QA"],
            [
                "model_client.create",
                "api_responses_create",
                "read_project_brief",
                "write_project_artifact",
            ],
            TokenBudget(max_prompt_tokens=1024, max_completion_tokens=512, max_total_tokens=1536, max_retries=1),
        )
    if task_kind == "ANALYSIS":
        return (
            common_roles + ["Architect", "QA"],
            [
                "model_client.create",
                "api_responses_create",
                "read_project_brief",
            ],
            TokenBudget(max_prompt_tokens=896, max_completion_tokens=384, max_total_tokens=1280, max_retries=0),
        )
    if task_kind == "REVIEW":
        return (
            common_roles + ["QA", "Architect", "Design"],
            [
                "model_client.create",
                "api_responses_create",
                "read_project_brief",
            ],
            TokenBudget(max_prompt_tokens=896, max_completion_tokens=384, max_total_tokens=1280, max_retries=0),
        )
    return (
        common_roles + ["Architect", "QA"],
        [
            "model_client.create",
            "api_responses_create",
            "read_project_brief",
        ],
        TokenBudget(max_prompt_tokens=768, max_completion_tokens=256, max_total_tokens=1024, max_retries=0),
    )


def _load_interpreter_summary(
    source: IntentDecision | InterpreterSummary,
    *,
    repo_root: str | Path | None = None,
    project_name: str | None = None,
) -> InterpreterSummary:
    if isinstance(source, InterpreterSummary):
        return InterpreterSummary.model_validate(source.model_dump())
    validated = IntentDecision.model_validate(source.model_dump())
    if validated.decision != "ROUTE_TASK" or validated.intent != "TASK" or not validated.safe_to_route:
        raise ValueError("Only safe ROUTE_TASK decisions compile to TaskPacket.")
    resolved_root = Path(repo_root).resolve() if repo_root is not None else authoritative_workspace_root()
    return compile_interpreter_summary(resolved_root, validated, project_name=project_name)


def compile_task_packet(
    source: IntentDecision | InterpreterSummary,
    *,
    repo_root: str | Path | None = None,
    project_name: str | None = None,
) -> TaskPacket:
    summary = _load_interpreter_summary(source, repo_root=repo_root, project_name=project_name)
    request_id = "req_" + hashlib.sha256(summary.normalized_request.encode("utf-8")).hexdigest()[:12]
    allowed_roles, allowed_tools, token_budget = _task_packet_defaults(summary.task_kind)

    return TaskPacket(
        request_id=request_id,
        intent="TASK",
        normalized_request=summary.normalized_request,
        task_type=summary.task_kind,  # type: ignore[arg-type]
        safe_to_route=True,
        allowed_roles=allowed_roles,
        allowed_tools=allowed_tools,
        forbidden_actions=[
            "policy_write",
            "kanban_state_change",
            "raw_text_reroute",
            "unbounded_context_lookup",
        ],
        token_budget=token_budget,
    )


def compile_policy_proposal(decision: IntentDecision) -> PolicyProposal:
    validated = IntentDecision.model_validate(decision.model_dump())
    if validated.decision != "ROUTE_ADMIN" or validated.intent != "POLICY_UPDATE" or validated.safe_to_route:
        raise ValueError("Only POLICY_UPDATE admin decisions compile to PolicyProposal.")

    proposal_id = "proposal_" + hashlib.sha256(validated.normalized_request.encode("utf-8")).hexdigest()[:12]
    target_kind, target_file, requested_value = _policy_target_details(validated.normalized_request)

    return PolicyProposal(
        proposal_id=proposal_id,
        source_intent="POLICY_UPDATE",
        normalized_request=validated.normalized_request,
        requested_changes=[validated.normalized_request],
        target_kind=target_kind,  # type: ignore[arg-type]
        target_file=target_file,
        requested_value=requested_value,
        status="PROPOSED",
        created_by="operator_ingress",
        safe_for_execution_path=False,
    )
