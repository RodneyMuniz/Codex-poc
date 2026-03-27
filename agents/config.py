from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv
from autogen_ext.models.openai import OpenAIChatCompletionClient


@dataclass(frozen=True)
class RoleModelPolicy:
    role: str
    env_var: str
    default_model: str
    reasoning_depth: str
    cost_tier: str


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

RUNTIME_MODES = {"custom", "sdk"}


def load_environment(repo_root: str | Path | None = None) -> None:
    root = Path(repo_root or Path.cwd())
    load_dotenv(root / ".env")
    load_dotenv(root / ".env.local", override=False)


def require_api_key() -> str:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY not found in environment, .env, or .env.local")
    return api_key


def resolve_model(role: str) -> str:
    policy = MODEL_POLICIES[role]
    return os.getenv(policy.env_var, policy.default_model)


def resolve_runtime_mode() -> str:
    value = os.getenv("AISTUDIO_RUNTIME_MODE", "custom").strip().lower()
    return value if value in RUNTIME_MODES else "custom"


def create_model_client(role: str) -> OpenAIChatCompletionClient:
    return OpenAIChatCompletionClient(
        model=resolve_model(role),
        api_key=require_api_key(),
    )
