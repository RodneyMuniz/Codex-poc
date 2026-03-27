from __future__ import annotations

import json

import pytest

from skills.tools import (
    WORKER_WRITE_MANIFEST_ENV,
    compute_worker_manifest_seal,
    validate_project_artifact_path,
    write_project_artifact,
)


def _prepare_repo(tmp_path):
    (tmp_path / "projects" / "tactics-game" / "artifacts").mkdir(parents=True)
    (tmp_path / "projects" / "program-kanban" / "artifacts").mkdir(parents=True)
    (tmp_path / "projects" / "tactics-game" / "governance").mkdir(parents=True)
    return tmp_path


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


def test_write_project_artifact_accepts_project_artifact_roots(tmp_path, monkeypatch):
    repo_root = _prepare_repo(tmp_path)
    monkeypatch.chdir(repo_root)

    tactics = write_project_artifact("projects/tactics-game/artifacts/test_design.md", "# Test\n")
    kanban = write_project_artifact("projects/program-kanban/artifacts/proof.json", "{}\n")

    assert tactics["path"] == "projects/tactics-game/artifacts/test_design.md"
    assert kanban["path"] == "projects/program-kanban/artifacts/proof.json"
    assert (repo_root / tactics["path"]).exists()
    assert (repo_root / kanban["path"]).exists()


def test_write_project_artifact_rejects_non_artifact_paths(tmp_path, monkeypatch):
    repo_root = _prepare_repo(tmp_path)
    monkeypatch.chdir(repo_root)

    with pytest.raises(ValueError, match="projects/<project>/artifacts/"):
        write_project_artifact("projects/tactics-game/governance/unsafe.md", "# No\n")

    with pytest.raises(ValueError, match="projects/<project>/artifacts/"):
        validate_project_artifact_path("../memory/framework_health.json")


def test_write_project_artifact_accepts_exact_manifest_path(tmp_path, monkeypatch):
    repo_root = _prepare_repo(tmp_path)
    monkeypatch.chdir(repo_root)
    relative_path = "projects/tactics-game/artifacts/manifest-approved.md"
    monkeypatch.setenv(WORKER_WRITE_MANIFEST_ENV, json.dumps(_worker_manifest(relative_path)))

    result = write_project_artifact(relative_path, "# Approved\n")

    assert result["path"] == relative_path
    assert (repo_root / relative_path).read_text(encoding="utf-8") == "# Approved\n"


def test_write_project_artifact_rejects_sibling_path_under_active_manifest(tmp_path, monkeypatch):
    repo_root = _prepare_repo(tmp_path)
    monkeypatch.chdir(repo_root)
    allowed_path = "projects/tactics-game/artifacts/manifest-approved.md"
    sibling_path = "projects/tactics-game/artifacts/sibling.md"
    monkeypatch.setenv(WORKER_WRITE_MANIFEST_ENV, json.dumps(_worker_manifest(allowed_path)))

    with pytest.raises(ValueError, match="manifest-approved path"):
        write_project_artifact(sibling_path, "# Rejected\n")
