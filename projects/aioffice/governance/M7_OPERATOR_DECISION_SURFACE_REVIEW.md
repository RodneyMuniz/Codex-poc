# M7 Operator Decision Surface Review

## 1. Purpose
- Record one explicit post-`M7` review grounded only in committed evidence.
- State exactly what `M7` proved about the narrow operator-facing decision surface.
- State what remains manual, fragile, or unproven.
- Ratify one and only one next conservative slice without widening workflow proof or changing readiness.

## 2. Evidence Base Used
- Governance and current-state sources reviewed:
  - `projects/aioffice/governance/PROJECT.md`
  - `projects/aioffice/governance/VISION.md`
  - `projects/aioffice/execution/KANBAN.md`
  - `projects/aioffice/governance/DECISION_LOG.md`
  - `projects/aioffice/governance/ACTIVE_STATE.md`
  - `projects/aioffice/governance/M6_NARROW_PROOF_REVIEW.md`
  - `projects/aioffice/governance/SYSTEM_REALITY_MAP.md`
  - `projects/aioffice/governance/OPERATOR_DECISION_SURFACE.md`
- `M6` proof-boundary evidence reviewed:
  - `projects/aioffice/artifacts/M6_APPLY_BRANCH_REHEARSAL.md`
  - `projects/aioffice/artifacts/M6_SHARED_STORE_REHEARSAL.md`
- `M7` audit and rehearsal evidence reviewed:
  - `projects/aioffice/artifacts/M7_OPERATOR_API_RESIDUE_TRIAGE.md`
  - `projects/aioffice/artifacts/M7_OPERATOR_API_RESIDUE.patch`
  - `projects/aioffice/artifacts/M7_OPERATOR_DECISION_SURFACE_REHEARSAL.md`
- Implementation grounding reviewed:
  - `scripts/operator_api.py`
  - `tests/test_operator_api.py`
  - `sessions/store.py`
- Stale planning-surface conflict checks reviewed:
  - `projects/aioffice/execution/PROJECT_BRAIN.md`
  - `projects/aioffice/governance/WORKFLOW_VISION.md`
- No new rehearsal runs were performed for this review.

## 3. Current Accepted Posture Before Review
- `M1` through `M7` are complete.
- Current readiness remains:
  - `ready only for narrow supervised bounded operation`
  - not ready for a bounded supervised semi-autonomous cycle
- Current live workflow proof still stops at `architect`.
- `M6` proved:
  - a GitHub-visible remote review surface exists
  - one supervised sanctioned `apply`-path run exists
  - sequential same-workspace and same-store reuse preserved control-plane identity and receipt scoping on the exercised path
  - reusing the same authoritative destination path is last-write-wins on the live destination file
- `M7` was a narrow operator decision-surface hardening slice, not a later-stage workflow expansion.

## 4. What AIO-040 Proved
- `AIO-040` proved the operator decision surface was defined explicitly before implementation.
- The committed design established:
  - one bundle at a time only
  - explicit supported actions `apply` and `promote`
  - explicit required inputs:
    - `bundle_id`
    - `action`
    - non-empty `approved_by`
    - explicit non-empty `destination_mappings`
    - optional non-empty `decision_note`
    - optional sanctioned `workspace_root`
  - fail-closed behavior for:
    - missing bundle
    - non-`pending_review` bundle state
    - invalid `action`
    - blank `approved_by`
    - missing or malformed `destination_mappings`
    - incomplete mapping coverage
    - out-of-root or forbidden destinations
    - invalid optional `workspace_root`
  - exact out-of-scope boundaries so the surface would not silently widen into packet issuance, bundle ingestion, later-stage workflow, concurrency handling, or readiness claims
- `AIO-040` proved design clarity and scope discipline only.
- `AIO-040` did not prove that the operator-facing command existed or worked in practice.

## 5. What AIO-041 Proved
- `AIO-041` proved a bounded operator-facing `bundle-decision` wrapper exists in `scripts/operator_api.py`.
- The committed implementation routes through the sanctioned persisted mutation path:
  - `scripts/operator_api.py::_execute_control_kernel_bundle_decision(...)`
  - `sessions/store.py::SessionStore.execute_apply_promotion_decision(...)`
- The committed wrapper requires explicit:
  - `--bundle-id`
  - `--action`
  - `--approved-by`
  - `--destination-mappings`
- The committed wrapper exposes optional:
  - `--decision-note`
  - `--workspace-root`
- The committed wrapper reuses the persisted inspection surface before and after the decision:
  - `control-kernel-details`
- Focused committed verification exists in `tests/test_operator_api.py` for:
  - one narrow success path
  - one fail-closed blank `approved_by` case
  - one fail-closed out-of-root destination case
- `AIO-041` proved the wrapper exists, is bundle-scoped, and preserves the sanctioned store-path enforcement model.
- `AIO-041` did not prove the wrapper was ergonomically stable in real operator use.

## 6. What AIO-042 Proved
- `AIO-042` proved one bounded supervised real decision can be driven through the operator-facing `bundle-decision` wrapper against persisted state.
- The committed rehearsal showed:
  - one persisted bundle existed in `pending_review`
  - before-decision inspection was captured through `control-kernel-details`
  - the successful decision step used `scripts/operator_api.py bundle-decision`
  - after-decision inspection was captured through `control-kernel-details`
  - the bundle moved from `pending_review` to `applied`
  - the authoritative destination write existed and matched source content by SHA
  - persisted receipts included:
    - `apply_promotion_decision`
    - `authoritative_destination_write`
- `AIO-042` also exposed two important remaining limits:
  - the operator still had to supply explicit `destination_mappings`
  - direct PowerShell JSON argument handling was brittle enough that two shell-level attempts failed closed before the successful subprocess-backed CLI invocation
- `AIO-042` therefore proved the operator-facing surface is real and usable, but still ergonomically fragile on the exercised shell path.

## 7. What Remains Manual Or Unproven
- Manual or friction-heavy operator glue still remains around:
  - explicit authoring of `destination_mappings`
  - shell-safe entry of JSON mapping payloads
  - manual setup of pending-review bundles outside the operator decision surface
  - manual review judgment before applying or promoting a bundle
- Unproven capability remains:
  - concurrent contention handling
  - later-stage live workflow beyond `architect`
  - bundle rejection as a first-class persisted bundle decision surface
  - real PM / Architect / Dev / QA / Art runtime separation
  - unattended, overnight, or semi-autonomous operation
  - UAT readiness
- The `bundle-decision` wrapper currently proves a narrow persisted-state decision surface, not a broader operator workspace or broader workflow maturity.

## 8. Residual Risks
- Shell and quoting brittleness around JSON input can block operator use even while the store path itself remains correct and fail-closed.
- Explicit destination mappings remain necessary for safety, but they also remain a manual error surface.
- The last-write-wins overwrite behavior observed in `M6` for reused authoritative destination paths remains an open boundary condition; `M7` did not remove that risk.
- Current-state document drift still creates avoidable interpretation risk for fresh readers even though `KANBAN.md`, `ACTIVE_STATE.md`, and the review artifacts are now more current.

## 9. Current Stale-Document / Planning-Surface Conflicts Still Open
- `projects/aioffice/governance/PROJECT.md`
  - still says current accepted posture is `M1` through `M4` complete and `M5` partial, with `AIO-032` through `AIO-034` remaining
  - this conflicts with the authoritative current status in `KANBAN.md`
- `projects/aioffice/governance/WORKFLOW_VISION.md`
  - still says supervised apply/promotion rehearsal evidence remains outstanding until `AIO-032` is completed
  - this is stale relative to completed `M5`, `M6`, and `M7` evidence
- `projects/aioffice/execution/PROJECT_BRAIN.md`
  - still says the next planned slice begins with `AIO-036`
  - this is stale relative to completed `M6` and `M7`
- `projects/aioffice/execution/KANBAN.md`
  - still uses bootstrap header wording:
    - `AIOffice Kanban Bootstrap`
    - `manual founding backlog seed`
  - the status body is current, but the header wording remains stale

## 10. Recommended Next Conservative Slice
- Ratified next slice:
  - `M8 - Post-M7 Operator Decision Input Ergonomics Hardening`
- Selected category:
  - operator decision input/ergonomics hardening
- Rationale:
  - this is the highest-signal remaining manual-glue problem on the already-real control surface
  - the evidence is specific and committed:
    - `AIO-041` proved the wrapper exists and routes through the sanctioned store path
    - `AIO-042` proved the wrapper works, but also recorded shell/JSON brittleness and continued explicit mapping friction
  - this slice stays inside the already-proven operator decision surface instead of widening into later-stage workflow or broader autonomy claims
  - stale-document reconciliation remains real work, but it is not the most direct blocker on the newly proven operator decision surface
- Seed only the minimum tasks for this slice:
  - `AIO-044`
    - define a shell-safe operator decision input contract over the existing `bundle-decision` surface
  - `AIO-045`
    - implement one narrow shell-safe input path and focused verification for explicit destination mappings
  - `AIO-046`
    - rehearse the shell-safe operator decision input path under supervision and record evidence

## 11. Readiness Posture Delta, If Any
- Readiness posture delta: none.
- The accepted posture remains:
  - `ready only for narrow supervised bounded operation`
  - not ready for a bounded supervised semi-autonomous cycle
- Current live workflow proof still stops at `architect`.
- `M7` closed a narrow operator-surface credibility gap, but it did not authorize a readiness upgrade.

## 12. Final Conclusion
- `M7` succeeded at its narrow goal:
  - the system reality was mapped
  - the narrow operator decision surface was defined
  - the operator-facing `bundle-decision` wrapper was implemented with focused verification
  - one bounded supervised operator-facing decision rehearsal was completed against persisted state
- `M7` did not prove broader workflow maturity or readiness beyond the already accepted narrow supervised posture.
- The next conservative move should stay on the same surface and reduce the specific operator input friction observed in committed `AIO-042` evidence.
- The review therefore ratifies exactly one next slice: operator decision input/ergonomics hardening.

## 13. Explicit Non-Claims
- This review does not claim concurrent contention safety.
- This review does not claim later-stage workflow proof.
- This review does not claim real multi-agent maturity.
- This review does not claim unattended, overnight, or semi-autonomous readiness.
- This review does not claim UAT readiness.
- This review does not resolve the stale-document conflicts listed above; it records them explicitly.
