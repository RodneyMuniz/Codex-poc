from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from pydantic import BaseModel, Field


class SpecialistPayload(BaseModel):
    session_id: str
    role: str
    project_name: str
    title: str
    objective: str
    details: str
    priority: str = "medium"
    expected_artifact_path: str
    project_brief: str
    correction_notes: str | None = None
    input_artifact_path: str | None = None
    input_artifact_content: str | None = None
    model: str
    reasoning_depth: str = "low"


class SpecialistOutput(BaseModel):
    summary: str
    artifact_text: str
    notes: list[str] = Field(default_factory=list)


def _load_environment() -> Path:
    repo_root = Path(os.environ["AISTUDIO_REPO_ROOT"]).resolve()
    load_dotenv(repo_root / ".env")
    load_dotenv(repo_root / ".env.local", override=False)
    return repo_root


def _specialist_instructions(payload: SpecialistPayload) -> str:
    if payload.role == "Architect":
        return (
            "You are the Architect specialist for AI Studio. "
            "You receive a bounded implementation request from the Orchestrator and return only strict JSON. "
            "Write concise, implementation-ready markdown. Follow requested headings exactly. "
            "Do not invent extra scope."
        )
    if payload.role == "Developer":
        return (
            "You are the Developer specialist for AI Studio. "
            "You receive a bounded implementation request from the Orchestrator and return only strict JSON. "
            "Transform approved intent and upstream design context into working implementation text. "
            "For Python targets, artifact_text must be valid Python source code only."
        )
    if payload.role == "Design":
        return (
            "You are the Design specialist for AI Studio. "
            "You receive a bounded implementation request from the Orchestrator and return only strict JSON. "
            "Produce concise markdown describing UI and visual direction. "
            "Do not invent extra product scope."
        )
    raise ValueError(f"Unsupported specialist role: {payload.role}")


def _specialist_prompt(payload: SpecialistPayload) -> str:
    base = [
        f"Project: {payload.project_name}",
        f"Role: {payload.role}",
        f"Priority: {payload.priority}",
        f"Title: {payload.title}",
        f"Objective: {payload.objective}",
        f"Details: {payload.details}",
        f"Expected artifact path: {payload.expected_artifact_path}",
        f"Correction notes: {payload.correction_notes or 'None'}",
        "Project brief:",
        payload.project_brief,
    ]
    if payload.role == "Architect":
        base.extend(
            [
                "Required headings:",
                "- Overview",
                "- Attributes",
                "- Abilities",
                "- Acceptance Criteria",
            ]
        )
    elif payload.role == "Developer":
        base.extend(
            [
                "Required implementation details:",
                "- include a reusable class matching the requested subject",
                "- include the methods take_damage, heal, cast_spell, is_alive",
                "- validate invalid initialization or invalid spell use",
                f"Upstream design artifact path: {payload.input_artifact_path or 'None'}",
                "Upstream design artifact content:",
                payload.input_artifact_content or "None",
            ]
        )
    elif payload.role == "Design":
        base.extend(
            [
                "Required headings:",
                "- UI Concepts",
                "- Visual Direction",
                "- Player Feedback",
            ]
        )
    base.append("Return JSON with a concise summary and the final artifact_text only.")
    return "\n".join(base)


async def _run_specialist_artifact(payload_json: str) -> dict[str, object]:
    repo_root = _load_environment()

    from agents import Agent, ModelSettings, Runner, SQLiteSession, __version__

    payload = SpecialistPayload.model_validate_json(payload_json)
    session_db = Path(os.environ.get("AISTUDIO_SDK_SESSIONS_DB", repo_root / "sessions" / "sdk_sessions.db"))
    session = SQLiteSession(session_id=payload.session_id, db_path=session_db)
    instructions = _specialist_instructions(payload)
    prompt = _specialist_prompt(payload)
    agent = Agent(
        name=f"{payload.role}Specialist",
        instructions=instructions,
        model=payload.model,
        model_settings=ModelSettings(temperature=0, tool_choice="none", parallel_tool_calls=False),
        output_type=SpecialistOutput,
    )
    result = await Runner.run(agent, prompt, session=session, max_turns=1)
    output = result.final_output_as(SpecialistOutput, raise_if_incorrect_type=True)
    trace = getattr(result, "trace", None)
    return {
        "runtime": "sdk",
        "role": payload.role,
        "package": "openai-agents",
        "version": __version__,
        "session_id": payload.session_id,
        "model": payload.model,
        "response_id": result.last_response_id,
        "trace_id": getattr(trace, "trace_id", None) if trace else None,
        **output.model_dump(),
    }


def _health() -> dict[str, object]:
    _load_environment()
    from agents import __version__

    return {
        "ok": True,
        "package": "openai-agents",
        "version": __version__,
        "python": sys.version.split()[0],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Isolated bridge into the official OpenAI Agents SDK.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    health = subparsers.add_parser("health")
    health.set_defaults(func=lambda args: _health())

    specialist = subparsers.add_parser("specialist-artifact")
    specialist.add_argument("--payload-json", required=True)
    specialist.set_defaults(func=lambda args: asyncio.run(_run_specialist_artifact(args.payload_json)))

    args = parser.parse_args()
    payload = args.func(args)
    print(json.dumps(payload, ensure_ascii=True))


if __name__ == "__main__":
    main()
