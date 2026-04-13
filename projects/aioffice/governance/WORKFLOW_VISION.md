# AIOffice Workflow Vision

Policy status:
- drafted under AIO-010 for operator review
- governing workflow-run and first integrity-slice contract draft for AIOffice
- defines conceptual workflow structure without claiming runtime persistence, gate automation, or execution enforcement already exists

## 1. Purpose And Scope

AIOffice needs a workflow-run model because loose task narration is not a trustworthy control surface. A governed request must move through explicit workflow structure with visible stage position, distinct artifacts, and reviewable progression. Without that structure, persuasive summaries can masquerade as execution truth.

Stage labels alone do not prove workflow integrity. A request is not "through PM" or "through architect" because a model says so. Workflow integrity exists only when stage-specific outputs and progression evidence are present in durable form.

The first orchestration-integrity slice is intentionally bounded. It covers `intake`, `pm`, `context_audit`, and `architect`, and it must stop after `architect` for the first trial. `design`, `build_or_write`, `qa`, and `publish` are intentionally out of scope for this document's first-slice trial model.

## 2. Workflow Run Concept

A `workflow_run` is the governance-level container for one governed request moving through the canonical AIOffice stages.

A `workflow_run` conceptually binds:
- the objective being pursued
- the bounded scope of the request
- the authoritative workspace for the run
- the current stage position
- the artifacts produced by the run
- the review state attached to those artifacts
- the traceable progression from one stage to the next

Rules:
- a `workflow_run` is distinct from a single chat exchange
- a `workflow_run` is distinct from a single executor action
- a `workflow_run` is the container for stage runs and workflow evidence
- a `workflow_run` may stop before the full canonical stage order is exhausted if the governing trial scope says so
- a `workflow_run` may not claim progression that cannot be supported by stage artifacts and handoffs

## 3. Stage Run Concept

A `stage_run` is the conceptual unit of one governed attempt of one canonical stage within a `workflow_run`.

Rules:
- one `stage_run` represents one stage-specific attempt within one `workflow_run`
- `stage_run`s are ordered within the enclosing `workflow_run`
- `stage_run`s are stage-specific and evidence-bearing
- a `stage_run` is not satisfied by role labeling alone
- a `stage_run` is not satisfied by summary text alone
- a later implementation may persist `stage_run` state explicitly, but this document defines the concept only

A valid `stage_run` conceptually carries:
- the stage identity
- the stage objective
- the artifact or artifacts produced by that stage attempt
- the handoff or declared stop condition associated with the stage
- the reviewable evidence needed for downstream progression

## 4. First Integrity Slice

The first bounded AIOffice workflow slice is:

1. `intake`
2. `pm`
3. `context_audit`
4. `architect`

Rules:
- this is the first proof slice for orchestration integrity
- the workflow must stop after `architect` for the first integrity trial
- the purpose of the first trial is to prove distinct stage outputs and progression discipline, not full end-to-end delivery
- `design`, `build_or_write`, `qa`, and `publish` remain out of scope for this first trial
- out-of-scope later stages may be named as future stages, but they may not be treated as executed or satisfied in the first trial

## 5. First-Slice Artifact Contract Set

The following artifacts are the contract outputs for the first integrity slice.

| Contract name | Stage | Purpose | Minimum required contents | Proof value | Downstream requirement |
| --- | --- | --- | --- | --- | --- |
| `intake_request_v1` | `intake` | Capture the governed request and its workspace boundary. | original request; explicit objective; authoritative workspace path; optional duplicate or non-authoritative path note if relevant | Proves what was asked, where it applies, and what workspace authority governs the run. | Required to start `pm`. Required to treat `intake` as complete. |
| `pm_plan_v1` | `pm` | Normalize the request into a planned work shape. | problem framing; scope; out_of_scope; decomposition; intended stage path | Proves that the request was translated into an explicit work plan rather than passed through by narration. | Required to complete `pm`. Required to start `context_audit`. |
| `pm_assumption_register_v1` | `pm` | Record explicit assumptions when work can proceed under declared uncertainty. | explicit assumptions; impact or risk per assumption; open implications | Proves that uncertainty was surfaced deliberately rather than collapsed silently. | Required for PM completion when proceeding by assumptions. Can support `context_audit` and `architect` understanding. |
| `pm_clarification_questions_v1` | `pm` | Record unresolved questions that block safe planning certainty. | unanswered questions; why each matters; what cannot be decided safely without answers | Proves that unresolved uncertainty was identified explicitly instead of buried in a plan. | Required for PM completion when proceeding by questions rather than assumptions. May block downstream progression conceptually until resolved or governed otherwise. |
| `context_audit_report_v1` | `context_audit` | Record the relevant environment and evidence audit. | sources checked; relevant context found; gaps; risks | Proves that downstream architecture work is grounded in inspected context rather than narrated context. | Required to complete `context_audit`. Required to start `architect`. |
| `architecture_decision_v1` | `architect` | Record the selected solution approach for the bounded slice. | chosen approach; rationale; tradeoffs; dependencies; downstream implications | Proves that architecture exists as a durable decision artifact rather than an implied idea. | Required to complete `architect`. In the first trial, also acts as the explicit stop artifact before later stages. |

Interpretation rules:
- the PM stage always requires `pm_plan_v1`
- the PM stage also requires either `pm_assumption_register_v1` or `pm_clarification_questions_v1`
- an empty file, title-only file, or purely narrative summary does not satisfy any artifact contract
- downstream progression must reference the required upstream artifact contracts, not merely mention the stage names

## 6. PM Branching Rule In The First Slice

The PM branching rule is reserved explicitly in the workflow vision because non-trivial work cannot pass PM silently.

Rules:
- PM must produce `pm_plan_v1`
- PM must also produce either `pm_assumption_register_v1` or `pm_clarification_questions_v1`
- the branch taken must be visible in durable artifact form
- the exact governance discipline for PM branching will be refined later, but this workflow vision reserves the branch now
- a PM output set that includes only a plan and no assumptions or questions branch is not a complete first-slice PM result

## 7. Workflow Evidence Model

The workflow integrity model includes the following concepts:

| Concept | Conceptual role | Current status in this document |
| --- | --- | --- |
| `workflow_run` | Container for governed request progression across stages | Defined conceptually |
| `stage_run` | One governed attempt of one stage within a workflow run | Defined conceptually |
| `artifact` | Durable output that proves stage work or decision state | Required conceptually |
| `handoff` | Downstream transfer summary that references upstream proof | Required conceptually for trustworthy stage progression |
| `blocker` | Durable record that work cannot proceed safely | Included conceptually, not yet implemented |
| `question_or_assumption` | Durable record of unresolved uncertainty or declared working assumptions | Included conceptually, partially represented in PM branch artifacts |
| `orchestration_trace` | Traceable record of how workflow progression occurred | Included conceptually, not yet implemented as a persisted model |

Rules:
- not all of these concepts are implemented yet
- all of them are part of the AIOffice workflow integrity model
- artifacts carry proof; summaries do not replace proof
- final output without stage artifacts is workflow failure

## 8. First-Slice Dependency Logic

The conceptual dependency chain for the first slice is:

- `pm` follows `intake`
- `context_audit` follows `pm`
- `architect` follows `pm` and `context_audit`

First-slice dependency rules:
- `pm` cannot be treated as complete without `pm_plan_v1` and one PM branch artifact
- `context_audit` cannot be treated as complete without `context_audit_report_v1`
- `architect` cannot start safely without the PM outputs and the context audit artifact
- `architect` cannot be treated as satisfied without `architecture_decision_v1`
- downstream stages after `architect` are intentionally excluded from the first trial and may not be claimed as part of first-slice completion

## 9. Minimal Examples

### Good Example: Workflow Run Stops After Architect With Distinct Artifacts

A governed request enters a `workflow_run` scoped to the authoritative repo.

- `intake` produces `intake_request_v1` with the original request, explicit objective, and authoritative workspace path.
- `pm` produces `pm_plan_v1` and `pm_assumption_register_v1`.
- `context_audit` produces `context_audit_report_v1` based on inspected sources.
- `architect` produces `architecture_decision_v1` referencing the PM and context audit artifacts.
- The run stops after `architect` because the first integrity trial ends there.

This is valid because each stage has distinct durable output and the stop point is explicit.

### Invalid Example: PM Produces A Plan But No Assumptions Or Questions Branch

`pm` produces `pm_plan_v1`, but there is no `pm_assumption_register_v1` and no `pm_clarification_questions_v1`.

This is invalid because the PM branch was hidden. Non-trivial work did not pass through PM in a reviewable way, so PM completion cannot be treated as proven.

### Invalid Example: Architect Starts Without Context Audit Artifact

An architecture document is drafted after intake and PM, but no `context_audit_report_v1` exists.

This is invalid because `architect` depends conceptually on both PM output and context audit output. Without the context audit artifact, architecture is running on unsupported environmental assumptions.

### Invalid Example: Final Narrative Claimed Without Stage Artifacts

A summary says the request was fully analyzed and is ready for implementation, but no first-slice artifacts exist in durable form.

This is invalid because narration is not workflow evidence. Without stage artifacts, there is no proof that the workflow run actually progressed through its required stages.

## 10. Deferred Implementation Notes

The following are intentionally not implemented yet:
- no persisted `workflow_run` model yet
- no persisted `stage_run` model yet
- no stage gate engine yet
- no artifact validation engine yet
- no handoff, blocker, or question persistence yet
- no inspection UI requirement in this task

This document still governs now because it defines the conceptual workflow model that later code, gates, storage, and tests must derive from.
