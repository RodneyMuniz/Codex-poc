# Program Kanban M1 Basic Operation Spec

This document captures the operator-approved requirements for `M1 - Basic Operation Level`.

Decision date:
- `2026-03-21`

Decision source:
- Studio Lead review and approval in the current orchestration thread

## Goal

Bring the new `Program Kanban` board back to a trustworthy basic operational level inside the current framework.

That means:
- the board workflow matches how work should actually move
- tasks cannot look build-ready before requirements are complete
- milestones exist as first-class planning objects again
- the wall restores milestone review and task-id reference behavior
- the board stays compatible with the current SQLite-first framework

## Approved Workflow

Primary board columns:
- `Backlog`
- `Ready for Build`
- `In Progress`
- `In Review`
- `Complete`

Column meaning:
- `Backlog`: ideas and tasks with incomplete requirements
- `Ready for Build`: all required planning fields are captured and there are no active blockers
- `In Progress`: being built or being corrected
- `In Review`: waiting for Studio Lead review
- `Complete`: reviewed and closed

Secondary state treatment:
- `Blocked` and `Deferred` do not remain primary columns in the first pass
- they should be represented as secondary task states, warnings, or badges without replacing the primary workflow

Closure rule:
- `Complete` means operator-reviewed and closed

## Ready For Build Gate

A task cannot move to `Ready for Build` unless all of the following are present:
- milestone assigned
- acceptance criteria captured
- responsible owner assigned
- expected artifact or output defined
- no active blockers

First-pass enforcement direction:
- these should become real gate conditions, not just loose conventions
- missing required fields should block the transition to `Ready for Build`

## Milestone Model

Milestones are first-class canonical records in SQLite in the first pass.

First-pass milestone membership:
- each task belongs to exactly one milestone

Required milestone fields at creation:
- milestone id
- milestone title
- entry goal
- exit goal
- milestone order
- milestone status

Recommended first-pass milestone statuses:
- `planned`
- `active`
- `complete`

Planning ownership:
- the orchestrator helps define milestone goals and the required tasks for each cycle
- milestone creation and milestone updates remain operator-reviewed decisions

## Milestone View

Top-level wall navigation in the first pass:
- `Board`
- `Milestones`

Default landing view:
- `Board`

Milestone view requirements:
- tasks are grouped under milestones
- milestone-linked tasks are shown as `id + name` only
- milestone progress uses simple task-count completion: `completed tasks / total tasks`
- milestone filtering for completed or backlog-only milestones is not part of the first rebuild slice

Working assumption for first-pass presentation:
- milestone groups should start expanded by default for easier operator scanning during rebuild

## Task Id Copy Behavior

Approved first-pass behavior:
- click-to-copy is available in both `Board` and `Milestones`
- the copied content is only the task id
- a small non-blocking toast confirms success, for example `Copied TGD-034`

Working assumption:
- the same interaction should work for standard desktop click and normal browser tap behavior where clipboard support exists

## Validation Direction

First-pass validation must support trust in the planning board.

Validation priorities:
- a task cannot become `Ready for Build` if required planning fields are missing
- a task cannot silently remain build-ready if it loses a required planning field
- a task cannot reach `Complete` unless it has been reviewed and accepted
- milestone progress should reflect the same canonical task state used by the board

Working assumption for visibility:
- gate failures that affect status transitions should block the transition
- non-transition consistency problems should appear as visible warnings rather than silently passing

## Implementation Queue Derived From This Spec

Definition tasks closed by this spec:
- `TGD-030`
- `TGD-031`
- `TGD-032`
- `TGD-035`

Implementation tasks now ready from this spec:
- `TGD-033`
- `TGD-034`
- `TGD-036`

Additional implementation follow-through created from this spec:
- `TGD-045` implement the approved board workflow columns and secondary state treatment
- `TGD-046` implement first-class milestone records and single-milestone task linkage
- `TGD-047` enforce `Ready for Build` gating in canonical task transitions and validation surfaces
