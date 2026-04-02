# Approval Templates

Date:
- `2026-04-02`

Status:
- `Implemented baseline`

## Tier 1 Approval Template

```markdown
## Approval Request

- Reason: Tier 1 senior reasoning is required.
- Why this tier is needed: <explain ambiguity, architecture risk, or recovery risk>
- Expected cost impact: <low / medium / high or estimated USD>
- Risk of not proceeding: <what fails or stays unresolved if denied>
- Cheaper path attempted first: <yes / no and why>
- Expected output: <decision note, architecture plan, review packet, etc>
```

## Large Task Approval Template

```markdown
## Approval Request

- Reason: large multi-step task
- Why this tier is needed: <explain why the work cannot stay as a small bounded slice>
- Expected cost impact: <estimate or band>
- Risk of not proceeding: <what delivery or review step stays blocked>
- Decomposition plan: <summary of the bounded subtasks>
- Expected output: <artifact or review package>
```

## Architecture Change Approval Template

```markdown
## Approval Request

- Reason: architecture change
- Why this tier is needed: <what contract, schema, or routing behavior changes>
- Expected cost impact: <estimate or band>
- Risk of not proceeding: <why the current architecture is insufficient>
- Blast radius: <files, services, or future tasks affected>
- Expected output: <architecture note, migration plan, implementation slice>
```
