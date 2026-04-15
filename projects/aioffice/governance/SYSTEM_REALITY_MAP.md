# AIOffice System Reality Map

## 1. Purpose
- Record one authoritative repo-grounded map of what AIOffice actually is after `M6`, not what the constitutional vision hopes it becomes later.
- Distinguish proof-backed control surfaces from partial or fragile behavior and from still-conceptual workflow components.
- Ground the next conservative slice in current file, process, and control-surface reality without widening readiness claims.

## 2. Accepted Posture After M6
- `M1` through `M6` are complete in `execution/KANBAN.md`.
- Current readiness remains:
  - `ready only for narrow supervised bounded operation`
  - not ready for a bounded supervised semi-autonomous cycle
- Current live workflow proof still stops at `architect`.
- `M6` proved:
  - a GitHub-visible remote review surface exists
  - one supervised sanctioned `apply`-path run exists
  - sequential same-workspace and same-store reuse preserved control-plane identity and receipt scoping on the exercised path
  - reusing the same authoritative destination path causes last-write-wins overwrite behavior on the live destination file
- `M6` did not prove:
  - concurrent contention handling
  - later-stage workflow
  - real multi-agent maturity
  - UAT readiness

## 3. Authoritative Document Hierarchy
- Current hierarchy, as supported by `PROJECT.md` and current evidence:
  - `projects/aioffice/execution/KANBAN.md`
    - authoritative milestone and task status truth
  - `projects/aioffice/governance/VISION.md`
    - constitutional product framing
  - `projects/aioffice/governance/DECISION_LOG.md`
    - ratified divergence and explicit planning/governance decisions
  - `projects/aioffice/governance/ACTIVE_STATE.md`
    - current accepted branch/tag/posture anchor for review
  - `projects/aioffice/governance/M6_NARROW_PROOF_REVIEW.md`
    - explicit `M6` proof-boundary review
  - this file, `projects/aioffice/governance/SYSTEM_REALITY_MAP.md`
    - current system-reality map and next conservative slice anchor
- Historical but still useful supporting evidence:
  - `projects/aioffice/governance/M5_READINESS_REVIEW.md`
  - `projects/aioffice/governance/M5_CLOSEOUT_DECISION.md`
  - `projects/aioffice/governance/POST_M5_NEXT_SLICE_PLAN.md`
  - `projects/aioffice/artifacts/M6_APPLY_BRANCH_REHEARSAL.md`
  - `projects/aioffice/artifacts/M6_SHARED_STORE_REHEARSAL.md`

## 4. Active Proof-Backed Control Surfaces
- `workspace_root.py`
  - `ensure_authoritative_workspace_root(...)`
  - `ensure_authoritative_workspace_path(...)`
  - Real control value: exact-root and exact-path enforcement against duplicate-root and out-of-root drift.
- `intake/ingress.py`
  - `preview_operator_request(...)`
  - `dispatch_operator_request(...)`
  - Real control value: the operator request passes through an intent gateway before routing.
- `agents/orchestrator.py`
  - `Orchestrator(...)`
  - `dispatch_request(...)`, `resume_run(...)`, and related execution orchestration path
  - Real control value: current runtime coordinator over sanctioned store, board, and approval plumbing.
- `scripts/operator_api.py`
  - CLI commands:
    - `dispatch`
    - `run-details`
    - `task-details`
    - `control-kernel-details`
  - Real control value: current operator-facing invocation and read-only inspection surface against sanctioned persisted state.
- `sessions/store.py`
  - `create_workflow_run(...)`
  - `create_stage_run(...)`
  - `create_workflow_artifact(...)`
  - `create_handoff(...)`
  - `issue_control_execution_packet(...)`
  - `ingest_execution_bundle(...)`
  - `execute_apply_promotion_decision(...)`
  - Real control value: authoritative persisted control-plane state and controlled mutation path for apply/promotion.
- `state_machine.py`
  - `evaluate_first_slice_transition(...)`
  - `ensure_first_slice_stage_start(...)`
  - `ensure_first_slice_stage_completion(...)`
  - Real control value: fail-closed first-slice gate logic through `architect`.

## 5. Active Implementation Files And Their Current Role
- `sessions/store.py`
  - current authoritative persisted-state and mutation layer for workflow, stage, artifact, packet, bundle, and apply/promotion decisions
  - also a mixed multi-project store with legacy and non-AIO concerns still present
- `scripts/operator_api.py`
  - current operator CLI wrapper around preview, dispatch, approvals, resume, run/task evidence, and control-kernel inspection
  - also contains AIOffice-specific supervised proof harness code
- `state_machine.py`
  - current machine-evaluable first-slice governance enforcement through `architect`
- `intake/ingress.py`
  - current request-routing gateway between free-form operator input and governed task routing
- `workspace_root.py`
  - current authoritative-root and authoritative-path guardrail layer
- `agents/orchestrator.py`
  - current runtime coordinator that binds task packets, store, approvals, and specialist-agent invocation
  - imports PM / Architect / Developer / Design / QA agents, but that import graph is not proof that AIOffice currently has a convincingly real multi-role operating loop

## 6. Proven Capabilities
- AIOffice has a real sanctioned persisted control-kernel state path in `sessions/store.py`.
- AIOffice has a real read-only inspection surface in `scripts/operator_api.py control-kernel-details`.
- AIOffice has real first-slice gate logic through `architect` in `state_machine.py`.
- AIOffice has a real operator CLI routing and runtime entry surface through `scripts/operator_api.py` and `intake/ingress.py`.
- AIOffice has a real sanctioned apply/promotion mutation path in `sessions/store.py`.
- AIOffice has a real external review surface on the pushed GitHub branch plus accepted baseline tag.
- AIOffice has proof of one supervised sanctioned `apply`-path run.
- AIOffice has proof that sequential same-workspace and same-store reuse can preserve workflow, stage, packet, bundle, and receipt identity separation on the exercised path.

## 7. Partial / Fragile Capabilities
- The apply/promotion decision path is implemented in the store, but the current proof for `apply` still depends on direct store-path use rather than a generic operator-facing decision command.
- The operator CLI exposes read-only control-kernel inspection, but not a general bundle-level apply/promotion decision wrapper.
- Sequential same-workspace reuse preserved persisted control-plane identity, but shared authoritative destination reuse is last-write-wins on the filesystem.
- `sessions/store.py` is functionally real but structurally mixed:
  - it still carries non-AIO defaults such as `PROJECT_NAME = "tactics-game"`
  - it is a large shared file with both AIO and donor-system responsibilities
- `agents/orchestrator.py` is a real runtime coordinator, but the repo does not currently prove that its imported PM / Architect / Developer / Design / QA roles operate as a convincingly real separated AIOffice loop.
- AIOffice backlog truth still lives in markdown `KANBAN.md`; canonical task import remains deferred because the current schema does not preserve durable `dependencies` safely.

## 8. Conceptual / Not-Yet-Real Components
- Later-stage live workflow for:
  - `design`
  - `build_or_write`
  - `qa`
  - `publish`
- True concurrent same-workspace or shared-store contention handling.
- A generic operator-facing apply/promotion decision surface over pending bundles.
- A convincingly real PM / Architect / Dev / QA / Art loop with distinct proven execution surfaces.
- A distinct Art runtime or Art pipeline proof surface for AIOffice was not found in the inspected AIOffice control path.
- A broadly proven readiness-detection engine beyond the current narrow request gateway path.
- Any operator workspace alpha beyond the current inspection-oriented and CLI-oriented surfaces.

## 9. Manual Operator Glue Points
- Audit and review still require manual cross-checking between governance docs, artifact reports, and `KANBAN.md`.
- `AIO-036` and `AIO-037` required direct store-path execution rather than a generic operator-facing apply/promotion command.
- Destination mappings for apply/promotion decisions still require explicit manual authoring and review.
- Git commit and push remain manual steps required before work becomes externally reviewable truth.
- The operator still has to interpret stale document wording manually because not every historical or current-state file has been reconciled to post-`M6` truth.

## 10. Known Document Conflicts Or Stale Status Wording
- `projects/aioffice/governance/PROJECT.md`
  - still says `M5` is partially complete and lists `AIO-032` through `AIO-034` as remaining
  - this conflicts with the authoritative `KANBAN.md` state through `M6`
- `projects/aioffice/execution/PROJECT_BRAIN.md`
  - still says the next planned slice is proof of `AIO-036` and `AIO-037`
  - this is stale after `M6` completion
- `projects/aioffice/governance/WORKFLOW_VISION.md`
  - still says supervised apply/promotion rehearsal evidence remains outstanding until `AIO-032`
  - this is stale relative to recorded `M5` and `M6` evidence
- `projects/aioffice/execution/KANBAN.md`
  - still has bootstrap/header wording such as `AIOffice Kanban Bootstrap` and `manual founding backlog seed`
  - its milestone and task status body is current, but those header phrases are stale

## 11. Current System/File/Process/Control Map
- Operator request path:
  - operator input
  - `scripts/operator_api.py` `preview` or `dispatch`
  - `intake/ingress.py` request classification and routing decision
  - `agents/orchestrator.py` runtime coordination
  - `sessions/store.py` persisted run/task/workflow state
- First-slice workflow proof path:
  - `sessions/store.py` workflow and stage persistence
  - `state_machine.py` first-slice start/completion checks
  - durable first-slice artifacts and handoffs
  - stop at `architect`
- Inspection path:
  - operator
  - `scripts/operator_api.py control-kernel-details`
  - `sessions/store.py` list/get helpers
  - persisted workflow/stage/packet/bundle evidence returned read-only
- Current apply/promotion path:
  - pending-review bundle already persisted in `sessions/store.py`
  - direct call to `SessionStore.execute_apply_promotion_decision(...)`
  - authoritative destination write
  - receipts preserved in persisted bundle state
  - no generic operator-facing CLI apply/promotion command found in the inspected surface
- Review surface path:
  - local bounded work
  - explicit staging / commit / push
  - pushed branch state and committed artifacts on GitHub become reviewable truth

## 12. Recommended Next Conservative Slice
- Recommended next slice: `M7 - Post-M6 Operator Decision Surface Hardening`
- Reason:
  - the highest-signal remaining current-boundary gap is not later-stage workflow; it is the missing operator-facing decision surface over a mutation path that already exists only in store code
  - this directly targets a real manual glue point without pretending the broader multi-role loop is already real
- Seed only this narrow slice:
  - `AIO-040`
    - define the narrow operator-facing bundle decision surface and its fail-closed rules
  - `AIO-041`
    - implement a narrow operator CLI wrapper over the sanctioned bundle decision path
  - `AIO-042`
    - rehearse the operator-facing decision surface under supervision and record evidence
- Keep explicitly out of scope for that slice:
  - later-stage workflow expansion
  - concurrency claims
  - real multi-agent maturity claims
  - readiness upgrades

## 13. Explicit Non-Claims
- This map does not claim later-stage workflow proof.
- This map does not claim concurrent contention safety.
- This map does not claim a real PM / Architect / Dev / QA / Art operating loop.
- This map does not claim a ready operator workspace alpha beyond current inspection-oriented surfaces.
- This map does not claim unattended, overnight, semi-autonomous, or UAT readiness.
