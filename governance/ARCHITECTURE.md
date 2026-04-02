# Hybrid Execution Architecture

Date:
- `2026-04-02`

Status:
- `Phase 1 baseline`

Scope:
- reusable across projects and users
- optimized to reduce ChatGPT-plan usage and shift bounded execution into API lanes

## Goal

Move AI Studio from a ChatGPT-heavy execution pattern into a hybrid model where:

- the operator conversation stays in ChatGPT or Codex only for intake, steering, approval, and final review
- bounded planning and execution move into API-driven lanes
- senior reasoning is scarce and explicit
- cost, escalation, and token usage are visible per task and per tier

## Core Principle

ChatGPT is the control room.

The API is the factory floor.

The Orchestrator should protect scope, board truth, and approvals while the tiered API agents do the bulk of the repeatable planning and execution work.

## System Layers

### 1. Operator Layer

Responsibilities:
- receive the user request
- clarify intent when necessary
- approve high-cost or high-risk execution
- review milestone outcomes

Primary channel:
- `ChatGPT / Codex app`

Not allowed:
- becoming the default execution engine for routine planning or implementation

### 2. Deterministic Control Plane

Components:
- `agents/orchestrator.py`
- `agents/pm.py`
- `sessions/store.py`
- `scripts/cli.py`
- `scripts/operator_api.py`
- `scripts/operator_wall_snapshot.py`

Responsibilities:
- classify incoming work
- assign a tier
- decompose work before execution
- enforce approvals and escalation
- persist canonical trace, artifact, validation, and cost evidence

Primary channel:
- local deterministic Python runtime

Not allowed:
- performing specialist generation directly when an API lane is available

### 3. API Execution Plane

Components:
- `agents/api_router.py`
- `agents/cost_tracker.py`
- tier-aware specialist workers

Responsibilities:
- run bounded work on the assigned model tier
- return structured outputs only
- log token usage and estimated cost
- write artifacts into the project structure

Primary channel:
- OpenAI API

### 4. Review And Governance Plane

Responsibilities:
- gate Tier 1 usage
- gate expensive or large runs
- gate architecture changes
- publish markdown receipts and test results

Primary surfaces:
- repo governance docs
- Program Kanban board
- canonical SQLite evidence in `sessions/studio.db`

## Tiered Execution Model

### Tier 1

Purpose:
- scarce senior reasoning for ambiguity, architecture, conflict resolution, and recovery

Default runtime:
- OpenAI API

Default model:
- `gpt-5.4`

### Tier 2

Purpose:
- structured planning, decomposition refinement, review framing, synthesis, and mid-complexity implementation support

Default runtime:
- OpenAI API

Default model:
- `gpt-5.4-mini`

### Tier 3

Purpose:
- low-cost execution, structured transforms, extraction, formatting, implementation scaffolding, and repetitive task work

Default runtime:
- OpenAI API

Default model:
- `gpt-5.4-nano`

## Interaction Flow

1. Operator sends request to the Orchestrator.
2. Orchestrator classifies complexity, ambiguity, and size.
3. Orchestrator assigns a tier and produces a decomposition packet.
4. Approval is requested if the route crosses a defined gate.
5. PM or the execution layer dispatches the bounded subtask to the assigned API tier.
6. API worker returns structured output plus usage and cost metadata.
7. Deterministic control code stores artifacts, trace, validations, and usage facts.
8. QA validates acceptance criteria.
9. Operator reviews only the evidence that matters.

## Why This Reduces ChatGPT Usage

- intake stays conversational, but most repeatable work moves to API calls
- Tier 3 handles cheap routine work instead of burning senior or ChatGPT capacity
- Tier 2 handles most planning without escalating to senior reasoning
- Tier 1 is approval-gated and used only when ambiguity or risk justifies it

## Official OpenAI Basis

This architecture is grounded in the current official OpenAI platform:

- the Responses API is the unified endpoint and returns structured `usage` data including input, cached input, output, and reasoning tokens
- the Responses API supports `previous_response_id`, `store`, and `background`
- current model docs expose separate pricing for input, cached input, output, and Batch API pricing

Reference links:
- [Responses API create](https://developers.openai.com/api/reference/resources/responses/methods/create)
- [All models](https://developers.openai.com/api/docs/models/all)
- [GPT-5.4 nano](https://developers.openai.com/api/docs/models/gpt-5.4-nano)
- [GPT-5.2 Codex](https://developers.openai.com/api/docs/models/gpt-5.2-codex)

## Implementation Boundary

This baseline does not claim that all existing specialist execution has already moved to the new router. It defines the operating contract the next implementation phases must satisfy.
