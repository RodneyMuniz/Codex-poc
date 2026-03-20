from __future__ import annotations

from pathlib import Path

from agents.role_base import StudioRoleAgent
from agents.schemas import QAReviewResult


class QAAgent(StudioRoleAgent):
    def __init__(self, *, repo_root: str | Path, store, telemetry, project_brief: str) -> None:
        super().__init__(role_name="QA", model_role="qa", repo_root=repo_root, store=store, telemetry=telemetry)
        self.project_brief = project_brief

    async def review_artifact(self, *, run_id: str, task: dict) -> QAReviewResult:
        issues: list[str] = []
        artifact_path = self.repo_root / task["expected_artifact_path"]
        if task["acceptance"].get("artifact_must_exist", True) and not artifact_path.exists():
            issues.append(f"Missing artifact: {task['expected_artifact_path']}")
        content = artifact_path.read_text(encoding="utf-8") if artifact_path.exists() else ""
        lowered = content.lower()

        for heading in task["acceptance"].get("required_headings", []):
            if heading.lower() not in lowered:
                issues.append(f"Missing required heading: {heading}")
        for keyword in task["acceptance"].get("required_keywords", []):
            if keyword.lower() not in lowered:
                issues.append(f"Missing required keyword: {keyword}")
        for required in task["acceptance"].get("required_strings", []):
            if required not in content:
                issues.append(f"Missing required text: {required}")
        if task["acceptance"].get("python_compile") and artifact_path.exists():
            try:
                compile(content, str(artifact_path), "exec")
            except SyntaxError as exc:
                issues.append(f"Python compile failed: {exc}")

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
        return QAReviewResult(approved=approved, summary=summary, issues=issues)
