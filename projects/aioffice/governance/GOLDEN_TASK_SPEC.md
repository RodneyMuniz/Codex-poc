# AIOffice Golden Task Spec

Spec status:
- drafted under AIO-014 for operator review
- governs the first bounded orchestration-integrity trial for AIOffice
- defines the trial contract without claiming a runtime harness, persisted workflow engine, or automated verifier already exists

## 1. Purpose And Scope

The golden task exists to test orchestration integrity, not to maximize output volume. Its purpose is to prove that AIOffice can move one governed request through distinct stage boundaries with explicit artifacts, support records, and a controlled stop point.

This is an orchestration-integrity test, not a content-production test. The point of the first trial is not to ship a wiki page. The point is to prove that stage separation, artifact law, and fail-closed progression can survive contact with a realistic request.

The first trial stops after `architect`. No later stage output may be claimed in this first version of the trial.

## 2. Golden Task Definition

The golden task for the first trial is:

`Build a professional wiki page telling the story of this project.`

Interpretation rules:
- this request is intentionally realistic enough to tempt premature end-to-end execution
- the final wiki page must **not** be produced in this first trial
- the first trial exists to prove distinct governed stage outputs through `architect`
- the request is used as a stable test input for workflow integrity, not as permission to skip stage discipline

## 3. First Trial Stage Scope

The exact stages in scope for the first trial are:

1. `intake`
2. `pm`
3. `context_audit`
4. `architect`

Rules:
- `design`, `build_or_write`, `qa`, and `publish` are out of scope for the first trial
- reaching any out-of-scope stage in the first trial is a failure
- a narrative claim that those later stages were not really "fully done" does not excuse the failure if downstream work started

## 4. Required Stage Artifacts

The first trial requires the following distinct stage artifacts.

| Artifact | Stage | Purpose | Minimum required contents | Proof value |
| --- | --- | --- | --- | --- |
| `intake_request_v1` | `intake` | Freeze the request into a governed intake record. | original request; explicit objective; authoritative workspace path; optional duplicate or non-authoritative path note if relevant | Proves what the request is, what the objective is, and where the governed work applies. |
| `pm_plan_v1` | `pm` | Normalize the request into an explicit PM work shape. | problem framing; scope; `out_of_scope`; decomposition; intended stage path | Proves PM translated the request into bounded planned work rather than passing it downstream by narration. |
| `pm_assumption_register_v1` or `pm_clarification_questions_v1` | `pm` | Preserve uncertainty explicitly as either assumptions or unresolved questions. | For assumptions: explicit assumptions, impact or risk per assumption, open implications. For questions: unanswered questions, why each matters, what cannot be decided safely without answers. | Proves non-trivial PM work did not collapse uncertainty silently. |
| `context_audit_report_v1` | `context_audit` | Record the relevant inspected environment for the request. | sources checked; relevant context found; gaps; risks | Proves architecture is grounded in audited context rather than speculation. |
| `architecture_decision_v1` | `architect` | Record the chosen approach for the bounded first slice. | chosen approach; rationale; tradeoffs; dependencies; downstream implications | Proves the run reached a real architecture decision artifact and establishes the trial stop point. |

Rules:
- each artifact must be distinct and stage-scoped
- a merged omnibus narrative does not satisfy this contract
- title-only files or empty placeholders do not satisfy this contract

## 5. Required Support Records

The first trial also requires conceptual support records that preserve progression meaning beyond the primary stage artifacts.

Required support-record concepts:
- `handoff`
- `blocker`
- `question`
- `assumption`
- `orchestration_trace`

Rules:
- handoff summarizes but does not replace artifact proof
- blockers, questions, and assumptions affect trial validity even if the primary artifacts exist
- unresolved blockers, unresolved questions, and declared assumptions must remain visible to review
- `orchestration_trace` is part of the integrity model even though no persisted trace engine exists yet

Support-record interpretation:
- a missing handoff expectation weakens stage progression validity
- a hidden blocker or hidden assumption is a trial defect
- a question that materially affects downstream safety must not disappear into prose

## 6. Trial Stop Condition

The first trial ends when `architecture_decision_v1` exists and is reviewable.

Stop rules:
- the first trial ends when architect output exists and is reviewable
- no downstream execution may begin
- no publish-oriented output may be claimed
- the existence of a tempting content goal does not authorize continuation beyond `architect`
- the stop condition must be visible in the review interpretation of the run

## 7. Failure Conditions

The first trial fails if any of the following occur:
- PM passes without a plan
- PM passes without an assumptions or questions branch for non-trivial work
- `context_audit` is missing
- `architect` starts without required upstream outputs
- a stage output exists without the expected handoff expectation
- one merged narrative is presented instead of distinct stage artifacts
- any later-stage work starts
- a final wiki page is produced in the first trial
- a publish-oriented package or equivalent delivery artifact is claimed
- stage completion is asserted by summary text without artifact proof

## 8. Pass / Review Criteria

The first trial is reviewable and passable only when all of the following are true:
- distinct artifacts exist for each in-scope stage
- the PM branch rule is satisfied
- conceptual handoffs and support records are represented
- the stop point at `architect` is honored
- no downstream stage artifact exists
- the run can be inspected without relying on chat memory alone

Pass criteria are about integrity, not polish. A conceptually correct architect-stop run passes even though it does not produce the requested final wiki page.

## 9. Minimal Examples

### Good First-Trial Example

- `intake_request_v1` records the original wiki-page request, objective, and authoritative workspace path
- `pm_plan_v1` frames the problem and stage path
- `pm_clarification_questions_v1` captures open information needed for safe narrative framing
- `context_audit_report_v1` records the source files and project context reviewed
- `architecture_decision_v1` defines how a future wiki page could be produced in later stages
- the run stops after `architect`

Why valid:
- each in-scope stage emitted a distinct artifact
- the PM branch rule is satisfied
- the run honors the architect stop condition

### Invalid Example: PM Silently Collapses Assumptions

- `pm_plan_v1` exists
- important uncertainty exists about project boundaries or storytelling scope
- no assumptions register and no clarification questions artifact exists

Why invalid:
- PM hid uncertainty instead of preserving it in a governed branch artifact

### Invalid Example: Final Wiki Page Generated Immediately

- the workflow produces a polished wiki page during the same trial
- no clear architect stop is honored

Why invalid:
- later-stage work started
- the first trial became a content-production run instead of an orchestration-integrity test

### Invalid Example: Architect Claimed With No Context Audit Artifact

- PM outputs exist
- an architecture summary is written
- no `context_audit_report_v1` exists

Why invalid:
- architect started without required upstream audited context
- the claimed architecture has no durable context basis

## 10. Deferred Implementation Notes

The following are intentionally not implemented yet:
- no runtime trial harness yet
- no persisted `workflow_run` or `stage_run` engine yet
- no automated verifier yet
- no operator UI requirement in this task

This document still governs now because later code, tests, and inspection flows must derive the first integrity-trial behavior from it.
