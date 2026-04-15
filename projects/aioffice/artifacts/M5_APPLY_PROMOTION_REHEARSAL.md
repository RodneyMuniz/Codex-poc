# M5 Apply/Promotion Rehearsal

## Purpose Of The Rehearsal
- Execute one supervised rehearsal of the implemented controlled apply/promotion path without claiming unattended behavior, later-stage workflow proof, or broader autonomy readiness.
- Keep the rehearsal low risk by using one non-authoritative artifact and one explicit authoritative destination inside an isolated workspace rooted under `projects/aioffice/artifacts/`.

## Preconditions
- Required governance/context files were loaded first:
  - `projects/aioffice/governance/PROJECT.md`
  - `projects/aioffice/governance/VISION.md`
  - `projects/aioffice/execution/KANBAN.md`
  - `projects/aioffice/governance/DECISION_LOG.md`
  - `projects/aioffice/governance/WORKFLOW_VISION.md`
  - `projects/aioffice/governance/STAGE_GOVERNANCE.md`
- Accepted posture at execution time remained:
  - `M1` through `M4` complete
  - `M5` partial
  - `AIO-029`, `AIO-030`, and `AIO-031` complete
  - `AIO-032` ready
- The implemented sanctioned apply/promotion path was identified in `sessions/store.py` as `SessionStore.execute_apply_promotion_decision(...)`.
- No operator-facing apply/promotion wrapper was found in `scripts/operator_api.py`; only the read-only `control-kernel-details` inspection command was available there.
- A focused automated validation was run first and passed:
  - command: `.\venv\Scripts\python.exe -m pytest tests/test_control_kernel_store.py -k controlled_apply_promotion_with_explicit_approved_decision`
  - observed result: `1 passed, 14 deselected`
- The rehearsal used an isolated workspace:
  - `C:\Users\rodne\OneDrive\Desktop\_AIStudio_POC\projects\aioffice\artifacts\m5_apply_promotion_supervised_rehearsal_20260415\workspace`

## Exact Bounded Scope Used
- One workflow run tied to `AIO-032`
- One `architect` stage run
- One non-authoritative source artifact created under the isolated workspace artifact tree
- One explicit promotion decision with `action=promote`
- One explicit authoritative destination path inside the isolated workspace
- Out of scope:
  - `apply` branch rehearsal
  - later workflow stages beyond the existing architect-bound context
  - unattended or overnight operation
  - any code, schema, migration, runtime, or CLI behavior change

## Relevant Sanctioned Path Inspected
- `sessions/store.py`
  - `SessionStore.issue_control_execution_packet(...)`
  - `SessionStore.ingest_execution_bundle(...)`
  - `SessionStore.execute_apply_promotion_decision(...)`
- `scripts/operator_api.py`
  - `control-kernel-details` read-only inspection command against the isolated rehearsal workspace

## Steps Executed
1. Ran the focused store test for the explicit approved-decision promotion case:
   - `.\venv\Scripts\python.exe -m pytest tests/test_control_kernel_store.py -k controlled_apply_promotion_with_explicit_approved_decision`
2. Created an isolated rehearsal workspace and instantiated `SessionStore` against that workspace root.
3. Created one persisted `workflow_run` and one persisted `stage_run` for `AIO-032`.
4. Wrote one non-authoritative source artifact at:
   - `projects/aioffice/artifacts/m5_apply_promotion_supervised_rehearsal/workflow_review/architect/architecture_decision_v1.md`
5. Persisted that source artifact as workflow artifact:
   - `workflow_run_id`: `workflow_fcbc1db7214f`
   - `stage_run_id`: `stage_f3bf8f02d3a0`
   - `source_artifact_id`: `wf_artifact_ff560f2a1045`
6. Issued one control execution packet for the rehearsal:
   - `packet_id`: `packet_c4596d656167`
   - authoritative workspace root: `projects/aioffice`
   - allowed write path: `projects/aioffice/artifacts/m5_apply_promotion_supervised_rehearsal/workflow_review/architect/architecture_decision_v1.md`
   - forbidden paths: `projects/aioffice/governance`, `projects/aioffice/execution/protected`
   - forbidden actions: `self_accept`, `self_promote`
7. Ingested one execution bundle:
   - `bundle_id`: `bundle_adfaad906f4b`
   - initial `acceptance_state`: `pending_review`
8. Executed the sanctioned apply/promotion decision through `SessionStore.execute_apply_promotion_decision(...)` with:
   - `decision`: `approved`
   - `action`: `promote`
   - `approved_by`: `Project Orchestrator`
   - destination path: `projects/aioffice/execution/approved/architecture_decision_v1.md`
9. Ran read-only inspection after the decision:
   - `.\venv\Scripts\python.exe scripts/operator_api.py control-kernel-details --bundle-id bundle_adfaad906f4b --workspace-root "C:\Users\rodne\OneDrive\Desktop\_AIStudio_POC\projects\aioffice\artifacts\m5_apply_promotion_supervised_rehearsal_20260415\workspace"`

## Evidence Observed
- Focused validation command passed before the rehearsal.
- The persisted bundle state changed from `pending_review` to `promoted`.
- The promoted destination file existed after the decision at:
  - `projects/aioffice/execution/approved/architecture_decision_v1.md`
- The promoted destination content matched the non-authoritative source content.
- The destination write receipt showed matching source and destination SHA-256:
  - `61a49153915ef2ae35fb744e1959f96968378be040f17b93c3f384a8a6f9a3a6`
- The updated bundle contained the expected review/provenance receipts:
  - `apply_promotion_decision`
  - `authoritative_destination_write`
- Read-only inspection through `operator_api.py control-kernel-details` returned:
  - the expected `workflow_run_id`, `stage_run_id`, `packet_id`, and `bundle_id`
  - one workflow artifact for the rehearsal source artifact
  - one execution bundle with `acceptance_state: promoted`
  - the preserved decision and destination-write evidence receipts
- Additional side effects observed inside the isolated rehearsal workspace:
  - `memory/framework_health.json`
  - `memory/session_summaries.json`
  - `projects/tactics-game/execution/KANBAN.md`

## Result
- One supervised rehearsal of the implemented controlled apply/promotion path was executed successfully.
- The rehearsal exercised the shared sanctioned apply/promotion decision path through the `promote` action.
- The rehearsal remained bounded and isolated; it did not mutate the main repo runtime path outside the isolated rehearsal workspace and the required evidence report artifact.

## Limitations
- This run exercised only the `promote` branch of the shared apply/promotion path. It did not separately rehearse the `apply` branch.
- No operator-facing apply/promotion command wrapper was exercised because no such wrapper was found in `scripts/operator_api.py`; the sanctioned store path was used directly.
- The rehearsal did not prove later-stage workflow, unattended operation, overnight operation, or semi-autonomous readiness.
- The isolated workspace still accumulated unrelated bootstrap files (`memory/*.json` and `projects/tactics-game/execution/KANBAN.md`), so workspace hygiene remains imperfect even though the promotion path itself succeeded.

## Whether The Rehearsal Satisfied AIO-032
- Yes for the current task acceptance:
  - one supervised rehearsal was executed
  - evidence was recorded factually
  - no autonomy overclaim was made
- No broader claim is supported beyond this bounded supervised promotion rehearsal.

## Blocker Or Follow-Up Needed
- Immediate follow-up remains `AIO-033` for broader supervised multi-run coverage.
- The workspace side-effect observation should remain visible during `AIO-033`/`AIO-034` review and may warrant separate hardening follow-up if it is confirmed as an active hygiene regression rather than an accepted bootstrap byproduct.
