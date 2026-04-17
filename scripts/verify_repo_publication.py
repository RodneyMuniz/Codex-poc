from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Sequence

REPO_ROOT = Path(__file__).resolve().parents[1]
AUTHORITATIVE_BRANCH = "feature/aioffice-m13-design-lane-operationalization"
REMOTE_NAME = "origin"


class GitCommandError(RuntimeError):
    def __init__(self, args: Sequence[str], returncode: int, stdout: str, stderr: str) -> None:
        self.args_list = list(args)
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr
        command = " ".join(["git", *self.args_list])
        super().__init__(f"git command failed ({returncode}): {command}")


def _run_git(args: Sequence[str], *, cwd: Path = REPO_ROOT, check: bool = True) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(
        ["git", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
    )
    if check and completed.returncode != 0:
        raise GitCommandError(args, completed.returncode, completed.stdout, completed.stderr)
    return completed


def _stdout(args: Sequence[str], *, cwd: Path = REPO_ROOT) -> str:
    return _run_git(args, cwd=cwd).stdout.strip()


def _is_worktree_clean(*, cwd: Path = REPO_ROOT) -> bool:
    return _stdout(["status", "--porcelain"], cwd=cwd) == ""


def _fetch_remote_branch(target_branch: str, *, cwd: Path = REPO_ROOT) -> None:
    _run_git(["fetch", "--quiet", REMOTE_NAME, target_branch], cwd=cwd)


def _remote_ref(target_branch: str) -> str:
    return f"refs/remotes/{REMOTE_NAME}/{target_branch}"


def _reported_sha_visible_on_remote(reported_sha: str, target_branch: str, *, cwd: Path = REPO_ROOT) -> bool:
    completed = _run_git(
        ["merge-base", "--is-ancestor", reported_sha, _remote_ref(target_branch)],
        cwd=cwd,
        check=False,
    )
    return completed.returncode == 0


def verify_repo_publication(
    *,
    target_branch: str = AUTHORITATIVE_BRANCH,
    reported_sha: str | None = None,
    strict: bool = False,
    cwd: Path = REPO_ROOT,
) -> dict[str, object]:
    result: dict[str, object] = {
        "branch_name": None,
        "local_head_sha": None,
        "remote_head_sha": None,
        "reported_sha": reported_sha,
        "reported_sha_visible_remotely": False,
        "worktree_clean": None,
        "status": "blocked_unknown",
        "reason": "publication verification did not complete",
    }

    try:
        branch_name = _stdout(["branch", "--show-current"], cwd=cwd)
        local_head_sha = _stdout(["rev-parse", "HEAD"], cwd=cwd)
        worktree_clean = _is_worktree_clean(cwd=cwd)

        result["branch_name"] = branch_name
        result["local_head_sha"] = local_head_sha
        result["worktree_clean"] = worktree_clean

        effective_reported_sha = reported_sha.strip() if reported_sha else local_head_sha
        result["reported_sha"] = effective_reported_sha

        if not effective_reported_sha:
            result["reason"] = "reported SHA is blank"
            return result

        try:
            _fetch_remote_branch(target_branch, cwd=cwd)
            remote_head_sha = _stdout(["rev-parse", _remote_ref(target_branch)], cwd=cwd)
        except GitCommandError as error:
            stderr = error.stderr.lower()
            if "couldn't find remote ref" in stderr or "unknown revision or path not in the working tree" in stderr:
                result["status"] = "blocked_missing_remote_branch"
                result["reason"] = f"remote branch '{REMOTE_NAME}/{target_branch}' could not be resolved"
                return result
            result["reason"] = error.stderr.strip() or str(error)
            return result

        result["remote_head_sha"] = remote_head_sha

        visible = _reported_sha_visible_on_remote(effective_reported_sha, target_branch, cwd=cwd)
        result["reported_sha_visible_remotely"] = visible

        if branch_name != target_branch:
            result["status"] = "blocked_branch_mismatch"
            result["reason"] = f"local branch '{branch_name}' does not match target branch '{target_branch}'"
            return result

        if not visible:
            result["status"] = "blocked_missing_remote_commit"
            result["reason"] = (
                f"reported SHA '{effective_reported_sha}' is not visible on remote branch '{REMOTE_NAME}/{target_branch}'"
            )
            return result

        if strict and effective_reported_sha != remote_head_sha:
            result["status"] = "blocked_local_remote_mismatch"
            result["reason"] = "strict mode requires reported SHA to equal the authoritative remote head"
            return result

        if local_head_sha != remote_head_sha:
            result["status"] = "blocked_local_remote_mismatch"
            result["reason"] = "local HEAD does not match the authoritative remote HEAD"
            return result

        result["status"] = "ok"
        result["reason"] = "reported SHA is visible remotely and local and remote heads match"
        return result
    except GitCommandError as error:
        result["reason"] = error.stderr.strip() or str(error)
        return result
    except Exception as error:  # pragma: no cover - defensive fail-closed path
        result["reason"] = str(error)
        return result


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Verify bounded repo publication truth for the authoritative milestone loop.")
    parser.add_argument(
        "--target-branch",
        default=AUTHORITATIVE_BRANCH,
        help="Target authoritative branch to verify.",
    )
    parser.add_argument(
        "--reported-sha",
        default=None,
        help="Optional reported SHA to check for remote visibility. Defaults to the local HEAD SHA.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Require the reported SHA to equal the authoritative remote head exactly.",
    )
    args = parser.parse_args(argv)

    result = verify_repo_publication(
        target_branch=args.target_branch,
        reported_sha=args.reported_sha,
        strict=args.strict,
    )
    print(json.dumps(result, indent=2))
    return 0 if result["status"] == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
