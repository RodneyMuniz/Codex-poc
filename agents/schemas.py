from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


Priority = Literal["low", "medium", "high"]
AgentRole = Literal["Orchestrator", "PM", "PromptSpecialist", "Architect", "Developer", "Design", "QA"]
DeliverableContractKind = Literal["code", "image", "audio", "map", "review", "implementation_handoff"]
ExecutionTier = Literal["tier_1_senior", "tier_2_mid", "tier_3_junior"]
ExecutionChannel = Literal["chatgpt_control", "api", "deterministic"]
ExecutionLane = Literal["sync_api", "background_api", "batch_api", "deterministic"]
TaskComplexity = Literal["low", "medium", "high"]
TaskAmbiguity = Literal["low", "medium", "high"]
TaskSize = Literal["small", "medium", "large"]


class DeliverableContract(BaseModel):
    kind: DeliverableContractKind = Field(..., description="Capability-ladder contract kind for the deliverable.")
    summary: str = Field(..., description="Short human-readable description of the contract.")
    required_input_role: Literal["Architect", "Developer", "Design"] | None = Field(
        default=None,
        description="Role that must supply the upstream input before this deliverable can proceed.",
    )
    evidence_surface: str | None = Field(
        default=None,
        description="Canonical evidence surface used to validate the deliverable in review.",
    )


class DelegationPacket(BaseModel):
    objective: str = Field(..., description="Short statement of the user's goal.")
    details: str = Field(..., description="Additional context or extracted constraints.")
    priority: Priority = Field("medium", description="Task priority.")
    requires_approval: bool = Field(False, description="Whether the request should pause for operator approval.")
    assumptions: list[str] = Field(default_factory=list, description="Key assumptions inferred from the request.")
    risks: list[str] = Field(default_factory=list, description="Known risks or ambiguities to surface to the operator.")


class DesignRequestPreview(BaseModel):
    goal: str
    target_surface: str
    style_direction: str | None = None
    deliverables: list[str] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)
    open_questions: list[str] = Field(default_factory=list)


class TaskClassification(BaseModel):
    complexity: TaskComplexity
    ambiguity: TaskAmbiguity
    size: TaskSize
    rationale: list[str] = Field(default_factory=list)


class TierAssignment(BaseModel):
    tier: ExecutionTier
    channel: ExecutionChannel
    execution_lane: ExecutionLane
    model: str
    reasoning_effort: str
    route_family: str
    background_eligible: bool = False
    batch_eligible: bool = False
    cache_policy: dict[str, str | None] = Field(default_factory=dict)
    budget_policy: dict[str, float | int | str | None] = Field(default_factory=dict)
    rationale: list[str] = Field(default_factory=list)
    approval_required: bool = False
    approval_reasons: list[str] = Field(default_factory=list)


class ExecutionPacketAuthority(BaseModel):
    authority_packet_id: str
    authority_job_id: str
    authority_token: str
    authority_schema_name: str
    authority_execution_tier: ExecutionTier
    authority_execution_lane: ExecutionLane
    authority_delegated_work: bool
    priority_class: Priority
    budget_max_tokens: int
    budget_reservation_id: str | None = None
    retry_limit: int
    early_stop_rule: str


class ExecutionPacketTelemetry(BaseModel):
    packet_id: str
    job_id: str
    priority_class: Priority
    budget_reservation_id: str | None = None
    budget_max_tokens: int
    actual_total_tokens: int = 0
    retry_count: int = 0
    escalation_target: str | None = None
    stop_reason: str | None = None
    status: str


class ExecutionJobReservation(BaseModel):
    job_id: str
    priority_class: Priority
    reserved_max_tokens: int
    reservation_status: str


class DecompositionSubtask(BaseModel):
    title: str
    instructions: str
    expected_output_format: str
    assigned_tier: ExecutionTier
    execution_lane: ExecutionLane
    route_family: str
    acceptance_criteria: list[str] = Field(default_factory=list)
    assigned_role: Literal["Architect", "Developer", "Design", "QA"] | None = None


class DecompositionPlan(BaseModel):
    summary: str
    subtasks: list[DecompositionSubtask] = Field(default_factory=list)
    approval_required: bool = False
    approval_reasons: list[str] = Field(default_factory=list)


class AcceptanceCriteria(BaseModel):
    artifact_must_exist: bool = True
    required_headings: list[str] = Field(default_factory=list)
    required_keywords: list[str] = Field(default_factory=list)
    required_strings: list[str] = Field(default_factory=list)
    python_compile: bool = False
    required_input_role: Literal["Architect", "Developer", "Design"] | None = None
    deliverable_contract: DeliverableContract | None = Field(
        default=None,
        description="Shared studio contract metadata for the deliverable type.",
    )
    assigned_tier: ExecutionTier | None = Field(
        default=None,
        description="Assigned execution tier for the bounded subtask.",
    )
    execution_lane: ExecutionLane | None = Field(
        default=None,
        description="Assigned execution lane for the bounded subtask.",
    )
    route_family: str | None = Field(
        default=None,
        description="Stable prompt-family identifier for caching and evaluation.",
    )
    cache_policy: dict[str, str | None] | None = Field(
        default=None,
        description="Cache-key and retention guidance for the bounded subtask.",
    )
    budget_policy: dict[str, float | int | str | None] | None = Field(
        default=None,
        description="Budget guardrails for the bounded subtask.",
    )
    expected_output_format: str | None = Field(
        default=None,
        description="Expected output format for the bounded subtask.",
    )


class SubtaskPlan(BaseModel):
    title: str
    assignee: Literal["Architect", "Developer", "Design"]
    deliverable_type: str
    objective: str
    details: str
    expected_artifact_path: str
    acceptance: AcceptanceCriteria
    assigned_tier: ExecutionTier = "tier_3_junior"
    execution_lane: ExecutionLane = "sync_api"
    route_family: str = "execution.tier_3_junior.text.v1"
    expected_output_format: str = "text"
    allowed_tools: list[str] = Field(default_factory=list)
    requires_dispatch_approval: bool = False
    category: str = "Implementation"


class PlanSummary(BaseModel):
    summary: str
    subtasks: list[SubtaskPlan]


class ArtifactResult(BaseModel):
    artifact_path: str
    summary: str


class QAReviewResult(BaseModel):
    approved: bool
    summary: str
    issues: list[str] = Field(default_factory=list)
    checks: dict[str, bool] = Field(default_factory=dict)


class HealthCheckResult(BaseModel):
    ok: bool
    checked_tables: list[str] = Field(default_factory=list)
    checked_files: list[str] = Field(default_factory=list)
    checked_agents: list[str] = Field(default_factory=list)
    issues: list[str] = Field(default_factory=list)


class ApprovalPacket(BaseModel):
    approval_scope: Literal["program", "project"]
    target_role: str
    purpose: str
    exact_task: str
    expected_output: str
    why_now: str
    risks: list[str] = Field(default_factory=list)


class WorkerResult(BaseModel):
    role: Literal["Architect", "Developer", "Design", "QA"]
    task_id: str
    agent_run_id: str
    approved: bool | None = None
    summary: str
    artifact_path: str | None = None
    issues: list[str] = Field(default_factory=list)
