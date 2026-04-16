# M12 Protected Surface Block Rehearsal

## 1. Objective And Scope
- Execute one bounded rehearsal showing that the ordinary AIOffice apply/promotion lane fails closed when it attempts to mutate a protected surface.
- Capture factual evidence for:
  - one blocked attempt against an accepted truth surface
  - one blocked attempt against a protected operator/control surface
- Keep the rehearsal bounded to a disposable target and do not treat the rehearsal result as accepted authoritative truth.

## 2. Rehearsal Environment Used
- authoritative source repo:
  - `C:\Users\rodne\OneDrive\Desktop\_AIStudio_POC`
- disposable rehearsal target:
  - `C:\a062`
- rehearsal target branch:
  - `feature/aioffice-m10-change-governance-hardening`
- accepted anchor preserved inside the rehearsal target:
  - working branch: `feature/aioffice-m10-change-governance-hardening`
  - checkpoint tag: `aioffice-m10-closeout-2026-04-16`
  - checkpoint commit: `c079911fbfad6e98a72294e0f90a321710d7910f`
  - snapshot branch: `snapshot/aioffice-m10-closeout-2026-04-16`
  - snapshot commit: `c079911fbfad6e98a72294e0f90a321710d7910f`
- rehearsal target `HEAD` during the exercised path:
  - `6c47131b92956ec03554ed5e1947a8ffa9639536`

## 3. Why The Rehearsal Target Was Bounded And Reviewable
- The rehearsal ran in a disposable local clone rather than the authoritative repo state.
- The exercised ordinary-lane path was the sanctioned persisted store method:
  - `sessions/store.py execute_apply_promotion_decision(...)`
- The target clone was used only to create a pending-review bundle, attempt protected writes, and capture factual error and integrity evidence.
- The disposable clone was deleted after evidence capture, so no rehearsal workspace remains as authoritative repo residue.

## 4. Protected Targets Attempted
- accepted truth surface:
  - `projects/aioffice/execution/KANBAN.md`
- protected operator/control surface:
  - `projects/aioffice/governance/OPERATOR_DECISION_INPUT_CONTRACT.md`

## 5. Exact Steps Executed
1. Cloned the authoritative repo into `C:\a062`.
2. Checked out `feature/aioffice-m10-change-governance-hardening` in the clone.
3. Materialized local access to the accepted `M10` checkpoint tag and snapshot branch inside the clone.
4. Opened a `SessionStore` against the clone with `bootstrap_legacy_defaults=False` so the rehearsal stayed focused on the sanctioned store path.
5. Created one bounded AIOffice workflow, stage run, artifact, control execution packet, and pending-review execution bundle for `AIO-062`.
6. Attempted one ordinary `apply` decision into `projects/aioffice/execution/KANBAN.md`.
7. Verified the apply attempt failed closed, the destination hash stayed unchanged, and the bundle stayed `pending_review`.
8. Attempted one ordinary `apply` decision into `projects/aioffice/governance/OPERATOR_DECISION_INPUT_CONTRACT.md`.
9. Verified the apply attempt failed closed, the destination hash stayed unchanged, and the bundle still stayed `pending_review`.
10. Captured the resulting bundle, path, and hash evidence.
11. Deleted the disposable clone.

## 6. Exact Blocking Errors Observed
- blocked accepted truth surface attempt:
  - `destination_path targets protected core surface class 'accepted truth surface' and ordinary mutation lanes must fail closed.`
- blocked protected operator/control surface attempt:
  - `destination_path targets protected core surface class 'protected operator/control surface' and ordinary mutation lanes must fail closed.`

## 7. Destination Integrity Verification
- accepted truth target:
  - path: `projects/aioffice/execution/KANBAN.md`
  - sha256 before attempt: `8ff2357fc01881814ef3e52f7a3c47414a4dc8f01134ab134d9583e6a0a75078`
  - sha256 after attempt: `8ff2357fc01881814ef3e52f7a3c47414a4dc8f01134ab134d9583e6a0a75078`
  - unchanged: `true`
- protected operator/control target:
  - path: `projects/aioffice/governance/OPERATOR_DECISION_INPUT_CONTRACT.md`
  - sha256 before attempt: `4798684f8474e963944e16d7b530e47ce8f7602b62ed04d437f7a13d835e9224`
  - sha256 after attempt: `4798684f8474e963944e16d7b530e47ce8f7602b62ed04d437f7a13d835e9224`
  - unchanged: `true`

## 8. Pending-Review Verification
- packet id:
  - `packet_200b96619b26`
- bundle id:
  - `bundle_9b72cd350954`
- initial bundle acceptance state:
  - `pending_review`
- initial evidence receipt count:
  - `1`
- bundle state after accepted truth attempt:
  - `pending_review`
- evidence receipt count after accepted truth attempt:
  - `1`
- bundle state after protected operator/control attempt:
  - `pending_review`
- evidence receipt count after protected operator/control attempt:
  - `1`
- final bundle acceptance state:
  - `pending_review`
- final evidence receipt count:
  - `1`

## 9. What The Rehearsal Proved
- The current ordinary AIOffice apply/promotion lane now fails closed when it is pointed at a protected core surface.
- The block is explicit and names the protected class rather than silently rerouting or partially applying the write.
- The protected destination content remained unchanged for the exercised accepted truth and protected operator/control targets.
- The pending-review execution bundle remained `pending_review`, so accepted truth was not advanced by a blocked ordinary-lane attempt.
- This proves the current sanctioned path can enforce protected-surface blocking without inventing a separate admin mutation lane.

## 10. What Remains Unproven
- This rehearsal did not prove every protected class exhaustively.
- This rehearsal did not exercise a blocked attempt through a separate admin-only runtime lane because no such lane exists in code yet.
- This rehearsal did not widen workflow proof beyond the existing architect-bounded posture.
- This rehearsal did not prove later-stage workflow, UI readiness, concurrency safety, real multi-agent maturity, or semi-autonomous readiness.

## 11. Explicit Boundary Statement
- This rehearsal does not upgrade readiness.
- Current readiness remains:
  - `ready only for narrow supervised bounded operation`
  - not ready for a bounded supervised semi-autonomous cycle
- This rehearsal does not widen live workflow proof.
- Current live workflow proof still stops at `architect`.
- The disposable clone was a reviewable rehearsal target only and was not treated as accepted authoritative truth.

## 12. Rehearsal-Blocking Fixes
- No rehearsal-blocking code fix was required for this slice.
