from __future__ import annotations

import subprocess
from pathlib import Path


class GitService:
    def __init__(self, repo_root: str | Path) -> None:
        self.repo_root = Path(repo_root)

    def status_summary(self) -> str:
        result = subprocess.run(
            ["git", "status", "--short"],
            cwd=self.repo_root,
            capture_output=True,
            text=True,
            check=False,
        )
        return result.stdout.strip()

    def create_checkpoint(self, message: str) -> str:
        status = self.status_summary()
        if not status:
            return "No changes to commit."
        subprocess.run(["git", "add", "-A"], cwd=self.repo_root, check=True)
        subprocess.run(["git", "commit", "-m", message], cwd=self.repo_root, check=True)
        head = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=self.repo_root,
            capture_output=True,
            text=True,
            check=True,
        )
        return head.stdout.strip()
