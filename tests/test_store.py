from __future__ import annotations

import json
import sqlite3
import subprocess
from pathlib import Path

import pytest

from sessions import SessionStore


def _prepare_repo(tmp_path):
    (tmp_path / "projects" / "tactics-game" / "execution").mkdir(parents=True)
    (tmp_path / "projects" / "tactics-game" / "governance").mkdir(parents=True)
    (tmp_path / "sessions").mkdir(parents=True)
    (tmp_path / "governance").mkdir(parents=True)
    (tmp_path / "projects" / "tactics-game" / "governance" / "PROJECT_BRIEF.md").write_text(
        "# Brief\n\nTest project.\n",
        encoding="utf-8",
    )
    (tmp_path / "sessions" / "approvals.json").write_text("", encoding="utf-8")
    return tmp_path


def _run_git(repo_root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise AssertionError(f"git {' '.join(args)} failed: {(result.stderr or result.stdout).strip()}")
    return result.stdout.strip()


def _prepare_aioffice_recovery_repo(tmp_path: Path) -> tuple[Path, SessionStore]:
    repo_root = tmp_path
    (repo_root / "projects" / "aioffice" / "execution").mkdir(parents=True)
    (repo_root / "projects" / "aioffice" / "governance").mkdir(parents=True)
    (repo_root / "sessions").mkdir(parents=True)
    (repo_root / "governance").mkdir(parents=True)
    (repo_root / ".gitignore").write_text(
        "sessions/*.db\nsessions/*.db-*\nsessions/backups/\nmemory/\n",
        encoding="utf-8",
    )
    (repo_root / "sessions" / "approvals.json").write_text("", encoding="utf-8")
    (repo_root / "projects" / "aioffice" / "execution" / "KANBAN.md").write_text(
        "# AIOffice Operational Ledger\n\n### M10 - Change Governance, Recovery, And Maintainability Hardening\n- status: completed\n\n### M11 - Recovery Discipline Operationalization\n- status: in_progress\n",
        encoding="utf-8",
    )
    (repo_root / "projects" / "aioffice" / "governance" / "ACTIVE_STATE.md").write_text(
        "# AIOffice Active State\n\n"
        "## Authoritative Review Anchor\n"
        "- authoritative working branch: `feature/aioffice-m10-change-governance-hardening`\n"
        "- authoritative milestone checkpoint tag: `aioffice-m10-closeout-2026-04-16`\n"
        "- authoritative milestone snapshot branch: `snapshot/aioffice-m10-closeout-2026-04-16`\n",
        encoding="utf-8",
    )
    (repo_root / "projects" / "aioffice" / "governance" / "DECISION_LOG.md").write_text(
        "# AIOffice Decision Log\n\n## Decisions\n\n### AIO-D-010\n- status: reviewed\n",
        encoding="utf-8",
    )
    (repo_root / "projects" / "aioffice" / "governance" / "RECOVERY_AND_ROLLBACK_CONTRACT.md").write_text(
        "# Recovery And Rollback Contract\n\n- no committed artifact proves automated snapshot/version/restore/rollback discipline\n- no restore or rollback rehearsal has been executed\n",
        encoding="utf-8",
    )
    store = SessionStore(repo_root)
    _run_git(repo_root, "init")
    _run_git(repo_root, "config", "user.email", "test@example.com")
    _run_git(repo_root, "config", "user.name", "Test Runner")
    _run_git(repo_root, "checkout", "-b", "feature/aioffice-m10-change-governance-hardening")
    _run_git(repo_root, "add", ".")
    _run_git(repo_root, "commit", "-m", "Initial recovery anchor")
    _run_git(repo_root, "tag", "-a", "aioffice-m10-closeout-2026-04-16", "-m", "M10 closeout")
    _run_git(repo_root, "branch", "snapshot/aioffice-m10-closeout-2026-04-16")
    return repo_root, store


def _commit_all(repo_root: Path, message: str) -> None:
    _run_git(repo_root, "add", ".")
    _run_git(repo_root, "commit", "-m", message)


def test_store_persists_queue_states_subtasks_and_kanban(tmp_path):
    repo_root = _prepare_repo(tmp_path)
    store = SessionStore(repo_root)

    task = store.create_task("tactics-game", "Mage request", "Design and implement the mage class", requires_approval=True)
    assert task["status"] == "backlog"

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
    assert subtask["task_kind"] == "subtask"
    assert subtask["parent_task_id"] == task["id"]
    assert subtask["milestone_id"] == task["milestone_id"]

    run = store.create_run("tactics-game", task["id"])
    approval = store.create_approval(run["id"], task["id"], "Orchestrator", "High impact request")
    assert approval["status"] == "pending"

    decided = store.decide_approval(approval["id"], "approve", "Looks good")
    assert decided["status"] == "approved"

    store.update_task(subtask["id"], status="completed", owner_role="QA", result_summary="Approved")
    store.update_task(task["id"], status="completed", owner_role="QA", result_summary="Complete")

    kanban = (repo_root / "projects" / "tactics-game" / "execution" / "KANBAN.md").read_text(encoding="utf-8")
    assert "Backlog" in kanban
    assert "Ready for Build" in kanban
    assert "Complete" in kanban
    assert "Mage request" in kanban


def test_store_records_messages_and_usage(tmp_path):
    repo_root = _prepare_repo(tmp_path)
    store = SessionStore(repo_root)
    task = store.create_task("tactics-game", "Telemetry Task", "Verify message logging")
    run = store.create_run("tactics-game", task["id"])

    store.record_message(
        run["id"],
        task["id"],
        "agent_text",
        {"content": "hello"},
        source="PM",
        prompt_tokens=11,
        completion_tokens=7,
    )

    connection = sqlite3.connect(store.paths.db_path)
    connection.row_factory = sqlite3.Row
    try:
        messages = connection.execute("SELECT payload_json FROM messages").fetchall()
        usage = connection.execute(
            """
            SELECT
                prompt_tokens,
                completion_tokens,
                model,
                tier,
                lane,
                cached_input_tokens,
                reasoning_tokens,
                estimated_cost_usd
            FROM usage_events
            """
        ).fetchall()
    finally:
        connection.close()

    assert json.loads(messages[0][0])["content"] == "hello"
    assert dict(usage[0]) == {
        "prompt_tokens": 11,
        "completion_tokens": 7,
        "model": None,
        "tier": None,
        "lane": None,
        "cached_input_tokens": 0,
        "reasoning_tokens": 0,
        "estimated_cost_usd": 0.0,
    }


def test_store_records_rich_usage_fields_and_exposes_them_in_run_evidence(tmp_path):
    repo_root = _prepare_repo(tmp_path)
    store = SessionStore(repo_root)
    task = store.create_task("tactics-game", "Budget Truth Task", "Verify rich usage metadata persists")
    run = store.create_run("tactics-game", task["id"])

    store.record_usage(
        run["id"],
        task["id"],
        source="APIExecutionTest",
        prompt_tokens=120,
        completion_tokens=40,
        model="gpt-5.4-mini",
        tier="tier_2_mid",
        lane="background_api",
        cached_input_tokens=20,
        reasoning_tokens=8,
        estimated_cost_usd=0.000197,
    )

    usage_event = store.list_usage_events(run["id"])[0]
    evidence = store.get_run_evidence(run["id"])

    assert usage_event["source"] == "APIExecutionTest"
    assert usage_event["model"] == "gpt-5.4-mini"
    assert usage_event["tier"] == "tier_2_mid"
    assert usage_event["lane"] == "background_api"
    assert usage_event["cached_input_tokens"] == 20
    assert usage_event["reasoning_tokens"] == 8
    assert usage_event["estimated_cost_usd"] == 0.000197
    assert evidence["usage_events"][0]["lane"] == "background_api"


def test_store_records_execution_packet_and_job_reservation(tmp_path):
    repo_root = _prepare_repo(tmp_path)
    store = SessionStore(repo_root)
    task = store.create_task("tactics-game", "Execution Contract Task", "Verify execution contract records")
    run = store.create_run("tactics-game", task["id"])

    packet = store.sync_execution_packet(
        authority_job_id="job-001",
        authority_packet_id="packet-001",
        authority_token="auth-token",
        authority_schema_name="authority.contract.v1",
        authority_execution_tier="tier_3_junior",
        authority_execution_lane="sync_api",
        authority_delegated_work=True,
        priority_class="medium",
        budget_max_tokens=1200,
        budget_reservation_id="res-001",
        retry_limit=2,
        early_stop_rule="sufficient_output",
        run_id=run["id"],
        task_id=task["id"],
        actual_total_tokens=22,
        retry_count=1,
        escalation_target=None,
        stop_reason=None,
        status="running",
    )
    reservation = store.sync_execution_job_reservation(
        job_id="job-001",
        priority_class="medium",
        reserved_max_tokens=1200,
        reservation_status="reserved",
        run_id=run["id"],
        task_id=task["id"],
    )
    updated_reservation = store.sync_execution_job_reservation(
        job_id="job-001",
        priority_class="high",
        reserved_max_tokens=1500,
        reservation_status="active",
        run_id=run["id"],
        task_id=task["id"],
    )

    evidence = store.get_run_evidence(run["id"])

    assert packet["authority_packet_id"] == "packet-001"
    assert packet["authority_job_id"] == "job-001"
    assert packet["packet_id"] == "packet-001"
    assert packet["job_id"] == "job-001"
    assert packet["status"] == "running"
    assert packet["actual_total_tokens"] == 22
    assert packet["retry_count"] == 1
    assert packet["authority_delegated_work"] is True
    assert packet["budget_reservation_id"] == "res-001"
    assert reservation["job_id"] == "job-001"
    assert reservation["priority_class"] == "medium"
    assert reservation["reserved_max_tokens"] == 1200
    assert reservation["reservation_status"] == "reserved"
    assert updated_reservation["priority_class"] == "high"
    assert updated_reservation["reserved_max_tokens"] == 1500
    assert updated_reservation["reservation_status"] == "active"
    assert evidence["execution_packets"][0]["authority_packet_id"] == "packet-001"
    assert evidence["execution_job_reservations"][0]["job_id"] == "job-001"
    assert evidence["execution_job_reservations"][0]["reservation_status"] == "active"


def test_store_exposes_unified_task_work_graph_and_run_context(tmp_path):
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
        "Unify task and run context",
        "Bridge task context into governed execution reads",
        objective="Bridge task context into governed execution reads",
        milestone_id=milestone["id"],
    )
    first_run = store.create_run("tactics-game", task["id"])
    second_run = store.create_run("tactics-game", task["id"])

    connection = sqlite3.connect(store.paths.db_path)
    try:
        connection.execute(
            "UPDATE runs SET created_at = ?, updated_at = ? WHERE id = ?",
            ("2026-04-12T10:00:00+00:00", "2026-04-12T10:00:00+00:00", first_run["id"]),
        )
        connection.execute(
            "UPDATE runs SET created_at = ?, updated_at = ? WHERE id = ?",
            ("2026-04-12T10:05:00+00:00", "2026-04-12T10:05:00+00:00", second_run["id"]),
        )
        connection.commit()
    finally:
        connection.close()

    store.create_governed_external_call_record(
        external_call_id="external_call_success",
        execution_group_id="execution_group_success",
        attempt_number=1,
        run_id=first_run["id"],
        task_packet_id="req_success",
        reservation_id="reservation_success",
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
        provider_request_id="resp_success",
    )
    store.create_governed_pre_execution_block(
        run_id=second_run["id"],
        task_id=task["id"],
        task_packet_id="req_blocked",
        authority_packet_id="packet_blocked",
        block_stage="wrapper_governance_precheck",
        block_reason_code="role_state_blocked",
        occurred_at="2026-04-12T10:05:00+00:00",
    )

    first_evidence = store.get_run_evidence(first_run["id"])
    task_graph = store.get_task_work_graph(task["id"])

    assert first_evidence["project"]["name"] == "tactics-game"
    assert first_evidence["milestone"]["id"] == milestone["id"]
    assert first_evidence["run_context"]["task_id"] == task["id"]
    assert first_evidence["run_context"]["project_id"] == first_evidence["project"]["id"]
    assert first_evidence["run_context"]["milestone_id"] == milestone["id"]
    assert first_evidence["run_context"]["control_room_path"] == f"/control-room?run_id={first_run['id']}"

    assert task_graph["task"]["id"] == task["id"]
    assert task_graph["project"]["id"] == first_evidence["project"]["id"]
    assert task_graph["milestone"]["id"] == milestone["id"]
    assert task_graph["linked_run_count"] == 2
    assert [item["id"] for item in task_graph["linked_runs"]] == [second_run["id"], first_run["id"]]
    assert task_graph["latest_run_summary"]["id"] == second_run["id"]
    assert task_graph["latest_attention_summary"]["pre_observation_block_count"] == 1
    assert task_graph["latest_health_summary"]["has_attention"] is True
    assert task_graph["latest_execution_summary"]["latest_execution_path_classification"] == "blocked_pre_execution"
    assert task_graph["trust_summary"]["trust_followup_needed"] is True
    assert task_graph["trust_summary"]["trust_followup_count"] == 1
    assert task_graph["trust_summary"]["latest_trust_status"] is None
    assert task_graph["trust_summary"]["latest_reconciliation_state"] is None
    assert task_graph["trust_summary"]["highest_priority_trust_issue"] == "proof_captured_not_reconciled"
    assert task_graph["trust_summary"]["highest_priority_run_id"] == first_run["id"]
    assert task_graph["linked_runs"][1]["execution_summary"]["latest_execution_path_classification"] == "governed_api_executed"
    assert task_graph["linked_runs"][1]["execution_summary"]["latest_proof_status"] == "proved"


def test_store_defaults_governed_reconciliation_state_and_trust_status_conservatively(tmp_path):
    repo_root = _prepare_repo(tmp_path)
    store = SessionStore(repo_root)
    task = store.create_task("tactics-game", "Trust Default Task", "Verify default governed trust state")
    run = store.create_run("tactics-game", task["id"])

    record = store.create_governed_external_call_record(
        external_call_id="external_call_default_trust",
        execution_group_id="execution_group_default_trust",
        attempt_number=1,
        run_id=run["id"],
        task_packet_id="req_default_trust",
        reservation_id="reservation_default_trust",
        provider="openai",
        model="gpt-5.4-mini",
        execution_path="governed_api",
        execution_path_classification="governed_api_executed",
        claim_status="claimed",
        proof_status="missing",
        started_at="2026-04-12T11:00:00+00:00",
        outcome_status="completed",
    )
    evidence = store.get_run_evidence(run["id"])

    assert record["reconciliation_state"] == "not_reconciled"
    assert record["reconciliation_checked_at"] is None
    assert record["reconciliation_reason_code"] is None
    assert record["reconciliation_evidence_source"] is None
    assert record["trust_status"] == "claimed_only"
    assert evidence["governed_external_calls"][0]["trust_status"] == "claimed_only"
    assert evidence["governed_external_execution_groups"][0]["final_trust_status"] == "claimed_only"
    assert evidence["governed_external_run_summary"]["final_claimed_only_count"] == 1


def test_store_records_reconciliation_outcomes_and_derives_trust_status(tmp_path):
    repo_root = _prepare_repo(tmp_path)
    store = SessionStore(repo_root)
    task = store.create_task("tactics-game", "Trust Reconciliation Task", "Verify reconciliation outcomes")
    run = store.create_run("tactics-game", task["id"])

    store.create_governed_external_call_record(
        external_call_id="external_call_reconciled",
        execution_group_id="execution_group_reconciled",
        attempt_number=1,
        run_id=run["id"],
        task_packet_id="req_reconciled",
        reservation_id="reservation_reconciled",
        provider="openai",
        model="gpt-5.4-mini",
        execution_path="governed_api",
        execution_path_classification="governed_api_executed",
        claim_status="claimed",
        proof_status="proved",
        provider_request_id="resp_reconciled",
        started_at="2026-04-12T11:05:00+00:00",
        outcome_status="completed",
    )

    result = store.record_governed_external_reconciliation(
        external_call_id="external_call_reconciled",
        provider_request_id="resp_reconciled",
        reconciliation_evidence_source="provider_ledger",
        reconciliation_state="reconciled",
        reconciliation_checked_at="2026-04-12T11:06:00+00:00",
        details={"provider_record_state": "matched"},
    )
    evidence = store.get_run_evidence(run["id"])
    reconciliation = result["reconciliation_record"]
    updated_call = result["governed_external_call"]

    assert reconciliation["reconciliation_state"] == "reconciled"
    assert reconciliation["provider_request_id"] == "resp_reconciled"
    assert reconciliation["reconciliation_evidence_source"] == "provider_ledger"
    assert reconciliation["details"]["provider_record_state"] == "matched"
    assert updated_call["trust_status"] == "trusted_reconciled"
    assert evidence["governed_external_reconciliation_records"][0]["external_call_id"] == "external_call_reconciled"
    assert evidence["governed_external_calls"][0]["reconciliation_state"] == "reconciled"
    assert evidence["governed_external_calls"][0]["trust_status"] == "trusted_reconciled"
    assert evidence["governed_external_execution_groups"][0]["final_reconciliation_state"] == "reconciled"
    assert evidence["governed_external_execution_groups"][0]["final_trust_status"] == "trusted_reconciled"
    assert evidence["governed_external_run_summary"]["final_trusted_reconciled_count"] == 1


def test_store_distinguishes_reconciliation_failed_from_proof_missing(tmp_path):
    repo_root = _prepare_repo(tmp_path)
    store = SessionStore(repo_root)
    task = store.create_task("tactics-game", "Trust Distinction Task", "Verify reconciliation failure stays distinct")
    run = store.create_run("tactics-game", task["id"])

    store.create_governed_external_call_record(
        external_call_id="external_call_proof_missing",
        execution_group_id="execution_group_proof_missing",
        attempt_number=1,
        run_id=run["id"],
        task_packet_id="req_proof_missing",
        reservation_id="reservation_proof_missing",
        provider="openai",
        model="gpt-5.4-mini",
        execution_path="governed_api",
        execution_path_classification="governed_api_executed",
        claim_status="claimed",
        proof_status="missing",
        started_at="2026-04-12T11:10:00+00:00",
        outcome_status="completed",
    )
    store.create_governed_external_call_record(
        external_call_id="external_call_reconciliation_failed",
        execution_group_id="execution_group_reconciliation_failed",
        attempt_number=1,
        run_id=run["id"],
        task_packet_id="req_reconciliation_failed",
        reservation_id="reservation_reconciliation_failed",
        provider="openai",
        model="gpt-5.4-mini",
        execution_path="governed_api",
        execution_path_classification="governed_api_executed",
        claim_status="claimed",
        proof_status="proved",
        provider_request_id="resp_reconciliation_failed",
        started_at="2026-04-12T11:11:00+00:00",
        outcome_status="completed",
    )
    store.record_governed_external_reconciliation(
        external_call_id="external_call_reconciliation_failed",
        provider_request_id="resp_reconciliation_failed",
        reconciliation_evidence_source="provider_ledger",
        reconciliation_state="reconciliation_failed",
        reconciliation_checked_at="2026-04-12T11:12:00+00:00",
        reconciliation_reason_code="provider_record_not_found",
    )

    evidence = store.get_run_evidence(run["id"])
    groups = {group["execution_group_id"]: group for group in evidence["governed_external_execution_groups"]}

    assert groups["execution_group_proof_missing"]["final_proof_status"] == "missing"
    assert groups["execution_group_proof_missing"]["final_trust_status"] == "claimed_only"
    assert groups["execution_group_reconciliation_failed"]["final_proof_status"] == "proved"
    assert groups["execution_group_reconciliation_failed"]["final_reconciliation_state"] == "reconciliation_failed"
    assert groups["execution_group_reconciliation_failed"]["final_trust_status"] == "reconciliation_failed"
    assert groups["execution_group_reconciliation_failed"]["final_reconciliation_reason_code"] == "provider_record_not_found"
    assert evidence["governed_external_run_summary"]["final_proof_missing_count"] == 1
    assert evidence["governed_external_run_summary"]["final_reconciliation_failed_count"] == 1


def test_store_reconciliation_input_rejects_missing_proof_or_mismatched_provider_request_id(tmp_path):
    repo_root = _prepare_repo(tmp_path)
    store = SessionStore(repo_root)
    task = store.create_task("tactics-game", "Trust Guardrail Task", "Verify reconciliation input validation")
    run = store.create_run("tactics-game", task["id"])

    store.create_governed_external_call_record(
        external_call_id="external_call_no_proof",
        execution_group_id="execution_group_no_proof",
        attempt_number=1,
        run_id=run["id"],
        task_packet_id="req_no_proof",
        reservation_id="reservation_no_proof",
        provider="openai",
        model="gpt-5.4-mini",
        execution_path="governed_api",
        execution_path_classification="governed_api_executed",
        claim_status="claimed",
        proof_status="missing",
        started_at="2026-04-12T11:15:00+00:00",
        outcome_status="completed",
    )
    store.create_governed_external_call_record(
        external_call_id="external_call_mismatched_proof",
        execution_group_id="execution_group_mismatched_proof",
        attempt_number=1,
        run_id=run["id"],
        task_packet_id="req_mismatched_proof",
        reservation_id="reservation_mismatched_proof",
        provider="openai",
        model="gpt-5.4-mini",
        execution_path="governed_api",
        execution_path_classification="governed_api_executed",
        claim_status="claimed",
        proof_status="proved",
        provider_request_id="resp_expected",
        started_at="2026-04-12T11:16:00+00:00",
        outcome_status="completed",
    )

    with pytest.raises(ValueError, match="Cannot record reconciliation without provider proof"):
        store.record_governed_external_reconciliation(
            external_call_id="external_call_no_proof",
            provider_request_id="resp_missing",
            reconciliation_state="reconciled",
            reconciliation_evidence_source="provider_ledger",
        )

    with pytest.raises(ValueError, match="provider_request_id does not match"):
        store.record_governed_external_reconciliation(
            external_call_id="external_call_mismatched_proof",
            provider_request_id="resp_wrong",
            reconciliation_state="reconciled",
            reconciliation_evidence_source="provider_ledger",
        )

    with pytest.raises(ValueError, match="reconciliation_reason_code is required"):
        store.record_governed_external_reconciliation(
            external_call_id="external_call_mismatched_proof",
            provider_request_id="resp_expected",
            reconciliation_state="reconciliation_failed",
            reconciliation_evidence_source="provider_ledger",
        )


def test_store_lists_governed_external_trust_worklist_with_context_and_deterministic_order(tmp_path):
    repo_root = _prepare_repo(tmp_path)
    store = SessionStore(repo_root)
    milestone = store.create_milestone(
        "tactics-game",
        "M2 - Trust Follow-up",
        "Reconciliation follow-up is not yet visible.",
        "Operators can review unreconciled trust work cleanly.",
    )
    task = store.create_task(
        "tactics-game",
        "Review governed trust backlog",
        "Surface unreconciled provider-proof calls for follow-up",
        milestone_id=milestone["id"],
    )

    run_proof_old = store.create_run("tactics-game", task["id"])
    run_proof_new = store.create_run("tactics-game", task["id"])
    run_pending = store.create_run("tactics-game", task["id"])
    run_failed = store.create_run("tactics-game", task["id"])
    run_trusted = store.create_run("tactics-game", task["id"])

    store.create_governed_external_call_record(
        external_call_id="external_call_proof_old",
        execution_group_id="execution_group_proof_old",
        attempt_number=1,
        run_id=run_proof_old["id"],
        task_packet_id="req_proof_old",
        reservation_id="reservation_proof_old",
        provider="openai",
        model="gpt-5.4-mini",
        execution_path="governed_api",
        execution_path_classification="governed_api_executed",
        claim_status="claimed",
        proof_status="proved",
        provider_request_id="resp_proof_old",
        started_at="2026-04-12T11:00:00+00:00",
        finished_at="2026-04-12T11:00:05+00:00",
        outcome_status="completed",
    )
    store.create_governed_external_call_record(
        external_call_id="external_call_proof_new",
        execution_group_id="execution_group_proof_new",
        attempt_number=1,
        run_id=run_proof_new["id"],
        task_packet_id="req_proof_new",
        reservation_id="reservation_proof_new",
        provider="openai",
        model="gpt-5.4-mini",
        execution_path="governed_api",
        execution_path_classification="governed_api_executed",
        claim_status="claimed",
        proof_status="proved",
        provider_request_id="resp_proof_new",
        started_at="2026-04-12T11:01:00+00:00",
        finished_at="2026-04-12T11:01:05+00:00",
        outcome_status="completed",
    )
    store.create_governed_external_call_record(
        external_call_id="external_call_pending",
        execution_group_id="execution_group_pending",
        attempt_number=1,
        run_id=run_pending["id"],
        task_packet_id="req_pending",
        reservation_id="reservation_pending",
        provider="openai",
        model="gpt-5.4-mini",
        execution_path="governed_api",
        execution_path_classification="governed_api_executed",
        claim_status="claimed",
        proof_status="proved",
        provider_request_id="resp_pending",
        started_at="2026-04-12T11:02:00+00:00",
        finished_at="2026-04-12T11:02:05+00:00",
        outcome_status="completed",
    )
    store.create_governed_external_call_record(
        external_call_id="external_call_failed",
        execution_group_id="execution_group_failed",
        attempt_number=1,
        run_id=run_failed["id"],
        task_packet_id="req_failed",
        reservation_id="reservation_failed",
        provider="openai",
        model="gpt-5.4-mini",
        execution_path="governed_api",
        execution_path_classification="governed_api_executed",
        claim_status="claimed",
        proof_status="proved",
        provider_request_id="resp_failed",
        started_at="2026-04-12T11:03:00+00:00",
        finished_at="2026-04-12T11:03:05+00:00",
        outcome_status="completed",
    )
    store.create_governed_external_call_record(
        external_call_id="external_call_trusted",
        execution_group_id="execution_group_trusted",
        attempt_number=1,
        run_id=run_trusted["id"],
        task_packet_id="req_trusted",
        reservation_id="reservation_trusted",
        provider="openai",
        model="gpt-5.4-mini",
        execution_path="governed_api",
        execution_path_classification="governed_api_executed",
        claim_status="claimed",
        proof_status="proved",
        provider_request_id="resp_trusted",
        started_at="2026-04-12T11:04:00+00:00",
        finished_at="2026-04-12T11:04:05+00:00",
        outcome_status="completed",
    )

    store.record_governed_external_reconciliation(
        external_call_id="external_call_pending",
        provider_request_id="resp_pending",
        reconciliation_state="reconciliation_pending",
        reconciliation_evidence_source="provider_ledger",
        reconciliation_checked_at="2026-04-12T11:05:00+00:00",
    )
    store.record_governed_external_reconciliation(
        external_call_id="external_call_failed",
        provider_request_id="resp_failed",
        reconciliation_state="reconciliation_failed",
        reconciliation_evidence_source="provider_ledger",
        reconciliation_checked_at="2026-04-12T11:06:00+00:00",
        reconciliation_reason_code="provider_record_not_found",
    )
    store.record_governed_external_reconciliation(
        external_call_id="external_call_trusted",
        provider_request_id="resp_trusted",
        reconciliation_state="reconciled",
        reconciliation_evidence_source="provider_ledger",
        reconciliation_checked_at="2026-04-12T11:07:00+00:00",
    )

    worklist = store.list_governed_external_trust_worklist()
    include_trusted = store.list_governed_external_trust_worklist(include_trusted=True)

    assert [item["external_call_id"] for item in worklist] == [
        "external_call_failed",
        "external_call_pending",
        "external_call_proof_new",
        "external_call_proof_old",
    ]
    assert worklist[0]["worklist_category"] == "reconciliation_failed"
    assert worklist[0]["task_id"] == task["id"]
    assert worklist[0]["project_name"] == "tactics-game"
    assert worklist[0]["milestone_id"] == milestone["id"]
    assert worklist[0]["provider_request_id"] == "resp_failed"
    assert worklist[0]["reconciliation_reason_code"] == "provider_record_not_found"
    assert worklist[0]["reconciliation_checked_at"] == "2026-04-12T11:06:00+00:00"
    assert worklist[0]["trust_status"] == "reconciliation_failed"
    assert worklist[1]["worklist_category"] == "reconciliation_pending"
    assert worklist[2]["worklist_category"] == "proof_captured_not_reconciled"
    assert worklist[2]["started_at"] == "2026-04-12T11:01:00+00:00"
    assert all(item["trust_status"] != "trusted_reconciled" for item in worklist)
    assert [item["external_call_id"] for item in include_trusted][-1] == "external_call_trusted"
    assert include_trusted[-1]["trust_status"] == "trusted_reconciled"


def test_store_aggregates_task_milestone_and_project_trust_followup_summaries(tmp_path):
    repo_root = _prepare_repo(tmp_path)
    store = SessionStore(repo_root)
    milestone_active = store.create_milestone(
        "tactics-game",
        "M3 - Trust Aggregation",
        "Trust follow-up is only visible at run level.",
        "Task, milestone, and project trust summaries are available.",
    )
    milestone_clean = store.create_milestone(
        "tactics-game",
        "M4 - Trusted Slice",
        "Trusted runs should stay clean in rollups.",
        "Trusted runs do not create false follow-up.",
    )
    task_followup = store.create_task(
        "tactics-game",
        "Aggregate trust follow-up",
        "Surface unresolved trust states from linked runs.",
        milestone_id=milestone_active["id"],
    )
    task_pending = store.create_task(
        "tactics-game",
        "Aggregate pending reconciliation",
        "Surface reconciliation pending distinctly.",
        milestone_id=milestone_active["id"],
    )
    task_clean = store.create_task(
        "tactics-game",
        "Keep trusted runs clean",
        "Trusted runs should not add trust follow-up noise.",
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
        external_call_id="external_call_task_failed",
        execution_group_id="execution_group_task_failed",
        attempt_number=1,
        run_id=run_failed["id"],
        task_packet_id="req_task_failed",
        reservation_id="reservation_task_failed",
        provider="openai",
        model="gpt-5.4-mini",
        execution_path="governed_api",
        execution_path_classification="governed_api_executed",
        claim_status="claimed",
        proof_status="proved",
        provider_request_id="resp_task_failed",
        started_at="2026-04-12T12:00:00+00:00",
        finished_at="2026-04-12T12:00:05+00:00",
        outcome_status="completed",
    )
    store.record_governed_external_reconciliation(
        external_call_id="external_call_task_failed",
        provider_request_id="resp_task_failed",
        reconciliation_state="reconciliation_failed",
        reconciliation_evidence_source="provider_ledger",
        reconciliation_checked_at="2026-04-12T12:01:00+00:00",
        reconciliation_reason_code="provider_record_not_found",
    )

    store.create_governed_external_call_record(
        external_call_id="external_call_task_unreconciled",
        execution_group_id="execution_group_task_unreconciled",
        attempt_number=1,
        run_id=run_unreconciled["id"],
        task_packet_id="req_task_unreconciled",
        reservation_id="reservation_task_unreconciled",
        provider="openai",
        model="gpt-5.4-mini",
        execution_path="governed_api",
        execution_path_classification="governed_api_executed",
        claim_status="claimed",
        proof_status="proved",
        provider_request_id="resp_task_unreconciled",
        started_at="2026-04-12T12:02:00+00:00",
        finished_at="2026-04-12T12:02:05+00:00",
        outcome_status="completed",
    )

    store.create_governed_external_call_record(
        external_call_id="external_call_task_pending",
        execution_group_id="execution_group_task_pending",
        attempt_number=1,
        run_id=run_pending["id"],
        task_packet_id="req_task_pending",
        reservation_id="reservation_task_pending",
        provider="openai",
        model="gpt-5.4-mini",
        execution_path="governed_api",
        execution_path_classification="governed_api_executed",
        claim_status="claimed",
        proof_status="proved",
        provider_request_id="resp_task_pending",
        started_at="2026-04-12T12:03:00+00:00",
        finished_at="2026-04-12T12:03:05+00:00",
        outcome_status="completed",
    )
    store.record_governed_external_reconciliation(
        external_call_id="external_call_task_pending",
        provider_request_id="resp_task_pending",
        reconciliation_state="reconciliation_pending",
        reconciliation_evidence_source="provider_ledger",
        reconciliation_checked_at="2026-04-12T12:04:00+00:00",
    )

    store.create_governed_external_call_record(
        external_call_id="external_call_task_trusted",
        execution_group_id="execution_group_task_trusted",
        attempt_number=1,
        run_id=run_trusted["id"],
        task_packet_id="req_task_trusted",
        reservation_id="reservation_task_trusted",
        provider="openai",
        model="gpt-5.4-mini",
        execution_path="governed_api",
        execution_path_classification="governed_api_executed",
        claim_status="claimed",
        proof_status="proved",
        provider_request_id="resp_task_trusted",
        started_at="2026-04-12T12:05:00+00:00",
        finished_at="2026-04-12T12:05:05+00:00",
        outcome_status="completed",
    )
    store.record_governed_external_reconciliation(
        external_call_id="external_call_task_trusted",
        provider_request_id="resp_task_trusted",
        reconciliation_state="reconciled",
        reconciliation_evidence_source="provider_ledger",
        reconciliation_checked_at="2026-04-12T12:06:00+00:00",
    )

    task_followup_graph = store.get_task_work_graph(task_followup["id"])
    task_followup_trust = store.summarize_task_trust(task_followup["id"])
    milestone_active_trust = store.summarize_milestone_trust(milestone_active["id"])
    milestone_clean_trust = store.summarize_milestone_trust(milestone_clean["id"])
    project_trust = store.summarize_project_trust("tactics-game")

    assert task_followup_graph["trust_summary"] == task_followup_trust
    assert task_followup_trust["trust_followup_needed"] is True
    assert task_followup_trust["trust_followup_count"] == 2
    assert task_followup_trust["unreconciled_run_count"] == 2
    assert task_followup_trust["latest_trust_status"] == "proof_captured_not_reconciled"
    assert task_followup_trust["latest_reconciliation_state"] == "not_reconciled"
    assert task_followup_trust["highest_priority_trust_issue"] == "reconciliation_failed"
    assert task_followup_trust["highest_priority_run_id"] == run_failed["id"]
    assert task_followup_trust["reconciliation_failed_count"] == 1
    assert task_followup_trust["reconciliation_pending_count"] == 0
    assert task_followup_trust["proof_captured_not_reconciled_count"] == 1

    assert milestone_active_trust == {
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
    assert milestone_clean_trust == {
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
    assert project_trust == {
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


def test_store_migrates_legacy_usage_event_schema(tmp_path):
    repo_root = _prepare_repo(tmp_path)
    db_path = repo_root / "sessions" / "studio.db"
    connection = sqlite3.connect(db_path)
    try:
        connection.execute(
            """
            CREATE TABLE usage_events (
                id TEXT PRIMARY KEY,
                run_id TEXT NOT NULL,
                task_id TEXT NOT NULL,
                source TEXT,
                prompt_tokens INTEGER NOT NULL,
                completion_tokens INTEGER NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        connection.commit()
    finally:
        connection.close()

    store = SessionStore(repo_root)

    connection = sqlite3.connect(store.paths.db_path)
    connection.row_factory = sqlite3.Row
    try:
        columns = {row["name"] for row in connection.execute("PRAGMA table_info(usage_events)").fetchall()}
    finally:
        connection.close()

    assert {
        "model",
        "tier",
        "lane",
        "cached_input_tokens",
        "reasoning_tokens",
        "estimated_cost_usd",
    }.issubset(columns)


def test_store_schema_health_includes_execution_tables(tmp_path):
    repo_root = _prepare_repo(tmp_path)
    store = SessionStore(repo_root)

    health = store.schema_health()

    assert health["ok"] is True
    assert "execution_packets" in health["tables"]
    assert "execution_job_reservations" in health["tables"]
    assert "governed_pre_execution_blocks" in health["tables"]
    assert "governed_external_call_records" in health["tables"]
    assert "governed_external_reconciliation_records" in health["tables"]
    assert "governed_external_call_events" in health["tables"]


def test_store_run_evidence_includes_trace_events(tmp_path):
    repo_root = _prepare_repo(tmp_path)
    store = SessionStore(repo_root)
    task = store.create_task("tactics-game", "Trace Task", "Verify trace ledger recording")
    run = store.create_run("tactics-game", task["id"])

    store.record_trace_event(
        run["id"],
        task["id"],
        "operator_request_confirmed",
        source="Orchestrator",
        summary="Operator confirmed the request.",
        packet={"objective": "Verify trace ledger recording"},
        route={"runtime_role": "Orchestrator", "model": "gpt-test"},
        raw_json={"request_text": "Verify trace ledger recording"},
    )

    evidence = store.get_run_evidence(run["id"])

    assert evidence["trace_events"][0]["event_type"] == "operator_request_confirmed"
    assert evidence["trace_events"][0]["payload"]["summary"] == "Operator confirmed the request."


def test_store_run_evidence_includes_sdk_runtime_summary(tmp_path):
    repo_root = _prepare_repo(tmp_path)
    store = SessionStore(repo_root)
    task = store.create_task("tactics-game", "SDK Task", "Verify SDK runtime evidence")
    run = store.create_run(
        "tactics-game",
        task["id"],
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
    agent_run = store.create_agent_run(run["id"], task["id"], "Architect")
    store.record_trace_event(
        run["id"],
        task["id"],
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
    store.record_trace_event(
        run["id"],
        task["id"],
        "sdk_approval_bridge_requested",
        source="PM",
        summary="Paused for SDK specialist approval.",
        packet={
            "approval_id": "approval_test",
            "target_role": "Developer",
            "session_id": f"studio-specialist-developer-{run['id']}",
            "expected_artifact_path": "projects/tactics-game/artifacts/sdk.py",
            "runtime_mode": "sdk",
        },
        route={"runtime_role": "Developer", "runtime_mode": "sdk"},
        raw_json={"approval_id": "approval_test"},
    )

    evidence = store.get_run_evidence(run["id"])

    assert evidence["sdk_runtime"]["mode"] == "sdk"
    assert evidence["sdk_runtime"]["sessions"][0]["session_id"] == f"studio-specialist-architect-{run['id']}"
    assert evidence["sdk_runtime"]["approval_bridge_events"][0]["approval_id"] == "approval_test"
    assert evidence["sdk_runtime"]["specialist_run_count"] == 1


def test_store_run_evidence_includes_worker_manifest_summary(tmp_path):
    repo_root = _prepare_repo(tmp_path)
    store = SessionStore(repo_root)
    task = store.create_task("tactics-game", "Manifest Task", "Verify worker manifest evidence")
    run = store.create_run("tactics-game", task["id"])
    store.update_run(
        run["id"],
        team_state={
            "execution_mode": "worker_only",
            "runtime_mode": "custom",
            "worker_dispatch": {
                "task_id": task["id"],
                "role": "Developer",
                "expected_output_path": "projects/tactics-game/artifacts/manifest-task.py",
                "manifest": {
                    "manifest_version": 1,
                    "execution_mode": "worker_only",
                    "run_id": run["id"],
                    "task_id": task["id"],
                    "project_name": "tactics-game",
                    "role": "Developer",
                    "runtime_mode": "custom",
                    "write_scope": "exact_paths_only",
                    "expected_output_path": "projects/tactics-game/artifacts/manifest-task.py",
                    "allowed_write_paths": ["projects/tactics-game/artifacts/manifest-task.py"],
                    "allowed_write_modes": ["overwrite"],
                    "input_artifact_paths": [],
                    "issued_by": "PM",
                    "issued_at": "2026-03-29T00:00:00+00:00",
                    "seal_sha256": "test-seal",
                },
            },
        },
    )

    evidence = store.get_run_evidence(run["id"])

    assert evidence["worker_dispatch"]["expected_output_path"] == "projects/tactics-game/artifacts/manifest-task.py"
    assert evidence["worker_dispatch"]["manifest"]["write_scope"] == "exact_paths_only"
    assert evidence["worker_manifest"]["seal_sha256"] == "test-seal"


def test_store_run_evidence_includes_context_receipt(tmp_path):
    repo_root = _prepare_repo(tmp_path)
    store = SessionStore(repo_root)
    task = store.create_task(
        "tactics-game",
        "Receipt Task",
        "Verify continuity receipts are persisted canonically.",
        objective="Persist a restore-safe continuity receipt.",
        expected_artifact_path="projects/tactics-game/artifacts/receipt.md",
    )
    run = store.create_run("tactics-game", task["id"], team_state={"phase": "intake", "runtime_mode": "custom"})

    receipt = store.save_context_receipt(
        run["id"],
        {
            "active_lane": task["id"],
            "approved_objective": task["objective"],
            "accepted_assumptions": ["Use the canonical SQLite store."],
            "allowed_tools": ["read_project_brief", "write_project_artifact"],
            "allowed_paths": [task["expected_artifact_path"]],
            "prior_artifact_paths": ["projects/tactics-game/artifacts/upstream.md"],
            "expected_output": task["expected_artifact_path"],
            "next_reviewer": "QA",
            "resume_conditions": ["Resume the same lane unless the receipt changes materially."],
            "current_owner_role": "Architect",
        },
    )
    evidence = store.get_run_evidence(run["id"])

    assert receipt["task_id"] == task["id"]
    assert evidence["context_receipt"]["active_lane"] == task["id"]
    assert evidence["context_receipt"]["allowed_tools"] == ["read_project_brief", "write_project_artifact"]
    assert evidence["context_receipt"]["allowed_paths"] == [task["expected_artifact_path"]]
    assert evidence["context_receipt"]["next_reviewer"] == "QA"
    assert evidence["context_receipt"]["current_owner_role"] == "Architect"
    assert evidence["context_receipt"]["updated_at"]


def test_save_context_receipt_merges_with_existing_worker_dispatch_team_state(tmp_path):
    repo_root = _prepare_repo(tmp_path)
    store = SessionStore(repo_root)
    task = store.create_task(
        "tactics-game",
        "Merge Task",
        "Verify context receipt persistence does not clobber worker dispatch state.",
        objective="Verify context receipt persistence does not clobber worker dispatch state.",
        expected_artifact_path="projects/tactics-game/artifacts/merge.py",
    )
    run = store.create_run("tactics-game", task["id"])
    original_team_state = {
        "execution_mode": "worker_only",
        "runtime_mode": "custom",
        "worker_dispatch": {
            "task_id": task["id"],
            "role": "Developer",
            "expected_output_path": task["expected_artifact_path"],
            "manifest": {
                "manifest_version": 1,
                "execution_mode": "worker_only",
                "run_id": run["id"],
                "task_id": task["id"],
                "project_name": "tactics-game",
                "role": "Developer",
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
    }
    store.update_run(run["id"], team_state=original_team_state)

    store.save_context_receipt(
        run["id"],
        {
            "active_lane": task["id"],
            "approved_objective": task["objective"],
            "allowed_tools": ["read_project_brief", "write_project_artifact"],
            "next_reviewer": "QA",
            "resume_conditions": ["Resume the same lane unless the receipt changes materially."],
        },
    )

    team_state = store.load_team_state(run["id"])
    evidence = store.get_run_evidence(run["id"])

    assert team_state is not None
    assert team_state["worker_dispatch"] == original_team_state["worker_dispatch"]
    assert team_state["context_receipt"]["task_id"] == task["id"]
    assert evidence["worker_manifest"]["seal_sha256"] == "test-seal"
    assert evidence["context_receipt"]["next_reviewer"] == "QA"


def test_store_records_compliance_breaches_and_local_exception_approvals(tmp_path):
    repo_root = _prepare_repo(tmp_path)
    store = SessionStore(repo_root)
    task = store.create_task("tactics-game", "Compliance Task", "Verify compliance ledger recording")
    run = store.create_run("tactics-game", task["id"])

    compliant = store.record_compliance_record(
        run["id"],
        task["id"],
        record_kind="compliant_delegated_run",
        details="Delegated run stayed within policy and budget.",
        source_role="Developer",
        evidence={"mode": "delegated"},
    )
    assert compliant["record_kind"] == "compliant_delegated_run"
    assert compliant["compliance_state"] == "compliant"

    approval = store.create_local_exception_approval(
        run["id"],
        task["id"],
        "Orchestrator",
        "Framework repair needs a temporary local exception.",
        target_role="Developer",
        exact_task="Patch the runtime boundary guard.",
        expected_output="A minimal guarded fix.",
        why_now="The current run is blocked on a repair-only path.",
        risks=["Temporary local repair only"],
    )
    decided = store.decide_local_exception_approval(approval["id"], "approve", "Approved for one-shot use.")
    assert decided["status"] == "approved"

    local_exception = store.record_compliance_record(
        run["id"],
        task["id"],
        record_kind="local_exception_approved",
        details="Local exception used for the approved framework repair.",
        local_exception_approval_id=approval["id"],
        source_role="Developer",
        evidence={"mode": "local-exception"},
    )
    assert local_exception["record_kind"] == "local_exception_approved"
    assert local_exception["compliance_state"] == "approved_exception"
    assert local_exception["local_exception_approval_id"] == approval["id"]

    breach = store.record_breach_event(
        run["id"],
        task["id"],
        policy_area="budget",
        violation_type="token_limit_exceeded",
        details="Budget cap exceeded during the run.",
        source_role="Developer",
        evidence={"overage": 12},
    )
    assert breach["record_kind"] == "breach"
    assert breach["compliance_state"] == "breach"

    try:
        store.record_compliance_record(
            run["id"],
            task["id"],
            record_kind="local_exception_approved",
            details="Missing approval reference should fail closed.",
        )
        assert False, "Expected a local-exception compliance record to require an approval id."
    except ValueError as error:
        assert "local exception approval id" in str(error)

    try:
        store.record_compliance_record(
            run["id"],
            task["id"],
            record_kind="local_exception_approved",
            details="Reusing the approval should fail closed.",
            local_exception_approval_id=approval["id"],
        )
        assert False, "Expected a consumed local-exception approval to be one-shot."
    except ValueError as error:
        assert "already been consumed" in str(error)

    records = store.list_compliance_records(run["id"])
    assert [record["record_kind"] for record in records] == [
        "compliant_delegated_run",
        "local_exception_approved",
        "breach",
    ]

    approvals = store.list_local_exception_approvals(run["id"])
    assert approvals[0]["status"] == "approved"
    assert approvals[0]["consumed_at"] is not None

    evidence = store.get_run_evidence(run["id"])
    assert [record["record_kind"] for record in evidence["compliance_records"]] == [
        "compliant_delegated_run",
        "local_exception_approved",
        "breach",
    ]
    assert evidence["local_exception_approvals"][0]["id"] == approval["id"]


def test_create_dispatch_backup_writes_backup_and_manifest(tmp_path):
    repo_root = _prepare_repo(tmp_path)
    store = SessionStore(repo_root)
    task = store.create_task("tactics-game", "Backup Task", "Verify pre-dispatch backups")
    run = store.create_run("tactics-game", task["id"], team_state={"phase": "intake", "runtime_mode": "custom"})
    receipt = store.save_context_receipt(
        run["id"],
        {
            "active_lane": task["id"],
            "approved_objective": task["title"],
            "next_reviewer": "PM",
            "resume_conditions": ["Resume with the existing task frame."],
            "current_owner_role": "Orchestrator",
        },
    )

    backup = store.create_dispatch_backup(
        project_name="tactics-game",
        trigger="dispatch_request",
        task_id=task["id"],
        note="Verify pre-dispatch backups",
    )

    assert Path(backup["path"]).exists()
    assert Path(backup["manifest_path"]).exists()
    assert backup["sha256"]

    connection = sqlite3.connect(backup["path"])
    try:
        tables = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type = 'table'")}
    finally:
        connection.close()
    assert "tasks" in tables

    manifest = json.loads(Path(backup["manifest_path"]).read_text(encoding="utf-8"))
    assert manifest["project_name"] == "tactics-game"
    assert manifest["task_id"] == task["id"]
    assert manifest["source_run_id"] == run["id"]
    assert manifest["source_context_receipt"]["task_id"] == task["id"]
    assert manifest["source_context_receipt"]["next_reviewer"] == "PM"
    assert backup["source_run_id"] == run["id"]
    assert backup["source_context_receipt"]["approved_objective"] == receipt["approved_objective"]
    assert manifest["source_run_id"] == run["id"]
    assert manifest["source_context_receipt"]["task_id"] == task["id"]
    assert manifest["source_context_receipt"]["next_reviewer"] == "PM"


def test_restore_dispatch_backup_restores_db_and_creates_receipt(tmp_path):
    repo_root = _prepare_repo(tmp_path)
    store = SessionStore(repo_root)
    task = store.create_task("tactics-game", "Restore Task", "Verify control-room restore flow")
    run = store.create_run("tactics-game", task["id"], team_state={"phase": "intake", "runtime_mode": "custom"})
    original_receipt = store.save_context_receipt(
        run["id"],
        {
            "active_lane": task["id"],
            "approved_objective": "Verify control-room restore flow",
            "accepted_assumptions": ["Use the restored canonical store."],
            "allowed_tools": ["read_project_brief", "write_project_artifact"],
            "allowed_paths": ["projects/tactics-game/artifacts/restore.md"],
            "prior_artifact_paths": ["projects/tactics-game/artifacts/upstream.md"],
            "expected_output": "projects/tactics-game/artifacts/restore.md",
            "next_reviewer": "QA",
            "resume_conditions": ["Resume the same lane unless the receipt changes materially."],
            "current_owner_role": "Architect",
        },
    )

    backup = store.create_dispatch_backup(
        project_name="tactics-game",
        trigger="restore_test",
        task_id=task["id"],
        note="Create a snapshot before changing task state.",
    )

    store.update_task(task["id"], status="in_progress", owner_role="Developer", result_summary="State changed")
    store.save_context_receipt(
        run["id"],
        {
            "next_reviewer": "Operator",
            "resume_conditions": ["This mutated receipt should be replaced by restore."],
            "current_owner_role": "Developer",
        },
    )
    changed = store.get_task(task["id"])
    assert changed is not None
    assert changed["status"] == "in_progress"

    restore = store.restore_dispatch_backup(backup_id=backup["backup_id"], requested_by="Test Runner")

    restored_store = SessionStore(repo_root)
    restored_task = restored_store.get_task(task["id"])
    restored_receipt = restored_store.load_context_receipt(run["id"])

    assert restored_task is not None
    assert restored_task["status"] == "backlog"
    assert restored_receipt is not None
    for field in (
        "task_id",
        "active_lane",
        "approved_objective",
        "accepted_assumptions",
        "allowed_tools",
        "allowed_paths",
        "prior_artifact_paths",
        "expected_output",
        "next_reviewer",
        "resume_conditions",
        "current_owner_role",
    ):
        assert restored_receipt[field] == original_receipt[field]
    assert Path(restore["receipt_path"]).exists()
    assert Path(restore["pre_restore_backup"]["path"]).exists()
    assert restore["store_health"]["ok"] is True
    assert restore["source_run_id"] == run["id"]
    assert restore["restored_run_id"] == run["id"]
    assert restore["source_context_receipt"]["next_reviewer"] == "QA"
    assert restore["restored_context_receipt"]["next_reviewer"] == "QA"
    assert restore["restored_context_receipt"]["resume_conditions"] == [
        "Resume the same lane unless the receipt changes materially."
    ]
    evidence = restored_store.get_run_evidence(run["id"])
    assert evidence["restore_history"][0]["restore_id"] == restore["restore_id"]
    assert evidence["restore_history"][0]["restored_context_receipt"]["current_owner_role"] == "Architect"


def test_store_builds_recovery_checkpoint_refs_for_aioffice_closeout(tmp_path):
    repo_root = _prepare_repo(tmp_path)
    store = SessionStore(repo_root)

    refs = store.build_recovery_checkpoint_refs(
        project_name="aioffice",
        milestone_key="M10",
        closeout_date="2026-04-16",
    )

    assert refs["project_name"] == "aioffice"
    assert refs["milestone_key"] == "m10"
    assert refs["closeout_date"] == "2026-04-16"
    assert refs["checkpoint_tag"] == "aioffice-m10-closeout-2026-04-16"
    assert refs["snapshot_branch"] == "snapshot/aioffice-m10-closeout-2026-04-16"
    assert store.validate_recovery_checkpoint_refs(
        project_name="aioffice",
        milestone_key="M10",
        closeout_date="2026-04-16",
        checkpoint_tag=refs["checkpoint_tag"],
        snapshot_branch=refs["snapshot_branch"],
    )["checkpoint_tag"] == "aioffice-m10-closeout-2026-04-16"


def test_store_creates_recovery_snapshot_manifest_after_preflight(tmp_path):
    repo_root, store = _prepare_aioffice_recovery_repo(tmp_path)

    manifest = store.create_recovery_snapshot_manifest(
        project_name="aioffice",
        milestone_key="M10",
        closeout_date="2026-04-16",
        working_branch="feature/aioffice-m10-change-governance-hardening",
    )

    manifest_path = Path(manifest["manifest_path"])
    assert manifest_path.exists()
    saved_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    expected_checkpoint_sha = _run_git(repo_root, "rev-list", "-n", "1", "aioffice-m10-closeout-2026-04-16")
    expected_snapshot_sha = _run_git(repo_root, "rev-parse", "snapshot/aioffice-m10-closeout-2026-04-16")
    expected_head_sha = _run_git(repo_root, "rev-parse", "HEAD")

    assert saved_manifest["schema_version"] == "recovery_snapshot_manifest_v1"
    assert saved_manifest["checkpoint_tag"] == "aioffice-m10-closeout-2026-04-16"
    assert saved_manifest["snapshot_branch"] == "snapshot/aioffice-m10-closeout-2026-04-16"
    assert saved_manifest["working_branch"] == "feature/aioffice-m10-change-governance-hardening"
    assert saved_manifest["checkpoint_commit_sha"] == expected_checkpoint_sha
    assert saved_manifest["snapshot_commit_sha"] == expected_snapshot_sha
    assert saved_manifest["current_head_commit_sha"] == expected_head_sha
    assert saved_manifest["clean_worktree"]["required"] is True
    assert saved_manifest["clean_worktree"]["is_clean"] is True
    assert saved_manifest["checkpoint_alignment"]["refs_match"] is True
    assert any(
        doc["path"] == "projects/aioffice/governance/ACTIVE_STATE.md"
        and doc["all_required_markers_present"] is True
        for doc in saved_manifest["authoritative_documents"]
    )


def test_store_recovery_preflight_rejects_dirty_worktree(tmp_path):
    repo_root, store = _prepare_aioffice_recovery_repo(tmp_path)
    (repo_root / "projects" / "aioffice" / "execution" / "KANBAN.md").write_text(
        "# AIOffice Operational Ledger\n\nDirty worktree\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="clean worktree"):
        store.run_recovery_preflight(
            project_name="aioffice",
            milestone_key="M10",
            closeout_date="2026-04-16",
            working_branch="feature/aioffice-m10-change-governance-hardening",
        )


def test_store_recovery_preflight_rejects_active_state_anchor_mismatch(tmp_path):
    repo_root, store = _prepare_aioffice_recovery_repo(tmp_path)
    active_state_path = repo_root / "projects" / "aioffice" / "governance" / "ACTIVE_STATE.md"
    active_state_path.write_text(
        active_state_path.read_text(encoding="utf-8").replace(
            "snapshot/aioffice-m10-closeout-2026-04-16",
            "snapshot/aioffice-m9-closeout-2026-04-16",
        ),
        encoding="utf-8",
    )
    _run_git(repo_root, "add", ".")
    _run_git(repo_root, "commit", "-m", "Break active state anchor")

    with pytest.raises(ValueError, match="authoritative docs to match the expected recovery anchors"):
        store.run_recovery_preflight(
            project_name="aioffice",
            milestone_key="M10",
            closeout_date="2026-04-16",
            working_branch="feature/aioffice-m10-change-governance-hardening",
        )


def test_store_creates_recovery_snapshot_package_with_backup_and_manifest(tmp_path):
    repo_root, store = _prepare_aioffice_recovery_repo(tmp_path)
    task = store.create_task("aioffice", "Recovery Package Task", "Create recovery package")
    _commit_all(repo_root, "Add recovery package task")

    package = store.create_recovery_snapshot_package(
        project_name="aioffice",
        milestone_key="M10",
        closeout_date="2026-04-16",
        working_branch="feature/aioffice-m10-change-governance-hardening",
        task_id=task["id"],
        trigger="prepare_restore",
        note="Create a lawful recovery package.",
        requested_by="Test Runner",
    )

    package_path = Path(package["package_path"])
    assert package_path.exists()
    saved_package = json.loads(package_path.read_text(encoding="utf-8"))
    assert saved_package["package_kind"] == "recovery_snapshot_package"
    assert saved_package["receipt_kind"] == "recovery_snapshot_created"
    assert saved_package["checkpoint_tag"] == "aioffice-m10-closeout-2026-04-16"
    assert saved_package["snapshot_branch"] == "snapshot/aioffice-m10-closeout-2026-04-16"
    assert Path(saved_package["recovery_manifest_path"]).exists()
    assert Path(saved_package["dispatch_backup_path"]).exists()
    assert Path(saved_package["dispatch_backup_manifest_path"]).exists()
    assert saved_package["verification"]["backup_manifest_verified"] is True
    assert saved_package["verification"]["backup_sha256_matches"] is True


def test_restore_recovery_snapshot_package_restores_db_and_records_receipt(tmp_path):
    repo_root, store = _prepare_aioffice_recovery_repo(tmp_path)
    task = store.create_task("aioffice", "Recovery Restore Task", "Verify hardened recovery restore")
    _commit_all(repo_root, "Add recovery restore task")
    run = store.create_run("aioffice", task["id"], team_state={"phase": "architect", "runtime_mode": "custom"})
    original_receipt = store.save_context_receipt(
        run["id"],
        {
            "active_lane": task["id"],
            "approved_objective": "Verify hardened recovery restore",
            "next_reviewer": "QA",
            "resume_conditions": ["Resume on the restored checkpoint."],
            "current_owner_role": "Architect",
        },
    )
    package = store.create_recovery_snapshot_package(
        project_name="aioffice",
        milestone_key="M10",
        closeout_date="2026-04-16",
        working_branch="feature/aioffice-m10-change-governance-hardening",
        task_id=task["id"],
        trigger="prepare_restore",
        note="Create recovery package before mutation.",
        requested_by="Test Runner",
    )

    store.save_context_receipt(
        run["id"],
        {
            "next_reviewer": "Operator",
            "resume_conditions": ["This mutated receipt should be replaced by restore."],
            "current_owner_role": "Developer",
        },
    )

    restore = store.restore_recovery_snapshot_package(
        recovery_package_id=package["recovery_package_id"],
        requested_by="Test Runner",
        project_name="aioffice",
        milestone_key="M10",
        closeout_date="2026-04-16",
        working_branch="feature/aioffice-m10-change-governance-hardening",
    )

    restored_store = SessionStore(repo_root)
    restored_receipt = restored_store.load_context_receipt(run["id"])

    assert restored_receipt is not None
    assert restored_receipt["approved_objective"] == original_receipt["approved_objective"]
    assert restored_receipt["next_reviewer"] == original_receipt["next_reviewer"]
    assert Path(restore["receipt_path"]).exists()
    assert restore["receipt_kind"] == "recovery_restore_completed"
    assert restore["verification"]["target_recovery_package_verified"] is True
    assert restore["verification"]["pre_action_snapshot_created"] is True
    assert restore["accepted_current_truth_changed"] is False
    assert restore["restore_status"] == "verified_candidate_only"
    assert Path(restore["pre_restore_recovery_package_path"]).exists()
    evidence = restored_store.get_run_evidence(run["id"])
    assert evidence["restore_history"][0]["restore_id"] == restore["restore_id"]
    assert evidence["restore_history"][0]["receipt_kind"] == "recovery_restore_completed"


def test_restore_recovery_snapshot_package_rejects_missing_backup_file(tmp_path):
    repo_root, store = _prepare_aioffice_recovery_repo(tmp_path)
    task = store.create_task("aioffice", "Missing Backup Task", "Reject missing recovery backup")
    _commit_all(repo_root, "Add missing backup task")
    package = store.create_recovery_snapshot_package(
        project_name="aioffice",
        milestone_key="M10",
        closeout_date="2026-04-16",
        working_branch="feature/aioffice-m10-change-governance-hardening",
        task_id=task["id"],
        trigger="prepare_restore",
        note="Create recovery package before deleting backup.",
        requested_by="Test Runner",
    )
    Path(package["dispatch_backup_path"]).unlink()

    with pytest.raises(ValueError, match="Backup file missing"):
        store.restore_recovery_snapshot_package(
            recovery_package_id=package["recovery_package_id"],
            requested_by="Test Runner",
            project_name="aioffice",
            milestone_key="M10",
            closeout_date="2026-04-16",
            working_branch="feature/aioffice-m10-change-governance-hardening",
        )


def test_prepare_recovery_rollback_creates_pre_action_snapshot_and_receipt(tmp_path):
    repo_root, store = _prepare_aioffice_recovery_repo(tmp_path)
    task = store.create_task("aioffice", "Rollback Task", "Prepare bounded rollback")
    _commit_all(repo_root, "Add rollback task")
    package = store.create_recovery_snapshot_package(
        project_name="aioffice",
        milestone_key="M10",
        closeout_date="2026-04-16",
        working_branch="feature/aioffice-m10-change-governance-hardening",
        task_id=task["id"],
        trigger="prepare_rollback_target",
        note="Create target recovery package before rollback prep.",
        requested_by="Test Runner",
    )

    receipt = store.prepare_recovery_rollback(
        recovery_package_id=package["recovery_package_id"],
        requested_by="Test Runner",
        project_name="aioffice",
        milestone_key="M10",
        closeout_date="2026-04-16",
        working_branch="feature/aioffice-m10-change-governance-hardening",
    )

    assert Path(receipt["receipt_path"]).exists()
    assert receipt["receipt_kind"] == "recovery_rollback_prepared"
    assert receipt["rollback_ready"] is True
    assert receipt["rollback_executed"] is False
    assert receipt["verification"]["target_recovery_package_verified"] is True
    assert receipt["verification"]["pre_action_snapshot_created"] is True
    assert Path(receipt["pre_rollback_recovery_package_path"]).exists()


def test_execute_recovery_rollback_restores_db_and_records_receipt(tmp_path):
    repo_root, store = _prepare_aioffice_recovery_repo(tmp_path)
    task = store.create_task("aioffice", "Rollback Execute Task", "Execute bounded rollback")
    _commit_all(repo_root, "Add rollback execution task")
    run = store.create_run("aioffice", task["id"], team_state={"phase": "architect", "runtime_mode": "custom"})
    original_receipt = store.save_context_receipt(
        run["id"],
        {
            "active_lane": task["id"],
            "approved_objective": "Verify bounded rollback execution",
            "next_reviewer": "QA",
            "resume_conditions": ["Resume only after rollback verification."],
            "current_owner_role": "Architect",
        },
    )
    package = store.create_recovery_snapshot_package(
        project_name="aioffice",
        milestone_key="M10",
        closeout_date="2026-04-16",
        working_branch="feature/aioffice-m10-change-governance-hardening",
        task_id=task["id"],
        trigger="prepare_rollback_target",
        note="Create rollback target package before mutation.",
        requested_by="Test Runner",
    )
    store.save_context_receipt(
        run["id"],
        {
            "next_reviewer": "Operator",
            "resume_conditions": ["Mutated state should be replaced by rollback."],
            "current_owner_role": "Developer",
        },
    )
    prepared = store.prepare_recovery_rollback(
        recovery_package_id=package["recovery_package_id"],
        requested_by="Test Runner",
        project_name="aioffice",
        milestone_key="M10",
        closeout_date="2026-04-16",
        working_branch="feature/aioffice-m10-change-governance-hardening",
    )

    receipt = store.execute_recovery_rollback(
        rollback_id=prepared["rollback_id"],
        requested_by="Test Runner",
        project_name="aioffice",
        milestone_key="M10",
        closeout_date="2026-04-16",
        working_branch="feature/aioffice-m10-change-governance-hardening",
    )

    rolled_back_store = SessionStore(repo_root)
    rolled_back_receipt = rolled_back_store.load_context_receipt(run["id"])

    assert rolled_back_receipt is not None
    assert rolled_back_receipt["approved_objective"] == original_receipt["approved_objective"]
    assert rolled_back_receipt["next_reviewer"] == original_receipt["next_reviewer"]
    assert rolled_back_receipt["current_owner_role"] == original_receipt["current_owner_role"]
    assert Path(receipt["receipt_path"]).exists()
    assert receipt["receipt_kind"] == "recovery_rollback_completed"
    assert receipt["prepared_rollback_id"] == prepared["rollback_id"]
    assert receipt["rollback_executed"] is True
    assert receipt["rollback_status"] == "executed_candidate_only"
    assert receipt["verification"]["prepared_rollback_receipt_verified"] is True
    assert receipt["verification"]["pre_action_snapshot_verified"] is True
    assert receipt["accepted_current_truth_changed"] is False


def test_execute_recovery_rollback_rejects_missing_pre_action_snapshot_evidence(tmp_path):
    repo_root, store = _prepare_aioffice_recovery_repo(tmp_path)
    task = store.create_task("aioffice", "Rollback Reject Task", "Reject incomplete rollback prep")
    _commit_all(repo_root, "Add rollback reject task")
    package = store.create_recovery_snapshot_package(
        project_name="aioffice",
        milestone_key="M10",
        closeout_date="2026-04-16",
        working_branch="feature/aioffice-m10-change-governance-hardening",
        task_id=task["id"],
        trigger="prepare_rollback_target",
        note="Create rollback target package before validation failure.",
        requested_by="Test Runner",
    )
    prepared = store.prepare_recovery_rollback(
        recovery_package_id=package["recovery_package_id"],
        requested_by="Test Runner",
        project_name="aioffice",
        milestone_key="M10",
        closeout_date="2026-04-16",
        working_branch="feature/aioffice-m10-change-governance-hardening",
    )
    receipt_path = Path(prepared["receipt_path"])
    saved_receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    saved_receipt["verification"]["pre_action_snapshot_created"] = False
    receipt_path.write_text(json.dumps(saved_receipt, indent=2) + "\n", encoding="utf-8")

    with pytest.raises(ValueError, match="pre-action snapshot evidence"):
        store.execute_recovery_rollback(
            rollback_id=prepared["rollback_id"],
            requested_by="Test Runner",
            project_name="aioffice",
            milestone_key="M10",
            closeout_date="2026-04-16",
            working_branch="feature/aioffice-m10-change-governance-hardening",
        )


def test_store_creates_and_lists_visual_artifacts(tmp_path):
    repo_root = _prepare_repo(tmp_path)
    design_dir = repo_root / "projects" / "tactics-game" / "artifacts" / "design"
    design_dir.mkdir(parents=True)
    image_path = design_dir / "concept-a.txt"
    image_path.write_text("concept-a", encoding="utf-8")

    store = SessionStore(repo_root)
    task = store.create_task("tactics-game", "Concept Task", "Track a visual artifact")
    run = store.create_run("tactics-game", task["id"])

    visual = store.create_visual_artifact(
        "tactics-game",
        task["id"],
        run_id=run["id"],
        artifact_path="projects/tactics-game/artifacts/design/concept-a.txt",
        provider="openai",
        model="gpt-image-1",
        prompt_summary="Top-down tactics board concept.",
        metadata={"variant": "A"},
        selected_direction=True,
    )

    listed = store.list_visual_artifacts("tactics-game", task_id=task["id"])

    assert visual["task_id"] == task["id"]
    assert visual["artifact_path"] == "projects/tactics-game/artifacts/design/concept-a.txt"
    assert visual["provider"] == "openai"
    assert visual["selected_direction"] is True
    assert visual["metadata"]["variant"] == "A"
    assert listed[0]["id"] == visual["id"]
    assert listed[0]["artifact_sha256"]


def test_store_sync_visual_artifact_updates_existing_record(tmp_path):
    repo_root = _prepare_repo(tmp_path)
    design_dir = repo_root / "projects" / "tactics-game" / "artifacts" / "design"
    design_dir.mkdir(parents=True)
    image_path = design_dir / "concept-b.txt"
    image_path.write_text("concept-b-v1", encoding="utf-8")

    store = SessionStore(repo_root)
    task = store.create_task("tactics-game", "Concept Sync Task", "Track synced visual artifacts")
    first_run = store.create_run("tactics-game", task["id"])
    second_run = store.create_run("tactics-game", task["id"])

    first = store.sync_visual_artifact(
        "tactics-game",
        task["id"],
        run_id=first_run["id"],
        artifact_path="projects/tactics-game/artifacts/design/concept-b.txt",
        provider="openai",
        model="gpt-image-1",
        prompt_summary="Initial concept.",
        metadata={"variant": "v1"},
    )

    image_path.write_text("concept-b-v2", encoding="utf-8")
    second = store.sync_visual_artifact(
        "tactics-game",
        task["id"],
        run_id=second_run["id"],
        artifact_path="projects/tactics-game/artifacts/design/concept-b.txt",
        provider="openai",
        model="gpt-image-1",
        prompt_summary="Revised concept.",
        metadata={"variant": "v2"},
    )

    listed = store.list_visual_artifacts("tactics-game", task_id=task["id"])

    assert first["id"] == second["id"]
    assert len(listed) == 1
    assert second["run_id"] == second_run["id"]
    assert second["prompt_summary"] == "Revised concept."
    assert second["metadata"]["variant"] == "v2"
    assert second["artifact_sha256"]


def test_store_tracks_locked_base_and_edit_session_provenance(tmp_path):
    repo_root = _prepare_repo(tmp_path)
    design_dir = repo_root / "projects" / "tactics-game" / "artifacts" / "design"
    design_dir.mkdir(parents=True)
    base_path = design_dir / "concept-base.txt"
    edit_path = design_dir / "concept-edit.txt"
    base_path.write_text("base-concept", encoding="utf-8")
    edit_path.write_text("edit-concept", encoding="utf-8")

    store = SessionStore(repo_root)
    task = store.create_task("tactics-game", "Edit Provenance Task", "Track locked-base lineage")
    run = store.create_run("tactics-game", task["id"])
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
        prompt_summary="Localised armor edit.",
        revised_prompt="Keep pose, change armor, preserve face.",
        parent_visual_artifact_id=root["id"],
        lineage_root_visual_artifact_id=root["id"],
        locked_base_visual_artifact_id=root["id"],
        edit_session_id="edit-session-001",
        edit_intent="localized_edit",
        edit_scope={"mode": "localized_edit", "regions": ["armor"]},
        protected_regions=["face", "hands", "background"],
        mask_reference={"kind": "region_mask", "path": "projects/tactics-game/artifacts/design/mask.json"},
        iteration_index=1,
        metadata={"variant": "B2"},
    )

    evidence = store.get_run_evidence(run["id"])

    assert edited["parent_visual_artifact_id"] == root["id"]
    assert edited["lineage_root_visual_artifact_id"] == root["id"]
    assert edited["locked_base_visual_artifact_id"] == root["id"]
    assert edited["edit_session_id"] == "edit-session-001"
    assert edited["edit_intent"] == "localized_edit"
    assert edited["edit_scope"]["regions"] == ["armor"]
    assert edited["protected_regions"] == ["face", "hands", "background"]
    assert edited["mask_reference"]["kind"] == "region_mask"
    assert edited["iteration_index"] == 1
    assert edited["metadata"]["variant"] == "B2"
    evidence_artifact = next(item for item in evidence["visual_artifacts"] if item["id"] == edited["id"])
    assert evidence_artifact["lineage_root_visual_artifact_id"] == root["id"]
    assert evidence_artifact["locked_base_visual_artifact_id"] == root["id"]
    assert evidence_artifact["edit_session_id"] == "edit-session-001"


def test_store_run_evidence_includes_visual_artifacts_from_subtasks(tmp_path):
    repo_root = _prepare_repo(tmp_path)
    design_dir = repo_root / "projects" / "tactics-game" / "artifacts" / "design"
    design_dir.mkdir(parents=True)
    image_path = design_dir / "concept-c.txt"
    image_path.write_text("concept-c", encoding="utf-8")

    store = SessionStore(repo_root)
    task = store.create_task("tactics-game", "Parent Visual Task", "Collect visual artifacts in run evidence")
    subtask = store.create_subtask(
        "tactics-game",
        task["id"],
        "Concept Variant",
        "Create a concept variant",
        objective="Create a concept variant",
        owner_role="Design",
        priority="medium",
        expected_artifact_path="projects/tactics-game/artifacts/design/concept-c.txt",
        acceptance={"deliverable_type": "image"},
    )
    run = store.create_run("tactics-game", task["id"])
    visual = store.sync_visual_artifact(
        "tactics-game",
        subtask["id"],
        run_id=run["id"],
        artifact_path="projects/tactics-game/artifacts/design/concept-c.txt",
        provider="openai",
        model="gpt-image-1",
        prompt_summary="Concept variant",
        metadata={"registered_by": "Framework"},
    )

    evidence = store.get_run_evidence(run["id"])

    assert evidence["visual_artifacts"][0]["id"] == visual["id"]
    assert evidence["visual_artifacts"][0]["task_id"] == subtask["id"]
    assert evidence["visual_artifacts"][0]["metadata"]["registered_by"] == "Framework"


def test_store_run_evidence_includes_media_service_contracts_for_visual_request(tmp_path):
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
        "Visual review boundary",
        "Keep visual asset bookkeeping deterministic.",
        objective="Keep visual asset bookkeeping deterministic.",
        expected_artifact_path="agents/orchestrator.py",
        acceptance={
            "proposed_milestone": "M8 - Visual Production And Digital Asset Management",
            "entry_goal": "Visual review is still conflated with specialist behavior.",
            "exit_goal": "The deterministic media-service boundary is operator-visible.",
            "design_request_preview": {
                "goal": "Review a visual request packet.",
                "target_surface": "control-room review gallery",
                "style_direction": None,
                "deliverables": ["design request preview", "screen or UI review packet"],
                "constraints": ["Keep review state canonical."],
                "open_questions": [],
            },
        },
    )
    run = store.create_run("program-kanban", task["id"])

    evidence = store.get_run_evidence(run["id"])

    assert evidence["media_service_contracts"]
    assert evidence["media_service_contracts"][0]["family"] == "visual"
    assert any(item["service_key"] == "review_state_persistence" for item in evidence["media_service_contracts"])


def test_visual_artifact_requires_design_artifact_path(tmp_path):
    repo_root = _prepare_repo(tmp_path)
    wrong_path = repo_root / "projects" / "tactics-game" / "artifacts" / "misc.txt"
    wrong_path.parent.mkdir(parents=True, exist_ok=True)
    wrong_path.write_text("not in design", encoding="utf-8")

    store = SessionStore(repo_root)
    task = store.create_task("tactics-game", "Bad Artifact Task", "Reject non-design artifact paths")

    try:
        store.create_visual_artifact(
            "tactics-game",
            task["id"],
            artifact_path="projects/tactics-game/artifacts/misc.txt",
        )
    except ValueError as exc:
        assert "artifacts/design" in str(exc)
    else:
        raise AssertionError("Expected create_visual_artifact to reject non-design artifact paths")


def test_program_kanban_ready_gate_requires_milestone_and_expected_output(tmp_path):
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
        "Implement the milestone wall.",
        objective="Implement the milestone wall.",
        owner_role="Dashboard Implementer",
        assigned_role="Dashboard Implementer",
        acceptance={
            "proposed_milestone": "M1 - Basic Operation Level",
            "entry_goal": "The board is missing milestone review.",
            "exit_goal": "Milestones are visible again.",
            "approved_decisions": {"progress_formula": "completed/total"},
        },
    )

    try:
        store.update_task(task["id"], status="ready")
        assert False, "Expected the Ready for Build gate to reject missing expected output."
    except ValueError as error:
        assert "Missing expected artifact or output." in str(error)

    updated = store.update_task(
        task["id"],
        expected_artifact_path="projects/program-kanban/app/app.js",
        status="ready",
    )
    assert updated["status"] == "ready"
    assert updated["milestone_id"] is not None
    milestone = store.get_milestone(updated["milestone_id"])
    assert milestone is not None
    assert milestone["title"] == "M1 - Basic Operation Level"


def test_program_kanban_complete_requires_explicit_acceptance(tmp_path):
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
        "Define workflow columns",
        "Capture the workflow model.",
        objective="Capture the workflow model.",
        owner_role="Project Orchestrator",
        assigned_role="Project Orchestrator",
        expected_artifact_path="projects/program-kanban/governance/spec.md",
        acceptance={
            "proposed_milestone": "M1 - Basic Operation Level",
            "entry_goal": "Columns are undefined.",
            "exit_goal": "Columns are approved.",
            "approved_decisions": {"columns": ["Backlog", "Ready for Build"]},
        },
    )
    store.update_task(task["id"], status="ready")

    try:
        store.update_task(task["id"], status="completed")
        assert False, "Expected Complete to require Accepted review state."
    except ValueError as error:
        assert "Complete requires review_state 'Accepted'." in str(error)

    completed = store.update_task(task["id"], status="completed", review_state="Accepted")
    assert completed["status"] == "completed"
    assert completed["review_state"] == "Accepted"
