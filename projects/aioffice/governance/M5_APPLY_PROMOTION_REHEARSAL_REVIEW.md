# M5 Apply/Promotion Rehearsal Review

## Purpose
- Run a narrow post-`AIO-032` governance and ledger review before broader `AIO-033` rehearsal work begins.
- Determine whether the isolated-workspace residue observed during `AIO-032` changes the completion decision for `AIO-032`.
- Classify the residue explicitly against `AIO-029` rather than silently absorbing it into narrative prose.

## Evidence Reviewed
- `projects/aioffice/execution/KANBAN.md`
  - `AIO-029` acceptance wording
  - current `AIO-032` status in `in_review`
- `projects/aioffice/artifacts/M5_APPLY_PROMOTION_REHEARSAL.md`
  - factual `AIO-032` rehearsal report
- file listings from prior isolated M5 rehearsal workspaces:
  - `projects/aioffice/artifacts/m5_supervised_operator_cli_rehearsal/workspace`
  - `projects/aioffice/artifacts/m5_supervised_operator_cli_rehearsal_codex_validation/workspace`
- current `AIO-032` isolated rehearsal workspace file list:
  - `projects/aioffice/artifacts/m5_apply_promotion_supervised_rehearsal_20260415/workspace`
- `projects/aioffice/governance/M4_IMPLEMENTATION_REVIEW.md`
  - prior hardening expectation that isolated rehearsal residue should be removed or contained

## What AIO-032 Proved
- One supervised rehearsal of the implemented controlled apply/promotion path was executed.
- The rehearsal used the sanctioned persisted store path in `SessionStore.execute_apply_promotion_decision(...)`.
- The bounded rehearsal moved one bundle from `pending_review` to `promoted` under an explicit approved decision.
- Read-only inspection confirmed the persisted post-decision packet, bundle, artifact, and receipt state.
- The evidence was recorded factually without claiming unattended operation, later-stage workflow proof, or broader autonomy readiness.

## What AIO-032 Did Not Prove
- It did not prove unattended, overnight, or semi-autonomous readiness.
- It did not prove later-stage workflow beyond the currently proven architect-bounded context.
- It did not rehearse the `apply` branch separately from the shared `promote` branch exercised here.
- It did not prove a new operator-facing apply/promotion wrapper because no such wrapper was used in this rehearsal.

## Isolated-Workspace Residue Observed
- `memory/framework_health.json`
- `memory/session_summaries.json`
- `projects/tactics-game/execution/KANBAN.md`

## Residue Classification
- Classification: `regression against AIO-029`

### Rationale
- `AIO-029` acceptance states: `isolated rehearsal setup no longer creates unrelated project side files`.
- The `AIO-032` rehearsal workspace did create unrelated side files, including a non-AIOffice project ledger path: `projects/tactics-game/execution/KANBAN.md`.
- Earlier isolated M5 rehearsal workspaces currently do not show the same residue set in their file listings; they contain the expected rehearsal artifacts plus `sessions/studio.db`.
- That makes the `AIO-032` residue best classified as a regression against the accepted `AIO-029` hardening outcome, not as a harmless scope exception.

## Impact On AIO-029
- The current observation conflicts with the accepted `AIO-029` acceptance wording.
- This review does not reopen `AIO-029` directly, because the current accepted execution posture already ratifies `AIO-029` as completed and this pass is intentionally narrow.
- Instead, the regression should be tracked explicitly as a new narrow bug so the contradiction is visible in the authoritative backlog without silently rewriting accepted history.

## Decision On Whether AIO-032 Is Complete
- Decision: `AIO-032` is complete if and only if the residue regression is recorded separately.

### Why AIO-032 Can Still Complete
- `AIO-032` acceptance requires:
  - one supervised rehearsal executed
  - evidence recorded factually
  - no overclaim of autonomy
- Those acceptance criteria were satisfied.
- The residue does not invalidate the existence of the rehearsal or the factual evidence it produced.
- The residue is a separate hardening regression and should be tracked as such, rather than used to misstate what `AIO-032` itself proved.

### Why M5 Does Not Close
- The residue regression remains open hardening work.
- `AIO-033` and `AIO-034` remain outstanding.
- No unattended or later-stage readiness claim is supported by this review.

## Immediate Next Step
- Record the regression as a new narrow bug in `execution/KANBAN.md`.
- Move `AIO-032` from `in_review` to `completed` in a separate lawful ledger pass after the review artifact and bug record both exist.
- After that, proceed to `AIO-033` only with the residue regression kept explicit and visible.
