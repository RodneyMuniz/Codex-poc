# Program Kanban

This file is rendered from `sessions/studio.db`. Do not use it as the source of truth.

## Backlog

### Add queued worker orchestration with controlled concurrency limits
- ID: PK-067
- Kind: request
- Status: backlog
- Owner: Architect
- Assigned Role: Developer
- Priority: high
- Requires Approval: no
- Review State: None
- Milestone: M10 - Platform Scaling And Operational Follow-Ons
- Expected Artifact: scripts/worker.py
- Objective: Add a queue-backed worker path with explicit concurrency limits while preserving the safe sequential fallback for debugging and recovery.
- Details: Design a queued worker orchestration layer with explicit concurrency limits and controlled ownership. The first pass should support queue-backed delegation as an optional runtime path while preserving the current sequential fallback for safety and debugging.
- Review Notes: Deferred out of M7 on 2026-04-02. Queue-backed orchestration remains a later platform-scaling slice after the core studio lane is operating.

### Add artifact lineage and dependency views to the control room
- ID: PK-068
- Kind: request
- Status: backlog
- Owner: Dashboard Implementer
- Assigned Role: Developer
- Priority: medium
- Requires Approval: no
- Review State: None
- Milestone: M10 - Platform Scaling And Operational Follow-Ons
- Expected Artifact: scripts/operator_wall_snapshot.py
- Objective: Show artifact ancestry and dependencies from canonical store evidence so the operator can trace outputs without reading raw trace records.
- Details: Add artifact lineage and dependency views to the control room so the operator can see what artifact was produced from what upstream input, task, or run. The first pass should stay grounded in canonical store evidence and avoid inventing lineage that the framework did not actually record.
- Review Notes: Deferred out of M7 on 2026-04-02. Artifact lineage views now sit behind the later event-ledger and platform-scaling work.

### Add a first-class immutable runtime event ledger separate from summary messages
- ID: PK-065
- Kind: request
- Status: backlog
- Owner: Architect
- Assigned Role: Architect
- Priority: high
- Requires Approval: no
- Review State: None
- Milestone: M10 - Platform Scaling And Operational Follow-Ons
- Expected Artifact: sessions/store.py
- Objective: Create an immutable event ledger that preserves execution facts separately from summary-style messages and later UI interpretation.
- Details: Design and implement a dedicated runtime event ledger separate from the current summary-style message stream. The ledger should preserve immutable execution facts that later control-room views can trust for replay, auditing, and analytics without reconstructing history from mixed commentary.
- Review Notes: Deferred out of M7 on 2026-04-02 after safeguard closure. Resume later as platform-scaling work rather than a gate on visual or audio production.

### Define the large-media storage policy for generated images, source files, and audio
- ID: PK-081
- Kind: request
- Status: backlog
- Owner: Architect
- Assigned Role: Architect
- Priority: medium
- Requires Approval: no
- Review State: None
- Milestone: M8 - Visual Production And Digital Asset Management
- Expected Artifact: projects/program-kanban/governance/LARGE_MEDIA_POLICY.md
- Objective: Define a large-media storage policy that prevents binary sprawl while keeping review artifacts, source files, and metadata recoverable and auditable.
- Details: Set the first storage policy for generated review images, exported deliverables, larger editable source files, and audio assets so the repo does not drift into uncontrolled binary growth. This should define what stays in repo, what stays optional, when Git LFS becomes necessary, and what metadata must always remain in the canonical store.
- Review Notes: Moved from M7 to M8 on 2026-04-02. Large-media policy now gates the visual and audio production wave instead of the closed M7 substrate milestone.

### Add a Design Review gallery to the control room
- ID: PK-077
- Kind: request
- Status: backlog
- Owner: Dashboard Implementer
- Assigned Role: Dashboard Implementer
- Priority: high
- Requires Approval: no
- Review State: None
- Milestone: M8 - Visual Production And Digital Asset Management
- Expected Artifact: projects/program-kanban/app/app.js
- Objective: Make design artifacts reviewable in the control room with canonical gallery browsing, filters, provenance, and selected-direction state.
- Details: Add a control-room gallery surface for design artifacts with project and task filters, thumbnail browsing, prompt summary, provenance, and selected-direction state. The gallery must be derived from canonical folder artifacts plus SQLite metadata instead of becoming a second source of truth.
- Review Notes: Moved into M8 Visual Production And Digital Asset Management on 2026-03-27.

### Add variant comparison, approval, and revision lineage for design artifacts
- ID: PK-078
- Kind: request
- Status: backlog
- Owner: Product Designer / Workflow Planner
- Assigned Role: Product Designer / Workflow Planner
- Priority: high
- Requires Approval: no
- Review State: None
- Milestone: M8 - Visual Production And Digital Asset Management
- Expected Artifact: projects/program-kanban/app/app.js
- Objective: Make design review variant-first so approval decisions happen on comparable options with side-by-side evidence and revision lineage.
- Details: Make design review variant-first instead of file-first. Support side-by-side comparison for up to three variants, zoom, approve, reject, and revise-from-selected-variant actions while preserving lineage such as A, B, C, and B2.
- Review Notes: Moved into M8 Visual Production And Digital Asset Management on 2026-03-27.

### Add the OpenAI image-generation specialist runtime and provenance capture
- ID: PK-080
- Kind: request
- Status: backlog
- Owner: Design Specialist Runtime Builder
- Assigned Role: Design Specialist Runtime Builder
- Priority: high
- Requires Approval: no
- Review State: None
- Milestone: M8 - Visual Production And Digital Asset Management
- Expected Artifact: agents/sdk_specialists.py
- Objective: Enable a bounded image-generation specialist that records provenance and supports iterative concept revision without bypassing canonical artifact storage.
- Details: Add a bounded design or artist specialist path that can call the current OpenAI image-generation workflow for concept exploration and iterative revisions. Persist model, provider, prompt summary, revised prompt, parent artifact, response identifiers, and output file metadata for each generated artifact.
- Review Notes: Moved into M8 Visual Production And Digital Asset Management on 2026-03-27.

### Implement canonical visual artifact storage, manifests, and SQLite indexing
- ID: PK-076
- Kind: request
- Status: backlog
- Owner: Architect
- Assigned Role: Architect
- Priority: high
- Requires Approval: no
- Review State: None
- Milestone: M8 - Visual Production And Digital Asset Management
- Expected Artifact: sessions/store.py
- Objective: Create the canonical visual-artifact data model so generated and imported design assets are stored on disk, indexed in SQLite, and ready for review and handoff.
- Details: Add the first filesystem-backed storage model for generated or imported visual artifacts under projects/<project>/artifacts/design/, with SQLite keeping metadata only. Record prompt summary, provider, parent artifact, review state, selected direction, file paths, and file hashes.
- Review Notes: Retitled and moved into M8 on 2026-03-27.

### Implement approved visual artifact to implementation handoff
- ID: PK-079
- Kind: request
- Status: backlog
- Owner: Architect
- Assigned Role: Architect
- Priority: high
- Requires Approval: no
- Review State: None
- Milestone: M8 - Visual Production And Digital Asset Management
- Expected Artifact: agents/orchestrator.py
- Objective: Make approved visual artifacts explicit implementation inputs so downstream code work consumes selected asset ids and preserved lineage instead of vague design intent.
- Details: Make approved visual artifacts explicit inputs to later implementation tasks so code work references a chosen artifact id or path instead of relying on vague design intent. The bridge should preserve approval state and artifact lineage.
- Review Notes: Retitled and moved into M8 on 2026-03-27.

### Add a manual external visual-asset import lane
- ID: PK-082
- Kind: request
- Status: backlog
- Owner: Dashboard Implementer
- Assigned Role: Dashboard Implementer
- Priority: medium
- Requires Approval: no
- Review State: None
- Milestone: M8 - Visual Production And Digital Asset Management
- Expected Artifact: projects/program-kanban/app/server.mjs
- Objective: Create a controlled import path for externally produced visual assets so they enter the same canonical artifact lifecycle as generated concepts.
- Details: Add the first controlled import path for visual artifacts created outside the generation runtime, such as exported mockups or curated image assets. The framework should ingest those files into the canonical visual-artifact folder structure and preserve provenance and review state.
- Review Notes: Retitled and moved into M8 on 2026-03-27.

### Add the Art Director critique loop and approval rubric
- ID: PK-086
- Kind: request
- Status: backlog
- Owner: Art Director
- Assigned Role: Art Director
- Priority: high
- Requires Approval: no
- Review State: None
- Milestone: M8 - Visual Production And Digital Asset Management
- Expected Artifact: projects/program-kanban/governance/ART_DIRECTOR_REVIEW_CONTRACT.md
- Objective: Introduce a professional critique and approval model for visual deliverables.
- Details: Define the first Art Director critique loop so visual concepts are reviewed against a clear rubric before implementation begins. The first pass should cover concept quality, readability, style fit, production feasibility, and operator-facing approval language.
- Review Notes: Created during the approved M7-M11 board rewrite on 2026-03-27.

### Add Technical Artist packaging and Phaser-ready manifest generation
- ID: PK-087
- Kind: request
- Status: backlog
- Owner: Technical Artist
- Assigned Role: Technical Artist
- Priority: medium
- Requires Approval: no
- Review State: None
- Milestone: M8 - Visual Production And Digital Asset Management
- Expected Artifact: sessions/store.py
- Objective: Bridge approved visual review outputs into Phaser-ready packages and manifests.
- Details: Define how approved visual assets become runtime-ready packages with anchors, layers, variant labels, and manifest metadata that the TacticsGame renderer can consume. The first pass should stay framework-owned and not assume final production-quality art.
- Review Notes: Created during the approved M7-M11 board rewrite on 2026-03-27.

### Add board and map concept review support
- ID: PK-088
- Kind: request
- Status: backlog
- Owner: Art Director
- Assigned Role: Dashboard Implementer
- Priority: medium
- Requires Approval: no
- Review State: None
- Milestone: M8 - Visual Production And Digital Asset Management
- Expected Artifact: projects/program-kanban/app/app.js
- Objective: Support board and map concept review as a first-class visual deliverable type.
- Details: Extend the visual review flow so board, terrain, and map concepts can be reviewed cleanly alongside HUD or unit-direction work. The first pass should make board-shape, terrain language, and map identity reviewable without pretending they are already runtime-ready.
- Review Notes: Created during the approved M7-M11 board rewrite on 2026-03-27.

### Implement the audio request preview and clarification gate
- ID: PK-089
- Kind: request
- Status: backlog
- Owner: Project Orchestrator
- Assigned Role: Project Orchestrator
- Priority: high
- Requires Approval: no
- Review State: None
- Milestone: M9 - Audio Production Pipeline
- Expected Artifact: agents/orchestrator.py
- Objective: Make audio work start from an approved request packet so generation or import begins with clear intent, constraints, and reference material.
- Details: Add an audio request preview so the Orchestrator can capture target surface, mood, asset type, runtime constraints, and references before generation or import begins. Audio specialists should ask at most three blocking questions when crucial information is missing.
- Review Notes: Created during the approved M7-M11 board rewrite on 2026-03-27.

### Implement canonical audio artifact storage and SQLite indexing
- ID: PK-090
- Kind: request
- Status: backlog
- Owner: Architect
- Assigned Role: Architect
- Priority: high
- Requires Approval: no
- Review State: None
- Milestone: M9 - Audio Production Pipeline
- Expected Artifact: sessions/store.py
- Objective: Create the canonical audio-artifact data model so imported and generated audio lives on disk with SQLite-backed provenance and review metadata.
- Details: Add the first filesystem-backed audio artifact model so imported or generated sound assets land in canonical project folders while SQLite keeps metadata only. Track provenance, revision lineage, playback metadata, and selected direction without storing binary audio blobs in SQLite.
- Review Notes: Created during the approved M7-M11 board rewrite on 2026-03-27.

### Add an Audio Review surface with playback, approval, and revision lineage
- ID: PK-091
- Kind: request
- Status: backlog
- Owner: Dashboard Implementer
- Assigned Role: Dashboard Implementer
- Priority: medium
- Requires Approval: no
- Review State: None
- Milestone: M9 - Audio Production Pipeline
- Expected Artifact: projects/program-kanban/app/app.js
- Objective: Make audio review practical in the control room with playback, approval state, and revision lineage tied to canonical audio artifacts.
- Details: Add a control-room audio review surface that supports playback, provenance, approval state, and revision lineage. The first pass should make short-form sound review practical without trying to replace full external audio editing tools.
- Review Notes: Created during the approved M7-M11 board rewrite on 2026-03-27.

### Add a manual external-audio import lane
- ID: PK-092
- Kind: request
- Status: backlog
- Owner: Dashboard Implementer
- Assigned Role: Dashboard Implementer
- Priority: medium
- Requires Approval: no
- Review State: None
- Milestone: M9 - Audio Production Pipeline
- Expected Artifact: projects/program-kanban/app/server.mjs
- Objective: Create a controlled import path for externally produced audio so curated sounds enter the canonical artifact lifecycle without losing provenance.
- Details: Add the first controlled import path for curated sound effects, processed edits, and other audio assets created outside the generation runtime. The framework should ingest those files into the canonical audio folder structure and preserve provenance, review state, and later runtime references.
- Review Notes: Created during the approved M7-M11 board rewrite on 2026-03-27.

### Implement approved audio-to-runtime handoff
- ID: PK-093
- Kind: request
- Status: backlog
- Owner: Architect
- Assigned Role: Architect
- Priority: medium
- Requires Approval: no
- Review State: None
- Milestone: M9 - Audio Production Pipeline
- Expected Artifact: sessions/store.py
- Objective: Make approved audio artifacts explicit runtime inputs so downstream implementation references chosen assets and preserved lineage.
- Details: Make approved audio artifacts explicit inputs to later runtime implementation tasks so playback, effects hooks, and manifest references point to chosen artifacts instead of vague intent. The first pass should preserve approval state, lineage, and runtime-facing metadata.
- Review Notes: Created during the approved M7-M11 board rewrite on 2026-03-27.

### Normalize tracked generated artifacts and stale path metadata after Git recovery
- ID: PK-102
- Kind: request
- Status: backlog
- Owner: Project Orchestrator
- Assigned Role: Architect
- Priority: high
- Requires Approval: no
- Review State: None
- Milestone: M10 - Platform Scaling And Operational Follow-Ons
- Expected Artifact: projects/program-kanban/artifacts/repo_hygiene_normalization_plan.md
- Objective: Remove tracked runtime noise and stale root metadata without destabilizing the recovered active workspace or losing source work.
- Details: Repo-hygiene follow-up to remove tracked generated/runtime noise, correct stale root metadata, and protect the clean post-recovery workspace before the next larger delivery wave.
- Review Notes: Deferred out of M7 on 2026-04-02. Partial repo-hygiene cleanup is preserved, but the remaining cleanup is operational follow-on work rather than a gate on the studio capability milestones.

### Add the OpenAI audio specialist runtime and provenance capture
- ID: PK-105
- Kind: request
- Status: backlog
- Owner: Audio Specialist Runtime Builder
- Assigned Role: Audio Specialist Runtime Builder
- Priority: high
- Requires Approval: no
- Review State: None
- Milestone: M9 - Audio Production Pipeline
- Expected Artifact: agents/sdk_specialists.py
- Objective: Enable a bounded OpenAI audio specialist runtime with provenance capture so the audio lane can generate or transform assets without bypassing canonical artifact discipline.
- Details: Add the missing audio-runtime task so M9 has the same bounded runtime foundation that M8 already expects for image generation.

### AUDIT governed API truth check
- ID: PK-113
- Kind: request
- Status: backlog
- Owner: Developer
- Assigned Role: Developer
- Priority: medium
- Requires Approval: no
- Review State: None
- Objective: Audit governed external API execution truth.
- Details: Audit-only governed specialist execution against the real external provider boundary.

### AUDIT governed API truth check
- ID: PK-114
- Kind: request
- Status: backlog
- Owner: Developer
- Assigned Role: Developer
- Priority: medium
- Requires Approval: no
- Review State: None
- Objective: Audit governed external API execution truth.
- Details: Audit-only governed specialist execution against the real external provider boundary.

### AUDIT governed API truth check
- ID: PK-115
- Kind: request
- Status: backlog
- Owner: Developer
- Assigned Role: Developer
- Priority: medium
- Requires Approval: no
- Review State: None
- Objective: Audit governed external API execution truth.
- Details: Audit-only governed specialist execution against the real external provider boundary.

## Ready for Build

_No items_

## In Progress

_No items_

## In Review

### Separate deterministic media services from AI specialist roles
- ID: PK-085
- Kind: request
- Status: in_review
- Owner: QA
- Assigned Role: Architect
- Priority: high
- Requires Approval: no
- Review State: In Review
- Milestone: M8 - Visual Production And Digital Asset Management
- Expected Artifact: agents/orchestrator.py
- Objective: Keep media services deterministic while AI specialists stay bounded to generative or evaluative work.
- Details: Split media indexing, import bookkeeping, manifest generation, and review-state persistence away from AI specialist behavior. The first pass should make it clear which work is deterministic platform logic and which work belongs to delegated design or audio specialists.
- Result: Slice 1 exposed deterministic media-service ownership; slice 2 now registers design outputs into canonical visual artifacts before QA and surfaces them in run evidence.
- Review Notes: Evidence: projects/program-kanban/artifacts/pk085_media_service_boundary_slice1.md and projects/program-kanban/artifacts/pk085_visual_registration_slice2.md. Validation: focused pytest suite 30 passed; broader regression suite 70 passed.

## Complete

### Define the canonical board workflow and visible columns for the new Program Kanban wall
- ID: PK-030
- Kind: request
- Status: completed
- Owner: Project Orchestrator
- Assigned Role: Project Orchestrator
- Priority: high
- Requires Approval: yes
- Review State: Accepted
- Milestone: M1 - Basic Operation Level
- Objective: Replace the current generic runtime board columns with the operator-approved delivery workflow so the wall matches how work actually moves.
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
- ID: PK-031
- Kind: request
- Status: completed
- Owner: Project Orchestrator
- Assigned Role: Project Orchestrator
- Priority: high
- Requires Approval: yes
- Review State: Accepted
- Milestone: M1 - Basic Operation Level
- Objective: Make it impossible for underspecified work to look build-ready in the board.
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
- ID: PK-032
- Kind: request
- Status: completed
- Owner: Project Orchestrator
- Assigned Role: Project Orchestrator
- Priority: high
- Requires Approval: yes
- Review State: Accepted
- Milestone: M1 - Basic Operation Level
- Objective: Give the new framework a clean milestone model so planning is not implied through ad hoc task notes.
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
- ID: PK-033
- Kind: request
- Status: completed
- Owner: Dashboard Implementer
- Assigned Role: Dashboard Implementer
- Priority: high
- Requires Approval: yes
- Review State: Accepted
- Milestone: M1 - Basic Operation Level
- Expected Artifact: projects/program-kanban/app/app.js
- Objective: Bring back the operator milestone surface in a form that fits the new framework-backed board.
- Details: Restore a dedicated milestone view.

Requested outcome:
- separate milestone view accessible from the wall
- tasks grouped under milestones
- tasks shown as id plus name in this view
- visible percent completion per milestone
- milestone progress easy to scan during review
- Review Notes: Studio Lead reviewed the milestone view and accepted it as complete on 2026-03-23.

### Restore task-id click-to-copy in approved operator surfaces
- ID: PK-034
- Kind: request
- Status: completed
- Owner: Dashboard Implementer
- Assigned Role: Dashboard Implementer
- Priority: medium
- Requires Approval: yes
- Review State: Accepted
- Milestone: M1 - Basic Operation Level
- Expected Artifact: projects/program-kanban/app/app.js
- Objective: Let the operator reference board work quickly in chat and review without manual retyping.
- Details: Restore click-to-copy for task ids in the new wall.

The first pass should confirm:
- which views support click-to-copy
- copied text format
- visible feedback after copy
- expected desktop and touch behavior
- Review Notes: Studio Lead reviewed click-to-copy behavior and accepted it as complete on 2026-03-23.

### Add top-level Board and Milestones navigation in the operator wall
- ID: PK-035
- Kind: request
- Status: completed
- Owner: Product Designer / Workflow Planner
- Assigned Role: Product Designer / Workflow Planner
- Priority: high
- Requires Approval: yes
- Review State: Accepted
- Milestone: M1 - Basic Operation Level
- Objective: Restore clear view switching so the operator can move between board and milestone contexts without confusion.
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
- ID: PK-036
- Kind: request
- Status: completed
- Owner: Dashboard Implementer
- Assigned Role: Dashboard Implementer
- Priority: high
- Requires Approval: yes
- Review State: Accepted
- Milestone: M1 - Basic Operation Level
- Expected Artifact: scripts/operator_wall_snapshot.py
- Objective: Make the new board trustworthy by validating critical planning rules instead of only displaying task data.
- Details: Define and later implement the first integrity checks for the new board model.

Candidate validation areas:
- Ready for Build tasks missing required planning fields
- tasks without milestone assignment where assignment is required
- completed work not actually reviewed and accepted
- milestone progress drift caused by task state mismatch
- Review Notes: Studio Lead reviewed the planning validation behavior and accepted it as complete on 2026-03-23.

### Reintroduce a lightweight recent-updates context panel in the new wall
- ID: PK-037
- Kind: request
- Status: completed
- Owner: Dashboard Implementer
- Assigned Role: Dashboard Implementer
- Priority: medium
- Requires Approval: yes
- Review State: Accepted
- Milestone: M3 - Operator Clarity Recovery
- Expected Artifact: projects/program-kanban/app/app.js
- Objective: Recover quick operator context without making the board feel like a reporting dashboard.
- Details: Revisit the old recent-updates support surface and decide what belongs in the new board after M1 basic operation is stable.
- Result: Implemented a recent updates panel fed from task updates, approvals, runs, agent runs, validations, and artifacts.
- Review Notes: Accepted by Studio Lead after UI review.

### Reintroduce lightweight hierarchy cues for role clarity
- ID: PK-038
- Kind: request
- Status: completed
- Owner: Project Orchestrator
- Assigned Role: Dashboard Implementer
- Priority: low
- Requires Approval: yes
- Review State: Accepted
- Milestone: M3 - Operator Clarity Recovery
- Expected Artifact: projects/program-kanban/app/styles.css
- Objective: Recover the useful parts of the old hierarchy rail only if they still improve operator scanning in the new wall.
- Details: Revisit role and hierarchy visibility now that the wall is framework-backed and more evidence-driven than the legacy version.
- Result: Added subtle ownership cues through styled owner and assigned-role badges plus milestone role labels.
- Review Notes: Accepted by Studio Lead after UI review.

### Decide and implement scoped project filtering for multi-project board use
- ID: PK-039
- Kind: request
- Status: completed
- Owner: Dashboard Implementer
- Assigned Role: Dashboard Implementer
- Priority: low
- Requires Approval: yes
- Review State: Accepted
- Milestone: M3 - Operator Clarity Recovery
- Expected Artifact: projects/program-kanban/app/app.js
- Objective: Preserve useful project focus controls only if they still fit the new board architecture.
- Details: Revisit project chip filtering and decide whether it belongs in the Program Kanban planning wall after M1 is stable.
- Result: Polished scoped project visibility with clearer scope metadata and all-project rollup cards.
- Review Notes: Accepted by Studio Lead after UI review.

### Add milestone filtering for completed or backlog-only milestones
- ID: PK-040
- Kind: request
- Status: completed
- Owner: Product Designer / Workflow Planner
- Assigned Role: Dashboard Implementer
- Priority: low
- Requires Approval: yes
- Review State: Accepted
- Milestone: M3 - Operator Clarity Recovery
- Expected Artifact: projects/program-kanban/app/app.js
- Objective: Refine milestone scanning after the basic milestone surface is working again.
- Details: Revisit optional milestone filtering once the core milestone model and milestone view are stable.
- Result: Implemented milestone filters plus collapsible milestone headers and project-grouped milestone columns.
- Review Notes: Accepted by Studio Lead after UI review.

### Explore response-chip answers for orchestrator question flows
- ID: PK-041
- Kind: request
- Status: completed
- Owner: Orchestrator
- Assigned Role: Dashboard Implementer
- Priority: low
- Requires Approval: yes
- Review State: Accepted
- Milestone: M4 - Later Extensions
- Expected Artifact: projects/program-kanban/app/app.js
- Objective: Decide whether bounded click-to-answer patterns would genuinely help the new board workflow.
- Details: Revisit optional response chips after the basic board and milestone planning flows are operating cleanly again.
- Result: Closed as no longer necessary after the chat-first operating model.
- Review Notes: Closed as no longer necessary after the chat-first Orchestrator and control-room split.

### Plan workspace-level multi-project rollup after single-project flow is stable
- ID: PK-042
- Kind: request
- Status: completed
- Owner: Workflow Systems Planner
- Assigned Role: Workflow Systems Planner
- Priority: low
- Requires Approval: yes
- Review State: Accepted
- Milestone: M4 - Later Extensions
- Expected Artifact: scripts/operator_wall_snapshot.py
- Objective: Keep workspace rollup as a later extension instead of mixing it into the basic board reset.
- Details: Revisit safe multi-project aggregation only after the Program Kanban board is trustworthy on its own.
- Result: Added an all-project workspace rollup with per-project counts, milestone totals, root paths, and quick-open actions.
- Review Notes: Accepted by Studio Lead after UI review.

### Evaluate file-watch refresh after basic operation stabilizes
- ID: PK-043
- Kind: request
- Status: completed
- Owner: Dashboard Implementer
- Assigned Role: Dashboard Implementer
- Priority: low
- Requires Approval: yes
- Review State: Accepted
- Milestone: M4 - Later Extensions
- Expected Artifact: projects/program-kanban/app/app.js
- Objective: Decide whether auto-refresh belongs in the new board after the planning model is settled.
- Details: Keep file-watch or auto-refresh evaluation out of M1 and revisit it only after the basic board is trusted.
- Result: Replaced forced polling with Refresh Now plus an optional persisted auto-refresh toggle.
- Review Notes: Accepted by Studio Lead after UI review.

### Evaluate richer cross-linking after the new board model settles
- ID: PK-044
- Kind: request
- Status: completed
- Owner: Dashboard Implementer
- Assigned Role: Dashboard Implementer
- Priority: low
- Requires Approval: yes
- Review State: Accepted
- Milestone: M4 - Later Extensions
- Expected Artifact: projects/program-kanban/app/app.js
- Objective: Decide whether deeper navigation is genuinely useful after the core planning experience is restored.
- Details: Keep richer linking out of the basic board reset and revisit it only after core operator flow is stable.
- Result: Added task evidence links into an in-page Evidence Spotlight for latest run, artifact, and validation details.
- Review Notes: Accepted by Studio Lead after UI review.

### Implement the approved board workflow columns and secondary state treatment
- ID: PK-045
- Kind: request
- Status: completed
- Owner: Dashboard Implementer
- Assigned Role: Dashboard Implementer
- Priority: high
- Requires Approval: yes
- Review State: Accepted
- Milestone: M1 - Basic Operation Level
- Expected Artifact: projects/program-kanban/app/styles.css
- Objective: Put the M1 workflow model into the live Program Kanban wall so the visible board matches the approved planning flow.
- Details: Implement the approved primary board workflow.

Required outcome:
- visible columns are Backlog, Ready for Build, In Progress, In Review, and Complete
- Blocked and Deferred are treated as secondary states rather than primary columns
- the live wall reflects the approved workflow names and ordering
- Review Notes: Studio Lead accepted the ultrawide layout revision on 2026-03-23.

### Implement first-class milestone records and single-milestone task linkage
- ID: PK-046
- Kind: request
- Status: completed
- Owner: Dashboard Implementer
- Assigned Role: Dashboard Implementer
- Priority: high
- Requires Approval: yes
- Review State: Accepted
- Milestone: M1 - Basic Operation Level
- Expected Artifact: sessions/store.py
- Objective: Add the canonical milestone data layer required for the restored milestone planning workflow.
- Details: Implement the first-pass milestone model.

Required outcome:
- milestones become first-class canonical records in SQLite
- each task links to exactly one milestone in the first pass
- milestone records carry id, title, entry goal, exit goal, order, and status
- Review Notes: Studio Lead reviewed milestone records and task linkage and accepted them as complete on 2026-03-23.

### Enforce Ready for Build gates in canonical task transitions and validation surfaces
- ID: PK-047
- Kind: request
- Status: completed
- Owner: Dashboard Implementer
- Assigned Role: Dashboard Implementer
- Priority: high
- Requires Approval: yes
- Review State: Accepted
- Milestone: M1 - Basic Operation Level
- Expected Artifact: sessions/store.py
- Objective: Make the board trustworthy by blocking premature Ready for Build transitions and surfacing planning-state violations clearly.
- Details: Implement Ready for Build gate enforcement.

Required outcome:
- tasks cannot move to Ready for Build unless all approved planning fields exist
- missing required planning fields are visible to the operator
- completion closure remains tied to review acceptance
- Review Notes: Studio Lead accepted Ready for Build gate enforcement on 2026-03-23.

### Define and review the M2 operator-client trust boundary and proof criteria
- ID: PK-048
- Kind: request
- Status: completed
- Owner: Project Orchestrator
- Assigned Role: Project Orchestrator
- Priority: medium
- Requires Approval: yes
- Review State: Accepted
- Milestone: M2 - Operator Client And Traceable Delegation
- Expected Artifact: projects/program-kanban/governance/M2_OPERATOR_CLIENT_SPEC_2026-03-21.md
- Objective: Define the operator-client trust boundary so requests, approvals, trace evidence, and proof criteria are explicit before the client replaces chat as the primary execution surface.
- Details: Capture the minimum operator-client requirements needed to stop depending on this Codex thread as the production orchestration surface.

The output must define the operator surfaces, trace expectations, trust rules, and proof scenario for the first client milestone.
- Review Notes: Studio Lead accepted the M2 operator-client spec and the recommended requirement defaults on 2026-03-23.

### Add operator-client request intake and dispatch confirmation flow
- ID: PK-049
- Kind: request
- Status: completed
- Owner: Dashboard Implementer
- Assigned Role: Dashboard Implementer
- Priority: high
- Requires Approval: yes
- Review State: Accepted
- Milestone: M2 - Operator Client And Traceable Delegation
- Expected Artifact: projects/program-kanban/app/app.js
- Objective: Let the operator create a request, review the Orchestrator interpretation, answer clarifying questions, and confirm dispatch without depending on a chat-only flow.
- Details: Build the Program Kanban app surface where the Studio Lead can enter a natural-language request, see the Orchestrator interpretation, answer clarifying questions, and confirm dispatch before work starts.
- Result: Built an operator-facing Orchestrator tab with request intake, preview, and dispatch confirmation.
- Review Notes: Accepted as optional web dispatch. The Program Kanban app is no longer required to be the primary conversational client.

### Add operator actions API for request, approval, rejection, and resume
- ID: PK-050
- Kind: request
- Status: completed
- Owner: Orchestration Runtime Implementer
- Assigned Role: Orchestration Runtime Implementer
- Priority: high
- Requires Approval: yes
- Review State: Accepted
- Milestone: M2 - Operator Client And Traceable Delegation
- Expected Artifact: projects/program-kanban/app/server.mjs
- Objective: Provide a stable app-facing API for request creation, approval, rejection, and resume actions so Program Kanban can drive orchestration safely.
- Details: Extend the Program Kanban server layer so the operator client can create requests, confirm dispatch, approve or reject pauses, and resume runs without dropping into the CLI.
- Result: Added operator actions API endpoints for preview, dispatch, approve, reject, resume, and run inspection.
- Review Notes: Accepted by Studio Lead without further manual validation; capability acknowledged as present in the framework.

### Persist the orchestration trace ledger and structured handoff packets
- ID: PK-051
- Kind: request
- Status: completed
- Owner: Workflow Systems Planner
- Assigned Role: Workflow Systems Planner
- Priority: high
- Requires Approval: yes
- Review State: Accepted
- Milestone: M2 - Operator Client And Traceable Delegation
- Expected Artifact: sessions/store.py
- Objective: Persist structured handoff packets and trace events so delegation history is auditable without reconstructing mixed summary messages.
- Details: Extend the canonical store so the semantic handoff chain is visible as structured events and packets, not just inferred from task status or agent run records.
- Result: Persisted a structured trace ledger in the canonical store and exposed it in run evidence.
- Review Notes: Accepted by Studio Lead without further manual validation; capability acknowledged as present in the framework.

### Add a run inspector for trace, delegation, artifacts, validation, and final summary
- ID: PK-052
- Kind: request
- Status: completed
- Owner: Dashboard Implementer
- Assigned Role: Dashboard Implementer
- Priority: high
- Requires Approval: yes
- Review State: Accepted
- Milestone: M2 - Operator Client And Traceable Delegation
- Expected Artifact: projects/program-kanban/app/app.js
- Objective: Give the operator a single run-inspection surface for trace, delegation, artifacts, validation, and final outcome evidence.
- Details: Create an operator-facing run detail view so the Studio Lead can audit what happened in a run without using ad hoc SQL or raw CLI output.
- Result: Added a run inspector with trace events, delegations, artifacts, validations, and final summary visibility.
- Review Notes: Accepted by Studio Lead without further manual validation; capability acknowledged as present in the framework.

### Expose role profiles, model routing, and skill metadata in operator views
- ID: PK-053
- Kind: request
- Status: completed
- Owner: Workflow Systems Planner
- Assigned Role: Workflow Systems Planner
- Priority: medium
- Requires Approval: yes
- Review State: Accepted
- Milestone: M2 - Operator Client And Traceable Delegation
- Expected Artifact: scripts/operator_wall_snapshot.py
- Objective: Make each handoff explainable by surfacing the role profile, model route, and skill metadata used during the run.
- Details: Make the route explainable by showing which role, model, and skills were used for each handoff and why that route was chosen at a short summary level.
- Result: Exposed role profiles, model routing, route reasons, and profile-skill metadata in the operator client.
- Review Notes: Accepted by Studio Lead without further manual validation; capability acknowledged as present in the framework.

### Prove an end-to-end app-driven orchestration run that bypasses chat dependence
- ID: PK-054
- Kind: request
- Status: completed
- Owner: QA
- Assigned Role: QA
- Priority: medium
- Requires Approval: yes
- Review State: Accepted
- Milestone: M2 - Operator Client And Traceable Delegation
- Expected Artifact: projects/program-kanban/artifacts/m2_operator_client_proof.json
- Objective: Prove that the Program Kanban app can drive a full orchestration run end to end without depending on this chat thread as the operator surface.
- Details: Run a real proof scenario from the Program Kanban app so the request, approvals, trace, artifacts, validation, and final summary all come from the operator client rather than this thread.
- Result: Completed an app-driven proof run and wrote the evidence packet to projects/program-kanban/artifacts/m2_operator_client_proof.json.
- Review Notes: Historical proof artifact retained, but app-only orchestration is no longer the gating operating model for future validation.

### Create an offline one-click launcher page for Program Kanban and TacticsGame
- ID: PK-055
- Kind: request
- Status: completed
- Owner: Dashboard Implementer
- Assigned Role: Dashboard Implementer
- Priority: high
- Requires Approval: yes
- Review State: Accepted
- Milestone: M1 - Basic Operation Level
- Expected Artifact: projects/program-kanban/app/offline-launcher.html
- Objective: Provide a local one-click launcher so Program Kanban and TacticsGame can be started reliably without manual terminal setup.
- Details: Create a local launcher page inside the Program Kanban folder structure so the Studio Lead can bring both apps online without asking Codex to do it manually.

The first pass should feel intentional and pleasant to use, not like a bare placeholder admin page.

Important constraint: a normal offline HTML file in a browser cannot directly start local processes for security reasons, so the build must pair the page with a supported local helper mechanism such as a PowerShell or command wrapper, a tiny local launcher endpoint, or a desktop-style wrapper.
- Review Notes: Studio Lead accepted the launcher flow on 2026-03-23. The launcher supports helper-mode cold start plus browser-mode status, logs, and command access from the bookmarked page.

### Show board-column status badges in milestone task rows
- ID: PK-056
- Kind: request
- Status: completed
- Owner: Dashboard Implementer
- Assigned Role: Dashboard Implementer
- Priority: medium
- Requires Approval: yes
- Review State: Accepted
- Milestone: M1 - Basic Operation Level
- Expected Artifact: projects/program-kanban/app/app.js
- Objective: Show each task's live board status directly in milestone rows so milestone review does not require opening every task card.
- Details: Update the milestone view so each task row shows its current primary board-column status, such as Backlog, Ready for Build, In Progress, In Review, or Complete.
- Review Notes: Studio Lead accepted milestone task-row board status badges on 2026-03-23.

### Add the official Agents SDK dependency and an isolated runtime adapter path
- ID: PK-057
- Kind: request
- Status: completed
- Owner: QA
- Assigned Role: Developer
- Priority: high
- Requires Approval: yes
- Review State: Accepted
- Milestone: M5 - SDK-Native Runtime Migration
- Expected Artifact: agents/sdk_runtime.py
- Objective: Bootstrap an SDK-native runtime entry point without removing the current custom orchestration path yet.
- Details: The first pass should update dependencies, add a new runtime adapter module, and prove the framework can instantiate an SDK-native execution path behind a feature flag or equivalent routing decision.
- Result: Accepted by Studio Lead.
- Review Notes: Accepted by Studio Lead after specialist-only SDK review.

### Implement shared SDK specialist-session support without creating a second Orchestrator role
- ID: PK-058
- Kind: request
- Status: completed
- Owner: QA
- Assigned Role: Architect
- Priority: high
- Requires Approval: yes
- Review State: Accepted
- Milestone: M5 - SDK-Native Runtime Migration
- Expected Artifact: agents/sdk_orchestrator.py
- Objective: Make the Orchestrator manager SDK-native while keeping the current operator-facing behavior intact.
- Details: This task should create an SDK-native Orchestrator implementation, use shared session support for the thread or run, and keep the Orchestrator as the manager instead of handing the conversation away to specialists.
- Result: Accepted by Studio Lead.
- Review Notes: Accepted by Studio Lead after specialist-only SDK review.

### Implement direct specialist delegation through SDK-native bounded agent calls
- ID: PK-059
- Kind: request
- Status: completed
- Owner: QA
- Assigned Role: Developer
- Priority: high
- Requires Approval: yes
- Review State: Accepted
- Milestone: M5 - SDK-Native Runtime Migration
- Expected Artifact: agents/sdk_pm.py
- Objective: Use the official SDK for PM to call Architect, Developer, Design, and QA as bounded specialist helpers.
- Details: The preferred pattern is agents-as-tools or equivalently bounded SDK-native delegation, not unrestricted conversational handoff. This task begins after the SDK runtime adapter and manager agent exist.
- Result: Accepted by Studio Lead.
- Review Notes: Accepted by Studio Lead after specialist-only SDK review.

### Bridge SDK human-in-the-loop pauses and resumes into the canonical approval model for specialist delegation
- ID: PK-060
- Kind: request
- Status: completed
- Owner: QA
- Assigned Role: Developer
- Priority: high
- Requires Approval: yes
- Review State: Accepted
- Milestone: M5 - SDK-Native Runtime Migration
- Expected Artifact: scripts/operator_api.py
- Objective: Keep approval control trustworthy while the runtime migrates to the official SDK.
- Details: This pass should map SDK-native human-in-the-loop events into the canonical approvals table and allow the control room to approve or resume the migrated path without dropping existing safety rules.
- Result: Accepted by Studio Lead.
- Review Notes: Accepted by Studio Lead after final SDK approval bridge and evidence review.

### Mirror SDK traces and session evidence into the SQLite control store and run inspector
- ID: PK-061
- Kind: request
- Status: completed
- Owner: QA
- Assigned Role: Developer
- Priority: high
- Requires Approval: yes
- Review State: Accepted
- Milestone: M5 - SDK-Native Runtime Migration
- Expected Artifact: sessions/store.py
- Objective: Keep the wall and SQLite store authoritative even after the execution runtime changes.
- Details: This task should map the migrated SDK runtime trace and session information into the existing run inspector, trace ledger, and evidence surfaces without requiring raw SDK internals in the UI.
- Result: Accepted by Studio Lead.
- Review Notes: Accepted by Studio Lead after final SDK approval bridge and evidence review.

### Preserve deterministic board-control actions outside the agent runtime and route only generative work into the SDK path
- ID: PK-062
- Kind: request
- Status: completed
- Owner: QA
- Assigned Role: Architect
- Priority: medium
- Requires Approval: yes
- Review State: Accepted
- Milestone: M5 - SDK-Native Runtime Migration
- Expected Artifact: agents/orchestrator.py
- Objective: Keep direct task-state and board-control operations deterministic while using the SDK only for generative orchestration work.
- Details: This task should formalize routing boundaries so direct board actions remain handled by framework code, while generative planning or specialist work can use the SDK-native runtime path.
- Result: Accepted by Studio Lead.
- Review Notes: Accepted by Studio Lead after specialist-only SDK review.

### Prove a chat-led Orchestrator flow that delegates to SDK specialists and is fully visible in the control room
- ID: PK-063
- Kind: request
- Status: completed
- Owner: QA
- Assigned Role: QA
- Priority: high
- Requires Approval: yes
- Review State: Accepted
- Milestone: M5 - SDK-Native Runtime Migration
- Expected Artifact: projects/program-kanban/artifacts/m5_sdk_runtime_proof.json
- Objective: Replace the old app-first proof criterion with a chat-led proof that still produces full control-room evidence.
- Details: The proof should start from chat or the chat-bridged orchestration entry point, use the SDK-native runtime, pause at approval if required, and export a canonical evidence packet for review.
- Result: Accepted by Studio Lead.
- Review Notes: Accepted by Studio Lead after specialist-only SDK review.

### Add one-click restore for SQLite safety backups in the control room
- ID: PK-064
- Kind: request
- Status: completed
- Owner: Project Orchestrator
- Assigned Role: Developer
- Priority: high
- Requires Approval: yes
- Review State: Accepted
- Milestone: M6 - Trust, Restore, And Operator Speed
- Expected Artifact: projects/program-kanban/app/app.js
- Objective: Let the operator restore a safety snapshot from the control room without manual database handling.
- Details: Add a restore flow in the control room for the existing SQLite safety backups. The flow should make restore choices visible, require explicit confirmation, create a fresh pre-restore safety backup, and report the outcome clearly so the operator can recover confidently without dropping into manual file work.
- Result: Control room now lists recorded SQLite safety backups, supports one-click restore with confirmation, creates a fresh pre-restore safety backup, and writes a restore receipt.
- Review Notes: Accepted by Studio Lead after control-room restore review.

### Turn the run inspector into a visual orchestration timeline
- ID: PK-069
- Kind: request
- Status: completed
- Owner: Orchestrator
- Assigned Role: Design
- Priority: high
- Requires Approval: yes
- Review State: Accepted
- Milestone: M6 - Trust, Restore, And Operator Speed
- Expected Artifact: projects/program-kanban/app/app.js
- Objective: Make orchestration easier to read by presenting execution as a clearer visual sequence.
- Details: Upgrade the current run inspector from a mostly list-based inspection surface into a visual orchestration timeline. The first pass should make approvals, specialist work, validations, and final summary transitions easier to scan while preserving access to the underlying evidence details.
- Result: Run Inspector now includes a visual orchestration timeline built from approvals, trace events, specialist runs, artifacts, and validations.
- Review Notes: Implementation ready for Studio Lead review of the timeline readability and sequencing.

### Visually distinguish deterministic framework actions from AI-delegated actions
- ID: PK-070
- Kind: request
- Status: completed
- Owner: Orchestrator
- Assigned Role: Design
- Priority: high
- Requires Approval: yes
- Review State: Accepted
- Milestone: M6 - Trust, Restore, And Operator Speed
- Expected Artifact: projects/program-kanban/app/app.js
- Objective: Help the operator understand provenance at a glance by separating rule-based actions from delegated model work.
- Details: Add a consistent visual treatment that clearly distinguishes deterministic framework actions from AI-delegated actions across run-inspection surfaces. The operator should not need to read deep trace text to understand what was code-driven versus model-driven.
- Result: Control-room run surfaces now visually distinguish deterministic framework actions from AI-delegated specialist actions.
- Review Notes: Implementation ready for Studio Lead review of provenance clarity across approvals, timeline, and trace cards.

### Add board density modes optimized for ultrawide review
- ID: PK-071
- Kind: request
- Status: completed
- Owner: Product Designer / Workflow Planner
- Assigned Role: Design
- Priority: medium
- Requires Approval: yes
- Review State: Accepted
- Milestone: M6 - Trust, Restore, And Operator Speed
- Expected Artifact: projects/program-kanban/app/styles.css
- Objective: Give the operator faster, more comfortable control-room scanning on large desktop monitors.
- Details: Add operator-selectable board density modes for compact, normal, and detailed review. The first pass should be explicitly tuned for ultrawide use while preserving acceptable behavior on smaller screens and remembering the local preference across refreshes.
- Result: Board now supports compact, normal, and detailed density modes persisted in local browser storage for ultrawide review.
- Review Notes: Accepted by Studio Lead after density-mode review.

### Enrich approval cards with upstream and downstream context
- ID: PK-072
- Kind: request
- Status: completed
- Owner: Product Designer / Workflow Planner
- Assigned Role: Design
- Priority: medium
- Requires Approval: yes
- Review State: Accepted
- Milestone: M6 - Trust, Restore, And Operator Speed
- Expected Artifact: projects/program-kanban/app/app.js
- Objective: Reduce approval friction by making each decision easier to understand in-place.
- Details: Improve approval cards so they explain why the approval is being requested, what upstream work led to it, and what downstream step is expected after approval. The first pass should stay compact enough for repeated daily use instead of turning approval review into a full report-reading exercise.
- Result: Approval cards now include upstream and downstream context, including exact task, why-now context, latest signals, and expected continuation.
- Review Notes: Implementation ready for Studio Lead review of approval readability and decision context.
Accepted by Studio Lead on 2026-03-27 after control-room review.

### Add a persistent system health strip to the control room
- ID: PK-073
- Kind: request
- Status: completed
- Owner: Project Orchestrator
- Assigned Role: Developer
- Priority: high
- Requires Approval: yes
- Review State: Accepted
- Milestone: M6 - Trust, Restore, And Operator Speed
- Expected Artifact: projects/program-kanban/app/app.js
- Objective: Keep the operator oriented by surfacing the most important runtime health signals all the time.
- Details: Add a persistent system health strip to the control room that shows the most important runtime signals at a glance. The first pass should include runtime mode, last backup, last run, pending approvals, and store-health context without becoming a noisy dashboard.
- Result: The control room now exposes a persistent system health strip with runtime mode, last backup, last run, pending approvals, and store health.
- Review Notes: Accepted by Studio Lead after health-strip review.

### Add a role and capability registry to remove hardcoded planning assumptions
- ID: PK-066
- Kind: request
- Status: completed
- Owner: Architect
- Assigned Role: Architect
- Priority: medium
- Requires Approval: no
- Review State: Accepted
- Milestone: M7 - Studio Foundations
- Expected Artifact: agents/config.py
- Objective: Replace hardcoded planning assumptions with a role-and-capability registry that routing, PM planning, and specialist selection can trust.
- Details: Replace scattered project-shaped planning assumptions with an explicit role and capability registry. The first pass should let planning and orchestration helpers route by deliverable type and specialist capability instead of baking assumptions into a fixed project template path.
- Result: Capability-registry hardening is review-ready: PM uses registry defaults, operator routes expose capability summaries, and local plus SDK specialist prompts now follow acceptance-driven task packets instead of tactics-game defaults.
- Review Notes: Execution completed on 2026-03-30 for the current first-pass scope. Slice 1 added registry-backed routing and PM defaults; Slice 2 hardened Architect, Developer, Design, and SDK specialist prompts against tactics-game leakage and validated the result with 44 passing tests. Follow-on memory continuity remains a separate PK-083 concern. Operator accepted closure on 2026-03-30 after canonical evidence review.

### Review the visual pipeline contract and design review operating model baseline
- ID: PK-074
- Kind: request
- Status: completed
- Owner: Project Orchestrator
- Assigned Role: Project Orchestrator
- Priority: high
- Requires Approval: yes
- Review State: Accepted
- Milestone: M8 - Visual Production And Digital Asset Management
- Expected Artifact: projects/program-kanban/governance/M7_IMAGE_ASSET_PIPELINE_AND_DESIGN_REVIEW_SPEC_2026-03-26.md
- Objective: Approve the baseline visual pipeline contract so later design and image tasks share one intake, review, storage, and handoff model.
- Details: Review the baseline contract that defines chat-first visual intake, bounded clarification, canonical artifact storage on disk, SQLite metadata indexing, and control-room review. This completed governance task now serves as the predecessor planning receipt for the later M8 visual-production milestone after the studio ladder rewrite.
- Result: Visual pipeline operating contract approved as the planning baseline. No runtime implementation shipped in this task.
- Review Notes: Drafted from architect and design review plus current official OpenAI image and agent guidance.
Accepted by Studio Lead on 2026-03-27 as a governance/planning checkpoint. The task approves the M7 contract; implementation remains in follow-on tasks. Re-contextualized under M8 after the studio milestone ladder rewrite on 2026-03-27.

### Implement the design request preview and clarification gate
- ID: PK-075
- Kind: request
- Status: completed
- Owner: QA
- Assigned Role: Project Orchestrator
- Priority: high
- Requires Approval: no
- Review State: Accepted
- Milestone: M8 - Visual Production And Digital Asset Management
- Expected Artifact: agents/orchestrator.py
- Objective: Start design work from an approved preview packet so the design lane does not jump from vague chat input straight into implementation.
- Details: Add a chat-aligned design request packet so the Orchestrator can preview goal, target surface, style direction, deliverables, constraints, and open questions before generation starts. The design specialist should ask at most three blocking questions when critical information is missing.
- Result: Design request previews now create tracked prompt-specialist API usage and pause for clarification before downstream execution.
- Review Notes: April 2, 2026 audit confirmed fresh API usage on tracked PK-075 runs. Root cause was split runtime visibility plus a milestone-normalization gap in request-preview execution.

### Add a deliverable contract schema for code, image, audio, map, review, and implementation handoff
- ID: PK-084
- Kind: request
- Status: completed
- Owner: QA
- Assigned Role: Architect
- Priority: high
- Requires Approval: no
- Review State: Accepted
- Milestone: M8 - Visual Production And Digital Asset Management
- Expected Artifact: agents/schemas.py
- Objective: Create a shared deliverable contract model for the studio capability ladder.
- Details: Define the first explicit deliverable contract schema so the studio can reason about code, image, audio, map, review, and implementation-handoff outputs consistently. The first pass should clarify what metadata, provenance, review state, and downstream references each deliverable type must carry.
- Result: Accepted as the implemented M8 foundation baseline after the paused-board drift was reconciled with the code and artifact evidence.
- Review Notes: Accepted on 2026-04-02 when M8 resumed under the API-first model. The deliverable-contract slice had already landed in code and tests before the milestone pause.

### Add Orchestrator context receipts and restore-safe compaction
- ID: PK-083
- Kind: request
- Status: completed
- Owner: QA
- Assigned Role: Developer
- Priority: high
- Requires Approval: no
- Review State: Accepted
- Milestone: M7 - Studio Foundations
- Expected Artifact: agents/orchestrator.py
- Objective: Make the Orchestrator and delegated specialists resilient to long conversations and restore events through explicit context receipts.
- Details: Add structured continuity receipts so the Orchestrator and delegated specialists can preserve the current decision frame, accepted assumptions, open questions, prior artifact lineage, allowed tools, allowed paths, and next-step contract across long-running conversations and restore events. The first pass should reduce restart cost without inventing work that was never executed.
- Result: Continuity receipts now preserve operator and specialist context across orchestration, approval pauses, restore, and resume flows.
- Review Notes: Accepted on 2026-03-30 after slice-1 and slice-2 implementation plus PK-099 proof coverage validated restore-aware continuity end to end.

### Restore canonical runtime store and operator control API alignment
- ID: PK-094
- Kind: request
- Status: completed
- Owner: Architect
- Assigned Role: Architect
- Priority: high
- Requires Approval: yes
- Review State: Accepted
- Milestone: M7 - Studio Foundations
- Expected Artifact: sessions/store.py
- Objective: Restore the canonical runtime store and operator control API alignment before adding safeguard enforcement.
- Details: Bring SessionStore, operator API, CLI, and control-room snapshot back onto the same canonical runtime surface so the studio can enforce contract truth from one place instead of drifting across mismatched helpers.
- Result: Completed for the narrowed safeguard scope on 2026-03-27: canonical store/import/CLI/snapshot alignment restored and verified through delegated implementation, targeted tests, and manual Program Kanban snapshot smokes. Broader Orchestrator compatibility remains intentionally out of scope for later safeguard tasks.
- Review Notes: Created on 2026-03-27 as the first M7 safeguard task after repeated Orchestrator delegation-contract breaches.

Closed on 2026-03-27 after delegated implementation and QA for the narrowed safeguard scope only. Scope covered canonical store/import/CLI/snapshot alignment; later Orchestrator compatibility remains out of scope.

### Freeze the Orchestrator delegation contract and execution-mode policy
- ID: PK-095
- Kind: request
- Status: completed
- Owner: Project Orchestrator
- Assigned Role: Architect
- Priority: high
- Requires Approval: yes
- Review State: Accepted
- Milestone: M7 - Studio Foundations
- Expected Artifact: agents/config.py
- Objective: Lock the runtime execution-mode and delegation policy so the Orchestrator and PM cannot drift into local implementation.
- Details: Define the runtime execution modes, deterministic-local boundary, delegation thresholds, and the narrow approved-local-exception rule so Orchestrator and PM cannot silently drift into implementation.
- Result: Completed for the approved safeguard scope on 2026-03-27: runtime mode policy, deterministic board-action routing, preview/dispatch/resume compatibility, and PM dispatch-approval behavior are implemented and QA-passed. Worker-only write enforcement remains intentionally deferred to PK-096.
- Review Notes: Created on 2026-03-27 as part of the M7 safeguard slice.

Started delegated execution on 2026-03-27 with Architect-defined contract and parallel worker ownership split across orchestrator/config and PM.

Moved to in review on 2026-03-27 after delegated implementation and QA PASS for the approved PK-095 scope. PK-096 planning started, but implementation remains blocked.

Closed on 2026-03-27 after delegated implementation and QA PASS for the approved PK-095 scope. Worker-only write enforcement remains deferred to PK-096.

### Enforce worker-only implementation with sealed write-scope manifests
- ID: PK-096
- Kind: request
- Status: completed
- Owner: Project Orchestrator
- Assigned Role: Developer
- Priority: high
- Requires Approval: yes
- Review State: Accepted
- Milestone: M7 - Studio Foundations
- Expected Artifact: agents/orchestrator.py
- Objective: Enforce exact-path worker write boundaries so delegated implementation cannot escape the approved manifest scope.
- Details: Block local implementation for delegated work unless a run carries a sealed manifest defining role, allowed paths, expected outputs, and write scope. Out-of-scope writes must fail closed.
- Result: Completed for the approved safeguard scope on 2026-03-28: PM now issues sealed manifests, delegated artifact work flows through the worker boundary, and worker/tools enforce exact-path fail-closed write scope. Breach ledger and compliance surfacing remain intentionally deferred to PK-097+.
- Review Notes: Created on 2026-03-27 as part of the M7 safeguard slice.

Started delegated execution on 2026-03-27 with disjoint worker ownership across orchestrator/pm and worker/tools for sealed write-scope manifest enforcement.

Moved to in review on 2026-03-28 after delegated implementation and QA PASS for the approved PK-096 scope. Breach ledger and compliance surfacing remain downstream in PK-097+.

Closed on 2026-03-28 after delegated implementation and QA PASS for the approved PK-096 scope. Breach ledger and compliance surfacing remain deferred to PK-097+.

### Add breach pause behavior, local-exception approval, and compliance ledger
- ID: PK-097
- Kind: request
- Status: completed
- Owner: Project Orchestrator
- Assigned Role: Developer
- Priority: high
- Requires Approval: yes
- Review State: Accepted
- Milestone: M7 - Studio Foundations
- Expected Artifact: sessions/store.py
- Objective: Add breach pause behavior, local-exception approval, and a compliance ledger.
- Details: Add immutable breach/compliance records, pause behavior for policy and budget violations, and a one-shot operator approval flow for rare framework-repair local exceptions.
- Review Notes: Completed for the approved safeguard scope: compliance ledger, breach pause, and local-exception flow implemented and QA-verified. Repeated breaches now record separate immutable breach rows. Residual risk accepted: second-precision created_at ordering may make latest/list selection nondeterministic in same-second cases.

### Make Program Kanban surfaces compliance-aware
- ID: PK-098
- Kind: request
- Status: completed
- Owner: QA
- Assigned Role: Dashboard Implementer
- Priority: medium
- Requires Approval: no
- Review State: Accepted
- Milestone: M7 - Studio Foundations
- Expected Artifact: projects/program-kanban/app/app.js
- Objective: Expose compliance truth across Program Kanban, the operator API, wall snapshots, and the CLI so enforcement state is auditable at a glance.
- Details: Expose execution mode, manifests, pause reasons, breach counts, and local-exception state in Program Kanban, the operator API, the wall snapshot, and the CLI so the operator can see enforcement truth directly.
- Result: Compliance truth is exposed across Program Kanban UI, operator API, wall snapshot, CLI, and canonical run evidence.
- Review Notes: Accepted on 2026-03-30 after canonical review. UI syntax check passed and the targeted compliance suite passed with 31 tests.

### Add the contract QA matrix for delegation drift and boundary enforcement
- ID: PK-099
- Kind: request
- Status: completed
- Owner: QA
- Assigned Role: QA
- Priority: high
- Requires Approval: no
- Review State: Accepted
- Milestone: M7 - Studio Foundations
- Expected Artifact: tests/test_orchestrator.py
- Objective: Prove safeguard enforcement with a focused QA matrix so delegation boundaries, breach handling, and safe resume behavior remain trustworthy.
- Details: Prove the safeguard slice with tests that cover deterministic board actions, delegated worker runs, SDK runs, path violations, budget violations, local exceptions, and safe resume behavior.
- Result: Expanded the safeguard QA matrix, fixed failure-state evidence preservation, and passed the broader 53-test M7 proof suite.
- Review Notes: Accepted on 2026-03-30 after the focused PK-099 proof suite passed with 47 tests and the broader M7 suite passed with 53 tests. Worker-boundary failures now preserve manifest evidence during failure handling.

### Recover local Codex workflow from crash-era Git noise
- ID: PK-100
- Kind: request
- Status: completed
- Owner: QA
- Assigned Role: Architect
- Priority: high
- Requires Approval: no
- Review State: Accepted
- Milestone: M7 - Studio Foundations
- Expected Artifact: projects/program-kanban/governance/wiki/PROGRAM_KANBAN_STUDIO_OPERATIONS_WIKI.md
- Objective: Retire crash-era root confusion and document the safe local recovery path for Codex operation without broad cleanup risk.
- Details: Stabilize the local AI Studio operator workflow after the workspace crash by separating the live repo from stale roots, noisy deletions, and runtime artifacts, then define a safer recovery path before any broad cleanup or remote migration.
- Result: Original crash-recovery placeholder closed as superseded by PK-101 recovery execution and PK-102 hygiene follow-on tracking.
- Review Notes: Accepted on 2026-04-02 as a provenance placeholder only. Recovery execution moved through PK-101 and repo-hygiene follow-on remains tracked separately.

### Stabilize Git workspace and define a Codex-safe repo recovery architecture
- ID: PK-101
- Kind: request
- Status: completed
- Owner: QA
- Assigned Role: Project Orchestrator
- Priority: high
- Requires Approval: no
- Review State: Accepted
- Milestone: M7 - Studio Foundations
- Expected Artifact: projects/program-kanban/artifacts/git_codex_recovery_options.md
- Objective: Contain the broken Git workspace safely and define a durable recovery architecture for the active Codex lane before larger cleanup.
- Details: Emergency task to diagnose the current Git/worktree breakage affecting local Codex operation, contain the immediate repo-risk safely, and produce operator-facing options for a durable professional fix before execution.
- Result: The Codex-safe recovery architecture is implemented and accepted: the active workspace now runs from the non-OneDrive sparse worktree and the recovery options are recorded canonically.
- Review Notes: Accepted on 2026-04-02 after the active Codex lane was recovered into C:\Users\rodne\Dev\_AIStudio_worktrees\studio-control and the recovery artifact plus validation evidence were preserved.

### Repair orchestrator continuity, memory persistence, and specialist ownership contracts
- ID: PK-103
- Kind: request
- Status: completed
- Owner: QA
- Assigned Role: Architect
- Priority: high
- Requires Approval: no
- Review State: Accepted
- Milestone: M7 - Studio Foundations
- Expected Artifact: projects/program-kanban/artifacts/process_reliability_repair_plan.md
- Objective: Repair the operator/orchestrator framework so continuity, specialist ownership, task standards, and API-backed delegation behave reliably without weekly reconfiguration.
- Details: Framework repair task to address workflow drift, weak specialist continuity, non-standard task identity behavior, unreliable memory handoff, and the mismatch between intended orchestrator/API contracts and actual execution behavior.
- Result: Framework repair is complete for the current lane: continuity, specialist ownership, compliance truth, and safeguard proof gates are now implemented and accepted.
- Review Notes: Accepted on 2026-04-02 after PK-066, PK-083, PK-098, and PK-099 all closed with canonical evidence and passing proof. The next active lane is PK-104 for official connector baseline work.

### Add official connector and MCP baseline for Figma and OpenAI tooling
- ID: PK-104
- Kind: request
- Status: completed
- Owner: QA
- Assigned Role: Architect
- Priority: high
- Requires Approval: no
- Review State: Accepted
- Milestone: M7 - Studio Foundations
- Expected Artifact: projects/program-kanban/governance/M7_CONNECTOR_BASELINE_SPEC_2026-03-30.md
- Objective: Establish the official connector baseline for Figma and OpenAI tooling so the studio can use native external tools without falling back into ad hoc prompt drift.
- Details: Add the missing connector baseline task so the studio can adopt official Figma and OpenAI tooling through governed setup, trust rules, and a clean handoff into visual and audio production lanes.
- Result: Official connector baseline is now defined canonically for Figma and OpenAI tooling, including trust rules, sequencing, and the current shell blocker on codex mcp activation.
- Review Notes: Accepted on 2026-04-02 as the M7 connector-baseline governance task. Actual connector activation and downstream implementation now move into the next milestone wave.

### PHASE 1 - SYSTEM DESIGN
- ID: PK-106
- Kind: request
- Status: completed
- Owner: QA
- Assigned Role: Architect
- Priority: high
- Requires Approval: no
- Review State: Accepted
- Milestone: M11 - API-First Hybrid Execution Model
- Expected Artifact: governance/ARCHITECTURE.md
- Objective: Design the hybrid execution model with three agent tiers, model mapping, routing, escalation, and approval surfaces before code changes continue.
- Details: Produce the architecture, tier policy, and routing-rule documents that define how ChatGPT and API execution interact. This phase must stay markdown-first and become the reference baseline for later implementation.
- Result: Delivered architecture, tier policy, and routing-rule governance for the API-first hybrid model.
- Review Notes: Accepted on 2026-04-02 after the design baseline landed in governance markdown and aligned with the code implementation plan.

### PHASE 2 - TASK DECOMPOSITION ENGINE
- ID: PK-107
- Kind: request
- Status: completed
- Owner: QA
- Assigned Role: Project Orchestrator
- Priority: high
- Requires Approval: no
- Review State: Accepted
- Milestone: M11 - API-First Hybrid Execution Model
- Expected Artifact: governance/TASK_DECOMPOSITION.md
- Objective: Make every incoming delegated task pass through classification, tier assignment, and decomposition before execution begins.
- Details: Upgrade the Orchestrator and PM flow so each delegated task carries a task profile, assigned tier, decomposition packet, expected output format, and acceptance criteria.
- Result: Implemented mandatory task classification, tier assignment, and decomposition before delegated execution.
- Review Notes: Accepted on 2026-04-02 after the Orchestrator and PM flow enforced task profiling and decomposition before delegated work.

### PHASE 3 - API EXECUTION LAYER
- ID: PK-108
- Kind: request
- Status: completed
- Owner: QA
- Assigned Role: Developer
- Priority: high
- Requires Approval: no
- Review State: Accepted
- Milestone: M11 - API-First Hybrid Execution Model
- Expected Artifact: agents/api_router.py
- Objective: Add the tier-aware API routing and cost-tracking layer so execution can shift out of ChatGPT-heavy flows and into explicit API calls.
- Details: Implement the reusable API router, cost tracker, and execution log conventions so task runs can select models by tier, log usage, and persist outputs into the project structure.
- Result: Delivered the tier-aware API router and cost tracker baseline with canonical usage logging.
- Review Notes: Accepted on 2026-04-02 after API routing, usage recording, and cost estimation passed focused and broader tests.

### PHASE 4 - GOVERNANCE AND APPROVALS
- ID: PK-109
- Kind: request
- Status: completed
- Owner: QA
- Assigned Role: Project Orchestrator
- Priority: high
- Requires Approval: no
- Review State: Accepted
- Milestone: M11 - API-First Hybrid Execution Model
- Expected Artifact: governance/APPROVAL_RULES.md
- Objective: Add approval rules and operator-facing approval packets for expensive, senior-tier, or architecture-changing work.
- Details: Define approval gates for Tier 1 usage, expensive tasks, and architecture changes, then implement approval packets that explain need, expected cost, and risk of not proceeding.
- Result: Delivered approval rules and reusable approval packet templates for senior, large, and architecture-changing work.
- Review Notes: Accepted on 2026-04-02 after approval gates and templates were captured in the governance layer.

### PHASE 5 - TESTING WITH CONTROLLED SCENARIOS
- ID: PK-110
- Kind: request
- Status: completed
- Owner: QA
- Assigned Role: QA
- Priority: high
- Requires Approval: no
- Review State: Accepted
- Milestone: M11 - API-First Hybrid Execution Model
- Expected Artifact: governance/TEST_RESULTS.md
- Objective: Prove the tiering and routing rules with controlled scenarios before wider rollout.
- Details: Run a small, medium, and ambiguous scenario through the new execution model, verify the correct tiering, and capture the results in a reviewable markdown report.
- Result: Validated the execution model through controlled routing scenarios and regression tests.
- Review Notes: Accepted on 2026-04-02 after controlled scenario tests and the broader regression suite both passed.

### PHASE 6 - OPTIMIZATION LOOP
- ID: PK-111
- Kind: request
- Status: completed
- Owner: QA
- Assigned Role: Architect
- Priority: high
- Requires Approval: no
- Review State: Accepted
- Milestone: M11 - API-First Hybrid Execution Model
- Expected Artifact: governance/OPTIMIZATION_REPORT.md
- Objective: Analyze cost, escalation, and failure signals from the new model and propose the next efficiency improvements.
- Details: Review token usage, cost estimates, escalation frequency, and failure patterns from the controlled scenarios, then publish an optimization report with concrete next actions.
- Result: Published optimization findings, execution logs, and the operator-facing summary for the new workstream.
- Review Notes: Accepted on 2026-04-02 after the optimization report, execution logs, and workstream summary were published.

### Implementation Capability Architecture
- ID: PK-112
- Kind: subtask
- Status: completed
- Owner: QA
- Assigned Role: Architect
- Priority: high
- Requires Approval: no
- Review State: Accepted
- Parent Task: PK-075
- Milestone: M8 - Visual Production And Digital Asset Management
- Expected Artifact: projects/program-kanban/artifacts/implementation_architecture.md
- Objective: Define the architecture and routing contract for Implementation.
- Details: Write an implementation-ready architecture note for Implementation covering scope, constraints, routing, risks, and acceptance criteria.
- Result: QA approved the artifact.
- Review Notes: QA approved the artifact.
