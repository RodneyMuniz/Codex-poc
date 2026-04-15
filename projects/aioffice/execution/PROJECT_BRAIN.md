# AIOffice Project Brain

Snapshot status:
- accepted current-state snapshot
- compact summon primer, not a transcript dump
- subordinate to `execution/KANBAN.md` for task and milestone status truth

## What Is Now True
- AIOffice is a governance-first, fail-closed, thin-control-kernel project around untrusted models and bounded executors.
- `execution/KANBAN.md` is the authoritative operational truth source.
- `M1` through `M9` are complete.
- no post-`M9` milestone is ratified yet.
- current readiness posture is:
  - `ready only for narrow supervised bounded operation`
  - not ready for a bounded supervised semi-autonomous cycle
- current proof includes sanctioned control-kernel persistence, read-only inspection, fail-closed first-slice checks through `architect`, supervised proof of the separate `apply` path, sequential same-workspace and same-store reuse with preserved control-plane identity, the operator-facing `bundle-decision` surface with focused verification, one supervised operator-facing decision rehearsal against persisted state, and the file-based `--destination-mappings-file` path with focused verification plus one supervised rehearsal against persisted state.
- current live workflow proof still stops at `architect`; later stages are not yet proven as live workflow.
- `M9` closed as a documentation and planning-surface reconciliation slice; it did not change control behavior or readiness claims.

## What Is Unproven
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
  - `M6` through `M9` were used as narrow proof, hardening, and reconciliation slices rather than broad later-stage workflow expansion
- no post-`M9` milestone is ratified yet

## Next Recommended Action
- no post-`M9` milestone is ratified in this snapshot
- use `execution/KANBAN.md` and `governance/ACTIVE_STATE.md` as the authoritative starting point for any later slice decision
- keep later-stage workflow expansion deferred until a new conservative slice is explicitly reviewed and accepted

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
- `governance/M6_NARROW_PROOF_REVIEW.md`
- `governance/M7_OPERATOR_DECISION_SURFACE_REVIEW.md`
- `governance/M8_OPERATOR_DECISION_INPUT_REVIEW.md`

## Ignore On Fresh Summon
- old transcript drift and narrative summaries that are not backed by current artifacts
- rehearsal workspaces and scratch copies as status authority
- product-vision ideas that were not explicitly accepted into `execution/KANBAN.md`
- any claim that `M5` is still partial or that `AIO-032` through `AIO-034` remain current work
- any claim that supervised apply/promotion evidence is still outstanding
- any claim that the next planned slice still begins with `AIO-036`
- any claim that a post-`M9` milestone is already ratified
- any claim that later-stage workflow proof already exists
- any claim that bounded supervised semi-autonomous readiness is already proven
