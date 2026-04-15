# AIOffice Project Brain

Snapshot status:
- accepted current-state bootstrap
- compact summon primer, not a transcript dump
- subordinate to `execution/KANBAN.md` for task and milestone status truth

## What Is Now True
- AIOffice is a governance-first, fail-closed, thin-control-kernel project around untrusted models and bounded executors.
- `execution/KANBAN.md` is the authoritative operational truth source.
- `M1` through `M4` are complete.
- `M5` is complete.
- current readiness posture is:
  - `ready only for narrow supervised bounded operation`
  - not ready for a bounded supervised semi-autonomous cycle
- current proof includes sanctioned control-kernel persistence, read-only inspection, fail-closed first-slice checks through `architect`, operator CLI proof against sanctioned state, controlled `promote`-branch proof, multi-run supervised coverage, and validated isolated-workspace hardening on the tested path.
- current live workflow proof still stops at `architect`; later stages are not yet proven as live workflow.
- the next planned slice is narrow:
  - separate supervised proof of the `apply` branch
  - bounded proof for same-workspace repeated-run or shared-store contention behavior

## What Is Unproven
- supervised proof of the separate `apply` branch
- same-workspace repeated-run or shared-store contention behavior
- later-stage workflow proof for `design`, `build_or_write`, `qa`, and `publish`
- unattended, overnight, or self-directing operation
- any operator workspace alpha beyond the currently proven inspection-oriented surfaces

## Current Milestone Posture
- the original `M1` through `M10` roadmap remains the strategic backbone
- accepted divergence is explicit:
  - original `M3` operator-design work was deferred
  - control-kernel, persistence, inspection, and supervised-control work were pulled forward into current `M3` through `M5`
- `M6` is now ratified as a planned narrow post-`M5` proof slice rather than a broad later-stage expansion milestone
- later milestones beyond `M6` remain preserved with refinements, not replaced, and are not new backlog commitments by themselves

## Next Recommended Action
- approve the post-`M5` narrow next slice and begin with `AIO-036`
- keep later-stage workflow expansion deferred until current-boundary proof gaps are addressed explicitly

## Blockers / Assumptions
- no additional ratified blockers or assumptions are declared in this snapshot beyond the unproven items and accepted governance baselines listed above

## Load First
- `governance/PROJECT.md`
- `governance/VISION.md`
- `execution/KANBAN.md`
- `governance/DECISION_LOG.md`
- `governance/WORKFLOW_VISION.md`
- `governance/STAGE_GOVERNANCE.md`

## Ignore On Fresh Summon
- old transcript drift and narrative summaries that are not backed by current artifacts
- rehearsal workspaces and scratch copies as status authority
- product-vision ideas that were not explicitly accepted into `execution/KANBAN.md`
- any claim that later-stage workflow proof already exists
- any claim that bounded supervised semi-autonomous readiness is already proven
