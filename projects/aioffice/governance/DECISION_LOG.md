# AIOffice Decision Log

## Decisions

### AIO-D-001
- date: 2026-04-13
- status: seeded
- decision: the authoritative repository root for AIOffice bootstrap is `C:\Users\rodne\OneDrive\Desktop\_AIStudio_POC`.
- rationale: the duplicate Documents root is explicitly non-authoritative for this project.

### AIO-D-002
- date: 2026-04-13
- status: seeded
- decision: the bootstrap scope is governance-only and excludes UI, old orchestration changes, and worker execution changes.
- rationale: the founding pass needs clarity without disturbing existing runtime behavior.

### AIO-D-003
- date: 2026-04-13
- status: seeded
- decision: project registration may use the minimal store/read-model path, but backlog planning stays in project-local artifacts until a later sync decision is approved.
- rationale: this keeps AIOffice visible as a project without binding the founding backlog to the current runtime planning path.

### AIO-D-004
- date: 2026-04-13
- status: seeded
- decision: AIOffice project registration must occur through sanctioned code, using the deterministic store helper surfaced by the CLI project-registration path rather than ad hoc SQL.
- rationale: the sanctioned path is idempotent, testable, and avoids unrelated `KANBAN.md` rewrites during registration.

### AIO-D-005
- date: 2026-04-13
- status: seeded
- decision: canonical import of `AIO-001` through `AIO-007` remains deferred because the current `tasks` schema does not preserve a durable `dependencies` field safely.
- rationale: AIOffice backlog truth must not be degraded by importing work items into canonical task rows that cannot store one of the required durable fields.

### AIO-D-006
- date: 2026-04-13
- status: reviewed
- decision: the observed defect was that bundled `KANBAN.md` normalization recorded end states that bypassed the declared lifecycle transitions. AIOffice will treat `KANBAN.md` as authoritative current-state ledger truth and allow condensed end-of-bundle state recording only for operator-authorized bounded bundles with explicit scope, dependency handling, reviewable execution order, required artifacts, and preserved provenance.
- rationale: this policy keeps current backlog truth aligned with accepted board law without inventing a second authoritative surface. It is acceptable in the current model because `KANBAN.md` is a current-state ledger, not a sanctioned event-history log. What remains deferred is a future canonical state or event model that can preserve both authoritative snapshot truth and first-class transition history without requiring condensed recording exceptions.

### AIO-D-007
- date: 2026-04-15
- status: reviewed
- decision: the AIOffice documentation baseline is re-ratified as follows:
  - current status truth comes from the local `execution/KANBAN.md`
  - the original `M1` through `M10` roadmap remains the strategic backbone unless accepted execution has already diverged
  - the updated AIOffice product spec is accepted as the constitutional product baseline and is promoted through `governance/VISION.md`
  - original `M3` operator-design work is explicitly deferred rather than silently collapsed
  - control-kernel, protocol, persistence, inspection, and supervised-control work are accepted as having been pulled forward into current `M3` through `M5`
  - original `M6` through `M10` are preserved with refinements rather than replaced
  - current accepted execution truth is `M1` through `M4` complete and `M5` partial, with `AIO-029`, `AIO-030`, and `AIO-031` complete and `AIO-032`, `AIO-033`, and `AIO-034` remaining
- rationale:
  - the local KANBAN now carries the accepted operational truth and must outrank stale roadmap wording for status claims
  - the strategic backbone still matters because re-baselining is a reconciliation pass, not permission to invent a new roadmap
  - the constitutional product baseline needs a stable home that is separate from run logs and backlog movement
  - approved divergence must be explicit so later readers do not confuse deferral with deletion or mistake pulled-forward control work for original sequencing
- thin-control-kernel ADR treatment:
  - the thin-control-kernel framing is absorbed into this re-baseline across `PROJECT.md`, `VISION.md`, and this decision entry
  - this entry does not claim that a separate standalone ADR artifact has been completed
  - if a dedicated ADR is still desired later, it remains outstanding and must be tracked explicitly rather than implied here

### AIO-D-008
- date: 2026-04-15
- status: reviewed
- decision: after `M5` closeout, the next operational slice is ratified as a narrow post-`M5` proof slice focused on supervised proof of the separate `apply` branch and bounded proof of same-workspace repeated-run or shared-store contention behavior. Later-stage workflow expansion remains deferred as an operational next step until those current-boundary gaps are reviewed explicitly.
- rationale:
  - the accepted `M5` readiness review identified the separate `apply` branch and same-workspace or shared-store behavior as explicit missing proof inside the current sanctioned boundary
  - the accepted readiness posture remains `ready only for narrow supervised bounded operation`, not ready for a bounded supervised semi-autonomous cycle
  - proving unresolved behavior inside the already implemented boundary is safer and more reviewable than widening the workflow claim into later stages at the same time
  - this ratifies `M6` as a planned narrow proof slice, not as proof that later-stage workflow, unattended operation, or broader semi-autonomous readiness has been achieved

### AIO-D-009
- date: 2026-04-15
- status: reviewed
- decision: before additional `M6` proof rehearsals, AIOffice will establish a narrow GitHub-visible remote review anchor for the current accepted state using the current working branch, the accepted post-`M5` baseline tag, and a project-local `governance/ACTIVE_STATE.md` file. GitHub is the external review surface for audit; the local repository remains the implementation workspace.
- rationale:
  - current `M6` proof work benefits from an external review anchor that is stronger than local-only state when later audit or review is needed
  - this is a narrow proof-auditability step inside `M6`, not a separate infrastructure initiative
  - the task does not change the accepted readiness posture and does not imply later-stage workflow proof, autonomy readiness, or real multi-agent maturity
  - grounding later `M6` artifacts on pushed branch, tag, and file evidence makes future proof review more conservative and reviewable

### AIO-D-010
- date: 2026-04-16
- status: reviewed
- decision: after `AIO-052` closed `M10`, the authoritative review anchor is re-anchored from the `M9` closeout refs to dedicated `M10` closeout refs:
  - checkpoint tag: `aioffice-m10-closeout-2026-04-16`
  - snapshot branch: `snapshot/aioffice-m10-closeout-2026-04-16`
  - working branch remains: `feature/aioffice-m10-change-governance-hardening`
- rationale:
  - `KANBAN.md` and `ACTIVE_STATE.md` now both record `M10` as complete, so the externally reviewable checkpoint/snapshot anchor should match that accepted closeout boundary
  - this is checkpoint and review-anchor hygiene only
  - the historical `M9` tag and `M9` snapshot branch remain preserved as prior accepted anchors and are not rewritten, moved, or deleted
  - this decision does not imply any readiness change, workflow-proof expansion, UI expansion, autonomy expansion, or later-stage workflow claim
