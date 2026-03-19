import json
import os
from dotenv import load_dotenv
from openai import OpenAI

from skills.file_utils import read_text, append_under_heading, ensure_file


class ProgramOrchestrator:
    def __init__(self) -> None:
        load_dotenv()
        load_dotenv(".env.local", override=False)

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in .env")

        self.client = OpenAI(api_key=api_key)

        self.framework_path = "governance/FRAMEWORK.md"
        self.project_path = "projects/tactics-game/governance/PROJECT_BRIEF.md"
        self.kanban_path = "projects/tactics-game/execution/KANBAN.md"

        ensure_file(
            self.framework_path,
            "# Framework\n\n## Purpose\nThis repository is a lean AI Studio POC.\n"
        )

        ensure_file(
            self.project_path,
            "# Tactics Game Project Brief\n\n## Purpose\nPrototype a tactics game project using a structured multi-agent workflow.\n"
        )

        ensure_file(
            self.kanban_path,
            "# Tactics Game Kanban\n\n## Backlog\n\n## In Progress\n\n## Done\n"
        )

    def load_context(self) -> dict:
        framework = read_text(self.framework_path)
        project = read_text(self.project_path)

        return {
            "framework": framework,
            "project": project
        }

    def classify_request(self, user_input: str) -> dict:
        context = self.load_context()

        system_prompt = """
You are a Program Orchestrator for a lean multi-agent POC.

Your task is to classify a user request into one of two categories:
- governance
- project_work

Return JSON only with this structure:
{
  "classification": "governance" or "project_work",
  "project": "tactics-game" or "none",
  "title": "short actionable title",
  "description": "clear one-paragraph description"
}

Rules:
- Use "governance" when the request changes framework, rules, governance, or operating model.
- Use "project_work" when the request is an actual project feature, task, or execution item.
- If the request clearly targets the tactics game project, set project to "tactics-game".
- If governance, set project to "none".
- Output valid JSON only.
"""

        user_prompt = f"""
Framework context:
{context["framework"]}

Project context:
{context["project"]}

User request:
{user_input}
"""

        response = self.client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
        )

        content = response.choices[0].message.content
        return json.loads(content)

    def create_ticket(self, classification_result: dict) -> dict:
        return {
            "project": classification_result["project"],
            "title": classification_result["title"],
            "description": classification_result["description"],
            "status": "Backlog",
            "owner": "Project PO"
        }

    def format_ticket_markdown(self, ticket: dict) -> str:
        return (
            f"### {ticket['title']}\n"
            f"- Project: {ticket['project']}\n"
            f"- Status: {ticket['status']}\n"
            f"- Owner: {ticket['owner']}\n"
            f"- Description: {ticket['description']}"
        )

    def update_kanban(self, ticket: dict) -> bool:
        block = self.format_ticket_markdown(ticket)
        return append_under_heading(self.kanban_path, "## Backlog", block)

    def plan(self, user_input: str) -> str:
        classification_result = self.classify_request(user_input)

        if classification_result["classification"] == "governance":
            return (
                "Request classified as governance.\n"
                f"Title: {classification_result['title']}\n"
                f"Description: {classification_result['description']}\n"
                "No project kanban update was made."
            )

        ticket = self.create_ticket(classification_result)
        success = self.update_kanban(ticket)

        if not success:
            return (
                "Request classified as project work, but failed to update the kanban.\n"
                f"Ticket: {ticket}"
            )

        return (
            "Request classified as project work.\n"
            f"Ticket created in kanban backlog:\n"
            f"- Title: {ticket['title']}\n"
            f"- Project: {ticket['project']}\n"
            f"- Owner: {ticket['owner']}\n"
            f"- Status: {ticket['status']}"
        )
