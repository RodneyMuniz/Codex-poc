from __future__ import annotations

import os
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from typing import Any
import re

from dotenv import load_dotenv
from autogen_ext.models.openai import OpenAIChatCompletionClient


@dataclass(frozen=True)
class RoleModelPolicy:
    role: str
    env_var: str
    default_model: str
    reasoning_depth: str
    cost_tier: str


@dataclass(frozen=True)
class TierPolicy:
    tier: str
    env_var: str
    default_model: str
    reasoning_effort: str
    channel: str
    cost_tier: str


@dataclass(frozen=True)
class ModelPricing:
    model: str
    input_per_million: float
    cached_input_per_million: float
    output_per_million: float


MODEL_POLICIES: dict[str, RoleModelPolicy] = {
    "selector": RoleModelPolicy("selector", "AISTUDIO_MODEL_SELECTOR", "gpt-4.1-mini", "low", "low"),
    "orchestrator": RoleModelPolicy("orchestrator", "AISTUDIO_MODEL_ORCHESTRATOR", "gpt-4.1-mini", "low", "low"),
    "prompt_specialist": RoleModelPolicy("prompt_specialist", "AISTUDIO_MODEL_PROMPT_SPECIALIST", "gpt-4.1-mini", "low", "low"),
    "pm": RoleModelPolicy("pm", "AISTUDIO_MODEL_PM", "gpt-4.1-mini", "medium", "low"),
    "architect": RoleModelPolicy("architect", "AISTUDIO_MODEL_ARCHITECT", "gpt-4.1-mini", "high", "medium"),
    "developer": RoleModelPolicy("developer", "AISTUDIO_MODEL_DEVELOPER", "gpt-4.1-mini", "medium", "low"),
    "design": RoleModelPolicy("design", "AISTUDIO_MODEL_DESIGN", "gpt-4.1-mini", "medium", "low"),
    "qa": RoleModelPolicy("qa", "AISTUDIO_MODEL_QA", "gpt-4.1-mini", "low", "low"),
}

TIER_POLICIES: dict[str, TierPolicy] = {
    "tier_1_senior": TierPolicy(
        "tier_1_senior",
        "AISTUDIO_MODEL_TIER_1",
        "gpt-5.4",
        "high",
        "api",
        "high",
    ),
    "tier_2_mid": TierPolicy(
        "tier_2_mid",
        "AISTUDIO_MODEL_TIER_2",
        "gpt-5.4-mini",
        "medium",
        "api",
        "medium",
    ),
    "tier_3_junior": TierPolicy(
        "tier_3_junior",
        "AISTUDIO_MODEL_TIER_3",
        "gpt-5.4-mini",
        "low",
        "api",
        "low",
    ),
}

ROLE_FLOOR_TIERS: dict[str, str] = {
    "selector": "tier_3_junior",
    "orchestrator": "tier_1_senior",
    "prompt_specialist": "tier_2_mid",
    "pm": "tier_2_mid",
    "architect": "tier_1_senior",
    "developer": "tier_2_mid",
    "design": "tier_2_mid",
    "qa": "tier_3_junior",
}

MODEL_PRICING: dict[str, ModelPricing] = {
    "gpt-5.4": ModelPricing("gpt-5.4", input_per_million=2.0, cached_input_per_million=0.5, output_per_million=8.0),
    "gpt-5.4-mini": ModelPricing(
        "gpt-5.4-mini",
        input_per_million=0.675,
        cached_input_per_million=0.3375,
        output_per_million=3.075,
    ),
    "gpt-4.1-mini": ModelPricing(
        "gpt-4.1-mini",
        input_per_million=0.4,
        cached_input_per_million=0.1,
        output_per_million=1.6,
    ),
}

DELIVERABLE_SPECS: dict[str, dict[str, Any]] = {
    "tactics-game": {
        "default_deliverables": ("architecture_note", "python_module", "ui_notes"),
        "deliverables": {
            "architecture_note": {
                "assigned_role": "Architect",
                "title_template": "{subject_label} Architecture Note",
                "objective_template": "Define the implementation contract for {subject_label}.",
                "details_template": "Produce an implementation-ready architecture note for {subject_label}.",
                "artifact_template": "projects/{project_name}/artifacts/{subject_slug}_architecture.md",
                "required_headings": ("Overview", "Attributes", "Abilities", "Acceptance Criteria"),
                "required_keywords": ("{subject_label}",),
                "required_strings": (),
                "python_compile": False,
                "required_input_role": None,
                "allowed_tools": ("read_project_brief", "write_project_artifact"),
                "requires_dispatch_approval": False,
                "category": "Architecture",
                "deliverable_contract": {
                    "kind": "review",
                    "summary": "Review-oriented architecture note that defines bounded implementation intent.",
                    "required_input_role": None,
                    "evidence_surface": "run-details.artifacts and run-details.trace_events",
                },
            },
            "python_module": {
                "assigned_role": "Developer",
                "title_template": "{subject_label} Python Module",
                "objective_template": "Implement the {subject_label} module from the approved architecture note.",
                "details_template": "Write the production-ready Python implementation for {subject_label}.",
                "artifact_template": "projects/{project_name}/artifacts/{subject_slug}.py",
                "required_headings": (),
                "required_keywords": (),
                "required_strings": ("class {class_name}",),
                "python_compile": True,
                "required_input_role": "Architect",
                "allowed_tools": ("read_project_brief", "write_project_artifact"),
                "requires_dispatch_approval": True,
                "category": "Implementation",
                "deliverable_contract": {
                    "kind": "code",
                    "summary": "Production implementation artifact generated from an approved architecture note.",
                    "required_input_role": "Architect",
                    "evidence_surface": "run-details.artifacts, validation_results, and usage_events",
                },
            },
            "ui_notes": {
                "assigned_role": "Design",
                "title_template": "{subject_label} UI Notes",
                "objective_template": "Document UI and feedback guidance for {subject_label}.",
                "details_template": "Produce concise UI and player-feedback notes for {subject_label}.",
                "artifact_template": "projects/{project_name}/artifacts/{subject_slug}_ui.md",
                "required_headings": ("UI Concepts", "Visual Direction", "Player Feedback"),
                "required_keywords": ("{subject_label}",),
                "required_strings": (),
                "python_compile": False,
                "required_input_role": None,
                "allowed_tools": ("read_project_brief", "write_project_artifact"),
                "requires_dispatch_approval": False,
                "category": "Design",
                "deliverable_contract": {
                    "kind": "review",
                    "summary": "Review-oriented design notes for the player-facing presentation layer.",
                    "required_input_role": None,
                    "evidence_surface": "run-details.artifacts and run-details.trace_events",
                },
            },
        },
    },
    "program-kanban": {
        "default_deliverables": ("architecture_note",),
        "deliverables": {
            "architecture_note": {
                "assigned_role": "Architect",
                "title_template": "{subject_label} Architecture Note",
                "objective_template": "Define the architecture contract for {subject_label}.",
                "details_template": "Write a bounded architecture note covering {subject_label}.",
                "artifact_template": "projects/{project_name}/artifacts/{subject_slug}_architecture.md",
                "required_headings": ("Overview", "Current Surface", "Implementation Notes", "Acceptance Criteria"),
                "required_keywords": ("{subject_label}",),
                "required_strings": (),
                "python_compile": False,
                "required_input_role": None,
                "allowed_tools": ("read_project_brief", "write_project_artifact"),
                "requires_dispatch_approval": False,
                "category": "Architecture",
                "deliverable_contract": {
                    "kind": "review",
                    "summary": "Review-oriented architecture note for bounded framework changes.",
                    "required_input_role": None,
                    "evidence_surface": "run-details.artifacts and run-details.trace_events",
                },
            },
        },
    },
}

RUNTIME_MODES = {"custom", "sdk"}
TIER_ORDER = ("tier_1_senior", "tier_2_mid", "tier_3_junior")


def load_environment(repo_root: str | Path | None = None) -> None:
    root = Path(repo_root or Path.cwd())
    load_dotenv(root / ".env")
    load_dotenv(root / ".env.local", override=False)


def require_api_key() -> str:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY not found in environment, .env, or .env.local")
    return api_key


def _normalize_role(role: str) -> str:
    collapsed = re.sub(r"(?<!^)(?=[A-Z])", "_", role.strip()).replace(" ", "_")
    normalized = collapsed.lower()
    if normalized not in MODEL_POLICIES:
        raise KeyError(f"Unknown role policy: {role}")
    return normalized


def _normalize_tier(tier: str) -> str:
    normalized = tier.strip().lower()
    if normalized not in TIER_POLICIES:
        raise KeyError(f"Unknown execution tier: {tier}")
    return normalized


def resolve_model(role: str) -> str:
    policy = MODEL_POLICIES[_normalize_role(role)]
    return os.getenv(policy.env_var, policy.default_model)


def resolve_runtime_mode() -> str:
    value = os.getenv("AISTUDIO_RUNTIME_MODE", "custom").strip().lower()
    return value if value in RUNTIME_MODES else "custom"


def get_tier_policy(tier: str) -> TierPolicy:
    normalized = _normalize_tier(tier)
    base = TIER_POLICIES[normalized]
    model = os.getenv(base.env_var, base.default_model)
    channel = os.getenv(f"{base.env_var}_CHANNEL", base.channel).strip().lower() or base.channel
    reasoning_effort = os.getenv(
        f"{base.env_var}_REASONING_EFFORT",
        base.reasoning_effort,
    ).strip().lower() or base.reasoning_effort
    return TierPolicy(
        tier=base.tier,
        env_var=base.env_var,
        default_model=model,
        reasoning_effort=reasoning_effort,
        channel=channel,
        cost_tier=base.cost_tier,
    )


def resolve_tier_model(tier: str) -> str:
    return get_tier_policy(tier).default_model


def resolve_tier_reasoning_effort(tier: str) -> str:
    return get_tier_policy(tier).reasoning_effort


def resolve_tier_channel(tier: str) -> str:
    return get_tier_policy(tier).channel


def role_floor_tier(role: str) -> str:
    normalized = re.sub(r"(?<!^)(?=[A-Z])", "_", role.strip()).replace(" ", "_").lower()
    return ROLE_FLOOR_TIERS.get(normalized, "tier_3_junior")


def model_pricing(model: str) -> ModelPricing | None:
    return MODEL_PRICING.get(model.strip())


def get_capability_registry(project_name: str) -> dict[str, Any]:
    registry = DELIVERABLE_SPECS.get(project_name)
    if registry is None:
        registry = DELIVERABLE_SPECS["tactics-game"]
    return deepcopy(registry)


def get_deliverable_spec(project_name: str, deliverable_type: str) -> dict[str, Any]:
    registry = get_capability_registry(project_name)
    deliverable = registry["deliverables"].get(deliverable_type)
    if deliverable is None:
        raise KeyError(f"Unknown deliverable type for {project_name}: {deliverable_type}")
    return deepcopy(deliverable)


def infer_output_format(artifact_path: str) -> str:
    suffix = Path(artifact_path).suffix.lower()
    if suffix == ".py":
        return "python"
    if suffix == ".json":
        return "json"
    if suffix in {".md", ".markdown"}:
        return "markdown"
    if suffix in {".txt", ".rst"}:
        return "text"
    return "text"


def resolve_subtask_tier(*, assignee: str, requested_tier: str | None = None) -> str:
    default_tier = {
        "Architect": "tier_2_mid",
        "Developer": "tier_3_junior",
        "Design": "tier_2_mid",
        "QA": "tier_3_junior",
    }.get(assignee, "tier_3_junior")
    if not requested_tier:
        return default_tier
    normalized_requested = _normalize_tier(requested_tier)
    requested_rank = TIER_ORDER.index(normalized_requested)
    default_rank = TIER_ORDER.index(default_tier)
    return TIER_ORDER[min(requested_rank, default_rank)]


def create_model_client(role: str) -> OpenAIChatCompletionClient:
    return OpenAIChatCompletionClient(
        model=resolve_model(role),
        api_key=require_api_key(),
    )
