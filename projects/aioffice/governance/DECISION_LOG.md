# AIOffice Decision Log Stub

Bootstrap status:
- seeded with founding decisions only

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

## TODO
- convert seeded bootstrap decisions into reviewed entries
- add owners, reviewers, and supersession rules
- record later donor-import decisions here
- define when a draft decision becomes binding
