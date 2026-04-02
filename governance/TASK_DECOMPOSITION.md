# Task Decomposition Engine

Date:
- `2026-04-02`

Status:
- `Implemented baseline`

Primary code surfaces:
- `agents/orchestrator.py`
- `agents/pm.py`
- `agents/schemas.py`

## Rule

No delegated task should go directly to execution without decomposition.

Deterministic board-control actions remain the exception because they stay local and do not enter the delegated execution path.

## Intake Flow

1. Prompt Specialist produces a delegation packet.
2. Orchestrator classifies:
   - complexity
   - ambiguity
   - size
3. Orchestrator assigns an execution tier.
4. Orchestrator produces a decomposition packet.
5. The task is persisted with:
   - `classification`
   - `tier_assignment`
   - `decomposition`
6. PM turns the bounded plan into concrete specialist subtasks.

## Classification Dimensions

### Complexity

- `low`: one bounded output, low risk
- `medium`: structured implementation or review work
- `high`: architecture, schema, workflow, multi-surface, or recovery-sensitive work

### Ambiguity

- `low`: goal and path are clear
- `medium`: assumptions or risks exist but the path is still workable
- `high`: the system must define direction, resolve conflict, or pick standards

### Size

- `small`: one main output
- `medium`: multiple linked outputs or validation/review steps
- `large`: clearly multi-phase or cross-surface

## Decomposition Output

Each generated decomposition subtask includes:
- title
- instructions
- expected output format
- assigned tier
- acceptance criteria
- assigned role when known

## Tier-Aware Decomposition Pattern

### Small task

- `tier_3_junior` execution
- `tier_2_mid` review gate

### Medium task

- `tier_2_mid` task plan
- `tier_3_junior` execution
- `tier_2_mid` validation

### Ambiguous or high-risk task

- `tier_1_senior` framing
- `tier_2_mid` implementation plan
- `tier_3_junior` bounded execution
- `tier_2_mid` QA validation

## PM Propagation

Concrete PM subtasks now carry:
- `deliverable_type`
- `allowed_tools`
- `deliverable_contract`
- `assigned_tier`
- `expected_output_format`

This data is persisted into subtask acceptance metadata so downstream execution does not have to guess.

## Expected Output Format Mapping

Current deterministic mapping:
- `.md` -> `markdown`
- `.py` -> `python`
- `.json` -> `json`
- `.js`, `.mjs`, `.ts`, `.tsx` -> `javascript`
- fallback -> `text`

## Notes

- the tiering rules are reusable across projects
- the PM still owns concrete specialist subtasks
- the Orchestrator now freezes the task profile before delegated execution begins
