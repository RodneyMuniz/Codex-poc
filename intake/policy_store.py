from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from intake.models import PolicyAuditEvent, PolicyProposal
from workspace_root import ensure_authoritative_workspace_path, ensure_authoritative_workspace_root


def policy_proposals_dir(repo_root: str | Path) -> Path:
    root = ensure_authoritative_workspace_root(repo_root, label="policy proposal repo_root")
    return ensure_authoritative_workspace_path(root / "governance" / "policy_proposals", label="policy proposals path")


def _utc_now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def policy_proposal_path_from_id(repo_root: str | Path, proposal_id: str) -> Path:
    return ensure_authoritative_workspace_path(
        policy_proposals_dir(repo_root) / f"{proposal_id}.json",
        label="policy proposal path",
    )


def policy_proposal_path(repo_root: str | Path, proposal: PolicyProposal) -> Path:
    return policy_proposal_path_from_id(repo_root, proposal.proposal_id)


def policy_proposal_audit_path(repo_root: str | Path, proposal_id: str) -> Path:
    return ensure_authoritative_workspace_path(
        policy_proposals_dir(repo_root) / f"{proposal_id}.audit.jsonl",
        label="policy proposal audit path",
    )


def load_policy_proposal(repo_root: str | Path, proposal_id: str) -> PolicyProposal:
    proposal_path = policy_proposal_path_from_id(repo_root, proposal_id)
    if not proposal_path.exists():
        raise FileNotFoundError(f"Policy proposal {proposal_id} does not exist.")
    payload = json.loads(proposal_path.read_text(encoding="utf-8"))
    return PolicyProposal.model_validate(payload)


def write_policy_proposal(repo_root: str | Path, proposal: PolicyProposal) -> Path:
    validated = PolicyProposal.model_validate(proposal.model_dump())
    proposals_root = policy_proposals_dir(repo_root)
    proposals_root.mkdir(parents=True, exist_ok=True)
    proposal_path = policy_proposal_path(repo_root, validated)
    proposal_path.write_text(
        json.dumps(validated.model_dump(), ensure_ascii=True, indent=2) + "\n",
        encoding="utf-8",
    )
    return proposal_path


def append_policy_audit_event(repo_root: str | Path, event: PolicyAuditEvent) -> Path:
    validated = PolicyAuditEvent.model_validate(event.model_dump())
    proposals_root = policy_proposals_dir(repo_root)
    proposals_root.mkdir(parents=True, exist_ok=True)
    audit_path = policy_proposal_audit_path(repo_root, validated.proposal_id)
    with audit_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(validated.model_dump(), ensure_ascii=True) + "\n")
    return audit_path


def record_policy_proposal(repo_root: str | Path, proposal: PolicyProposal) -> dict[str, Any]:
    validated = PolicyProposal.model_validate(proposal.model_dump())
    proposal_path = write_policy_proposal(repo_root, validated)
    audit_path = append_policy_audit_event(
        repo_root,
        PolicyAuditEvent(
            proposal_id=validated.proposal_id,
            action="PROPOSE",
            prior_status=None,
            new_status="PROPOSED",
            actor=validated.created_by,
            source="policy_proposal_record",
            timestamp=_utc_now(),
            target_kind=validated.target_kind,
        ),
    )
    return {
        "status": "recorded",
        "proposal_id": validated.proposal_id,
        "path": str(proposal_path),
        "audit_path": str(audit_path),
        "proposal": validated.model_dump(),
    }
