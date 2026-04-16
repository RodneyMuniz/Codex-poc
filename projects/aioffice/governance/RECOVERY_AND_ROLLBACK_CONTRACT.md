# Recovery And Rollback Contract

## 1. Purpose
- Define the narrow AIOffice contract for snapshots, version checkpoints, restore, rollback, and the bounded rehearsal plan required before broader writable or parallel surfaces are considered.
- Formalize recovery discipline before UI expansion, stronger autonomy claims, or broader control-surface broadening are considered.
- Keep the contract grounded in current committed AIOffice reality without claiming that restore or rollback automation is already implemented or rehearsed.

## 2. Current Committed Reality This Contract Must Fit
- `M1` through `M10` are complete.
- No post-`M10` milestone is ratified yet.
- Current readiness remains `ready only for narrow supervised bounded operation`.
- AIOffice is not ready for a bounded supervised semi-autonomous cycle.
- Current live workflow proof still stops at `architect`.
- `projects/aioffice/execution/KANBAN.md` remains the authoritative milestone and task truth surface.
- `projects/aioffice/governance/ACTIVE_STATE.md` remains the accepted branch, checkpoint, snapshot, and posture anchor for external review.
- `PRODUCT_CHANGE_GOVERNANCE.md` now defines which product/self-change actions are admin-only and must not be collapsed into ordinary execution-bundle approval.
- The current repo already contains shared recovery-related primitives in `sessions/store.py`:
  - `create_dispatch_backup(...)`
  - `restore_dispatch_backup(...)`
  - `restore_history` inspection support
- Those primitives are not yet an accepted AIOffice recovery contract by themselves.
- The currently proven operator decision surfaces remain:
  - `scripts/operator_api.py control-kernel-details`
  - `scripts/operator_api.py bundle-decision`
  - `sessions/store.py execute_apply_promotion_decision(...)`
- No committed AIOffice artifact currently proves:
  - automated snapshot/version/restore/rollback discipline
  - a restore or rollback rehearsal
  - broader writable UI or later-stage workflow recovery semantics

## 3. Exact Definitions
- `snapshot`
  - a deliberate captured recovery package for a defined scope at a defined moment, including the exact refs, commit identity, and state evidence needed to attempt later recovery safely
- `version checkpoint`
  - a named immutable or intended-immutable recovery boundary tying together a checkpoint tag, snapshot branch, commit SHA, and the authoritative docs/task truth that describe that accepted state
- `restore`
  - the controlled re-creation or rehydration of a previously snapshotted state into a reviewable target so its contents can be inspected and verified
  - restore does not by itself make that state the accepted current truth again
- `rollback`
  - the explicit operator-admin authorized act of returning authoritative AIOffice product state to a previously verified checkpoint after restore-level verification succeeds
  - rollback changes what AIOffice treats as the accepted current product state

## 4. Relationship Between Working Branch, Checkpoint Tag, Snapshot Branch, Commit SHA, Authoritative Docs, And Task Truth
- `working branch`
  - the mutable implementation lane for the current accepted slice
  - in current committed reality: `feature/aioffice-m10-change-governance-hardening`
- `checkpoint tag`
  - the milestone closeout anchor for a previously accepted boundary
  - intended to identify the exact checkpoint commit immutably
  - in current committed reality: `aioffice-m10-closeout-2026-04-16`
- `snapshot branch`
  - a human-readable recovery ref expected to point at the same checkpoint commit when created
  - kept as a reviewable snapshot anchor without replacing the checkpoint tag
  - in current committed reality: `snapshot/aioffice-m10-closeout-2026-04-16`
- `commit SHA`
  - the exact Git object identity underneath the checkpoint tag, snapshot branch, and working branch head at a specific moment
- `authoritative docs and task truth`
  - `projects/aioffice/execution/KANBAN.md` defines authoritative milestone/task truth
  - `projects/aioffice/governance/ACTIVE_STATE.md` defines accepted branch/checkpoint/posture anchor
  - the relevant governance artifacts define the accepted control boundary around that state
- A lawful recovery target is not identified by Git refs alone.
- A lawful recovery target is the combined package of:
  - checkpoint tag
  - snapshot branch
  - exact commit SHA
  - matching authoritative docs and task truth
- If those surfaces disagree, the checkpoint is not recovery-ready and recovery must fail closed.

## 5. Clean-Worktree Preconditions
- Before creating a recovery snapshot, restore, or rollback action:
  - `git status --short` must be empty
  - the current branch must be the expected working branch or explicitly declared recovery target branch
  - the relevant checkpoint tag and snapshot branch must resolve exactly as expected
  - the required authoritative docs must be present at `HEAD`
- Before destructive restore or rollback actions:
  - a fresh pre-action snapshot must be created for the current state
  - no uncommitted local residue may remain
  - no ambiguous repo root or duplicate-root path may be in use
- If any precondition fails, the action fails closed and no destructive recovery step is lawful.

## 6. Authority And Approval Boundaries
- Ordinary bounded execution recovery concerns may remain in the ordinary supervised execution lane only when they do not change product law or authoritative accepted truth.
- Product/self-change recovery concerns are admin-only under `PRODUCT_CHANGE_GOVERNANCE.md`.
- Authority boundary:
  - ordinary operator approval may cover bounded non-product-changing recovery inside an already-accepted execution scope
  - operator-admin approval is required for restore or rollback actions that affect:
    - governance law
    - control behavior
    - sanctioned mutation paths
    - milestone/task truth
    - accepted current product posture
- Restore may be initiated for verification purposes before rollback is authorized, but rollback itself requires explicit operator-admin approval.
- No ordinary `bundle-decision` approval path may be used as a substitute for admin-only restore or rollback authority.

## 7. Ordinary Bounded Execution Recovery Vs Admin-Only Product/Self-Change Recovery
- Ordinary bounded execution recovery:
  - concerns bounded rehearsal or execution artifacts produced inside already-sanctioned product behavior
  - may include re-checking a bundle, rebuilding a transient workspace, or rehydrating non-authoritative outputs for inspection
  - does not alter product law, control guardrails, or accepted milestone/state truth by itself
- Admin-only product/self-change recovery:
  - concerns the AIOffice product's own governing behavior or accepted truth surfaces
  - includes restore or rollback of:
    - governance artifacts that define accepted posture
    - `projects/aioffice/execution/KANBAN.md`
    - `projects/aioffice/governance/ACTIVE_STATE.md`
    - control-path code such as `scripts/operator_api.py` and `sessions/store.py` when product behavior is affected
    - milestone checkpoint refs used as accepted recovery anchors
- If classification is ambiguous, recovery is treated as admin-only until explicitly resolved.

## 8. Snapshot Contract
- A lawful snapshot must capture, at minimum:
  - working branch name
  - checkpoint tag name, if one is being anchored or referenced
  - snapshot branch name, if one is being anchored or referenced
  - exact commit SHA
  - clean-worktree confirmation
  - the authoritative AIOffice document set required to interpret the state
- Required snapshot triggers:
  - before any destructive restore
  - before any rollback
  - before any admin-only product/self-change operation with meaningful blast radius
  - before any future restore/rollback rehearsal
- Snapshot contract rules:
  - snapshot creation must be explicit, not inferred
  - snapshot naming must be reviewable and tied to a specific boundary
  - snapshot capture must not silently rewrite history
  - snapshot capture must not rely on local-only narration
- In the current Git-based AIOffice reality, the minimum lawful snapshot package is expected to include:
  - an exact commit SHA
  - a pushed checkpoint tag or equivalent immutable anchor
  - a pushed snapshot branch
  - matching authoritative docs committed at that boundary

## 9. Restore Contract
- Restore means recreating a prior checkpointed state into a reviewable target so that correctness can be verified before any rollback decision is made.
- Restore rules:
  - restore target must be explicit
  - restore source snapshot/checkpoint must be explicit
  - restore must not be treated as accepted current truth until verification succeeds
  - restore should prefer a bounded reviewable target over direct destructive overwrite where possible
- Restore preconditions:
  - clean worktree
  - explicit identified snapshot/checkpoint package
  - explicit requested-by authority
  - explicit restoration target
  - pre-action snapshot of the current state if the restore could be destructive
- Restore correctness must be verified against:
  - expected branch/tag/SHA relationships
  - expected authoritative doc content
  - expected task/milestone truth in `KANBAN.md`
  - expected accepted posture in `ACTIVE_STATE.md`
- A restore that has not been verified remains a candidate state, not an accepted state.

## 10. Rollback Contract
- Rollback is narrower and stricter than restore.
- Rollback means making a previously verified checkpoint authoritative again for the product state.
- Rollback rules:
  - rollback target must already have passed restore-level verification or equivalent deterministic verification
  - rollback must be explicitly operator-admin approved
  - rollback must capture the current state first so the just-replaced state is not lost
  - rollback must not rely on force-push, hidden history rewrite, or undocumented manual correction
- Rollback is lawful only when:
  - the target checkpoint is explicit
  - the target checkpoint package is internally consistent
  - the current state has been snapshotted
  - the verification package shows that rollback returns to the intended accepted state
- Rollback is not:
  - a convenience undo for ordinary execution-bundle decisions
  - a substitute for bundle rejection
  - permission to rewrite acceptance history silently

## 11. Fail-Closed Conditions
- Dirty worktree: fail
- Wrong branch for the declared action: fail
- Missing checkpoint tag, snapshot branch, or exact commit identity: fail
- Checkpoint tag and snapshot branch resolving to different unintended commits: fail
- Missing or inconsistent authoritative docs for the target checkpoint: fail
- Missing fresh pre-action snapshot before destructive restore or rollback: fail
- Missing operator-admin approval for admin-only recovery: fail
- Ambiguous recovery classification between ordinary and admin-only: fail
- Missing verification package for restore correctness: fail
- Missing verification package for rollback correctness: fail
- Any destructive action that would rely on force-push, hidden history rewrite, or undocumented filesystem mutation: fail

## 12. Verification Requirements Before Destructive Restore/Rollback Actions
- Required verification before destructive restore or rollback:
  - confirm repo root is the authoritative root
  - confirm `git status --short` is empty
  - confirm working branch name
  - confirm target checkpoint tag resolves
  - confirm target snapshot branch resolves
  - confirm target commit SHA resolves
  - confirm authoritative docs exist at the target state
  - confirm `KANBAN.md` and `ACTIVE_STATE.md` agree about milestone/task posture
  - confirm the target state matches the intended accepted checkpoint description
- Required destructive-action gate:
  - no restore or rollback action is lawful until those checks pass deterministically
- Verification must be artifact-backed and reviewable, not chat-only.

## 13. Evidence And Receipt Expectations For Future Restore Or Rollback Runs
- Future restore or rollback runs should capture a reviewable evidence package that includes:
  - pre-action repo hygiene output
  - current branch, tag, snapshot branch, and commit SHA
  - target checkpoint tag, snapshot branch, and commit SHA
  - authoritative-doc existence check
  - pre-action snapshot confirmation
  - explicit approval identity and authority lane
  - post-action branch/tag/SHA state
  - post-action `KANBAN.md` and `ACTIVE_STATE.md` verification
  - any residual risk or mismatch detected
- Expected future receipt/evidence classes include:
  - `recovery_preflight`
  - `recovery_snapshot_created`
  - `restore_requested`
  - `restore_completed`
  - `restore_verified`
  - `rollback_requested`
  - `rollback_completed`
  - `rollback_verified`
- These are contract-level evidence expectations only.
- This artifact does not claim those receipt classes are already implemented in runtime code.

## 14. Bounded Rehearsal Plan
- Rehearsal purpose:
  - prove that the recovery contract can be exercised in a bounded, reviewable, fail-closed way before broader writable or parallel surfaces are considered
- Rehearsal prerequisites:
  - accepted recovery contract exists
  - accepted admin-only governance boundary exists
  - a named checkpoint tag and snapshot branch exist
  - a clean worktree exists
  - the rehearsal target is bounded and does not broaden into UI or later-stage workflow work
- Exact artifacts and evidence to capture:
  - preflight repo hygiene output
  - branch/tag/snapshot/SHA resolution output
  - pre-action snapshot evidence
  - restore verification report
  - rollback verification report
  - updated post-rehearsal review artifact with explicit residual risks
- Pass criteria:
  - restore target matches the intended checkpoint package exactly
  - rollback target restores the intended accepted truth surfaces exactly
  - all verification checks pass deterministically
  - no unrelated residue remains after the rehearsal
  - no readiness or workflow-proof inflation is introduced
- Fail criteria:
  - any ref mismatch
  - dirty worktree
  - target-state mismatch
  - authoritative-doc mismatch
  - missing pre-action snapshot
  - ambiguous approval authority
- Restore correctness verification:
  - compare branch/tag/snapshot/SHA to the intended checkpoint
  - compare authoritative docs at the target against expected accepted posture
  - verify `KANBAN.md` and `ACTIVE_STATE.md` match the intended checkpoint truth
- Rollback correctness verification:
  - verify the pre-rollback state was snapshotted
  - verify the post-rollback state matches the intended checkpoint package
  - verify the restored accepted truth is externally reviewable on the pushed branch state
- Residual-risk recording:
  - record any manual steps still required
  - record any repo-structure or shared-file risks still present
  - record any remaining ambiguity between Git ref recovery and product-state recovery
- Execution note:
  - this rehearsal is planned here only
  - it is not executed in `AIO-051`
  - a later bounded task must explicitly authorize and record the rehearsal

## 15. Explicit Non-Claims
- This artifact does not claim restore/rollback automation is already implemented for AIOffice.
- This artifact does not claim any restore or rollback rehearsal has already been executed.
- This artifact does not claim UI readiness.
- This artifact does not claim later-stage workflow proof.
- This artifact does not claim concurrency safety.
- This artifact does not claim real multi-agent maturity.
- This artifact does not claim unattended, overnight, or semi-autonomous readiness.
- This artifact does not claim UAT readiness.
