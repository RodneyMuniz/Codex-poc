from __future__ import annotations

from autogen_agentchat.agents import AssistantAgent

from skills import build_skill_tools


def build_developer_agent(model_client, project_brief: str) -> AssistantAgent:
    system_message = f"""
You are the Developer for the tactics-game project.

Project brief:
{project_brief}

Rules:
- Respond to ProjectPO with implementation-oriented advice, validation steps, and practical file-level suggestions.
- Use tools when repository inspection or validation helps.
- Do not request operator approval.
- Do not mark the task complete.
- Keep the response concrete and short.
""".strip()
    return AssistantAgent(
        name="Developer",
        model_client=model_client,
        tools=build_skill_tools(),
        description="Focuses on implementation planning, code-level changes, and validation steps.",
        system_message=system_message,
        reflect_on_tool_use=True,
        max_tool_iterations=2,
    )
