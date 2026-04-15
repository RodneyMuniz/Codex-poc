# M6 Apply Branch Rehearsal

## Purpose Of The Rehearsal
- Execute one bounded supervised rehearsal of the separate sanctioned `apply` branch so current proof does not rely only on the already-recorded `promote` rehearsal.
- Keep the rehearsal low risk by using one non-authoritative source artifact and one explicit authoritative destination inside an isolated workspace rooted under `projects/aioffice/artifacts/`.

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
  - `projects/aioffice/artifacts/M5_APPLY_PROMOTION_REHEARSAL.md`
- Accepted posture at execution time remained:
  - `M1` through `M5` complete
  - current readiness `ready only for narrow supervised bounded operation`
  - not ready for a bounded supervised semi-autonomous cycle
  - current live workflow proof stops at `architect`
  - `AIO-036` is a narrow `M6` task and does not authorize a broader readiness claim
- The sanctioned apply/promotion path was identified in `sessions/store.py` as `SessionStore.execute_apply_promotion_decision(...)`, which explicitly accepts `approved_decision.action` values of `apply` or `promote`.
- No operator-facing apply/promotion command wrapper was found in `scripts/operator_api.py`; only the read-only `control-kernel-details` inspection command was available there.
- The required report file did not exist before this run:
  - `projects/aioffice/artifacts/M6_APPLY_BRANCH_REHEARSAL.md`

## Exact Bounded Scope Used
- One workflow run tied to `AIO-036`
- One `architect` stage run
- One non-authoritative source artifact created under the isolated workspace artifact tree
- One explicit approved decision with `action=apply`
- One explicit authoritative destination path inside the isolated workspace
- Out of scope:
  - later workflow stages beyond the existing architect-bound context
  - same-workspace or shared-store rehearsal behavior
  - unattended, overnight, or semi-autonomous operation
  - any code, schema, migration, runtime, or CLI behavior change

## Relevant Sanctioned Path Inspected
- `sessions/store.py`
  - `SessionStore.issue_control_execution_packet(...)`
  - `SessionStore.ingest_execution_bundle(...)`
  - `SessionStore.execute_apply_promotion_decision(...)`
- `scripts/operator_api.py`
  - `control-kernel-details` read-only inspection command against the isolated rehearsal workspace

## Verification Commands Run
1. Preflight shared apply/promotion store tests:

```powershell
C:\Users\rodne\OneDrive\Desktop\_AIStudio_POC\venv\Scripts\python.exe -m pytest tests/test_control_kernel_store.py -k apply_promotion
```

2. Supervised inline Python rehearsal using the sanctioned `SessionStore` path:

```powershell
C:\Users\rodne\OneDrive\Desktop\_AIStudio_POC\venv\Scripts\python.exe -
```

The inline rehearsal script performed these exact actions:
- instantiated `SessionStore` against `C:\Users\rodne\OneDrive\Desktop\_AIStudio_POC\projects\aioffice\artifacts\m6_apply_branch_supervised_rehearsal_20260415_run01\workspace`
- created one `workflow_run` and one `stage_run` for `AIO-036`
- wrote one non-authoritative source artifact
- persisted that source artifact as a workflow artifact
- issued one control execution packet
- ingested one pending-review execution bundle
- executed `SessionStore.execute_apply_promotion_decision(...)` with:
  - `decision: approved`
  - `action: apply`
  - `approved_by: Project Orchestrator`
  - destination path `projects/aioffice/execution/applied/architecture_decision_v1.md`

3. Post-decision read-only inspection:

```powershell
C:\Users\rodne\OneDrive\Desktop\_AIStudio_POC\venv\Scripts\python.exe scripts/operator_api.py control-kernel-details --bundle-id bundle_3c7eee67d328 --workspace-root "C:\Users\rodne\OneDrive\Desktop\_AIStudio_POC\projects\aioffice\artifacts\m6_apply_branch_supervised_rehearsal_20260415_run01\workspace"
```

4. Independent isolated-workspace file and side-effect check:

```powershell
$workspace = 'C:\Users\rodne\OneDrive\Desktop\_AIStudio_POC\projects\aioffice\artifacts\m6_apply_branch_supervised_rehearsal_20260415_run01\workspace'
$files = Get-ChildItem -Path $workspace -Recurse -File | ForEach-Object { $_.FullName.Substring($workspace.Length + 1).Replace('\','/') } | Sort-Object
$checks = [ordered]@{
  workspace_files = $files
  memory_framework_health = Test-Path (Join-Path $workspace 'memory\framework_health.json')
  memory_session_summaries = Test-Path (Join-Path $workspace 'memory\session_summaries.json')
  tactics_game_kanban = Test-Path (Join-Path $workspace 'projects\tactics-game\execution\KANBAN.md')
}
$checks | ConvertTo-Json -Depth 4
```

## Exact Rehearsal Identifiers And Paths
- isolated workspace:
  - `C:\Users\rodne\OneDrive\Desktop\_AIStudio_POC\projects\aioffice\artifacts\m6_apply_branch_supervised_rehearsal_20260415_run01\workspace`
- `workflow_run_id`: `workflow_7dbadce2cd5e`
- `stage_run_id`: `stage_294c547d0625`
- `source_artifact_id`: `wf_artifact_2680991ac047`
- `packet_id`: `packet_19f45b84d277`
- `bundle_id`: `bundle_3c7eee67d328`
- non-authoritative source artifact path:
  - `projects/aioffice/artifacts/m6_apply_branch_supervised_rehearsal/workflow_review/architect/architecture_decision_v1.md`
- authoritative destination path:
  - `projects/aioffice/execution/applied/architecture_decision_v1.md`

## Exact Results Of Verification
- Preflight store test result:
  - `6 passed, 10 deselected in 0.82s`
- Bundle acceptance-state transition:
  - before decision: `pending_review`
  - after decision: `applied`
- Destination-write result:
  - destination file existed after the decision
  - destination content matched the non-authoritative source content
  - source SHA-256: `5a4cbdfa3334502e14e1d58523c9cbf193a235e94a5a8299660e288d41be0693`
  - destination SHA-256: `5a4cbdfa3334502e14e1d58523c9cbf193a235e94a5a8299660e288d41be0693`
- Evidence receipts recorded on the updated bundle:
  - `provider_metadata`
  - `apply_promotion_decision`
  - `authoritative_destination_write`
- Tail receipts captured by the rehearsal:
  - `apply_promotion_decision`
    - `action: apply`
    - `approved_by: Project Orchestrator`
    - `decision: approved`
    - `decision_note: Approved bounded apply into the authoritative workspace.`
    - `captured_at: 2026-04-15T07:02:16+00:00`
  - `authoritative_destination_write`
    - `action: apply`
    - `destination_path: projects/aioffice/execution/applied/architecture_decision_v1.md`
    - `bytes_written: 56`
    - `source_artifact_id: wf_artifact_2680991ac047`
    - `modified_at: 2026-04-15T07:02:16+00:00`
- Read-only inspection result from `control-kernel-details`:
  - returned the expected `workflow_run`, `stage_run`, `packet`, and `bundle`
  - showed `task_id: AIO-036`
  - showed the packet provenance note `AIO-036 bounded apply-branch packet`
  - showed `execution_bundle.acceptance_state: applied`
  - showed preserved `apply_promotion_decision` and `authoritative_destination_write` receipts on the inspected bundle
- Independent isolated-workspace file and side-effect check result:
  - workspace files:
    - `projects/aioffice/artifacts/m6_apply_branch_supervised_rehearsal/workflow_review/architect/architecture_decision_v1.md`
    - `projects/aioffice/execution/applied/architecture_decision_v1.md`
    - `sessions/studio.db`
  - `memory/framework_health.json`: not present
  - `memory/session_summaries.json`: not present
  - `projects/tactics-game/execution/KANBAN.md`: not present

## Observed Behavior
- The separate sanctioned `apply` branch was executed through the implemented shared apply/promotion decision path, not merely inferred from policy text.
- The bounded bundle moved from `pending_review` to `applied`, not `promoted`.
- The authoritative destination write stayed inside the packet `authoritative_workspace_root` and outside governance-controlled, forbidden, and artifact-tree paths.
- The isolated rehearsal workspace did not show the specific unrelated side effects previously observed during the older `M5` promotion rehearsal path.

## Failure Or Ambiguity
- No execution failure was observed on the bounded path exercised here.
- One verification gap remains explicit:
  - the existing automated test suite covers shared apply/promotion constraints and the `promote` success path, but there was no pre-existing focused success test for `action=apply`; this rehearsal filled that gap with supervised store-path evidence rather than with a new code change.

## Result
- One bounded supervised rehearsal of the separate sanctioned `apply` branch was executed successfully.
- The rehearsal used existing sanctioned paths only and produced inspectable persisted evidence.
- This run does not change the accepted readiness posture by itself.

## Limitations
- This was one isolated rehearsal only.
- No operator-facing apply/promotion wrapper was exercised because no such wrapper was found in `scripts/operator_api.py`.
- The rehearsal did not prove later-stage workflow, same-workspace or shared-store behavior, unattended operation, overnight operation, or semi-autonomous readiness.

## Whether The Rehearsal Satisfied AIO-036
- Yes for the current task acceptance:
  - one supervised rehearsal of the sanctioned `apply` branch was executed
  - evidence was recorded factually
  - resulting state and limits are explicit
  - no later-stage, unattended, or overnight claim is made
- No broader claim is supported beyond this bounded supervised `apply` rehearsal.

## Follow-Up
- Immediate follow-up remains `AIO-037` for same-workspace repeated-run or shared-store contention behavior.
- Any readiness-posture change, if any, should wait for the later narrow review artifact under `AIO-038`.
