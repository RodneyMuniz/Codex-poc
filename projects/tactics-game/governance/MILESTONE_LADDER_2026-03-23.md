# TacticsGame Milestone Ladder

Date: 2026-03-23

This roadmap reorganizes the imported TacticsGame board into milestone-based planning in the canonical SQLite store.

## Approved Planning Decisions

- Near-term focus stays on the local playable prototype and combat foundations before heavier progression work.
- `TG-101` belongs in the playable-surface milestone.
- `TG-062` and `TG-063` are the first build-ready combat-foundation tasks.
- `TG-064` through `TG-069` remain follow-on combat tasks behind the first metadata and blocker groundwork.
- The current magical baseline from `TG-058` and `TG-068` stays fixed for now.
- `TG-089` waits behind `TG-083` and `TG-094`.
- AI stays later until the playable prototype and combat foundations are clearer.

## Milestones

### M0 - Sandbox Foundation And First Combat Slice

Entry:
Core sandbox rules and the first local tactical slice are not yet proven.

Exit:
The local tactical sandbox is playable and stable, with core deployment, objectives, first combat extensions, and initial presentation support already validated.

Included work:
Historical completed foundation work such as the original sandbox packets, first implementation slice, setup and objective flow, terrain objects, first magical slice, and first presentation improvements.

### M1 - Playable Prototype Surface And Visual Cohesion

Entry:
The sandbox is playable, but the battle surface, panel structure, and visual language still feel fragmented.

Exit:
The playable prototype has a reviewed battle-screen flow, coherent UI structure, stronger battle-panel direction, and clear visual-identity guidance for the next implementation pass.

Primary tasks:
`TG-070`, `TG-071`, `TG-072`, `TG-073`, `TG-085`, `TG-086`, `TG-087`, `TG-098`, `TG-101`

### M2 - Combat Model Expansion Foundations

Entry:
The prototype works, but combat semantics are still partly encoded in narrow rules and terminology.

Exit:
The next-step combat metadata, blocker vocabulary, delivery-path separation, and family-aware expansion path are shaped cleanly enough to guide implementation without reopening approved baselines.

Primary tasks:
`TG-062`, `TG-063`, `TG-064`, `TG-065`, `TG-066`, `TG-067`, `TG-069`

### M3 - Progression And Meta-Loop Foundation

Entry:
The battle prototype exists, but roster growth, economy, persistence, and mission-loop structure are not yet grounded in a shared architecture.

Exit:
The project has a modular progression foundation covering growth vision, economy shape, persistence direction, and safe testing controls.

Primary tasks:
`TG-083`, `TG-089`, `TG-094`, `TG-095`, `TG-088`, `TG-090`, `TG-091`, `TG-092`, `TG-093`, `TG-084`, `TG-050`

### M4 - Content, AI, And Expansion Lanes

Entry:
Expansion ideas exist, but mission variety, AI, and tooling are still broad future concepts.

Exit:
Mission, AI, and pipeline lanes are defined well enough to guide later execution without pretending they belong in the current prototype milestone.

Primary tasks:
`TG-051`, `TG-052`, `TG-096`, `TG-097`

### M5 - Deferred Post-Prototype Platform Work

Entry:
Some ideas are known, but intentionally out of current scope.

Exit:
These items are reconsidered only after the playable prototype and the first progression foundations are stable enough to justify expansion.

Primary tasks:
`TG-060`, `TG-061`

## Ready-For-Build Promotions From This Pass

- `TG-094` is promoted as the first M3 architecture gate.
- `TG-101` is promoted as the first M1 surface refinement task.
- `TG-089` is moved back behind `TG-083` and `TG-094`.
