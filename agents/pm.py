from __future__ import annotations

import asyncio
import os
import json
import re
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from agents.architect import ArchitectAgent
from agents.developer import DeveloperAgent
from agents.design import DesignAgent
from agents.qa import QAAgent
from agents.role_base import StudioRoleAgent
from agents.schemas import AcceptanceCriteria, ArtifactResult, PlanSummary, QAReviewResult, SubtaskPlan
from skills.tools import WORKER_WRITE_MANIFEST_ENV, compute_worker_manifest_seal

WORKER_MANIFEST_ENV = WORKER_WRITE_MANIFEST_ENV


class ProjectManagerAgent(StudioRoleAgent):
    def __init__(
        self,
        *,
        repo_root: str | Path,
        store,
        telemetry,
        project_brief: str,
        architect: ArchitectAgent | None = None,
        developer: DeveloperAgent | None = None,
        design: DesignAgent | None = None,
        qa: QAAgent | None = None,
    ) -> None:
        super().__init__(role_name="PM", model_role="pm", repo_root=repo_root, store=store, telemetry=telemetry)
        self.project_brief = project_brief
        self.architect = architect
        self.developer = developer
        self.design = design
        self.qa = qa

    async def execute_request(self, *, run_id: str, task: dict) -> dict:
        self.store.update_task(task["id"], status="ready", owner_role="PM")
        plan = self._build_plan(task)
        self.store.record_artifact(run_id, task["id"], "pm_plan", plan.model_dump_json(indent=2))
        existing = self.store.get_subtasks(task["id"])
        subtasks = existing if existing else [self._create_subtask(task, item) for item in plan.subtasks]

        self.store.update_task(task["id"], status="in_progress", owner_role="PM")
        for subtask in subtasks:
            result = await self._run_subtask(run_id=run_id, subtask=subtask)
            if result.get("paused"):
                return result
            if not result["approved"]:
                for pending_subtask in self.store.get_subtasks(task["id"]):
                    if pending_subtask["status"] not in {"completed", "blocked"}:
                        self.store.update_task(
                            pending_subtask["id"],
                            status="blocked",
                            owner_role="PM",
                            review_notes="Parent task blocked after unresolved QA review.",
                        )
                self.store.update_task(task["id"], status="blocked", owner_role="PM", review_notes="QA requested changes that were not resolved.")
                return {"completed": False, "issues": result["issues"], "task_id": task["id"]}

        self.store.update_task(task["id"], status="in_review", owner_role="QA")
        final_review = await self._review_parent_task(run_id=run_id, parent_task=task)
        if not final_review.approved:
            self.store.update_task(task["id"], status="blocked", owner_role="PM", review_notes="; ".join(final_review.issues))
            return {"completed": False, "issues": final_review.issues, "task_id": task["id"]}

        summary = "PM completed all subtasks and QA approved the final deliverables."
        self.store.update_task(task["id"], status="completed", owner_role="QA", result_summary=summary, review_notes=final_review.summary)
        return {"completed": True, "summary": summary, "task_id": task["id"]}

    def _build_plan(self, task: dict) -> PlanSummary:
        subject = self._infer_subject(task["objective"], task["details"])
        subject_slug = self._slugify(subject)
        class_name = "".join(part.capitalize() for part in subject_slug.split("-")) or "Feature"

        design_doc = f"projects/tactics-game/artifacts/{subject_slug}_design.md"
        code_path = f"projects/tactics-game/artifacts/{subject_slug}.py"
        ui_path = f"projects/tactics-game/artifacts/{subject_slug}_ui_notes.md"

        return PlanSummary(
            summary=f"PM decomposed the request into architecture, code, and UI subtasks for {class_name}.",
            subtasks=[
                SubtaskPlan(
                    title=f"{class_name} Architecture Design",
                    assignee="Architect",
                    objective=f"Create the architecture and gameplay design document for {class_name}.",
                    details=f"Document the {class_name} unit for the tactics game with explicit sections for overview, attributes, abilities, and acceptance criteria.",
                    expected_artifact_path=design_doc,
                    acceptance=AcceptanceCriteria(
                        required_headings=["Overview", "Attributes", "Abilities", "Acceptance Criteria"],
                        required_keywords=[class_name],
                    ),
                ),
                SubtaskPlan(
                    title=f"{class_name} Python Module",
                    assignee="Developer",
                    objective=f"Implement the {class_name} class in Python.",
                    details=f"Write a Python module for {class_name} suitable for the tactics game domain. Include health, mana, spell power, and casting behavior.",
                    expected_artifact_path=code_path,
                    acceptance=AcceptanceCriteria(
                        required_strings=[f"class {class_name}", "cast_spell", "take_damage", "heal", "is_alive"],
                        required_keywords=["mana", "spell_power"],
                        python_compile=True,
                    ),
                    requires_dispatch_approval=True,
                ),
                SubtaskPlan(
                    title=f"{class_name} UI Notes",
                    assignee="Design",
                    objective=f"Create UI and visual notes for presenting {class_name}.",
                    details=f"Describe how the UI should communicate {class_name} identity, spellcasting feedback, and player readability.",
                    expected_artifact_path=ui_path,
                    acceptance=AcceptanceCriteria(
                        required_headings=["UI Concepts", "Visual Direction", "Player Feedback"],
                        required_keywords=[class_name, "spell"],
                    ),
                ),
            ],
        )

    def _infer_subject(self, objective: str, details: str) -> str:
        text = f"{objective} {details}"
        match = re.search(r"\b(mage|warrior|archer|healer)\b", text, flags=re.IGNORECASE)
        if match:
            return match.group(1)
        words = re.findall(r"[A-Za-z]+", objective)
        return words[-1] if words else "feature"

    def _slugify(self, text: str) -> str:
        return "-".join(part.lower() for part in re.findall(r"[A-Za-z0-9]+", text)) or "feature"

    def _create_subtask(self, parent_task: dict, plan: SubtaskPlan) -> dict:
        acceptance = plan.acceptance.model_dump()
        acceptance["requires_dispatch_approval"] = plan.requires_dispatch_approval
        return self.store.create_subtask(
            parent_task["project_name"],
            parent_task["id"],
            plan.title,
            plan.details,
            objective=plan.objective,
            owner_role=plan.assignee,
            priority=parent_task["priority"],
            expected_artifact_path=plan.expected_artifact_path,
            acceptance=acceptance,
        )

    async def _run_subtask(self, *, run_id: str, subtask: dict) -> dict:
        assignee = subtask["owner_role"]
        if self._requires_dispatch_approval(subtask) and not self._dispatch_approval_ready(subtask):
            return self._pause_for_dispatch_approval(run_id=run_id, subtask=subtask)
        correction_notes: str | None = None

        for attempt in range(2):
            self.store.update_task(subtask["id"], status="ready", owner_role="PM")
            self.store.record_delegation(run_id, subtask["id"], from_role="PM", to_role=assignee, note=subtask["objective"])
            self.store.update_task(subtask["id"], status="in_progress", owner_role=assignee)
            await self._launch_worker_subtask(run_id=run_id, subtask=subtask, correction_notes=correction_notes)
            self.store.update_task(subtask["id"], status="in_review", owner_role="QA")
            if self.qa is None:
                raise ValueError("QA agent is required to review delegated worker artifacts.")
            review = await self.qa.review_artifact(run_id=run_id, task=subtask)
            if review.approved:
                self.store.update_task(subtask["id"], status="completed", owner_role="QA", review_notes=review.summary, result_summary=review.summary)
                return {"approved": True, "issues": [], "review": review}
            correction_notes = "\n".join(review.issues)
            self.store.update_task(subtask["id"], status="ready", owner_role=assignee, review_notes=correction_notes)

        return {"approved": False, "issues": review.issues, "review": review}

    async def _review_parent_task(self, *, run_id: str, parent_task: dict) -> QAReviewResult:
        subtasks = self.store.get_subtasks(parent_task["id"])
        validation_results = self.store.list_validation_results(run_id)
        issues: list[str] = []
        for subtask in subtasks:
            if subtask["status"] != "completed":
                issues.append(f"Subtask not completed: {subtask['title']}")
            artifact = self.repo_root / subtask["expected_artifact_path"]
            if not artifact.exists():
                issues.append(f"Missing approved artifact: {subtask['expected_artifact_path']}")
            if not self._has_passing_validation(validation_results, subtask["id"], subtask["expected_artifact_path"]):
                issues.append(f"Missing passing validation result: {subtask['title']}")
        approved = not issues
        summary = "QA approved the parent task." if approved else "Parent task review found issues."
        self.store.record_message(
            run_id,
            parent_task["id"],
            "qa_parent_review",
            {"approved": approved, "issues": issues},
            source="QA",
        )
        return QAReviewResult(approved=approved, summary=summary, issues=issues)

    def _requires_dispatch_approval(self, subtask: dict[str, Any]) -> bool:
        acceptance = subtask.get("acceptance") or {}
        return bool(acceptance.get("requires_dispatch_approval"))

    def _dispatch_approval_ready(self, subtask: dict[str, Any]) -> bool:
        if not self._requires_dispatch_approval(subtask):
            return True
        approval = self.store.latest_approval_for_task(subtask["id"])
        return bool(approval and approval.get("status") == "approved")

    def _runtime_mode(self, run_id: str) -> str:
        team_state = self.store.load_team_state(run_id) or {}
        runtime_mode = team_state.get("runtime_mode") or os.environ.get("AISTUDIO_RUNTIME_MODE") or "custom"
        return "sdk" if runtime_mode == "sdk" else "custom"

    def _canonical_manifest_json(self, payload: dict[str, Any]) -> str:
        return json.dumps(payload, ensure_ascii=True, separators=(",", ":"), sort_keys=True)

    def _manifest_input_artifact_paths(self, subtask: dict[str, Any], correction_notes: str | None) -> list[str]:
        artifact_path = subtask.get("expected_artifact_path")
        if not correction_notes or not artifact_path:
            return []
        if not (self.repo_root / artifact_path).exists():
            return []
        return [artifact_path]

    def _build_write_manifest(self, *, run_id: str, subtask: dict[str, Any], correction_notes: str | None) -> dict[str, Any]:
        expected_output_path = subtask["expected_artifact_path"]
        manifest = {
            "manifest_version": 1,
            "execution_mode": "worker_only",
            "run_id": run_id,
            "task_id": subtask["id"],
            "project_name": subtask["project_name"],
            "role": subtask["owner_role"],
            "runtime_mode": self._runtime_mode(run_id),
            "write_scope": "exact_paths_only",
            "expected_output_path": expected_output_path,
            "allowed_write_paths": [expected_output_path],
            "allowed_write_modes": ["overwrite"],
            "input_artifact_paths": self._manifest_input_artifact_paths(subtask, correction_notes),
            "issued_by": "PM",
            "issued_at": datetime.now(UTC).isoformat(timespec="seconds"),
        }
        manifest["seal_sha256"] = compute_worker_manifest_seal(manifest)
        return manifest

    def _update_worker_team_state(self, *, run_id: str, subtask: dict[str, Any], manifest: dict[str, Any]) -> None:
        team_state = self.store.load_team_state(run_id) or {}
        team_state["execution_mode"] = "worker_only"
        team_state["runtime_mode"] = manifest["runtime_mode"]
        team_state["worker_dispatch"] = {
            "task_id": subtask["id"],
            "role": subtask["owner_role"],
            "expected_output_path": manifest["expected_output_path"],
        }
        pending_sdk = team_state.get("pending_sdk_approval")
        if isinstance(pending_sdk, dict) and pending_sdk.get("task_id") == subtask["id"]:
            team_state.pop("pending_sdk_approval", None)
        self.store.update_run(run_id, team_state=team_state)

    async def _launch_worker_subtask(
        self,
        *,
        run_id: str,
        subtask: dict[str, Any],
        correction_notes: str | None,
    ) -> dict[str, Any]:
        manifest = self._build_write_manifest(run_id=run_id, subtask=subtask, correction_notes=correction_notes)
        self._update_worker_team_state(run_id=run_id, subtask=subtask, manifest=manifest)

        command = [
            sys.executable,
            str(self.repo_root / "scripts" / "worker.py"),
            "--role",
            subtask["owner_role"],
            "--run-id",
            run_id,
            "--task-id",
            subtask["id"],
        ]
        input_artifact_paths = manifest["input_artifact_paths"]
        if input_artifact_paths:
            command.extend(["--input-artifact-path", input_artifact_paths[-1]])
        if correction_notes:
            command.extend(["--correction-notes", correction_notes])

        env = os.environ.copy()
        env[WORKER_MANIFEST_ENV] = self._canonical_manifest_json(manifest)
        completed = await asyncio.to_thread(
            subprocess.run,
            command,
            cwd=self.repo_root,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        if completed.returncode != 0:
            output = "\n".join(part for part in [completed.stdout.strip(), completed.stderr.strip()] if part).strip()
            raise RuntimeError(output or f"Worker process failed for {subtask['id']}.")

        output_lines = [line for line in completed.stdout.splitlines() if line.strip()]
        if not output_lines:
            raise RuntimeError(f"Worker process returned no output for {subtask['id']}.")
        try:
            return json.loads(output_lines[-1])
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"Worker process returned invalid JSON for {subtask['id']}.") from exc

    def _pause_for_dispatch_approval(self, *, run_id: str, subtask: dict[str, Any]) -> dict[str, Any]:
        assignee = subtask["owner_role"]
        reason = subtask["objective"]
        approval = self.store.create_approval(
            run_id,
            subtask["id"],
            "PM",
            reason,
            approval_scope="project",
            target_role=assignee,
            exact_task=subtask["title"],
            expected_output=subtask.get("expected_artifact_path"),
            why_now=subtask["details"],
            risks=["Dispatch approval is required before specialist execution."],
        )
        payload: dict[str, Any] = {
            "paused": True,
            "task_id": subtask["id"],
            "approval": approval,
            "team_state": None,
        }
        runtime_mode = self._runtime_mode(run_id)
        if runtime_mode == "sdk":
            session_id = f"studio-specialist-{assignee.lower()}-{run_id}"
            team_state = self.store.load_team_state(run_id) or {}
            team_state["runtime_mode"] = "sdk"
            team_state["pending_sdk_approval"] = {
                "session_id": session_id,
                "target_role": assignee,
                "task_id": subtask["id"],
                "approval_id": approval["id"],
                "expected_output": subtask.get("expected_artifact_path"),
            }
            self.store.update_run(run_id, team_state=team_state)
            self.store.record_trace_event(
                run_id,
                subtask["id"],
                "sdk_approval_bridge_requested",
                source="PM",
                packet={
                    "approval_id": approval["id"],
                    "runtime_mode": "sdk",
                    "target_role": assignee,
                    "session_id": session_id,
                    "expected_output": subtask.get("expected_artifact_path"),
                    "exact_task": subtask["title"],
                },
            )
            payload["team_state"] = team_state
        return payload

    def _has_passing_validation(
        self,
        validation_results: list[dict[str, Any]],
        task_id: str,
        expected_artifact_path: str | None,
    ) -> bool:
        passing_statuses = {"passed", "approved", "success"}
        for result in validation_results:
            if result.get("task_id") != task_id:
                continue
            if str(result.get("status") or "").lower() not in passing_statuses:
                continue
            if expected_artifact_path and result.get("artifact_path") and result["artifact_path"] != expected_artifact_path:
                continue
            return True
        return False
