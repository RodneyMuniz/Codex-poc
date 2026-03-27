from __future__ import annotations

import json

import pytest

from skills.tools import WORKER_WRITE_MANIFEST_ENV, compute_worker_manifest_seal, require_worker_write_manifest, write_project_artifact


def test_write_project_artifact_scoped_to_project_artifacts(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    artifacts_dir = tmp_path / "projects" / "tactics-game" / "artifacts"
    artifacts_dir.mkdir(parents=True)

    result = write_project_artifact(
        "projects/tactics-game/artifacts/example.txt",
        "hello world",
    )

    assert result["path"] == "projects/tactics-game/artifacts/example.txt"
    assert (artifacts_dir / "example.txt").read_text(encoding="utf-8") == "hello world"


def test_write_project_artifact_rejects_paths_outside_scope(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "projects" / "tactics-game" / "artifacts").mkdir(parents=True)

    try:
        write_project_artifact("../README.md", "bad")
    except ValueError as exc:
        assert "Artifacts may only be written" in str(exc)
    else:
        raise AssertionError("Expected ValueError for out-of-scope path.")


def _worker_manifest(relative_path: str) -> dict[str, object]:
    manifest = {
        "manifest_version": 1,
        "execution_mode": "worker_only",
        "run_id": "run_test",
        "task_id": "task_test",
        "project_name": "tactics-game",
        "role": "Developer",
        "runtime_mode": "custom",
        "write_scope": "exact_paths_only",
        "expected_output_path": relative_path,
        "allowed_write_paths": [relative_path],
        "allowed_write_modes": ["overwrite"],
        "input_artifact_paths": [],
        "issued_by": "PM",
        "issued_at": "2026-03-27T06:00:00+00:00",
    }
    manifest["seal_sha256"] = compute_worker_manifest_seal(manifest)
    return manifest


def test_worker_manifest_is_required_for_delegated_artifact_execution(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    with pytest.raises(ValueError, match="manifest is required"):
        require_worker_write_manifest(
            role="Developer",
            run_id="run_test",
            task_id="task_test",
            project_name="tactics-game",
            runtime_mode="custom",
            expected_output_path="projects/tactics-game/artifacts/example.txt",
        )


def test_worker_manifest_rejects_bad_seal(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    relative_path = "projects/tactics-game/artifacts/example.txt"
    manifest = _worker_manifest(relative_path)
    manifest["seal_sha256"] = "not-a-real-seal"
    monkeypatch.setenv(WORKER_WRITE_MANIFEST_ENV, json.dumps(manifest))
    with pytest.raises(ValueError, match="seal_sha256 is invalid"):
        require_worker_write_manifest(
            role="Developer",
            run_id="run_test",
            task_id="task_test",
            project_name="tactics-game",
            runtime_mode="custom",
            expected_output_path=relative_path,
        )


def test_worker_manifest_rejects_task_mismatch(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    relative_path = "projects/tactics-game/artifacts/example.txt"
    monkeypatch.setenv(WORKER_WRITE_MANIFEST_ENV, json.dumps(_worker_manifest(relative_path)))
    with pytest.raises(ValueError, match="task_id mismatch"):
        require_worker_write_manifest(
            role="Developer",
            run_id="run_test",
            task_id="task_other",
            project_name="tactics-game",
            runtime_mode="custom",
            expected_output_path=relative_path,
        )
