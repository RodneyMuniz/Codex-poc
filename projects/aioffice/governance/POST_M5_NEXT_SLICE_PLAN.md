# Post-M5 Next Slice Plan

## 1. Purpose
- Turn the accepted post-`M5` gaps into the next narrow, testable, fail-closed proof slice.
- Preserve `M5` as completed work rather than reopening it.
- Avoid broad roadmap expansion while the current proof boundary still has explicitly recorded gaps.

## 2. Current Accepted Posture After M5 Closeout
- `execution/KANBAN.md` remains the authoritative backlog source.
- `M5` is completed.
- The current readiness posture remains:
  - `ready only for narrow supervised bounded operation`
  - not ready for a bounded supervised semi-autonomous cycle
- The current proven live workflow boundary still stops at `architect`.
- `AIO-033`, `AIO-034`, and `AIO-035` are completed and do not need to be reopened for this planning pass.

## 3. Proven Boundaries
- Sanctioned persisted control-kernel state is the source of truth for the proven slice.
- Read-only inspection is proven on the sanctioned persisted-state path.
- Fail-closed first-slice checks are proven through `architect`.
- Operator CLI proof exists for the supervised architect-stop path.
- Controlled `promote` behavior is implemented and proven under supervised rehearsal.
- Multi-run supervised coverage exists on the validated isolated-workspace path.
- The known isolated-workspace residue regression was remediated narrowly and did not reappear on the validated path.

## 4. Unproven Boundaries
- Supervised proof of the separate `apply` branch is still missing.
- Same-workspace repeated-run and shared-store contention behavior are still unproven.
- Later-stage workflow beyond `architect` remains unproven.
- Unattended and overnight operation remain unproven.

## 5. Recommended Next Slice Objective
- Objective: prove the still-unvalidated control paths that sit inside the current sanctioned boundary before attempting later-stage workflow expansion.

### Option A: `apply` branch proof plus shared-store / same-workspace proof
- Stays inside the already implemented control surface.
- Reduces ambiguity around the current readiness boundary without broadening the workflow claim.
- Keeps failure attribution narrow because it exercises known sanctioned paths rather than introducing later-stage stage-work at the same time.

### Option B: later-stage workflow expansion
- Would widen the proof boundary and the implementation surface at the same time.
- Would mix unresolved current-path validation gaps with new stage-contract proof work.
- Raises the risk of over-claim because later-stage execution can look like progress while still leaving the current control-path gaps unresolved.

### Conservative Recommendation
- Choose Option A first.
- Rationale: the separate `apply` branch and same-workspace/shared-store behavior are directly named in the accepted `M5` readiness review as missing proof within the current boundary. Closing those gaps is a safer prerequisite than expanding into `design`, `build_or_write`, `qa`, or `publish`.

## 6. Proposed Next Tasks
- `AIO-036`:
  - rehearse the sanctioned `apply` branch under supervision and record factual evidence
- `AIO-037`:
  - run a bounded same-workspace repeated-run / shared-store rehearsal and record whether collision, leakage, residue, or contention appears
- `AIO-038`:
  - record a narrow review of what the new slice proved, what remains unproven, and whether the readiness posture changed

## 7. Why These Tasks Come Before Broader Autonomy Or Later-Stage Expansion
- They exercise already implemented sanctioned paths instead of mixing proof with new workflow construction.
- They directly target the highest-signal gaps named in the accepted `M5` readiness review.
- They keep the system fail-closed by strengthening the current boundary before widening it.
- They preserve honest sequencing: prove current-path behavior first, then decide whether later-stage expansion is justified.

## 8. Risks Of Skipping This Slice
- Later-stage expansion could rest on an unproven `apply` path.
- Same-workspace or shared-store instability could remain hidden until the workflow surface is larger and harder to debug.
- Readiness claims could drift upward without direct evidence.
- Failure analysis would become harder because new later-stage behavior and unresolved current-path behavior would be entangled.

## 9. Immediate Operator Decision Needed
- Approve whether the next operational slice should stay narrow and begin with `AIO-036` through `AIO-038` under a planned `M6` proof milestone.
- If approved, the first execution step should be moving `AIO-036` into `ready` without treating that as proof of later-stage workflow or improved semi-autonomous readiness.
