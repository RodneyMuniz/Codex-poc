from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

from governance.rules import load_policies
from intake.models import PolicyAuditEvent, PolicyProposal
from intake.policy_store import (
    append_policy_audit_event,
    load_policy_proposal,
    write_policy_proposal,
)
from workspace_root import ensure_authoritative_workspace_path, ensure_authoritative_workspace_root


SUPPORTED_POLICY_TARGETS = {
    "CONSENSUS_REVIEW_VOTES_REQUIRED": "governance/rules.yml",
}


def _utc_now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def _normalize_actor(actor: str) -> str:
    collapsed = " ".join((actor or "").split())
    if not collapsed:
        raise ValueError("actor is required.")
    if len(collapsed) > 160:
        raise ValueError("actor must be 160 characters or fewer.")
    return collapsed


def _normalize_source(source: str) -> str:
    collapsed = " ".join((source or "").split())
    if not collapsed:
        raise ValueError("source is required.")
    if len(collapsed) > 160:
        raise ValueError("source must be 160 characters or fewer.")
    return collapsed


def _rules_path(repo_root: str | Path) -> Path:
    root = ensure_authoritative_workspace_root(repo_root, label="policy apply repo_root")
    return ensure_authoritative_workspace_path(root / "governance" / "rules.yml", label="policy rules path")


def _load_rules_payload(rules_path: Path) -> dict[str, Any]:
    if not rules_path.exists():
        raise FileNotFoundError("Supported policy target governance/rules.yml does not exist.")
    payload = yaml.safe_load(rules_path.read_text(encoding="utf-8")) or {}
    if not isinstance(payload, dict):
        raise RuntimeError("governance/rules.yml must parse to a mapping.")
    return payload


def _write_rules_payload(rules_path: Path, payload: dict[str, Any]) -> None:
    rules_path.write_text(
        yaml.safe_dump(payload, sort_keys=False, allow_unicode=False),
        encoding="utf-8",
    )
    load_policies.cache_clear()


def _proposal_audit_event(
    proposal: PolicyProposal,
    *,
    action: str,
    prior_status: str | None,
    new_status: str,
    actor: str,
    source: str,
    result: str | None = None,
) -> PolicyAuditEvent:
    return PolicyAuditEvent(
        proposal_id=proposal.proposal_id,
        action=action,  # type: ignore[arg-type]
        prior_status=prior_status,  # type: ignore[arg-type]
        new_status=new_status,  # type: ignore[arg-type]
        actor=actor,
        source=source,
        timestamp=_utc_now(),
        target_kind=proposal.target_kind,
        result=result,
    )


def approve_policy_proposal(
    repo_root: str | Path,
    proposal_id: str,
    *,
    actor: str,
    source: str = "governance_plane",
) -> dict[str, Any]:
    normalized_actor = _normalize_actor(actor)
    normalized_source = _normalize_source(source)
    proposal = load_policy_proposal(repo_root, proposal_id)
    if proposal.status != "PROPOSED":
        raise ValueError("Only PROPOSED proposals may be approved.")

    updated = proposal.model_copy(
        update={
            "status": "APPROVED",
            "approved_by": normalized_actor,
            "approved_at": _utc_now(),
        }
    )
    proposal_path = write_policy_proposal(repo_root, updated)
    audit_path = append_policy_audit_event(
        repo_root,
        _proposal_audit_event(
            updated,
            action="APPROVE",
            prior_status="PROPOSED",
            new_status="APPROVED",
            actor=normalized_actor,
            source=normalized_source,
        ),
    )
    return {
        "status": "approved",
        "proposal_id": updated.proposal_id,
        "path": str(proposal_path),
        "audit_path": str(audit_path),
        "proposal": updated.model_dump(),
    }


def reject_policy_proposal(
    repo_root: str | Path,
    proposal_id: str,
    *,
    actor: str,
    source: str = "governance_plane",
) -> dict[str, Any]:
    normalized_actor = _normalize_actor(actor)
    normalized_source = _normalize_source(source)
    proposal = load_policy_proposal(repo_root, proposal_id)
    if proposal.status != "PROPOSED":
        raise ValueError("Only PROPOSED proposals may be rejected.")

    updated = proposal.model_copy(
        update={
            "status": "REJECTED",
            "rejected_by": normalized_actor,
            "rejected_at": _utc_now(),
        }
    )
    proposal_path = write_policy_proposal(repo_root, updated)
    audit_path = append_policy_audit_event(
        repo_root,
        _proposal_audit_event(
            updated,
            action="REJECT",
            prior_status="PROPOSED",
            new_status="REJECTED",
            actor=normalized_actor,
            source=normalized_source,
        ),
    )
    return {
        "status": "rejected",
        "proposal_id": updated.proposal_id,
        "path": str(proposal_path),
        "audit_path": str(audit_path),
        "proposal": updated.model_dump(),
    }


def _apply_supported_policy_change(repo_root: str | Path, proposal: PolicyProposal) -> tuple[str, str]:
    if proposal.target_kind != "CONSENSUS_REVIEW_VOTES_REQUIRED" or proposal.target_file != SUPPORTED_POLICY_TARGETS["CONSENSUS_REVIEW_VOTES_REQUIRED"]:
        raise ValueError("Policy proposal target is unsupported for v1 apply.")
    if proposal.requested_value is None:
        raise ValueError("Supported policy proposal is missing requested_value.")

    rules_path = _rules_path(repo_root)
    payload = _load_rules_payload(rules_path)
    consensus = payload.get("consensus") or {}
    if not isinstance(consensus, dict):
        raise RuntimeError("governance/rules.yml consensus section must be a mapping.")
    prior_value = consensus.get("review_votes_required")
    consensus["review_votes_required"] = proposal.requested_value
    payload["consensus"] = consensus
    _write_rules_payload(rules_path, payload)
    result = (
        "Applied governance/rules.yml consensus.review_votes_required "
        f"from {prior_value} to {proposal.requested_value}."
    )
    return (str(rules_path), result)


def apply_policy_proposal(
    repo_root: str | Path,
    proposal_id: str,
    *,
    actor: str,
    source: str = "governance_plane",
) -> dict[str, Any]:
    normalized_actor = _normalize_actor(actor)
    normalized_source = _normalize_source(source)
    proposal = load_policy_proposal(repo_root, proposal_id)
    if proposal.status != "APPROVED":
        raise ValueError("Only APPROVED proposals may be applied.")

    try:
        target_path, apply_result = _apply_supported_policy_change(repo_root, proposal)
    except Exception as exc:
        append_policy_audit_event(
            repo_root,
            _proposal_audit_event(
                proposal,
                action="APPLY_FAILED",
                prior_status="APPROVED",
                new_status="APPROVED",
                actor=normalized_actor,
                source=normalized_source,
                result=str(exc),
            ),
        )
        raise

    updated = proposal.model_copy(
        update={
            "status": "APPLIED",
            "applied_by": normalized_actor,
            "applied_at": _utc_now(),
            "apply_result": apply_result,
        }
    )
    proposal_path = write_policy_proposal(repo_root, updated)
    audit_path = append_policy_audit_event(
        repo_root,
        _proposal_audit_event(
            updated,
            action="APPLY",
            prior_status="APPROVED",
            new_status="APPLIED",
            actor=normalized_actor,
            source=normalized_source,
            result=apply_result,
        ),
    )
    return {
        "status": "applied",
        "proposal_id": updated.proposal_id,
        "path": str(proposal_path),
        "audit_path": str(audit_path),
        "target_path": target_path,
        "apply_result": apply_result,
        "proposal": updated.model_dump(),
    }
