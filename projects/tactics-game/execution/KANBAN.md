# Tactics Game Kanban

This file is rendered from `sessions/studio.db`. Do not use it as the source of truth.

## Backlog

_No items_

## In Progress

### Warrior Unit Tests
- ID: task_f3b834d7835d
- Status: delegated
- Owner: Developer
- Requires Approval: no
- Description: Create the test module `projects/tactics-game/artifacts/test_warrior.py`. ProjectPO must consult both Architect and Developer. Developer should write pytest tests that cover initialization validation, attack damage, healing cap, and defeated-warrior combat behavior. Then use `run_unit_tests` with pytest args `projects/tactics-game/artifacts/test_warrior.py -q` and only complete if the tests pass.

### Warrior Unit Tests Recovery
- ID: task_7381585ff045
- Status: delegated
- Owner: Developer
- Requires Approval: no
- Description: Fix `projects/tactics-game/artifacts/test_warrior.py` so it matches the current Warrior implementation in `projects/tactics-game/artifacts/warrior.py`. ProjectPO must consult Architect and Developer. Developer should avoid direct writes to read-only properties and should simulate defeated warriors through valid public behavior such as damage application. Run `run_unit_tests` with pytest args `projects/tactics-game/artifacts/test_warrior.py -q` and complete only if the tests pass.

## Awaiting Approval

_No items_

## Done

### Warrior Design Document
- ID: task_00f46633ebc1
- Status: completed
- Owner: ProjectPO
- Requires Approval: no
- Description: Create the markdown artifact `projects/tactics-game/artifacts/warrior_design.md`. ProjectPO must consult both Architect and Developer. Architect should write the design document and Developer should review implementability. The document must describe the purpose of the Warrior slice, core fields (name, max_hp, attack_power, current_hp), behaviors (take_damage, heal, attack, is_alive), validation rules, and acceptance criteria. Complete only after the markdown file exists.
- Result: Warrior design document created, reviewed by Developer, and confirmed ready for implementation without required approval.

### Warrior Architecture Plan
- ID: task_ec986b41068f
- Status: completed
- Owner: ProjectPO
- Requires Approval: no
- Description: Create the markdown artifact `projects/tactics-game/artifacts/warrior_architecture_plan.md`. ProjectPO must consult both Architect and Developer. Architect should define the module layout, class API, risk notes, and test strategy for a minimal Warrior implementation. Developer should comment on practicality and testability. Complete only after the markdown file exists.
- Result: Completed Warrior Architecture Plan with Architect's detailed design and Developer's practical feedback.

### Warrior Code Implementation
- ID: task_f82c44da7873
- Status: completed
- Owner: ProjectPO
- Requires Approval: yes
- Description: Create the Python module `projects/tactics-game/artifacts/warrior.py`. ProjectPO must consult both Architect and Developer. Before any `.py` artifact is written, ProjectPO must request operator approval and pause the run. After approval is granted and the run resumes, Developer should write the module using `write_project_artifact`. The module must define a reusable Warrior class with name, max_hp, attack_power, current_hp, an is_alive property, and methods take_damage, heal, and attack. It must reject invalid initialization and invalid combat operations. Complete only after the Python file exists.
- Result: Warrior.py module implemented per design approval. Includes fully validated Warrior class with private attributes, properties, combat methods, and docstrings. Verified by ProjectPO. Task complete.

### Warrior Architecture Artifact Recovery
- ID: task_f901c6a81b2d
- Status: completed
- Owner: ProjectPO
- Requires Approval: no
- Description: The prior Warrior Architecture Plan task recorded architecture notes but did not write the required markdown file. Create `projects/tactics-game/artifacts/warrior_architecture_plan.md` from the agreed architecture content. ProjectPO must consult Architect and Developer. Architect should write the markdown artifact, and Developer should verify that it matches the Warrior implementation and test strategy. Complete only after the markdown file exists.
- Result: Completed warrior_architecture_plan.md creation and verification.

## Blocked

_No items_
