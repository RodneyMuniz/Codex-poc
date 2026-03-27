from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agents.architect import ArchitectAgent
from agents.config import load_environment, resolve_runtime_mode
from agents.design import DesignAgent
from agents.developer import DeveloperAgent
from agents.qa import QAAgent
from agents.schemas import WorkerResult
from agents.telemetry import TelemetryRecorder
from sessions import SessionStore
from skills.tools import require_worker_write_manifest


def _project_brief(repo_root: Path, project_name: str) -> str:
    return (repo_root / "projects" / project_name / "governance" / "PROJECT_BRIEF.md").read_text(encoding="utf-8")


def _role_route_metadata(role: str) -> dict[str, str]:
    model_role = {"Architect": "architect", "Developer": "developer", "Design": "design", "QA": "qa"}[role]
    return {
        "runtime_role": role,
        "model_role": model_role,
        "profile_label": f"{role} Worker",
    }


def _load_write_manifest(*, args: argparse.Namespace, task: dict[str, object], runtime_mode: str) -> dict[str, object]:
    return require_worker_write_manifest(
        role=args.role,
        run_id=args.run_id,
        task_id=args.task_id,
        project_name=str(task["project_name"]),
        runtime_mode=runtime_mode,
        expected_output_path=str(task["expected_artifact_path"]),
    )


async def _run(args: argparse.Namespace) -> WorkerResult:
    repo_root = ROOT
    load_environment(repo_root)
    store = SessionStore(repo_root)
    telemetry = TelemetryRecorder(repo_root)
    task = store.get_task(args.task_id)
    if task is None:
        raise ValueError(f"Task not found: {args.task_id}")
    project_brief = _project_brief(repo_root, task["project_name"])
    runtime_mode = resolve_runtime_mode()

    if args.role == "QA":
        agent = QAAgent(repo_root=repo_root, store=store, telemetry=telemetry, project_brief=project_brief)
        agent_run = store.create_agent_run(args.run_id, args.task_id, "QA", notes="Artifact review")
        store.record_trace_event(
            args.run_id,
            args.task_id,
            "worker_started",
            source="QA",
            summary="QA worker process started.",
            packet={"agent_run_id": agent_run["id"], "pid": agent_run["pid"], "notes": agent_run.get("notes")},
            route=_role_route_metadata("QA"),
            raw_json=agent_run,
        )
        try:
            review = await agent.review_artifact(run_id=args.run_id, task=task)
            store.update_agent_run(agent_run["id"], status="completed", notes=review.summary)
            store.record_trace_event(
                args.run_id,
                args.task_id,
                "worker_completed",
                source="QA",
                summary=review.summary,
                packet=review.model_dump(),
                route=_role_route_metadata("QA"),
                raw_json=review.model_dump(),
            )
            return WorkerResult(
                role="QA",
                task_id=args.task_id,
                agent_run_id=agent_run["id"],
                approved=review.approved,
                summary=review.summary,
                issues=review.issues,
            )
        except Exception as exc:
            store.update_agent_run(agent_run["id"], status="failed", error=str(exc))
            store.record_trace_event(
                args.run_id,
                args.task_id,
                "worker_failed",
                source="QA",
                summary=str(exc),
                packet={"agent_run_id": agent_run["id"], "error": str(exc)},
                route=_role_route_metadata("QA"),
                raw_json={"error": str(exc)},
            )
            raise
        finally:
            await agent.close()

    _load_write_manifest(args=args, task=task, runtime_mode=runtime_mode)
    input_sha = store.file_metadata(args.input_artifact_path)["artifact_sha256"] if args.input_artifact_path else None
    agent_run = store.create_agent_run(
        args.run_id,
        args.task_id,
        args.role,
        input_artifact_path=args.input_artifact_path,
        input_artifact_sha256=input_sha,
        notes=args.correction_notes,
    )
    store.record_trace_event(
        args.run_id,
        args.task_id,
        "worker_started",
        source=args.role,
        summary=f"{args.role} worker process started.",
        packet={
            "agent_run_id": agent_run["id"],
            "pid": agent_run["pid"],
            "input_artifact_path": args.input_artifact_path,
            "correction_notes": args.correction_notes,
            "runtime_mode": runtime_mode,
        },
        route={**_role_route_metadata(args.role), "runtime_mode": runtime_mode},
        raw_json=agent_run,
    )
    try:
        if runtime_mode == "sdk":
            from agents.sdk_specialists import SDKSpecialistCoordinator

            specialist_runtime = SDKSpecialistCoordinator(repo_root=repo_root, store=store, telemetry=telemetry)
            artifact, specialist_result = await specialist_runtime.produce_artifact(
                run_id=args.run_id,
                task=task,
                role=args.role,
                project_brief=project_brief,
                correction_notes=args.correction_notes,
                agent_run_id=agent_run["id"],
                input_artifact_path=args.input_artifact_path,
            )
            store.record_trace_event(
                args.run_id,
                args.task_id,
                "sdk_specialist_result_received",
                source=args.role,
                summary=specialist_result.summary,
                packet={
                    "session_id": specialist_result.session_id,
                    "response_id": specialist_result.response_id,
                    "trace_id": specialist_result.trace_id,
                    "model": specialist_result.model,
                },
                route={**_role_route_metadata(args.role), "runtime_mode": "sdk"},
                raw_json={
                    "runtime": specialist_result.runtime,
                    "role": specialist_result.role,
                    "session_id": specialist_result.session_id,
                    "response_id": specialist_result.response_id,
                    "trace_id": specialist_result.trace_id,
                    "model": specialist_result.model,
                    "notes": specialist_result.notes,
                },
            )
        else:
            agent_map = {
                "Architect": ArchitectAgent,
                "Developer": DeveloperAgent,
                "Design": DesignAgent,
            }
            agent_cls = agent_map[args.role]
            agent = agent_cls(repo_root=repo_root, store=store, telemetry=telemetry, project_brief=project_brief)
            try:
                if args.role == "Developer":
                    artifact = await agent.produce_artifact(
                        run_id=args.run_id,
                        task=task,
                        correction_notes=args.correction_notes,
                        agent_run_id=agent_run["id"],
                        input_artifact_path=args.input_artifact_path,
                    )
                else:
                    artifact = await agent.produce_artifact(
                        run_id=args.run_id,
                        task=task,
                        correction_notes=args.correction_notes,
                        agent_run_id=agent_run["id"],
                    )
            finally:
                await agent.close()
        output_metadata = store.file_metadata(artifact.artifact_path)
        store.update_agent_run(
            agent_run["id"],
            status="completed",
            output_artifact_path=artifact.artifact_path,
            output_artifact_sha256=output_metadata["artifact_sha256"],
            notes=artifact.summary,
        )
        store.record_trace_event(
            args.run_id,
            args.task_id,
            "worker_completed",
            source=args.role,
            summary=artifact.summary,
            packet={
                "agent_run_id": agent_run["id"],
                "artifact_path": artifact.artifact_path,
                "artifact_sha256": output_metadata["artifact_sha256"],
            },
            route={**_role_route_metadata(args.role), "runtime_mode": runtime_mode},
            raw_json={"artifact_path": artifact.artifact_path, "summary": artifact.summary},
        )
        return WorkerResult(
            role=args.role,
            task_id=args.task_id,
            agent_run_id=agent_run["id"],
            summary=artifact.summary,
            artifact_path=artifact.artifact_path,
        )
    except Exception as exc:
        store.update_agent_run(agent_run["id"], status="failed", error=str(exc))
        store.record_trace_event(
            args.run_id,
            args.task_id,
            "worker_failed",
            source=args.role,
            summary=str(exc),
            packet={"agent_run_id": agent_run["id"], "error": str(exc)},
            route={**_role_route_metadata(args.role), "runtime_mode": runtime_mode},
            raw_json={"error": str(exc)},
        )
        raise


def main() -> None:
    parser = argparse.ArgumentParser(description="Execute a role-specific AI Studio worker.")
    parser.add_argument("--role", choices=["Architect", "Developer", "Design", "QA"], required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--task-id", required=True)
    parser.add_argument("--input-artifact-path", default=None)
    parser.add_argument("--correction-notes", default=None)
    args = parser.parse_args()
    result = asyncio.run(_run(args))
    print(json.dumps(result.model_dump(), ensure_ascii=True))


if __name__ == "__main__":
    main()
