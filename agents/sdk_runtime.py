from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


class SDKRuntimeError(RuntimeError):
    pass


class SDKBridgeHealth(BaseModel):
    ok: bool
    package: str
    version: str | None = None
    python: str | None = None


class SDKSpecialistArtifact(BaseModel):
    runtime: str = "sdk"
    role: str
    session_id: str
    model: str
    response_id: str | None = None
    trace_id: str | None = None
    summary: str
    artifact_text: str
    notes: list[str] = Field(default_factory=list)


class SDKRuntimeAdapter:
    def __init__(self, repo_root: str | Path, *, python_executable: str | None = None) -> None:
        self.repo_root = Path(repo_root).resolve()
        self.python_executable = python_executable or sys.executable
        self.bridge_script = self.repo_root / "scripts" / "sdk_runtime_bridge.py"
        self.sessions_db_path = self.repo_root / "sessions" / "sdk_sessions.db"

    def health(self) -> SDKBridgeHealth:
        return SDKBridgeHealth.model_validate(self._run_bridge("health"))

    def run_specialist(self, payload: dict[str, Any]) -> SDKSpecialistArtifact:
        return SDKSpecialistArtifact.model_validate(self._run_bridge("specialist-artifact", payload))

    def _bridge_environment(self) -> dict[str, str]:
        env = os.environ.copy()
        env["AISTUDIO_REPO_ROOT"] = str(self.repo_root)
        env["AISTUDIO_SDK_SESSIONS_DB"] = str(self.sessions_db_path)
        pythonpath = env.get("PYTHONPATH", "")
        if pythonpath:
            filtered = [
                part
                for part in pythonpath.split(os.pathsep)
                if Path(part or ".").resolve() != self.repo_root
            ]
            if filtered:
                env["PYTHONPATH"] = os.pathsep.join(filtered)
            else:
                env.pop("PYTHONPATH", None)
        return env

    def _run_bridge(self, command: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        if not self.bridge_script.exists():
            raise SDKRuntimeError(f"SDK bridge script is missing: {self.bridge_script}")

        args = [self.python_executable, str(self.bridge_script), command]
        if payload is not None:
            args.extend(["--payload-json", json.dumps(payload, ensure_ascii=True)])

        completed = subprocess.run(
            args,
            cwd=self.repo_root / "sessions",
            env=self._bridge_environment(),
            capture_output=True,
            text=True,
            check=False,
            timeout=120,
        )
        stdout = completed.stdout.strip()
        stderr = completed.stderr.strip()
        if completed.returncode != 0:
            raise SDKRuntimeError(stderr or stdout or f"SDK bridge exited with code {completed.returncode}")
        if not stdout:
            raise SDKRuntimeError("SDK bridge returned no output.")
        try:
            return json.loads(stdout.splitlines()[-1])
        except json.JSONDecodeError as exc:
            raise SDKRuntimeError(f"SDK bridge returned invalid JSON: {stdout}") from exc
