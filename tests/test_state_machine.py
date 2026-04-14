from __future__ import annotations

import pytest

from sessions import SessionStore
from state_machine import (
    apply_task_state,
    can_transition,
    determine_task_state,
    ensure_first_slice_stage_completion,
    ensure_first_slice_stage_start,
    ensure_transition,
)


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


def _prepare_first_slice_repo(tmp_path):
    (tmp_path / "projects" / "aioffice" / "execution").mkdir(parents=True)
    (tmp_path / "projects" / "aioffice" / "governance").mkdir(parents=True)
    (tmp_path / "sessions").mkdir(parents=True)
    (tmp_path / "governance").mkdir(parents=True)
    (tmp_path / "projects" / "aioffice" / "governance" / "PROJECT_BRIEF.md").write_text(
        "# Brief\n\nAIOffice first-slice test project.\n",
        encoding="utf-8",
    )
    (tmp_path / "sessions" / "approvals.json").write_text("", encoding="utf-8")
    return tmp_path


def _create_first_slice_fixture(tmp_path, *, include_pm_plan=True, include_pm_branch=True, include_context_report=True):
    repo_root = _prepare_first_slice_repo(tmp_path)
    store = SessionStore(repo_root)
    workflow = store.create_workflow_run(
        "aioffice",
        task_id="AIO-026",
        objective="Evaluate first-slice transition gates.",
        authoritative_workspace_root="projects/aioffice",
        current_stage="architect",
        scope={"non_trivial": True},
    )
    intake = store.create_stage_run(workflow["id"], stage_name="intake", status="completed")
    pm = store.create_stage_run(workflow["id"], stage_name="pm", status="completed")
    context_audit = store.create_stage_run(workflow["id"], stage_name="context_audit", status="completed")
    architect = store.create_stage_run(workflow["id"], stage_name="architect", status="in_progress")

    intake_artifact = store.create_workflow_artifact(
        "aioffice",
        workflow_run_id=workflow["id"],
        stage_run_id=intake["id"],
        task_id="AIO-026",
        contract_name="intake_request_v1",
        kind="document",
        content="# Intake\n\nCapture the governed request.\n",
        proof_value="intake_output",
    )

    pm_plan = None
    if include_pm_plan:
        pm_plan = store.create_workflow_artifact(
            "aioffice",
            workflow_run_id=workflow["id"],
            stage_run_id=pm["id"],
            task_id="AIO-026",
            contract_name="pm_plan_v1",
            kind="document",
            content="# PM Plan\n\nBounded plan.\n",
            proof_value="stage_output",
        )

    pm_branch = None
    if include_pm_branch:
        pm_branch = store.create_workflow_artifact(
            "aioffice",
            workflow_run_id=workflow["id"],
            stage_run_id=pm["id"],
            task_id="AIO-026",
            contract_name="pm_assumption_register_v1",
            kind="document",
            content="# Assumptions\n\nExplicit assumptions.\n",
            proof_value="stage_output",
        )

    context_report = None
    if include_context_report:
        context_report = store.create_workflow_artifact(
            "aioffice",
            workflow_run_id=workflow["id"],
            stage_run_id=context_audit["id"],
            task_id="AIO-026",
            contract_name="context_audit_report_v1",
            kind="document",
            content="# Context Audit\n\nRelevant sources and risks.\n",
            proof_value="audit_output",
        )

    architecture_decision = store.create_workflow_artifact(
        "aioffice",
        workflow_run_id=workflow["id"],
        stage_run_id=architect["id"],
        task_id="AIO-026",
        contract_name="architecture_decision_v1",
        kind="document",
        content="# Architecture\n\nChosen approach.\n",
        proof_value="architecture_output",
    )

    intake_handoff_ids = [intake_artifact["id"]]
    store.create_handoff(
        workflow["id"],
        from_stage_name="intake",
        to_stage_name="pm",
        summary="Intake is ready for PM.",
        stage_run_id=intake["id"],
        upstream_artifact_ids=intake_handoff_ids,
    )

    pm_handoff_ids = [item["id"] for item in (pm_plan, pm_branch) if item is not None]
    if pm_handoff_ids:
        store.create_handoff(
            workflow["id"],
            from_stage_name="pm",
            to_stage_name="context_audit",
            summary="PM outputs are ready for context audit.",
            stage_run_id=pm["id"],
            upstream_artifact_ids=pm_handoff_ids,
        )

    if context_report is not None:
        store.create_handoff(
            workflow["id"],
            from_stage_name="context_audit",
            to_stage_name="architect",
            summary="Context audit is ready for architecture.",
            stage_run_id=context_audit["id"],
            upstream_artifact_ids=[context_report["id"]],
        )

    return {
        "store": store,
        "workflow": workflow,
        "intake_stage": intake,
        "pm_stage": pm,
        "context_stage": context_audit,
        "architect_stage": architect,
        "intake_artifact": intake_artifact,
        "pm_plan": pm_plan,
        "pm_branch": pm_branch,
        "context_report": context_report,
        "architecture_decision": architecture_decision,
    }


def test_first_slice_progression_passes_when_required_artifacts_and_handoffs_exist(tmp_path):
    fixture = _create_first_slice_fixture(tmp_path)
    store = fixture["store"]
    workflow_id = fixture["workflow"]["id"]

    assert (
        ensure_first_slice_stage_completion(
            store,
            workflow_id,
            stage_name="intake",
            stage_run_id=fixture["intake_stage"]["id"],
        )["allowed"]
        is True
    )
    assert (
        ensure_first_slice_stage_start(
            store,
            workflow_id,
            stage_name="pm",
            stage_run_id=fixture["pm_stage"]["id"],
        )["allowed"]
        is True
    )
    assert (
        ensure_first_slice_stage_completion(
            store,
            workflow_id,
            stage_name="pm",
            stage_run_id=fixture["pm_stage"]["id"],
        )["allowed"]
        is True
    )
    assert (
        ensure_first_slice_stage_start(
            store,
            workflow_id,
            stage_name="context_audit",
            stage_run_id=fixture["context_stage"]["id"],
        )["allowed"]
        is True
    )
    assert (
        ensure_first_slice_stage_completion(
            store,
            workflow_id,
            stage_name="context_audit",
            stage_run_id=fixture["context_stage"]["id"],
        )["allowed"]
        is True
    )
    assert (
        ensure_first_slice_stage_start(
            store,
            workflow_id,
            stage_name="architect",
            stage_run_id=fixture["architect_stage"]["id"],
        )["allowed"]
        is True
    )
    assert (
        ensure_first_slice_stage_completion(
            store,
            workflow_id,
            stage_name="architect",
            stage_run_id=fixture["architect_stage"]["id"],
        )["allowed"]
        is True
    )


def test_first_slice_pm_completion_fails_without_plan(tmp_path):
    fixture = _create_first_slice_fixture(tmp_path, include_pm_plan=False)

    with pytest.raises(ValueError) as exc_info:
        ensure_first_slice_stage_completion(
            fixture["store"],
            fixture["workflow"]["id"],
            stage_name="pm",
            stage_run_id=fixture["pm_stage"]["id"],
        )

    assert "pm_plan_v1" in str(exc_info.value)


def test_first_slice_pm_completion_fails_without_branch_for_non_trivial_work(tmp_path):
    fixture = _create_first_slice_fixture(tmp_path, include_pm_branch=False)

    with pytest.raises(ValueError) as exc_info:
        ensure_first_slice_stage_completion(
            fixture["store"],
            fixture["workflow"]["id"],
            stage_name="pm",
            stage_run_id=fixture["pm_stage"]["id"],
        )

    assert "pm_assumption_register_v1" in str(exc_info.value) or "pm_clarification_questions_v1" in str(exc_info.value)


def test_first_slice_architect_start_fails_without_context_audit_artifact(tmp_path):
    fixture = _create_first_slice_fixture(tmp_path, include_context_report=False)

    with pytest.raises(ValueError) as exc_info:
        ensure_first_slice_stage_start(
            fixture["store"],
            fixture["workflow"]["id"],
            stage_name="architect",
            stage_run_id=fixture["architect_stage"]["id"],
        )

    assert "context_audit_report_v1" in str(exc_info.value)


def test_first_slice_context_audit_start_fails_without_required_handoff(tmp_path):
    fixture = _create_first_slice_fixture(tmp_path)
    store = fixture["store"]
    workflow_id = fixture["workflow"]["id"]

    with store._connect() as connection:
        connection.execute(
            "DELETE FROM handoffs WHERE workflow_run_id = ? AND from_stage_name = ? AND to_stage_name = ?",
            (workflow_id, "pm", "context_audit"),
        )

    with pytest.raises(ValueError) as exc_info:
        ensure_first_slice_stage_start(
            store,
            workflow_id,
            stage_name="context_audit",
            stage_run_id=fixture["context_stage"]["id"],
        )

    assert "handoff pm->context_audit" in str(exc_info.value)


def test_first_slice_narration_alone_does_not_satisfy_progression(tmp_path):
    repo_root = _prepare_first_slice_repo(tmp_path)
    store = SessionStore(repo_root)
    workflow = store.create_workflow_run(
        "aioffice",
        task_id="AIO-026",
        objective="Narration should not satisfy gates.",
        authoritative_workspace_root="projects/aioffice",
        current_stage="architect",
        scope={"non_trivial": True},
    )
    architect = store.create_stage_run(workflow["id"], stage_name="architect", status="in_progress")
    store.record_orchestration_trace(
        workflow["id"],
        stage_run_id=architect["id"],
        event_type="narration_claimed_ready",
        source="Codex executor",
        payload={"summary": "Architect is done."},
    )

    with pytest.raises(ValueError) as exc_info:
        ensure_first_slice_stage_start(
            store,
            workflow["id"],
            stage_name="architect",
            stage_run_id=architect["id"],
        )

    assert "pm_plan_v1" in str(exc_info.value)


def test_first_slice_rejects_out_of_scope_stage_requests(tmp_path):
    fixture = _create_first_slice_fixture(tmp_path)

    with pytest.raises(ValueError) as exc_info:
        ensure_first_slice_stage_start(fixture["store"], fixture["workflow"]["id"], stage_name="design")

    assert "Unsupported first-slice stage" in str(exc_info.value)


def test_first_slice_second_attempt_completion_cannot_use_earlier_attempt_artifact(tmp_path):
    fixture = _create_first_slice_fixture(tmp_path)
    store = fixture["store"]
    workflow_id = fixture["workflow"]["id"]
    pm_attempt_two = store.create_stage_run(
        workflow_id,
        stage_name="pm",
        attempt_number=2,
        status="in_progress",
    )

    with pytest.raises(ValueError) as exc_info:
        ensure_first_slice_stage_completion(
            store,
            workflow_id,
            stage_name="pm",
            stage_run_id=pm_attempt_two["id"],
        )

    assert "pm_plan_v1" in str(exc_info.value)


def test_first_slice_second_attempt_start_cannot_use_earlier_attempt_handoff(tmp_path):
    fixture = _create_first_slice_fixture(tmp_path)
    store = fixture["store"]
    workflow_id = fixture["workflow"]["id"]
    pm_attempt_two = store.create_stage_run(
        workflow_id,
        stage_name="pm",
        attempt_number=2,
        status="pending",
    )

    with pytest.raises(ValueError) as exc_info:
        ensure_first_slice_stage_start(
            store,
            workflow_id,
            stage_name="pm",
            stage_run_id=pm_attempt_two["id"],
        )

    assert "handoff intake->pm for attempt 2" in str(exc_info.value)


def test_first_slice_ambiguous_multiple_attempt_history_fails_closed(tmp_path):
    fixture = _create_first_slice_fixture(tmp_path)
    store = fixture["store"]
    workflow_id = fixture["workflow"]["id"]
    pm_attempt_two_a = store.create_stage_run(
        workflow_id,
        stage_name="pm",
        attempt_number=2,
        status="completed",
    )
    pm_attempt_two_b = store.create_stage_run(
        workflow_id,
        stage_name="pm",
        attempt_number=2,
        status="completed",
    )
    pm_attempt_two_artifact_ids = []
    for stage_run in (pm_attempt_two_a, pm_attempt_two_b):
        pm_plan = store.create_workflow_artifact(
            "aioffice",
            workflow_run_id=workflow_id,
            stage_run_id=stage_run["id"],
            task_id="AIO-026",
            contract_name="pm_plan_v1",
            kind="document",
            content="# PM Plan\n\nAttempt two plan.\n",
            proof_value="stage_output",
        )
        pm_branch = store.create_workflow_artifact(
            "aioffice",
            workflow_run_id=workflow_id,
            stage_run_id=stage_run["id"],
            task_id="AIO-026",
            contract_name="pm_assumption_register_v1",
            kind="document",
            content="# Assumptions\n\nAttempt two assumptions.\n",
            proof_value="stage_output",
        )
        pm_attempt_two_artifact_ids.append((stage_run, [pm_plan["id"], pm_branch["id"]]))

    context_attempt_two = store.create_stage_run(
        workflow_id,
        stage_name="context_audit",
        attempt_number=2,
        status="in_progress",
    )
    for stage_run, artifact_ids in pm_attempt_two_artifact_ids:
        store.create_handoff(
            workflow_id,
            from_stage_name="pm",
            to_stage_name="context_audit",
            summary="Attempt two PM outputs are ready for context audit.",
            stage_run_id=stage_run["id"],
            upstream_artifact_ids=artifact_ids,
        )

    with pytest.raises(ValueError) as exc_info:
        ensure_first_slice_stage_start(
            store,
            workflow_id,
            stage_name="context_audit",
            stage_run_id=context_attempt_two["id"],
        )

    assert "ambiguous because multiple handoffs pm->context_audit match attempt 2" in str(exc_info.value) or (
        "ambiguous because multiple pm attempts match attempt 2" in str(exc_info.value)
    )
