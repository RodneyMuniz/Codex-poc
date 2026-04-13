from __future__ import annotations

import asyncio
from types import SimpleNamespace

import pytest

from agents.cost_tracker import CostTracker
from agents.prompt_specialist import PromptSpecialistAgent
from agents.role_base import DelegatedExecutionBypassError
from agents.telemetry import TelemetryRecorder
from intake.compiler import compile_task_packet
from intake.gateway import classify_operator_request
from sessions import SessionStore


def _prepare_repo(tmp_path):
    (tmp_path / "projects" / "program-kanban" / "execution").mkdir(parents=True)
    (tmp_path / "projects" / "program-kanban" / "governance").mkdir(parents=True)
    (tmp_path / "projects" / "program-kanban" / "artifacts").mkdir(parents=True)
    (tmp_path / "sessions").mkdir(parents=True)
    (tmp_path / "governance").mkdir(parents=True)
    (tmp_path / "memory").mkdir(parents=True)
    (tmp_path / "memory" / "framework_health.json").write_text("{}\n", encoding="utf-8")
    (tmp_path / "memory" / "session_summaries.json").write_text("[]\n", encoding="utf-8")
    (tmp_path / "projects" / "program-kanban" / "governance" / "PROJECT_BRIEF.md").write_text("# Brief\n", encoding="utf-8")
    return tmp_path


def _task_packet():
    return compile_task_packet(classify_operator_request("Implement the governed API-first specialist flow"))


class _FakeModelClient:
    async def create(self, messages, json_output=None):
        raise AssertionError("StudioRoleAgent should route tracked execution through APIRouter by default.")

    async def close(self):
        return None


class _UngovernedLocalClient:
    async def create(self, messages, json_output=None):
        return SimpleNamespace(
            content=(
                '{"objective":"Local preview","details":"Use the non-governed local compatibility path.",'
                '"priority":"medium","requires_approval":false,"assumptions":[],"risks":[]}'
            ),
            usage=SimpleNamespace(prompt_tokens=12, completion_tokens=4),
        )

    async def close(self):
        return None


class _FakeAPIRouter:
    def __init__(self, repo_root, *, store, **kwargs):
        self.repo_root = repo_root
        self.store = store
        self.calls = []
        self.cost_tracker = CostTracker(repo_root=repo_root, store=store)

    def invoke_json(
        self,
        *,
        run_id,
        task_id,
        tier,
        system_prompt,
        user_prompt,
        source,
        lane="sync_api",
        route_family=None,
        schema=None,
        metadata=None,
        background=False,
        authority_packet_id=None,
        authority_job_id=None,
        authority_token=None,
        authority_schema_name=None,
        authority_execution_tier=None,
        authority_execution_lane=None,
        authority_delegated_work=False,
        priority_class=None,
        budget_max_tokens=None,
        budget_reservation_id=None,
        retry_limit=None,
        early_stop_rule=None,
    ):
        reservation = self.store.get_execution_job_reservation(str(budget_reservation_id or ""))
        self.calls.append(
            {
                "run_id": run_id,
                "task_id": task_id,
                "tier": tier,
                "system_prompt": system_prompt,
                "user_prompt": user_prompt,
                "source": source,
                "lane": lane,
                "route_family": route_family,
                "background": background,
                "authority_packet_id": authority_packet_id,
                "authority_job_id": authority_job_id,
                "authority_token": authority_token,
                "authority_schema_name": authority_schema_name,
                "authority_execution_tier": authority_execution_tier,
                "authority_execution_lane": authority_execution_lane,
                "authority_delegated_work": authority_delegated_work,
                "priority_class": priority_class,
                "budget_max_tokens": budget_max_tokens,
                "budget_reservation_id": budget_reservation_id,
                "retry_limit": retry_limit,
                "early_stop_rule": early_stop_rule,
                "reservation_status_at_call": reservation["reservation_status"] if reservation else None,
            }
        )
        output_text = (
            '{"objective":"Design intake packet","details":"Create a preview packet.","priority":"medium",'
            '"requires_approval":false,"assumptions":[],"risks":[]}'
        )
        estimate = self.cost_tracker.record_api_usage(
            run_id=run_id,
            task_id=task_id,
            source=source,
            model="gpt-5.4-mini",
            tier=tier,
            lane=lane,
            usage={
                "input_tokens": 111,
                "input_tokens_details": {"cached_tokens": 9},
                "output_tokens": 37,
                "output_tokens_details": {"reasoning_tokens": 4},
            },
            notes="agent_json via StudioRoleAgent",
        )
        routed = SimpleNamespace(
            model="gpt-5.4-mini",
            output_text=output_text,
            input_tokens=estimate.input_tokens,
            cached_input_tokens=estimate.cached_input_tokens,
            output_tokens=estimate.output_tokens,
            reasoning_tokens=estimate.reasoning_tokens,
            estimated_cost_usd=estimate.estimated_cost_usd,
        )
        parsed = schema.model_validate_json(output_text) if schema is not None else output_text
        return parsed, routed


def test_prompt_specialist_records_usage_events_and_execution_log(tmp_path, monkeypatch):
    repo_root = _prepare_repo(tmp_path)
    monkeypatch.chdir(repo_root)
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    fake_router = _FakeAPIRouter(repo_root, store=SessionStore(repo_root))
    monkeypatch.setattr("agents.role_base.OpenAIChatCompletionClient", _FakeModelClient)
    monkeypatch.setattr("agents.role_base.create_model_client", lambda role: _FakeModelClient())
    monkeypatch.setattr("agents.role_base.APIRouter", lambda *args, **kwargs: fake_router)

    store = fake_router.store
    telemetry = TelemetryRecorder(repo_root)
    agent = PromptSpecialistAgent(repo_root=repo_root, store=store, telemetry=telemetry)
    task = store.create_task(
        "program-kanban",
        "Preview usage",
        "Track prompt-specialist API usage.",
        acceptance={"task_packet": _task_packet().model_dump()},
    )
    run = store.create_run("program-kanban", task["id"])

    packet = asyncio.run(agent.process_input("Create a design intake preview.", run_id=run["id"], task_id=task["id"]))
    evidence = store.get_run_evidence(run["id"])
    reservation = store.get_execution_job_reservation(f"{run['id']}:reservation")

    assert packet.objective == "Design intake packet"
    assert len(fake_router.calls) == 1
    assert fake_router.calls[0]["tier"] == "tier_2_mid"
    assert fake_router.calls[0]["source"] == "PromptSpecialist"
    assert fake_router.calls[0]["lane"] == "sync_api"
    assert fake_router.calls[0]["reservation_status_at_call"] == "reserved"
    assert reservation is not None
    assert reservation["reservation_status"] == "reserved"
    assert reservation["run_id"] == run["id"]
    assert reservation["task_id"] == task["id"]
    assert len(evidence["usage_events"]) == 1
    assert evidence["usage_events"][0]["prompt_tokens"] == 111
    assert evidence["usage_events"][0]["completion_tokens"] == 37
    log_text = (repo_root / "governance" / "execution_logs.md").read_text(encoding="utf-8")
    assert task["id"] in log_text
    assert "PromptSpecialist" in log_text


def test_prompt_specialist_tracked_api_failure_does_not_fall_back_to_heuristic_packet(tmp_path, monkeypatch):
    repo_root = _prepare_repo(tmp_path)
    monkeypatch.chdir(repo_root)
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setattr("agents.role_base.OpenAIChatCompletionClient", _FakeModelClient)
    monkeypatch.setattr("agents.role_base.create_model_client", lambda role: _FakeModelClient())

    class _FailingAPIRouter:
        def __init__(self, repo_root, *, store, **kwargs):
            self.store = store

        def invoke_json(self, **kwargs):
            raise RuntimeError("api unavailable")

    monkeypatch.setattr("agents.role_base.APIRouter", lambda *args, **kwargs: _FailingAPIRouter(*args, **kwargs))

    store = SessionStore(repo_root)
    telemetry = TelemetryRecorder(repo_root)
    agent = PromptSpecialistAgent(repo_root=repo_root, store=store, telemetry=telemetry)
    task = store.create_task(
        "program-kanban",
        "Preview usage",
        "Track prompt-specialist API usage.",
        acceptance={"task_packet": _task_packet().model_dump()},
    )
    run = store.create_run("program-kanban", task["id"])

    with pytest.raises(RuntimeError, match="api unavailable"):
        asyncio.run(agent.process_input("Create a design intake preview.", run_id=run["id"], task_id=task["id"]))


def test_prompt_specialist_rejects_task_packet_backed_local_compatibility_path(tmp_path, monkeypatch):
    repo_root = _prepare_repo(tmp_path)
    monkeypatch.chdir(repo_root)
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setattr("agents.role_base.create_model_client", lambda role: _UngovernedLocalClient())

    store = SessionStore(repo_root)
    telemetry = TelemetryRecorder(repo_root)
    agent = PromptSpecialistAgent(repo_root=repo_root, store=store, telemetry=telemetry)
    task = store.create_task(
        "program-kanban",
        "Preview usage",
        "Track prompt-specialist API usage.",
        acceptance={"task_packet": _task_packet().model_dump()},
    )

    with pytest.raises(RuntimeError, match="non-governed only"):
        asyncio.run(agent.process_input("Create a design intake preview.", task_id=task["id"]))


def test_prompt_specialist_allows_ungoverned_local_compatibility_path(tmp_path, monkeypatch):
    repo_root = _prepare_repo(tmp_path)
    monkeypatch.chdir(repo_root)
    monkeypatch.setattr("agents.role_base.create_model_client", lambda role: _UngovernedLocalClient())

    store = SessionStore(repo_root)
    telemetry = TelemetryRecorder(repo_root)
    agent = PromptSpecialistAgent(repo_root=repo_root, store=store, telemetry=telemetry)

    packet = asyncio.run(agent.process_input("Create a design intake preview."))

    assert packet.objective == "Local preview"


def test_prompt_specialist_fails_closed_for_delegated_work_without_api_router(tmp_path, monkeypatch):
    repo_root = _prepare_repo(tmp_path)
    monkeypatch.chdir(repo_root)
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setattr("agents.role_base.create_model_client", lambda role: _FakeModelClient())

    store = SessionStore(repo_root)
    telemetry = TelemetryRecorder(repo_root)
    agent = PromptSpecialistAgent(repo_root=repo_root, store=store, telemetry=telemetry)
    task = store.create_task(
        "program-kanban",
        "Preview usage",
        "Track prompt-specialist API usage.",
        acceptance={"task_packet": _task_packet().model_dump()},
    )
    run = store.create_run("program-kanban", task["id"])

    with pytest.raises(DelegatedExecutionBypassError, match="api_router"):
        asyncio.run(agent.process_input("Create a design intake preview.", run_id=run["id"], task_id=task["id"]))
