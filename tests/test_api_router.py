from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from agents.api_router import APIRouter, APIRouterError
from agents.cost_tracker import CostTracker
from intake.compiler import compile_task_packet
from intake.gateway import classify_operator_request
from intake.models import TaskPacket
from sessions import SessionStore


def _prepare_repo(tmp_path):
    (tmp_path / "projects" / "program-kanban" / "artifacts").mkdir(parents=True)
    (tmp_path / "projects" / "program-kanban" / "governance").mkdir(parents=True)
    (tmp_path / "projects" / "program-kanban" / "execution").mkdir(parents=True)
    (tmp_path / "sessions").mkdir(parents=True)
    (tmp_path / "governance").mkdir(parents=True)
    (tmp_path / "memory").mkdir(parents=True)
    (tmp_path / "memory" / "framework_health.json").write_text("{}\n", encoding="utf-8")
    (tmp_path / "memory" / "session_summaries.json").write_text("[]\n", encoding="utf-8")
    (tmp_path / "projects" / "program-kanban" / "governance" / "PROJECT_BRIEF.md").write_text("# Brief\n", encoding="utf-8")
    return tmp_path


class _FakeResponses:
    def __init__(self):
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        return _make_response()


class _RetryableError(RuntimeError):
    pass


class _SequencedResponses:
    def __init__(self, outcomes):
        self.calls = []
        self.outcomes = list(outcomes)

    def create(self, **kwargs):
        self.calls.append(kwargs)
        if not self.outcomes:
            raise AssertionError("No outcome configured.")
        outcome = self.outcomes.pop(0)
        if isinstance(outcome, Exception):
            raise outcome
        return outcome


def _make_response(
    output_text: str = '{"ok": true}',
    response_id: str = "resp_test",
    *,
    input_tokens: int = 120,
    cached_input_tokens: int = 20,
    output_tokens: int = 40,
    reasoning_tokens: int = 8,
):
    return SimpleNamespace(
        id=response_id,
        output_text=output_text,
        usage={
            "input_tokens": input_tokens,
            "input_tokens_details": {"cached_tokens": cached_input_tokens},
            "output_tokens": output_tokens,
            "output_tokens_details": {"reasoning_tokens": reasoning_tokens},
        },
    )


class _FakeClient:
    def __init__(self):
        self.responses = _FakeResponses()


def _governed_task_packet(
    *,
    max_prompt_tokens: int = 1024,
    max_completion_tokens: int = 512,
    max_total_tokens: int = 1536,
    max_retries: int = 1,
):
    base = compile_task_packet(classify_operator_request("Implement the governed API-first specialist flow")).model_dump()
    base["token_budget"] = {
        "max_prompt_tokens": max_prompt_tokens,
        "max_completion_tokens": max_completion_tokens,
        "max_total_tokens": max_total_tokens,
        "max_retries": max_retries,
    }
    return TaskPacket.model_validate(base)


def _create_active_reservation(store, *, reservation_id: str, priority_class: str = "P1", reserved_max_tokens: int = 1536):
    return store.sync_execution_job_reservation(
        job_id=reservation_id,
        priority_class=priority_class,
        reserved_max_tokens=reserved_max_tokens,
        reservation_status="reserved",
    )


def _invoke_governed_text(
    router,
    *,
    run_id: str,
    task_id: str,
    lane: str = "background_api",
    authority_packet_id: str = "packet-1",
    budget_reservation_id: str = "reservation-1",
):
    return router.invoke_text(
        run_id=run_id,
        task_id=task_id,
        tier="tier_2_mid",
        lane=lane,
        route_family="execution.tier_2_mid.json.v1",
        system_prompt="Return strict JSON.",
        user_prompt="Return {'ok': true} as JSON.",
        source="APIExecutionTest",
        authority_delegated_work=True,
        authority_packet_id=authority_packet_id,
        authority_job_id="job-1",
        authority_token="auth-1",
        authority_schema_name="schema-v1",
        authority_execution_tier="tier_2_mid",
        authority_execution_lane=lane,
        priority_class="P1",
        budget_max_tokens=1536,
        budget_reservation_id=budget_reservation_id,
        retry_limit=1,
        early_stop_rule="stop_on_first_success",
    )


def _assert_no_governed_observability_writes(store, *, run_id: str, reservation_id: str):
    reservation = store.get_execution_job_reservation(reservation_id)
    assert reservation is not None
    assert reservation["run_id"] in {None, ""}
    assert reservation["task_id"] in {None, ""}
    assert store.list_execution_packets(run_id=run_id) == []
    assert store.list_governed_external_call_records(run_id=run_id) == []
    assert store.list_governed_external_call_events(run_id=run_id) == []


def test_cost_tracker_estimates_cached_input_cost(tmp_path):
    repo_root = _prepare_repo(tmp_path)
    tracker = CostTracker(repo_root=repo_root, store=SessionStore(repo_root))

    estimate = tracker.estimate_cost(
        "gpt-5.4-mini",
        {
            "input_tokens": 1_000_000,
            "input_tokens_details": {"cached_tokens": 200_000},
            "output_tokens": 100_000,
            "output_tokens_details": {"reasoning_tokens": 10_000},
        },
    )

    assert estimate.input_tokens == 1_000_000
    assert estimate.cached_input_tokens == 200_000
    assert estimate.output_tokens == 100_000
    assert estimate.estimated_cost_usd == 0.915


def test_api_router_selects_tier_model_and_records_usage(tmp_path, monkeypatch):
    repo_root = _prepare_repo(tmp_path)
    monkeypatch.chdir(repo_root)
    store = SessionStore(repo_root)
    task = store.create_task(
        "program-kanban",
        "API router slice",
        "Verify the tier-aware API router logs usage and writes outputs.",
        expected_artifact_path="projects/program-kanban/artifacts/router_output.md",
    )
    run = store.create_run("program-kanban", task["id"])
    _create_active_reservation(store, reservation_id="reservation-1")
    client = _FakeClient()
    router = APIRouter(repo_root, client=client, store=store)

    result = router.invoke_text(
        run_id=run["id"],
        task_id=task["id"],
        tier="tier_2_mid",
        lane="background_api",
        route_family="execution.tier_2_mid.json.v1",
        system_prompt="Return strict JSON.",
        user_prompt="Return {'ok': true} as JSON.",
        source="APIExecutionTest",
        artifact_path="projects/program-kanban/artifacts/router_output.md",
        notes="router smoke test",
    )

    assert client.responses.calls
    assert client.responses.calls[0]["model"] == "gpt-5.4-mini"
    assert client.responses.calls[0]["background"] is True
    assert result.model == "gpt-5.4-mini"
    assert result.channel == "api"
    assert result.lane == "background_api"
    assert result.input_tokens == 120
    assert result.cached_input_tokens == 20
    assert result.output_tokens == 40
    assert result.artifact_path == "projects/program-kanban/artifacts/router_output.md"
    assert (repo_root / "projects/program-kanban/artifacts/router_output.md").exists()

    usage_events = store.get_run_evidence(run["id"])["usage_events"]
    assert len(usage_events) == 1
    assert usage_events[0]["prompt_tokens"] == 120
    assert usage_events[0]["completion_tokens"] == 40
    assert usage_events[0]["model"] == "gpt-5.4-mini"
    assert usage_events[0]["tier"] == "tier_2_mid"
    assert usage_events[0]["lane"] == "background_api"
    assert usage_events[0]["cached_input_tokens"] == 20
    assert usage_events[0]["reasoning_tokens"] == 8
    assert usage_events[0]["estimated_cost_usd"] == 0.000197
    assert (repo_root / "governance/execution_logs.md").exists()


def test_api_router_records_execution_packet_telemetry_for_delegated_success(tmp_path, monkeypatch):
    repo_root = _prepare_repo(tmp_path)
    monkeypatch.chdir(repo_root)
    store = SessionStore(repo_root)
    task = store.create_task(
        "program-kanban",
        "Delegated telemetry",
        "Verify delegated packets persist telemetry in the canonical store.",
        expected_artifact_path="projects/program-kanban/artifacts/router_telemetry.md",
        acceptance={"task_packet": _governed_task_packet().model_dump()},
    )
    run = store.create_run("program-kanban", task["id"])
    _create_active_reservation(store, reservation_id="reservation-1")
    client = _FakeClient()
    router = APIRouter(repo_root, client=client, store=store)

    result = router.invoke_text(
        run_id=run["id"],
        task_id=task["id"],
        tier="tier_2_mid",
        lane="background_api",
        route_family="execution.tier_2_mid.json.v1",
        system_prompt="Return strict JSON.",
        user_prompt="Return {'ok': true} as JSON.",
        source="APIExecutionTest",
        artifact_path="projects/program-kanban/artifacts/router_telemetry.md",
        authority_delegated_work=True,
        authority_packet_id="packet-1",
        authority_job_id="job-1",
        authority_token="auth-1",
        authority_schema_name="schema-v1",
        authority_execution_tier="tier_2_mid",
        authority_execution_lane="background_api",
        priority_class="P1",
        budget_max_tokens=1536,
        budget_reservation_id="reservation-1",
        retry_limit=1,
        early_stop_rule="stop_on_first_success",
    )

    evidence = store.get_run_evidence(run["id"])
    packet = evidence["execution_packets"][0]
    external_call = evidence["governed_external_calls"][0]
    execution_group = evidence["governed_external_execution_groups"][0]
    run_summary = evidence["governed_external_run_summary"]
    attention_items = evidence["governed_external_attention_items"]
    external_events = evidence["governed_external_call_events"]
    event_types = {event["event_type"] for event in external_events}

    assert result.output_text == '{"ok": true}'
    assert packet["packet_id"] == "packet-1"
    assert packet["job_id"] == "job-1"
    assert packet["priority_class"] == "P1"
    assert packet["budget_reservation_id"] == "reservation-1"
    assert packet["budget_max_tokens"] == 1536
    assert packet["actual_total_tokens"] == 168
    assert packet["retry_count"] == 0
    assert packet["escalation_target"] is None
    assert packet["stop_reason"] == "stop_on_first_success"
    assert packet["status"] == "completed"
    reservation = evidence["execution_job_reservations"][0]
    assert reservation["job_id"] == "reservation-1"
    assert reservation["run_id"] == run["id"]
    assert reservation["task_id"] == task["id"]
    assert reservation["reservation_status"] == "reserved"
    assert task["acceptance"]["task_packet"]["token_budget"]["max_total_tokens"] == packet["budget_max_tokens"]
    assert task["acceptance"]["task_packet"]["token_budget"]["max_total_tokens"] == reservation["reserved_max_tokens"]
    assert evidence["usage_events"][0]["prompt_tokens"] <= task["acceptance"]["task_packet"]["token_budget"]["max_prompt_tokens"]
    assert evidence["usage_events"][0]["completion_tokens"] <= task["acceptance"]["task_packet"]["token_budget"]["max_completion_tokens"]
    assert packet["actual_total_tokens"] <= task["acceptance"]["task_packet"]["token_budget"]["max_total_tokens"]
    assert external_call["run_id"] == run["id"]
    assert external_call["execution_group_id"] == execution_group["execution_group_id"]
    assert external_call["attempt_number"] == 1
    assert external_call["task_packet_id"] == task["acceptance"]["task_packet"]["request_id"]
    assert external_call["reservation_id"] == "reservation-1"
    assert external_call["provider"] == "openai"
    assert external_call["model"] == "gpt-5.4-mini"
    assert external_call["execution_path"] == "governed_api"
    assert external_call["execution_path_classification"] == "governed_api_executed"
    assert external_call["reservation_linkage_validated"] is True
    assert external_call["reservation_status"] == "reserved"
    assert external_call["claim_status"] == "claimed"
    assert external_call["proof_status"] == "proved"
    assert external_call["budget_authority_validated"] is True
    assert external_call["max_prompt_tokens"] == 1024
    assert external_call["max_completion_tokens"] == 512
    assert external_call["max_total_tokens"] == 1536
    assert external_call["retry_limit"] == 1
    assert external_call["observed_prompt_tokens"] == 120
    assert external_call["observed_completion_tokens"] == 40
    assert external_call["observed_reasoning_tokens"] == 8
    assert external_call["observed_total_tokens"] == 168
    assert external_call["retry_count"] == 0
    assert external_call["budget_stop_enforced"] is False
    assert external_call["budget_stop_reason_code"] is None
    assert external_call["provider_request_id"] == "resp_test"
    assert external_call["outcome_status"] == "completed"
    assert execution_group["total_attempts"] == 1
    assert execution_group["execution_path_classification"] == "governed_api_executed"
    assert execution_group["final_attempt_number"] == 1
    assert execution_group["final_outcome_status"] == "completed"
    assert execution_group["final_budget_stop_enforced"] is False
    assert execution_group["final_budget_stop_reason_code"] is None
    assert execution_group["final_proof_status"] == "proved"
    assert execution_group["final_external_call_id"] == external_call["external_call_id"]
    assert run_summary == {
        "total_execution_groups": 1,
        "total_attempts": 1,
        "governed_api_execution_count": 1,
        "blocked_execution_count": 0,
        "pre_observation_block_count": 0,
        "final_success_count": 1,
        "final_failed_count": 0,
        "final_stopped_count": 0,
        "final_budget_stopped_count": 0,
        "final_proof_missing_count": 0,
        "final_proved_count": 1,
        "final_trusted_reconciled_count": 0,
        "final_proof_captured_not_reconciled_count": 1,
        "final_reconciliation_failed_count": 0,
        "final_claim_missing_count": 0,
        "final_claimed_only_count": 0,
    }
    assert attention_items == []
    assert {
        "reservation.bound_to_execution",
        "execution.wrapper_invoked",
        "execution.path_selected",
        "execution.api_boundary_reached",
        "external_call.recorded",
        "external_call.provider_metadata_captured",
        "budget.checked",
    }.issubset(event_types)
    assert "reservation.consumed_for_execution" not in event_types
    reservation_bound = next(event for event in external_events if event["event_type"] == "reservation.bound_to_execution")
    assert reservation_bound["reason_code"] == "reservation_linkage_validated"
    assert reservation_bound["data"]["reservation_status"] == "reserved"
    budget_checked = next(event for event in external_events if event["event_type"] == "budget.checked")
    assert budget_checked["reason_code"] == "within_authority"
    assert budget_checked["data"]["within_authority"] is True
    assert budget_checked["data"]["observed_total_tokens"] == 168


def test_api_router_enforces_retry_limit_for_delegated_packets(tmp_path, monkeypatch):
    repo_root = _prepare_repo(tmp_path)
    monkeypatch.chdir(repo_root)
    store = SessionStore(repo_root)
    task = store.create_task(
        "program-kanban",
        "Delegated retry cap",
        "Verify delegated packets stop at the configured retry limit.",
        expected_artifact_path="projects/program-kanban/artifacts/router_retry.md",
        acceptance={"task_packet": _governed_task_packet(max_retries=1).model_dump()},
    )
    run = store.create_run("program-kanban", task["id"])
    _create_active_reservation(store, reservation_id="reservation-1")
    client = _FakeClient()
    client.responses = _SequencedResponses([
        _RetryableError("transient-1"),
        _RetryableError("transient-2"),
        _make_response(),
    ])
    router = APIRouter(repo_root, client=client, store=store)
    router.should_retry = lambda exc: True  # type: ignore[method-assign]

    try:
        router.invoke_text(
            run_id=run["id"],
            task_id=task["id"],
            tier="tier_2_mid",
            lane="sync_api",
            route_family="execution.tier_2_mid.json.v1",
            system_prompt="Return strict JSON.",
            user_prompt="Return {'ok': true} as JSON.",
            source="APIExecutionTest",
            authority_delegated_work=True,
            authority_packet_id="packet-1",
            authority_job_id="job-1",
            authority_token="auth-1",
            authority_schema_name="schema-v1",
            authority_execution_tier="tier_2_mid",
            authority_execution_lane="sync_api",
            priority_class="P1",
            budget_max_tokens=1536,
            budget_reservation_id="reservation-1",
            retry_limit=1,
            early_stop_rule="stop_on_first_success",
        )
    except APIRouterError as exc:
        assert "transient-2" in str(exc)
    else:
        raise AssertionError("Expected delegated packet to stop at the retry limit.")

    assert len(client.responses.calls) == 2
    evidence = store.get_run_evidence(run["id"])
    packet = evidence["execution_packets"][0]
    external_calls = evidence["governed_external_calls"]
    execution_groups = evidence["governed_external_execution_groups"]
    run_summary = evidence["governed_external_run_summary"]
    attention_items = evidence["governed_external_attention_items"]
    external_events = evidence["governed_external_call_events"]
    failed_call = next(call for call in external_calls if call["outcome_status"] == "failed")
    retrying_call = next(call for call in external_calls if call["outcome_status"] == "retrying")
    assert len(external_calls) == 2
    assert len(execution_groups) == 1
    assert {call["execution_group_id"] for call in external_calls} == {execution_groups[0]["execution_group_id"]}
    assert sorted(call["attempt_number"] for call in external_calls) == [1, 2]
    assert {call["execution_path_classification"] for call in external_calls} == {"governed_api_executed"}
    assert retrying_call["attempt_number"] == 1
    assert failed_call["attempt_number"] == 2
    assert packet["retry_count"] == 1
    assert packet["stop_reason"] == "retry_limit_exceeded"
    assert packet["escalation_target"] == "tier_1_senior"
    assert packet["status"] == "failed"
    assert failed_call["retry_count"] == 1
    assert failed_call["budget_stop_enforced"] is True
    assert failed_call["budget_stop_reason_code"] == "retry_limit_exceeded"
    assert failed_call["observed_prompt_tokens"] is None
    assert failed_call["observed_completion_tokens"] is None
    assert failed_call["observed_reasoning_tokens"] is None
    assert failed_call["observed_total_tokens"] is None
    assert execution_groups[0]["total_attempts"] == 2
    assert execution_groups[0]["execution_path_classification"] == "governed_api_executed"
    assert execution_groups[0]["final_attempt_number"] == 2
    assert execution_groups[0]["final_outcome_status"] == "failed"
    assert execution_groups[0]["final_budget_stop_enforced"] is True
    assert execution_groups[0]["final_budget_stop_reason_code"] == "retry_limit_exceeded"
    assert execution_groups[0]["final_proof_status"] == failed_call["proof_status"]
    assert execution_groups[0]["final_external_call_id"] == failed_call["external_call_id"]
    assert run_summary == {
        "total_execution_groups": 1,
        "total_attempts": 2,
        "governed_api_execution_count": 1,
        "blocked_execution_count": 0,
        "pre_observation_block_count": 0,
        "final_success_count": 0,
        "final_failed_count": 0,
        "final_stopped_count": 0,
        "final_budget_stopped_count": 1,
        "final_proof_missing_count": 1,
        "final_proved_count": 0,
        "final_trusted_reconciled_count": 0,
        "final_proof_captured_not_reconciled_count": 0,
        "final_reconciliation_failed_count": 0,
        "final_claim_missing_count": 0,
        "final_claimed_only_count": 1,
    }
    assert attention_items == [
        {
            "execution_group_id": execution_groups[0]["execution_group_id"],
            "final_external_call_id": failed_call["external_call_id"],
            "final_attempt_number": 2,
            "execution_path_classification": "governed_api_executed",
            "final_outcome_status": "failed",
            "final_budget_stop_enforced": True,
            "final_budget_stop_reason_code": "retry_limit_exceeded",
            "final_proof_status": failed_call["proof_status"],
            "final_reconciliation_state": "not_reconciled",
            "final_trust_status": "claimed_only",
            "attention_reason": "retry_limit_exceeded",
        }
    ]
    assert {
        event["event_type"]
        for event in external_events
        if event["external_call_id"] == failed_call["external_call_id"]
    } >= {"budget.stop_enforced"}
    assert "budget.retry_incremented" in {event["event_type"] for event in external_events}


def test_api_router_single_pass_only_stops_after_first_attempt(tmp_path, monkeypatch):
    repo_root = _prepare_repo(tmp_path)
    monkeypatch.chdir(repo_root)
    store = SessionStore(repo_root)
    task = store.create_task(
        "program-kanban",
        "Delegated early stop",
        "Verify single-pass delegated packets stop after one attempt.",
        expected_artifact_path="projects/program-kanban/artifacts/router_stop.md",
        acceptance={"task_packet": _governed_task_packet(max_retries=3).model_dump()},
    )
    run = store.create_run("program-kanban", task["id"])
    _create_active_reservation(store, reservation_id="reservation-1")
    client = _FakeClient()
    client.responses = _SequencedResponses([
        _RetryableError("transient-1"),
        _make_response(),
    ])
    router = APIRouter(repo_root, client=client, store=store)
    router.should_retry = lambda exc: True  # type: ignore[method-assign]

    try:
        router.invoke_text(
            run_id=run["id"],
            task_id=task["id"],
            tier="tier_2_mid",
            lane="sync_api",
            route_family="execution.tier_2_mid.json.v1",
            system_prompt="Return strict JSON.",
            user_prompt="Return {'ok': true} as JSON.",
            source="APIExecutionTest",
            authority_delegated_work=True,
            authority_packet_id="packet-1",
            authority_job_id="job-1",
            authority_token="auth-1",
            authority_schema_name="schema-v1",
            authority_execution_tier="tier_2_mid",
            authority_execution_lane="sync_api",
            priority_class="P1",
            budget_max_tokens=1536,
            budget_reservation_id="reservation-1",
            retry_limit=3,
            early_stop_rule="single_pass_only",
        )
    except APIRouterError as exc:
        assert "transient-1" in str(exc)
    else:
        raise AssertionError("Expected single-pass-only delegated packet to stop after the first attempt.")

    assert len(client.responses.calls) == 1
    packet = store.get_run_evidence(run["id"])["execution_packets"][0]
    assert packet["retry_count"] == 0
    assert packet["stop_reason"] == "single_pass_only"
    assert packet["escalation_target"] == "tier_1_senior"
    assert packet["status"] == "stopped"


def test_api_router_rejects_delegated_packet_missing_authority_field(tmp_path, monkeypatch):
    repo_root = _prepare_repo(tmp_path)
    monkeypatch.chdir(repo_root)
    store = SessionStore(repo_root)
    task = store.create_task(
        "program-kanban",
        "API router gate",
        "Verify delegated packets are rejected when authority fields are missing.",
        expected_artifact_path="projects/program-kanban/artifacts/router_gate.md",
        acceptance={"task_packet": _governed_task_packet(max_retries=1).model_dump()},
    )
    run = store.create_run("program-kanban", task["id"])
    _create_active_reservation(store, reservation_id="reservation-1")
    client = _FakeClient()
    router = APIRouter(repo_root, client=client, store=store)

    try:
        router.invoke_text(
            run_id=run["id"],
            task_id=task["id"],
            tier="tier_2_mid",
            lane="sync_api",
            route_family="execution.tier_2_mid.json.v1",
            system_prompt="Return strict JSON.",
            user_prompt="Return {'ok': true} as JSON.",
            source="APIExecutionTest",
            authority_delegated_work=True,
            authority_packet_id="packet-1",
            authority_job_id="job-1",
            authority_schema_name="schema-v1",
            authority_execution_tier="tier_2_mid",
            authority_execution_lane="sync_api",
            priority_class="P1",
            budget_max_tokens=1536,
            budget_reservation_id="reservation-1",
            retry_limit=1,
            early_stop_rule="stop_on_first_success",
        )
    except APIRouterError as exc:
        assert "authority_token" in str(exc)
    else:
        raise AssertionError("Expected delegated packet without authority_token to be rejected.")

    assert not client.responses.calls


def test_api_router_allows_delegated_packet_with_complete_authority_contract(tmp_path, monkeypatch):
    repo_root = _prepare_repo(tmp_path)
    monkeypatch.chdir(repo_root)
    store = SessionStore(repo_root)
    task = store.create_task(
        "program-kanban",
        "API router gate",
        "Verify delegated packets pass when the authority contract is complete.",
        expected_artifact_path="projects/program-kanban/artifacts/router_gate.md",
        acceptance={"task_packet": _governed_task_packet(max_retries=1).model_dump()},
    )
    run = store.create_run("program-kanban", task["id"])
    _create_active_reservation(store, reservation_id="reservation-1")
    client = _FakeClient()
    router = APIRouter(repo_root, client=client, store=store)

    result = router.invoke_text(
        run_id=run["id"],
        task_id=task["id"],
        tier="tier_2_mid",
        lane="sync_api",
        route_family="execution.tier_2_mid.json.v1",
        system_prompt="Return strict JSON.",
        user_prompt="Return {'ok': true} as JSON.",
        source="APIExecutionTest",
        authority_delegated_work=True,
        authority_packet_id="packet-1",
        authority_job_id="job-1",
        authority_token="auth-1",
        authority_schema_name="schema-v1",
        authority_execution_tier="tier_2_mid",
        authority_execution_lane="sync_api",
        priority_class="P1",
        budget_max_tokens=1536,
        budget_reservation_id="reservation-1",
        retry_limit=1,
        early_stop_rule="stop_on_first_success",
    )

    assert result.output_text == '{"ok": true}'
    assert client.responses.calls
    assert client.responses.calls[0]["model"] == "gpt-5.4-mini"


def test_api_router_rejects_delegated_packet_without_task_packet_budget_authority(tmp_path, monkeypatch):
    repo_root = _prepare_repo(tmp_path)
    monkeypatch.chdir(repo_root)
    store = SessionStore(repo_root)
    task = store.create_task(
        "program-kanban",
        "Missing packet budget",
        "Verify delegated packets fail without TaskPacket token budget authority.",
        expected_artifact_path="projects/program-kanban/artifacts/router_missing_budget.md",
    )
    run = store.create_run("program-kanban", task["id"])
    _create_active_reservation(store, reservation_id="reservation-1", reserved_max_tokens=1536)
    client = _FakeClient()
    router = APIRouter(repo_root, client=client, store=store)

    try:
        router.invoke_text(
            run_id=run["id"],
            task_id=task["id"],
            tier="tier_2_mid",
            lane="sync_api",
            route_family="execution.tier_2_mid.json.v1",
            system_prompt="Return strict JSON.",
            user_prompt="Return {'ok': true} as JSON.",
            source="APIExecutionTest",
            authority_delegated_work=True,
            authority_packet_id="packet-1",
            authority_job_id="job-1",
            authority_token="auth-1",
            authority_schema_name="schema-v1",
            authority_execution_tier="tier_2_mid",
            authority_execution_lane="sync_api",
            priority_class="P1",
            budget_max_tokens=1536,
            budget_reservation_id="reservation-1",
            retry_limit=1,
            early_stop_rule="stop_on_first_success",
        )
    except APIRouterError as exc:
        assert "TaskPacket token_budget authority" in str(exc)
    else:
        raise AssertionError("Expected delegated packet without TaskPacket budget authority to be rejected.")

    assert not client.responses.calls


def test_api_router_rejects_delegated_packet_with_budget_authority_mismatch(tmp_path, monkeypatch):
    repo_root = _prepare_repo(tmp_path)
    monkeypatch.chdir(repo_root)
    store = SessionStore(repo_root)
    task = store.create_task(
        "program-kanban",
        "Mismatched packet budget",
        "Verify delegated packets fail when authority budget mismatches TaskPacket budget.",
        expected_artifact_path="projects/program-kanban/artifacts/router_budget_mismatch.md",
        acceptance={"task_packet": _governed_task_packet().model_dump()},
    )
    run = store.create_run("program-kanban", task["id"])
    _create_active_reservation(store, reservation_id="reservation-1", reserved_max_tokens=1536)
    client = _FakeClient()
    router = APIRouter(repo_root, client=client, store=store)

    try:
        router.invoke_text(
            run_id=run["id"],
            task_id=task["id"],
            tier="tier_2_mid",
            lane="sync_api",
            route_family="execution.tier_2_mid.json.v1",
            system_prompt="Return strict JSON.",
            user_prompt="Return {'ok': true} as JSON.",
            source="APIExecutionTest",
            authority_delegated_work=True,
            authority_packet_id="packet-1",
            authority_job_id="job-1",
            authority_token="auth-1",
            authority_schema_name="schema-v1",
            authority_execution_tier="tier_2_mid",
            authority_execution_lane="sync_api",
            priority_class="P1",
            budget_max_tokens=1200,
            budget_reservation_id="reservation-1",
            retry_limit=1,
            early_stop_rule="stop_on_first_success",
        )
    except APIRouterError as exc:
        assert "budget_max_tokens must match TaskPacket.token_budget.max_total_tokens" in str(exc)
    else:
        raise AssertionError("Expected delegated packet with mismatched authority budget to be rejected.")

    assert not client.responses.calls


def test_api_router_rejects_delegated_packet_without_active_reservation(tmp_path, monkeypatch):
    repo_root = _prepare_repo(tmp_path)
    monkeypatch.chdir(repo_root)
    store = SessionStore(repo_root)
    task = store.create_task(
        "program-kanban",
        "API router reservation gate",
        "Verify delegated packets fail closed without an active reservation.",
        expected_artifact_path="projects/program-kanban/artifacts/router_reservation_gate.md",
        acceptance={"task_packet": _governed_task_packet(max_retries=1).model_dump()},
    )
    run = store.create_run("program-kanban", task["id"])
    client = _FakeClient()
    router = APIRouter(repo_root, client=client, store=store)

    try:
        router.invoke_text(
            run_id=run["id"],
            task_id=task["id"],
            tier="tier_2_mid",
            lane="sync_api",
            route_family="execution.tier_2_mid.json.v1",
            system_prompt="Return strict JSON.",
            user_prompt="Return {'ok': true} as JSON.",
            source="APIExecutionTest",
            authority_delegated_work=True,
            authority_packet_id="packet-1",
            authority_job_id="job-1",
            authority_token="auth-1",
            authority_schema_name="schema-v1",
            authority_execution_tier="tier_2_mid",
            authority_execution_lane="sync_api",
            priority_class="P1",
            budget_max_tokens=1536,
            budget_reservation_id="reservation-1",
            retry_limit=1,
            early_stop_rule="stop_on_first_success",
        )
    except APIRouterError as exc:
        assert "active budget reservation" in str(exc)
    else:
        raise AssertionError("Expected delegated packet without an active reservation to be rejected.")

    assert not client.responses.calls


def test_api_router_rejects_delegated_packet_with_inactive_reservation(tmp_path, monkeypatch):
    repo_root = _prepare_repo(tmp_path)
    monkeypatch.chdir(repo_root)
    store = SessionStore(repo_root)
    task = store.create_task(
        "program-kanban",
        "API router reservation gate",
        "Verify delegated packets fail closed with an inactive reservation.",
        expected_artifact_path="projects/program-kanban/artifacts/router_reservation_gate.md",
        acceptance={"task_packet": _governed_task_packet(max_retries=1).model_dump()},
    )
    run = store.create_run("program-kanban", task["id"])
    store.sync_execution_job_reservation(
        job_id="reservation-1",
        priority_class="P1",
        reserved_max_tokens=1536,
        reservation_status="unreserved",
    )
    client = _FakeClient()
    router = APIRouter(repo_root, client=client, store=store)

    try:
        router.invoke_text(
            run_id=run["id"],
            task_id=task["id"],
            tier="tier_2_mid",
            lane="sync_api",
            route_family="execution.tier_2_mid.json.v1",
            system_prompt="Return strict JSON.",
            user_prompt="Return {'ok': true} as JSON.",
            source="APIExecutionTest",
            authority_delegated_work=True,
            authority_packet_id="packet-1",
            authority_job_id="job-1",
            authority_token="auth-1",
            authority_schema_name="schema-v1",
            authority_execution_tier="tier_2_mid",
            authority_execution_lane="sync_api",
            priority_class="P1",
            budget_max_tokens=1536,
            budget_reservation_id="reservation-1",
            retry_limit=1,
            early_stop_rule="stop_on_first_success",
        )
    except APIRouterError as exc:
        assert "active budget reservation" in str(exc)
    else:
        raise AssertionError("Expected delegated packet with an inactive reservation to be rejected.")

    assert not client.responses.calls


def test_api_router_rejects_delegated_usage_beyond_authorized_budget(tmp_path, monkeypatch):
    repo_root = _prepare_repo(tmp_path)
    monkeypatch.chdir(repo_root)
    store = SessionStore(repo_root)
    task = store.create_task(
        "program-kanban",
        "Budget exceeded",
        "Verify delegated execution fails closed when runtime usage exceeds TaskPacket authority.",
        expected_artifact_path="projects/program-kanban/artifacts/router_budget_exceeded.md",
        acceptance={
            "task_packet": _governed_task_packet(
                max_prompt_tokens=100,
                max_completion_tokens=40,
                max_total_tokens=140,
                max_retries=1,
            ).model_dump()
        },
    )
    run = store.create_run("program-kanban", task["id"])
    _create_active_reservation(store, reservation_id="reservation-1", reserved_max_tokens=140)
    client = _FakeClient()
    client.responses = _SequencedResponses(
        [
            _make_response(
                input_tokens=101,
                cached_input_tokens=0,
                output_tokens=20,
                reasoning_tokens=0,
            )
        ]
    )
    router = APIRouter(repo_root, client=client, store=store)

    try:
        router.invoke_text(
            run_id=run["id"],
            task_id=task["id"],
            tier="tier_2_mid",
            lane="sync_api",
            route_family="execution.tier_2_mid.json.v1",
            system_prompt="Return strict JSON.",
            user_prompt="Return {'ok': true} as JSON.",
            source="APIExecutionTest",
            artifact_path="projects/program-kanban/artifacts/router_budget_exceeded.md",
            authority_delegated_work=True,
            authority_packet_id="packet-1",
            authority_job_id="job-1",
            authority_token="auth-1",
            authority_schema_name="schema-v1",
            authority_execution_tier="tier_2_mid",
            authority_execution_lane="sync_api",
            priority_class="P1",
            budget_max_tokens=140,
            budget_reservation_id="reservation-1",
            retry_limit=1,
            early_stop_rule="stop_on_first_success",
        )
    except APIRouterError as exc:
        assert "max_prompt_tokens" in str(exc)
    else:
        raise AssertionError("Expected over-budget delegated execution to fail closed.")

    evidence = store.get_run_evidence(run["id"])
    packet = evidence["execution_packets"][0]
    usage_event = evidence["usage_events"][0]
    external_call = evidence["governed_external_calls"][0]
    external_events = evidence["governed_external_call_events"]
    assert packet["stop_reason"] == "prompt_budget_exceeded"
    assert packet["status"] == "failed"
    assert packet["actual_total_tokens"] == 121
    assert usage_event["prompt_tokens"] == 101
    assert external_call["outcome_status"] == "failed"
    assert external_call["budget_stop_enforced"] is True
    assert external_call["budget_stop_reason_code"] == "prompt_budget_exceeded"
    assert external_call["max_prompt_tokens"] == 100
    assert external_call["max_completion_tokens"] == 40
    assert external_call["max_total_tokens"] == 140
    assert external_call["retry_limit"] == 1
    assert external_call["observed_prompt_tokens"] == 101
    assert external_call["observed_completion_tokens"] == 20
    assert external_call["observed_reasoning_tokens"] == 0
    assert external_call["observed_total_tokens"] == 121
    assert {
        "budget.checked",
        "budget.stop_enforced",
    }.issubset({event["event_type"] for event in external_events})
    budget_stop = next(event for event in external_events if event["event_type"] == "budget.stop_enforced")
    assert budget_stop["reason_code"] == "prompt_budget_exceeded"
    assert budget_stop["data"]["observed_total_tokens"] == 121
    assert not (repo_root / "projects/program-kanban/artifacts/router_budget_exceeded.md").exists()


def test_api_router_allows_high_cost_but_explicitly_authorized_budget(tmp_path, monkeypatch):
    repo_root = _prepare_repo(tmp_path)
    monkeypatch.chdir(repo_root)
    store = SessionStore(repo_root)
    task = store.create_task(
        "program-kanban",
        "High budget allowed",
        "Verify explicitly authorized high-cost governed execution is allowed.",
        expected_artifact_path="projects/program-kanban/artifacts/router_high_budget.md",
        acceptance={
            "task_packet": _governed_task_packet(
                max_prompt_tokens=20_000,
                max_completion_tokens=12_000,
                max_total_tokens=32_000,
                max_retries=7,
            ).model_dump()
        },
    )
    run = store.create_run("program-kanban", task["id"])
    _create_active_reservation(store, reservation_id="reservation-1", reserved_max_tokens=32_000)
    client = _FakeClient()
    router = APIRouter(repo_root, client=client, store=store)

    result = router.invoke_text(
        run_id=run["id"],
        task_id=task["id"],
        tier="tier_2_mid",
        lane="sync_api",
        route_family="execution.tier_2_mid.json.v1",
        system_prompt="Return strict JSON.",
        user_prompt="Return {'ok': true} as JSON.",
        source="APIExecutionTest",
        authority_delegated_work=True,
        authority_packet_id="packet-1",
        authority_job_id="job-1",
        authority_token="auth-1",
        authority_schema_name="schema-v1",
        authority_execution_tier="tier_2_mid",
        authority_execution_lane="sync_api",
        priority_class="P1",
        budget_max_tokens=32_000,
        budget_reservation_id="reservation-1",
        retry_limit=7,
        early_stop_rule="stop_on_first_success",
    )

    evidence = store.get_run_evidence(run["id"])
    packet = evidence["execution_packets"][0]
    assert result.output_text == '{"ok": true}'
    assert packet["retry_limit"] == 7
    assert packet["budget_max_tokens"] == 32_000
    assert evidence["execution_job_reservations"][0]["reserved_max_tokens"] == 32_000


def test_api_router_marks_governed_external_proof_missing_without_provider_request_id(tmp_path, monkeypatch):
    repo_root = _prepare_repo(tmp_path)
    monkeypatch.chdir(repo_root)
    store = SessionStore(repo_root)
    task = store.create_task(
        "program-kanban",
        "Missing provider proof",
        "Verify governed external calls remain claimed but unproved when provider metadata lacks a request id.",
        expected_artifact_path="projects/program-kanban/artifacts/router_missing_proof.md",
        acceptance={"task_packet": _governed_task_packet().model_dump()},
    )
    run = store.create_run("program-kanban", task["id"])
    _create_active_reservation(store, reservation_id="reservation-1")
    client = _FakeClient()
    client.responses = _SequencedResponses([_make_response(response_id=None)])
    router = APIRouter(repo_root, client=client, store=store)

    result = router.invoke_text(
        run_id=run["id"],
        task_id=task["id"],
        tier="tier_2_mid",
        lane="sync_api",
        route_family="execution.tier_2_mid.json.v1",
        system_prompt="Return strict JSON.",
        user_prompt="Return {'ok': true} as JSON.",
        source="APIExecutionTest",
        authority_delegated_work=True,
        authority_packet_id="packet-1",
        authority_job_id="job-1",
        authority_token="auth-1",
        authority_schema_name="schema-v1",
        authority_execution_tier="tier_2_mid",
        authority_execution_lane="sync_api",
        priority_class="P1",
        budget_max_tokens=1536,
        budget_reservation_id="reservation-1",
        retry_limit=1,
        early_stop_rule="stop_on_first_success",
    )

    evidence = store.get_run_evidence(run["id"])
    external_call = evidence["governed_external_calls"][0]
    execution_group = evidence["governed_external_execution_groups"][0]
    run_summary = evidence["governed_external_run_summary"]
    attention_items = evidence["governed_external_attention_items"]
    external_events = evidence["governed_external_call_events"]

    assert result.output_text == '{"ok": true}'
    assert external_call["claim_status"] == "claimed"
    assert external_call["proof_status"] == "missing"
    assert external_call["execution_path_classification"] == "governed_api_executed"
    assert execution_group["execution_path_classification"] == "governed_api_executed"
    assert external_call["provider_request_id"] is None
    assert external_call["outcome_status"] == "completed"
    assert external_call["task_packet_id"] == task["acceptance"]["task_packet"]["request_id"]
    assert external_call["reservation_id"] == "reservation-1"
    assert "external_call.proof_missing" in {event["event_type"] for event in external_events}
    proof_missing = next(event for event in external_events if event["event_type"] == "external_call.proof_missing")
    assert proof_missing["run_id"] == run["id"]
    assert proof_missing["task_packet_id"] == task["acceptance"]["task_packet"]["request_id"]
    assert proof_missing["reservation_id"] == "reservation-1"
    assert proof_missing["status"] == "missing"
    assert proof_missing["reason_code"] == "provider_request_id_missing"
    assert run_summary == {
        "total_execution_groups": 1,
        "total_attempts": 1,
        "governed_api_execution_count": 1,
        "blocked_execution_count": 0,
        "pre_observation_block_count": 0,
        "final_success_count": 1,
        "final_failed_count": 0,
        "final_stopped_count": 0,
        "final_budget_stopped_count": 0,
        "final_proof_missing_count": 1,
        "final_proved_count": 0,
        "final_trusted_reconciled_count": 0,
        "final_proof_captured_not_reconciled_count": 0,
        "final_reconciliation_failed_count": 0,
        "final_claim_missing_count": 0,
        "final_claimed_only_count": 1,
    }
    assert attention_items == [
        {
            "execution_group_id": execution_group["execution_group_id"],
            "final_external_call_id": execution_group["final_external_call_id"],
            "final_attempt_number": 1,
            "execution_path_classification": "governed_api_executed",
            "final_outcome_status": "completed",
            "final_budget_stop_enforced": False,
            "final_budget_stop_reason_code": None,
            "final_proof_status": "missing",
            "final_reconciliation_state": "not_reconciled",
            "final_trust_status": "claimed_only",
            "attention_reason": "final_proof_missing",
        }
    ]


def test_api_router_persists_pre_observation_role_state_block_without_external_attempt_record(tmp_path, monkeypatch):
    repo_root = _prepare_repo(tmp_path)
    monkeypatch.chdir(repo_root)
    store = SessionStore(repo_root)
    task = store.create_task(
        "program-kanban",
        "Role/state block",
        "Verify governed delegated execution is marked blocked when the role/state gate stops before provider dispatch.",
        expected_artifact_path="projects/program-kanban/artifacts/router_blocked.md",
        acceptance={"task_packet": _governed_task_packet().model_dump()},
    )
    run = store.create_run("program-kanban", task["id"])
    _create_active_reservation(store, reservation_id="reservation-1")
    client = _FakeClient()
    router = APIRouter(repo_root, client=client, store=store)

    try:
        router.invoke_text(
            run_id=run["id"],
            task_id=task["id"],
            tier="tier_2_mid",
            lane="sync_api",
            route_family="execution.tier_2_mid.json.v1",
            system_prompt="Reply exactly with OK.",
            user_prompt="Reply exactly with OK.",
            source="Developer",
            authority_delegated_work=True,
            authority_packet_id="packet-1",
            authority_job_id="job-1",
            authority_token="auth-1",
            authority_schema_name="schema-v1",
            authority_execution_tier="tier_2_mid",
            authority_execution_lane="sync_api",
            priority_class="P1",
            budget_max_tokens=1536,
            budget_reservation_id="reservation-1",
            retry_limit=1,
            early_stop_rule="stop_on_first_success",
        )
    except APIRouterError as exc:
        assert "Idea stage" in str(exc)
    else:
        raise AssertionError("Expected the Developer role/state gate to block before provider execution.")

    assert len(client.responses.calls) == 0
    evidence = store.get_run_evidence(run["id"])
    pre_execution_blocks = evidence["governed_pre_execution_blocks"]
    run_summary = evidence["governed_external_run_summary"]
    attention_items = evidence["governed_external_attention_items"]
    assert evidence["governed_external_calls"] == []
    assert evidence["governed_external_call_events"] == []
    assert evidence["governed_external_execution_groups"] == []
    assert pre_execution_blocks == [
        {
            "block_id": pre_execution_blocks[0]["block_id"],
            "occurred_at": pre_execution_blocks[0]["occurred_at"],
            "run_id": run["id"],
            "task_id": task["id"],
            "task_packet_id": task["acceptance"]["task_packet"]["request_id"],
            "authority_packet_id": "packet-1",
            "block_stage": "wrapper_governance_precheck",
            "block_reason_code": "role_state_blocked",
        }
    ]
    assert run_summary == {
        "total_execution_groups": 0,
        "total_attempts": 0,
        "governed_api_execution_count": 0,
        "blocked_execution_count": 0,
        "pre_observation_block_count": 1,
        "final_success_count": 0,
        "final_failed_count": 0,
        "final_stopped_count": 0,
        "final_budget_stopped_count": 0,
        "final_proof_missing_count": 0,
        "final_proved_count": 0,
        "final_trusted_reconciled_count": 0,
        "final_proof_captured_not_reconciled_count": 0,
        "final_reconciliation_failed_count": 0,
        "final_claim_missing_count": 0,
        "final_claimed_only_count": 0,
    }
    assert attention_items == []


def test_api_router_rejects_blank_governed_observability_correlation_before_persistence(tmp_path, monkeypatch):
    repo_root = _prepare_repo(tmp_path)
    monkeypatch.chdir(repo_root)
    store = SessionStore(repo_root)
    task = store.create_task(
        "program-kanban",
        "Correlation guard",
        "Verify governed observability correlation fails before persistence.",
        expected_artifact_path="projects/program-kanban/artifacts/router_correlation_guard.md",
        acceptance={"task_packet": _governed_task_packet().model_dump()},
    )
    run = store.create_run("program-kanban", task["id"])
    _create_active_reservation(store, reservation_id="reservation-1")
    router = APIRouter(repo_root, client=_FakeClient(), store=store)

    for case in (
        {
            "label": "run_id",
            "run_id": "",
            "task_id": task["id"],
            "authority_packet_id": "packet-1",
            "budget_reservation_id": "reservation-1",
            "expected_message": "Governed external observability requires run_id.",
        },
        {
            "label": "task_id",
            "run_id": run["id"],
            "task_id": "",
            "authority_packet_id": "packet-1",
            "budget_reservation_id": "reservation-1",
            "expected_message": "Governed external observability requires task_id.",
        },
        {
            "label": "authority_packet_id",
            "run_id": run["id"],
            "task_id": task["id"],
            "authority_packet_id": "",
            "budget_reservation_id": "reservation-1",
            "expected_message": "authority_packet_id",
        },
        {
            "label": "reservation_id",
            "run_id": run["id"],
            "task_id": task["id"],
            "authority_packet_id": "packet-1",
            "budget_reservation_id": "",
            "expected_message": "budget_reservation_id",
        },
    ):
        try:
            _invoke_governed_text(
                router,
                run_id=case["run_id"],
                task_id=case["task_id"],
                authority_packet_id=case["authority_packet_id"],
                budget_reservation_id=case["budget_reservation_id"],
            )
        except APIRouterError as exc:
            assert case["expected_message"] in str(exc), case["label"]
            assert "FOREIGN KEY constraint failed" not in str(exc), case["label"]
        else:
            raise AssertionError(f"Expected APIRouterError for {case['label']}.")
        _assert_no_governed_observability_writes(
            store,
            run_id=run["id"],
            reservation_id="reservation-1",
        )


def test_api_router_rejects_invalid_task_packet_correlation_before_persistence(tmp_path, monkeypatch):
    repo_root = _prepare_repo(tmp_path)
    monkeypatch.chdir(repo_root)
    store = SessionStore(repo_root)
    invalid_packet = _governed_task_packet().model_dump()
    invalid_packet["request_id"] = ""
    task = store.create_task(
        "program-kanban",
        "Invalid task packet correlation",
        "Verify malformed task_packet correlation fails before persistence.",
        expected_artifact_path="projects/program-kanban/artifacts/router_invalid_packet.md",
        acceptance={"task_packet": invalid_packet},
    )
    run = store.create_run("program-kanban", task["id"])
    _create_active_reservation(store, reservation_id="reservation-1")
    router = APIRouter(repo_root, client=_FakeClient(), store=store)

    try:
        _invoke_governed_text(
            router,
            run_id=run["id"],
            task_id=task["id"],
        )
    except APIRouterError as exc:
        assert "Delegated execution TaskPacket token_budget authority is invalid" in str(exc)
        assert "request_id must match req_<12 lowercase hex>" in str(exc)
        assert "FOREIGN KEY constraint failed" not in str(exc)
    else:
        raise AssertionError("Expected APIRouterError for malformed task_packet_id.")

    _assert_no_governed_observability_writes(
        store,
        run_id=run["id"],
        reservation_id="reservation-1",
    )
