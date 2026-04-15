# Codex Change Isolation Contract

## 1. Purpose And Scope
- Define the narrow maintainability contract for future Codex-delivered changes that touch shared AIOffice control surfaces.
- Make feature-isolation expectations, write-scope discipline, review expectations, and cross-project regression-prevention rules explicit before broader control, UI, or integration work is considered.
- Keep this artifact governance-first. It defines acceptance law for future changes. It does not implement new runtime enforcement by itself.

## 2. Current Committed Reality This Contract Must Fit
- `M1` through `M9` are complete, and this contract is the closing governance artifact for `M10`.
- Current readiness remains `ready only for narrow supervised bounded operation`.
- AIOffice is not ready for a bounded supervised semi-autonomous cycle.
- Current live workflow proof still stops at `architect`.
- The currently real AIOffice control path remains narrow and shared-file heavy:
  - `scripts/operator_api.py` provides the real operator-facing inspection and bundle-decision wrapper surface.
  - `sessions/store.py` provides the sanctioned persisted mutation path and also contains broader shared multi-project behavior.
  - `tests/test_operator_api.py` provides focused verification around the operator control surface rather than broad system isolation guarantees.
- `PRODUCT_CHANGE_GOVERNANCE.md` already defines which product-change and self-modification actions are admin-only.
- `RECOVERY_AND_ROLLBACK_CONTRACT.md` already defines the recovery and rollback discipline that higher-risk changes must eventually obey.
- No committed AIOffice artifact currently proves:
  - a new file-level isolation mechanism
  - concurrency safety
  - real multi-agent runtime isolation
  - writable UI readiness
  - later-stage workflow proof
- This contract therefore defines governance expectations for future Codex-delivered changes inside the current repo reality. It does not claim that the repo is already structurally ideal.

## 3. Why Shared-File Change Risk Is Significant In AIOffice
- AIOffice lives inside a larger repo that contains other projects, donor material, and shared infrastructure.
- Some AIOffice-critical surfaces are already real but structurally mixed:
  - `sessions/store.py` carries AIOffice control behavior and broader shared persistence logic.
  - `scripts/operator_api.py` carries narrow AIOffice operator behavior and related command wiring in one file.
- A small local change in a shared surface can therefore:
  - alter AIOffice control behavior beyond the intended task
  - create regressions in non-AIO flows or donor/shared code paths
  - widen accepted authority or readiness claims unintentionally
  - make later review and recovery harder because blast radius is no longer obvious
- Shared-file risk is especially significant here because current accepted proof is narrow, explicit, and review-backed. The repo does not yet have strong structural isolation that would make broad opportunistic edits safe.

## 4. Feature Isolation Expectations For Codex-Delivered Work
- Current governance expectation:
  - a bounded Codex task should prefer a dedicated file or already-bounded local surface when that path exists lawfully
  - a task must not widen from one narrowly defined concern into unrelated governance, UI, art-pipeline, or later-stage workflow changes
- Future desired discipline:
  - new behavior should be isolated into dedicated modules or clearly bounded helpers before existing mixed shared files are expanded further
  - shared-file edits should shrink over time rather than become the default delivery mode
- When a lawful shared-file edit is unavoidable, feature isolation still requires:
  - keeping the change scoped to one named task and one accepted objective
  - avoiding opportunistic cleanup or adjacent refactors not required by the task
  - keeping new logic locally bounded so future extraction remains feasible
  - preserving the existing sanctioned mutation path instead of introducing side lanes
- A Codex-delivered change is not considered isolated merely because the diff is small. It must also preserve task scope, authority boundaries, and reviewability.

## 5. Write-Scope Discipline And Allowed-Path Expectations
- The declared task packet and accepted artifact path define the default lawful write scope.
- For ordinary governance slices, allowed writes should remain limited to:
  - the expected artifact path
  - `projects/aioffice/execution/KANBAN.md` when task completion truth must be updated
  - `projects/aioffice/governance/ACTIVE_STATE.md` when current accepted state must be updated
- For code-bearing tasks, any shared-file write must be explicitly justified by the task objective and current repo truth.
- Write-scope discipline requires:
  - naming the exact files to be changed before editing
  - staging only those files
  - refusing opportunistic edits in nearby files that are not required by the accepted task
  - stopping if a task can no longer be completed inside its declared write scope without broader product-law review
- Allowed-path expectations are stricter for shared surfaces than for isolated artifacts. If a task starts as a narrow artifact task and later appears to require a mixed shared-file change, it must fail closed instead of silently broadening.

## 6. Handling Mixed Shared Surfaces
- `scripts/operator_api.py`
  - treat as a narrow but high-importance operator control surface
  - changes must preserve bundle-scoped behavior, sanctioned persisted-state routing, and existing fail-closed boundaries unless a separately accepted task explicitly changes them
  - command-surface edits should be paired with focused verification in `tests/test_operator_api.py`
- `sessions/store.py`
  - treat as a high-risk mixed shared surface because it carries AIOffice behavior alongside broader shared persistence responsibilities
  - changes should be avoided unless no narrower lawful path exists
  - when touched, the task packet must explicitly call out the blast radius and the review must verify that the sanctioned mutation path remains intact
- Other shared control files, when they become relevant, should be treated by the same rule:
  - assume higher risk when the file governs authority boundaries, workspace boundaries, stage law, or sanctioned mutation behavior
  - prefer bounded helper extraction or narrow local edits over broad reshaping
- Mixed shared surfaces are not forbidden absolutely, but they are never routine. They require tighter discipline than isolated artifact or single-feature files.

## 7. Review Expectations Before Accepting Codex-Delivered Changes
- Every Codex-delivered change must remain GitHub-reviewable and artifact-backed.
- Review should confirm, at minimum:
  - the task stayed inside accepted scope
  - the changed files match the declared write scope
  - the task did not silently widen readiness, workflow proof, or authority claims
  - the resulting artifact or diff is coherent with current accepted AIOffice posture
- When shared files are touched, review expectations become stricter:
  - the reason the shared file had to change must be explicit
  - the intended blast radius must be explicit
  - the verification should show why adjacent AIOffice and non-AIO paths were not unintentionally changed
  - any unproven risk that remains must be stated explicitly rather than implied away
- Acceptance review remains governance-first. A passing diff alone is not enough if the task violated scope discipline or weakened truth-surface clarity.

## 8. Cross-Project Regression Prevention Expectations
- AIOffice changes must not silently mutate other repo projects or donor surfaces as incidental fallout.
- Cross-project regression prevention requires:
  - avoiding writes outside the declared AIOffice scope unless the task explicitly authorizes them
  - checking whether a touched file is shared across AIOffice and other project paths
  - using focused verification that exercises the changed shared surface without pretending full-repo proof
  - recording any remaining shared-file risk explicitly when broad isolation does not yet exist
- AIOffice-specific success is not sufficient if the same change introduces unreviewed risk for shared repo behavior.
- If a change would require simultaneous broad edits across AIOffice and non-AIO surfaces to stay correct, that change is outside a narrow Codex task unless explicitly re-scoped through accepted governance.

## 9. Expectations For Bounded Task Packets When Shared Files Are Touched
- A bounded task packet that proposes touching a shared file must explicitly state:
  - why the shared file is in scope
  - why a narrower isolated path was not sufficient
  - the exact files allowed to change
  - the verification expected for the shared-file blast radius
  - the explicit non-goals that keep the task from widening
- For high-risk shared surfaces, the packet should also identify:
  - whether the change is ordinary bounded work or product/self-change subject to `PRODUCT_CHANGE_GOVERNANCE.md`
  - whether recovery implications need to be considered under `RECOVERY_AND_ROLLBACK_CONTRACT.md`
- If those packet elements are missing, the task is under-specified for a lawful shared-file edit and should fail closed.

## 10. Required Evidence And Receipts For High-Risk Shared-File Changes
- High-risk shared-file changes should leave a reviewable evidence package that includes:
  - repo-hygiene preflight output
  - current branch and `HEAD` identity
  - exact files changed
  - explicit reason the shared surface had to be touched
  - focused verification output tied to the changed surface
  - exact commit SHA and pushed review anchor
  - explicit statement of residual risk or remaining unproven behavior
- When the shared change touches a sanctioned control surface, the evidence should also show:
  - the sanctioned path that remains in use
  - the checks that guard against unintended authority or path changes
  - the fact that current readiness posture did not change unless a separately accepted review artifact says otherwise
- These evidence expectations are governance-level receipts. This artifact does not claim that new receipt types or automation have already been implemented in code.

## 11. Fail-Closed Conditions
- If a task needs to touch an undeclared shared file to succeed, it fails closed until scope is re-authorized.
- If a task combines a shared control-file change with unrelated UI, art-pipeline, or later-stage workflow work, it fails closed.
- If a task touches a mixed shared surface without focused verification appropriate to that surface, it fails closed.
- If review cannot distinguish the intended AIOffice effect from possible cross-project fallout, it fails closed.
- If a change appears to alter product law, readiness posture, sanctioned mutation behavior, or milestone/state truth without explicit governance authorization, it fails closed.
- If the repo truth surfaces disagree about whether a change is ordinary bounded work or product/self-change, it is treated as higher-risk and fails closed until clarified.

## 12. Explicit Non-Claims
- This contract does not claim implementation of a new isolation mechanism.
- This contract does not claim automatic module boundaries, automatic path guards, or automatic cross-project regression detection now exist.
- This contract does not claim concurrency safety.
- This contract does not claim real multi-agent readiness.
- This contract does not claim UI readiness.
- This contract does not claim later-stage workflow proof.
- This contract does not claim unattended, overnight, or semi-autonomous readiness.
- This contract does not claim UAT readiness.
