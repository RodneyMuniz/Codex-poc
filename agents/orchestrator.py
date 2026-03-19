from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

from autogen_agentchat.base import TaskResult

from agents.config import load_environment
from agents.git_service import GitService
from agents.project_po import build_project_team
from agents.telemetry import TelemetryRecorder
from sessions import SessionStore


class ProgramOrchestrator:
    def __init__(self, repo_root: str | Path | None = None) -> None:
        self.repo_root = Path(repo_root or Path.cwd()).resolve()
        load_environment(self.repo_root)
        self.store = SessionStore(self.repo_root)
        self.telemetry = TelemetryRecorder(self.repo_root)
        self.git = GitService(self.repo_root)

    def _read_text(self, relative_path: str) -> str:
        return (self.repo_root / relative_path).read_text(encoding="utf-8")

    def load_governance_context(self) -> str:
        parts = [
            self._read_text("governance/FRAMEWORK.md"),
            self._read_text("governance/GOVERNANCE_RULES.md"),
            self._read_text("governance/VISION.md"),
            self._read_text("governance/MODEL_REASONING_MATRIX.md"),
            self._read_text("governance/MEMORY_MAP.md"),
        ]
        return "\n\n".join(parts)

    def load_project_brief(self, project_name: str) -> str:
        return self._read_text(f"projects/{project_name}/governance/PROJECT_BRIEF.md")

    def create_task(self, project_name: str, title: str, description: str, requires_approval: bool = False) -> dict[str, Any]:
        task = self.store.create_task(project_name, title, description, requires_approval)
        self.telemetry.info("task_created", task_id=task["id"], project_name=project_name, requires_approval=requires_approval)
        return task

    def list_tasks(self, project_name: str | None = None) -> list[dict[str, Any]]:
        return self.store.list_tasks(project_name)

    def list_approvals(self, status: str | None = None) -> list[dict[str, Any]]:
        return self.store.list_approvals(status)

    def approve(self, approval_id: str, note: str | None = None) -> dict[str, Any]:
        approval = self.store.decide_approval(approval_id, "approve", note)
        self.telemetry.info("approval_decided", approval_id=approval_id, decision="approved", run_id=approval["run_id"])
        return approval

    def reject(self, approval_id: str, note: str | None = None) -> dict[str, Any]:
        approval = self.store.decide_approval(approval_id, "reject", note)
        self.store.update_run(approval["run_id"], status="cancelled", stop_reason="approval_rejected", completed=True)
        self.telemetry.info("approval_decided", approval_id=approval_id, decision="rejected", run_id=approval["run_id"])
        return approval

    async def run_next_task(self, project_name: str) -> dict[str, Any]:
        task = self.store.get_next_runnable_task(project_name)
        if task is None:
            return {"status": "idle", "message": f"No queued tasks for {project_name}."}
        run = self.store.create_run(project_name, task["id"])
        prompt = self._build_initial_prompt(task)
        return await self._execute_run(run["id"], task, prompt, resume=False)

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
        self.store.update_task(task["id"], status="in_progress", owner_role="ProjectPO")
        self.store.update_run(run_id, status="running", stop_reason=None, last_error=None)
        prompt = (
            f"Operator decision received. Approval {approval['id']} was approved."
            " Continue the task, record any final summary, and close it when ready."
        )
        return await self._execute_run(run_id, task, prompt, resume=True)

    def create_git_checkpoint(self, message: str) -> str:
        sha = self.git.create_checkpoint(message)
        self.telemetry.info("git_checkpoint", commit=sha, message=message)
        return sha

    def _build_initial_prompt(self, task: dict[str, Any]) -> str:
        return (
            "Operate on the active project task using the ProjectPO -> Architect -> Developer workflow.\n"
            f"Task title: {task['title']}\n"
            f"Task description: {task['description']}\n"
            f"Requires approval: {'yes' if task['requires_approval'] else 'no'}\n"
            "ProjectPO must manage the queue, delegate through the team, and either request approval or complete the task."
        )

    async def _execute_run(self, run_id: str, task: dict[str, Any], prompt: str, *, resume: bool) -> dict[str, Any]:
        governance_context = self.load_governance_context()
        project_brief = self.load_project_brief(task["project_name"])
        team, model_clients = build_project_team(
            store=self.store,
            run_id=run_id,
            task_record=task,
            governance_context=governance_context,
            project_brief=project_brief,
        )
        try:
            if resume:
                prior_state = self.store.load_team_state(run_id)
                if prior_state:
                    await team.load_state(prior_state)
            task_result: TaskResult | None = None
            async for event in team.run_stream(task=prompt):
                if isinstance(event, TaskResult):
                    task_result = event
                    continue
                self._record_event(run_id, task["id"], event)
            team_state = await team.save_state()
            self.store.save_team_state(run_id, team_state)
            final_task = self.store.get_task(task["id"]) or task
            stop_reason = task_result.stop_reason if task_result else None
            status = "running"
            completed = False
            if final_task["status"] == "awaiting_approval":
                status = "paused_approval"
            elif final_task["status"] == "completed":
                status = "completed"
                completed = True
            elif final_task["status"] in {"failed", "rejected"}:
                status = final_task["status"]
                completed = True
            self.store.update_run(run_id, status=status, stop_reason=stop_reason, team_state=team_state, completed=completed)
            for role, client in model_clients.items():
                usage = client.total_usage()
                self.telemetry.append_event(
                    "model_usage_totals",
                    {
                        "run_id": run_id,
                        "task_id": task["id"],
                        "role": role,
                        "prompt_tokens": usage.prompt_tokens,
                        "completion_tokens": usage.completion_tokens,
                    },
                )
            outcome = {
                "run_id": run_id,
                "task_id": task["id"],
                "task_status": final_task["status"],
                "run_status": status,
                "stop_reason": stop_reason,
                "result_summary": final_task.get("result_summary"),
            }
            self.telemetry.info("run_finished", **outcome)
            return outcome
        except Exception as exc:
            self.store.update_task(task["id"], status="failed", owner_role="ProjectPO")
            self.store.update_run(run_id, status="failed", last_error=str(exc), completed=True)
            self.telemetry.error("run_failed", run_id=run_id, task_id=task["id"], error=str(exc))
            raise
        finally:
            for client in model_clients.values():
                await client.close()

    def _record_event(self, run_id: str, task_id: str, event: Any) -> None:
        payload = event.model_dump(mode="json") if hasattr(event, "model_dump") else {"repr": repr(event)}
        usage = getattr(event, "models_usage", None)
        prompt_tokens = getattr(usage, "prompt_tokens", None)
        completion_tokens = getattr(usage, "completion_tokens", None)
        source = getattr(event, "source", None)
        event_type = event.__class__.__name__
        self.store.record_message(
            run_id,
            task_id,
            event_type,
            payload,
            source=source,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
        )
        self.telemetry.append_event(
            event_type,
            {
                "run_id": run_id,
                "task_id": task_id,
                "source": source,
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "payload": payload,
            },
        )


def run_async(coro):
    return asyncio.run(coro)
