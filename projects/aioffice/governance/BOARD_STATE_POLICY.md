# AIOffice Board State Policy

Policy status:
- drafted under AIO-008 for operator review
- governing backlog truth and projection draft for AIOffice
- intended to support later enforcement, not replace it

## 1. Purpose And Scope
Backlog truth is a control issue, not a convenience issue. The component or artifact that is allowed to define task state, task existence, and task metadata determines what work is real inside AIOffice.

Split backlog authority is a workflow risk. If markdown, app projections, SQL assumptions, and executor summaries can all appear to define the backlog at the same time, the system loses clear state authority and invites silent divergence.

Summaries and views are not proof unless they are tied back to the authoritative source. A view may help an operator inspect state, but it does not become state truth simply because it is easier to read.

This policy defines:
- the current authoritative AIO backlog truth model
- the allowed role of projections and summaries
- interim allowed mutation paths
- reconciliation rules when surfaces disagree
- the conditions required before backlog truth may move to a sanctioned canonical-state model

## 2. Current Temporary Truth Model
The current AIOffice reality is explicit and temporary:
- `projects/aioffice/execution/KANBAN.md` is the current AIO backlog source of truth.
- app surfaces for AIO are projections only.
- executor summaries are claims, not authoritative state.
- no sanctioned canonical AIO task import path exists yet.
- this is an interim model pending a safe canonical-state migration path.

Interim rule:
- until the migration conditions in this document are satisfied, backlog truth remains in the authoritative backlog artifact, not in app views, store assumptions, or conversational summaries.

## 3. Backlog Truth Hierarchy
Backlog state must follow one explicit precedence order. Conflict resolution depends on whether AIOffice is still in the interim artifact-truth phase or has completed an approved canonical-state migration.

### Interim hierarchy
1. Authoritative backlog artifact
   Current authority is `projects/aioffice/execution/KANBAN.md`.
2. Sanctioned canonical state, if and when it safely exists for AIO
   This does not currently exist for AIO backlog truth and therefore has no authority yet.
3. Derived projections and views
   App boards, operator views, and reporting views are derived only.
4. Executor summaries and conversational narration
   These are the lowest-precedence surfaces and count only as claims.

Conflict rule in the interim phase:
- if any other surface disagrees with `KANBAN.md`, `KANBAN.md` wins
- the disagreement must be reconciled explicitly

### Current-state ledger truth versus event-history truth
In the current AIO model, `projects/aioffice/execution/KANBAN.md` is authoritative current-state ledger truth. It records the present task and milestone snapshot that the project treats as authoritative.

A sanctioned event-history truth surface does not yet exist for AIO. That means AIOffice does not currently preserve every conceptual lifecycle transition as a first-class authoritative history record.

Interpretation rules:
- current-state ledger truth answers `what is the authoritative state now`
- event-history truth would answer `what sequence of governed transitions occurred`
- projections remain derived from the authoritative source and do not become peer truth
- executor summaries remain claims and may provide provenance context, but they do not become authoritative state

### Post-migration hierarchy
1. Sanctioned canonical state
   After approved migration, this becomes the authoritative backlog source.
2. Authoritative backlog artifact, if retained as a governed derived artifact
   If `KANBAN.md` remains, it must become a projection or archival artifact, not a peer truth source.
3. Derived projections and views
4. Executor summaries and conversational narration

Conflict rule after migration:
- the sanctioned canonical state wins
- no legacy markdown backlog may continue as a competing truth source

## 4. Projection Policy
The following surfaces are derived projections. They may assist inspection, but they do not define authoritative AIO backlog truth in the current phase.

| Surface | Purpose | Authoritative | Mutable | Must derive from |
| --- | --- | --- | --- | --- |
| App board and app views | Show task state, milestones, or task summaries in an operator-friendly form. | No | No authoritative mutation for AIO backlog state. | The active authoritative backlog source. Currently this is `projects/aioffice/execution/KANBAN.md`. |
| Future operator UI | Provide a future operator workspace for inspection and controlled actions. | No until an explicit sanctioned mutation path exists. | Only if a future governed mutation path is added and documented. | The active authoritative backlog source. |
| Codex summaries | Report what the executor believes changed or found. | No | No | The authoritative backlog source and other governed artifacts. |
| Inspection and reporting views | Summarize current state, discrepancies, milestones, or task facts for review. | No | No | The active authoritative backlog source and any governed supporting artifacts. |

Projection rules:
- a projection may summarize, sort, filter, or reformat state
- a projection may not silently add, remove, or reinterpret governed backlog truth
- a projection may not become a hidden peer authority
- if a projection caches stale state, the authoritative source still wins

## 5. Allowed Mutation Paths
During this interim phase, AIO backlog state may change only through explicit, operator-directed updates to the authoritative backlog artifact.

Allowed interim path:
- the authoritative AIO backlog may only be changed through explicitly scoped, operator-directed updates to `projects/aioffice/execution/KANBAN.md`

Interim mutation rules:
- executor-generated state change claims do not count until reflected in the authoritative backlog artifact
- uncontrolled side-channel mutation is forbidden
- app projections must not become hidden peer authorities
- direct assumptions about AIO backlog state in canonical stores do not count as authoritative truth
- a summary that says a task changed does not change the task

### Bundle-state recording in the current-state ledger
Because `KANBAN.md` is a current-state ledger rather than a full event-history log, it may record the final state reached by an operator-authorized bounded bundle without separately rendering every intermediate lifecycle transition.

Bundle-state recording is valid only when:
- the bundle scope explicitly identifies the included tasks
- the task execution order is reviewable
- intra-bundle dependencies are explicit
- the conceptual lifecycle requirements for the recorded end state were actually satisfied
- required artifacts exist before a task is recorded as `in_review`
- no task is recorded as `completed` in the same pass that first executes it
- the change preserves reviewable provenance for why the end-of-bundle snapshot is valid

Valid provenance may include:
- the scoped operator instruction that authorized the bounded bundle
- the governed artifact changes produced by the bundle
- an explicit decision-log entry or equivalent governed record that explains the condensed recording rule

Bundle-state recording does not grant executor authority to self-accept work. It only governs how the authoritative current-state ledger may record the end-of-bundle snapshot.

Interim non-authority examples:
- conversational claims such as `AIO-008 is complete`
- app displays that show a different state than the governed backlog artifact
- internal notes or memory artifacts that mention a task transition without updating the authoritative backlog source

## 6. Verification And Reconciliation Rules
Backlog discrepancies must be handled explicitly.

Rules:
- if a Codex summary and `KANBAN.md` disagree, `KANBAN.md` wins
- if a projection and `KANBAN.md` disagree, `KANBAN.md` wins
- if a bundle summary and `KANBAN.md` disagree, `KANBAN.md` wins
- discrepancies must be reconciled explicitly, not silently absorbed
- review of the authoritative artifact is required before treating task state as factual
- reconciliation must identify which surface drifted and why

Reconciliation procedure in the interim phase:
1. inspect `projects/aioffice/execution/KANBAN.md`
2. compare the disagreeing surface to the authoritative artifact
3. treat the non-authoritative surface as stale, mistaken, or incomplete unless proven otherwise
4. update the non-authoritative surface only through its proper derived path, or update the authoritative artifact only through an explicit governed change
5. record any important governance consequence in the appropriate governed artifact if needed

Bundle summary rule:
- a bundle summary may explain why the authoritative current-state ledger shows an end-of-bundle state
- a bundle summary does not outrank `KANBAN.md`
- if the bundle summary lacks required provenance or conflicts with the authoritative ledger, the discrepancy must be reviewed explicitly rather than silently normalized

## 7. Future Canonical-State Migration Policy
Backlog truth may move from `KANBAN.md` to a sanctioned canonical-state path only after explicit migration approval and only when the following conditions are satisfied:
- all required durable task fields are preservable without loss
- the write path is sanctioned and deterministic
- projection behavior is derived from the canonical source
- migration preserves provenance
- there are not two competing truth sources after migration

Required migration conditions:
- the future canonical path must preserve task fields such as `id`, `title`, `details`, `objective`, `owner_role`, `assigned_role`, milestone reference, `expected_artifact_path`, `acceptance`, `dependencies`, and `status`
- migration must not drop or silently reshape required durable fields
- the canonical write path must be controlled by sanctioned code, not ad hoc mutation
- the source of migrated truth must be identifiable and reviewable
- any surviving markdown backlog must be redefined as a derived artifact or explicitly retired

Migration approval rule:
- AIO backlog truth does not move merely because a store row, app page, or helper exists
- it moves only after governance confirms that the new canonical path preserves durable truth and eliminates split authority

## 8. Anti-Patterns
The following behaviors are forbidden:
- split truth between markdown and app
- executor summaries treated as authoritative
- ad hoc state mutation in canonical stores
- silent reconciliation
- status claims without artifact or source update
- hidden synchronization rules not written in governance
- treating a projection as authoritative because it looks newer or more convenient
- assuming a future canonical state path already exists for AIO when it does not
- allowing bundle-state recording to become a hidden second truth surface
- treating bundle self-report as acceptance authority

## 9. Minimal Examples
### Valid interim state update
- Operator directs a scoped update to `projects/aioffice/execution/KANBAN.md` to add `AIO-008` as `ready`.
- The file is updated deliberately and reviewed as the authoritative backlog artifact.
- Result: valid because the state change occurred in the active authoritative source.

### Valid projection example
- A reporting surface shows `AIO-001` as `ready` by reading the current AIO backlog artifact.
- The report is clearly treated as derived and is not used to mutate task state.
- Result: valid because the projection derives from the authoritative source and does not compete with it.

### Invalid executor-summary-only example
- Codex reports that `AIO-003` moved to `completed`, but `projects/aioffice/execution/KANBAN.md` still shows `backlog`.
- Result: invalid because the summary is only a claim and the authoritative backlog source was not updated.

### Invalid split-truth example
- `projects/aioffice/execution/KANBAN.md` shows `AIO-005` as `backlog` while an app surface shows `ready`, and both are treated as equally real.
- Result: invalid because AIOffice cannot operate with two peer backlog truths.

## 10. Deferred Implementation Notes
The following are intentionally not implemented yet:
- no canonical AIO task import path yet
- no sanctioned AIO board-sync engine yet
- no automated reconciliation engine yet
- no authoritative app-side mutation path yet

This policy still matters now because it defines the truth model later code must enforce.
