# AIOffice Handoff Contract

Contract status:
- drafted under AIO-011 for operator review
- governs handoff, blocker, question, and assumption records for AIOffice workflow progression
- defines contract requirements without claiming persistence or runtime enforcement already exists

## 1. Purpose And Scope

This document defines the contract model for handoffs and adjacent transfer-state records in AIOffice. The purpose is to make workflow progression reviewable and fail closed when important uncertainty, transfer state, or blocking conditions are missing.

Handoffs are workflow connectors, not decorative summaries. Blockers, questions, and assumptions are control surfaces that preserve why work may continue, stop, or require escalation.

This document applies to governed AIOffice workflow progression. It does not claim that a persistence engine, runtime validator, or automatic state machine already exists.

## 2. Handoff Concept

A handoff is the stage-to-stage transfer record that summarizes upstream state for a downstream consumer.

Rules:
- a handoff belongs to a specific workflow context
- a handoff references one or more upstream artifacts
- a handoff identifies the sending stage and intended receiving stage, or an explicit stop point
- a handoff summarizes what downstream work should know next
- a handoff does not replace the upstream artifact that proves the stage output

A handoff is valid only when it points to real upstream proof. Summary text alone is not sufficient.

## 3. Blocker Concept

A blocker is a durable record that work cannot proceed safely or truthfully.

Rules:
- a blocker must describe a factual stopping condition
- a blocker must identify what is blocked
- a blocker must explain why continuation would violate governance or accuracy
- a blocker remains active until explicitly resolved, narrowed, or superseded through a controlled path

A blocker is not a vague concern, mood, or preference. It is a declared workflow impediment.

## 4. Question Concept

A question is a durable record of unresolved information required for safe progression.

Rules:
- a question must be specific
- a question must explain why it matters
- a question must identify what cannot be decided safely without an answer
- an unresolved question may block or limit downstream readiness

A question is not satisfied because a model guessed an answer. It is satisfied only when the answer is made explicit through a controlled path or the workflow is intentionally narrowed or converted to a declared assumption.

## 5. Assumption Concept

An assumption is a durable record that work is proceeding under explicitly declared uncertainty.

Rules:
- an assumption must be stated directly
- an assumption must record its impact or risk
- an assumption must preserve open implications
- an assumption does not erase uncertainty; it exposes it

An assumption is allowed only when governance permits provisional continuation. It must not be used to hide a blocker or bypass necessary clarification.

## 6. Minimum Required Fields

The following minimum fields define the contract floor for each record type.

### Handoff Minimum Fields
- `handoff_id`
- `workflow_or_task_ref`
- `from_stage`
- `to_stage_or_stop_point`
- `upstream_artifact_refs`
- `summary`
- `open_items`
- `next_action`
- `status`

### Blocker Minimum Fields
- `blocker_id`
- `workflow_or_task_ref`
- `stage_ref`
- `blocking_condition`
- `why_blocked`
- `required_resolution`
- `owner_or_escalation_target`
- `status`

### Question Minimum Fields
- `question_id`
- `workflow_or_task_ref`
- `stage_ref`
- `question`
- `why_it_matters`
- `what_cannot_be_decided_safely`
- `requested_from`
- `status`

### Assumption Minimum Fields
- `assumption_id`
- `workflow_or_task_ref`
- `stage_ref`
- `assumption_statement`
- `basis_or_reason`
- `impact_or_risk`
- `open_implications`
- `status`

Rules:
- a record missing any minimum field is not a valid governed record
- free-form notes do not become contract records merely because they mention a stage
- a title-only file or one-line summary does not satisfy these contracts

## 7. Relationship To Artifacts And Stage Progression

Handoffs, blockers, questions, and assumptions relate to artifacts and stage progression as follows:

- artifacts prove that a stage emitted its required output
- handoffs summarize what downstream work must inherit from those artifacts
- blockers preserve stop conditions that prevent safe progression
- questions preserve unresolved information that may prevent safe progression
- assumptions preserve declared uncertainty when progression is permitted provisionally

Progression rules:
- downstream work must reference upstream artifacts, not just upstream handoff text
- a stage boundary is not trustworthy if the upstream artifact exists but the transfer state is missing
- a blocker, unresolved question, or invalid assumption record may prevent stage start or completion
- handoff and support records help govern progression, but they do not outrank the artifact proof chain

## 8. Why Handoff Text Alone Is Not Proof

Handoff text alone does not count as proof because a summary can be persuasive while still omitting critical facts, missing upstream evidence, or misrepresenting what actually exists.

Rules:
- a handoff may summarize; it may not substitute
- a handoff without upstream artifact references is insufficient
- a handoff that points to missing or invalid artifacts is insufficient
- a handoff cannot prove stage completion by tone, confidence, or role claim

If artifact proof and handoff text disagree, the artifact chain governs and the discrepancy must be reconciled explicitly.

## 9. Minimal Examples

### Valid Handoff Example

```yaml
handoff_id: handoff_architect_001
workflow_or_task_ref: AIO-014
from_stage: architect
to_stage_or_stop_point: stop_after_architect
upstream_artifact_refs:
  - projects/aioffice/governance/WORKFLOW_VISION.md
  - projects/aioffice/governance/STAGE_GOVERNANCE.md
  - projects/aioffice/artifacts/run-001/architect/ARCHITECTURE_DECISION.md
summary: Architect completed the first-slice decision artifact and the integrity trial stops at architect.
open_items:
  - downstream stages remain intentionally out of scope
next_action: operator review of architecture decision and trial sufficiency
status: open
```

Why valid:
- the handoff identifies source and destination
- upstream artifacts are explicit
- the stop point is visible
- the next action is reviewable

### Invalid Handoff Example

```yaml
from_stage: architect
summary: Architecture is done. QA can proceed.
```

Why invalid:
- no workflow or task reference exists
- no upstream artifact references exist
- destination is unclear
- no open items or next action are recorded
- the summary attempts to advance workflow by narration alone

### Invalid Proof Example

`Architect finished. Trust me.` written in a chat or note file is not a valid handoff.

Why invalid:
- it is not a governed handoff record
- it does not reference artifact proof
- it does not preserve transfer state for downstream work

## 10. Deferred Implementation Notes

The following are intentionally not implemented yet:
- no persisted handoff registry yet
- no persisted blocker registry yet
- no persisted question registry yet
- no persisted assumption registry yet
- no automated handoff validation yet
- no automatic gate enforcement tied to these contracts yet

This document still matters now because later code and tests must derive their transfer-state validation rules from it.
