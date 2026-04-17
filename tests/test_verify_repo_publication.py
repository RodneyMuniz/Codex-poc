from __future__ import annotations

import io
import json
import subprocess
from contextlib import redirect_stdout

from scripts import verify_repo_publication as helper


def _completed(args: list[str], stdout: str = "", returncode: int = 0, stderr: str = "") -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(["git", *args], returncode, stdout=stdout, stderr=stderr)


def _fake_git_runner(outputs: dict[tuple[str, ...], subprocess.CompletedProcess[str]]):
    def _runner(args, *, cwd=helper.REPO_ROOT, check=True):
        key = tuple(args)
        if key not in outputs:
            raise AssertionError(f"Unexpected git args: {key}")
        completed = outputs[key]
        if check and completed.returncode != 0:
            raise helper.GitCommandError(args, completed.returncode, completed.stdout, completed.stderr)
        return completed

    return _runner


def test_verify_repo_publication_returns_ok_when_local_and_remote_match() -> None:
    branch = helper.AUTHORITATIVE_BRANCH
    sha = "abc123"
    outputs = {
        ("branch", "--show-current"): _completed(["branch", "--show-current"], stdout=f"{branch}\n"),
        ("rev-parse", "HEAD"): _completed(["rev-parse", "HEAD"], stdout=f"{sha}\n"),
        ("status", "--porcelain"): _completed(["status", "--porcelain"], stdout=""),
        ("fetch", "--quiet", helper.REMOTE_NAME, branch): _completed(["fetch", "--quiet", helper.REMOTE_NAME, branch]),
        ("rev-parse", f"refs/remotes/{helper.REMOTE_NAME}/{branch}"): _completed(
            ["rev-parse", f"refs/remotes/{helper.REMOTE_NAME}/{branch}"],
            stdout=f"{sha}\n",
        ),
        ("merge-base", "--is-ancestor", sha, f"refs/remotes/{helper.REMOTE_NAME}/{branch}"): _completed(
            ["merge-base", "--is-ancestor", sha, f"refs/remotes/{helper.REMOTE_NAME}/{branch}"],
        ),
    }

    original = helper._run_git
    helper._run_git = _fake_git_runner(outputs)
    try:
        result = helper.verify_repo_publication(target_branch=branch)
    finally:
        helper._run_git = original

    assert result["status"] == "ok"
    assert result["branch_name"] == branch
    assert result["local_head_sha"] == sha
    assert result["remote_head_sha"] == sha
    assert result["reported_sha"] == sha
    assert result["reported_sha_visible_remotely"] is True
    assert result["worktree_clean"] is True


def test_verify_repo_publication_blocks_when_reported_sha_missing_remotely() -> None:
    branch = helper.AUTHORITATIVE_BRANCH
    local_sha = "abc123"
    reported_sha = "def456"
    outputs = {
        ("branch", "--show-current"): _completed(["branch", "--show-current"], stdout=f"{branch}\n"),
        ("rev-parse", "HEAD"): _completed(["rev-parse", "HEAD"], stdout=f"{local_sha}\n"),
        ("status", "--porcelain"): _completed(["status", "--porcelain"], stdout=""),
        ("fetch", "--quiet", helper.REMOTE_NAME, branch): _completed(["fetch", "--quiet", helper.REMOTE_NAME, branch]),
        ("rev-parse", f"refs/remotes/{helper.REMOTE_NAME}/{branch}"): _completed(
            ["rev-parse", f"refs/remotes/{helper.REMOTE_NAME}/{branch}"],
            stdout=f"{local_sha}\n",
        ),
        ("merge-base", "--is-ancestor", reported_sha, f"refs/remotes/{helper.REMOTE_NAME}/{branch}"): _completed(
            ["merge-base", "--is-ancestor", reported_sha, f"refs/remotes/{helper.REMOTE_NAME}/{branch}"],
            returncode=1,
        ),
    }

    original = helper._run_git
    helper._run_git = _fake_git_runner(outputs)
    try:
        result = helper.verify_repo_publication(target_branch=branch, reported_sha=reported_sha)
    finally:
        helper._run_git = original

    assert result["status"] == "blocked_missing_remote_commit"
    assert result["reported_sha"] == reported_sha
    assert result["reported_sha_visible_remotely"] is False
    assert "not visible" in str(result["reason"])


def test_verify_repo_publication_blocks_when_local_and_remote_heads_diverge() -> None:
    branch = helper.AUTHORITATIVE_BRANCH
    local_sha = "abc123"
    remote_sha = "def456"
    outputs = {
        ("branch", "--show-current"): _completed(["branch", "--show-current"], stdout=f"{branch}\n"),
        ("rev-parse", "HEAD"): _completed(["rev-parse", "HEAD"], stdout=f"{local_sha}\n"),
        ("status", "--porcelain"): _completed(["status", "--porcelain"], stdout=" M scripts/verify_repo_publication.py\n"),
        ("fetch", "--quiet", helper.REMOTE_NAME, branch): _completed(["fetch", "--quiet", helper.REMOTE_NAME, branch]),
        ("rev-parse", f"refs/remotes/{helper.REMOTE_NAME}/{branch}"): _completed(
            ["rev-parse", f"refs/remotes/{helper.REMOTE_NAME}/{branch}"],
            stdout=f"{remote_sha}\n",
        ),
        ("merge-base", "--is-ancestor", local_sha, f"refs/remotes/{helper.REMOTE_NAME}/{branch}"): _completed(
            ["merge-base", "--is-ancestor", local_sha, f"refs/remotes/{helper.REMOTE_NAME}/{branch}"],
        ),
    }

    original = helper._run_git
    helper._run_git = _fake_git_runner(outputs)
    try:
        result = helper.verify_repo_publication(target_branch=branch)
    finally:
        helper._run_git = original

    assert result["status"] == "blocked_local_remote_mismatch"
    assert result["worktree_clean"] is False
    assert result["local_head_sha"] == local_sha
    assert result["remote_head_sha"] == remote_sha


def test_verify_repo_publication_main_prints_structured_json() -> None:
    payload = {
        "branch_name": helper.AUTHORITATIVE_BRANCH,
        "local_head_sha": "abc123",
        "remote_head_sha": "abc123",
        "reported_sha": "abc123",
        "reported_sha_visible_remotely": True,
        "worktree_clean": True,
        "status": "ok",
        "reason": "reported SHA is visible remotely and local and remote heads match",
    }

    original = helper.verify_repo_publication
    helper.verify_repo_publication = lambda **_: payload
    stream = io.StringIO()
    try:
        with redirect_stdout(stream):
            exit_code = helper.main(["--target-branch", helper.AUTHORITATIVE_BRANCH, "--strict"])
    finally:
        helper.verify_repo_publication = original

    parsed = json.loads(stream.getvalue())
    assert exit_code == 0
    assert parsed["status"] == "ok"
    assert parsed["branch_name"] == helper.AUTHORITATIVE_BRANCH
    assert sorted(parsed.keys()) == sorted(
        [
            "branch_name",
            "local_head_sha",
            "remote_head_sha",
            "reported_sha",
            "reported_sha_visible_remotely",
            "worktree_clean",
            "status",
            "reason",
        ]
    )
