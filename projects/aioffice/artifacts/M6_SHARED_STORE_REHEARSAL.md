# M6 Shared-Store Rehearsal

## Purpose Of The Rehearsal
- Execute a bounded same-workspace repeated-run rehearsal to determine whether the current sanctioned path remains stable when isolation is reduced by reusing the same workspace root and the same persisted store path across multiple supervised runs.
- Keep the rehearsal narrow by using the already-implemented sanctioned `apply` path, sequential reuse only, and no behavior changes during the run.

## Preconditions
- Required grounding files were loaded first:
  - `projects/aioffice/governance/PROJECT.md`
  - `projects/aioffice/governance/VISION.md`
  - `projects/aioffice/execution/KANBAN.md`
  - `projects/aioffice/governance/DECISION_LOG.md`
  - `projects/aioffice/governance/WORKFLOW_VISION.md`
  - `projects/aioffice/governance/STAGE_GOVERNANCE.md`
  - `projects/aioffice/execution/PROJECT_BRAIN.md`
  - `projects/aioffice/governance/M5_READINESS_REVIEW.md`
  - `projects/aioffice/governance/M5_CLOSEOUT_DECISION.md`
  - `projects/aioffice/governance/POST_M5_NEXT_SLICE_PLAN.md`
  - `projects/aioffice/governance/APPLY_PROMOTION_POLICY.md`
  - `projects/aioffice/artifacts/M6_APPLY_BRANCH_REHEARSAL.md`
- Accepted posture at execution time remained:
  - `M1` through `M5` complete
  - current readiness `ready only for narrow supervised bounded operation`
  - not ready for a bounded supervised semi-autonomous cycle
  - current live workflow proof stops at `architect`
  - `AIO-037` is a narrow `M6` task and does not authorize a broader readiness claim
- The sanctioned path used for both runs was the shared apply/promotion store path in `sessions/store.py`:
  - `SessionStore.issue_control_execution_packet(...)`
  - `SessionStore.ingest_execution_bundle(...)`
  - `SessionStore.execute_apply_promotion_decision(...)`
- The user-facing inspection surface used for post-run verification was the existing read-only operator CLI command:
  - `scripts/operator_api.py control-kernel-details`
- No operator-facing apply/promotion wrapper was found; the rehearsal therefore used the sanctioned persisted store path directly.
- The required report file did not exist before this run:
  - `projects/aioffice/artifacts/M6_SHARED_STORE_REHEARSAL.md`

## Exact Bounded Scope Used
- Two sequential supervised runs tied to `AIO-037`
- The same workspace root for both runs:
  - `C:\Users\rodne\OneDrive\Desktop\_AIStudio_POC\projects\aioffice\artifacts\m6_shared_store_rehearsal_20260415_run01\workspace`
- The same persisted store path for both runs:
  - `C:\Users\rodne\OneDrive\Desktop\_AIStudio_POC\projects\aioffice\artifacts\m6_shared_store_rehearsal_20260415_run01\workspace\sessions\studio.db`
- No workspace reset or cleanup between run 1 and run 2
- A fresh `SessionStore(...)` instance was opened for run 2 against the same workspace/store root to prove persistence rather than in-memory carryover
- Both runs used:
  - one `workflow_run`
  - one `architect` `stage_run`
  - one source artifact
  - one packet
  - one pending-review bundle
  - one approved decision with `action=apply`
- Both runs deliberately reused the same authoritative destination path:
  - `projects/aioffice/execution/applied/shared_store_decision.md`
- Out of scope:
  - later workflow stages beyond `architect`
  - any system fix or behavior change
  - concurrency beyond sequential reuse
  - unattended, overnight, or semi-autonomous operation

## Verification Commands Run
1. Preflight shared apply/promotion store tests:

```powershell
C:\Users\rodne\OneDrive\Desktop\_AIStudio_POC\venv\Scripts\python.exe -m pytest tests/test_control_kernel_store.py -k apply_promotion
```

2. Sequential same-workspace shared-store rehearsal:

```powershell
C:\Users\rodne\OneDrive\Desktop\_AIStudio_POC\venv\Scripts\python.exe -
```

The inline rehearsal script performed these exact actions:
- instantiated `SessionStore` against the shared workspace root for run 1
- executed run 1 through the sanctioned `apply` branch
- recorded counts after run 1
- instantiated a fresh `SessionStore` against the same workspace root for run 2
- confirmed that run 1 records were already visible before run 2 started
- executed run 2 through the sanctioned `apply` branch using the same destination path as run 1
- listed aggregate workflow, packet, and bundle counts after run 2
- listed the full shared workspace file tree after both runs
- checked for memory side files and cross-project leakage

3. Read-only inspection for run 1 bundle:

```powershell
C:\Users\rodne\OneDrive\Desktop\_AIStudio_POC\venv\Scripts\python.exe scripts/operator_api.py control-kernel-details --bundle-id bundle_01e63557b61f --workspace-root "C:\Users\rodne\OneDrive\Desktop\_AIStudio_POC\projects\aioffice\artifacts\m6_shared_store_rehearsal_20260415_run01\workspace"
```

4. Read-only inspection for run 2 bundle:

```powershell
C:\Users\rodne\OneDrive\Desktop\_AIStudio_POC\venv\Scripts\python.exe scripts/operator_api.py control-kernel-details --bundle-id bundle_41068dce7ef7 --workspace-root "C:\Users\rodne\OneDrive\Desktop\_AIStudio_POC\projects\aioffice\artifacts\m6_shared_store_rehearsal_20260415_run01\workspace"
```

5. Explicit file-tree and residue check after both runs:

```powershell
$workspace = 'C:\Users\rodne\OneDrive\Desktop\_AIStudio_POC\projects\aioffice\artifacts\m6_shared_store_rehearsal_20260415_run01\workspace'
$files = Get-ChildItem -Path $workspace -Recurse -File | ForEach-Object { $_.FullName.Substring($workspace.Length + 1).Replace('\','/') } | Sort-Object
$checks = [ordered]@{
  workspace_files = $files
  memory_framework_health = Test-Path (Join-Path $workspace 'memory\framework_health.json')
  memory_session_summaries = Test-Path (Join-Path $workspace 'memory\session_summaries.json')
  tactics_game_kanban = Test-Path (Join-Path $workspace 'projects\tactics-game\execution\KANBAN.md')
  duplicate_shared_destination_files = ($files | Where-Object { $_ -like 'projects/aioffice/execution/applied/shared_store_decision*' }).Count
}
$checks | ConvertTo-Json -Depth 4
```

## Exact Rehearsal Identifiers And Paths
### Shared Workspace And Store
- workspace root:
  - `C:\Users\rodne\OneDrive\Desktop\_AIStudio_POC\projects\aioffice\artifacts\m6_shared_store_rehearsal_20260415_run01\workspace`
- store path:
  - `C:\Users\rodne\OneDrive\Desktop\_AIStudio_POC\projects\aioffice\artifacts\m6_shared_store_rehearsal_20260415_run01\workspace\sessions\studio.db`
- shared authoritative destination path:
  - `projects/aioffice/execution/applied/shared_store_decision.md`

### Run 1
- `workflow_run_id`: `workflow_1d6960ab9ff1`
- `stage_run_id`: `stage_18ecfc28a1a1`
- `source_artifact_id`: `wf_artifact_571d3955900e`
- `packet_id`: `packet_9734459410c1`
- `bundle_id`: `bundle_01e63557b61f`
- source artifact path:
  - `projects/aioffice/artifacts/m6_shared_store_rehearsal/workflow_review/run_1/architect/architecture_decision_v1.md`
- source SHA-256:
  - `f281741f8b15582c31f2129203f80d3591cc334ee2839f6af70f3a96e358c326`

### Run 2
- `workflow_run_id`: `workflow_e4e92419397d`
- `stage_run_id`: `stage_596c15f45466`
- `source_artifact_id`: `wf_artifact_93bab8f1d737`
- `packet_id`: `packet_7a619c6e9646`
- `bundle_id`: `bundle_41068dce7ef7`
- source artifact path:
  - `projects/aioffice/artifacts/m6_shared_store_rehearsal/workflow_review/run_2/architect/architecture_decision_v1.md`
- source SHA-256:
  - `4fcef89cbb92d91f0f4e3f18ab4088bc98731226b870f86b4dc651241376bae1`

## Exact Results Of Verification
- Preflight store test result:
  - `6 passed, 10 deselected in 0.71s`
- Run 1 acceptance-state transition:
  - before decision: `pending_review`
  - after decision: `applied`
- Shared-store persistence check before run 2:
  - state after run 1:
    - `workflow_count: 1`
    - `packet_count: 1`
    - `bundle_count: 1`
  - state seen by a fresh `SessionStore(...)` before run 2:
    - `workflow_count: 1`
    - `packet_count: 1`
    - `bundle_count: 1`
- Aggregate counts after run 2:
  - `workflow_count: 2`
  - `packet_count: 2`
  - `bundle_count: 2`
- Identifier uniqueness check:
  - `workflow_run_ids_unique: true`
  - `stage_run_ids_unique: true`
  - `packet_ids_unique: true`
  - `bundle_ids_unique: true`
  - `artifact_ids_unique: true`
- Acceptance states across both runs:
  - run 1 bundle `bundle_01e63557b61f`: `applied`
  - run 2 bundle `bundle_41068dce7ef7`: `applied`
- Shared destination analysis:
  - both runs used the same destination path: `true`
  - destination existed after run 2: `true`
  - destination SHA after run 2:
    - `4fcef89cbb92d91f0f4e3f18ab4088bc98731226b870f86b4dc651241376bae1`
  - destination content after run 2:

```text
# Architecture Decision

Shared-store rehearsal run 2.
```

  - run 1 destination SHA at write time:
    - `f281741f8b15582c31f2129203f80d3591cc334ee2839f6af70f3a96e358c326`
  - run 2 destination SHA at write time:
    - `4fcef89cbb92d91f0f4e3f18ab4088bc98731226b870f86b4dc651241376bae1`
  - `run2_overwrote_run1_destination: true`
- Bundle scoping results:
  - run 1 bundle preserved:
    - `decision_action: apply`
    - `decision_note: Approved bounded shared-store apply run 1.`
    - `write_source_artifact_id: wf_artifact_571d3955900e`
    - `write_source_artifact_path: projects/aioffice/artifacts/m6_shared_store_rehearsal/workflow_review/run_1/architect/architecture_decision_v1.md`
    - `write_destination_sha: f281741f8b15582c31f2129203f80d3591cc334ee2839f6af70f3a96e358c326`
  - run 2 bundle preserved:
    - `decision_action: apply`
    - `decision_note: Approved bounded shared-store apply run 2.`
    - `write_source_artifact_id: wf_artifact_93bab8f1d737`
    - `write_source_artifact_path: projects/aioffice/artifacts/m6_shared_store_rehearsal/workflow_review/run_2/architect/architecture_decision_v1.md`
    - `write_destination_sha: 4fcef89cbb92d91f0f4e3f18ab4088bc98731226b870f86b4dc651241376bae1`
- Control-kernel inspection results:
  - run 1 `control-kernel-details` returned:
    - `task_id: AIO-037`
    - `workflow_run.id: workflow_1d6960ab9ff1`
    - `stage_run.id: stage_18ecfc28a1a1`
    - `control_execution_packet.packet_id: packet_9734459410c1`
    - `execution_bundle.bundle_id: bundle_01e63557b61f`
    - `execution_bundle.acceptance_state: applied`
    - `provenance_note: AIO-037 shared-store rehearsal packet run 1`
  - run 2 `control-kernel-details` returned:
    - `task_id: AIO-037`
    - `workflow_run.id: workflow_e4e92419397d`
    - `stage_run.id: stage_596c15f45466`
    - `control_execution_packet.packet_id: packet_7a619c6e9646`
    - `execution_bundle.bundle_id: bundle_41068dce7ef7`
    - `execution_bundle.acceptance_state: applied`
    - `provenance_note: AIO-037 shared-store rehearsal packet run 2`
- Full workspace file tree after both runs:
  - `projects/aioffice/artifacts/m6_shared_store_rehearsal/workflow_review/run_1/architect/architecture_decision_v1.md`
  - `projects/aioffice/artifacts/m6_shared_store_rehearsal/workflow_review/run_2/architect/architecture_decision_v1.md`
  - `projects/aioffice/execution/applied/shared_store_decision.md`
  - `sessions/studio.db`
- Side-effect and residue check:
  - `memory/framework_health.json`: `false`
  - `memory/session_summaries.json`: `false`
  - `projects/tactics-game/execution/KANBAN.md`: `false`
  - `duplicate_shared_destination_files: 1`

## Run 1 Versus Run 2 Comparison
- Both runs created unique workflow, stage, packet, bundle, and source-artifact identifiers.
- Both runs reached `acceptance_state: applied`.
- The same shared store root preserved run 1 state so a fresh `SessionStore(...)` saw `1 workflow / 1 packet / 1 bundle` before run 2 started.
- The same shared destination path was reused successfully by run 2.
- Run 2 overwrote the authoritative destination file created by run 1.
- The two non-authoritative source artifacts remained isolated in distinct per-run artifact-tree paths.
- The two bundles retained correctly scoped receipts even though the live authoritative destination file changed between run 1 and run 2.
- No cross-project leakage or unexpected side files appeared in the shared workspace during these sequential runs.

## Observed Behavior
- Sequential same-workspace reuse did not collapse bundle identity, packet identity, or receipt scoping in the persisted store on the path exercised here.
- The sanctioned path did not isolate the authoritative destination file by run. Reusing the same destination path caused the second run to replace the file content from the first run.
- The persisted store continued to expose both runs separately while the filesystem authoritative destination represented only the latest write.

## Failure Or Ambiguity
- No store-level collision, ID reuse, bundle disappearance, or cross-project leakage was observed in this sequential rehearsal.
- One material overwrite behavior was observed and kept explicit:
  - reusing the same authoritative destination path caused run 2 to overwrite the destination file from run 1
- This run was sequential only. It does not prove true concurrent contention handling.

## Result
- At least two supervised runs were executed sequentially against the same workspace root and the same persisted store path without resetting the workspace between runs.
- The control-kernel store remained inspectable and correctly scoped both runs by ID.
- The shared authoritative destination file was not isolated by run and was overwritten by the later run when the same destination path was reused.

## Limitations
- This rehearsal does not prove concurrency safety.
- This rehearsal does not prove later-stage workflow, unattended operation, overnight operation, or semi-autonomous readiness.
- This rehearsal does not change accepted readiness claims by itself.

## Whether The Rehearsal Satisfied AIO-037
- Yes for the current task acceptance:
  - a bounded same-workspace repeated-run/shared-store rehearsal was executed under supervision
  - collisions, overwrite behavior, residue checks, and scoping observations were recorded explicitly
  - authority boundaries remained unchanged
  - no later-stage, unattended, or overnight claim is made

## Follow-Up
- Immediate follow-up remains `AIO-038` to review what `AIO-036` and `AIO-037` together proved, what remains unproven, and whether the readiness posture changes at all.
