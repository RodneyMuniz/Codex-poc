from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agents.orchestrator import Orchestrator, run_async
from intake.ingress import dispatch_operator_request, preview_operator_request
from workspace_root import ensure_authoritative_workspace_root


def _orchestrator() -> Orchestrator:
    ensure_authoritative_workspace_root(ROOT, label="operator_api root")
    return Orchestrator(ROOT)


def _routing_catalog() -> dict[str, Any]:
    try:
        from agents.config import routing_catalog
    except ImportError:
        return {}
    return routing_catalog()


def main() -> None:
    parser = argparse.ArgumentParser(description="Program Kanban operator-client service wrapper.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    preview = subparsers.add_parser("preview")
    preview.add_argument("--project", required=True)
    preview.add_argument("--text", required=True)
    preview.add_argument("--clarification", default=None)

    dispatch = subparsers.add_parser("dispatch")
    dispatch.add_argument("--project", required=True)
    dispatch.add_argument("--text", required=True)
    dispatch.add_argument("--clarification", default=None)

    approve = subparsers.add_parser("approve")
    approve.add_argument("--approval-id", required=True)
    approve.add_argument("--note", default=None)

    approve_resume = subparsers.add_parser("approve-resume")
    approve_resume.add_argument("--approval-id", required=True)
    approve_resume.add_argument("--note", default=None)

    reject = subparsers.add_parser("reject")
    reject.add_argument("--approval-id", required=True)
    reject.add_argument("--note", default=None)

    resume = subparsers.add_parser("resume")
    resume.add_argument("--run-id", required=True)

    run_details = subparsers.add_parser("run-details")
    run_details.add_argument("--run-id", required=True)

    task_details = subparsers.add_parser("task-details")
    task_details.add_argument("--task-id", required=True)

    trust_worklist = subparsers.add_parser("trust-worklist")
    trust_worklist.add_argument("--include-trusted", action="store_true")

    record_reconciliation = subparsers.add_parser("record-reconciliation")
    record_reconciliation.add_argument("--external-call-id", required=True)
    record_reconciliation.add_argument("--provider-request-id", required=True)
    record_reconciliation.add_argument(
        "--reconciliation-state",
        required=True,
        choices=["reconciliation_pending", "reconciled", "reconciliation_failed"],
    )
    record_reconciliation.add_argument("--reconciliation-evidence-source", required=True)
    record_reconciliation.add_argument("--checked-at", default=None)
    record_reconciliation.add_argument("--reason-code", default=None)

    subparsers.add_parser("routing-catalog")

    try:
        args = parser.parse_args()
        orchestrator = _orchestrator()
        if args.command == "preview":
            payload = run_async(preview_operator_request(orchestrator, args.project, args.text, args.clarification))
        elif args.command == "dispatch":
            payload = run_async(dispatch_operator_request(orchestrator, args.project, args.text, args.clarification))
            run_result = payload.get("run_result", {})
            run_id = run_result.get("run_id")
            if run_id:
                payload["run_evidence"] = orchestrator.store.get_run_evidence(run_id)
            payload["routing_catalog"] = _routing_catalog()
        elif args.command == "approve":
            payload = orchestrator.approve(args.approval_id, args.note)
        elif args.command == "approve-resume":
            payload = run_async(orchestrator.approve_and_resume(args.approval_id, args.note))
            run_id = payload.get("run_id")
            if run_id:
                payload["run_evidence"] = orchestrator.store.get_run_evidence(run_id)
            payload["routing_catalog"] = _routing_catalog()
        elif args.command == "reject":
            payload = orchestrator.reject(args.approval_id, args.note)
        elif args.command == "resume":
            payload = run_async(orchestrator.resume_run(args.run_id))
            run_id = payload.get("run_id") or args.run_id
            payload["run_evidence"] = orchestrator.store.get_run_evidence(run_id)
            payload["routing_catalog"] = _routing_catalog()
        elif args.command == "run-details":
            payload = orchestrator.store.get_run_evidence(args.run_id)
            payload["routing_catalog"] = _routing_catalog()
        elif args.command == "task-details":
            payload = orchestrator.store.get_task_work_graph(args.task_id)
            payload["routing_catalog"] = _routing_catalog()
        elif args.command == "trust-worklist":
            worklist = orchestrator.store.list_governed_external_trust_worklist(
                include_trusted=bool(args.include_trusted)
            )
            payload = {
                "trust_worklist": worklist,
                "trust_worklist_count": len(worklist),
                "include_trusted_reconciled": bool(args.include_trusted),
            }
        elif args.command == "record-reconciliation":
            payload = orchestrator.store.record_governed_external_reconciliation(
                external_call_id=args.external_call_id,
                provider_request_id=args.provider_request_id,
                reconciliation_state=args.reconciliation_state,
                reconciliation_evidence_source=args.reconciliation_evidence_source,
                reconciliation_checked_at=args.checked_at,
                reconciliation_reason_code=args.reason_code,
            )
        else:
            payload = {"routes": _routing_catalog()}
    except Exception as exc:
        print(
            json.dumps(
                {
                    "error": str(exc),
                    "error_type": exc.__class__.__name__,
                },
                ensure_ascii=True,
            )
        )
        raise SystemExit(1) from exc

    print(json.dumps(payload, ensure_ascii=True))


if __name__ == "__main__":
    main()
