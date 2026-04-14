from __future__ import annotations

import asyncio
import json
import os
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agents import role_base
from agents.api_router import APIRouter
from agents.config import load_environment, require_api_key
from agents.developer import DeveloperAgent
from agents.telemetry import TelemetryRecorder
from intake.compiler import compile_task_packet
from intake.gateway import classify_operator_request
from sessions import SessionStore
from workspace_root import ensure_authoritative_workspace_root


class BoundaryAudit:
    def __init__(self, repo_root: Path) -> None:
        self.repo_root = repo_root
        self.boundary_events: list[dict[str, Any]] = []

    def instrument_create(self, create_callable):
        def _wrapped_create(**kwargs):
            event: dict[str, Any] = {
                "observed_at": datetime.now(UTC).isoformat(),
                "model": kwargs.get("model"),
                "credential_available_at_boundary": bool(os.getenv("OPENAI_API_KEY")),
                "external_call_attempted": True,
                "result": "pending",
                "status_code": None,
                "exception_class": None,
                "provider_request_id_present": False,
            }
            self.boundary_events.append(event)
            try:
                response = create_callable(**kwargs)
                provider_request_id = getattr(response, "id", None) or getattr(response, "response_id", None)
                event["result"] = "returned"
                event["provider_request_id_present"] = bool(str(provider_request_id or "").strip())
                event["response_class"] = response.__class__.__name__
                return response
            except Exception as exc:  # pragma: no cover - exercised by real audit outcome
                status_code = getattr(exc, "status_code", None)
                if status_code is None:
                    response = getattr(exc, "response", None)
                    status_code = getattr(response, "status_code", None)
                event["result"] = "raised"
                event["status_code"] = int(status_code) if status_code is not None else None
                event["exception_class"] = exc.__class__.__name__
                raise

        return _wrapped_create


class InstrumentedAPIRouter(APIRouter):
    audit: BoundaryAudit | None = None

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        if self.audit is not None:
            self.client.responses.create = self.audit.instrument_create(self.client.responses.create)


def _dotenv_contains_openai_key(path: Path) -> bool:
    if not path.exists():
        return False
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped.startswith("OPENAI_API_KEY=") and len(stripped) > len("OPENAI_API_KEY="):
            return True
    return False


def _safe_credential_audit(repo_root: Path) -> dict[str, Any]:
    env_present_before_load = bool(os.getenv("OPENAI_API_KEY"))
    dot_env_path = repo_root / ".env"
    dot_env_local_path = repo_root / ".env.local"
    load_environment(repo_root)
    env_present_after_load = bool(os.getenv("OPENAI_API_KEY"))
    require_api_key_loaded = False
    require_api_key_error: str | None = None
    try:
        require_api_key()
        require_api_key_loaded = True
    except Exception as exc:  # pragma: no cover - depends on local environment
        require_api_key_error = exc.__class__.__name__

    saved_key = os.environ.pop("OPENAI_API_KEY", None)
    try:
        load_environment(repo_root)
        env_present_after_forced_file_reload = bool(os.getenv("OPENAI_API_KEY"))
    finally:
        if saved_key is not None:
            os.environ["OPENAI_API_KEY"] = saved_key
        else:
            os.environ.pop("OPENAI_API_KEY", None)
        load_environment(repo_root)

    return {
        "expected_env_var": "OPENAI_API_KEY",
        "env_present_before_load": env_present_before_load,
        "env_present_after_load": env_present_after_load,
        "require_api_key_loaded": require_api_key_loaded,
        "require_api_key_error": require_api_key_error,
        "authoritative_dotenv_exists": dot_env_path.exists(),
        "authoritative_dotenv_local_exists": dot_env_local_path.exists(),
        "authoritative_dotenv_has_openai_key": _dotenv_contains_openai_key(dot_env_path),
        "authoritative_dotenv_local_has_openai_key": _dotenv_contains_openai_key(dot_env_local_path),
        "env_present_after_forced_file_reload": env_present_after_forced_file_reload,
    }


async def _run_live_audit(repo_root: Path) -> dict[str, Any]:
    credential_audit = _safe_credential_audit(repo_root)
    store = SessionStore(repo_root)
    telemetry = TelemetryRecorder(repo_root)
    project_brief = (repo_root / "projects" / "program-kanban" / "governance" / "PROJECT_BRIEF.md").read_text(
        encoding="utf-8"
    )
    task_packet = compile_task_packet(classify_operator_request("Implement the governed API-first specialist flow"))
    task = store.create_task(
        "program-kanban",
        "AUDIT governed API truth check",
        "Audit-only governed specialist execution against the real external provider boundary.",
        objective="Audit governed external API execution truth.",
        owner_role="Developer",
        acceptance={"task_packet": task_packet.model_dump(), "task_state": "In Progress"},
    )
    run = store.create_run("program-kanban", task["id"])

    audit = BoundaryAudit(repo_root)
    original_router = role_base.APIRouter
    InstrumentedAPIRouter.audit = audit
    role_base.APIRouter = InstrumentedAPIRouter
    agent = DeveloperAgent(repo_root=repo_root, store=store, telemetry=telemetry, project_brief=project_brief)
    try:
        result_text = await agent.generate_text(
            system_prompt="Reply with the exact string OK.",
            user_prompt="Reply with the exact string OK.",
            run_id=run["id"],
            task_id=task["id"],
            event_type="audit_live_governed_text",
        )
        execution_error: dict[str, Any] | None = None
    except Exception as exc:
        result_text = None
        status_code = getattr(exc, "status_code", None)
        if status_code is None:
            response = getattr(exc, "response", None)
            status_code = getattr(response, "status_code", None)
        execution_error = {
            "exception_class": exc.__class__.__name__,
            "message": str(exc),
            "status_code": int(status_code) if status_code is not None else None,
        }
    finally:
        await agent.close()
        role_base.APIRouter = original_router
        InstrumentedAPIRouter.audit = None

    run_evidence = store.get_run_evidence(run["id"])
    governed_calls = run_evidence.get("governed_external_calls") or []
    governed_events = run_evidence.get("governed_external_call_events") or []

    last_boundary_event = audit.boundary_events[-1] if audit.boundary_events else None
    auth_succeeded = execution_error is None
    if execution_error and (
        execution_error["exception_class"] == "AuthenticationError" or execution_error.get("status_code") == 401
    ):
        auth_succeeded = False
    elif execution_error:
        auth_succeeded = False

    return {
        "credential_audit": credential_audit,
        "execution_trace": [
            "DeveloperAgent.generate_text",
            "StudioRoleAgent.generate_text",
            "StudioRoleAgent._assert_api_router_authority",
            "StudioRoleAgent._ensure_delegated_execution_reservation",
            "APIRouter.invoke_text",
            "wrappers.llm_wrapper.llm_call",
            "runtime.OpenAIResponsesRuntime.invoke",
            "OpenAI.client.responses.create",
        ],
        "run_id": run["id"],
        "task_id": task["id"],
        "result_text": result_text,
        "execution_error": execution_error,
        "boundary_events": audit.boundary_events,
        "persisted_governed_call_count": len(governed_calls),
        "persisted_governed_event_count": len(governed_events),
        "persisted_governed_calls": governed_calls,
        "persisted_governed_events": governed_events,
        "observed_behavior": {
            "api_boundary_reached": bool(audit.boundary_events),
            "credential_available_at_boundary": bool(last_boundary_event and last_boundary_event["credential_available_at_boundary"]),
            "external_call_attempted": bool(last_boundary_event and last_boundary_event["external_call_attempted"]),
            "authentication_succeeded": auth_succeeded,
            "provider_response_received": bool(
                last_boundary_event
                and last_boundary_event.get("result") == "returned"
                and last_boundary_event.get("provider_request_id_present")
            ),
        },
    }


def main() -> None:
    repo_root = ensure_authoritative_workspace_root(ROOT, label="audit repo_root")
    payload = asyncio.run(_run_live_audit(repo_root))
    print(json.dumps(payload, ensure_ascii=True, indent=2))


if __name__ == "__main__":
    main()
