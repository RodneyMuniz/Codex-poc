# Operator Decision Surface

## 1. Purpose
- Define one narrow operator-facing surface for inspecting already-persisted `pending_review` execution bundles and issuing one sanctioned `apply` or `promote` decision against that persisted state.
- Reduce current manual glue on the already-real apply/promotion path without widening workflow proof, redesigning store behavior, or changing readiness claims.
- Provide the exact bounded design target for `AIO-041`.

## 2. Current Committed Reality This Surface Must Fit
- Current accepted posture remains:
  - `M1` through `M6` complete
  - `M7` active as a narrow operator decision-surface hardening slice
  - `ready only for narrow supervised bounded operation`
  - not ready for a bounded supervised semi-autonomous cycle
  - current live workflow proof still stops at `architect`
- The authoritative mutation path already exists in `sessions/store.py` as `SessionStore.execute_apply_promotion_decision(...)`.
- That store path already enforces, at minimum:
  - bundle existence
  - `acceptance_state == pending_review`
  - explicit `approved_decision.decision == approved`
  - explicit `approved_decision.action in {apply, promote}`
  - non-empty `approved_decision.approved_by`
  - non-empty `destination_mappings`
  - exact mapping coverage over `produced_artifact_ids`
  - destination-path containment inside the packet `authoritative_workspace_root`
  - blocking writes into governance-controlled paths, the non-authoritative artifact tree, and packet-forbidden paths
- The current operator CLI reality in `scripts/operator_api.py` is narrower than the store reality:
  - `control-kernel-details` exists as the current operator-facing read-only inspection surface
  - generic approval commands such as `approve`, `approve-resume`, and `reject` act on approval IDs, not on persisted execution bundles
  - no generic operator-facing bundle decision command exists yet for `apply` or `promote`
- `workspace_root.py` already enforces authoritative-root and authoritative-path checks for optional inspection workspace targeting.
- `state_machine.py` currently proves the live workflow slice only through `architect`; this decision surface must not imply later-stage workflow proof.

## 3. Supported Decision Scope
- One bundle at a time.
- One explicit sanctioned decision at a time.
- Supported actions:
  - `apply`
  - `promote`
- Supported bundle state:
  - only bundles currently persisted as `pending_review`
- Supported source of truth:
  - already-existing sanctioned persisted state in `sessions/studio.db`
- Supported operator flow:
  1. inspect a target bundle through the existing read-only control-kernel surface
  2. issue one explicit approved decision against that same bundle
  3. inspect the resulting persisted state and decision receipts
- This surface does not create bundles, does not infer readiness, and does not advance workflow beyond the already-proven control boundary.

## 4. Required Operator Inputs
- `bundle_id`
  - required
  - the primary decision target identifier
- `action`
  - required
  - must be exactly `apply` or `promote`
- `approved_by`
  - required
  - must be a non-empty operator identity string
- `destination_mappings`
  - required
  - must be an explicit non-empty mapping set supplied by the operator
- `decision`
  - fixed to `approved` for this narrow surface
  - not a free-form operator choice in this slice
- `decision_note`
  - optional
  - if supplied, must be non-empty
- `workspace_root`
  - optional only when the operator needs to inspect or decide against a sanctioned non-default rehearsal workspace
  - if supplied, it must resolve inside the authoritative workspace root and must already contain `sessions/studio.db`

## 5. Required Bundle Identifiers And Lookup Behavior
- Primary bundle identifier:
  - `bundle_id`
- Required lookup behavior:
  - the surface resolves the bundle first
  - the surface then resolves the source packet from `bundle.packet_id`
  - the surface then relies on persisted packet context for:
    - `project_name`
    - `task_id`
    - `workflow_run_id`
    - `stage_run_id`
    - `authoritative_workspace_root`
    - `allowed_write_paths`
    - `forbidden_paths`
- Existing read-only lookup surface:
  - `scripts/operator_api.py control-kernel-details --bundle-id <bundle_id> [--workspace-root <path>]`
- Optional cross-check identifiers for inspection only:
  - `workflow_run_id`
  - `stage_run_id`
  - `packet_id`
- If any optional cross-check identifiers are later accepted by `AIO-041`, they must be treated only as mismatch detectors:
  - they may narrow or verify inspection context
  - they must not replace `bundle_id` as the authoritative decision target
  - any mismatch must fail closed

## 6. Destination-Mapping Rules
- The surface must require explicit operator-supplied `destination_mappings`.
- The surface must not infer destination paths automatically.
- Each mapping must contain:
  - `source_artifact_id`
  - `destination_path`
- Mapping rules must match the existing sanctioned store behavior:
  - `destination_mappings` must be a non-empty list
  - each mapping must be a dictionary/object
  - `source_artifact_id` entries must be unique
  - `destination_path` entries must be unique
  - every `source_artifact_id` must belong to the bundle `produced_artifact_ids`
  - every produced artifact in the bundle must receive exactly one destination mapping
  - each source artifact must have a persisted `artifact_path`
  - each source artifact path must already be covered by the packet `allowed_write_paths`
  - `destination_path` must be normalized as a repo-relative path
  - `destination_path` must not equal the non-authoritative source artifact path
  - `destination_path` must stay within the packet `authoritative_workspace_root`
  - `destination_path` must not target:
    - governance-controlled paths
    - the non-authoritative artifact tree
    - packet-forbidden paths
- This surface does not add path isolation guarantees beyond what the current sanctioned store path already enforces.
- This surface does not solve the already-observed last-write-wins overwrite behavior when the same authoritative destination path is reused across sequential runs.

## 7. Fail-Closed Rules
- Missing bundle:
  - if `bundle_id` does not resolve, the decision must fail with no write attempt
- Non-pending-review bundle state:
  - if the bundle `acceptance_state` is anything other than `pending_review`, the decision must fail with no write attempt
- Missing approval input:
  - if `approved_by` is blank, fail
  - if `decision_note` is provided but blank, fail
  - if `decision` is not explicit `approved`, fail
- Invalid action:
  - if `action` is not exactly `apply` or `promote`, fail
- Missing destination mapping:
  - if `destination_mappings` is absent, not a list, or empty, fail
  - if a mapping is malformed, fail
  - if mapping coverage is incomplete for the bundle `produced_artifact_ids`, fail
- Missing or inconsistent persisted context:
  - if the bundle packet is missing, fail
  - if packet, workflow, or stage context is inconsistent with the bundle, fail
- Invalid source artifact reference:
  - if a mapped `source_artifact_id` is missing, fail
  - if a mapped `source_artifact_id` is not one of the bundle `produced_artifact_ids`, fail
  - if the source artifact has no persisted `artifact_path`, fail
  - if the source artifact path is not covered by packet `allowed_write_paths`, fail
- Invalid destination path:
  - if the destination is out of the packet `authoritative_workspace_root`, fail
  - if the destination targets governance-controlled paths, fail
  - if the destination stays inside the non-authoritative artifact tree, fail
  - if the destination targets packet-forbidden paths, fail
  - if the destination duplicates another destination in the same decision request, fail
  - if the destination reuses the source artifact path, fail
- Invalid inspection workspace:
  - if an optional `workspace_root` resolves into the known duplicate root or outside the authoritative root, fail
  - if an optional `workspace_root` lacks `sessions/studio.db`, fail
- No partial convenience fallback:
  - the surface must not silently skip invalid mappings
  - the surface must not silently downgrade `promote` to `apply`
  - the surface must not fabricate destination mappings
  - the surface must fail before any authoritative destination write if preconditions are not satisfied

## 8. Exact Out-Of-Scope Boundaries
- Out of scope for this surface:
  - bundle rejection as a first-class bundle decision path
  - packet issuance
  - bundle ingestion
  - artifact generation
  - later-stage workflow execution beyond `architect`
  - readiness detection
  - stage-completion inference
  - concurrent contention handling
  - multi-bundle batch decisions
  - automatic destination-path selection
  - destination conflict remediation
  - workspace cleanup or isolation redesign
  - operator workspace UI expansion
  - real multi-agent proof
  - autonomy, overnight, semi-autonomous, or UAT readiness claims
- Existing `scripts/operator_api.py reject` behavior is out of scope here because it targets approval IDs rather than persisted execution bundles.

## 9. Relationship To Current Store And Operator CLI Reality
- The store is already the authoritative mutation surface:
  - `sessions/store.py::SessionStore.execute_apply_promotion_decision(...)`
- The current operator-facing read-only inspection surface is:
  - `scripts/operator_api.py control-kernel-details`
- The missing piece is a narrow operator-facing wrapper that bridges those two realities without widening authority:
  - inspect a persisted bundle
  - submit explicit operator approval inputs
  - pass those inputs into the already-sanctioned store mutation path
  - return inspectable persisted results
- This design therefore describes a thin operator wrapper over existing sanctioned persisted state, not a new control plane and not a workflow redesign.
- `workspace_root.py` remains the path-safety boundary for any optional workspace-root targeting.
- `state_machine.py` remains unchanged by this design and continues to define the currently proven workflow stop at `architect`.

## 10. Evidence And Audit Requirements
- The operator-facing surface must preserve the existing evidence model rather than replace it.
- Required audit expectations:
  - bundle inspection must remain available before the decision
  - the explicit decision input must be reconstructable from persisted receipts
  - resulting authoritative destination writes must remain tied to bundle provenance
  - post-decision inspection must show the resulting `acceptance_state`
- The surface must rely on the store receipts already produced by the sanctioned mutation path, including:
  - `apply_promotion_decision`
  - `authoritative_destination_write`
- The surface must not treat CLI narration as proof.
- External reviewable truth remains:
  - committed artifacts
  - verification output
  - pushed GitHub branch state
- `AIO-041` and `AIO-042` should preserve the pattern used in `M6`:
  - factual artifact
  - narrow verification
  - explicit non-claims

## 11. Non-Goals
- Do not redesign `apply` or `promote` semantics.
- Do not change `sessions/store.py` behavior in this design task.
- Do not change `scripts/operator_api.py` behavior in this design task.
- Do not add concurrency claims or locking claims.
- Do not imply later-stage workflow proof.
- Do not imply a real PM / Architect / Dev / QA / Art operating loop.
- Do not imply readiness improvement beyond the accepted current posture.

## 12. Next Implementation Implications For AIO-041
- `AIO-041` should add one narrow operator CLI command over the already-sanctioned store path.
- That wrapper should:
  - target one `bundle_id` at a time
  - require explicit `action`
  - require explicit `approved_by`
  - require explicit `destination_mappings`
  - optionally accept `decision_note`
  - optionally accept `workspace_root` for sanctioned non-default inspection/decision contexts
- The wrapper should internally call the existing store method with:
  - `approved_decision = {"decision": "approved", "action": <action>, "approved_by": <approved_by>, "decision_note": <optional>}`
  - explicit operator-supplied `destination_mappings`
- The wrapper should reuse the existing inspection path for preflight and post-decision visibility rather than inventing a second truth surface.
- The wrapper should remain bundle-scoped, sequential, and fail-closed.
- The wrapper should not:
  - issue packets
  - create bundles
  - infer destination paths
  - continue workflow beyond the already-proven boundary
  - upgrade readiness claims
