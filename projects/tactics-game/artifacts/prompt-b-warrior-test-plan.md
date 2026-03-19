# Prompt B Test Plan: Warrior Slice

## Feature Slice

Implement a minimal `Warrior` domain object for the tactics-game project.

## Goal

Validate that the Program Orchestrator, Project PO, Architect, and Developer can collaborate end to end across planning, approval, implementation, and test outputs.

## Planned Tasks

### Task 1: Design Document
- Owner workflow: Project PO delegates to Architect and consults Developer.
- Approval required: no
- Expected output: `projects/tactics-game/artifacts/warrior_design.md`
- Acceptance criteria:
  - Documents the user-facing purpose of the `Warrior` slice.
  - Lists the core fields, behaviors, and validation rules.
  - Includes implementation constraints and review notes.

### Task 2: Architecture Plan
- Owner workflow: Project PO delegates to Architect and consults Developer.
- Approval required: no
- Expected output: `projects/tactics-game/artifacts/warrior_architecture_plan.md`
- Acceptance criteria:
  - Defines module layout and API shape.
  - Explains tradeoffs and test strategy.
  - Calls out any risks or simplifications for the MVP.

### Task 3: Code Implementation
- Owner workflow: Project PO delegates to Architect and Developer.
- Approval required: yes
- Expected output: `projects/tactics-game/artifacts/warrior.py`
- Acceptance criteria:
  - Defines a reusable `Warrior` Python class.
  - Supports health tracking, damage, healing, and attack behavior.
  - Rejects invalid initialization and invalid combat operations.
  - Requests operator approval before final code artifact creation and task completion.

### Task 4: Unit Tests
- Owner workflow: Project PO delegates to Developer and consults Architect.
- Approval required: no
- Expected output: `projects/tactics-game/artifacts/test_warrior.py`
- Acceptance criteria:
  - Covers initialization, attack flow, healing cap, and defeated combat behavior.
  - Runs successfully with `pytest`.

## Final Report
- Expected output: `projects/tactics-game/artifacts/prompt-b-report.md`
- Acceptance criteria:
  - Summarizes task statuses, approvals, logs, artifacts, and observed bottlenecks.
