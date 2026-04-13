# AIOffice Control Kernel Model

Model status:
- drafted under AIO-019 for operator review
- defines the conceptual control-kernel entity model for AIOffice
- describes first-class control-plane entities without claiming a persistence engine or runtime implementation already exists

## 1. Purpose And Scope

This document defines the conceptual entity model the future AIOffice control kernel will persist, inspect, and reason over. Its purpose is to give AIOffice one coherent control-plane vocabulary before implementation begins.

The model is conceptual only. It does not claim that a database schema, runtime engine, or read-model surface already exists.

## 2. Entity Overview

The core control-kernel entities are:
- `workflow_run`
- `stage_run`
- `artifact`
- `handoff`
- `blocker`
- `question_or_assumption`
- `orchestration_trace`

All of them are first-class control-kernel concepts. None of them are mere prose conveniences.

## 3. workflow_run

### Concept / Purpose
`workflow_run` is the governing container for one request path through AIOffice workflow.

### Minimum Conceptual Fields
- `workflow_run_id`
- `request_ref`
- `objective`
- `authoritative_workspace_root`
- `canonical_stage_path`
- `current_stage_ref_or_stop_point`
- `review_state`
- `stage_run_refs`
- `artifact_refs`

### Why It Exists
`workflow_run` exists so one governed request has one authoritative control-plane container rather than being spread across unrelated summaries.

### Relationship To Accepted Workflow And Artifact Model
- contains ordered `stage_run` attempts
- references the artifacts and support records produced during the run
- anchors the stop condition for bounded trials such as the architect-stop golden task

## 4. stage_run

### Concept / Purpose
`stage_run` is one stage-specific attempt within a `workflow_run`.

### Minimum Conceptual Fields
- `stage_run_id`
- `workflow_run_id`
- `stage_name`
- `attempt_number`
- `entry_basis_refs`
- `output_refs`
- `handoff_refs`
- `stage_state`
- `blocker_or_question_refs`

### Why It Exists
`stage_run` exists so stage progression is evidence-bearing and reviewable rather than implied by role narration.

### Relationship To Accepted Workflow And Artifact Model
- belongs to exactly one `workflow_run`
- corresponds to one canonical stage attempt
- links upstream basis, outputs, and transfer state

## 5. artifact

### Concept / Purpose
`artifact` is the first-class representation of a durable output that may satisfy a task, stage, or governance requirement.

### Minimum Conceptual Fields
- `artifact_id`
- `artifact_type`
- `producing_ref`
- `canonical_path_or_state_ref`
- `proof_role`
- `provenance_ref`
- `review_state`

### Why It Exists
`artifact` exists because durable outputs are the proof containers for AIOffice workflow integrity.

### Relationship To Accepted Workflow And Artifact Model
- may be produced by a `stage_run`, governance task, or bounded execution packet
- may be referenced by handoffs, bundles, and review decisions
- may exist before it is accepted as authoritative

## 6. handoff

### Concept / Purpose
`handoff` is the transfer-state record that summarizes what downstream work should inherit from upstream proof.

### Minimum Conceptual Fields
- `handoff_id`
- `from_ref`
- `to_ref_or_stop_point`
- `upstream_artifact_refs`
- `summary`
- `open_items`
- `status`

### Why It Exists
`handoff` exists so stage progression preserves transfer context explicitly.

### Relationship To Accepted Workflow And Artifact Model
- references upstream artifacts
- supports stage progression but does not replace artifact proof
- may point to a next stage or an explicit bounded stop point

## 7. blocker

### Concept / Purpose
`blocker` is the first-class record that work cannot proceed safely or truthfully.

### Minimum Conceptual Fields
- `blocker_id`
- `scope_ref`
- `blocking_condition`
- `required_resolution`
- `owner_or_escalation_target`
- `status`

### Why It Exists
`blocker` exists so stop conditions remain visible and cannot be silently collapsed into optimistic narration.

### Relationship To Accepted Workflow And Artifact Model
- may attach to a `workflow_run`, `stage_run`, packet, or bundle
- may prevent stage start, stage completion, or apply/promotion decisions

## 8. question_or_assumption

### Concept / Purpose
`question_or_assumption` is the first-class record of unresolved uncertainty or explicitly declared provisional basis.

### Minimum Conceptual Fields
- `question_or_assumption_id`
- `kind`
- `scope_ref`
- `statement`
- `why_it_matters_or_impact`
- `open_implications`
- `status`

### Why It Exists
This entity exists so uncertainty is preserved durably instead of disappearing into confident planning prose.

### Relationship To Accepted Workflow And Artifact Model
- supports PM branching discipline
- may affect stage readiness, gate outcomes, and apply/promotion decisions
- may be surfaced in bundles, handoffs, and review records

## 9. orchestration_trace

### Concept / Purpose
`orchestration_trace` is the first-class trace record of workflow-relevant actions, decisions, and observed state changes.

### Minimum Conceptual Fields
- `orchestration_trace_id`
- `workflow_run_ref`
- `event_type`
- `source_ref`
- `related_entity_refs`
- `observed_effect`
- `provenance_receipts`

### Why It Exists
`orchestration_trace` exists so the control plane can later explain how a workflow moved, not just what the current state is.

### Relationship To Accepted Workflow And Artifact Model
- may reference packets, bundles, stage runs, artifacts, handoffs, blockers, and decisions
- supports later inspection and audit surfaces
- does not replace the authoritative current-state backlog while that remains the active source of truth

## 10. Core Relationships Between Entities

Core relationship rules:
- one `workflow_run` contains one or more ordered `stage_run` attempts
- one `stage_run` may produce zero or more `artifact` references, but cannot be considered satisfied without the required ones
- one `handoff` references upstream `artifact` outputs and connects one stage context to another or to a stop point
- one `blocker` may attach to a `workflow_run`, `stage_run`, packet, or bundle context
- one `question_or_assumption` may attach to planning, execution, or review contexts
- one `orchestration_trace` may reference any of the other entities as related evidence

## 11. Responsibility Boundaries

Responsibility rules:
- the operator directs and reviews, but does not need to hand-author every entity
- the control kernel owns authoritative interpretation of entity state and relationships
- reasoning systems may propose, summarize, and help draft entity content, but do not self-authorize entity acceptance
- Codex may produce bounded artifacts and bundle content, but does not define authoritative workflow truth

## 12. Inspection / Read-Model Implications

Future inspection surfaces should derive from this model rather than invent their own competing truth vocabulary.

Read-model implications:
- operator inspection should be able to answer what workflow is active, what stage is active, what proof exists, and what remains blocked
- the read model should distinguish current-state truth from event-history or trace truth
- projections must remain derived and non-authoritative unless future governance explicitly changes that rule

## 13. Minimal Examples

### Valid Conceptual Example

- one `workflow_run` represents the golden-task trial request
- it contains four `stage_run` attempts: `intake`, `pm`, `context_audit`, `architect`
- each stage run references its required artifact
- the `architect` stage run references a stop-point handoff

Why valid:
- one request path has one governing container
- stage-specific attempts and proof are distinct

### Invalid Conceptual Example

- a summary claims `architect completed`
- no `stage_run` concept is preserved
- no artifact or handoff relationship is visible

Why invalid:
- workflow state is being narrated instead of modeled
- the control plane would have no durable basis for inspection

## 14. Deferred Implementation Notes

The following are intentionally not implemented yet:
- no persistence engine
- no runtime implementation
- no read-model database
- no automated trace store

This model still governs now because later code, persistence, and tests must derive their entity structure from it.
