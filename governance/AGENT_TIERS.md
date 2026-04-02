# Agent Tiers

Date:
- `2026-04-02`

Status:
- `Phase 1 baseline`

## Tier Table

| Tier | Label | Default Model | Default Channel | Core Responsibility | Use By Default For |
| --- | --- | --- | --- | --- | --- |
| `tier_1_senior` | Senior | `gpt-5.4` | API | architecture, ambiguity resolution, risk review, recovery | ambiguous, high-risk, cross-system, architecture-changing work |
| `tier_2_mid` | Mid-level | `gpt-5.4-mini` | API | planning, structured synthesis, review framing, medium implementation support | decomposition, review packets, medium complexity tasks |
| `tier_3_junior` | Junior | `gpt-5.4-nano` | API | routine execution, extraction, transforms, scaffolding | small bounded tasks, repetitive outputs, mechanical implementation steps |

## Tier 1

Allowed task types:
- architecture changes
- unclear requests that cannot be safely decomposed at lower tiers
- conflict resolution between plans or artifacts
- recovery and root-cause analysis
- final review of expensive execution paths

Prohibited behaviors:
- handling routine formatting or extraction work
- being used as the default developer lane
- running repeatedly when a Tier 2 or Tier 3 route already succeeded
- consuming operator budget for exploratory work that can be staged more cheaply

Escalate into Tier 1 when:
- ambiguity is high
- failure impact is high
- the task changes contracts, schemas, or architecture
- lower tiers return conflicting outputs or repeated failure

## Tier 2

Allowed task types:
- decompose requests into subtasks
- generate structured plans
- synthesize research into actionable notes
- create review packets and evaluation rubrics
- handle medium-complexity implementation support

Prohibited behaviors:
- bypassing Tier 1 for architecture-risk calls
- delegating trivial work upward
- acting as the final approval authority

Escalate into Tier 2 when:
- the task is larger than a one-step execution job
- the task needs structure before implementation
- the output needs clear review framing or comparison

## Tier 3

Allowed task types:
- transform inputs into bounded outputs
- produce first-pass scaffolding
- extract, classify, summarize, or rewrite structured content
- generate low-risk implementation artifacts from approved plans

Prohibited behaviors:
- redefining project architecture
- inventing scope
- approving its own work
- escalating itself to senior repeatedly without clear trigger evidence

Escalate out of Tier 3 when:
- inputs are contradictory or underspecified
- the task exceeds the small bounded scope
- failure repeats after controlled retry
- a schema, architecture, or policy decision is required

## ChatGPT Versus API

ChatGPT or Codex local usage is reserved for:
- operator conversation
- milestone steering
- direct local board-control actions
- final review and repo-integrated edits

API usage is the default for:
- tiered specialist planning
- low-cost execution
- structured generation
- repeated or parallel bounded work

## Hard Rule

Do not use Tier 1 just because it is available.

The default path is:
- Tier 3 first for small bounded work
- Tier 2 for structured planning or medium work
- Tier 1 only by rule, not by habit
