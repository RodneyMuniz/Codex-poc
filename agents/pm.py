from __future__ import annotations

import re
from pathlib import Path

from agents.architect import ArchitectAgent
from agents.developer import DeveloperAgent
from agents.design import DesignAgent
from agents.qa import QAAgent
from agents.role_base import StudioRoleAgent
from agents.schemas import AcceptanceCriteria, ArtifactResult, PlanSummary, QAReviewResult, SubtaskPlan


class ProjectManagerAgent(StudioRoleAgent):
    def __init__(
        self,
        *,
        repo_root: str | Path,
        store,
        telemetry,
        project_brief: str,
        architect: ArchitectAgent,
        developer: DeveloperAgent,
        design: DesignAgent,
        qa: QAAgent,
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
        return self.store.create_subtask(
            parent_task["project_name"],
            parent_task["id"],
            plan.title,
            plan.details,
            objective=plan.objective,
            owner_role=plan.assignee,
            priority=parent_task["priority"],
            expected_artifact_path=plan.expected_artifact_path,
            acceptance=plan.acceptance.model_dump(),
        )

    async def _run_subtask(self, *, run_id: str, subtask: dict) -> dict:
        assignee = subtask["owner_role"]
        producer = {
            "Architect": self.architect,
            "Developer": self.developer,
            "Design": self.design,
        }[assignee]
        correction_notes: str | None = None

        for attempt in range(2):
            self.store.update_task(subtask["id"], status="ready", owner_role="PM")
            self.store.record_delegation(run_id, subtask["id"], from_role="PM", to_role=assignee, note=subtask["objective"])
            self.store.update_task(subtask["id"], status="in_progress", owner_role=assignee)
            await producer.produce_artifact(run_id=run_id, task=subtask, correction_notes=correction_notes)
            self.store.update_task(subtask["id"], status="in_review", owner_role="QA")
            review = await self.qa.review_artifact(run_id=run_id, task=subtask)
            if review.approved:
                self.store.update_task(subtask["id"], status="completed", owner_role="QA", review_notes=review.summary, result_summary=review.summary)
                return {"approved": True, "issues": [], "review": review}
            correction_notes = "\n".join(review.issues)
            self.store.update_task(subtask["id"], status="ready", owner_role=assignee, review_notes=correction_notes)

        return {"approved": False, "issues": review.issues, "review": review}

    async def _review_parent_task(self, *, run_id: str, parent_task: dict) -> QAReviewResult:
        subtasks = self.store.get_subtasks(parent_task["id"])
        issues: list[str] = []
        for subtask in subtasks:
            if subtask["status"] != "completed":
                issues.append(f"Subtask not completed: {subtask['title']}")
            artifact = self.repo_root / subtask["expected_artifact_path"]
            if not artifact.exists():
                issues.append(f"Missing approved artifact: {subtask['expected_artifact_path']}")
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
