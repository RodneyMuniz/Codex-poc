const appRoot = typeof document !== "undefined" ? document.querySelector("#app") : null;
const CONTROL_ROOM_CONTEXT_STORAGE_KEY = "operator-wall:control-room-context:v1";

function browserLocalStorage() {
  if (typeof window === "undefined") {
    return null;
  }
  try {
    return window.localStorage ?? null;
  } catch {
    return null;
  }
}

export function normalizeStickyControlRoomContext(value) {
  const runId = String(value?.runId || "").trim();
  const selectedGroupId = String(value?.selectedGroupId || "").trim() || null;
  const selectedAttemptId = String(value?.selectedAttemptId || "").trim() || null;
  return {
    runId,
    selectedGroupId,
    selectedAttemptId,
  };
}

export function readStickyControlRoomContext(storage = browserLocalStorage()) {
  if (!storage) {
    return normalizeStickyControlRoomContext({});
  }
  try {
    const raw = storage.getItem(CONTROL_ROOM_CONTEXT_STORAGE_KEY);
    if (!raw) {
      return normalizeStickyControlRoomContext({});
    }
    return normalizeStickyControlRoomContext(JSON.parse(raw));
  } catch {
    return normalizeStickyControlRoomContext({});
  }
}

export function writeStickyControlRoomContext(context, storage = browserLocalStorage()) {
  if (!storage) {
    return false;
  }
  const normalized = normalizeStickyControlRoomContext(context);
  try {
    if (!normalized.runId) {
      storage.removeItem(CONTROL_ROOM_CONTEXT_STORAGE_KEY);
      return true;
    }
    storage.setItem(CONTROL_ROOM_CONTEXT_STORAGE_KEY, JSON.stringify(normalized));
    return true;
  } catch {
    return false;
  }
}

export function deriveInitialStickyControlRoomState(queryRunId, savedContext) {
  const normalizedQueryRunId = String(queryRunId || "").trim();
  const normalizedSavedContext = normalizeStickyControlRoomContext(savedContext);
  const runId = normalizedQueryRunId || normalizedSavedContext.runId || "";
  const shouldRestoreSelection = Boolean(runId) && runId === normalizedSavedContext.runId;
  return {
    runId,
    selectedGroupId: shouldRestoreSelection ? normalizedSavedContext.selectedGroupId : null,
    selectedAttemptId: shouldRestoreSelection ? normalizedSavedContext.selectedAttemptId : null,
  };
}

const initialQueryRunId = typeof window !== "undefined"
  ? new URLSearchParams(window.location.search).get("run_id") || ""
  : "";
const initialStickyControlRoomState = deriveInitialStickyControlRoomState(
  initialQueryRunId,
  readStickyControlRoomContext(),
);
const initialRunId = initialStickyControlRoomState.runId;

let currentRunDetails = null;
let currentRunId = initialRunId;
let selectedGroupId = initialStickyControlRoomState.selectedGroupId;
let selectedAttemptId = initialStickyControlRoomState.selectedAttemptId;
let currentRecentRuns = [];
let currentRecentActivity = null;
let currentRecentRunsStatus = "idle";

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function statusLabel(value) {
  return String(value ?? "unknown").replaceAll("_", " ");
}

function safeArray(value) {
  return Array.isArray(value) ? value : [];
}

function numberValue(value) {
  const numeric = Number(value ?? 0);
  return Number.isFinite(numeric) ? numeric : 0;
}

export function renderViewStatusStrip(viewState = "empty", runId = "") {
  const normalizedState = String(viewState || "empty").trim() || "empty";
  const normalizedRunId = String(runId || "").trim();
  const stateConfig = {
    loaded: {
      label: "Loaded",
      tone: "success",
      description: normalizedRunId
        ? "Read-only governed evidence is loaded for this run."
        : "Read-only governed evidence is loaded.",
    },
    loading: {
      label: "Loading",
      tone: "warning",
      description: normalizedRunId
        ? "Fetching persisted governed evidence for this run."
        : "Fetching persisted governed evidence.",
    },
    error: {
      label: "Unavailable",
      tone: "warning",
      description: "Run details could not be loaded from the read-only evidence path.",
    },
    empty: {
      label: "No run loaded",
      tone: "muted",
      description: "Enter a run id to inspect the control room.",
    },
  };
  const currentState = stateConfig[normalizedState] || stateConfig.empty;
  const runMarkup = normalizedRunId
    ? `<li class="badge badge--strong">Run ${escapeHtml(normalizedRunId)}</li>`
    : `<li class="badge badge--muted">Run not selected</li>`;

  return `
    <section class="status-strip" aria-label="Control room status">
      <div class="status-strip__copy">
        <p class="status-strip__eyebrow">Control Room</p>
        <h2>Governed external evidence</h2>
        <p>${escapeHtml(currentState.description)}</p>
      </div>
      <div class="status-strip__meta">
        <ul class="badge-list">
          <li class="badge badge--${escapeHtml(currentState.tone)}">${escapeHtml(currentState.label)}</li>
          ${runMarkup}
        </ul>
      </div>
    </section>
  `;
}

export function normalizeRecentRuns(snapshotPayload) {
  return safeArray(snapshotPayload?.recent_runs).slice(0, 8).map((run) => ({
    id: run?.id || "",
    status: run?.status || "unknown",
    timestamp: run?.updated_at || run?.created_at || run?.completed_at || "-",
    taskTitle: run?.task_title || "",
    stopReason: run?.stop_reason || "",
    totalExecutionGroups: numberValue(run?.governed_external_run_summary?.total_execution_groups),
    totalAttempts: numberValue(run?.governed_external_run_summary?.total_attempts),
    governedApiExecutionCount: numberValue(run?.governed_external_run_summary?.governed_api_execution_count),
    blockedExecutionCount: numberValue(run?.governed_external_run_summary?.blocked_execution_count),
    preObservationBlockCount: numberValue(run?.governed_external_run_summary?.pre_observation_block_count),
    finalSuccessCount: numberValue(run?.governed_external_run_summary?.final_success_count),
    finalFailedCount: numberValue(run?.governed_external_run_summary?.final_failed_count),
    finalBudgetStoppedCount: numberValue(run?.governed_external_run_summary?.final_budget_stopped_count),
    finalProofMissingCount: numberValue(run?.governed_external_run_summary?.final_proof_missing_count),
  })).filter((run) => run.id);
}

export async function fetchRecentRuns(fetchImpl = globalThis.fetch) {
  const response = await fetchImpl("/api/snapshot?project=all", {
    cache: "no-store",
  });
  if (!response.ok) {
    throw new Error(`Recent runs request failed with ${response.status}`);
  }
  const payload = await response.json();
  return normalizeRecentRuns(payload);
}

export function summarizeRecentActivity(recentRuns) {
  const runs = safeArray(recentRuns);
  const summary = {
    totalRuns: runs.length,
    runsWithFailures: 0,
    runsWithBudgetStops: 0,
    runsWithProofMissing: 0,
    runsWithGovernedApiExecution: 0,
    runsWithPreExecutionBlocks: 0,
    successfulRuns: 0,
    hints: [],
  };

  for (const run of runs) {
    const failed = run.finalFailedCount > 0 || ["failed", "paused_breach"].includes(String(run.status || "").trim());
    const budgetStopped = run.finalBudgetStoppedCount > 0 || [
      "retry_limit_exceeded",
      "prompt_budget_exceeded",
      "completion_budget_exceeded",
      "total_budget_exceeded",
    ].includes(String(run.stopReason || "").trim());
    const proofMissing = run.finalProofMissingCount > 0;
    const governedApi = run.governedApiExecutionCount > 0;
    const preExecutionBlocked = run.blockedExecutionCount > 0 || run.preObservationBlockCount > 0;
    const successful = run.finalSuccessCount > 0 || String(run.status || "").trim() === "completed";

    if (failed) {
      summary.runsWithFailures += 1;
    }
    if (budgetStopped) {
      summary.runsWithBudgetStops += 1;
    }
    if (proofMissing) {
      summary.runsWithProofMissing += 1;
    }
    if (governedApi) {
      summary.runsWithGovernedApiExecution += 1;
    }
    if (preExecutionBlocked) {
      summary.runsWithPreExecutionBlocks += 1;
    }
    if (successful) {
      summary.successfulRuns += 1;
    }
  }

  if (summary.totalRuns === 0) {
    summary.hints.push("No recent runs are available in this window");
    return summary;
  }

  if (summary.runsWithFailures > summary.successfulRuns) {
    summary.hints.push("More failures than successful runs");
  } else if (summary.successfulRuns > 0 && summary.runsWithFailures === 0) {
    summary.hints.push("Most recent runs are successful");
  }

  if (summary.runsWithPreExecutionBlocks >= 2) {
    summary.hints.push("Frequent pre-execution blocks detected");
  }

  if (summary.runsWithGovernedApiExecution === 0) {
    summary.hints.push("No governed API execution recorded in this window");
  } else if (summary.runsWithGovernedApiExecution < Math.ceil(summary.totalRuns / 2)) {
    summary.hints.push("Governed API execution appears less common in this window");
  }

  return summary;
}

export function summarizeSystemHealth(activitySummary) {
  const summary = activitySummary || summarizeRecentActivity([]);
  const totalRuns = numberValue(summary.totalRuns);
  const runsWithFailures = numberValue(summary.runsWithFailures);
  const runsWithBudgetStops = numberValue(summary.runsWithBudgetStops);
  const runsWithProofMissing = numberValue(summary.runsWithProofMissing);
  const runsWithGovernedApiExecution = numberValue(summary.runsWithGovernedApiExecution);
  const runsWithPreExecutionBlocks = numberValue(summary.runsWithPreExecutionBlocks);
  const successfulRuns = numberValue(summary.successfulRuns);
  const majorityThreshold = Math.ceil(Math.max(totalRuns, 1) / 2);

  if (totalRuns === 0) {
    return {
      label: "Limited signal",
      tone: "muted",
      explanation: "Recent run data is not yet available to judge system health.",
    };
  }

  if (runsWithPreExecutionBlocks >= majorityThreshold) {
    return {
      label: "At Risk",
      tone: "risk",
      explanation: "Frequent pre-execution blocks are showing up in the recent run window.",
    };
  }

  if (runsWithGovernedApiExecution === 0) {
    return {
      label: "At Risk",
      tone: "risk",
      explanation: "Recent runs are not showing governed API execution right now.",
    };
  }

  if (runsWithFailures >= majorityThreshold) {
    if (runsWithBudgetStops > 0) {
      return {
        label: "At Risk",
        tone: "risk",
        explanation: "Recent runs show repeated failures with budget-stop signals present.",
      };
    }
    return {
      label: "At Risk",
      tone: "risk",
      explanation: "Recent runs show more failures than successful completions.",
    };
  }

  if (
    successfulRuns > 0
    && runsWithFailures === 0
    && runsWithBudgetStops === 0
    && runsWithProofMissing === 0
    && runsWithPreExecutionBlocks === 0
  ) {
    return {
      label: "Healthy",
      tone: "healthy",
      explanation: "Most recent runs completed successfully with minimal issues.",
    };
  }

  if (runsWithBudgetStops > 0) {
    return {
      label: "Degraded",
      tone: "degraded",
      explanation: "Recent runs show budget-stop pressure even though the system is still moving.",
    };
  }

  if (runsWithProofMissing > 0) {
    return {
      label: "Degraded",
      tone: "degraded",
      explanation: "Recent runs are executing, but proof-missing outcomes are still present.",
    };
  }

  return {
    label: "Degraded",
    tone: "degraded",
    explanation: "Recent runs are mixed, with some issues still needing operator review.",
  };
}

function stopReasonIsBudgetStop(stopReason) {
  return [
    "retry_limit_exceeded",
    "prompt_budget_exceeded",
    "completion_budget_exceeded",
    "total_budget_exceeded",
  ].includes(String(stopReason || "").trim());
}

function summarizeComparableRunSignals(runLike) {
  const status = String(runLike?.status || "").trim();
  const stopReason = String(runLike?.stopReason || runLike?.stop_reason || "").trim();
  const finalFailedCount = numberValue(runLike?.finalFailedCount ?? runLike?.final_failed_count);
  const finalBudgetStoppedCount = numberValue(runLike?.finalBudgetStoppedCount ?? runLike?.final_budget_stopped_count);
  const finalProofMissingCount = numberValue(runLike?.finalProofMissingCount ?? runLike?.final_proof_missing_count);
  const governedApiExecutionCount = numberValue(runLike?.governedApiExecutionCount ?? runLike?.governed_api_execution_count);
  const blockedExecutionCount = numberValue(runLike?.blockedExecutionCount ?? runLike?.blocked_execution_count);
  const preObservationBlockCount = numberValue(runLike?.preObservationBlockCount ?? runLike?.pre_observation_block_count);
  const finalSuccessCount = numberValue(runLike?.finalSuccessCount ?? runLike?.final_success_count);

  const hasFailure = finalFailedCount > 0 || ["failed", "paused_breach"].includes(status);
  const hasBudgetStop = finalBudgetStoppedCount > 0 || stopReasonIsBudgetStop(stopReason);
  const hasProofMissing = finalProofMissingCount > 0;
  const hasGovernedApiExecution = governedApiExecutionCount > 0;
  const hasPreObservationBlock = blockedExecutionCount > 0 || preObservationBlockCount > 0;
  const hasSuccess = finalSuccessCount > 0 || status === "completed";

  return {
    id: String(runLike?.id || "").trim(),
    status,
    stopReason,
    hasFailure,
    hasBudgetStop,
    hasProofMissing,
    hasGovernedApiExecution,
    hasPreObservationBlock,
    hasSuccess,
    attentionSignalCount: [
      hasFailure,
      hasBudgetStop,
      hasProofMissing,
      hasPreObservationBlock,
    ].filter(Boolean).length,
  };
}

function summarizeLoadedRunSignals(runDetails) {
  const run = runDetails?.run || {};
  const summary = runDetails?.governed_external_run_summary || {};
  return summarizeComparableRunSignals({
    id: run.id || "",
    status: run.status || "unknown",
    stop_reason: run.stop_reason || "",
    final_failed_count: summary.final_failed_count,
    final_budget_stopped_count: summary.final_budget_stopped_count,
    final_proof_missing_count: summary.final_proof_missing_count,
    governed_api_execution_count: summary.governed_api_execution_count,
    blocked_execution_count: summary.blocked_execution_count,
    pre_observation_block_count: summary.pre_observation_block_count,
    final_success_count: summary.final_success_count,
  });
}

export function compareLoadedRunToRecentWindow(runDetails, recentRuns) {
  const loaded = summarizeLoadedRunSignals(runDetails);
  if (!loaded.id) {
    return null;
  }

  const peers = safeArray(recentRuns)
    .filter((run) => String(run?.id || "").trim() && String(run?.id || "").trim() !== loaded.id)
    .map((run) => summarizeComparableRunSignals(run));

  if (!peers.length) {
    return {
      headline: "Recent comparison is limited because this run is the only one in the current window.",
      cues: [],
    };
  }

  const countPeers = (predicate) => peers.filter(predicate).length;
  const majorityThreshold = Math.ceil(peers.length / 2);
  const peersWithMoreAttention = countPeers((peer) => peer.attentionSignalCount > loaded.attentionSignalCount);
  const peersWithLessAttention = countPeers((peer) => peer.attentionSignalCount < loaded.attentionSignalCount);
  const peersWithPreBlocks = countPeers((peer) => peer.hasPreObservationBlock);
  const peersWithBudgetStops = countPeers((peer) => peer.hasBudgetStop);
  const peersWithProofMissing = countPeers((peer) => peer.hasProofMissing);
  const peersWithGovernedApi = countPeers((peer) => peer.hasGovernedApiExecution);

  let headline = "This run looks broadly in line with the recent window.";
  if (loaded.attentionSignalCount === 0 && peersWithMoreAttention >= majorityThreshold) {
    headline = "This run looks cleaner than most recent runs.";
  } else if (loaded.attentionSignalCount > 0 && peersWithLessAttention >= majorityThreshold) {
    headline = "This run has more attention signals than most recent runs.";
  } else if (!loaded.hasGovernedApiExecution && peersWithGovernedApi >= majorityThreshold) {
    headline = "This run did not reach governed API execution, unlike most recent runs.";
  } else if (loaded.hasGovernedApiExecution && peersWithGovernedApi === 0) {
    headline = "This run reached governed API execution, unlike most recent runs.";
  }

  const cues = [];
  if (loaded.hasPreObservationBlock && peersWithPreBlocks < majorityThreshold) {
    cues.push("This run includes a pre-execution block, which is uncommon in the recent window.");
  }
  if (loaded.hasBudgetStop && peersWithBudgetStops < majorityThreshold) {
    cues.push("This run hit a budget stop, which is less common in the recent window.");
  }
  if (loaded.hasProofMissing && peersWithProofMissing < majorityThreshold) {
    cues.push("This run has proof-missing outcomes, which are uncommon in the recent window.");
  }

  return {
    headline,
    cues: cues.slice(0, 2),
  };
}

export async function handleRecentRunSelection(runId, loadRunImpl) {
  const normalizedRunId = String(runId || "").trim();
  if (!normalizedRunId) {
    return false;
  }
  await loadRunImpl(normalizedRunId, { preserveSelection: false });
  return true;
}

const SUMMARY_METRIC_GUIDES = {
  total_execution_groups: {
    label: "Execution groups",
    meaning: "Logical governed execution chains recorded for this run.",
    why: "It shows whether work stayed contained or split into multiple governed paths.",
    goodBad: "A small expected count is usually healthy; unexpected growth can point to retries or fragmented work.",
    inspectNext: "Open Execution Groups to compare final outcomes and attention items.",
  },
  total_attempts: {
    label: "Attempts",
    meaning: "Total governed external attempts recorded across every execution group.",
    why: "It shows how much retry pressure or repetition the run created.",
    goodBad: "Fewer clean attempts are usually healthier; spikes often deserve a closer look.",
    inspectNext: "Inspect attempt chains and any retry or budget stop evidence.",
  },
  governed_api_execution_count: {
    label: "API executed",
    meaning: "Execution groups with evidence that they reached the governed API boundary.",
    why: "It separates real external execution from work that never reached the provider call.",
    goodBad: "Higher is not always better, but nonzero confirms governed API use actually happened.",
    inspectNext: "Check final proof state and execution-group outcomes.",
  },
  blocked_execution_count: {
    label: "Blocked pre-exec",
    meaning: "Observed governed attempts that were blocked before completing execution.",
    why: "It surfaces work that entered the governed path but did not finish cleanly.",
    goodBad: "Zero is cleaner; nonzero means follow-up is needed on blocked groups.",
    inspectNext: "Inspect blocked execution groups and their attempt evidence.",
  },
  pre_observation_block_count: {
    label: "Pre-observation blocks",
    meaning: "Governed requests blocked before any external attempt record was created.",
    why: "It prevents blocked work from disappearing before the external observation stage.",
    goodBad: "Zero is ideal; any nonzero count usually points to upstream gating or policy blocks.",
    inspectNext: "Review pre-observation block cards and their block reasons first.",
  },
  final_success_count: {
    label: "Final success",
    meaning: "Execution groups whose final recorded outcome completed successfully.",
    why: "It shows how much governed work finished cleanly.",
    goodBad: "Higher is healthier; drops usually mean more operator follow-up.",
    inspectNext: "Compare clean groups against attention items to see what did not land cleanly.",
  },
  final_failed_count: {
    label: "Final failed",
    meaning: "Execution groups whose final recorded outcome ended failed.",
    why: "These are unresolved governed executions that still need review.",
    goodBad: "Zero is ideal; any nonzero count deserves attention.",
    inspectNext: "Open failed groups and inspect attempt evidence before retrying.",
  },
  final_stopped_count: {
    label: "Final stopped",
    meaning: "Execution groups whose final recorded outcome stopped before clean completion.",
    why: "It shows how often governing stop conditions shaped the end state.",
    goodBad: "Zero is cleaner; nonzero means a stop boundary mattered in this run.",
    inspectNext: "Inspect stop reasons and the final attempt for each stopped group.",
  },
  final_budget_stopped_count: {
    label: "Budget stopped",
    meaning: "Execution groups whose final outcome was stopped by retry or token budget policy.",
    why: "It shows where budget governance actively halted execution.",
    goodBad: "Zero is usually cleaner; nonzero means spend or retry boundaries mattered.",
    inspectNext: "Review the stop reason and the suggested next step on attention items.",
  },
  final_proof_missing_count: {
    label: "Proof missing",
    meaning: "Final governed outcomes that still lack provider proof metadata.",
    why: "Claim exists, but first-step external proof was not captured.",
    goodBad: "Zero is stronger; nonzero means trust is still limited.",
    inspectNext: "Inspect proof-missing attention items and supporting attempt events.",
  },
  final_proved_count: {
    label: "Final proved",
    meaning: "Final governed outcomes with first-step provider proof captured.",
    why: "It shows how much of the run has external proof, not full reconciliation.",
    goodBad: "Higher is stronger, but it still does not mean the run is fully reconciled.",
    inspectNext: "Use verification badges and attempt evidence to confirm the proof signal.",
  },
  final_trusted_reconciled_count: {
    label: "Trusted",
    meaning: "Final governed outcomes whose provider proof has also been reconciled.",
    why: "This is the strongest trust state currently available in the read model.",
    goodBad: "Higher is stronger; zero means trust has not fully closed for this run.",
    inspectNext: "Open execution groups to confirm which governed outcomes are fully trusted.",
  },
  final_proof_captured_not_reconciled_count: {
    label: "Proof not reconciled",
    meaning: "Final governed outcomes with provider proof captured but no successful reconciliation yet.",
    why: "These runs have external proof, but trust follow-up is still open.",
    goodBad: "Zero is cleaner; nonzero means reconciliation work remains.",
    inspectNext: "Inspect trust badges and reconciliation state on the affected groups.",
  },
  final_reconciliation_failed_count: {
    label: "Reconciliation failed",
    meaning: "Final governed outcomes where reconciliation was attempted and failed.",
    why: "This is distinct from missing proof and usually needs direct operator review.",
    goodBad: "Zero is ideal; nonzero means explicit trust failures are present.",
    inspectNext: "Review reconciliation reason codes and supporting evidence first.",
  },
  final_claimed_only_count: {
    label: "Claimed only",
    meaning: "Final governed outcomes with a claim signal but no provider proof captured.",
    why: "Trust remains limited because proof was not recorded.",
    goodBad: "Zero is stronger; nonzero means claim-only evidence is still present.",
    inspectNext: "Inspect proof-missing groups and their supporting attempt events.",
  },
  final_claim_missing_count: {
    label: "Claim missing",
    meaning: "Final governed outcomes missing even the expected claim signal.",
    why: "This is the weakest trust state in the current read model.",
    goodBad: "Zero is expected; nonzero should be investigated carefully.",
    inspectNext: "Review the affected attempts and the evidence capture path.",
  },
};

function metricTone(metricKey, value) {
  const numericValue = Number(value ?? 0);
  if ([
    "final_failed_count",
    "final_budget_stopped_count",
    "final_proof_missing_count",
    "blocked_execution_count",
    "pre_observation_block_count",
    "final_proof_captured_not_reconciled_count",
    "final_reconciliation_failed_count",
    "final_claimed_only_count",
    "final_claim_missing_count",
  ].includes(metricKey)) {
    return numericValue > 0 ? "warning" : "neutral";
  }
  if ([
    "final_success_count",
    "final_proved_count",
    "governed_api_execution_count",
    "final_trusted_reconciled_count",
  ].includes(metricKey)) {
    return numericValue > 0 ? "success" : "neutral";
  }
  return "neutral";
}

function renderMetricHelp(metricKey) {
  const guide = SUMMARY_METRIC_GUIDES[metricKey];
  if (!guide) {
    return "";
  }

  return `
    <details class="metric-help">
      <summary aria-label="Explain ${escapeHtml(guide.label)}" title="Explain ${escapeHtml(guide.label)}">?</summary>
      <div class="metric-help__body">
        <p><strong>What it means:</strong> ${escapeHtml(guide.meaning)}</p>
        <p><strong>Why it matters:</strong> ${escapeHtml(guide.why)}</p>
        <p><strong>Good vs bad:</strong> ${escapeHtml(guide.goodBad)}</p>
        <p><strong>Inspect next:</strong> ${escapeHtml(guide.inspectNext)}</p>
      </div>
    </details>
  `;
}

function renderStat(metricKey, value) {
  const guide = SUMMARY_METRIC_GUIDES[metricKey];
  const label = guide?.label || metricKey;
  const tone = metricTone(metricKey, value);
  return `
    <article class="stat-card stat-card--${escapeHtml(tone)}" data-metric-key="${escapeHtml(metricKey)}">
      <div class="stat-card__top">
        <span class="stat-card__label">${escapeHtml(label)}</span>
        ${renderMetricHelp(metricKey)}
      </div>
      <strong class="stat-card__value">${escapeHtml(value)}</strong>
    </article>
  `;
}

function renderKeyValue(label, value) {
  return `<li><strong>${escapeHtml(label)}:</strong> ${escapeHtml(value)}</li>`;
}

function renderOptionalKeyValue(label, value) {
  const normalized = String(value ?? "").trim();
  if (!normalized) {
    return "";
  }
  return renderKeyValue(label, normalized);
}

function proofStatusLabel(value) {
  const normalized = String(value ?? "").trim();
  if (normalized === "proved") {
    return "Proof captured";
  }
  if (normalized === "missing") {
    return "Proof missing";
  }
  return normalized ? statusLabel(normalized) : "";
}

function reconciliationStateLabel(value) {
  const normalized = String(value ?? "").trim();
  if (normalized === "not_reconciled") {
    return "Not reconciled";
  }
  if (normalized === "reconciliation_pending") {
    return "Reconciliation pending";
  }
  if (normalized === "reconciled") {
    return "Reconciled";
  }
  if (normalized === "reconciliation_failed") {
    return "Reconciliation failed";
  }
  return normalized ? statusLabel(normalized) : "";
}

function reconciliationStateTone(value) {
  const normalized = String(value ?? "").trim();
  if (normalized === "reconciled") {
    return "success";
  }
  if (normalized === "reconciliation_pending" || normalized === "reconciliation_failed") {
    return "warning";
  }
  return "muted";
}

function trustStatusLabel(value) {
  const normalized = String(value ?? "").trim();
  if (normalized === "trusted_reconciled") {
    return "Trusted (reconciled)";
  }
  if (normalized === "proof_captured_not_reconciled") {
    return "Proof captured, not reconciled";
  }
  if (normalized === "reconciliation_failed") {
    return "Reconciliation failed";
  }
  if (normalized === "claimed_only") {
    return "Claimed only";
  }
  if (normalized === "claim_missing") {
    return "Claim missing";
  }
  return normalized ? statusLabel(normalized) : "";
}

function trustStatusTone(value) {
  const normalized = String(value ?? "").trim();
  if (normalized === "trusted_reconciled") {
    return "success";
  }
  if ([
    "proof_captured_not_reconciled",
    "reconciliation_failed",
    "claimed_only",
  ].includes(normalized)) {
    return "warning";
  }
  return "muted";
}

function explainTrustState(trustStatus, reconciliationState) {
  const normalizedTrust = String(trustStatus ?? "").trim();
  const normalizedReconciliation = String(reconciliationState ?? "").trim();

  if (normalizedTrust === "trusted_reconciled" || normalizedReconciliation === "reconciled") {
    return "Trusted after provider reconciliation";
  }
  if (normalizedTrust === "reconciliation_failed" || normalizedReconciliation === "reconciliation_failed") {
    return "Reconciliation failed after provider proof was captured";
  }
  if (normalizedReconciliation === "reconciliation_pending") {
    return "Proof captured, and reconciliation is still pending";
  }
  if (normalizedTrust === "proof_captured_not_reconciled") {
    return "Proof captured, but reconciliation is still outstanding";
  }
  if (normalizedTrust === "claimed_only") {
    return "Claim recorded, but provider proof is still missing";
  }
  if (normalizedTrust === "claim_missing") {
    return "Claim signal is missing for this governed execution";
  }
  return "";
}

function suggestNextStepForTrustState(trustStatus, reconciliationState) {
  const normalizedTrust = String(trustStatus ?? "").trim();
  const normalizedReconciliation = String(reconciliationState ?? "").trim();

  if (normalizedTrust === "trusted_reconciled" || normalizedReconciliation === "reconciled") {
    return "Inspect the reconciled run evidence if you need to confirm the trusted path.";
  }
  if (normalizedTrust === "reconciliation_failed" || normalizedReconciliation === "reconciliation_failed") {
    return "Inspect reconciliation evidence and the failure reason before treating this run as trusted.";
  }
  if (normalizedReconciliation === "reconciliation_pending" || normalizedTrust === "proof_captured_not_reconciled") {
    return "Check reconciliation evidence and follow-up status before treating this run as trusted.";
  }
  if (normalizedTrust === "claimed_only") {
    return "Check provider proof capture and future reconciliation status.";
  }
  if (normalizedTrust === "claim_missing") {
    return "Inspect claim capture and governed evidence before treating this run as trusted.";
  }
  return "";
}

function explainBudgetStop(reasonCode) {
  const normalized = String(reasonCode ?? "").trim();
  if (normalized === "retry_limit_exceeded") {
    return "Execution stopped by retry limit";
  }
  if ([
    "prompt_budget_exceeded",
    "completion_budget_exceeded",
    "total_budget_exceeded",
  ].includes(normalized)) {
    return "Execution stopped by token budget";
  }
  if (normalized) {
    return "Execution stopped by budget policy";
  }
  return null;
}

function explainAttentionItem(item) {
  const executionPath = String(item?.execution_path_classification ?? "").trim();
  const finalOutcome = String(item?.final_outcome_status ?? "").trim();
  const finalProof = String(item?.final_proof_status ?? "").trim();
  const budgetStopReason = String(item?.final_budget_stop_reason_code ?? "").trim();
  const trustExplanation = explainTrustState(item?.final_trust_status, item?.final_reconciliation_state);

  if (item?.final_trust_status === "reconciliation_failed" || item?.final_reconciliation_state === "reconciliation_failed") {
    return trustExplanation;
  }

  const budgetExplanation = explainBudgetStop(budgetStopReason);
  if (budgetExplanation) {
    return budgetExplanation;
  }
  if (
    item?.final_reconciliation_state === "reconciliation_pending"
    || item?.final_trust_status === "proof_captured_not_reconciled"
  ) {
    return trustExplanation;
  }
  if (executionPath === "governed_api_executed" && finalOutcome === "completed" && finalProof === "missing") {
    return trustExplanation || "Executed via governed API, but proof is still missing";
  }
  if (executionPath === "governed_api_executed" && finalOutcome && finalOutcome !== "completed") {
    return "Execution failed after governed API execution";
  }
  if (executionPath === "blocked_pre_execution") {
    return "Blocked before API call";
  }
  return trustExplanation || "Governed execution needs operator review";
}

function explainPreObservationBlock(block) {
  const reasonCode = String(block?.block_reason_code ?? "").trim();
  if (reasonCode === "role_state_blocked") {
    return "Blocked before API call: task state not eligible";
  }
  if (reasonCode === "tool_access_blocked") {
    return "Blocked before API call: tool access not allowed";
  }
  if (reasonCode === "prompt_blocked") {
    return "Blocked before API call: prompt blocked by policy";
  }
  if (reasonCode === "permission_blocked") {
    return "Blocked before API call: governance permission check failed";
  }
  return "Blocked before API call";
}

function suggestNextStepForAttentionItem(item) {
  const executionPath = String(item?.execution_path_classification ?? "").trim();
  const finalOutcome = String(item?.final_outcome_status ?? "").trim();
  const finalProof = String(item?.final_proof_status ?? "").trim();
  const budgetStopReason = String(item?.final_budget_stop_reason_code ?? "").trim();
  const trustSuggestion = suggestNextStepForTrustState(item?.final_trust_status, item?.final_reconciliation_state);

  if (item?.final_trust_status === "reconciliation_failed" || item?.final_reconciliation_state === "reconciliation_failed") {
    return trustSuggestion;
  }

  if (budgetStopReason === "retry_limit_exceeded") {
    return "Review retry limits or task quality before retrying.";
  }
  if ([
    "prompt_budget_exceeded",
    "completion_budget_exceeded",
    "total_budget_exceeded",
  ].includes(budgetStopReason)) {
    return "Review token budget or reduce prompt size.";
  }
  if (
    item?.final_reconciliation_state === "reconciliation_pending"
    || item?.final_trust_status === "proof_captured_not_reconciled"
  ) {
    return trustSuggestion;
  }
  if (executionPath === "governed_api_executed" && finalOutcome === "completed" && finalProof === "missing") {
    return trustSuggestion || "Check provider proof capture and future reconciliation status.";
  }
  if (executionPath === "governed_api_executed" && finalOutcome && finalOutcome !== "completed") {
    return "Inspect attempt evidence and failure reason before retrying.";
  }
  if (executionPath === "blocked_pre_execution") {
    return "Inspect the block reason before retrying.";
  }
  return trustSuggestion || "Review the supporting evidence before retrying.";
}

function suggestNextStepForPreObservationBlock(block) {
  const reasonCode = String(block?.block_reason_code ?? "").trim();
  if (reasonCode === "role_state_blocked") {
    return "Move the task to an eligible state before retrying.";
  }
  if (reasonCode === "tool_access_blocked") {
    return "Review tool access policy before retrying.";
  }
  if (reasonCode === "prompt_blocked") {
    return "Revise the prompt to satisfy governance policy.";
  }
  if (reasonCode === "permission_blocked") {
    return "Review the governance permission failure before retrying.";
  }
  return "Review the block reason before retrying.";
}

function priorityMeta(rank, label, tone) {
  return { rank, label, tone };
}

function priorityForPreObservationBlock() {
  return priorityMeta(0, "High", "high");
}

function priorityForAttentionItem(item) {
  const executionPath = String(item?.execution_path_classification ?? "").trim();
  const finalOutcome = String(item?.final_outcome_status ?? "").trim();
  const finalProof = String(item?.final_proof_status ?? "").trim();
  const budgetStopReason = String(item?.final_budget_stop_reason_code ?? "").trim();

  if (executionPath === "governed_api_executed" && finalOutcome && finalOutcome !== "completed" && !budgetStopReason) {
    return priorityMeta(1, "High", "high");
  }
  if (budgetStopReason) {
    return priorityMeta(2, "Medium", "medium");
  }
  if (executionPath === "governed_api_executed" && finalOutcome === "completed" && finalProof === "missing") {
    return priorityMeta(3, "Low", "low");
  }
  return priorityMeta(4, "Low", "low");
}

export function prioritizeAttentionEntries(items, preExecutionBlocks) {
  const blockEntries = safeArray(preExecutionBlocks).map((block) => ({
    kind: "pre_execution_block",
    priority: priorityForPreObservationBlock(),
    payload: block,
  }));
  const attentionEntries = safeArray(items).map((item) => ({
    kind: "attention_item",
    priority: priorityForAttentionItem(item),
    payload: item,
  }));

  return [...blockEntries, ...attentionEntries].sort((left, right) => left.priority.rank - right.priority.rank);
}

function renderVerificationBadges({
  claimStatus,
  proofStatus,
  providerRequestId,
  reconciliationState,
  trustStatus,
}) {
  const normalizedClaim = String(claimStatus ?? "").trim();
  const normalizedProof = String(proofStatus ?? "").trim();
  const normalizedReconciliation = String(reconciliationState ?? "").trim();
  const normalizedTrust = String(trustStatus ?? "").trim();
  const hasProviderRequestId = typeof providerRequestId === "string" && providerRequestId.trim().length > 0;
  const badges = [];
  const pushBadge = (label, tone) => {
    if (!label || badges.some((badge) => badge.label === label)) {
      return;
    }
    badges.push({ label, tone });
  };

  if (normalizedTrust) {
    pushBadge(trustStatusLabel(normalizedTrust), trustStatusTone(normalizedTrust));
  }

  if (!normalizedTrust) {
    if (normalizedProof === "proved" || hasProviderRequestId) {
      pushBadge("Proof captured", "success");
    } else if (normalizedProof === "missing") {
      if (normalizedClaim === "claimed") {
        pushBadge("Claimed only", "warning");
      }
      pushBadge("Proof missing", "warning");
    } else if (normalizedClaim === "claimed") {
      pushBadge("Claim recorded", "muted");
    }
  }

  const reconciliationIsImplicit = (
    (normalizedTrust === "trusted_reconciled" && normalizedReconciliation === "reconciled")
    || (normalizedTrust === "proof_captured_not_reconciled" && normalizedReconciliation === "not_reconciled")
    || (normalizedTrust === "reconciliation_failed" && normalizedReconciliation === "reconciliation_failed")
    || (normalizedTrust === "claimed_only" && normalizedReconciliation === "not_reconciled")
    || (normalizedTrust === "claim_missing" && normalizedReconciliation === "not_reconciled")
  );

  if (normalizedReconciliation && !reconciliationIsImplicit) {
    pushBadge(reconciliationStateLabel(normalizedReconciliation), reconciliationStateTone(normalizedReconciliation));
  }

  return `
    <ul class="badge-list verification-badges">
      ${badges.map((badge) => `
        <li class="badge badge--${escapeHtml(badge.tone)}">${escapeHtml(badge.label)}</li>
      `).join("")}
    </ul>
  `;
}

function executionPathLabel(value) {
  const normalized = String(value ?? "").trim();
  if (normalized === "governed_api_executed") {
    return "Governed API executed";
  }
  if (normalized === "blocked_pre_execution") {
    return "Blocked pre-execution";
  }
  if (normalized === "non_governed_execution") {
    return "Non-governed execution";
  }
  return "Unknown";
}

function renderExecutionPathBadge(executionPathClassification) {
  const normalized = String(executionPathClassification ?? "").trim();
  const tone = normalized === "governed_api_executed" ? "success" : normalized === "blocked_pre_execution" ? "warning" : "muted";
  return `
    <ul class="badge-list">
      <li class="badge badge--${escapeHtml(tone)}">${escapeHtml(executionPathLabel(normalized))}</li>
    </ul>
  `;
}

export function defaultSelectedGroupId(runDetails) {
  const attentionItems = safeArray(runDetails?.governed_external_attention_items);
  if (attentionItems.length) {
    return attentionItems[0].execution_group_id || null;
  }
  const groups = safeArray(runDetails?.governed_external_execution_groups);
  return groups.length ? groups[0].execution_group_id || null : null;
}

export function filterAttemptsForGroup(runDetails, executionGroupId) {
  if (!executionGroupId) {
    return [];
  }
  return safeArray(runDetails?.governed_external_calls).filter(
    (attempt) => attempt.execution_group_id === executionGroupId,
  );
}

export function filterEventsForAttempt(runDetails, externalCallId) {
  if (!externalCallId) {
    return [];
  }
  return safeArray(runDetails?.governed_external_call_events).filter(
    (event) => event.external_call_id === externalCallId,
  );
}

export function resolveStickySelections(runDetails, preferredGroupId = null, preferredAttemptId = null) {
  const groups = safeArray(runDetails?.governed_external_execution_groups);
  const attempts = safeArray(runDetails?.governed_external_calls);
  const normalizedGroupId = String(preferredGroupId || "").trim();
  const normalizedAttemptId = String(preferredAttemptId || "").trim();
  const preferredAttempt = normalizedAttemptId
    ? attempts.find((attempt) => attempt.external_call_id === normalizedAttemptId)
    : null;
  const preferredAttemptGroupId = preferredAttempt?.execution_group_id || null;
  const preferredAttemptGroupIsValid = preferredAttemptGroupId
    ? groups.some((group) => group.execution_group_id === preferredAttemptGroupId)
    : false;
  const preferredGroupIsValid = normalizedGroupId
    ? groups.some((group) => group.execution_group_id === normalizedGroupId)
    : false;

  const selectedResolvedGroupId = preferredAttemptGroupIsValid
    ? preferredAttemptGroupId
    : preferredGroupIsValid
      ? normalizedGroupId
      : defaultSelectedGroupId(runDetails);

  const selectedResolvedAttemptId = preferredAttemptGroupIsValid
    && preferredAttemptGroupId === selectedResolvedGroupId
      ? preferredAttempt.external_call_id
      : null;

  return {
    selectedGroupId: selectedResolvedGroupId || null,
    selectedAttemptId: selectedResolvedAttemptId,
  };
}

function renderLookup(runId) {
  return `
    <section class="hero">
      <div>
        <p class="eyebrow">Governed External Control Room</p>
        <h1>Read-only run evidence shell</h1>
        <p class="lede">Load one run by <code>run_id</code>, see summary and attention first, then inspect grouped governed executions and per-attempt detail.</p>
      </div>
      <form class="run-lookup" id="run-lookup-form">
        <label for="run-id-input">Run ID</label>
        <div class="run-lookup__row">
          <input id="run-id-input" name="run_id" type="text" value="${escapeHtml(runId)}" placeholder="run_..." autocomplete="off" />
          <button type="submit">Load run</button>
        </div>
      </form>
    </section>
  `;
}

export function renderRecentRunsRail(recentRuns, activeRunId, recentRunsStatus = "idle") {
  const runs = safeArray(recentRuns);
  const normalizedActiveRunId = String(activeRunId || "").trim();

  let body = '<article class="empty-card">Recent runs will appear here once the read-only snapshot is available.</article>';
  if (recentRunsStatus === "loading") {
    body = '<article class="empty-card">Loading recent runs from the read-only operator snapshot.</article>';
  } else if (recentRunsStatus === "error") {
    body = '<article class="empty-card">Recent runs are temporarily unavailable.</article>';
  } else if (runs.length) {
    body = `
      <div class="recent-run-list">
        ${runs.map((run) => `
          <button
            type="button"
            class="recent-run-chip ${run.id === normalizedActiveRunId ? "recent-run-chip--active" : ""}"
            data-recent-run-id="${escapeHtml(run.id)}"
          >
            <span class="recent-run-chip__id">${escapeHtml(run.id)}</span>
            <span class="recent-run-chip__meta">${escapeHtml(statusLabel(run.status))} | ${escapeHtml(run.timestamp)}</span>
            ${run.taskTitle ? `<span class="recent-run-chip__title">${escapeHtml(run.taskTitle)}</span>` : ""}
          </button>
        `).join("")}
      </div>
    `;
  } else if (recentRunsStatus === "loaded") {
    body = '<article class="empty-card">No recent runs are available yet.</article>';
  }

  return `
    <section class="panel panel--recent-runs">
      <div class="panel__header">
        <h2>Recent Runs</h2>
        <span>${escapeHtml(runs.length)}</span>
      </div>
      <p class="panel__lede">Pick a recent run to load it into the control room, or keep using the manual <code>run_id</code> lookup.</p>
      ${body}
    </section>
  `;
}

export function renderRecentActivity(summary, recentRunsStatus = "idle") {
  if (recentRunsStatus === "loading") {
    return `
      <section class="panel panel--recent-activity">
        <div class="panel__header">
          <h2>Recent Activity</h2>
        </div>
        <article class="empty-card">Loading lightweight run signals from recent activity.</article>
      </section>
    `;
  }

  if (recentRunsStatus === "error") {
    return `
      <section class="panel panel--recent-activity">
        <div class="panel__header">
          <h2>Recent Activity</h2>
        </div>
        <article class="empty-card">Recent activity signals are temporarily unavailable.</article>
      </section>
    `;
  }

  const activity = summary || summarizeRecentActivity([]);
  const items = [
    ["Runs in window", activity.totalRuns],
    ["Runs with failures", activity.runsWithFailures],
    ["Budget-stopped runs", activity.runsWithBudgetStops],
    ["Proof-missing runs", activity.runsWithProofMissing],
    ["Governed API runs", activity.runsWithGovernedApiExecution],
  ];

  return `
    <section class="panel panel--recent-activity">
      <div class="panel__header">
        <h2>Recent Activity</h2>
      </div>
      <p class="panel__lede">Lightweight signals from the current recent-run window. These are operator cues, not analytics or forecasts.</p>
      <div class="activity-signal-grid">
        ${items.map(([label, value]) => `
          <article class="activity-signal">
            <span>${escapeHtml(label)}</span>
            <strong>${escapeHtml(value)}</strong>
          </article>
        `).join("")}
      </div>
      <ul class="activity-hints">
        ${safeArray(activity.hints).map((hint) => `<li>${escapeHtml(hint)}</li>`).join("")}
      </ul>
    </section>
  `;
}

export function renderSystemHealth(summary, recentRunsStatus = "idle") {
  if (recentRunsStatus === "loading") {
    return `
      <section class="panel panel--system-health">
        <div class="panel__header">
          <h2>System Health</h2>
        </div>
        <article class="empty-card">Loading recent system health signals.</article>
      </section>
    `;
  }

  const health = summarizeSystemHealth(summary);

  return `
    <section class="panel panel--system-health">
      <div class="panel__header">
        <h2>System Health</h2>
      </div>
      <p class="panel__lede">A compact signal from the recent-run window. This is a read-only operating cue, not a system verdict.</p>
      <article class="health-callout health-callout--${escapeHtml(health.tone)}">
        <span class="health-pill health-pill--${escapeHtml(health.tone)}">${escapeHtml(health.label)}</span>
        <p class="health-callout__explanation">${escapeHtml(health.explanation)}</p>
      </article>
    </section>
  `;
}

export function renderRunComparison(runDetails, recentRuns) {
  const comparison = compareLoadedRunToRecentWindow(runDetails, recentRuns);
  if (!comparison) {
    return "";
  }

  return `
    <section class="panel panel--run-context">
      <div class="panel__header">
        <h2>Run Context</h2>
      </div>
      <p class="panel__lede">Small comparison cues for the currently loaded run against the recent-run window.</p>
      <article class="context-callout">
        <p class="context-callout__headline">${escapeHtml(comparison.headline)}</p>
        ${comparison.cues.length ? `
          <ul class="context-callout__list">
            ${comparison.cues.map((cue) => `<li>${escapeHtml(cue)}</li>`).join("")}
          </ul>
        ` : ""}
      </article>
    </section>
  `;
}

function renderRunSummary(summary) {
  const items = [
    ["total_execution_groups", summary.total_execution_groups ?? 0],
    ["total_attempts", summary.total_attempts ?? 0],
    ["governed_api_execution_count", summary.governed_api_execution_count ?? 0],
    ["blocked_execution_count", summary.blocked_execution_count ?? 0],
    ["pre_observation_block_count", summary.pre_observation_block_count ?? 0],
    ["final_success_count", summary.final_success_count ?? 0],
    ["final_failed_count", summary.final_failed_count ?? 0],
    ["final_stopped_count", summary.final_stopped_count ?? 0],
    ["final_budget_stopped_count", summary.final_budget_stopped_count ?? 0],
    ["final_proof_missing_count", summary.final_proof_missing_count ?? 0],
    ["final_proved_count", summary.final_proved_count ?? 0],
    ["final_trusted_reconciled_count", summary.final_trusted_reconciled_count ?? 0],
    ["final_proof_captured_not_reconciled_count", summary.final_proof_captured_not_reconciled_count ?? 0],
    ["final_reconciliation_failed_count", summary.final_reconciliation_failed_count ?? 0],
    ["final_claimed_only_count", summary.final_claimed_only_count ?? 0],
    ["final_claim_missing_count", summary.final_claim_missing_count ?? 0],
  ];

  return `
    <section class="panel panel--summary">
      <div class="panel__header">
        <h2>Run Summary</h2>
      </div>
      <p class="panel__lede">Read-derived sensors from persisted governed execution evidence. Open the small help affordances for what each metric means and what to inspect next.</p>
      <div class="stats-grid control-room-stats">
        ${items.map(([metricKey, value]) => renderStat(metricKey, value)).join("")}
      </div>
    </section>
  `;
}

function renderPreObservationBlocks(blocks) {
  return blocks.map((block) => `
    <article
      class="evidence-card evidence-card--warning evidence-card--priority-high"
      data-attention-kind="pre_execution_block"
      data-priority-label="High"
    >
      <div class="evidence-card__heading">
        <div class="evidence-card__title">Pre-observation block</div>
        <span class="priority-pill priority-pill--high">High</span>
      </div>
      <p>${escapeHtml(explainPreObservationBlock(block))}</p>
      <p class="operator-suggestion"><strong>Suggested next step:</strong> ${escapeHtml(suggestNextStepForPreObservationBlock(block))}</p>
      <div class="evidence-card__meta">Blocked before governed external observation began.</div>
      <ul>
        ${renderKeyValue("Occurred", block.occurred_at || "-")}
        ${renderKeyValue("Stage", block.block_stage || "-")}
        ${renderKeyValue("Reason", block.block_reason_code || "-")}
        ${renderKeyValue("Task packet", block.task_packet_id || "-")}
      </ul>
    </article>
  `).join("");
}

function renderAttentionItems(items, preExecutionBlocks) {
  if (!items.length && !preExecutionBlocks.length) {
    return `<article class="empty-card">No governed execution items currently need operator attention.</article>`;
  }

  const prioritizedEntries = prioritizeAttentionEntries(items, preExecutionBlocks);

  return `
    <div class="stack">
      ${prioritizedEntries.map((entry) => {
        if (entry.kind === "pre_execution_block") {
          return renderPreObservationBlocks([entry.payload]);
        }
        const item = entry.payload;
        return `
          <article
            class="evidence-card evidence-card--warning evidence-card--priority-${escapeHtml(entry.priority.tone)}"
            data-attention-kind="attention_item"
            data-priority-label="${escapeHtml(entry.priority.label)}"
          >
            <div class="evidence-card__heading">
              <div class="evidence-card__title">${escapeHtml(item.execution_group_id)}</div>
              <span class="priority-pill priority-pill--${escapeHtml(entry.priority.tone)}">${escapeHtml(entry.priority.label)}</span>
            </div>
            <p>${escapeHtml(explainAttentionItem(item))}</p>
            <p class="operator-suggestion"><strong>Suggested next step:</strong> ${escapeHtml(suggestNextStepForAttentionItem(item))}</p>
            <div class="evidence-card__meta">Attention is derived from the final grouped outcome and proof state already persisted for this run.</div>
            <ul>
              ${renderKeyValue("Final attempt", item.final_attempt_number)}
              ${renderKeyValue("Execution path", executionPathLabel(item.execution_path_classification))}
              ${renderKeyValue("Final outcome", statusLabel(item.final_outcome_status))}
              ${renderKeyValue("Budget stop", item.final_budget_stop_reason_code || "-")}
              ${renderKeyValue("Attention", item.attention_reason)}
              ${renderOptionalKeyValue("Trust", trustStatusLabel(item.final_trust_status))}
              ${renderOptionalKeyValue("Reconciliation", reconciliationStateLabel(item.final_reconciliation_state))}
              ${renderOptionalKeyValue("Reconciliation reason", item.final_reconciliation_reason_code)}
              ${renderOptionalKeyValue("Reconciliation checked", item.final_reconciliation_checked_at)}
            </ul>
            ${renderExecutionPathBadge(item.execution_path_classification)}
            ${renderVerificationBadges({
              proofStatus: item.final_proof_status,
              reconciliationState: item.final_reconciliation_state,
              trustStatus: item.final_trust_status,
            })}
          </article>
        `;
      }).join("")}
    </div>
  `;
}

function renderExecutionGroups(groups, activeGroupId) {
  if (!groups.length) {
    return `<article class="empty-card">No governed external execution groups are recorded for this run.</article>`;
  }

  return `
    <div class="group-list">
      ${groups.map((group) => `
        <button
          type="button"
          class="group-card ${group.execution_group_id === activeGroupId ? "group-card--selected" : ""}"
          data-group-id="${escapeHtml(group.execution_group_id)}"
        >
          <div class="group-card__title">${escapeHtml(group.execution_group_id)}</div>
          <ul>
            ${renderKeyValue("Attempts", group.total_attempts)}
            ${renderKeyValue("Execution path", executionPathLabel(group.execution_path_classification))}
            ${renderKeyValue("Final outcome", statusLabel(group.final_outcome_status))}
            ${renderKeyValue("Budget stop", group.final_budget_stop_enforced ? (group.final_budget_stop_reason_code || "enforced") : "no")}
            ${renderKeyValue("Final call", group.final_external_call_id)}
            ${renderOptionalKeyValue("Trust", trustStatusLabel(group.final_trust_status))}
            ${renderOptionalKeyValue("Reconciliation", reconciliationStateLabel(group.final_reconciliation_state))}
            ${renderOptionalKeyValue("Reconciliation reason", group.final_reconciliation_reason_code)}
            ${renderOptionalKeyValue("Reconciliation checked", group.final_reconciliation_checked_at)}
          </ul>
          ${renderExecutionPathBadge(group.execution_path_classification)}
          ${renderVerificationBadges({
            proofStatus: group.final_proof_status,
            reconciliationState: group.final_reconciliation_state,
            trustStatus: group.final_trust_status,
          })}
        </button>
      `).join("")}
    </div>
  `;
}

function renderAttemptEvents(events, selectedAttemptId) {
  if (!selectedAttemptId) {
    return "";
  }
  if (!events.length) {
    return `
      <section class="attempt-events">
        <div class="attempt-events__header">Attempt Event Evidence</div>
        <article class="empty-card">No persisted governed external events were recorded for ${escapeHtml(selectedAttemptId)}.</article>
      </section>
    `;
  }

  return `
    <section class="attempt-events">
      <div class="attempt-events__header">Attempt Event Evidence</div>
      <div class="stack">
        ${events.map((event) => `
          <article class="evidence-card">
            <div class="evidence-card__title">${escapeHtml(event.event_type)}</div>
            <ul>
              ${renderKeyValue("Occurred", event.occurred_at || "-")}
              ${renderKeyValue("Status", event.status || "-")}
              ${renderKeyValue("Reason", event.reason_code || "-")}
            </ul>
          </article>
        `).join("")}
      </div>
    </section>
  `;
}

function renderAttempts(attempts, activeGroupId, activeAttemptId, attemptEvents) {
  if (!activeGroupId) {
    return `<article class="empty-card">Select an execution group to inspect its attempts.</article>`;
  }
  if (!attempts.length) {
    return `<article class="empty-card">No attempts recorded for ${escapeHtml(activeGroupId)}.</article>`;
  }

  return `
    <div class="attempt-detail">
      <div class="attempt-detail__header">Showing attempts for ${escapeHtml(activeGroupId)}</div>
      <div class="attempt-table-wrap">
        <table class="attempt-table">
          <thead>
            <tr>
              <th>Attempt</th>
              <th>External call</th>
              <th>Outcome</th>
              <th>Execution path</th>
              <th>Budget stop</th>
              <th>Trust</th>
              <th>Provider request</th>
            </tr>
          </thead>
          <tbody>
            ${attempts.map((attempt) => `
              <tr class="${attempt.external_call_id === activeAttemptId ? "attempt-row--selected" : ""}">
                <td>${escapeHtml(attempt.attempt_number)}</td>
                <td>
                  <button
                    type="button"
                    class="attempt-link ${attempt.external_call_id === activeAttemptId ? "attempt-link--selected" : ""}"
                    data-external-call-id="${escapeHtml(attempt.external_call_id)}"
                  >
                    ${escapeHtml(attempt.external_call_id)}
                  </button>
                 </td>
                 <td>${escapeHtml(statusLabel(attempt.outcome_status))}</td>
                 <td>${renderExecutionPathBadge(attempt.execution_path_classification)}</td>
                 <td>${escapeHtml(attempt.budget_stop_reason_code || "-")}</td>
                 <td>${renderVerificationBadges({
                   claimStatus: attempt.claim_status,
                   proofStatus: attempt.proof_status,
                   providerRequestId: attempt.provider_request_id,
                   reconciliationState: attempt.reconciliation_state,
                   trustStatus: attempt.trust_status,
                 })}</td>
                <td>${escapeHtml(attempt.provider_request_id || "-")}</td>
              </tr>
            `).join("")}
          </tbody>
        </table>
      </div>
      ${renderAttemptEvents(attemptEvents, activeAttemptId)}
    </div>
  `;
}

export function renderControlRoom(
  runDetails,
  activeGroupId = defaultSelectedGroupId(runDetails),
  activeAttemptId = null,
  recentRuns = currentRecentRuns,
) {
  const summary = runDetails?.governed_external_run_summary || {};
  const attentionItems = safeArray(runDetails?.governed_external_attention_items);
  const preExecutionBlocks = safeArray(runDetails?.governed_pre_execution_blocks);
  const executionGroups = safeArray(runDetails?.governed_external_execution_groups);
  const attempts = filterAttemptsForGroup(runDetails, activeGroupId);
  const attemptEvents = filterEventsForAttempt(runDetails, activeAttemptId);
  const run = runDetails?.run || {};
  const task = runDetails?.task || {};

  return `
    <main class="shell control-room-shell">
      ${renderLookup(run.id || currentRunId)}
      ${renderViewStatusStrip("loaded", run.id || currentRunId)}
      ${renderRecentRunsRail(recentRuns, run.id || currentRunId, currentRecentRunsStatus)}
      ${renderRecentActivity(currentRecentActivity, currentRecentRunsStatus)}
      ${renderSystemHealth(currentRecentActivity, currentRecentRunsStatus)}
      ${renderRunComparison(runDetails, recentRuns)}
    <section class="panel panel--run">
      <div class="panel__header">
        <h2>Run</h2>
        <span>${escapeHtml(run.id || "-")}</span>
        </div>
        <div class="stack">
          <article class="evidence-card">
            <div class="evidence-card__title">${escapeHtml(task.title || "Governed external run")}</div>
            <ul>
              ${renderKeyValue("Run status", statusLabel(run.status))}
              ${renderKeyValue("Task ID", run.task_id || task.id || "-")}
              ${renderKeyValue("Project", run.project_name || task.project_name || "-")}
              ${renderKeyValue("Stop reason", run.stop_reason || "-")}
            </ul>
          </article>
        </div>
      </section>
      ${renderRunSummary(summary)}
      <section class="panel panel--attention">
        <div class="panel__header">
          <h2>Attention</h2>
          <span>${escapeHtml(attentionItems.length + preExecutionBlocks.length)}</span>
        </div>
        ${renderAttentionItems(attentionItems, preExecutionBlocks)}
      </section>
      <section class="panel panel--groups">
        <div class="panel__header">
          <h2>Execution Groups</h2>
          <span>${escapeHtml(executionGroups.length)}</span>
        </div>
        ${renderExecutionGroups(executionGroups, activeGroupId)}
      </section>
      <section class="panel panel--detail">
        <div class="panel__header">
          <h2>Attempt Detail</h2>
          <span>${escapeHtml(activeAttemptId || activeGroupId || "No group selected")}</span>
        </div>
        ${renderAttempts(attempts, activeGroupId, activeAttemptId, attemptEvents)}
      </section>
    </main>
  `;
}

function renderEmpty(runId = "") {
  if (!appRoot) {
    return;
  }
  appRoot.innerHTML = `
    <main class="shell control-room-shell">
      ${renderLookup(runId)}
      ${renderViewStatusStrip("empty", runId)}
      ${renderRecentRunsRail(currentRecentRuns, runId, currentRecentRunsStatus)}
      ${renderRecentActivity(currentRecentActivity, currentRecentRunsStatus)}
      ${renderSystemHealth(currentRecentActivity, currentRecentRunsStatus)}
      <section class="panel">
        <div class="stack">
          <article class="empty-card">Enter a run id to inspect governed external evidence.</article>
        </div>
      </section>
    </main>
  `;
}

function renderError(runId, message) {
  if (!appRoot) {
    return;
  }
  appRoot.innerHTML = `
    <main class="shell control-room-shell">
      ${renderLookup(runId)}
      ${renderViewStatusStrip("error", runId)}
      ${renderRecentRunsRail(currentRecentRuns, runId, currentRecentRunsStatus)}
      ${renderRecentActivity(currentRecentActivity, currentRecentRunsStatus)}
      ${renderSystemHealth(currentRecentActivity, currentRecentRunsStatus)}
      <section class="panel">
        <div class="stack">
          <article class="evidence-card evidence-card--warning">
            <div class="evidence-card__title">Run details unavailable</div>
            <ul>${renderKeyValue("Error", message)}</ul>
          </article>
        </div>
      </section>
    </main>
  `;
}

function bindControls() {
  if (!appRoot) {
    return;
  }
  const form = document.querySelector("#run-lookup-form");
  if (form) {
    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      const formData = new FormData(form);
      const runId = String(formData.get("run_id") || "").trim();
      await loadRun(runId, { preserveSelection: false });
    });
  }

  document.querySelectorAll("[data-group-id]").forEach((button) => {
    button.addEventListener("click", () => {
      selectedGroupId = button.getAttribute("data-group-id");
      selectedAttemptId = null;
      writeStickyControlRoomContext({
        runId: currentRunId,
        selectedGroupId,
        selectedAttemptId,
      });
      if (appRoot && currentRunDetails) {
        appRoot.innerHTML = renderControlRoom(currentRunDetails, selectedGroupId, selectedAttemptId);
        bindControls();
      }
    });
  });

  document.querySelectorAll("[data-external-call-id]").forEach((button) => {
    button.addEventListener("click", () => {
      selectedAttemptId = button.getAttribute("data-external-call-id");
      writeStickyControlRoomContext({
        runId: currentRunId,
        selectedGroupId,
        selectedAttemptId,
      });
      if (appRoot && currentRunDetails) {
        appRoot.innerHTML = renderControlRoom(currentRunDetails, selectedGroupId, selectedAttemptId);
        bindControls();
      }
    });
  });

  document.querySelectorAll("[data-recent-run-id]").forEach((button) => {
    button.addEventListener("click", async () => {
      const runId = button.getAttribute("data-recent-run-id");
      await handleRecentRunSelection(runId, loadRun);
    });
  });
}

function updateUrl(runId) {
  if (typeof window === "undefined") {
    return;
  }
  const url = new URL(window.location.href);
  if (runId) {
    url.searchParams.set("run_id", runId);
  } else {
    url.searchParams.delete("run_id");
  }
  window.history.replaceState({}, "", url);
}

export async function fetchRunDetails(runId, fetchImpl = globalThis.fetch) {
  const normalizedRunId = String(runId || "").trim();
  if (!normalizedRunId) {
    throw new Error("run_id is required.");
  }
  const response = await fetchImpl(`/api/run-details?run_id=${encodeURIComponent(normalizedRunId)}`, {
    cache: "no-store",
  });
  if (!response.ok) {
    let errorMessage = `Run details request failed with ${response.status}`;
    try {
      const payload = await response.json();
      if (payload?.error) {
        errorMessage = payload.error;
      }
    } catch {
      // Ignore JSON parsing failures and fall back to the HTTP error.
    }
    throw new Error(errorMessage);
  }
  return response.json();
}

async function loadRun(runId, { preserveSelection } = { preserveSelection: false }) {
  const normalizedRunId = String(runId || "").trim();
  currentRunId = normalizedRunId;
  updateUrl(normalizedRunId);
  if (!normalizedRunId) {
    currentRunDetails = null;
    selectedGroupId = null;
    selectedAttemptId = null;
    writeStickyControlRoomContext({ runId: "", selectedGroupId: null, selectedAttemptId: null });
    renderEmpty("");
    bindControls();
    return;
  }

  try {
    if (appRoot) {
      appRoot.innerHTML = `
        <main class="shell control-room-shell">
          ${renderLookup(normalizedRunId)}
          ${renderViewStatusStrip("loading", normalizedRunId)}
          ${renderRecentRunsRail(currentRecentRuns, normalizedRunId, currentRecentRunsStatus)}
          <section class="panel">
            <div class="stack">
              <article class="empty-card">Loading persisted governed evidence for ${escapeHtml(normalizedRunId)}.</article>
            </div>
          </section>
        </main>
      `;
      bindControls();
    }
    const details = await fetchRunDetails(normalizedRunId);
    currentRunDetails = details;
    const resolvedSelections = resolveStickySelections(
      details,
      preserveSelection ? selectedGroupId : null,
      preserveSelection ? selectedAttemptId : null,
    );
    selectedGroupId = resolvedSelections.selectedGroupId;
    selectedAttemptId = resolvedSelections.selectedAttemptId;
    writeStickyControlRoomContext({
      runId: normalizedRunId,
      selectedGroupId,
      selectedAttemptId,
    });
    if (appRoot) {
      appRoot.innerHTML = renderControlRoom(details, selectedGroupId, selectedAttemptId);
      bindControls();
    }
  } catch (error) {
    currentRunDetails = null;
    selectedGroupId = null;
    selectedAttemptId = null;
    renderError(normalizedRunId, error instanceof Error ? error.message : String(error));
    bindControls();
  }
}

async function loadRecentRuns() {
  currentRecentRunsStatus = "loading";
  if (!currentRunDetails && !currentRunId) {
    renderEmpty("");
    bindControls();
  }

  try {
    currentRecentRuns = await fetchRecentRuns();
    currentRecentActivity = summarizeRecentActivity(currentRecentRuns);
    currentRecentRunsStatus = "loaded";
  } catch {
    currentRecentRuns = [];
    currentRecentActivity = summarizeRecentActivity([]);
    currentRecentRunsStatus = "error";
  }

  if (appRoot) {
    if (currentRunDetails) {
      appRoot.innerHTML = renderControlRoom(currentRunDetails, selectedGroupId, selectedAttemptId);
    } else if (!currentRunId) {
      renderEmpty("");
    }
    bindControls();
  }
}

export function initializeControlRoom() {
  if (!appRoot) {
    return;
  }
  currentRecentRunsStatus = "loading";
  loadRecentRuns();
  if (initialRunId) {
    loadRun(initialRunId, { preserveSelection: true });
    return;
  }
  renderEmpty("");
  bindControls();
}

if (appRoot) {
  initializeControlRoom();
}

