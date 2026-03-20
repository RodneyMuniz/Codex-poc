from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

from agents.architect import ArchitectAgent
from agents.config import load_environment
from agents.design import DesignAgent
from agents.git_service import GitService
from agents.pm import ProjectManagerAgent
from agents.prompt_specialist import PromptSpecialistAgent
from agents.qa import QAAgent
from agents.developer import DeveloperAgent
from agents.schemas import HealthCheckResult
from agents.telemetry import TelemetryRecorder
from sessions import SessionStore


class Orchestrator:
    def __init__(self, repo_root: str | Path | None = None) -> None:
        self.repo_root = Path(repo_root or Path.cwd()).resolve()
        load_environment(self.repo_root)
        self.store = SessionStore(self.repo_root)
        self.telemetry = TelemetryRecorder(self.repo_root)
        self.git = GitService(self.repo_root)
        self.prompt_specialist = PromptSpecialistAgent(repo_root=self.repo_root, store=self.store, telemetry=self.telemetry)

    def _read_text(self, relative_path: str) -> str:
        return (self.repo_root / relative_path).read_text(encoding="utf-8")

    def load_project_brief(self, project_name: str) -> str:
        return self._read_text(f"projects/{project_name}/governance/PROJECT_BRIEF.md")

    async def intake_request(self, project_name: str, user_text: str) -> dict[str, Any]:
        packet = await self.prompt_specialist.process_input(user_text)
        title = packet.objective[:80]
        task = self.store.create_task(
            project_name,
            title,
            packet.details,
            objective=packet.objective,
            status="backlog",
            requires_approval=packet.requires_approval,
            owner_role="Orchestrator",
            task_kind="request",
            priority=packet.priority,
            raw_request=user_text,
        )
        self.telemetry.info(
            "task_intake",
            task_id=task["id"],
            project_name=project_name,
            priority=packet.priority,
            requires_approval=packet.requires_approval,
        )
        return {"packet": packet.model_dump(), "task": task}

    def list_tasks(self, project_name: str | None = None, status: str | None = None) -> list[dict[str, Any]]:
        return self.store.list_tasks(project_name, status=status)

    def list_approvals(self, status: str | None = None) -> list[dict[str, Any]]:
        return self.store.list_approvals(status)

    def approve(self, approval_id: str, note: str | None = None) -> dict[str, Any]:
        approval = self.store.decide_approval(approval_id, "approve", note)
        self.telemetry.info("approval_decided", approval_id=approval_id, decision="approved", run_id=approval["run_id"])
        return approval

    def reject(self, approval_id: str, note: str | None = None) -> dict[str, Any]:
        approval = self.store.decide_approval(approval_id, "reject", note)
        run_id = approval["run_id"]
        if run_id:
            self.store.update_run(run_id, status="cancelled", stop_reason="approval_rejected", completed=True)
        self.telemetry.info("approval_decided", approval_id=approval_id, decision="rejected", run_id=run_id)
        return approval

    def health_check(self) -> dict[str, Any]:
        required_files = [
            "governance/FRAMEWORK.md",
            "governance/GOVERNANCE_RULES.md",
            "governance/VISION.md",
            "governance/MODEL_REASONING_MATRIX.md",
            "governance/MEMORY_MAP.md",
            "projects/tactics-game/governance/PROJECT_BRIEF.md",
            "memory/framework_health.json",
            "memory/session_summaries.json",
        ]
        required_agents = [
            "agents/prompt_specialist.py",
            "agents/orchestrator.py",
            "agents/pm.py",
            "agents/architect.py",
            "agents/developer.py",
            "agents/design.py",
            "agents/qa.py",
        ]
        issues: list[str] = []
        checked_files: list[str] = []
        checked_agents: list[str] = []

        schema = self.store.schema_health()
        for relative_path in required_files:
            checked_files.append(relative_path)
            if not (self.repo_root / relative_path).exists():
                issues.append(f"Missing required file: {relative_path}")
        for relative_path in required_agents:
            checked_agents.append(relative_path)
            if not (self.repo_root / relative_path).exists():
                issues.append(f"Missing registered agent file: {relative_path}")

        for task in self.store.list_tasks():
            if task["status"] not in {"backlog", "ready", "in_progress", "in_review", "completed", "blocked"}:
                issues.append(f"Invalid task status for {task['id']}: {task['status']}")
            if task["parent_task_id"] and not self.store.get_task(task["parent_task_id"]):
                issues.append(f"Subtask {task['id']} has missing parent {task['parent_task_id']}")
            if task["task_kind"] == "subtask" and task["parent_task_id"]:
                parent = self.store.get_task(task["parent_task_id"])
                if parent and parent["status"] in {"completed", "blocked"} and task["status"] not in {"completed", "blocked"}:
                    issues.append(
                        f"Subtask {task['id']} is {task['status']} while parent {parent['id']} is {parent['status']}"
                    )

        payload = HealthCheckResult(
            ok=schema["ok"] and not issues,
            checked_tables=schema["tables"],
            checked_files=checked_files,
            checked_agents=checked_agents,
            issues=schema["issues"] + issues,
        ).model_dump()
        self.store.write_health_snapshot(payload)
        self.telemetry.append_event("health_check", payload)
        return payload

    async def run_next_task(self, project_name: str) -> dict[str, Any]:
        health = self.health_check()
        if not health["ok"]:
            return {"status": "health_check_failed", "issues": health["issues"]}
        task = self.store.get_next_runnable_task(project_name)
        if task is None:
            return {"status": "idle", "message": f"No backlog or ready tasks for {project_name}."}
        run = self.store.create_run(project_name, task["id"], team_state={"phase": "intake"})
        if task["requires_approval"] and self.store.approval_required_and_missing(task["id"]):
            approval = self.store.create_approval(run["id"], task["id"], requested_by="Orchestrator", reason=task["objective"])
            self.store.update_run(run["id"], status="paused_approval", stop_reason="awaiting_operator_approval", team_state={"phase": "awaiting_approval"})
            return {"status": "paused_approval", "run_id": run["id"], "task_id": task["id"], "approval_id": approval["id"]}
        return await self._execute_run(run["id"], task)

    async def resume_run(self, run_id: str) -> dict[str, Any]:
        run = self.store.get_run(run_id)
        if run is None:
            raise ValueError(f"Run not found: {run_id}")
        if run["status"] != "paused_approval":
            raise ValueError(f"Run {run_id} is not waiting for approval.")
        task = self.store.get_task(run["task_id"])
        if task is None:
            raise ValueError(f"Task not found for run {run_id}")
        approval = self.store.latest_approval_for_task(task["id"])
        if approval is None or approval["status"] != "approved":
            raise ValueError(f"Run {run_id} cannot resume until its approval is approved.")
        self.store.update_run(run_id, status="running", stop_reason=None, team_state={"phase": "resumed"})
        return await self._execute_run(run_id, task)

    def create_git_checkpoint(self, message: str) -> str:
        sha = self.git.create_checkpoint(message)
        self.telemetry.info("git_checkpoint", commit=sha, message=message)
        return sha

    async def _execute_run(self, run_id: str, task: dict) -> dict[str, Any]:
        project_brief = self.load_project_brief(task["project_name"])
        architect = ArchitectAgent(repo_root=self.repo_root, store=self.store, telemetry=self.telemetry, project_brief=project_brief)
        developer = DeveloperAgent(repo_root=self.repo_root, store=self.store, telemetry=self.telemetry, project_brief=project_brief)
        design = DesignAgent(repo_root=self.repo_root, store=self.store, telemetry=self.telemetry, project_brief=project_brief)
        qa = QAAgent(repo_root=self.repo_root, store=self.store, telemetry=self.telemetry, project_brief=project_brief)
        pm = ProjectManagerAgent(
            repo_root=self.repo_root,
            store=self.store,
            telemetry=self.telemetry,
            project_brief=project_brief,
            architect=architect,
            developer=developer,
            design=design,
            qa=qa,
        )
        try:
            result = await pm.execute_request(run_id=run_id, task=task)
            completed = bool(result.get("completed"))
            status = "completed" if completed else "blocked"
            stop_reason = "completed" if completed else "review_or_execution_issue"
            self.store.update_run(run_id, status=status, stop_reason=stop_reason, team_state={"phase": status}, completed=completed)
            summary = {
                "run_id": run_id,
                "task_id": task["id"],
                "task_status": self.store.get_task(task["id"])["status"],
                "run_status": status,
                "result_summary": result.get("summary"),
            }
            self.store.append_session_summary(summary)
            self.telemetry.info("run_finished", **summary)
            return summary
        except Exception as exc:
            self.store.update_task(task["id"], status="blocked", owner_role="Orchestrator", review_notes=str(exc))
            self.store.update_run(run_id, status="failed", last_error=str(exc), completed=True)
            self.telemetry.error("run_failed", run_id=run_id, task_id=task["id"], error=str(exc))
            raise
        finally:
            await pm.close()
            await architect.close()
            await developer.close()
            await design.close()
            await qa.close()


ProgramOrchestrator = Orchestrator


def run_async(coro):
    return asyncio.run(coro)
