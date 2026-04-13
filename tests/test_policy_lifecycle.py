from __future__ import annotations

import asyncio
import json
from pathlib import Path

import pytest
import yaml

from governance.policy_lifecycle import apply_policy_proposal, approve_policy_proposal
from intake.compiler import compile_policy_proposal
from intake.gateway import classify_operator_request
from intake.ingress import intake_operator_request
from intake.policy_store import load_policy_proposal, record_policy_proposal
from workspace_root import (
    AUTHORITATIVE_ROOT_ENV,
    KNOWN_DUPLICATE_ROOT_ENV,
    WorkspaceRootAuthorityError,
    write_workspace_authority_marker,
)


def _prepare_repo(tmp_path: Path) -> None:
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
    (tmp_path / "governance" / "rules.yml").write_text(
        "roles:\n  orchestrator:\n    allowed_states: [Idea]\n    tools: [api_responses_create]\n"
        "transitions:\n  Idea: [Spec]\n"
        "forbidden_patterns:\n  - bypass policy\n"
        "consensus:\n  review_votes_required: 2\n",
        encoding="utf-8",
    )


def _supported_policy_proposal():
    return compile_policy_proposal(
        classify_operator_request("Change governance review votes required to 3")
    )


def _unsupported_policy_proposal():
    return compile_policy_proposal(
        classify_operator_request("Allow the architect agent to edit governance rules directly")
    )


def test_proposed_policy_proposal_transitions_to_approved(tmp_path):
    _prepare_repo(tmp_path)
    proposal = _supported_policy_proposal()
    record_policy_proposal(tmp_path, proposal)

    result = approve_policy_proposal(tmp_path, proposal.proposal_id, actor="governance_admin")

    stored = load_policy_proposal(tmp_path, proposal.proposal_id)
    assert result["status"] == "approved"
    assert stored.status == "APPROVED"
    assert stored.approved_by == "governance_admin"
    assert stored.approved_at is not None


def test_unapproved_policy_proposal_cannot_be_applied(tmp_path):
    _prepare_repo(tmp_path)
    proposal = _supported_policy_proposal()
    record_policy_proposal(tmp_path, proposal)

    with pytest.raises(ValueError, match="Only APPROVED proposals may be applied"):
        apply_policy_proposal(tmp_path, proposal.proposal_id, actor="governance_admin")


def test_approved_policy_proposal_applies_bounded_rules_change(tmp_path):
    _prepare_repo(tmp_path)
    proposal = _supported_policy_proposal()
    record_policy_proposal(tmp_path, proposal)
    approve_policy_proposal(tmp_path, proposal.proposal_id, actor="governance_admin")

    result = apply_policy_proposal(tmp_path, proposal.proposal_id, actor="governance_admin")

    stored = load_policy_proposal(tmp_path, proposal.proposal_id)
    rules_payload = yaml.safe_load((tmp_path / "governance" / "rules.yml").read_text(encoding="utf-8"))
    assert result["status"] == "applied"
    assert result["target_path"] == str(tmp_path / "governance" / "rules.yml")
    assert stored.status == "APPLIED"
    assert stored.apply_result == result["apply_result"]
    assert rules_payload["consensus"]["review_votes_required"] == 3


def test_unsupported_policy_target_fails_closed(tmp_path):
    _prepare_repo(tmp_path)
    proposal = _unsupported_policy_proposal()
    record_policy_proposal(tmp_path, proposal)
    approve_policy_proposal(tmp_path, proposal.proposal_id, actor="governance_admin")

    with pytest.raises(ValueError, match="unsupported for v1 apply"):
        apply_policy_proposal(tmp_path, proposal.proposal_id, actor="governance_admin")

    stored = load_policy_proposal(tmp_path, proposal.proposal_id)
    audit_lines = (tmp_path / "governance" / "policy_proposals" / f"{proposal.proposal_id}.audit.jsonl").read_text(
        encoding="utf-8"
    ).splitlines()
    failed_apply_event = json.loads(audit_lines[-1])
    assert stored.status == "APPROVED"
    assert failed_apply_event["action"] == "APPLY_FAILED"
    assert failed_apply_event["new_status"] == "APPROVED"


def test_workspace_root_authority_still_applies_to_policy_apply_storage(tmp_path, monkeypatch):
    authoritative_root = tmp_path / "authoritative"
    duplicate_root = tmp_path / "duplicate"
    authoritative_root.mkdir()
    duplicate_root.mkdir()
    _prepare_repo(authoritative_root)
    write_workspace_authority_marker(authoritative_root, repo_name="authoritative-test-root")
    monkeypatch.setenv(AUTHORITATIVE_ROOT_ENV, str(authoritative_root))
    monkeypatch.setenv(KNOWN_DUPLICATE_ROOT_ENV, str(duplicate_root))
    proposal = _supported_policy_proposal()
    record_policy_proposal(authoritative_root, proposal)

    with pytest.raises(WorkspaceRootAuthorityError, match="known non-authoritative duplicate workspace root"):
        approve_policy_proposal(duplicate_root, proposal.proposal_id, actor="governance_admin")


def test_policy_lifecycle_audit_artifacts_are_recorded(tmp_path):
    _prepare_repo(tmp_path)
    proposal = _supported_policy_proposal()
    record = record_policy_proposal(tmp_path, proposal)
    approve_policy_proposal(tmp_path, proposal.proposal_id, actor="governance_admin", source="policy_admin_api")
    apply_policy_proposal(tmp_path, proposal.proposal_id, actor="governance_admin", source="policy_admin_api")

    audit_path = Path(record["audit_path"])
    events = [json.loads(line) for line in audit_path.read_text(encoding="utf-8").splitlines()]
    assert [event["action"] for event in events] == ["PROPOSE", "APPROVE", "APPLY"]
    assert events[1]["prior_status"] == "PROPOSED"
    assert events[1]["new_status"] == "APPROVED"
    assert events[1]["actor"] == "governance_admin"
    assert events[1]["source"] == "policy_admin_api"
    assert events[2]["new_status"] == "APPLIED"
    assert "review_votes_required" in events[2]["result"]


def test_supported_policy_update_is_reachable_end_to_end_via_public_ingress(tmp_path):
    _prepare_repo(tmp_path)

    class _PolicyIngressOrchestrator:
        def __init__(self, repo_root: Path) -> None:
            self.repo_root = repo_root

    orchestrator = _PolicyIngressOrchestrator(tmp_path)

    intake_result = asyncio.run(
        intake_operator_request(
            orchestrator,
            "program-kanban",
            "Change governance review votes required to 3",
        )
    )

    assert intake_result["status"] == "proposal_recorded"
    assert intake_result["gateway_decision"]["decision"] == "ROUTE_ADMIN"
    assert intake_result["gateway_decision"]["intent"] == "POLICY_UPDATE"
    assert intake_result["task"] is None
    assert intake_result["packet"] is None
    assert intake_result["policy_proposal"]["target_kind"] == "CONSENSUS_REVIEW_VOTES_REQUIRED"
    assert intake_result["policy_proposal"]["requested_value"] == 3

    proposal_id = intake_result["policy_proposal"]["proposal_id"]
    approve_policy_proposal(tmp_path, proposal_id, actor="governance_admin", source="policy_admin_api")
    apply_result = apply_policy_proposal(tmp_path, proposal_id, actor="governance_admin", source="policy_admin_api")

    stored = load_policy_proposal(tmp_path, proposal_id)
    rules_payload = yaml.safe_load((tmp_path / "governance" / "rules.yml").read_text(encoding="utf-8"))
    audit_path = Path(intake_result["proposal_record"]["audit_path"])
    audit_events = [json.loads(line) for line in audit_path.read_text(encoding="utf-8").splitlines()]

    assert apply_result["status"] == "applied"
    assert stored.status == "APPLIED"
    assert rules_payload["consensus"]["review_votes_required"] == 3
    assert [event["action"] for event in audit_events] == ["PROPOSE", "APPROVE", "APPLY"]
    assert audit_events[-1]["new_status"] == "APPLIED"
    assert "review_votes_required" in audit_events[-1]["result"]
