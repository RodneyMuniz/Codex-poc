from __future__ import annotations

from pathlib import Path

from hooks import post_task, pre_task
from agents.role_base import StudioRoleAgent
from agents.schemas import ArtifactResult
from skills.tools import write_project_artifact


class ArchitectAgent(StudioRoleAgent):
    def __init__(self, *, repo_root: str | Path, store, telemetry, project_brief: str) -> None:
        super().__init__(role_name="Architect", model_role="architect", repo_root=repo_root, store=store, telemetry=telemetry)
        self.project_brief = project_brief

    @pre_task("In Progress")
    @post_task("In Progress")
    async def produce_artifact(
        self,
        *,
        run_id: str,
        task: dict,
        correction_notes: str | None = None,
        agent_run_id: str | None = None,
    ) -> ArtifactResult:
        subject_name = Path(task["expected_artifact_path"]).stem.replace("-", " ").replace("_", " ").title()
        system_prompt = f"""
You are the Architect for the tactics-game project.

Project brief:
{self.project_brief}

Write concise, implementation-ready markdown. Follow the requested headings exactly when they are provided.
Return markdown only.
""".strip()
        user_prompt = f"""
Create the artifact for this task.

Title: {task['title']}
Objective: {task['objective']}
Details: {task['details']}
Expected artifact path: {task['expected_artifact_path']}

Required headings:
- Overview
- Attributes
- Abilities
- Acceptance Criteria

Name the unit or feature clearly as {subject_name}.

If correction notes are present, fix the artifact accordingly.
Correction notes: {correction_notes or 'None'}
""".strip()
        content = await self.generate_text(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            run_id=run_id,
            task_id=task["id"],
        )
        write_project_artifact(task["expected_artifact_path"], content)
        summary = f"Architect produced {task['expected_artifact_path']}."
        self.store.record_artifact(
            run_id,
            task["id"],
            "architect_output",
            summary,
            artifact_path=task["expected_artifact_path"],
            produced_by="Architect",
            source_agent_run_id=agent_run_id,
        )
        return ArtifactResult(artifact_path=task["expected_artifact_path"], summary=summary)
