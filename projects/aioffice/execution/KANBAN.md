# AIOffice Kanban Bootstrap

Bootstrap status:
- manual founding backlog seed
- governance-first planning surface
- not yet mirrored into canonical task rows
- canonical task import deferred while durable `dependencies` cannot be preserved in the current schema

## Backlog Source Of Truth
- AIOffice task tracking currently lives in this project-local `KANBAN.md`.
- AIO tasks are not yet mirrored into the app/canonical task board.
- Until canonical task import safely preserves required durable fields, this file is the AIOffice backlog source of truth.
- App surfaces for AIO are projections only and must not be treated as authoritative backlog state.

## Board Lifecycle
- `backlog`
- `ready`
- `in_progress`
- `in_review`
- `completed`
- `blocked` and `deferred` remain secondary states

## Milestone Ledger

### M1 - AIOffice Founding And Governance Reset
- milestone_order: 1
- entry_goal: AIOffice has a bounded project shell, explicit governance stubs, and a founding backlog with durable metadata.
- exit_goal: The founding governance set is ratified enough to start bounded implementation planning without leaning on the old orchestration model.
- owner_role: Project Orchestrator
- status: completed

### M2 - Workflow Contracts And PM Discipline
- milestone_order: 2
- entry_goal: AIOffice has a reviewed founding governance base and can define workflow contracts, stage intent, and PM discipline without claiming runtime enforcement that does not exist yet.
- exit_goal: The first workflow-contract, handoff, gate, and PM-discipline rules are defined clearly enough to support a bounded integrity trial specification through architect.
- owner_role: Project Orchestrator
- status: completed

### M3 - Control Kernel Protocol And Execution Packets
- milestone_order: 3
- entry_goal: AIOffice has accepted workflow contracts through the first architect-stop integrity-trial specification and can now define the outer control-kernel interfaces that constrain reasoning and execution.
- exit_goal: Controlled chat, execution packet, execution bundle, promotion policy, control-kernel entity model, and manual airlock trial procedure are defined clearly enough to guide implementation without granting authority to Codex or projections.
- owner_role: Project Orchestrator
- status: in_progress

## Completed

### Write AIOffice charter, doctrine, non-goals, and success definition
- id: AIO-001
- title: Write AIOffice charter, doctrine, non-goals, and success definition
- details: Expand the bootstrap `PROJECT.md` stub into the first approved charter artifact for AIOffice. The output should make the project mission, doctrine, non-goals, and success definition explicit without reusing the current multi-role runtime as the planning model.
- objective: Establish the first durable charter for AIOffice so later governance and execution work has a stable reference point.
- owner_role: Project Orchestrator
- assigned_role: Project Orchestrator
- milestone: M1 - AIOffice Founding And Governance Reset
- expected_artifact_path: projects/aioffice/governance/PROJECT.md
- acceptance:
  - `PROJECT.md` defines charter, doctrine, non-goals, and success definition.
  - doctrine explicitly rejects bootstrap dependence on old orchestration behavior.
  - success definition is concrete enough to guide later milestone exits.
- dependencies:
  - none
- status: completed

### Define naming conventions, item taxonomy, board lifecycle, and ready gate
- id: AIO-002
- title: Define naming conventions, item taxonomy, board lifecycle, and ready gate
- details: Turn the bootstrap `BOARD_RULES.md` note into an approved governance artifact covering naming conventions, item taxonomy, board lifecycle, and the AIOffice ready gate. The result should stay governance-first and should not rely on the current runtime planning path.
- objective: Give AIOffice an explicit board contract before any non-bootstrap execution begins.
- owner_role: Project Orchestrator
- assigned_role: Project Orchestrator
- milestone: M1 - AIOffice Founding And Governance Reset
- expected_artifact_path: projects/aioffice/governance/BOARD_RULES.md
- acceptance:
  - `BOARD_RULES.md` defines naming conventions, taxonomy, lifecycle, and ready gate.
  - primary and secondary board states are explicit.
  - ready criteria are compatible with the founding backlog metadata.
- dependencies:
  - AIO-001
- status: completed

### Define AIOffice core artifact set and ownership map
- id: AIO-003
- title: Define AIOffice core artifact set and ownership map
- details: Convert the bootstrap `ARTIFACT_MAP.md` into a durable map of core AIOffice artifacts, their purposes, and their owners. The output should distinguish governance artifacts from execution artifacts and note what remains intentionally undefined.
- objective: Make artifact ownership explicit before future implementation or import work starts.
- owner_role: Architect
- assigned_role: Architect
- milestone: M1 - AIOffice Founding And Governance Reset
- expected_artifact_path: projects/aioffice/governance/ARTIFACT_MAP.md
- acceptance:
  - `ARTIFACT_MAP.md` lists the core artifact set with purpose and ownership.
  - governance and execution artifacts are clearly separated.
  - known gaps remain visible as TODOs rather than hidden assumptions.
- dependencies:
  - AIO-001
- status: completed

### Audit ProjectKanban donors into keep, adapt, discard, and defer
- id: AIO-004
- title: Audit ProjectKanban donors into keep, adapt, discard, and defer
- details: Review potential donor patterns from `projects/program-kanban/` and classify them in `DONOR_LEDGER.md` as keep, adapt, discard, or defer. The audit must explicitly reject reuse of the old multi-role planning runtime for AIOffice bootstrap.
- objective: Preserve useful governance patterns without silently importing incompatible runtime behavior.
- owner_role: Project Orchestrator
- assigned_role: Project Orchestrator
- milestone: M1 - AIOffice Founding And Governance Reset
- expected_artifact_path: projects/aioffice/governance/DONOR_LEDGER.md
- acceptance:
  - `DONOR_LEDGER.md` classifies donor elements into keep, adapt, discard, and defer.
  - each donor choice includes a rationale.
  - multi-role runtime planning reuse is recorded as discard for bootstrap.
- dependencies:
  - AIO-001
- status: completed

### Define workspace boundaries, authoritative-root rules, scratch-space rules, and import rules
- id: AIO-005
- title: Define workspace boundaries, authoritative-root rules, scratch-space rules, and import rules
- details: Turn the bootstrap boundary notes into a durable workspace policy that names the authoritative root, rejects the duplicate Documents root, defines scratch-space rules, and explains how donor material may be imported without mutating the source project.
- objective: Keep AIOffice bootstrap work safely inside the approved workspace boundaries.
- owner_role: Architect
- assigned_role: Architect
- milestone: M1 - AIOffice Founding And Governance Reset
- expected_artifact_path: projects/aioffice/governance/WORKSPACE_BOUNDARIES.md
- acceptance:
  - `WORKSPACE_BOUNDARIES.md` defines authoritative-root, duplicate-root, scratch, and import rules.
  - allowed exceptions outside `projects/aioffice/` are explicit.
  - the duplicate Documents root is marked non-authoritative.
- dependencies:
  - AIO-001
- status: completed

### Seed the first milestone ledger and founding backlog
- id: AIO-006
- title: Seed the first milestone ledger and founding backlog
- details: Replace this bootstrap backlog with the first approved milestone ledger for AIOffice. The resulting `KANBAN.md` should keep durable task metadata, preserve the founding milestone, and remain explicit about statuses and dependencies without auto-closing any work.
- objective: Stabilize the first execution ledger for AIOffice so later planning work has a durable starting point.
- owner_role: Project Orchestrator
- assigned_role: Project Orchestrator
- milestone: M1 - AIOffice Founding And Governance Reset
- expected_artifact_path: projects/aioffice/execution/KANBAN.md
- acceptance:
  - `KANBAN.md` includes the founding milestone and AIO-001 through AIO-007 with durable fields.
  - task statuses respect the defined lifecycle and ready gate.
  - no AIO task is auto-completed or auto-closed as part of the seed.
- dependencies:
  - AIO-001
  - AIO-002
  - AIO-003
  - AIO-004
  - AIO-005
- status: completed

### [Bug] AIOffice bootstrap used direct SQLite project registration outside sanctioned store path
- id: AIO-007
- item_type: bug
- title: [Bug] AIOffice bootstrap used direct SQLite project registration outside sanctioned store path
- details: Record the historical bootstrap defect and note that the sanctioned registration path was later added, but the bug entry itself was missing from the local backlog.
- objective: Preserve factual defect history and ensure bootstrap state is represented in the AIOffice local backlog.
- owner_role: Project Orchestrator
- assigned_role: Architect
- milestone: M1 - AIOffice Founding And Governance Reset
- expected_artifact_path: sessions/store.py
- acceptance:
  - the defect is described factually.
  - the sanctioned replacement path is referenced as the corrective direction.
  - the local backlog now includes AIO-007.
  - no other AIO task status is changed by this reconciliation.
- dependencies: []
- status: completed

### Define AIOffice backlog source-of-truth and projection policy
- id: AIO-008
- item_type: task
- title: Define AIOffice backlog source-of-truth and projection policy
- details: Define one authoritative backlog state model for AIOffice, projection rules for non-authoritative views, and the migration path from project-local backlog truth to a sanctioned canonical state path once durable fields can be preserved safely.
- objective: Eliminate split backlog truth between markdown, app projection, executor summary, and canonical state assumptions.
- owner_role: Project Orchestrator
- assigned_role: Architect
- milestone: M1 - AIOffice Founding And Governance Reset
- expected_artifact_path: projects/aioffice/governance/BOARD_STATE_POLICY.md
- acceptance:
  - one authoritative AIO backlog source is defined explicitly.
  - projection surfaces are defined as derived, not peer truth.
  - allowed state mutation paths are defined.
  - migration conditions to a future canonical state path are defined.
  - no other AIO task status is changed by this reconciliation.
- dependencies: []
- status: completed

### Define canonical workflow stages, stage intent, and ownership map
- id: AIO-009
- item_type: task
- title: Define canonical workflow stages, stage intent, and ownership map
- details: Define the ordered AIOffice workflow stages, their purpose, conceptual entry and exit expectations, and stage-level ownership rules without pretending the runtime engine already exists.
- objective: Establish the canonical stage contract that later code and gate policy will enforce.
- owner_role: Project Orchestrator
- assigned_role: Architect
- milestone: M2 - Workflow Contracts And PM Discipline
- expected_artifact_path: projects/aioffice/governance/STAGE_GOVERNANCE.md
- acceptance:
  - canonical stage order is explicit.
  - stage purpose is defined.
  - conceptual entry and exit expectations are defined.
  - stage ownership is defined without treating role labels as proof.
  - no runtime implementation is claimed.
- dependencies: []
- status: completed

### Define workflow-run concepts and first integrity-slice artifact contracts
- id: AIO-010
- item_type: task
- title: Define workflow-run concepts and first integrity-slice artifact contracts
- details: Define the workflow-run model and the initial contract set for intake, pm, context audit, and architect artifacts.
- objective: Establish the conceptual workflow-run and artifact-contract model for the first orchestration integrity slice.
- owner_role: Project Orchestrator
- assigned_role: Architect
- milestone: M2 - Workflow Contracts And PM Discipline
- expected_artifact_path: projects/aioffice/governance/WORKFLOW_VISION.md
- acceptance:
  - workflow-run concept is defined.
  - first-slice artifact contracts are enumerated.
  - artifacts are tied to stages, not narration.
  - no persistence engine is claimed.
- dependencies:
  - AIO-009
- status: completed

### Define handoff, blocker, and question/assumption contract model
- id: AIO-011
- item_type: task
- title: Define handoff, blocker, and question/assumption contract model
- details: Define the contract model for handoffs, blockers, questions, and assumptions so later workflow execution can fail closed on unresolved ambiguity or missing transfer state.
- objective: Establish the non-artifact support contracts required for trustworthy stage transitions.
- owner_role: Project Orchestrator
- assigned_role: Architect
- milestone: M2 - Workflow Contracts And PM Discipline
- expected_artifact_path: projects/aioffice/execution/HANDOFF.md
- acceptance:
  - handoff contract is defined.
  - blocker contract is defined.
  - question and assumption contracts are defined.
  - unresolved state is treated as meaningful workflow state.
- dependencies:
  - AIO-009
- status: completed

### Define fail-closed stage-gate policy for the first integrity slice
- id: AIO-012
- item_type: task
- title: Define fail-closed stage-gate policy for the first integrity slice
- details: Define the governance-level start and completion gate rules for intake, pm, context audit, and architect.
- objective: Establish the first enforceable stage-gate contract before runtime implementation.
- owner_role: Project Orchestrator
- assigned_role: Architect
- milestone: M2 - Workflow Contracts And PM Discipline
- expected_artifact_path: projects/aioffice/governance/STAGE_GATE_POLICY.md
- acceptance:
  - start and completion gates are defined for the first integrity slice.
  - downstream dependency rules are explicit.
  - missing artifacts or handoffs are treated as gate failures.
  - no runtime gate engine is claimed.
- dependencies:
  - AIO-009
  - AIO-010
  - AIO-011
- status: completed

### Define PM clarification and assumption discipline
- id: AIO-013
- item_type: task
- title: Define PM clarification and assumption discipline
- details: Define the rule that PM must either ask clarification questions or produce an explicit assumption register for non-trivial work.
- objective: Eliminate silent assumption collapse in AIOffice planning.
- owner_role: Project Orchestrator
- assigned_role: PM
- milestone: M2 - Workflow Contracts And PM Discipline
- expected_artifact_path: projects/aioffice/governance/PM_DISCIPLINE.md
- acceptance:
  - PM clarification rule is explicit.
  - assumption register rule is explicit.
  - non-trivial work cannot pass through PM silently.
  - no fake PM execution is claimed.
- dependencies:
  - AIO-009
  - AIO-010
- status: completed

### Define golden-task integrity trial spec through architect only
- id: AIO-014
- item_type: task
- title: Define golden-task integrity trial spec through architect only
- details: Define the partial golden-task trial that must stop after intake, pm, context audit, and architect, with distinct artifacts and handoffs.
- objective: Establish the first non-theatrical orchestration integrity trial for AIOffice.
- owner_role: Project Orchestrator
- assigned_role: QA
- milestone: M2 - Workflow Contracts And PM Discipline
- expected_artifact_path: projects/aioffice/governance/GOLDEN_TASK_SPEC.md
- acceptance:
  - the golden task is defined explicitly.
  - the stop point at architect is explicit.
  - required stage artifacts are explicit.
  - later stages remain out of scope for the first trial.
- dependencies:
  - AIO-009
  - AIO-010
  - AIO-011
  - AIO-012
  - AIO-013
- status: completed

### [Bug] Bundled KANBAN normalization bypassed declared board lifecycle transitions
- id: AIO-021
- item_type: bug
- title: [Bug] Bundled KANBAN normalization bypassed declared board lifecycle transitions
- details: recent bounded execution bundles moved AIO tasks from backlog directly to in_review in the authoritative local backlog, which conflicts with the declared lifecycle in BOARD_RULES.md
- objective: correct the governance contract for bundled execution state recording so authoritative backlog truth and declared lifecycle law no longer conflict
- owner_role: Project Orchestrator
- assigned_role: Architect
- milestone: M3 - Control Kernel Protocol And Execution Packets
- expected_artifact_path: projects/aioffice/governance/BOARD_RULES.md
- repro_steps:
  - inspect BOARD_RULES.md lifecycle transitions
  - inspect recent KANBAN status changes for bundled execution
  - observe that at least one bundled task moved backlog -> in_review directly
- expected_behavior: bundled execution state recording must follow declared board law or an explicit approved condensed-transition policy
- observed_behavior: bundled execution status normalization recorded end states that are not currently permitted by the declared lifecycle rules
- impact: authoritative backlog truth currently conflicts with accepted governance, which weakens auditability for larger bounded bundles
- acceptance:
  - the defect is recorded factually
  - governance is updated so bundle-state recording rules are explicit
  - future larger bundles have a lawful status-recording rule
  - no runtime or app behavior is changed in this pass
- dependencies: []
- status: completed

### Define bundle execution and condensed-transition policy for the authoritative backlog
- id: AIO-022
- item_type: task
- title: Define bundle execution and condensed-transition policy for the authoritative backlog
- details: define how operator-authorized bounded execution bundles may be reflected in the authoritative current-state backlog without creating hidden lifecycle violations
- objective: make larger Codex bundles compatible with AIOffice board truth and lifecycle law
- owner_role: Project Orchestrator
- assigned_role: Architect
- milestone: M3 - Control Kernel Protocol And Execution Packets
- expected_artifact_path: projects/aioffice/governance/BOARD_STATE_POLICY.md
- acceptance:
  - the relationship between current-state ledger truth and lifecycle transitions is explicit
  - bundled execution rules are explicit
  - intra-bundle dependency handling is explicit
  - condensed state recording, if allowed, is tightly bounded and reviewable
  - no hidden second truth surface is introduced
- dependencies:
  - AIO-021
- status: completed

### Define controlled chat command grammar and operator decision protocol
- id: AIO-015
- item_type: task
- title: Define controlled chat command grammar and operator decision protocol
- details: define the permitted operator-to-control-kernel command surface and decision verbs so reasoning remains advisory and state changes remain explicit
- objective: establish the operator-facing control-chat contract that separates proposal from authority
- owner_role: Project Orchestrator
- assigned_role: Architect
- milestone: M3 - Control Kernel Protocol And Execution Packets
- expected_artifact_path: projects/aioffice/governance/CONTROL_CHAT_PROTOCOL.md
- acceptance:
  - command classes are defined
  - authoritative versus advisory actions are distinguished
  - operator decision verbs are explicit
  - chat alone is not granted execution or state authority
- dependencies: []
- status: completed

### Define bounded execution packet schema for Codex work
- id: AIO-016
- item_type: task
- title: Define bounded execution packet schema for Codex work
- details: define the packet structure used to delegate bounded execution to Codex, including scope, allowed paths, forbidden actions, required outputs, and validation expectations
- objective: establish the packet-out contract that constrains executor work
- owner_role: Project Orchestrator
- assigned_role: Architect
- milestone: M3 - Control Kernel Protocol And Execution Packets
- expected_artifact_path: projects/aioffice/governance/EXECUTION_PACKET_SPEC.md
- acceptance:
  - minimum packet fields are defined
  - scope and write-boundary controls are explicit
  - required artifact and validation expectations are defined
  - packet issuance does not grant stage authority
- dependencies:
  - AIO-015
- status: completed

### Define return bundle schema, evidence receipts, and self-report limits
- id: AIO-017
- item_type: task
- title: Define return bundle schema, evidence receipts, and self-report limits
- details: define the structure of executor return bundles, including produced artifacts, diffs, command/test receipts, blockers, questions, assumptions, and limits on self-reported completion
- objective: establish the bundle-back contract that separates claims from proof
- owner_role: Project Orchestrator
- assigned_role: Architect
- milestone: M3 - Control Kernel Protocol And Execution Packets
- expected_artifact_path: projects/aioffice/governance/EXECUTION_BUNDLE_SPEC.md
- acceptance:
  - minimum bundle fields are defined
  - claim versus proof is explicit
  - evidence receipts and provenance are defined
  - bundle self-acceptance is explicitly forbidden
- dependencies:
  - AIO-016
- status: completed

### Define apply, reject, and promotion policy for non-authoritative outputs
- id: AIO-018
- item_type: task
- title: Define apply, reject, and promotion policy for non-authoritative outputs
- details: define how scratch or non-authoritative executor outputs may be accepted, rejected, or promoted into authoritative state through controlled paths
- objective: establish the decision boundary between produced output and authoritative state
- owner_role: Project Orchestrator
- assigned_role: Architect
- milestone: M3 - Control Kernel Protocol And Execution Packets
- expected_artifact_path: projects/aioffice/governance/APPLY_PROMOTION_POLICY.md
- acceptance:
  - apply, reject, and promotion paths are defined
  - authoritative-state mutation is explicitly controlled
  - provenance and destination-path requirements are explicit
  - uncontrolled self-promotion is forbidden
- dependencies:
  - AIO-016
  - AIO-017
- status: completed

### Define control-kernel entity model for workflow_run, stage_run, artifact, handoff, blocker, question_or_assumption, and orchestration_trace
- id: AIO-019
- item_type: task
- title: Define control-kernel entity model for workflow_run, stage_run, artifact, handoff, blocker, question_or_assumption, and orchestration_trace
- details: define the conceptual entity model that the future control kernel will persist and inspect
- objective: establish the authoritative control-plane data model before implementation
- owner_role: Project Orchestrator
- assigned_role: Architect
- milestone: M3 - Control Kernel Protocol And Execution Packets
- expected_artifact_path: projects/aioffice/governance/CONTROL_KERNEL_MODEL.md
- acceptance:
  - all core control-kernel entities are defined
  - entity responsibilities and relationships are explicit
  - the model aligns with accepted workflow and artifact governance
  - no persistence engine is claimed
- dependencies:
  - AIO-015
  - AIO-016
  - AIO-017
- status: completed

## In Review

### Define manual packet-out and bundle-back trial procedure
- id: AIO-020
- item_type: task
- title: Define manual packet-out and bundle-back trial procedure
- details: define the first manual trial procedure for bounded Codex execution using the packet and bundle contracts before automation exists
- objective: establish the first real executor-airlock rehearsal procedure for AIOffice
- owner_role: Project Orchestrator
- assigned_role: QA
- milestone: M3 - Control Kernel Protocol And Execution Packets
- expected_artifact_path: projects/aioffice/governance/MANUAL_AIRLOCK_TRIAL.md
- acceptance:
  - trial steps are explicit
  - packet issuance and bundle return are defined
  - review and rejection checkpoints are explicit
  - the procedure does not assume runtime automation already exists
- dependencies:
  - AIO-016
  - AIO-017
  - AIO-018
  - AIO-019
- status: in_review

## TODO
- decide whether and when to mirror these tasks into the canonical SQLite task store
- replace bootstrap acceptance wording with ratified governance language
- add later milestones only after M1 artifacts are approved
- record any blocker or deferred states explicitly instead of inventing silent transitions
