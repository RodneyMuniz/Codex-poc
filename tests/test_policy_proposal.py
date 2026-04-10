from __future__ import annotations

import asyncio
import json
from pathlib import Path

import pytest

from agents.orchestrator import Orchestrator
from intake.compiler import compile_policy_proposal, compile_task_packet
from intake.gateway import classify_operator_request
from intake.ingress import dispatch_operator_request, intake_operator_request
from intake.models import PolicyProposal, TaskPacket


def _prepare_repo(tmp_path):
    (tmp_path / "projects" / "program-kanban" / "governance").mkdir(parents=True)
    (tmp_path / "projects" / "program-kanban" / "execution").mkdir(parents=True)
    (tmp_path / "sessions").mkdir(parents=True)
    (tmp_path / "governance").mkdir(parents=True)
    (tmp_path / "memory").mkdir(parents=True)
    (tmp_path / "agents").mkdir(parents=True)
    for name in ["FRAMEWORK.md", "GOVERNANCE_RULES.md", "VISION.md", "MODEL_REASONING_MATRIX.md", "MEMORY_MAP.md"]:
        (tmp_path / "governance" / name).write_text(f"# {name}\n", encoding="utf-8")
    (tmp_path / "projects" / "program-kanban" / "governance" / "PROJECT_BRIEF.md").write_text("# Brief\n", encoding="utf-8")
    (tmp_path / "memory" / "framework_health.json").write_text("{}\n", encoding="utf-8")
    (tmp_path / "memory" / "session_summaries.json").write_text("[]\n", encoding="utf-8")
    for name in ["prompt_specialist.py", "orchestrator.py", "pm.py", "architect.py", "developer.py", "design.py", "qa.py"]:
        (tmp_path / "agents" / name).write_text("# placeholder\n", encoding="utf-8")


class _DummyClient:
    async def close(self) -> None:
        return None


class _DummyPolicyIngressOrchestrator:
    def __init__(self, repo_root: Path) -> None:
        self.repo_root = repo_root

    async def intake_request(self, *args, **kwargs):
        raise AssertionError("Policy proposal ingress must not route into task intake.")

    async def dispatch_request(self, *args, **kwargs):
        raise AssertionError("Policy proposal ingress must not route into task dispatch.")


def test_policy_update_decision_compiles_to_valid_policy_proposal():
    decision = classify_operator_request("Allow the architect agent to edit governance rules directly")

    proposal = compile_policy_proposal(decision)

    assert proposal.schema_version == "policy_proposal_v1"
    assert proposal.source_intent == "POLICY_UPDATE"
    assert proposal.status == "PROPOSED"
    assert proposal.safe_for_execution_path is False
    assert proposal.target_kind == "UNSUPPORTED"
    assert proposal.requested_value is None
    assert proposal.requested_changes == [proposal.normalized_request]


def test_policy_update_does_not_compile_to_task_packet():
    decision = classify_operator_request("Allow the architect agent to edit governance rules directly")

    with pytest.raises(ValueError, match="Only safe ROUTE_TASK decisions"):
        compile_task_packet(decision)


def test_task_execution_path_rejects_policy_proposal_misuse(tmp_path, monkeypatch):
    _prepare_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setattr("agents.role_base.create_model_client", lambda role: _DummyClient())

    orchestrator = Orchestrator(tmp_path)
    proposal = compile_policy_proposal(
        classify_operator_request("Allow the architect agent to edit governance rules directly")
    )

    with pytest.raises(RuntimeError, match="validated TaskPacket"):
        asyncio.run(
            orchestrator.preview_request(
                "program-kanban",
                task_packet=proposal,  # type: ignore[arg-type]
            )
        )


def test_policy_proposal_is_recorded_in_governance_storage_path(tmp_path):
    _prepare_repo(tmp_path)
    orchestrator = _DummyPolicyIngressOrchestrator(tmp_path)

    result = asyncio.run(
        intake_operator_request(
            orchestrator,
            "program-kanban",
            "Allow the architect agent to edit governance rules directly",
        )
    )

    assert result["status"] == "proposal_recorded"
    assert result["task"] is None
    assert result["packet"] is None
    record = result["proposal_record"]
    proposal_path = Path(record["path"])
    assert proposal_path.exists()
    assert proposal_path.parent == tmp_path / "governance" / "policy_proposals"
    assert Path(record["audit_path"]).exists()
    stored = json.loads(proposal_path.read_text(encoding="utf-8"))
    assert stored["schema_version"] == "policy_proposal_v1"
    assert stored["safe_for_execution_path"] is False


def test_task_decision_still_uses_task_packet_path(tmp_path):
    _prepare_repo(tmp_path)
    captured: dict[str, object] = {}

    class _DummyTaskIngressOrchestrator:
        repo_root = tmp_path

        async def dispatch_request(self, project_name: str, *, task_packet: TaskPacket):
            captured["project_name"] = project_name
            captured["task_packet"] = task_packet
            return {"task": {"id": "TASK-1"}, "run_result": {"run_status": "queued"}}

    result = asyncio.run(
        dispatch_operator_request(
            _DummyTaskIngressOrchestrator(),
            "program-kanban",
            "Implement the gateway",
        )
    )

    assert result["run_result"]["run_status"] == "queued"
    assert isinstance(captured["task_packet"], TaskPacket)
    assert (tmp_path / "governance" / "policy_proposals").exists() is False


def test_mixed_request_creates_neither_proposal_nor_task(tmp_path):
    _prepare_repo(tmp_path)
    orchestrator = _DummyPolicyIngressOrchestrator(tmp_path)

    result = asyncio.run(
        dispatch_operator_request(
            orchestrator,
            "program-kanban",
            "Change governance review votes required to 3 and implement the routing flow",
        )
    )

    assert result["gateway_decision"]["decision"] == "NEEDS_SPLIT"
    assert result["task"] is None
    assert "policy_proposal" not in result
    assert "proposal_record" not in result
    assert (tmp_path / "governance" / "policy_proposals").exists() is False
