from __future__ import annotations

import asyncio
import json
import re
from pathlib import Path
from typing import Any

from agents.architect import ArchitectAgent
from agents.config import get_tier_policy, load_environment, resolve_runtime_mode, resolve_tier_model, resolve_tier_reasoning_effort
from agents.design import DesignAgent
from agents.git_service import GitService
from agents.pm import ProjectManagerAgent
from agents.prompt_specialist import PromptSpecialistAgent
from agents.qa import QAAgent
from agents.developer import DeveloperAgent
from agents.schemas import (
    DecompositionPlan,
    DecompositionSubtask,
    DesignRequestPreview,
    HealthCheckResult,
    TaskClassification,
    TierAssignment,
)
from agents.telemetry import TelemetryRecorder
from intake.compiler import compile_task_packet
from intake.gateway import classify_operator_request
from intake.models import IntentDecision, TaskPacket
from kanban.board import KanbanBoard
from sessions import SessionStore
from state_machine import BOARD_STATE_IDEA, BOARD_STATE_IN_PROGRESS, BOARD_STATE_TODO
from workspace_root import ensure_authoritative_workspace_path, ensure_authoritative_workspace_root


SDK_PLANNING_LAYER = "deterministic_internal_helper"
TASK_ID_PATTERN = re.compile(r"\b([A-Z]+-\d+)\b")
BREACH_PAUSE_STATUS = "paused_breach"
BREACH_STOP_REASON = "awaiting_operator_exception"
BREACH_COMPLIANCE_MODE = "local_exception_pending"
BREACH_APPROVED_COMPLIANCE_MODE = "local_exception_approved"
DELEGATED_COMPLIANCE_MODE = "delegated"


class Orchestrator:
    def __init__(self, repo_root: str | Path | None = None) -> None:
        self.repo_root = ensure_authoritative_workspace_root(
            repo_root or Path.cwd(),
            label="orchestrator repo_root",
        )
        load_environment(self.repo_root)
        self.runtime_mode = resolve_runtime_mode()
        self.store = SessionStore(self.repo_root)
        self.board = KanbanBoard(self.repo_root, store=self.store)
        self.telemetry = TelemetryRecorder(self.repo_root)
        self.git = GitService(self.repo_root)
        self.prompt_specialist = PromptSpecialistAgent(repo_root=self.repo_root, store=self.store, telemetry=self.telemetry)

    def _read_text(self, relative_path: str) -> str:
        target_path = ensure_authoritative_workspace_path(
            self.repo_root / relative_path,
            label="orchestrator read path",
        )
        return target_path.read_text(encoding="utf-8")

    def _require_valid_task_packet(self, task_packet: TaskPacket) -> TaskPacket:
        if not isinstance(task_packet, TaskPacket):
            raise RuntimeError("No execution without validated TaskPacket.")
        try:
            validated = TaskPacket.model_validate(task_packet.model_dump())
        except Exception as exc:
            raise RuntimeError(f"Invalid TaskPacket: {exc}") from exc
        if validated.schema_version != "task_packet_v1":
            raise RuntimeError("Unsupported TaskPacket schema_version.")
        return validated

    def _require_routable_task_packet(self, task_packet: TaskPacket) -> TaskPacket:
        validated = self._require_valid_task_packet(task_packet)
        if validated.intent != "TASK" or not validated.safe_to_route:
            raise RuntimeError("Unsafe TaskPacket cannot start orchestrator routing.")
        return validated

    def _load_task_packet_payload(self, payload: Any, *, context: str = "TaskPacket contract") -> TaskPacket:
        try:
            validated = TaskPacket.model_validate(payload)
        except Exception as exc:
            raise RuntimeError(f"Invalid {context}: {exc}") from exc
        if validated.schema_version != "task_packet_v1":
            raise RuntimeError("Unsupported TaskPacket schema_version.")
        return validated

    def _load_task_packet_from_task(self, task: dict[str, Any] | None) -> TaskPacket | None:
        raw_packet = ((task or {}).get("acceptance") or {}).get("task_packet")
        if raw_packet is None:
            return None
        return self._load_task_packet_payload(raw_packet)

    def _require_task_packet_from_task(self, task: dict[str, Any] | None, *, context: str) -> TaskPacket:
        raw_packet = ((task or {}).get("acceptance") or {}).get("task_packet")
        if raw_packet is None:
            raise RuntimeError(f"Execution requires validated TaskPacket: missing task_packet for {context}.")
        validated = self._load_task_packet_payload(raw_packet, context=f"{context} TaskPacket")
        return self._require_routable_task_packet(validated)

    def _task_packet_budget_total(self, task_packet: TaskPacket) -> int:
        return int(task_packet.token_budget.max_total_tokens)

    def _task_packet_early_stop_rule(self, task_packet: TaskPacket) -> str:
        return "single_pass_only" if task_packet.token_budget.max_retries == 0 else "stop_on_first_success"

    def _merge_task_packet_acceptance(self, acceptance: dict[str, Any], task_packet: TaskPacket | None) -> dict[str, Any]:
        merged = dict(acceptance)
        if task_packet is None:
            return merged
        merged["task_packet"] = task_packet.model_dump()
        merged["budget_max_tokens"] = self._task_packet_budget_total(task_packet)
        merged["retry_limit"] = int(task_packet.token_budget.max_retries)
        merged["early_stop_rule"] = self._task_packet_early_stop_rule(task_packet)
        return merged

    def _ensure_task_packet_allows_role(self, task_packet: TaskPacket, role: str) -> None:
        if role not in task_packet.allowed_roles:
            raise RuntimeError(f"TaskPacket disallows role: {role}")

    def _ensure_task_packet_allows_tool(self, task_packet: TaskPacket, tool_name: str) -> None:
        if tool_name not in task_packet.allowed_tools:
            raise RuntimeError(f"TaskPacket disallows tool: {tool_name}")

    def _planned_preview_roles(self, preview_payload: dict[str, Any]) -> list[str]:
        roles = {"Orchestrator", "PromptSpecialist", "PM", "QA"}
        decomposition = (preview_payload.get("decomposition") or {}).get("subtasks") or []
        for item in decomposition:
            assigned_role = str((item or {}).get("assigned_role") or "").strip()
            if assigned_role:
                roles.add(assigned_role)
        return sorted(roles)

    def _enforce_preview_execution_roles(self, task_packet: TaskPacket, preview_payload: dict[str, Any]) -> None:
        for role in self._planned_preview_roles(preview_payload):
            self._ensure_task_packet_allows_role(task_packet, role)

    def _looks_like_policy_write_request(self, text: str) -> bool:
        return self._contains_any_token(
            text,
            (
                "policy",
                "governance",
                "rules",
                "rules yml",
                "permission",
                "permissions",
                "wrapper bypass",
            ),
        ) and self._contains_any_token(
            text,
            ("change", "update", "edit", "write", "modify", "allow", "bypass"),
        )

    def _looks_like_unbounded_context_lookup(self, text: str) -> bool:
        return self._contains_any_token(
            text,
            (
                "entire repo",
                "whole repo",
                "entire codebase",
                "whole codebase",
                "all files",
                "everything in the repo",
                "full history",
            ),
        )

    def _enforce_task_packet_forbidden_actions(
        self,
        task_packet: TaskPacket,
        *,
        user_text: str,
        direct_action: dict[str, Any] | None = None,
    ) -> None:
        forbidden = set(task_packet.forbidden_actions)
        lowered = user_text.lower()
        if direct_action is not None and "kanban_state_change" in forbidden:
            raise RuntimeError("TaskPacket forbids kanban_state_change.")
        if "policy_write" in forbidden and self._looks_like_policy_write_request(lowered):
            raise RuntimeError("TaskPacket forbids policy_write.")
        if "unbounded_context_lookup" in forbidden and self._looks_like_unbounded_context_lookup(lowered):
            raise RuntimeError("TaskPacket forbids unbounded_context_lookup.")

    def _bind_task_packet_to_team_state(self, team_state: dict[str, Any], task_packet: TaskPacket | None) -> dict[str, Any]:
        if task_packet is None:
            return team_state
        team_state["task_packet"] = task_packet.model_dump()
        team_state["task_packet_budget"] = task_packet.token_budget.model_dump()
        team_state["allowed_roles"] = list(task_packet.allowed_roles)
        team_state["allowed_tools"] = list(task_packet.allowed_tools)
        team_state["forbidden_actions"] = list(task_packet.forbidden_actions)
        return team_state

    def _explicit_internal_raw_text_entry(self, *, explicitly_internal: bool) -> None:
        if not explicitly_internal:
            raise RuntimeError("Raw-text entry is not allowed.")

    def _gateway_allows_task_routing(self, decision: IntentDecision) -> bool:
        return decision.decision == "ROUTE_TASK" and decision.intent == "TASK" and decision.safe_to_route

    def _gateway_operator_brief(self, decision: IntentDecision) -> dict[str, Any]:
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

    def _gateway_preview_payload(self, project_name: str, decision: IntentDecision) -> dict[str, Any]:
        return {
            "project_name": project_name,
            "gateway_decision": decision.model_dump(),
            "operator_brief": self._gateway_operator_brief(decision),
            "route_preview": [],
            "execution_runtime": {"mode": "blocked"},
        }

    def _gateway_dispatch_payload(self, project_name: str, decision: IntentDecision) -> dict[str, Any]:
        preview = self._gateway_preview_payload(project_name, decision)
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

    def _contains_any_token(self, text: str, tokens: tuple[str, ...] | list[str]) -> bool:
        lowered = text.lower()
        for token in tokens:
            pattern = r"\b" + re.escape(token.lower()).replace(r"\ ", r"\s+") + r"\b"
            if re.search(pattern, lowered):
                return True
        return False

    def load_project_brief(self, project_name: str) -> str:
        return self._read_text(f"projects/{project_name}/governance/PROJECT_BRIEF.md")

    def get_run_evidence(self, run_id: str) -> dict[str, Any]:
        return self.store.get_run_evidence(run_id)

    def _route_step(
        self,
        *,
        runtime_role: str,
        model_role: str,
        profile_label: str,
        profile_summary: str,
        reasoning_depth: str,
        cost_tier: str,
        route_reason: str,
        runtime_mode: str | None = None,
    ) -> dict[str, Any]:
        route = {
            "runtime_role": runtime_role,
            "model_role": model_role,
            "profile_label": profile_label,
            "profile_summary": profile_summary,
            "reasoning_depth": reasoning_depth,
            "cost_tier": cost_tier,
            "route_reason": route_reason,
        }
        if runtime_mode is not None:
            route["runtime_mode"] = runtime_mode
        return route

    def _operator_brief(
        self,
        *,
        objective: str,
        details: str,
        assumptions: list[str] | None = None,
        risks: list[str] | None = None,
        priority: str = "medium",
        requires_approval: bool = False,
    ) -> dict[str, Any]:
        response_chips: list[dict[str, str]] = []
        if requires_approval or risks:
            response_chips.append(
                {
                    "label": "Need Proof",
                    "value": "Confirm the scope with evidence before downstream dispatch.",
                }
            )
        else:
            response_chips.append(
                {
                    "label": "Ready",
                    "value": "The request can move forward without an approval pause.",
                }
            )
        response_chips.append({"label": "Priority", "value": priority.title()})
        if assumptions:
            response_chips.append({"label": "Assumptions", "value": "; ".join(assumptions[:2])})
        if risks:
            response_chips.append({"label": "Risks", "value": "; ".join(risks[:2])})
        return {
            "objective": objective,
            "details": details,
            "response_chips": response_chips,
        }

    def _classification_keywords(self, text: str) -> tuple[set[str], set[str], set[str]]:
        complexity_keywords = {
            "architecture",
            "schema",
            "workflow",
            "multi-agent",
            "multi agent",
            "routing",
            "migration",
            "refactor",
            "system",
        }
        ambiguity_keywords = {
            "research",
            "evaluate",
            "decide",
            "figure out",
            "what should",
            "maybe",
            "option",
            "strategy",
            "vision",
        }
        implementation_keywords = {
            "implement",
            "build",
            "update",
            "create",
            "write",
            "generate",
        }
        lowered = text.lower()
        return (
            {item for item in complexity_keywords if item in lowered},
            {item for item in ambiguity_keywords if item in lowered},
            {item for item in implementation_keywords if item in lowered},
        )

    def _classify_request_packet(self, packet: dict[str, Any], raw_request: str) -> TaskClassification:
        text = "\n".join(
            [
                raw_request,
                str(packet.get("objective") or ""),
                str(packet.get("details") or ""),
            ]
        ).strip()
        complexity_hits, ambiguity_hits, implementation_hits = self._classification_keywords(text)
        rationale: list[str] = []

        complexity = "low"
        if complexity_hits or len(text) > 600:
            complexity = "high"
            rationale.append("The request changes workflow, routing, schema, or architecture surfaces.")
        elif implementation_hits or len(text) > 220:
            complexity = "medium"
            rationale.append("The request needs structured implementation rather than a one-line action.")

        ambiguity = "low"
        if ambiguity_hits or not packet.get("details"):
            ambiguity = "high"
            rationale.append("The request requires direction-setting or unresolved judgment calls.")
        elif packet.get("risks") or packet.get("assumptions"):
            ambiguity = "medium"
            rationale.append("The request carries assumptions or risks that should stay visible.")

        size = "small"
        enumerated_steps = len(re.findall(r"^\s*\d+\.", text, flags=re.MULTILINE))
        bullet_steps = len(re.findall(r"^\s*-\s+", text, flags=re.MULTILINE))
        if enumerated_steps >= 3 or bullet_steps >= 5 or len(text) > 900:
            size = "large"
            rationale.append("The request spans multiple linked outputs or phases.")
        elif enumerated_steps >= 1 or bullet_steps >= 2 or len(text) > 320:
            size = "medium"
            rationale.append("The request is larger than a single bounded output.")

        if not rationale:
            rationale.append("The request is a small bounded execution slice.")

        return TaskClassification(
            complexity=complexity,
            ambiguity=ambiguity,
            size=size,
            rationale=rationale,
        )

    def _approval_reasons_for_request(self, classification: TaskClassification, packet: dict[str, Any], raw_request: str) -> list[str]:
        reasons: list[str] = []
        lowered = "\n".join(
            [
                raw_request,
                str(packet.get("objective") or ""),
                str(packet.get("details") or ""),
            ]
        ).lower()
        if classification.ambiguity == "high" or classification.complexity == "high":
            reasons.append("tier_1_usage")
        if classification.size == "large":
            reasons.append("large_task")
        if any(token in lowered for token in ("architecture", "architecture change", "schema", "routing", "model mapping", "approval rule")):
            reasons.append("architecture_change")
        return list(dict.fromkeys(reasons))

    def _tier_assignment_for_request(self, classification: TaskClassification, packet: dict[str, Any], raw_request: str) -> TierAssignment:
        approval_reasons = self._approval_reasons_for_request(classification, packet, raw_request)
        if classification.ambiguity == "high" or classification.complexity == "high":
            tier = "tier_1_senior"
            rationale = ["High ambiguity or high system complexity requires senior review before downstream execution."]
        elif classification.size != "small" or classification.complexity == "medium":
            tier = "tier_2_mid"
            rationale = ["The request needs structured planning and synthesis before low-cost execution."]
        else:
            tier = "tier_3_junior"
            rationale = ["The request is bounded enough for the low-cost execution lane."]
        policy = get_tier_policy(tier)
        execution_lane = self._execution_lane_for_request(classification, tier=tier)
        route_family = self._route_family_for_request(packet=packet, tier=tier)
        return TierAssignment(
            tier=tier,
            channel=policy.channel,  # type: ignore[arg-type]
            execution_lane=execution_lane,  # type: ignore[arg-type]
            model=resolve_tier_model(tier),
            reasoning_effort=resolve_tier_reasoning_effort(tier),
            route_family=route_family,
            background_eligible=execution_lane == "background_api",
            batch_eligible=classification.size == "large" and classification.ambiguity != "high",
            cache_policy=self._cache_policy_for_route(route_family, packet=packet),
            budget_policy=self._budget_policy_for_tier(tier=tier, lane=execution_lane),
            rationale=rationale,
            approval_required=bool(approval_reasons),
            approval_reasons=approval_reasons,
        )

    def _execution_lane_for_request(self, classification: TaskClassification, *, tier: str) -> str:
        if tier == "tier_1_senior":
            return "background_api"
        if classification.size == "large":
            return "background_api"
        if classification.size == "medium" or classification.complexity == "medium":
            return "background_api"
        return "sync_api"

    def _route_family_for_request(self, *, packet: dict[str, Any], tier: str) -> str:
        output_format = self._expected_output_format(packet)
        return f"execution.{tier}.{output_format}.v1"

    def _cache_policy_for_route(self, route_family: str, *, packet: dict[str, Any]) -> dict[str, str | None]:
        objective = str(packet.get("objective") or "studio-task").strip().lower().replace(" ", "-")
        objective_slug = "".join(ch if ch.isalnum() or ch in {"-", "_"} else "-" for ch in objective).strip("-") or "studio-task"
        return {
            "prompt_cache_key": f"{route_family}:{objective_slug[:48]}",
            "prompt_cache_retention": "24h",
        }

    def _budget_policy_for_tier(self, *, tier: str, lane: str) -> dict[str, float | int | str | None]:
        defaults = {
            "tier_1_senior": (2.0, 0.5),
            "tier_2_mid": (0.5, 0.25),
            "tier_3_junior": (0.1, 0.05),
        }
        hard_limit, approval_threshold = defaults[tier]
        return {
            "lane": lane,
            "estimated_cost_ceiling_usd": hard_limit,
            "approval_threshold_usd": approval_threshold,
            "max_retries": 2,
        }

    def _preferred_execution_role(self, project_name: str, packet: dict[str, Any]) -> str:
        text = f"{packet.get('objective') or ''}\n{packet.get('details') or ''}".lower()
        if self._contains_any_token(text, ("design", "visual", "ui", "art", "audio", "review gallery")):
            return "Design"
        if project_name == "program-kanban":
            return "Architect"
        return "Developer"

    def _is_design_request(self, project_name: str, packet: dict[str, Any], raw_request: str) -> bool:
        if self._preferred_execution_role(project_name, packet) == "Design":
            return True
        lowered = "\n".join(
            [
                str(packet.get("objective") or ""),
                str(packet.get("details") or ""),
                str(raw_request or ""),
            ]
        ).lower()
        return self._contains_any_token(
            lowered,
            ("design", "visual", "ui", "art", "image", "gallery", "mockup", "layout", "screen", "map", "board"),
        )

    def _infer_design_target_surface(self, text: str) -> str:
        lowered = text.lower()
        if self._contains_any_token(lowered, ("board", "map", "battlefield")):
            return "board or map concept"
        if self._contains_any_token(lowered, ("gallery", "control room")):
            return "control-room review gallery"
        if self._contains_any_token(lowered, ("hud", "menu", "overlay")):
            return "game HUD or menu surface"
        if self._contains_any_token(lowered, ("screen", "view", "page", "dashboard", "kanban", "app", "layout", "ui")):
            return "application screen or view"
        if self._contains_any_token(lowered, ("icon", "logo", "badge")):
            return "brand or icon asset"
        if self._contains_any_token(lowered, ("image", "art", "illustration", "concept")):
            return "visual concept asset"
        return "unspecified design surface"

    def _infer_style_direction(self, text: str) -> str | None:
        match = re.search(r"(?:style|visual direction|look(?: and feel)?|tone)\s*(?:is|:)?\s*([^\n.]+)", text, re.IGNORECASE)
        if match:
            value = match.group(1).strip(" -:")
            return value or None
        style_keywords = (
            "minimal",
            "cinematic",
            "tactical",
            "brutalist",
            "retro",
            "clean",
            "dark",
            "bright",
            "painterly",
            "stylized",
            "grounded",
        )
        hits = [keyword for keyword in style_keywords if keyword in text.lower()]
        if hits:
            return ", ".join(hits[:3])
        return None

    def _design_deliverables(self, text: str) -> list[str]:
        lowered = text.lower()
        deliverables = ["design request preview"]
        if self._contains_any_token(lowered, ("board", "map", "battlefield")):
            deliverables.append("board or map concept review packet")
        elif self._contains_any_token(lowered, ("screen", "view", "page", "dashboard", "kanban", "app", "ui", "layout")):
            deliverables.append("screen or UI review packet")
        elif self._contains_any_token(lowered, ("image", "art", "illustration", "concept")):
            deliverables.append("reviewable concept image direction")
        if self._contains_any_token(lowered, ("handoff", "implement", "implementation")):
            deliverables.append("implementation handoff notes")
        return deliverables

    def _design_constraints(self, packet: dict[str, Any], raw_request: str) -> list[str]:
        constraints: list[str] = []
        for item in packet.get("assumptions") or []:
            text = str(item).strip()
            if text:
                constraints.append(text)
        detail_text = "\n".join([str(packet.get("details") or ""), str(raw_request or "")])
        for line in re.split(r"[\n.]", detail_text):
            candidate = line.strip(" -")
            lowered = candidate.lower()
            if candidate and any(token in lowered for token in ("must", "should", "keep", "avoid", "without", "constraint")):
                constraints.append(candidate)
        deduped: list[str] = []
        seen: set[str] = set()
        for item in constraints:
            if item in seen:
                continue
            seen.add(item)
            deduped.append(item)
        return deduped[:5]

    def _design_open_questions(
        self,
        *,
        target_surface: str,
        style_direction: str | None,
        deliverables: list[str],
    ) -> list[str]:
        questions: list[str] = []
        if target_surface == "unspecified design surface":
            questions.append("Which surface should the first design pass target?")
        if not style_direction:
            questions.append("What visual direction or references should guide the first pass?")
        if len(deliverables) <= 1:
            questions.append("What output should come first: review notes, concept image, map, or implementation handoff?")
        return questions[:3]

    def _build_design_request_preview(self, *, packet: dict[str, Any], raw_request: str) -> DesignRequestPreview:
        combined_text = "\n".join([str(packet.get("objective") or ""), str(packet.get("details") or ""), str(raw_request or "")])
        target_surface = self._infer_design_target_surface(combined_text)
        style_direction = self._infer_style_direction(combined_text)
        deliverables = self._design_deliverables(combined_text)
        constraints = self._design_constraints(packet, raw_request)
        open_questions = self._design_open_questions(
            target_surface=target_surface,
            style_direction=style_direction,
            deliverables=deliverables,
        )
        return DesignRequestPreview(
            goal=str(packet.get("objective") or "Prepare the first design pass."),
            target_surface=target_surface,
            style_direction=style_direction,
            deliverables=deliverables,
            constraints=constraints,
            open_questions=open_questions,
        )

    def _clarification_gate(self, design_request_preview: DesignRequestPreview | None) -> dict[str, Any] | None:
        if design_request_preview is None:
            return None
        questions = [str(item) for item in design_request_preview.open_questions if str(item).strip()][:3]
        return {
            "active": bool(questions),
            "ready_to_execute": not questions,
            "questions": questions,
        }

    def _expected_output_format(self, packet: dict[str, Any]) -> str:
        text = f"{packet.get('objective') or ''}\n{packet.get('details') or ''}".lower()
        if any(token in text for token in ("python", "module", "script", "code")):
            return "python"
        if "json" in text:
            return "json"
        return "markdown"

    def _decomposition_subtask(
        self,
        *,
        title: str,
        instructions: str,
        expected_output_format: str,
        assigned_tier: str,
        execution_lane: str,
        route_family: str,
        acceptance_criteria: list[str],
        assigned_role: str | None,
    ) -> DecompositionSubtask:
        return DecompositionSubtask(
            title=title,
            instructions=instructions,
            expected_output_format=expected_output_format,
            assigned_tier=assigned_tier,  # type: ignore[arg-type]
            execution_lane=execution_lane,  # type: ignore[arg-type]
            route_family=route_family,
            acceptance_criteria=acceptance_criteria,
            assigned_role=assigned_role,  # type: ignore[arg-type]
        )

    def _build_decomposition_plan(
        self,
        project_name: str,
        packet: dict[str, Any],
        classification: TaskClassification,
        tier_assignment: TierAssignment,
    ) -> DecompositionPlan:
        objective = str(packet.get("objective") or "Deliver the requested outcome.")
        execution_role = self._preferred_execution_role(project_name, packet)
        output_format = self._expected_output_format(packet)

        if tier_assignment.tier == "tier_1_senior":
            subtasks = [
                self._decomposition_subtask(
                    title="Senior framing",
                    instructions=f"Resolve ambiguity and produce the governing approach for: {objective}",
                    expected_output_format="markdown",
                    assigned_tier="tier_1_senior",
                    execution_lane="background_api",
                    route_family="planning.tier_1_senior.markdown.v1",
                    acceptance_criteria=[
                        "Clarify assumptions and open questions.",
                        "State the chosen direction and why lower tiers can safely continue.",
                    ],
                    assigned_role="Architect",
                ),
                self._decomposition_subtask(
                    title="Mid-level implementation plan",
                    instructions="Translate the senior decision into bounded implementation steps and review checkpoints.",
                    expected_output_format="markdown",
                    assigned_tier="tier_2_mid",
                    execution_lane="background_api",
                    route_family="planning.tier_2_mid.markdown.v1",
                    acceptance_criteria=[
                        "List bounded execution steps.",
                        "Define expected output format and review gate.",
                    ],
                    assigned_role="Architect",
                ),
                self._decomposition_subtask(
                    title="Bounded execution",
                    instructions=f"Produce the approved execution artifact for: {objective}",
                    expected_output_format=output_format,
                    assigned_tier="tier_3_junior",
                    execution_lane="background_api",
                    route_family=f"execution.tier_3_junior.{output_format}.v1",
                    acceptance_criteria=[
                        "Stay inside the approved plan.",
                        "Return only the expected output artifact.",
                    ],
                    assigned_role=execution_role,
                ),
                self._decomposition_subtask(
                    title="QA validation",
                    instructions="Validate the execution artifact against the approved plan and acceptance criteria.",
                    expected_output_format="markdown",
                    assigned_tier="tier_2_mid",
                    execution_lane="background_api",
                    route_family="review.qa.markdown.v1",
                    acceptance_criteria=[
                        "Confirm acceptance criteria.",
                        "Call out any mismatch before completion.",
                    ],
                    assigned_role="QA",
                ),
            ]
        elif tier_assignment.tier == "tier_2_mid":
            subtasks = [
                self._decomposition_subtask(
                    title="Task plan",
                    instructions=f"Break the request into a bounded execution packet for: {objective}",
                    expected_output_format="markdown",
                    assigned_tier="tier_2_mid",
                    execution_lane="background_api",
                    route_family="planning.tier_2_mid.markdown.v1",
                    acceptance_criteria=[
                        "Capture constraints, expected output, and review gate.",
                    ],
                    assigned_role="Architect",
                ),
                self._decomposition_subtask(
                    title="Execution",
                    instructions=f"Produce the requested output for: {objective}",
                    expected_output_format=output_format,
                    assigned_tier="tier_3_junior",
                    execution_lane=tier_assignment.execution_lane,
                    route_family=tier_assignment.route_family,
                    acceptance_criteria=[
                        "Stay within the defined packet.",
                    ],
                    assigned_role=execution_role,
                ),
                self._decomposition_subtask(
                    title="Validation",
                    instructions="Review the execution output against the packet before completion.",
                    expected_output_format="markdown",
                    assigned_tier="tier_2_mid",
                    execution_lane="background_api",
                    route_family="review.qa.markdown.v1",
                    acceptance_criteria=[
                        "Confirm the output matches the packet and acceptance criteria.",
                    ],
                    assigned_role="QA",
                ),
            ]
        else:
            subtasks = [
                self._decomposition_subtask(
                    title="Bounded execution",
                    instructions=f"Produce the requested small output for: {objective}",
                    expected_output_format=output_format,
                    assigned_tier="tier_3_junior",
                    execution_lane=tier_assignment.execution_lane,
                    route_family=tier_assignment.route_family,
                    acceptance_criteria=[
                        "Return the requested output only.",
                        "Avoid inventing additional scope.",
                    ],
                    assigned_role=execution_role,
                ),
                self._decomposition_subtask(
                    title="Review gate",
                    instructions="Validate the small output before marking the task complete.",
                    expected_output_format="markdown",
                    assigned_tier="tier_2_mid",
                    execution_lane="sync_api",
                    route_family="review.qa.markdown.v1",
                    acceptance_criteria=[
                        "Confirm that the output is complete and bounded.",
                    ],
                    assigned_role="QA",
                ),
            ]

        return DecompositionPlan(
            summary=f"{tier_assignment.tier} route selected after classification; {len(subtasks)} bounded subtask(s) prepared before execution.",
            subtasks=subtasks,
            approval_required=tier_assignment.approval_required,
            approval_reasons=list(tier_assignment.approval_reasons),
        )

    def _ensure_execution_profile(
        self,
        project_name: str,
        task: dict[str, Any],
        preview_payload: dict[str, Any] | None,
    ) -> dict[str, Any]:
        if preview_payload and preview_payload.get("classification") and preview_payload.get("decomposition"):
            return preview_payload
        preview_packet = dict((preview_payload or {}).get("packet") or {})
        packet = {
            "objective": preview_packet.get("objective") or task.get("objective") or task["title"],
            "details": preview_packet.get("details") or task.get("details") or task.get("description") or task["title"],
            "priority": preview_packet.get("priority") or task.get("priority") or "medium",
            "requires_approval": bool(preview_packet.get("requires_approval", task.get("requires_approval"))),
            "assumptions": list(preview_packet.get("assumptions") or []),
            "risks": list(preview_packet.get("risks") or []),
        }
        classification = self._classify_request_packet(packet, task.get("raw_request") or packet["details"])
        tier_assignment = self._tier_assignment_for_request(classification, packet, task.get("raw_request") or packet["details"])
        decomposition = self._build_decomposition_plan(project_name, packet, classification, tier_assignment)
        design_request_preview = None
        if self._is_design_request(project_name, packet, task.get("raw_request") or packet["details"]):
            design_request_preview = self._build_design_request_preview(packet=packet, raw_request=task.get("raw_request") or packet["details"])
            packet["blocked_questions"] = list(design_request_preview.open_questions)
        acceptance = dict(task.get("acceptance") or {})
        acceptance.setdefault("classification", classification.model_dump())
        acceptance.setdefault("tier_assignment", tier_assignment.model_dump())
        acceptance.setdefault("decomposition", decomposition.model_dump())
        if design_request_preview is not None:
            acceptance.setdefault("design_request_preview", design_request_preview.model_dump())
        self.store.update_task(task["id"], acceptance=acceptance)
        refreshed_task = self.store.get_task(task["id"]) or task
        task.update(refreshed_task)
        return {
            **(preview_payload or {}),
            "project_name": project_name,
            "packet": packet,
            "classification": classification.model_dump(),
            "tier_assignment": tier_assignment.model_dump(),
            "decomposition": decomposition.model_dump(),
            "design_request_preview": design_request_preview.model_dump() if design_request_preview is not None else None,
        }

    def _seed_context_receipt(
        self,
        *,
        run_id: str,
        task: dict[str, Any],
        preview_payload: dict[str, Any] | None = None,
        active_lane: str | None = None,
        current_owner_role: str = "Orchestrator",
        next_reviewer: str = "PM",
        resume_conditions: list[str] | None = None,
    ) -> dict[str, Any]:
        packet = preview_payload.get("packet") if isinstance(preview_payload, dict) else {}
        assumptions = []
        blocked_questions = []
        if isinstance(packet, dict):
            assumptions = [str(item) for item in packet.get("assumptions") or [] if str(item).strip()]
            blocked_questions = [str(item) for item in packet.get("blocked_questions") or [] if str(item).strip()]
        expected_output = task.get("expected_artifact_path")
        receipt_payload = {
            "task_id": task["id"],
            "active_lane": active_lane or task["id"],
            "approved_objective": task.get("objective") or task["title"],
            "accepted_assumptions": assumptions,
            "blocked_questions": blocked_questions,
            "allowed_tools": [],
            "allowed_paths": [expected_output] if expected_output else [],
            "prior_artifact_paths": [],
            "expected_output": expected_output,
            "next_reviewer": next_reviewer,
            "resume_conditions": resume_conditions
            or ["Resume the existing lane with the same objective unless the operator changes scope."],
            "current_owner_role": current_owner_role,
        }
        if isinstance(preview_payload, dict):
            tier_assignment = preview_payload.get("tier_assignment") or {}
            classification = preview_payload.get("classification") or {}
            if isinstance(tier_assignment, dict):
                receipt_payload["assigned_tier"] = tier_assignment.get("tier")
                receipt_payload["execution_channel"] = tier_assignment.get("channel")
                receipt_payload["execution_lane"] = tier_assignment.get("execution_lane")
                receipt_payload["route_family"] = tier_assignment.get("route_family")
                receipt_payload["cache_policy"] = tier_assignment.get("cache_policy") or {}
                receipt_payload["budget_policy"] = tier_assignment.get("budget_policy") or {}
            if isinstance(classification, dict):
                receipt_payload["task_profile"] = classification
        return self.store.save_context_receipt(
            run_id,
            receipt_payload,
        )

    def _parse_target_status(self, user_text: str) -> str | None:
        lowered = user_text.lower()
        if "in progress" in lowered or "in_progress" in lowered:
            return "in_progress"
        if "in review" in lowered or "review" in lowered:
            return "in_review"
        if "ready" in lowered:
            return "ready"
        if "backlog" in lowered:
            return "backlog"
        if "blocked" in lowered:
            return "blocked"
        if "completed" in lowered or "complete" in lowered or "done" in lowered:
            return "completed"
        return None

    def _direct_board_action(self, project_name: str, user_text: str) -> dict[str, Any] | None:
        task_match = TASK_ID_PATTERN.search(user_text)
        target_status = self._parse_target_status(user_text)
        if task_match is None or target_status is None:
            return None
        task_id = task_match.group(1)
        task = self.store.get_task(task_id)
        if task is None:
            return None
        return {
            "task": task,
            "project_name": task["project_name"],
            "operator_action": {
                "action_type": "move_task_status",
                "target_task_id": task_id,
                "target_status": target_status,
            },
            "execution_runtime": {"mode": "deterministic"},
        }

    async def _preview_prompt_specialist(
        self,
        project_name: str,
        user_text: str,
        clarification: str | None = None,
        *,
        run_id: str | None = None,
        task_id: str | None = None,
    ) -> dict[str, Any]:
        combined_text = user_text if clarification is None else f"{user_text}\n\n{clarification}"
        packet = await self.prompt_specialist.process_input(combined_text, run_id=run_id, task_id=task_id)
        packet_data = packet.model_dump()
        classification = self._classify_request_packet(packet_data, combined_text)
        tier_assignment = self._tier_assignment_for_request(classification, packet_data, combined_text)
        decomposition = self._build_decomposition_plan(project_name, packet_data, classification, tier_assignment)
        design_request_preview = None
        if self._is_design_request(project_name, packet_data, combined_text):
            design_request_preview = self._build_design_request_preview(packet=packet_data, raw_request=combined_text)
            packet_data["blocked_questions"] = list(design_request_preview.open_questions)
        clarification_gate = self._clarification_gate(design_request_preview)
        preview_acceptance = {
            "classification": classification.model_dump(),
            "tier_assignment": tier_assignment.model_dump(),
            "decomposition": decomposition.model_dump(),
            "design_request_preview": design_request_preview.model_dump() if design_request_preview is not None else None,
            "clarification_gate": clarification_gate,
        }
        media_service_contracts = self.store.media_service_contracts(
            project_name,
            acceptance=preview_acceptance,
            raw_request=combined_text,
        )
        packet_data["requires_approval"] = bool(packet_data.get("requires_approval")) or decomposition.approval_required
        operator_brief = self._operator_brief(
            objective=packet_data["objective"],
            details=packet_data["details"],
            assumptions=packet_data.get("assumptions") or [],
            risks=packet_data.get("risks") or [],
            priority=str(packet_data.get("priority") or "medium"),
            requires_approval=bool(packet_data.get("requires_approval")),
        )
        operator_brief["response_chips"].append({"label": "Tier", "value": tier_assignment.tier.replace("_", " ").title()})
        operator_brief["response_chips"].append({"label": "Channel", "value": get_tier_policy(tier_assignment.tier).channel.upper()})
        operator_brief["response_chips"].append({"label": "Lane", "value": tier_assignment.execution_lane.replace("_", " ").title()})
        if design_request_preview is not None:
            operator_brief["response_chips"].append({"label": "Design Packet", "value": design_request_preview.target_surface})
        if clarification_gate and clarification_gate["active"]:
            operator_brief["response_chips"].append({"label": "Clarification", "value": f"{len(clarification_gate['questions'])} question(s)"})
        if media_service_contracts:
            families = ", ".join(sorted({contract["family"].title() for contract in media_service_contracts}))
            operator_brief["response_chips"].append({"label": "Media Services", "value": f"{families} deterministic"})
        route_preview = [
            self._route_step(
                runtime_role="PromptSpecialist",
                model_role="prompt_specialist",
                profile_label="Prompt Specialist",
                profile_summary="Translates natural-language operator intent into a delegation packet.",
                reasoning_depth="low",
                cost_tier="low",
                route_reason="Used first so the operator gets a clearer objective, assumptions, risks, and approval expectation before dispatch.",
            ),
            self._route_step(
                runtime_role="Orchestrator",
                model_role="orchestrator",
                profile_label="Project Orchestrator",
                profile_summary="Owns operator interaction, validates scope, and decides when specialist work should start or pause.",
                reasoning_depth="low",
                cost_tier="low",
                route_reason="Keeps the Studio Lead in the loop and protects framework integrity before downstream delegation.",
                runtime_mode=self.runtime_mode,
            ),
        ]
        if media_service_contracts:
            route_preview.append(
                self._route_step(
                    runtime_role="MediaService",
                    model_role="deterministic",
                    profile_label="Deterministic Media Service",
                    profile_summary="Keeps indexing, import bookkeeping, manifests, and review-state truth in platform-owned services.",
                    reasoning_depth="none",
                    cost_tier="zero",
                    route_reason="Media provenance and approval state stay deterministic even when AI specialists generate or review assets.",
                    runtime_mode="deterministic",
                )
            )
        route_preview.append(
            self._route_step(
                runtime_role=tier_assignment.tier,
                model_role=tier_assignment.model,
                profile_label=tier_assignment.tier.replace("_", " ").title(),
                profile_summary="Tier-selected API execution lane prepared after intake classification.",
                reasoning_depth=tier_assignment.reasoning_effort,
                cost_tier=get_tier_policy(tier_assignment.tier).cost_tier,
                route_reason="Downstream execution must follow the assigned tier and decomposition packet, not direct ad hoc execution.",
                runtime_mode=tier_assignment.channel,
            )
        )
        preview_usage = None
        if run_id and task_id:
            usage_events = self.store.list_usage_events(run_id, task_id=task_id)
            if usage_events:
                preview_usage = usage_events[-1]
        return {
            "project_name": project_name,
            "packet": packet_data,
            "classification": classification.model_dump(),
            "tier_assignment": tier_assignment.model_dump(),
            "decomposition": decomposition.model_dump(),
            "design_request_preview": design_request_preview.model_dump() if design_request_preview is not None else None,
            "clarification_gate": clarification_gate,
            "media_service_contracts": media_service_contracts,
            "operator_brief": operator_brief,
            "route_preview": route_preview,
            "execution_runtime": {"mode": self.runtime_mode},
            "prompt_specialist_usage": preview_usage,
        }

    def _preview_direct_board_action(self, direct_action: dict[str, Any], user_text: str) -> dict[str, Any]:
        task = direct_action["task"]
        target_status = direct_action["operator_action"]["target_status"]
        return {
            "project_name": direct_action["project_name"],
            "task": task,
            "packet": {
                "objective": task["objective"] or task["title"],
                "details": task["details"],
                "request_text": user_text,
            },
            "operator_action": direct_action["operator_action"],
            "operator_brief": self._operator_brief(
                objective=task["objective"] or task["title"],
                details=task["details"],
                assumptions=[],
                risks=[],
                priority=str(task.get("priority") or "medium"),
                requires_approval=target_status == "completed",
            ),
            "route_preview": [
                self._route_step(
                    runtime_role="Orchestrator",
                    model_role="orchestrator",
                    profile_label="Project Orchestrator",
                    profile_summary="Owns operator interaction and direct board actions.",
                    reasoning_depth="low",
                    cost_tier="low",
                    route_reason="Direct board actions bypass the Prompt Specialist and execute as a one-hop deterministic route.",
                    runtime_mode="deterministic",
                ),
            ],
            "execution_runtime": {"mode": "deterministic"},
        }

    async def _record_tracked_prompt_usage(
        self,
        *,
        run_id: str,
        task: dict[str, Any],
        preview_payload: dict[str, Any] | None,
    ) -> None:
        if not isinstance(preview_payload, dict):
            return
        if preview_payload.get("operator_action"):
            return
        preview_usage = preview_payload.get("prompt_specialist_usage")
        if isinstance(preview_usage, dict):
            self.store.record_usage(
                run_id,
                task["id"],
                source=str(preview_usage.get("source") or "PromptSpecialist"),
                prompt_tokens=int(preview_usage.get("prompt_tokens") or 0),
                completion_tokens=int(preview_usage.get("completion_tokens") or 0),
                model=preview_usage.get("model"),
                tier=preview_usage.get("tier"),
                lane=preview_usage.get("lane"),
                cached_input_tokens=int(preview_usage.get("cached_input_tokens") or 0),
                reasoning_tokens=int(preview_usage.get("reasoning_tokens") or 0),
                estimated_cost_usd=float(preview_usage.get("estimated_cost_usd") or 0.0),
            )
            summary = "Prompt-specialist preview usage copied into the execution run without a second intake call."
            packet = preview_usage
            route_reason = "Reused preview-time usage evidence instead of paying for a second intake call."
        else:
            raw_request = str(task.get("raw_request") or "").strip()
            if not raw_request:
                return
            try:
                packet_model = await self.prompt_specialist.process_input(raw_request, run_id=run_id, task_id=task["id"])
            except Exception as exc:
                self.store.record_trace_event(
                    run_id,
                    task["id"],
                    "prompt_specialist_usage_failed",
                    source="PromptSpecialist",
                    summary="Tracked prompt-specialist intake usage could not be recorded.",
                    packet={"error": str(exc)},
                    route={
                        "runtime_role": "PromptSpecialist",
                        "model_role": "prompt_specialist",
                        "runtime_mode": "api",
                        "route_reason": "Tracked intake call required because preview usage evidence was unavailable.",
                    },
                )
                raise
            packet = packet_model.model_dump()
            summary = "Tracked prompt-specialist intake usage recorded for this run."
            route_reason = "Tracked intake call required because preview usage evidence was unavailable."
        self.store.record_trace_event(
            run_id,
            task["id"],
            "prompt_specialist_usage_recorded",
            source="PromptSpecialist",
            summary=summary,
            packet=packet,
            route={
                "runtime_role": "PromptSpecialist",
                "model_role": "prompt_specialist",
                "runtime_mode": "api",
                "route_reason": route_reason,
            },
        )

    def _already_progressed_payload(self, run: dict[str, Any], *, approval_id: str | None = None) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "status": "already_progressed",
            "run_id": run["id"],
            "run_status": run["status"],
            "task_id": run["task_id"],
        }
        if approval_id is not None:
            payload["approval_id"] = approval_id
        return payload

    def _record_compliance_once(
        self,
        *,
        run_id: str,
        task: dict[str, Any],
        record_kind: str,
        details: str,
        policy_area: str | None = None,
        violation_type: str | None = None,
        severity: str = "info",
        local_exception_approval_id: str | None = None,
        source_role: str | None = "Orchestrator",
        decision_note: str | None = None,
        evidence: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        existing = self.store.list_compliance_records(run_id, task_id=task["id"], record_kind=record_kind)
        if existing:
            return existing[0]
        return self.store.record_compliance_record(
            run_id,
            task["id"],
            record_kind=record_kind,
            details=details,
            policy_area=policy_area,
            violation_type=violation_type,
            severity=severity,
            local_exception_approval_id=local_exception_approval_id,
            source_role=source_role,
            decision_note=decision_note,
            evidence=evidence,
        )

    def _normalize_violation_items(self, value: Any) -> list[Any]:
        if value is None:
            return []
        if isinstance(value, list):
            return value
        return [value]

    def _extract_breach_payload(self, result: dict[str, Any]) -> dict[str, Any] | None:
        compliance = result.get("compliance")
        if isinstance(compliance, dict):
            status = str(compliance.get("status") or "").lower()
            if status in {"breach", "violated", "paused", "pause"}:
                return compliance
        breach = result.get("breach")
        if isinstance(breach, dict):
            return breach

        violations: list[Any] = []
        for key in ("policy_violation", "budget_violation", "violations"):
            violations.extend(self._normalize_violation_items(result.get(key)))
        pause_reason = str(result.get("pause_reason") or result.get("stop_reason") or "").lower()
        if violations or any(token in pause_reason for token in ("policy", "budget", "breach", "violation")):
            return {
                "kind": "policy" if "policy" in pause_reason else "budget" if "budget" in pause_reason else "compliance",
                "summary": result.get("summary") or result.get("message") or pause_reason or "Compliance breach detected.",
                "violations": violations,
                "local_exception_allowed": bool(
                    result.get("local_exception_allowed")
                    or result.get("allow_local_exception")
                    or result.get("framework_repair")
                ),
            }
        if result.get("policy_violation") is True or result.get("budget_violation") is True:
            return {
                "kind": "policy" if result.get("policy_violation") else "budget",
                "summary": result.get("summary") or "Compliance breach detected.",
                "violations": violations,
                "local_exception_allowed": bool(result.get("local_exception_allowed") or result.get("allow_local_exception")),
            }
        return None

    def _pause_for_breach(
        self,
        *,
        run_id: str,
        task: dict[str, Any],
        breach: dict[str, Any],
        preview_payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        summary = str(breach.get("summary") or breach.get("message") or "Compliance breach detected.")
        violations = self._normalize_violation_items(breach.get("violations"))
        approval = self.store.create_approval(
            run_id,
            task["id"],
            "Orchestrator",
            summary,
            approval_scope="program",
            target_role="Orchestrator",
            exact_task=task["title"],
            expected_output=task.get("expected_artifact_path"),
            why_now="A policy or budget violation paused the run and needs explicit operator intervention.",
            risks=[str(item) for item in violations] if violations else [summary],
        )
        policy_area = str(breach.get("kind") or "compliance")
        violation_type = policy_area
        current_team_state = self.store.load_team_state(run_id) or {}
        current_team_state.setdefault("runtime_mode", self.runtime_mode)
        current_team_state["phase"] = "awaiting_operator_exception"
        current_team_state["execution_mode"] = "local_exception"
        current_team_state["compliance_state"] = {
            "mode": BREACH_COMPLIANCE_MODE,
            "kind": str(breach.get("kind") or "compliance"),
            "summary": summary,
            "violations": violations,
            "approval_id": approval["id"],
            "local_exception_allowed": bool(breach.get("local_exception_allowed")),
        }
        self.store.update_run(
            run_id,
            status=BREACH_PAUSE_STATUS,
            stop_reason=BREACH_STOP_REASON,
            team_state=current_team_state,
        )
        self.store.save_context_receipt(
            run_id,
            {
                "active_lane": task["id"],
                "next_reviewer": "Operator",
                "resume_conditions": [
                    "Local exception approval is required before the same run can continue.",
                ],
                "current_owner_role": "Orchestrator",
            },
        )
        self.store.record_compliance_record(
            run_id=run_id,
            task_id=task["id"],
            record_kind="breach",
            details=f"{summary} Violations: {', '.join(str(item) for item in violations) if violations else 'none recorded'}.",
            policy_area=policy_area,
            violation_type=violation_type,
            severity="high",
            evidence={
                "summary": summary,
                "violations": violations,
                "local_exception_allowed": bool(breach.get("local_exception_allowed")),
                "approval_id": approval["id"],
            },
        )
        self.store.record_trace_event(
            run_id,
            task["id"],
            "compliance_breach_paused",
            source="Orchestrator",
            summary=summary,
            packet={
                "approval_id": approval["id"],
                "kind": breach.get("kind") or "compliance",
                "violations": violations,
                "local_exception_allowed": bool(breach.get("local_exception_allowed")),
            },
            route={
                "runtime_role": "Orchestrator",
                "model_role": "orchestrator",
                "profile_label": "Project Orchestrator",
                "profile_summary": "Pauses breached runs and records the operator exception path.",
                "reasoning_depth": "low",
                "cost_tier": "low",
                "route_reason": "A policy or budget violation requires explicit operator intervention before work can continue.",
                "runtime_mode": self.runtime_mode,
            },
            raw_json={"breach": breach, "approval": approval, "preview": preview_payload or {}},
        )
        return {
            "status": BREACH_PAUSE_STATUS,
            "run_status": BREACH_PAUSE_STATUS,
            "run_id": run_id,
            "task_id": task["id"],
            "approval_id": approval["id"],
            "breach": breach,
            "preview": preview_payload,
        }

    def _pause_for_standard_approval(
        self,
        *,
        run_id: str,
        task: dict[str, Any],
        approval: dict[str, Any],
        preview_payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        current_team_state = self.store.load_team_state(run_id) or {}
        current_team_state.setdefault("runtime_mode", self.runtime_mode)
        current_team_state["phase"] = "awaiting_approval"
        current_team_state["execution_mode"] = "worker_only"
        current_team_state.setdefault("compliance_state", {"mode": DELEGATED_COMPLIANCE_MODE})
        self.store.update_run(
            run_id,
            status="paused_approval",
            stop_reason="awaiting_operator_approval",
            team_state=current_team_state,
        )
        self.store.save_context_receipt(
            run_id,
            {
                "active_lane": task["id"],
                "next_reviewer": "Operator",
                "resume_conditions": [
                    "Approval is required before PM planning and delegation can continue.",
                ],
                "current_owner_role": "Orchestrator",
            },
        )
        return {
            "status": "paused_approval",
            "run_status": "paused_approval",
            "run_id": run_id,
            "task_id": task["id"],
            "approval_id": approval["id"],
            "preview": preview_payload,
        }

    def _resolve_local_exception_approval(
        self,
        *,
        approval: dict[str, Any],
        task: dict[str, Any],
        note: str | None = None,
    ) -> dict[str, Any]:
        if "one_shot" in approval:
            if approval["status"] != "approved":
                return self.store.decide_local_exception_approval(approval["id"], "approve", note)
            return approval
        local_exception = self.store.latest_local_exception_approval_for_task(task["id"])
        if local_exception is None or local_exception["run_id"] != approval["run_id"]:
            local_exception = self.store.create_local_exception_approval(
                approval["run_id"],
                task["id"],
                approval.get("requested_by") or "Orchestrator",
                approval.get("reason") or "Approved local exception resume.",
                approval_scope="local-exception",
                target_role=approval.get("target_role"),
                exact_task=approval.get("exact_task") or task["title"],
                expected_output=approval.get("expected_output") or task.get("expected_artifact_path"),
                why_now=approval.get("why_now"),
                risks=list(approval.get("risks") or []),
            )
        if local_exception["status"] != "approved":
            local_exception = self.store.decide_local_exception_approval(local_exception["id"], "approve", note)
        return local_exception

    async def _resume_after_approval(
        self,
        *,
        approval: dict[str, Any],
        note: str | None = None,
    ) -> dict[str, Any]:
        run = self.store.get_run(approval["run_id"])
        if run is None:
            raise ValueError(f"Run not found for approval {approval['run_id']}")
        task = self.store.get_task(run["task_id"])
        if task is None:
            raise ValueError(f"Task not found for run {run['id']}")
        if approval["status"] != "approved":
            approval = self.store.decide_approval(approval["id"], "approve", note)
        team_state = self.store.load_team_state(run["id"]) or {}
        if run["status"] == BREACH_PAUSE_STATUS:
            team_state["phase"] = "resumed"
            team_state["execution_mode"] = "local_exception"
            local_exception_approval = self._resolve_local_exception_approval(approval=approval, task=task, note=note)
            compliance_state = dict(team_state.get("compliance_state") or {})
            compliance_state.update(
                {
                    "mode": BREACH_APPROVED_COMPLIANCE_MODE,
                    "approval_id": local_exception_approval["id"],
                    "approved_at": local_exception_approval.get("decided_at"),
                }
            )
            team_state["compliance_state"] = compliance_state
            self.store.update_run(run["id"], status="running", stop_reason=None, team_state=team_state)
            return await self._execute_run(run["id"], task, local_exception_approval=local_exception_approval)
        if run["status"] != "paused_approval":
            return self._already_progressed_payload(run, approval_id=approval["id"])
        team_state["phase"] = "resumed"
        team_state["execution_mode"] = "worker_only"
        self.store.update_run(run["id"], status="running", stop_reason=None, team_state=team_state)
        return await self._execute_run(run["id"], task)

    async def preview_request(
        self,
        project_name: str,
        *,
        task_packet: TaskPacket,
    ) -> dict[str, Any]:
        validated_packet = self._require_routable_task_packet(task_packet)
        self._ensure_task_packet_allows_role(validated_packet, "Orchestrator")
        self._ensure_task_packet_allows_role(validated_packet, "PromptSpecialist")
        self._ensure_task_packet_allows_tool(validated_packet, "model_client.create")
        user_text = validated_packet.normalized_request
        direct_action = self._direct_board_action(project_name, user_text)
        self._enforce_task_packet_forbidden_actions(validated_packet, user_text=user_text, direct_action=direct_action)
        if direct_action is not None:
            preview = self._preview_direct_board_action(direct_action, user_text)
            preview["task_packet"] = validated_packet.model_dump()
            return preview
        preview = await self._preview_prompt_specialist(project_name, user_text, None)
        self._enforce_preview_execution_roles(validated_packet, preview)
        preview["task_packet"] = validated_packet.model_dump()
        return preview

    async def _preview_request_from_text(
        self,
        project_name: str,
        user_text: str,
        clarification: str | None = None,
        *,
        explicitly_internal: bool = False,
    ) -> dict[str, Any]:
        self._explicit_internal_raw_text_entry(explicitly_internal=explicitly_internal)
        decision = classify_operator_request(user_text if clarification is None else f"{user_text}\n\n{clarification}")
        if not self._gateway_allows_task_routing(decision):
            return self._gateway_preview_payload(project_name, decision)
        task_packet = compile_task_packet(decision, repo_root=self.repo_root, project_name=project_name)
        return await self.preview_request(
            project_name,
            task_packet=task_packet,
        )

    async def dispatch_request(
        self,
        project_name: str,
        *,
        task_packet: TaskPacket,
    ) -> dict[str, Any]:
        validated_packet = self._require_routable_task_packet(task_packet)
        self._ensure_task_packet_allows_role(validated_packet, "Orchestrator")
        self._ensure_task_packet_allows_role(validated_packet, "PromptSpecialist")
        self._ensure_task_packet_allows_tool(validated_packet, "model_client.create")
        user_text = validated_packet.normalized_request
        direct_action = self._direct_board_action(project_name, user_text)
        self._enforce_task_packet_forbidden_actions(validated_packet, user_text=user_text, direct_action=direct_action)
        if direct_action is not None:
            preview = self._preview_direct_board_action(direct_action, user_text)
        else:
            provisional_title = user_text.strip().splitlines()[0][:80] or "New request"
            task = self.store.create_task(
                project_name,
                provisional_title,
                user_text,
                objective=provisional_title,
                status="backlog",
                requires_approval=False,
                owner_role="Orchestrator",
                task_kind="request",
                priority="medium",
                raw_request=user_text,
                acceptance=self._merge_task_packet_acceptance({"task_state": BOARD_STATE_IDEA}, validated_packet),
            )
            preview_run = self.store.create_run(
                project_name,
                task["id"],
                team_state=self._bind_task_packet_to_team_state(
                    {"phase": "request_preview", "runtime_mode": self.runtime_mode, "execution_mode": "preview_only"},
                    validated_packet,
                ),
            )
            preview = await self._preview_prompt_specialist(
                project_name,
                user_text,
                None,
                run_id=preview_run["id"],
                task_id=task["id"],
            )
            self._enforce_preview_execution_roles(validated_packet, preview)
            packet = preview["packet"]
            clarification_gate = preview.get("clarification_gate") or {}
            review_notes = None
            if clarification_gate.get("active"):
                review_notes = "Awaiting design clarification: " + " | ".join(clarification_gate.get("questions") or [])
            task = self.store.update_task(
                task["id"],
                title=packet["objective"][:80],
                details=packet["details"],
                objective=packet["objective"],
                priority=str(packet.get("priority") or "medium"),
                requires_approval=bool(packet.get("requires_approval")),
                raw_request=user_text,
                acceptance=self._merge_task_packet_acceptance({
                    "classification": preview.get("classification"),
                    "tier_assignment": preview.get("tier_assignment"),
                    "decomposition": preview.get("decomposition"),
                    "design_request_preview": preview.get("design_request_preview"),
                    "clarification_gate": preview.get("clarification_gate"),
                    "media_service_contracts": preview.get("media_service_contracts"),
                }, validated_packet),
                review_notes=review_notes,
            )
            preview["task"] = task
            self._seed_context_receipt(
                run_id=preview_run["id"],
                task=task,
                preview_payload=preview,
                next_reviewer="Operator",
                resume_conditions=(
                    ["Answer the blocking design questions before execution can start."]
                    if clarification_gate.get("active")
                    else ["Request preview recorded. Continue into execution only after operator confirmation."]
                ),
            )
            self.store.record_artifact(
                preview_run["id"],
                task["id"],
                "request_preview",
                json.dumps(
                    {
                        "packet": preview.get("packet"),
                        "design_request_preview": preview.get("design_request_preview"),
                        "clarification_gate": preview.get("clarification_gate"),
                        "media_service_contracts": preview.get("media_service_contracts"),
                    },
                    ensure_ascii=True,
                    indent=2,
                ),
            )
            preview_team_state = self.store.load_team_state(preview_run["id"]) or {}
            preview_team_state["phase"] = "preview_recorded"
            preview_team_state["execution_mode"] = "preview_only"
            if clarification_gate.get("active"):
                preview_team_state["clarification_gate"] = clarification_gate
            self.store.update_run(
                preview_run["id"],
                status="completed",
                stop_reason="awaiting_design_clarification" if clarification_gate.get("active") else "request_preview_recorded",
                team_state=preview_team_state,
                completed=True,
            )
            if clarification_gate.get("active"):
                return {
                    "preview": preview,
                    "task": task,
                    "task_packet": validated_packet.model_dump(),
                    "run_result": {
                        "status": "needs_clarification",
                        "run_status": "needs_clarification",
                        "run_id": preview_run["id"],
                        "task_id": task["id"],
                        "questions": list(clarification_gate.get("questions") or []),
                    },
                    "dispatch_backup": None,
                }
        task = preview.get("task")
        if task is None:
            packet = preview["packet"]
            task = self.store.create_task(
                preview["project_name"],
                packet["objective"][:80],
                packet["details"],
                objective=packet["objective"],
                status="backlog",
                requires_approval=bool(packet.get("requires_approval")),
                owner_role="Orchestrator",
                task_kind="request",
                priority=str(packet.get("priority") or "medium"),
                raw_request=user_text,
                acceptance=self._merge_task_packet_acceptance({
                    "classification": preview.get("classification"),
                    "tier_assignment": preview.get("tier_assignment"),
                    "decomposition": preview.get("decomposition"),
                    "design_request_preview": preview.get("design_request_preview"),
                }, validated_packet),
            )
            preview["task"] = task
        backup_info = self.store.create_dispatch_backup(
            project_name=preview["project_name"],
            trigger="dispatch_request",
            task_id=task["id"],
            note=user_text,
        )
        self._ensure_task_packet_allows_role(validated_packet, "PM")
        run_result = await self.start_task(
            task["id"],
            preview_payload=preview,
            backup_info=backup_info,
            task_packet=validated_packet,
        )
        refreshed_task = self.store.get_task(task["id"]) or task
        return {
            "preview": preview,
            "task": refreshed_task,
            "task_packet": validated_packet.model_dump(),
            "run_result": run_result,
            "dispatch_backup": backup_info,
        }

    async def _dispatch_request_from_text(
        self,
        project_name: str,
        user_text: str,
        clarification: str | None = None,
        *,
        explicitly_internal: bool = False,
    ) -> dict[str, Any]:
        self._explicit_internal_raw_text_entry(explicitly_internal=explicitly_internal)
        decision = classify_operator_request(user_text if clarification is None else f"{user_text}\n\n{clarification}")
        if not self._gateway_allows_task_routing(decision):
            return self._gateway_dispatch_payload(project_name, decision)
        task_packet = compile_task_packet(decision, repo_root=self.repo_root, project_name=project_name)
        return await self.dispatch_request(
            project_name,
            task_packet=task_packet,
        )

    async def approve_and_resume(self, approval_id: str, note: str | None = None) -> dict[str, Any]:
        approval = self.store.get_approval(approval_id)
        if approval is None:
            raise ValueError(f"Approval not found: {approval_id}")
        return await self._resume_after_approval(approval=approval, note=note)

    async def start_task(
        self,
        task_id: str,
        *,
        preview_payload: dict[str, Any] | None = None,
        backup_info: dict[str, Any] | None = None,
        task_packet: TaskPacket | None = None,
    ) -> dict[str, Any]:
        task = self.store.get_task(task_id)
        if task is None:
            raise ValueError(f"Task not found: {task_id}")
        if task_packet is not None:
            resolved_task_packet = self._require_routable_task_packet(task_packet)
        else:
            resolved_task_packet = self._require_task_packet_from_task(task, context="start_task")
        self._ensure_task_packet_allows_role(resolved_task_packet, "Orchestrator")
        merged_acceptance = self._merge_task_packet_acceptance(dict(task.get("acceptance") or {}), resolved_task_packet)
        if merged_acceptance != (task.get("acceptance") or {}):
            task = self.store.update_task(task_id, acceptance=merged_acceptance or None)
        if not (preview_payload and preview_payload.get("operator_action")):
            preview_payload = self._ensure_execution_profile(task["project_name"], task, preview_payload)
        if task["project_name"] == "program-kanban":
            acceptance = dict(task.get("acceptance") or {})
            if isinstance(preview_payload, dict):
                for key in (
                    "classification",
                    "tier_assignment",
                    "decomposition",
                    "design_request_preview",
                    "clarification_gate",
                    "proposed_milestone",
                    "entry_goal",
                    "exit_goal",
                    "milestone_status",
                    "milestone_owner_role",
                    "milestone_slug",
                ):
                    value = preview_payload.get(key)
                    if value is not None and key not in acceptance:
                        acceptance[key] = value
            acceptance = self._merge_task_packet_acceptance(acceptance, resolved_task_packet)
            if acceptance != (task.get("acceptance") or {}) or not task.get("milestone_id"):
                task = self.store.update_task(task_id, acceptance=acceptance or None)
        clarification_gate = None
        if isinstance(preview_payload, dict):
            clarification_gate = preview_payload.get("clarification_gate")
        if clarification_gate is None:
            clarification_gate = (task.get("acceptance") or {}).get("clarification_gate")
        if isinstance(clarification_gate, dict) and clarification_gate.get("active"):
            updated_task = self.store.update_task(
                task_id,
                status="backlog",
                owner_role="Orchestrator",
                review_notes="Awaiting design clarification: " + " | ".join(clarification_gate.get("questions") or []),
            )
            return {
                "status": "needs_clarification",
                "run_status": "needs_clarification",
                "task_id": task_id,
                "task": updated_task,
                "questions": list(clarification_gate.get("questions") or []),
                "dispatch_backup": backup_info,
                "preview": preview_payload,
            }
        if preview_payload and preview_payload.get("operator_action", {}).get("action_type") == "move_task_status":
            if resolved_task_packet is not None:
                self._enforce_task_packet_forbidden_actions(
                    resolved_task_packet,
                    user_text=str(resolved_task_packet.normalized_request),
                    direct_action=preview_payload.get("operator_action"),
                )
            target_status = preview_payload["operator_action"]["target_status"]
            review_state = "Accepted" if target_status == "completed" else "Revision Needed"
            updated_task = self.store.update_task(task_id, status=target_status, review_state=review_state)
            run = self.store.create_run(
                task["project_name"],
                task_id,
                team_state=self._bind_task_packet_to_team_state(
                    {"runtime_mode": self.runtime_mode, "dispatch_mode": "deterministic"},
                    resolved_task_packet,
                ),
            )
            self._seed_context_receipt(
                run_id=run["id"],
                task=task,
                preview_payload=preview_payload,
                next_reviewer="Operator",
                resume_conditions=["Direct board action completed locally."],
            )
            current_team_state = self.store.load_team_state(run["id"]) or {}
            current_team_state.setdefault("runtime_mode", self.runtime_mode)
            current_team_state["dispatch_mode"] = "deterministic"
            current_team_state["phase"] = "completed"
            self.store.update_run(
                run["id"],
                status="completed",
                stop_reason="direct_board_action",
                team_state=current_team_state,
                completed=True,
            )
            return {
                "status": "completed",
                "run_status": "completed",
                "run_id": run["id"],
                "task_id": task_id,
                "target_task_id": task_id,
                "task": updated_task,
                "dispatch_backup": backup_info,
                "preview": preview_payload,
            }
        run = self.store.create_run(
            task["project_name"],
            task_id,
            team_state=self._bind_task_packet_to_team_state(
                {"phase": "intake", "runtime_mode": self.runtime_mode},
                resolved_task_packet,
            ),
        )
        await self._record_tracked_prompt_usage(run_id=run["id"], task=task, preview_payload=preview_payload)
        self._seed_context_receipt(run_id=run["id"], task=task, preview_payload=preview_payload)
        if resolved_task_packet is not None:
            self._ensure_task_packet_allows_role(resolved_task_packet, "PM")
            self.store.save_context_receipt(
                run["id"],
                {
                    "task_packet_request_id": resolved_task_packet.request_id,
                    "allowed_roles": list(resolved_task_packet.allowed_roles),
                    "allowed_tools": list(resolved_task_packet.allowed_tools),
                    "forbidden_actions": list(resolved_task_packet.forbidden_actions),
                    "token_budget": resolved_task_packet.token_budget.model_dump(),
                },
            )
        current_team_state = self.store.load_team_state(run["id"]) or {}
        current_team_state["execution_mode"] = "worker_only"
        tier_assignment = ((preview_payload or {}).get("tier_assignment") if isinstance(preview_payload, dict) else {}) or {}
        if isinstance(tier_assignment, dict):
            current_team_state["execution_lane"] = tier_assignment.get("execution_lane")
            current_team_state["route_family"] = tier_assignment.get("route_family")
            current_team_state["cache_policy"] = tier_assignment.get("cache_policy") or {}
            current_team_state["budget_policy"] = tier_assignment.get("budget_policy") or {}
        if resolved_task_packet is not None:
            current_team_state = self._bind_task_packet_to_team_state(current_team_state, resolved_task_packet)
        self.store.update_run(run["id"], team_state=current_team_state)
        if task["requires_approval"] and self.store.approval_required_and_missing(task_id):
            approval = self.store.create_approval(run["id"], task_id, requested_by="Orchestrator", reason=task["objective"])
            paused = self._pause_for_standard_approval(run_id=run["id"], task=task, approval=approval, preview_payload=preview_payload)
            paused["dispatch_backup"] = backup_info
            return paused
        return await self._execute_run(run["id"], task)

    async def intake_request(
        self,
        project_name: str,
        *,
        task_packet: TaskPacket,
    ) -> dict[str, Any]:
        validated_packet = self._require_routable_task_packet(task_packet)
        self._ensure_task_packet_allows_role(validated_packet, "Orchestrator")
        self._ensure_task_packet_allows_role(validated_packet, "PromptSpecialist")
        self._ensure_task_packet_allows_tool(validated_packet, "model_client.create")
        user_text = validated_packet.normalized_request
        self._enforce_task_packet_forbidden_actions(validated_packet, user_text=user_text)
        packet = await self.prompt_specialist.process_input(user_text)
        title = packet.objective[:80]
        task = self.store.create_task(
            project_name,
            title,
            packet.details,
            objective=packet.objective,
            status="backlog",
            requires_approval=packet.requires_approval,
            owner_role="Orchestrator",
            task_kind="request",
            priority=packet.priority,
            raw_request=user_text,
            acceptance=self._merge_task_packet_acceptance({"task_state": BOARD_STATE_IDEA}, validated_packet),
        )
        self.telemetry.info(
            "task_intake",
            task_id=task["id"],
            project_name=project_name,
            priority=packet.priority,
            requires_approval=packet.requires_approval,
        )
        return {"packet": packet.model_dump(), "task": task, "task_packet": validated_packet.model_dump()}

    async def _intake_request_from_text(
        self,
        project_name: str,
        user_text: str,
        *,
        explicitly_internal: bool = False,
    ) -> dict[str, Any]:
        self._explicit_internal_raw_text_entry(explicitly_internal=explicitly_internal)
        decision = classify_operator_request(user_text)
        if not self._gateway_allows_task_routing(decision):
            return {
                "project_name": project_name,
                "gateway_decision": decision.model_dump(),
                "task": None,
                "packet": None,
                "status": "not_routed",
            }
        task_packet = compile_task_packet(decision, repo_root=self.repo_root, project_name=project_name)
        return await self.intake_request(project_name, task_packet=task_packet)

    def list_tasks(self, project_name: str | None = None, status: str | None = None) -> list[dict[str, Any]]:
        return self.store.list_tasks(project_name, status=status)

    def fetch_next_board_task(self, column_name: str = BOARD_STATE_TODO, *, project_name: str | None = None) -> dict[str, Any] | None:
        return self.board.fetch_next_task(column_name, project_name=project_name)

    def move_task_to_board_state(self, task_id: str, column_name: str) -> dict[str, Any]:
        return self.board.move_task(task_id, column_name)

    def record_review_vote(self, task_id: str, reviewer_role: str, approved: bool) -> dict[str, Any]:
        return self.board.record_review_vote(task_id, reviewer_role, approved)

    def list_approvals(self, status: str | None = None) -> list[dict[str, Any]]:
        return self.store.list_approvals(status)

    def approve(self, approval_id: str, note: str | None = None) -> dict[str, Any]:
        approval = self.store.decide_approval(approval_id, "approve", note)
        self.telemetry.info("approval_decided", approval_id=approval_id, decision="approved", run_id=approval["run_id"])
        return approval

    def reject(self, approval_id: str, note: str | None = None) -> dict[str, Any]:
        approval = self.store.decide_approval(approval_id, "reject", note)
        run_id = approval["run_id"]
        if run_id:
            self.store.update_run(run_id, status="cancelled", stop_reason="approval_rejected", completed=True)
        self.telemetry.info("approval_decided", approval_id=approval_id, decision="rejected", run_id=run_id)
        return approval

    def health_check(self) -> dict[str, Any]:
        required_files = [
            "governance/FRAMEWORK.md",
            "governance/GOVERNANCE_RULES.md",
            "governance/VISION.md",
            "governance/MODEL_REASONING_MATRIX.md",
            "governance/MEMORY_MAP.md",
            "projects/tactics-game/governance/PROJECT_BRIEF.md",
            "memory/framework_health.json",
            "memory/session_summaries.json",
        ]
        required_agents = [
            "agents/prompt_specialist.py",
            "agents/orchestrator.py",
            "agents/pm.py",
            "agents/architect.py",
            "agents/developer.py",
            "agents/design.py",
            "agents/qa.py",
        ]
        issues: list[str] = []
        checked_files: list[str] = []
        checked_agents: list[str] = []

        schema = self.store.schema_health()
        for relative_path in required_files:
            checked_files.append(relative_path)
            if not (self.repo_root / relative_path).exists():
                issues.append(f"Missing required file: {relative_path}")
        for relative_path in required_agents:
            checked_agents.append(relative_path)
            if not (self.repo_root / relative_path).exists():
                issues.append(f"Missing registered agent file: {relative_path}")

        for task in self.store.list_tasks():
            if task["status"] not in {"backlog", "ready", "in_progress", "in_review", "completed", "blocked"}:
                issues.append(f"Invalid task status for {task['id']}: {task['status']}")
            if task["parent_task_id"] and not self.store.get_task(task["parent_task_id"]):
                issues.append(f"Subtask {task['id']} has missing parent {task['parent_task_id']}")
            if task["task_kind"] == "subtask" and task["parent_task_id"]:
                parent = self.store.get_task(task["parent_task_id"])
                if parent and parent["status"] in {"completed", "blocked"} and task["status"] not in {"completed", "blocked"}:
                    issues.append(
                        f"Subtask {task['id']} is {task['status']} while parent {parent['id']} is {parent['status']}"
                    )

        payload = HealthCheckResult(
            ok=schema["ok"] and not issues,
            checked_tables=schema["tables"],
            checked_files=checked_files,
            checked_agents=checked_agents,
            issues=schema["issues"] + issues,
        ).model_dump()
        self.store.write_health_snapshot(payload)
        self.telemetry.append_event("health_check", payload)
        return payload

    async def run_next_task(self, project_name: str) -> dict[str, Any]:
        health = self.health_check()
        if not health["ok"]:
            return {"status": "health_check_failed", "issues": health["issues"]}
        task = self.board.fetch_next_task(BOARD_STATE_TODO, project_name=project_name)
        if task is None:
            candidate = self.store.get_next_runnable_task(project_name)
            if candidate is not None and not ((candidate.get("acceptance") or {}).get("task_state")):
                task = candidate
        if task is None:
            return {"status": "idle", "message": f"No backlog or ready tasks for {project_name}."}
        self._require_task_packet_from_task(task, context="run_next_task")
        acceptance = dict(task.get("acceptance") or {})
        acceptance.setdefault("task_state", BOARD_STATE_IN_PROGRESS)
        self.store.update_task(task["id"], acceptance=acceptance, status="in_progress")
        task = self.store.get_task(task["id"]) or task
        run = self.store.create_run(
            project_name,
            task["id"],
            team_state={"phase": "intake", "runtime_mode": self.runtime_mode, "execution_mode": "worker_only"},
        )
        if task["requires_approval"] and self.store.approval_required_and_missing(task["id"]):
            approval = self.store.create_approval(run["id"], task["id"], requested_by="Orchestrator", reason=task["objective"])
            return self._pause_for_standard_approval(
                run_id=run["id"],
                task=task,
                approval=approval,
                preview_payload=None,
            )
        return await self._execute_run(run["id"], task)

    async def resume_run(self, run_id: str) -> dict[str, Any]:
        run = self.store.get_run(run_id)
        if run is None:
            raise ValueError(f"Run not found: {run_id}")
        if run["status"] != "paused_approval":
            return self._already_progressed_payload(run)
        task = self.store.get_task(run["task_id"])
        if task is None:
            raise ValueError(f"Task not found for run {run_id}")
        self._require_task_packet_from_task(task, context="resume_run")
        approval = self.store.latest_approval_for_task(task["id"])
        if approval is None or approval["status"] != "approved":
            raise ValueError(f"Run {run_id} cannot resume until its approval is approved.")
        team_state = self.store.load_team_state(run_id) or {}
        team_state["phase"] = "resumed"
        self.store.update_run(run_id, status="running", stop_reason=None, team_state=team_state)
        return await self._execute_run(run_id, task)

    def create_git_checkpoint(self, message: str) -> str:
        sha = self.git.create_checkpoint(message)
        self.telemetry.info("git_checkpoint", commit=sha, message=message)
        return sha

    async def _execute_run(self, run_id: str, task: dict, *, local_exception_approval: dict[str, Any] | None = None) -> dict[str, Any]:
        task = dict(task)
        task["authority_delegated_work"] = True
        runtime_mode = self.runtime_mode
        task["runtime_mode"] = runtime_mode
        task_packet = self._require_task_packet_from_task(task, context="_execute_run")
        team_state = self.store.load_team_state(run_id) or {}
        team_state["runtime_mode"] = runtime_mode
        team_state.setdefault("execution_mode", "worker_only")
        team_state["authority_delegated_work"] = True
        self._ensure_task_packet_allows_role(task_packet, "PM")
        team_state = self._bind_task_packet_to_team_state(team_state, task_packet)
        if local_exception_approval is not None:
            team_state["compliance_state"] = {
                **(team_state.get("compliance_state") or {}),
                "mode": BREACH_APPROVED_COMPLIANCE_MODE,
                "approval_id": local_exception_approval["id"],
            }
            team_state["execution_mode"] = "local_exception"
        if runtime_mode == "sdk":
            error = (
                "Governed specialist execution requires the API-backed custom runtime; "
                "SDK specialist execution is excluded until reservation and evidence parity exists."
            )
            team_state["specialist_runtime"] = {
                "mode": "sdk",
                "rejected": True,
                "reason": error,
                "planning_layer": SDK_PLANNING_LAYER,
            }
            team_state["phase"] = "failed"
            self.store.record_trace_event(
                run_id,
                task["id"],
                "sdk_specialist_runtime_rejected",
                source="Orchestrator",
                summary=error,
                packet={
                    "mode": "sdk",
                    "governed_execution": True,
                    "planning_layer": SDK_PLANNING_LAYER,
                    "specialist_roles": ["Architect", "Developer", "Design"],
                },
                route={
                    "runtime_mode": "sdk",
                    "runtime_role": "Orchestrator",
                    "model_role": "orchestrator",
                    "profile_label": "Project Orchestrator",
                },
                raw_json=team_state["specialist_runtime"],
            )
            self.store.update_task(task["id"], status="blocked", owner_role="Orchestrator", review_notes=error)
            self.store.update_run(
                run_id,
                status="failed",
                stop_reason="sdk_runtime_rejected",
                last_error=error,
                team_state=team_state,
                completed=True,
            )
            self.telemetry.error("run_failed", run_id=run_id, task_id=task["id"], error=error)
            raise RuntimeError(error)
        self.store.update_run(run_id, team_state=team_state)
        self.store.record_trace_event(
            run_id,
            task["id"],
            "task_packet_contract_bound",
            source="Orchestrator",
            summary="Execution bound the validated TaskPacket contract before PM routing.",
            packet={
                "request_id": task_packet.request_id,
                "allowed_roles": list(task_packet.allowed_roles),
                "allowed_tools": list(task_packet.allowed_tools),
                "forbidden_actions": list(task_packet.forbidden_actions),
                "token_budget": task_packet.token_budget.model_dump(),
            },
            route={
                "runtime_mode": runtime_mode,
                "runtime_role": "Orchestrator",
                "model_role": "orchestrator",
            },
            raw_json=task_packet.model_dump(),
        )
        self.store.save_context_receipt(
            run_id,
            {
                "active_lane": task["id"],
                "next_reviewer": "PM",
                "resume_conditions": [
                    "Continue with PM sequencing unless scope or receipt changes materially.",
                ],
                "current_owner_role": "PM",
                },
            )
        acceptance = task.get("acceptance") or {}
        classification = acceptance.get("classification") or {}
        tier_assignment = acceptance.get("tier_assignment") or {}
        decomposition = acceptance.get("decomposition") or {}
        if classification or tier_assignment or decomposition:
            self.store.record_trace_event(
                run_id,
                task["id"],
                "tiered_execution_profile_selected",
                source="Orchestrator",
                summary="Task classification, tier assignment, and decomposition were frozen before delegated execution.",
                packet={
                    "classification": classification,
                    "tier_assignment": tier_assignment,
                },
                raw_json={"decomposition": decomposition},
            )
        project_brief = self.load_project_brief(task["project_name"])
        architect = ArchitectAgent(repo_root=self.repo_root, store=self.store, telemetry=self.telemetry, project_brief=project_brief)
        developer = DeveloperAgent(repo_root=self.repo_root, store=self.store, telemetry=self.telemetry, project_brief=project_brief)
        design = DesignAgent(repo_root=self.repo_root, store=self.store, telemetry=self.telemetry, project_brief=project_brief)
        qa = QAAgent(repo_root=self.repo_root, store=self.store, telemetry=self.telemetry, project_brief=project_brief)
        pm = ProjectManagerAgent(
            repo_root=self.repo_root,
            store=self.store,
            telemetry=self.telemetry,
            project_brief=project_brief,
            architect=architect,
            developer=developer,
            design=design,
            qa=qa,
        )
        try:
            result = await pm.execute_request(run_id=run_id, task=task)
            breach = self._extract_breach_payload(result)
            if result.get("paused"):
                approval_obj = result.get("approval")
                if breach is not None:
                    return self._pause_for_breach(run_id=run_id, task=task, breach=breach, preview_payload=result)
                if isinstance(approval_obj, dict):
                    return self._pause_for_standard_approval(run_id=run_id, task=task, approval=approval_obj, preview_payload=result)
                pause_state = self.store.load_team_state(run_id) or {}
                pause_state["phase"] = "awaiting_approval"
                self.store.update_run(run_id, status="paused_approval", stop_reason="awaiting_operator_approval", team_state=pause_state)
                return {
                    "status": "paused_approval",
                    "run_status": "paused_approval",
                    "run_id": run_id,
                    "task_id": task["id"],
                    "preview": result,
                }
            if breach is not None:
                return self._pause_for_breach(run_id=run_id, task=task, breach=breach, preview_payload=result)
            completed = bool(result.get("completed"))
            status = "completed" if completed else "blocked"
            stop_reason = "completed" if completed else "review_or_execution_issue"
            team_state["phase"] = status
            compliance_record: dict[str, Any] | None = None
            if completed and local_exception_approval is not None:
                team_state["compliance_state"] = {
                    **(team_state.get("compliance_state") or {}),
                    "mode": BREACH_APPROVED_COMPLIANCE_MODE,
                    "approval_id": local_exception_approval["id"],
                }
            elif completed:
                team_state.setdefault("compliance_state", {"mode": DELEGATED_COMPLIANCE_MODE})
            self.store.update_run(run_id, status=status, stop_reason=stop_reason, team_state=team_state, completed=completed)
            if completed:
                compliance_record = self._record_compliance_once(
                    run_id=run_id,
                    task=task,
                    record_kind="local_exception_approved" if local_exception_approval is not None else "compliant_delegated_run",
                    details=(
                        "Local exception run completed after the approved operator exception."
                        if local_exception_approval is not None
                        else "Delegated run completed successfully without requiring an exception."
                    ),
                    local_exception_approval_id=local_exception_approval["id"] if local_exception_approval is not None else None,
                    source_role="Orchestrator",
                    evidence={
                        "summary": result.get("summary"),
                        "mode": team_state.get("execution_mode") or "worker_only",
                        "runtime_mode": runtime_mode,
                    },
                )
            self.store.save_context_receipt(
                run_id,
                {
                    "active_lane": task["id"],
                    "next_reviewer": "Operator" if completed else "Architect",
                    "resume_conditions": [
                        "Review the recorded run evidence before opening the next lane."
                        if completed
                        else "Unblock the task or update the receipt before retrying the run.",
                    ],
                    "current_owner_role": "QA" if completed else "Orchestrator",
                },
            )
            summary = {
                "run_id": run_id,
                "task_id": task["id"],
                "task_status": self.store.get_task(task["id"])["status"],
                "run_status": status,
                "result_summary": result.get("summary"),
            }
            if compliance_record is not None:
                summary["compliance_record_id"] = compliance_record["id"]
            self.store.append_session_summary(summary)
            self.telemetry.info("run_finished", **summary)
            return summary
        except Exception as exc:
            self.store.update_task(task["id"], status="blocked", owner_role="Orchestrator", review_notes=str(exc))
            failure_state = self.store.load_team_state(run_id) or dict(team_state)
            failure_state["phase"] = "failed"
            self.store.update_run(run_id, status="failed", last_error=str(exc), team_state=failure_state, completed=True)
            self.telemetry.error("run_failed", run_id=run_id, task_id=task["id"], error=str(exc))
            raise
        finally:
            await pm.close()
            await architect.close()
            await developer.close()
            await design.close()
            await qa.close()


ProgramOrchestrator = Orchestrator


def run_async(coro):
    return asyncio.run(coro)
