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
from agents.config import get_capability_registry, get_deliverable_spec, infer_output_format, resolve_model, resolve_subtask_tier
from agents.developer import DeveloperAgent
from agents.design import DesignAgent
from agents.qa import QAAgent
from agents.role_base import StudioRoleAgent
from agents.schemas import AcceptanceCriteria, ArtifactResult, DeliverableContract, PlanSummary, QAReviewResult, SubtaskPlan
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
        self.store.update_task(
            task["id"],
            status="completed",
            owner_role="QA",
            result_summary=summary,
            review_notes=final_review.summary,
            review_state="Accepted",
        )
        return {"completed": True, "summary": summary, "task_id": task["id"]}

    def _build_plan(self, task: dict) -> PlanSummary:
        subject = self._infer_subject(task["objective"], task["details"])
        subject_slug = self._slugify(subject)
        class_name = "".join(part.capitalize() for part in subject_slug.split("-")) or "Feature"
        subject_label = subject.replace("-", " ").replace("_", " ").strip().title() or "Feature"
        context = {
            "project_name": task["project_name"],
            "subject": subject,
            "subject_slug": subject_slug,
            "subject_label": subject_label,
            "class_name": class_name,
        }
        registry = get_capability_registry(task["project_name"])
        requested_deliverables = (task.get("acceptance") or {}).get("requested_deliverables") or registry["default_deliverables"]
        subtasks = [self._build_subtask_plan(task, deliverable_type, context) for deliverable_type in requested_deliverables]
        deliverable_labels = ", ".join(plan.deliverable_type for plan in subtasks)
        return PlanSummary(
            summary=f"PM decomposed the request into capability-backed deliverables for {subject_label}: {deliverable_labels}.",
            subtasks=subtasks,
        )

    def _infer_subject(self, objective: str, details: str) -> str:
        text = f"{objective} {details}"
        lowered = text.lower()
        for phrase in ("capability registry", "context receipts", "context receipt", "compliance truth", "workflow repair"):
            if phrase in lowered:
                return phrase
        match = re.search(r"\b(mage|warrior|archer|healer)\b", text, flags=re.IGNORECASE)
        if match:
            return match.group(1)
        words = re.findall(r"[A-Za-z]+", objective)
        return words[-1] if words else "feature"

    def _slugify(self, text: str) -> str:
        return "-".join(part.lower() for part in re.findall(r"[A-Za-z0-9]+", text)) or "feature"

    def _format_spec_value(self, template: str, context: dict[str, str]) -> str:
        return template.format(**context)

    def _resolve_artifact_path(self, task: dict, spec: dict[str, Any], context: dict[str, str]) -> str:
        requested_output = (task.get("expected_artifact_path") or "").strip()
        if requested_output and spec["assigned_role"] == "Developer":
            return requested_output
        return self._format_spec_value(spec["artifact_template"], context)

    def _build_subtask_plan(self, task: dict, deliverable_type: str, context: dict[str, str]) -> SubtaskPlan:
        spec = get_deliverable_spec(task["project_name"], deliverable_type)
        artifact_path = self._resolve_artifact_path(task, spec, context)
        acceptance = AcceptanceCriteria(
            required_headings=[self._format_spec_value(item, context) for item in spec.get("required_headings", ())],
            required_keywords=[self._format_spec_value(item, context) for item in spec.get("required_keywords", ())],
            required_strings=[self._format_spec_value(item, context) for item in spec.get("required_strings", ())],
            python_compile=bool(spec.get("python_compile")),
            required_input_role=spec.get("required_input_role"),
            deliverable_contract=DeliverableContract(**spec["deliverable_contract"]) if spec.get("deliverable_contract") else None,
        )
        requested_tier = ((task.get("acceptance") or {}).get("tier_assignment") or {}).get("tier")
        assigned_tier = resolve_subtask_tier(assignee=spec["assigned_role"], requested_tier=requested_tier)
        output_format = infer_output_format(artifact_path)
        tier_assignment = (task.get("acceptance") or {}).get("tier_assignment") or {}
        default_lane = "background_api" if assigned_tier != "tier_3_junior" else "sync_api"
        execution_lane = str(tier_assignment.get("execution_lane") or default_lane)
        route_family = str(tier_assignment.get("route_family") or f"execution.{assigned_tier}.{output_format}.v1")
        cache_policy = dict(tier_assignment.get("cache_policy") or {})
        budget_policy = dict(tier_assignment.get("budget_policy") or {})
        acceptance.assigned_tier = assigned_tier
        acceptance.execution_lane = execution_lane
        acceptance.route_family = route_family
        acceptance.cache_policy = cache_policy
        acceptance.budget_policy = budget_policy
        acceptance.expected_output_format = output_format
        return SubtaskPlan(
            title=self._format_spec_value(spec["title_template"], context),
            assignee=spec["assigned_role"],
            deliverable_type=deliverable_type,
            objective=self._format_spec_value(spec["objective_template"], context),
            details=self._format_spec_value(spec["details_template"], context),
            expected_artifact_path=artifact_path,
            acceptance=acceptance,
            assigned_tier=assigned_tier,
            execution_lane=execution_lane,  # type: ignore[arg-type]
            route_family=route_family,
            expected_output_format=output_format,
            allowed_tools=list(spec.get("allowed_tools", ())),
            requires_dispatch_approval=bool(spec.get("requires_dispatch_approval")),
            category=spec.get("category", "Implementation"),
        )

    def _create_subtask(self, parent_task: dict, plan: SubtaskPlan) -> dict:
        acceptance = plan.acceptance.model_dump()
        acceptance["deliverable_type"] = plan.deliverable_type
        acceptance["allowed_tools"] = list(plan.allowed_tools)
        acceptance["assigned_tier"] = plan.assigned_tier
        acceptance["execution_lane"] = plan.execution_lane
        acceptance["route_family"] = plan.route_family
        acceptance["expected_output_format"] = plan.expected_output_format
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
            worker_result = await self._launch_worker_subtask(run_id=run_id, subtask=subtask, correction_notes=correction_notes)
            self._register_media_outputs(run_id=run_id, subtask=subtask, worker_result=worker_result, correction_notes=correction_notes)
            self.store.update_task(subtask["id"], status="in_review", owner_role="QA")
            if self.qa is None:
                raise ValueError("QA agent is required to review delegated worker artifacts.")
            review = await self.qa.review_artifact(run_id=run_id, task=subtask)
            if review.approved:
                self.store.update_task(
                    subtask["id"],
                    status="completed",
                    owner_role="QA",
                    review_notes=review.summary,
                    result_summary=review.summary,
                    review_state="Accepted",
                )
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

    def _summarize_worker_manifest(self, manifest: dict[str, Any]) -> dict[str, Any]:
        return {
            "manifest_version": manifest["manifest_version"],
            "execution_mode": manifest["execution_mode"],
            "run_id": manifest["run_id"],
            "task_id": manifest["task_id"],
            "project_name": manifest["project_name"],
            "role": manifest["role"],
            "runtime_mode": manifest["runtime_mode"],
            "write_scope": manifest["write_scope"],
            "expected_output_path": manifest["expected_output_path"],
            "allowed_write_paths": list(manifest["allowed_write_paths"]),
            "allowed_write_modes": list(manifest["allowed_write_modes"]),
            "input_artifact_paths": list(manifest["input_artifact_paths"]),
            "allowed_tools": list(manifest.get("allowed_tools", [])),
            "issued_by": manifest["issued_by"],
            "issued_at": manifest["issued_at"],
            "seal_sha256": manifest["seal_sha256"],
        }

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
            "allowed_tools": list((subtask.get("acceptance") or {}).get("allowed_tools", [])),
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
            "manifest": self._summarize_worker_manifest(manifest),
        }
        pending_sdk = team_state.get("pending_sdk_approval")
        if isinstance(pending_sdk, dict) and pending_sdk.get("task_id") == subtask["id"]:
            team_state.pop("pending_sdk_approval", None)
        self.store.update_run(run_id, team_state=team_state)
        self.store.save_context_receipt(
            run_id,
            {
                "active_lane": subtask["id"],
                "allowed_tools": manifest.get("allowed_tools", []),
                "allowed_paths": manifest.get("allowed_write_paths", []),
                "prior_artifact_paths": manifest.get("input_artifact_paths", []),
                "expected_output": manifest.get("expected_output_path"),
                "next_reviewer": "QA",
                "resume_conditions": [
                    "Resume the same specialist lane unless the continuity receipt changes materially.",
                    "Keep writes inside the approved manifest paths and tools.",
                ],
                "current_owner_role": subtask["owner_role"],
                "specialist_role": subtask["owner_role"],
            },
        )

    def _register_media_outputs(
        self,
        *,
        run_id: str,
        subtask: dict[str, Any],
        worker_result: dict[str, Any],
        correction_notes: str | None,
    ) -> None:
        artifact_path = str(worker_result.get("artifact_path") or subtask.get("expected_artifact_path") or "").strip()
        if not artifact_path:
            return
        normalized_path = artifact_path.replace("\\", "/")
        expected_prefix = f"projects/{subtask['project_name']}/artifacts/design/"
        if not normalized_path.startswith(expected_prefix):
            return
        provider, model = self._resolve_visual_output_model(subtask["owner_role"])
        metadata = {
            "registered_by": "Framework",
            "registration_mode": "deterministic",
            "service_family": "visual",
            "owner_role": subtask["owner_role"],
            "deliverable_type": (subtask.get("acceptance") or {}).get("deliverable_type"),
            "deliverable_contract_kind": ((subtask.get("acceptance") or {}).get("deliverable_contract") or {}).get("kind"),
            "runtime_mode": self._runtime_mode(run_id),
            "agent_run_id": worker_result.get("agent_run_id"),
            "worker_summary": worker_result.get("summary"),
        }
        provenance_fields = (
            "parent_visual_artifact_id",
            "lineage_root_visual_artifact_id",
            "locked_base_visual_artifact_id",
            "edit_session_id",
            "edit_intent",
            "edit_scope",
            "protected_regions",
            "mask_reference",
            "iteration_index",
        )
        propagation_kwargs = {
            field: worker_result[field]
            for field in provenance_fields
            if worker_result.get(field) is not None
        }
        visual_artifact = self.store.sync_visual_artifact(
            subtask["project_name"],
            subtask["id"],
            artifact_path=normalized_path,
            run_id=run_id,
            artifact_kind="image",
            provider=provider,
            model=model,
            prompt_summary=subtask.get("objective"),
            revised_prompt=correction_notes,
            review_state="pending_review",
            selected_direction=False,
            metadata=metadata,
            **propagation_kwargs,
        )
        self.store.record_trace_event(
            run_id,
            subtask["id"],
            "media_service_visual_registered",
            source="PM",
            summary="Framework registered the specialist visual output into canonical visual artifacts.",
            packet={
                "visual_artifact_id": visual_artifact["id"],
                "artifact_path": visual_artifact["artifact_path"],
                "review_state": visual_artifact["review_state"],
                "selected_direction": visual_artifact["selected_direction"],
                "agent_run_id": worker_result.get("agent_run_id"),
            },
            route={
                "runtime_role": "MediaService",
                "execution_mode": "deterministic",
                "service_family": "visual",
                "service_key": "artifact_indexing",
            },
            raw_json=visual_artifact,
        )

    def _resolve_visual_output_model(self, owner_role: str) -> tuple[str | None, str | None]:
        model_role = {
            "Architect": "architect",
            "Developer": "developer",
            "Design": "design",
            "QA": "qa",
        }.get(owner_role)
        if not model_role:
            return None, None
        return "openai", resolve_model(model_role)

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
        self.store.save_context_receipt(
            run_id,
            {
                "active_lane": subtask["id"],
                "allowed_tools": list((subtask.get("acceptance") or {}).get("allowed_tools", [])),
                "allowed_paths": [subtask["expected_artifact_path"]] if subtask.get("expected_artifact_path") else [],
                "expected_output": subtask.get("expected_artifact_path"),
                "next_reviewer": "Operator",
                "resume_conditions": [
                    "Dispatch approval is required before the specialist lane can continue.",
                ],
                "current_owner_role": assignee,
                "specialist_role": assignee,
            },
        )
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
