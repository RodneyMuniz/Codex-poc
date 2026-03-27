from __future__ import annotations

import subprocess
from pathlib import Path

from agents.sdk_runtime import SDKRuntimeAdapter


def test_sdk_runtime_adapter_parses_bridge_health(monkeypatch, tmp_path):
    adapter = SDKRuntimeAdapter(tmp_path, python_executable="python")
    (tmp_path / "scripts").mkdir(parents=True)
    (tmp_path / "sessions").mkdir(parents=True)
    adapter.bridge_script.write_text("# bridge placeholder\n", encoding="utf-8")

    def _fake_run(*args, **kwargs):
        return subprocess.CompletedProcess(
            args=args[0],
            returncode=0,
            stdout='{"ok": true, "package": "openai-agents", "version": "0.12.4", "python": "3.14"}\n',
            stderr="",
        )

    monkeypatch.setattr("subprocess.run", _fake_run)

    health = adapter.health()

    assert health.ok is True
    assert health.package == "openai-agents"
    assert health.version == "0.12.4"


def test_sdk_runtime_adapter_parses_specialist_artifact(monkeypatch, tmp_path):
    adapter = SDKRuntimeAdapter(tmp_path, python_executable="python")
    (tmp_path / "scripts").mkdir(parents=True)
    (tmp_path / "sessions").mkdir(parents=True)
    adapter.bridge_script.write_text("# bridge placeholder\n", encoding="utf-8")

    def _fake_run(*args, **kwargs):
        return subprocess.CompletedProcess(
            args=args[0],
            returncode=0,
            stdout=(
                '{"runtime": "sdk", "role": "Architect", "session_id": "studio-specialist-architect-run_123", '
                '"model": "gpt-4.1-mini", "response_id": "resp_123", "trace_id": "trace_123", '
                '"summary": "Architect prepared the artifact.", "artifact_text": "# Overview", "notes": []}\n'
            ),
            stderr="",
        )

    monkeypatch.setattr("subprocess.run", _fake_run)

    artifact = adapter.run_specialist({"role": "Architect"})

    assert artifact.runtime == "sdk"
    assert artifact.role == "Architect"
    assert artifact.session_id == "studio-specialist-architect-run_123"
    assert artifact.summary == "Architect prepared the artifact."
