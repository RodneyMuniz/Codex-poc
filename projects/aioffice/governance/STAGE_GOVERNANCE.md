# AIOffice Stage Governance

Status:
- drafted under AIO-009 for operator review
- governing workflow-stage contract draft for AIOffice
- defines canonical stage intent and expectations without claiming runtime enforcement already exists

## 1. Purpose And Scope

Stage governance exists to protect orchestration integrity. AIOffice does not treat workflow as a narration problem. It treats workflow as a control problem with explicit boundaries, required artifacts, and reviewable handoffs.

Stage names are not evidence. A stage is not complete because a model says it is complete, because a role label was used, or because a summary sounds plausible. A stage may be treated as satisfied only when the required artifact and handoff expectations for that stage have been met through a controlled acceptance path.

Final output without required stage artifacts and handoffs is workflow failure. This document defines the canonical stage contract that later code, gates, and inspection surfaces must enforce.

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
- This order is canonical for AIOffice workflow interpretation.
- Later stages do not self-authorize.
- A downstream stage may not treat itself as valid merely because upstream work was implied in chat.
- Stage skipping is a workflow failure unless a future policy explicitly defines a valid exception.
- A later stage may remain out of scope for a given trial, but it may not be claimed as satisfied unless its own stage expectations are met.

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

These are governance-level prerequisites. They define what must exist conceptually before a stage may begin. They do not claim that enforcement code already exists.

### `intake`
- An operator-directed work request exists.
- The work is identifiable enough to be recorded against a governed backlog item or equivalent bounded instruction.

### `pm`
- `intake` has produced a request artifact or equivalent intake record.
- The requested work is bounded enough for planning, clarification, or assumption handling.

### `context_audit`
- `pm` has produced a planning artifact, clarification artifact, assumption artifact, or equivalent PM output.
- There is enough scope definition to identify what context must be audited.

### `architect`
- `pm` output exists.
- `context_audit` output exists.
- The work is ready for structural decision-making rather than further intake narration.

### `design`
- `architect` output exists.
- The approved architecture is specific enough to guide implementation planning.

### `build_or_write`
- `architect` output exists.
- Any required `design` output exists when design is part of the chosen path.
- The intended write/build scope is bounded enough to execute without inventing upstream truth.

### `qa`
- `build_or_write` output exists.
- The produced output is reviewable against explicit acceptance or verification expectations.

### `publish`
- `qa` output exists.
- The output proposed for promotion has a reviewable verification record.

Dependency summary:
- `pm` follows `intake`.
- `context_audit` follows `pm`.
- `architect` follows `pm` and `context_audit`.
- `design` and `build_or_write` follow `architect`.
- `qa` follows `build_or_write`.
- `publish` follows `qa`.

## 5. Stage Exit Expectations

A stage is complete only when its conceptual proof exists in durable form. Exit expectations are defined in artifact and handoff terms, not in persona-performance terms.

### `intake`
- The request is captured in a durable artifact.
- Scope boundaries and visible constraints are recorded clearly enough for PM follow-up.
- The next stage does not need to infer the original ask from chat alone.

### `pm`
- A planning output exists in durable form.
- Clarification questions or explicit assumptions exist where ambiguity remains.
- Downstream stages can see what was decided, what remains open, and what is provisional.

### `context_audit`
- A context audit artifact records the relevant environment findings.
- Material constraints, evidence sources, and observed gaps are visible.
- Downstream design work does not need to trust unsupported environment claims.

### `architect`
- A durable architecture decision artifact exists.
- Structural approach, major tradeoffs, and declared constraints are explicit.
- Downstream implementation work can reference a stable design basis instead of inferring one.

### `design`
- A durable design artifact exists for the approved architecture.
- The implementation shape, packetization, or content plan is explicit enough for bounded execution.
- The next stage does not need to invent missing design decisions silently.

### `build_or_write`
- A durable implementation or content artifact exists.
- The produced output is bounded to the approved scope and path.
- The next stage can inspect what was produced without relying on execution narration.

### `qa`
- A durable QA artifact exists.
- Verification results, failures, or limits are explicit.
- Publish decisions can reference observed proof rather than completion claims.

### `publish`
- A durable publish package or equivalent promotion artifact exists.
- What is being promoted, from which verified source, and by which path is explicit.
- Final delivery is tied to preserved provenance and verification context.

## 6. Ownership Model

Ownership is defined at the contract level. It is not proof that separate human or model entities performed the work.

### Operator
- Gives direction, scope, priorities, and acceptance intent.
- May approve, reject, defer, or redirect work.
- Does not replace required artifacts with conversational preference alone.

### Control Kernel
- Owns workflow state, stage sufficiency rules, acceptance logic, and controlled mutation paths.
- Determines whether a stage may be treated as satisfied.
- Must fail closed when required evidence is missing.

### Reasoning / Orchestration Model
- May propose plans, identify gaps, question assumptions, and review artifacts.
- May assist with stage outputs when explicitly tasked.
- Does not become authoritative merely by using stage labels or persuasive narration.

### Codex Executor
- May produce bounded stage artifacts, diffs, and reports within assigned scope.
- Does not determine stage sufficiency.
- Does not decide acceptance, promotion, or canonical workflow truth.

### Stage Contract Owners
- Are responsible for the contract expectations of a stage.
- Own the definition of what that stage must prove.
- Do not prove stage satisfaction merely by title or role label.

Rules:
- Role labels do not prove separate execution.
- Codex may produce bounded stage artifacts.
- Codex does not determine stage sufficiency.
- Only controlled acceptance paths may treat a stage as satisfied.

## 7. Handoff Expectations

Handoffs are required workflow connectors between stages.

Rules:
- Downstream work must reference upstream artifacts.
- A handoff summarizes upstream state, open issues, and next-stage expectations.
- A handoff does not replace the upstream artifact that proves the stage output.
- Missing handoff is a governance failure even if some document exists.
- A downstream artifact that cannot identify its upstream basis is not trustworthy stage progression.

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
- failed verification
- insufficient upstream output
- conflicting sources of truth
- missing acceptance context for the current stage

Rules:
- Blocked state is meaningful workflow state, not mere inconvenience.
- A blocked stage must not self-resolve by assumption collapse.
- Escalation is required when ambiguity, missing proof, or conflicting evidence prevents trustworthy continuation.

## 10. Forward-Compatible Enforcement Notes

This document defines governance now and identifies what later code should enforce.

Future enforcement targets:
- stage-run persistence
- gate engine
- artifact validation
- handoff enforcement
- inspection surface

Not yet implemented:
- persistent stage-run records
- automated stage gate evaluation
- automated artifact sufficiency checks
- automated handoff validation
- authoritative workflow inspection UI or equivalent control-plane surface

## 11. Minimal Examples

### Good Partial Workflow Example

A golden-task trial enters `intake`, `pm`, `context_audit`, and `architect` only.

- `intake` produces an intake request artifact that records the bounded ask and constraints.
- `pm` produces a PM plan plus an assumption register.
- `context_audit` produces a context audit report tied to the code and environment reviewed.
- `architect` produces an architecture decision artifact that references both upstream artifacts.
- A handoff records that the trial stops after `architect`.

This is valid because each completed stage has distinct durable output and the workflow stop point is explicit.

### Invalid Example: `build_or_write` Starts Without Architecture

`pm` produces a plan, then an executor starts writing code and claims architecture was obvious.

This is invalid because `build_or_write` does not outrank `architect`. The missing architecture artifact and missing handoff mean the workflow has skipped a required stage without approved policy.

### Invalid Example: `publish` Claimed Without QA Artifact

A build artifact exists, and a summary says the output is ready to ship, but no QA report exists.

This is invalid because `publish` cannot be treated as satisfied without the QA-stage proof that verifies what is being promoted.
