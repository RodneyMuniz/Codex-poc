## changed_files
- `scripts/operator_wall_snapshot.py`
- `tests/test_operator_wall_snapshot.py`

## exact_visibility_behavior
- `build_snapshot(...)` now includes canonical visual artifacts from the store in the operator wall artifact feed for the scoped project path.
- Task cards now resolve `latest_artifact` from canonical visual artifact records when present, so the card reflects the visual artifact returned by the store rather than only the generic artifact list.
- `recent_artifacts` now includes the canonical visual artifact record, and the visual artifact entry preserves fields such as `artifact_path`, `artifact_sha256`, `review_state`, `parent_visual_artifact_id`, `lineage_root_visual_artifact_id`, and `locked_base_visual_artifact_id`.
- The focused proof shows the edited visual artifact becomes the task card’s `latest_artifact` and also appears in `recent_artifacts` with matching canonical values.

## focused_tests_run
- `tests/test_operator_wall_snapshot.py::test_operator_wall_snapshot_reads_canonical_store` — passed
- `tests/test_operator_wall_snapshot.py::test_operator_wall_snapshot_surfaces_canonical_visual_artifacts` — passed

## result
Implemented.

## blocker_if_any
None.