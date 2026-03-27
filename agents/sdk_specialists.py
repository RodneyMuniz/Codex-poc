from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

from agents.config import resolve_model, resolve_reasoning_depth
from agents.sdk_runtime import SDKRuntimeAdapter, SDKSpecialistArtifact
from agents.schemas import ArtifactResult
from skills.tools import write_project_artifact


class SDKSpecialistCoordinator:
    def __init__(self, *, repo_root: str | Path, store, telemetry) -> None:
        self.repo_root = Path(repo_root).resolve()
        self.store = store
        self.telemetry = telemetry
        self.adapter = SDKRuntimeAdapter(self.repo_root)

    def health(self):
        return self.adapter.health()

    def build_session_id(self, run_id: str, role: str) -> str:
        return f"studio-specialist-{role.lower()}-{run_id}"

    async def produce_artifact(
        self,
        *,
        run_id: str,
        task: dict[str, Any],
        role: str,
        project_brief: str,
        correction_notes: str | None = None,
        input_artifact_path: str | None = None,
        agent_run_id: str | None = None,
    ) -> tuple[ArtifactResult, SDKSpecialistArtifact]:
        payload = {
            "session_id": self.build_session_id(run_id, role),
            "role": role,
            "project_name": task["project_name"],
            "title": task["title"],
            "objective": task.get("objective") or task["title"],
            "details": task.get("details") or task.get("description") or task["title"],
            "priority": task.get("priority") or "medium",
            "expected_artifact_path": task["expected_artifact_path"],
            "project_brief": project_brief,
            "correction_notes": correction_notes,
            "input_artifact_path": input_artifact_path,
            "input_artifact_content": self._input_artifact_content(input_artifact_path),
            "model": resolve_model(role.lower()),
            "reasoning_depth": resolve_reasoning_depth(role.lower()),
        }
        specialist_result = await asyncio.to_thread(self.adapter.run_specialist, payload)
        artifact_text = specialist_result.artifact_text
        if task["expected_artifact_path"].endswith(".py"):
            artifact_text = self._strip_code_fences(artifact_text)
        write_project_artifact(task["expected_artifact_path"], artifact_text)

        artifact_summary = specialist_result.summary or f"{role} produced {task['expected_artifact_path']}."
        kind = {
            "Architect": "architect_output",
            "Developer": "developer_output",
            "Design": "design_output",
        }[role]
        self.store.record_artifact(
            run_id,
            task["id"],
            kind,
            artifact_summary,
            artifact_path=task["expected_artifact_path"],
            produced_by=role,
            source_agent_run_id=agent_run_id,
            input_artifact_paths=[input_artifact_path] if input_artifact_path else [],
        )
        self.telemetry.append_event(
            "sdk_specialist_invocation",
            {
                "run_id": run_id,
                "task_id": task["id"],
                "role": role,
                "payload": {
                    "session_id": specialist_result.session_id,
                    "model": specialist_result.model,
                    "response_id": specialist_result.response_id,
                    "trace_id": specialist_result.trace_id,
                    "summary": artifact_summary,
                },
            },
        )
        return ArtifactResult(artifact_path=task["expected_artifact_path"], summary=artifact_summary), specialist_result

    def _input_artifact_content(self, relative_path: str | None) -> str | None:
        if not relative_path:
            return None
        file_path = self.repo_root / relative_path
        if not file_path.exists():
            return None
        return file_path.read_text(encoding="utf-8")

    def _strip_code_fences(self, content: str) -> str:
        stripped = content.strip()
        if stripped.startswith("```"):
            lines = stripped.splitlines()
            if lines and lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            return "\n".join(lines).strip() + "\n"
        return stripped + ("\n" if stripped and not stripped.endswith("\n") else "")
