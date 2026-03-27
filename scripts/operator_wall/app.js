const appRoot = document.querySelector("#app");
const REFRESH_MS = 5000;
let activeProject = new URLSearchParams(window.location.search).get("project") || "all";
let currentSnapshot = null;

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

function projectLabel(value) {
  return String(value ?? "")
    .split("-")
    .filter(Boolean)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

function badge(label, value, strong = false) {
  return `
    <li class="badge ${strong ? "badge--strong" : ""}">
      <span>${escapeHtml(label)}</span>
      <strong>${escapeHtml(value)}</strong>
    </li>
  `;
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

function renderTaskCard(card) {
  const tags = [
    badge("Project", card.project_label || projectLabel(card.project_name)),
    badge("ID", card.id),
    badge("Kind", card.task_kind),
    badge("Owner", card.owner_role),
    badge("Assigned", card.assigned_role || "-"),
    badge("Layer", card.layer || "-"),
    badge("Category", card.category || "-"),
    badge("Review", card.review_state || "-", true),
  ].join("");

  return `
    <article class="task-card">
      <div class="task-card__title">${escapeHtml(card.title)}</div>
      <div class="task-card__meta">${escapeHtml(card.details)}</div>
      <ul class="badge-list">${tags}</ul>
      <div class="task-card__path">${escapeHtml(card.expected_artifact_path || "No artifact path recorded.")}</div>
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

function renderStat(label, value) {
  return `
    <article class="stat-card">
      <span>${escapeHtml(label)}</span>
      <strong>${escapeHtml(value)}</strong>
    </article>
  `;
}

function renderListItem(title, lines, emphasis = "") {
  const detailLines = lines.length
    ? lines.map((line) => `<li>${escapeHtml(line)}</li>`).join("")
    : `<li>No details recorded.</li>`;

  return `
    <article class="evidence-card ${emphasis}">
      <div class="evidence-card__title">${escapeHtml(title)}</div>
      <ul>${detailLines}</ul>
    </article>
  `;
}

function renderApprovals(snapshot) {
  if (!snapshot.pending_approvals.length) {
    return `<article class="empty-card">No pending approvals.</article>`;
  }

  return snapshot.pending_approvals.map((approval) =>
    renderListItem(
      `${approval.project_label || projectLabel(approval.project_name)} | ${approval.task_title}`,
      [
        `Approval ID: ${approval.id}`,
        `Scope: ${approval.approval_scope}`,
        `Target role: ${approval.target_role || "-"}`,
        `Expected output: ${approval.expected_output || "-"}`,
        `Why now: ${approval.why_now || "-"}`,
      ],
      "evidence-card--warning",
    )
  ).join("");
}

function renderRuns(snapshot) {
  if (!snapshot.recent_runs.length) {
    return `<article class="empty-card">No runs recorded yet.</article>`;
  }

  return snapshot.recent_runs.map((run) =>
    renderListItem(`${run.project_label || projectLabel(run.project_name)} | ${run.task_title}`, [
      `Run ID: ${run.id}`,
      `Status: ${statusLabel(run.status)}`,
      `Stop reason: ${run.stop_reason || "-"}`,
      `Updated: ${run.updated_at}`,
    ])
  ).join("");
}

function renderAgentRuns(snapshot) {
  if (!snapshot.recent_agent_runs.length) {
    return `<article class="empty-card">No worker runs recorded yet.</article>`;
  }

  return snapshot.recent_agent_runs.map((item) =>
    renderListItem(`${item.project_label || projectLabel(item.project_name)} | ${item.role} | ${item.task_title}`, [
      `Agent run ID: ${item.id}`,
      `PID: ${item.pid || "-"}`,
      `Status: ${statusLabel(item.status)}`,
      `Input artifact: ${item.input_artifact_path || "-"}`,
      `Output artifact: ${item.output_artifact_path || "-"}`,
    ])
  ).join("");
}

function renderValidations(snapshot) {
  if (!snapshot.recent_validations.length) {
    return `<article class="empty-card">No validation results recorded yet.</article>`;
  }

  return snapshot.recent_validations.map((item) =>
    renderListItem(`${item.project_label || projectLabel(item.project_name)} | ${item.validator_role} | ${item.task_title}`, [
      `Validation ID: ${item.id}`,
      `Status: ${item.status}`,
      `Artifact: ${item.artifact_path || "-"}`,
      `Summary: ${item.summary}`,
      `Checks: ${Object.entries(item.checks || {}).map(([key, value]) => `${key}=${value}`).join(", ") || "-"}`,
    ], item.status === "passed" ? "evidence-card--success" : "evidence-card--warning")
  ).join("");
}

function renderArtifacts(snapshot) {
  if (!snapshot.recent_artifacts.length) {
    return `<article class="empty-card">No artifacts recorded yet.</article>`;
  }

  return snapshot.recent_artifacts.map((artifact) =>
    renderListItem(`${artifact.project_label || projectLabel(artifact.project_name)} | ${artifact.kind} | ${artifact.task_title}`, [
      `Artifact ID: ${artifact.id}`,
      `Path: ${artifact.artifact_path || "-"}`,
      `SHA256: ${artifact.artifact_sha256 || "-"}`,
      `Produced by: ${artifact.produced_by || "-"}`,
      `Inputs: ${(artifact.input_artifact_paths || []).join(", ") || "-"}`,
    ])
  ).join("");
}

function renderFocusRun(snapshot) {
  if (!snapshot.focus_run) {
    return `<article class="empty-card">No run evidence available yet.</article>`;
  }

  const evidence = snapshot.focus_run;
  const delegations = (evidence.delegations || []).map((item) =>
    `<li>${escapeHtml(`${item.from_role} -> ${item.to_role} | ${item.note}`)}</li>`
  ).join("") || "<li>No delegations recorded.</li>";
  const artifacts = (evidence.artifacts || []).map((item) =>
    `<li>${escapeHtml(`${item.kind} | ${item.artifact_path || "-"} | ${item.artifact_sha256 || "-"}`)}</li>`
  ).join("") || "<li>No artifacts recorded.</li>";

  return `
    <article class="focus-card">
      <div class="focus-card__header">
        <h2>Latest Run Evidence</h2>
        <span>${escapeHtml(evidence.run.id)}</span>
      </div>
      <p>${escapeHtml(snapshot.focus_run.task.project_name ? `${projectLabel(snapshot.focus_run.task.project_name)} | ` : "")}${escapeHtml(snapshot.focus_run.task_title)} | ${escapeHtml(statusLabel(evidence.run.status))}</p>
      <div class="focus-grid">
        <section>
          <h3>Delegation Chain</h3>
          <ul>${delegations}</ul>
        </section>
        <section>
          <h3>Artifacts</h3>
          <ul>${artifacts}</ul>
        </section>
      </div>
    </article>
  `;
}

function renderSnapshot(snapshot) {
  const stats = [
    ["Tasks", snapshot.summary.task_count],
    ["Pending approvals", snapshot.summary.pending_approvals],
    ["Runs", snapshot.summary.run_count],
    ["Worker runs", snapshot.summary.agent_run_count],
    ["Validations", snapshot.summary.validation_count],
    ["Artifacts", snapshot.summary.artifact_count],
  ].map(([label, value]) => renderStat(label, value)).join("");

  const board = snapshot.board.map(renderColumn).join("");

  appRoot.innerHTML = `
    <main class="shell">
      <section class="hero">
        <div>
          <p class="eyebrow">Studio Operator Wall</p>
          <h1>Canonical runtime board for ${escapeHtml(snapshot.project_label || projectLabel(snapshot.project_name))}</h1>
          <p class="lede">This wall reads ${escapeHtml(snapshot.canonical_store)} and refreshes every ${REFRESH_MS / 1000}s.</p>
          <div class="project-chip-row" id="project-chip-row">${renderProjectChips(snapshot)}</div>
        </div>
        <div class="hero__summary">
          <div class="hero__meta">Generated at ${escapeHtml(snapshot.generated_at)}</div>
          <div class="hero__meta">Scope: ${escapeHtml(snapshot.project_label || projectLabel(snapshot.project_name))}</div>
        </div>
      </section>

      <section class="stats-grid">${stats}</section>
      ${renderFocusRun(snapshot)}

      <section class="panel">
        <div class="panel__header">
          <h2>Operator Kanban</h2>
          <span>${snapshot.summary.status_counts.completed || 0} completed</span>
        </div>
        <div class="board-grid">${board}</div>
      </section>

      <section class="panel-grid">
        <section class="panel">
          <div class="panel__header"><h2>Pending Approvals</h2></div>
          <div class="stack">${renderApprovals(snapshot)}</div>
        </section>
        <section class="panel">
          <div class="panel__header"><h2>Recent Runs</h2></div>
          <div class="stack">${renderRuns(snapshot)}</div>
        </section>
        <section class="panel">
          <div class="panel__header"><h2>Worker Runs</h2></div>
          <div class="stack">${renderAgentRuns(snapshot)}</div>
        </section>
        <section class="panel">
          <div class="panel__header"><h2>Validation Results</h2></div>
          <div class="stack">${renderValidations(snapshot)}</div>
        </section>
        <section class="panel panel--wide">
          <div class="panel__header"><h2>Artifacts</h2></div>
          <div class="stack">${renderArtifacts(snapshot)}</div>
        </section>
      </section>
    </main>
  `;

  document.querySelectorAll("[data-project]").forEach((button) => {
    button.addEventListener("click", () => {
      activeProject = button.dataset.project || "all";
      const url = new URL(window.location.href);
      url.searchParams.set("project", activeProject);
      window.history.replaceState({}, "", url);
      fetchSnapshot();
    });
  });
}

function renderLoading() {
  appRoot.innerHTML = `
    <main class="shell">
      <section class="hero">
        <p class="eyebrow">Studio Operator Wall</p>
        <h1>Loading runtime evidence</h1>
        <p class="lede">Reading the canonical store and rebuilding the operator view.</p>
      </section>
    </main>
  `;
}

function renderError(message) {
  appRoot.innerHTML = `
    <main class="shell">
      <section class="hero">
        <p class="eyebrow">Studio Operator Wall</p>
        <h1>Operator wall unavailable</h1>
        <p class="lede">The runtime snapshot could not be generated.</p>
      </section>
      <section class="panel">
        <div class="stack">
          <article class="evidence-card evidence-card--warning">
            <div class="evidence-card__title">Reader error</div>
            <ul><li>${escapeHtml(message)}</li></ul>
          </article>
        </div>
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
    renderSnapshot(currentSnapshot);
  } catch (error) {
    renderError(error instanceof Error ? error.message : String(error));
  }
}

fetchSnapshot();
window.setInterval(fetchSnapshot, REFRESH_MS);
