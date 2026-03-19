from __future__ import annotations

from pathlib import Path

from skills.tools import write_project_artifact


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
