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


def _prepare_pending_review_apply_bundle(tmp_path):
    repo_root = _prepare_repo(tmp_path)
    store = SessionStore(repo_root)

    workflow = store.create_workflow_run(
        "aioffice",
        task_id="AIO-031",
        objective="Prepare a bounded pending-review bundle for controlled promotion.",
        authoritative_workspace_root="projects/aioffice",
        current_stage="architect",
    )
    stage = store.create_stage_run(
        workflow["id"],
        stage_name="architect",
        status="in_progress",
    )

    source_artifact_path = (
        "projects/aioffice/artifacts/m5_apply_promotion/workflow_review/architect/architecture_decision_v1.md"
    )
    source_artifact_file = repo_root / "projects" / "aioffice" / "artifacts" / "m5_apply_promotion" / "workflow_review" / "architect" / "architecture_decision_v1.md"
    source_artifact_file.parent.mkdir(parents=True, exist_ok=True)
    source_artifact_file.write_text("# Architecture Decision\n\nPromote this reviewed output.\n", encoding="utf-8")

    artifact = store.create_workflow_artifact(
        "aioffice",
        workflow_run_id=workflow["id"],
        stage_run_id=stage["id"],
        task_id="AIO-031",
        contract_name="architecture_decision_v1",
        kind="document",
        content=source_artifact_file.read_text(encoding="utf-8"),
        proof_value="architecture_output",
        artifact_path=source_artifact_path,
        produced_by="Architect",
    )
    packet = store.issue_control_execution_packet(
        "aioffice",
        "AIO-031",
        objective="Apply or promote reviewed bundle outputs through a controlled store path.",
        authoritative_workspace_root="projects/aioffice",
        allowed_write_paths=[source_artifact_path],
        required_artifact_outputs=[source_artifact_path],
        required_validations=["pytest tests/test_control_kernel_store.py"],
        expected_return_bundle_contents=["produced artifacts", "evidence receipts"],
        failure_reporting_expectations=["report blockers", "report assumptions", "report proof gaps"],
        workflow_run_id=workflow["id"],
        stage_run_id=stage["id"],
        issued_by="Project Orchestrator",
        forbidden_paths=["projects/aioffice/governance", "projects/aioffice/execution/protected"],
        forbidden_actions=["self_accept", "self_promote"],
        provenance_note="AIO-031 bounded apply/promotion packet",
    )
    bundle = store.ingest_execution_bundle(
        packet["packet_id"],
        produced_artifact_ids=[artifact["id"]],
        diff_refs=[source_artifact_path],
        commands_run=["pytest tests/test_control_kernel_store.py"],
        test_results=[{"command": "pytest", "status": "passed"}],
        self_report_summary="Pending review bundle is ready for controlled promotion.",
        open_risks=["AIO-032 rehearsal remains out of scope."],
        evidence_receipts=[{"kind": "provider_metadata", "provider": "manual_harness", "status": "captured"}],
    )
    return {
        "repo_root": repo_root,
        "store": store,
        "workflow": workflow,
        "stage": stage,
        "artifact": artifact,
        "packet": packet,
        "bundle": bundle,
        "source_artifact_file": source_artifact_file,
        "source_artifact_path": source_artifact_path,
    }


def test_store_persists_control_kernel_entities_without_canonical_task_rows(tmp_path):
    repo_root = _prepare_repo(tmp_path)
    store = SessionStore(repo_root)

    workflow = store.create_workflow_run(
        "aioffice",
        task_id="AIO-023",
        objective="Persist the first control-kernel slice.",
        authoritative_workspace_root="projects/aioffice",
        current_stage="pm",
        scope={"trial": "m4-first-slice"},
    )
    stage = store.create_stage_run(
        workflow["id"],
        stage_name="pm",
        status="in_progress",
    )
    artifact = store.create_workflow_artifact(
        "aioffice",
        workflow_run_id=workflow["id"],
        stage_run_id=stage["id"],
        task_id="AIO-023",
        contract_name="pm_plan_v1",
        kind="document",
        content="# PM Plan\n\nBounded work.\n",
        proof_value="stage_output",
        produced_by="Architect",
    )
    handoff = store.create_handoff(
        workflow["id"],
        from_stage_name="pm",
        to_stage_name="context_audit",
        summary="PM plan is ready for audit.",
        stage_run_id=stage["id"],
        upstream_artifact_ids=[artifact["id"]],
    )
    blocker = store.create_blocker(
        workflow["id"],
        blocker_kind="missing_context",
        summary="Need donor path review before architecture starts.",
        stage_run_id=stage["id"],
    )
    question = store.create_question_or_assumption(
        workflow["id"],
        record_type="question",
        summary="Should the first slice persist bundle review notes?",
        stage_run_id=stage["id"],
        why_it_matters="Review state needs a durable home.",
    )
    assumption = store.create_question_or_assumption(
        workflow["id"],
        record_type="assumption",
        summary="AIO backlog remains project-local during M4.",
        stage_run_id=stage["id"],
        impact_or_risk="Canonical task rows are still out of scope.",
    )
    trace = store.record_orchestration_trace(
        workflow["id"],
        stage_run_id=stage["id"],
        event_type="packet_scope_defined",
        source="Project Orchestrator",
        payload={"allowed_write_paths": ["sessions/store.py"]},
    )

    assert workflow["task_id"] == "AIO-023"
    assert workflow["authoritative_workspace_root"] == "projects/aioffice"
    assert workflow["scope"]["trial"] == "m4-first-slice"
    assert stage["workflow_run_id"] == workflow["id"]
    assert store.list_workflow_artifacts(workflow["id"], stage_run_id=stage["id"])[0]["id"] == artifact["id"]
    assert store.list_handoffs(workflow["id"])[0]["upstream_artifact_ids"] == [artifact["id"]]
    assert store.list_blockers(workflow["id"])[0]["id"] == blocker["id"]
    records = store.list_question_or_assumptions(workflow["id"])
    assert {item["record_type"] for item in records} == {"question", "assumption"}
    assert trace["payload"]["allowed_write_paths"] == ["sessions/store.py"]


def test_store_defaults_skip_legacy_bootstrap_side_effects_for_isolated_rehearsal_roots(tmp_path):
    repo_root = tmp_path / "projects" / "aioffice" / "artifacts" / "m5_isolated_rehearsal" / "workspace"
    store = SessionStore(repo_root)
    workflow = store.create_workflow_run(
        "aioffice",
        task_id="AIO-029",
        objective="Run an isolated supervised rehearsal.",
        authoritative_workspace_root="projects/aioffice",
        current_stage="architect",
    )
    files = sorted(str(path.relative_to(repo_root)).replace("\\", "/") for path in repo_root.rglob("*") if path.is_file())

    assert workflow["project_name"] == "aioffice"
    assert (repo_root / "projects" / "aioffice").exists()
    assert not (repo_root / "projects" / "tactics-game" / "execution" / "KANBAN.md").exists()
    assert not (repo_root / "memory" / "framework_health.json").exists()
    assert not (repo_root / "memory" / "session_summaries.json").exists()
    assert files == ["sessions/studio.db"]


def test_store_can_explicitly_restore_legacy_bootstrap_side_effects_for_isolated_rehearsal_roots(tmp_path):
    repo_root = tmp_path / "projects" / "aioffice" / "artifacts" / "m5_isolated_rehearsal" / "workspace"

    SessionStore(repo_root, bootstrap_legacy_defaults=True)

    assert (repo_root / "projects" / "tactics-game" / "execution" / "KANBAN.md").exists()
    assert (repo_root / "memory" / "framework_health.json").exists()
    assert (repo_root / "memory" / "session_summaries.json").exists()


def test_store_issues_control_packets_and_ingests_bundles_without_self_acceptance(tmp_path):
    repo_root = _prepare_repo(tmp_path)
    store = SessionStore(repo_root)

    workflow = store.create_workflow_run(
        "aioffice",
        task_id="AIO-024",
        objective="Persist packets and bundles.",
        authoritative_workspace_root="projects/aioffice",
        current_stage="architect",
    )
    stage = store.create_stage_run(
        workflow["id"],
        stage_name="architect",
        status="in_progress",
    )
    artifact = store.create_workflow_artifact(
        "aioffice",
        workflow_run_id=workflow["id"],
        stage_run_id=stage["id"],
        task_id="AIO-024",
        contract_name="architecture_decision_v1",
        kind="document",
        content="# Architecture\n\nChosen approach.\n",
        proof_value="architecture_output",
    )
    blocker = store.create_blocker(
        workflow["id"],
        blocker_kind="review_pending",
        summary="Bundle review still required before apply.",
        stage_run_id=stage["id"],
    )
    question = store.create_question_or_assumption(
        workflow["id"],
        record_type="question",
        summary="Should inspection land before transition checks?",
        stage_run_id=stage["id"],
    )
    assumption = store.create_question_or_assumption(
        workflow["id"],
        record_type="assumption",
        summary="Initial inspection remains read-only.",
        stage_run_id=stage["id"],
    )

    packet = store.issue_control_execution_packet(
        "aioffice",
        "AIO-024",
        objective="Persist packet and bundle records in the sanctioned store.",
        authoritative_workspace_root="projects/aioffice",
        allowed_write_paths=["sessions/store.py", "tests/test_control_kernel_store.py"],
        scratch_path="tmp/aioffice/control-kernel",
        forbidden_paths=["projects/aioffice/governance"],
        forbidden_actions=["self_accept", "self_promote"],
        required_artifact_outputs=["sessions/store.py"],
        required_validations=["pytest tests/test_control_kernel_store.py"],
        expected_return_bundle_contents=["produced artifacts", "evidence receipts"],
        failure_reporting_expectations=["report blockers", "report open risks"],
        workflow_run_id=workflow["id"],
        stage_run_id=stage["id"],
        issued_by="Project Orchestrator",
        provenance_note="M4 bounded implementation bundle",
    )

    bundle = store.ingest_execution_bundle(
        packet["packet_id"],
        produced_artifact_ids=[artifact["id"]],
        diff_refs=["sessions/store.py"],
        commands_run=["pytest tests/test_control_kernel_store.py"],
        test_results=[{"command": "pytest", "status": "passed"}],
        blocker_ids=[blocker["id"]],
        question_ids=[question["id"]],
        assumption_ids=[assumption["id"]],
        self_report_summary="Persisted control-kernel entities and packet/bundle records.",
        open_risks=["Inspection path is still out of scope for this bundle."],
        evidence_receipts=[{"kind": "pytest", "status": "passed"}],
    )

    assert packet["project_name"] == "aioffice"
    assert packet["allowed_write_paths"] == ["sessions/store.py", "tests/test_control_kernel_store.py"]
    assert packet["packet_status"] == "issued"
    assert bundle["packet_id"] == packet["packet_id"]
    assert bundle["acceptance_state"] == "pending_review"
    assert store.list_execution_bundles(packet_id=packet["packet_id"])[0]["bundle_id"] == bundle["bundle_id"]


def test_store_control_packet_and_bundle_paths_fail_closed_on_missing_required_fields(tmp_path):
    repo_root = _prepare_repo(tmp_path)
    store = SessionStore(repo_root)
    workflow = store.create_workflow_run(
        "aioffice",
        task_id="AIO-024",
        objective="Fail closed on missing packet fields.",
        authoritative_workspace_root="projects/aioffice",
        current_stage="intake",
    )

    try:
        store.issue_control_execution_packet(
            "aioffice",
            "AIO-024",
            objective="Missing allowed paths should fail.",
            authoritative_workspace_root="projects/aioffice",
            allowed_write_paths=[],
            required_artifact_outputs=["sessions/store.py"],
            required_validations=["pytest tests/test_control_kernel_store.py"],
            expected_return_bundle_contents=["produced artifacts"],
            failure_reporting_expectations=["report blockers"],
            workflow_run_id=workflow["id"],
        )
    except ValueError as exc:
        assert "allowed_write_paths" in str(exc)
    else:
        raise AssertionError("Expected issue_control_execution_packet to fail closed on missing allowed_write_paths.")

    packet = store.issue_control_execution_packet(
        "aioffice",
        "AIO-024",
        objective="Question and assumption references must be typed correctly.",
        authoritative_workspace_root="projects/aioffice",
        allowed_write_paths=["sessions/store.py"],
        required_artifact_outputs=["sessions/store.py"],
        required_validations=["pytest tests/test_control_kernel_store.py"],
        expected_return_bundle_contents=["produced artifacts"],
        failure_reporting_expectations=["report blockers"],
        workflow_run_id=workflow["id"],
    )
    artifact = store.create_workflow_artifact(
        "aioffice",
        workflow_run_id=workflow["id"],
        task_id="AIO-024",
        contract_name="intake_request_v1",
        kind="document",
        content="# Intake\n\nRequest captured.\n",
        proof_value="intake_output",
    )
    assumption = store.create_question_or_assumption(
        workflow["id"],
        record_type="assumption",
        summary="This record should not satisfy question_ids.",
    )

    try:
        store.ingest_execution_bundle(
            packet["packet_id"],
            produced_artifact_ids=[artifact["id"]],
            diff_refs=[],
            commands_run=[],
            test_results=[],
            question_ids=[assumption["id"]],
            self_report_summary="This bundle should be rejected.",
            open_risks=[],
            evidence_receipts=[{"kind": "manual_review", "status": "captured"}],
        )
    except ValueError as exc:
        assert "question_ids" in str(exc)
    else:
        raise AssertionError("Expected ingest_execution_bundle to reject assumption ids in question_ids.")


def test_store_rejects_bundle_without_evidence_receipts(tmp_path):
    repo_root = _prepare_repo(tmp_path)
    store = SessionStore(repo_root)
    workflow = store.create_workflow_run(
        "aioffice",
        task_id="AIO-024",
        objective="Reject empty evidence receipts.",
        authoritative_workspace_root="projects/aioffice",
        current_stage="architect",
    )
    packet = store.issue_control_execution_packet(
        "aioffice",
        "AIO-024",
        objective="Require bundle receipts.",
        authoritative_workspace_root="projects/aioffice",
        allowed_write_paths=["sessions/store.py"],
        required_artifact_outputs=[],
        required_validations=["pytest tests/test_control_kernel_store.py"],
        expected_return_bundle_contents=["evidence receipts"],
        failure_reporting_expectations=["report blockers"],
        workflow_run_id=workflow["id"],
    )

    try:
        store.ingest_execution_bundle(
            packet["packet_id"],
            produced_artifact_ids=[],
            diff_refs=[],
            commands_run=[],
            test_results=[],
            self_report_summary="No receipts should fail closed.",
            open_risks=[],
            evidence_receipts=[],
        )
    except ValueError as exc:
        assert "evidence_receipts" in str(exc)
    else:
        raise AssertionError("Expected ingest_execution_bundle to reject empty evidence_receipts.")


def test_store_rejects_bundle_without_artifacts_when_packet_requires_outputs(tmp_path):
    repo_root = _prepare_repo(tmp_path)
    store = SessionStore(repo_root)
    workflow = store.create_workflow_run(
        "aioffice",
        task_id="AIO-024",
        objective="Reject empty produced artifacts when outputs are required.",
        authoritative_workspace_root="projects/aioffice",
        current_stage="architect",
    )
    packet = store.issue_control_execution_packet(
        "aioffice",
        "AIO-024",
        objective="Require produced artifacts.",
        authoritative_workspace_root="projects/aioffice",
        allowed_write_paths=["sessions/store.py"],
        required_artifact_outputs=["sessions/store.py"],
        required_validations=["pytest tests/test_control_kernel_store.py"],
        expected_return_bundle_contents=["produced artifacts"],
        failure_reporting_expectations=["report blockers"],
        workflow_run_id=workflow["id"],
    )

    try:
        store.ingest_execution_bundle(
            packet["packet_id"],
            produced_artifact_ids=[],
            diff_refs=[],
            commands_run=[],
            test_results=[],
            self_report_summary="Missing produced artifacts should fail.",
            open_risks=[],
            evidence_receipts=[{"kind": "manual_review", "status": "captured"}],
        )
    except ValueError as exc:
        assert "produced_artifact_ids" in str(exc)
    else:
        raise AssertionError(
            "Expected ingest_execution_bundle to reject empty produced_artifact_ids when outputs are required."
        )


def test_store_rejects_bundle_records_from_another_workflow_run(tmp_path):
    repo_root = _prepare_repo(tmp_path)
    store = SessionStore(repo_root)
    packet_workflow = store.create_workflow_run(
        "aioffice",
        task_id="AIO-024",
        objective="Packet workflow.",
        authoritative_workspace_root="projects/aioffice",
        current_stage="architect",
    )
    other_workflow = store.create_workflow_run(
        "aioffice",
        task_id="AIO-024",
        objective="Other workflow.",
        authoritative_workspace_root="projects/aioffice",
        current_stage="architect",
    )
    packet = store.issue_control_execution_packet(
        "aioffice",
        "AIO-024",
        objective="Reject cross-workflow references.",
        authoritative_workspace_root="projects/aioffice",
        allowed_write_paths=["sessions/store.py"],
        required_artifact_outputs=["sessions/store.py"],
        required_validations=["pytest tests/test_control_kernel_store.py"],
        expected_return_bundle_contents=["produced artifacts", "evidence receipts"],
        failure_reporting_expectations=["report blockers"],
        workflow_run_id=packet_workflow["id"],
    )
    valid_artifact = store.create_workflow_artifact(
        "aioffice",
        workflow_run_id=packet_workflow["id"],
        task_id="AIO-024",
        contract_name="architecture_decision_v1",
        kind="document",
        content="# Correct Workflow\n\nRight workflow.\n",
        proof_value="architecture_output",
    )
    other_artifact = store.create_workflow_artifact(
        "aioffice",
        workflow_run_id=other_workflow["id"],
        task_id="AIO-024",
        contract_name="architecture_decision_v1",
        kind="document",
        content="# Other Architecture\n\nWrong workflow.\n",
        proof_value="architecture_output",
    )
    other_blocker = store.create_blocker(
        other_workflow["id"],
        blocker_kind="review_pending",
        summary="Wrong workflow blocker.",
    )
    other_question = store.create_question_or_assumption(
        other_workflow["id"],
        record_type="question",
        summary="Wrong workflow question.",
    )
    other_assumption = store.create_question_or_assumption(
        other_workflow["id"],
        record_type="assumption",
        summary="Wrong workflow assumption.",
    )

    for payload, expected_fragment in (
        ({"produced_artifact_ids": [other_artifact["id"]]}, "artifact"),
        ({"blocker_ids": [other_blocker["id"]]}, "blocker"),
        ({"question_ids": [other_question["id"]]}, "question"),
        ({"assumption_ids": [other_assumption["id"]]}, "assumption"),
    ):
        try:
            store.ingest_execution_bundle(
                packet["packet_id"],
                produced_artifact_ids=payload.get("produced_artifact_ids", [valid_artifact["id"]]),
                diff_refs=[],
                commands_run=[],
                test_results=[],
                blocker_ids=payload.get("blocker_ids"),
                question_ids=payload.get("question_ids"),
                assumption_ids=payload.get("assumption_ids"),
                self_report_summary="Cross-workflow records should fail.",
                open_risks=[],
                evidence_receipts=[{"kind": "manual_review", "status": "captured"}],
            )
        except ValueError as exc:
            assert expected_fragment in str(exc)
            assert "workflow_run_id" in str(exc)
        else:
            raise AssertionError(f"Expected ingest_execution_bundle to reject cross-workflow {expected_fragment}.")


def test_store_rejects_bundle_records_from_another_stage_run(tmp_path):
    repo_root = _prepare_repo(tmp_path)
    store = SessionStore(repo_root)
    workflow = store.create_workflow_run(
        "aioffice",
        task_id="AIO-024",
        objective="Reject cross-stage references.",
        authoritative_workspace_root="projects/aioffice",
        current_stage="architect",
    )
    packet_stage = store.create_stage_run(workflow["id"], stage_name="architect", status="in_progress")
    other_stage = store.create_stage_run(workflow["id"], stage_name="architect", attempt_number=2, status="in_progress")
    packet = store.issue_control_execution_packet(
        "aioffice",
        "AIO-024",
        objective="Reject cross-stage records.",
        authoritative_workspace_root="projects/aioffice",
        allowed_write_paths=["sessions/store.py"],
        required_artifact_outputs=["sessions/store.py"],
        required_validations=["pytest tests/test_control_kernel_store.py"],
        expected_return_bundle_contents=["produced artifacts", "evidence receipts"],
        failure_reporting_expectations=["report blockers"],
        workflow_run_id=workflow["id"],
        stage_run_id=packet_stage["id"],
    )
    valid_artifact = store.create_workflow_artifact(
        "aioffice",
        workflow_run_id=workflow["id"],
        stage_run_id=packet_stage["id"],
        task_id="AIO-024",
        contract_name="architecture_decision_v1",
        kind="document",
        content="# Correct Stage\n\nRight stage.\n",
        proof_value="architecture_output",
    )
    other_artifact = store.create_workflow_artifact(
        "aioffice",
        workflow_run_id=workflow["id"],
        stage_run_id=other_stage["id"],
        task_id="AIO-024",
        contract_name="architecture_decision_v1",
        kind="document",
        content="# Other Stage\n\nWrong stage.\n",
        proof_value="architecture_output",
    )
    other_blocker = store.create_blocker(
        workflow["id"],
        blocker_kind="review_pending",
        summary="Wrong stage blocker.",
        stage_run_id=other_stage["id"],
    )
    other_question = store.create_question_or_assumption(
        workflow["id"],
        record_type="question",
        summary="Wrong stage question.",
        stage_run_id=other_stage["id"],
    )
    other_assumption = store.create_question_or_assumption(
        workflow["id"],
        record_type="assumption",
        summary="Wrong stage assumption.",
        stage_run_id=other_stage["id"],
    )

    for payload, expected_fragment in (
        ({"produced_artifact_ids": [other_artifact["id"]]}, "artifact"),
        ({"blocker_ids": [other_blocker["id"]]}, "blocker"),
        ({"question_ids": [other_question["id"]]}, "question"),
        ({"assumption_ids": [other_assumption["id"]]}, "assumption"),
    ):
        try:
            store.ingest_execution_bundle(
                packet["packet_id"],
                produced_artifact_ids=payload.get("produced_artifact_ids", [valid_artifact["id"]]),
                diff_refs=[],
                commands_run=[],
                test_results=[],
                blocker_ids=payload.get("blocker_ids"),
                question_ids=payload.get("question_ids"),
                assumption_ids=payload.get("assumption_ids"),
                self_report_summary="Cross-stage records should fail.",
                open_risks=[],
                evidence_receipts=[{"kind": "manual_review", "status": "captured"}],
            )
        except ValueError as exc:
            assert expected_fragment in str(exc)
            assert "stage_run_id" in str(exc)
        else:
            raise AssertionError(f"Expected ingest_execution_bundle to reject cross-stage {expected_fragment}.")


def test_store_rejects_packet_when_stage_run_context_is_inconsistent(tmp_path):
    repo_root = _prepare_repo(tmp_path)
    store = SessionStore(repo_root)
    workflow_a = store.create_workflow_run(
        "aioffice",
        task_id="AIO-024",
        objective="Workflow A",
        authoritative_workspace_root="projects/aioffice",
        current_stage="architect",
    )
    workflow_b = store.create_workflow_run(
        "aioffice",
        task_id="AIO-024",
        objective="Workflow B",
        authoritative_workspace_root="projects/aioffice",
        current_stage="architect",
    )
    stage_a = store.create_stage_run(workflow_a["id"], stage_name="architect", status="in_progress")

    try:
        store.issue_control_execution_packet(
            "aioffice",
            "AIO-024",
            objective="This packet mixes workflow and stage context.",
            authoritative_workspace_root="projects/aioffice",
            allowed_write_paths=["sessions/store.py"],
            required_artifact_outputs=["sessions/store.py"],
            required_validations=["pytest tests/test_control_kernel_store.py"],
            expected_return_bundle_contents=["produced artifacts"],
            failure_reporting_expectations=["report blockers"],
            workflow_run_id=workflow_b["id"],
            stage_run_id=stage_a["id"],
        )
    except ValueError as exc:
        assert "stage_run_id" in str(exc) or "stage_run workflow" in str(exc)
    else:
        raise AssertionError("Expected issue_control_execution_packet to reject inconsistent stage_run/workflow_run context.")


def test_store_can_execute_controlled_apply_promotion_with_explicit_approved_decision(tmp_path):
    context = _prepare_pending_review_apply_bundle(tmp_path)
    repo_root = context["repo_root"]
    store = context["store"]
    artifact = context["artifact"]
    bundle = context["bundle"]
    destination_path = "projects/aioffice/execution/approved/architecture_decision_v1.md"
    destination_file = repo_root / "projects" / "aioffice" / "execution" / "approved" / "architecture_decision_v1.md"

    updated_bundle = store.execute_apply_promotion_decision(
        bundle["bundle_id"],
        approved_decision={
            "decision": "approved",
            "action": "promote",
            "approved_by": "Project Orchestrator",
            "decision_note": "Approved bounded promotion into the authoritative workspace.",
        },
        destination_mappings=[
            {
                "source_artifact_id": artifact["id"],
                "destination_path": destination_path,
            }
        ],
    )

    assert bundle["acceptance_state"] == "pending_review"
    assert updated_bundle["acceptance_state"] == "promoted"
    assert destination_file.read_text(encoding="utf-8") == context["source_artifact_file"].read_text(encoding="utf-8")
    assert len(updated_bundle["evidence_receipts"]) == len(bundle["evidence_receipts"]) + 2
    assert updated_bundle["evidence_receipts"][-2]["kind"] == "apply_promotion_decision"
    assert updated_bundle["evidence_receipts"][-2]["action"] == "promote"
    assert updated_bundle["evidence_receipts"][-1]["kind"] == "authoritative_destination_write"
    assert updated_bundle["evidence_receipts"][-1]["source_artifact_id"] == artifact["id"]
    assert updated_bundle["evidence_receipts"][-1]["destination_path"] == destination_path


def test_store_rejects_apply_promotion_without_explicit_approved_decision(tmp_path):
    context = _prepare_pending_review_apply_bundle(tmp_path)
    repo_root = context["repo_root"]
    store = context["store"]
    artifact = context["artifact"]
    bundle = context["bundle"]
    destination_file = repo_root / "projects" / "aioffice" / "execution" / "approved" / "architecture_decision_v1.md"

    try:
        store.execute_apply_promotion_decision(
            bundle["bundle_id"],
            approved_decision={
                "decision": "pending",
                "action": "promote",
                "approved_by": "Project Orchestrator",
            },
            destination_mappings=[
                {
                    "source_artifact_id": artifact["id"],
                    "destination_path": "projects/aioffice/execution/approved/architecture_decision_v1.md",
                }
            ],
        )
    except ValueError as exc:
        assert "explicit approved decision" in str(exc)
    else:
        raise AssertionError("Expected apply/promotion to reject non-approved decision input.")

    assert store.get_execution_bundle(bundle["bundle_id"])["acceptance_state"] == "pending_review"
    assert not destination_file.exists()


def test_store_rejects_apply_promotion_destination_outside_authoritative_workspace(tmp_path):
    context = _prepare_pending_review_apply_bundle(tmp_path)
    repo_root = context["repo_root"]
    store = context["store"]
    artifact = context["artifact"]
    bundle = context["bundle"]
    destination_file = repo_root / "sessions" / "not_allowed.md"

    try:
        store.execute_apply_promotion_decision(
            bundle["bundle_id"],
            approved_decision={
                "decision": "approved",
                "action": "apply",
                "approved_by": "Project Orchestrator",
            },
            destination_mappings=[
                {
                    "source_artifact_id": artifact["id"],
                    "destination_path": "sessions/not_allowed.md",
                }
            ],
        )
    except ValueError as exc:
        assert "authoritative_workspace_root" in str(exc)
    else:
        raise AssertionError("Expected apply/promotion to reject destinations outside the authoritative workspace root.")

    assert store.get_execution_bundle(bundle["bundle_id"])["acceptance_state"] == "pending_review"
    assert not destination_file.exists()


def test_store_rejects_apply_promotion_into_governance_or_forbidden_paths(tmp_path):
    context = _prepare_pending_review_apply_bundle(tmp_path)
    repo_root = context["repo_root"]
    store = context["store"]
    artifact = context["artifact"]
    bundle = context["bundle"]

    for destination_path, expected_fragment in (
        ("projects/aioffice/governance/approved_decision.md", "governance"),
        ("projects/aioffice/execution/protected/restricted.md", "packet-forbidden"),
    ):
        try:
            store.execute_apply_promotion_decision(
                bundle["bundle_id"],
                approved_decision={
                    "decision": "approved",
                    "action": "apply",
                    "approved_by": "Project Orchestrator",
                },
                destination_mappings=[
                    {
                        "source_artifact_id": artifact["id"],
                        "destination_path": destination_path,
                    }
                ],
            )
        except ValueError as exc:
            assert expected_fragment in str(exc)
        else:
            raise AssertionError("Expected apply/promotion to reject governance-controlled destination paths.")
        assert not (repo_root / destination_path).exists()

    assert store.get_execution_bundle(bundle["bundle_id"])["acceptance_state"] == "pending_review"


def test_store_rejects_apply_promotion_into_accepted_truth_surface(tmp_path):
    context = _prepare_pending_review_apply_bundle(tmp_path)
    repo_root = context["repo_root"]
    store = context["store"]
    artifact = context["artifact"]
    bundle = context["bundle"]
    destination_path = "projects/aioffice/execution/KANBAN.md"
    destination_file = repo_root / "projects" / "aioffice" / "execution" / "KANBAN.md"
    destination_file.parent.mkdir(parents=True, exist_ok=True)
    destination_file.write_text("# Accepted Truth\n\nDo not overwrite.\n", encoding="utf-8")
    before_text = destination_file.read_text(encoding="utf-8")

    try:
        store.execute_apply_promotion_decision(
            bundle["bundle_id"],
            approved_decision={
                "decision": "approved",
                "action": "apply",
                "approved_by": "Project Orchestrator",
            },
            destination_mappings=[
                {
                    "source_artifact_id": artifact["id"],
                    "destination_path": destination_path,
                }
            ],
        )
    except ValueError as exc:
        assert "accepted truth surface" in str(exc)
        assert "fail closed" in str(exc)
    else:
        raise AssertionError("Expected apply/promotion to reject accepted truth surface destinations.")

    assert store.get_execution_bundle(bundle["bundle_id"])["acceptance_state"] == "pending_review"
    assert destination_file.read_text(encoding="utf-8") == before_text


def test_store_rejects_apply_promotion_into_protected_control_path_code_surface(tmp_path):
    context = _prepare_pending_review_apply_bundle(tmp_path)
    repo_root = context["repo_root"]
    store = context["store"]
    artifact = context["artifact"]
    bundle = context["bundle"]
    destination_path = "sessions/store.py"
    destination_file = repo_root / "sessions" / "store.py"
    destination_file.parent.mkdir(parents=True, exist_ok=True)
    destination_file.write_text("# protected control path\n", encoding="utf-8")
    before_text = destination_file.read_text(encoding="utf-8")

    try:
        store.execute_apply_promotion_decision(
            bundle["bundle_id"],
            approved_decision={
                "decision": "approved",
                "action": "apply",
                "approved_by": "Project Orchestrator",
            },
            destination_mappings=[
                {
                    "source_artifact_id": artifact["id"],
                    "destination_path": destination_path,
                }
            ],
        )
    except ValueError as exc:
        assert "protected control-path code surface" in str(exc)
        assert "fail closed" in str(exc)
    else:
        raise AssertionError("Expected apply/promotion to reject protected control-path code surface destinations.")

    assert store.get_execution_bundle(bundle["bundle_id"])["acceptance_state"] == "pending_review"
    assert destination_file.read_text(encoding="utf-8") == before_text


def test_store_rejects_apply_promotion_with_missing_or_ambiguous_destination_mappings(tmp_path):
    context = _prepare_pending_review_apply_bundle(tmp_path)
    store = context["store"]
    artifact = context["artifact"]
    bundle = context["bundle"]

    for destination_mappings, expected_fragment in (
        ([], "destination_mappings"),
        (
            [
                {
                    "source_artifact_id": artifact["id"],
                    "destination_path": "projects/aioffice/execution/approved/architecture_decision_v1.md",
                },
                {
                    "source_artifact_id": artifact["id"],
                    "destination_path": "projects/aioffice/execution/approved/architecture_decision_v2.md",
                },
            ],
            "duplicate source_artifact_id",
        ),
    ):
        try:
            store.execute_apply_promotion_decision(
                bundle["bundle_id"],
                approved_decision={
                    "decision": "approved",
                    "action": "promote",
                    "approved_by": "Project Orchestrator",
                },
                destination_mappings=destination_mappings,
            )
        except ValueError as exc:
            assert expected_fragment in str(exc)
        else:
            raise AssertionError("Expected apply/promotion to reject missing or ambiguous destination mappings.")

    assert store.get_execution_bundle(bundle["bundle_id"])["acceptance_state"] == "pending_review"


def test_store_rejects_apply_promotion_self_promotion_paths(tmp_path):
    context = _prepare_pending_review_apply_bundle(tmp_path)
    store = context["store"]
    artifact = context["artifact"]
    bundle = context["bundle"]

    try:
        store.execute_apply_promotion_decision(
            bundle["bundle_id"],
            approved_decision={
                "decision": "approved",
                "action": "promote",
                "approved_by": "Project Orchestrator",
            },
            destination_mappings=[
                {
                    "source_artifact_id": artifact["id"],
                    "destination_path": context["source_artifact_path"],
                }
            ],
        )
    except ValueError as exc:
        assert "source artifact path" in str(exc)
    else:
        raise AssertionError("Expected apply/promotion to reject self-promotion destination paths.")

    assert store.get_execution_bundle(bundle["bundle_id"])["acceptance_state"] == "pending_review"
