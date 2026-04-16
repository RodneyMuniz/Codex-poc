# AIOffice Project Brain

Snapshot status:
- accepted current-state snapshot
- compact summon primer, not a transcript dump
- subordinate to `execution/KANBAN.md` for task and milestone status truth

## What Is Now True
- AIOffice is a governance-first, fail-closed, thin-control-kernel project around untrusted models and bounded executors.
- `execution/KANBAN.md` is the authoritative operational truth source.
- `M1` through `M12` are complete.
- `M13` is active as `Structural Truth Layer Baseline`.
- `M13` was originally ratified as `Design Lane Operationalization` and rebaselined before implementation.
- `AIO-064` through `AIO-067` are seeded only; no `M13` implementation has started yet.
- design-lane work is deferred, not canceled.
- current readiness posture is:
  - `ready only for narrow supervised bounded operation`
  - not ready for a bounded supervised semi-autonomous cycle
- current proof includes sanctioned control-kernel persistence, read-only inspection, fail-closed first-slice checks through `architect`, supervised proof of the separate `apply` path, sequential same-workspace and same-store reuse with preserved control-plane identity, the operator-facing `bundle-decision` surface with focused verification, one supervised operator-facing decision rehearsal against persisted state, the file-based `--destination-mappings-file` path with focused verification plus one supervised rehearsal against persisted state, bounded recovery-discipline rehearsal, and bounded protected-surface blocking rehearsal.
- current live workflow proof still stops at `architect`; later stages are not yet proven as live workflow.
- current control-surface maturity now outruns dependency, impact, and traceability truth, which is why `M13` was rebaselined before implementation.

## What Is Unproven
- deterministic structural truth artifact generation and bounded structural review utility
- concurrent contention handling
- later-stage workflow proof for `design`, `build_or_write`, `qa`, and `publish`
- unattended, overnight, or self-directing operation
- any bounded supervised semi-autonomous cycle
- UAT readiness
- automatic bundle discovery or automatic destination authoring

## Current Milestone Posture
- the original `M1` through `M10` roadmap remains the strategic backbone
- accepted divergence is explicit:
  - original `M3` operator-design work was deferred
  - control-kernel, persistence, inspection, and supervised-control work were pulled forward into accepted `M3` through `M5`
  - `M6` through `M12` were used as narrow proof, hardening, reconciliation, recovery, and protected-surface-control slices rather than broad later-stage workflow expansion
- the active milestone is `M13 - Structural Truth Layer Baseline`
- no post-`M13` milestone is ratified yet

## Next Recommended Action
- start from `AIO-064` and the committed `M13` rebaseline artifacts before any implementation work
- use `execution/KANBAN.md`, `governance/ACTIVE_STATE.md`, `governance/M13_SCOPE_REBASELINE.md`, and `governance/STRUCTURAL_TRUTH_LAYER_CONTRACT.md` as the authoritative starting point for the current slice
- keep hook/automation work and design-lane breadth deferred until later review explicitly ratifies them

## Blockers / Assumptions
- no additional ratified blockers or assumptions are declared in this snapshot beyond the unproven items and accepted governance baselines listed above

## Load First
- `governance/PROJECT.md`
- `governance/VISION.md`
- `execution/KANBAN.md`
- `governance/DECISION_LOG.md`
- `governance/WORKFLOW_VISION.md`
- `governance/STAGE_GOVERNANCE.md`
- `governance/ACTIVE_STATE.md`
- `governance/M12_PROTECTED_SURFACE_REVIEW.md`
- `governance/M13_SCOPE_REBASELINE.md`
- `governance/STRUCTURAL_TRUTH_LAYER_CONTRACT.md`

## Ignore On Fresh Summon
- old transcript drift and narrative summaries that are not backed by current artifacts
- rehearsal workspaces and scratch copies as status authority
- product-vision ideas that were not explicitly accepted into `execution/KANBAN.md`
- any claim that `M5` is still partial or that `AIO-032` through `AIO-034` remain current work
- any claim that supervised apply/promotion evidence is still outstanding
- any claim that a post-`M9` milestone is still the current planning boundary
- any claim that `M13` is still design-lane operationalization in current accepted planning
- any claim that design-lane implementation has already begun
- any claim that hook/automation work is already ratified
- any claim that later-stage workflow proof already exists
- any claim that bounded supervised semi-autonomous readiness is already proven
