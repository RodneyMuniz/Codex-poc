const appRoot = typeof document !== "undefined" ? document.querySelector("#app") : null;

const initialQuery =
  typeof window !== "undefined" ? new URLSearchParams(window.location.search || "") : new URLSearchParams();

const state = {
  activeProject: (initialQuery.get("project") || "all").trim() || "all",
  snapshot: null,
  snapshotStatus: "loading",
  snapshotError: "",
  selectedMilestoneId: (initialQuery.get("milestone_id") || "").trim(),
  selectedTaskId: (initialQuery.get("task_id") || "").trim(),
  taskDetails: null,
  taskStatus: "idle",
  taskError: "",
  selectedRunId: (initialQuery.get("run_id") || "").trim(),
  runDetails: null,
  runStatus: "idle",
  runError: "",
  snapshotRequestToken: 0,
  taskRequestToken: 0,
  runRequestToken: 0,
};

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function safeArray(value) {
  return Array.isArray(value) ? value : [];
}

function countValue(value) {
  return Number.isFinite(Number(value)) ? Number(value) : 0;
}

function statusLabel(value) {
  return String(value || "unknown")
    .replaceAll(/[_-]+/g, " ")
    .replace(/\b\w/g, (character) => character.toUpperCase());
}

function formatTimestamp(value) {
  if (!value) {
    return "Not recorded";
  }
  return escapeHtml(value);
}

function latestExecutionBadge(executionSummary) {
  if (!executionSummary) {
    return "No run evidence yet";
  }
  const pieces = [];
  if (executionSummary.latest_execution_path_classification) {
    pieces.push(statusLabel(executionSummary.latest_execution_path_classification));
  }
  if (executionSummary.latest_outcome_status) {
    pieces.push(statusLabel(executionSummary.latest_outcome_status));
  }
  if (executionSummary.latest_proof_status) {
    pieces.push(`Proof ${statusLabel(executionSummary.latest_proof_status)}`);
  }
  return pieces.length ? pieces.join(" | ") : "No run evidence yet";
}

function trustCategoryForExecutionSummary(executionSummary) {
  if (!executionSummary) {
    return "";
  }
  const reconciliationState = String(executionSummary.latest_reconciliation_state || "").trim();
  const trustStatus = String(executionSummary.latest_trust_status || "").trim();
  if (reconciliationState === "reconciliation_failed" || trustStatus === "reconciliation_failed") {
    return "reconciliation_failed";
  }
  if (reconciliationState === "reconciliation_pending") {
    return "reconciliation_pending";
  }
  if (trustStatus === "proof_captured_not_reconciled") {
    return "proof_captured_not_reconciled";
  }
  return "";
}

function trustToneForExecutionSummary(executionSummary) {
  const category = trustCategoryForExecutionSummary(executionSummary);
  if (category === "reconciliation_failed") {
    return "warning";
  }
  if (category === "reconciliation_pending" || category === "proof_captured_not_reconciled") {
    return "strong";
  }
  if (String(executionSummary?.latest_trust_status || "").trim() === "trusted_reconciled") {
    return "success";
  }
  return "muted";
}

function trustIssueLabel(category) {
  if (category === "reconciliation_failed") {
    return "Reconciliation failed";
  }
  if (category === "reconciliation_pending") {
    return "Reconciliation pending";
  }
  if (category === "proof_captured_not_reconciled") {
    return "Proof captured, not reconciled";
  }
  return "Trust follow-up needed";
}

function badgeToneForTrustTone(tone) {
  if (tone === "risk") {
    return "warning";
  }
  if (tone === "warning") {
    return "strong";
  }
  if (tone === "success") {
    return "success";
  }
  return "muted";
}

function summarizeBoardTrust(card) {
  const trustSummary = card?.trust_summary || {};
  const latestExecution = card?.latest_execution_summary || {};
  const followUpCount = countValue(trustSummary.trust_followup_count);
  const highestPriorityIssue = String(trustSummary.highest_priority_trust_issue || "").trim();
  const latestTrustStatus = String(trustSummary.latest_trust_status || latestExecution.latest_trust_status || "").trim();
  const latestReconciliationState = String(
    trustSummary.latest_reconciliation_state || latestExecution.latest_reconciliation_state || "",
  ).trim();
  const linkedRunCount = countValue(card?.linked_run_count);

  if (followUpCount > 0) {
    const issueLabel = trustIssueLabel(highestPriorityIssue);
    return {
      tone: highestPriorityIssue === "reconciliation_failed" ? "risk" : "warning",
      bannerLabel: "Trust follow-up needed",
      detail: `${issueLabel} on ${followUpCount} linked run(s)`,
      badgeLabel: issueLabel,
    };
  }

  if (latestTrustStatus === "trusted_reconciled") {
    return {
      tone: "success",
      bannerLabel: "Trust clean",
      detail: "Latest linked run is trusted and reconciled.",
      badgeLabel: statusLabel(latestTrustStatus),
    };
  }

  if (latestTrustStatus === "claimed_only") {
    return {
      tone: "muted",
      bannerLabel: "Claimed only",
      detail: "Latest linked run does not yet have provider proof.",
      badgeLabel: statusLabel(latestTrustStatus),
    };
  }

  if (latestTrustStatus || latestReconciliationState) {
    return {
      tone: latestReconciliationState === "reconciled" ? "success" : "muted",
      bannerLabel: "Trust recorded",
      detail: latestTrustStatus
        ? `Latest trust state is ${statusLabel(latestTrustStatus)}.`
        : `Latest reconciliation state is ${statusLabel(latestReconciliationState)}.`,
      badgeLabel: latestTrustStatus
        ? statusLabel(latestTrustStatus)
        : statusLabel(latestReconciliationState),
    };
  }

  if (linkedRunCount > 0) {
    return {
      tone: "muted",
      bannerLabel: "No trust follow-up visible",
      detail: "Linked governed runs are present without an active trust follow-up signal.",
      badgeLabel: "No follow-up visible",
    };
  }

  return {
    tone: "muted",
    bannerLabel: "No trust evidence yet",
    detail: "This task does not have linked governed runs yet.",
    badgeLabel: "No evidence yet",
  };
}

export function summarizeTaskTrust(taskDetails) {
  const linkedRuns = safeArray(taskDetails?.linked_runs);
  const latestRun = linkedRuns[0] || null;
  const latestExecution =
    taskDetails?.latest_execution_summary ||
    (latestRun && latestRun.execution_summary) ||
    {};

  let concern = null;
  for (let index = 0; index < linkedRuns.length; index += 1) {
    const run = linkedRuns[index];
    const executionSummary = run?.execution_summary || {};
    const category = trustCategoryForExecutionSummary(executionSummary);
    if (!category) {
      continue;
    }
    const rank =
      category === "reconciliation_failed"
        ? 0
        : category === "reconciliation_pending"
          ? 1
          : 2;
    if (!concern || rank < concern.rank) {
      concern = {
        runId: run.id || "",
        category,
        rank,
        executionSummary,
        index,
      };
    }
  }

  return {
    latestRunId: latestRun?.id || "",
    latestTrustStatus: String(latestExecution.latest_trust_status || "").trim(),
    latestReconciliationState: String(latestExecution.latest_reconciliation_state || "").trim(),
    latestProofStatus: String(latestExecution.latest_proof_status || "").trim(),
    hasOutstandingFollowUp: Boolean(concern),
    followUpRunId: concern?.runId || "",
    followUpCategory: concern?.category || "",
    concernIsLatestRun: Boolean(concern && concern.runId && concern.runId === latestRun?.id),
  };
}

function renderBadge(label, value, tone = "default") {
  const toneClass =
    tone === "strong"
      ? "badge badge--strong"
      : tone === "success"
        ? "badge badge--success"
        : tone === "warning"
          ? "badge badge--warning"
          : tone === "muted"
            ? "badge badge--muted"
            : "badge";
  return `<li class="${toneClass}"><strong>${escapeHtml(label)}</strong><span>${escapeHtml(value)}</span></li>`;
}

function renderSummaryCard(label, value, meta, tone = "default") {
  const toneClass =
    tone === "success"
      ? "stat-card stat-card--success"
      : tone === "warning"
        ? "stat-card stat-card--warning"
        : "stat-card";
  return `
    <article class="${toneClass}">
      <div class="stat-card__top">
        <span class="stat-card__label">${escapeHtml(label)}</span>
      </div>
      <strong class="stat-card__value">${escapeHtml(value)}</strong>
      <span class="task-summary-card__meta">${escapeHtml(meta)}</span>
    </article>
  `;
}

function renderTaskHealthCallout(healthSummary) {
  if (!healthSummary) {
    return `
      <div class="context-callout">
        <p class="context-callout__headline">Latest health</p>
        <p class="health-callout__explanation">No governed run health signal has been recorded for this task yet.</p>
      </div>
    `;
  }

  const hasAttention = Boolean(healthSummary.has_attention);
  const label = hasAttention ? "Needs attention" : "Stable";
  const toneClass = hasAttention ? "health-callout health-callout--degraded" : "health-callout health-callout--healthy";
  const pillClass = hasAttention ? "health-pill health-pill--degraded" : "health-pill health-pill--healthy";
  const explanation = hasAttention
    ? "The latest linked run still carries attention signals that deserve review before this task is considered clean."
    : "The latest linked run looks clean, with successful governed execution and no active attention signal.";

  return `
    <div class="${toneClass}">
      <span class="${pillClass}">${escapeHtml(label)}</span>
      <p class="health-callout__explanation">${escapeHtml(explanation)}</p>
    </div>
  `;
}

function renderTaskTrustCallout(taskDetails) {
  const trustSummary = summarizeTaskTrust(taskDetails);
  const linkedRuns = safeArray(taskDetails?.linked_runs);

  if (!linkedRuns.length) {
    return `
      <div class="trust-callout trust-callout--muted">
        <span class="trust-pill trust-pill--muted">No trust evidence yet</span>
        <p class="trust-callout__explanation">This task does not have any linked governed runs yet, so there is no trust follow-up to review.</p>
      </div>
    `;
  }

  const latestTrustLabel = trustSummary.latestTrustStatus
    ? statusLabel(trustSummary.latestTrustStatus)
    : "Not recorded";
  const latestReconciliationLabel = trustSummary.latestReconciliationState
    ? statusLabel(trustSummary.latestReconciliationState)
    : "Not recorded";

  let toneClass = "trust-callout trust-callout--muted";
  let pillClass = "trust-pill trust-pill--muted";
  let headline = "Trust state recorded";
  let explanation =
    "The latest linked run has trust fields recorded, and no active trust follow-up is currently visible in this task view.";
  let inspectNext = "Inspect the linked run evidence only if you need deeper control-room audit detail.";

  if (trustSummary.followUpCategory === "reconciliation_failed") {
    toneClass = "trust-callout trust-callout--risk";
    pillClass = "trust-pill trust-pill--risk";
    headline = trustSummary.concernIsLatestRun
      ? "Reconciliation failed on the latest run"
      : "Trust follow-up needed on an earlier run";
    explanation = trustSummary.concernIsLatestRun
      ? `Run ${trustSummary.followUpRunId} reached provider proof, but reconciliation failed and still needs review.`
      : `Run ${trustSummary.followUpRunId} still has a failed reconciliation record, even though newer runs exist for this task.`;
    inspectNext = `Inspect run ${trustSummary.followUpRunId} next and review its reconciliation reason in the full run evidence view.`;
  } else if (trustSummary.followUpCategory === "reconciliation_pending") {
    toneClass = "trust-callout trust-callout--degraded";
    pillClass = "trust-pill trust-pill--degraded";
    headline = trustSummary.concernIsLatestRun
      ? "Reconciliation pending on the latest run"
      : "Trust follow-up still pending on an earlier run";
    explanation = `Run ${trustSummary.followUpRunId} has provider proof captured and is still waiting on reconciliation confirmation.`;
    inspectNext = `Inspect run ${trustSummary.followUpRunId} next and review the latest reconciliation check before treating it as trusted.`;
  } else if (trustSummary.followUpCategory === "proof_captured_not_reconciled") {
    toneClass = "trust-callout trust-callout--degraded";
    pillClass = "trust-pill trust-pill--degraded";
    headline = trustSummary.concernIsLatestRun
      ? "Trust follow-up needed"
      : "An earlier run still needs trust follow-up";
    explanation = `Run ${trustSummary.followUpRunId} has provider proof captured, but no reconciliation has been recorded yet.`;
    inspectNext = `Inspect run ${trustSummary.followUpRunId} next and review its provider proof and reconciliation state in the full run evidence view.`;
  } else if (trustSummary.latestTrustStatus === "trusted_reconciled") {
    toneClass = "trust-callout trust-callout--healthy";
    pillClass = "trust-pill trust-pill--healthy";
    headline = "Latest run is trusted";
    explanation = `Latest run ${trustSummary.latestRunId} is reconciled, and no linked run currently needs trust follow-up.`;
    inspectNext = "Inspect the linked run evidence only if you need the deeper audit trail.";
  } else if (trustSummary.latestTrustStatus) {
    headline = `Latest trust state: ${latestTrustLabel}`;
    explanation = `Latest run ${trustSummary.latestRunId} is currently recorded as ${latestTrustLabel.toLowerCase()}.`;
    inspectNext = "Inspect the linked run evidence next if you need the supporting claim, proof, or reconciliation detail.";
  }

  return `
    <div class="${toneClass}">
      <div class="trust-callout__header">
        <span class="${pillClass}">${escapeHtml(headline)}</span>
      </div>
      <p class="trust-callout__explanation">${escapeHtml(explanation)}</p>
      <ul class="badge-list trust-callout__badges">
        ${renderBadge("Latest trust", latestTrustLabel, trustToneForExecutionSummary(taskDetails?.latest_execution_summary || {}))}
        ${renderBadge(
          "Reconciliation",
          latestReconciliationLabel,
          trustSummary.latestReconciliationState === "reconciled"
            ? "success"
            : trustSummary.latestReconciliationState === "reconciliation_failed"
              ? "warning"
              : trustSummary.latestReconciliationState === "reconciliation_pending"
                ? "strong"
                : "muted",
        )}
        ${renderBadge(
          "Follow-up run",
          trustSummary.followUpRunId || "None visible",
          trustSummary.followUpRunId ? "warning" : "muted",
        )}
      </ul>
      <p class="trust-callout__next"><strong>Inspect next:</strong> ${escapeHtml(inspectNext)}</p>
    </div>
  `;
}

function renderRunEvidenceSummary(runDetails) {
  if (!runDetails) {
    return `
      <div class="empty-card task-evidence-empty">
        <div class="task-evidence-empty__title">Run evidence not loaded</div>
        <p>Select a linked run to inspect governed execution evidence for this task.</p>
      </div>
    `;
  }

  const run = runDetails.run || {};
  const summary = runDetails.governed_external_run_summary || {};
  const attentionItems = safeArray(runDetails.governed_external_attention_items);
  const preBlocks = safeArray(runDetails.governed_pre_execution_blocks);
  const executionGroups = safeArray(runDetails.governed_external_execution_groups);
  const evidenceCards = [];

  if (attentionItems.length) {
    evidenceCards.push(
      `
        <article class="evidence-card evidence-card--warning">
          <div class="evidence-card__heading">
            <div>
              <div class="evidence-card__title">Attention summary</div>
              <p class="evidence-card__meta">The latest run still has operator-visible execution concerns.</p>
            </div>
            <span class="priority-pill priority-pill--high">Attention</span>
          </div>
          <ul>
            ${attentionItems
              .slice(0, 3)
              .map(
                (item) =>
                  `<li>${escapeHtml(item.execution_group_id || "Unknown group")} | ${escapeHtml(
                    statusLabel(item.final_outcome_status || item.attention_reason || "attention"),
                  )}</li>`,
              )
              .join("")}
          </ul>
        </article>
      `,
    );
  }

  if (preBlocks.length) {
    evidenceCards.push(
      `
        <article class="evidence-card evidence-card--warning">
          <div class="evidence-card__title">Pre-execution blocks</div>
          <p class="evidence-card__meta">Some governed requests were blocked before external observation began.</p>
          <ul>
            ${preBlocks
              .slice(0, 3)
              .map(
                (block) =>
                  `<li>${escapeHtml(statusLabel(block.block_reason_code || "blocked"))} | ${formatTimestamp(
                    block.occurred_at,
                  )}</li>`,
              )
              .join("")}
          </ul>
        </article>
      `,
    );
  }

  if (!evidenceCards.length) {
    evidenceCards.push(
      `
        <article class="evidence-card evidence-card--success">
          <div class="evidence-card__title">Latest evidence snapshot</div>
          <p class="evidence-card__meta">This linked run looks clean from the current governed execution evidence.</p>
          <ul>
            <li>${escapeHtml(countValue(summary.final_success_count))} successful execution group(s)</li>
            <li>${escapeHtml(countValue(summary.final_proved_count))} proved execution group(s)</li>
          </ul>
        </article>
      `,
    );
  }

  return `
    <section class="task-run-evidence">
      <div class="task-run-evidence__header">
        <div>
          <p class="eyebrow">Run Evidence</p>
          <h3>Linked governed run</h3>
          <p class="panel__lede">Compact governed evidence inside task context. Use the full control room when you want the complete run drill-down.</p>
        </div>
        <a class="task-run-evidence__link" href="/control-room?run_id=${encodeURIComponent(run.id || "")}">Open full run evidence</a>
      </div>

      <ul class="badge-list">
        ${renderBadge("Run", run.id || "Unknown")}
        ${renderBadge("Status", statusLabel(run.status))}
        ${renderBadge("Execution groups", countValue(summary.total_execution_groups))}
        ${renderBadge("Attempts", countValue(summary.total_attempts))}
        ${renderBadge("Proof missing", countValue(summary.final_proof_missing_count), countValue(summary.final_proof_missing_count) ? "warning" : "muted")}
      </ul>

      <div class="task-run-metrics">
        ${renderSummaryCard("API executions", countValue(summary.governed_api_execution_count), "Governed API path hits in this run.", countValue(summary.governed_api_execution_count) ? "success" : "default")}
        ${renderSummaryCard("Failures", countValue(summary.final_failed_count), "Final execution groups that ended failed.", countValue(summary.final_failed_count) ? "warning" : "default")}
        ${renderSummaryCard("Budget stops", countValue(summary.final_budget_stopped_count), "Final execution groups stopped by budget controls.", countValue(summary.final_budget_stopped_count) ? "warning" : "default")}
        ${renderSummaryCard("Pre-exec blocks", countValue(summary.pre_observation_block_count), "Governed requests blocked before observation started.", countValue(summary.pre_observation_block_count) ? "warning" : "default")}
      </div>

      <div class="task-run-insights">
        ${evidenceCards.join("")}
      </div>

      <div class="task-run-groups">
        <div class="task-run-groups__header">
          <h4>Execution groups</h4>
          <span>${escapeHtml(String(executionGroups.length))}</span>
        </div>
        <div class="task-run-groups__list">
          ${executionGroups.length
            ? executionGroups
                .slice(0, 4)
                .map(
                  (group) => `
                    <article class="group-card group-card--static">
                      <div class="group-card__title">${escapeHtml(group.execution_group_id || "Unknown group")}</div>
                      <ul>
                        <li>Path: ${escapeHtml(statusLabel(group.execution_path_classification || "unknown"))}</li>
                        <li>Outcome: ${escapeHtml(statusLabel(group.final_outcome_status || "unknown"))}</li>
                        <li>Proof: ${escapeHtml(statusLabel(group.final_proof_status || "unknown"))}</li>
                      </ul>
                    </article>
                  `,
                )
                .join("")
            : `<div class="empty-card">No governed execution groups were recorded for this run.</div>`}
        </div>
      </div>
    </section>
  `;
}

function renderLinkedRunCard(run, selectedRunId) {
  const executionSummary = run.execution_summary || {};
  const attentionSummary = run.attention_summary || {};
  const healthSummary = run.health_summary || {};
  const isSelected = selectedRunId && selectedRunId === run.id;
  const trustStatus = executionSummary.latest_trust_status;
  const reconciliationState = executionSummary.latest_reconciliation_state;
  return `
    <button
      class="task-run-chip${isSelected ? " task-run-chip--selected" : ""}"
      type="button"
      data-linked-run-id="${escapeHtml(run.id)}"
    >
      <div class="task-run-chip__header">
        <strong>${escapeHtml(run.id)}</strong>
        <span>${escapeHtml(statusLabel(run.status))}</span>
      </div>
      <div class="task-run-chip__summary">${escapeHtml(latestExecutionBadge(executionSummary))}</div>
      ${
        trustStatus || reconciliationState
          ? `
            <ul class="badge-list task-run-chip__badges">
              ${trustStatus ? renderBadge("Trust", statusLabel(trustStatus), trustToneForExecutionSummary(executionSummary)) : ""}
              ${
                reconciliationState
                  ? renderBadge(
                      "Reconciliation",
                      statusLabel(reconciliationState),
                      reconciliationState === "reconciled"
                        ? "success"
                        : reconciliationState === "reconciliation_failed"
                          ? "warning"
                          : reconciliationState === "reconciliation_pending"
                            ? "strong"
                            : "muted",
                    )
                  : ""
              }
            </ul>
          `
          : ""
      }
      <div class="task-run-chip__meta">
        ${escapeHtml(String(countValue(attentionSummary.attention_count)))} attention |
        ${escapeHtml(String(countValue(healthSummary.final_success_count)))} success |
        ${formatTimestamp(run.started_at || run.created_at)}
      </div>
    </button>
  `;
}

export function selectLinkedRunId(taskDetails, preferredRunId = "") {
  const linkedRuns = safeArray(taskDetails?.linked_runs);
  if (!linkedRuns.length) {
    return "";
  }
  if (preferredRunId && linkedRuns.some((run) => run.id === preferredRunId)) {
    return preferredRunId;
  }
  return linkedRuns[0]?.id || "";
}

function flattenBoardCards(snapshot) {
  return safeArray(snapshot?.board).flatMap((column) => safeArray(column.cards));
}

function findTaskCard(snapshot, taskId) {
  return flattenBoardCards(snapshot).find((card) => card.id === taskId) || null;
}

export function summarizeMilestones(snapshot) {
  const milestoneRecords = safeArray(snapshot?.milestones);
  const cardsById = new Map(flattenBoardCards(snapshot).map((card) => [card.id, card]));

  return milestoneRecords.map((milestone) => {
    const milestoneTasks = safeArray(milestone.tasks)
      .map((task) => cardsById.get(task.id) || task)
      .filter(Boolean);
    const linkedRunCount = milestoneTasks.reduce((total, task) => total + countValue(task.linked_run_count), 0);
    const attentionTaskCount = milestoneTasks.reduce(
      (total, task) => total + (countValue(task.latest_attention_summary?.attention_count) > 0 ? 1 : 0),
      0,
    );
    const governedRunTaskCount = milestoneTasks.reduce(
      (total, task) =>
        total +
        (task.latest_execution_summary?.latest_execution_path_classification ||
        task.latest_run?.governed_external_run_summary?.governed_api_execution_count
          ? 1
          : 0),
      0,
    );
    const signalSummary = attentionTaskCount
      ? `${attentionTaskCount} task(s) need attention`
      : linkedRunCount
        ? `${governedRunTaskCount} task(s) show governed run evidence`
        : "No linked run evidence yet";
    const trustSummary = milestone?.trust_summary || {};
    const tasksWithTrustFollowUp = countValue(trustSummary.tasks_with_trust_followup);
    const unreconciledRunCount = countValue(trustSummary.unreconciled_run_count);
    const highestPriorityTrustIssue = String(trustSummary.highest_priority_trust_issue || "").trim();
    const trustTone = tasksWithTrustFollowUp
      ? highestPriorityTrustIssue === "reconciliation_failed"
        ? "risk"
        : "warning"
      : linkedRunCount
        ? "success"
        : "muted";
    const trustLabel = tasksWithTrustFollowUp
      ? `${tasksWithTrustFollowUp} task(s) need trust follow-up`
      : linkedRunCount
        ? "No trust follow-up visible"
        : "No trust evidence yet";
    const trustDetail = tasksWithTrustFollowUp
      ? `${trustIssueLabel(highestPriorityTrustIssue || "proof_captured_not_reconciled")} across ${unreconciledRunCount} linked run(s)`
      : linkedRunCount
        ? "Linked governed runs are currently clean at milestone scope."
        : "This milestone has not produced linked governed trust evidence yet.";
    return {
      id: milestone.id,
      title: milestone.title || "Untitled milestone",
      status: milestone.status || "unknown",
      taskCount: countValue(milestone.task_count || milestoneTasks.length),
      linkedRunCount,
      attentionTaskCount,
      governedRunTaskCount,
      signalSummary,
      trustTone,
      trustLabel,
      trustDetail,
      tasksWithTrustFollowUp,
      unreconciledRunCount,
      highestPriorityTrustIssue,
    };
  });
}

export function filterBoardByMilestone(snapshot, selectedMilestoneId = "") {
  if (!selectedMilestoneId) {
    return safeArray(snapshot?.board);
  }
  return safeArray(snapshot?.board).map((column) => {
    const cards = safeArray(column.cards).filter((card) => card.milestone_id === selectedMilestoneId);
    return {
      ...column,
      cards,
      count: cards.length,
    };
  });
}

function renderMilestoneCard(summary, selectedMilestoneId) {
  const isSelected = selectedMilestoneId && selectedMilestoneId === summary.id;
  return `
    <button
      class="milestone-card milestone-card--trust-${escapeHtml(summary.trustTone || "muted")}${isSelected ? " milestone-card--selected" : ""}"
      type="button"
      data-milestone-id="${escapeHtml(summary.id)}"
    >
      <div class="milestone-card__header">
        <strong>${escapeHtml(summary.title)}</strong>
        <span>${escapeHtml(statusLabel(summary.status))}</span>
      </div>
      <div class="milestone-card__metrics">
        <span>${escapeHtml(String(summary.taskCount))} tasks</span>
        <span>${escapeHtml(String(summary.linkedRunCount))} linked runs</span>
      </div>
      <div class="milestone-card__trust milestone-card__trust--${escapeHtml(summary.trustTone || "muted")}">
        <span class="milestone-card__trust-pill milestone-card__trust-pill--${escapeHtml(summary.trustTone || "muted")}">${escapeHtml(summary.trustLabel)}</span>
        <p>${escapeHtml(summary.trustDetail)}</p>
      </div>
      <div class="milestone-card__signal">${escapeHtml(summary.signalSummary)}</div>
    </button>
  `;
}

function renderMilestoneRail(snapshot, selectedMilestoneId) {
  const milestoneSummaries = summarizeMilestones(snapshot);
  if (!milestoneSummaries.length) {
    return "";
  }
  return `
    <section class="panel panel--milestones">
      <div class="panel__header">
        <div>
          <p class="eyebrow">Milestones</p>
          <h2>Milestone context</h2>
          <p class="panel__lede">Use milestones as the top work lens before drilling into task and run evidence.</p>
        </div>
        <button class="project-chip${selectedMilestoneId ? "" : " project-chip--active"}" type="button" data-milestone-id="">
          All milestones
        </button>
      </div>
      <div class="milestone-rail">
        ${milestoneSummaries.map((summary) => renderMilestoneCard(summary, selectedMilestoneId)).join("")}
      </div>
    </section>
  `;
}

export function renderIntegratedTaskDetail(taskDetails, runDetails, options = {}) {
  const taskStatus = options.taskStatus || "loaded";
  const taskError = options.taskError || "";
  const runStatus = options.runStatus || "idle";
  const runError = options.runError || "";
  const selectedRunId = options.selectedRunId || "";

  if (taskStatus === "loading") {
    return `
      <aside class="panel panel--detail task-detail-panel">
        <div class="empty-card task-detail-empty">
          <div class="task-detail-empty__title">Loading task context</div>
          <p>Pulling the unified task-to-run graph from the read-only task-details route.</p>
        </div>
      </aside>
    `;
  }

  if (taskStatus === "error") {
    return `
      <aside class="panel panel--detail task-detail-panel">
        <div class="empty-card task-detail-empty">
          <div class="task-detail-empty__title">Task detail unavailable</div>
          <p>${escapeHtml(taskError || "Task context could not be loaded from the read-only route.")}</p>
        </div>
      </aside>
    `;
  }

  if (!taskDetails || !taskDetails.task) {
    return `
      <aside class="panel panel--detail task-detail-panel">
        <div class="task-detail-placeholder">
          <p class="eyebrow">Integrated Task Detail</p>
          <h2>Select a task from the board</h2>
          <p class="panel__lede">This drawer bridges planning context to governed execution evidence. Pick a task to inspect its milestone context, linked runs, and the latest governed run summary together.</p>
        </div>
      </aside>
    `;
  }

  const task = taskDetails.task;
  const project = taskDetails.project || {};
  const milestone = taskDetails.milestone || {};
  const linkedRuns = safeArray(taskDetails.linked_runs);
  const latestAttention = taskDetails.latest_attention_summary || {};
  const latestHealth = taskDetails.latest_health_summary || {};
  const latestExecution = taskDetails.latest_execution_summary || {};
  const trustSummary = summarizeTaskTrust(taskDetails);

  return `
    <aside class="panel panel--detail task-detail-panel" aria-label="Integrated task detail">
      <div class="task-detail-panel__header">
        <div>
          <p class="eyebrow">Integrated Task Detail</p>
          <h2>${escapeHtml(task.title || task.id)}</h2>
          <p class="panel__lede">${escapeHtml(task.objective || task.details || "No objective recorded.")}</p>
        </div>
        <span class="task-detail-panel__status">${escapeHtml(statusLabel(task.status))}</span>
      </div>

      <ul class="badge-list">
        ${renderBadge("Task", task.id || "Unknown")}
        ${renderBadge("Project", project.name || task.project_name || "Unknown")}
        ${renderBadge("Milestone", milestone.title || "Unassigned", milestone.title ? "strong" : "muted")}
        ${renderBadge("Linked runs", taskDetails.linked_run_count || linkedRuns.length || 0, linkedRuns.length ? "success" : "muted")}
      </ul>

      <div class="task-context-grid">
        <div class="task-context-card">
          <span class="task-context-card__label">Task status</span>
          <strong>${escapeHtml(statusLabel(task.status))}</strong>
        </div>
        <div class="task-context-card">
          <span class="task-context-card__label">Latest attention</span>
          <strong>${escapeHtml(String(countValue(latestAttention.attention_count)))}</strong>
        </div>
        <div class="task-context-card">
          <span class="task-context-card__label">Latest health</span>
          <strong>${escapeHtml(
            countValue(latestHealth.final_failed_count) || countValue(latestHealth.pre_observation_block_count)
              ? "Needs review"
              : "Clearer signal",
          )}</strong>
        </div>
        <div class="task-context-card">
          <span class="task-context-card__label">Latest execution</span>
          <strong>${escapeHtml(latestExecutionBadge(latestExecution))}</strong>
        </div>
        <div class="task-context-card">
          <span class="task-context-card__label">Latest trust</span>
          <strong>${escapeHtml(statusLabel(trustSummary.latestTrustStatus || "not recorded"))}</strong>
        </div>
      </div>

      <div class="task-summary-grid">
        ${renderSummaryCard(
          "Attention items",
          countValue(latestAttention.attention_count),
          latestAttention.top_attention_reason
            ? `Top signal: ${statusLabel(latestAttention.top_attention_reason)}`
            : "No active governed attention in the latest linked run.",
          countValue(latestAttention.attention_count) ? "warning" : "success",
        )}
        ${renderSummaryCard(
          "Health signal",
          countValue(latestHealth.final_success_count),
          countValue(latestHealth.final_failed_count)
            ? "Latest linked run still shows failed execution groups."
            : "Latest linked run reports successful governed execution groups.",
          countValue(latestHealth.final_failed_count) || countValue(latestHealth.pre_observation_block_count)
            ? "warning"
            : "success",
        )}
        ${renderSummaryCard(
          "Execution path",
          statusLabel(latestExecution.latest_execution_path_classification || "not recorded"),
          latestExecution.latest_proof_status
            ? `Proof ${statusLabel(latestExecution.latest_proof_status)} on the latest linked run.`
            : "Proof state has not been recorded on the latest linked run.",
          latestExecution.latest_execution_path_classification === "governed_api_executed" ? "success" : "default",
        )}
        ${renderSummaryCard(
          "Trust follow-up",
          trustSummary.hasOutstandingFollowUp ? "Needed" : statusLabel(trustSummary.latestTrustStatus || "not recorded"),
          trustSummary.hasOutstandingFollowUp
            ? `Run ${trustSummary.followUpRunId || "unknown"} currently carries the visible trust concern.`
            : trustSummary.latestReconciliationState
              ? `Reconciliation ${statusLabel(trustSummary.latestReconciliationState)} on the latest linked run.`
              : "No active trust follow-up is visible in linked runs.",
          trustSummary.hasOutstandingFollowUp
            ? "warning"
            : trustSummary.latestTrustStatus === "trusted_reconciled"
              ? "success"
              : "default",
        )}
      </div>

      ${renderTaskHealthCallout(latestHealth)}
      ${renderTaskTrustCallout(taskDetails)}

      <section class="task-run-section">
        <div class="task-run-section__header">
          <div>
            <h3>Linked runs</h3>
            <p class="panel__lede">Read-only run context tied directly to this task through the unified work graph.</p>
          </div>
          <span>${escapeHtml(String(linkedRuns.length))}</span>
        </div>
        <div class="task-run-chip-list">
          ${linkedRuns.length
            ? linkedRuns.map((run) => renderLinkedRunCard(run, selectedRunId)).join("")
            : `<div class="empty-card task-detail-empty"><div class="task-detail-empty__title">No linked runs yet</div><p>This task has not produced a governed run record yet.</p></div>`}
        </div>
      </section>

      ${
        runStatus === "loading"
          ? `
            <div class="empty-card task-detail-empty">
              <div class="task-detail-empty__title">Loading run evidence</div>
              <p>Pulling governed execution evidence for ${escapeHtml(selectedRunId || "the selected run")}.</p>
            </div>
          `
          : runStatus === "error"
            ? `
              <div class="empty-card task-detail-empty">
                <div class="task-detail-empty__title">Run evidence unavailable</div>
                <p>${escapeHtml(runError || "Run evidence could not be loaded from the read-only route.")}</p>
              </div>
            `
            : renderRunEvidenceSummary(runDetails)
      }
    </aside>
  `;
}

function renderTaskCard(card, selectedTaskId) {
  const isSelected = selectedTaskId && selectedTaskId === card.id;
  const latestExecutionSummary = card.latest_execution_summary || {};
  const latestAttentionSummary = card.latest_attention_summary || {};
  const taskTrust = summarizeBoardTrust(card);
  const executionTone =
    latestExecutionSummary.latest_execution_path_classification === "governed_api_executed"
      ? "success"
      : latestExecutionSummary.latest_execution_path_classification === "blocked_pre_execution"
        ? "warning"
        : "muted";
  return `
    <button
      class="task-card task-card--selectable task-card--trust-${escapeHtml(taskTrust.tone)}${isSelected ? " task-card--selected" : ""}"
      type="button"
      data-task-id="${escapeHtml(card.id)}"
    >
      <div class="task-card__header">
        <div>
          <div class="task-card__title">${escapeHtml(card.title || card.id)}</div>
          <div class="task-card__meta">${escapeHtml(card.id)} | ${escapeHtml(statusLabel(card.status))}</div>
        </div>
        <span class="task-card__count">${escapeHtml(String(countValue(card.linked_run_count)))}</span>
      </div>
      <p class="task-card__path">${escapeHtml(card.objective || card.details || "No objective recorded.")}</p>
      <div class="task-card__trust task-card__trust--${escapeHtml(taskTrust.tone)}">
        <span class="task-card__trust-pill task-card__trust-pill--${escapeHtml(taskTrust.tone)}">${escapeHtml(taskTrust.bannerLabel)}</span>
        <p class="task-card__trust-copy">${escapeHtml(taskTrust.detail)}</p>
      </div>
      <ul class="badge-list">
        ${renderBadge("Milestone", card.milestone_title || "Unassigned", card.milestone_title ? "strong" : "muted")}
        ${renderBadge("Trust", taskTrust.badgeLabel, badgeToneForTrustTone(taskTrust.tone))}
        ${renderBadge(
          "Execution",
          latestExecutionBadge(latestExecutionSummary),
          executionTone,
        )}
        ${renderBadge(
          "Attention",
          countValue(latestAttentionSummary.attention_count),
          countValue(latestAttentionSummary.attention_count) ? "warning" : "muted",
        )}
      </ul>
    </button>
  `;
}

function renderBoard(snapshot, selectedTaskId) {
  const board = safeArray(snapshot?.board);
  if (!board.length) {
    return `<div class="empty-card">No board data was returned for this project.</div>`;
  }
  return `
    <div class="board-grid">
      ${board
        .map(
          (column) => `
            <section class="board-column">
              <div class="board-column__header">
                <h2>${escapeHtml(column.name)}</h2>
                <span>${escapeHtml(String(countValue(column.count)))}</span>
              </div>
              <div class="board-column__body">
                ${
                  safeArray(column.cards).length
                    ? safeArray(column.cards).map((card) => renderTaskCard(card, selectedTaskId)).join("")
                    : `<div class="empty-card">No tasks in this lane.</div>`
                }
              </div>
            </section>
          `,
        )
        .join("")}
    </div>
  `;
}

function projectLabel(projectName) {
  if (!projectName || projectName === "all") {
    return "All Projects";
  }
  return statusLabel(projectName);
}

function workspacePriorityForCard(card) {
  const taskTrust = summarizeBoardTrust(card);
  const blocked =
    String(card?.latest_execution_summary?.latest_execution_path_classification || "").trim() === "blocked_pre_execution";
  const attentionCount = countValue(card?.latest_attention_summary?.attention_count);
  if (taskTrust.tone === "risk") {
    return 0;
  }
  if (taskTrust.tone === "warning") {
    return 1;
  }
  if (blocked) {
    return 2;
  }
  if (attentionCount > 0) {
    return 3;
  }
  if (taskTrust.tone === "success") {
    return 4;
  }
  return 5;
}

function summarizeWorkspaceShell(snapshot, options = {}) {
  const selectedMilestoneId = options.selectedMilestoneId || "";
  const selectedTaskId = options.selectedTaskId || "";
  const filteredBoard = filterBoardByMilestone(snapshot, selectedMilestoneId);
  const boardCards = flattenBoardCards({ board: filteredBoard });
  const selectedCard =
    boardCards.find((card) => card.id === selectedTaskId) || findTaskCard(snapshot, selectedTaskId) || null;

  const trustFollowUpCards = boardCards.filter((card) => countValue(card?.trust_summary?.trust_followup_count) > 0);
  const blockedCards = boardCards.filter(
    (card) => String(card?.latest_execution_summary?.latest_execution_path_classification || "").trim() === "blocked_pre_execution",
  );
  const attentionCards = boardCards.filter((card) => countValue(card?.latest_attention_summary?.attention_count) > 0);

  const focusCard =
    selectedCard ||
    [...boardCards].sort((left, right) => workspacePriorityForCard(left) - workspacePriorityForCard(right))[0] ||
    null;
  const focusTrust = focusCard ? summarizeBoardTrust(focusCard) : null;

  let focusHeadline = "Board is ready for inspection";
  let focusBody = "Use the milestone lens to narrow scope, then open a task to inspect linked trust and run evidence.";
  let focusTone = "muted";
  let focusBadge = "Scan tasks";

  if (focusCard && focusTrust) {
    if (focusTrust.tone === "risk") {
      focusHeadline = `Start with ${focusCard.id}`;
      focusBody = `${focusTrust.detail}. Open the task drawer to inspect the affected linked run and its deeper control-room evidence.`;
      focusTone = "risk";
      focusBadge = "Highest trust risk";
    } else if (focusTrust.tone === "warning") {
      focusHeadline = `Trust follow-up is visible on ${focusCard.id}`;
      focusBody = `${focusTrust.detail}. Review the task drawer next to see which linked run still needs trust attention.`;
      focusTone = "warning";
      focusBadge = "Trust follow-up";
    } else if (workspacePriorityForCard(focusCard) === 2) {
      focusHeadline = `${focusCard.id} is blocked before execution`;
      focusBody = "This task has a blocked execution signal. Open the task drawer to inspect the run path and follow-up evidence.";
      focusTone = "warning";
      focusBadge = "Blocked";
    } else if (workspacePriorityForCard(focusCard) === 3) {
      focusHeadline = `${focusCard.id} still needs attention`;
      focusBody = "Attention signals are visible on this task even though trust follow-up is not currently leading the board.";
      focusTone = "warning";
      focusBadge = "Attention";
    } else if (focusTrust.tone === "success") {
      focusHeadline = `${focusCard.id} looks clean`;
      focusBody = "The strongest visible task signal is currently healthy. Use the board to scan for the next task worth opening.";
      focusTone = "success";
      focusBadge = "Clean signal";
    } else if (selectedCard) {
      focusHeadline = `Selected task: ${selectedCard.id}`;
      focusBody = "The drawer is ready to carry you from planning context into linked run evidence for this task.";
      focusTone = "muted";
      focusBadge = "Selected";
    }
  }

  return {
    boardCards,
    trustFollowUpCount: trustFollowUpCards.length,
    blockedCount: blockedCards.length,
    attentionCount: attentionCards.length,
    focusHeadline,
    focusBody,
    focusTone,
    focusBadge,
  };
}

function renderWorkspaceOverview(snapshot, options = {}) {
  const selectedMilestoneId = options.selectedMilestoneId || "";
  const activeProject = options.activeProject || snapshot?.project_name || "all";
  const selectedTaskId = options.selectedTaskId || "";
  const milestoneSummaries = summarizeMilestones(snapshot);
  const activeMilestone = milestoneSummaries.find((item) => item.id === selectedMilestoneId) || null;
  const workspace = summarizeWorkspaceShell(snapshot, options);

  return `
    <section class="workspace-overview">
      <article class="workspace-overview__focus workspace-overview__focus--${escapeHtml(workspace.focusTone)}">
        <div class="workspace-overview__focus-header">
          <div>
            <p class="eyebrow">What Matters Now</p>
            <h2>${escapeHtml(workspace.focusHeadline)}</h2>
          </div>
          <span class="workspace-overview__pill workspace-overview__pill--${escapeHtml(workspace.focusTone)}">${escapeHtml(workspace.focusBadge)}</span>
        </div>
        <p class="workspace-overview__copy">${escapeHtml(workspace.focusBody)}</p>
      </article>
      <div class="workspace-overview__grid">
        <article class="workspace-overview__card">
          <p class="eyebrow">Current Lens</p>
          <h3>${escapeHtml(projectLabel(activeProject))}</h3>
          <p>${escapeHtml(activeMilestone ? `Milestone filter: ${activeMilestone.title}` : "Showing all milestones in the current project scope.")}</p>
        </article>
        <article class="workspace-overview__card">
          <p class="eyebrow">Board Pulse</p>
          <h3>${escapeHtml(String(workspace.trustFollowUpCount))} trust follow-up task(s)</h3>
          <p>${escapeHtml(`${workspace.attentionCount} attention task(s) and ${workspace.blockedCount} blocked task(s) are visible in the current board window.`)}</p>
        </article>
        <article class="workspace-overview__card">
          <p class="eyebrow">Workflow Path</p>
          <h3>Board -> Task -> Run</h3>
          <p>${escapeHtml(selectedTaskId ? "You are already inside the connected planning-to-evidence workflow." : "Start on the board, open a task, then inspect linked run evidence or the full control room.")}</p>
        </article>
      </div>
    </section>
  `;
}

export function fetchSnapshot(projectName, fetchImpl = globalThis.fetch) {
  return fetchImpl(`/api/snapshot?project=${encodeURIComponent(projectName || "all")}`, {
    cache: "no-store",
  }).then(async (response) => {
    if (!response.ok) {
      const payload = await response.json().catch(() => ({}));
      throw new Error(payload.error || `Snapshot request failed with status ${response.status}.`);
    }
    return response.json();
  });
}

export function fetchTaskDetails(taskId, fetchImpl = globalThis.fetch) {
  return fetchImpl(`/api/task-details?task_id=${encodeURIComponent(taskId)}`, {
    cache: "no-store",
  }).then(async (response) => {
    if (!response.ok) {
      const payload = await response.json().catch(() => ({}));
      throw new Error(payload.error || `Task-details request failed with status ${response.status}.`);
    }
    return response.json();
  });
}

export function fetchRunDetails(runId, fetchImpl = globalThis.fetch) {
  return fetchImpl(`/api/run-details?run_id=${encodeURIComponent(runId)}`, {
    cache: "no-store",
  }).then(async (response) => {
    if (!response.ok) {
      const payload = await response.json().catch(() => ({}));
      throw new Error(payload.error || `Run-details request failed with status ${response.status}.`);
    }
    return response.json();
  });
}

export function renderOperatorWall(snapshot, viewState = {}) {
  const snapshotStatus = viewState.snapshotStatus || "loaded";
  const activeProject = viewState.activeProject || snapshot?.project_name || "all";
  const selectedMilestoneId = viewState.selectedMilestoneId || "";
  const selectedTaskId = viewState.selectedTaskId || "";
  const taskDetails = viewState.taskDetails || null;
  const taskStatus = viewState.taskStatus || "idle";
  const taskError = viewState.taskError || "";
  const runDetails = viewState.runDetails || null;
  const runStatus = viewState.runStatus || "idle";
  const runError = viewState.runError || "";
  const selectedRunId = viewState.selectedRunId || "";
  const summary = snapshot?.summary || {};
  const availableProjects = safeArray(snapshot?.available_projects);
  const filteredBoard = filterBoardByMilestone(snapshot, selectedMilestoneId);
  const activeMilestone = summarizeMilestones(snapshot).find((item) => item.id === selectedMilestoneId) || null;
  const workspaceShell = summarizeWorkspaceShell(snapshot, { selectedMilestoneId, selectedTaskId });

  const heroStats = `
    <div class="stats-grid">
      ${renderSummaryCard("Tasks", countValue(summary.task_count), "Tasks in the selected project window.")}
      ${renderSummaryCard("Runs", countValue(summary.run_count), "Canonical runs linked to this project.", countValue(summary.run_count) ? "success" : "default")}
      ${renderSummaryCard("Planning warnings", countValue(summary.planning_warning_count), "Tasks with gate issues still visible in the board.", countValue(summary.planning_warning_count) ? "warning" : "default")}
      ${renderSummaryCard("Pending approvals", countValue(summary.pending_approvals), "Read-only approval backlog carried by the current project scope.", countValue(summary.pending_approvals) ? "warning" : "default")}
    </div>
  `;

  const projectChipRow = availableProjects.length
    ? `
      <div class="project-chip-row">
        <button class="project-chip${activeProject === "all" ? " project-chip--active" : ""}" type="button" data-project-chip="all">All Projects</button>
        ${availableProjects
          .map(
            (project) => `
              <button
                class="project-chip${activeProject === project.name ? " project-chip--active" : ""}"
                type="button"
                data-project-chip="${escapeHtml(project.name)}"
              >
                ${escapeHtml(project.label)}
              </button>
            `,
          )
          .join("")}
      </div>
    `
    : "";

  const body =
    snapshotStatus === "loading"
      ? `
        <section class="panel panel--summary">
          <div class="empty-card">Loading operator wall snapshot from the canonical read-only route.</div>
        </section>
      `
      : snapshotStatus === "error"
        ? `
          <section class="panel panel--summary">
            <div class="empty-card">Snapshot unavailable. ${escapeHtml(viewState.snapshotError || "Try reloading the board.")}</div>
          </section>
        `
      : `
          <div class="workspace-stack">
            ${renderWorkspaceOverview(snapshot, { activeProject, selectedMilestoneId, selectedTaskId })}
            ${renderMilestoneRail(snapshot, selectedMilestoneId)}
            <section class="panel panel--workspace">
              <div class="panel__header">
                <div>
                  <p class="eyebrow">Integrated Workspace</p>
                  <h2>Task board connected to governed execution evidence</h2>
                  <p class="panel__lede">Select a task from the board to inspect its latest run summaries and linked governed evidence in one read-only workflow.</p>
                </div>
                ${
                  activeMilestone
                    ? `<span class="workspace-milestone-pill">Milestone filter: ${escapeHtml(activeMilestone.title)}</span>`
                    : `<span class="workspace-milestone-pill workspace-milestone-pill--muted">Showing all milestones</span>`
                }
              </div>
              <div class="workspace-grid">
                <section class="workspace-pane workspace-pane--board">
                  <div class="workspace-pane__header">
                    <div>
                      <p class="eyebrow">Planning Surface</p>
                      <h3>Trust-aware board</h3>
                      <p class="workspace-pane__copy">Scan workflow lanes first, then open a task when you need deeper trust or evidence detail.</p>
                    </div>
                    <span class="workspace-pane__meta">${escapeHtml(String(workspaceShell.boardCards.length))} visible task(s)</span>
                  </div>
                  ${renderBoard({ board: filteredBoard }, selectedTaskId)}
                </section>
                <section class="workspace-pane workspace-pane--detail">
                  <div class="workspace-pane__header">
                    <div>
                      <p class="eyebrow">Evidence Surface</p>
                      <h3>Task and run detail</h3>
                      <p class="workspace-pane__copy">Keep planning context, trust state, linked runs, and governed evidence in one read-only workspace.</p>
                    </div>
                    <span class="workspace-pane__meta">${escapeHtml(selectedTaskId ? `Selected: ${selectedTaskId}` : "No task selected")}</span>
                  </div>
                  ${renderIntegratedTaskDetail(taskDetails, runDetails, {
                    taskStatus,
                    taskError,
                    runStatus,
                    runError,
                    selectedRunId,
                  })}
                </section>
              </div>
            </section>
          </div>
        `;

  return `
    <div class="shell">
      <section class="hero">
        <div>
          <p class="eyebrow">Unified Operator Workspace</p>
          <h1>Task context flows directly into governed run evidence.</h1>
          <p class="lede">This first integrated surface bridges the Kanban board to the governed control-room model using the shared read-only work graph.</p>

          <form class="project-form" id="project-form">
            <label for="project-input">Project scope</label>
            <div class="project-form__row">
              <input id="project-input" name="project" value="${escapeHtml(activeProject)}" placeholder="all or project slug" />
              <button type="submit">Load project</button>
            </div>
          </form>
          ${projectChipRow}
        </div>
        <div class="hero__summary">
          <p class="eyebrow">Current scope</p>
          <h2>${escapeHtml(projectLabel(activeProject))}</h2>
          <p class="hero__meta">Read-only board context, linked task detail, and governed run evidence from one backend contract.</p>
          ${heroStats}
        </div>
      </section>
      ${body}
    </div>
  `;
}

function syncQueryState() {
  if (typeof window === "undefined") {
    return;
  }
  const params = new URLSearchParams();
  if (state.activeProject && state.activeProject !== "all") {
    params.set("project", state.activeProject);
  }
  if (state.selectedMilestoneId) {
    params.set("milestone_id", state.selectedMilestoneId);
  }
  if (state.selectedTaskId) {
    params.set("task_id", state.selectedTaskId);
  }
  if (state.selectedRunId) {
    params.set("run_id", state.selectedRunId);
  }
  const query = params.toString();
  const nextUrl = query ? `/?${query}` : "/";
  window.history.replaceState({}, "", nextUrl);
}

function renderCurrentView() {
  if (!appRoot) {
    return;
  }
  appRoot.innerHTML = renderOperatorWall(state.snapshot, state);
}

async function loadRunDetails(runId) {
  const normalizedRunId = String(runId || "").trim();
  state.selectedRunId = normalizedRunId;
  state.runDetails = null;
  state.runError = "";
  state.runStatus = normalizedRunId ? "loading" : "idle";
  syncQueryState();
  renderCurrentView();

  if (!normalizedRunId) {
    return;
  }

  const requestToken = ++state.runRequestToken;
  try {
    const details = await fetchRunDetails(normalizedRunId);
    if (requestToken !== state.runRequestToken) {
      return;
    }
    state.runDetails = details;
    state.runStatus = "loaded";
    state.runError = "";
  } catch (error) {
    if (requestToken !== state.runRequestToken) {
      return;
    }
    state.runStatus = "error";
    state.runError = error instanceof Error ? error.message : String(error);
  }
  syncQueryState();
  renderCurrentView();
}

async function loadTaskDetails(taskId, options = {}) {
  const normalizedTaskId = String(taskId || "").trim();
  state.selectedTaskId = normalizedTaskId;
  state.taskDetails = null;
  state.taskError = "";
  state.taskStatus = normalizedTaskId ? "loading" : "idle";
  state.runDetails = null;
  state.runError = "";
  state.runStatus = "idle";
  state.selectedRunId = "";
  syncQueryState();
  renderCurrentView();

  if (!normalizedTaskId) {
    return;
  }

  const requestToken = ++state.taskRequestToken;
  try {
    const details = await fetchTaskDetails(normalizedTaskId);
    if (requestToken !== state.taskRequestToken) {
      return;
    }
    state.taskDetails = details;
    state.taskStatus = "loaded";
    state.taskError = "";

    const preferredRunId = options.preferredRunId || state.selectedRunId || "";
    const nextRunId = selectLinkedRunId(details, preferredRunId);
    state.selectedRunId = nextRunId;
    syncQueryState();
    renderCurrentView();

    if (nextRunId) {
      await loadRunDetails(nextRunId);
    }
  } catch (error) {
    if (requestToken !== state.taskRequestToken) {
      return;
    }
    state.taskStatus = "error";
    state.taskError = error instanceof Error ? error.message : String(error);
    syncQueryState();
    renderCurrentView();
  }
}

async function loadSnapshot(projectName, options = {}) {
  const normalizedProject = String(projectName || "all").trim() || "all";
  state.activeProject = normalizedProject;
  state.snapshotStatus = "loading";
  state.snapshotError = "";
  if (!options.preserveSelection) {
    state.selectedTaskId = "";
    state.selectedRunId = "";
    state.taskDetails = null;
    state.runDetails = null;
    state.taskStatus = "idle";
    state.runStatus = "idle";
  }
  syncQueryState();
  renderCurrentView();

  const requestToken = ++state.snapshotRequestToken;
  try {
    const snapshot = await fetchSnapshot(normalizedProject);
    if (requestToken !== state.snapshotRequestToken) {
      return;
    }
    state.snapshot = snapshot;
    state.snapshotStatus = "loaded";
    state.snapshotError = "";

    const milestoneSummaries = summarizeMilestones(snapshot);
    if (state.selectedMilestoneId && !milestoneSummaries.some((item) => item.id === state.selectedMilestoneId)) {
      state.selectedMilestoneId = "";
    }

    syncQueryState();
    renderCurrentView();

    if (state.selectedTaskId) {
      const taskCard = findTaskCard(snapshot, state.selectedTaskId);
      const taskStillVisible =
        taskCard && (!state.selectedMilestoneId || taskCard.milestone_id === state.selectedMilestoneId);
      if (taskStillVisible) {
        await loadTaskDetails(state.selectedTaskId, {
          preferredRunId: state.selectedRunId,
        });
      } else {
        state.selectedTaskId = "";
        state.selectedRunId = "";
        state.taskDetails = null;
        state.runDetails = null;
        state.taskStatus = "idle";
        state.runStatus = "idle";
        syncQueryState();
        renderCurrentView();
      }
    }
  } catch (error) {
    if (requestToken !== state.snapshotRequestToken) {
      return;
    }
    state.snapshotStatus = "error";
    state.snapshotError = error instanceof Error ? error.message : String(error);
    renderCurrentView();
  }
}

function bindAppEvents() {
  if (!appRoot) {
    return;
  }

  appRoot.addEventListener("submit", async (event) => {
    const form = event.target;
    if (!(form instanceof HTMLFormElement) || form.id !== "project-form") {
      return;
    }
    event.preventDefault();
    const input = form.querySelector("#project-input");
    const nextProject = input instanceof HTMLInputElement ? input.value : state.activeProject;
    await loadSnapshot(nextProject, { preserveSelection: false });
  });

  appRoot.addEventListener("click", async (event) => {
    const target = event.target instanceof Element ? event.target : null;
    const projectChip = target?.closest("[data-project-chip]");
    if (projectChip instanceof HTMLElement) {
      const nextProject = projectChip.dataset.projectChip || "all";
      await loadSnapshot(nextProject, { preserveSelection: false });
      return;
    }

    const milestoneButton = target?.closest("[data-milestone-id]");
    if (milestoneButton instanceof HTMLElement) {
      const nextMilestoneId = milestoneButton.dataset.milestoneId || "";
      state.selectedMilestoneId = nextMilestoneId;
      const selectedTask = findTaskCard(state.snapshot, state.selectedTaskId);
      if (selectedTask && nextMilestoneId && selectedTask.milestone_id !== nextMilestoneId) {
        state.selectedTaskId = "";
        state.selectedRunId = "";
        state.taskDetails = null;
        state.runDetails = null;
        state.taskStatus = "idle";
        state.runStatus = "idle";
      }
      syncQueryState();
      renderCurrentView();
      return;
    }

    const taskButton = target?.closest("[data-task-id]");
    if (taskButton instanceof HTMLElement) {
      const taskId = taskButton.dataset.taskId || "";
      await loadTaskDetails(taskId);
      return;
    }

    const runButton = target?.closest("[data-linked-run-id]");
    if (runButton instanceof HTMLElement) {
      const runId = runButton.dataset.linkedRunId || "";
      await loadRunDetails(runId);
    }
  });
}

if (appRoot) {
  renderCurrentView();
  bindAppEvents();
  loadSnapshot(state.activeProject, { preserveSelection: true });
}
