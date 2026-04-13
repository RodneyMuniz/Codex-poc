# AIOffice Artifact Map

Map status:
- drafted under AIO-003 for operator review
- authoritative artifact inventory draft for AIOffice
- intended to support later enforcement, not replace it

## 1. Purpose And Scope
Artifacts are central to AIOffice because the system is designed to prove control, stage separation, and bounded execution through durable outputs rather than narration. In AIOffice, an artifact is an evidence container. It exists to preserve a task decision, a stage output, a traceable handoff, or a reviewable proof surface.

Final output without the required stage artifacts is workflow failure. A useful result that bypasses the required evidence chain does not count as a valid workflow success.

Artifacts are not decorative documents. They are durable records that later code, review, and audit can evaluate without depending on chat memory or role claims.

This map defines:
- which artifacts are mandatory
- which are optional
- which are standing project artifacts versus workflow-run artifacts
- which stage owns each artifact
- what each artifact proves
- where each artifact lives
- how artifacts relate to later stage gates and handoffs

## 2. Artifact Classification Model
| Category | Purpose | Durability expectation | Operator-facing | Stage-gating |
| --- | --- | --- | --- | --- |
| Standing governance artifacts | Define durable project doctrine, rules, boundaries, and decision policy. | Persistent for the life of the project and updated by explicit governance changes. | Yes | Yes, because later stages depend on valid governance. |
| Standing execution artifacts | Hold ongoing project-level execution context such as the backlog, handoff state, and working memory. | Persistent while the project remains active. | Yes | Yes for workflow operation; they anchor what work may proceed. |
| Workflow-run artifacts | Capture bounded outputs from a specific run or task execution path. | Persistent for audit and replay unless explicitly superseded. | Usually yes | Yes when a downstream stage depends on that run output. |
| Stage-output artifacts | Represent the required deliverable for a workflow stage. | Persistent as long as the stage result remains authoritative. | Yes | Yes by definition; they are the gate evidence. |
| Audit/trace artifacts | Preserve proof, reconciliation, QA, and other review surfaces that explain what actually happened. | Persistent and reviewable; not optional if they are the only proof surface. | Yes | Yes when trust or acceptance depends on them. |
| Optional supporting artifacts | Add context, references, drafts, or convenience material that helps interpretation but does not prove stage completion alone. | Persistent only if still useful; may be replaced or removed by controlled decision. | Sometimes | No by themselves. |

## 3. Core Standing AIOffice Artifact Set
These are the minimum standing artifacts for AIOffice.

| Artifact name | Path | Purpose | What it proves | owner_role | Update trigger | Required for |
| --- | --- | --- | --- | --- | --- | --- |
| `PROJECT.md` | `projects/aioffice/governance/PROJECT.md` | Founding charter, doctrine, non-goals, authority model, and success definition. | The project has an explicit control-first charter. | Project Orchestrator | Charter change, doctrine correction, or approved project reframing. | Both |
| `VISION.md` | `projects/aioffice/governance/VISION.md` | Durable statement of intended project direction. | The project has a bounded direction statement distinct from execution narration. | Project Orchestrator | Vision clarification or approved scope shift. | Bootstrapping |
| `WORKFLOW_VISION.md` | `projects/aioffice/governance/WORKFLOW_VISION.md` | High-level request-to-artifact workflow direction. | Workflow design intent exists before implementation. | Project Orchestrator | Workflow framing change or approved process redesign. | Bootstrapping |
| `STAGE_GOVERNANCE.md` | `projects/aioffice/governance/STAGE_GOVERNANCE.md` | Defines stage model and transition framing. | Stage separation is declared as governance, not implied by chat behavior. | Project Orchestrator | Stage model update or approved governance refinement. | Both |
| `DECISION_LOG.md` | `projects/aioffice/governance/DECISION_LOG.md` | Durable record of binding project decisions. | Key project decisions are reviewable and not hidden in chat history. | Project Orchestrator | New decision, supersession, or correction. | Both |
| `BOARD_RULES.md` | `projects/aioffice/governance/BOARD_RULES.md` | Strict PM operating model, ready gate, and lifecycle rules. | Work-item validity and board transitions are explicitly governed. | Project Orchestrator | Board rule change or operating-model correction. | Both |
| `ARTIFACT_MAP.md` | `projects/aioffice/governance/ARTIFACT_MAP.md` | Authoritative inventory of artifacts, proof value, and ownership. | Artifact sufficiency is defined as policy rather than guessed per run. | Architect | Artifact inventory change or new stage-output requirement. | Both |
| `DONOR_LEDGER.md` | `projects/aioffice/governance/DONOR_LEDGER.md` | Records keep/adapt/do-not-inherit donor decisions. | Reuse is selective and traceable. | Project Orchestrator | New donor decision or reuse-policy refinement. | Bootstrapping |
| `WORKSPACE_BOUNDARIES.md` | `projects/aioffice/governance/WORKSPACE_BOUNDARIES.md` | Defines authoritative-root and governed path boundaries. | Artifact and state changes are bounded to controlled paths. | Architect | Boundary rule change or path exception decision. | Both |
| `KANBAN.md` | `projects/aioffice/execution/KANBAN.md` | Standing milestone and task ledger. | The current declared project work set exists durably outside narration. | Project Orchestrator | Task addition, correction, sequencing, or explicit state change. | Both |
| `HANDOFF.md` | `projects/aioffice/execution/HANDOFF.md` | Current next-step handoff summary for operator review. | The current handoff frame is visible, but not sufficient as proof alone. | Project Orchestrator | Change in next action, reviewer, or active handoff frame. | Workflow operation |
| `PROJECT_BRAIN.md` | `projects/aioffice/execution/PROJECT_BRAIN.md` | Temporary working memory and open questions. | Open assumptions and unresolved issues are visible instead of implicit. | Project Orchestrator | New known constraint, open question, or contextual correction. | Workflow operation |

Notes:
- `Both` means the artifact is required for project bootstrapping and later workflow operation.
- Standing artifacts are project truth anchors. They are not stage substitutes.

## 4. Forward-Compatible Workflow Artifact Set
These artifacts are not fully implemented yet, but they define the minimum future per-run and per-stage output model.

| Artifact name | Intended stage | Purpose | Minimal proof value | Required to start next stage |
| --- | --- | --- | --- | --- |
| Intake request artifact | intake | Freeze the operator request into a durable intake packet. | Proves the run started from a bounded request rather than free-form narration. | Yes |
| PM plan artifact | planning | Define bounded plan, sequencing, and expected outputs. | Proves downstream work was planned explicitly. | Yes |
| PM assumption register | planning | Record accepted assumptions and unresolved uncertainty. | Proves assumptions were declared instead of silently collapsed. | Yes |
| PM clarification questions artifact | planning | Capture blocking clarification questions when required. | Proves missing information was surfaced instead of improvised away. | Yes when clarification is required |
| Context audit report | context audit | Record input context, allowed evidence, and context exclusions. | Proves downstream work had a bounded context frame. | Yes |
| Architecture decision | architect | Produce the architecture or structure decision for the slice. | Proves the architect stage emitted a durable output. | Yes |
| Design plan artifact | design | Define design or presentation direction when design is part of the workflow. | Proves design intent exists as an artifact, not only chat text. | Yes when design stage is part of the path |
| Build/write artifact | build_or_write | Produce the bounded implementation output. | Proves the executor produced the requested deliverable. | Yes |
| QA report | QA | Evaluate artifact completeness and rule compliance. | Proves acceptance was reviewed against evidence. | Yes |
| Publish package | publish | Bundle the approved output and any release-facing metadata. | Proves the publish stage received reviewed upstream artifacts. | Yes for publish |

Rules:
- A future stage may not start if its required upstream artifact is missing.
- A stage handoff without the required artifact is invalid.
- A stage output is not interchangeable with a later stage report.

## 5. Ownership Model
Artifact ownership is about contract responsibility, not persona theater.

### Operator
- gives direction
- approves or rejects sufficiency through controlled paths
- does not need to author every artifact personally

### Control kernel
- owns workflow state, stage acceptance, and canonical artifact sufficiency decisions
- is the only authority that may accept an artifact as stage-satisfying
- may reject artifacts that are missing, weak, or off-path

### Reasoning/orchestration model
- may propose plans, questions, reviews, or structure
- may help draft bounded artifacts
- does not decide artifact sufficiency

### Codex executor
- may produce bounded artifacts
- may only work within the declared task and path boundary
- does not decide artifact sufficiency
- does not decide stage completion

### Future stage owners as contract owners
- `PM`: owns planning artifacts and assumption surfaces
- `context audit`: owns context audit outputs
- `architect`: owns architecture-stage artifacts
- `design`: owns design-stage artifacts
- `build_or_write`: owns bounded implementation outputs
- `QA`: owns review and validation reports
- `publish`: owns publish package assembly

Contract rule:
- only controlled paths can accept an artifact as stage-satisfying

## 6. Artifact Path Rules
- Every governed task must declare one canonical `expected_artifact_path`.
- The declared artifact path is a write boundary, not only a documentation hint.
- Governed artifacts must live under governed project paths, normally `projects/aioffice/...`.
- Duplicate truth across multiple uncontrolled files is forbidden.
- Path changes require explicit decision and logging.
- A handoff may reference many upstream artifacts, but each task still needs one canonical expected artifact path for bounded execution and review.

## 7. Artifact Sufficiency Rules
An artifact counts as valid only if it is:
- non-empty
- scoped to the task or stage it claims to satisfy
- structured enough for audit
- tied to a task, stage, or decision
- reviewable without relying on chat memory

An artifact does not count if it is:
- chat summary alone
- final output with no prior stage artifact
- role claim with no durable output
- file with placeholder title only
- merged omnibus document that hides stage separation

Sufficiency rule:
- the existence of a file is necessary but not sufficient
- the artifact must also prove the right stage output in the right scope

## 8. Handoff Relationship
`HANDOFF.md` and later handoff records are summaries, not proof sources.

Rules:
- every handoff must reference its upstream artifact or artifacts
- downstream work cannot treat handoff text alone as proof
- handoff summarizes; artifact proves
- if the handoff points to missing or invalid upstream artifacts, the handoff is not sufficient for stage progression

## 9. Minimal Examples
### Good artifact entry
```yaml
artifact_name: Architecture decision
path: projects/aioffice/artifacts/runs/run-001/architect/ARCHITECTURE_DECISION.md
stage: architect
task_id: AIO-021
purpose: define the bounded architecture decision for the current slice
proof_value: proves the architect stage produced a reviewable decision artifact
owner_role: Architect
stage_gating: true
required_for_next_stage: true
```

Why good:
- the path is governed and specific
- the stage is named
- the proof value is explicit
- the artifact is tied to a task and a next-stage gate

### Bad artifact entry
```yaml
artifact_name: Notes
path: desktop_notes.txt
purpose: some thoughts about the system
owner_role: Architect
```

Why bad:
- path is not governed
- no task or stage linkage exists
- proof value is missing
- it cannot support a gate or handoff

### Why handoff without artifact proof is insufficient
- Handoff text: `Architect finished the slice. QA can proceed.`
- Missing upstream artifact: no architecture decision file exists
- Result: downstream QA cannot treat the handoff as proof because the summary does not replace the required stage artifact

## 10. Deferred Implementation Notes
The following are intentionally not implemented yet:
- no workflow engine yet
- no artifact validation engine yet
- no stage-run persistence yet
- no automatic sufficiency checks yet

This map is still useful now because it defines the contract future enforcement must implement.
