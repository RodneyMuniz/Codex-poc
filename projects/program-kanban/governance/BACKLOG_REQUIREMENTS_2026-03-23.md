# Program Kanban Backlog Requirements

This document captures the Studio Lead's approved requirement decisions from `2026-03-23` for the remaining Program Kanban backlog and the open M1 revision.

## Review Outcome

Accepted as complete:
- `TGD-033`
- `TGD-034`
- `TGD-036`
- `TGD-046`

Accepted with revision required:
- `TGD-045`

Requirement approval basis:
- the Studio Lead accepted all recommended defaults proposed during the `2026-03-23` backlog refinement pass

## M1 - Basic Operation Level

### TGD-045 Layout Revision

Approved direction:
- the board should use the available browser width on large screens instead of staying artificially narrow
- ultrawide layouts should prefer wider readable columns and cards over oversized surrounding whitespace
- smaller screens should preserve readable card width and allow horizontal board scrolling instead of squeezing columns too tightly

Expected first-pass outcome:
- the board feels comfortable on ultrawide monitors
- task cards remain readable in all five primary workflow columns
- the layout remains usable on smaller screens without collapsing card content

### TGD-055 Offline Launcher

Approved direction:
- create a launcher page inside the Program Kanban app folder structure
- the launcher should feel intentional and pleasant to use, not like a plain maintenance screen
- the operator gets one obvious `Start Apps` action in the first pass
- the launcher should show local status, local URLs, and log links
- after startup, both Program Kanban and TacticsGame may be opened automatically

Important constraint:
- a normal offline HTML page cannot directly spawn local processes in a standard browser
- the first pass is therefore allowed to pair the page with a supported local helper such as PowerShell, `.cmd`, or a local launcher endpoint

## M2 - Operator Client And Traceable Delegation

### TGD-048 Trust Boundary

Approved outcome:
- `M2_OPERATOR_CLIENT_SPEC_2026-03-21.md` is accepted as the trust-boundary definition for the next operator-client milestone

### TGD-049 Operator Request Intake

Approved direction:
- add an `Orchestrator` top-level view in the Program Kanban app
- the operator enters a natural-language request there
- the app shows an Orchestrator interpretation before a run begins
- clarification happens before runtime execution starts
- the request remains in a planning state until the operator confirms dispatch

Dispatch preview must include:
- goal
- chosen roles
- expected outputs
- approvals
- risks

### TGD-050 Operator Actions API

Approved direction:
- the first operator-actions API pass targets `program-kanban`
- the design should still be extensible to `tactics-game` next

Required first-pass actions:
- create request
- confirm dispatch
- approve
- reject
- resume

### TGD-051 Trace Ledger

Approved direction:
- trace events must be persisted as structured canonical records
- trace presentation must support both an operator summary and raw JSON inspection

Required first-pass events:
- `operator_message_received`
- `orchestrator_interpretation_created`
- `clarification_requested`
- `operator_confirmation_recorded`
- `pm_dispatch_packet_created`
- `worker_input_packet_sent`
- `worker_result_packet_received`
- `approval_requested`
- `approval_decided`
- `run_resumed`
- `validation_recorded`
- `orchestrator_final_summary_published`

### TGD-052 Run Inspector

Approved direction:
- the run inspector lives in the app, not only in CLI or raw SQL
- it should support a one-click JSON export of the proof and evidence packet

Required first-pass sections:
- trace
- delegations
- agent runs
- artifacts
- validations
- final summary

### TGD-053 Routing Visibility

Approved direction:
- routing should be explainable without allowing UI editing of role profiles yet

Required visible metadata:
- role
- model
- skill or profile
- route reason
- reasoning effort

### TGD-054 App-Driven Proof Run

Approved direction:
- the first end-to-end proof run should use a real board task such as `TGD-055` once that task is built
- the proof must begin from the app, not from this Codex chat
- the proof must include an approval pause and resume from the app

Required first-pass evidence:
- app-created request
- persisted handoff trace
- artifact evidence
- validation evidence
- exportable proof packet

## M3 - Operator Clarity Recovery

### TGD-037 Recent Updates Panel

Approved direction:
- add a lightweight recent-updates panel to the wall
- keep it supportive and fast to scan instead of turning it into a second trace viewer

Required item types:
- task state changes
- approvals
- run events
- artifact creation

### TGD-038 Role Clarity Cues

Approved direction:
- use subtle role badges and ownership cues
- do not introduce strong swimlanes or heavy hierarchy framing in the first pass

### TGD-039 Project Filtering

Approved direction:
- default to the current project view
- keep an optional `All Projects` view
- persist the selected project scope in the URL or equivalent client state

### TGD-040 Milestone Filters

Approved direction:
- first-pass milestone filters should be simple toggles

Required first-pass filters:
- `Hide Complete`
- `Hide Empty`

## M4 - Later Extensions

### TGD-041 Response Chips

Approved direction:
- first-pass response chips are limited to approval and clarification shortcuts
- they should accelerate common answers rather than replace freeform operator input

### TGD-042 Workspace Rollup

Working requirement direction for the first buildable pass:
- provide a read-only workspace rollup
- aggregate project-level task counts, active milestone state, and pending approvals
- keep the current project as the default focus
- do not allow inline task editing from the workspace rollup view

### TGD-043 Refresh Behavior

Approved direction:
- manual refresh remains available
- add an optional `Auto-refresh` toggle instead of forcing always-on watching
- the first-pass default is `off`
- a reasonable first-pass polling interval is `15` seconds

### TGD-044 Cross-Linking

Approved direction:
- first-pass cross-linking should prioritize:
  - task to run
  - task to artifact
- milestone to run-summary linking can wait until later
