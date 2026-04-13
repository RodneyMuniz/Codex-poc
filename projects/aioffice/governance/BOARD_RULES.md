# AIOffice Board Rules

Rules status:
- drafted under AIO-002 for operator review
- governs task structure and board movement
- intended to fail closed

## 1. Naming Conventions
- All AIOffice work items use one ID system: `AIO-###`.
- `AIO-###` applies to both tasks and bugs.
- Milestones use exactly: `M<number> - <Capability Wave Name>`.
- Bugs use exactly: `[Bug] <factual defect>`.
- No second local ID system is allowed for the same board.
- No alias IDs, temporary IDs, or narrative labels may replace the canonical item ID.

## 2. Item Taxonomy
### Task
- purpose: a bounded unit of planned work that should produce a defined artifact or observable output
- when it is created:
  - when a bounded outcome is known
  - when the expected artifact path can be named
  - when acceptance can be written without relying on narration
- required fields:
  - `id`
  - `title`
  - `details`
  - `objective`
  - `owner_role`
  - `assigned_role`
  - milestone reference
  - `expected_artifact_path`
  - `acceptance`
  - `dependencies`
  - `status`
- lifecycle expectation:
  - a task starts in `backlog`
  - it may move to `ready` only after the ready gate passes
  - it must produce reviewable outputs before `in_review`
  - it cannot reach `completed` by narration

### Bug
- purpose: a factual defect in behavior, enforcement, artifact integrity, or workflow state
- when it is created:
  - when a real defect is observed
  - when repro steps can be stated
  - when expected and observed behavior can be distinguished
- required fields:
  - all standard work-item fields required for a task
  - `repro_steps`
  - `expected_behavior`
  - `observed_behavior`
  - `impact`
- lifecycle expectation:
  - a bug follows the same board lifecycle as a task
  - a bug remains invalid if it is speculative, hypothetical, or only a concern without observed evidence

## 3. Required Task Fields (Durable)
Every AIOffice task must contain all of the following:
- `id`
- `title`
- `details`
- `objective`
- `owner_role`
- `assigned_role`
- milestone reference
- `expected_artifact_path`
- `acceptance`
- `dependencies`
- `status`

Rules:
- A task missing any required field is not a valid work item.
- `dependencies` is mandatory even if the value is an explicit empty declaration such as `none` or an empty list.
- The current canonical task schema limitation does not waive the requirement to declare `dependencies`.
- Until canonical schema support exists, the governed project artifacts remain the authoritative location for any required field that cannot yet be preserved safely elsewhere.

## 4. Board Lifecycle
Only sanctioned control paths may change board state. Executors do not self-transition work items by narration.

### `backlog`
- meaning: defined but not yet permitted to execute
- allowed transitions:
  - `backlog -> ready`
  - `backlog -> blocked`
- who can move it:
  - operator through sanctioned control
  - control kernel applying declared rules
- before entering:
  - the item must exist as a valid work item

### `ready`
- meaning: the work item passed the ready gate and may be started
- allowed transitions:
  - `ready -> in_progress`
  - `ready -> blocked`
  - `ready -> backlog` if required fields are lost or invalidated
- who can move it:
  - operator through sanctioned control
  - control kernel enforcing the ready gate
- before entering:
  - every required field must exist
  - the ready gate must pass

### `in_progress`
- meaning: bounded execution has started against a ready work item
- allowed transitions:
  - `in_progress -> in_review`
  - `in_progress -> blocked`
  - `in_progress -> backlog` only if the work item is explicitly reset and prior execution is rejected
- who can move it:
  - operator through sanctioned control
  - control kernel after explicit start of bounded work
- before entering:
  - the item must already be `ready`
  - execution context must be tied to the task, not free-floating

### `in_review`
- meaning: required outputs exist and are awaiting acceptance review
- allowed transitions:
  - `in_review -> completed`
  - `in_review -> in_progress`
  - `in_review -> blocked`
- who can move it:
  - operator through sanctioned control
  - control kernel after required review artifacts are present
- before entering:
  - the expected artifact or observable output must exist
  - acceptance checks must be reviewable against observable evidence

### `completed`
- meaning: reviewed, accepted, and closed
- allowed transitions:
  - none in normal flow
  - reopening requires an explicit new control decision
- who can move it:
  - operator through sanctioned control
  - never by executor self-assertion
- before entering:
  - reviewable outputs must exist
  - acceptance must be satisfied by observable evidence
  - no open blocker may remain

### `blocked`
- meaning: interrupt state; work cannot proceed safely or truthfully
- allowed transitions:
  - `blocked -> backlog`
  - `blocked -> ready`
  - `blocked -> in_progress`
  - `blocked -> in_review`
  - only after the blocking condition is explicitly resolved
- who can move it:
  - operator through sanctioned control
  - control kernel when enforcement detects a hard stop
- before entering:
  - the blocking reason must be factual and explicit
  - the item must not continue under implicit assumptions

## 5. Ready Gate
A task cannot move to `ready` unless all of the following are true:
- milestone is defined
- acceptance criteria are explicit
- `owner_role` is defined
- `expected_artifact_path` is defined
- `dependencies` are explicitly declared, even if empty

Strict rules:
- `details` must describe bounded work, not open-ended exploration
- `objective` must identify the intended outcome, not a vague aspiration
- `acceptance` must be testable and observable
- dependencies must be explicit; silence is not a dependency model

Forbidden at the ready gate:
- `we'll figure it out later`
- placeholder acceptance
- implicit assumptions
- missing artifact targets
- silent dependency gaps

If any required field is missing or weak, the task remains out of `ready`.

## 6. Acceptance Criteria Rules
Acceptance criteria must be:
- testable
- verifiable without trusting narration
- tied to observable outputs such as files, tests, traces, or artifacts

Acceptance criteria must not:
- rely on role claims
- rely on conversational confidence
- rely on undocumented side effects

Forbidden acceptance language:
- `looks good`
- `done`
- `seems correct`
- other vague success statements
- narrative completion claims without evidence

## 7. Bug Handling Model
Bug rules:
- bugs are created only from factual defects
- bugs use the same ID system: `AIO-###`
- bug titles must use `[Bug] <factual defect>`
- no speculative bugs are allowed

Every bug must include:
- `repro_steps`
- `expected_behavior`
- `observed_behavior`
- `impact`

If any of those fields are missing, the bug is not valid. A suspicion, theory, or future concern is not a bug until a factual defect is observed.

## 8. Stage-Awareness (Forward-Compatible)
AIOffice tasks are expected to map later to workflow stages.

Compatibility rules:
- artifacts are treated as stage outputs
- stage boundaries will require distinct artifacts and handoffs
- stage completion will require both artifacts and handoff evidence
- board rules must remain compatible with later stage enforcement

This document does not define a stage engine. It defines the minimum discipline required so later stage enforcement is possible.

## 9. Bundle Execution And Status Recording
`BOARD_RULES.md` defines the canonical lifecycle and remains authoritative. The lifecycle meanings and gate expectations do not disappear merely because the current AIO backlog is recorded as a current-state ledger instead of a full event-history log.

If AIOffice uses an authoritative current-state backlog ledger rather than an event-history log, operator-authorized bounded bundles may use a special condensed status-recording rule for the end-of-bundle snapshot.

Chosen policy:
- condensed transition recording is allowed only for authoritative current-state backlog recording
- condensed transition recording does not change the canonical lifecycle itself
- condensed transition recording does not create permission to skip the conceptual lifecycle, ready gate, artifact law, or review law

Strict constraints:
- the bundle scope must explicitly name all included tasks
- intra-bundle dependencies must be explicit
- task execution order inside the bundle must be reviewable
- conceptual ready-gate sufficiency must exist before a task is treated as having begun execution inside the bundle
- no task may be recorded as `completed` in the same pass that first executes it
- required artifacts must exist before a task may be recorded as `in_review`
- condensed recording does not erase the conceptual lifecycle; it only affects how the current-state ledger records the end-of-bundle snapshot
- if bundle scope, order, dependencies, or required outputs are not reviewable, condensed recording is not allowed

Interpretation rules:
- the authoritative backlog may show a task at its end-of-bundle state without separately rendering every intermediate transition
- this is a bounded exception for authoritative current-state backlog recording, not a general license to skip workflow law
- executor summaries alone do not satisfy this rule
- condensed recording still requires operator-authorized or otherwise governed bundle context

## 10. Anti-Patterns
The following behaviors are forbidden:
- task completion by narration
- implicit assumption collapse
- skipping the ready gate
- generating artifacts without task context
- modifying state outside controlled paths
- treating role labels as proof of workflow separation
- moving items forward because the output is convenient rather than verified
- accepting missing dependencies because the canonical schema is incomplete
- bundled status normalization with no explicit bundle scope, dependency handling, or reviewable provenance

## 11. Minimal Examples
### Valid task
```yaml
id: AIO-014
title: Define executor packet envelope
details: Write the first packet envelope contract for bounded executor dispatch.
objective: Produce a reviewable packet contract artifact for executor dispatch.
owner_role: Project Orchestrator
assigned_role: Architect
milestone: M2 - Workflow Contract And Stage Separation
expected_artifact_path: projects/aioffice/governance/PACKET_CONTRACT.md
acceptance:
  - artifact exists at the expected path
  - contract defines required packet fields
  - contract defines rejection conditions
dependencies:
  - AIO-001
status: backlog
```

Why valid:
- every required field exists
- the artifact path is explicit
- acceptance is observable
- dependencies are declared

### Invalid task
```yaml
id: draft-packet-task
title: Work on packet flow
details: Start exploring and figure out the right shape later.
objective: Make packet flow better.
owner_role: Architect
expected_artifact_path: ""
acceptance:
  - looks good
status: ready
```

Why invalid:
- ID format is wrong
- `assigned_role` is missing
- milestone reference is missing
- artifact path is empty
- dependencies are missing
- acceptance is vague
- the item was moved to `ready` without passing the ready gate
