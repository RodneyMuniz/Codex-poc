# M8 Operator Decision Input Rehearsal

## 1. Purpose

Record one bounded supervised rehearsal of the shell-safe operator decision input path selected in `AIO-044` and implemented in `AIO-045`, using the operator-facing `bundle-decision` surface with `--destination-mappings-file`.

## 2. Current Accepted Posture At Run Time

- `M1` through `M7` were complete at run start.
- `M8` was active as a narrow operator decision input/ergonomics hardening slice.
- Current readiness remained `ready only for narrow supervised bounded operation`.
- AIOffice remained not ready for a bounded supervised semi-autonomous cycle.
- Current live workflow proof still stopped at `architect`.
- This rehearsal did not widen workflow scope, did not add autonomy claims, and did not claim concurrency safety.

## 3. Exact Bounded Scope

- one persisted `pending_review` bundle only
- one explicit `apply` decision only
- one explicit `approved_by` value only
- one explicit file-based destination-mapping payload only
- no direct store-path decision execution for the decision step
- no later-stage workflow proof

## 4. Rehearsal Workspace/Store Setup

- transient rehearsal root:
  - `C:\Users\rodne\OneDrive\Desktop\_AIStudio_POC\projects\aioffice\artifacts\m8_operator_decision_input_rehearsal_20260415_run01`
- transient authoritative workspace root:
  - `C:\Users\rodne\OneDrive\Desktop\_AIStudio_POC\projects\aioffice\artifacts\m8_operator_decision_input_rehearsal_20260415_run01\workspace`
- sanctioned persisted store path:
  - `sessions/studio.db` under that workspace root
- setup used existing persisted-state helpers to create:
  - one `workflow_run`
  - one `stage_run`
  - one `workflow_artifact`
  - one `control_execution_packet`
  - one `execution_bundle`
- setup left the bundle in `pending_review` before the operator-facing decision step.

## 5. Exact Commands Run

```powershell
@'...setup fixture script...'@ | C:\Users\rodne\OneDrive\Desktop\_AIStudio_POC\venv\Scripts\python.exe -

C:\Users\rodne\OneDrive\Desktop\_AIStudio_POC\venv\Scripts\python.exe scripts/operator_api.py control-kernel-details --bundle-id bundle_d7f489586046 --workspace-root "C:\Users\rodne\OneDrive\Desktop\_AIStudio_POC\projects\aioffice\artifacts\m8_operator_decision_input_rehearsal_20260415_run01\workspace"

C:\Users\rodne\OneDrive\Desktop\_AIStudio_POC\venv\Scripts\python.exe scripts/operator_api.py bundle-decision --bundle-id bundle_d7f489586046 --action apply --approved-by project_orchestrator --destination-mappings-file "C:\Users\rodne\OneDrive\Desktop\_AIStudio_POC\projects\aioffice\artifacts\m8_operator_decision_input_rehearsal_20260415_run01\workspace\projects\aioffice\artifacts\m8_operator_decision_input_rehearsal\mappings\operator_decision_input_mappings.json" --decision-note "Supervised AIO-046 apply rehearsal via file-based operator input path." --workspace-root "C:\Users\rodne\OneDrive\Desktop\_AIStudio_POC\projects\aioffice\artifacts\m8_operator_decision_input_rehearsal_20260415_run01\workspace"

C:\Users\rodne\OneDrive\Desktop\_AIStudio_POC\venv\Scripts\python.exe scripts/operator_api.py control-kernel-details --bundle-id bundle_d7f489586046 --workspace-root "C:\Users\rodne\OneDrive\Desktop\_AIStudio_POC\projects\aioffice\artifacts\m8_operator_decision_input_rehearsal_20260415_run01\workspace"

@'...verification script...'@ | C:\Users\rodne\OneDrive\Desktop\_AIStudio_POC\venv\Scripts\python.exe -
```

## 6. Exact Identifiers Used

- `workflow_run_id`: `workflow_15f3d8d6f9d7`
- `stage_run_id`: `stage_eacba4e8e20a`
- `packet_id`: `packet_cb70fbd090e2`
- `bundle_id`: `bundle_d7f489586046`
- `artifact_id`: `wf_artifact_2f1274e84bd5`
- source artifact path:
  - `projects/aioffice/artifacts/m8_operator_decision_input_rehearsal/workflow_review/architect/operator_decision_input_rehearsal.md`
- authoritative destination path:
  - `projects/aioffice/execution/approved/operator_decision_input_rehearsal.md`

## 7. Before-Decision Inspection Result

Read-only inspection through `control-kernel-details` returned the persisted bundle context and showed:

- `execution_bundle.acceptance_state = pending_review`
- `task_id = AIO-046`
- `authoritative_workspace_root = projects/aioffice`
- `produced_artifact_ids = ["wf_artifact_2f1274e84bd5"]`
- initial evidence receipts:
  - `provider_metadata`

This confirmed the setup produced one persisted `pending_review` bundle before the operator-facing decision step.

## 8. Mapping-File Preparation And Contents

The successful decision step used a file-based mapping payload only.

- mapping file path:
  - `C:\Users\rodne\OneDrive\Desktop\_AIStudio_POC\projects\aioffice\artifacts\m8_operator_decision_input_rehearsal_20260415_run01\workspace\projects\aioffice\artifacts\m8_operator_decision_input_rehearsal\mappings\operator_decision_input_mappings.json`

Exact file contents:

```json
[
  {
    "source_artifact_id": "wf_artifact_2f1274e84bd5",
    "destination_path": "projects/aioffice/execution/approved/operator_decision_input_rehearsal.md"
  }
]
```

## 9. Decision Command Result

The actual decision step was executed through the operator-facing CLI wrapper with `--destination-mappings-file`.

Observed command result:

- exit code: `0`
- `command = bundle-decision`
- `action = apply`
- `approved_by = project_orchestrator`
- `destination_mappings_file` resolved to the mapping file above
- `inspection_before.bundle_acceptance_state = pending_review`
- `inspection_after.bundle_acceptance_state = applied`

The decision result also returned the updated persisted bundle with:

- `acceptance_state = applied`
- new evidence receipt kinds:
  - `apply_promotion_decision`
  - `authoritative_destination_write`

## 10. After-Decision Inspection Result

Read-only post-decision inspection through `control-kernel-details` returned the same persisted identifiers and showed:

- `execution_bundle.acceptance_state = applied`
- the same `workflow_run_id`, `stage_run_id`, `packet_id`, and `bundle_id`
- evidence receipts now included:
  - `provider_metadata`
  - `apply_promotion_decision`
  - `authoritative_destination_write`

This confirmed inspection remained tied to persisted state before and after the operator-facing decision step.

## 11. Verification Results

- setup verification:
  - one persisted `pending_review` bundle was created successfully
- operator-surface verification:
  - the successful decision used `scripts/operator_api.py bundle-decision`
  - the successful decision used `--destination-mappings-file`
  - no inline JSON was used for the successful decision step
- acceptance-state verification:
  - before decision: `pending_review`
  - after decision: `applied`
- authoritative write verification:
  - destination file exists: `true`
  - source SHA-256: `31bc4fe07a2546dcf5d77926fdce3b59ef3d4f323fd1628f8332c9e59aa3568b`
  - destination SHA-256: `31bc4fe07a2546dcf5d77926fdce3b59ef3d4f323fd1628f8332c9e59aa3568b`
  - source/destination content match: `true`
- workspace tree observed before cleanup:
  - `.workspace_authority.json`
  - `projects/aioffice/artifacts/m8_operator_decision_input_rehearsal/mappings/operator_decision_input_mappings.json`
  - `projects/aioffice/artifacts/m8_operator_decision_input_rehearsal/workflow_review/architect/operator_decision_input_rehearsal.md`
  - `projects/aioffice/execution/approved/operator_decision_input_rehearsal.md`
  - `projects/aioffice/governance/PROJECT_BRIEF.md`
  - `sessions/studio.db`
- unrelated residue checks inside the transient workspace:
  - `memory/framework_health.json`: `false`
  - `memory/session_summaries.json`: `false`
  - `projects/tactics-game/execution/KANBAN.md`: `false`

## 12. Manual Glue Reduced

- the successful decision step no longer required inline JSON transport on the exercised PowerShell path
- the operator could prepare mappings once in a JSON file and pass the file path directly to `bundle-decision`
- the decision surface remained one-bundle-at-a-time and stayed tied to persisted-state inspection before and after mutation

## 13. Remaining Manual Glue And Limits

- the operator still must prepare the destination-mapping file explicitly
- the operator still must know the target `bundle_id`
- the operator still must supply `approved_by` explicitly
- the operator still must author the destination path deliberately; no automatic mapping inference exists
- this rehearsal used an explicit transient `workspace_root`; default-root ergonomics were not expanded here
- this run proved one supervised `apply` decision only

## 14. Residual Risks

- concurrent contention handling remains unproven
- later-stage workflow remains unproven
- real multi-agent maturity remains unproven
- UAT readiness remains unproven
- shared-destination overwrite behavior observed in `M6` remains a live limit outside this one-bundle rehearsal

## 15. Final Conclusion

`AIO-046` proved that the operator-facing `bundle-decision` wrapper can drive one real sanctioned persisted-state decision through the shell-safe file-based mapping path selected in `AIO-044` and implemented in `AIO-045`. The rehearsal reduced operator input brittleness on the exercised shell path, but it did not expand workflow proof, did not reduce the need for explicit destination authoring, and did not change the accepted readiness posture.

## 16. Explicit Non-Claims

- no concurrency safety claim
- no later-stage workflow claim
- no semi-autonomous readiness claim
- no unattended or overnight operation claim
- no real multi-agent maturity claim
- no UAT readiness claim
