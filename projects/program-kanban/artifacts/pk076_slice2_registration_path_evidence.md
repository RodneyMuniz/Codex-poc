## 1. current_registration_path
Deterministic registration of a worker-produced visual artifact occurs via PM framework code calling the session store sync method and recording a trace event.

Evidence:
- PM registers the artifact and passes deterministic routing metadata into `record_trace_event`:
  - `C:\Users\rodne\Dev\_AIStudio_worktrees\studio-control\agents\pm.py` (lines ~376-409)
- PM calls the canonical storage layer via:
  - `C:\Users\rodne\Dev\_AIStudio_worktrees\studio-control\sessions\store.py - update/sync path` (`sync_visual_artifact` at ~3077+)
- `sync_visual_artifact` either creates or updates the artifact record, backed by a SQLite row plus filesystem hashing/byte accounting in `update_visual_artifact`:
  - `C:\Users\rodne\Dev\_AIStudio_worktrees\studio-control\sessions\store.py - update/sync path` (`update_visual_artifact` at ~2968+; `sync_visual_artifact` at ~3077+)

Concrete call sequence (from evidence):
1. Worker result is registered by PM:
   - `visual_artifact = self.store.sync_visual_artifact(...)` in `agents/pm.py`
2. Trace is recorded with deterministic execution mode and artifact indexing route:
   - `self.store.record_trace_event(... route={..., "execution_mode": "deterministic", ..., "service_key": "artifact_indexing"} ...)` in `agents/pm.py`

## 2. current_metadata_available_at_registration
At registration time (PM → `sync_visual_artifact`), the following metadata fields are explicitly available/used for the canonical visual artifact record:

From the PM registration call (it passes these into `sync_visual_artifact`):
- `run_id` (passed as `run_id`)
- `artifact_kind="image"` (`agents/pm.py` lines ~376-383)
- `provider` and `model` (`agents/pm.py` lines ~382-384)
- `prompt_summary=subtask.get("objective")` (`agents/pm.py` line ~384)
- `revised_prompt=correction_notes` (`agents/pm.py` line ~385)
- `review_state="pending_review"` (`agents/pm.py` line ~386)
- `selected_direction=False` (`agents/pm.py` line ~387)
- `metadata=metadata` (`agents/pm.py` line ~388-389)

Additionally, the test verifies specific metadata inserted into the stored artifact:
- `registered[0]["metadata"]["registered_by"] == "Framework"`
- `registered[0]["metadata"]["registration_mode"] == "deterministic"`
- `registered[0]["metadata"]["agent_run_id"] == "agent_run_visual_test"`
  - Evidence: `C:\Users\rodne\Dev\_AIStudio_worktrees\studio-control\tests\test_pm_flow.py` (lines ~416-423)

Metadata persistence behavior inside the store:
- When updating an existing visual artifact record, the store merges:
  - `merged_metadata = dict(artifact.get("metadata") or {})`
  - then `merged_metadata.update(metadata)` if new `metadata` is provided
- Then writes it as `metadata_json` in SQLite:
  - `C:\Users\rodne\Dev\_AIStudio_worktrees\studio-control\sessions\store.py - update/sync path` (~2968-3070)

## 3. missing_pk076_fields_not_yet_propagated
PK-076 slice 2 deterministic registration propagation requires propagating “first filesystem-backed storage model … Record prompt summary, provider, parent artifact, review state, selected direction, file paths, and file hashes.”

From the provided bundle, we can confirm that some of these fields are recorded at registration time (prompt/provider/review/selected_direction plus the store computes file hash and bytes). However, the bundle does **not** provide evidence that deterministic propagation of **parent/lineage** and **file-hash/path** is performed “downstream” for slice 2 (i.e., into other tasks/artifacts).

What’s missing (evidence not present in bundle):
1. **Propagation mechanics for deterministic registration** beyond the immediate registration call
   - No code in the bundle shows a “propagate deterministically” step that copies registration attributes to child artifacts or downstream records.
2. **Parent artifact linkage propagation** for slice 2
   - The store supports these linkage fields:
     - `parent_visual_artifact_id`, `lineage_root_visual_artifact_id`, `locked_base_visual_artifact_id`
     - Evidence: `C:\Users\rodne\Dev\_AIStudio_worktrees\studio-control\sessions\store.py - update/sync path` (~2978-2980, ~3011-3017; also test_store verifies them)
   - But the PM deterministic registration call shown in `agents/pm.py` does **not** pass `parent_visual_artifact_id` / lineage fields (it only passes `artifact_path`, prompt/provider/review/selected_direction/metadata).
   - So we cannot confirm deterministic propagation of parent/lineage fields for slice 2 from the bundle.
3. **File paths and hashes propagation to “review/handoff” consumers**
   - The store computes and stores:
     - `artifact["artifact_sha256"]` and `bytes_written` in `update_visual_artifact`
     - Evidence: `C:\Users\rodne\Dev\_AIStudio_worktrees\studio-control\sessions\store.py - update/sync path` (~3033-3034, ~3065-3066)
   - But the bundle does not include the slice-2 propagation logic that ensures these values are present/consistent in any downstream propagation target (only that the artifact record is updated).

In short: the bundle shows deterministic *registration* + trace + storage update/create, but does not show deterministic *propagation* of the PK-076 required relational fields (parent/lineage) to downstream artifacts/tasks.

## 4. exact_files_and_functions_for_pk076e
(“pk076e” here treated as the exact implementation points needed for deterministic registration propagation evidence.)

1. `C:\Users\rodne\Dev\_AIStudio_worktrees\studio-control\agents\pm.py`
   - Function/section: PM visual registration + deterministic trace routing
   - Evidence lines ~376-409 show:
     - `self.store.sync_visual_artifact(...)`
     - `self.store.record_trace_event(... route.execution_mode="deterministic", service_key="artifact_indexing")`

2. `C:\Users\rodne\Dev\_AIStudio_worktrees\studio-control\sessions\store.py - update/sync path`
   - `SessionStore.update_visual_artifact(...)` (starts ~2968)
     - Stores/updates: prompt summary, provider/model, parent/lineage/locked-base/edit provenance fields, review_state, selected_direction
     - Computes/stores file hash + bytes:
       - `_normalize_visual_artifact_path(...)` + `file_metadata(...)`
       - sets `artifact_sha256`, `bytes_written`
   - `SessionStore.sync_visual_artifact(...)` (starts ~3077)
     - Deterministic registration entrypoint for create-or-update by `(project_name, artifact_path, task_id)`

3. `C:\Users\rodne\Dev\_AIStudio_worktrees\studio-control\tests\test_pm_flow.py`
   - `test_pm_registers_visual_artifact_from_worker_output_before_qa(...)` (around ~366)
   - Evidence asserts deterministic metadata and that the trace includes `media_service_visual_registered`.

4. `C:\Users\rodne\Dev\_AIStudio_worktrees\studio-control\tests\test_store.py`
   - `test_store_tracks_locked_base_and_edit_session_provenance(...)` (around ~789)
   - Evidence asserts parent/lineage/locked-base/edit provenance fields are persisted and appear in run evidence.
   - This is relevant to PK-076 “parent artifact” requirement, but not tied to deterministic propagation in slice 2 by the PM code shown.

## 5. blocker_if_any
Yes—**blocker** for “Slice 2 deterministic registration propagation” specifically:

- The bundle provides evidence for deterministic *registration* (PM → `sync_visual_artifact` + trace event with `execution_mode="deterministic"`), but it does **not** provide the code path for the “propagation” part (i.e., how deterministic registration attributes/relationships are forwarded to other artifacts/tasks/consumers).
- Additionally, the PM registration call in `agents/pm.py` does not pass `parent_visual_artifact_id` / lineage fields, so deterministic propagation of the “parent artifact” linkage (required by PK-076) cannot be verified from the bundle.

Files implicated in the missing piece (but not present in bundle as propagation logic):
- `agents/pm.py` deterministic registration call is present, but propagation logic after registration is not shown.
- `sessions/store.py` shows persistence of linkage fields, but slice-2 propagation orchestration is not shown in the provided excerpts.