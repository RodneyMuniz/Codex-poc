from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agents.config import routing_catalog
from agents.orchestrator import Orchestrator, run_async


def _orchestrator() -> Orchestrator:
    return Orchestrator(ROOT)


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

    subparsers.add_parser("routing-catalog")

    args = parser.parse_args()
    orchestrator = _orchestrator()

    try:
        if args.command == "preview":
            payload = run_async(orchestrator.preview_request(args.project, args.text, args.clarification))
        elif args.command == "dispatch":
            payload = run_async(orchestrator.dispatch_request(args.project, args.text, args.clarification))
            run_result = payload.get("run_result", {})
            run_id = run_result.get("run_id")
            if run_id:
                payload["run_evidence"] = orchestrator.store.get_run_evidence(run_id)
            payload["routing_catalog"] = routing_catalog()
        elif args.command == "approve":
            payload = orchestrator.approve(args.approval_id, args.note)
        elif args.command == "approve-resume":
            payload = run_async(orchestrator.approve_and_resume(args.approval_id, args.note))
            run_id = payload.get("run_id")
            if run_id:
                payload["run_evidence"] = orchestrator.store.get_run_evidence(run_id)
            payload["routing_catalog"] = routing_catalog()
        elif args.command == "reject":
            payload = orchestrator.reject(args.approval_id, args.note)
        elif args.command == "resume":
            payload = run_async(orchestrator.resume_run(args.run_id))
            run_id = payload.get("run_id") or args.run_id
            payload["run_evidence"] = orchestrator.store.get_run_evidence(run_id)
            payload["routing_catalog"] = routing_catalog()
        elif args.command == "run-details":
            payload = orchestrator.store.get_run_evidence(args.run_id)
            payload["routing_catalog"] = routing_catalog()
        else:
            payload = {"routes": routing_catalog()}
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
