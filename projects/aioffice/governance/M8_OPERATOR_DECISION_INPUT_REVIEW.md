# M8 Operator Decision Input Review

## 1. Purpose
- Record one explicit post-`M8` review grounded only in committed evidence.
- State exactly what `AIO-044`, `AIO-045`, and `AIO-046` proved.
- Reconcile the committed board/state inconsistency that left completed `AIO-045` and `AIO-046` physically under `Backlog`.
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
  - `projects/aioffice/governance/OPERATOR_DECISION_SURFACE.md`
  - `projects/aioffice/governance/OPERATOR_DECISION_INPUT_CONTRACT.md`
  - `projects/aioffice/governance/SYSTEM_REALITY_MAP.md`
- Rehearsal and proof artifacts reviewed:
  - `projects/aioffice/artifacts/M6_APPLY_BRANCH_REHEARSAL.md`
  - `projects/aioffice/artifacts/M6_SHARED_STORE_REHEARSAL.md`
  - `projects/aioffice/artifacts/M7_OPERATOR_DECISION_SURFACE_REHEARSAL.md`
  - `projects/aioffice/artifacts/M8_OPERATOR_DECISION_INPUT_REHEARSAL.md`
- Implementation grounding reviewed:
  - `scripts/operator_api.py`
  - `tests/test_operator_api.py`
  - `sessions/store.py`
- Additional planning-surface conflict checks reviewed because they were already recorded as open in committed governance:
  - `projects/aioffice/execution/PROJECT_BRAIN.md`
  - `projects/aioffice/governance/WORKFLOW_VISION.md`
- No new rehearsal runs were performed for this review.

## 3. Current Accepted Posture Before Review
- `M1` through `M8` are complete.
- Current readiness remains:
  - `ready only for narrow supervised bounded operation`
  - not ready for a bounded supervised semi-autonomous cycle
- Current live workflow proof still stops at `architect`.
- `M8` was a narrow operator decision input/ergonomics hardening slice over an already-proven operator decision surface.
- `M8` was not a later-stage workflow slice, not a concurrency slice, and not a readiness-upgrade slice.

## 4. What AIO-044 Proved
- `AIO-044` proved one shell-safe operator input contract was defined narrowly over the existing `bundle-decision` surface.
- The committed design selected one input path only:
  - `--destination-mappings-file`
- The committed contract kept explicit destination mappings mandatory and preserved fail-closed boundaries.
- The committed contract tied the design directly to real `AIO-042` evidence:
  - the wrapper already existed
  - the store path already enforced the real mutation rules
  - the brittle point was shell transport of inline JSON, not store semantics
- `AIO-044` proved design clarity and scope discipline only.
- `AIO-044` did not prove implementation or supervised operator use by itself.

## 5. What AIO-045 Proved
- `AIO-045` proved the operator-facing `bundle-decision` wrapper now supports:
  - `--destination-mappings-file`
- The committed implementation in `scripts/operator_api.py`:
  - decodes a JSON file before the decision call
  - keeps the command bundle-scoped
  - keeps explicit mappings required
  - still routes through `SessionStore.execute_apply_promotion_decision(...)`
- Focused committed verification in `tests/test_operator_api.py` proved at least:
  - one success path using `--destination-mappings-file`
  - one missing-file fail-closed case
  - one invalid-JSON fail-closed case
  - one preserved out-of-root failure after file decoding
- `AIO-045` proved the shell-safe file transport exists and preserves the sanctioned store path and fail-closed behavior.
- `AIO-045` did not prove real supervised operator use in practice.

## 6. What AIO-046 Proved
- `AIO-046` proved one bounded supervised real decision can be driven through:
  - `scripts/operator_api.py bundle-decision`
  - `--destination-mappings-file`
- The committed rehearsal showed:
  - one persisted bundle existed in `pending_review`
  - before-decision inspection used `control-kernel-details`
  - the successful decision step used the file-based mapping path, not inline JSON
  - after-decision inspection used `control-kernel-details`
  - the bundle moved from `pending_review` to `applied`
  - the authoritative destination write existed and matched source content by SHA
  - no unrelated memory or cross-project residue appeared in the transient rehearsal workspace
- `AIO-046` proved the file-based path reduced shell and JSON transport brittleness on the exercised operator path.
- `AIO-046` did not prove:
  - automatic bundle discovery
  - automatic destination authoring
  - concurrency handling
  - later-stage workflow

## 7. What Remains Manual Or Unproven
- Explicit destination authoring remains manual:
  - the operator still must choose and author `destination_path` deliberately
  - no mapping inference exists
- Bundle discovery and operator context remain manual:
  - the operator still must know or discover the target `bundle_id`
  - the operator still must inspect the persisted context deliberately before deciding
- Planning-surface interpretation still has manual friction because not every stale document has been reconciled to post-`M8` truth.
- Unproven capability remains:
  - concurrent contention handling
  - later-stage live workflow beyond `architect`
  - real PM / Architect / Dev / QA / Art runtime maturity
  - unattended, overnight, or semi-autonomous operation
  - UAT readiness

## 8. Residual Risks
- Explicit destination authoring remains an intentional but real error surface.
- Bundle discovery remains weaker than the now-proven decision input path; the operator still needs manual context gathering.
- The last-write-wins authoritative destination overwrite behavior observed in `M6` remains an open filesystem-level risk outside the one-bundle `M8` rehearsal.
- Stale current-state and planning-surface wording still creates avoidable audit friction even though the strongest review anchors are current.

## 9. Current Stale-Document / Planning-Surface / Board-Structure Conflicts Still Open
- `projects/aioffice/governance/PROJECT.md`
  - still says current accepted posture is `M1` through `M4` complete and `M5` partial
  - still says `AIO-032` through `AIO-034` remain
- `projects/aioffice/governance/WORKFLOW_VISION.md`
  - still says supervised apply/promotion rehearsal evidence remains outstanding until `AIO-032`
- `projects/aioffice/execution/PROJECT_BRAIN.md`
  - still says the next planned slice begins with `AIO-036`
- `projects/aioffice/execution/KANBAN.md`
  - still carries stale bootstrap/header wording such as:
    - `AIOffice Kanban Bootstrap`
    - `manual founding backlog seed`
- pre-reconciliation board structure conflict found in the committed pre-task `KANBAN.md` state:
  - `AIO-045` had `status: completed` but was still physically located under `## Backlog`
  - `AIO-046` had `status: completed` but was still physically located under `## Backlog`

## 10. Board/State Reconciliation Decisions Taken In This Task
- Decision 1:
  - create and commit `projects/aioffice/governance/M8_OPERATOR_DECISION_INPUT_REVIEW.md`
  - result: `AIO-047` may be recorded as completed
- Decision 2:
  - move `AIO-045` and `AIO-046` out of `## Backlog` and into `## Completed`
  - rationale: the committed evidence and status fields already supported completion, so the physical board structure was inconsistent with authoritative task state
- Decision 3:
  - keep the broader stale `KANBAN.md` bootstrap/header wording open
  - rationale: that wording conflict is real, but broader planning-surface cleanup is outside the minimum factual reconciliation needed in this task

## 11. Recommended Next Conservative Slice
- Ratified next slice:
  - `M9 - Post-M8 Current-State And Planning-Surface Reconciliation`
- Selected category:
  - current-state / planning-surface reconciliation and cleanup
- Rationale:
  - the file-based operator decision path is now defined, implemented, and rehearsed
  - the remaining highest-confidence conservative gap is not another control-behavior change; it is the stale and conflicting current-state surface that still forces manual interpretation
  - explicit destination authoring should remain manual for safety rather than being “smoothed over” prematurely
  - operator bundle discovery/context ergonomics is a plausible future slice, but it is less conservative than first reconciling the documents and planning surfaces that define what the current system claims to be
- Seed only the minimum next task for this slice:
  - `AIO-048`
    - reconcile stale current-state and planning-surface wording to post-`M8` truth

## 12. Readiness Posture Delta, If Any
- Readiness posture delta: none.
- The accepted posture remains:
  - `ready only for narrow supervised bounded operation`
  - not ready for a bounded supervised semi-autonomous cycle
- Current live workflow proof still stops at `architect`.
- `M8` reduced operator input brittleness on the exercised decision path, but it did not authorize a readiness upgrade.

## 13. Final Conclusion
- `M8` succeeded at its narrow goal:
  - one shell-safe operator decision input contract was defined
  - the operator-facing wrapper was hardened to accept a file-based mapping path
  - focused verification proved the new transport remained fail-closed
  - one bounded supervised rehearsal proved the file-based path against persisted state
- `M8` did not prove broader workflow maturity, concurrency safety, or any readiness increase beyond the accepted narrow supervised posture.
- The board/state inconsistency in `KANBAN.md` for `AIO-045` and `AIO-046` was factual and is reconciled by this task.
- The next conservative move should now focus on reconciling stale current-state and planning-surface wording so audit and operator interpretation no longer depend on manual conflict resolution.

## 14. Explicit Non-Claims
- This review does not claim concurrent contention safety.
- This review does not claim later-stage workflow proof.
- This review does not claim real multi-agent maturity.
- This review does not claim unattended, overnight, or semi-autonomous readiness.
- This review does not claim UAT readiness.
- This review does not claim automatic destination authoring or automatic bundle discovery.
