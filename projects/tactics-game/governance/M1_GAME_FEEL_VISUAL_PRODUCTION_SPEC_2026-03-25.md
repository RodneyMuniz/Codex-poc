# TacticsGame M1 Visual Production Spec

Date: 2026-03-25

## Purpose

Convert the current playable tactics sandbox from a clear proof of concept into a prototype that feels more like a game. This pass should improve board atmosphere, unit readability, and battle HUD presentation without changing core rules or depending on a custom art pipeline.

## Approved Direction

- Base visual direction: `Gilded War Table`
- Secondary influence: `Field Manual Ops` readability discipline
- First-pass scope: board, units, and battle HUD
- Board perspective: keep the current tapered grid for this pass
- Unit identity: heraldic tokens and crests rather than portrait cards
- Motion level: moderate game-feel polish, not heavy spectacle
- Asset strategy: CSS, SVG, layout, iconography, and motion first; no custom art dependency
- Right-side battle panel work is included in this same pass
- Combat-foundation and progression-architecture packets remain valid but are not the current build focus

## What This Pass Must Achieve

- The battlefield should read as a deliberate play surface instead of a prototype grid.
- Units should be distinguishable at a glance by side, class, and state.
- The right-side battle panel should feel more like a game HUD and less like stacked text blocks.
- Setup mode should visually belong to the same world as battle mode.
- The resulting UI should still preserve tactical clarity and not hide the approved gameplay signals.

## Explicit Non-Goals

- no combat-rule rewrite
- no progression systems
- no AI work
- no custom illustration pipeline
- no true isometric board conversion yet
- no heavy animation system

## Revalidated Backlog Position

### Immediate visual-production inputs

- `TG-070`
- `TG-071`
- `TG-072`
- `TG-073`
- `TG-085`
- `TG-086`
- `TG-087`
- `TG-098`
- `TG-101`

These older tasks remain useful as planning references, but the build should now proceed through implementation-facing tasks rather than waiting on each older document packet to be individually reviewed.

### Parked but still valid

- `TG-062`
- `TG-063`
- `TG-094`

These stay ready as future gates, but they should not displace the visual-production focus.

## First Implementation Wave

1. establish the `Gilded War Table` shell and board treatment
2. upgrade unit tokens, crests, and battlefield readability
3. redesign the right-side battle HUD into a command-folio presentation
4. bring setup mode into the same visual language
5. add restrained motion and feedback polish

## Acceptance Standard

- The live TacticsGame app shows a materially stronger board identity, unit identity, and HUD hierarchy.
- The prototype feels more game-like without sacrificing clarity.
- The build remains local-first, readable, and testable.
- The new visual pass is visible in the running application, not only in planning documents.
