from __future__ import annotations

import pytest

from state_machine import apply_task_state, can_transition, determine_task_state, ensure_transition


def test_can_transition_only_allows_next_stage():
    assert can_transition("Idea", "Spec") is True
    assert can_transition("Spec", "Review") is False


def test_ensure_transition_rejects_skips():
    with pytest.raises(ValueError):
        ensure_transition("Todo", "Done")


def test_determine_and_apply_task_state():
    task = {"status": "ready", "acceptance": {}}
    assert determine_task_state(task) == "Todo"
    updated = apply_task_state(task, "In Progress")
    assert updated["acceptance"]["task_state"] == "In Progress"
    assert updated["status"] == "in_progress"
