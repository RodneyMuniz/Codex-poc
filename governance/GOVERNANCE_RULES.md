# Governance Rules

## Authority Boundaries

- `governance/` defines studio-wide policy and may not contain project execution state.
- `projects/tactics-game/governance/` contains project-specific guidance and briefs.
- `projects/tactics-game/execution/` contains human-readable execution views and project artifacts.

## Delivery Rules

- All major implementation steps must land through Git commits.
- Operator approvals must gate any task marked `requires_approval`.
- Persistent runtime state belongs in `sessions/`, not in ad hoc markdown files.
- Logs and telemetry outputs belong in `logs/`.
