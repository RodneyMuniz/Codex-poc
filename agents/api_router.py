from __future__ import annotations

import hashlib
import json
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from openai import APIConnectionError, APITimeoutError, InternalServerError, OpenAI, RateLimitError
from pydantic import BaseModel, Field

from agents.config import require_api_key, resolve_tier_channel, resolve_tier_model, resolve_tier_reasoning_effort
from agents.cost_tracker import CostTracker
from governance.rules import check_prompt, check_role, check_tool_access, load_policies
from intake.models import TaskPacket
from sessions.governed_external_observability import determine_claim_status, determine_proof_status
from runtime import create_runtime
from skills.tools import write_project_artifact
from state_machine import default_state_for_role, determine_task_state
from wrappers.llm_wrapper import llm_call


class APIRouterError(RuntimeError):
    pass


class BudgetAuthorityExceededError(APIRouterError):
    def __init__(self, message: str, *, actual_total_tokens: int, stop_reason: str) -> None:
        super().__init__(message)
        self.actual_total_tokens = int(actual_total_tokens)
        self.stop_reason = stop_reason


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
        budget_authority = None
        governed_task_packet = None
        reservation = None
        request_metadata = dict(metadata or {})
        request_metadata.setdefault("execution_lane", lane)
        if route_family:
            request_metadata.setdefault("route_family", route_family)
        if delegated:
            observability_correlation = self._require_governed_external_observability_correlation(
                run_id=run_id,
                task_id=task_id,
                task_packet_id=None,
                reservation_id=str(budget_reservation_id or ""),
                authority_packet_id=str(authority_packet_id or ""),
                source_component="APIRouter",
            )
            run_id = observability_correlation["run_id"]
            task_id = observability_correlation["task_id"]
            authority_packet_id = observability_correlation["authority_packet_id"]
            budget_reservation_id = observability_correlation["reservation_id"]
            governed_task_packet = self._load_governed_task_packet(task_id=task_id)
            budget_authority = governed_task_packet.token_budget
            observability_correlation = self._require_governed_external_observability_correlation(
                run_id=run_id,
                task_id=task_id,
                task_packet_id=governed_task_packet.request_id,
                reservation_id=str(budget_reservation_id or ""),
                authority_packet_id=str(authority_packet_id or ""),
                source_component="APIRouter",
            )
            run_id = observability_correlation["run_id"]
            task_id = observability_correlation["task_id"]
            authority_packet_id = observability_correlation["authority_packet_id"]
            budget_reservation_id = observability_correlation["reservation_id"]
            self._validate_task_packet_budget_authority(
                budget_authority=budget_authority,
                budget_max_tokens=budget_max_tokens,
                retry_limit=retry_limit,
            )
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
            external_call_context: dict[str, Any] | None = None
            try:
                if delegated:
                    self._precheck_governed_pre_observation_blockers(
                        run_id=run_id,
                        task_id=task_id,
                        task_packet_id=governed_task_packet.request_id if governed_task_packet is not None else None,
                        authority_packet_id=authority_packet_id,
                        role=source,
                        task_state=self._resolve_task_state(task_id=task_id, role=source),
                        messages=(system_prompt, user_prompt),
                        tool_name="api_responses_create",
                    )
                    external_call_context = self._start_governed_external_call_observation(
                        run_id=run_id,
                        task_id=task_id,
                        task_packet_id=governed_task_packet.request_id if governed_task_packet is not None else "",
                        reservation_id=str(budget_reservation_id or ""),
                        authority_packet_id=str(authority_packet_id or ""),
                        provider="openai",
                        model=route["model"],
                        execution_path="governed_api",
                        lane=lane,
                        route_family=route_family,
                        tier=tier,
                        source_component="APIRouter",
                        attempt=attempt,
                        reservation_status=str((reservation or {}).get("reservation_status") or ""),
                        budget_authority=budget_authority,
                        retry_limit=retry_cap,
                        retry_count=attempt,
                    )
                def _invoke_provider(prepared_messages):
                    if delegated and external_call_context is not None:
                        self._mark_governed_external_api_boundary_reached(external_call_context)
                    return self.runtime.invoke(
                        model=route["model"],
                        messages=prepared_messages,
                        reasoning_effort=route["reasoning_effort"],
                        metadata=request_metadata,
                        background=use_background,
                    )
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
                    invoke=_invoke_provider,
                )
                output_text = self._extract_output_text(response)
                usage = self._usage_payload(response)
                provider_request_id = self._provider_request_id(response)
                if delegated and external_call_context is not None:
                    if provider_request_id is not None:
                        self._capture_governed_external_provider_metadata(
                            external_call_context,
                            provider_request_id=provider_request_id,
                            provider="openai",
                            model=route["model"],
                        )
                    else:
                        self._emit_governed_external_proof_missing(
                            external_call_context,
                            reason_code="provider_request_id_missing",
                            data={"provider": "openai", "model": route["model"]},
                        )
                if delegated and budget_authority is not None:
                    if external_call_context is not None:
                        self._record_governed_external_budget_check(
                            external_call_context,
                            usage=usage,
                            retry_count=attempt,
                        )
                    exceeded_message, exceeded_stop_reason = self._budget_authority_exceeded(
                        usage=usage,
                        budget_authority=budget_authority,
                    )
                    if exceeded_message is not None and exceeded_stop_reason is not None:
                        estimate = self.cost_tracker.record_api_usage(
                            run_id=run_id,
                            task_id=task_id,
                            source=source,
                            model=route["model"],
                            tier=tier,
                            lane=lane,
                            usage=usage,
                            artifact_path=None,
                            notes=exceeded_message,
                        )
                        raise BudgetAuthorityExceededError(
                            exceeded_message,
                            actual_total_tokens=self._actual_total_tokens(estimate),
                            stop_reason=exceeded_stop_reason,
                        )
                written_path = None
                if artifact_path:
                    write_project_artifact(artifact_path, output_text)
                    written_path = artifact_path
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
                    if external_call_context is not None:
                        self._finish_governed_external_call(
                            external_call_context,
                            outcome_status="completed",
                            reason_code=self._success_stop_reason(early_stop_mode),
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
                    actual_total_tokens = int(getattr(exc, "actual_total_tokens", 0) or 0)
                    explicit_stop_reason = getattr(exc, "stop_reason", None)
                    resolved_stop_reason = (
                        explicit_stop_reason
                        if explicit_stop_reason is not None and not should_retry
                        else self._failure_stop_reason(
                            exc,
                            early_stop_mode=early_stop_mode,
                            retrying=should_retry,
                            retry_cap=retry_cap,
                            attempt=attempt,
                        )
                    )
                    if external_call_context is not None:
                        if should_retry:
                            self._emit_governed_external_budget_retry_incremented(
                                external_call_context,
                                retry_count=attempt + 1,
                                error_type=exc.__class__.__name__,
                            )
                        elif self._is_governed_budget_stop_reason(resolved_stop_reason):
                            self._emit_governed_external_budget_stop_enforced(
                                external_call_context,
                                stop_reason=resolved_stop_reason or exc.__class__.__name__,
                                retry_count=attempt,
                            )
                        self._emit_governed_external_proof_missing(
                            external_call_context,
                            reason_code="provider_metadata_unavailable",
                            data={"error_type": exc.__class__.__name__},
                        )
                        self._finish_governed_external_call(
                            external_call_context,
                            outcome_status="retrying" if should_retry else "failed",
                            reason_code=str(resolved_stop_reason or exc.__class__.__name__),
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
                        actual_total_tokens=actual_total_tokens,
                        retry_count=attempt + 1 if should_retry else attempt,
                        escalation_target=self._escalation_target_for_tier(tier) if not should_retry else None,
                        stop_reason=resolved_stop_reason,
                        status="retrying"
                        if should_retry
                        else ("failed" if explicit_stop_reason is not None else ("stopped" if early_stop_mode == "single_pass_only" else "failed")),
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
        return max(0, int(retry_limit))

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

    def _utc_now(self) -> str:
        return datetime.now(UTC).isoformat(timespec="seconds")

    def _governed_external_execution_group_id(
        self,
        *,
        run_id: str,
        task_id: str,
        authority_packet_id: str,
    ) -> str:
        seed = f"{run_id}:{task_id}:{authority_packet_id}"
        return "execution_group_" + hashlib.sha256(seed.encode("utf-8")).hexdigest()[:12]

    def _governed_external_call_id(
        self,
        *,
        run_id: str,
        task_id: str,
        authority_packet_id: str,
        attempt: int,
    ) -> str:
        seed = f"{run_id}:{task_id}:{authority_packet_id}:{attempt}"
        return "external_call_" + hashlib.sha256(seed.encode("utf-8")).hexdigest()[:12]

    def _governed_external_store(self):
        store = getattr(self.cost_tracker, "store", None)
        if store is None:
            raise APIRouterError("Governed external observability requires store-backed persistence.")
        return store

    def _load_governed_task_packet(self, *, task_id: str) -> TaskPacket:
        store = getattr(self.cost_tracker, "store", None)
        if store is None:
            raise APIRouterError("Delegated execution requires store-backed TaskPacket budget authority.")
        task = store.get_task(task_id)
        raw_packet = ((task or {}).get("acceptance") or {}).get("task_packet")
        if raw_packet is None:
            raise APIRouterError("Delegated execution requires TaskPacket token_budget authority.")
        try:
            return TaskPacket.model_validate(raw_packet)
        except Exception as exc:
            raise APIRouterError(f"Delegated execution TaskPacket token_budget authority is invalid: {exc}") from exc

    def _load_task_packet_budget_authority(self, *, task_id: str):
        return self._load_governed_task_packet(task_id=task_id).token_budget

    def _provider_request_id(self, response: Any) -> str | None:
        for candidate in (getattr(response, "id", None), getattr(response, "response_id", None)):
            if isinstance(candidate, str) and candidate.strip():
                return candidate.strip()
        return None

    def _governed_external_budget_context(self, *, budget_authority, retry_limit: int) -> dict[str, Any]:
        if budget_authority is None:
            return {
                "budget_authority_validated": False,
                "max_prompt_tokens": None,
                "max_completion_tokens": None,
                "max_total_tokens": None,
                "retry_limit": int(retry_limit),
            }
        return {
            "budget_authority_validated": True,
            "max_prompt_tokens": int(budget_authority.max_prompt_tokens),
            "max_completion_tokens": int(budget_authority.max_completion_tokens),
            "max_total_tokens": int(budget_authority.max_total_tokens),
            "retry_limit": int(retry_limit),
        }

    def _governed_external_usage_metrics(self, usage: dict[str, Any]) -> dict[str, int]:
        observed_prompt_tokens = int(usage.get("input_tokens") or 0)
        observed_completion_tokens = int(usage.get("output_tokens") or 0)
        observed_reasoning_tokens = int((usage.get("output_tokens_details") or {}).get("reasoning_tokens") or 0)
        return {
            "observed_prompt_tokens": observed_prompt_tokens,
            "observed_completion_tokens": observed_completion_tokens,
            "observed_reasoning_tokens": observed_reasoning_tokens,
            "observed_total_tokens": observed_prompt_tokens + observed_completion_tokens + observed_reasoning_tokens,
        }

    def _is_governed_budget_stop_reason(self, stop_reason: str | None) -> bool:
        return str(stop_reason or "").strip() in {
            "prompt_budget_exceeded",
            "completion_budget_exceeded",
            "total_budget_exceeded",
            "retry_limit_exceeded",
        }

    def _require_governed_external_observability_correlation(
        self,
        *,
        run_id: str,
        task_id: str,
        task_packet_id: str | None,
        reservation_id: str,
        authority_packet_id: str,
        source_component: str,
    ) -> dict[str, str]:
        correlation: dict[str, str] = {}
        required_fields: list[tuple[str, str | None]] = [
            ("run_id", run_id),
            ("task_id", task_id),
            ("reservation_id", reservation_id),
            ("authority_packet_id", authority_packet_id),
            ("source_component", source_component),
        ]
        if task_packet_id is not None:
            required_fields.insert(2, ("task_packet_id", task_packet_id))
        for field_name, value in required_fields:
            collapsed = str(value or "").strip()
            if not collapsed:
                raise APIRouterError(f"Governed external observability requires {field_name}.")
            correlation[field_name] = collapsed
        store = self._governed_external_store()
        run = store.get_run(correlation["run_id"])
        if run is None:
            raise APIRouterError(
                f"Governed external observability requires a persisted run_id before external dispatch: "
                f"{correlation['run_id']}."
            )
        task = store.get_task(correlation["task_id"])
        if task is None:
            raise APIRouterError(
                f"Governed external observability requires a persisted task_id before external dispatch: "
                f"{correlation['task_id']}."
            )
        if str(run.get("task_id") or "").strip() != correlation["task_id"]:
            raise APIRouterError(
                "Governed external observability requires task_id to match the persisted run context."
            )
        stored_task_packet_id = str((((task.get("acceptance") or {}).get("task_packet") or {}).get("request_id") or "")).strip()
        if task_packet_id is not None and stored_task_packet_id and stored_task_packet_id != correlation["task_packet_id"]:
            raise APIRouterError(
                "Governed external observability requires task_packet_id to match the governed task context."
            )
        return correlation

    def _precheck_governed_pre_observation_blockers(
        self,
        *,
        run_id: str,
        task_id: str,
        task_packet_id: str | None,
        authority_packet_id: str | None,
        role: str,
        task_state: str,
        messages: tuple[str, ...],
        tool_name: str,
    ) -> None:
        policies = load_policies()
        try:
            check_role(role, task_state, policies)
            for message in messages:
                check_prompt(message, policies)
            check_tool_access(role, tool_name, policies)
        except (PermissionError, ValueError) as exc:
            self._record_governed_pre_execution_block(
                run_id=run_id,
                task_id=task_id,
                task_packet_id=task_packet_id,
                authority_packet_id=authority_packet_id,
                block_stage="wrapper_governance_precheck",
                block_reason_code=self._governed_pre_execution_block_reason_code(exc),
            )
            raise

    def _governed_pre_execution_block_reason_code(self, exc: Exception) -> str:
        message = str(exc).lower()
        if isinstance(exc, PermissionError):
            if "cannot operate" in message:
                return "role_state_blocked"
            if "may not call tool" in message:
                return "tool_access_blocked"
            return "permission_blocked"
        if isinstance(exc, ValueError) and "prompt contains forbidden pattern" in message:
            return "prompt_blocked"
        return exc.__class__.__name__

    def _require_governed_pre_execution_block_correlation(
        self,
        *,
        run_id: str,
        task_id: str,
        task_packet_id: str | None,
        authority_packet_id: str | None,
    ) -> dict[str, str | None]:
        correlation: dict[str, str | None] = {}
        for field_name, value in (
            ("run_id", run_id),
            ("task_id", task_id),
            ("authority_packet_id", authority_packet_id),
        ):
            collapsed = str(value or "").strip()
            if not collapsed:
                raise APIRouterError(f"Governed pre-execution block visibility requires {field_name}.")
            correlation[field_name] = collapsed
        normalized_task_packet_id = str(task_packet_id or "").strip() or None
        if normalized_task_packet_id is not None:
            correlation["task_packet_id"] = normalized_task_packet_id
        store = self._governed_external_store()
        run = store.get_run(str(correlation["run_id"]))
        if run is None:
            raise APIRouterError(
                f"Governed pre-execution block visibility requires a persisted run_id before dispatch: {correlation['run_id']}."
            )
        task = store.get_task(str(correlation["task_id"]))
        if task is None:
            raise APIRouterError(
                f"Governed pre-execution block visibility requires a persisted task_id before dispatch: {correlation['task_id']}."
            )
        if str(run.get("task_id") or "").strip() != correlation["task_id"]:
            raise APIRouterError(
                "Governed pre-execution block visibility requires task_id to match the persisted run context."
            )
        stored_task_packet_id = str((((task.get("acceptance") or {}).get("task_packet") or {}).get("request_id") or "")).strip()
        if normalized_task_packet_id is not None and stored_task_packet_id and stored_task_packet_id != normalized_task_packet_id:
            raise APIRouterError(
                "Governed pre-execution block visibility requires task_packet_id to match the governed task context."
            )
        return correlation

    def _record_governed_pre_execution_block(
        self,
        *,
        run_id: str,
        task_id: str,
        task_packet_id: str | None,
        authority_packet_id: str | None,
        block_stage: str,
        block_reason_code: str,
    ) -> None:
        correlation = self._require_governed_pre_execution_block_correlation(
            run_id=run_id,
            task_id=task_id,
            task_packet_id=task_packet_id,
            authority_packet_id=str(authority_packet_id or ""),
        )
        self._governed_external_store().create_governed_pre_execution_block(
            run_id=str(correlation["run_id"]),
            task_id=str(correlation["task_id"]),
            task_packet_id=correlation.get("task_packet_id"),
            authority_packet_id=correlation.get("authority_packet_id"),
            block_stage=block_stage,
            block_reason_code=block_reason_code,
            occurred_at=self._utc_now(),
        )

    def _start_governed_external_call_observation(
        self,
        *,
        run_id: str,
        task_id: str,
        task_packet_id: str,
        reservation_id: str,
        authority_packet_id: str,
        provider: str,
        model: str,
        execution_path: str,
        lane: str,
        route_family: str | None,
        tier: str,
        source_component: str,
        attempt: int,
        reservation_status: str,
        budget_authority,
        retry_limit: int,
        retry_count: int,
    ) -> dict[str, Any]:
        correlation = self._require_governed_external_observability_correlation(
            run_id=run_id,
            task_id=task_id,
            task_packet_id=task_packet_id,
            reservation_id=reservation_id,
            authority_packet_id=authority_packet_id,
            source_component=source_component,
        )
        store = self._governed_external_store()
        started_at = self._utc_now()
        budget_context = self._governed_external_budget_context(
            budget_authority=budget_authority,
            retry_limit=retry_limit,
        )
        execution_group_id = self._governed_external_execution_group_id(
            run_id=correlation["run_id"],
            task_id=correlation["task_id"],
            authority_packet_id=correlation["authority_packet_id"],
        )
        attempt_number = int(attempt) + 1
        external_call_id = self._governed_external_call_id(
            run_id=correlation["run_id"],
            task_id=correlation["task_id"],
            authority_packet_id=correlation["authority_packet_id"],
            attempt=attempt,
        )
        record = store.sync_governed_external_call_record(
            external_call_id=external_call_id,
            execution_group_id=execution_group_id,
            attempt_number=attempt_number,
            run_id=correlation["run_id"],
            task_packet_id=correlation["task_packet_id"],
            reservation_id=correlation["reservation_id"],
            reservation_linkage_validated=True,
            reservation_status=reservation_status,
            provider=provider,
            model=model,
            execution_path=execution_path,
            execution_path_classification="blocked_pre_execution",
            claim_status="missing",
            proof_status="missing",
            budget_authority_validated=bool(budget_context["budget_authority_validated"]),
            max_prompt_tokens=budget_context["max_prompt_tokens"],
            max_completion_tokens=budget_context["max_completion_tokens"],
            max_total_tokens=budget_context["max_total_tokens"],
            retry_limit=budget_context["retry_limit"],
            observed_prompt_tokens=None,
            observed_completion_tokens=None,
            observed_total_tokens=None,
            observed_reasoning_tokens=None,
            retry_count=int(retry_count),
            budget_stop_enforced=False,
            budget_stop_reason_code=None,
            provider_request_id=None,
            started_at=started_at,
            finished_at=None,
            outcome_status="started",
            reason_code="external_call_initialized",
        )
        context = {
            "external_call_id": external_call_id,
            "execution_group_id": record["execution_group_id"],
            "attempt_number": record["attempt_number"],
            "run_id": correlation["run_id"],
            "task_packet_id": correlation["task_packet_id"],
            "reservation_id": correlation["reservation_id"],
            "provider": provider,
            "model": model,
            "execution_path": execution_path,
            "execution_path_classification": record["execution_path_classification"],
            "started_at": started_at,
            "proof_status": record["proof_status"],
            "provider_request_id": record["provider_request_id"],
            "proof_missing_emitted": False,
            "reservation_linkage_validated": record["reservation_linkage_validated"],
            "reservation_status": record["reservation_status"],
            "budget_authority_validated": record["budget_authority_validated"],
            "max_prompt_tokens": record["max_prompt_tokens"],
            "max_completion_tokens": record["max_completion_tokens"],
            "max_total_tokens": record["max_total_tokens"],
            "retry_limit": record["retry_limit"],
            "observed_prompt_tokens": record["observed_prompt_tokens"],
            "observed_completion_tokens": record["observed_completion_tokens"],
            "observed_total_tokens": record["observed_total_tokens"],
            "observed_reasoning_tokens": record["observed_reasoning_tokens"],
            "retry_count": record["retry_count"],
            "budget_stop_enforced": record["budget_stop_enforced"],
            "budget_stop_reason_code": record["budget_stop_reason_code"],
            "budget_stop_emitted": False,
        }
        self._append_governed_external_call_event(
            context,
            event_type="reservation.bound_to_execution",
            status="validated",
            reason_code="reservation_linkage_validated",
            data={
                "execution_group_id": context["execution_group_id"],
                "attempt_number": context["attempt_number"],
                "reservation_status": context["reservation_status"],
                "reservation_linkage_validated": context["reservation_linkage_validated"],
                "budget_authority_validated": context["budget_authority_validated"],
                "max_total_tokens": context["max_total_tokens"],
                "retry_limit": context["retry_limit"],
            },
            occurred_at=started_at,
            source_component=source_component,
        )
        self._append_governed_external_call_event(
            context,
            event_type="execution.wrapper_invoked",
            status="invoked",
            reason_code="governed_api_wrapper_invoked",
            data={
                "execution_group_id": context["execution_group_id"],
                "attempt": attempt_number,
                "attempt_number": context["attempt_number"],
                "provider": provider,
                "model": model,
            },
            occurred_at=started_at,
            source_component=source_component,
        )
        self._append_governed_external_call_event(
            context,
            event_type="execution.path_selected",
            status="selected",
            reason_code="governed_api_path_selected",
            data={
                "execution_group_id": context["execution_group_id"],
                "execution_path": execution_path,
                "provider": provider,
                "model": model,
                "lane": lane,
                "route_family": route_family,
                "tier": tier,
                "attempt": attempt_number,
                "attempt_number": context["attempt_number"],
            },
            occurred_at=started_at,
            source_component=source_component,
        )
        claim_status = determine_claim_status(
            wrapper_invoked=True,
            governed_path_selected=execution_path == "governed_api",
            external_call_recorded=True,
        )
        self._append_governed_external_call_event(
            context,
            event_type="external_call.recorded",
            status="recorded",
            reason_code="external_call_record_created",
            data={
                "execution_group_id": context["execution_group_id"],
                "attempt_number": context["attempt_number"],
                "claim_status": claim_status,
                "execution_path": execution_path,
                "provider": provider,
                "model": model,
            },
            occurred_at=started_at,
            source_component=source_component,
        )
        store.update_governed_external_call_record(
            external_call_id,
            claim_status=claim_status,
            reason_code="external_call_record_created",
        )
        context["claim_status"] = claim_status
        return context

    def _mark_governed_external_api_boundary_reached(self, context: dict[str, Any]) -> None:
        if str(context.get("execution_path_classification") or "") == "governed_api_executed":
            return
        self._append_governed_external_call_event(
            context,
            event_type="execution.api_boundary_reached",
            status="reached",
            reason_code="governed_api_boundary_reached",
            data={
                "execution_group_id": context["execution_group_id"],
                "attempt_number": context["attempt_number"],
                "execution_path_classification": "governed_api_executed",
                "provider": context["provider"],
                "model": context["model"],
            },
        )
        self._governed_external_store().update_governed_external_call_record(
            str(context["external_call_id"]),
            execution_path_classification="governed_api_executed",
            reason_code="governed_api_boundary_reached",
        )
        context["execution_path_classification"] = "governed_api_executed"

    def _append_governed_external_call_event(
        self,
        context: dict[str, Any],
        *,
        event_type: str,
        status: str,
        reason_code: str | None,
        data: dict[str, Any],
        occurred_at: str | None = None,
        source_component: str = "APIRouter",
    ) -> None:
        self._governed_external_store().append_governed_external_call_event(
            event_type=event_type,
            occurred_at=occurred_at or self._utc_now(),
            run_id=str(context["run_id"]),
            task_packet_id=str(context["task_packet_id"]),
            reservation_id=str(context["reservation_id"]),
            external_call_id=str(context["external_call_id"]),
            source_component=source_component,
            status=status,
            reason_code=reason_code,
            data=data,
        )

    def _record_governed_external_budget_check(
        self,
        context: dict[str, Any],
        *,
        usage: dict[str, Any],
        retry_count: int,
    ) -> None:
        observed_metrics = self._governed_external_usage_metrics(usage)
        budget_stop_reason: str | None = None
        if observed_metrics["observed_prompt_tokens"] > int(context["max_prompt_tokens"] or 0):
            budget_stop_reason = "prompt_budget_exceeded"
        elif observed_metrics["observed_completion_tokens"] > int(context["max_completion_tokens"] or 0):
            budget_stop_reason = "completion_budget_exceeded"
        elif observed_metrics["observed_total_tokens"] > int(context["max_total_tokens"] or 0):
            budget_stop_reason = "total_budget_exceeded"
        self._append_governed_external_call_event(
            context,
            event_type="budget.checked",
            status="checked",
            reason_code=budget_stop_reason or "within_authority",
            data={
                "max_prompt_tokens": context["max_prompt_tokens"],
                "max_completion_tokens": context["max_completion_tokens"],
                "max_total_tokens": context["max_total_tokens"],
                "retry_limit": context["retry_limit"],
                "retry_count": int(retry_count),
                "within_authority": budget_stop_reason is None,
                **observed_metrics,
            },
        )
        self._governed_external_store().update_governed_external_call_record(
            str(context["external_call_id"]),
            observed_prompt_tokens=observed_metrics["observed_prompt_tokens"],
            observed_completion_tokens=observed_metrics["observed_completion_tokens"],
            observed_total_tokens=observed_metrics["observed_total_tokens"],
            observed_reasoning_tokens=observed_metrics["observed_reasoning_tokens"],
            retry_count=int(retry_count),
        )
        context.update(observed_metrics)
        context["retry_count"] = int(retry_count)

    def _emit_governed_external_budget_retry_incremented(
        self,
        context: dict[str, Any],
        *,
        retry_count: int,
        error_type: str,
    ) -> None:
        self._append_governed_external_call_event(
            context,
            event_type="budget.retry_incremented",
            status="retrying",
            reason_code="retry_scheduled",
            data={
                "retry_count": int(retry_count),
                "retry_limit": context["retry_limit"],
                "error_type": error_type,
            },
        )
        self._governed_external_store().update_governed_external_call_record(
            str(context["external_call_id"]),
            retry_count=int(retry_count),
        )
        context["retry_count"] = int(retry_count)

    def _emit_governed_external_budget_stop_enforced(
        self,
        context: dict[str, Any],
        *,
        stop_reason: str,
        retry_count: int,
    ) -> None:
        if bool(context.get("budget_stop_emitted")):
            return
        self._append_governed_external_call_event(
            context,
            event_type="budget.stop_enforced",
            status="stopped",
            reason_code=stop_reason,
            data={
                "max_prompt_tokens": context["max_prompt_tokens"],
                "max_completion_tokens": context["max_completion_tokens"],
                "max_total_tokens": context["max_total_tokens"],
                "retry_limit": context["retry_limit"],
                "retry_count": int(retry_count),
                "observed_prompt_tokens": context.get("observed_prompt_tokens"),
                "observed_completion_tokens": context.get("observed_completion_tokens"),
                "observed_total_tokens": context.get("observed_total_tokens"),
                "observed_reasoning_tokens": context.get("observed_reasoning_tokens"),
            },
        )
        self._governed_external_store().update_governed_external_call_record(
            str(context["external_call_id"]),
            retry_count=int(retry_count),
            budget_stop_enforced=True,
            budget_stop_reason_code=stop_reason,
        )
        context["retry_count"] = int(retry_count)
        context["budget_stop_enforced"] = True
        context["budget_stop_reason_code"] = stop_reason
        context["budget_stop_emitted"] = True

    def _capture_governed_external_provider_metadata(
        self,
        context: dict[str, Any],
        *,
        provider_request_id: str,
        provider: str,
        model: str,
    ) -> None:
        proof_status = determine_proof_status(provider_request_id=provider_request_id)
        self._append_governed_external_call_event(
            context,
            event_type="external_call.provider_metadata_captured",
            status="captured",
            reason_code="provider_request_id_captured",
            data={
                "provider": provider,
                "model": model,
                "provider_request_id": provider_request_id,
            },
        )
        self._governed_external_store().update_governed_external_call_record(
            str(context["external_call_id"]),
            proof_status=proof_status,
            provider_request_id=provider_request_id,
            reason_code="provider_request_id_captured",
        )
        context["proof_status"] = proof_status
        context["provider_request_id"] = provider_request_id

    def _emit_governed_external_proof_missing(
        self,
        context: dict[str, Any],
        *,
        reason_code: str,
        data: dict[str, Any],
    ) -> None:
        if str(context.get("proof_status") or "") == "proved":
            return
        if bool(context.get("proof_missing_emitted")):
            return
        self._append_governed_external_call_event(
            context,
            event_type="external_call.proof_missing",
            status="missing",
            reason_code=reason_code,
            data=data,
        )
        self._governed_external_store().update_governed_external_call_record(
            str(context["external_call_id"]),
            proof_status="missing",
            reason_code=reason_code,
        )
        context["proof_status"] = "missing"
        context["proof_missing_emitted"] = True

    def _finish_governed_external_call(
        self,
        context: dict[str, Any],
        *,
        outcome_status: str,
        reason_code: str | None,
    ) -> None:
        self._governed_external_store().update_governed_external_call_record(
            str(context["external_call_id"]),
            execution_path_classification=str(context.get("execution_path_classification") or "blocked_pre_execution"),
            provider_request_id=context.get("provider_request_id"),
            proof_status=str(context.get("proof_status") or "missing"),
            observed_prompt_tokens=context.get("observed_prompt_tokens"),
            observed_completion_tokens=context.get("observed_completion_tokens"),
            observed_total_tokens=context.get("observed_total_tokens"),
            observed_reasoning_tokens=context.get("observed_reasoning_tokens"),
            retry_count=int(context.get("retry_count") or 0),
            budget_stop_enforced=bool(context.get("budget_stop_enforced")),
            budget_stop_reason_code=context.get("budget_stop_reason_code"),
            finished_at=self._utc_now(),
            outcome_status=outcome_status,
            reason_code=reason_code,
        )

    def _validate_task_packet_budget_authority(
        self,
        *,
        budget_authority,
        budget_max_tokens: int | None,
        retry_limit: int | None,
    ) -> None:
        if int(budget_max_tokens or 0) != int(budget_authority.max_total_tokens):
            raise APIRouterError(
                "Delegated execution budget_max_tokens must match TaskPacket.token_budget.max_total_tokens."
            )
        if int(retry_limit or 0) != int(budget_authority.max_retries):
            raise APIRouterError(
                "Delegated execution retry_limit must match TaskPacket.token_budget.max_retries."
            )

    def _budget_authority_exceeded(self, *, usage: dict[str, Any], budget_authority) -> tuple[str | None, str | None]:
        input_tokens = int(usage.get("input_tokens") or 0)
        output_tokens = int(usage.get("output_tokens") or 0)
        reasoning_tokens = int((usage.get("output_tokens_details") or {}).get("reasoning_tokens") or 0)
        total_tokens = input_tokens + output_tokens + reasoning_tokens
        if input_tokens > int(budget_authority.max_prompt_tokens):
            return (
                "Delegated execution exceeded TaskPacket.token_budget.max_prompt_tokens.",
                "prompt_budget_exceeded",
            )
        if output_tokens > int(budget_authority.max_completion_tokens):
            return (
                "Delegated execution exceeded TaskPacket.token_budget.max_completion_tokens.",
                "completion_budget_exceeded",
            )
        if total_tokens > int(budget_authority.max_total_tokens):
            return (
                "Delegated execution exceeded TaskPacket.token_budget.max_total_tokens.",
                "total_budget_exceeded",
            )
        return None, None

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
        if requested_max_tokens != reserved_max_tokens:
            raise APIRouterError(
                f"Delegated execution reservation budget does not match the authorized budget: requested {requested_max_tokens}, "
                f"reserved {reserved_max_tokens}."
            )
        packet_job_id = (authority_job_id or "").strip()
        if not packet_job_id:
            raise APIRouterError("Delegated execution requires a valid authority_job_id.")
        reservation_run_id = reservation.get("run_id")
        if reservation_run_id not in {None, "", run_id}:
            raise APIRouterError("Delegated execution reservation is already bound to a different run.")
        reservation_task_id = reservation.get("task_id")
        if reservation_task_id not in {None, "", task_id}:
            raise APIRouterError("Delegated execution reservation is already bound to a different task.")
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
        if int(budget_max_tokens or 0) <= 0:
            raise APIRouterError("Delegated execution requires a positive budget_max_tokens authority.")
        if int(retry_limit or 0) < 0:
            raise APIRouterError("Delegated execution requires retry_limit to be 0 or greater.")
        if (early_stop_rule or "").strip() not in self._EARLY_STOP_RULES:
            raise APIRouterError(
                "Delegated execution requires a recognized early_stop_rule."
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
