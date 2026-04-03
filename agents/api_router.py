from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from openai import APIConnectionError, APITimeoutError, InternalServerError, OpenAI, RateLimitError
from pydantic import BaseModel, Field

from agents.config import require_api_key, resolve_tier_channel, resolve_tier_model, resolve_tier_reasoning_effort
from agents.cost_tracker import CostTracker
from runtime import create_runtime
from skills.tools import write_project_artifact
from state_machine import default_state_for_role, determine_task_state
from wrappers.llm_wrapper import llm_call


class APIRouterError(RuntimeError):
    pass


class RoutedAPIResult(BaseModel):
    tier: str
    channel: str
    lane: str
    model: str
    reasoning_effort: str
    route_family: str | None = None
    output_text: str
    response_id: str | None = None
    artifact_path: str | None = None
    input_tokens: int = 0
    cached_input_tokens: int = 0
    output_tokens: int = 0
    reasoning_tokens: int = 0
    estimated_cost_usd: float = 0.0
    raw_usage: dict[str, Any] = Field(default_factory=dict)


class APIRouter:
    _DELEGATED_REQUIRED_FIELDS = (
        "authority_packet_id",
        "authority_job_id",
        "authority_token",
        "authority_schema_name",
        "authority_execution_tier",
        "authority_execution_lane",
        "authority_delegated_work",
        "priority_class",
        "budget_max_tokens",
        "budget_reservation_id",
        "retry_limit",
        "early_stop_rule",
    )
    _EARLY_STOP_RULES = {"stop_on_first_success", "single_pass_only"}
    _ACTIVE_RESERVATION_STATUSES = {"reserved", "active"}

    def __init__(
        self,
        repo_root: str | Path,
        *,
        client: OpenAI | None = None,
        store=None,
        cost_tracker: CostTracker | None = None,
        max_retries: int = 2,
    ) -> None:
        self.repo_root = Path(repo_root).resolve()
        self.client = client or OpenAI(api_key=require_api_key())
        self.runtime = create_runtime("openai", client=self.client)
        self.cost_tracker = cost_tracker or CostTracker(repo_root=self.repo_root, store=store)
        self.max_retries = max_retries

    def resolve_route(self, tier: str) -> dict[str, str]:
        return {
            "tier": tier,
            "channel": resolve_tier_channel(tier),
            "model": resolve_tier_model(tier),
            "reasoning_effort": resolve_tier_reasoning_effort(tier),
        }

    def invoke_text(
        self,
        *,
        run_id: str,
        task_id: str,
        tier: str,
        system_prompt: str,
        user_prompt: str,
        source: str,
        lane: str = "sync_api",
        route_family: str | None = None,
        artifact_path: str | None = None,
        notes: str | None = None,
        metadata: dict[str, str] | None = None,
        background: bool | None = None,
        authority_packet_id: str | None = None,
        authority_job_id: str | None = None,
        authority_token: str | None = None,
        authority_schema_name: str | None = None,
        authority_execution_tier: str | None = None,
        authority_execution_lane: str | None = None,
        authority_delegated_work: bool = False,
        priority_class: str | None = None,
        budget_max_tokens: int | None = None,
        budget_reservation_id: str | None = None,
        retry_limit: int | None = None,
        early_stop_rule: str | None = None,
    ) -> RoutedAPIResult:
        self._validate_delegated_authority(
            authority_delegated_work=authority_delegated_work,
            authority_packet_id=authority_packet_id,
            authority_job_id=authority_job_id,
            authority_token=authority_token,
            authority_schema_name=authority_schema_name,
            authority_execution_tier=authority_execution_tier,
            authority_execution_lane=authority_execution_lane,
            priority_class=priority_class,
            budget_max_tokens=budget_max_tokens,
            budget_reservation_id=budget_reservation_id,
            retry_limit=retry_limit,
            early_stop_rule=early_stop_rule,
        )
        route = self.resolve_route(tier)
        use_background = background if background is not None else lane == "background_api"
        delegated = bool(authority_delegated_work)
        retry_cap = self._delegated_retry_cap(retry_limit)
        early_stop_mode = self._normalize_early_stop_rule(early_stop_rule)
        request_metadata = dict(metadata or {})
        request_metadata.setdefault("execution_lane", lane)
        if route_family:
            request_metadata.setdefault("route_family", route_family)
        if delegated:
            reservation = self._require_active_budget_reservation(
                run_id=run_id,
                task_id=task_id,
                authority_job_id=authority_job_id,
                budget_reservation_id=budget_reservation_id,
                budget_max_tokens=budget_max_tokens,
                priority_class=priority_class,
            )
            self._sync_execution_job_reservation(
                reservation=reservation,
                run_id=run_id,
                task_id=task_id,
            )
            self._sync_execution_packet(
                run_id=run_id,
                task_id=task_id,
                authority_packet_id=authority_packet_id,
                authority_job_id=authority_job_id,
                authority_token=authority_token,
                authority_schema_name=authority_schema_name,
                authority_execution_tier=authority_execution_tier,
                authority_execution_lane=authority_execution_lane,
                authority_delegated_work=True,
                priority_class=priority_class,
                budget_max_tokens=budget_max_tokens,
                budget_reservation_id=budget_reservation_id,
                retry_limit=retry_cap,
                early_stop_rule=early_stop_mode,
                actual_total_tokens=0,
                retry_count=0,
                escalation_target=None,
                stop_reason=None,
                status="running",
            )
        last_error: Exception | None = None
        max_attempts = 1 if early_stop_mode == "single_pass_only" else retry_cap + 1
        for attempt in range(max_attempts):
            try:
                response = llm_call(
                    source,
                    self._resolve_task_state(task_id=task_id, role=source),
                    [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    tool_name="api_responses_create",
                    repo_root=self.repo_root,
                    metadata={
                        "run_id": run_id,
                        "task_id": task_id,
                        "tier": tier,
                        "lane": lane,
                        "route_family": route_family,
                    },
                    invoke=lambda prepared_messages: self.runtime.invoke(
                        model=route["model"],
                        messages=prepared_messages,
                        reasoning_effort=route["reasoning_effort"],
                        metadata=request_metadata,
                        background=use_background,
                    ),
                )
                output_text = self._extract_output_text(response)
                written_path = None
                if artifact_path:
                    write_project_artifact(artifact_path, output_text)
                    written_path = artifact_path
                usage = self._usage_payload(response)
                estimate = self.cost_tracker.record_api_usage(
                    run_id=run_id,
                    task_id=task_id,
                    source=source,
                    model=route["model"],
                    tier=tier,
                    lane=lane,
                    usage=usage,
                    artifact_path=written_path,
                    notes=notes,
                )
                actual_total_tokens = self._actual_total_tokens(estimate)
                if delegated:
                    self._sync_execution_packet(
                        run_id=run_id,
                        task_id=task_id,
                        authority_packet_id=authority_packet_id,
                        authority_job_id=authority_job_id,
                        authority_token=authority_token,
                        authority_schema_name=authority_schema_name,
                        authority_execution_tier=authority_execution_tier,
                        authority_execution_lane=authority_execution_lane,
                        authority_delegated_work=True,
                        priority_class=priority_class,
                        budget_max_tokens=budget_max_tokens,
                        budget_reservation_id=budget_reservation_id,
                        retry_limit=retry_cap,
                        early_stop_rule=early_stop_mode,
                        actual_total_tokens=actual_total_tokens,
                        retry_count=attempt,
                        escalation_target=None,
                        stop_reason=self._success_stop_reason(early_stop_mode),
                        status="completed",
                    )
                return RoutedAPIResult(
                    tier=tier,
                    channel=route["channel"],
                    lane=lane,
                    model=route["model"],
                    reasoning_effort=route["reasoning_effort"],
                    route_family=route_family,
                    output_text=output_text,
                    response_id=getattr(response, "id", None),
                    artifact_path=written_path,
                    input_tokens=estimate.input_tokens,
                    cached_input_tokens=estimate.cached_input_tokens,
                    output_tokens=estimate.output_tokens,
                    reasoning_tokens=estimate.reasoning_tokens,
                    estimated_cost_usd=estimate.estimated_cost_usd,
                    raw_usage=usage,
                )
            except Exception as exc:
                last_error = exc
                should_retry = attempt < max_attempts - 1 and self.should_retry(exc)
                if delegated:
                    self._sync_execution_packet(
                        run_id=run_id,
                        task_id=task_id,
                        authority_packet_id=authority_packet_id,
                        authority_job_id=authority_job_id,
                        authority_token=authority_token,
                        authority_schema_name=authority_schema_name,
                        authority_execution_tier=authority_execution_tier,
                        authority_execution_lane=authority_execution_lane,
                        authority_delegated_work=True,
                        priority_class=priority_class,
                        budget_max_tokens=budget_max_tokens,
                        budget_reservation_id=budget_reservation_id,
                        retry_limit=retry_cap,
                        early_stop_rule=early_stop_mode,
                        actual_total_tokens=0,
                        retry_count=attempt + 1 if should_retry else attempt,
                        escalation_target=self._escalation_target_for_tier(tier) if not should_retry else None,
                        stop_reason=self._failure_stop_reason(
                            exc,
                            early_stop_mode=early_stop_mode,
                            retrying=should_retry,
                            retry_cap=retry_cap,
                            attempt=attempt,
                        ),
                        status="retrying" if should_retry else ("stopped" if early_stop_mode == "single_pass_only" else "failed"),
                    )
                if not should_retry:
                    break
                time.sleep(0.5 * (attempt + 1))
        raise APIRouterError(str(last_error or "API routing failed."))

    def invoke_json(
        self,
        *,
        run_id: str,
        task_id: str,
        tier: str,
        system_prompt: str,
        user_prompt: str,
        source: str,
        lane: str = "sync_api",
        route_family: str | None = None,
        schema=None,
        metadata: dict[str, str] | None = None,
        background: bool | None = None,
        authority_packet_id: str | None = None,
        authority_job_id: str | None = None,
        authority_token: str | None = None,
        authority_schema_name: str | None = None,
        authority_execution_tier: str | None = None,
        authority_execution_lane: str | None = None,
        authority_delegated_work: bool = False,
        priority_class: str | None = None,
        budget_max_tokens: int | None = None,
        budget_reservation_id: str | None = None,
        retry_limit: int | None = None,
        early_stop_rule: str | None = None,
    ) -> tuple[Any, RoutedAPIResult]:
        result = self.invoke_text(
            run_id=run_id,
            task_id=task_id,
            tier=tier,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            source=source,
            lane=lane,
            route_family=route_family,
            metadata=metadata,
            background=background,
            authority_packet_id=authority_packet_id,
            authority_job_id=authority_job_id,
            authority_token=authority_token,
            authority_schema_name=authority_schema_name,
            authority_execution_tier=authority_execution_tier,
            authority_execution_lane=authority_execution_lane,
            authority_delegated_work=authority_delegated_work,
            priority_class=priority_class,
            budget_max_tokens=budget_max_tokens,
            budget_reservation_id=budget_reservation_id,
            retry_limit=retry_limit,
            early_stop_rule=early_stop_rule,
        )
        try:
            payload = json.loads(result.output_text)
        except json.JSONDecodeError as exc:
            raise APIRouterError(f"API router expected strict JSON but received: {result.output_text}") from exc
        if schema is not None:
            return schema.model_validate(payload), result
        return payload, result

    def should_retry(self, exc: Exception) -> bool:
        return isinstance(exc, (RateLimitError, APITimeoutError, APIConnectionError, InternalServerError))

    def _delegated_retry_cap(self, retry_limit: int | None) -> int:
        if retry_limit is None:
            return max(self.max_retries, 0)
        return max(0, min(self.max_retries, int(retry_limit)))

    def _normalize_early_stop_rule(self, early_stop_rule: str | None) -> str:
        rule = (early_stop_rule or "").strip()
        return rule if rule in self._EARLY_STOP_RULES else rule

    def _success_stop_reason(self, early_stop_mode: str) -> str:
        return early_stop_mode or "success"

    def _failure_stop_reason(
        self,
        exc: Exception,
        *,
        early_stop_mode: str,
        retrying: bool,
        retry_cap: int,
        attempt: int,
    ) -> str | None:
        if retrying:
            return None
        if early_stop_mode == "single_pass_only":
            return "single_pass_only"
        if attempt >= retry_cap:
            return "retry_limit_exceeded"
        return exc.__class__.__name__

    def _escalation_target_for_tier(self, tier: str) -> str | None:
        return {
            "tier_3_junior": "tier_2_mid",
            "tier_2_mid": "tier_1_senior",
        }.get(tier)

    def _actual_total_tokens(self, estimate: Any) -> int:
        return int(getattr(estimate, "input_tokens", 0)) + int(getattr(estimate, "output_tokens", 0)) + int(getattr(estimate, "reasoning_tokens", 0))

    def _sync_execution_packet(
        self,
        *,
        run_id: str,
        task_id: str,
        authority_packet_id: str | None,
        authority_job_id: str | None,
        authority_token: str | None,
        authority_schema_name: str | None,
        authority_execution_tier: str | None,
        authority_execution_lane: str | None,
        authority_delegated_work: bool,
        priority_class: str | None,
        budget_max_tokens: int | None,
        budget_reservation_id: str | None,
        retry_limit: int | None,
        early_stop_rule: str | None,
        actual_total_tokens: int,
        retry_count: int,
        escalation_target: str | None,
        stop_reason: str | None,
        status: str,
    ) -> None:
        if not authority_delegated_work:
            return
        self.cost_tracker.store.sync_execution_packet(
            authority_packet_id=authority_packet_id or "",
            authority_job_id=authority_job_id or "",
            authority_token=authority_token or "",
            authority_schema_name=authority_schema_name or "",
            authority_execution_tier=authority_execution_tier or "",
            authority_execution_lane=authority_execution_lane or "",
            authority_delegated_work=True,
            priority_class=priority_class or "",
            budget_max_tokens=int(budget_max_tokens or 0),
            budget_reservation_id=budget_reservation_id,
            retry_limit=int(retry_limit or 0),
            early_stop_rule=early_stop_rule or "",
            run_id=run_id,
            task_id=task_id,
            actual_total_tokens=int(actual_total_tokens),
            retry_count=int(retry_count),
            escalation_target=escalation_target,
            stop_reason=stop_reason,
            status=status,
        )

    def _sync_execution_job_reservation(
        self,
        *,
        reservation: dict[str, Any],
        run_id: str,
        task_id: str,
    ) -> None:
        store = getattr(self.cost_tracker, "store", None)
        if store is None:
            raise APIRouterError("Delegated execution requires store-backed reservation tracking.")
        store.sync_execution_job_reservation(
            job_id=str(reservation["job_id"]),
            priority_class=str(reservation["priority_class"]),
            reserved_max_tokens=int(reservation["reserved_max_tokens"]),
            reservation_status=str(reservation["reservation_status"]),
            run_id=run_id,
            task_id=task_id,
        )

    def _require_active_budget_reservation(
        self,
        *,
        run_id: str,
        task_id: str,
        authority_job_id: str | None,
        budget_reservation_id: str | None,
        budget_max_tokens: int | None,
        priority_class: str | None,
    ) -> dict[str, Any]:
        store = getattr(self.cost_tracker, "store", None)
        if store is None:
            raise APIRouterError("Delegated execution requires store-backed reservation tracking.")
        reservation_key = (budget_reservation_id or "").strip()
        if not reservation_key:
            raise APIRouterError(
                "Delegated execution requires an active budget reservation before job start."
            )
        reservation = store.get_execution_job_reservation(reservation_key)
        if reservation is None:
            raise APIRouterError(
                f"Delegated execution requires an active budget reservation before job start: {reservation_key}."
            )
        reservation_status = str(reservation.get("reservation_status") or "").strip()
        if reservation_status not in self._ACTIVE_RESERVATION_STATUSES:
            raise APIRouterError(
                f"Delegated execution requires an active budget reservation before job start: "
                f"{reservation_key} is {reservation_status or 'missing'}."
            )
        reserved_max_tokens = int(reservation.get("reserved_max_tokens") or 0)
        requested_max_tokens = int(budget_max_tokens or 0)
        if reserved_max_tokens <= 0:
            raise APIRouterError(
                f"Delegated execution requires a positive reserved token cap before job start: {reservation_key}."
            )
        if requested_max_tokens > reserved_max_tokens:
            raise APIRouterError(
                f"Delegated execution budget exceeds active reservation: requested {requested_max_tokens}, "
                f"reserved {reserved_max_tokens}."
            )
        packet_job_id = (authority_job_id or "").strip()
        if not packet_job_id:
            raise APIRouterError("Delegated execution requires a valid authority_job_id.")
        if priority_class and str(reservation.get("priority_class") or "").strip() not in {"", priority_class}:
            raise APIRouterError(
                f"Delegated execution reservation priority does not match the packet priority: "
                f"{reservation.get('priority_class')} != {priority_class}."
            )
        return reservation

    def _validate_delegated_authority(
        self,
        *,
        authority_delegated_work: bool,
        authority_packet_id: str | None,
        authority_job_id: str | None,
        authority_token: str | None,
        authority_schema_name: str | None,
        authority_execution_tier: str | None,
        authority_execution_lane: str | None,
        priority_class: str | None,
        budget_max_tokens: int | None,
        budget_reservation_id: str | None,
        retry_limit: int | None,
        early_stop_rule: str | None,
    ) -> None:
        if not authority_delegated_work:
            return

        def _missing(field: str, value: Any) -> bool:
            if value is None:
                return True
            if isinstance(value, str):
                return not value.strip()
            return False

        missing = []
        for field, value in (
            ("authority_packet_id", authority_packet_id),
            ("authority_job_id", authority_job_id),
            ("authority_token", authority_token),
            ("authority_schema_name", authority_schema_name),
            ("authority_execution_tier", authority_execution_tier),
            ("authority_execution_lane", authority_execution_lane),
            ("priority_class", priority_class),
            ("budget_max_tokens", budget_max_tokens),
            ("budget_reservation_id", budget_reservation_id),
            ("retry_limit", retry_limit),
            ("early_stop_rule", early_stop_rule),
        ):
            if _missing(field, value):
                missing.append(field)

        if missing:
            required = ", ".join(self._DELEGATED_REQUIRED_FIELDS)
            raise APIRouterError(
                "Delegated execution packet is missing required authority/control fields: "
                f"{', '.join(missing)}. Required fields: {required}."
            )

    def _extract_output_text(self, response: Any) -> str:
        output_text = getattr(response, "output_text", None)
        if isinstance(output_text, str) and output_text.strip():
            return output_text.strip()
        outputs = getattr(response, "output", None) or []
        for item in outputs:
            if isinstance(item, dict):
                content = item.get("content", [])
            else:
                content = getattr(item, "content", None) or []
            for chunk in content:
                chunk_type = getattr(chunk, "type", None) or (chunk.get("type") if isinstance(chunk, dict) else None)
                if chunk_type == "output_text":
                    text = getattr(chunk, "text", None) or chunk.get("text")
                    if isinstance(text, str) and text.strip():
                        return text.strip()
        raise APIRouterError("API router received no output_text payload.")

    def _usage_payload(self, response: Any) -> dict[str, Any]:
        usage = getattr(response, "usage", None)
        if isinstance(usage, dict):
            return usage
        if usage is None:
            return {}
        input_details = getattr(usage, "input_tokens_details", None)
        output_details = getattr(usage, "output_tokens_details", None)
        return {
            "input_tokens": getattr(usage, "input_tokens", 0),
            "input_tokens_details": {
                "cached_tokens": getattr(input_details, "cached_tokens", 0) if input_details is not None else 0,
            },
            "output_tokens": getattr(usage, "output_tokens", 0),
            "output_tokens_details": {
                "reasoning_tokens": getattr(output_details, "reasoning_tokens", 0) if output_details is not None else 0,
            },
        }

    def _resolve_task_state(self, *, task_id: str | None, role: str) -> str:
        store = getattr(self.cost_tracker, "store", None)
        if store is not None and task_id:
            task = store.get_task(task_id)
            if task is not None:
                return determine_task_state(task)
        return default_state_for_role(role)
