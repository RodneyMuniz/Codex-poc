from __future__ import annotations

import hashlib
import json
import os
import re
import shlex
import subprocess
import sys
from pathlib import Path
from typing import Any

from .schemas import (
    ArtifactWriteInput,
    ArtifactWriteOutput,
    CodeDiffInput,
    CodeDiffOutput,
    FileSearchHit,
    FileSearchInput,
    FileSearchOutput,
    SummarizeInput,
    SummarizeOutput,
    UnitTestInput,
    UnitTestOutput,
)


IGNORED_DIRS = {".git", "venv", "__pycache__", ".pytest_cache", ".mypy_cache"}
WORKER_WRITE_MANIFEST_ENV = "AISTUDIO_WORKER_WRITE_MANIFEST"
REQUIRED_WORKER_MANIFEST_FIELDS = {
    "manifest_version",
    "execution_mode",
    "run_id",
    "task_id",
    "project_name",
    "role",
    "runtime_mode",
    "write_scope",
    "expected_output_path",
    "allowed_write_paths",
    "allowed_write_modes",
    "input_artifact_paths",
    "issued_by",
    "issued_at",
    "seal_sha256",
}


def _repo_root() -> Path:
    return Path.cwd()


def _normalize_manifest_path(path: str) -> str:
    return Path(path).as_posix()


def _canonical_manifest_payload(manifest: dict[str, Any]) -> str:
    payload = {key: value for key, value in manifest.items() if key != "seal_sha256"}
    return json.dumps(payload, ensure_ascii=True, sort_keys=True, separators=(",", ":"))


def compute_worker_manifest_seal(manifest: dict[str, Any]) -> str:
    return hashlib.sha256(_canonical_manifest_payload(manifest).encode("utf-8")).hexdigest()


def validate_worker_write_manifest(
    manifest: dict[str, Any],
    *,
    role: str | None = None,
    run_id: str | None = None,
    task_id: str | None = None,
    project_name: str | None = None,
    runtime_mode: str | None = None,
    expected_output_path: str | None = None,
) -> dict[str, Any]:
    missing = sorted(REQUIRED_WORKER_MANIFEST_FIELDS - set(manifest))
    if missing:
        raise ValueError(f"Worker write manifest is missing fields: {', '.join(missing)}")
    if manifest["manifest_version"] != 1:
        raise ValueError("Worker write manifest must use manifest_version 1.")
    if manifest["execution_mode"] != "worker_only":
        raise ValueError("Worker write manifest must set execution_mode to 'worker_only'.")
    if manifest["write_scope"] != "exact_paths_only":
        raise ValueError("Worker write manifest must use write_scope 'exact_paths_only'.")
    allowed_paths = manifest["allowed_write_paths"]
    if not isinstance(allowed_paths, list) or not allowed_paths:
        raise ValueError("Worker write manifest must include at least one allowed_write_path.")
    normalized_allowed_paths = [_normalize_manifest_path(path) for path in allowed_paths]
    if len(normalized_allowed_paths) != 1:
        raise ValueError("Worker write manifest v1 supports exactly one allowed_write_path.")
    expected_path = _normalize_manifest_path(str(manifest["expected_output_path"]))
    if normalized_allowed_paths[0] != expected_path:
        raise ValueError("Worker write manifest allowed_write_paths must match expected_output_path exactly.")
    allowed_modes = manifest["allowed_write_modes"]
    if allowed_modes != ["overwrite"]:
        raise ValueError("Worker write manifest v1 supports only allowed_write_modes ['overwrite'].")
    if not isinstance(manifest["input_artifact_paths"], list):
        raise ValueError("Worker write manifest input_artifact_paths must be a list.")
    actual_seal = compute_worker_manifest_seal(manifest)
    if manifest["seal_sha256"] != actual_seal:
        raise ValueError("Worker write manifest seal_sha256 is invalid.")
    if role is not None and manifest["role"] != role:
        raise ValueError(f"Worker write manifest role mismatch: expected {role}.")
    if run_id is not None and manifest["run_id"] != run_id:
        raise ValueError(f"Worker write manifest run_id mismatch: expected {run_id}.")
    if task_id is not None and manifest["task_id"] != task_id:
        raise ValueError(f"Worker write manifest task_id mismatch: expected {task_id}.")
    if project_name is not None and manifest["project_name"] != project_name:
        raise ValueError(f"Worker write manifest project_name mismatch: expected {project_name}.")
    if runtime_mode is not None and manifest["runtime_mode"] != runtime_mode:
        raise ValueError(f"Worker write manifest runtime_mode mismatch: expected {runtime_mode}.")
    if expected_output_path is not None and expected_path != _normalize_manifest_path(expected_output_path):
        raise ValueError("Worker write manifest expected_output_path does not match the task output path.")
    validated = dict(manifest)
    validated["allowed_write_paths"] = normalized_allowed_paths
    validated["expected_output_path"] = expected_path
    return validated


def load_active_worker_write_manifest() -> dict[str, Any] | None:
    raw_manifest = os.getenv(WORKER_WRITE_MANIFEST_ENV)
    if raw_manifest is None or not raw_manifest.strip():
        return None
    try:
        manifest = json.loads(raw_manifest)
    except json.JSONDecodeError as error:
        raise ValueError("Active worker write manifest is not valid JSON.") from error
    if not isinstance(manifest, dict):
        raise ValueError("Active worker write manifest must be a JSON object.")
    return validate_worker_write_manifest(manifest)


def require_worker_write_manifest(
    *,
    role: str,
    run_id: str,
    task_id: str,
    project_name: str,
    runtime_mode: str,
    expected_output_path: str,
) -> dict[str, Any]:
    manifest = load_active_worker_write_manifest()
    if manifest is None:
        raise ValueError("Worker write manifest is required for delegated artifact execution.")
    return validate_worker_write_manifest(
        manifest,
        role=role,
        run_id=run_id,
        task_id=task_id,
        project_name=project_name,
        runtime_mode=runtime_mode,
        expected_output_path=expected_output_path,
    )


def validate_project_artifact_path(relative_path: str, *, mode: str | None = None) -> dict[str, str]:
    repo_root = _repo_root()
    target_path = (repo_root / relative_path).resolve()
    projects_root = (repo_root / "projects").resolve()

    try:
        target_path.relative_to(projects_root)
    except ValueError as error:
        raise ValueError("Artifacts may only be written under projects/<project>/artifacts/.") from error

    parts = target_path.relative_to(projects_root).parts
    if len(parts) < 3 or parts[1] != "artifacts":
        raise ValueError("Artifacts may only be written under projects/<project>/artifacts/.")

    project_name = parts[0]
    artifacts_root = (projects_root / project_name / "artifacts").resolve()
    try:
        target_path.relative_to(artifacts_root)
    except ValueError as error:
        raise ValueError("Artifacts may only be written under projects/<project>/artifacts/.") from error

    manifest = load_active_worker_write_manifest()
    normalized_relative_path = _normalize_manifest_path(relative_path)
    if manifest is not None:
        if normalized_relative_path not in manifest["allowed_write_paths"]:
            raise ValueError("Artifacts may only be written to the exact manifest-approved path.")
        if mode is not None and mode not in manifest["allowed_write_modes"]:
            raise ValueError("Artifacts may only be written using a manifest-approved mode.")

    return {
        "project_name": project_name,
        "target_path": str(target_path),
        "artifacts_root": str(artifacts_root),
    }


def _trim_lines(content: str, max_lines: int) -> tuple[str, bool]:
    lines = content.splitlines()
    if len(lines) <= max_lines:
        return content, False
    trimmed = "\n".join(lines[:max_lines])
    return f"{trimmed}\n...<truncated>...", True


def file_search(pattern: str, root: str = ".", glob: str = "*.py", limit: int = 20) -> dict:
    request = FileSearchInput(pattern=pattern, root=root, glob=glob, limit=limit)
    compiled = re.compile(request.pattern)
    root_path = (_repo_root() / request.root).resolve()
    hits: list[FileSearchHit] = []
    truncated = False
    for file_path in root_path.rglob(request.glob):
        if not file_path.is_file():
            continue
        if any(part in IGNORED_DIRS for part in file_path.parts):
            continue
        try:
            lines = file_path.read_text(encoding="utf-8").splitlines()
        except UnicodeDecodeError:
            continue
        for line_number, line in enumerate(lines, start=1):
            if compiled.search(line):
                hits.append(
                    FileSearchHit(
                        path=str(file_path.relative_to(_repo_root())),
                        line_number=line_number,
                        line=line.strip(),
                    )
                )
                if len(hits) >= request.limit:
                    truncated = True
                    return FileSearchOutput(
                        pattern=request.pattern,
                        root=str(root_path),
                        hits=hits,
                        truncated=truncated,
                    ).model_dump()
    return FileSearchOutput(
        pattern=request.pattern,
        root=str(root_path),
        hits=hits,
        truncated=truncated,
    ).model_dump()


def summarize_text_or_file(text: str | None = None, path: str | None = None, max_points: int = 5) -> dict:
    request = SummarizeInput(text=text, path=path, max_points=max_points)
    if request.path:
        source = request.path
        raw_text = (_repo_root() / request.path).read_text(encoding="utf-8")
    elif request.text:
        source = "inline_text"
        raw_text = request.text
    else:
        source = "missing"
        raw_text = ""
    lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
    bullets: list[str] = []
    for line in lines:
        if line.startswith("#"):
            bullets.append(line.lstrip("# ").strip())
        elif len(line) > 25:
            bullets.append(line[:180])
        if len(bullets) >= request.max_points:
            break
    if not bullets:
        bullets.append("No substantial content was available to summarize.")
    return SummarizeOutput(source=source, bullets=bullets).model_dump()


def code_diff(target: str = "HEAD", path: str | None = None, max_lines: int = 200) -> dict:
    request = CodeDiffInput(target=target, path=path, max_lines=max_lines)
    command = ["git", "diff", "--no-color", request.target]
    if request.path:
        command.extend(["--", request.path])
    result = subprocess.run(
        command,
        cwd=_repo_root(),
        capture_output=True,
        text=True,
        check=False,
    )
    output = result.stdout or result.stderr
    diff, truncated = _trim_lines(output.strip(), request.max_lines)
    return CodeDiffOutput(
        target=request.target,
        path=request.path,
        return_code=result.returncode,
        truncated=truncated,
        diff=diff,
    ).model_dump()


def run_unit_tests(pytest_args: str = "-q", max_lines: int = 120) -> dict:
    request = UnitTestInput(pytest_args=pytest_args, max_lines=max_lines)
    command = [sys.executable, "-m", "pytest", *shlex.split(request.pytest_args)]
    result = subprocess.run(
        command,
        cwd=_repo_root(),
        capture_output=True,
        text=True,
        check=False,
    )
    output = "\n".join(part for part in [result.stdout.strip(), result.stderr.strip()] if part)
    trimmed, _ = _trim_lines(output, request.max_lines)
    return UnitTestOutput(
        return_code=result.returncode,
        passed=result.returncode == 0,
        output=trimmed,
    ).model_dump()


def write_project_artifact(relative_path: str, content: str, mode: str = "overwrite") -> dict:
    request = ArtifactWriteInput(relative_path=relative_path, content=content, mode=mode)
    repo_root = _repo_root()
    if request.mode not in {"overwrite", "append"}:
        raise ValueError("Mode must be 'overwrite' or 'append'.")
    artifact_target = validate_project_artifact_path(request.relative_path, mode=request.mode)
    target_path = Path(artifact_target["target_path"])

    target_path.parent.mkdir(parents=True, exist_ok=True)
    existing = ""
    if request.mode == "append" and target_path.exists():
        existing = target_path.read_text(encoding="utf-8")
    final_content = request.content if request.mode == "overwrite" else existing + request.content
    target_path.write_text(final_content, encoding="utf-8")
    return ArtifactWriteOutput(
        path=target_path.relative_to(repo_root).as_posix(),
        bytes_written=len(final_content.encode("utf-8")),
        mode=request.mode,
    ).model_dump()
