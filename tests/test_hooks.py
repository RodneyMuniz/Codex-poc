from __future__ import annotations

import asyncio
import sqlite3

import pytest

from hooks import post_task, pre_task


class _FakeAgent:
    def __init__(self, repo_root):
        self.repo_root = repo_root
        self.role_name = "Architect"
        self._memory_context = None

    @pre_task("In Progress")
    @post_task("In Progress")
    async def produce(self, *, objective: str):
        return objective.upper()


def test_hooks_capture_memory_and_metrics(tmp_path):
    agent = _FakeAgent(tmp_path)
    result = asyncio.run(agent.produce(objective="Create architecture note"))

    assert result == "CREATE ARCHITECTURE NOTE"
    assert agent._memory_context == []
    connection = sqlite3.connect(tmp_path / "memory" / "memory.db")
    row = connection.execute("SELECT COUNT(*) FROM metrics").fetchone()
    connection.close()
    assert row[0] == 1


def test_pre_task_rejects_wrong_state(tmp_path):
    class _PromptAgent:
        def __init__(self, repo_root):
            self.repo_root = repo_root
            self.role_name = "PromptSpecialist"

        @pre_task("In Progress")
        async def run(self):
            return "nope"

    with pytest.raises(PermissionError):
        asyncio.run(_PromptAgent(tmp_path).run())
