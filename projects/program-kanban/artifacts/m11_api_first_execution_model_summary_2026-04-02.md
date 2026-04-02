# M11 API-First Execution Model Summary

Date:
- `2026-04-02`

Milestone:
- `M11 - API-First Hybrid Execution Model`

Status:
- `implemented and ready for operator review`

## What Changed

- paused `M8` and `M9` so product-wave execution stops outrunning the framework
- added a reusable hybrid execution architecture with clear operator-versus-API boundaries
- defined three execution tiers:
  - `tier_1_senior`
  - `tier_2_mid`
  - `tier_3_junior`
- made delegated tasks pass through classification, tier assignment, and decomposition before execution
- added a reusable `APIRouter` with tier-aware model routing, retry handling, artifact writes, and cost logging
- added a reusable `CostTracker` with cached-token-aware estimation and markdown execution logs
- made PM subtasks carry:
  - `deliverable_type`
  - `allowed_tools`
  - `deliverable_contract`
  - `assigned_tier`
  - `expected_output_format`
- surfaced usage events through canonical run evidence

## New Ways Of Working

- ChatGPT or Codex is the control room, not the default execution engine
- API tiers handle bounded planning and execution work by default
- Tier 1 is scarce and approval-gated
- Tier 2 is the default structured planning lane
- Tier 3 is the default low-cost execution lane
- no delegated task should go straight to execution without decomposition
- deterministic board actions remain local and do not get forced through the tiered execution path

## Delivered Outputs

- `governance/ARCHITECTURE.md`
- `governance/AGENT_TIERS.md`
- `governance/ROUTING_RULES.md`
- `governance/TASK_DECOMPOSITION.md`
- `agents/api_router.py`
- `agents/cost_tracker.py`
- `governance/APPROVAL_RULES.md`
- `governance/approval_templates.md`
- `governance/TEST_RESULTS.md`
- `governance/OPTIMIZATION_REPORT.md`
- `governance/execution_logs.md`

## Validation

Focused suite:
- `33 passed`

Broader regression suite:
- `59 passed`

## Honest Remaining Gap

The execution model is now defined and wired into the framework, but the full end-to-end specialist runtime still needs more live production usage to prove its long-run cost profile. The biggest next improvement is capturing richer live API usage from the specialist runtime so the optimization loop can run on real task traffic instead of only controlled scenarios.
