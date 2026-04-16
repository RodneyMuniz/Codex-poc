# M13 Scope Rebaseline

## 1. Purpose
- Record the explicit pre-implementation rebaseline of `M13`.
- Preserve the historical fact that `M13` was first ratified differently, then rebaselined before implementation.
- Keep the active milestone, seeded task ids, and current non-claims aligned to committed repo truth.

## 2. Accepted Starting Truth Before Rebaseline
- `M12 - Protected Core Surfaces Enforcement` is complete.
- `M13` was originally ratified as `Design Lane Operationalization`.
- `AIO-064` through `AIO-067` were seeded only under that original `M13` scope.
- no `M13` implementation had started yet when this rebaseline was made.
- current live workflow proof still stops at `architect`.
- readiness remains `ready only for narrow supervised bounded operation`.

## 3. Explicit Rebaseline Decision
- Before implementation, the operator explicitly rebaselined `M13` from `Design Lane Operationalization` to `Structural Truth Layer Baseline`.
- The `AIO-064` through `AIO-067` task ids are preserved and reseeded under the new `M13` scope rather than replaced with new ids.
- This is a review and decision change recorded explicitly in governance. It is not a silent mutation.

## 4. Why The Rebaseline Was Necessary
- traceability, dependency-impact, and system-map maturity are still materially behind control-surface maturity
- current governance hygiene is still weak
- the `AIO-061` caution exposed that protected-surface enforcement is still conservative and not yet supported by a stronger structural map
- workflow breadth should not expand before dependency and impact truth improve

## 5. Deferred Rather Than Canceled
- design-lane work is deferred, not canceled
- the accepted direction is to strengthen structural truth, traceability, and impact-review foundations before resuming workflow-breadth expansion

## 6. Directional Queue Only
- likely next slice after `M13`: hook and automation discipline for the repo-governed milestone loop
- later likely breadth slice: design-lane operationalization
- these are directional queue notes only and are not ratified milestones

## 7. Active Anchor Facts For This Rebaseline
- active planning branch: `feature/aioffice-m13-design-lane-operationalization`
- accepted closeout / ratification commit before this change: `c5a3da56f89b9b45265ec885207153978ae9bf9f`
- accepted starting-point snapshot branch: `snapshot/aioffice-m12-closeout-2026-04-16`

## 8. Explicit Non-Claims
- no readiness or workflow-proof upgrade is authorized
- no design-lane proof is claimed
- no later-stage workflow proof is claimed
- no hook, automation, or graph-runtime implementation is authorized by this artifact by itself
- no post-`M13` milestone is ratified here
