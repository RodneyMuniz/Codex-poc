# Program Kanban M7 Image Asset Pipeline And Design Review Spec

This document captures the next planned enhancement cycle for the Program Kanban framework after the control-room, SDK-specialist runtime, and trust/restore baseline are operational.

Decision date:
- `2026-03-26`

Decision source:
- Studio Lead request to prepare an image-asset pipeline milestone for the framework
- architect review of storage, runtime boundaries, and artifact lineage
- design review of request intake, clarification UX, and comparison workflow
- current official OpenAI guidance for image generation and manager-plus-specialist orchestration

## Goal

Make the framework capable of handling real design requests, image-concept generation, artifact review, and design-to-implementation handoff without losing traceability, approval control, or canonical artifact discipline.

## Why This Milestone Exists

The framework can already orchestrate tasks, approvals, and specialist work, but it does not yet have a clean operating model for visual artifacts. That gap becomes important as the TacticsGame project moves from pure UI polish into a real art and design pipeline.

The milestone exists to make these workflows operational:
- you ask for a visual concept or design direction in chat
- the Orchestrator translates that into a bounded design request
- the design or artist specialist asks only the missing blocking questions
- the specialist produces concepts and stores them durably
- the control room shows the resulting artifacts in a reviewable, comparable format
- one design direction can be approved and later consumed by an implementation task

## Grounded Recommendations

### Architect recommendation

- Keep canonical design artifacts on disk under `projects/<project>/artifacts/design/`
- Keep SQLite as the metadata index, not the binary image store
- Keep the Program Kanban control room as the operator-facing review surface
- Do not let the design specialist write directly into app source folders
- Treat approved design artifacts as explicit inputs to later implementation work

### Designer recommendation

- Keep request intake chat-first, not form-first
- Show a short `Design Request Preview` before generation starts
- Let the design specialist ask at most `3` blocking questions at a time
- Make review variant-first, not file-first
- Show comparison, zoom, approve, reject, and revise-from-selected-variant in the control room
- Keep the gallery in the control room for the first pass rather than creating a separate review site

## External Guidance Used

OpenAI image guidance currently supports an iterative image workflow with the latest image model, explicit input and output modalities, image-generation and edit endpoints, and format controls such as `png`, `jpeg`, `webp`, and compression. The current multi-agent guidance also continues to recommend the manager-plus-specialist pattern when one agent should keep control of the conversation and call specialists for bounded subtasks.

Additional practical guidance for manual asset import remains useful:
- Figma export supports exporting frames, slices, pages, and nested folder structures from naming conventions
- larger binary-asset policy should be captured explicitly before the repo starts accumulating many generated images or source files

## Proposed Operating Model

### Intake

- Chat remains the main surface for natural-language design requests
- The Orchestrator creates a `Design Request Preview` with:
  - target project
  - target surface
  - goal
  - requested deliverables
  - visual direction
  - constraints
  - open questions
- The operator approves that preview before generation starts

### Clarification

- The design or artist specialist must not jump directly into generation from a vague request
- If critical information is missing, the specialist asks at most `3` grouped blocking questions
- If enough is already clear, the specialist should produce first-pass options instead of over-questioning

### Storage

- Canonical design artifacts live on disk:
  - `projects/<project>/artifacts/design/<request-slug>/<timestamp>/`
- SQLite stores metadata only:
  - request id
  - prompt and version summary
  - model and provider
  - parent artifact id
  - review state
  - selected direction flag
  - file paths
  - file hashes

### Review

- The Program Kanban control room gets a `Design Review` surface
- The gallery is derived from canonical folder artifacts and SQLite metadata
- The first review surface should support:
  - thumbnail grid
  - side-by-side compare for up to `3` variants
  - zoom
  - variant label such as `A`, `B`, `C`, `B2`
  - short rationale
  - prompt summary
  - run and task provenance
  - approve, reject, and request revision actions

### Handoff To Build

- Approved design artifacts become explicit inputs to later implementation tasks
- Implementation work must reference the approved artifact id or path rather than consuming an unreviewed concept by assumption

## Canonical Decision

For the first pass, the correct model is:
- folder on disk as the canonical design artifact store
- SQLite as the canonical metadata and review-state index
- control-room gallery as the operator-facing review surface

This is better than a gallery-only site because it avoids drift between what exists on disk and what the operator sees.

## Non-Goals For The First Pass

This milestone does not require the first build wave to:
- create a production-quality art pipeline for sprites or isometric scenes
- replace chat as the primary request surface
- make the gallery a public website
- store binary image blobs inside SQLite
- let the design specialist directly edit application code
- solve final outsourced art-production workflow

## Planned Task Wave

The initial task set for this milestone should cover:
- design request contract and clarification gate
- canonical artifact storage and manifest/index rules
- control-room design review gallery
- variant comparison and revision lineage
- approved-design-to-implementation bridge
- OpenAI image-generation specialist runtime and provenance capture
- large-asset storage policy
- manual external-asset import lane

## Success Criteria

`M7` is successful only when all of the following are true:
- a design request can be captured through the framework without losing operator intent
- the design specialist can ask bounded follow-up questions instead of generating blindly
- generated or imported design artifacts land in a canonical on-disk folder structure
- the control room can display and compare those artifacts with provenance
- one artifact can be explicitly marked as the approved direction
- later implementation tasks can reference that approved direction cleanly
- the repo has an explicit storage rule for growing image assets and external source files
