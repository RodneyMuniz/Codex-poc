# Program Kanban

This file is rendered from `sessions/studio.db`. Do not use it as the source of truth.

## Backlog

### Add queued worker orchestration with controlled concurrency limits
- ID: TGD-067
- Kind: request
- Status: backlog
- Owner: Architect
- Assigned Role: Developer
- Priority: high
- Requires Approval: yes
- Review State: None
- Milestone: M7 - Studio Foundations
- Expected Artifact: scripts/worker.py
- Details: Design a queued worker orchestration layer with explicit concurrency limits and controlled ownership. The first pass should support queue-backed delegation as an optional runtime path while preserving the current sequential fallback for safety and debugging.
- Review Notes: Migrated into M7 Studio Foundations on 2026-03-27. Keep in backlog until the event ledger lands.

### Add artifact lineage and dependency views to the control room
- ID: TGD-068
- Kind: request
- Status: backlog
- Owner: Dashboard Implementer
- Assigned Role: Developer
- Priority: medium
- Requires Approval: yes
- Review State: None
- Milestone: M7 - Studio Foundations
- Expected Artifact: scripts/operator_wall_snapshot.py
- Details: Add artifact lineage and dependency views to the control room so the operator can see what artifact was produced from what upstream input, task, or run. The first pass should stay grounded in canonical store evidence and avoid inventing lineage that the framework did not actually record.
- Review Notes: Migrated into M7 Studio Foundations on 2026-03-27. Lineage view stays downstream of the event truth work.

### Implement the design request preview and clarification gate
- ID: TGD-075
- Kind: request
- Status: backlog
- Owner: Project Orchestrator
- Assigned Role: Project Orchestrator
- Priority: high
- Requires Approval: yes
- Review State: None
- Milestone: M8 - Visual Production And Digital Asset Management
- Expected Artifact: agents/orchestrator.py
- Details: Add a chat-aligned design request packet so the Orchestrator can preview goal, target surface, style direction, deliverables, constraints, and open questions before generation starts. The design specialist should ask at most three blocking questions when critical information is missing.
- Review Notes: Moved into M8 Visual Production And Digital Asset Management on 2026-03-27.

### Add a Design Review gallery to the control room
- ID: TGD-077
- Kind: request
- Status: backlog
- Owner: Dashboard Implementer
- Assigned Role: Dashboard Implementer
- Priority: high
- Requires Approval: yes
- Review State: None
- Milestone: M8 - Visual Production And Digital Asset Management
- Expected Artifact: projects/program-kanban/app/app.js
- Details: Add a control-room gallery surface for design artifacts with project and task filters, thumbnail browsing, prompt summary, provenance, and selected-direction state. The gallery must be derived from canonical folder artifacts plus SQLite metadata instead of becoming a second source of truth.
- Review Notes: Moved into M8 Visual Production And Digital Asset Management on 2026-03-27.

### Add variant comparison, approval, and revision lineage for design artifacts
- ID: TGD-078
- Kind: request
- Status: backlog
- Owner: Product Designer / Workflow Planner
- Assigned Role: Product Designer / Workflow Planner
- Priority: high
- Requires Approval: yes
- Review State: None
- Milestone: M8 - Visual Production And Digital Asset Management
- Expected Artifact: projects/program-kanban/app/app.js
- Details: Make design review variant-first instead of file-first. Support side-by-side comparison for up to three variants, zoom, approve, reject, and revise-from-selected-variant actions while preserving lineage such as A, B, C, and B2.
- Review Notes: Moved into M8 Visual Production And Digital Asset Management on 2026-03-27.

### Add the OpenAI image-generation specialist runtime and provenance capture
- ID: TGD-080
- Kind: request
- Status: backlog
- Owner: Design Specialist Runtime Builder
- Assigned Role: Design Specialist Runtime Builder
- Priority: high
- Requires Approval: yes
- Review State: None
- Milestone: M8 - Visual Production And Digital Asset Management
- Expected Artifact: agents/sdk_specialists.py
- Details: Add a bounded design or artist specialist path that can call the current OpenAI image-generation workflow for concept exploration and iterative revisions. Persist model, provider, prompt summary, revised prompt, parent artifact, response identifiers, and output file metadata for each generated artifact.
- Review Notes: Moved into M8 Visual Production And Digital Asset Management on 2026-03-27.

### Implement canonical visual artifact storage, manifests, and SQLite indexing
- ID: TGD-076
- Kind: request
- Status: backlog
- Owner: Architect
- Assigned Role: Architect
- Priority: high
- Requires Approval: yes
- Review State: None
- Milestone: M8 - Visual Production And Digital Asset Management
- Expected Artifact: sessions/store.py
- Details: Add the first filesystem-backed storage model for generated or imported visual artifacts under projects/<project>/artifacts/design/, with SQLite keeping metadata only. Record prompt summary, provider, parent artifact, review state, selected direction, file paths, and file hashes.
- Review Notes: Retitled and moved into M8 on 2026-03-27.

### Implement approved visual artifact to implementation handoff
- ID: TGD-079
- Kind: request
- Status: backlog
- Owner: Architect
- Assigned Role: Architect
- Priority: high
- Requires Approval: yes
- Review State: None
- Milestone: M8 - Visual Production And Digital Asset Management
- Expected Artifact: agents/orchestrator.py
- Details: Make approved visual artifacts explicit inputs to later implementation tasks so code work references a chosen artifact id or path instead of relying on vague design intent. The bridge should preserve approval state and artifact lineage.
- Review Notes: Retitled and moved into M8 on 2026-03-27.

### Add a manual external visual-asset import lane
- ID: TGD-082
- Kind: request
- Status: backlog
- Owner: Dashboard Implementer
- Assigned Role: Dashboard Implementer
- Priority: medium
- Requires Approval: yes
- Review State: None
- Milestone: M8 - Visual Production And Digital Asset Management
- Expected Artifact: projects/program-kanban/app/server.mjs
- Details: Add the first controlled import path for visual artifacts created outside the generation runtime, such as exported mockups or curated image assets. The framework should ingest those files into the canonical visual-artifact folder structure and preserve provenance and review state.
- Review Notes: Retitled and moved into M8 on 2026-03-27.

### Add a deliverable contract schema for code, image, audio, map, review, and implementation handoff
- ID: TGD-084
- Kind: request
- Status: backlog
- Owner: Architect
- Assigned Role: Architect
- Priority: high
- Requires Approval: no
- Review State: None
- Milestone: M7 - Studio Foundations
- Expected Artifact: agents/schemas.py
- Details: Define the first explicit deliverable contract schema so the studio can reason about code, image, audio, map, review, and implementation-handoff outputs consistently. The first pass should clarify what metadata, provenance, review state, and downstream references each deliverable type must carry.
- Review Notes: Created during the approved M7-M11 board rewrite on 2026-03-27.

### Separate deterministic media services from AI specialist roles
- ID: TGD-085
- Kind: request
- Status: backlog
- Owner: Architect
- Assigned Role: Architect
- Priority: high
- Requires Approval: no
- Review State: None
- Milestone: M7 - Studio Foundations
- Expected Artifact: agents/orchestrator.py
- Details: Split media indexing, import bookkeeping, manifest generation, and review-state persistence away from AI specialist behavior. The first pass should make it clear which work is deterministic platform logic and which work belongs to delegated design or audio specialists.
- Review Notes: Created during the approved M7-M11 board rewrite on 2026-03-27.

### Add the Art Director critique loop and approval rubric
- ID: TGD-086
- Kind: request
- Status: backlog
- Owner: Art Director
- Assigned Role: Art Director
- Priority: high
- Requires Approval: no
- Review State: None
- Milestone: M8 - Visual Production And Digital Asset Management
- Expected Artifact: projects/program-kanban/governance/ART_DIRECTOR_REVIEW_CONTRACT.md
- Details: Define the first Art Director critique loop so visual concepts are reviewed against a clear rubric before implementation begins. The first pass should cover concept quality, readability, style fit, production feasibility, and operator-facing approval language.
- Review Notes: Created during the approved M7-M11 board rewrite on 2026-03-27.

### Add Technical Artist packaging and Phaser-ready manifest generation
- ID: TGD-087
- Kind: request
- Status: backlog
- Owner: Technical Artist
- Assigned Role: Technical Artist
- Priority: medium
- Requires Approval: no
- Review State: None
- Milestone: M8 - Visual Production And Digital Asset Management
- Expected Artifact: sessions/store.py
- Details: Define how approved visual assets become runtime-ready packages with anchors, layers, variant labels, and manifest metadata that the TacticsGame renderer can consume. The first pass should stay framework-owned and not assume final production-quality art.
- Review Notes: Created during the approved M7-M11 board rewrite on 2026-03-27.

### Add board and map concept review support
- ID: TGD-088
- Kind: request
- Status: backlog
- Owner: Art Director
- Assigned Role: Dashboard Implementer
- Priority: medium
- Requires Approval: no
- Review State: None
- Milestone: M8 - Visual Production And Digital Asset Management
- Expected Artifact: projects/program-kanban/app/app.js
- Details: Extend the visual review flow so board, terrain, and map concepts can be reviewed cleanly alongside HUD or unit-direction work. The first pass should make board-shape, terrain language, and map identity reviewable without pretending they are already runtime-ready.
- Review Notes: Created during the approved M7-M11 board rewrite on 2026-03-27.

### Implement the audio request preview and clarification gate
- ID: TGD-089
- Kind: request
- Status: backlog
- Owner: Project Orchestrator
- Assigned Role: Project Orchestrator
- Priority: high
- Requires Approval: no
- Review State: None
- Milestone: M9 - Audio Production Pipeline
- Expected Artifact: agents/orchestrator.py
- Details: Add an audio request preview so the Orchestrator can capture target surface, mood, asset type, runtime constraints, and references before generation or import begins. Audio specialists should ask at most three blocking questions when crucial information is missing.
- Review Notes: Created during the approved M7-M11 board rewrite on 2026-03-27.

### Implement canonical audio artifact storage and SQLite indexing
- ID: TGD-090
- Kind: request
- Status: backlog
- Owner: Architect
- Assigned Role: Architect
- Priority: high
- Requires Approval: no
- Review State: None
- Milestone: M9 - Audio Production Pipeline
- Expected Artifact: sessions/store.py
- Details: Add the first filesystem-backed audio artifact model so imported or generated sound assets land in canonical project folders while SQLite keeps metadata only. Track provenance, revision lineage, playback metadata, and selected direction without storing binary audio blobs in SQLite.
- Review Notes: Created during the approved M7-M11 board rewrite on 2026-03-27.

### Add an Audio Review surface with playback, approval, and revision lineage
- ID: TGD-091
- Kind: request
- Status: backlog
- Owner: Dashboard Implementer
- Assigned Role: Dashboard Implementer
- Priority: medium
- Requires Approval: no
- Review State: None
- Milestone: M9 - Audio Production Pipeline
- Expected Artifact: projects/program-kanban/app/app.js
- Details: Add a control-room audio review surface that supports playback, provenance, approval state, and revision lineage. The first pass should make short-form sound review practical without trying to replace full external audio editing tools.
- Review Notes: Created during the approved M7-M11 board rewrite on 2026-03-27.

### Add a manual external-audio import lane
- ID: TGD-092
- Kind: request
- Status: backlog
- Owner: Dashboard Implementer
- Assigned Role: Dashboard Implementer
- Priority: medium
- Requires Approval: no
- Review State: None
- Milestone: M9 - Audio Production Pipeline
- Expected Artifact: projects/program-kanban/app/server.mjs
- Details: Add the first controlled import path for curated sound effects, processed edits, and other audio assets created outside the generation runtime. The framework should ingest those files into the canonical audio folder structure and preserve provenance, review state, and later runtime references.
- Review Notes: Created during the approved M7-M11 board rewrite on 2026-03-27.

### Implement approved audio-to-runtime handoff
- ID: TGD-093
- Kind: request
- Status: backlog
- Owner: Architect
- Assigned Role: Architect
- Priority: medium
- Requires Approval: no
- Review State: None
- Milestone: M9 - Audio Production Pipeline
- Expected Artifact: sessions/store.py
- Details: Make approved audio artifacts explicit inputs to later runtime implementation tasks so playback, effects hooks, and manifest references point to chosen artifacts instead of vague intent. The first pass should preserve approval state, lineage, and runtime-facing metadata.
- Review Notes: Created during the approved M7-M11 board rewrite on 2026-03-27.

### Add breach pause behavior, local-exception approval, and compliance ledger
- ID: TGD-097
- Kind: request
- Status: backlog
- Owner: Project Orchestrator
- Assigned Role: Developer
- Priority: high
- Requires Approval: yes
- Review State: None
- Milestone: M7 - Studio Foundations
- Expected Artifact: sessions/store.py
- Details: Add immutable breach/compliance records, pause behavior for policy and budget violations, and a one-shot operator approval flow for rare framework-repair local exceptions.
- Review Notes: Created on 2026-03-27 as part of the M7 safeguard slice.

### Make Program Kanban surfaces compliance-aware
- ID: TGD-098
- Kind: request
- Status: backlog
- Owner: Dashboard Implementer
- Assigned Role: Dashboard Implementer
- Priority: medium
- Requires Approval: yes
- Review State: None
- Milestone: M7 - Studio Foundations
- Expected Artifact: projects/program-kanban/app/app.js
- Details: Expose execution mode, manifests, pause reasons, breach counts, and local-exception state in Program Kanban, the operator API, the wall snapshot, and the CLI so the operator can see enforcement truth directly.
- Review Notes: Created on 2026-03-27 as part of the M7 safeguard slice.

### Add the contract QA matrix for delegation drift and boundary enforcement
- ID: TGD-099
- Kind: request
- Status: backlog
- Owner: QA
- Assigned Role: QA
- Priority: high
- Requires Approval: no
- Review State: None
- Milestone: M7 - Studio Foundations
- Expected Artifact: tests/test_orchestrator.py
- Details: Prove the safeguard slice with tests that cover deterministic board actions, delegated worker runs, SDK runs, path violations, budget violations, local exceptions, and safe resume behavior.
- Review Notes: Created on 2026-03-27 as part of the M7 safeguard slice.

## Ready for Build

_No items_

## In Progress

_No items_

## In Review

_No items_

## Complete

### Define the canonical board workflow and visible columns for the new Program Kanban wall
- ID: TGD-030
- Kind: request
- Status: completed
- Owner: Project Orchestrator
- Assigned Role: Project Orchestrator
- Priority: high
- Requires Approval: yes
- Review State: Accepted
- Milestone: M1 - Basic Operation Level
- Details: Define the active board workflow for the new Program Kanban wall.

Target primary columns:
- Backlog
- Ready for Build
- In Progress
- In Review
- Complete

This task should settle the visible column model, state naming, and how secondary conditions such as blocked or deferred work are represented without confusing the main workflow.
- Result: Approved workflow columns and secondary state treatment are now captured in the M1 spec.
- Review Notes: Studio Lead approved the M1 decisions. See C:\Users\rodne\OneDrive\Documentos\_AIStudio_POC\projects\program-kanban\governance\M1_BASIC_OPERATION_SPEC_2026-03-21.md.

### Define Ready for Build completeness rules and transition gates
- ID: TGD-031
- Kind: request
- Status: completed
- Owner: Project Orchestrator
- Assigned Role: Project Orchestrator
- Priority: high
- Requires Approval: yes
- Review State: Accepted
- Milestone: M1 - Basic Operation Level
- Details: Define the exact requirements a task must satisfy before it can move from Backlog to Ready for Build.

Candidate gate areas:
- milestone assignment
- acceptance criteria
- responsible owner
- expected artifact or output
- blocker check
- review completeness for scope
- Result: Approved Ready for Build gates are now captured in the M1 spec.
- Review Notes: Studio Lead approved the M1 decisions. See C:\Users\rodne\OneDrive\Documentos\_AIStudio_POC\projects\program-kanban\governance\M1_BASIC_OPERATION_SPEC_2026-03-21.md.

### Define canonical milestone records and the orchestrator-led milestone planning cycle
- ID: TGD-032
- Kind: request
- Status: completed
- Owner: Project Orchestrator
- Assigned Role: Project Orchestrator
- Priority: high
- Requires Approval: yes
- Review State: Accepted
- Milestone: M1 - Basic Operation Level
- Details: Define how milestones exist in the current framework and how the orchestrator should help maintain them.

The first pass should cover:
- milestone identity and naming
- entry goals
- exit goals
- task membership
- operator review flow for milestone creation and updates
- Result: Approved canonical milestone model and planning-cycle direction are now captured in the M1 spec.
- Review Notes: Studio Lead approved the M1 decisions. See C:\Users\rodne\OneDrive\Documentos\_AIStudio_POC\projects\program-kanban\governance\M1_BASIC_OPERATION_SPEC_2026-03-21.md.

### Restore milestone view with grouped tasks, slim task rows, and percent completion
- ID: TGD-033
- Kind: request
- Status: completed
- Owner: Dashboard Implementer
- Assigned Role: Dashboard Implementer
- Priority: high
- Requires Approval: yes
- Review State: Accepted
- Milestone: M1 - Basic Operation Level
- Expected Artifact: projects/program-kanban/app/app.js
- Details: Restore a dedicated milestone view.

Requested outcome:
- separate milestone view accessible from the wall
- tasks grouped under milestones
- tasks shown as id plus name in this view
- visible percent completion per milestone
- milestone progress easy to scan during review
- Review Notes: Studio Lead reviewed the milestone view and accepted it as complete on 2026-03-23.

### Restore task-id click-to-copy in approved operator surfaces
- ID: TGD-034
- Kind: request
- Status: completed
- Owner: Dashboard Implementer
- Assigned Role: Dashboard Implementer
- Priority: medium
- Requires Approval: yes
- Review State: Accepted
- Milestone: M1 - Basic Operation Level
- Expected Artifact: projects/program-kanban/app/app.js
- Details: Restore click-to-copy for task ids in the new wall.

The first pass should confirm:
- which views support click-to-copy
- copied text format
- visible feedback after copy
- expected desktop and touch behavior
- Review Notes: Studio Lead reviewed click-to-copy behavior and accepted it as complete on 2026-03-23.

### Add top-level Board and Milestones navigation in the operator wall
- ID: TGD-035
- Kind: request
- Status: completed
- Owner: Product Designer / Workflow Planner
- Assigned Role: Product Designer / Workflow Planner
- Priority: high
- Requires Approval: yes
- Review State: Accepted
- Milestone: M1 - Basic Operation Level
- Details: Add explicit top-level navigation for the main Program Kanban wall.

The first pass should settle:
- board view presence
- milestone view presence
- navigation placement and labeling
- default landing view
- relation to the current evidence-heavy runtime surface
- Result: Approved top-level Board and Milestones navigation is now captured in the M1 spec.
- Review Notes: Studio Lead approved the M1 decisions. See C:\Users\rodne\OneDrive\Documentos\_AIStudio_POC\projects\program-kanban\governance\M1_BASIC_OPERATION_SPEC_2026-03-21.md.

### Add integrity validation for board state, milestone assignment, and completion closure
- ID: TGD-036
- Kind: request
- Status: completed
- Owner: Dashboard Implementer
- Assigned Role: Dashboard Implementer
- Priority: high
- Requires Approval: yes
- Review State: Accepted
- Milestone: M1 - Basic Operation Level
- Expected Artifact: scripts/operator_wall_snapshot.py
- Details: Define and later implement the first integrity checks for the new board model.

Candidate validation areas:
- Ready for Build tasks missing required planning fields
- tasks without milestone assignment where assignment is required
- completed work not actually reviewed and accepted
- milestone progress drift caused by task state mismatch
- Review Notes: Studio Lead reviewed the planning validation behavior and accepted it as complete on 2026-03-23.

### Reintroduce a lightweight recent-updates context panel in the new wall
- ID: TGD-037
- Kind: request
- Status: completed
- Owner: Dashboard Implementer
- Assigned Role: Dashboard Implementer
- Priority: medium
- Requires Approval: yes
- Review State: Accepted
- Milestone: M3 - Operator Clarity Recovery
- Expected Artifact: projects/program-kanban/app/app.js
- Details: Revisit the old recent-updates support surface and decide what belongs in the new board after M1 basic operation is stable.
- Result: Implemented a recent updates panel fed from task updates, approvals, runs, agent runs, validations, and artifacts.
- Review Notes: Accepted by Studio Lead after UI review.

### Reintroduce lightweight hierarchy cues for role clarity
- ID: TGD-038
- Kind: request
- Status: completed
- Owner: Project Orchestrator
- Assigned Role: Dashboard Implementer
- Priority: low
- Requires Approval: yes
- Review State: Accepted
- Milestone: M3 - Operator Clarity Recovery
- Expected Artifact: projects/program-kanban/app/styles.css
- Details: Revisit role and hierarchy visibility now that the wall is framework-backed and more evidence-driven than the legacy version.
- Result: Added subtle ownership cues through styled owner and assigned-role badges plus milestone role labels.
- Review Notes: Accepted by Studio Lead after UI review.

### Decide and implement scoped project filtering for multi-project board use
- ID: TGD-039
- Kind: request
- Status: completed
- Owner: Dashboard Implementer
- Assigned Role: Dashboard Implementer
- Priority: low
- Requires Approval: yes
- Review State: Accepted
- Milestone: M3 - Operator Clarity Recovery
- Expected Artifact: projects/program-kanban/app/app.js
- Details: Revisit project chip filtering and decide whether it belongs in the Program Kanban planning wall after M1 is stable.
- Result: Polished scoped project visibility with clearer scope metadata and all-project rollup cards.
- Review Notes: Accepted by Studio Lead after UI review.

### Add milestone filtering for completed or backlog-only milestones
- ID: TGD-040
- Kind: request
- Status: completed
- Owner: Product Designer / Workflow Planner
- Assigned Role: Dashboard Implementer
- Priority: low
- Requires Approval: yes
- Review State: Accepted
- Milestone: M3 - Operator Clarity Recovery
- Expected Artifact: projects/program-kanban/app/app.js
- Details: Revisit optional milestone filtering once the core milestone model and milestone view are stable.
- Result: Implemented milestone filters plus collapsible milestone headers and project-grouped milestone columns.
- Review Notes: Accepted by Studio Lead after UI review.

### Explore response-chip answers for orchestrator question flows
- ID: TGD-041
- Kind: request
- Status: completed
- Owner: Orchestrator
- Assigned Role: Dashboard Implementer
- Priority: low
- Requires Approval: yes
- Review State: Accepted
- Milestone: M4 - Later Extensions
- Expected Artifact: projects/program-kanban/app/app.js
- Details: Revisit optional response chips after the basic board and milestone planning flows are operating cleanly again.
- Result: Closed as no longer necessary after the chat-first operating model.
- Review Notes: Closed as no longer necessary after the chat-first Orchestrator and control-room split.

### Plan workspace-level multi-project rollup after single-project flow is stable
- ID: TGD-042
- Kind: request
- Status: completed
- Owner: Workflow Systems Planner
- Assigned Role: Workflow Systems Planner
- Priority: low
- Requires Approval: yes
- Review State: Accepted
- Milestone: M4 - Later Extensions
- Expected Artifact: scripts/operator_wall_snapshot.py
- Details: Revisit safe multi-project aggregation only after the Program Kanban board is trustworthy on its own.
- Result: Added an all-project workspace rollup with per-project counts, milestone totals, root paths, and quick-open actions.
- Review Notes: Accepted by Studio Lead after UI review.

### Evaluate file-watch refresh after basic operation stabilizes
- ID: TGD-043
- Kind: request
- Status: completed
- Owner: Dashboard Implementer
- Assigned Role: Dashboard Implementer
- Priority: low
- Requires Approval: yes
- Review State: Accepted
- Milestone: M4 - Later Extensions
- Expected Artifact: projects/program-kanban/app/app.js
- Details: Keep file-watch or auto-refresh evaluation out of M1 and revisit it only after the basic board is trusted.
- Result: Replaced forced polling with Refresh Now plus an optional persisted auto-refresh toggle.
- Review Notes: Accepted by Studio Lead after UI review.

### Evaluate richer cross-linking after the new board model settles
- ID: TGD-044
- Kind: request
- Status: completed
- Owner: Dashboard Implementer
- Assigned Role: Dashboard Implementer
- Priority: low
- Requires Approval: yes
- Review State: Accepted
- Milestone: M4 - Later Extensions
- Expected Artifact: projects/program-kanban/app/app.js
- Details: Keep richer linking out of the basic board reset and revisit it only after core operator flow is stable.
- Result: Added task evidence links into an in-page Evidence Spotlight for latest run, artifact, and validation details.
- Review Notes: Accepted by Studio Lead after UI review.

### Implement the approved board workflow columns and secondary state treatment
- ID: TGD-045
- Kind: request
- Status: completed
- Owner: Dashboard Implementer
- Assigned Role: Dashboard Implementer
- Priority: high
- Requires Approval: yes
- Review State: Accepted
- Milestone: M1 - Basic Operation Level
- Expected Artifact: projects/program-kanban/app/styles.css
- Details: Implement the approved primary board workflow.

Required outcome:
- visible columns are Backlog, Ready for Build, In Progress, In Review, and Complete
- Blocked and Deferred are treated as secondary states rather than primary columns
- the live wall reflects the approved workflow names and ordering
- Review Notes: Studio Lead accepted the ultrawide layout revision on 2026-03-23.

### Implement first-class milestone records and single-milestone task linkage
- ID: TGD-046
- Kind: request
- Status: completed
- Owner: Dashboard Implementer
- Assigned Role: Dashboard Implementer
- Priority: high
- Requires Approval: yes
- Review State: Accepted
- Milestone: M1 - Basic Operation Level
- Expected Artifact: sessions/store.py
- Details: Implement the first-pass milestone model.

Required outcome:
- milestones become first-class canonical records in SQLite
- each task links to exactly one milestone in the first pass
- milestone records carry id, title, entry goal, exit goal, order, and status
- Review Notes: Studio Lead reviewed milestone records and task linkage and accepted them as complete on 2026-03-23.

### Enforce Ready for Build gates in canonical task transitions and validation surfaces
- ID: TGD-047
- Kind: request
- Status: completed
- Owner: Dashboard Implementer
- Assigned Role: Dashboard Implementer
- Priority: high
- Requires Approval: yes
- Review State: Accepted
- Milestone: M1 - Basic Operation Level
- Expected Artifact: sessions/store.py
- Details: Implement Ready for Build gate enforcement.

Required outcome:
- tasks cannot move to Ready for Build unless all approved planning fields exist
- missing required planning fields are visible to the operator
- completion closure remains tied to review acceptance
- Review Notes: Studio Lead accepted Ready for Build gate enforcement on 2026-03-23.

### Define and review the M2 operator-client trust boundary and proof criteria
- ID: TGD-048
- Kind: request
- Status: completed
- Owner: Project Orchestrator
- Assigned Role: Project Orchestrator
- Priority: medium
- Requires Approval: yes
- Review State: Accepted
- Milestone: M2 - Operator Client And Traceable Delegation
- Expected Artifact: projects/program-kanban/governance/M2_OPERATOR_CLIENT_SPEC_2026-03-21.md
- Details: Capture the minimum operator-client requirements needed to stop depending on this Codex thread as the production orchestration surface.

The output must define the operator surfaces, trace expectations, trust rules, and proof scenario for the first client milestone.
- Review Notes: Studio Lead accepted the M2 operator-client spec and the recommended requirement defaults on 2026-03-23.

### Add operator-client request intake and dispatch confirmation flow
- ID: TGD-049
- Kind: request
- Status: completed
- Owner: Dashboard Implementer
- Assigned Role: Dashboard Implementer
- Priority: high
- Requires Approval: yes
- Review State: Accepted
- Milestone: M2 - Operator Client And Traceable Delegation
- Expected Artifact: projects/program-kanban/app/app.js
- Details: Build the Program Kanban app surface where the Studio Lead can enter a natural-language request, see the Orchestrator interpretation, answer clarifying questions, and confirm dispatch before work starts.
- Result: Built an operator-facing Orchestrator tab with request intake, preview, and dispatch confirmation.
- Review Notes: Accepted as optional web dispatch. The Program Kanban app is no longer required to be the primary conversational client.

### Add operator actions API for request, approval, rejection, and resume
- ID: TGD-050
- Kind: request
- Status: completed
- Owner: Orchestration Runtime Implementer
- Assigned Role: Orchestration Runtime Implementer
- Priority: high
- Requires Approval: yes
- Review State: Accepted
- Milestone: M2 - Operator Client And Traceable Delegation
- Expected Artifact: projects/program-kanban/app/server.mjs
- Details: Extend the Program Kanban server layer so the operator client can create requests, confirm dispatch, approve or reject pauses, and resume runs without dropping into the CLI.
- Result: Added operator actions API endpoints for preview, dispatch, approve, reject, resume, and run inspection.
- Review Notes: Accepted by Studio Lead without further manual validation; capability acknowledged as present in the framework.

### Persist the orchestration trace ledger and structured handoff packets
- ID: TGD-051
- Kind: request
- Status: completed
- Owner: Workflow Systems Planner
- Assigned Role: Workflow Systems Planner
- Priority: high
- Requires Approval: yes
- Review State: Accepted
- Milestone: M2 - Operator Client And Traceable Delegation
- Expected Artifact: sessions/store.py
- Details: Extend the canonical store so the semantic handoff chain is visible as structured events and packets, not just inferred from task status or agent run records.
- Result: Persisted a structured trace ledger in the canonical store and exposed it in run evidence.
- Review Notes: Accepted by Studio Lead without further manual validation; capability acknowledged as present in the framework.

### Add a run inspector for trace, delegation, artifacts, validation, and final summary
- ID: TGD-052
- Kind: request
- Status: completed
- Owner: Dashboard Implementer
- Assigned Role: Dashboard Implementer
- Priority: high
- Requires Approval: yes
- Review State: Accepted
- Milestone: M2 - Operator Client And Traceable Delegation
- Expected Artifact: projects/program-kanban/app/app.js
- Details: Create an operator-facing run detail view so the Studio Lead can audit what happened in a run without using ad hoc SQL or raw CLI output.
- Result: Added a run inspector with trace events, delegations, artifacts, validations, and final summary visibility.
- Review Notes: Accepted by Studio Lead without further manual validation; capability acknowledged as present in the framework.

### Expose role profiles, model routing, and skill metadata in operator views
- ID: TGD-053
- Kind: request
- Status: completed
- Owner: Workflow Systems Planner
- Assigned Role: Workflow Systems Planner
- Priority: medium
- Requires Approval: yes
- Review State: Accepted
- Milestone: M2 - Operator Client And Traceable Delegation
- Expected Artifact: scripts/operator_wall_snapshot.py
- Details: Make the route explainable by showing which role, model, and skills were used for each handoff and why that route was chosen at a short summary level.
- Result: Exposed role profiles, model routing, route reasons, and profile-skill metadata in the operator client.
- Review Notes: Accepted by Studio Lead without further manual validation; capability acknowledged as present in the framework.

### Prove an end-to-end app-driven orchestration run that bypasses chat dependence
- ID: TGD-054
- Kind: request
- Status: completed
- Owner: QA
- Assigned Role: QA
- Priority: medium
- Requires Approval: yes
- Review State: Accepted
- Milestone: M2 - Operator Client And Traceable Delegation
- Expected Artifact: projects/program-kanban/artifacts/m2_operator_client_proof.json
- Details: Run a real proof scenario from the Program Kanban app so the request, approvals, trace, artifacts, validation, and final summary all come from the operator client rather than this thread.
- Result: Completed an app-driven proof run and wrote the evidence packet to projects/program-kanban/artifacts/m2_operator_client_proof.json.
- Review Notes: Historical proof artifact retained, but app-only orchestration is no longer the gating operating model for future validation.

### Create an offline one-click launcher page for Program Kanban and TacticsGame
- ID: TGD-055
- Kind: request
- Status: completed
- Owner: Dashboard Implementer
- Assigned Role: Dashboard Implementer
- Priority: high
- Requires Approval: yes
- Review State: Accepted
- Milestone: M1 - Basic Operation Level
- Expected Artifact: projects/program-kanban/app/offline-launcher.html
- Details: Create a local launcher page inside the Program Kanban folder structure so the Studio Lead can bring both apps online without asking Codex to do it manually.

The first pass should feel intentional and pleasant to use, not like a bare placeholder admin page.

Important constraint: a normal offline HTML file in a browser cannot directly start local processes for security reasons, so the build must pair the page with a supported local helper mechanism such as a PowerShell or command wrapper, a tiny local launcher endpoint, or a desktop-style wrapper.
- Review Notes: Studio Lead accepted the launcher flow on 2026-03-23. The launcher supports helper-mode cold start plus browser-mode status, logs, and command access from the bookmarked page.

### Show board-column status badges in milestone task rows
- ID: TGD-056
- Kind: request
- Status: completed
- Owner: Dashboard Implementer
- Assigned Role: Dashboard Implementer
- Priority: medium
- Requires Approval: yes
- Review State: Accepted
- Milestone: M1 - Basic Operation Level
- Expected Artifact: projects/program-kanban/app/app.js
- Details: Update the milestone view so each task row shows its current primary board-column status, such as Backlog, Ready for Build, In Progress, In Review, or Complete.
- Review Notes: Studio Lead accepted milestone task-row board status badges on 2026-03-23.

### Add the official Agents SDK dependency and an isolated runtime adapter path
- ID: TGD-057
- Kind: request
- Status: completed
- Owner: QA
- Assigned Role: Developer
- Priority: high
- Requires Approval: yes
- Review State: Accepted
- Milestone: M5 - SDK-Native Runtime Migration
- Expected Artifact: agents/sdk_runtime.py
- Details: The first pass should update dependencies, add a new runtime adapter module, and prove the framework can instantiate an SDK-native execution path behind a feature flag or equivalent routing decision.
- Result: Accepted by Studio Lead.
- Review Notes: Accepted by Studio Lead after specialist-only SDK review.

### Implement shared SDK specialist-session support without creating a second Orchestrator role
- ID: TGD-058
- Kind: request
- Status: completed
- Owner: QA
- Assigned Role: Architect
- Priority: high
- Requires Approval: yes
- Review State: Accepted
- Milestone: M5 - SDK-Native Runtime Migration
- Expected Artifact: agents/sdk_orchestrator.py
- Details: This task should create an SDK-native Orchestrator implementation, use shared session support for the thread or run, and keep the Orchestrator as the manager instead of handing the conversation away to specialists.
- Result: Accepted by Studio Lead.
- Review Notes: Accepted by Studio Lead after specialist-only SDK review.

### Implement direct specialist delegation through SDK-native bounded agent calls
- ID: TGD-059
- Kind: request
- Status: completed
- Owner: QA
- Assigned Role: Developer
- Priority: high
- Requires Approval: yes
- Review State: Accepted
- Milestone: M5 - SDK-Native Runtime Migration
- Expected Artifact: agents/sdk_pm.py
- Details: The preferred pattern is agents-as-tools or equivalently bounded SDK-native delegation, not unrestricted conversational handoff. This task begins after the SDK runtime adapter and manager agent exist.
- Result: Accepted by Studio Lead.
- Review Notes: Accepted by Studio Lead after specialist-only SDK review.

### Bridge SDK human-in-the-loop pauses and resumes into the canonical approval model for specialist delegation
- ID: TGD-060
- Kind: request
- Status: completed
- Owner: QA
- Assigned Role: Developer
- Priority: high
- Requires Approval: yes
- Review State: Accepted
- Milestone: M5 - SDK-Native Runtime Migration
- Expected Artifact: scripts/operator_api.py
- Details: This pass should map SDK-native human-in-the-loop events into the canonical approvals table and allow the control room to approve or resume the migrated path without dropping existing safety rules.
- Result: Accepted by Studio Lead.
- Review Notes: Accepted by Studio Lead after final SDK approval bridge and evidence review.

### Mirror SDK traces and session evidence into the SQLite control store and run inspector
- ID: TGD-061
- Kind: request
- Status: completed
- Owner: QA
- Assigned Role: Developer
- Priority: high
- Requires Approval: yes
- Review State: Accepted
- Milestone: M5 - SDK-Native Runtime Migration
- Expected Artifact: sessions/store.py
- Details: This task should map the migrated SDK runtime trace and session information into the existing run inspector, trace ledger, and evidence surfaces without requiring raw SDK internals in the UI.
- Result: Accepted by Studio Lead.
- Review Notes: Accepted by Studio Lead after final SDK approval bridge and evidence review.

### Preserve deterministic board-control actions outside the agent runtime and route only generative work into the SDK path
- ID: TGD-062
- Kind: request
- Status: completed
- Owner: QA
- Assigned Role: Architect
- Priority: medium
- Requires Approval: yes
- Review State: Accepted
- Milestone: M5 - SDK-Native Runtime Migration
- Expected Artifact: agents/orchestrator.py
- Details: This task should formalize routing boundaries so direct board actions remain handled by framework code, while generative planning or specialist work can use the SDK-native runtime path.
- Result: Accepted by Studio Lead.
- Review Notes: Accepted by Studio Lead after specialist-only SDK review.

### Prove a chat-led Orchestrator flow that delegates to SDK specialists and is fully visible in the control room
- ID: TGD-063
- Kind: request
- Status: completed
- Owner: QA
- Assigned Role: QA
- Priority: high
- Requires Approval: yes
- Review State: Accepted
- Milestone: M5 - SDK-Native Runtime Migration
- Expected Artifact: projects/program-kanban/artifacts/m5_sdk_runtime_proof.json
- Details: The proof should start from chat or the chat-bridged orchestration entry point, use the SDK-native runtime, pause at approval if required, and export a canonical evidence packet for review.
- Result: Accepted by Studio Lead.
- Review Notes: Accepted by Studio Lead after specialist-only SDK review.

### Add one-click restore for SQLite safety backups in the control room
- ID: TGD-064
- Kind: request
- Status: completed
- Owner: Project Orchestrator
- Assigned Role: Developer
- Priority: high
- Requires Approval: yes
- Review State: Accepted
- Milestone: M6 - Trust, Restore, And Operator Speed
- Expected Artifact: projects/program-kanban/app/app.js
- Details: Add a restore flow in the control room for the existing SQLite safety backups. The flow should make restore choices visible, require explicit confirmation, create a fresh pre-restore safety backup, and report the outcome clearly so the operator can recover confidently without dropping into manual file work.
- Result: Control room now lists recorded SQLite safety backups, supports one-click restore with confirmation, creates a fresh pre-restore safety backup, and writes a restore receipt.
- Review Notes: Accepted by Studio Lead after control-room restore review.

### Turn the run inspector into a visual orchestration timeline
- ID: TGD-069
- Kind: request
- Status: completed
- Owner: Orchestrator
- Assigned Role: Design
- Priority: high
- Requires Approval: yes
- Review State: Accepted
- Milestone: M6 - Trust, Restore, And Operator Speed
- Expected Artifact: projects/program-kanban/app/app.js
- Details: Upgrade the current run inspector from a mostly list-based inspection surface into a visual orchestration timeline. The first pass should make approvals, specialist work, validations, and final summary transitions easier to scan while preserving access to the underlying evidence details.
- Result: Run Inspector now includes a visual orchestration timeline built from approvals, trace events, specialist runs, artifacts, and validations.
- Review Notes: Implementation ready for Studio Lead review of the timeline readability and sequencing.

### Visually distinguish deterministic framework actions from AI-delegated actions
- ID: TGD-070
- Kind: request
- Status: completed
- Owner: Orchestrator
- Assigned Role: Design
- Priority: high
- Requires Approval: yes
- Review State: Accepted
- Milestone: M6 - Trust, Restore, And Operator Speed
- Expected Artifact: projects/program-kanban/app/app.js
- Details: Add a consistent visual treatment that clearly distinguishes deterministic framework actions from AI-delegated actions across run-inspection surfaces. The operator should not need to read deep trace text to understand what was code-driven versus model-driven.
- Result: Control-room run surfaces now visually distinguish deterministic framework actions from AI-delegated specialist actions.
- Review Notes: Implementation ready for Studio Lead review of provenance clarity across approvals, timeline, and trace cards.

### Add board density modes optimized for ultrawide review
- ID: TGD-071
- Kind: request
- Status: completed
- Owner: Product Designer / Workflow Planner
- Assigned Role: Design
- Priority: medium
- Requires Approval: yes
- Review State: Accepted
- Milestone: M6 - Trust, Restore, And Operator Speed
- Expected Artifact: projects/program-kanban/app/styles.css
- Details: Add operator-selectable board density modes for compact, normal, and detailed review. The first pass should be explicitly tuned for ultrawide use while preserving acceptable behavior on smaller screens and remembering the local preference across refreshes.
- Result: Board now supports compact, normal, and detailed density modes persisted in local browser storage for ultrawide review.
- Review Notes: Accepted by Studio Lead after density-mode review.

### Enrich approval cards with upstream and downstream context
- ID: TGD-072
- Kind: request
- Status: completed
- Owner: Product Designer / Workflow Planner
- Assigned Role: Design
- Priority: medium
- Requires Approval: yes
- Review State: Accepted
- Milestone: M6 - Trust, Restore, And Operator Speed
- Expected Artifact: projects/program-kanban/app/app.js
- Details: Improve approval cards so they explain why the approval is being requested, what upstream work led to it, and what downstream step is expected after approval. The first pass should stay compact enough for repeated daily use instead of turning approval review into a full report-reading exercise.
- Result: Approval cards now include upstream and downstream context, including exact task, why-now context, latest signals, and expected continuation.
- Review Notes: Implementation ready for Studio Lead review of approval readability and decision context.
Accepted by Studio Lead on 2026-03-27 after control-room review.

### Add a persistent system health strip to the control room
- ID: TGD-073
- Kind: request
- Status: completed
- Owner: Project Orchestrator
- Assigned Role: Developer
- Priority: high
- Requires Approval: yes
- Review State: Accepted
- Milestone: M6 - Trust, Restore, And Operator Speed
- Expected Artifact: projects/program-kanban/app/app.js
- Details: Add a persistent system health strip to the control room that shows the most important runtime signals at a glance. The first pass should include runtime mode, last backup, last run, pending approvals, and store-health context without becoming a noisy dashboard.
- Result: The control room now exposes a persistent system health strip with runtime mode, last backup, last run, pending approvals, and store health.
- Review Notes: Accepted by Studio Lead after health-strip review.

### Review the visual pipeline contract and design review operating model baseline
- ID: TGD-074
- Kind: request
- Status: completed
- Owner: Project Orchestrator
- Assigned Role: Project Orchestrator
- Priority: high
- Requires Approval: yes
- Review State: Accepted
- Milestone: M8 - Visual Production And Digital Asset Management
- Expected Artifact: projects/program-kanban/governance/M7_IMAGE_ASSET_PIPELINE_AND_DESIGN_REVIEW_SPEC_2026-03-26.md
- Details: Review the baseline contract that defines chat-first visual intake, bounded clarification, canonical artifact storage on disk, SQLite metadata indexing, and control-room review. This completed governance task now serves as the predecessor planning receipt for the later M8 visual-production milestone after the studio ladder rewrite.
- Result: Visual pipeline operating contract approved as the planning baseline. No runtime implementation shipped in this task.
- Review Notes: Drafted from architect and design review plus current official OpenAI image and agent guidance.
Accepted by Studio Lead on 2026-03-27 as a governance/planning checkpoint. The task approves the M7 contract; implementation remains in follow-on tasks. Re-contextualized under M8 after the studio milestone ladder rewrite on 2026-03-27.

### Restore canonical runtime store and operator control API alignment
- ID: TGD-094
- Kind: request
- Status: completed
- Owner: Architect
- Assigned Role: Architect
- Priority: high
- Requires Approval: yes
- Review State: Accepted
- Milestone: M7 - Studio Foundations
- Expected Artifact: sessions/store.py
- Details: Bring SessionStore, operator API, CLI, and control-room snapshot back onto the same canonical runtime surface so the studio can enforce contract truth from one place instead of drifting across mismatched helpers.
- Result: Completed for the narrowed safeguard scope on 2026-03-27: canonical store/import/CLI/snapshot alignment restored and verified through delegated implementation, targeted tests, and manual Program Kanban snapshot smokes. Broader Orchestrator compatibility remains intentionally out of scope for later safeguard tasks.
- Review Notes: Created on 2026-03-27 as the first M7 safeguard task after repeated Orchestrator delegation-contract breaches.

Closed on 2026-03-27 after delegated implementation and QA for the narrowed safeguard scope only. Scope covered canonical store/import/CLI/snapshot alignment; later Orchestrator compatibility remains out of scope.

### Freeze the Orchestrator delegation contract and execution-mode policy
- ID: TGD-095
- Kind: request
- Status: completed
- Owner: Project Orchestrator
- Assigned Role: Architect
- Priority: high
- Requires Approval: yes
- Review State: Accepted
- Milestone: M7 - Studio Foundations
- Expected Artifact: agents/config.py
- Details: Define the runtime execution modes, deterministic-local boundary, delegation thresholds, and the narrow approved-local-exception rule so Orchestrator and PM cannot silently drift into implementation.
- Result: Completed for the approved safeguard scope on 2026-03-27: runtime mode policy, deterministic board-action routing, preview/dispatch/resume compatibility, and PM dispatch-approval behavior are implemented and QA-passed. Worker-only write enforcement remains intentionally deferred to TGD-096.
- Review Notes: Created on 2026-03-27 as part of the M7 safeguard slice.

Started delegated execution on 2026-03-27 with Architect-defined contract and parallel worker ownership split across orchestrator/config and PM.

Moved to in review on 2026-03-27 after delegated implementation and QA PASS for the approved TGD-095 scope. TGD-096 planning started, but implementation remains blocked.

Closed on 2026-03-27 after delegated implementation and QA PASS for the approved TGD-095 scope. Worker-only write enforcement remains deferred to TGD-096.

### Enforce worker-only implementation with sealed write-scope manifests
- ID: TGD-096
- Kind: request
- Status: completed
- Owner: Project Orchestrator
- Assigned Role: Developer
- Priority: high
- Requires Approval: yes
- Review State: Accepted
- Milestone: M7 - Studio Foundations
- Expected Artifact: agents/orchestrator.py
- Details: Block local implementation for delegated work unless a run carries a sealed manifest defining role, allowed paths, expected outputs, and write scope. Out-of-scope writes must fail closed.
- Result: Completed for the approved safeguard scope on 2026-03-28: PM now issues sealed manifests, delegated artifact work flows through the worker boundary, and worker/tools enforce exact-path fail-closed write scope. Breach ledger and compliance surfacing remain intentionally deferred to TGD-097+.
- Review Notes: Created on 2026-03-27 as part of the M7 safeguard slice.

Started delegated execution on 2026-03-27 with disjoint worker ownership across orchestrator/pm and worker/tools for sealed write-scope manifest enforcement.

Moved to in review on 2026-03-28 after delegated implementation and QA PASS for the approved TGD-096 scope. Breach ledger and compliance surfacing remain downstream in TGD-097+.

Closed on 2026-03-28 after delegated implementation and QA PASS for the approved TGD-096 scope. Breach ledger and compliance surfacing remain deferred to TGD-097+.

## Blocked

### Add a first-class immutable runtime event ledger separate from summary messages
- ID: TGD-065
- Status: blocked
- Secondary State: blocked
- Owner: Architect
- Details: Design and implement a dedicated runtime event ledger separate from the current summary-style message stream. The ledger should preserve immutable execution facts that later control-room views can trust for replay, auditing, and analytics without reconstructing history from mixed commentary.

### Add a role and capability registry to remove hardcoded planning assumptions
- ID: TGD-066
- Status: blocked
- Secondary State: blocked
- Owner: Architect
- Details: Replace scattered project-shaped planning assumptions with an explicit role and capability registry. The first pass should let planning and orchestration helpers route by deliverable type and specialist capability instead of baking assumptions into a fixed project template path.

### Define the large-media storage policy for generated images, source files, and audio
- ID: TGD-081
- Status: blocked
- Secondary State: blocked
- Owner: Architect
- Details: Set the first storage policy for generated review images, exported deliverables, larger editable source files, and audio assets so the repo does not drift into uncontrolled binary growth. This should define what stays in repo, what stays optional, when Git LFS becomes necessary, and what metadata must always remain in the canonical store.

### Add Orchestrator context receipts and restore-safe compaction
- ID: TGD-083
- Status: blocked
- Secondary State: blocked
- Owner: Project Orchestrator
- Details: Add structured context receipts so the Orchestrator can preserve the current decision frame, accepted assumptions, open questions, and next-step contract across long-running conversations and restore events. The first pass should reduce context loss without inventing work that was never executed.
