from __future__ import annotations

from autogen_agentchat.agents import AssistantAgent

from skills import build_skill_tools


def build_architect_agent(model_client, project_brief: str) -> AssistantAgent:
    system_message = f"""
You are the Architect for the tactics-game project.

Project brief:
{project_brief}

Rules:
- Respond to ProjectPO with architecture guidance, risks, and acceptance criteria.
- Use tools when repository inspection helps.
- When the task explicitly asks for a markdown artifact, write it under `projects/tactics-game/artifacts/`.
- Do not request operator approval.
- Do not mark the task complete.
- Keep output concise and decision-oriented.
""".strip()
    return AssistantAgent(
        name="Architect",
        model_client=model_client,
        tools=build_skill_tools(),
        description="Analyzes architecture, risks, and delivery tradeoffs for the project.",
        system_message=system_message,
        reflect_on_tool_use=True,
        max_tool_iterations=2,
    )
