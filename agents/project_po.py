from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Literal, Sequence

from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.conditions import MaxMessageTermination, TextMentionTermination
from autogen_agentchat.messages import BaseChatMessage
from autogen_agentchat.teams import SelectorGroupChat

from agents.architect import build_architect_agent
from agents.config import create_model_client
from agents.developer import build_developer_agent
from sessions import SessionStore


PROJECT_PO_NAME = "ProjectPO"


def _message_text(message: BaseChatMessage) -> str:
    content = getattr(message, "content", "")
    if isinstance(content, str):
        return content.strip()
    return json.dumps(content, ensure_ascii=True, default=str)


def project_team_candidate_func(messages: Sequence[Any]) -> list[str]:
    chat_messages = [message for message in messages if isinstance(message, BaseChatMessage)]
    if not chat_messages:
        return [PROJECT_PO_NAME]
    last_message = chat_messages[-1]
    source = getattr(last_message, "source", "")
    text = _message_text(last_message)
    if source == PROJECT_PO_NAME:
        if text.startswith("Architect:"):
            return ["Architect"]
        if text.startswith("Developer:"):
            return ["Developer"]
        return [PROJECT_PO_NAME]
    if source in {"Architect", "Developer"}:
        return [PROJECT_PO_NAME]
    return [PROJECT_PO_NAME]


@dataclass
class ProjectPOCoordinatorTools:
    store: SessionStore
    run_id: str
    task_id: str
    project_name: str

    def view_project_queue(self) -> dict[str, Any]:
        """Return the current task queue for the active project."""
        tasks = self.store.list_tasks(self.project_name)
        return {"project": self.project_name, "tasks": tasks}

    def _delegated_roles(self) -> set[str]:
        return {edge["to_role"] for edge in self.store.list_delegations(self.run_id)}

    def start_current_task(self, note: str = "") -> dict[str, Any]:
        """Mark the active task as in progress under ProjectPO ownership."""
        task = self.store.update_task(self.task_id, status="in_progress", owner_role=PROJECT_PO_NAME)
        if note:
            self.store.record_artifact(self.run_id, self.task_id, "start_note", note)
        return {"status": task["status"], "owner": task["owner_role"], "task_id": self.task_id}

    def delegate_current_task(self, assignee: Literal["Architect", "Developer"], reason: str) -> dict[str, Any]:
        """Record a delegation from ProjectPO to Architect or Developer."""
        edge = self.store.record_delegation(
            self.run_id,
            self.task_id,
            from_role=PROJECT_PO_NAME,
            to_role=assignee,
            note=reason,
        )
        return {
            "delegation_id": edge["id"],
            "assignee": assignee,
            "instruction": f"Address the next message to {assignee} by starting with '{assignee}:'",
        }

    def record_project_note(self, kind: Literal["architecture", "implementation", "summary"], content: str) -> dict[str, Any]:
        """Store a structured project note for the current run."""
        self.store.record_artifact(self.run_id, self.task_id, kind, content)
        return {"recorded": True, "kind": kind}

    def request_operator_approval(self, reason: str) -> dict[str, Any]:
        """Pause the task until the operator explicitly approves or rejects it."""
        missing_roles = {"Architect", "Developer"} - self._delegated_roles()
        if missing_roles:
            return {
                "status": "blocked",
                "missing_roles": sorted(missing_roles),
                "instruction": "Consult both Architect and Developer before requesting approval.",
            }
        latest = self.store.latest_approval_for_task(self.task_id)
        if latest and latest["status"] == "pending":
            return {
                "approval_id": latest["id"],
                "status": latest["status"],
                "instruction": "Reply with AWAITING_APPROVAL.",
            }
        approval = self.store.create_approval(self.run_id, self.task_id, requested_by=PROJECT_PO_NAME, reason=reason)
        return {
            "approval_id": approval["id"],
            "status": approval["status"],
            "instruction": "Reply with AWAITING_APPROVAL.",
        }

    def complete_current_task(self, summary: str) -> dict[str, Any]:
        """Complete the task if any required approval has already been granted."""
        missing_roles = {"Architect", "Developer"} - self._delegated_roles()
        if missing_roles:
            return {
                "completed": False,
                "status": "blocked",
                "missing_roles": sorted(missing_roles),
                "instruction": "Consult both Architect and Developer before completion.",
            }
        if self.store.approval_required_and_missing(self.task_id):
            return {
                "completed": False,
                "status": "blocked",
                "instruction": "Approval is still required. Request operator approval before completion.",
            }
        self.store.record_artifact(self.run_id, self.task_id, "outcome", summary)
        task = self.store.update_task(
            self.task_id,
            status="completed",
            owner_role=PROJECT_PO_NAME,
            result_summary=summary,
        )
        return {
            "completed": True,
            "status": task["status"],
            "instruction": "Reply with TASK_COMPLETE.",
        }


def build_project_po_agent(
    model_client,
    store: SessionStore,
    run_id: str,
    task_record: dict[str, Any],
    governance_context: str,
    project_brief: str,
) -> AssistantAgent:
    tools = ProjectPOCoordinatorTools(
        store=store,
        run_id=run_id,
        task_id=task_record["id"],
        project_name=task_record["project_name"],
    )
    system_message = f"""
You are ProjectPO, the owner of the tactics-game task queue.

Governance context:
{governance_context}

Project brief:
{project_brief}

Active task:
- ID: {task_record['id']}
- Title: {task_record['title']}
- Description: {task_record['description']}
- Requires approval: {'yes' if task_record['requires_approval'] else 'no'}

Operating protocol:
1. Start by calling `start_current_task`.
2. You control delegation. When you need specialist input, call `delegate_current_task` first.
3. After delegating, send a normal chat message beginning exactly with `Architect:` or `Developer:` so the selected specialist receives the request.
4. You must consult Architect and Developer at least once each before requesting approval or completion.
5. After a specialist responds, decide whether to delegate again, record a note, request approval, or complete the task.
6. If approval is required and has not been granted, call `request_operator_approval` and then reply exactly `AWAITING_APPROVAL`.
7. When the task is complete, call `complete_current_task` and then reply exactly `TASK_COMPLETE`.
8. Keep every message short, operational, and specific.
""".strip()
    return AssistantAgent(
        name=PROJECT_PO_NAME,
        model_client=model_client,
        tools=[
            tools.view_project_queue,
            tools.start_current_task,
            tools.delegate_current_task,
            tools.record_project_note,
            tools.request_operator_approval,
            tools.complete_current_task,
        ],
        description="Owns the kanban queue, delegates work, enforces approvals, and closes tasks.",
        system_message=system_message,
        reflect_on_tool_use=True,
        max_tool_iterations=3,
    )


def build_project_team(
    store: SessionStore,
    run_id: str,
    task_record: dict[str, Any],
    governance_context: str,
    project_brief: str,
):
    model_clients = {
        "selector": create_model_client("selector"),
        "project_po": create_model_client("project_po"),
        "architect": create_model_client("architect"),
        "developer": create_model_client("developer"),
    }
    project_po = build_project_po_agent(
        model_clients["project_po"],
        store=store,
        run_id=run_id,
        task_record=task_record,
        governance_context=governance_context,
        project_brief=project_brief,
    )
    architect = build_architect_agent(model_clients["architect"], project_brief)
    developer = build_developer_agent(model_clients["developer"], project_brief)
    termination = (
        TextMentionTermination("TASK_COMPLETE", sources=[PROJECT_PO_NAME])
        | TextMentionTermination("AWAITING_APPROVAL", sources=[PROJECT_PO_NAME])
        | MaxMessageTermination(12)
    )
    team = SelectorGroupChat(
        participants=[project_po, architect, developer],
        model_client=model_clients["selector"],
        name="TacticsGameTeam",
        description="Project PO team for tactics-game delivery.",
        termination_condition=termination,
        max_turns=12,
        candidate_func=project_team_candidate_func,
        emit_team_events=True,
    )
    return team, model_clients
