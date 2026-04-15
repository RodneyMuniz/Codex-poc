# AIOffice Stage Governance

Status:
- accepted stage-governance baseline under completed `AIO-009`
- governing workflow-stage contract for AIOffice
- preserves the canonical stage set while distinguishing the narrower currently proven implementation scope

## 1. Purpose And Scope

Stage governance exists to protect orchestration integrity. AIOffice does not treat workflow as a narration problem. It treats workflow as a control problem with explicit boundaries, required artifacts, and reviewable handoffs.

Stage names are not evidence. A stage is not complete because a model says it is complete, because a role label was used, or because a summary sounds plausible. A stage may be treated as satisfied only when the required artifact and handoff expectations for that stage have been met through a controlled acceptance path.

Final output without required stage artifacts and handoffs is workflow failure. Ambiguous state is blocked state by default. When evidence is missing, conflicting, or unclear, the system must fail closed rather than infer a convenient interpretation.

## 2. Canonical Stage Order

The canonical ordered workflow stages for AIOffice are:

1. `intake`
2. `pm`
3. `context_audit`
4. `architect`
5. `design`
6. `build_or_write`
7. `qa`
8. `publish`

Rules:
- this order is canonical for AIOffice workflow interpretation
- later stages do not self-authorize
- a downstream stage may not treat itself as valid merely because upstream work was implied in chat
- stage skipping is a workflow failure unless a future policy explicitly defines a valid exception
- a later stage may remain out of scope for a given trial, but it may not be claimed as satisfied unless its own stage expectations are met

Current proof boundary:
- the currently proven implementation scope is narrower than the full conceptual stage set
- current live workflow proof is limited to the first slice through `architect`
- `design`, `build_or_write`, `qa`, and `publish` remain canonical stages, but they are not yet proven as live workflow stages in current evidence

## 3. Stage Purpose Summary

| Stage | Stage purpose | Primary question answered | Expected output type | Why the stage exists in the control model |
| --- | --- | --- | --- | --- |
| `intake` | Capture the requested work, visible scope, and governing constraints. | What work is being requested, under what boundaries, and with what declared outcome? | Intake request artifact | Prevents hidden scope and undocumented operator intent. |
| `pm` | Normalize the request into an explicit work plan, assumptions, and questions. | What is the intended work shape, and what still needs clarification or declared assumptions? | PM plan, assumption register, or clarification questions artifact | Prevents silent assumption collapse before downstream execution. |
| `context_audit` | Audit relevant code, files, systems, and constraints before solution design. | What facts in the current environment materially constrain the work? | Context audit report | Prevents design and execution from running on narrative instead of environment truth. |
| `architect` | Define the solution approach, structure, risks, and decision boundaries. | What solution should be built or changed, and why is that structure acceptable? | Architecture decision artifact | Prevents build activity from inventing architecture on the fly. |
| `design` | Translate architecture into implementation-ready design or content plans. | How should the approved architecture be shaped into executable work packets? | Design plan artifact | Separates structural decision-making from implementation detail generation. |
| `build_or_write` | Produce the bounded implementation or content artifact. | What was actually produced within the approved design and boundary rules? | Build/write artifact | Creates a distinct execution phase with reviewable outputs instead of implied completion. |
| `qa` | Verify the produced output against acceptance and observable evidence. | Did the produced artifact satisfy the required conditions, and what evidence supports that claim? | QA report | Prevents completion claims from outranking verification evidence. |
| `publish` | Package or apply accepted output through approved release paths. | What verified output is being promoted, and through what controlled path? | Publish package | Prevents unverified or ambiguous outputs from being treated as final delivery. |

## 4. Stage Entry Expectations

These are governance-level prerequisites. They define what must exist conceptually before a stage may begin. They do not claim that the full enforcement engine already exists.

### `intake`
- an operator-directed work request exists
- the work is identifiable enough to be recorded against a governed backlog item or equivalent bounded instruction

### `pm`
- `intake` has produced a request artifact or equivalent intake record
- the requested work is bounded enough for planning, clarification, or assumption handling

### `context_audit`
- `pm` has produced a planning artifact, clarification artifact, assumption artifact, or equivalent PM output
- there is enough scope definition to identify what context must be audited

### `architect`
- `pm` output exists
- `context_audit` output exists
- the work is ready for structural decision-making rather than further intake narration

### `design`
- `architect` output exists
- the approved architecture is specific enough to guide implementation planning

### `build_or_write`
- `architect` output exists
- any required `design` output exists when design is part of the chosen path
- the intended write/build scope is bounded enough to execute without inventing upstream truth

### `qa`
- `build_or_write` output exists
- the produced output is reviewable against explicit acceptance or verification expectations

### `publish`
- `qa` output exists
- the output proposed for promotion has a reviewable verification record

Dependency summary:
- `pm` follows `intake`
- `context_audit` follows `pm`
- `architect` follows `pm` and `context_audit`
- `design` and `build_or_write` follow `architect`
- `qa` follows `build_or_write`
- `publish` follows `qa`

Entry rule:
- if prerequisite truth is ambiguous, conflicting, or unsupported, the next stage does not start

## 5. Stage Exit Expectations

A stage is complete only when its conceptual proof exists in durable form. Exit expectations are defined in artifact and handoff terms, not in persona-performance terms.

### `intake`
- the request is captured in a durable artifact
- scope boundaries and visible constraints are recorded clearly enough for PM follow-up
- the next stage does not need to infer the original ask from chat alone

### `pm`
- a planning output exists in durable form
- clarification questions or explicit assumptions exist where ambiguity remains
- downstream stages can see what was decided, what remains open, and what is provisional

### `context_audit`
- a context audit artifact records the relevant environment findings
- material constraints, evidence sources, and observed gaps are visible
- downstream design work does not need to trust unsupported environment claims

### `architect`
- a durable architecture decision artifact exists
- structural approach, major tradeoffs, and declared constraints are explicit
- downstream implementation work can reference a stable design basis instead of inferring one

### `design`
- a durable design artifact exists for the approved architecture
- the implementation shape, packetization, or content plan is explicit enough for bounded execution
- the next stage does not need to invent missing design decisions silently

### `build_or_write`
- a durable implementation or content artifact exists
- the produced output is bounded to the approved scope and path
- the next stage can inspect what was produced without relying on execution narration

### `qa`
- a durable QA artifact exists
- verification results, failures, or limits are explicit
- publish decisions can reference observed proof rather than completion claims

### `publish`
- a durable publish package or equivalent promotion artifact exists
- what is being promoted, from which verified source, and by which path is explicit
- final delivery is tied to preserved provenance and verification context

## 6. Ownership Model

Ownership is defined at the contract level. It is not proof that separate human or model entities performed the work.

### Operator
- gives direction, scope, priorities, and acceptance intent
- may approve, reject, defer, or redirect work
- does not replace required artifacts with conversational preference alone

### Control Kernel
- owns workflow state, stage sufficiency rules, acceptance logic, and controlled mutation paths
- determines whether a stage may be treated as satisfied
- must fail closed when required evidence is missing

### Reasoning / Orchestration Model
- may propose plans, identify gaps, question assumptions, and review artifacts
- may assist with stage outputs when explicitly tasked
- does not become authoritative merely by using stage labels or persuasive narration

### Codex Executor
- may produce bounded stage artifacts, diffs, and reports within assigned scope
- does not determine stage sufficiency
- does not decide acceptance, promotion, or canonical workflow truth

### Stage Contract Owners
- are responsible for the contract expectations of a stage
- own the definition of what that stage must prove
- do not prove stage satisfaction merely by title or role label

Rules:
- role labels do not prove separate execution
- Codex may produce bounded stage artifacts
- Codex does not determine stage sufficiency
- only controlled acceptance paths may treat a stage as satisfied
- execution profiles, higher-spend modes, or richer model lanes may not weaken stage governance

## 7. Handoff Expectations

Handoffs are required workflow connectors between stages.

Rules:
- downstream work must reference upstream artifacts
- a handoff summarizes upstream state, open issues, and next-stage expectations
- a handoff does not replace the upstream artifact that proves the stage output
- missing handoff is a governance failure even if some document exists
- a downstream artifact that cannot identify its upstream basis is not trustworthy stage progression

## 8. Artifact Expectations By Stage

Each stage has an expected primary artifact set. These artifacts are the default proof containers for stage output.

| Stage | Expected primary artifact(s) | Proof value |
| --- | --- | --- |
| `intake` | Intake request artifact | Proves what was requested, bounded, and directed. |
| `pm` | PM plan artifact and either assumption register or clarification questions artifact | Proves how the request was normalized and where uncertainty remains. |
| `context_audit` | Context audit report | Proves the relevant environment and constraint findings used downstream. |
| `architect` | Architecture decision artifact | Proves the selected solution structure and major decisions. |
| `design` | Design plan artifact | Proves how architecture was translated into implementation-ready form. |
| `build_or_write` | Build/write artifact | Proves what bounded output was actually produced. |
| `qa` | QA report | Proves verification results, failures, and limits. |
| `publish` | Publish package | Proves what verified output is being promoted and with what provenance. |

These artifact expectations align with AIOffice artifact policy. A future enforcement layer may add stronger validation, but it must not lower these proof requirements.

## 9. Blocked / Escalation Conditions

A stage is blocked when required progress cannot continue without violating governance.

Blocked or escalation conditions include:
- missing prerequisite artifact
- missing prerequisite handoff
- unresolved question
- unresolved blocker
- ambiguous scope
- ambiguous state
- conflicting sources of truth
- failed verification
- insufficient upstream output
- missing acceptance context for the current stage

Rules:
- blocked state is meaningful workflow state, not mere inconvenience
- ambiguous state fails closed by default
- a blocked stage must not self-resolve by assumption collapse
- when evidence conflicts, the system must escalate instead of choosing the most optimistic interpretation
- escalation is required when ambiguity, missing proof, or conflicting evidence prevents trustworthy continuation

## 10. Governance Invariance Across Execution Modes

Governance does not become weaker because a run is more expensive, faster, or using a different execution profile.

Rules:
- execution profiles may change cost, speed, or model selection, but not stage order
- execution profiles may not waive required artifacts, handoffs, approvals, or proof thresholds
- higher-spend modes may not justify skipping blocked-state handling
- convenience is not a valid reason to weaken fail-closed governance

## 11. Forward-Compatible Enforcement Notes

This document defines governance now and identifies what later code should enforce.

Future enforcement targets:
- stage-run persistence
- gate engine
- artifact validation
- handoff enforcement
- inspection surface

Not yet fully proven or implemented:
- later-stage live workflow beyond `architect`
- automated stage gate evaluation across the full canonical stage set
- automated artifact sufficiency checks across all later stages
- automated handoff validation across the whole workflow
- authoritative workflow inspection UI or equivalent control-plane surface beyond the current narrower proof slice
