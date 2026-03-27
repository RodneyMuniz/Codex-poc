# Program Kanban Reset And Milestone Plan

This document defines the clean-start backlog for `Program Kanban` after reviewing the imported legacy board against the current framework-backed wall.

## Reset Goal

Reach a basic operational level for the new `Program Kanban` board so it is trustworthy for planning and build dispatch again.

That means:
- the board uses the intended delivery workflow
- tasks cannot look build-ready before requirements are complete
- milestones are visible and usable again
- task ids are easy to reference in chat
- the active board reflects the new framework, not legacy completion history

## Milestone Structure

### M1 - Basic Operation Level

Entry goal:
- the new wall is live, but it does not yet behave like the operator's real planning board

Exit goal:
- the board is usable for real planning and build preparation with clean workflow columns, milestone grouping, and operator-friendly reference behavior

Planned tasks:
- `TGD-030` Define the canonical board workflow and visible columns
- `TGD-031` Define `Ready for Build` completeness rules and transition gates
- `TGD-032` Define canonical milestone records and the orchestrator-led milestone planning cycle
- `TGD-033` Restore milestone view with grouped tasks, slim task rows, and percent completion
- `TGD-034` Restore task-id click-to-copy in approved operator surfaces
- `TGD-035` Add top-level board and milestone navigation in the operator wall
- `TGD-036` Add integrity validation for board state, milestone assignment, and completion closure

### M2 - Operator Clarity Recovery

Entry goal:
- the board is operational, but supporting operator context is still thinner than the legacy experience

Exit goal:
- the wall restores the most valuable lightweight support signals without turning into a heavy dashboard

Planned tasks:
- `TGD-037` Reintroduce a lightweight recent-updates context panel
- `TGD-038` Reintroduce lightweight hierarchy cues for role clarity
- `TGD-039` Decide and implement scoped project filtering for multi-project board use
- `TGD-040` Add milestone filtering for completed or backlog-only milestones

### M3 - Later Extensions

Entry goal:
- the board is operational and clear, and we are considering enhancements rather than core recovery

Exit goal:
- future extension ideas are captured cleanly without polluting the basic-operation milestone

Planned tasks:
- `TGD-041` Explore response-chip answers for orchestrator question flows
- `TGD-042` Plan workspace-level multi-project rollup after single-project flow is stable
- `TGD-043` Evaluate file-watch refresh after basic operation stabilizes
- `TGD-044` Evaluate richer cross-linking after the new board model settles

## Legacy-To-New Mapping

- Legacy `TGD-004`, `TGD-020`, and reset draft `TGD-027` inform `TGD-030` and `TGD-036`
- Legacy `TGD-003`, `TGD-014`, and reset draft `TGD-027` inform `TGD-031`
- Legacy `TGD-018`, `TGD-024`, `TGD-025`, and reset draft `TGD-029` inform `TGD-032`, `TGD-033`, and `TGD-035`
- Legacy `TGD-017` and reset draft `TGD-028` inform `TGD-034`
- Legacy `TGD-002` and `TGD-021` inform `TGD-037`
- Legacy `TGD-016` informs `TGD-038`
- Legacy `TGD-023` informs `TGD-039`
- Legacy backlog `TGD-019` informs `TGD-040`
- Legacy `TGD-026` informs `TGD-041`
- Legacy backlog `TGD-005`, `TGD-010`, and `TGD-011` inform `TGD-042` to `TGD-044`

## Operating Note

The active board should now be treated as a fresh implementation queue. The archived board remains preserved for traceability, but it should not define the new runtime backlog directly.
