# AIOffice Workflow Vision

Policy status:
- governing workflow model for AIOffice
- aligned to the constitutional product loop
- distinguishes conceptual end-to-end workflow from the narrower currently proven implementation surface

## 1. Purpose And Scope

AIOffice needs a workflow model because loose task narration is not a trustworthy control surface. A governed request must move through explicit workflow structure with visible stage position, distinct artifacts, bounded execution, and reviewable progression. Without that structure, persuasive summaries can masquerade as execution truth.

Stage labels alone do not prove workflow integrity. A request is not "through PM," "through architect," or "ready to apply" because a model says so. Workflow integrity exists only when stage-specific outputs, approval checkpoints, and progression evidence are present in durable form.

This document defines the conceptual end-to-end workflow while also stating clearly what is currently proven versus what remains planned.

## 2. Canonical Workflow Shape

The intended AIOffice workflow is:

1. `free_form_chat`
2. `readiness_detection`
3. `structured_collaboration`
4. `operator_approval`
5. `bounded_execution`
6. `evidence_return`
7. `review_apply_reject`
8. `durable_state_update`

Interpretation:
- `free_form_chat` is where operator intent first enters the system.
- `readiness_detection` decides whether the request remains conversational, needs clarification, or is ready for governed workflow handling.
- `structured_collaboration` produces durable PM, architecture, and design artifacts rather than role-play summaries.
- `operator_approval` is the review boundary before consequential execution or state change.
- `bounded_execution` is packet-constrained work performed by a subordinate executor.
- `evidence_return` separates produced artifacts and receipts from self-reported completion claims.
- `review_apply_reject` is the sanctioned decision point for accepting, rejecting, or promoting returned work.
- `durable_state_update` is the controlled persistence of accepted truth.

Rules:
- later steps do not self-authorize
- missing evidence or ambiguous state blocks progression
- the full loop is the workflow vision, not a blanket claim of current implementation proof

## 3. Workflow Run Concept

A `workflow_run` is the governance-level container for one governed request moving through the AIOffice workflow.

A `workflow_run` conceptually binds:
- the objective being pursued
- the bounded scope of the request
- the authoritative workspace for the run
- the current stage position
- the artifacts produced by the run
- the approval and review state attached to those artifacts
- the traceable progression from one stage to the next

Rules:
- a `workflow_run` is distinct from a single chat exchange
- a `workflow_run` is distinct from a single executor action
- a `workflow_run` may stop before the full canonical flow is exhausted if the accepted trial scope says so
- a `workflow_run` may not claim progression that cannot be supported by durable artifacts, evidence, approvals, and handoffs

## 4. Stage Run Concept

A `stage_run` is the conceptual unit of one governed attempt of one canonical stage within a `workflow_run`.

Rules:
- one `stage_run` represents one stage-specific attempt within one `workflow_run`
- `stage_run`s are ordered within the enclosing `workflow_run`
- `stage_run`s are stage-specific and evidence-bearing
- a `stage_run` is not satisfied by role labeling alone
- a `stage_run` is not satisfied by summary text alone
- a later implementation may persist `stage_run` state explicitly, but this document defines the concept whether or not the full end-to-end engine exists yet

A valid `stage_run` conceptually carries:
- the stage identity
- the stage objective
- the artifact or artifacts produced by that stage attempt
- the handoff, approval, or declared stop condition associated with the stage
- the reviewable evidence needed for downstream progression

## 5. Currently Proven Vs Planned

| Area | Current posture | Boundary |
| --- | --- | --- |
| Controlled workflow state | Proven for the implemented control-kernel slice through sanctioned persisted state and read-only inspection. | This is not proof that the full conceptual workflow engine exists end-to-end. |
| First-slice stage progression | Proven for `intake`, `pm`, `context_audit`, and `architect` as the current fail-closed workflow slice. | Current workflow proof stops at `architect`; later stages remain planned unless evidence proves otherwise. |
| Operator invocation | Proven as an operator-facing sanctioned path under current accepted `M5` execution truth. | This does not prove later-stage workflow completion or unattended operation. |
| Apply / promotion control path | Implemented as a sanctioned path under current accepted `M5` execution truth. | Supervised rehearsal evidence for apply/promotion remains outstanding until current `AIO-032` is completed. |
| Design, build, QA, and publish flow | Canonical and planned. | They may be described conceptually, but they must not be claimed as proven live workflow stages without new evidence. |
| Semi-autonomous or unattended operation | Planned for explicit later review only. | Not proven. No claim of unattended readiness is authorized here. |

## 6. First Integrity Slice

The currently proven AIOffice workflow slice is:

1. `intake`
2. `pm`
3. `context_audit`
4. `architect`

Rules:
- this is the first proof slice for orchestration integrity
- the workflow must stop after `architect` for the currently proven slice
- the purpose of the slice is to prove distinct stage outputs and progression discipline, not full end-to-end delivery
- `design`, `build_or_write`, `qa`, and `publish` remain canonical later stages, but they are not part of the currently proven live workflow slice
- later stages beyond `architect` remain planned unless current evidence proves otherwise

## 7. First-Slice Artifact Contract Set

The following artifacts are the contract outputs for the currently proven first slice.

| Contract name | Stage | Purpose | Minimum required contents | Proof value | Downstream requirement |
| --- | --- | --- | --- | --- | --- |
| `intake_request_v1` | `intake` | Capture the governed request and its workspace boundary. | original request; explicit objective; authoritative workspace path; optional duplicate or non-authoritative path note if relevant | Proves what was asked, where it applies, and what workspace authority governs the run. | Required to start `pm`. Required to treat `intake` as complete. |
| `pm_plan_v1` | `pm` | Normalize the request into a planned work shape. | problem framing; scope; out_of_scope; decomposition; intended stage path | Proves that the request was translated into an explicit work plan rather than passed through by narration. | Required to complete `pm`. Required to start `context_audit`. |
| `pm_assumption_register_v1` | `pm` | Record explicit assumptions when work can proceed under declared uncertainty. | explicit assumptions; impact or risk per assumption; open implications | Proves that uncertainty was surfaced deliberately rather than collapsed silently. | Required for PM completion when proceeding by assumptions. Can support `context_audit` and `architect` understanding. |
| `pm_clarification_questions_v1` | `pm` | Record unresolved questions that block safe planning certainty. | unanswered questions; why each matters; what cannot be decided safely without answers | Proves that unresolved uncertainty was identified explicitly instead of buried in a plan. | Required for PM completion when proceeding by questions rather than assumptions. May block downstream progression conceptually until resolved or governed otherwise. |
| `context_audit_report_v1` | `context_audit` | Record the relevant environment and evidence audit. | sources checked; relevant context found; gaps; risks | Proves that downstream architecture work is grounded in inspected context rather than narrated context. | Required to complete `context_audit`. Required to start `architect`. |
| `architecture_decision_v1` | `architect` | Record the selected solution approach for the bounded slice. | chosen approach; rationale; tradeoffs; dependencies; downstream implications | Proves that architecture exists as a durable decision artifact rather than an implied idea. | Required to complete `architect`. In the currently proven slice, also acts as the explicit stop artifact before later stages. |

Interpretation rules:
- the PM stage always requires `pm_plan_v1`
- the PM stage also requires either `pm_assumption_register_v1` or `pm_clarification_questions_v1`
- an empty file, title-only file, or purely narrative summary does not satisfy any artifact contract
- downstream progression must reference the required upstream artifact contracts, not merely mention stage names

## 8. Dependency Logic

The conceptual dependency chain for the currently proven slice is:

- `pm` follows `intake`
- `context_audit` follows `pm`
- `architect` follows `pm` and `context_audit`

Dependency rules:
- `pm` cannot be treated as complete without `pm_plan_v1` and one PM branch artifact
- `context_audit` cannot be treated as complete without `context_audit_report_v1`
- `architect` cannot start safely without the PM outputs and the context audit artifact
- `architect` cannot be treated as satisfied without `architecture_decision_v1`
- downstream stages after `architect` remain canonical but may not be claimed as part of currently proven completion

## 9. Governance Rules For Planned Later Stages

The later canonical stages remain:
- `design`
- `build_or_write`
- `qa`
- `publish`

Rules:
- these stages are part of the AIOffice workflow model
- they remain planned as live workflow proof until current evidence proves them
- they may be referenced as future handoff targets, but they may not be claimed as executed or satisfied without their own artifacts, approvals, and evidence
- higher-spend execution modes, richer models, or convenience shortcuts do not authorize skipping the missing proof boundary

## 10. Deferred Implementation Notes

The following remain intentionally incomplete or unproven in the current baseline:
- no broadly proven readiness-detection engine yet
- no proven later-stage live workflow beyond `architect`
- no proof here of a full end-to-end stage engine across the whole conceptual loop
- no claim here that apply/promotion rehearsal evidence already exists
- no claim here of unattended, overnight, or self-directing operation

This document still governs now because later code, tests, rehearsals, and reviews must derive workflow behavior from these fail-closed expectations.
