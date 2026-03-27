const appRoot = document.querySelector("#app");
const DEFAULT_PROJECT = "program-kanban";
const DEFAULT_VIEW = "board";
const AUTO_REFRESH_MS = 15000;
const STORAGE_KEYS = {
  autoRefresh: "studio.wall.autoRefresh",
  densityMode: "studio.wall.densityMode",
  hideCompleteMilestones: "studio.wall.hideCompleteMilestones",
  hideEmptyMilestones: "studio.wall.hideEmptyMilestones",
  collapsedMilestones: "studio.wall.collapsedMilestones",
};

let activeProject = new URLSearchParams(window.location.search).get("project") || DEFAULT_PROJECT;
let activeView = new URLSearchParams(window.location.search).get("view") || DEFAULT_VIEW;
let currentSnapshot = null;
let toastTimer = null;
let refreshTimer = null;
let selectedEvidence = null;
let selectedRunId = null;
let selectedRunEvidence = null;
let runInspectorLoading = false;
let runInspectorError = null;
let operatorDraft = {
  text: "",
  clarification: "",
};
let operatorPreview = null;
let operatorRequestBusy = false;
let operatorRequestError = null;
let restoreBusyId = null;
let restoreError = null;
let restoreOutcome = null;
let autoRefreshEnabled = readStoredFlag(STORAGE_KEYS.autoRefresh, false);
let densityMode = normalizeDensityMode(readStoredJson(STORAGE_KEYS.densityMode, "normal"));
let hideCompleteMilestones = readStoredFlag(STORAGE_KEYS.hideCompleteMilestones, false);
let hideEmptyMilestones = readStoredFlag(STORAGE_KEYS.hideEmptyMilestones, false);
let collapsedMilestones = readStoredJson(STORAGE_KEYS.collapsedMilestones, {});

function readStoredFlag(key, fallback) {
  try {
    const raw = window.localStorage.getItem(key);
    if (raw === null) {
      return fallback;
    }
    return raw === "1";
  } catch {
    return fallback;
  }
}

function writeStoredFlag(key, value) {
  try {
    window.localStorage.setItem(key, value ? "1" : "0");
  } catch {
    // Ignore storage errors and keep the in-memory setting.
  }
}

function readStoredJson(key, fallback) {
  try {
    const raw = window.localStorage.getItem(key);
    if (!raw) {
      return fallback;
    }
    return JSON.parse(raw);
  } catch {
    return fallback;
  }
}

function writeStoredJson(key, value) {
  try {
    window.localStorage.setItem(key, JSON.stringify(value));
  } catch {
    // Ignore storage errors and keep the in-memory setting.
  }
}

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

function statusToken(value) {
  return String(value ?? "unknown")
    .toLowerCase()
    .replaceAll(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");
}

function projectLabel(value) {
  return String(value ?? "")
    .split("-")
    .filter(Boolean)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

function formatTimestamp(value) {
  if (!value) {
    return "No timestamp";
  }
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return String(value);
  }
  return date.toLocaleString();
}

function formatBytes(value) {
  const bytes = Number(value || 0);
  if (!Number.isFinite(bytes) || bytes <= 0) {
    return "0 B";
  }
  const units = ["B", "KB", "MB", "GB"];
  let size = bytes;
  let unitIndex = 0;
  while (size >= 1024 && unitIndex < units.length - 1) {
    size /= 1024;
    unitIndex += 1;
  }
  const digits = size >= 10 || unitIndex === 0 ? 0 : 1;
  return `${size.toFixed(digits)} ${units[unitIndex]}`;
}

function normalizeDensityMode(value) {
  return ["compact", "normal", "detailed"].includes(value) ? value : "normal";
}

function resolveActionMode({ runtimeRole = "", source = "", eventType = "" } = {}) {
  const specialistRoles = ["Architect", "Developer", "Design", "QA"];
  const runtimeValue = String(runtimeRole || "");
  const sourceValue = String(source || "");
  const eventValue = String(eventType || "").toLowerCase();
  if (eventValue.startsWith("sdk_") || specialistRoles.includes(runtimeValue) || specialistRoles.includes(sourceValue)) {
    return { key: "ai-delegated", label: "AI Delegated" };
  }
  return { key: "framework", label: "Framework Action" };
}

async function requestJson(url, options = {}) {
  const response = await fetch(url, {
    cache: "no-store",
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
    ...options,
  });
  if (!response.ok) {
    const body = await response.text();
    try {
      const parsed = JSON.parse(body);
      throw new Error(parsed.error || parsed.message || `Request failed with ${response.status}`);
    } catch {
      throw new Error(body || `Request failed with ${response.status}`);
    }
  }
  return response.json();
}

function renderProjectChips(snapshot) {
  const chips = [
    { name: "all", label: "All Projects" },
    ...snapshot.available_projects.map((project) => ({ name: project.name, label: project.label || projectLabel(project.name) })),
  ];

  return chips.map((project) => `
    <button class="project-chip ${activeProject === project.name ? "project-chip--active" : ""}" type="button" data-project="${escapeHtml(project.name)}">
      ${escapeHtml(project.label)}
    </button>
  `).join("");
}

function renderViewTabs(snapshot) {
  return (snapshot.available_views || []).map((view) => {
    const labels = {
      board: "Board",
      milestones: "Milestones",
      orchestrator: "Control Room",
    };
    const label = labels[view] || view;
    return `
      <button class="view-tab ${activeView === view ? "view-tab--active" : ""}" type="button" data-view="${escapeHtml(view)}">
        ${escapeHtml(label)}
      </button>
    `;
  }).join("");
}

function copyButton(text, className = "copy-pill") {
  return `
    <button class="${className}" type="button" data-copy-text="${escapeHtml(text)}" aria-label="Copy ${escapeHtml(text)}">
      ${escapeHtml(text)}
    </button>
  `;
}

function badge(label, value, modifier = "") {
  return `
    <li class="badge ${modifier}">
      <span>${escapeHtml(label)}</span>
      <strong>${escapeHtml(value)}</strong>
    </li>
  `;
}

function evidenceAction(label, taskId, kind) {
  return `
    <button class="mini-action" type="button" data-evidence-kind="${escapeHtml(kind)}" data-task-id="${escapeHtml(taskId)}">
      ${escapeHtml(label)}
    </button>
  `;
}

function renderRefreshControls() {
  return `
    <div class="refresh-controls">
      <button class="action-button action-button--primary" type="button" data-refresh-now="true">Refresh Now</button>
      <button class="action-button ${autoRefreshEnabled ? "action-button--active" : ""}" type="button" data-auto-refresh-toggle="true">
        Auto-refresh ${autoRefreshEnabled ? "On" : "Off"}
      </button>
    </div>
  `;
}

function renderDensityControls() {
  const densityOptions = [
    { key: "compact", label: "Compact" },
    { key: "normal", label: "Normal" },
    { key: "detailed", label: "Detailed" },
  ];
  return `
    <div class="density-controls">
      <span class="density-controls__label">Density</span>
      <div class="chip-row chip-row--tight">
        ${densityOptions.map((option) => `
          <button
            class="filter-chip ${densityMode === option.key ? "filter-chip--active" : ""}"
            type="button"
            data-density-mode="${escapeHtml(option.key)}"
          >
            ${escapeHtml(option.label)}
          </button>
        `).join("")}
      </div>
    </div>
  `;
}

function provenanceBadge(mode) {
  if (!mode) {
    return "";
  }
  return `
    <span class="provenance-badge provenance-badge--${escapeHtml(mode.key)}">
      ${escapeHtml(mode.label)}
    </span>
  `;
}

function renderResponseChips(chips, attribute = "data-response-chip") {
  if (!chips?.length) {
    return "";
  }
  return `
    <div class="chip-row">
      ${chips.map((chip) => `
        <button class="filter-chip" type="button" ${attribute}="${escapeHtml(chip.text)}">
          ${escapeHtml(chip.label)}
        </button>
      `).join("")}
    </div>
  `;
}

function renderMilestoneFilters(snapshot) {
  const filteredMilestones = getVisibleMilestones(snapshot);
  return `
    <div class="filter-row">
      <button class="filter-chip ${hideCompleteMilestones ? "filter-chip--active" : ""}" type="button" data-filter-toggle="hideComplete">
        Hide Complete
      </button>
      <button class="filter-chip ${hideEmptyMilestones ? "filter-chip--active" : ""}" type="button" data-filter-toggle="hideEmpty">
        Hide Empty
      </button>
      <span class="filter-row__meta">${filteredMilestones.length}/${snapshot.milestones.length} milestones shown</span>
    </div>
  `;
}

function renderTaskCard(card) {
  const tags = [
    badge("ID", card.id, "badge--copy"),
    badge("Owner", card.owner_role, `badge--role badge--role-${statusToken(card.owner_role)}`),
  ];
  if (card.assigned_role) {
    tags.push(badge("Assigned", card.assigned_role, `badge--role badge--role-${statusToken(card.assigned_role)}`));
  }
  tags.push(
    badge("Layer", card.layer || "-"),
    badge("Category", card.category || "-"),
    badge("Review", card.review_state || "-", "badge--strong"),
  );
  if (card.milestone_title) {
    tags.push(badge("Milestone", card.milestone_title));
  }
  if (card.secondary_state) {
    tags.push(badge("State", statusLabel(card.secondary_state), "badge--warning"));
  }

  const gateIssues = (card.gate_issues || []).length
    ? `
      <div class="task-card__issues">
        ${(card.gate_issues || []).map((issue) => `<p>${escapeHtml(issue)}</p>`).join("")}
      </div>
    `
    : "";

  const evidenceActions = [];
  if (card.latest_run) {
    evidenceActions.push(evidenceAction(`Run ${card.latest_run.id}`, card.id, "run"));
  }
  if (card.latest_artifact) {
    evidenceActions.push(evidenceAction("Latest Artifact", card.id, "artifact"));
  }
  if (card.latest_validation) {
    evidenceActions.push(evidenceAction(`Validation ${statusLabel(card.latest_validation.status)}`, card.id, "validation"));
  }

  return `
    <article class="task-card">
      <div class="task-card__header">
        ${copyButton(card.copy_text)}
        <span class="task-card__project">${escapeHtml(card.project_label || projectLabel(card.project_name))}</span>
      </div>
      <div class="task-card__title">${escapeHtml(card.title)}</div>
      <div class="task-card__meta">${escapeHtml(card.details)}</div>
      <ul class="badge-list">${tags.join("")}</ul>
      <div class="task-card__path">${escapeHtml(card.expected_artifact_path || "Expected output not recorded yet.")}</div>
      ${gateIssues}
      <div class="task-card__footer">
        <span class="task-card__updated">Updated ${escapeHtml(formatTimestamp(card.updated_at))}</span>
        <div class="task-card__actions">
          ${evidenceActions.length ? evidenceActions.join("") : '<span class="mini-note">No runtime evidence recorded yet.</span>'}
        </div>
      </div>
    </article>
  `;
}

function renderColumn(column) {
  const cards = column.cards.length
    ? column.cards.map(renderTaskCard).join("")
    : `<article class="empty-card">No tasks in this column.</article>`;

  return `
    <section class="board-column">
      <div class="board-column__header">
        <h2>${escapeHtml(column.name)}</h2>
        <span>${column.count}</span>
      </div>
      <div class="board-column__body">${cards}</div>
    </section>
  `;
}

function renderStat(label, value, tone = "") {
  return `
    <article class="stat-card ${tone}">
      <span>${escapeHtml(label)}</span>
      <strong>${escapeHtml(value)}</strong>
    </article>
  `;
}

function renderPlanningWarnings(snapshot) {
  if (!snapshot.planning_warnings?.length) {
    return `
      <section class="panel">
        <div class="panel__header">
          <h2>Planning Checks</h2>
          <span>0 warnings</span>
        </div>
        <article class="empty-card">No planning warnings in the current view.</article>
      </section>
    `;
  }

  return `
    <section class="panel">
      <div class="panel__header">
        <h2>Planning Checks</h2>
        <span>${snapshot.planning_warnings.length} warnings</span>
      </div>
      <div class="stack">
        ${snapshot.planning_warnings.map((warning) => `
          <article class="evidence-card evidence-card--warning">
            <div class="evidence-card__title">${copyButton(warning.task_id, "copy-pill copy-pill--small")} ${escapeHtml(warning.task_title)}</div>
            <ul>
              ${warning.issues.map((issue) => `<li>${escapeHtml(issue)}</li>`).join("")}
            </ul>
          </article>
        `).join("")}
      </div>
    </section>
  `;
}

function renderMilestoneTask(task) {
  const evidenceActions = [];
  if (task.latest_run) {
    evidenceActions.push(evidenceAction("Run", task.id, "run"));
  }
  if (task.latest_artifact) {
    evidenceActions.push(evidenceAction("Artifact", task.id, "artifact"));
  }

  return `
    <li class="milestone-task">
      <div class="milestone-task__left">
        ${copyButton(task.copy_text, "copy-pill copy-pill--small")}
        <div class="milestone-task__copy">
          <span>${escapeHtml(task.title)}</span>
          <span class="milestone-task__role">${escapeHtml(task.assigned_role || task.owner_role || "Role not assigned")}</span>
        </div>
      </div>
      <div class="milestone-task__right">
        ${evidenceActions.length ? `<div class="milestone-task__actions">${evidenceActions.join("")}</div>` : ""}
        <span class="milestone-task__status milestone-task__status--${escapeHtml(statusToken(task.board_column_key))}">
          ${escapeHtml(task.board_column_label)}
        </span>
      </div>
    </li>
  `;
}

function renderMilestoneCard(card) {
  const isCollapsed = Boolean(collapsedMilestones[card.id]);
  const tasks = card.tasks.length
    ? card.tasks.map(renderMilestoneTask).join("")
    : `<li class="milestone-task milestone-task--empty">No tasks linked yet.</li>`;

  return `
    <article class="milestone-card">
      <button class="milestone-card__toggle" type="button" data-milestone-toggle="${escapeHtml(card.id)}" aria-expanded="${isCollapsed ? "false" : "true"}">
        <div class="milestone-card__header">
          <div>
            <p class="milestone-card__project">${escapeHtml(card.project_label)}</p>
            <h2>${escapeHtml(card.title)}</h2>
          </div>
          <div class="milestone-card__summary">
            <strong>${card.completion_percent}%</strong>
            <span>${card.completed_task_count}/${card.task_count}</span>
            <span class="milestone-card__toggle-label">${isCollapsed ? "Show details" : "Hide details"}</span>
          </div>
        </div>
      </button>
      <div class="milestone-card__body ${isCollapsed ? "milestone-card__body--collapsed" : ""}">
        <div class="milestone-card__meta">
          <span>Status: ${escapeHtml(card.status)}</span>
          <span>Entry: ${escapeHtml(card.entry_goal)}</span>
          <span>Exit: ${escapeHtml(card.exit_goal)}</span>
        </div>
        <div class="progress-bar">
          <div class="progress-bar__fill" style="width: ${card.completion_percent}%;"></div>
        </div>
        <ul class="milestone-task-list">${tasks}</ul>
      </div>
    </article>
  `;
}

function getVisibleMilestones(snapshot) {
  return (snapshot.milestones || []).filter((milestone) => {
    if (hideCompleteMilestones && milestone.completion_percent >= 100) {
      return false;
    }
    if (hideEmptyMilestones && milestone.task_count === 0) {
      return false;
    }
    return true;
  });
}

function renderMilestones(snapshot) {
  const milestones = getVisibleMilestones(snapshot);
  if (!snapshot.milestones?.length) {
    return `
      <section class="panel">
        <div class="panel__header">
          <h2>Milestones</h2>
        </div>
        <article class="empty-card">No milestones are defined for the current view yet.</article>
      </section>
    `;
  }

  const milestonesByProject = milestones.reduce((groups, milestone) => {
    const key = milestone.project_name || "unknown";
    if (!groups[key]) {
      groups[key] = [];
    }
    groups[key].push(milestone);
    return groups;
  }, {});

  return `
    <section class="panel">
      <div class="panel__header panel__header--stack">
        <div>
          <h2>Milestones</h2>
          <span>${snapshot.summary.milestone_count} tracked</span>
        </div>
        ${renderMilestoneFilters(snapshot)}
      </div>
      <div class="milestone-project-grid">
        ${milestones.length ? Object.entries(milestonesByProject).map(([projectName, items]) => `
          <section class="milestone-project-column">
            <div class="milestone-project-column__header">
              <p class="eyebrow">Project</p>
              <h3>${escapeHtml(projectLabel(projectName))}</h3>
            </div>
            <div class="milestone-stack">
              ${items.map(renderMilestoneCard).join("")}
            </div>
          </section>
        `).join("") : '<article class="empty-card">All milestones are hidden by the current filters.</article>'}
      </div>
    </section>
  `;
}

function renderBoard(snapshot) {
  return `
    ${renderPlanningWarnings(snapshot)}
    <section class="panel">
      <div class="panel__header">
        <h2>Operator Board</h2>
        <span>${snapshot.summary.status_counts.completed || 0} complete</span>
      </div>
      <div class="board-scroll">
        <div class="board-grid">${snapshot.board.map(renderColumn).join("")}</div>
      </div>
    </section>
  `;
}

function renderProjectRollup(snapshot) {
  if (activeProject !== "all" || !snapshot.project_rollup?.length) {
    return "";
  }

  return `
    <section class="panel">
      <div class="panel__header">
        <h2>Workspace Rollup</h2>
        <span>${snapshot.project_rollup.length} registered projects</span>
      </div>
      <div class="rollup-grid">
        ${snapshot.project_rollup.map((project) => `
          <article class="rollup-card">
            <div class="rollup-card__header">
              <div>
                <p class="rollup-card__eyebrow">Workspace</p>
                <h3>${escapeHtml(project.project_label)}</h3>
              </div>
              <button class="mini-action" type="button" data-project="${escapeHtml(project.project_name)}">Open Board</button>
            </div>
            <p class="rollup-card__path">${escapeHtml(project.root_path)}</p>
            <div class="rollup-card__stats">
              <span>Tasks <strong>${project.task_count}</strong></span>
              <span>Milestones <strong>${project.milestone_count}</strong></span>
              <span>Updated <strong>${escapeHtml(formatTimestamp(project.latest_updated_at))}</strong></span>
            </div>
            <ul class="rollup-status-list">
              ${Object.entries(project.status_counts || {}).map(([key, count]) => `
                <li>
                  <span>${escapeHtml(project.status_labels?.[key] || statusLabel(key))}</span>
                  <strong>${escapeHtml(count)}</strong>
                </li>
              `).join("")}
            </ul>
          </article>
        `).join("")}
      </div>
    </section>
  `;
}

function renderRecentUpdates(snapshot) {
  if (!snapshot.recent_updates?.length) {
    return `
      <section class="panel">
        <div class="panel__header">
          <h2>Recent Updates</h2>
          <span>0 items</span>
        </div>
        <article class="empty-card">No recent runtime updates were found for the current scope.</article>
      </section>
    `;
  }

  return `
    <section class="panel">
      <div class="panel__header">
        <h2>Recent Updates</h2>
        <span>${snapshot.recent_updates.length} most recent events</span>
      </div>
      <div class="updates-grid">
        ${snapshot.recent_updates.map((item) => `
          <article class="evidence-card evidence-card--${escapeHtml(statusToken(item.event_type))}">
            <div class="evidence-card__title">
              ${copyButton(item.task_id || item.run_id || "event", "copy-pill copy-pill--small")}
              <span>${escapeHtml(item.event_label)}</span>
            </div>
            <p class="evidence-card__summary">${escapeHtml(item.summary || "Runtime event recorded.")}</p>
            <div class="evidence-card__meta">
              <span>${escapeHtml(item.project_label || projectLabel(item.project_name))}</span>
              <span>${escapeHtml(formatTimestamp(item.event_at))}</span>
            </div>
            <div class="evidence-card__footer">
              <span>${escapeHtml(item.task_title || item.task_id || item.run_id || "Studio event")}</span>
              <div class="evidence-card__actions">
                ${item.run_id ? evidenceAction("Inspect Run", item.task_id, "run") : ""}
                ${item.artifact_path ? evidenceAction("Inspect Artifact", item.task_id, "artifact") : ""}
              </div>
            </div>
          </article>
        `).join("")}
      </div>
    </section>
  `;
}

function collectTaskCards(snapshot) {
  return (snapshot.board || []).flatMap((column) => column.cards || []);
}

function findTaskCard(snapshot, taskId) {
  return collectTaskCards(snapshot).find((card) => card.id === taskId) || null;
}

function resolveEvidencePayload(snapshot) {
  if (!selectedEvidence || !snapshot) {
    return null;
  }
  const task = findTaskCard(snapshot, selectedEvidence.taskId);
  if (!task) {
    return null;
  }

  if (selectedEvidence.kind === "run" && task.latest_run) {
    return {
      title: `${task.id} latest run`,
      subtitle: task.title,
      rows: [
        ["Run ID", task.latest_run.id],
        ["Status", statusLabel(task.latest_run.status)],
        ["Project", task.project_label],
        ["Created", formatTimestamp(task.latest_run.created_at)],
        ["Completed", formatTimestamp(task.latest_run.completed_at)],
      ],
    };
  }

  if (selectedEvidence.kind === "artifact" && task.latest_artifact) {
    return {
      title: `${task.id} latest artifact`,
      subtitle: task.title,
      rows: [
        ["Artifact", task.latest_artifact.artifact_kind],
        ["Path", task.latest_artifact.artifact_path || "Path not recorded"],
        ["Producer", task.latest_artifact.produced_by || "Unknown"],
        ["Created", formatTimestamp(task.latest_artifact.created_at)],
        ["SHA", task.latest_artifact.artifact_sha256 || "Hash not recorded"],
      ],
    };
  }

  if (selectedEvidence.kind === "validation" && task.latest_validation) {
    return {
      title: `${task.id} latest validation`,
      subtitle: task.title,
      rows: [
        ["Validation ID", task.latest_validation.id],
        ["Status", statusLabel(task.latest_validation.status)],
        ["Validator", task.latest_validation.validator_role],
        ["Artifact", task.latest_validation.artifact_path || "Artifact path not recorded"],
        ["Created", formatTimestamp(task.latest_validation.created_at)],
        ["Summary", task.latest_validation.summary],
      ],
    };
  }

  return null;
}

function renderEvidenceSpotlight(snapshot) {
  const payload = resolveEvidencePayload(snapshot);
  if (!payload) {
    return `
      <section class="panel">
        <div class="panel__header">
          <h2>Evidence Spotlight</h2>
          <span>Waiting for selection</span>
        </div>
        <article class="empty-card">Choose a task Run, Artifact, or Validation action to inspect its latest recorded evidence.</article>
      </section>
    `;
  }

  return `
    <section class="panel">
      <div class="panel__header">
        <h2>Evidence Spotlight</h2>
        <button class="action-button" type="button" data-evidence-clear="true">Clear</button>
      </div>
      <article class="evidence-card evidence-card--spotlight">
        <div class="evidence-card__title">${escapeHtml(payload.title)}</div>
        <p class="evidence-card__summary">${escapeHtml(payload.subtitle)}</p>
        <div class="spotlight-grid">
          ${payload.rows.map(([label, value]) => `
            <div class="spotlight-row">
              <span>${escapeHtml(label)}</span>
              <strong>${escapeHtml(value)}</strong>
            </div>
          `).join("")}
        </div>
      </article>
    </section>
  `;
}

function renderControlRoomGuide(snapshot) {
  return `
    <section class="panel">
      <div class="panel__header panel__header--stack">
        <div>
          <h2>Control Room</h2>
          <span>Use chat for language. Use this page for runtime control and proof.</span>
        </div>
        <div class="hero__meta">Project scope: ${escapeHtml(projectLabel(activeProject))}</div>
      </div>
      <div class="control-room-grid">
        <article class="evidence-card evidence-card--spotlight">
          <div class="evidence-card__title">Recommended Workflow</div>
          <ul class="plain-list">
            <li>Use chat for natural-language requests, clarification, and iteration.</li>
            <li>Use this page to approve work, inspect runs, review artifacts, and validate outcomes.</li>
            <li>Use web dispatch only for bounded direct actions or when chat is not the active surface.</li>
          </ul>
        </article>
        <article class="evidence-card">
          <div class="evidence-card__title">Live Control Summary</div>
          <div class="spotlight-grid">
            <div class="spotlight-row"><span>Pending approvals</span><strong>${escapeHtml(snapshot.pending_approvals?.length || 0)}</strong></div>
            <div class="spotlight-row"><span>Recent runs</span><strong>${escapeHtml(snapshot.recent_runs?.length || 0)}</strong></div>
            <div class="spotlight-row"><span>Current project</span><strong>${escapeHtml(projectLabel(activeProject))}</strong></div>
            <div class="spotlight-row"><span>Runtime mode</span><strong>${escapeHtml(statusLabel(snapshot.system_health?.runtime_mode || "custom"))}</strong></div>
          </div>
        </article>
      </div>
    </section>
  `;
}

function renderSystemHealthStrip(snapshot) {
  const health = snapshot.system_health || {};
  const store = health.store || {};
  const lastBackup = health.last_backup;
  const lastRun = health.last_run;
  const healthCheck = health.last_health_check || {};

  return `
    <section class="health-strip panel">
      <article class="health-pill">
        <span>Runtime Mode</span>
        <strong>${escapeHtml(statusLabel(health.runtime_mode || "custom"))}</strong>
      </article>
      <article class="health-pill">
        <span>Last Backup</span>
        <strong>${escapeHtml(lastBackup ? formatTimestamp(lastBackup.created_at) : "None recorded")}</strong>
      </article>
      <article class="health-pill">
        <span>Last Run</span>
        <strong>${escapeHtml(lastRun ? `${lastRun.id} • ${statusLabel(lastRun.status)}` : "No runs yet")}</strong>
      </article>
      <article class="health-pill">
        <span>Pending Approvals</span>
        <strong>${escapeHtml(snapshot.pending_approvals?.length || 0)}</strong>
      </article>
      <article class="health-pill health-pill--${store.ok ? "ok" : "warning"}">
        <span>Store Health</span>
        <strong>${escapeHtml(store.ok ? "Healthy" : `${store.issue_count || 0} issue(s)`)}</strong>
      </article>
      <article class="health-pill">
        <span>Last Health Check</span>
        <strong>${escapeHtml(healthCheck.generated_at ? formatTimestamp(healthCheck.generated_at) : "Not recorded")}</strong>
      </article>
    </section>
  `;
}

function renderBackupRestorePanel(snapshot) {
  const backups = snapshot.system_health?.available_backups || [];
  return `
    <section class="panel panel--subsection">
      <div class="panel__header panel__header--stack">
        <div>
          <h2>Safety Backups</h2>
          <span>Restore from a recorded SQLite snapshot with an automatic pre-restore safety copy.</span>
        </div>
        <div class="hero__meta">${backups.length} backup${backups.length === 1 ? "" : "s"} available</div>
      </div>
      ${restoreError ? `<article class="evidence-card evidence-card--warning"><div class="evidence-card__title">Restore error</div><ul><li>${escapeHtml(restoreError)}</li></ul></article>` : ""}
      ${restoreOutcome ? `
        <article class="evidence-card evidence-card--spotlight">
          <div class="evidence-card__title">Latest Restore Result</div>
          <p class="evidence-card__summary">Restored from ${escapeHtml(restoreOutcome.restored_from?.backup_id || "backup")} at ${escapeHtml(formatTimestamp(restoreOutcome.restored_at))}.</p>
          <div class="spotlight-grid">
            <div class="spotlight-row"><span>Pre-restore safety backup</span><strong>${escapeHtml(restoreOutcome.pre_restore_backup?.backup_id || "Not recorded")}</strong></div>
            <div class="spotlight-row"><span>Receipt</span><strong>${escapeHtml(restoreOutcome.receipt_path || "Not recorded")}</strong></div>
            <div class="spotlight-row"><span>Store SHA</span><strong>${escapeHtml(restoreOutcome.store_sha256 || "Not recorded")}</strong></div>
            <div class="spotlight-row"><span>Projects rendered</span><strong>${escapeHtml((restoreOutcome.restored_projects || []).join(", ") || "Not recorded")}</strong></div>
          </div>
        </article>
      ` : ""}
      <div class="updates-grid">
        ${backups.map((backup) => `
          <article class="evidence-card">
            <div class="evidence-card__title">
              ${copyButton(backup.backup_id, "copy-pill copy-pill--small")}
              <span>${escapeHtml(statusLabel(backup.trigger || "dispatch backup"))}</span>
            </div>
            <p class="evidence-card__summary">${escapeHtml(backup.note || "Safety backup captured by the framework.")}</p>
            <div class="spotlight-grid">
              <div class="spotlight-row"><span>Created</span><strong>${escapeHtml(formatTimestamp(backup.created_at))}</strong></div>
              <div class="spotlight-row"><span>Project</span><strong>${escapeHtml(projectLabel(backup.project_name || activeProject))}</strong></div>
              <div class="spotlight-row"><span>Size</span><strong>${escapeHtml(formatBytes(backup.bytes))}</strong></div>
              <div class="spotlight-row"><span>Exists</span><strong>${backup.exists ? "Yes" : "Missing"}</strong></div>
            </div>
            <div class="task-card__path">${escapeHtml(backup.path || "Path not recorded.")}</div>
            <div class="operator-action-row">
              <button
                class="action-button action-button--primary"
                type="button"
                data-backup-restore="${escapeHtml(backup.backup_id)}"
                ${!backup.exists || restoreBusyId ? "disabled" : ""}
              >
                ${restoreBusyId === backup.backup_id ? "Restoring..." : "Restore Backup"}
              </button>
            </div>
          </article>
        `).join("") || '<article class="empty-card">No framework backups are recorded for this scope yet.</article>'}
      </div>
    </section>
  `;
}

function renderOperatorPreview() {
  if (!operatorPreview) {
    return `
      <article class="empty-card">Use Preview Web Dispatch only when you want to send a bounded request from the page itself.</article>
    `;
  }

  const packet = operatorPreview.packet || {};
  const brief = operatorPreview.operator_brief || {};
  const previewProjectName = operatorPreview.project_name || activeProject;
  const operatorAction = operatorPreview.operator_action || null;
  return `
    <div class="stack">
      <article class="evidence-card evidence-card--spotlight">
        <div class="evidence-card__title">Web Dispatch Preview</div>
        <p class="evidence-card__summary">${escapeHtml(packet.objective || "No objective captured.")}</p>
        <div class="spotlight-grid">
          <div class="spotlight-row"><span>Priority</span><strong>${escapeHtml(packet.priority || "medium")}</strong></div>
          <div class="spotlight-row"><span>Approval Gate</span><strong>${packet.requires_approval ? "Required" : "Not Required"}</strong></div>
          <div class="spotlight-row"><span>Project</span><strong>${escapeHtml(projectLabel(previewProjectName))}</strong></div>
          <div class="spotlight-row"><span>Mode</span><strong>${escapeHtml(operatorAction ? "Direct board action" : "Delegated run")}</strong></div>
        </div>
        <div class="operator-preview__body">
          <div>
            <h3>Details</h3>
            <p>${escapeHtml(packet.details || "No details recorded.")}</p>
          </div>
          <div>
            <h3>Assumptions</h3>
            <ul class="plain-list">${(brief.assumptions || []).map((item) => `<li>${escapeHtml(item)}</li>`).join("") || "<li>No assumptions recorded.</li>"}</ul>
          </div>
          <div>
            <h3>Risks</h3>
            <ul class="plain-list">${(brief.risks || []).map((item) => `<li>${escapeHtml(item)}</li>`).join("") || "<li>No risks recorded.</li>"}</ul>
          </div>
          <div>
            <h3>Clarifications</h3>
            <ul class="plain-list">${(brief.questions || []).map((item) => `<li>${escapeHtml(item)}</li>`).join("") || "<li>No follow-up questions in this pass.</li>"}</ul>
          </div>
        </div>
        ${renderResponseChips(brief.response_chips || [])}
        <div class="operator-action-row">
          <button class="action-button action-button--primary" type="button" data-operator-dispatch="true" ${operatorRequestBusy ? "disabled" : ""}>Confirm Web Dispatch</button>
          <button class="action-button" type="button" data-operator-clear-preview="true">Clear Preview</button>
        </div>
      </article>
      <section class="panel">
        <div class="panel__header">
          <h2>Dispatch Route Preview</h2>
          <span>${(operatorPreview.route_preview || []).length} roles</span>
        </div>
        <div class="route-grid">
          ${(operatorPreview.route_preview || []).map((route) => `
            <article class="route-card">
              <p class="route-card__eyebrow">${escapeHtml(route.profile_label)}</p>
              <h3>${escapeHtml(route.runtime_role)}</h3>
              <p>${escapeHtml(route.route_reason)}</p>
              <ul class="plain-list">
                <li>Model: ${escapeHtml(route.model)}</li>
                <li>Depth: ${escapeHtml(route.reasoning_depth)}</li>
                <li>Cost tier: ${escapeHtml(route.cost_tier)}</li>
              </ul>
            </article>
          `).join("")}
        </div>
      </section>
    </div>
  `;
}

function renderWebDispatchPanel() {
  return `
    <section class="panel panel--subsection">
      <div class="panel__header panel__header--stack">
        <div>
          <h2>Optional Web Dispatch</h2>
          <span>Secondary to chat. Best for bounded direct actions and quick runtime requests.</span>
        </div>
      </div>
      <div class="operator-intake-grid">
        <label class="form-field">
          <span>Request</span>
          <textarea id="operator-request" rows="5" placeholder="Use this for bounded requests or direct board actions.">${escapeHtml(operatorDraft.text)}</textarea>
        </label>
        <label class="form-field">
          <span>Clarification Notes</span>
          <textarea id="operator-clarification" rows="5" placeholder="Optional: scope, proof, or approval notes.">${escapeHtml(operatorDraft.clarification)}</textarea>
        </label>
      </div>
      ${renderResponseChips([
        { label: "Keep Scope Tight", text: "Keep the implementation to one bounded slice." },
        { label: "Need Proof", text: "Include explicit proof and evidence in the final result." },
        { label: "Planning Only", text: "Limit this pass to planning and operator review only." },
        { label: "Use Current Project", text: "Use the currently selected project." },
      ])}
      <div class="operator-action-row">
        <button class="action-button action-button--primary" type="button" data-operator-preview="true" ${operatorRequestBusy ? "disabled" : ""}>Preview Web Dispatch</button>
        <button class="action-button" type="button" data-operator-reset="true">Reset Web Draft</button>
      </div>
      ${operatorRequestError ? `<article class="evidence-card evidence-card--warning"><div class="evidence-card__title">Web dispatch error</div><ul><li>${escapeHtml(operatorRequestError)}</li></ul></article>` : ""}
      ${renderOperatorPreview()}
    </section>
  `;
}

function renderApprovalInbox(snapshot) {
  if (!snapshot.pending_approvals?.length) {
    return `
      <section class="panel">
        <div class="panel__header">
          <h2>Approval Inbox</h2>
          <span>0 pending</span>
        </div>
        <article class="empty-card">No pending approvals for the current scope.</article>
      </section>
    `;
  }

  return `
    <section class="panel">
      <div class="panel__header">
        <h2>Approval Inbox</h2>
        <span>${snapshot.pending_approvals.length} pending</span>
      </div>
      <div class="updates-grid">
        ${snapshot.pending_approvals.map((approval) => `
          <article class="evidence-card">
            <div class="evidence-card__title">
              ${copyButton(approval.id, "copy-pill copy-pill--small")}
              <span>${escapeHtml(approval.task_title)}</span>
              ${provenanceBadge(approval.action_mode)}
            </div>
            <p class="evidence-card__summary">${escapeHtml(approval.reason || "Approval request recorded.")}</p>
            <div class="spotlight-grid">
              <div class="spotlight-row"><span>Requested by</span><strong>${escapeHtml(approval.requested_by || "Unknown")}</strong></div>
              <div class="spotlight-row"><span>Target</span><strong>${escapeHtml(approval.target_role || "Unknown")}</strong></div>
              <div class="spotlight-row"><span>Scope</span><strong>${escapeHtml(statusLabel(approval.approval_scope || "project"))}</strong></div>
              <div class="spotlight-row"><span>Task status</span><strong>${escapeHtml(statusLabel(approval.task_status || "unknown"))}</strong></div>
              <div class="spotlight-row"><span>Expected</span><strong>${escapeHtml(approval.expected_output || "Not recorded")}</strong></div>
              ${approval.sdk_bridge?.runtime_mode ? `<div class="spotlight-row"><span>Runtime</span><strong>${escapeHtml(statusLabel(approval.sdk_bridge.runtime_mode))}</strong></div>` : ""}
              ${approval.sdk_bridge?.session_id ? `<div class="spotlight-row"><span>SDK Session</span><strong>${escapeHtml(approval.sdk_bridge.session_id)}</strong></div>` : ""}
            </div>
            <div class="approval-context-grid">
              <article class="evidence-card evidence-card--muted">
                <div class="evidence-card__title">Upstream Context</div>
                <ul class="plain-list">
                  <li>Exact ask: ${escapeHtml(approval.upstream_context?.exact_task || "Not recorded")}</li>
                  <li>Why now: ${escapeHtml(approval.upstream_context?.why_now || "Not recorded")}</li>
                  <li>Latest signal: ${escapeHtml(approval.upstream_context?.latest_signal || "Not recorded")}</li>
                  <li>Latest artifact: ${escapeHtml(approval.upstream_context?.latest_artifact_path || "Not recorded")}</li>
                  <li>Latest validation: ${escapeHtml(approval.upstream_context?.latest_validation_summary || "Not recorded")}</li>
                </ul>
              </article>
              <article class="evidence-card evidence-card--muted">
                <div class="evidence-card__title">Downstream Context</div>
                <ul class="plain-list">
                  <li>Next role: ${escapeHtml(approval.downstream_context?.target_role || approval.target_role || "Not recorded")}</li>
                  <li>Output target: ${escapeHtml(approval.downstream_context?.expected_output || approval.expected_output || "Not recorded")}</li>
                  <li>${escapeHtml(approval.downstream_context?.continuation_summary || "No downstream summary recorded.")}</li>
                </ul>
              </article>
            </div>
            <ul class="plain-list">${(approval.risks || []).map((item) => `<li>${escapeHtml(item)}</li>`).join("") || "<li>No explicit risks recorded.</li>"}</ul>
            <div class="operator-action-row">
              <button class="action-button action-button--primary" type="button" data-operator-approve="${escapeHtml(approval.id)}" data-operator-run="${escapeHtml(approval.run_id)}">Approve</button>
              <button class="action-button" type="button" data-operator-approve-resume="${escapeHtml(approval.id)}" data-operator-run="${escapeHtml(approval.run_id)}">Approve And Continue</button>
              <button class="action-button" type="button" data-operator-reject="${escapeHtml(approval.id)}">Reject</button>
            </div>
          </article>
        `).join("")}
      </div>
    </section>
  `;
}

function renderRunList(snapshot) {
  if (!snapshot.recent_runs?.length) {
    return `
      <section class="panel">
        <div class="panel__header">
          <h2>Recent Runs</h2>
          <span>0 runs</span>
        </div>
        <article class="empty-card">No runs recorded for the current scope yet.</article>
      </section>
    `;
  }

  return `
    <section class="panel">
      <div class="panel__header">
        <h2>Recent Runs</h2>
        <span>${snapshot.recent_runs.length} recent</span>
      </div>
      <div class="stack">
        ${snapshot.recent_runs.map((run) => `
          <article class="evidence-card ${selectedRunId === run.id ? "evidence-card--spotlight" : ""}">
            <div class="evidence-card__title">${copyButton(run.id, "copy-pill copy-pill--small")} ${escapeHtml(run.task_title)}</div>
            <div class="evidence-card__meta">
              <span>${escapeHtml(statusLabel(run.status))}</span>
              <span>${escapeHtml(formatTimestamp(run.created_at))}</span>
            </div>
            <div class="operator-action-row">
              <button class="action-button" type="button" data-run-inspect="${escapeHtml(run.id)}">Inspect Run</button>
              ${run.status === "paused_approval" ? `<button class="action-button" type="button" data-run-resume="${escapeHtml(run.id)}">Resume Run</button>` : ""}
            </div>
          </article>
        `).join("")}
      </div>
    </section>
  `;
}

function renderTraceEvent(event) {
  const payload = event.payload || {};
  const route = payload.route || {};
  const actionMode = resolveActionMode({
    runtimeRole: route.runtime_role,
    source: event.source,
    eventType: event.event_type,
  });
  return `
    <article class="evidence-card evidence-card--${escapeHtml(statusToken(event.event_type))}">
      <div class="evidence-card__title">
        ${copyButton(event.id, "copy-pill copy-pill--small")}
        <span>${escapeHtml(event.event_type)}</span>
        ${provenanceBadge(actionMode)}
      </div>
      <p class="evidence-card__summary">${escapeHtml(payload.summary || "Trace event recorded.")}</p>
      <div class="evidence-card__meta">
        <span>${escapeHtml(event.source || "Unknown source")}</span>
        <span>${escapeHtml(formatTimestamp(event.created_at))}</span>
      </div>
      ${route.runtime_role ? `
        <ul class="plain-list">
          <li>Route: ${escapeHtml(route.runtime_role)} via ${escapeHtml(route.model || "unknown model")}</li>
          <li>Reason: ${escapeHtml(route.route_reason || "No route reason recorded.")}</li>
        </ul>
      ` : ""}
      <details class="raw-json">
        <summary>Raw JSON</summary>
        <pre>${escapeHtml(JSON.stringify(payload.raw_json || payload.packet || payload, null, 2))}</pre>
      </details>
    </article>
  `;
}

function buildRunTimeline(evidence) {
  if (!evidence) {
    return [];
  }
  const timeline = [];
  const run = evidence.run || {};
  if (run.id) {
    timeline.push({
      id: `${run.id}-created`,
      timestamp: run.created_at,
      title: "Run Created",
      summary: `Run ${run.id} started for ${evidence.task?.title || evidence.task?.id || "the selected task"}.`,
      mode: resolveActionMode({ runtimeRole: "Orchestrator", source: "Orchestrator", eventType: "run_created" }),
      details: [
        ["Status", statusLabel(run.status)],
        ["Stop reason", run.stop_reason || "Not recorded"],
      ],
    });
  }

  (evidence.approvals || []).forEach((approval) => {
    timeline.push({
      id: approval.id,
      timestamp: approval.decided_at || approval.created_at,
      title: `Approval ${statusLabel(approval.status)}`,
      summary: approval.reason || approval.decision_note || "Approval event recorded.",
      mode: resolveActionMode({ runtimeRole: "Orchestrator", source: approval.requested_by, eventType: "approval" }),
      details: [
        ["Requested by", approval.requested_by || "Unknown"],
        ["Target", approval.target_role || "Not recorded"],
        ["Expected output", approval.expected_output || "Not recorded"],
      ],
    });
  });

  (evidence.trace_events || []).forEach((event) => {
    const payload = event.payload || {};
    const route = payload.route || {};
    timeline.push({
      id: event.id,
      timestamp: event.created_at,
      title: statusLabel(event.event_type),
      summary: payload.summary || "Trace event recorded.",
      mode: resolveActionMode({
        runtimeRole: route.runtime_role,
        source: event.source,
        eventType: event.event_type,
      }),
      details: [
        ["Source", event.source || "Unknown source"],
        ["Route", route.runtime_role || "Framework"],
        ["Model", route.model || "Not recorded"],
      ],
    });
  });

  (evidence.agent_runs || []).forEach((agentRun) => {
    timeline.push({
      id: agentRun.id,
      timestamp: agentRun.completed_at || agentRun.started_at,
      title: `${agentRun.role} ${statusLabel(agentRun.status)}`,
      summary: agentRun.notes || `${agentRun.role} recorded a ${agentRun.status} specialist run.`,
      mode: resolveActionMode({ runtimeRole: agentRun.role, source: agentRun.role, eventType: "agent_run" }),
      details: [
        ["Output", agentRun.output_artifact_path || "Not recorded"],
        ["PID", agentRun.pid || "Not recorded"],
      ],
    });
  });

  (evidence.artifacts || []).forEach((artifact) => {
    timeline.push({
      id: artifact.id,
      timestamp: artifact.created_at,
      title: `Artifact ${artifact.kind}`,
      summary: artifact.artifact_path || "Runtime artifact recorded.",
      mode: resolveActionMode({ runtimeRole: artifact.produced_by, source: artifact.produced_by, eventType: "artifact" }),
      details: [
        ["Produced by", artifact.produced_by || "Unknown"],
        ["SHA", artifact.artifact_sha256 || "Not recorded"],
      ],
    });
  });

  (evidence.validations || []).forEach((validation) => {
    timeline.push({
      id: validation.id,
      timestamp: validation.created_at,
      title: `Validation ${statusLabel(validation.status)}`,
      summary: validation.summary,
      mode: resolveActionMode({ runtimeRole: validation.validator_role, source: validation.validator_role, eventType: "validation" }),
      details: [
        ["Validator", validation.validator_role || "Unknown"],
        ["Artifact", validation.artifact_path || "Not recorded"],
      ],
    });
  });

  return timeline
    .filter((item) => item.timestamp)
    .sort((left, right) => new Date(left.timestamp).getTime() - new Date(right.timestamp).getTime());
}

function renderTimelineItem(item) {
  return `
    <article class="timeline-item timeline-item--${escapeHtml(item.mode.key)}">
      <div class="timeline-item__rail">
        <span class="timeline-item__dot"></span>
      </div>
      <div class="timeline-item__content">
        <div class="timeline-item__header">
          <div>
            <div class="evidence-card__title">${escapeHtml(item.title)}</div>
            <p class="evidence-card__summary">${escapeHtml(item.summary)}</p>
          </div>
          <div class="timeline-item__meta">
            ${provenanceBadge(item.mode)}
            <span>${escapeHtml(formatTimestamp(item.timestamp))}</span>
          </div>
        </div>
        <div class="spotlight-grid">
          ${(item.details || []).map(([label, value]) => `
            <div class="spotlight-row">
              <span>${escapeHtml(label)}</span>
              <strong>${escapeHtml(value)}</strong>
            </div>
          `).join("")}
        </div>
      </div>
    </article>
  `;
}

function renderRouteCatalog(routes) {
  if (!routes?.length) {
    return '<article class="empty-card">No role routing metadata recorded.</article>';
  }
  return `
    <div class="route-grid">
      ${routes.map((route) => `
        <article class="route-card">
          <p class="route-card__eyebrow">${escapeHtml(route.profile_label)}</p>
          <h3>${escapeHtml(route.runtime_role)}</h3>
          <p>${escapeHtml(route.profile_summary)}</p>
          <ul class="plain-list">
            <li>Model: ${escapeHtml(route.model)}</li>
            <li>Depth: ${escapeHtml(route.reasoning_depth)}</li>
            <li>Cost tier: ${escapeHtml(route.cost_tier)}</li>
            <li>Skills: ${escapeHtml((route.skill_metadata || []).map((item) => item.name).join(", ") || "None")}</li>
          </ul>
        </article>
      `).join("")}
    </div>
  `;
}

function renderSdkRuntimeSection(sdkRuntime) {
  if (!sdkRuntime) {
    return "";
  }

  const sessions = sdkRuntime.sessions || [];
  const approvalBridgeEvents = sdkRuntime.approval_bridge_events || [];
  return `
    <section class="panel panel--subsection">
      <div class="panel__header"><h2>SDK Runtime</h2><span>${escapeHtml(sdkRuntime.specialist_run_count || 0)} specialist runs</span></div>
      <div class="spotlight-grid">
        <div class="spotlight-row"><span>Mode</span><strong>${escapeHtml(statusLabel(sdkRuntime.mode || "sdk"))}</strong></div>
        <div class="spotlight-row"><span>Orchestrator Source</span><strong>${escapeHtml(sdkRuntime.orchestrator_source || "chat_or_control_room")}</strong></div>
        <div class="spotlight-row"><span>Planning Layer</span><strong>${escapeHtml(sdkRuntime.planning_layer || "Not recorded")}</strong></div>
        <div class="spotlight-row"><span>Approval Events</span><strong>${escapeHtml(approvalBridgeEvents.length)}</strong></div>
      </div>
      <div class="updates-grid">
        ${sessions.map((session) => `
          <article class="evidence-card">
            <div class="evidence-card__title">${copyButton(session.session_id || session.role || "sdk-session", "copy-pill copy-pill--small")} ${escapeHtml(session.role || "SDK Specialist")}</div>
            <p class="evidence-card__summary">${escapeHtml(session.model || "Model not recorded")}</p>
            <div class="spotlight-grid">
              <div class="spotlight-row"><span>Session</span><strong>${escapeHtml(session.session_id || "Not recorded")}</strong></div>
              <div class="spotlight-row"><span>Response</span><strong>${escapeHtml(session.response_id || "Not recorded")}</strong></div>
              <div class="spotlight-row"><span>Trace</span><strong>${escapeHtml(session.trace_id || "Not recorded")}</strong></div>
              <div class="spotlight-row"><span>Recorded</span><strong>${escapeHtml(formatTimestamp(session.created_at))}</strong></div>
            </div>
          </article>
        `).join("") || '<article class="empty-card">No SDK specialist sessions were mirrored for this run.</article>'}
      </div>
      <div class="stack">
        ${approvalBridgeEvents.map((event) => `
          <article class="evidence-card evidence-card--spotlight">
            <div class="evidence-card__title">${escapeHtml(event.event_type || "sdk_bridge_event")}</div>
            <p class="evidence-card__summary">${escapeHtml(event.target_role || "Specialist")} approval bridge</p>
            <div class="spotlight-grid">
              <div class="spotlight-row"><span>Approval</span><strong>${escapeHtml(event.approval_id || "Not recorded")}</strong></div>
              <div class="spotlight-row"><span>Session</span><strong>${escapeHtml(event.session_id || "Not recorded")}</strong></div>
              <div class="spotlight-row"><span>Artifact</span><strong>${escapeHtml(event.expected_artifact_path || "Not recorded")}</strong></div>
              <div class="spotlight-row"><span>When</span><strong>${escapeHtml(formatTimestamp(event.created_at))}</strong></div>
            </div>
          </article>
        `).join("") || ""}
      </div>
    </section>
  `;
}

function renderRunInspector() {
  if (runInspectorLoading) {
    return `
      <section class="panel">
        <div class="panel__header">
          <h2>Run Inspector</h2>
          <span>Loading</span>
        </div>
        <article class="empty-card">Loading run details from the framework runtime.</article>
      </section>
    `;
  }

  if (runInspectorError) {
    return `
      <section class="panel">
        <div class="panel__header">
          <h2>Run Inspector</h2>
          <span>Error</span>
        </div>
        <article class="evidence-card evidence-card--warning">
          <div class="evidence-card__title">Run details unavailable</div>
          <ul><li>${escapeHtml(runInspectorError)}</li></ul>
        </article>
      </section>
    `;
  }

  if (!selectedRunEvidence) {
    return `
      <section class="panel">
        <div class="panel__header">
          <h2>Run Inspector</h2>
          <span>Waiting for selection</span>
        </div>
        <article class="empty-card">Inspect a run to view the trace ledger, approvals, delegations, artifacts, validations, and route metadata.</article>
      </section>
    `;
  }

  const run = selectedRunEvidence.run || {};
  const task = selectedRunEvidence.task || {};
  const finalTrace = (selectedRunEvidence.trace_events || []).filter((item) => item.event_type === "orchestrator_final_summary").slice(-1)[0];
  const timeline = buildRunTimeline(selectedRunEvidence);
  return `
    <section class="panel">
      <div class="panel__header panel__header--stack">
        <div>
          <h2>Run Inspector</h2>
          <span>${escapeHtml(run.id || "Unknown run")} for ${escapeHtml(task.title || task.id || "Unknown task")}</span>
        </div>
        <div class="operator-action-row">
          ${run.status === "paused_approval" ? `<button class="action-button" type="button" data-run-resume="${escapeHtml(run.id)}">Resume Run</button>` : ""}
          <button class="action-button" type="button" data-run-refresh="${escapeHtml(run.id)}">Refresh Inspector</button>
        </div>
      </div>
      <div class="spotlight-grid">
        <div class="spotlight-row"><span>Status</span><strong>${escapeHtml(statusLabel(run.status))}</strong></div>
        <div class="spotlight-row"><span>Created</span><strong>${escapeHtml(formatTimestamp(run.created_at))}</strong></div>
        <div class="spotlight-row"><span>Completed</span><strong>${escapeHtml(formatTimestamp(run.completed_at))}</strong></div>
        <div class="spotlight-row"><span>Stop Reason</span><strong>${escapeHtml(run.stop_reason || "Not recorded")}</strong></div>
      </div>
      ${finalTrace ? `<article class="evidence-card evidence-card--spotlight"><div class="evidence-card__title">Final Summary</div><p class="evidence-card__summary">${escapeHtml(finalTrace.payload?.summary || "No final summary recorded.")}</p></article>` : ""}
      ${renderSdkRuntimeSection(selectedRunEvidence.sdk_runtime)}
      <section class="panel panel--subsection">
        <div class="panel__header"><h2>Run Timeline</h2><span>${timeline.length} steps</span></div>
        <div class="timeline">
          ${timeline.map(renderTimelineItem).join("") || '<article class="empty-card">No timeline items recorded.</article>'}
        </div>
      </section>
      <section class="panel panel--subsection">
        <div class="panel__header"><h2>Trace Ledger</h2><span>${(selectedRunEvidence.trace_events || []).length} events</span></div>
        <div class="stack">${(selectedRunEvidence.trace_events || []).map(renderTraceEvent).join("") || '<article class="empty-card">No trace events recorded.</article>'}</div>
      </section>
      <section class="panel panel--subsection">
        <div class="panel__header"><h2>Delegations</h2><span>${(selectedRunEvidence.delegations || []).length} edges</span></div>
        <div class="stack">
          ${(selectedRunEvidence.delegations || []).map((edge) => `
            <article class="evidence-card">
              <div class="evidence-card__title">${copyButton(edge.id, "copy-pill copy-pill--small")} ${escapeHtml(edge.from_role)} -> ${escapeHtml(edge.to_role)}</div>
              <p class="evidence-card__summary">${escapeHtml(edge.note)}</p>
            </article>
          `).join("") || '<article class="empty-card">No delegation edges recorded.</article>'}
        </div>
      </section>
      <section class="panel panel--subsection">
        <div class="panel__header"><h2>Artifacts And Validation</h2><span>${(selectedRunEvidence.artifacts || []).length} artifacts / ${(selectedRunEvidence.validations || []).length} validations</span></div>
        <div class="updates-grid">
          ${(selectedRunEvidence.artifacts || []).map((artifact) => `
            <article class="evidence-card">
              <div class="evidence-card__title">${copyButton(artifact.id, "copy-pill copy-pill--small")} ${escapeHtml(artifact.kind)}</div>
              <p class="evidence-card__summary">${escapeHtml(artifact.artifact_path || "No artifact path recorded.")}</p>
            </article>
          `).join("")}
          ${(selectedRunEvidence.validations || []).map((validation) => `
            <article class="evidence-card">
              <div class="evidence-card__title">${copyButton(validation.id, "copy-pill copy-pill--small")} Validation ${escapeHtml(statusLabel(validation.status))}</div>
              <p class="evidence-card__summary">${escapeHtml(validation.summary)}</p>
            </article>
          `).join("")}
          ${(!(selectedRunEvidence.artifacts || []).length && !(selectedRunEvidence.validations || []).length) ? '<article class="empty-card">No artifacts or validations recorded.</article>' : ""}
        </div>
      </section>
      <section class="panel panel--subsection">
        <div class="panel__header"><h2>Role Routing</h2><span>${(selectedRunEvidence.routing_catalog || []).length} profiles</span></div>
        ${renderRouteCatalog(selectedRunEvidence.routing_catalog || [])}
      </section>
    </section>
  `;
}

function renderOrchestrator(snapshot) {
  if (activeProject === "all") {
    return `
      <section class="panel">
        <div class="panel__header">
          <h2>Control Room</h2>
        </div>
        <article class="empty-card">Choose a specific project first. The control room manages one project at a time.</article>
      </section>
    `;
  }

  return `
    ${renderControlRoomGuide(snapshot)}
    ${renderBackupRestorePanel(snapshot)}
    ${renderApprovalInbox(snapshot)}
    ${renderRunList(snapshot)}
    ${renderRunInspector()}
    ${renderWebDispatchPanel()}
  `;
}

async function previewOperatorRequest() {
  if (!operatorDraft.text.trim()) {
    operatorRequestError = "Enter a request before previewing the web dispatch.";
    renderSnapshot(currentSnapshot);
    return;
  }
  operatorRequestBusy = true;
  operatorRequestError = null;
  renderSnapshot(currentSnapshot);
  try {
    operatorPreview = await requestJson("/api/operator/preview", {
      method: "POST",
      body: JSON.stringify({
        project_name: activeProject,
        text: operatorDraft.text,
        clarification: operatorDraft.clarification,
      }),
    });
    showToast("Web dispatch preview ready");
  } catch (error) {
    operatorRequestError = error instanceof Error ? error.message : String(error);
  } finally {
    operatorRequestBusy = false;
    renderSnapshot(currentSnapshot);
  }
}

async function dispatchOperatorRequest() {
  if (!operatorDraft.text.trim()) {
    operatorRequestError = "Enter a request before sending a web dispatch.";
    renderSnapshot(currentSnapshot);
    return;
  }
  operatorRequestBusy = true;
  operatorRequestError = null;
  renderSnapshot(currentSnapshot);
  try {
    const payload = await requestJson("/api/operator/dispatch", {
      method: "POST",
      body: JSON.stringify({
        project_name: activeProject,
        text: operatorDraft.text,
        clarification: operatorDraft.clarification,
      }),
    });
    operatorPreview = payload.preview || null;
    if (payload.preview?.project_name && payload.preview.project_name !== activeProject) {
      activeProject = payload.preview.project_name;
      syncUrl();
    }
    if (payload.run_evidence?.run?.id) {
      selectedRunId = payload.run_evidence.run.id;
      selectedRunEvidence = payload.run_evidence;
    }
    showToast(payload.run_result?.result_summary || "Request dispatched through the framework");
    await fetchSnapshot();
  } catch (error) {
    operatorRequestError = error instanceof Error ? error.message : String(error);
  } finally {
    operatorRequestBusy = false;
    renderSnapshot(currentSnapshot);
  }
}

async function loadRunEvidence(runId, { silent = false } = {}) {
  if (!silent) {
    runInspectorLoading = true;
    runInspectorError = null;
    selectedRunId = runId;
    renderSnapshot(currentSnapshot);
  }
  try {
    selectedRunEvidence = await requestJson(`/api/operator/run?run_id=${encodeURIComponent(runId)}`);
    selectedRunId = runId;
  } catch (error) {
    runInspectorError = error instanceof Error ? error.message : String(error);
  } finally {
    runInspectorLoading = false;
    renderSnapshot(currentSnapshot);
  }
}

async function approveOperatorApproval(approvalId, runId, { resume = false } = {}) {
  try {
    const endpoint = resume ? "/api/operator/approve-resume" : "/api/operator/approve";
    const payload = await requestJson(endpoint, {
      method: "POST",
      body: JSON.stringify({ approval_id: approvalId }),
    });
    if (runId) {
      selectedRunId = runId;
    }
    if (resume) {
      if (payload.run_evidence) {
        selectedRunEvidence = payload.run_evidence;
      } else if (runId) {
        selectedRunEvidence = await requestJson(`/api/operator/run?run_id=${encodeURIComponent(runId)}`);
      }
      showToast(payload.message || "Approval granted and run continued");
    } else {
      showToast("Approval granted");
    }
    await fetchSnapshot();
    if (!resume && runId) {
      await loadRunEvidence(runId, { silent: true });
    }
  } catch (error) {
    operatorRequestError = error instanceof Error ? error.message : String(error);
    renderSnapshot(currentSnapshot);
  }
}

async function rejectOperatorApproval(approvalId) {
  try {
    await requestJson("/api/operator/reject", {
      method: "POST",
      body: JSON.stringify({ approval_id: approvalId }),
    });
    showToast("Approval rejected");
    await fetchSnapshot();
  } catch (error) {
    operatorRequestError = error instanceof Error ? error.message : String(error);
    renderSnapshot(currentSnapshot);
  }
}

async function resumeOperatorRun(runId) {
  try {
    const payload = await requestJson("/api/operator/resume", {
      method: "POST",
      body: JSON.stringify({ run_id: runId }),
    });
    selectedRunId = runId;
    selectedRunEvidence = payload.run_evidence || selectedRunEvidence;
    if (payload.status === "already_progressed") {
      showToast(payload.message || "Run already moved forward");
    } else if (payload.status === "awaiting_approval") {
      showToast(payload.message || "Run is still waiting for approval");
    } else {
      showToast(payload.message || "Run resumed");
    }
    await fetchSnapshot();
  } catch (error) {
    operatorRequestError = error instanceof Error ? error.message : String(error);
    renderSnapshot(currentSnapshot);
  }
}

async function restoreBackup(backupId) {
  if (!backupId) {
    return;
  }
  const confirmed = window.confirm(
    "Restore this SQLite backup? The framework will create a fresh pre-restore safety backup first.",
  );
  if (!confirmed) {
    return;
  }
  restoreBusyId = backupId;
  restoreError = null;
  renderSnapshot(currentSnapshot);
  try {
    restoreOutcome = await requestJson("/api/control-room/restore", {
      method: "POST",
      body: JSON.stringify({
        backup_id: backupId,
        requested_by: "Control Room",
      }),
    });
    selectedRunId = null;
    selectedRunEvidence = null;
    showToast(`Restored ${backupId}`);
    await fetchSnapshot();
  } catch (error) {
    restoreError = error instanceof Error ? error.message : String(error);
    renderSnapshot(currentSnapshot);
  } finally {
    restoreBusyId = null;
    renderSnapshot(currentSnapshot);
  }
}

function renderSnapshot(snapshot) {
  const heroLede = activeView === "orchestrator"
    ? "Chat-first orchestration with a web control room for approvals, run visibility, artifacts, and proof."
    : "Planning wall derived from the canonical SQLite store, with manual refresh by default and optional timed polling.";
  const stats = [
    ["Tasks", snapshot.summary.task_count],
    ["Milestones", snapshot.summary.milestone_count],
    ["Ready", snapshot.summary.status_counts.ready || 0],
    ["In Review", snapshot.summary.status_counts.in_review || 0],
    ["Complete", snapshot.summary.status_counts.completed || 0],
    ["Warnings", snapshot.summary.planning_warning_count || 0, (snapshot.summary.planning_warning_count || 0) ? "stat-card--warning" : "stat-card--success"],
  ].map(([label, value, tone]) => renderStat(label, value, tone || "")).join("");

  let mainView = renderBoard(snapshot);
  if (activeView === "milestones") {
    mainView = renderMilestones(snapshot);
  }
  if (activeView === "orchestrator") {
    mainView = renderOrchestrator(snapshot);
  }

  appRoot.innerHTML = `
    <main class="shell" data-density="${escapeHtml(densityMode)}">
      <section class="hero">
        <div>
          <p class="eyebrow">Program Kanban</p>
          <h1>${escapeHtml(snapshot.project_label || projectLabel(snapshot.project_name))}</h1>
          <p class="lede">${escapeHtml(heroLede)}</p>
          <div class="view-tab-row">${renderViewTabs(snapshot)}</div>
          <div class="project-chip-row">${renderProjectChips(snapshot)}</div>
          ${renderRefreshControls()}
          ${renderDensityControls()}
        </div>
        <div class="hero__summary">
          <div class="hero__meta">Generated at ${escapeHtml(formatTimestamp(snapshot.generated_at))}</div>
          <div class="hero__meta">Store: ${escapeHtml(snapshot.canonical_store)}</div>
          <div class="hero__meta">Scope: ${escapeHtml(snapshot.project_label || projectLabel(snapshot.project_name))}</div>
          <div class="hero__meta">Auto-refresh: ${autoRefreshEnabled ? `On (${AUTO_REFRESH_MS / 1000}s)` : "Off"}</div>
        </div>
      </section>

      ${renderSystemHealthStrip(snapshot)}
      <section class="stats-grid">${stats}</section>
      ${renderProjectRollup(snapshot)}
      ${mainView}
      ${activeView === "orchestrator" ? "" : renderEvidenceSpotlight(snapshot)}
      ${renderRecentUpdates(snapshot)}
      <div class="copy-toast" id="copy-toast" aria-live="polite"></div>
    </main>
  `;

  document.querySelectorAll("[data-project]").forEach((button) => {
    button.addEventListener("click", () => {
      activeProject = button.dataset.project || DEFAULT_PROJECT;
      selectedEvidence = null;
      syncUrl();
      fetchSnapshot();
    });
  });

  document.querySelectorAll("[data-view]").forEach((button) => {
    button.addEventListener("click", () => {
      activeView = button.dataset.view || DEFAULT_VIEW;
      syncUrl();
      renderSnapshot(currentSnapshot);
    });
  });

  document.querySelectorAll("[data-copy-text]").forEach((button) => {
    button.addEventListener("click", async () => {
      const copyText = button.dataset.copyText || "";
      try {
        await navigator.clipboard.writeText(copyText);
        showToast(`Copied ${copyText}`);
      } catch {
        showToast(`Copy failed for ${copyText}`);
      }
    });
  });

  document.querySelectorAll("[data-refresh-now]").forEach((button) => {
    button.addEventListener("click", () => {
      fetchSnapshot();
    });
  });

  document.querySelectorAll("[data-auto-refresh-toggle]").forEach((button) => {
    button.addEventListener("click", () => {
      autoRefreshEnabled = !autoRefreshEnabled;
      writeStoredFlag(STORAGE_KEYS.autoRefresh, autoRefreshEnabled);
      updateRefreshTimer();
      renderSnapshot(currentSnapshot);
    });
  });

  document.querySelectorAll("[data-density-mode]").forEach((button) => {
    button.addEventListener("click", () => {
      densityMode = normalizeDensityMode(button.dataset.densityMode || "normal");
      writeStoredJson(STORAGE_KEYS.densityMode, densityMode);
      renderSnapshot(currentSnapshot);
    });
  });

  document.querySelectorAll("[data-filter-toggle]").forEach((button) => {
    button.addEventListener("click", () => {
      const mode = button.dataset.filterToggle;
      if (mode === "hideComplete") {
        hideCompleteMilestones = !hideCompleteMilestones;
        writeStoredFlag(STORAGE_KEYS.hideCompleteMilestones, hideCompleteMilestones);
      }
      if (mode === "hideEmpty") {
        hideEmptyMilestones = !hideEmptyMilestones;
        writeStoredFlag(STORAGE_KEYS.hideEmptyMilestones, hideEmptyMilestones);
      }
      renderSnapshot(currentSnapshot);
    });
  });

  document.querySelectorAll("[data-evidence-kind]").forEach((button) => {
    button.addEventListener("click", () => {
      selectedEvidence = {
        kind: button.dataset.evidenceKind || "run",
        taskId: button.dataset.taskId || "",
      };
      renderSnapshot(currentSnapshot);
      document.querySelector(".evidence-card--spotlight")?.scrollIntoView({ behavior: "smooth", block: "nearest" });
    });
  });

  document.querySelectorAll("[data-evidence-clear]").forEach((button) => {
    button.addEventListener("click", () => {
      selectedEvidence = null;
      renderSnapshot(currentSnapshot);
    });
  });

  document.querySelectorAll("[data-milestone-toggle]").forEach((button) => {
    button.addEventListener("click", () => {
      const milestoneId = button.dataset.milestoneToggle || "";
      collapsedMilestones = {
        ...collapsedMilestones,
        [milestoneId]: !collapsedMilestones[milestoneId],
      };
      writeStoredJson(STORAGE_KEYS.collapsedMilestones, collapsedMilestones);
      renderSnapshot(currentSnapshot);
    });
  });

  document.querySelectorAll("[data-response-chip]").forEach((button) => {
    button.addEventListener("click", () => {
      const text = button.dataset.responseChip || "";
      operatorDraft.clarification = operatorDraft.clarification
        ? `${operatorDraft.clarification}\n${text}`
        : text;
      renderSnapshot(currentSnapshot);
    });
  });

  document.querySelector("#operator-request")?.addEventListener("input", (event) => {
    operatorDraft.text = event.target.value;
  });

  document.querySelector("#operator-clarification")?.addEventListener("input", (event) => {
    operatorDraft.clarification = event.target.value;
  });

  document.querySelectorAll("[data-operator-preview]").forEach((button) => {
    button.addEventListener("click", () => {
      previewOperatorRequest();
    });
  });

  document.querySelectorAll("[data-operator-dispatch]").forEach((button) => {
    button.addEventListener("click", () => {
      dispatchOperatorRequest();
    });
  });

  document.querySelectorAll("[data-operator-reset]").forEach((button) => {
    button.addEventListener("click", () => {
      operatorDraft = { text: "", clarification: "" };
      operatorPreview = null;
      operatorRequestError = null;
      renderSnapshot(currentSnapshot);
    });
  });

  document.querySelectorAll("[data-operator-clear-preview]").forEach((button) => {
    button.addEventListener("click", () => {
      operatorPreview = null;
      renderSnapshot(currentSnapshot);
    });
  });

  document.querySelectorAll("[data-operator-approve]").forEach((button) => {
    button.addEventListener("click", () => {
      approveOperatorApproval(button.dataset.operatorApprove || "", button.dataset.operatorRun || "", { resume: false });
    });
  });

  document.querySelectorAll("[data-operator-approve-resume]").forEach((button) => {
    button.addEventListener("click", () => {
      approveOperatorApproval(button.dataset.operatorApproveResume || "", button.dataset.operatorRun || "", { resume: true });
    });
  });

  document.querySelectorAll("[data-operator-reject]").forEach((button) => {
    button.addEventListener("click", () => {
      rejectOperatorApproval(button.dataset.operatorReject || "");
    });
  });

  document.querySelectorAll("[data-run-inspect]").forEach((button) => {
    button.addEventListener("click", () => {
      loadRunEvidence(button.dataset.runInspect || "");
    });
  });

  document.querySelectorAll("[data-run-resume]").forEach((button) => {
    button.addEventListener("click", () => {
      resumeOperatorRun(button.dataset.runResume || "");
    });
  });

  document.querySelectorAll("[data-run-refresh]").forEach((button) => {
    button.addEventListener("click", () => {
      loadRunEvidence(button.dataset.runRefresh || "");
    });
  });

  document.querySelectorAll("[data-backup-restore]").forEach((button) => {
    button.addEventListener("click", () => {
      restoreBackup(button.dataset.backupRestore || "");
    });
  });
}

function syncUrl() {
  const url = new URL(window.location.href);
  url.searchParams.set("project", activeProject);
  url.searchParams.set("view", activeView);
  window.history.replaceState({}, "", url);
}

function showToast(message) {
  const toast = document.querySelector("#copy-toast");
  if (!toast) {
    return;
  }
  toast.textContent = message;
  toast.classList.add("copy-toast--visible");
  if (toastTimer) {
    window.clearTimeout(toastTimer);
  }
  toastTimer = window.setTimeout(() => {
    toast.classList.remove("copy-toast--visible");
  }, 1800);
}

function renderLoading() {
  appRoot.innerHTML = `
    <main class="shell">
      <section class="hero">
        <p class="eyebrow">Program Kanban</p>
        <h1>Loading planning wall</h1>
        <p class="lede">Reading the canonical store and rebuilding the current board.</p>
      </section>
    </main>
  `;
}

function renderError(message) {
  appRoot.innerHTML = `
    <main class="shell">
      <section class="hero">
        <p class="eyebrow">Program Kanban</p>
        <h1>Planning wall unavailable</h1>
        <p class="lede">The current snapshot could not be generated.</p>
      </section>
      <section class="panel">
        <article class="evidence-card evidence-card--warning">
          <div class="evidence-card__title">Snapshot error</div>
          <ul><li>${escapeHtml(message)}</li></ul>
        </article>
      </section>
    </main>
  `;
}

async function fetchSnapshot() {
  if (!currentSnapshot) {
    renderLoading();
  }

  try {
    const response = await fetch(`/api/snapshot?project=${encodeURIComponent(activeProject)}`, { cache: "no-store" });
    if (!response.ok) {
      throw new Error(`Snapshot request failed with ${response.status}`);
    }
    currentSnapshot = await response.json();
    if (selectedRunId && activeView === "orchestrator") {
      try {
        selectedRunEvidence = await requestJson(`/api/operator/run?run_id=${encodeURIComponent(selectedRunId)}`);
        runInspectorError = null;
      } catch (error) {
        runInspectorError = error instanceof Error ? error.message : String(error);
      }
    }
    renderSnapshot(currentSnapshot);
  } catch (error) {
    renderError(error instanceof Error ? error.message : String(error));
  }
}

function updateRefreshTimer() {
  if (refreshTimer) {
    window.clearInterval(refreshTimer);
    refreshTimer = null;
  }
  if (autoRefreshEnabled) {
    refreshTimer = window.setInterval(fetchSnapshot, AUTO_REFRESH_MS);
  }
}

fetchSnapshot();
updateRefreshTimer();
