## changed_files
- `C:\Users\rodne\Dev\_AIStudio_worktrees\studio-control\agents\pm.py`
- `C:\Users\rodne\Dev\_AIStudio_worktrees\studio-control\tests\test_pm_flow.py`

## exact_propagation_behavior
- `ProjectManagerAgent._run_subtask()` now registers visual outputs immediately after worker completion and before QA review.
- When a worker result includes accepted lineage/edit fields, `_register_media_outputs()` propagates them into the canonical visual artifact record via `store.sync_visual_artifact(...)`.
- The propagated fields proven by the applied diff and focused test are:
  - `parent_visual_artifact_id`
  - `lineage_root_visual_artifact_id`
  - `locked_base_visual_artifact_id`
  - `edit_session_id`
  - `edit_intent`
  - `edit_scope`
  - `protected_regions`
  - `mask_reference`
  - `iteration_index`
- The canonical visual artifact record is created with deterministic metadata including:
  - `registered_by = "Framework"`
  - `registration_mode = "deterministic"`
  - `service_family = "visual"`
  - `owner_role`
  - `deliverable_type`
  - `deliverable_contract_kind`
  - `runtime_mode`
  - `agent_run_id`
  - `worker_summary`
- The run evidence records a `media_service_visual_registered` trace event containing the registered artifact id, artifact path, review state, selected direction, and agent run id.
- The test proves the propagated lineage/edit fields are present on both:
  - the stored visual artifact record, and
  - the corresponding run evidence entry.

## focused_tests_run
- `tests/test_pm_flow.py::test_pm_registers_visual_artifact_from_worker_output_before_qa`
  - Result: `.` `[`100%`]`
  - `1 passed in 0.78s`

## result
Implemented.

## blocker_if_any
None.