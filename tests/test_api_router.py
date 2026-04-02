from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from agents.api_router import APIRouter, APIRouterError
from agents.cost_tracker import CostTracker
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


def _make_response(output_text: str = '{"ok": true}', response_id: str = "resp_test"):
    return SimpleNamespace(
        id=response_id,
        output_text=output_text,
        usage={
            "input_tokens": 120,
            "input_tokens_details": {"cached_tokens": 20},
            "output_tokens": 40,
            "output_tokens_details": {"reasoning_tokens": 8},
        },
    )


class _FakeClient:
    def __init__(self):
        self.responses = _FakeResponses()


def _create_active_reservation(store, *, reservation_id: str, priority_class: str = "P1", reserved_max_tokens: int = 1000):
    return store.sync_execution_job_reservation(
        job_id=reservation_id,
        priority_class=priority_class,
        reserved_max_tokens=reserved_max_tokens,
        reservation_status="reserved",
    )


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
        budget_max_tokens=1000,
        budget_reservation_id="reservation-1",
        retry_limit=1,
        early_stop_rule="stop_on_first_success",
    )

    evidence = store.get_run_evidence(run["id"])
    packet = evidence["execution_packets"][0]

    assert result.output_text == '{"ok": true}'
    assert packet["packet_id"] == "packet-1"
    assert packet["job_id"] == "job-1"
    assert packet["priority_class"] == "P1"
    assert packet["budget_reservation_id"] == "reservation-1"
    assert packet["budget_max_tokens"] == 1000
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


def test_api_router_enforces_retry_limit_for_delegated_packets(tmp_path, monkeypatch):
    repo_root = _prepare_repo(tmp_path)
    monkeypatch.chdir(repo_root)
    store = SessionStore(repo_root)
    task = store.create_task(
        "program-kanban",
        "Delegated retry cap",
        "Verify delegated packets stop at the configured retry limit.",
        expected_artifact_path="projects/program-kanban/artifacts/router_retry.md",
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
            budget_max_tokens=1000,
            budget_reservation_id="reservation-1",
            retry_limit=1,
            early_stop_rule="stop_on_first_success",
        )
    except APIRouterError as exc:
        assert "transient-2" in str(exc)
    else:
        raise AssertionError("Expected delegated packet to stop at the retry limit.")

    assert len(client.responses.calls) == 2
    packet = store.get_run_evidence(run["id"])["execution_packets"][0]
    assert packet["retry_count"] == 1
    assert packet["stop_reason"] == "retry_limit_exceeded"
    assert packet["escalation_target"] == "tier_1_senior"
    assert packet["status"] == "failed"


def test_api_router_single_pass_only_stops_after_first_attempt(tmp_path, monkeypatch):
    repo_root = _prepare_repo(tmp_path)
    monkeypatch.chdir(repo_root)
    store = SessionStore(repo_root)
    task = store.create_task(
        "program-kanban",
        "Delegated early stop",
        "Verify single-pass delegated packets stop after one attempt.",
        expected_artifact_path="projects/program-kanban/artifacts/router_stop.md",
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
            budget_max_tokens=1000,
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
            budget_max_tokens=1000,
            budget_reservation_id="reservation-1",
            retry_limit=1,
            early_stop_rule="stop-on-sufficient-output",
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
        budget_max_tokens=1000,
        budget_reservation_id="reservation-1",
        retry_limit=1,
        early_stop_rule="stop-on-sufficient-output",
    )

    assert result.output_text == '{"ok": true}'
    assert client.responses.calls
    assert client.responses.calls[0]["model"] == "gpt-5.4-mini"


def test_api_router_rejects_delegated_packet_without_active_reservation(tmp_path, monkeypatch):
    repo_root = _prepare_repo(tmp_path)
    monkeypatch.chdir(repo_root)
    store = SessionStore(repo_root)
    task = store.create_task(
        "program-kanban",
        "API router reservation gate",
        "Verify delegated packets fail closed without an active reservation.",
        expected_artifact_path="projects/program-kanban/artifacts/router_reservation_gate.md",
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
            budget_max_tokens=1000,
            budget_reservation_id="reservation-1",
            retry_limit=1,
            early_stop_rule="stop-on-sufficient-output",
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
    )
    run = store.create_run("program-kanban", task["id"])
    store.sync_execution_job_reservation(
        job_id="reservation-1",
        priority_class="P1",
        reserved_max_tokens=1000,
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
            budget_max_tokens=1000,
            budget_reservation_id="reservation-1",
            retry_limit=1,
            early_stop_rule="stop-on-sufficient-output",
        )
    except APIRouterError as exc:
        assert "active budget reservation" in str(exc)
    else:
        raise AssertionError("Expected delegated packet with an inactive reservation to be rejected.")

    assert not client.responses.calls
