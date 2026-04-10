from __future__ import annotations

import json
from pathlib import Path

from click.testing import CliRunner

from agents.orchestrator import Orchestrator
from intake.compiler import compile_task_packet
from intake.gateway import classify_operator_request
from scripts import cli


def _prepare_repo(tmp_path: Path) -> None:
    (tmp_path / "projects" / "tactics-game" / "execution").mkdir(parents=True)
    (tmp_path / "projects" / "tactics-game" / "governance").mkdir(parents=True)
    (tmp_path / "projects" / "program-kanban" / "governance").mkdir(parents=True)
    (tmp_path / "sessions").mkdir(parents=True)
    (tmp_path / "governance").mkdir(parents=True)
    (tmp_path / "memory").mkdir(parents=True)
    (tmp_path / "agents").mkdir(parents=True)
    for name in ["FRAMEWORK.md", "GOVERNANCE_RULES.md", "VISION.md", "MODEL_REASONING_MATRIX.md", "MEMORY_MAP.md"]:
        (tmp_path / "governance" / name).write_text(f"# {name}\n", encoding="utf-8")
    (tmp_path / "projects" / "tactics-game" / "governance" / "PROJECT_BRIEF.md").write_text("# Brief\n", encoding="utf-8")
    (tmp_path / "projects" / "program-kanban" / "governance" / "PROJECT_BRIEF.md").write_text("# Brief\n", encoding="utf-8")
    (tmp_path / "memory" / "framework_health.json").write_text("{}\n", encoding="utf-8")
    (tmp_path / "memory" / "session_summaries.json").write_text("[]\n", encoding="utf-8")
    for name in ["prompt_specialist.py", "orchestrator.py", "pm.py", "architect.py", "developer.py", "design.py", "qa.py"]:
        (tmp_path / "agents" / name).write_text("# placeholder\n", encoding="utf-8")


class _DummyClient:
    async def close(self) -> None:
        return None


def test_cli_request_routes_through_ingress_first(monkeypatch):
    runner = CliRunner()
    captured: dict[str, object] = {}

    class _DummyOrchestrator:
        async def intake_request(self, *args, **kwargs):
            raise AssertionError("CLI should not bypass ingress with raw-text intake calls.")

    async def _fake_intake_operator_request(orchestrator, project_name: str, user_text: str):
        captured["project_name"] = project_name
        captured["user_text"] = user_text
        captured["orchestrator_type"] = orchestrator.__class__.__name__
        return {
            "gateway_decision": {
                "schema_version": "intent_decision_v1",
                "decision": "ROUTE_TASK",
                "intent": "TASK",
                "contains_task_request": True,
                "contains_policy_request": False,
                "contains_status_request": False,
                "safe_to_route": True,
                "reason_codes": ["task_request_detected"],
                "normalized_request": "Implement the gateway",
            },
            "task": {"id": "TASK-1"},
        }

    monkeypatch.setattr(cli, "_orchestrator", lambda: _DummyOrchestrator())
    monkeypatch.setattr(cli, "intake_operator_request", _fake_intake_operator_request)

    result = runner.invoke(cli.cli, ["request", "--project", "program-kanban", "Implement", "the", "gateway"])

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["gateway_decision"]["decision"] == "ROUTE_TASK"
    assert captured["project_name"] == "program-kanban"
    assert captured["user_text"] == "Implement the gateway"


def test_cli_task_create_requires_task_packet_file():
    runner = CliRunner()

    result = runner.invoke(
        cli.cli,
        ["task", "create", "--project", "program-kanban", "--title", "Implement gateway", "--details", "Build it"],
    )

    assert result.exit_code != 0
    assert "--task-packet-file" in result.output


def test_cli_run_fails_closed_when_next_task_has_no_task_packet(tmp_path, monkeypatch):
    _prepare_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setattr("agents.role_base.create_model_client", lambda role: _DummyClient())

    orchestrator = Orchestrator(tmp_path)
    orchestrator.store.create_task(
        "tactics-game",
        "Legacy queued task",
        "CLI run should fail closed without a TaskPacket.",
        objective="CLI run should fail closed without a TaskPacket.",
    )

    runner = CliRunner()
    monkeypatch.setattr(cli, "_orchestrator", lambda: orchestrator)
    result = runner.invoke(cli.cli, ["run", "--project", "tactics-game"])

    assert result.exit_code != 0
    assert isinstance(result.exception, RuntimeError)
    assert "TaskPacket" in str(result.exception)


def test_cli_task_create_persists_explicit_task_packet(tmp_path, monkeypatch):
    runner = CliRunner()
    packet = compile_task_packet(classify_operator_request("Implement the gateway"))
    packet_file = tmp_path / "task_packet.json"
    packet_file.write_text(json.dumps(packet.model_dump(), ensure_ascii=True), encoding="utf-8")
    captured: dict[str, object] = {}

    class _DummyStore:
        def create_task(self, project_name: str, title: str, details: str, **kwargs):
            captured["project_name"] = project_name
            captured["title"] = title
            captured["details"] = details
            captured["acceptance"] = kwargs.get("acceptance")
            return {"id": "TASK-1", "project_name": project_name}

    class _DummyOrchestrator:
        store = _DummyStore()

    monkeypatch.setattr(cli, "_orchestrator", lambda: _DummyOrchestrator())

    result = runner.invoke(
        cli.cli,
        [
            "task",
            "create",
            "--project",
            "program-kanban",
            "--title",
            "Implement gateway",
            "--details",
            "Build it",
            "--task-packet-file",
            str(packet_file),
        ],
    )

    assert result.exit_code == 0
    assert captured["project_name"] == "program-kanban"
    assert captured["acceptance"]["task_packet"]["schema_version"] == "task_packet_v1"
