from __future__ import annotations

import asyncio
import json
from functools import partial
from pathlib import Path
from typing import Any

from autogen_core.models import SystemMessage, UserMessage
from autogen_ext.models.openai import OpenAIChatCompletionClient

from agents.api_router import APIRouter
from agents.config import create_model_client
from agents.config import resolve_model
from agents.config import role_floor_tier
from agents.cost_tracker import CostTracker
from intake.models import TaskPacket
from state_machine import default_state_for_role, determine_task_state
from wrappers.llm_wrapper import llm_call_async


class DelegatedExecutionBypassError(BaseException):
    pass


class StudioRoleAgent:
    def __init__(self, *, role_name: str, model_role: str, repo_root: str | Path, store, telemetry) -> None:
        self.role_name = role_name
        self.model_role = model_role
        self.repo_root = Path(repo_root)
        self.store = store
        self.telemetry = telemetry
        self.model_client = create_model_client(model_role)
        self._use_legacy_client = not isinstance(self.model_client, OpenAIChatCompletionClient)
        self._api_router: APIRouter | None = None
        self.cost_tracker = CostTracker(repo_root=self.repo_root, store=store)

    async def close(self) -> None:
        await self.model_client.close()

    async def generate_text(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        run_id: str | None = None,
        task_id: str | None = None,
        event_type: str = "agent_text",
    ) -> str:
        direct_tool_name = "api_responses_create" if self._delegated_work_requested(run_id=run_id, task_id=task_id) else "model_client.create"
        task_packet = self._enforce_task_packet_contract(task_id=task_id, tool_name=direct_tool_name)
        if self._delegated_work_requested(run_id=run_id, task_id=task_id):
            self._assert_api_router_authority(run_id=run_id, task_id=task_id)
            authority = self._ensure_delegated_execution_reservation(
                run_id=run_id,
                task_id=task_id,
                authority=self._resolve_authority_context(run_id=run_id, task_id=task_id),
            )
            routed = await asyncio.to_thread(
                partial(
                    self._get_api_router().invoke_text,
                    run_id=run_id,
                    task_id=task_id,
                    tier=self._resolve_execution_tier(task_id),
                    lane=self._resolve_execution_lane(task_id),
                    route_family=self._resolve_route_family(task_id),
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    source=self.role_name,
                    notes=f"{event_type} via StudioRoleAgent",
                    **authority,
                )
            )
            content = routed.output_text
            self._record(
                run_id=run_id,
                task_id=task_id,
                event_type=event_type,
                content=content,
                usage=routed,
                model=routed.model,
                usage_already_recorded=True,
            )
            return content
        self._assert_local_compatibility_path_allowed(run_id=run_id, task_id=task_id, task_packet=task_packet)
        result = await llm_call_async(
            self.role_name,
            self._resolve_task_state(task_id),
            [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            tool_name="model_client.create",
            repo_root=self.repo_root,
            metadata={
                "event_type": event_type,
                "task_id": task_id,
                "run_id": run_id,
                **self._task_packet_metadata(task_packet),
            },
            invoke_async=lambda prepared_messages: self._model_client_create(prepared_messages),
        )
        content = self._normalize_content(result.content)
        self._record(
            run_id=run_id,
            task_id=task_id,
            event_type=event_type,
            content=content,
            usage=getattr(result, "usage", None),
        )
        return content

    async def generate_json(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        schema,
        run_id: str | None = None,
        task_id: str | None = None,
        event_type: str = "agent_json",
    ):
        direct_tool_name = "api_responses_create" if self._delegated_work_requested(run_id=run_id, task_id=task_id) else "model_client.create"
        task_packet = self._enforce_task_packet_contract(task_id=task_id, tool_name=direct_tool_name)
        if self._delegated_work_requested(run_id=run_id, task_id=task_id):
            self._assert_api_router_authority(run_id=run_id, task_id=task_id)
            authority = self._ensure_delegated_execution_reservation(
                run_id=run_id,
                task_id=task_id,
                authority=self._resolve_authority_context(run_id=run_id, task_id=task_id),
            )
            parsed, routed = await asyncio.to_thread(
                partial(
                    self._get_api_router().invoke_json,
                    run_id=run_id,
                    task_id=task_id,
                    tier=self._resolve_execution_tier(task_id),
                    lane=self._resolve_execution_lane(task_id),
                    route_family=self._resolve_route_family(task_id),
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    schema=schema,
                    source=self.role_name,
                    **authority,
                )
            )
            self._record(
                run_id=run_id,
                task_id=task_id,
                event_type=event_type,
                content=routed.output_text,
                usage=routed,
                model=routed.model,
                usage_already_recorded=True,
            )
            return parsed
        self._assert_local_compatibility_path_allowed(run_id=run_id, task_id=task_id, task_packet=task_packet)
        result = await llm_call_async(
            self.role_name,
            self._resolve_task_state(task_id),
            [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            tool_name="model_client.create",
            repo_root=self.repo_root,
            metadata={
                "event_type": event_type,
                "task_id": task_id,
                "run_id": run_id,
                "json_output": True,
                **self._task_packet_metadata(task_packet),
            },
            invoke_async=lambda prepared_messages: self._model_client_create(prepared_messages, json_output=schema),
        )
        raw_content = self._normalize_content(result.content)
        try:
            parsed = schema.model_validate_json(raw_content)
        except Exception:
            parsed = schema.model_validate(json.loads(raw_content))
        self._record(
            run_id=run_id,
            task_id=task_id,
            event_type=event_type,
            content=raw_content,
            usage=getattr(result, "usage", None),
        )
        return parsed

    def _normalize_content(self, content: Any) -> str:
        if isinstance(content, str):
            return content.strip()
        return json.dumps(content, ensure_ascii=True, default=str)

    def _load_task_packet(self, task_id: str | None) -> TaskPacket | None:
        task = self.store.get_task(task_id) if task_id else None
        acceptance = (task or {}).get("acceptance") or {}
        raw_packet = acceptance.get("task_packet")
        if raw_packet is None:
            return None
        try:
            return TaskPacket.model_validate(raw_packet)
        except Exception as exc:
            raise RuntimeError(f"Invalid TaskPacket contract for {task_id}: {exc}") from exc

    def _enforce_task_packet_contract(self, *, task_id: str | None, tool_name: str) -> TaskPacket | None:
        task_packet = self._load_task_packet(task_id)
        if task_packet is None:
            return None
        if self.role_name not in task_packet.allowed_roles:
            raise RuntimeError(f"TaskPacket disallows role: {self.role_name}")
        if tool_name not in task_packet.allowed_tools:
            raise RuntimeError(f"TaskPacket disallows tool: {tool_name}")
        return task_packet

    def _task_packet_metadata(self, task_packet: TaskPacket | None) -> dict[str, Any]:
        if task_packet is None:
            return {}
        return {
            "task_packet_request_id": task_packet.request_id,
            "task_packet_token_budget": task_packet.token_budget.model_dump(),
        }

    def _task_packet_budget_authority(self, task_id: str | None):
        task_packet = self._load_task_packet(task_id)
        if task_packet is None:
            return None
        task = self.store.get_task(task_id) if task_id else None
        acceptance = (task or {}).get("acceptance") or {}
        budget = task_packet.token_budget
        declared_budget_max = acceptance.get("budget_max_tokens")
        if declared_budget_max is not None and int(declared_budget_max) != int(budget.max_total_tokens):
            raise RuntimeError(
                "Inconsistent governed budget authority: acceptance budget_max_tokens does not match TaskPacket.token_budget.max_total_tokens."
            )
        declared_retry_limit = acceptance.get("retry_limit")
        if declared_retry_limit is not None and int(declared_retry_limit) != int(budget.max_retries):
            raise RuntimeError(
                "Inconsistent governed budget authority: acceptance retry_limit does not match TaskPacket.token_budget.max_retries."
            )
        return budget

    def _assert_local_compatibility_path_allowed(
        self,
        *,
        run_id: str | None,
        task_id: str | None,
        task_packet: TaskPacket | None,
    ) -> None:
        if task_packet is None:
            return
        if not self._delegated_work_requested(run_id=run_id, task_id=task_id):
            raise RuntimeError(
                "TaskPacket-backed specialist execution requires tracked run_id and task_id routed through api_router; "
                "the local compatibility path is non-governed only."
            )

    async def _model_client_create(self, prepared_messages: list[dict[str, str]], json_output=None):
        model_messages = []
        for message in prepared_messages:
            role = str(message.get("role") or "user").lower()
            content = str(message.get("content") or "")
            if role == "system":
                model_messages.append(SystemMessage(content=content))
            else:
                model_messages.append(UserMessage(content=content, source=role))
        if json_output is not None:
            return await self.model_client.create(model_messages, json_output=json_output)
        return await self.model_client.create(model_messages)

    def _get_api_router(self) -> APIRouter:
        if self._api_router is None:
            self._api_router = APIRouter(repo_root=self.repo_root, store=self.store)
        return self._api_router

    def _ensure_delegated_execution_reservation(
        self,
        *,
        run_id: str | None,
        task_id: str | None,
        authority: dict[str, Any],
    ) -> dict[str, Any]:
        if not self._delegated_work_requested(run_id=run_id, task_id=task_id):
            return authority
        if not run_id or not task_id:
            raise RuntimeError("Delegated execution requires tracked run_id and task_id.")
        budget = self._task_packet_budget_authority(task_id)
        if budget is None:
            raise RuntimeError("Delegated execution requires TaskPacket token_budget authority.")
        reservation_id = str(authority.get("budget_reservation_id") or "").strip()
        priority_class = str(authority.get("priority_class") or "").strip()
        reserved_max_tokens = int(authority.get("budget_max_tokens") or 0)
        retry_limit = int(authority.get("retry_limit") or 0)
        if not reservation_id:
            raise RuntimeError("Delegated execution requires a budget_reservation_id.")
        if not priority_class:
            raise RuntimeError("Delegated execution requires a priority_class.")
        if reserved_max_tokens <= 0:
            raise RuntimeError("Delegated execution requires a positive budget_max_tokens cap.")
        if reserved_max_tokens != int(budget.max_total_tokens):
            raise RuntimeError(
                "Inconsistent governed budget authority: authority budget_max_tokens does not match TaskPacket.token_budget.max_total_tokens."
            )
        if retry_limit != int(budget.max_retries):
            raise RuntimeError(
                "Inconsistent governed budget authority: authority retry_limit does not match TaskPacket.token_budget.max_retries."
            )
        existing = self.store.get_execution_job_reservation(reservation_id)
        if existing is None:
            self.store.create_execution_job_reservation(
                job_id=reservation_id,
                priority_class=priority_class,
                reserved_max_tokens=int(budget.max_total_tokens),
                reservation_status="reserved",
                run_id=run_id,
                task_id=task_id,
            )
            return authority
        existing_priority = str(existing.get("priority_class") or "").strip()
        if existing_priority not in {"", priority_class}:
            raise RuntimeError(
                "Inconsistent governed budget authority: reservation priority_class does not match the packet authority."
            )
        if int(existing.get("reserved_max_tokens") or 0) != int(budget.max_total_tokens):
            raise RuntimeError(
                "Inconsistent governed budget authority: reservation reserved_max_tokens does not match TaskPacket.token_budget.max_total_tokens."
            )
        existing_run_id = existing.get("run_id")
        if existing_run_id not in {None, "", run_id}:
            raise RuntimeError("Delegated execution reservation is already bound to a different run.")
        existing_task_id = existing.get("task_id")
        if existing_task_id not in {None, "", task_id}:
            raise RuntimeError("Delegated execution reservation is already bound to a different task.")
        self.store.update_execution_job_reservation(
            reservation_id,
            run_id=run_id,
            task_id=task_id,
        )
        return authority

    def _should_use_api_router(self, *, run_id: str | None, task_id: str | None) -> bool:
        return bool(run_id and task_id and not self._use_legacy_client)

    def _delegated_work_requested(self, *, run_id: str | None, task_id: str | None) -> bool:
        return bool(run_id and task_id)

    def _assert_api_router_authority(self, *, run_id: str | None, task_id: str | None) -> None:
        if self._should_use_api_router(run_id=run_id, task_id=task_id):
            return
        raise DelegatedExecutionBypassError(
            "Delegated work must route through api_router; direct StudioRoleAgent execution is disabled."
        )

    def _resolve_execution_tier(self, task_id: str | None) -> str:
        task = self.store.get_task(task_id) if task_id else None
        acceptance = (task or {}).get("acceptance") or {}
        assigned_tier = acceptance.get("assigned_tier")
        if isinstance(assigned_tier, str) and assigned_tier:
            return assigned_tier
        tier_assignment = acceptance.get("tier_assignment") or {}
        tier = tier_assignment.get("tier")
        if isinstance(tier, str) and tier:
            return tier
        return role_floor_tier(self.role_name)

    def _resolve_execution_lane(self, task_id: str | None) -> str:
        task = self.store.get_task(task_id) if task_id else None
        acceptance = (task or {}).get("acceptance") or {}
        lane = acceptance.get("execution_lane")
        if isinstance(lane, str) and lane:
            return lane
        tier_assignment = acceptance.get("tier_assignment") or {}
        lane = tier_assignment.get("execution_lane")
        if isinstance(lane, str) and lane:
            return lane
        return "sync_api"

    def _resolve_route_family(self, task_id: str | None) -> str | None:
        task = self.store.get_task(task_id) if task_id else None
        acceptance = (task or {}).get("acceptance") or {}
        route_family = acceptance.get("route_family")
        if isinstance(route_family, str) and route_family:
            return route_family
        tier_assignment = acceptance.get("tier_assignment") or {}
        route_family = tier_assignment.get("route_family")
        if isinstance(route_family, str) and route_family:
            return route_family
        return None

    def _resolve_task_state(self, task_id: str | None) -> str:
        task = self.store.get_task(task_id) if task_id else None
        if task is not None:
            return determine_task_state(task)
        return default_state_for_role(self.role_name)

    def _resolve_authority_context(self, *, run_id: str | None, task_id: str | None) -> dict[str, Any]:
        task = self.store.get_task(task_id) if task_id else None
        acceptance = (task or {}).get("acceptance") or {}
        budget = self._task_packet_budget_authority(task_id)
        priority_class = acceptance.get("priority_class") or (task or {}).get("priority_class") or (task or {}).get("priority") or "medium"
        job_id = run_id or task_id or f"{self.role_name.lower()}-job"
        packet_id = task_id or run_id or f"{self.role_name.lower()}-packet"
        return {
            "authority_packet_id": str(acceptance.get("authority_packet_id") or packet_id),
            "authority_job_id": str(acceptance.get("authority_job_id") or job_id),
            "authority_token": str(
                acceptance.get("authority_token") or f"{job_id}:{packet_id}:{self.role_name}"
            ),
            "authority_schema_name": str(acceptance.get("authority_schema_name") or "execution_contract_v1"),
            "authority_execution_tier": str(
                acceptance.get("authority_execution_tier") or self._resolve_execution_tier(task_id)
            ),
            "authority_execution_lane": str(
                acceptance.get("authority_execution_lane") or self._resolve_execution_lane(task_id)
            ),
            "authority_delegated_work": True,
            "priority_class": str(priority_class),
            "budget_max_tokens": int(
                budget.max_total_tokens
                if budget is not None
                else (acceptance.get("budget_max_tokens") or (task or {}).get("budget_max_tokens") or 4096)
            ),
            "budget_reservation_id": str(
                acceptance.get("budget_reservation_id") or (task or {}).get("budget_reservation_id") or f"{job_id}:reservation"
            ),
            "retry_limit": int(
                budget.max_retries
                if budget is not None
                else (acceptance.get("retry_limit") or (task or {}).get("retry_limit") or 1)
            ),
            "early_stop_rule": str(
                acceptance.get("early_stop_rule")
                or (task or {}).get("early_stop_rule")
                or ("single_pass_only" if budget is not None and budget.max_retries == 0 else "stop_on_first_success")
            ),
        }

    def _usage_counts(self, usage: Any) -> tuple[int | None, int | None]:
        if usage is None:
            return None, None
        prompt_tokens = getattr(usage, "prompt_tokens", None)
        completion_tokens = getattr(usage, "completion_tokens", None)
        if prompt_tokens is None:
            prompt_tokens = getattr(usage, "input_tokens", None)
        if completion_tokens is None:
            completion_tokens = getattr(usage, "output_tokens", None)
        if isinstance(usage, dict):
            prompt_tokens = usage.get("prompt_tokens", usage.get("input_tokens", prompt_tokens))
            completion_tokens = usage.get("completion_tokens", usage.get("output_tokens", completion_tokens))
        return (
            int(prompt_tokens) if prompt_tokens is not None else None,
            int(completion_tokens) if completion_tokens is not None else None,
        )

    def _record(
        self,
        *,
        run_id: str | None,
        task_id: str | None,
        event_type: str,
        content: str,
        usage: Any,
        model: str | None = None,
        usage_already_recorded: bool = False,
    ) -> None:
        prompt_tokens, completion_tokens = self._usage_counts(usage)
        resolved_model = model or resolve_model(self.model_role)
        payload = {
            "role": self.role_name,
            "model_role": self.model_role,
            "model": resolved_model,
            "content": content,
        }
        if run_id and task_id:
            self.store.record_message(
                run_id,
                task_id,
                event_type,
                payload,
                source=self.role_name,
                prompt_tokens=None if usage_already_recorded else prompt_tokens,
                completion_tokens=None if usage_already_recorded else completion_tokens,
            )
            if prompt_tokens is not None and completion_tokens is not None and not usage_already_recorded:
                estimate = self.cost_tracker.estimate_cost(
                    resolved_model,
                    {
                        "input_tokens": int(prompt_tokens),
                        "output_tokens": int(completion_tokens),
                        "input_tokens_details": {"cached_tokens": 0},
                        "output_tokens_details": {"reasoning_tokens": 0},
                    },
                )
                self.cost_tracker._append_markdown_log(
                    run_id=run_id,
                    task_id=task_id,
                    source=self.role_name,
                    model=resolved_model,
                    tier=role_floor_tier(self.role_name),
                    artifact_path=None,
                    notes=f"{event_type} via StudioRoleAgent",
                    estimate=estimate,
                )
        self.telemetry.append_event(
            event_type,
            {
                "run_id": run_id,
                "task_id": task_id,
                "source": self.role_name,
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "payload": payload,
            },
        )
