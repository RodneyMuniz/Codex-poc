from __future__ import annotations

from pathlib import Path

from agents.role_base import StudioRoleAgent
from agents.schemas import ArtifactResult
from skills.tools import write_project_artifact


class DeveloperAgent(StudioRoleAgent):
    def __init__(self, *, repo_root: str | Path, store, telemetry, project_brief: str) -> None:
        super().__init__(role_name="Developer", model_role="developer", repo_root=repo_root, store=store, telemetry=telemetry)
        self.project_brief = project_brief

    async def produce_artifact(
        self,
        *,
        run_id: str,
        task: dict,
        correction_notes: str | None = None,
    ) -> ArtifactResult:
        class_name = Path(task["expected_artifact_path"]).stem.replace("-", "_").title().replace("_", "")
        system_prompt = f"""
You are the Developer for the tactics-game project.

Project brief:
{self.project_brief}

Return only the final artifact text. For Python tasks, return valid Python source code only.
""".strip()
        user_prompt = f"""
Create the artifact for this task.

Title: {task['title']}
Objective: {task['objective']}
Details: {task['details']}
Expected artifact path: {task['expected_artifact_path']}

Required implementation details:
- define a reusable {class_name} class
- include name, max_hp, current_hp, mana, max_mana, spell_power
- include methods take_damage, heal, cast_spell, is_alive
- validate invalid initialization or invalid spell use

If correction notes are present, fix the artifact accordingly.
Correction notes: {correction_notes or 'None'}
""".strip()
        content = await self.generate_text(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            run_id=run_id,
            task_id=task["id"],
        )
        if task["expected_artifact_path"].endswith(".py"):
            content = self._strip_code_fences(content)
        write_project_artifact(task["expected_artifact_path"], content)
        summary = f"Developer produced {task['expected_artifact_path']}."
        self.store.record_artifact(run_id, task["id"], "developer_output", summary)
        return ArtifactResult(artifact_path=task["expected_artifact_path"], summary=summary)

    def _strip_code_fences(self, content: str) -> str:
        stripped = content.strip()
        if stripped.startswith("```"):
            lines = stripped.splitlines()
            if lines and lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            return "\n".join(lines).strip() + "\n"
        return stripped + ("\n" if not stripped.endswith("\n") else "")
