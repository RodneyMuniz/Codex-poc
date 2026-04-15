# M9 Control Surface Priority Review

## 1. Purpose
- Record one explicit post-`M9` review grounded in committed evidence plus the operator concerns raised for this review.
- State why further control-surface hardening should or should not outrank UI expansion right now.
- Ratify exactly one next conservative slice without changing readiness or widening workflow proof.

## 2. Evidence Base Used
- Governance and current-state sources reviewed:
  - `projects/aioffice/governance/PROJECT.md`
  - `projects/aioffice/governance/VISION.md`
  - `projects/aioffice/execution/KANBAN.md`
  - `projects/aioffice/governance/DECISION_LOG.md`
  - `projects/aioffice/governance/ACTIVE_STATE.md`
  - `projects/aioffice/governance/M6_NARROW_PROOF_REVIEW.md`
  - `projects/aioffice/governance/M7_OPERATOR_DECISION_SURFACE_REVIEW.md`
  - `projects/aioffice/governance/M8_OPERATOR_DECISION_INPUT_REVIEW.md`
  - `projects/aioffice/governance/OPERATOR_DECISION_SURFACE.md`
  - `projects/aioffice/governance/OPERATOR_DECISION_INPUT_CONTRACT.md`
  - `projects/aioffice/governance/SYSTEM_REALITY_MAP.md`
  - `projects/aioffice/execution/PROJECT_BRAIN.md`
  - `projects/aioffice/governance/WORKFLOW_VISION.md`
- Rehearsal and proof artifacts reviewed:
  - `projects/aioffice/artifacts/M6_APPLY_BRANCH_REHEARSAL.md`
  - `projects/aioffice/artifacts/M6_SHARED_STORE_REHEARSAL.md`
  - `projects/aioffice/artifacts/M7_OPERATOR_DECISION_SURFACE_REHEARSAL.md`
  - `projects/aioffice/artifacts/M8_OPERATOR_DECISION_INPUT_REHEARSAL.md`
- Implementation grounding reviewed:
  - `scripts/operator_api.py`
  - `tests/test_operator_api.py`
  - `sessions/store.py`
- Operator concerns raised for this review and treated as review inputs, not pre-proven facts:
  - admin-only product/self-change governance
  - automated snapshot, version, restore, and rollback discipline
  - feature isolation, maintainability, and code-review discipline for future Codex changes
  - eventual DB-backed canonical state before serious multi-agent parallelism or writable UI
  - timing for UI and art-pipeline work
- No new rehearsal runs were performed for this review.

## 3. Current Accepted Posture Before Review
- `M1` through `M9` are complete.
- Current readiness remains:
  - `ready only for narrow supervised bounded operation`
  - not ready for a bounded supervised semi-autonomous cycle
- Current live workflow proof still stops at `architect`.
- No post-`M9` milestone is ratified yet.
- `M6` through `M8` proved narrow supervised operator decision surfaces and shell-safe input hardening only.
- `M6` through `M9` did not prove:
  - concurrent contention handling
  - later-stage workflow
  - real multi-agent maturity
  - UAT readiness

## 4. Why Further Control-Surface Hardening Outranks UI Right Now
- The committed proof surface is still control-plane-first and narrow:
  - `scripts/operator_api.py` proves `control-kernel-details` and `bundle-decision`
  - `tests/test_operator_api.py` proves narrow fail-closed operator decision paths
  - `sessions/store.py` proves the sanctioned persisted mutation path
- `PROJECT.md` explicitly rejects a `UI-first rebuild detached from enforcement`.
- `VISION.md` explicitly says UI convenience must not weaken governance and that no interface may imply an operator workspace alpha unless evidence says so.
- `SYSTEM_REALITY_MAP.md` records that the currently real operator surfaces are inspection-oriented and CLI-oriented, not a broader writable operator workspace.
- `M9` reconciled wording and board/state truth, but it did not add new control behavior.
- A UI-first next slice would therefore add a new operator-facing interpretation or write surface before the next safety contracts for product change governance, recovery, and maintainability are defined.

## 5. Admin-Only Product/Self-Change Governance Concern
- Current committed AIOffice governance is strong on general authority boundaries:
  - operator direction and approval
  - sanctioned code paths for canonical mutation
  - bounded execution under a control kernel
- Current committed AIOffice governance is narrow on product/self-change governance:
  - `OPERATOR_DECISION_SURFACE.md` governs execution-bundle decisions, not product self-modification
  - `OPERATOR_DECISION_INPUT_CONTRACT.md` governs mapping transport, not product-change authority
- No committed AIOffice artifact currently defines:
  - which product or system changes are admin-only
  - whether self-modifying changes must follow a stricter approval lane
  - how admin-only product changes are proposed, reviewed, and audited separately from ordinary bundle decisions
- That concern becomes more important before writable UI or self-service product editing, because the current narrow decision surface is intentionally scoped to persisted execution bundles, not product-wide mutation law.

## 6. Versioning / Snapshot / Restore / Rollback Concern
- `VISION.md` already requires continuity across pauses, reviews, and later resumption.
- `sessions/store.py` already contains shared backup and restore primitives:
  - `create_dispatch_backup(...)`
  - `restore_dispatch_backup(...)`
  - restore-history composition in evidence views
- Those shared primitives are not yet the same thing as an accepted AIOffice control contract.
- No committed AIOffice artifact currently defines:
  - when snapshots must be taken
  - what version boundary applies across repo state, store state, and accepted artifacts
  - who may request restore or rollback
  - what counts as a lawful rollback scope
  - how restore and rollback should be rehearsed for AIOffice specifically
- Before UI or broader writable control surfaces expand the blast radius, AIOffice needs a narrow recovery contract and rehearsal plan rather than relying on implicit shared-store capability.

## 7. Feature Isolation / Maintainability / Code Review Concern
- `SYSTEM_REALITY_MAP.md` records that `sessions/store.py` is functionally real but structurally mixed, including non-AIO defaults and shared multi-project responsibilities.
- The same map records that `scripts/operator_api.py` is a real operator wrapper, but the repo does not yet prove a broader maintainability contract for future changes around it.
- `M7` and `M8` proved that narrow operator surfaces can be added and rehearsed successfully.
- They did not prove:
  - a feature-isolation contract for future Codex-delivered changes
  - a formal code-review contract for cross-project shared files
  - a rule for keeping future control-surface work out of unrelated UI or art work
- Without that contract, future work on shared files such as `sessions/store.py` and `scripts/operator_api.py` carries unnecessary regression risk across AIOffice and donor/shared system concerns.

## 8. Markdown Ledger Vs Canonical DB Concern
- `KANBAN.md` is still the authoritative AIOffice milestone and task source of truth.
- `DECISION_LOG.md` and `KANBAN.md` both record that canonical import remains deferred because the current schema does not preserve durable `dependencies` safely.
- `SYSTEM_REALITY_MAP.md` repeats that AIOffice backlog truth still lives in markdown for this reason.
- This is acceptable for the current narrow supervised posture because:
  - task count is still manageable
  - review remains explicit and manual
  - no writable UI or serious multi-agent parallelism is being claimed
- It is not a strong enough long-term control surface for:
  - serious multi-agent parallelism
  - writable client interfaces
  - frequent concurrent status mutation
- The eventual DB-backed canonical-state concern is therefore real, but the most conservative immediate slice is still to define the governance, recovery, and maintainability contracts that any later canonical-state migration or writable UI would need to obey.

## 9. UI Timing Recommendation
- UI should not be the next slice.
- A read-oriented UI remains conceptually compatible with `VISION.md`, but even that should remain subordinate to the already-real CLI and inspection truth surfaces until the next control contracts exist.
- A writable client app should not be ratified next because:
  - admin-only product/self-change governance is not yet defined
  - AIOffice-specific recovery/rollback rules are not yet defined
  - maintainability and feature-isolation rules for future changes are not yet defined
  - markdown remains the authoritative task ledger for now
- Recommendation:
  - do not start UI implementation in the next slice
  - revisit UI only after change governance, recovery, and maintainability boundaries are explicitly defined

## 10. Art-Pipeline Timing Recommendation
- Art-pipeline work should not be the next slice.
- `WORKFLOW_VISION.md` and `VISION.md` keep later-stage live workflow beyond `architect` unproven.
- `SYSTEM_REALITY_MAP.md` explicitly says a distinct Art runtime or Art pipeline proof surface for AIOffice was not found in the inspected control path.
- Art-pipeline work would therefore broaden into later-stage workflow and presentation concerns before the nearer-term control-surface hardening concerns are settled.
- Recommendation:
  - do not start art-pipeline implementation in the next slice
  - keep art-pipeline work deferred until later-stage workflow proof and stronger control contracts exist

## 11. Recommended Next Conservative Slice
- Ratified next slice:
  - `M10 - Change Governance, Recovery, and Maintainability Hardening`
- Reason:
  - it responds directly to the newly raised operator concerns
  - it stays inside governance and control-surface hardening rather than widening into UI or art execution
  - it addresses the most consequential missing contracts before any future writable or broader operator surface is considered

## 12. Proposed Next Milestone And Minimum Tasks
- Proposed milestone:
  - `M10 - Change Governance, Recovery, and Maintainability Hardening`
- Proposed entry goal:
  - `M9` has closed with reconciled planning surfaces, and the next work should harden change governance, recovery discipline, and maintainability contracts before any UI or art-pipeline expansion is considered.
- Proposed exit goal:
  - an admin-only product/self-change governance boundary, an automated snapshot/version/restore/rollback contract with rehearsal plan, and a feature-isolation/code-review contract are defined clearly enough to guide later implementation without changing readiness or widening workflow proof.
- Minimum tasks to seed:
  - `AIO-050`
    - define the admin-only product-change and self-modification governance boundary
  - `AIO-051`
    - define the automated snapshot/version/restore/rollback contract and rehearsal plan
  - `AIO-052`
    - define the feature-isolation and code-review contract for Codex-delivered changes
- Conservative sequencing decision:
  - do not seed an implementation or rehearsal task in `M10` yet
  - define the governance contracts first, then decide whether any implementation slice is justified

## 13. Readiness Posture Delta, If Any
- Readiness posture delta: none.
- The accepted posture remains:
  - `ready only for narrow supervised bounded operation`
  - not ready for a bounded supervised semi-autonomous cycle
- Current live workflow proof still stops at `architect`.
- Ratifying `M10` does not authorize UI readiness, art-pipeline readiness, later-stage workflow proof, or any broader autonomy claim.

## 14. Explicit Non-Claims
- This review does not claim concurrent contention safety.
- This review does not claim later-stage workflow proof.
- This review does not claim real multi-agent maturity.
- This review does not claim unattended, overnight, or semi-autonomous readiness.
- This review does not claim UAT readiness.
- This review does not authorize UI implementation as the next slice.
- This review does not authorize art-pipeline implementation as the next slice.
- This review does not claim that markdown task truth is sufficient for serious multi-agent parallelism or writable UI forever.
