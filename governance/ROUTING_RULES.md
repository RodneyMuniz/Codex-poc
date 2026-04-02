# Routing Rules

Date:
- `2026-04-02`

Status:
- `Phase 1 baseline`

## Intake Rule

Every delegated request must be classified before execution.

Required dimensions:
- complexity
- ambiguity
- size

## Classification Scale

### Complexity

- `low`: one bounded output, low risk, no architecture change
- `medium`: multiple constraints, structured reasoning needed, but still locally bounded
- `high`: schema, architecture, multi-surface, or recovery-sensitive work

### Ambiguity

- `low`: request already states goal, output, and constraints clearly
- `medium`: some operator intent must be inferred, but the path is still reasonably stable
- `high`: the system must choose direction, reconcile conflicts, or define new standards

### Size

- `small`: one main output
- `medium`: multiple linked outputs or one output plus validation and review
- `large`: multi-phase or cross-surface work

## Default Routing

| Classification | Default Tier | Reason |
| --- | --- | --- |
| low complexity + low ambiguity + small size | `tier_3_junior` | cheapest safe route |
| medium in any one dimension | `tier_2_mid` | needs structure before execution |
| high ambiguity | `tier_1_senior` | direction-setting must be explicit |
| high complexity + medium or large size | `tier_1_senior` | architecture or system risk |
| repeated Tier 3 or Tier 2 failure | escalate one tier | controlled recovery |

## Decomposition Rule

No delegated task goes directly to execution.

Minimum decomposition output:
- subtask title
- clear instructions
- expected output format
- assigned agent tier
- acceptance criteria

Small tasks may decompose into one bounded execution step plus validation.

Medium or large tasks must decompose into at least:
- framing or planning
- execution
- review or validation

## Approval Gates

Approval is required for:
- any Tier 1 route
- large or expensive tasks
- architecture changes
- retries that would materially increase cost

Approval packets must explain:
- why this tier is needed
- expected cost impact
- risk of not proceeding

## Escalation Rules

- Tier 3 may escalate to Tier 2 after bounded failure or ambiguity
- Tier 2 may escalate to Tier 1 when architectural or ambiguity risk remains
- direct Tier 3 to Tier 1 escalation is allowed only when architecture change or severe ambiguity is obvious at intake

## Prohibited Behaviors

- routing everything to Tier 1
- skipping decomposition
- letting a worker define its own tier after dispatch
- hiding approval-worthy cost under repeated retries
- sending deterministic board actions through tiered API execution

## Interaction Model

1. Orchestrator receives request.
2. Prompt shaping happens.
3. Classification is recorded.
4. Tier is assigned.
5. Decomposition packet is produced.
6. Approval is requested if rules require it.
7. API worker runs the bounded subtask.
8. Output returns with usage and cost evidence.
9. QA validates.
10. Operator reviews summary and proof.
