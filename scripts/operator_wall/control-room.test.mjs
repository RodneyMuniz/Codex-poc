import test from "node:test";
import assert from "node:assert/strict";

import {
  compareLoadedRunToRecentWindow,
  deriveInitialStickyControlRoomState,
  defaultSelectedGroupId,
  fetchRunDetails,
  fetchRecentRuns,
  filterAttemptsForGroup,
  filterEventsForAttempt,
  handleRecentRunSelection,
  normalizeStickyControlRoomContext,
  prioritizeAttentionEntries,
  readStickyControlRoomContext,
  renderControlRoom,
  renderRecentActivity,
  renderRunComparison,
  renderRecentRunsRail,
  renderSystemHealth,
  summarizeRecentActivity,
  summarizeSystemHealth,
  renderViewStatusStrip,
  resolveStickySelections,
  writeStickyControlRoomContext,
} from "./control-room.js";

const sampleRunDetails = {
  run: {
    id: "run_test123",
    status: "failed",
    task_id: "PK-001",
    project_name: "program-kanban",
    stop_reason: "retry_limit_exceeded",
  },
  task: {
    id: "PK-001",
    title: "Governed external execution",
    project_name: "program-kanban",
  },
  governed_external_run_summary: {
    total_execution_groups: 2,
    total_attempts: 3,
    governed_api_execution_count: 2,
    blocked_execution_count: 0,
    pre_observation_block_count: 0,
    final_success_count: 1,
    final_failed_count: 0,
    final_stopped_count: 0,
    final_budget_stopped_count: 1,
    final_proof_missing_count: 1,
    final_proved_count: 1,
    final_trusted_reconciled_count: 0,
    final_proof_captured_not_reconciled_count: 1,
    final_reconciliation_failed_count: 0,
    final_claim_missing_count: 0,
    final_claimed_only_count: 1,
  },
  governed_external_attention_items: [
    {
      execution_group_id: "execution_group_alpha",
      final_external_call_id: "external_call_002",
      final_attempt_number: 2,
      execution_path_classification: "governed_api_executed",
      final_outcome_status: "failed",
      final_budget_stop_enforced: true,
      final_budget_stop_reason_code: "retry_limit_exceeded",
      final_proof_status: "missing",
      final_reconciliation_state: "not_reconciled",
      final_trust_status: "claimed_only",
      attention_reason: "retry_limit_exceeded",
    },
  ],
  governed_pre_execution_blocks: [],
  governed_external_execution_groups: [
    {
      execution_group_id: "execution_group_alpha",
      total_attempts: 2,
      execution_path_classification: "governed_api_executed",
      final_attempt_number: 2,
      final_outcome_status: "failed",
      final_budget_stop_enforced: true,
      final_budget_stop_reason_code: "retry_limit_exceeded",
      final_proof_status: "missing",
      final_reconciliation_state: "not_reconciled",
      final_trust_status: "claimed_only",
      final_external_call_id: "external_call_002",
    },
    {
      execution_group_id: "execution_group_beta",
      total_attempts: 1,
      execution_path_classification: "governed_api_executed",
      final_attempt_number: 1,
      final_outcome_status: "completed",
      final_budget_stop_enforced: false,
      final_budget_stop_reason_code: null,
      final_proof_status: "proved",
      final_reconciliation_state: "not_reconciled",
      final_trust_status: "proof_captured_not_reconciled",
      final_external_call_id: "external_call_003",
    },
  ],
  governed_external_calls: [
    {
      execution_group_id: "execution_group_alpha",
      attempt_number: 1,
      external_call_id: "external_call_001",
      execution_path_classification: "governed_api_executed",
      claim_status: "claimed",
      outcome_status: "retrying",
      budget_stop_reason_code: null,
      proof_status: "missing",
      reconciliation_state: "not_reconciled",
      trust_status: "claimed_only",
      provider_request_id: null,
    },
    {
      execution_group_id: "execution_group_alpha",
      attempt_number: 2,
      external_call_id: "external_call_002",
      execution_path_classification: "governed_api_executed",
      claim_status: "claimed",
      outcome_status: "failed",
      budget_stop_reason_code: "retry_limit_exceeded",
      proof_status: "missing",
      reconciliation_state: "not_reconciled",
      trust_status: "claimed_only",
      provider_request_id: null,
    },
    {
      execution_group_id: "execution_group_beta",
      attempt_number: 1,
      external_call_id: "external_call_003",
      execution_path_classification: "governed_api_executed",
      claim_status: "claimed",
      outcome_status: "completed",
      budget_stop_reason_code: null,
      proof_status: "proved",
      reconciliation_state: "not_reconciled",
      trust_status: "proof_captured_not_reconciled",
      provider_request_id: "resp_beta",
    },
  ],
  governed_external_call_events: [
    {
      external_call_id: "external_call_001",
      event_type: "execution.wrapper_invoked",
      occurred_at: "2026-04-12T10:00:00+00:00",
      status: "invoked",
      reason_code: "governed_api_wrapper_invoked",
    },
    {
      external_call_id: "external_call_002",
      event_type: "budget.stop_enforced",
      occurred_at: "2026-04-12T10:00:03+00:00",
      status: "stopped",
      reason_code: "retry_limit_exceeded",
    },
    {
      external_call_id: "external_call_002",
      event_type: "external_call.proof_missing",
      occurred_at: "2026-04-12T10:00:04+00:00",
      status: "missing",
      reason_code: "provider_metadata_unavailable",
    },
    {
      external_call_id: "external_call_003",
      event_type: "external_call.provider_metadata_captured",
      occurred_at: "2026-04-12T10:00:05+00:00",
      status: "captured",
      reason_code: "provider_request_id_captured",
    },
  ],
};

test("fetchRunDetails uses the GET run-details path without mutation semantics", async () => {
  const calls = [];
  const payload = await fetchRunDetails("run_test123", async (url, options) => {
    calls.push({ url, options });
    return {
      ok: true,
      json: async () => sampleRunDetails,
    };
  });

  assert.deepEqual(payload, sampleRunDetails);
  assert.equal(calls[0].url, "/api/run-details?run_id=run_test123");
  assert.deepEqual(calls[0].options, { cache: "no-store" });
});

test("fetchRecentRuns uses the existing read-only snapshot path", async () => {
  const calls = [];
  const runs = await fetchRecentRuns(async (url, options) => {
    calls.push({ url, options });
    return {
      ok: true,
      json: async () => ({
        recent_runs: [
          {
            id: "run_test123",
            status: "failed",
            updated_at: "2026-04-12T10:00:00+00:00",
            task_title: "Governed external execution",
            governed_external_run_summary: {
              governed_api_execution_count: 1,
              final_failed_count: 1,
              final_budget_stopped_count: 1,
              final_proof_missing_count: 1,
              final_success_count: 0,
              blocked_execution_count: 0,
              pre_observation_block_count: 0,
              total_execution_groups: 1,
              total_attempts: 2,
            },
          },
        ],
      }),
    };
  });

  assert.deepEqual(runs, [
    {
      id: "run_test123",
      status: "failed",
      timestamp: "2026-04-12T10:00:00+00:00",
      taskTitle: "Governed external execution",
      stopReason: "",
      totalExecutionGroups: 1,
      totalAttempts: 2,
      governedApiExecutionCount: 1,
      blockedExecutionCount: 0,
      preObservationBlockCount: 0,
      finalSuccessCount: 0,
      finalFailedCount: 1,
      finalBudgetStoppedCount: 1,
      finalProofMissingCount: 1,
    },
  ]);
  assert.equal(calls[0].url, "/api/snapshot?project=all");
  assert.deepEqual(calls[0].options, { cache: "no-store" });
});

test("handleRecentRunSelection loads the chosen recent run without mutation semantics", async () => {
  const calls = [];
  const loaded = await handleRecentRunSelection("run_test123", async (runId, options) => {
    calls.push({ runId, options });
  });

  assert.equal(loaded, true);
  assert.deepEqual(calls, [
    {
      runId: "run_test123",
      options: { preserveSelection: false },
    },
  ]);
});

test("deriveInitialStickyControlRoomState restores the last saved run context when no query run is present", () => {
  const state = deriveInitialStickyControlRoomState("", {
    runId: "run_test123",
    selectedGroupId: "execution_group_alpha",
    selectedAttemptId: "external_call_002",
  });

  assert.deepEqual(state, {
    runId: "run_test123",
    selectedGroupId: "execution_group_alpha",
    selectedAttemptId: "external_call_002",
  });
});

test("deriveInitialStickyControlRoomState prefers an explicit query run and drops stale saved selections", () => {
  const state = deriveInitialStickyControlRoomState("run_override", {
    runId: "run_test123",
    selectedGroupId: "execution_group_alpha",
    selectedAttemptId: "external_call_002",
  });

  assert.deepEqual(state, {
    runId: "run_override",
    selectedGroupId: null,
    selectedAttemptId: null,
  });
});

test("sticky control-room context round-trips through local storage safely", () => {
  const storageState = new Map();
  const storage = {
    getItem(key) {
      return storageState.has(key) ? storageState.get(key) : null;
    },
    setItem(key, value) {
      storageState.set(key, value);
    },
    removeItem(key) {
      storageState.delete(key);
    },
  };

  const normalized = normalizeStickyControlRoomContext({
    runId: "  run_test123  ",
    selectedGroupId: " execution_group_alpha ",
    selectedAttemptId: " external_call_002 ",
  });
  assert.deepEqual(normalized, {
    runId: "run_test123",
    selectedGroupId: "execution_group_alpha",
    selectedAttemptId: "external_call_002",
  });

  assert.equal(writeStickyControlRoomContext(normalized, storage), true);
  assert.deepEqual(readStickyControlRoomContext(storage), normalized);

  assert.equal(
    writeStickyControlRoomContext({ runId: "", selectedGroupId: null, selectedAttemptId: null }, storage),
    true,
  );
  assert.deepEqual(readStickyControlRoomContext(storage), {
    runId: "",
    selectedGroupId: null,
    selectedAttemptId: null,
  });
});

test("resolveStickySelections restores the saved attempt and its owning execution group when both remain valid", () => {
  const resolved = resolveStickySelections(
    sampleRunDetails,
    "execution_group_alpha",
    "external_call_002",
  );

  assert.deepEqual(resolved, {
    selectedGroupId: "execution_group_alpha",
    selectedAttemptId: "external_call_002",
  });
});

test("resolveStickySelections falls back cleanly when saved group or attempt context is stale", () => {
  const resolved = resolveStickySelections(
    sampleRunDetails,
    "execution_group_missing",
    "external_call_missing",
  );

  assert.deepEqual(resolved, {
    selectedGroupId: "execution_group_alpha",
    selectedAttemptId: null,
  });
});

test("renderViewStatusStrip shows loaded and empty read-only status states", () => {
  const loadedHtml = renderViewStatusStrip("loaded", "run_test123");
  const emptyHtml = renderViewStatusStrip("empty", "");

  assert.match(loadedHtml, /Control Room/);
  assert.match(loadedHtml, /Governed external evidence/);
  assert.match(loadedHtml, /Loaded/);
  assert.match(loadedHtml, /Run run_test123/);
  assert.match(loadedHtml, /Read-only governed evidence is loaded for this run\./);
  assert.match(emptyHtml, /No run loaded/);
  assert.match(emptyHtml, /Run not selected/);
  assert.match(emptyHtml, /Enter a run id to inspect the control room\./);
  assert.doesNotMatch(loadedHtml, /Approve|Reject|Dispatch run|Retry run/i);
  assert.doesNotMatch(emptyHtml, /Approve|Reject|Dispatch run|Retry run/i);
});

test("renderRecentRunsRail renders compact recent-run navigation without mutation controls", () => {
  const html = renderRecentRunsRail(
    [
      {
        id: "run_test123",
        status: "failed",
        timestamp: "2026-04-12T10:00:00+00:00",
        taskTitle: "Governed external execution",
        stopReason: "",
        totalExecutionGroups: 1,
        totalAttempts: 2,
        governedApiExecutionCount: 1,
        blockedExecutionCount: 0,
        preObservationBlockCount: 0,
        finalSuccessCount: 0,
        finalFailedCount: 1,
        finalBudgetStoppedCount: 1,
        finalProofMissingCount: 1,
      },
      {
        id: "run_test999",
        status: "completed",
        timestamp: "2026-04-12T09:30:00+00:00",
        taskTitle: "Another governed run",
        stopReason: "",
        totalExecutionGroups: 1,
        totalAttempts: 1,
        governedApiExecutionCount: 1,
        blockedExecutionCount: 0,
        preObservationBlockCount: 0,
        finalSuccessCount: 1,
        finalFailedCount: 0,
        finalBudgetStoppedCount: 0,
        finalProofMissingCount: 0,
      },
    ],
    "run_test123",
    "loaded",
  );

  assert.match(html, /Recent Runs/);
  assert.match(html, /Pick a recent run to load it into the control room/);
  assert.match(html, /data-recent-run-id="run_test123"/);
  assert.match(html, /recent-run-chip--active/);
  assert.match(html, /failed \| 2026-04-12T10:00:00\+00:00/);
  assert.match(html, /Another governed run/);
  assert.doesNotMatch(html, /Delete run|Retry run|Dispatch run|Approve|Reject/i);
});

test("summarizeRecentActivity derives compact recent-run signals conservatively", () => {
  const summary = summarizeRecentActivity([
    {
      id: "run_a",
      status: "failed",
      stopReason: "retry_limit_exceeded",
      governedApiExecutionCount: 1,
      blockedExecutionCount: 0,
      preObservationBlockCount: 0,
      finalSuccessCount: 0,
      finalFailedCount: 1,
      finalBudgetStoppedCount: 1,
      finalProofMissingCount: 1,
    },
    {
      id: "run_b",
      status: "completed",
      stopReason: "",
      governedApiExecutionCount: 1,
      blockedExecutionCount: 0,
      preObservationBlockCount: 0,
      finalSuccessCount: 1,
      finalFailedCount: 0,
      finalBudgetStoppedCount: 0,
      finalProofMissingCount: 0,
    },
    {
      id: "run_c",
      status: "failed",
      stopReason: "",
      governedApiExecutionCount: 0,
      blockedExecutionCount: 1,
      preObservationBlockCount: 1,
      finalSuccessCount: 0,
      finalFailedCount: 1,
      finalBudgetStoppedCount: 0,
      finalProofMissingCount: 0,
    },
  ]);

  assert.deepEqual(summary, {
    totalRuns: 3,
    runsWithFailures: 2,
    runsWithBudgetStops: 1,
    runsWithProofMissing: 1,
    runsWithGovernedApiExecution: 2,
    runsWithPreExecutionBlocks: 1,
    successfulRuns: 1,
    hints: [
      "More failures than successful runs",
    ],
  });
});

test("renderRecentActivity shows lightweight trend signals without mutation controls", () => {
  const html = renderRecentActivity(
    {
      totalRuns: 3,
      runsWithFailures: 2,
      runsWithBudgetStops: 1,
      runsWithProofMissing: 1,
      runsWithGovernedApiExecution: 2,
      runsWithPreExecutionBlocks: 1,
      successfulRuns: 1,
      hints: ["More failures than successful runs"],
    },
    "loaded",
  );

  assert.match(html, /Recent Activity/);
  assert.match(html, /Runs in window/);
  assert.match(html, /Runs with failures/);
  assert.match(html, /Budget-stopped runs/);
  assert.match(html, /Proof-missing runs/);
  assert.match(html, /Governed API runs/);
  assert.match(html, /More failures than successful runs/);
  assert.doesNotMatch(html, /Delete run|Retry run|Dispatch run|Approve|Reject/i);
});

test("summarizeSystemHealth classifies a clean recent window as healthy", () => {
  const health = summarizeSystemHealth({
    totalRuns: 3,
    runsWithFailures: 0,
    runsWithBudgetStops: 0,
    runsWithProofMissing: 0,
    runsWithGovernedApiExecution: 3,
    runsWithPreExecutionBlocks: 0,
    successfulRuns: 3,
  });

  assert.deepEqual(health, {
    label: "Healthy",
    tone: "healthy",
    explanation: "Most recent runs completed successfully with minimal issues.",
  });
});

test("summarizeSystemHealth classifies repeated failures and blocks as at risk", () => {
  const health = summarizeSystemHealth({
    totalRuns: 4,
    runsWithFailures: 3,
    runsWithBudgetStops: 1,
    runsWithProofMissing: 1,
    runsWithGovernedApiExecution: 1,
    runsWithPreExecutionBlocks: 2,
    successfulRuns: 1,
  });

  assert.deepEqual(health, {
    label: "At Risk",
    tone: "risk",
    explanation: "Frequent pre-execution blocks are showing up in the recent run window.",
  });
});

test("renderSystemHealth shows health label and explanation without mutation controls", () => {
  const html = renderSystemHealth({
    totalRuns: 3,
    runsWithFailures: 1,
    runsWithBudgetStops: 1,
    runsWithProofMissing: 0,
    runsWithGovernedApiExecution: 3,
    runsWithPreExecutionBlocks: 0,
    successfulRuns: 2,
  }, "loaded");

  assert.match(html, /System Health/);
  assert.match(html, /Degraded/);
  assert.match(html, /Recent runs show budget-stop pressure even though the system is still moving\./);
  assert.doesNotMatch(html, /Delete run|Retry run|Dispatch run|Approve|Reject/i);
});

test("compareLoadedRunToRecentWindow shows cleaner-than-most context conservatively", () => {
  const comparison = compareLoadedRunToRecentWindow(
    {
      ...sampleRunDetails,
      run: { ...sampleRunDetails.run, id: "run_clean", status: "completed", stop_reason: null },
      governed_external_run_summary: {
        total_execution_groups: 1,
        total_attempts: 1,
        governed_api_execution_count: 1,
        blocked_execution_count: 0,
        pre_observation_block_count: 0,
        final_success_count: 1,
        final_failed_count: 0,
        final_stopped_count: 0,
        final_budget_stopped_count: 0,
        final_proof_missing_count: 0,
        final_proved_count: 1,
      },
    },
    [
      {
        id: "run_peer_1",
        status: "failed",
        stopReason: "retry_limit_exceeded",
        governedApiExecutionCount: 1,
        blockedExecutionCount: 0,
        preObservationBlockCount: 0,
        finalSuccessCount: 0,
        finalFailedCount: 1,
        finalBudgetStoppedCount: 1,
        finalProofMissingCount: 1,
      },
      {
        id: "run_peer_2",
        status: "failed",
        stopReason: "",
        governedApiExecutionCount: 0,
        blockedExecutionCount: 1,
        preObservationBlockCount: 1,
        finalSuccessCount: 0,
        finalFailedCount: 1,
        finalBudgetStoppedCount: 0,
        finalProofMissingCount: 0,
      },
    ],
  );

  assert.deepEqual(comparison, {
    headline: "This run looks cleaner than most recent runs.",
    cues: [],
  });
});

test("renderRunComparison highlights uncommon pre-execution blocks without mutation controls", () => {
  const html = renderRunComparison(
    {
      ...sampleRunDetails,
      run: { ...sampleRunDetails.run, id: "run_blocked" },
      governed_external_run_summary: {
        total_execution_groups: 1,
        total_attempts: 1,
        governed_api_execution_count: 0,
        blocked_execution_count: 1,
        pre_observation_block_count: 1,
        final_success_count: 0,
        final_failed_count: 1,
        final_stopped_count: 0,
        final_budget_stopped_count: 0,
        final_proof_missing_count: 0,
        final_proved_count: 0,
      },
    },
    [
      {
        id: "run_peer_1",
        status: "completed",
        stopReason: "",
        governedApiExecutionCount: 1,
        blockedExecutionCount: 0,
        preObservationBlockCount: 0,
        finalSuccessCount: 1,
        finalFailedCount: 0,
        finalBudgetStoppedCount: 0,
        finalProofMissingCount: 0,
      },
      {
        id: "run_peer_2",
        status: "completed",
        stopReason: "",
        governedApiExecutionCount: 1,
        blockedExecutionCount: 0,
        preObservationBlockCount: 0,
        finalSuccessCount: 1,
        finalFailedCount: 0,
        finalBudgetStoppedCount: 0,
        finalProofMissingCount: 0,
      },
    ],
  );

  assert.match(html, /Run Context/);
  assert.match(html, /This run has more attention signals than most recent runs\./);
  assert.match(html, /This run includes a pre-execution block, which is uncommon in the recent window\./);
  assert.doesNotMatch(html, /Delete run|Retry run|Dispatch run|Approve|Reject/i);
});

test("prioritizeAttentionEntries orders attention deterministically by operator priority", () => {
  const entries = prioritizeAttentionEntries(
    [
      {
        execution_group_id: "proof_group",
        execution_path_classification: "governed_api_executed",
        final_outcome_status: "completed",
        final_budget_stop_reason_code: null,
        final_proof_status: "missing",
      },
      {
        execution_group_id: "budget_group",
        execution_path_classification: "governed_api_executed",
        final_outcome_status: "failed",
        final_budget_stop_reason_code: "total_budget_exceeded",
        final_proof_status: "missing",
      },
      {
        execution_group_id: "failure_group",
        execution_path_classification: "governed_api_executed",
        final_outcome_status: "failed",
        final_budget_stop_reason_code: null,
        final_proof_status: "missing",
      },
      {
        execution_group_id: "other_group",
        execution_path_classification: "blocked_pre_execution",
        final_outcome_status: "failed",
        final_budget_stop_reason_code: null,
        final_proof_status: "missing",
      },
    ],
    [
      {
        block_stage: "wrapper_governance_precheck",
        block_reason_code: "role_state_blocked",
        occurred_at: "2026-04-12T10:00:00+00:00",
      },
    ],
  );

  assert.deepEqual(
    entries.map((entry) => ({
      kind: entry.kind,
      label: entry.priority.label,
      id: entry.kind === "pre_execution_block"
        ? entry.payload.block_reason_code
        : entry.payload.execution_group_id,
    })),
    [
      { kind: "pre_execution_block", label: "High", id: "role_state_blocked" },
      { kind: "attention_item", label: "High", id: "failure_group" },
      { kind: "attention_item", label: "Medium", id: "budget_group" },
      { kind: "attention_item", label: "Low", id: "proof_group" },
      { kind: "attention_item", label: "Low", id: "other_group" },
    ],
  );
});

test("renderControlRoom shows priority labels in triage order without mutation controls", () => {
  const prioritizedRunDetails = {
    ...sampleRunDetails,
    governed_external_attention_items: [
      {
        execution_group_id: "proof_group",
        final_external_call_id: "external_call_proof",
        final_attempt_number: 1,
        execution_path_classification: "governed_api_executed",
        final_outcome_status: "completed",
        final_budget_stop_enforced: false,
        final_budget_stop_reason_code: null,
        final_proof_status: "missing",
        attention_reason: "final_proof_missing",
      },
      {
        execution_group_id: "budget_group",
        final_external_call_id: "external_call_budget",
        final_attempt_number: 1,
        execution_path_classification: "governed_api_executed",
        final_outcome_status: "failed",
        final_budget_stop_enforced: true,
        final_budget_stop_reason_code: "retry_limit_exceeded",
        final_proof_status: "missing",
        attention_reason: "retry_limit_exceeded",
      },
      {
        execution_group_id: "failure_group",
        final_external_call_id: "external_call_failure",
        final_attempt_number: 1,
        execution_path_classification: "governed_api_executed",
        final_outcome_status: "failed",
        final_budget_stop_enforced: false,
        final_budget_stop_reason_code: null,
        final_proof_status: "missing",
        attention_reason: "final_failed",
      },
    ],
    governed_pre_execution_blocks: [
      {
        run_id: "run_test123",
        task_id: "PK-001",
        task_packet_id: "req_blocked",
        authority_packet_id: "PK-001",
        block_stage: "wrapper_governance_precheck",
        block_reason_code: "role_state_blocked",
        occurred_at: "2026-04-12T09:59:00+00:00",
      },
    ],
  };

  const html = renderControlRoom(prioritizedRunDetails, "failure_group");

  const preObservationIndex = html.indexOf("Pre-observation block");
  const failureIndex = html.indexOf("failure_group");
  const budgetIndex = html.indexOf("budget_group");
  const proofIndex = html.indexOf("proof_group");

  assert.ok(preObservationIndex >= 0);
  assert.ok(failureIndex > preObservationIndex);
  assert.ok(budgetIndex > failureIndex);
  assert.ok(proofIndex > budgetIndex);
  assert.match(html, /data-priority-label="High"/);
  assert.match(html, /data-priority-label="Medium"/);
  assert.match(html, /data-priority-label="Low"/);
  assert.match(html, /priority-pill priority-pill--high">High</);
  assert.match(html, /priority-pill priority-pill--medium">Medium</);
  assert.match(html, /priority-pill priority-pill--low">Low</);
  assert.doesNotMatch(html, /Approve|Reject|Dispatch run|Retry run/i);
});

test("renderControlRoom shows run comparison context for the loaded run without mutation controls", () => {
  const html = renderControlRoom(
    sampleRunDetails,
    "execution_group_alpha",
    null,
    [
      {
        id: "run_peer_1",
        status: "completed",
        timestamp: "2026-04-12T09:30:00+00:00",
        taskTitle: "Clean governed run",
        stopReason: "",
        totalExecutionGroups: 1,
        totalAttempts: 1,
        governedApiExecutionCount: 1,
        blockedExecutionCount: 0,
        preObservationBlockCount: 0,
        finalSuccessCount: 1,
        finalFailedCount: 0,
        finalBudgetStoppedCount: 0,
        finalProofMissingCount: 0,
      },
      {
        id: "run_peer_2",
        status: "completed",
        timestamp: "2026-04-12T09:00:00+00:00",
        taskTitle: "Another clean run",
        stopReason: "",
        totalExecutionGroups: 1,
        totalAttempts: 1,
        governedApiExecutionCount: 1,
        blockedExecutionCount: 0,
        preObservationBlockCount: 0,
        finalSuccessCount: 1,
        finalFailedCount: 0,
        finalBudgetStoppedCount: 0,
        finalProofMissingCount: 0,
      },
    ],
  );

  assert.match(html, /Run Context/);
  assert.match(html, /This run has more attention signals than most recent runs\./);
  assert.match(html, /This run hit a budget stop, which is less common in the recent window\./);
  assert.match(html, /This run has proof-missing outcomes, which are uncommon in the recent window\./);
  assert.doesNotMatch(html, /Approve|Reject|Dispatch run|Retry run/i);
});

test("renderControlRoom renders explainable summary KPIs, attention, and selected-group attempts without mutation controls", () => {
  assert.equal(defaultSelectedGroupId(sampleRunDetails), "execution_group_alpha");
  assert.equal(filterAttemptsForGroup(sampleRunDetails, "execution_group_alpha").length, 2);
  assert.equal(filterEventsForAttempt(sampleRunDetails, "external_call_002").length, 2);

  const html = renderControlRoom(sampleRunDetails, "execution_group_alpha");

  assert.match(html, /aria-label="Control room status"/);
  assert.match(html, /Governed external evidence/);
  assert.match(html, /Loaded/);
  assert.match(html, /Run run_test123/);
  assert.match(html, /Recent Runs/);
  assert.match(html, /Recent Activity/);
  assert.match(html, /id="run-id-input"/);
  assert.match(html, /Run Summary/);
  assert.match(html, /System Health/);
  assert.match(html, /Read-derived sensors from persisted governed execution evidence/);
  assert.match(html, /Execution groups/);
  assert.match(html, /API executed/);
  assert.match(html, /Blocked pre-exec/);
  assert.match(html, /Pre-observation blocks/);
  assert.match(html, /Budget stopped/);
  assert.match(html, /data-metric-key="total_execution_groups"/);
  assert.match(html, /aria-label="Explain Execution groups"/);
  assert.match(html, /Logical governed execution chains recorded for this run\./);
  assert.match(html, /data-metric-key="total_attempts"[\s\S]*?stat-card__value">3</);
  assert.match(html, /data-metric-key="governed_api_execution_count"/);
  assert.match(html, /data-metric-key="pre_observation_block_count"/);
  assert.match(html, /data-metric-key="final_proof_captured_not_reconciled_count"/);
  assert.match(html, /data-metric-key="final_claimed_only_count"/);
  assert.match(html, /data-metric-key="final_reconciliation_failed_count"/);
  assert.match(html, /It prevents blocked work from disappearing before the external observation stage\./);
  assert.match(html, /retry_limit_exceeded/);
  assert.match(html, /execution_group_alpha/);
  assert.match(html, /external_call_001/);
  assert.match(html, /external_call_002/);
  assert.match(html, /Governed API executed/);
  assert.match(html, /Execution stopped by retry limit/);
  assert.match(html, /Suggested next step:/);
  assert.match(html, /Review retry limits or task quality before retrying\./);
  assert.match(html, /Claimed only/);
  assert.match(html, /Proof captured, not reconciled/);
  assert.doesNotMatch(html, />Not reconciled</);
  assert.doesNotMatch(html, /Trusted \(reconciled\)|Verified/i);
  assert.doesNotMatch(html, /Attempt Event Evidence/);
  assert.doesNotMatch(html, /resp_beta/);
  assert.doesNotMatch(html, /Approve|Reject|Dispatch run|Retry run/i);
});

test("renderControlRoom shows only the selected attempt events in the secondary evidence section", () => {
  const html = renderControlRoom(sampleRunDetails, "execution_group_alpha", "external_call_002");

  assert.match(html, /Attempt Event Evidence/);
  assert.match(html, /budget\.stop_enforced/);
  assert.match(html, /external_call\.proof_missing/);
  assert.match(html, /retry_limit_exceeded/);
  assert.match(html, /provider_metadata_unavailable/);
  assert.doesNotMatch(html, /governed_api_wrapper_invoked/);
  assert.doesNotMatch(html, /provider_request_id_captured/);
  assert.doesNotMatch(html, /Approve|Reject|Dispatch run|Retry run/i);
});

test("renderControlRoom shows trusted reconciled attempts when backend trust confirms them", () => {
  const trustedRunDetails = {
    ...sampleRunDetails,
    governed_external_run_summary: {
      total_execution_groups: 1,
      total_attempts: 1,
      governed_api_execution_count: 1,
      blocked_execution_count: 0,
      pre_observation_block_count: 0,
      final_success_count: 1,
      final_failed_count: 0,
      final_stopped_count: 0,
      final_budget_stopped_count: 0,
      final_proof_missing_count: 0,
      final_proved_count: 1,
      final_trusted_reconciled_count: 1,
      final_proof_captured_not_reconciled_count: 0,
      final_reconciliation_failed_count: 0,
      final_claim_missing_count: 0,
      final_claimed_only_count: 0,
    },
    governed_external_attention_items: [],
    governed_pre_execution_blocks: [],
    governed_external_execution_groups: [
      {
        ...sampleRunDetails.governed_external_execution_groups[1],
        final_reconciliation_state: "reconciled",
        final_trust_status: "trusted_reconciled",
        final_reconciliation_checked_at: "2026-04-12T10:10:00+00:00",
      },
    ],
    governed_external_calls: [
      {
        ...sampleRunDetails.governed_external_calls[2],
        reconciliation_state: "reconciled",
        trust_status: "trusted_reconciled",
      },
    ],
    governed_external_call_events: [sampleRunDetails.governed_external_call_events[3]],
  };
  const html = renderControlRoom(trustedRunDetails, "execution_group_beta");

  assert.match(html, /execution_group_beta/);
  assert.match(html, /Governed API executed/);
  assert.match(html, /Trusted \(reconciled\)/);
  assert.match(html, /Reconciled/);
  assert.match(html, /data-metric-key="final_trusted_reconciled_count"[\s\S]*?stat-card__value">1</);
  assert.doesNotMatch(html, /Proof captured, not reconciled/);
  assert.doesNotMatch(html, /Not reconciled/);
  assert.doesNotMatch(html, /Approve|Reject|Dispatch run|Retry run/i);
});

test("renderControlRoom keeps reconciliation failure distinct from proof missing and claimed only", () => {
  const reconciliationFailedRunDetails = {
    ...sampleRunDetails,
    governed_external_run_summary: {
      total_execution_groups: 1,
      total_attempts: 1,
      governed_api_execution_count: 1,
      blocked_execution_count: 0,
      pre_observation_block_count: 0,
      final_success_count: 1,
      final_failed_count: 0,
      final_stopped_count: 0,
      final_budget_stopped_count: 0,
      final_proof_missing_count: 0,
      final_proved_count: 1,
      final_trusted_reconciled_count: 0,
      final_proof_captured_not_reconciled_count: 0,
      final_reconciliation_failed_count: 1,
      final_claim_missing_count: 0,
      final_claimed_only_count: 0,
    },
    governed_external_attention_items: [
      {
        execution_group_id: "execution_group_recon_failed",
        final_external_call_id: "external_call_recon_failed",
        final_attempt_number: 1,
        execution_path_classification: "governed_api_executed",
        final_outcome_status: "completed",
        final_budget_stop_enforced: false,
        final_budget_stop_reason_code: null,
        final_proof_status: "proved",
        final_reconciliation_state: "reconciliation_failed",
        final_trust_status: "reconciliation_failed",
        final_reconciliation_reason_code: "provider_record_not_found",
        attention_reason: "reconciliation_failed",
      },
    ],
    governed_pre_execution_blocks: [],
    governed_external_execution_groups: [
      {
        execution_group_id: "execution_group_recon_failed",
        total_attempts: 1,
        execution_path_classification: "governed_api_executed",
        final_attempt_number: 1,
        final_outcome_status: "completed",
        final_budget_stop_enforced: false,
        final_budget_stop_reason_code: null,
        final_proof_status: "proved",
        final_reconciliation_state: "reconciliation_failed",
        final_trust_status: "reconciliation_failed",
        final_reconciliation_reason_code: "provider_record_not_found",
        final_external_call_id: "external_call_recon_failed",
      },
    ],
    governed_external_calls: [
      {
        execution_group_id: "execution_group_recon_failed",
        attempt_number: 1,
        external_call_id: "external_call_recon_failed",
        execution_path_classification: "governed_api_executed",
        claim_status: "claimed",
        outcome_status: "completed",
        budget_stop_reason_code: null,
        proof_status: "proved",
        reconciliation_state: "reconciliation_failed",
        trust_status: "reconciliation_failed",
        provider_request_id: "resp_recon_failed",
      },
    ],
    governed_external_call_events: [],
  };

  const html = renderControlRoom(reconciliationFailedRunDetails, "execution_group_recon_failed");

  assert.match(html, /Reconciliation failed/);
  assert.match(html, /provider_record_not_found/);
  assert.match(html, /Inspect reconciliation evidence and the failure reason before treating this run as trusted\./);
  assert.match(html, /data-metric-key="final_reconciliation_failed_count"[\s\S]*?stat-card__value">1</);
  assert.match(html, /data-metric-key="final_proof_missing_count"[\s\S]*?stat-card__value">0</);
  assert.match(html, /data-metric-key="final_claimed_only_count"[\s\S]*?stat-card__value">0</);
  assert.doesNotMatch(html, /Approve|Reject|Dispatch run|Retry run/i);
});

test("renderControlRoom explains proof-missing attention items in operator language", () => {
  const proofMissingAttentionRunDetails = {
    ...sampleRunDetails,
    governed_external_run_summary: {
      total_execution_groups: 1,
      total_attempts: 1,
      governed_api_execution_count: 1,
      blocked_execution_count: 0,
      pre_observation_block_count: 0,
      final_success_count: 1,
      final_failed_count: 0,
      final_stopped_count: 0,
      final_budget_stopped_count: 0,
      final_proof_missing_count: 1,
      final_proved_count: 0,
    },
    governed_external_attention_items: [
      {
        execution_group_id: "execution_group_missing_proof",
        final_external_call_id: "external_call_missing_proof",
        final_attempt_number: 1,
        execution_path_classification: "governed_api_executed",
        final_outcome_status: "completed",
        final_budget_stop_enforced: false,
        final_budget_stop_reason_code: null,
        final_proof_status: "missing",
        attention_reason: "final_proof_missing",
      },
    ],
    governed_pre_execution_blocks: [],
    governed_external_execution_groups: [
      {
        execution_group_id: "execution_group_missing_proof",
        total_attempts: 1,
        execution_path_classification: "governed_api_executed",
        final_attempt_number: 1,
        final_outcome_status: "completed",
        final_budget_stop_enforced: false,
        final_budget_stop_reason_code: null,
        final_proof_status: "missing",
        final_external_call_id: "external_call_missing_proof",
      },
    ],
    governed_external_calls: [
      {
        execution_group_id: "execution_group_missing_proof",
        attempt_number: 1,
        external_call_id: "external_call_missing_proof",
        execution_path_classification: "governed_api_executed",
        claim_status: "claimed",
        outcome_status: "completed",
        budget_stop_reason_code: null,
        proof_status: "missing",
        provider_request_id: null,
      },
    ],
    governed_external_call_events: [],
  };

  const html = renderControlRoom(proofMissingAttentionRunDetails, "execution_group_missing_proof");

  assert.match(html, /Executed via governed API, but proof is still missing/);
  assert.match(html, /Suggested next step:/);
  assert.match(html, /Check provider proof capture and future reconciliation status\./);
  assert.match(html, /final_proof_missing/);
  assert.doesNotMatch(html, /Trusted \(reconciled\)|Verified/i);
  assert.doesNotMatch(html, /Approve|Reject|Dispatch run|Retry run/i);
});

test("renderControlRoom explains token budget stops with a grounded suggested next step", () => {
  const tokenBudgetRunDetails = {
    ...sampleRunDetails,
    governed_external_attention_items: [
      {
        execution_group_id: "execution_group_budget",
        final_external_call_id: "external_call_budget",
        final_attempt_number: 1,
        execution_path_classification: "governed_api_executed",
        final_outcome_status: "failed",
        final_budget_stop_enforced: true,
        final_budget_stop_reason_code: "total_budget_exceeded",
        final_proof_status: "missing",
        attention_reason: "total_budget_exceeded",
      },
    ],
    governed_external_execution_groups: [
      {
        execution_group_id: "execution_group_budget",
        total_attempts: 1,
        execution_path_classification: "governed_api_executed",
        final_attempt_number: 1,
        final_outcome_status: "failed",
        final_budget_stop_enforced: true,
        final_budget_stop_reason_code: "total_budget_exceeded",
        final_proof_status: "missing",
        final_external_call_id: "external_call_budget",
      },
    ],
    governed_external_calls: [
      {
        execution_group_id: "execution_group_budget",
        attempt_number: 1,
        external_call_id: "external_call_budget",
        execution_path_classification: "governed_api_executed",
        claim_status: "claimed",
        outcome_status: "failed",
        budget_stop_reason_code: "total_budget_exceeded",
        proof_status: "missing",
        providerRequestId: null,
      },
    ],
    governed_external_call_events: [],
  };

  const html = renderControlRoom(tokenBudgetRunDetails, "execution_group_budget");

  assert.match(html, /Execution stopped by token budget/);
  assert.match(html, /Suggested next step:/);
  assert.match(html, /Review token budget or reduce prompt size\./);
  assert.doesNotMatch(html, /Approve|Reject|Dispatch run|Retry run/i);
});

test("renderControlRoom shows blocked pre-execution groups without inventing alternative meaning", () => {
  const blockedRunDetails = {
    ...sampleRunDetails,
    governed_external_run_summary: {
      total_execution_groups: 1,
      total_attempts: 1,
      governed_api_execution_count: 0,
      blocked_execution_count: 1,
      pre_observation_block_count: 0,
      final_success_count: 0,
      final_failed_count: 1,
      final_stopped_count: 0,
      final_budget_stopped_count: 0,
      final_proof_missing_count: 1,
      final_proved_count: 0,
    },
    governed_external_attention_items: [
      {
        execution_group_id: "execution_group_blocked",
        final_external_call_id: "external_call_blocked",
        final_attempt_number: 1,
        execution_path_classification: "blocked_pre_execution",
        final_outcome_status: "failed",
        final_budget_stop_enforced: false,
        final_budget_stop_reason_code: null,
        final_proof_status: "missing",
        attention_reason: "final_failed",
      },
    ],
    governed_pre_execution_blocks: [],
    governed_external_execution_groups: [
      {
        execution_group_id: "execution_group_blocked",
        total_attempts: 1,
        execution_path_classification: "blocked_pre_execution",
        final_attempt_number: 1,
        final_outcome_status: "failed",
        final_budget_stop_enforced: false,
        final_budget_stop_reason_code: null,
        final_proof_status: "missing",
        final_external_call_id: "external_call_blocked",
      },
    ],
    governed_external_calls: [
      {
        execution_group_id: "execution_group_blocked",
        attempt_number: 1,
        external_call_id: "external_call_blocked",
        execution_path_classification: "blocked_pre_execution",
        claim_status: "claimed",
        outcome_status: "failed",
        budget_stop_reason_code: null,
        proof_status: "missing",
        provider_request_id: null,
      },
    ],
    governed_external_call_events: [
      {
        external_call_id: "external_call_blocked",
        event_type: "execution.wrapper_invoked",
        occurred_at: "2026-04-12T10:00:00+00:00",
        status: "invoked",
        reason_code: "governed_api_wrapper_invoked",
      },
      {
        external_call_id: "external_call_blocked",
        event_type: "external_call.proof_missing",
        occurred_at: "2026-04-12T10:00:01+00:00",
        status: "missing",
        reason_code: "provider_metadata_unavailable",
      },
    ],
  };

  const html = renderControlRoom(blockedRunDetails, "execution_group_blocked");

  assert.match(html, /Blocked pre-execution/);
  assert.match(html, /Blocked before API call/);
  assert.match(html, /Suggested next step:/);
  assert.match(html, /Inspect the block reason before retrying\./);
  assert.match(html, /final_failed/);
  assert.doesNotMatch(html, /Trusted \(reconciled\)|Verified/i);
  assert.doesNotMatch(html, /Approve|Reject|Dispatch run|Retry run/i);
});

test("renderControlRoom surfaces pre-observation blocks without fabricating external attempts", () => {
  const blockedBeforeObservationRunDetails = {
    ...sampleRunDetails,
    governed_external_run_summary: {
      total_execution_groups: 0,
      total_attempts: 0,
      governed_api_execution_count: 0,
      blocked_execution_count: 0,
      pre_observation_block_count: 1,
      final_success_count: 0,
      final_failed_count: 0,
      final_stopped_count: 0,
      final_budget_stopped_count: 0,
      final_proof_missing_count: 0,
      final_proved_count: 0,
    },
    governed_external_attention_items: [],
    governed_pre_execution_blocks: [
      {
        block_id: "preblock_001",
        occurred_at: "2026-04-12T10:00:00+00:00",
        run_id: "run_test123",
        task_id: "PK-001",
        task_packet_id: "req_test",
        authority_packet_id: "packet-1",
        block_stage: "wrapper_governance_precheck",
        block_reason_code: "role_state_blocked",
      },
    ],
    governed_external_execution_groups: [],
    governed_external_calls: [],
    governed_external_call_events: [],
  };

  const html = renderControlRoom(blockedBeforeObservationRunDetails);

  assert.match(html, /Pre-observation blocks/);
  assert.match(html, /Blocked before API call: task state not eligible/);
  assert.match(html, /Suggested next step:/);
  assert.match(html, /Move the task to an eligible state before retrying\./);
  assert.match(html, /role_state_blocked/);
  assert.match(html, /wrapper_governance_precheck/);
  assert.doesNotMatch(html, /external_call_001|external_call_002|external_call_003/);
  assert.doesNotMatch(html, /Approve|Reject|Dispatch run|Retry run/i);
});

