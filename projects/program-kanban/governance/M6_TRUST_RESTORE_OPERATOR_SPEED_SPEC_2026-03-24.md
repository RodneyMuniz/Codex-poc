# Program Kanban M6 Trust, Restore, And Operator Speed Spec

This document captures the next enhancement cycle for the Program Kanban control room after the base board, control-room model, and SDK specialist runtime are operational.

Decision date:
- `2026-03-24`

Decision source:
- Studio Lead approval of the Architect and Designer recommendation set after completion of Program Kanban milestones `M1` through `M5`

## Goal

Improve trust, recovery, and daily operator speed without destabilizing the now-working framework foundation.

## Why This Milestone Exists

The framework is operational, but the next gains are no longer about proving that orchestration works at all. They are about making the system safer to use, faster to inspect, and easier to trust during real project work.

The strongest next opportunities are:
- safer rollback from the control room
- clearer orchestration and approval visibility
- denser, faster use on wide monitors
- better separation between deterministic framework actions and AI-delegated work
- cleaner foundations for later runtime scaling

## Target Outcomes

This milestone should leave the Program Kanban control room in a state where:
- the operator can recover from mistakes without returning to chat for manual database handling
- run history is easier to read visually
- action provenance is easier to understand at a glance
- approval review is more contextual and less mechanical
- everyday board use feels faster on wide desktop screens
- deeper runtime improvements are framed as explicit next steps instead of hidden technical debt

## Success Criteria

`M6` is complete only when all of the following are true:
- the control room exposes a safe restore flow for existing SQLite safety backups
- run inspection includes a clearer visual orchestration sequence
- deterministic framework actions and AI-delegated actions are visually distinguishable
- the board supports density modes that work well on ultrawide monitors
- approval cards show enough upstream and downstream context to be trusted quickly
- the control room exposes an always-visible health strip for backup, runtime, and approval state
- deeper architectural improvements have been captured as explicit backlog work with clear intent and non-goals

## Non-Goals For The First Ready Wave

This milestone does not require the first implementation wave to:
- replace the current SQLite control plane
- add full distributed execution
- make the wall multi-user
- redesign the core board workflow again
- expose role-prompt editing

## Ready Wave

These tasks are defined enough to move directly into `Ready for Build`:
- `TGD-064` add one-click restore for SQLite safety backups in the control room
- `TGD-069` turn the run inspector into a visual orchestration timeline
- `TGD-070` visually distinguish deterministic framework actions from AI-delegated actions
- `TGD-071` add board density modes optimized for ultrawide review
- `TGD-072` enrich approval cards with upstream and downstream context
- `TGD-073` add a persistent system health strip to the control room

## Architecture Backlog Wave

These tasks are important, but should remain in backlog until we choose to open deeper runtime and planning refactor work:
- `TGD-065` add a first-class immutable runtime event ledger separate from summary messages
- `TGD-066` add a project template registry to remove hardcoded planning assumptions
- `TGD-067` add queued worker orchestration with controlled concurrency limits
- `TGD-068` add artifact lineage and dependency views to the control room

## Derived Task Queue

Safety and control:
- `TGD-064` add one-click restore for SQLite safety backups in the control room
- `TGD-073` add a persistent system health strip to the control room

Trust and visibility:
- `TGD-069` turn the run inspector into a visual orchestration timeline
- `TGD-070` visually distinguish deterministic framework actions from AI-delegated actions
- `TGD-072` enrich approval cards with upstream and downstream context
- `TGD-068` add artifact lineage and dependency views to the control room

Operator speed:
- `TGD-071` add board density modes optimized for ultrawide review

Deeper runtime foundations:
- `TGD-065` add a first-class immutable runtime event ledger separate from summary messages
- `TGD-066` add a project template registry to remove hardcoded planning assumptions
- `TGD-067` add queued worker orchestration with controlled concurrency limits
