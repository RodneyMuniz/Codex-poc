# Thin Manager API-First Operating Policy

Date:
- `2026-04-02`

Status:
- `Proposed operating policy`
- `Supersedes chat-heavy execution habits`

Scope:
- reusable across projects and users
- optimized for lower ChatGPT-plan consumption
- optimized for API-first bounded execution

## 1. Diagnosis

The Studio is not failing because it lacks models.

It is failing because the control layer is still doing too much work in chat and local orchestration code.

Current local evidence:

- [orchestrator.py](C:\Users\rodne\Dev\_AIStudio_worktrees\studio-control\agents\orchestrator.py) still performs classification, tier assignment, decomposition framing, and operator-facing preview assembly locally.
- [pm.py](C:\Users\rodne\Dev\_AIStudio_worktrees\studio-control\agents\pm.py) remains the main downstream planner and worker dispatcher.
- [api_router.py](C:\Users\rodne\Dev\_AIStudio_worktrees\studio-control\agents\api_router.py) exists, but it is not the active default execution path for the Studio.
- [sdk_specialists.py](C:\Users\rodne\Dev\_AIStudio_worktrees\studio-control\agents\sdk_specialists.py) and [role_base.py](C:\Users\rodne\Dev\_AIStudio_worktrees\studio-control\agents\role_base.py) still run real model work through separate paths, which fragments routing, evidence, and cost tracking.
- [cost_tracker.py](C:\Users\rodne\Dev\_AIStudio_worktrees\studio-control\agents\cost_tracker.py) estimates cost, but the operating model still lacks first-class lane selection for sync vs background vs batch and does not optimize around cache efficiency by default.

This means the fastest savings will not come from making Codex smarter.

The fastest savings will come from making Codex thinner and forcing bounded work into one observable API fabric.

## 2. Revised Operating Policy

### Layer 1: Control Room

Execution channel:
- `Codex / chat only`

Responsibilities:
- validate the request
- clarify only when blocked
- assign project, milestone, and approval posture
- choose execution lane
- choose tier
- review final evidence

Hard rule:
- Codex is not the default planning engine
- Codex must not run long specialist execution unless explicitly justified

Default response contract for operator requests:

1. validation
2. route
3. what stays in Codex
4. what goes to API
5. execution lane: sync, background, or batch
6. tier choice
7. approval need
8. next action

### Layer 2: Deterministic Task Compiler

Execution channel:
- `local deterministic runtime`

Responsibilities:
- classify complexity, ambiguity, and size
- compile dispatch packets
- assign tier
- assign execution lane
- enforce budget ceilings
- enforce approval gates
- enforce artifact contracts

Hard rule:
- no delegated task goes to execution without a compiled packet
- deterministic actions stay local
- compiled packets must be stable-prefix prompt inputs suitable for caching

### Layer 3: API Execution Fabric

Execution channel:
- `OpenAI API`

Responsibilities:
- perform bounded planning or execution
- return structured output
- return usage and cost evidence
- write artifacts or structured payloads
- support sync, background, and batch modes

Hard rule:
- bounded downstream work defaults to API
- Tier 1 is scarce and approval-gated
- no second free-form orchestrator persona is allowed

### Layer 4: Evaluation and Budget Governor

Execution channel:
- `deterministic local analytics + control-room reporting`

Responsibilities:
- track pass rate
- track retry rate
- track escalation rate
- track latency
- track cached-token ratio
- track cost per successful artifact
- tune routing from evidence instead of intuition

Hard rule:
- if a lane is expensive and not measurably better, it must be demoted

## 3. Thin-Manager Runtime Rules

### Codex must do only:

- project selection
- clarification when necessary
- approval gating
- milestone judgment
- final review synthesis
- deterministic board actions

### Codex must not do by default:

- deep task planning
- repeated specialist synthesis
- routine writing or transformation work
- medium-complexity decomposition if an API lane can do it
- repeated comparison of alternatives

### Deterministic compiler must always produce:

- `classification`
- `tier_assignment`
- `execution_lane`
- `budget_policy`
- `approval_policy`
- `prompt_shape`
- `expected_output_format`
- `artifact_contract`
- `evaluation_contract`

## 4. Routing Policy

| Route | Use for | Default models | Default approval | Notes |
| --- | --- | --- | --- | --- |
| `Codex` | intake, clarification, approvals, final review, deterministic board control | n/a | operator-owned | keep compact |
| `sync_api` | short bounded work where the operator is waiting | Tier 3 or Tier 2 | none unless cost/risk threshold crossed | default for most immediate work |
| `background_api` | long-running but still interactive-value work | Tier 2 or Tier 1 | required for Tier 1, optional for Tier 2 above budget threshold | use polling or webhooks |
| `batch_api` | non-urgent bulk work, evals, enrichment, backlog transforms | Tier 3 or Tier 2 | no operator approval by default unless aggregate budget is large | cheapest large-scale lane |

### Default lane selection

- `small + bounded + operator waiting` -> `sync_api`
- `medium + may take minutes + operator does not need continuous interaction` -> `background_api`
- `bulk + repeated + non-urgent + many homogeneous requests` -> `batch_api`
- `board mutation / approval / milestone acceptance` -> `Codex`

### Tier defaults

- `Tier 3` first for routine bounded work
- `Tier 2` for planning, synthesis, structured review packets
- `Tier 1` only for ambiguity, architecture risk, or repeated lower-tier failure

### Tier 1 approval triggers

- architecture change
- high ambiguity with cross-system effect
- repeated failure after controlled retries
- expected cost above threshold

## 5. Prompt-Shaping Policy For Prompt Caching

All API prompts should be structured as:

1. stable policy prefix
2. stable role contract
3. stable output schema
4. stable tool/artifact rules
5. variable task payload

### Stable prefix contents

- role behavior
- allowed and prohibited actions
- output schema
- artifact rules
- evaluation rules
- house style

### Variable suffix contents

- task title
- project name
- objective
- details
- constraints
- acceptance criteria
- prior artifact references
- correction notes

### Cache policy

- use exact stable prefixes per route family
- keep task payload last
- use a consistent `prompt_cache_key` per route family or project-lane
- use `prompt_cache_retention='24h'` for repeated specialist lanes with shared prefixes
- avoid stuffing ephemeral commentary into the stable prefix

### Prompt families

- `intake.packet.v1`
- `planning.decompose.v1`
- `execution.tier3.code.v1`
- `execution.tier3.design.v1`
- `review.qa.v1`
- `eval.route_audit.v1`

## 6. Eval And Budget Framework

Track per task, per lane, per tier:

- request count
- success count
- failure count
- retry count
- escalation count
- median latency
- p95 latency
- input tokens
- cached input tokens
- output tokens
- reasoning tokens
- estimated cost
- cost per successful artifact
- cache hit ratio

### Budget controls

- soft warning threshold per task
- hard stop threshold per task
- daily lane budget
- weekly Tier 1 budget
- retry ceiling before forced escalation review

### Required dashboards

- cost by tier
- cost by lane
- cache ratio by route family
- retries by route family
- escalations by route family
- success rate by model+tier+lifecycle lane

### Optimization loop

Weekly:
- demote tasks that succeed cheaply at lower tier
- split prompts that miss cache frequently
- move long sync tasks into background
- move repeated background tasks into batch
- reduce Codex involvement where evidence shows API success is already high

## 7. Concrete Runtime Changes Needed

### Fastest savings first

#### A. Make `APIRouter` the single execution fabric

Current problem:
- [api_router.py](C:\Users\rodne\Dev\_AIStudio_worktrees\studio-control\agents\api_router.py) is not the active default path.

Change:
- route all bounded downstream specialist execution through `APIRouter` or an `ExecutionFabric` wrapper built on top of it.
- retire separate cost/logging behavior inside [role_base.py](C:\Users\rodne\Dev\_AIStudio_worktrees\studio-control\agents\role_base.py) as the primary runtime path.

Immediate savings:
- unified cost visibility
- unified lane control
- unified prompt caching policy

#### B. Move decomposition out of Codex-heavy flow

Current problem:
- [orchestrator.py](C:\Users\rodne\Dev\_AIStudio_worktrees\studio-control\agents\orchestrator.py) still performs too much classification and decomposition logic locally.

Change:
- keep only a lightweight deterministic classifier locally
- send any non-trivial decomposition to Tier 2 API using a stable JSON schema

Immediate savings:
- fewer long control-room turns
- cheaper repeatable planning

#### C. Add explicit lane assignment to task packets

Current problem:
- tier exists, but sync vs background vs batch is not first-class in runtime enforcement.

Change:
- extend task acceptance / compiled packet to include:
  - `execution_lane`
  - `background_eligible`
  - `batch_eligible`
  - `budget_policy`

Immediate savings:
- long-running work stops occupying sync execution unnecessarily

#### D. Replace prompt-specialist freeform behavior with route templates

Current problem:
- intake still risks overthinking and variable prompts.

Change:
- convert prompt specialist into a thin packet normalizer
- stable JSON output only
- no long prose

Immediate savings:
- better cache reuse
- lower intake token consumption

#### E. Upgrade cost tracking from estimates-only to governor inputs

Current problem:
- [cost_tracker.py](C:\Users\rodne\Dev\_AIStudio_worktrees\studio-control\agents\cost_tracker.py) logs cost, but it does not govern routing.

Change:
- add budget decisions that can:
  - block Tier 1
  - demote sync to background
  - move large homogeneous jobs into batch
  - cap retries

Immediate savings:
- stops silent overspend

## 8. File-Level Implementation Targets

### `agents/orchestrator.py`

Change:
- reduce to thin intake, approval, and review behavior
- remove non-essential local planning
- emit compact response envelope only
- persist `execution_lane`

### `agents/pm.py`

Change:
- stop acting like a rich planning engine
- consume compiled packets
- dispatch only
- enforce packet completeness

### `agents/api_router.py`

Change:
- become the primary execution interface
- add lane support:
  - `sync`
  - `background`
  - `batch`
- add `prompt_cache_key`
- add `prompt_cache_retention`
- add structured lane metadata

### `agents/cost_tracker.py`

Change:
- persist cached tokens and reasoning tokens as first-class fields
- compute cost per successful artifact
- emit lane-aware summaries

### `agents/role_base.py`

Change:
- stop being a parallel execution fabric
- either:
  - wrap `APIRouter`, or
  - be demoted to compatibility-only legacy path

### `agents/sdk_specialists.py` and `scripts/sdk_runtime_bridge.py`

Change:
- keep only if the SDK lane offers a measurable quality advantage
- otherwise make it a secondary adapter behind the same execution-fabric contract
- capture usage in the same schema as `APIRouter`

### `agents/schemas.py`

Add:
- `execution_lane`
- `budget_policy`
- `cache_policy`
- `route_family`
- `background_eligible`
- `batch_eligible`

### `sessions/store.py`

Add canonical fields or evidence for:
- lane
- route family
- cached tokens
- reasoning tokens
- latency
- retries
- escalation source
- cost per artifact

## 9. Immediate Routing Policy

Apply this now:

- If the task is deterministic board control:
  - keep in Codex
- If the task is bounded and under 2 minutes:
  - `sync_api`
  - `tier_3_junior` by default
- If the task is bounded but may exceed 2 minutes:
  - `background_api`
  - `tier_2_mid` unless obviously Tier 3
- If the task is large-scale, repetitive, or non-urgent:
  - `batch_api`
  - `tier_3_junior`
- If ambiguity is high or architecture is touched:
  - `tier_1_senior`
  - approval required

## 10. Fastest-Savings-First Implementation Sequence

### Step 1

Enforce thin control-room responses.

Deliver:
- compact eight-part operator response template
- no long specialist execution in chat by default

Savings:
- immediate reduction in plan burn

### Step 2

Make `APIRouter` the default bounded execution path.

Deliver:
- route Tier 2 and Tier 3 specialist work through `APIRouter`
- mark old execution paths as legacy

Savings:
- immediate shift from chat-heavy to API-heavy execution

### Step 3

Add lane selection.

Deliver:
- `sync`, `background`, and `batch` as first-class runtime choices

Savings:
- long-running work stops blocking interactive flow
- bulk work becomes much cheaper

### Step 4

Enforce cache-shaped prompts.

Deliver:
- route-family prompt templates
- stable prefixes
- `prompt_cache_key`
- `prompt_cache_retention`

Savings:
- lower input cost
- lower latency

### Step 5

Add budget governor decisions.

Deliver:
- soft and hard cost thresholds
- retry ceilings
- Tier 1 scarcity enforcement

Savings:
- stops hidden waste

### Step 6

Add weekly route optimization from evidence.

Deliver:
- route audit
- cache audit
- demotion/escalation recommendations

Savings:
- sustained cost reduction instead of one-time cleanup

## 11. Immediate Decision

Do not spend the next cycle making the orchestrator more sophisticated.

Spend the next cycle:

- thinning the control layer
- enforcing API-first execution
- unifying execution into one lane fabric
- making routing measurable by cost, cache hit rate, and success rate

## 12. Official OpenAI Basis

This policy is aligned with current official OpenAI guidance:

- The Responses API is recommended for new projects and improves cache utilization versus Chat Completions: [Migrate to Responses](https://platform.openai.com/docs/guides/migrate-to-responses)
- Background mode supports asynchronous long-running tasks with polling or streaming catch-up: [Responses API features](https://openai.com/index/new-tools-and-features-in-the-responses-api/)
- Prompt caching works on exact prefix matches, benefits from stable prefixes, supports `prompt_cache_key`, and can use `prompt_cache_retention='24h'`: [Prompt caching guide](https://platform.openai.com/docs/guides/prompt-caching)
- Current response objects and request params expose `previous_response_id`, `prompt_cache_key`, and `prompt_cache_retention`: [Responses API reference](https://platform.openai.com/docs/api-reference/responses/retrieve)
- Batch API provides asynchronous processing with a 24-hour completion window and a 50% discount: [Batch API reference](https://platform.openai.com/docs/api-reference/batch/retrieve)
- Cost optimization guidance explicitly recommends Batch and Flex processing for lower-cost asynchronous workloads: [Cost optimization guide](https://platform.openai.com/docs/guides/cost-optimization)
