# Optimization Report

Date:
- `2026-04-02`

Status:
- `Phase 6 complete`

## What Improved

- delegated work now has an explicit tier instead of implicit model choice
- decomposition is mandatory before delegated execution
- API routing has a reusable wrapper with cost estimation
- usage facts can now surface through canonical run evidence

## Current Cost Leaks To Watch

### 1. Tier 1 Overuse

Risk:
- architecture or strategy language can pull too much work upward

Current control:
- explicit approval gate
- prohibited Tier 1 behaviors documented in `AGENT_TIERS.md`

### 2. ChatGPT Control-Plane Overreach

Risk:
- the operator conversation still does too much if the API router is not actually used for downstream lanes

Current control:
- architecture now treats ChatGPT as control room only

Next improvement:
- move more specialist generation through the tier-aware API router or enrich the SDK bridge with full usage reporting

### 3. Missing Production Cost Corpus

Risk:
- this implementation has controlled test evidence, not yet a large live execution dataset

Current control:
- execution log format exists
- cost tracker writes canonical usage and markdown logs

Next improvement:
- collect production run data and aggregate cost per task, per tier, and per role

## Misrouting Risks

- medium tasks that mention approvals or governance language may drift toward Tier 1 if keyword rules become too aggressive
- developer subtasks should remain cheap unless a senior planning step explicitly justifies escalation

## Recommended Next Improvements

1. Add a production usage dashboard from `usage_events`.
2. Extend the SDK specialist bridge so returned API usage is captured without relying on synthetic smoke coverage.
3. Add threshold-based cost warnings for repeated retries.
4. Evaluate Batch or background execution for non-interactive Tier 3 backlogs.
5. Periodically review Tier 1 approval frequency to prevent slow drift.
