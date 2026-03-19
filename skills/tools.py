from __future__ import annotations

import re
import shlex
import subprocess
import sys
from pathlib import Path

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


def _repo_root() -> Path:
    return Path.cwd()


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
    artifacts_root = (repo_root / "projects" / "tactics-game" / "artifacts").resolve()
    target_path = (repo_root / request.relative_path).resolve()

    if not str(target_path).startswith(str(artifacts_root)):
        raise ValueError("Artifacts may only be written under projects/tactics-game/artifacts/.")
    if request.mode not in {"overwrite", "append"}:
        raise ValueError("Mode must be 'overwrite' or 'append'.")

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
