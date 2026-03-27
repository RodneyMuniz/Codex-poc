from __future__ import annotations

import asyncio
import re
from pathlib import Path
from typing import Any

from agents.architect import ArchitectAgent
from agents.config import load_environment, resolve_runtime_mode
from agents.design import DesignAgent
from agents.git_service import GitService
from agents.pm import ProjectManagerAgent
from agents.prompt_specialist import PromptSpecialistAgent
from agents.qa import QAAgent
from agents.developer import DeveloperAgent
from agents.schemas import HealthCheckResult
from agents.telemetry import TelemetryRecorder
from sessions import SessionStore


SDK_PLANNING_LAYER = "deterministic_internal_helper"
TASK_ID_PATTERN = re.compile(r"\b([A-Z]+-\d+)\b")


class Orchestrator:
    def __init__(self, repo_root: str | Path | None = None) -> None:
        self.repo_root = Path(repo_root or Path.cwd()).resolve()
        load_environment(self.repo_root)
        self.runtime_mode = resolve_runtime_mode()
        self.store = SessionStore(self.repo_root)
        self.telemetry = TelemetryRecorder(self.repo_root)
        self.git = GitService(self.repo_root)
        self.prompt_specialist = PromptSpecialistAgent(repo_root=self.repo_root, store=self.store, telemetry=self.telemetry)

    def _read_text(self, relative_path: str) -> str:
        return (self.repo_root / relative_path).read_text(encoding="utf-8")

    def load_project_brief(self, project_name: str) -> str:
        return self._read_text(f"projects/{project_name}/governance/PROJECT_BRIEF.md")

    def get_run_evidence(self, run_id: str) -> dict[str, Any]:
        return self.store.get_run_evidence(run_id)

    def _route_step(
        self,
        *,
        runtime_role: str,
        model_role: str,
        profile_label: str,
        profile_summary: str,
        reasoning_depth: str,
        cost_tier: str,
        route_reason: str,
        runtime_mode: str | None = None,
    ) -> dict[str, Any]:
        route = {
            "runtime_role": runtime_role,
            "model_role": model_role,
            "profile_label": profile_label,
            "profile_summary": profile_summary,
            "reasoning_depth": reasoning_depth,
            "cost_tier": cost_tier,
            "route_reason": route_reason,
        }
        if runtime_mode is not None:
            route["runtime_mode"] = runtime_mode
        return route

    def _operator_brief(
        self,
        *,
        objective: str,
        details: str,
        assumptions: list[str] | None = None,
        risks: list[str] | None = None,
        priority: str = "medium",
        requires_approval: bool = False,
    ) -> dict[str, Any]:
        response_chips: list[dict[str, str]] = []
        if requires_approval or risks:
            response_chips.append(
                {
                    "label": "Need Proof",
                    "value": "Confirm the scope with evidence before downstream dispatch.",
                }
            )
        else:
            response_chips.append(
                {
                    "label": "Ready",
                    "value": "The request can move forward without an approval pause.",
                }
            )
        response_chips.append({"label": "Priority", "value": priority.title()})
        if assumptions:
            response_chips.append({"label": "Assumptions", "value": "; ".join(assumptions[:2])})
        if risks:
            response_chips.append({"label": "Risks", "value": "; ".join(risks[:2])})
        return {
            "objective": objective,
            "details": details,
            "response_chips": response_chips,
        }

    def _parse_target_status(self, user_text: str) -> str | None:
        lowered = user_text.lower()
        if "in progress" in lowered or "in_progress" in lowered:
            return "in_progress"
        if "in review" in lowered or "review" in lowered:
            return "in_review"
        if "ready" in lowered:
            return "ready"
        if "backlog" in lowered:
            return "backlog"
        if "blocked" in lowered:
            return "blocked"
        if "completed" in lowered or "complete" in lowered or "done" in lowered:
            return "completed"
        return None

    def _direct_board_action(self, project_name: str, user_text: str) -> dict[str, Any] | None:
        task_match = TASK_ID_PATTERN.search(user_text)
        target_status = self._parse_target_status(user_text)
        if task_match is None or target_status is None:
            return None
        task_id = task_match.group(1)
        task = self.store.get_task(task_id)
        if task is None:
            return None
        return {
            "task": task,
            "project_name": task["project_name"],
            "operator_action": {
                "action_type": "move_task_status",
                "target_task_id": task_id,
                "target_status": target_status,
            },
            "execution_runtime": {"mode": "deterministic"},
        }

    async def _preview_prompt_specialist(self, project_name: str, user_text: str, clarification: str | None = None) -> dict[str, Any]:
        combined_text = user_text if clarification is None else f"{user_text}\n\n{clarification}"
        packet = await self.prompt_specialist.process_input(combined_text)
        packet_data = packet.model_dump()
        return {
            "project_name": project_name,
            "packet": packet_data,
            "operator_brief": self._operator_brief(
                objective=packet_data["objective"],
                details=packet_data["details"],
                assumptions=packet_data.get("assumptions") or [],
                risks=packet_data.get("risks") or [],
                priority=str(packet_data.get("priority") or "medium"),
                requires_approval=bool(packet_data.get("requires_approval")),
            ),
            "route_preview": [
                self._route_step(
                    runtime_role="PromptSpecialist",
                    model_role="prompt_specialist",
                    profile_label="Prompt Specialist",
                    profile_summary="Translates natural-language operator intent into a delegation packet.",
                    reasoning_depth="low",
                    cost_tier="low",
                    route_reason="Used first so the operator gets a clearer objective, assumptions, risks, and approval expectation before dispatch.",
                ),
                self._route_step(
                    runtime_role="Orchestrator",
                    model_role="orchestrator",
                    profile_label="Project Orchestrator",
                    profile_summary="Owns operator interaction, validates scope, and decides when specialist work should start or pause.",
                    reasoning_depth="low",
                    cost_tier="low",
                    route_reason="Keeps the Studio Lead in the loop and protects framework integrity before downstream delegation.",
                    runtime_mode=self.runtime_mode,
                ),
            ],
            "execution_runtime": {"mode": self.runtime_mode},
        }

    def _preview_direct_board_action(self, direct_action: dict[str, Any], user_text: str) -> dict[str, Any]:
        task = direct_action["task"]
        target_status = direct_action["operator_action"]["target_status"]
        return {
            "project_name": direct_action["project_name"],
            "task": task,
            "packet": {
                "objective": task["objective"] or task["title"],
                "details": task["details"],
                "request_text": user_text,
            },
            "operator_action": direct_action["operator_action"],
            "operator_brief": self._operator_brief(
                objective=task["objective"] or task["title"],
                details=task["details"],
                assumptions=[],
                risks=[],
                priority=str(task.get("priority") or "medium"),
                requires_approval=target_status == "completed",
            ),
            "route_preview": [
                self._route_step(
                    runtime_role="Orchestrator",
                    model_role="orchestrator",
                    profile_label="Project Orchestrator",
                    profile_summary="Owns operator interaction and direct board actions.",
                    reasoning_depth="low",
                    cost_tier="low",
                    route_reason="Direct board actions bypass the Prompt Specialist and execute as a one-hop deterministic route.",
                    runtime_mode="deterministic",
                ),
            ],
            "execution_runtime": {"mode": "deterministic"},
        }

    def _already_progressed_payload(self, run: dict[str, Any], *, approval_id: str | None = None) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "status": "already_progressed",
            "run_id": run["id"],
            "run_status": run["status"],
            "task_id": run["task_id"],
        }
        if approval_id is not None:
            payload["approval_id"] = approval_id
        return payload

    async def preview_request(self, project_name: str, user_text: str, clarification: str | None = None) -> dict[str, Any]:
        direct_action = self._direct_board_action(project_name, user_text)
        if direct_action is not None:
            return self._preview_direct_board_action(direct_action, user_text)
        return await self._preview_prompt_specialist(project_name, user_text, clarification)

    async def dispatch_request(self, project_name: str, user_text: str, clarification: str | None = None) -> dict[str, Any]:
        preview = await self.preview_request(project_name, user_text, clarification)
        task = preview.get("task")
        if task is None:
            packet = preview["packet"]
            task = self.store.create_task(
                preview["project_name"],
                packet["objective"][:80],
                packet["details"],
                objective=packet["objective"],
                status="backlog",
                requires_approval=bool(packet.get("requires_approval")),
                owner_role="Orchestrator",
                task_kind="request",
                priority=str(packet.get("priority") or "medium"),
                raw_request=user_text,
            )
            preview["task"] = task
        backup_info = self.store.create_dispatch_backup(
            project_name=preview["project_name"],
            trigger="dispatch_request",
            task_id=task["id"],
            note=user_text,
        )
        run_result = await self.start_task(task["id"], preview_payload=preview, backup_info=backup_info)
        refreshed_task = self.store.get_task(task["id"]) or task
        return {
            "preview": preview,
            "task": refreshed_task,
            "run_result": run_result,
            "dispatch_backup": backup_info,
        }

    async def approve_and_resume(self, approval_id: str, note: str | None = None) -> dict[str, Any]:
        approval = self.store.get_approval(approval_id)
        if approval is None:
            raise ValueError(f"Approval not found: {approval_id}")
        run = self.store.get_run(approval["run_id"])
        if run is None:
            raise ValueError(f"Run not found for approval {approval_id}")
        if run["status"] != "paused_approval":
            return self._already_progressed_payload(run, approval_id=approval_id)
        if approval["status"] != "approved":
            approval = self.store.decide_approval(approval_id, "approve", note)
        task = self.store.get_task(run["task_id"])
        if task is None:
            raise ValueError(f"Task not found for run {run['id']}")
        team_state = self.store.load_team_state(run["id"]) or {}
        team_state["phase"] = "resumed"
        self.store.update_run(run["id"], status="running", stop_reason=None, team_state=team_state)
        return await self._execute_run(run["id"], task)

    async def start_task(
        self,
        task_id: str,
        *,
        preview_payload: dict[str, Any] | None = None,
        backup_info: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        task = self.store.get_task(task_id)
        if task is None:
            raise ValueError(f"Task not found: {task_id}")
        if preview_payload and preview_payload.get("operator_action", {}).get("action_type") == "move_task_status":
            target_status = preview_payload["operator_action"]["target_status"]
            review_state = "Accepted" if target_status == "completed" else "Revision Needed"
            updated_task = self.store.update_task(task_id, status=target_status, review_state=review_state)
            run = self.store.create_run(
                task["project_name"],
                task_id,
                team_state={"runtime_mode": self.runtime_mode, "dispatch_mode": "deterministic"},
            )
            current_team_state = self.store.load_team_state(run["id"]) or {}
            current_team_state.setdefault("runtime_mode", self.runtime_mode)
            current_team_state["dispatch_mode"] = "deterministic"
            current_team_state["phase"] = "completed"
            self.store.update_run(
                run["id"],
                status="completed",
                stop_reason="direct_board_action",
                team_state=current_team_state,
                completed=True,
            )
            return {
                "status": "completed",
                "run_status": "completed",
                "run_id": run["id"],
                "task_id": task_id,
                "target_task_id": task_id,
                "task": updated_task,
                "dispatch_backup": backup_info,
                "preview": preview_payload,
            }
        run = self.store.create_run(task["project_name"], task_id, team_state={"phase": "intake", "runtime_mode": self.runtime_mode})
        current_team_state = self.store.load_team_state(run["id"]) or {}
        current_team_state["execution_mode"] = "worker_only"
        self.store.update_run(run["id"], team_state=current_team_state)
        if task["requires_approval"] and self.store.approval_required_and_missing(task_id):
            approval = self.store.create_approval(run["id"], task_id, requested_by="Orchestrator", reason=task["objective"])
            self.store.update_run(
                run["id"],
                status="paused_approval",
                stop_reason="awaiting_operator_approval",
                team_state={**current_team_state, "phase": "awaiting_approval", "runtime_mode": self.runtime_mode},
            )
            return {
                "status": "paused_approval",
                "run_id": run["id"],
                "task_id": task_id,
                "approval_id": approval["id"],
                "dispatch_backup": backup_info,
                "preview": preview_payload,
            }
        return await self._execute_run(run["id"], task)

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
        run = self.store.create_run(
            project_name,
            task["id"],
            team_state={"phase": "intake", "runtime_mode": self.runtime_mode, "execution_mode": "worker_only"},
        )
        if task["requires_approval"] and self.store.approval_required_and_missing(task["id"]):
            approval = self.store.create_approval(run["id"], task["id"], requested_by="Orchestrator", reason=task["objective"])
            self.store.update_run(
                run["id"],
                status="paused_approval",
                stop_reason="awaiting_operator_approval",
                team_state={"phase": "awaiting_approval", "runtime_mode": self.runtime_mode, "execution_mode": "worker_only"},
            )
            return {"status": "paused_approval", "run_id": run["id"], "task_id": task["id"], "approval_id": approval["id"]}
        return await self._execute_run(run["id"], task)

    async def resume_run(self, run_id: str) -> dict[str, Any]:
        run = self.store.get_run(run_id)
        if run is None:
            raise ValueError(f"Run not found: {run_id}")
        if run["status"] != "paused_approval":
            return self._already_progressed_payload(run)
        task = self.store.get_task(run["task_id"])
        if task is None:
            raise ValueError(f"Task not found for run {run_id}")
        approval = self.store.latest_approval_for_task(task["id"])
        if approval is None or approval["status"] != "approved":
            raise ValueError(f"Run {run_id} cannot resume until its approval is approved.")
        team_state = self.store.load_team_state(run_id) or {}
        team_state["phase"] = "resumed"
        self.store.update_run(run_id, status="running", stop_reason=None, team_state=team_state)
        return await self._execute_run(run_id, task)

    def create_git_checkpoint(self, message: str) -> str:
        sha = self.git.create_checkpoint(message)
        self.telemetry.info("git_checkpoint", commit=sha, message=message)
        return sha

    async def _execute_run(self, run_id: str, task: dict) -> dict[str, Any]:
        task = dict(task)
        runtime_mode = self.runtime_mode
        task["runtime_mode"] = runtime_mode
        team_state = self.store.load_team_state(run_id) or {}
        team_state["runtime_mode"] = runtime_mode
        team_state.setdefault("execution_mode", "worker_only")
        if runtime_mode == "sdk":
            task["sdk_runtime_context"] = {
                "planning_layer": SDK_PLANNING_LAYER,
                "orchestrator_source": "chat_or_control_room",
                "specialist_roles": ["Architect", "Developer", "Design"],
            }
            team_state["specialist_runtime"] = dict(task["sdk_runtime_context"])
            self.store.record_trace_event(
                run_id,
                task["id"],
                "sdk_specialist_runtime_selected",
                source="Orchestrator",
                summary="Orchestrator kept control and selected the official Agents SDK for downstream specialist work.",
                packet={
                    "mode": "sdk",
                    "orchestrator_source": "chat_or_control_room",
                    "planning_layer": SDK_PLANNING_LAYER,
                    "specialist_roles": ["Architect", "Developer", "Design"],
                },
                route={
                    "runtime_mode": "sdk",
                    "runtime_role": "Orchestrator",
                    "model_role": "orchestrator",
                    "profile_label": "Project Orchestrator",
                },
                raw_json={
                    "mode": "sdk",
                    "orchestrator_source": "chat_or_control_room",
                    "planning_layer": SDK_PLANNING_LAYER,
                    "specialist_roles": ["Architect", "Developer", "Design"],
                },
            )
        self.store.update_run(run_id, team_state=team_state)
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
            team_state["phase"] = status
            self.store.update_run(run_id, status=status, stop_reason=stop_reason, team_state=team_state, completed=completed)
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
            team_state["phase"] = "failed"
            self.store.update_run(run_id, status="failed", last_error=str(exc), team_state=team_state, completed=True)
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
