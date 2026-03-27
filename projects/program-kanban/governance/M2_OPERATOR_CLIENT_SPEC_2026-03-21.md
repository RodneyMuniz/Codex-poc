# Program Kanban M2 Operator Client And Traceable Delegation Spec

This document captures the minimum operator-client requirements needed to make the Program Kanban app the trusted control room for the studio runtime.

This spec has been refined after live operator testing:
- the Codex chat remains the best primary surface for natural-language orchestration
- the Program Kanban app should not try to replace chat as the main conversational client
- the Program Kanban app should instead be the trusted control room for approvals, run visibility, evidence, artifacts, and board state

Decision date:
- `2026-03-21`

Decision source:
- Studio Lead request in the current orchestration thread

## Goal

Make the Program Kanban app the real operator-facing control room for the studio runtime.

This milestone succeeds when the Studio Lead can monitor, interrupt, resume, and review a framework run from the app itself, while still being free to use chat as the primary natural-language interface.

## Why This Milestone Exists

The current framework already has useful runtime pieces:
- canonical SQLite persistence
- board and milestone views
- approvals and resume support in the CLI
- worker subprocess execution
- artifact and validation evidence

The current weak link is the operator surface:
- this Codex thread can still mix manual implementation work with framework work
- the wall originally tried to become a full Orchestrator chat client, but that is not its strongest role
- the wall must instead become excellent at approvals, run control, evidence, and trace visibility
- approvals and resume originally depended on CLI flows rather than the operator client

## Minimum Success Condition

The milestone is complete only when all of the following are true:
- the app can display approvals, recent runs, traces, artifacts, and validations from the canonical runtime store
- the PM and specialist handoff chain is persisted as visible runtime evidence
- approvals can pause and resume the run from the app
- the operator can inspect artifacts, validations, and the final summary from the app
- the final proof run clearly shows that the flow was driven by the framework and not by this Codex thread
- optional web dispatch is available, but the operating model does not require the website to be the main conversational surface

## Non-Goals For This Pass

The first pass does not need to include:
- true parallel execution
- editable role prompts from the UI
- advanced cost dashboards
- multi-operator permissions
- external hosting or authentication
- complex real-time collaboration beyond simple refresh and reload

## Required Operator Surfaces

### 1. Control Room Guidance

The app must clearly explain the intended operator workflow:
- use chat for natural-language thinking, clarification, and iteration
- use the app for approvals, traces, artifacts, validations, and board state
- use optional web dispatch only for bounded direct actions or when chat is not the active surface

Minimum first-pass behavior:
- the app communicates that it is the runtime control room
- the app does not imply that the website is better than chat at natural-language orchestration
- optional dispatch controls remain available, but visually secondary to approvals and evidence

### 2. Optional Web Dispatch

The app may provide a lightweight Orchestrator-facing request surface where the Studio Lead can:
- enter a bounded request
- preview the Orchestrator interpretation
- confirm a dispatch when appropriate

Minimum first-pass behavior:
- the request surface is secondary, not the dominant control-room element
- the Orchestrator interpretation is persisted as a structured packet
- direct board actions and bounded dispatches are supported

### 3. Approval Inbox

The app must surface pending approvals clearly.

Each approval should show:
- requesting role
- target role
- exact task
- expected output
- why now
- risks
- current run and task references

Minimum first-pass controls:
- approve
- reject
- resume the paused run after approval

### 4. Run Trace

The app must provide a trace view for the selected run.

The trace must show the handoff chain as explicit records, not implied status changes.

Minimum first-pass events:
- operator message received
- orchestrator interpretation created
- clarification requested
- operator confirmation recorded
- PM dispatch packet created
- worker input packet sent
- worker result packet received
- approval requested
- approval decided
- run resumed
- validation recorded
- orchestrator final summary published

### 5. Evidence Inspector

The app must provide a run detail surface where the operator can inspect:
- delegation edges
- agent runs
- produced artifacts
- validation records
- final summary

Minimum first-pass goal:
- every finished run in the client can be audited without dropping into raw SQL

## Canonical Persistence Requirements

The runtime must persist structured trace and packet data in the canonical SQLite store.

Minimum first-pass persistence:
- each trace event has a type, timestamp, run id, task id, source role, and payload
- each worker handoff stores both a summary and the structured packet body
- each worker result stores both a summary and the structured result body
- each final orchestrator response links to the run that produced it

The trace must remain available after refresh and across restarts.

## Role Routing Visibility Requirements

The operator client must make the runtime route explainable.

Minimum first-pass visibility:
- which role was selected
- which model was selected
- which skill or profile instructions were used
- why that route was chosen at a short summary level

First-pass scope:
- read-only visibility is enough
- editing role profiles from the UI is not required yet

## Trust And Review Rules

The app must not present a run as complete unless the stored runtime evidence supports that claim.

Minimum trust rules:
- final completion must still depend on validation and review status
- the final summary shown to the operator must be linked to the run id
- the trace must distinguish framework execution from manual notes or commentary
- proof artifacts for the demonstration run must be exportable from the canonical store

## Proof Scenario For Milestone Closure

Milestone closure requires a real end-to-end proof run performed from the operator client.

The proof run must show:
- request entered in the app
- Orchestrator clarification or interpretation persisted
- dispatch preview accepted
- PM dispatch recorded
- at least one specialist worker receiving a structured packet
- at least one specialist worker returning a structured result
- approval pause and resume performed from the app
- artifact and validation evidence visible in the app
- final operator-facing summary linked to the proof run

## Derived Task Queue

Definition and review:
- `TGD-048` define and review the M2 operator-client trust boundary and proof criteria

Implementation:
- `TGD-049` add operator-client request intake and dispatch confirmation flow
- `TGD-050` add operator actions API for request, approval, rejection, and resume
- `TGD-051` persist the orchestration trace ledger and handoff packets
- `TGD-052` add a run inspector for trace, delegation, artifacts, validation, and final summary
- `TGD-053` expose role profiles, model routing, and skill metadata in operator views
- `TGD-054` prove an end-to-end app-driven orchestration run that bypasses chat dependence
