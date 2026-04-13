import test from "node:test";
import assert from "node:assert/strict";

import {
  filterBoardByMilestone,
  fetchRunDetails,
  fetchTaskDetails,
  renderIntegratedTaskDetail,
  renderOperatorWall,
  selectLinkedRunId,
  summarizeMilestones,
  summarizeTaskTrust,
} from "./app.js";

const sampleSnapshot = {
  project_name: "program-kanban",
  summary: {
    task_count: 12,
    run_count: 4,
    planning_warning_count: 1,
    pending_approvals: 0,
  },
  available_projects: [
    {
      name: "program-kanban",
      label: "Program Kanban",
    },
  ],
  board: [
    {
      key: "backlog",
      name: "Backlog",
      count: 1,
      cards: [
        {
          id: "PK-115",
          title: "AUDIT governed API truth check",
          objective: "Audit governed external API execution truth.",
          status: "backlog",
          milestone_id: "milestone_cd78dafc9f81",
          milestone_title: "M7 - Studio Foundations",
          linked_run_count: 1,
          latest_attention_summary: {
            attention_count: 0,
          },
          latest_execution_summary: {
            latest_execution_path_classification: "governed_api_executed",
            latest_outcome_status: "completed",
            latest_proof_status: "proved",
            latest_reconciliation_state: "not_reconciled",
            latest_trust_status: "proof_captured_not_reconciled",
          },
          trust_summary: {
            trust_followup_needed: true,
            trust_followup_count: 1,
            unreconciled_run_count: 1,
            reconciliation_failed_count: 0,
            reconciliation_pending_count: 0,
            proof_captured_not_reconciled_count: 1,
            latest_trust_status: "proof_captured_not_reconciled",
            latest_reconciliation_state: "not_reconciled",
            highest_priority_trust_issue: "proof_captured_not_reconciled",
            highest_priority_run_id: "run_cbfef7e75b58",
          },
        },
        {
          id: "PK-101",
          title: "Workspace recovery architecture",
          objective: "Define durable Git workspace recovery architecture.",
          status: "backlog",
          milestone_id: "milestone_other",
          milestone_title: "M8 - Recovery Hardening",
          linked_run_count: 0,
          latest_attention_summary: {
            attention_count: 1,
          },
          latest_execution_summary: {
            latest_execution_path_classification: "blocked_pre_execution",
            latest_outcome_status: "failed",
            latest_proof_status: "missing",
          },
          trust_summary: {
            trust_followup_needed: false,
            trust_followup_count: 0,
            unreconciled_run_count: 0,
            reconciliation_failed_count: 0,
            reconciliation_pending_count: 0,
            proof_captured_not_reconciled_count: 0,
            latest_trust_status: "",
            latest_reconciliation_state: "",
            highest_priority_trust_issue: "",
            highest_priority_run_id: "",
          },
        },
      ],
    },
  ],
  milestones: [
    {
      id: "milestone_cd78dafc9f81",
      title: "M7 - Studio Foundations",
      status: "complete",
      task_count: 1,
      trust_summary: {
        task_count: 1,
        tasks_with_trust_followup: 1,
        unreconciled_run_count: 1,
        reconciliation_failed_count: 0,
        reconciliation_pending_count: 0,
        proof_captured_not_reconciled_count: 1,
        trust_followup_needed: true,
        highest_priority_trust_issue: "proof_captured_not_reconciled",
        highest_priority_task_id: "PK-115",
        highest_priority_run_id: "run_cbfef7e75b58",
      },
      tasks: [{ id: "PK-115" }],
    },
    {
      id: "milestone_other",
      title: "M8 - Recovery Hardening",
      status: "in_progress",
      task_count: 1,
      trust_summary: {
        task_count: 1,
        tasks_with_trust_followup: 0,
        unreconciled_run_count: 0,
        reconciliation_failed_count: 0,
        reconciliation_pending_count: 0,
        proof_captured_not_reconciled_count: 0,
        trust_followup_needed: false,
        highest_priority_trust_issue: null,
        highest_priority_task_id: null,
        highest_priority_run_id: null,
      },
      tasks: [{ id: "PK-101" }],
    },
  ],
};

const sampleTaskDetails = {
  project: {
    id: "project_769a8ecf4455",
    name: "program-kanban",
  },
  milestone: {
    id: "milestone_cd78dafc9f81",
    title: "M7 - Studio Foundations",
  },
  task: {
    id: "PK-115",
    project_name: "program-kanban",
    title: "AUDIT governed API truth check",
    status: "backlog",
    objective: "Audit governed external API execution truth.",
  },
  linked_run_count: 1,
  linked_runs: [
    {
      id: "run_cbfef7e75b58",
      status: "running",
      started_at: "2026-04-12T01:49:04+00:00",
      attention_summary: {
        attention_count: 0,
      },
      health_summary: {
        final_success_count: 1,
      },
      execution_summary: {
        latest_execution_path_classification: "governed_api_executed",
        latest_outcome_status: "completed",
        latest_proof_status: "proved",
        latest_reconciliation_state: "not_reconciled",
        latest_trust_status: "proof_captured_not_reconciled",
      },
    },
  ],
  latest_attention_summary: {
    attention_count: 0,
    top_attention_reason: null,
  },
  latest_health_summary: {
    has_attention: false,
    final_success_count: 1,
    final_failed_count: 0,
    pre_observation_block_count: 0,
  },
  latest_execution_summary: {
    latest_execution_path_classification: "governed_api_executed",
    latest_outcome_status: "completed",
    latest_proof_status: "proved",
    latest_reconciliation_state: "not_reconciled",
    latest_trust_status: "proof_captured_not_reconciled",
  },
};

const sampleTrustedTaskDetails = {
  ...sampleTaskDetails,
  linked_runs: [
    {
      ...sampleTaskDetails.linked_runs[0],
      execution_summary: {
        latest_execution_path_classification: "governed_api_executed",
        latest_outcome_status: "completed",
        latest_proof_status: "proved",
        latest_reconciliation_state: "reconciled",
        latest_trust_status: "trusted_reconciled",
      },
    },
  ],
  latest_execution_summary: {
    latest_execution_path_classification: "governed_api_executed",
    latest_outcome_status: "completed",
    latest_proof_status: "proved",
    latest_reconciliation_state: "reconciled",
    latest_trust_status: "trusted_reconciled",
  },
};

const sampleTaskDetailsWithOlderTrustFailure = {
  ...sampleTrustedTaskDetails,
  linked_run_count: 2,
  linked_runs: [
    sampleTrustedTaskDetails.linked_runs[0],
    {
      id: "run_older_failed",
      status: "completed",
      started_at: "2026-04-12T01:40:00+00:00",
      attention_summary: {
        attention_count: 1,
      },
      health_summary: {
        final_success_count: 0,
      },
      execution_summary: {
        latest_execution_path_classification: "governed_api_executed",
        latest_outcome_status: "completed",
        latest_proof_status: "proved",
        latest_reconciliation_state: "reconciliation_failed",
        latest_trust_status: "reconciliation_failed",
      },
    },
  ],
};

const sampleRunDetails = {
  run: {
    id: "run_cbfef7e75b58",
    status: "running",
  },
  governed_external_run_summary: {
    total_execution_groups: 1,
    total_attempts: 1,
    governed_api_execution_count: 1,
    final_failed_count: 0,
    final_budget_stopped_count: 0,
    pre_observation_block_count: 0,
    final_proof_missing_count: 0,
    final_success_count: 1,
    final_proved_count: 1,
  },
  governed_external_attention_items: [],
  governed_pre_execution_blocks: [],
  governed_external_execution_groups: [
    {
      execution_group_id: "execution_group_088f06edadb2",
      execution_path_classification: "governed_api_executed",
      final_outcome_status: "completed",
      final_proof_status: "proved",
    },
  ],
};

test("fetchTaskDetails uses the read-only task-details route", async () => {
  const calls = [];
  const payload = await fetchTaskDetails("PK-115", async (url, options) => {
    calls.push({ url, options });
    return {
      ok: true,
      json: async () => sampleTaskDetails,
    };
  });

  assert.deepEqual(payload, sampleTaskDetails);
  assert.deepEqual(calls, [
    {
      url: "/api/task-details?task_id=PK-115",
      options: { cache: "no-store" },
    },
  ]);
});

test("fetchRunDetails uses the existing read-only run-details route", async () => {
  const calls = [];
  const payload = await fetchRunDetails("run_cbfef7e75b58", async (url, options) => {
    calls.push({ url, options });
    return {
      ok: true,
      json: async () => sampleRunDetails,
    };
  });

  assert.deepEqual(payload, sampleRunDetails);
  assert.deepEqual(calls, [
    {
      url: "/api/run-details?run_id=run_cbfef7e75b58",
      options: { cache: "no-store" },
    },
  ]);
});

test("selectLinkedRunId restores a valid preferred run and falls back cleanly", () => {
  assert.equal(selectLinkedRunId(sampleTaskDetails, "run_cbfef7e75b58"), "run_cbfef7e75b58");
  assert.equal(selectLinkedRunId(sampleTaskDetails, "run_missing"), "run_cbfef7e75b58");
  assert.equal(selectLinkedRunId({ linked_runs: [] }), "");
});

test("summarizeMilestones derives milestone cues from existing board and task summaries", () => {
  const summaries = summarizeMilestones(sampleSnapshot);

  assert.deepEqual(
    summaries.map((summary) => ({
      id: summary.id,
      taskCount: summary.taskCount,
      linkedRunCount: summary.linkedRunCount,
      attentionTaskCount: summary.attentionTaskCount,
      signalSummary: summary.signalSummary,
      trustLabel: summary.trustLabel,
      trustTone: summary.trustTone,
      highestPriorityTrustIssue: summary.highestPriorityTrustIssue,
    })),
    [
      {
        id: "milestone_cd78dafc9f81",
        taskCount: 1,
        linkedRunCount: 1,
        attentionTaskCount: 0,
        signalSummary: "1 task(s) show governed run evidence",
        trustLabel: "1 task(s) need trust follow-up",
        trustTone: "warning",
        highestPriorityTrustIssue: "proof_captured_not_reconciled",
      },
      {
        id: "milestone_other",
        taskCount: 1,
        linkedRunCount: 0,
        attentionTaskCount: 1,
        signalSummary: "1 task(s) need attention",
        trustLabel: "No trust evidence yet",
        trustTone: "muted",
        highestPriorityTrustIssue: "",
      },
    ],
  );
});

test("filterBoardByMilestone keeps the board read-only while narrowing task context", () => {
  const filteredBoard = filterBoardByMilestone(sampleSnapshot, "milestone_cd78dafc9f81");

  assert.equal(filteredBoard[0].cards.length, 1);
  assert.equal(filteredBoard[0].cards[0].id, "PK-115");
});

test("renderIntegratedTaskDetail shows task context and linked run evidence together", () => {
  const html = renderIntegratedTaskDetail(sampleTaskDetails, sampleRunDetails, {
    taskStatus: "loaded",
    runStatus: "loaded",
    selectedRunId: "run_cbfef7e75b58",
  });

  assert.match(html, /Integrated Task Detail/);
  assert.match(html, /AUDIT governed API truth check/);
  assert.match(html, /Project/);
  assert.match(html, /M7 - Studio Foundations/);
  assert.match(html, /Linked runs/);
  assert.match(html, /run_cbfef7e75b58/);
  assert.match(html, /Trust follow-up needed/);
  assert.match(html, /Proof Captured Not Reconciled/);
  assert.match(html, /Not Reconciled/);
  assert.match(html, /Run Evidence/);
  assert.match(html, /Open full run evidence/);
  assert.match(html, /Execution groups/);
  assert.match(html, /governed api executed/i);
  assert.doesNotMatch(html, /Retry run|Approve|Reject|Dispatch|Edit task/i);
});

test("summarizeTaskTrust prefers outstanding trust follow-up over a newer trusted run", () => {
  const summary = summarizeTaskTrust(sampleTaskDetailsWithOlderTrustFailure);

  assert.equal(summary.latestTrustStatus, "trusted_reconciled");
  assert.equal(summary.latestReconciliationState, "reconciled");
  assert.equal(summary.hasOutstandingFollowUp, true);
  assert.equal(summary.followUpRunId, "run_older_failed");
  assert.equal(summary.followUpCategory, "reconciliation_failed");
  assert.equal(summary.concernIsLatestRun, false);
});

test("renderIntegratedTaskDetail shows trusted latest run while pointing to the run that needs trust review", () => {
  const html = renderIntegratedTaskDetail(sampleTaskDetailsWithOlderTrustFailure, sampleRunDetails, {
    taskStatus: "loaded",
    runStatus: "loaded",
    selectedRunId: "run_cbfef7e75b58",
  });

  assert.match(html, /Trust follow-up needed on an earlier run/);
  assert.match(html, /run_older_failed/);
  assert.match(html, /Latest run is trusted|Trusted Reconciled/);
  assert.match(html, /Inspect next:/);
  assert.doesNotMatch(html, /Retry run|Approve|Reject|Dispatch|Edit task/i);
});

test("renderOperatorWall keeps board and integrated task context in one read-only surface", () => {
  const html = renderOperatorWall(sampleSnapshot, {
    snapshotStatus: "loaded",
    activeProject: "program-kanban",
    selectedMilestoneId: "milestone_cd78dafc9f81",
    selectedTaskId: "PK-115",
    taskDetails: sampleTaskDetails,
    taskStatus: "loaded",
    runDetails: sampleRunDetails,
    runStatus: "loaded",
    selectedRunId: "run_cbfef7e75b58",
  });

  assert.match(html, /Unified Operator Workspace/);
  assert.match(html, /What Matters Now/);
  assert.match(html, /Board Pulse/);
  assert.match(html, /Workflow Path/);
  assert.match(html, /Milestone context/);
  assert.match(html, /M7 - Studio Foundations/);
  assert.match(html, /Showing all milestones|Milestone filter:/);
  assert.match(html, /Task board connected to governed execution evidence/);
  assert.match(html, /Planning Surface/);
  assert.match(html, /Evidence Surface/);
  assert.match(html, /Trust-aware board/);
  assert.match(html, /Task and run detail/);
  assert.match(html, /data-task-id="PK-115"/);
  assert.doesNotMatch(html, /data-task-id="PK-101"/);
  assert.match(html, /Integrated task detail/);
  assert.match(html, /AUDIT governed API truth check/);
  assert.match(html, /Trust follow-up needed/);
  assert.match(html, /Linked governed run/);
  assert.match(html, /Load project/);
  assert.doesNotMatch(html, /Retry run|Approve|Reject|Dispatch|Move card|Edit task/i);
});

test("renderOperatorWall surfaces trust-aware cues on milestone and task cards while staying read-only", () => {
  const html = renderOperatorWall(sampleSnapshot, {
    snapshotStatus: "loaded",
    activeProject: "program-kanban",
  });

  assert.match(html, /What Matters Now/);
  assert.match(html, /Current Lens/);
  assert.match(html, /Board Pulse/);
  assert.match(html, /data-task-id="PK-115"/);
  assert.match(html, /Trust follow-up needed/);
  assert.match(html, /Proof captured, not reconciled on 1 linked run\(s\)/);
  assert.match(html, /1 task\(s\) need trust follow-up/);
  assert.match(html, /Proof captured, not reconciled across 1 linked run\(s\)/);
  assert.match(html, /No trust evidence yet/);
  assert.doesNotMatch(html, /Retry run|Approve|Reject|Dispatch|Move card|Edit task/i);
});
