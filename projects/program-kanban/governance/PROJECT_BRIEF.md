# Program Kanban Project Brief

- Imported project slug: `program-kanban`
- Runtime project root: `C:\Users\rodne\OneDrive\Documentos\_AIStudio_POC\projects\program-kanban`
- Runtime app root: `C:\Users\rodne\OneDrive\Documentos\_AIStudio_POC\projects\program-kanban\app`
- Legacy source root: `C:\Users\rodne\OneDrive\Documentos\_Codex Projects\Program Kanban`
- Legacy project doc: `C:\Users\rodne\OneDrive\Documentos\_Codex Projects\Program Kanban\PROJECT.md`
- Legacy kanban doc: `C:\Users\rodne\OneDrive\Documentos\_Codex Projects\Program Kanban\KANBAN.md`
- Imported task count: `21`

## One-Sentence Description
A small local read-only program board that visualizes selected project markdown state without replacing the orchestrator workflow or becoming an editing system.

## Current Status
The imported legacy Program Kanban board has been intentionally retired from the active queue and archived so the new framework-backed board can restart from a clean implementation baseline. `M1 - Basic Operation Level`, `M2 - Operator Client And Traceable Delegation`, `M3 - Operator Clarity Recovery`, `M4 - Later Extensions`, and `M5 - SDK-Native Runtime Migration` are complete. `M6 - Trust, Restore, And Operator Speed` remains the active enhancement cycle. `M7 - Image Asset Pipeline And Design Review` is now planned so the framework can support real design requests, generated image concepts, artifact review, and approved design-to-implementation handoff without losing traceability.

## Next Step
Close the remaining `M6` review item and refine `M7` requirements so the framework can support a chat-first design request flow, bounded design clarifications, canonical on-disk design artifacts, and a control-room design review gallery.

## Operating Notes
- Legacy markdown was used as the source for import provenance.
- The canonical operator-facing board in this repo is now derived from `sessions/studio.db`.
- New runtime work should be dispatched through the framework, not by editing the imported legacy markdown directly.
- Chat is the preferred surface for natural-language orchestration, clarification, and iterative planning.
- The Program Kanban app is the preferred surface for approvals, run evidence, trace inspection, artifact browsing, and board control.
- For future image and design work, canonical artifacts should stay on disk under project artifact folders while the control room acts as the operator-facing review surface.
- Optional web dispatch should stay available for bounded direct actions, but should not try to replace chat as the best conversational surface.
- Direct board-control actions should remain deterministic framework actions instead of being forced through multi-agent delegation.
- The framework should not create a second conversational Orchestrator persona inside the SDK runtime. SDK work should happen at the specialist layer.
