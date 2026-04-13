from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator


GovernedExternalEventType = Literal[
    "reservation.bound_to_execution",
    "execution.wrapper_invoked",
    "execution.path_selected",
    "execution.api_boundary_reached",
    "external_call.recorded",
    "external_call.provider_metadata_captured",
    "external_call.proof_missing",
    "budget.checked",
    "budget.retry_incremented",
    "budget.stop_enforced",
]
GovernedExternalClaimStatus = Literal["claimed", "missing"]
GovernedExternalProofStatus = Literal["proved", "missing"]
GovernedExternalExecutionPathClassification = Literal[
    "governed_api_executed",
    "blocked_pre_execution",
    "non_governed_execution",
]
GovernedExternalReconciliationState = Literal[
    "not_reconciled",
    "reconciliation_pending",
    "reconciled",
    "reconciliation_failed",
]
GovernedExternalTrustStatus = Literal[
    "claim_missing",
    "claimed_only",
    "proof_captured_not_reconciled",
    "trusted_reconciled",
    "reconciliation_failed",
]


def determine_claim_status(
    *,
    wrapper_invoked: bool,
    governed_path_selected: bool,
    external_call_recorded: bool,
) -> GovernedExternalClaimStatus:
    if wrapper_invoked and governed_path_selected and external_call_recorded:
        return "claimed"
    return "missing"


def determine_proof_status(*, provider_request_id: str | None) -> GovernedExternalProofStatus:
    return "proved" if isinstance(provider_request_id, str) and provider_request_id.strip() else "missing"


def determine_trust_status(
    *,
    claim_status: GovernedExternalClaimStatus,
    proof_status: GovernedExternalProofStatus,
    reconciliation_state: GovernedExternalReconciliationState,
) -> GovernedExternalTrustStatus:
    if reconciliation_state == "reconciliation_failed":
        return "reconciliation_failed"
    if claim_status != "claimed":
        return "claim_missing"
    if proof_status == "proved" and reconciliation_state == "reconciled":
        return "trusted_reconciled"
    if proof_status == "proved":
        return "proof_captured_not_reconciled"
    return "claimed_only"


class GovernedExternalExecutionEvent(BaseModel):
    event_id: str
    event_type: GovernedExternalEventType
    occurred_at: str
    run_id: str
    task_packet_id: str
    reservation_id: str
    external_call_id: str
    source_component: str
    status: str
    reason_code: str | None = None
    data: dict[str, Any] = Field(default_factory=dict)

    @field_validator(
        "event_id",
        "occurred_at",
        "run_id",
        "task_packet_id",
        "reservation_id",
        "external_call_id",
        "source_component",
        "status",
    )
    @classmethod
    def _validate_required_strings(cls, value: str) -> str:
        collapsed = " ".join(str(value).split())
        if not collapsed:
            raise ValueError("governed external event fields must not be empty.")
        return collapsed

    @field_validator("reason_code")
    @classmethod
    def _validate_optional_reason(cls, value: str | None) -> str | None:
        if value is None:
            return None
        collapsed = " ".join(str(value).split())
        return collapsed or None


class GovernedExternalCallRecord(BaseModel):
    external_call_id: str
    execution_group_id: str
    attempt_number: int = 1
    run_id: str
    task_packet_id: str
    reservation_id: str
    reservation_linkage_validated: bool = False
    reservation_status: str | None = None
    provider: str
    model: str
    execution_path: str
    execution_path_classification: GovernedExternalExecutionPathClassification | None = None
    claim_status: GovernedExternalClaimStatus
    proof_status: GovernedExternalProofStatus
    reconciliation_state: GovernedExternalReconciliationState = "not_reconciled"
    reconciliation_checked_at: str | None = None
    reconciliation_reason_code: str | None = None
    reconciliation_evidence_source: str | None = None
    trust_status: GovernedExternalTrustStatus
    budget_authority_validated: bool = False
    max_prompt_tokens: int | None = None
    max_completion_tokens: int | None = None
    max_total_tokens: int | None = None
    retry_limit: int | None = None
    observed_prompt_tokens: int | None = None
    observed_completion_tokens: int | None = None
    observed_total_tokens: int | None = None
    observed_reasoning_tokens: int | None = None
    retry_count: int = 0
    budget_stop_enforced: bool = False
    budget_stop_reason_code: str | None = None
    provider_request_id: str | None = None
    started_at: str
    finished_at: str | None = None
    outcome_status: str
    reason_code: str | None = None

    @field_validator(
        "external_call_id",
        "execution_group_id",
        "run_id",
        "task_packet_id",
        "reservation_id",
        "provider",
        "model",
        "execution_path",
        "started_at",
        "outcome_status",
    )
    @classmethod
    def _validate_required_strings(cls, value: str) -> str:
        collapsed = " ".join(str(value).split())
        if not collapsed:
            raise ValueError("governed external call fields must not be empty.")
        return collapsed

    @field_validator(
        "provider_request_id",
        "finished_at",
        "reason_code",
        "reservation_status",
        "budget_stop_reason_code",
        "reconciliation_checked_at",
        "reconciliation_reason_code",
        "reconciliation_evidence_source",
    )
    @classmethod
    def _validate_optional_strings(cls, value: str | None) -> str | None:
        if value is None:
            return None
        collapsed = " ".join(str(value).split())
        return collapsed or None

    @field_validator(
        "max_prompt_tokens",
        "max_completion_tokens",
        "max_total_tokens",
        "retry_limit",
        "observed_prompt_tokens",
        "observed_completion_tokens",
        "observed_total_tokens",
        "observed_reasoning_tokens",
    )
    @classmethod
    def _validate_optional_non_negative_ints(cls, value: int | None) -> int | None:
        if value is None:
            return None
        if int(value) < 0:
            raise ValueError("governed external call integer fields must be 0 or greater.")
        return int(value)

    @field_validator("retry_count")
    @classmethod
    def _validate_retry_count(cls, value: int) -> int:
        if int(value) < 0:
            raise ValueError("retry_count must be 0 or greater.")
        return int(value)

    @field_validator("attempt_number")
    @classmethod
    def _validate_attempt_number(cls, value: int) -> int:
        if int(value) <= 0:
            raise ValueError("attempt_number must be 1 or greater.")
        return int(value)


class GovernedPreExecutionBlockRecord(BaseModel):
    block_id: str
    occurred_at: str
    run_id: str
    task_id: str
    task_packet_id: str | None = None
    authority_packet_id: str | None = None
    block_stage: str
    block_reason_code: str

    @field_validator(
        "block_id",
        "occurred_at",
        "run_id",
        "task_id",
        "block_stage",
        "block_reason_code",
    )
    @classmethod
    def _validate_required_strings(cls, value: str) -> str:
        collapsed = " ".join(str(value).split())
        if not collapsed:
            raise ValueError("governed pre-execution block fields must not be empty.")
        return collapsed

    @field_validator("task_packet_id", "authority_packet_id")
    @classmethod
    def _validate_optional_strings(cls, value: str | None) -> str | None:
        if value is None:
            return None
        collapsed = " ".join(str(value).split())
        return collapsed or None


class GovernedExternalReconciliationRecord(BaseModel):
    reconciliation_id: str
    external_call_id: str
    execution_group_id: str
    run_id: str
    provider_request_id: str | None = None
    reconciliation_state: GovernedExternalReconciliationState
    reconciliation_checked_at: str
    reconciliation_reason_code: str | None = None
    reconciliation_evidence_source: str | None = None
    details: dict[str, Any] = Field(default_factory=dict)

    @field_validator(
        "reconciliation_id",
        "external_call_id",
        "execution_group_id",
        "run_id",
        "reconciliation_checked_at",
    )
    @classmethod
    def _validate_required_strings(cls, value: str) -> str:
        collapsed = " ".join(str(value).split())
        if not collapsed:
            raise ValueError("governed external reconciliation fields must not be empty.")
        return collapsed

    @field_validator("provider_request_id", "reconciliation_reason_code", "reconciliation_evidence_source")
    @classmethod
    def _validate_optional_strings(cls, value: str | None) -> str | None:
        if value is None:
            return None
        collapsed = " ".join(str(value).split())
        return collapsed or None
