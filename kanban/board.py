from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from governance.rules import check_transition
from sessions import SessionStore
from state_machine import determine_task_state, normalize_task_state, review_consensus_satisfied, state_to_store_status


class KanbanBoardError(RuntimeError):
    pass


class KanbanBoard:
    def __init__(
        self,
        repo_root: str | Path,
        *,
        store: SessionStore | None = None,
        project_id: str | None = None,
        token: str | None = None,
        repository: str | None = None,
    ) -> None:
        self.repo_root = Path(repo_root).resolve()
        self.store = store or SessionStore(self.repo_root)
        self.project_id = project_id or os.getenv("AISTUDIO_GITHUB_PROJECT_ID")
        self.token = token or os.getenv("GITHUB_TOKEN") or os.getenv("AISTUDIO_GITHUB_TOKEN")
        self.repository = repository or os.getenv("GITHUB_REPOSITORY") or os.getenv("AISTUDIO_GITHUB_REPO")

    def move_card(self, issue_number: int, column_name: str) -> dict[str, Any]:
        if self._github_enabled():
            return self._move_github_card(issue_number, column_name)
        task = self._find_local_task(issue_number)
        if task is None:
            raise KanbanBoardError(f"Task for issue/card {issue_number} was not found.")
        return self.move_task(task["id"], column_name)

    def move_task(self, task_id: str, column_name: str) -> dict[str, Any]:
        task = self.store.get_task(task_id)
        if task is None:
            raise KanbanBoardError(f"Task not found: {task_id}")
        current_state = determine_task_state(task)
        target_state = normalize_task_state(column_name)
        check_transition(current_state, target_state)
        updated_acceptance = dict(task.get("acceptance") or {})
        updated_acceptance["task_state"] = target_state
        if target_state == "Done":
            review_votes = updated_acceptance.get("review_votes") or {}
            approvals = sum(1 for approved in review_votes.values() if approved)
            rejections = sum(1 for approved in review_votes.values() if not approved)
            if not review_consensus_satisfied(approvals, rejections):
                raise KanbanBoardError("Review state requires approval by at least two agents before Done.")
        target_status = state_to_store_status(target_state)
        try:
            updated = self.store.update_task(
                task_id,
                status=target_status,
                acceptance=updated_acceptance,
            )
        except ValueError:
            updated = self.store.update_task(
                task_id,
                acceptance=updated_acceptance,
            )
        updated["task_state"] = target_state
        return updated

    def record_review_vote(self, task_id: str, reviewer_role: str, approved: bool) -> dict[str, Any]:
        task = self.store.get_task(task_id)
        if task is None:
            raise KanbanBoardError(f"Task not found: {task_id}")
        updated_acceptance = dict(task.get("acceptance") or {})
        review_votes = dict(updated_acceptance.get("review_votes") or {})
        review_votes[reviewer_role] = bool(approved)
        updated_acceptance["review_votes"] = review_votes
        updated = self.store.update_task(task_id, acceptance=updated_acceptance)
        updated["task_state"] = determine_task_state(updated)
        return updated

    def fetch_next_task(self, column_name: str, *, project_name: str | None = None) -> dict[str, Any] | None:
        if self._github_enabled():
            return self._fetch_next_github_task(column_name)
        target_state = normalize_task_state(column_name)
        tasks = self.store.list_tasks(project_name)
        for task in tasks:
            if determine_task_state(task) == target_state:
                task["task_state"] = target_state
                return task
        return None

    def create_issue(
        self,
        *,
        project_name: str,
        title: str,
        details: str,
        objective: str,
        owner_role: str = "Orchestrator",
    ) -> dict[str, Any]:
        if self._github_enabled():
            return self._create_github_issue(project_name=project_name, title=title, details=details, objective=objective)
        task = self.store.create_task(
            project_name,
            title,
            details,
            objective=objective,
            owner_role=owner_role,
            acceptance={"task_state": "Idea"},
            status=state_to_store_status("Idea"),
        )
        task["task_state"] = "Idea"
        return task

    def _github_enabled(self) -> bool:
        return bool(self.project_id and self.token and self.repository)

    def _graphql(self, query: str, variables: dict[str, Any]) -> dict[str, Any]:
        if not self._github_enabled():
            raise KanbanBoardError("GitHub project configuration is not available.")
        payload = json.dumps({"query": query, "variables": variables}).encode("utf-8")
        request = urllib.request.Request(
            url="https://api.github.com/graphql",
            data=payload,
            method="POST",
            headers={
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json",
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=20) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            raise KanbanBoardError(f"GitHub Project API request failed: {exc}") from exc

    def _move_github_card(self, issue_number: int, column_name: str) -> dict[str, Any]:
        return {"issue_number": issue_number, "column_name": column_name, "project_id": self.project_id}

    def _fetch_next_github_task(self, column_name: str) -> dict[str, Any] | None:
        return None

    def _create_github_issue(self, *, project_name: str, title: str, details: str, objective: str) -> dict[str, Any]:
        return {
            "project_name": project_name,
            "title": title,
            "details": details,
            "objective": objective,
            "task_state": "Idea",
        }

    def _find_local_task(self, issue_number: int) -> dict[str, Any] | None:
        suffix = str(issue_number)
        for task in self.store.list_tasks():
            if str(task["id"]).split("-")[-1] == suffix:
                task["task_state"] = determine_task_state(task)
                return task
        return None
