from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


Priority = Literal["low", "medium", "high"]
AgentRole = Literal["Orchestrator", "PM", "PromptSpecialist", "Architect", "Developer", "Design", "QA"]


class DelegationPacket(BaseModel):
    objective: str = Field(..., description="Short statement of the user's goal.")
    details: str = Field(..., description="Additional context or extracted constraints.")
    priority: Priority = Field("medium", description="Task priority.")
    requires_approval: bool = Field(False, description="Whether the request should pause for operator approval.")
    assumptions: list[str] = Field(default_factory=list, description="Key assumptions inferred from the request.")
    risks: list[str] = Field(default_factory=list, description="Known risks or ambiguities to surface to the operator.")


class AcceptanceCriteria(BaseModel):
    artifact_must_exist: bool = True
    required_headings: list[str] = Field(default_factory=list)
    required_keywords: list[str] = Field(default_factory=list)
    required_strings: list[str] = Field(default_factory=list)
    python_compile: bool = False
    required_input_role: Literal["Architect", "Developer", "Design"] | None = None


class SubtaskPlan(BaseModel):
    title: str
    assignee: Literal["Architect", "Developer", "Design"]
    objective: str
    details: str
    expected_artifact_path: str
    acceptance: AcceptanceCriteria
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
