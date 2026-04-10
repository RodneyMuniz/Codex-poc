from __future__ import annotations

import re
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator


GatewayDecision = Literal["ROUTE_TASK", "ROUTE_STATUS", "ROUTE_ADMIN", "NEEDS_SPLIT", "REJECT"]
GatewayIntent = Literal["TASK", "STATUS_QUERY", "POLICY_UPDATE", "AMBIGUOUS"]
GatewaySchemaVersion = Literal["intent_decision_v1"]
InterpreterSummarySchemaVersion = Literal["interpreter_summary_v1"]
InterpreterSummaryIntent = Literal["TASK"]
InterpreterTaskKind = Literal["IMPLEMENTATION", "ANALYSIS", "REVIEW", "UNKNOWN"]
TaskPacketSchemaVersion = Literal["task_packet_v1"]
TaskPacketIntent = Literal["TASK"]
TaskType = Literal["GENERAL_TASK", "IMPLEMENTATION", "ANALYSIS", "REVIEW", "UNKNOWN"]
PolicyProposalSchemaVersion = Literal["policy_proposal_v1"]
PolicyProposalIntent = Literal["POLICY_UPDATE"]
PolicyProposalStatus = Literal["PROPOSED", "APPROVED", "APPLIED", "REJECTED"]
PolicyProposalTarget = Literal["CONSENSUS_REVIEW_VOTES_REQUIRED", "UNSUPPORTED"]
PolicyAuditEventSchemaVersion = Literal["policy_audit_event_v1"]
PolicyAuditAction = Literal["PROPOSE", "APPROVE", "APPLY", "REJECT", "APPLY_FAILED"]
StatusResponseSchemaVersion = Literal["status_response_v1"]
StatusResponseIntent = Literal["STATUS_QUERY"]
StatusKind = Literal["SYSTEM", "TASK", "GOVERNANCE", "UNKNOWN"]

_REQUEST_ID_PATTERN = re.compile(r"^req_[0-9a-f]{12}$")
_INTERPRETER_ID_PATTERN = re.compile(r"^interp_[0-9a-f]{12}$")
_PROPOSAL_ID_PATTERN = re.compile(r"^proposal_[0-9a-f]{12}$")
_STATUS_ID_PATTERN = re.compile(r"^status_[0-9a-f]{12}$")


class IntentDecision(BaseModel):
    schema_version: GatewaySchemaVersion = "intent_decision_v1"
    decision: GatewayDecision
    intent: GatewayIntent
    contains_task_request: bool
    contains_policy_request: bool
    contains_status_request: bool
    safe_to_route: bool
    reason_codes: list[str] = Field(default_factory=list)
    normalized_request: str

    @field_validator("normalized_request")
    @classmethod
    def _validate_normalized_request(cls, value: str) -> str:
        collapsed = " ".join(value.split())
        if not collapsed:
            raise ValueError("normalized_request is required")
        if len(collapsed) > 160:
            raise ValueError("normalized_request must be 160 characters or fewer.")
        if any(char in collapsed for char in ("\n", "\r", "\t")):
            raise ValueError("normalized_request must be single-line and sanitized.")
        return collapsed

    @model_validator(mode="after")
    def _validate_consistency(self) -> "IntentDecision":
        if not self.reason_codes:
            raise ValueError("reason_codes must not be empty")

        if self.decision == "ROUTE_TASK":
            if self.intent != "TASK" or not self.contains_task_request:
                raise ValueError("ROUTE_TASK requires TASK intent and task detection.")
            if self.contains_policy_request or self.contains_status_request or not self.safe_to_route:
                raise ValueError("ROUTE_TASK must be task-only and safe_to_route=true.")
        elif self.decision == "ROUTE_STATUS":
            if self.intent != "STATUS_QUERY" or not self.contains_status_request:
                raise ValueError("ROUTE_STATUS requires STATUS_QUERY intent and status detection.")
            if self.contains_task_request or self.contains_policy_request or not self.safe_to_route:
                raise ValueError("ROUTE_STATUS must be status-only and safe_to_route=true.")
        elif self.decision == "ROUTE_ADMIN":
            if self.intent != "POLICY_UPDATE" or not self.contains_policy_request:
                raise ValueError("ROUTE_ADMIN requires POLICY_UPDATE intent and policy detection.")
            if self.contains_task_request or self.contains_status_request or self.safe_to_route:
                raise ValueError("ROUTE_ADMIN must not route as a task execution request.")
        elif self.decision == "NEEDS_SPLIT":
            if self.intent != "AMBIGUOUS" or self.safe_to_route:
                raise ValueError("NEEDS_SPLIT must be ambiguous and fail closed.")
        elif self.decision == "REJECT":
            if self.safe_to_route:
                raise ValueError("REJECT must fail closed.")

        return self


class TokenBudget(BaseModel):
    max_prompt_tokens: int
    max_completion_tokens: int
    max_retries: int

    @field_validator("max_prompt_tokens")
    @classmethod
    def _validate_prompt_tokens(cls, value: int) -> int:
        if value < 1 or value > 4096:
            raise ValueError("max_prompt_tokens must be between 1 and 4096.")
        return value

    @field_validator("max_completion_tokens")
    @classmethod
    def _validate_completion_tokens(cls, value: int) -> int:
        if value < 1 or value > 2048:
            raise ValueError("max_completion_tokens must be between 1 and 2048.")
        return value

    @field_validator("max_retries")
    @classmethod
    def _validate_retries(cls, value: int) -> int:
        if value < 0 or value > 3:
            raise ValueError("max_retries must be between 0 and 3.")
        return value


class InterpreterSummary(BaseModel):
    schema_version: InterpreterSummarySchemaVersion = "interpreter_summary_v1"
    summary_id: str
    source_intent: InterpreterSummaryIntent = "TASK"
    normalized_request: str
    task_kind: InterpreterTaskKind
    relevant_refs: list[str] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)
    open_questions: list[str] = Field(default_factory=list)
    safe_for_execution_path: bool = False

    @field_validator("summary_id")
    @classmethod
    def _validate_summary_id(cls, value: str) -> str:
        if not _INTERPRETER_ID_PATTERN.fullmatch(value):
            raise ValueError("summary_id must match interp_<12 lowercase hex>.")
        return value

    @field_validator("normalized_request")
    @classmethod
    def _validate_interpreter_normalized_request(cls, value: str) -> str:
        collapsed = " ".join(value.split())
        if not collapsed:
            raise ValueError("normalized_request is required")
        if len(collapsed) > 160:
            raise ValueError("normalized_request must be 160 characters or fewer.")
        if any(char in collapsed for char in ("\n", "\r", "\t")):
            raise ValueError("normalized_request must be single-line and sanitized.")
        return collapsed

    @field_validator("relevant_refs", "constraints", "open_questions")
    @classmethod
    def _validate_string_lists(cls, value: list[str], info) -> list[str]:
        collapsed = [" ".join(str(item).split()) for item in value if str(item).strip()]
        if len(collapsed) > 5:
            raise ValueError(f"{info.field_name} must contain at most 5 entries.")
        if any(len(item) > 160 for item in collapsed):
            raise ValueError(f"{info.field_name} entries must be 160 characters or fewer.")
        return collapsed

    @model_validator(mode="after")
    def _validate_interpreter_summary(self) -> "InterpreterSummary":
        if self.source_intent != "TASK":
            raise ValueError("InterpreterSummary source_intent must be TASK.")
        if not self.relevant_refs:
            raise ValueError("InterpreterSummary relevant_refs must not be empty.")
        if not self.constraints:
            raise ValueError("InterpreterSummary constraints must not be empty.")
        if self.safe_for_execution_path:
            raise ValueError("InterpreterSummary safe_for_execution_path must be false.")
        return self


class TaskPacket(BaseModel):
    schema_version: TaskPacketSchemaVersion = "task_packet_v1"
    request_id: str
    intent: TaskPacketIntent = "TASK"
    normalized_request: str
    task_type: TaskType = "GENERAL_TASK"
    safe_to_route: bool = True
    allowed_roles: list[str] = Field(default_factory=list)
    allowed_tools: list[str] = Field(default_factory=list)
    forbidden_actions: list[str] = Field(default_factory=list)
    token_budget: TokenBudget

    @field_validator("request_id")
    @classmethod
    def _validate_request_id(cls, value: str) -> str:
        if not _REQUEST_ID_PATTERN.fullmatch(value):
            raise ValueError("request_id must match req_<12 lowercase hex>.")
        return value

    @field_validator("normalized_request")
    @classmethod
    def _validate_task_normalized_request(cls, value: str) -> str:
        collapsed = " ".join(value.split())
        if not collapsed:
            raise ValueError("normalized_request is required")
        if len(collapsed) > 160:
            raise ValueError("normalized_request must be 160 characters or fewer.")
        if any(char in collapsed for char in ("\n", "\r", "\t")):
            raise ValueError("normalized_request must be single-line and sanitized.")
        return collapsed

    @field_validator("allowed_roles", "allowed_tools", "forbidden_actions")
    @classmethod
    def _validate_non_empty_lists(cls, value: list[str]) -> list[str]:
        collapsed = [item.strip() for item in value if item and item.strip()]
        if not collapsed:
            raise ValueError("packet lists must not be empty.")
        return collapsed

    @model_validator(mode="after")
    def _validate_consistency(self) -> "TaskPacket":
        if self.intent != "TASK":
            raise ValueError("TaskPacket intent must be TASK.")
        if not self.safe_to_route:
            raise ValueError("TaskPacket must be safe_to_route=true.")
        if "PromptSpecialist" not in self.allowed_roles or "Orchestrator" not in self.allowed_roles:
            raise ValueError("TaskPacket must allow PromptSpecialist and Orchestrator.")
        if "raw_text_reroute" not in self.forbidden_actions:
            raise ValueError("TaskPacket must explicitly forbid raw_text_reroute.")
        return self


class PolicyProposal(BaseModel):
    schema_version: PolicyProposalSchemaVersion = "policy_proposal_v1"
    proposal_id: str
    source_intent: PolicyProposalIntent = "POLICY_UPDATE"
    normalized_request: str
    requested_changes: list[str] = Field(default_factory=list)
    target_kind: PolicyProposalTarget = "UNSUPPORTED"
    target_file: str | None = None
    requested_value: int | None = None
    status: PolicyProposalStatus = "PROPOSED"
    created_by: str = "operator_ingress"
    approved_by: str | None = None
    approved_at: str | None = None
    applied_by: str | None = None
    applied_at: str | None = None
    rejected_by: str | None = None
    rejected_at: str | None = None
    apply_result: str | None = None
    safe_for_execution_path: bool = False

    @field_validator("proposal_id")
    @classmethod
    def _validate_proposal_id(cls, value: str) -> str:
        if not _PROPOSAL_ID_PATTERN.fullmatch(value):
            raise ValueError("proposal_id must match proposal_<12 lowercase hex>.")
        return value

    @field_validator("normalized_request")
    @classmethod
    def _validate_proposal_normalized_request(cls, value: str) -> str:
        collapsed = " ".join(value.split())
        if not collapsed:
            raise ValueError("normalized_request is required")
        if len(collapsed) > 160:
            raise ValueError("normalized_request must be 160 characters or fewer.")
        if any(char in collapsed for char in ("\n", "\r", "\t")):
            raise ValueError("normalized_request must be single-line and sanitized.")
        return collapsed

    @field_validator("requested_changes")
    @classmethod
    def _validate_requested_changes(cls, value: list[str]) -> list[str]:
        collapsed = [" ".join(str(item).split()) for item in value if str(item).strip()]
        if not collapsed:
            raise ValueError("requested_changes must not be empty.")
        if any(len(item) > 160 for item in collapsed):
            raise ValueError("requested_changes entries must be 160 characters or fewer.")
        return collapsed

    @field_validator("target_file")
    @classmethod
    def _validate_target_file(cls, value: str | None) -> str | None:
        if value is None:
            return None
        collapsed = " ".join(value.split())
        if not collapsed:
            raise ValueError("target_file must not be empty when provided.")
        if len(collapsed) > 160:
            raise ValueError("target_file must be 160 characters or fewer.")
        return collapsed

    @field_validator("requested_value")
    @classmethod
    def _validate_requested_value(cls, value: int | None) -> int | None:
        if value is None:
            return None
        if value < 1 or value > 5:
            raise ValueError("requested_value must be between 1 and 5 for v1 supported targets.")
        return value

    @field_validator(
        "approved_by",
        "approved_at",
        "applied_by",
        "applied_at",
        "rejected_by",
        "rejected_at",
        "apply_result",
    )
    @classmethod
    def _validate_optional_metadata(cls, value: str | None, info) -> str | None:
        if value is None:
            return None
        collapsed = " ".join(value.split())
        if not collapsed:
            raise ValueError(f"{info.field_name} must not be empty when provided.")
        limit = 240 if info.field_name == "apply_result" else 160
        if len(collapsed) > limit:
            raise ValueError(f"{info.field_name} must be {limit} characters or fewer.")
        return collapsed

    @model_validator(mode="after")
    def _validate_policy_proposal(self) -> "PolicyProposal":
        if self.source_intent != "POLICY_UPDATE":
            raise ValueError("PolicyProposal source_intent must be POLICY_UPDATE.")
        if self.created_by != "operator_ingress":
            raise ValueError("PolicyProposal created_by must be operator_ingress.")
        if self.safe_for_execution_path:
            raise ValueError("PolicyProposal safe_for_execution_path must be false.")
        if self.target_kind == "CONSENSUS_REVIEW_VOTES_REQUIRED":
            if self.target_file != "governance/rules.yml":
                raise ValueError("Supported consensus target must resolve to governance/rules.yml.")
            if self.requested_value is None:
                raise ValueError("Supported consensus target requires requested_value.")
        elif self.target_kind == "UNSUPPORTED":
            if self.requested_value is not None:
                raise ValueError("Unsupported proposal targets must not carry requested_value.")
        if self.status == "PROPOSED":
            if any(
                value is not None
                for value in (
                    self.approved_by,
                    self.approved_at,
                    self.applied_by,
                    self.applied_at,
                    self.rejected_by,
                    self.rejected_at,
                    self.apply_result,
                )
            ):
                raise ValueError("PROPOSED proposals must not contain approval, apply, or rejection metadata.")
        elif self.status == "APPROVED":
            if self.approved_by is None or self.approved_at is None:
                raise ValueError("APPROVED proposals require approved_by and approved_at.")
            if any(
                value is not None
                for value in (
                    self.applied_by,
                    self.applied_at,
                    self.rejected_by,
                    self.rejected_at,
                    self.apply_result,
                )
            ):
                raise ValueError("APPROVED proposals must not contain apply or rejection metadata.")
        elif self.status == "APPLIED":
            if self.approved_by is None or self.approved_at is None:
                raise ValueError("APPLIED proposals require prior approval metadata.")
            if self.applied_by is None or self.applied_at is None or self.apply_result is None:
                raise ValueError("APPLIED proposals require applied_by, applied_at, and apply_result.")
            if self.rejected_by is not None or self.rejected_at is not None:
                raise ValueError("APPLIED proposals must not contain rejection metadata.")
        elif self.status == "REJECTED":
            if self.rejected_by is None or self.rejected_at is None:
                raise ValueError("REJECTED proposals require rejected_by and rejected_at.")
            if any(
                value is not None
                for value in (
                    self.approved_by,
                    self.approved_at,
                    self.applied_by,
                    self.applied_at,
                    self.apply_result,
                )
            ):
                raise ValueError("REJECTED proposals must not contain approval or apply metadata.")
        return self


class PolicyAuditEvent(BaseModel):
    schema_version: PolicyAuditEventSchemaVersion = "policy_audit_event_v1"
    proposal_id: str
    action: PolicyAuditAction
    prior_status: PolicyProposalStatus | None = None
    new_status: PolicyProposalStatus
    actor: str
    source: str
    timestamp: str
    target_kind: PolicyProposalTarget
    result: str | None = None

    @field_validator("proposal_id")
    @classmethod
    def _validate_audit_proposal_id(cls, value: str) -> str:
        if not _PROPOSAL_ID_PATTERN.fullmatch(value):
            raise ValueError("proposal_id must match proposal_<12 lowercase hex>.")
        return value

    @field_validator("actor", "source", "timestamp", "result")
    @classmethod
    def _validate_audit_strings(cls, value: str | None, info) -> str | None:
        if value is None:
            return None
        collapsed = " ".join(value.split())
        if not collapsed:
            raise ValueError(f"{info.field_name} must not be empty when provided.")
        limit = 240 if info.field_name == "result" else 160
        if len(collapsed) > limit:
            raise ValueError(f"{info.field_name} must be {limit} characters or fewer.")
        return collapsed

    @model_validator(mode="after")
    def _validate_audit_event(self) -> "PolicyAuditEvent":
        if self.action == "PROPOSE":
            if self.prior_status is not None or self.new_status != "PROPOSED":
                raise ValueError("PROPOSE audit events must create PROPOSED state from no prior status.")
        elif self.action == "APPROVE":
            if self.prior_status != "PROPOSED" or self.new_status != "APPROVED":
                raise ValueError("APPROVE audit events must transition PROPOSED to APPROVED.")
        elif self.action == "APPLY":
            if self.prior_status != "APPROVED" or self.new_status != "APPLIED":
                raise ValueError("APPLY audit events must transition APPROVED to APPLIED.")
        elif self.action == "REJECT":
            if self.prior_status != "PROPOSED" or self.new_status != "REJECTED":
                raise ValueError("REJECT audit events must transition PROPOSED to REJECTED.")
        elif self.action == "APPLY_FAILED":
            if self.prior_status != "APPROVED" or self.new_status != "APPROVED":
                raise ValueError("APPLY_FAILED audit events must leave APPROVED proposals unchanged.")
            if self.result is None:
                raise ValueError("APPLY_FAILED audit events must record a result.")
        return self


class StatusResponse(BaseModel):
    schema_version: StatusResponseSchemaVersion = "status_response_v1"
    response_id: str
    source_intent: StatusResponseIntent = "STATUS_QUERY"
    normalized_request: str
    status_kind: StatusKind
    summary: str
    evidence_refs: list[str] = Field(default_factory=list)
    safe_for_execution_path: bool = False

    @field_validator("response_id")
    @classmethod
    def _validate_response_id(cls, value: str) -> str:
        if not _STATUS_ID_PATTERN.fullmatch(value):
            raise ValueError("response_id must match status_<12 lowercase hex>.")
        return value

    @field_validator("normalized_request")
    @classmethod
    def _validate_status_normalized_request(cls, value: str) -> str:
        collapsed = " ".join(value.split())
        if not collapsed:
            raise ValueError("normalized_request is required")
        if len(collapsed) > 160:
            raise ValueError("normalized_request must be 160 characters or fewer.")
        if any(char in collapsed for char in ("\n", "\r", "\t")):
            raise ValueError("normalized_request must be single-line and sanitized.")
        return collapsed

    @field_validator("summary")
    @classmethod
    def _validate_summary(cls, value: str) -> str:
        collapsed = " ".join(value.split())
        if not collapsed:
            raise ValueError("summary is required")
        if len(collapsed) > 240:
            raise ValueError("summary must be 240 characters or fewer.")
        return collapsed

    @field_validator("evidence_refs")
    @classmethod
    def _validate_evidence_refs(cls, value: list[str]) -> list[str]:
        collapsed = [" ".join(str(item).split()) for item in value if str(item).strip()]
        if len(collapsed) > 5:
            raise ValueError("evidence_refs must contain at most 5 entries.")
        if any(len(item) > 160 for item in collapsed):
            raise ValueError("evidence_refs entries must be 160 characters or fewer.")
        return collapsed

    @model_validator(mode="after")
    def _validate_status_response(self) -> "StatusResponse":
        if self.source_intent != "STATUS_QUERY":
            raise ValueError("StatusResponse source_intent must be STATUS_QUERY.")
        if self.safe_for_execution_path:
            raise ValueError("StatusResponse safe_for_execution_path must be false.")
        return self
