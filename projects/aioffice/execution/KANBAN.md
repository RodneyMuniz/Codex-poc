# AIOffice Operational Ledger

Ledger status:
- accepted authoritative AIOffice milestone and task ledger
- governance-first current-state planning surface
- canonical task import remains deferred while durable `dependencies` cannot be preserved safely in the current schema

## Operational Source Of Truth
- AIOffice operational task tracking currently lives in this project-local `KANBAN.md`.
- AIO tasks are not yet mirrored into the app/canonical task board.
- Until canonical task import safely preserves required durable fields, this file is the AIOffice milestone and task source of truth.
- App surfaces for AIO are projections only and must not be treated as authoritative task or milestone state.

## Board Lifecycle
- `backlog`
- `ready`
- `in_progress`
- `in_review`
- `completed`
- `blocked` and `deferred` remain secondary states

## Board Invariants
- `status` is the canonical task-state signal for every `AIO-*` task row.
- Physical section placement is derived from canonical `status` and must match it.
- Any mismatch between a task row's `status` and its section placement is a ledger defect.
- Each `AIO-*` task row must appear exactly once in this file.
- `## Completed` may contain only task rows whose canonical `status` is `completed`.
- `## Ready`, `## In Progress`, and `## In Review` may contain only task rows whose canonical `status` matches the section name.
- `## Backlog` may contain only task rows whose canonical `status` is `backlog`.

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
- status: completed

### M4 - Minimum Control Kernel Implementation
- milestone_order: 4
- entry_goal: AIOffice has accepted governance and protocol definitions through the manual airlock trial procedure and can now implement the first sanctioned control-kernel state path.
- exit_goal: persisted control-kernel entities, packet and bundle persistence, first-slice fail-closed transition checks, and a read-only inspection path exist well enough to support one supervised closed-loop rehearsal without granting authority to Codex or projections.
- owner_role: Project Orchestrator
- status: completed

### M5 - Operational Hardening And Supervised Expansion
- milestone_order: 5
- entry_goal: AIOffice has a completed minimum control-kernel slice and one supervised rehearsal, and can now harden operational boundaries while expanding supervised evidence.
- exit_goal: store bootstrap side effects are isolated, end-to-end operator invocation is proven, controlled apply/promotion is implemented and rehearsed, broader supervised rehearsal evidence exists, and readiness for semi-autonomous bounded operation can be reviewed explicitly.
- owner_role: Project Orchestrator
- status: completed

### M6 - Post-M5 Narrow Proof Slice
- milestone_order: 6
- entry_goal: `M5` has closed with an explicit fail-closed readiness review, and the next work should reduce current-boundary uncertainty without broadening into later-stage workflow proof.
- exit_goal: the separate `apply` branch is rehearsed under supervision, same-workspace repeated-run or shared-store contention behavior is reviewed explicitly under bounded evidence, and the resulting proof boundary is re-stated without implying later-stage or unattended readiness.
- owner_role: Project Orchestrator
- status: completed

### M7 - Post-M6 Operator Decision Surface Hardening
- milestone_order: 7
- entry_goal: `M6` has closed with an explicit narrow proof review and a current system-reality map, and the next work should reduce manual operator glue on the already-real control surfaces without widening workflow proof.
- exit_goal: a narrow operator-facing bundle decision surface is defined, implemented over sanctioned persisted state, and rehearsed under supervision without implying later-stage workflow or readiness upgrades.
- owner_role: Project Orchestrator
- status: completed

### M8 - Post-M7 Operator Decision Input Ergonomics Hardening
- milestone_order: 8
- entry_goal: `M7` has closed with an explicit review, and the next work should reduce remaining manual operator glue on the already-real `bundle-decision` surface, especially shell-safe explicit input handling, without changing readiness claims or widening workflow proof.
- exit_goal: a shell-safe operator decision input contract is defined, implemented, and rehearsed on the existing `bundle-decision` surface without weakening explicit destination-mapping control or implying later-stage workflow or readiness upgrades.
- owner_role: Project Orchestrator
- status: completed

### M9 - Post-M8 Current-State And Planning-Surface Reconciliation
- milestone_order: 9
- entry_goal: `M8` has closed with an explicit review, and the next work should reconcile stale current-state and planning-surface wording to accepted post-`M8` truth without changing control behavior or readiness claims.
- exit_goal: the stale current-state, workflow, project-brain, and ledger-header surfaces identified in committed governance are reconciled to post-`M8` truth, reducing audit friction without widening workflow proof.
- owner_role: Project Orchestrator
- status: completed

### M10 - Change Governance, Recovery, And Maintainability Hardening
- milestone_order: 10
- entry_goal: `M9` has closed with reconciled planning surfaces, and the next work should harden change governance, recovery discipline, and maintainability contracts before any UI or art-pipeline expansion is considered.
- exit_goal: an admin-only product/self-change governance boundary, an automated snapshot/version/restore/rollback contract with rehearsal plan, and a feature-isolation/code-review contract are defined clearly enough to guide later implementation without changing readiness or widening workflow proof.
- owner_role: Project Orchestrator
- status: completed

### M11 - Recovery Discipline Operationalization
- milestone_order: 11
- entry_goal: `M10` closeout is complete and anchored, and the next work should operationalize recovery discipline by making checkpoint naming, snapshot packaging, restore/rollback routines, and recovery proof more real before protected-surface enforcement or workflow-breadth expansion increases blast radius.
- exit_goal: checkpoint naming and version discipline are explicit in current practice, recovery preflight and backup/restore routines are hardened over the existing repo reality, one bounded restore/rollback rehearsal is executed and recorded, and the resulting recovery posture is reviewed without changing readiness or widening workflow proof.
- owner_role: Project Orchestrator
- status: completed

### M12 - Protected Core Surfaces Enforcement
- milestone_order: 12
- entry_goal: `M11` has proved a bounded recovery path through preflight, snapshot packaging, restore, rollback preparation, and rollback execution in a disposable rehearsal target, and the next work should protect core product/state/governance surfaces from ordinary user-facing mutation before workflow breadth expands.
- exit_goal: protected surface classes are reconciled to current truth, ordinary lanes are fail-closed from mutating those surfaces in code, one bounded blocked-attempt rehearsal is recorded, and the resulting enforcement boundary is reviewed without changing readiness or widening workflow proof.
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
- status: completed

### Implement persisted control-kernel entities and sanctioned store helpers
- id: AIO-023
- item_type: task
- title: Implement persisted control-kernel entities and sanctioned store helpers
- details: implement the first persisted representations and store helpers for workflow_run, stage_run, artifact, handoff, blocker, question_or_assumption, and orchestration_trace through sanctioned code paths
- objective: move the accepted control-kernel model from conceptual governance into authoritative persisted state
- owner_role: Project Orchestrator
- assigned_role: Architect
- milestone: M4 - Minimum Control Kernel Implementation
- expected_artifact_path: sessions/store.py
- acceptance:
  - sanctioned persisted representations exist for the accepted control-kernel entities
  - create/read helpers exist through sanctioned store paths
  - idempotent behavior is explicit where required
  - no executor or projection surface gains authority
  - focused tests exist
- dependencies: []
- status: completed

### Implement persisted packet issuance and bundle ingestion paths
- id: AIO-024
- item_type: task
- title: Implement persisted packet issuance and bundle ingestion paths
- details: implement the first sanctioned persistence path for execution packets and returned bundles using the accepted packet and bundle contracts
- objective: turn packet-out and bundle-back from governance-only contracts into persisted control-kernel state
- owner_role: Project Orchestrator
- assigned_role: Architect
- milestone: M4 - Minimum Control Kernel Implementation
- expected_artifact_path: sessions/store.py
- acceptance:
  - packet issuance can be recorded through sanctioned code
  - bundle ingestion can be recorded through sanctioned code
  - required packet and bundle fields are checked fail-closed
  - bundle ingestion does not self-accept work
  - focused tests exist
- dependencies:
  - AIO-023
- status: completed

### Implement read-only inspection path for workflow, packet, and bundle state
- id: AIO-025
- item_type: task
- title: Implement read-only inspection path for workflow, packet, and bundle state
- details: implement the first read-only inspection surface for persisted workflow, stage, packet, bundle, and evidence state without introducing a writable UI authority surface
- objective: make control-kernel state inspectable without relying on narration
- owner_role: Project Orchestrator
- assigned_role: Architect
- milestone: M4 - Minimum Control Kernel Implementation
- expected_artifact_path: scripts/operator_api.py
- acceptance:
  - persisted control-kernel state is inspectable through a read-only path
  - projection is clearly derived from sanctioned state
  - no writable authority surface is introduced by this task
  - focused tests or verification steps exist
- dependencies:
  - AIO-023
  - AIO-024
- status: completed

### Implement fail-closed first-slice transition checks
- id: AIO-026
- item_type: task
- title: Implement fail-closed first-slice transition checks
- details: implement the first machine-evaluable checks for intake, pm, context_audit, and architect progression using the accepted stage, workflow, handoff, PM, and gate policies
- objective: move first-slice progression from governance-only definition into fail-closed state checks
- owner_role: Project Orchestrator
- assigned_role: Architect
- milestone: M4 - Minimum Control Kernel Implementation
- expected_artifact_path: state_machine.py
- acceptance:
  - first-slice progression checks exist for start and completion conditions
  - missing artifacts, missing handoffs, or missing PM branch outputs fail closed
  - downstream progression cannot be implied by narration
  - focused tests exist
- dependencies:
  - AIO-023
  - AIO-024
- status: completed

### Run one supervised closed-loop rehearsal against a bounded task
- id: AIO-027
- item_type: task
- title: Run one supervised closed-loop rehearsal against a bounded task
- details: execute one supervised implementation-facing rehearsal using persisted packet, bundle, inspection, and first-slice control checks against a bounded low-risk task
- objective: validate that the first implemented control-kernel slice behaves as intended under supervision
- owner_role: Project Orchestrator
- assigned_role: QA
- milestone: M4 - Minimum Control Kernel Implementation
- expected_artifact_path: projects/aioffice/artifacts/M4_FIRST_REHEARSAL_REPORT.md
- acceptance:
  - one bounded rehearsal is executed under supervision
  - packet issuance, bundle return, review, and state inspection are exercised
  - observed failures or gaps are recorded explicitly
  - no unattended autonomy is implied by this task
- dependencies:
  - AIO-024
  - AIO-025
  - AIO-026
- status: completed

### Record M4 implementation review and residual blockers
- id: AIO-028
- item_type: task
- title: Record M4 implementation review and residual blockers
- details: summarize what the implemented M4 slice proves, what remains unproven, and what must still exist before unattended or overnight operation is considered
- objective: produce an explicit go/no-go review for moving beyond supervised control-kernel rehearsal
- owner_role: Project Orchestrator
- assigned_role: QA
- milestone: M4 - Minimum Control Kernel Implementation
- expected_artifact_path: projects/aioffice/governance/M4_IMPLEMENTATION_REVIEW.md
- acceptance:
  - proven capabilities are listed explicitly
  - unproven capabilities are listed explicitly
  - residual blockers to unattended operation are explicit
  - no false claim of autonomy readiness is made
- dependencies:
  - AIO-027
- status: completed

### Isolate store bootstrap side effects for bounded rehearsal environments
- id: AIO-029
- item_type: task
- title: Isolate store bootstrap side effects for bounded rehearsal environments
- details: remove or contain unrelated side-file creation when using isolated rehearsal or temporary store roots so bounded trials do not create irrelevant project residue
- objective: make rehearsal environments clean and predictable
- owner_role: Project Orchestrator
- assigned_role: Architect
- milestone: M5 - Operational Hardening And Supervised Expansion
- expected_artifact_path: sessions/store.py
- acceptance:
  - isolated rehearsal setup no longer creates unrelated project side files
  - the change is narrow and test-backed
  - no authority model is weakened
- dependencies: []
- status: completed

### Prove end-to-end operator CLI invocation against sanctioned persisted state
- id: AIO-030
- item_type: task
- title: Prove end-to-end operator CLI invocation against sanctioned persisted state
- details: exercise the operator CLI path end-to-end against the sanctioned persisted state model rather than only helper-level access
- objective: prove the actual operator-facing control path, not just internal helper behavior
- owner_role: Project Orchestrator
- assigned_role: Architect
- milestone: M5 - Operational Hardening And Supervised Expansion
- expected_artifact_path: scripts/operator_api.py
- acceptance:
  - end-to-end operator invocation is exercised under test or controlled rehearsal
  - sanctioned persisted state is the source of truth
  - no writable authority surface is introduced
- dependencies:
  - AIO-029
- status: completed

### Implement controlled apply/promotion execution path
- id: AIO-031
- item_type: task
- title: Implement controlled apply/promotion execution path
- details: implement the first sanctioned execution path for apply and promotion decisions so non-authoritative outputs can move toward authoritative state only through controlled code paths
- objective: turn apply/promotion from governance-only policy into implemented controlled behavior
- owner_role: Project Orchestrator
- assigned_role: Architect
- milestone: M5 - Operational Hardening And Supervised Expansion
- expected_artifact_path: sessions/store.py
- acceptance:
  - apply and promotion are implemented as controlled decisions
  - provenance and destination-path requirements are enforced
  - no executor self-promotion path exists
  - focused tests exist
- dependencies:
  - AIO-029
- status: completed

### Rehearse apply/promotion under supervision and record evidence
- id: AIO-032
- item_type: task
- title: Rehearse apply/promotion under supervision and record evidence
- details: run one supervised rehearsal that exercises the new apply/promotion path without implying unattended operation
- objective: prove apply/promotion behavior in practice
- owner_role: Project Orchestrator
- assigned_role: QA
- milestone: M5 - Operational Hardening And Supervised Expansion
- expected_artifact_path: projects/aioffice/artifacts/M5_APPLY_PROMOTION_REHEARSAL.md
- acceptance:
  - one supervised rehearsal is executed
  - evidence is recorded factually
  - no overclaim of autonomy is made
- dependencies:
  - AIO-031
- status: completed

### Run expanded supervised multi-run rehearsal coverage
- id: AIO-033
- item_type: task
- title: Run expanded supervised multi-run rehearsal coverage
- details: run broader supervised rehearsal coverage across more than one bounded task/run so multi-run behavior can be reviewed explicitly
- objective: prove broader supervised behavior before any autonomy claim
- owner_role: Project Orchestrator
- assigned_role: QA
- milestone: M5 - Operational Hardening And Supervised Expansion
- expected_artifact_path: projects/aioffice/artifacts/M5_MULTI_RUN_REHEARSAL_REPORT.md
- acceptance:
  - more than one bounded rehearsal run is exercised
  - results are recorded factually
  - observed failures or instability remain visible
- dependencies:
  - AIO-030
  - AIO-032
- status: completed

### Record M5 readiness review for semi-autonomous bounded operation
- id: AIO-034
- item_type: task
- title: Record M5 readiness review for semi-autonomous bounded operation
- details: review what M5 proved, what remains blocked, and whether the system is ready for a bounded supervised semi-autonomous cycle
- objective: produce an explicit go/no-go review for moving toward bounded semi-autonomous operation
- owner_role: Project Orchestrator
- assigned_role: QA
- milestone: M5 - Operational Hardening And Supervised Expansion
- expected_artifact_path: projects/aioffice/governance/M5_READINESS_REVIEW.md
- acceptance:
  - proven and unproven capabilities are explicit
  - residual blockers are explicit
  - no false claim of overnight autonomy readiness is made
- dependencies:
  - AIO-033
- status: completed

### [Bug] Isolated rehearsal workspace still creates unrelated side files after AIO-029
- id: AIO-035
- item_type: bug
- title: [Bug] Isolated rehearsal workspace still creates unrelated side files after AIO-029
- details: `AIO-032` observed isolated-workspace residue that conflicts with the accepted `AIO-029` hardening outcome, including unrelated memory bootstrap files and a non-AIOffice project `KANBAN.md` inside the rehearsal workspace.
- objective: record and remediate the regression so broader supervised rehearsal evidence does not accumulate avoidable unrelated residue.
- owner_role: Project Orchestrator
- assigned_role: Architect
- milestone: M5 - Operational Hardening And Supervised Expansion
- expected_artifact_path: sessions/store.py
- repro_steps:
  - create an isolated rehearsal workspace under `projects/aioffice/artifacts/`
  - instantiate the sanctioned store path and run a bounded supervised rehearsal as recorded in `projects/aioffice/artifacts/M5_APPLY_PROMOTION_REHEARSAL.md`
  - inspect the isolated workspace file tree after the run
  - observe `memory/framework_health.json`, `memory/session_summaries.json`, and `projects/tactics-game/execution/KANBAN.md`
- expected_behavior: isolated rehearsal setup should not create unrelated project side files or unrelated bootstrap residue outside the bounded rehearsal outputs needed for that workspace.
- observed_behavior: the isolated rehearsal workspace accumulated unrelated memory files and a non-AIOffice project ledger file despite `AIO-029` acceptance stating that isolated rehearsal setup no longer creates unrelated project side files.
- impact: this contradicts the accepted `AIO-029` hardening outcome and adds avoidable residue to future supervised rehearsal environments, though it does not by itself invalidate `AIO-032`.
- acceptance:
  - the regression is recorded factually
  - the conflict with `AIO-029` acceptance is explicit
  - remediation scope remains narrow and hardening-focused
  - no autonomy or later-stage workflow claim is implied
- dependencies: []
- status: completed

### Establish remote review surface for AIOffice
- id: AIO-035A
- item_type: task
- title: Establish remote review surface for AIOffice
- details: create a controlled GitHub-visible review anchor for the current accepted AIOffice state so future `M6` proof work and audit can be grounded on pushed branch, tag, and file evidence rather than local-only state
- objective: strengthen narrow supervised proof credibility and auditability without changing the accepted readiness posture or widening workflow proof
- owner_role: Project Orchestrator
- assigned_role: Project Orchestrator
- milestone: M6 - Post-M5 Narrow Proof Slice
- expected_artifact_path: projects/aioffice/governance/ACTIVE_STATE.md
- acceptance:
  - the current authoritative working branch and accepted baseline tag are recorded in `projects/aioffice/governance/ACTIVE_STATE.md`
  - GitHub-visible branch, tag, and grounding-file review anchors are established for audit
  - the current accepted posture and active `M6` tasks are restated without changing readiness claims
  - no later-stage workflow, autonomy, or UAT readiness claim is added
- dependencies:
  - AIO-034
- status: completed

### Rehearse separate apply branch under supervision and record evidence
- id: AIO-036
- item_type: task
- title: Rehearse separate apply branch under supervision and record evidence
- details: run one bounded supervised rehearsal that exercises the sanctioned `apply` branch explicitly so current readiness does not rely only on `promote`-branch proof
- objective: prove the separate `apply` decision path in practice without expanding the workflow boundary
- owner_role: Project Orchestrator
- assigned_role: QA
- milestone: M6 - Post-M5 Narrow Proof Slice
- expected_artifact_path: projects/aioffice/artifacts/M6_APPLY_BRANCH_REHEARSAL.md
- acceptance:
  - one supervised rehearsal of the sanctioned `apply` branch is executed
  - evidence is recorded factually
  - resulting state and limits are explicit
  - no later-stage, unattended, or overnight claim is made
- dependencies:
  - AIO-031
  - AIO-034
  - AIO-035A
- status: completed

### Run bounded same-workspace repeated-run or shared-store contention rehearsal
- id: AIO-037
- item_type: task
- title: Run bounded same-workspace repeated-run or shared-store contention rehearsal
- details: run a narrowly scoped supervised rehearsal that deliberately reuses the same workspace or sanctioned store root so repeated-run, state-collision, residue, or contention behavior can be inspected explicitly
- objective: determine whether the current sanctioned path remains stable when isolation is reduced in a controlled, reviewable way
- owner_role: Project Orchestrator
- assigned_role: QA
- milestone: M6 - Post-M5 Narrow Proof Slice
- expected_artifact_path: projects/aioffice/artifacts/M6_SHARED_STORE_REHEARSAL.md
- acceptance:
  - a bounded repeated-run or shared-store rehearsal is executed under supervision
  - collisions, leakage, residue, or contention observations remain visible
  - authority boundaries remain unchanged
  - no later-stage, unattended, or overnight claim is made
- dependencies:
  - AIO-030
  - AIO-034
  - AIO-035A
- status: completed

### Record narrow post-M5 proof review for apply and shared-store behavior
- id: AIO-038
- item_type: task
- title: Record narrow post-M5 proof review for apply and shared-store behavior
- details: review what the next narrow post-M5 slice proved, what remains unproven, and whether current readiness posture changed after `apply`-branch and same-workspace/shared-store evidence is gathered
- objective: keep the proof boundary explicit before any later-stage workflow expansion is considered
- owner_role: Project Orchestrator
- assigned_role: QA
- milestone: M6 - Post-M5 Narrow Proof Slice
- expected_artifact_path: projects/aioffice/governance/M6_NARROW_PROOF_REVIEW.md
- acceptance:
  - proven and unproven capabilities are explicit
  - readiness posture delta, if any, is explicit
  - residual risks remain visible
  - no later-stage, unattended, or overnight claim is made
- dependencies:
  - AIO-036
  - AIO-037
- status: completed

### Create AIOffice system reality map and seed the next conservative slice
- id: AIO-039
- item_type: task
- title: Create AIOffice system reality map and seed the next conservative slice
- details: create one authoritative post-`M6` system reality map that distinguishes built, partial, and conceptual AIOffice components, identifies active control surfaces and manual glue points, records document conflicts, and seeds the minimum next conservative slice without changing readiness claims
- objective: ground future AIOffice work in committed repo truth rather than narrated capability
- owner_role: Project Orchestrator
- assigned_role: Architect
- milestone: M7 - Post-M6 Operator Decision Surface Hardening
- expected_artifact_path: projects/aioffice/governance/SYSTEM_REALITY_MAP.md
- acceptance:
  - `SYSTEM_REALITY_MAP.md` distinguishes proven, partial, and conceptual system elements
  - current proof-backed control surfaces and manual glue points are explicit
  - stale or conflicting document wording is named factually
  - the next conservative slice is seeded narrowly in `KANBAN.md` and reflected in `ACTIVE_STATE.md`
- dependencies:
  - AIO-038
- status: completed

### Define narrow operator-facing bundle decision surface and fail-closed rules
- id: AIO-040
- item_type: task
- title: Define narrow operator-facing bundle decision surface and fail-closed rules
- details: define the operator-facing surface for inspecting pending-review bundles and issuing sanctioned apply/promotion decisions against persisted state, including required approval inputs, destination-mapping rules, and explicit out-of-scope boundaries
- objective: reduce manual glue on the currently real decision path before any later-stage workflow expansion
- owner_role: Project Orchestrator
- assigned_role: Architect
- milestone: M7 - Post-M6 Operator Decision Surface Hardening
- expected_artifact_path: projects/aioffice/governance/OPERATOR_DECISION_SURFACE.md
- acceptance:
  - the supported decision actions and identifiers are explicit
  - required approval inputs and destination-mapping rules are explicit
  - fail-closed behavior and out-of-scope boundaries are explicit
  - the surface is grounded in the current `sessions/store.py` and `scripts/operator_api.py` reality
- dependencies:
  - AIO-039
- status: completed

### Triage and clear pre-existing operator_api residue before AIO-041
- id: AIO-040A
- item_type: task
- title: Triage and clear pre-existing operator_api residue before AIO-041
- details: inspect the pre-existing local residue in `scripts/operator_api.py` that blocked `AIO-041`, capture the raw patch for audit, classify the residue, restore the file to committed `HEAD`, and record the cleanup explicitly without silently absorbing that residue into later implementation work
- objective: preserve auditability and restore a clean lawful starting point for `AIO-041`
- owner_role: Project Orchestrator
- assigned_role: Architect
- milestone: M7 - Post-M6 Operator Decision Surface Hardening
- expected_artifact_path: projects/aioffice/artifacts/M7_OPERATOR_API_RESIDUE_TRIAGE.md
- acceptance:
  - the pre-existing local diff is preserved in `projects/aioffice/artifacts/M7_OPERATOR_API_RESIDUE.patch`
  - the residue is classified factually in `projects/aioffice/artifacts/M7_OPERATOR_API_RESIDUE_TRIAGE.md`
  - `scripts/operator_api.py` is restored to committed `HEAD` state
  - `AIO-041` and `AIO-042` remain uncompleted
  - repo hygiene is clean again after this bounded cleanup task is committed and pushed
- dependencies:
  - AIO-040
- status: completed

### Implement narrow operator CLI wrapper over the sanctioned bundle decision path
- id: AIO-041
- item_type: task
- title: Implement narrow operator CLI wrapper over the sanctioned bundle decision path
- details: add a bounded operator-facing CLI command that uses sanctioned persisted state to inspect a target bundle context and issue an explicit approved apply/promotion decision without widening workflow proof
- objective: make the currently real decision path usable without direct store-path scripting
- owner_role: Project Orchestrator
- assigned_role: Architect
- milestone: M7 - Post-M6 Operator Decision Surface Hardening
- expected_artifact_path: scripts/operator_api.py
- acceptance:
  - a bounded operator-facing decision wrapper exists for the sanctioned bundle decision path
  - the wrapper requires explicit approval inputs and preserves exact-path enforcement
  - the wrapper does not imply later-stage workflow or readiness upgrades
  - focused verification exists
- dependencies:
  - AIO-040
- status: completed

### Rehearse the operator-facing decision surface under supervision and record evidence
- id: AIO-042
- item_type: task
- title: Rehearse the operator-facing decision surface under supervision and record evidence
- details: run one bounded supervised rehearsal that uses the operator-facing decision surface to inspect a pending-review bundle and issue a sanctioned decision, then record what the surface proved and what still remains manual or unproven
- objective: prove the next narrow operator decision surface in practice without widening workflow proof
- owner_role: Project Orchestrator
- assigned_role: QA
- milestone: M7 - Post-M6 Operator Decision Surface Hardening
- expected_artifact_path: projects/aioffice/artifacts/M7_OPERATOR_DECISION_SURFACE_REHEARSAL.md
- acceptance:
  - one bounded supervised rehearsal of the operator-facing decision surface is executed
  - evidence is recorded factually
  - manual-glue reduction and remaining limits are explicit
  - no concurrency, later-stage, or readiness overclaim is made
- dependencies:
  - AIO-041
- status: completed

### Record post-M7 proof review and ratify the next conservative slice
- id: AIO-043
- item_type: task
- title: Record post-M7 proof review and ratify the next conservative slice
- details: produce one explicit post-`M7` review artifact grounded only in committed evidence, state what `M7` truly proved, what remains manual or unproven, and ratify exactly one next conservative slice without inflating readiness or broadening workflow proof
- objective: keep the proof boundary explicit after `M7` and seed only one evidence-backed next slice
- owner_role: Project Orchestrator
- assigned_role: QA
- milestone: M7 - Post-M6 Operator Decision Surface Hardening
- expected_artifact_path: projects/aioffice/governance/M7_OPERATOR_DECISION_SURFACE_REVIEW.md
- acceptance:
  - the review uses committed evidence only
  - what `AIO-040`, `AIO-041`, and `AIO-042` proved is explicit
  - remaining manual glue, stale-document conflicts, and residual risks are explicit
  - exactly one next conservative slice is ratified, if supported by the evidence
- dependencies:
  - AIO-042
- status: completed

### Define shell-safe operator decision input contract over the existing bundle-decision surface
- id: AIO-044
- item_type: task
- title: Define shell-safe operator decision input contract over the existing bundle-decision surface
- details: define one narrow shell-safe operator input contract for `bundle-decision` so explicit destination mappings remain required and fail-closed while operator entry is less brittle on the currently exercised shell path
- objective: reduce operator input fragility on the already-proven decision surface without widening workflow scope
- owner_role: Project Orchestrator
- assigned_role: Architect
- milestone: M8 - Post-M7 Operator Decision Input Ergonomics Hardening
- expected_artifact_path: projects/aioffice/governance/OPERATOR_DECISION_INPUT_CONTRACT.md
- acceptance:
  - one shell-safe input contract is defined narrowly over the existing `bundle-decision` surface
  - explicit destination mappings remain required
  - fail-closed boundaries remain explicit
  - no later-stage workflow or readiness claim is added
- dependencies:
  - AIO-043
- status: completed

### Implement shell-safe operator decision input path and focused verification
- id: AIO-045
- item_type: task
- title: Implement shell-safe operator decision input path and focused verification
- details: implement one narrow shell-safe input path for explicit `destination_mappings` on the existing `bundle-decision` surface and add focused verification without changing the sanctioned store behavior
- objective: make the already-real decision surface less brittle for supervised operator use
- owner_role: Project Orchestrator
- assigned_role: Architect
- milestone: M8 - Post-M7 Operator Decision Input Ergonomics Hardening
- expected_artifact_path: scripts/operator_api.py
- acceptance:
  - one shell-safe input path exists for explicit destination mappings
  - the wrapper remains bundle-scoped and fail-closed
  - focused verification covers the new input path
  - no readiness upgrade or workflow expansion is implied
- dependencies:
  - AIO-044
- status: completed

### Rehearse the shell-safe operator decision input path under supervision and record evidence
- id: AIO-046
- item_type: task
- title: Rehearse the shell-safe operator decision input path under supervision and record evidence
- details: run one bounded supervised rehearsal of the shell-safe operator decision input path and record what manual glue was reduced and what limits remain
- objective: prove the narrowed ergonomics hardening slice in practice without widening workflow proof
- owner_role: Project Orchestrator
- assigned_role: QA
- milestone: M8 - Post-M7 Operator Decision Input Ergonomics Hardening
- expected_artifact_path: projects/aioffice/artifacts/M8_OPERATOR_DECISION_INPUT_REHEARSAL.md
- acceptance:
  - one bounded supervised rehearsal is executed through the shell-safe input path
  - evidence is recorded factually
  - remaining limits are explicit
  - no concurrency, later-stage, or readiness overclaim is made
- dependencies:
  - AIO-045
- status: completed

### Record post-M8 proof review, reconcile board/state inconsistencies, and ratify the next conservative slice
- id: AIO-047
- item_type: task
- title: Record post-M8 proof review, reconcile board/state inconsistencies, and ratify the next conservative slice
- details: produce one explicit post-`M8` review artifact grounded only in committed evidence, state what `M8` truly proved, reconcile the committed board/state inconsistency where completed `AIO-045` and `AIO-046` still sat under `Backlog`, and ratify exactly one next conservative slice without inflating readiness or broadening workflow proof
- objective: keep the proof boundary explicit after `M8` and re-align the authoritative planning surface before the next slice begins
- owner_role: Project Orchestrator
- assigned_role: QA
- milestone: M9 - Post-M8 Current-State And Planning-Surface Reconciliation
- expected_artifact_path: projects/aioffice/governance/M8_OPERATOR_DECISION_INPUT_REVIEW.md
- acceptance:
  - the review uses committed evidence only
  - what `AIO-044`, `AIO-045`, and `AIO-046` proved is explicit
  - board/state reconciliation decisions are explicit
  - exactly one next conservative slice is ratified, if supported by the evidence
- dependencies:
  - AIO-046
- status: completed

### Reconcile stale current-state and planning-surface wording to post-M8 truth
- id: AIO-048
- item_type: task
- title: Reconcile stale current-state and planning-surface wording to post-M8 truth
- details: reconcile the stale current-state and planning-surface documents already identified in committed governance so project status, workflow wording, project-brain guidance, and ledger header wording no longer conflict with accepted post-`M8` truth
- objective: reduce audit friction and operator ambiguity without changing control behavior or readiness claims
- owner_role: Project Orchestrator
- assigned_role: Architect
- milestone: M9 - Post-M8 Current-State And Planning-Surface Reconciliation
- expected_artifact_path: projects/aioffice/governance/PROJECT.md
- acceptance:
  - `PROJECT.md`, `WORKFLOW_VISION.md`, and `PROJECT_BRAIN.md` are reconciled to post-`M8` truth where they are currently stale
  - stale `KANBAN.md` header wording is reconciled to the current non-bootstrap state
  - `KANBAN.md` makes section placement subordinate to canonical `status` and preserves one-row-per-task discipline
  - `ACTIVE_STATE.md` reflects post-`M8` truth and post-`M9` state without readiness inflation
  - no readiness or workflow-proof inflation is introduced
  - any remaining unresolved conflict is left explicit rather than implied closed
- dependencies:
  - AIO-047
- status: completed

### Record post-M9 control-surface priorities review and ratify the next conservative slice
- id: AIO-049
- item_type: task
- title: Record post-M9 control-surface priorities review and ratify the next conservative slice
- details: produce one explicit post-`M9` review artifact grounded only in committed evidence and the newly raised operator concerns, then ratify exactly one next conservative slice focused on control-surface hardening before UI expansion
- objective: keep the proof boundary explicit after `M9` and choose the next conservative control-surface hardening slice before any UI or art-pipeline work begins
- owner_role: Project Orchestrator
- assigned_role: QA
- milestone: M10 - Change Governance, Recovery, And Maintainability Hardening
- expected_artifact_path: projects/aioffice/governance/M9_CONTROL_SURFACE_PRIORITY_REVIEW.md
- acceptance:
  - the review uses committed evidence plus the operator concerns raised for this review
  - the need for admin-only self-change governance, recovery discipline, maintainability isolation, and eventual canonical state is assessed explicitly
  - UI and art-pipeline timing recommendations are explicit
  - exactly one next conservative slice is ratified
- dependencies:
  - AIO-048
- status: completed

### Define admin-only product-change and self-modification governance boundary
- id: AIO-050
- item_type: task
- title: Define admin-only product-change and self-modification governance boundary
- details: define the narrow governance boundary for which AIOffice product and self-changing actions are admin-only, how they are proposed and approved, and how they stay distinct from ordinary execution-bundle decisions
- objective: prevent future writable surfaces from collapsing routine operator decisions and product-changing authority into the same lane
- owner_role: Project Orchestrator
- assigned_role: Architect
- milestone: M10 - Change Governance, Recovery, And Maintainability Hardening
- expected_artifact_path: projects/aioffice/governance/PRODUCT_CHANGE_GOVERNANCE.md
- acceptance:
  - admin-only product and self-change actions are explicit
  - approval lanes and audit expectations are explicit
  - the boundary remains narrow and does not imply UI or later-stage workflow expansion
- dependencies:
  - AIO-049
- status: completed

### Define automated snapshot/version/restore/rollback contract and rehearsal plan
- id: AIO-051
- item_type: task
- title: Define automated snapshot/version/restore/rollback contract and rehearsal plan
- details: define a narrow AIOffice contract for snapshots, version boundaries, restore authority, rollback scope, and the bounded rehearsal plan required before broader writable or parallel surfaces are considered
- objective: reduce recovery ambiguity before future UI or broader control-surface work increases change blast radius
- owner_role: Project Orchestrator
- assigned_role: Architect
- milestone: M10 - Change Governance, Recovery, And Maintainability Hardening
- expected_artifact_path: projects/aioffice/governance/RECOVERY_AND_ROLLBACK_CONTRACT.md
- acceptance:
  - snapshot and restore triggers are explicit
  - restore and rollback authority boundaries are explicit
  - a bounded rehearsal plan is defined
  - no readiness or later-stage workflow claim is added
- dependencies:
  - AIO-049
- status: completed

### Define feature-isolation and code-review contract for Codex-delivered changes
- id: AIO-052
- item_type: task
- title: Define feature-isolation and code-review contract for Codex-delivered changes
- details: define the maintainability contract for future Codex-delivered changes touching shared AIOffice control surfaces, including feature isolation, write-scope discipline, review expectations, and cross-project regression prevention
- objective: reduce maintainability and review risk before future control, UI, or integration work touches mixed shared files again
- owner_role: Project Orchestrator
- assigned_role: Architect
- milestone: M10 - Change Governance, Recovery, And Maintainability Hardening
- expected_artifact_path: projects/aioffice/governance/CODEX_CHANGE_ISOLATION_CONTRACT.md
- acceptance:
  - isolation and review expectations are explicit
  - shared-file risk handling is explicit
  - the contract stays narrow and does not imply new implementation behavior by itself
- dependencies:
  - AIO-049
- status: completed

### Re-anchor the authoritative M10 closeout checkpoint tag and snapshot branch
- id: AIO-053
- item_type: task
- title: Re-anchor the authoritative M10 closeout checkpoint tag and snapshot branch
- details: perform one narrow M10 closeout hygiene task so the externally reviewable checkpoint and snapshot anchors match the already-accepted M10 completion state without changing readiness, workflow proof, or post-M10 planning
- objective: make the accepted review anchor consistent with the committed M10 closeout truth while preserving the M9 anchors as historical references
- owner_role: Project Orchestrator
- assigned_role: Architect
- milestone: M10 - Change Governance, Recovery, And Maintainability Hardening
- expected_artifact_path: projects/aioffice/governance/ACTIVE_STATE.md
- acceptance:
  - `ACTIVE_STATE.md` points to dedicated `M10` closeout checkpoint and snapshot refs
  - `DECISION_LOG.md` records the re-anchoring as checkpoint hygiene only
  - `KANBAN.md` records `AIO-053` as completed without ratifying `M11`
  - the final closeout commit, new tag, and new snapshot branch all resolve to the same commit
- dependencies:
  - AIO-050
  - AIO-051
  - AIO-052
- status: completed

### Reconcile RECOVERY_AND_ROLLBACK_CONTRACT.md to post-M10 closeout truth
- id: AIO-054
- item_type: task
- title: Reconcile RECOVERY_AND_ROLLBACK_CONTRACT.md to post-M10 closeout truth
- details: perform one narrow post-AIO-053 reconciliation task so the recovery contract's current committed reality and checkpoint examples match the already-accepted post-M10 closeout state without changing scope, rehearsal status, readiness posture, or workflow-proof boundaries
- objective: keep the recovery contract aligned with the accepted M10 closeout review anchor without introducing new recovery functionality or broader milestone planning
- owner_role: Project Orchestrator
- assigned_role: Architect
- milestone: M10 - Change Governance, Recovery, And Maintainability Hardening
- expected_artifact_path: projects/aioffice/governance/RECOVERY_AND_ROLLBACK_CONTRACT.md
- acceptance:
  - `RECOVERY_AND_ROLLBACK_CONTRACT.md` reflects post-M10 closeout truth consistently with `ACTIVE_STATE.md`
  - rehearsal remains planned and not executed
  - explicit non-claims remain intact
  - no readiness, workflow-proof, or post-M10 planning inflation is introduced
- dependencies:
  - AIO-053
- status: completed

### Record post-M10 recovery-first priority review and ratify M11
- id: AIO-055
- item_type: task
- title: Record post-M10 recovery-first priority review and ratify M11
- details: record the accepted post-`M10` recovery-first priority order in the authoritative planning surfaces, ratify `M11` as the next conservative slice, and seed only the minimum recovery-discipline tasks required to begin operationalization
- objective: make recovery discipline the explicit next milestone theme before protected-surface enforcement or workflow breadth increase control-surface blast radius
- owner_role: Project Orchestrator
- assigned_role: QA
- milestone: M11 - Recovery Discipline Operationalization
- expected_artifact_path: projects/aioffice/governance/M10_RECOVERY_PRIORITY_REVIEW.md
- acceptance:
  - the review artifact uses committed repo truth only plus the accepted review direction
  - exactly one next conservative slice is ratified
  - later priorities are recorded directionally without ratifying later milestones
  - readiness and workflow-proof boundaries remain unchanged
- dependencies:
  - AIO-054
- status: completed

### Implement recovery checkpoint naming, snapshot manifest, and recovery preflight discipline
- id: AIO-056
- item_type: task
- title: Implement recovery checkpoint naming, snapshot manifest, and recovery preflight discipline
- details: implement the bounded recovery-discipline layer that makes checkpoint naming, snapshot packaging, and recovery preflight checks explicit over the accepted `M10` closeout reality without widening workflow proof or readiness claims
- objective: make checkpoint identity and recovery preconditions more real before backup, restore, and rollback behavior is hardened further
- owner_role: Project Orchestrator
- assigned_role: Architect
- milestone: M11 - Recovery Discipline Operationalization
- expected_artifact_path: sessions/store.py
- acceptance:
  - checkpoint naming and snapshot manifest expectations are enforceable in the accepted repo reality
  - recovery preflight checks are explicit and fail-closed
  - no readiness or workflow-proof inflation is introduced
- dependencies:
  - AIO-055
- status: completed

### Harden backup, restore, and rollback routines over the accepted M10 checkpoint reality
- id: AIO-057
- item_type: task
- title: Harden backup, restore, and rollback routines over the accepted M10 checkpoint reality
- details: harden the existing backup, restore, and rollback routines so they fit the accepted `M10` closeout anchor, recovery contract, and bounded repo reality without widening workflow scope
- objective: make the current recovery path more reliable and reviewable before any broader control-surface work increases blast radius
- owner_role: Project Orchestrator
- assigned_role: Architect
- milestone: M11 - Recovery Discipline Operationalization
- expected_artifact_path: sessions/store.py
- acceptance:
  - backup, restore, and rollback routines align with the accepted checkpoint reality
  - fail-closed verification boundaries remain explicit
  - no UI, readiness, or later-stage workflow claim is added
- dependencies:
  - AIO-056
- status: completed

### Rehearse bounded restore and rollback against the accepted M10 closeout anchor and record evidence
- id: AIO-058
- item_type: task
- title: Rehearse bounded restore and rollback against the accepted M10 closeout anchor and record evidence
- details: execute one bounded restore and rollback rehearsal against the accepted `M10` closeout anchor, then record what the recovery discipline proved and what still remains manual or unproven
- objective: prove the recovery-discipline slice in practice without changing readiness or widening live workflow proof
- owner_role: Project Orchestrator
- assigned_role: QA
- milestone: M11 - Recovery Discipline Operationalization
- expected_artifact_path: projects/aioffice/artifacts/M11_RECOVERY_REHEARSAL.md
- acceptance:
  - one bounded restore and rollback rehearsal is executed against the accepted closeout anchor
  - evidence is recorded factually
  - residual manual glue and remaining limits are explicit
  - no readiness or later-stage workflow overclaim is made
- dependencies:
  - AIO-057
- status: completed

### Implement bounded rollback execution over a verified recovery package
- id: AIO-057A
- item_type: task
- title: Implement bounded rollback execution over a verified recovery package
- details: add the narrowest lawful rollback execution routine needed so later bounded rehearsal can prove actual rollback execution rather than rollback preparation only
- objective: close the rollback-execution implementation gap exposed by the current committed `AIO-058` evidence without broadening beyond bounded recovery work
- owner_role: Project Orchestrator
- assigned_role: Architect
- milestone: M11 - Recovery Discipline Operationalization
- expected_artifact_path: sessions/store.py
- acceptance:
  - a bounded store-level rollback execution routine exists over a verified recovery package
  - rollback execution fails closed on target mismatch, anchor mismatch, or missing pre-action snapshot evidence
  - focused tests prove execution and at least one meaningful fail-closed path
  - no readiness or workflow-proof inflation is introduced
- dependencies:
  - AIO-057
- status: completed

### Rehearse bounded rollback execution and amend M11 recovery evidence
- id: AIO-058A
- item_type: task
- title: Rehearse bounded rollback execution and amend M11 recovery evidence
- details: execute one bounded rehearsal that exercises actual rollback execution over the corrected recovery path, then amend the committed `M11` recovery evidence so rollback execution proof is factual and explicit
- objective: close the remaining rollback-execution proof gap before the post-`M11` recovery review
- owner_role: Project Orchestrator
- assigned_role: QA
- milestone: M11 - Recovery Discipline Operationalization
- expected_artifact_path: projects/aioffice/artifacts/M11_RECOVERY_REHEARSAL.md
- acceptance:
  - one bounded rehearsal exercises rollback execution over a verified recovery package
  - the amended recovery evidence is factual about what was executed and what remains manual or unproven
  - readiness and workflow-proof boundaries remain unchanged
- dependencies:
  - AIO-057A
- status: completed

### Record post-M11 recovery discipline review and ratify the next conservative slice
- id: AIO-059
- item_type: task
- title: Record post-M11 recovery discipline review and ratify the next conservative slice
- details: produce one explicit post-`M11` review artifact grounded only in committed evidence, state what the recovery-discipline slice proved, what remains unproven, and ratify exactly one next conservative slice if the evidence supports it
- objective: keep the proof boundary explicit after `M11` and choose the next conservative slice without inflating readiness or widening workflow proof
- owner_role: Project Orchestrator
- assigned_role: QA
- milestone: M11 - Recovery Discipline Operationalization
- expected_artifact_path: projects/aioffice/governance/M11_RECOVERY_REVIEW.md
- acceptance:
  - the review uses committed evidence only
  - the proven and unproven recovery boundaries are explicit
  - exactly one next conservative slice is ratified only if the evidence supports it
  - readiness and workflow-proof boundaries remain unchanged
- dependencies:
  - AIO-058A
- status: completed

### Reconcile PRODUCT_CHANGE_GOVERNANCE.md to post-M11 truth and define enforceable protected core surface classes
- id: AIO-060
- item_type: task
- title: Reconcile PRODUCT_CHANGE_GOVERNANCE.md to post-M11 truth and define enforceable protected core surface classes
- details: reconcile the product-change governance artifact to post-`M11` truth and make the protected core product/state/governance surface classes explicit enough to support later fail-closed enforcement
- objective: define the exact protected surface classes that ordinary lanes must not mutate before workflow breadth expands
- owner_role: Project Orchestrator
- assigned_role: QA
- milestone: M12 - Protected Core Surfaces Enforcement
- expected_artifact_path: projects/aioffice/governance/PRODUCT_CHANGE_GOVERNANCE.md
- acceptance:
  - `PRODUCT_CHANGE_GOVERNANCE.md` reflects post-`M11` truth without widening substantive boundary law unnecessarily
  - protected core surface classes are explicit and enforceable in principle
  - readiness and workflow-proof boundaries remain unchanged
- dependencies:
  - AIO-059
- status: completed

## In Review

_No items_

## In Progress

_No items_

## Ready

_No items_

## Backlog

### Implement fail-closed blocking for protected core surfaces in ordinary mutation paths
- id: AIO-061
- item_type: task
- title: Implement fail-closed blocking for protected core surfaces in ordinary mutation paths
- details: implement the bounded fail-closed enforcement path that prevents ordinary mutation lanes from changing protected core product/state/governance surfaces in code
- objective: move protected-surface governance from review-only doctrine into explicit runtime blocking on the sanctioned mutation path
- owner_role: Project Orchestrator
- assigned_role: Architect
- milestone: M12 - Protected Core Surfaces Enforcement
- expected_artifact_path: sessions/store.py
- acceptance:
  - ordinary mutation paths fail closed on protected surface writes
  - protected surface enforcement composes with the current sanctioned mutation path rather than creating a parallel framework
  - readiness and workflow-proof boundaries remain unchanged
- dependencies:
  - AIO-060
- status: completed

### Rehearse blocked ordinary-lane attempts against a protected surface and record evidence
- id: AIO-062
- item_type: task
- title: Rehearse blocked ordinary-lane attempts against a protected surface and record evidence
- details: execute one bounded rehearsal showing that an ordinary lane is blocked from mutating a protected surface and record the resulting evidence without widening workflow proof
- objective: prove that protected-surface enforcement is real on the current sanctioned path before ratifying any later slice
- owner_role: Project Orchestrator
- assigned_role: QA
- milestone: M12 - Protected Core Surfaces Enforcement
- expected_artifact_path: projects/aioffice/artifacts/M12_PROTECTED_SURFACE_BLOCK_REHEARSAL.md
- acceptance:
  - one bounded blocked-attempt rehearsal is executed and recorded factually
  - the rehearsal shows fail-closed blocking on a protected surface
  - readiness and workflow-proof boundaries remain unchanged
- dependencies:
  - AIO-061
- status: completed

### Record post-M12 protected-surface enforcement review and ratify the next conservative slice
- id: AIO-063
- item_type: task
- title: Record post-M12 protected-surface enforcement review and ratify the next conservative slice
- details: produce one explicit post-`M12` review artifact grounded only in committed evidence, state what protected-surface enforcement proved, and ratify exactly one next conservative slice if the evidence supports it
- objective: close the protected-surface slice conservatively without widening readiness or workflow proof
- owner_role: Project Orchestrator
- assigned_role: QA
- milestone: M12 - Protected Core Surfaces Enforcement
- expected_artifact_path: projects/aioffice/governance/M12_PROTECTED_SURFACE_REVIEW.md
- acceptance:
  - the review uses committed evidence only
  - the protected-surface enforcement boundary and residual risks are explicit
  - exactly one next conservative slice is ratified only if the evidence supports it
- dependencies:
  - AIO-062
- status: backlog

## Open Planning Notes
- decide whether and when to mirror these tasks into the canonical SQLite task store
- record any blocker or deferred states explicitly instead of inventing silent transitions
- no post-`M12` milestone is ratified yet
