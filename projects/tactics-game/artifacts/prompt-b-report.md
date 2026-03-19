# Prompt B Report: Warrior Slice Scenario

## Scope

This scenario validated the Phase 1 framework against a small TacticsGame feature slice: a minimal `Warrior` domain object with design, implementation, and tests.

Plan artifact:
- `projects/tactics-game/artifacts/prompt-b-warrior-test-plan.md`

Runtime evidence:
- `sessions/studio.db`
- `logs/agent_events.jsonl`
- `logs/app.log`

## Task Results

| Task | Run | Status | Approval | Output Check | Notes |
| --- | --- | --- | --- | --- | --- |
| Warrior Design Document | `run_093c44c1364e` | Completed | No | `warrior_design.md` created | Expected collaboration occurred and artifact exists. |
| Warrior Architecture Plan | `run_40aa4261562d` | Completed | No | Missing `warrior_architecture_plan.md` | Task summary says complete, but acceptance was not actually satisfied. |
| Warrior Code Implementation | `run_bcca9acf6085` | Completed | Yes | `warrior.py` created | Approval gate worked as expected. |
| Warrior Unit Tests | `run_af7ed89e9819` | Stopped on max turns | No | `test_warrior.py` created, tests initially failed | Agents iterated on failures but hit the team turn limit before closure. |
| Warrior Architecture Artifact Recovery | `run_d5c009fe1b72` | Completed | No | Missing `warrior_architecture_plan.md` | Confirms acceptance checks are not enforced by the framework. |
| Warrior Unit Tests Recovery | `run_e3304ae35d7a` | Stopped on max turns | No | `test_warrior.py` repaired | Manual pytest after the run passed, but task state stayed open. |

## Approval Summary

One approval was required and processed successfully:

- Approval ID: `approval_48e6fd33cd25`
- Task: Warrior Code Implementation
- Result: approved
- Outcome: the run resumed and `warrior.py` was written and completed

## Artifact Summary

Created:
- `projects/tactics-game/artifacts/warrior_design.md`
- `projects/tactics-game/artifacts/warrior.py`
- `projects/tactics-game/artifacts/test_warrior.py`
- `projects/tactics-game/artifacts/prompt-b-report.md`

Missing:
- `projects/tactics-game/artifacts/warrior_architecture_plan.md`

Manual validation:
- `pytest projects/tactics-game/artifacts/test_warrior.py -q`
- Result after the recovery run's last file write: `7 passed`

## Behavior Assessment

What behaved as expected:
- The orchestrator created and persisted tasks, runs, approvals, messages, and delegation edges.
- The Project PO consulted both Architect and Developer before approval and completion.
- The approval gate for the code implementation task paused and resumed correctly.
- The Developer and Architect used the restricted artifact-writing tool to create real project outputs.

What did not behave as expected:
- Task completion is not tied to acceptance checks. Two tasks were marked complete without the required markdown file existing.
- Runs that stop on `MaxMessageTermination` cannot be resumed through the current CLI, even when the agents were close to completion.
- The test workflow required multiple repair iterations and exceeded the current 12-turn limit.

## Missing Capabilities And Bottlenecks

- No post-condition validators for required files, pytest success, or other completion criteria.
- No generic resume path for runs that stop because of turn limits or non-approval interruptions.
- Context retrieval is still shallow; the agents rely on search and summaries instead of richer file inspection, which increased rework.
- The Project PO can trust agent claims too early because completion depends on conversation flow, not on verified outputs.
- The current artifact-writing tool is useful, but the framework still lacks a structured patch/edit skill for safer code refinement.

## Improvement Suggestions

- Add task-level acceptance validators such as `required_files_exist` and `pytest_passed` before allowing `complete_current_task`.
- Add `resume <run-id>` support for turn-limit and recoverable error states, not only approval-paused runs.
- Increase or make configurable the team `max_turns` for repair-heavy tasks.
- Add a direct file-read tool and a restricted patch tool so agents can inspect and refine artifacts more accurately.
- Store expected artifact paths and validation commands directly on the task record so the orchestrator can verify them automatically.
