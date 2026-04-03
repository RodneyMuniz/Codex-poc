from __future__ import annotations

from pathlib import Path

from hooks import post_task, pre_task
from agents.role_base import StudioRoleAgent
from agents.schemas import QAReviewResult


class QAAgent(StudioRoleAgent):
    def __init__(self, *, repo_root: str | Path, store, telemetry, project_brief: str) -> None:
        super().__init__(role_name="QA", model_role="qa", repo_root=repo_root, store=store, telemetry=telemetry)
        self.project_brief = project_brief

    @pre_task("Review")
    @post_task("Review")
    async def review_artifact(self, *, run_id: str, task: dict) -> QAReviewResult:
        issues: list[str] = []
        artifact_path = self.repo_root / task["expected_artifact_path"]
        checks: dict[str, bool] = {}
        producer_run = self.store.latest_agent_run(run_id, task["id"], role=task["assigned_role"])
        if task["acceptance"].get("artifact_must_exist", True) and not artifact_path.exists():
            issues.append(f"Missing artifact: {task['expected_artifact_path']}")
        checks["artifact_exists"] = artifact_path.exists()
        content = artifact_path.read_text(encoding="utf-8") if artifact_path.exists() else ""
        lowered = content.lower()

        for heading in task["acceptance"].get("required_headings", []):
            if heading.lower() not in lowered:
                issues.append(f"Missing required heading: {heading}")
        checks["required_headings"] = all(
            heading.lower() in lowered for heading in task["acceptance"].get("required_headings", [])
        )
        for keyword in task["acceptance"].get("required_keywords", []):
            if keyword.lower() not in lowered:
                issues.append(f"Missing required keyword: {keyword}")
        checks["required_keywords"] = all(
            keyword.lower() in lowered for keyword in task["acceptance"].get("required_keywords", [])
        )
        for required in task["acceptance"].get("required_strings", []):
            if required not in content:
                issues.append(f"Missing required text: {required}")
        checks["required_strings"] = all(
            required in content for required in task["acceptance"].get("required_strings", [])
        )
        if task["acceptance"].get("python_compile") and artifact_path.exists():
            try:
                compile(content, str(artifact_path), "exec")
                checks["python_compile"] = True
            except SyntaxError as exc:
                issues.append(f"Python compile failed: {exc}")
                checks["python_compile"] = False
        elif task["acceptance"].get("python_compile"):
            checks["python_compile"] = False

        required_input_role = task["acceptance"].get("required_input_role")
        if required_input_role and task.get("parent_task_id"):
            parent_subtasks = self.store.get_subtasks(task["parent_task_id"])
            upstream = next(
                (item for item in parent_subtasks if item["assigned_role"] == required_input_role),
                None,
            )
            expected_input_path = upstream["expected_artifact_path"] if upstream else None
            input_matches = bool(
                producer_run
                and producer_run.get("input_artifact_path")
                and expected_input_path
                and producer_run["input_artifact_path"] == expected_input_path
            )
            checks["input_artifact_consumed"] = input_matches
            if not input_matches:
                issues.append(
                    f"Missing consumed input artifact evidence from {required_input_role}: {expected_input_path or 'unknown'}"
                )

        approved = not issues
        summary = "QA approved the artifact." if approved else "QA requested changes."
        self.store.record_message(
            run_id,
            task["id"],
            "qa_review",
            {"approved": approved, "issues": issues, "artifact_path": task["expected_artifact_path"]},
            source="QA",
        )
        self.store.record_artifact(run_id, task["id"], "qa_review", summary if approved else "\n".join(issues))
        self.store.record_validation_result(
            run_id,
            task["id"],
            agent_run_id=producer_run["id"] if producer_run else None,
            validator_role="QA",
            artifact_path=task["expected_artifact_path"],
            status="passed" if approved else "failed",
            checks=checks,
            summary=summary if approved else "\n".join(issues),
        )
        return QAReviewResult(approved=approved, summary=summary, issues=issues, checks=checks)
