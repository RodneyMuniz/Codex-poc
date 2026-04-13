from __future__ import annotations

import sqlite3

from scripts.operator_wall_snapshot import build_snapshot
from sessions import SessionStore


def _prepare_repo(tmp_path):
    (tmp_path / "projects" / "tactics-game" / "execution").mkdir(parents=True)
    (tmp_path / "projects" / "tactics-game" / "governance").mkdir(parents=True)
    (tmp_path / "projects" / "tactics-game" / "artifacts").mkdir(parents=True)
    (tmp_path / "sessions").mkdir(parents=True)
    (tmp_path / "governance").mkdir(parents=True)
    (tmp_path / "projects" / "tactics-game" / "governance" / "PROJECT_BRIEF.md").write_text(
        "# Brief\n\nTest project.\n",
        encoding="utf-8",
    )
    return tmp_path


def test_operator_wall_snapshot_reads_canonical_store(tmp_path):
    repo_root = _prepare_repo(tmp_path)
    store = SessionStore(repo_root)

    task = store.create_task(
        "tactics-game",
        "Mage request",
        "Design and implement the mage class",
        objective="Design and implement the mage class",
        requires_approval=True,
    )
    subtask = store.create_subtask(
        "tactics-game",
        task["id"],
        "Mage design",
        "Write the design doc",
        objective="Create the mage design doc",
        owner_role="Architect",
        priority="medium",
        expected_artifact_path="projects/tactics-game/artifacts/mage_design.md",
        acceptance={"required_headings": ["Overview", "Attributes"]},
    )
    artifact_path = repo_root / subtask["expected_artifact_path"]
    artifact_path.write_text("# Overview\n\n## Attributes\n", encoding="utf-8")

    run = store.create_run("tactics-game", task["id"])
    approval = store.create_approval(
        run["id"],
        subtask["id"],
        "PM",
        "Dispatch architecture work",
        approval_scope="project",
        target_role="Architect",
        expected_output=subtask["expected_artifact_path"],
        why_now="Architect design is the next bounded proof step.",
        risks=["Design output must remain scoped to the current class slice."],
    )
    store.record_delegation(run["id"], subtask["id"], from_role="PM", to_role="Architect", note=subtask["objective"])
    agent_run = store.create_agent_run(run["id"], subtask["id"], "Architect")
    store.update_agent_run(
        agent_run["id"],
        status="completed",
        output_artifact_path=subtask["expected_artifact_path"],
        output_artifact_sha256=store.file_metadata(subtask["expected_artifact_path"])["artifact_sha256"],
        notes="Created design doc.",
    )
    store.record_artifact(
        run["id"],
        subtask["id"],
        "architecture_doc",
        artifact_path.read_text(encoding="utf-8"),
        artifact_path=subtask["expected_artifact_path"],
        produced_by="Architect",
        source_agent_run_id=agent_run["id"],
    )
    store.record_trace_event(
        run["id"],
        subtask["id"],
        "sdk_approval_bridge_requested",
        source="PM",
        summary="Paused before SDK specialist dispatch.",
        packet={
            "approval_id": approval["id"],
            "target_role": "Architect",
            "session_id": f"studio-specialist-architect-{run['id']}",
            "expected_artifact_path": subtask["expected_artifact_path"],
            "runtime_mode": "sdk",
        },
        route={"runtime_role": "Architect", "runtime_mode": "sdk"},
        raw_json={"approval_id": approval["id"]},
    )
    store.record_trace_event(
        run["id"],
        subtask["id"],
        "sdk_specialist_result_received",
        source="Architect",
        summary="Architect session completed.",
        packet={
            "session_id": f"studio-specialist-architect-{run['id']}",
            "response_id": "resp_test",
            "trace_id": "trace_test",
            "model": "gpt-4.1-mini",
        },
        route={"runtime_role": "Architect", "runtime_mode": "sdk"},
        raw_json={"role": "Architect"},
    )
    store.update_run(
        run["id"],
        team_state={
            "runtime_mode": "sdk",
            "specialist_runtime": {
                "mode": "sdk",
                "orchestrator_source": "chat_or_control_room",
                "planning_layer": "deterministic_internal_helper",
                "specialist_roles": ["Architect", "Developer", "Design"],
            },
        },
    )
    store.save_context_receipt(
        run["id"],
        {
            "active_lane": subtask["id"],
            "approved_objective": subtask["objective"],
            "next_reviewer": "QA",
            "current_owner_role": "Architect",
            "resume_conditions": ["Resume the same specialist lane unless the receipt changes materially."],
        },
    )
    store.record_validation_result(
        run["id"],
        subtask["id"],
        agent_run_id=agent_run["id"],
        validator_role="QA",
        artifact_path=subtask["expected_artifact_path"],
        status="passed",
        checks={"artifact_exists": True},
        summary="Validated",
    )
    backup = store.create_dispatch_backup(
        project_name="tactics-game",
        trigger="snapshot-proof",
        task_id=task["id"],
        note="Snapshot proof backup.",
    )
    restore = store.restore_dispatch_backup(backup_id=backup["backup_id"], requested_by="Snapshot Test")
    store.write_health_snapshot(
        {
            "ok": True,
            "checked_tables": ["tasks", "runs", "approvals"],
            "issues": [],
        }
    )

    snapshot = build_snapshot(repo_root, project_name="tactics-game")
    cards = [card for column in snapshot["board"] for card in column["cards"]]
    subtask_card = next(card for card in cards if card["id"] == subtask["id"])

    assert snapshot["canonical_store"].endswith("studio.db")
    assert snapshot["summary"]["task_count"] == 2
    assert snapshot["summary"]["pending_approvals"] == 1
    assert snapshot["board"][1]["name"] == "Ready for Build"
    assert snapshot["recent_runs"][0]["governed_external_run_summary"]["governed_api_execution_count"] == 0
    assert snapshot["recent_runs"][0]["governed_external_run_summary"]["final_proof_missing_count"] == 0
    assert snapshot["recent_agent_runs"][0]["role"] == "Architect"
    assert snapshot["recent_validations"][0]["status"] == "passed"
    assert snapshot["recent_artifacts"][0]["produced_by"] == "Architect"
    assert snapshot["recent_updates"][0]["event_type"] in {"artifact", "validation", "agent_run", "run", "task_status", "approval"}
    assert snapshot["focus_run"]["delegations"][0]["to_role"] == "Architect"
    assert snapshot["focus_run"]["sdk_runtime"]["sessions"][0]["session_id"] == f"studio-specialist-architect-{run['id']}"
    assert snapshot["focus_run"]["context_receipt"]["approved_objective"] == subtask["objective"]
    assert snapshot["focus_run"]["context_receipt"]["next_reviewer"] == "QA"
    assert snapshot["focus_run"]["restore_history"][0]["restore_id"] == restore["restore_id"]
    assert snapshot["focus_run"]["restore_history"][0]["restored_run_id"] == run["id"]
    assert snapshot["pending_approvals"][0]["sdk_bridge"]["session_id"] == f"studio-specialist-architect-{run['id']}"
    assert snapshot["pending_approvals"][0]["action_mode"]["label"] == "AI Delegated"
    assert snapshot["pending_approvals"][0]["upstream_context"]["why_now"] == "Architect design is the next bounded proof step."
    assert snapshot["pending_approvals"][0]["downstream_context"]["target_role"] == "Architect"
    assert snapshot["system_health"]["last_backup"]["backup_id"] == restore["pre_restore_backup"]["backup_id"]
    assert snapshot["system_health"]["store"]["ok"] is True
    assert subtask_card["latest_run"]["id"] == run["id"]
    assert subtask_card["latest_artifact"]["artifact_path"] == subtask["expected_artifact_path"]
    assert subtask_card["latest_validation"]["status"] == "passed"


def test_operator_wall_snapshot_includes_milestones_and_copy_fields(tmp_path):
    repo_root = _prepare_repo(tmp_path)
    (repo_root / "projects" / "program-kanban" / "execution").mkdir(parents=True)
    (repo_root / "projects" / "program-kanban" / "governance").mkdir(parents=True)
    (repo_root / "projects" / "program-kanban" / "governance" / "PROJECT_BRIEF.md").write_text(
        "# Brief\n\nProgram Kanban.\n",
        encoding="utf-8",
    )
    store = SessionStore(repo_root)

    task = store.create_task(
        "program-kanban",
        "Restore milestone view",
        "Implement milestone view.",
        objective="Implement milestone view.",
        owner_role="Dashboard Implementer",
        assigned_role="Dashboard Implementer",
        expected_artifact_path="projects/program-kanban/app/app.js",
        acceptance={
            "proposed_milestone": "M1 - Basic Operation Level",
            "entry_goal": "Milestones are missing.",
            "exit_goal": "Milestones are visible again.",
            "approved_decisions": {"copy_behavior": "task_id_only"},
        },
    )
    store.update_task(task["id"], status="ready")

    snapshot = build_snapshot(repo_root, project_name="program-kanban")

    assert snapshot["available_views"] == ["board", "milestones", "orchestrator"]
    assert snapshot["summary"]["milestone_count"] == 1
    assert snapshot["summary"]["planning_warning_count"] == 0
    assert snapshot["board"][1]["cards"][0]["copy_text"] == task["id"]
    assert snapshot["board"][1]["cards"][0]["milestone_title"] == "M1 - Basic Operation Level"
    assert snapshot["milestones"][0]["title"] == "M1 - Basic Operation Level"
    assert snapshot["milestones"][0]["tasks"][0]["copy_text"] == task["id"]
    assert snapshot["milestones"][0]["tasks"][0]["board_column_label"] == "Ready for Build"


def test_operator_wall_snapshot_task_cards_surface_latest_run_work_graph_summary(tmp_path):
    repo_root = _prepare_repo(tmp_path)
    store = SessionStore(repo_root)
    milestone = store.create_milestone(
        "tactics-game",
        "M1 - Unified Work Graph",
        "Task-to-run linkage is missing.",
        "Task, run, and milestone context are linked.",
    )
    task = store.create_task(
        "tactics-game",
        "Bridge task board to governed control room",
        "Expose latest governed execution state from task context.",
        objective="Expose latest governed execution state from task context.",
        milestone_id=milestone["id"],
    )
    run = store.create_run("tactics-game", task["id"])
    store.create_governed_external_call_record(
        external_call_id="external_call_task_card",
        execution_group_id="execution_group_task_card",
        attempt_number=1,
        run_id=run["id"],
        task_packet_id="req_task_card",
        reservation_id="reservation_task_card",
        reservation_linkage_validated=True,
        reservation_status="reserved",
        provider="openai",
        model="gpt-5.4-mini",
        execution_path="governed_api",
        execution_path_classification="governed_api_executed",
        claim_status="claimed",
        proof_status="proved",
        budget_authority_validated=True,
        started_at="2026-04-12T10:00:00+00:00",
        finished_at="2026-04-12T10:00:05+00:00",
        outcome_status="completed",
        provider_request_id="resp_task_card",
    )

    snapshot = build_snapshot(repo_root, project_name="tactics-game")
    cards = [card for column in snapshot["board"] for card in column["cards"]]
    task_card = next(card for card in cards if card["id"] == task["id"])

    assert task_card["project_id"] is not None
    assert task_card["milestone_id"] == milestone["id"]
    assert task_card["linked_run_count"] == 1
    assert task_card["latest_run"]["id"] == run["id"]
    assert task_card["latest_run"]["control_room_path"] == f"/control-room?run_id={run['id']}"
    assert task_card["latest_run"]["governed_external_run_summary"]["governed_api_execution_count"] == 1
    assert task_card["latest_attention_summary"]["attention_count"] == 0
    assert task_card["latest_health_summary"]["final_success_count"] == 1
    assert task_card["latest_execution_summary"]["latest_execution_path_classification"] == "governed_api_executed"
    assert task_card["latest_execution_summary"]["latest_proof_status"] == "proved"
    assert task_card["trust_summary"]["trust_followup_needed"] is True
    assert task_card["trust_summary"]["trust_followup_count"] == 1
    assert task_card["trust_summary"]["latest_trust_status"] == "proof_captured_not_reconciled"
    assert task_card["trust_summary"]["latest_reconciliation_state"] == "not_reconciled"
    assert task_card["trust_summary"]["highest_priority_trust_issue"] == "proof_captured_not_reconciled"
    assert task_card["trust_summary"]["highest_priority_run_id"] == run["id"]


def test_operator_wall_snapshot_includes_project_rollup_for_all_projects(tmp_path):
    repo_root = _prepare_repo(tmp_path)
    (repo_root / "projects" / "program-kanban" / "execution").mkdir(parents=True)
    (repo_root / "projects" / "program-kanban" / "governance").mkdir(parents=True)
    (repo_root / "projects" / "program-kanban" / "governance" / "PROJECT_BRIEF.md").write_text(
        "# Brief\n\nProgram Kanban.\n",
        encoding="utf-8",
    )
    store = SessionStore(repo_root)

    store.create_task(
        "tactics-game",
        "Gameplay request",
        "Refine the tactics prototype.",
        objective="Refine the tactics prototype.",
    )
    ready_task = store.create_task(
        "program-kanban",
        "Board enhancement",
        "Improve the board wall.",
        objective="Improve the board wall.",
        owner_role="Dashboard Implementer",
        assigned_role="Dashboard Implementer",
        expected_artifact_path="projects/program-kanban/app/app.js",
        acceptance={
            "proposed_milestone": "M1 - Basic Operation Level",
            "entry_goal": "Board enhancement needed.",
            "exit_goal": "Board enhancement shipped.",
            "approved_decisions": {"scope": "ui"},
        },
    )
    store.update_task(ready_task["id"], status="ready")

    snapshot = build_snapshot(repo_root, project_name="all")
    rollup_lookup = {item["project_name"]: item for item in snapshot["project_rollup"]}

    assert snapshot["project_name"] == "all"
    assert "program-kanban" in rollup_lookup
    assert "tactics-game" in rollup_lookup
    assert rollup_lookup["program-kanban"]["status_counts"]["ready"] == 1


def test_operator_wall_snapshot_surfaces_task_milestone_and_project_trust_followup_summaries(tmp_path):
    repo_root = _prepare_repo(tmp_path)
    store = SessionStore(repo_root)
    milestone_active = store.create_milestone(
        "tactics-game",
        "M1 - Active Trust Follow-up",
        "Trust follow-up is not aggregated.",
        "Trust follow-up is visible at milestone scope.",
    )
    milestone_clean = store.create_milestone(
        "tactics-game",
        "M2 - Trusted",
        "Trusted work is not distinguished cleanly.",
        "Trusted work remains cleanly separated.",
    )
    task_followup = store.create_task(
        "tactics-game",
        "Reconcile governed developer run",
        "Track failed reconciliation distinctly.",
        objective="Track failed reconciliation distinctly.",
        milestone_id=milestone_active["id"],
    )
    task_pending = store.create_task(
        "tactics-game",
        "Await provider reconciliation",
        "Track pending reconciliation distinctly.",
        objective="Track pending reconciliation distinctly.",
        milestone_id=milestone_active["id"],
    )
    task_clean = store.create_task(
        "tactics-game",
        "Trusted architect run",
        "Keep fully trusted runs out of follow-up counts.",
        objective="Keep fully trusted runs out of follow-up counts.",
        milestone_id=milestone_clean["id"],
    )

    run_failed = store.create_run("tactics-game", task_followup["id"])
    run_unreconciled = store.create_run("tactics-game", task_followup["id"])
    run_pending = store.create_run("tactics-game", task_pending["id"])
    run_trusted = store.create_run("tactics-game", task_clean["id"])

    connection = sqlite3.connect(store.paths.db_path)
    try:
        connection.execute(
            "UPDATE runs SET created_at = ?, updated_at = ? WHERE id = ?",
            ("2026-04-12T12:00:00+00:00", "2026-04-12T12:00:00+00:00", run_failed["id"]),
        )
        connection.execute(
            "UPDATE runs SET created_at = ?, updated_at = ? WHERE id = ?",
            ("2026-04-12T12:02:00+00:00", "2026-04-12T12:02:00+00:00", run_unreconciled["id"]),
        )
        connection.execute(
            "UPDATE runs SET created_at = ?, updated_at = ? WHERE id = ?",
            ("2026-04-12T12:03:00+00:00", "2026-04-12T12:03:00+00:00", run_pending["id"]),
        )
        connection.execute(
            "UPDATE runs SET created_at = ?, updated_at = ? WHERE id = ?",
            ("2026-04-12T12:05:00+00:00", "2026-04-12T12:05:00+00:00", run_trusted["id"]),
        )
        connection.commit()
    finally:
        connection.close()

    store.create_governed_external_call_record(
        external_call_id="external_call_snapshot_failed",
        execution_group_id="execution_group_snapshot_failed",
        attempt_number=1,
        run_id=run_failed["id"],
        task_packet_id="req_snapshot_failed",
        reservation_id="reservation_snapshot_failed",
        provider="openai",
        model="gpt-5.4-mini",
        execution_path="governed_api",
        execution_path_classification="governed_api_executed",
        claim_status="claimed",
        proof_status="proved",
        provider_request_id="resp_snapshot_failed",
        started_at="2026-04-12T12:00:00+00:00",
        outcome_status="completed",
    )
    store.record_governed_external_reconciliation(
        external_call_id="external_call_snapshot_failed",
        provider_request_id="resp_snapshot_failed",
        reconciliation_evidence_source="provider_ledger",
        reconciliation_state="reconciliation_failed",
        reconciliation_reason_code="provider_record_not_found",
        reconciliation_checked_at="2026-04-12T12:01:00+00:00",
    )

    store.create_governed_external_call_record(
        external_call_id="external_call_snapshot_unreconciled",
        execution_group_id="execution_group_snapshot_unreconciled",
        attempt_number=1,
        run_id=run_unreconciled["id"],
        task_packet_id="req_snapshot_unreconciled",
        reservation_id="reservation_snapshot_unreconciled",
        provider="openai",
        model="gpt-5.4-mini",
        execution_path="governed_api",
        execution_path_classification="governed_api_executed",
        claim_status="claimed",
        proof_status="proved",
        provider_request_id="resp_snapshot_unreconciled",
        started_at="2026-04-12T12:02:00+00:00",
        outcome_status="completed",
    )

    store.create_governed_external_call_record(
        external_call_id="external_call_snapshot_pending",
        execution_group_id="execution_group_snapshot_pending",
        attempt_number=1,
        run_id=run_pending["id"],
        task_packet_id="req_snapshot_pending",
        reservation_id="reservation_snapshot_pending",
        provider="openai",
        model="gpt-5.4-mini",
        execution_path="governed_api",
        execution_path_classification="governed_api_executed",
        claim_status="claimed",
        proof_status="proved",
        provider_request_id="resp_snapshot_pending",
        started_at="2026-04-12T12:03:00+00:00",
        outcome_status="completed",
    )
    store.record_governed_external_reconciliation(
        external_call_id="external_call_snapshot_pending",
        provider_request_id="resp_snapshot_pending",
        reconciliation_evidence_source="provider_ledger",
        reconciliation_state="reconciliation_pending",
        reconciliation_checked_at="2026-04-12T12:04:00+00:00",
    )

    store.create_governed_external_call_record(
        external_call_id="external_call_snapshot_trusted",
        execution_group_id="execution_group_snapshot_trusted",
        attempt_number=1,
        run_id=run_trusted["id"],
        task_packet_id="req_snapshot_trusted",
        reservation_id="reservation_snapshot_trusted",
        provider="openai",
        model="gpt-5.4-mini",
        execution_path="governed_api",
        execution_path_classification="governed_api_executed",
        claim_status="claimed",
        proof_status="proved",
        provider_request_id="resp_snapshot_trusted",
        started_at="2026-04-12T12:05:00+00:00",
        outcome_status="completed",
    )
    store.record_governed_external_reconciliation(
        external_call_id="external_call_snapshot_trusted",
        provider_request_id="resp_snapshot_trusted",
        reconciliation_evidence_source="provider_ledger",
        reconciliation_state="reconciled",
        reconciliation_checked_at="2026-04-12T12:06:00+00:00",
    )

    snapshot = build_snapshot(repo_root, project_name="tactics-game")
    cards = [card for column in snapshot["board"] for card in column["cards"]]
    card_lookup = {card["id"]: card for card in cards}
    milestone_lookup = {item["id"]: item for item in snapshot["milestones"]}

    assert snapshot["project_trust_summary"] == {
        "task_count": 3,
        "tasks_with_trust_followup": 2,
        "unreconciled_run_count": 3,
        "reconciliation_failed_count": 1,
        "reconciliation_pending_count": 1,
        "proof_captured_not_reconciled_count": 1,
        "trust_followup_needed": True,
        "highest_priority_trust_issue": "reconciliation_failed",
        "highest_priority_task_id": task_followup["id"],
        "highest_priority_run_id": run_failed["id"],
    }
    assert milestone_lookup[milestone_active["id"]]["trust_summary"] == {
        "task_count": 2,
        "tasks_with_trust_followup": 2,
        "unreconciled_run_count": 3,
        "reconciliation_failed_count": 1,
        "reconciliation_pending_count": 1,
        "proof_captured_not_reconciled_count": 1,
        "trust_followup_needed": True,
        "highest_priority_trust_issue": "reconciliation_failed",
        "highest_priority_task_id": task_followup["id"],
        "highest_priority_run_id": run_failed["id"],
    }
    assert milestone_lookup[milestone_clean["id"]]["trust_summary"] == {
        "task_count": 1,
        "tasks_with_trust_followup": 0,
        "unreconciled_run_count": 0,
        "reconciliation_failed_count": 0,
        "reconciliation_pending_count": 0,
        "proof_captured_not_reconciled_count": 0,
        "trust_followup_needed": False,
        "highest_priority_trust_issue": None,
        "highest_priority_task_id": None,
        "highest_priority_run_id": None,
    }
    active_task_lookup = {item["id"]: item for item in milestone_lookup[milestone_active["id"]]["tasks"]}
    assert active_task_lookup[task_followup["id"]]["trust_summary"] == card_lookup[task_followup["id"]]["trust_summary"]
    assert card_lookup[task_followup["id"]]["trust_summary"] == {
        "trust_followup_needed": True,
        "trust_followup_count": 2,
        "unreconciled_run_count": 2,
        "reconciliation_failed_count": 1,
        "reconciliation_pending_count": 0,
        "proof_captured_not_reconciled_count": 1,
        "latest_trust_status": "proof_captured_not_reconciled",
        "latest_reconciliation_state": "not_reconciled",
        "latest_reconciliation_reason_code": None,
        "highest_priority_trust_issue": "reconciliation_failed",
        "highest_priority_run_id": run_failed["id"],
        "highest_priority_trust_status": "reconciliation_failed",
        "highest_priority_reconciliation_state": "reconciliation_failed",
        "highest_priority_reconciliation_reason_code": "provider_record_not_found",
    }
    assert card_lookup[task_pending["id"]]["trust_summary"]["highest_priority_trust_issue"] == "reconciliation_pending"
    assert card_lookup[task_pending["id"]]["trust_summary"]["trust_followup_count"] == 1
    assert card_lookup[task_clean["id"]]["trust_summary"]["trust_followup_needed"] is False
    assert card_lookup[task_clean["id"]]["trust_summary"]["latest_trust_status"] == "trusted_reconciled"


def test_operator_wall_snapshot_project_rollup_surfaces_project_trust_followup_summary(tmp_path):
    repo_root = _prepare_repo(tmp_path)
    (repo_root / "projects" / "program-kanban" / "execution").mkdir(parents=True)
    (repo_root / "projects" / "program-kanban" / "governance").mkdir(parents=True)
    (repo_root / "projects" / "program-kanban" / "governance" / "PROJECT_BRIEF.md").write_text(
        "# Brief\n\nProgram Kanban.\n",
        encoding="utf-8",
    )
    store = SessionStore(repo_root)

    trusted_task = store.create_task(
        "tactics-game",
        "Trusted run task",
        "Trusted work should stay out of follow-up.",
        objective="Trusted work should stay out of follow-up.",
    )
    followup_task = store.create_task(
        "program-kanban",
        "Unreconciled board task",
        "Proof-backed work still needs trust follow-up.",
        objective="Proof-backed work still needs trust follow-up.",
        owner_role="Dashboard Implementer",
        assigned_role="Dashboard Implementer",
        expected_artifact_path="projects/program-kanban/app/app.js",
        acceptance={
            "proposed_milestone": "M1 - Basic Operation Level",
            "entry_goal": "Trust follow-up is hidden.",
            "exit_goal": "Trust follow-up is visible.",
            "approved_decisions": {"scope": "read_model"},
        },
    )
    store.update_task(followup_task["id"], status="ready")

    trusted_run = store.create_run("tactics-game", trusted_task["id"])
    store.create_governed_external_call_record(
        external_call_id="external_call_rollup_trusted",
        execution_group_id="execution_group_rollup_trusted",
        attempt_number=1,
        run_id=trusted_run["id"],
        task_packet_id="req_rollup_trusted",
        reservation_id="reservation_rollup_trusted",
        provider="openai",
        model="gpt-5.4-mini",
        execution_path="governed_api",
        execution_path_classification="governed_api_executed",
        claim_status="claimed",
        proof_status="proved",
        provider_request_id="resp_rollup_trusted",
        started_at="2026-04-12T12:10:00+00:00",
        outcome_status="completed",
    )
    store.record_governed_external_reconciliation(
        external_call_id="external_call_rollup_trusted",
        provider_request_id="resp_rollup_trusted",
        reconciliation_evidence_source="provider_ledger",
        reconciliation_state="reconciled",
        reconciliation_checked_at="2026-04-12T12:11:00+00:00",
    )

    followup_run = store.create_run("program-kanban", followup_task["id"])
    store.create_governed_external_call_record(
        external_call_id="external_call_rollup_followup",
        execution_group_id="execution_group_rollup_followup",
        attempt_number=1,
        run_id=followup_run["id"],
        task_packet_id="req_rollup_followup",
        reservation_id="reservation_rollup_followup",
        provider="openai",
        model="gpt-5.4-mini",
        execution_path="governed_api",
        execution_path_classification="governed_api_executed",
        claim_status="claimed",
        proof_status="proved",
        provider_request_id="resp_rollup_followup",
        started_at="2026-04-12T12:12:00+00:00",
        outcome_status="completed",
    )

    snapshot = build_snapshot(repo_root, project_name="all")
    rollup_lookup = {item["project_name"]: item for item in snapshot["project_rollup"]}

    assert rollup_lookup["tactics-game"]["trust_summary"]["trust_followup_needed"] is False
    assert rollup_lookup["tactics-game"]["trust_summary"]["tasks_with_trust_followup"] == 0
    assert rollup_lookup["program-kanban"]["trust_summary"] == {
        "task_count": 1,
        "tasks_with_trust_followup": 1,
        "unreconciled_run_count": 1,
        "reconciliation_failed_count": 0,
        "reconciliation_pending_count": 0,
        "proof_captured_not_reconciled_count": 1,
        "trust_followup_needed": True,
        "highest_priority_trust_issue": "proof_captured_not_reconciled",
        "highest_priority_task_id": followup_task["id"],
        "highest_priority_run_id": followup_run["id"],
    }


def test_operator_wall_snapshot_surfaces_canonical_visual_artifacts(tmp_path):
    repo_root = _prepare_repo(tmp_path)
    design_dir = repo_root / "projects" / "tactics-game" / "artifacts" / "design"
    design_dir.mkdir(parents=True)
    store = SessionStore(repo_root)

    task = store.create_task(
        "tactics-game",
        "Visual artifact visibility",
        "Surface canonical visual artifacts in the operator wall snapshot.",
        objective="Surface canonical visual artifacts in the operator wall snapshot.",
    )
    run = store.create_run("tactics-game", task["id"])

    base_path = design_dir / "concept-base.txt"
    edit_path = design_dir / "concept-edit.txt"
    base_path.write_text("base concept", encoding="utf-8")
    edit_path.write_text("edited concept", encoding="utf-8")

    root = store.create_visual_artifact(
        "tactics-game",
        task["id"],
        run_id=run["id"],
        artifact_path="projects/tactics-game/artifacts/design/concept-base.txt",
        provider="openai",
        model="gpt-image-1",
        prompt_summary="Base concept.",
        selected_direction=True,
        metadata={"variant": "base"},
    )
    edited = store.sync_visual_artifact(
        "tactics-game",
        task["id"],
        run_id=run["id"],
        artifact_path="projects/tactics-game/artifacts/design/concept-edit.txt",
        provider="stability",
        model="stable-image-ultra",
        prompt_summary="Armor edit.",
        parent_visual_artifact_id=root["id"],
        lineage_root_visual_artifact_id=root["id"],
        locked_base_visual_artifact_id=root["id"],
        edit_session_id="edit-session-002",
        edit_intent="localized_edit",
        edit_scope={"mode": "localized_edit", "regions": ["armor"]},
        protected_regions=["face", "hands"],
        mask_reference={"kind": "region_mask", "path": "projects/tactics-game/artifacts/design/mask.json"},
        iteration_index=2,
        review_state="pending_review",
        metadata={"variant": "B2"},
    )

    snapshot = build_snapshot(repo_root, project_name="tactics-game")
    card = next(card for column in snapshot["board"] for card in column["cards"] if card["id"] == task["id"])
    recent_artifact = next(item for item in snapshot["recent_artifacts"] if item["id"] == edited["id"])

    assert card["latest_artifact"]["artifact_path"] == edited["artifact_path"]
    assert card["latest_artifact"]["artifact_sha256"] == edited["artifact_sha256"]
    assert card["latest_artifact"]["review_state"] == "pending_review"
    assert card["latest_artifact"]["lineage_root_visual_artifact_id"] == root["id"]
    assert recent_artifact["artifact_path"] == edited["artifact_path"]
    assert recent_artifact["artifact_sha256"] == edited["artifact_sha256"]
    assert recent_artifact["review_state"] == "pending_review"
    assert recent_artifact["locked_base_visual_artifact_id"] == root["id"]


def test_operator_wall_snapshot_surfaces_compliance_and_approval_lanes(tmp_path):
    repo_root = _prepare_repo(tmp_path)
    (repo_root / "projects" / "program-kanban" / "execution").mkdir(parents=True)
    (repo_root / "projects" / "program-kanban" / "governance").mkdir(parents=True)
    (repo_root / "projects" / "program-kanban" / "governance" / "PROJECT_BRIEF.md").write_text(
        "# Brief\n\nProgram Kanban.\n",
        encoding="utf-8",
    )
    store = SessionStore(repo_root)

    task = store.create_task(
        "program-kanban",
        "Compliance surface",
        "Expose compliance state on the wall.",
        objective="Expose compliance state on the wall.",
        expected_artifact_path="projects/program-kanban/app/app.js",
        acceptance={
            "proposed_milestone": "M1 - Basic Operation Level",
            "entry_goal": "Compliance state is hidden.",
            "exit_goal": "Compliance state is visible.",
        },
    )
    run = store.create_run("program-kanban", task["id"])
    store.record_breach_event(
        run["id"],
        task["id"],
        policy_area="budget",
        violation_type="token_limit_exceeded",
        details="Budget cap exceeded.",
        source_role="Orchestrator",
        evidence={"overage": 3},
    )
    delegated_approval = store.create_approval(
        run["id"],
        task["id"],
        "Orchestrator",
        "Delegated follow-up needs approval.",
        approval_scope="program",
        target_role="Orchestrator",
        exact_task=task["title"],
        expected_output=task["expected_artifact_path"],
        why_now="Pending delegated work should be explicit.",
    )
    local_exception = store.create_local_exception_approval(
        run["id"],
        task["id"],
        "Orchestrator",
        "Budget breach needs a local exception.",
        target_role="Orchestrator",
        exact_task=task["title"],
        expected_output=task["expected_artifact_path"],
        why_now="Pending exception should be visible.",
    )
    store.update_run(
        run["id"],
        status="paused_breach",
        stop_reason="awaiting_operator_exception",
        team_state={
            "phase": "awaiting_operator_exception",
            "execution_mode": "local_exception",
            "worker_dispatch": {
                "task_id": task["id"],
                "role": "Orchestrator",
                "expected_output_path": task["expected_artifact_path"],
                "manifest": {
                    "manifest_version": 1,
                    "execution_mode": "worker_only",
                    "run_id": run["id"],
                    "task_id": task["id"],
                    "project_name": "program-kanban",
                    "role": "Orchestrator",
                    "runtime_mode": "custom",
                    "write_scope": "exact_paths_only",
                    "expected_output_path": task["expected_artifact_path"],
                    "allowed_write_paths": [task["expected_artifact_path"]],
                    "allowed_write_modes": ["overwrite"],
                    "input_artifact_paths": [],
                    "issued_by": "PM",
                    "issued_at": "2026-03-29T00:00:00+00:00",
                    "seal_sha256": "test-seal",
                },
            },
            "compliance_state": {
                "mode": "local_exception_pending",
                "approval_id": local_exception["id"],
                "summary": "Budget cap exceeded.",
                "local_exception_allowed": True,
            },
        },
    )

    snapshot = build_snapshot(repo_root, project_name="program-kanban")
    card = next(card for column in snapshot["board"] for card in column["cards"] if card["id"] == task["id"])

    assert snapshot["summary"]["breach_count"] == 1
    assert snapshot["summary"]["pending_delegated_approval_count"] == 1
    assert snapshot["summary"]["pending_local_exception_approval_count"] == 1
    assert snapshot["compliance"]["paused_breach_run_count"] == 1
    assert snapshot["focus_run"]["worker_manifest"]["write_scope"] == "exact_paths_only"
    assert card["compliance_state"]["mode"] == "local_exception_pending"
    assert card["compliance_state"]["breach_count"] == 1
    assert card["compliance_state"]["pause_reason"] == "awaiting_operator_exception"
    assert card["compliance_state"]["local_exception_state"]["id"] == local_exception["id"]
    assert card["compliance_state"]["worker_manifest"]["seal_sha256"] == "test-seal"
    assert {item["approval_lane"] for item in snapshot["pending_approvals"]} == {"delegated_work", "local_exception"}
    assert any(item["approval_id"] == delegated_approval["id"] for item in snapshot["pending_approvals"])
    assert any(item["approval_id"] == local_exception["id"] for item in snapshot["pending_approvals"])
