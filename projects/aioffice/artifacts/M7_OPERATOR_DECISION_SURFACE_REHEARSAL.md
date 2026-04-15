# M7 Operator Decision Surface Rehearsal

## 1. Purpose
- Record one bounded supervised rehearsal of the operator-facing `bundle-decision` surface added in `AIO-041`.
- Prove only that one persisted `pending_review` bundle can be inspected and then decided through the operator CLI wrapper without calling the store mutation path directly for the decision step.
- Keep the conclusion narrow and fail-closed.

## 2. Current Accepted Posture At Run Time
- `M1` through `M6` were complete when this run started.
- `M7` was active as a narrow operator decision-surface hardening slice.
- Current readiness remained `ready only for narrow supervised bounded operation`.
- AIOffice remained not ready for a bounded supervised semi-autonomous cycle.
- Current live workflow proof still stopped at `architect`.
- This rehearsal did not authorize any readiness upgrade, workflow expansion, concurrency claim, or later-stage proof claim.

## 3. Exact Bounded Scope
- One temporary sanctioned rehearsal workspace only.
- One persisted `pending_review` bundle only.
- One explicit decision only: `apply`.
- Setup used existing sanctioned persisted-state helpers to create the packet and bundle.
- The actual decision step used `scripts/operator_api.py bundle-decision`.
- Before and after inspection used `scripts/operator_api.py control-kernel-details`.

## 4. Rehearsal Workspace/Store Setup
- transient rehearsal workspace root:
  - `C:\Users\rodne\OneDrive\Desktop\_AIStudio_POC\projects\aioffice\artifacts\m7_operator_decision_surface_rehearsal_20260415_run01\workspace`
- transient persisted store:
  - `C:\Users\rodne\OneDrive\Desktop\_AIStudio_POC\projects\aioffice\artifacts\m7_operator_decision_surface_rehearsal_20260415_run01\workspace\sessions\studio.db`
- setup created:
  - one workflow run
  - one `architect` stage run
  - one produced source artifact under the non-authoritative artifact tree
  - one control execution packet
  - one execution bundle in `pending_review`
- authoritative workspace root recorded in persisted state:
  - `projects/aioffice`
- source artifact path:
  - `projects/aioffice/artifacts/m7_operator_decision_surface_rehearsal/workflow_review/architect/operator_decision_surface_rehearsal.md`
- destination path supplied explicitly by the operator decision:
  - `projects/aioffice/execution/approved/operator_decision_surface_rehearsal.md`

## 5. Exact Commands Run
1. Hygiene preflight:
```powershell
git status --short
```

2. Setup one temporary authoritative rehearsal workspace and one persisted `pending_review` bundle:
```powershell
@'
import json
from pathlib import Path
from sessions import SessionStore
from workspace_root import write_workspace_authority_marker

repo_root = Path(r"C:\Users\rodne\OneDrive\Desktop\_AIStudio_POC")
workspace_root = repo_root / "projects" / "aioffice" / "artifacts" / "m7_operator_decision_surface_rehearsal_20260415_run01" / "workspace"
if workspace_root.exists():
    raise SystemExit(f"Workspace already exists: {workspace_root}")
(workspace_root / "projects" / "aioffice" / "execution").mkdir(parents=True)
(workspace_root / "projects" / "aioffice" / "governance").mkdir(parents=True)
(workspace_root / "sessions").mkdir(parents=True)
(workspace_root / "governance").mkdir(parents=True)
(workspace_root / "projects" / "aioffice" / "governance" / "PROJECT_BRIEF.md").write_text(
    "# Brief\n\nAIOffice bounded operator decision rehearsal workspace.\n",
    encoding="utf-8",
)
(workspace_root / "sessions" / "approvals.json").write_text("", encoding="utf-8")
write_workspace_authority_marker(
    workspace_root,
    repo_name="_AIStudio_POC",
    canonical_root_hint=repo_root,
)
store = SessionStore(workspace_root)
workflow = store.create_workflow_run(
    "aioffice",
    task_id="AIO-042",
    objective="Rehearse the operator-facing bundle decision surface under supervision.",
    authoritative_workspace_root="projects/aioffice",
    current_stage="architect",
)
stage = store.create_stage_run(
    workflow["id"],
    stage_name="architect",
    status="in_progress",
)
source_artifact_path = "projects/aioffice/artifacts/m7_operator_decision_surface_rehearsal/workflow_review/architect/operator_decision_surface_rehearsal.md"
source_artifact_file = workspace_root / "projects" / "aioffice" / "artifacts" / "m7_operator_decision_surface_rehearsal" / "workflow_review" / "architect" / "operator_decision_surface_rehearsal.md"
source_content = "# Operator Decision Surface Rehearsal Source\n\nThis persisted bundle is waiting for one supervised operator decision.\n"
source_artifact_file.parent.mkdir(parents=True, exist_ok=True)
source_artifact_file.write_text(source_content, encoding="utf-8")
artifact = store.create_workflow_artifact(
    "aioffice",
    workflow_run_id=workflow["id"],
    stage_run_id=stage["id"],
    task_id="AIO-042",
    contract_name="operator_decision_surface_rehearsal",
    kind="document",
    content=source_content,
    proof_value="architecture_output",
    artifact_path=source_artifact_path,
    produced_by="Architect",
)
packet = store.issue_control_execution_packet(
    "aioffice",
    "AIO-042",
    objective="Issue one supervised operator-facing bundle decision through the sanctioned CLI wrapper.",
    authoritative_workspace_root="projects/aioffice",
    allowed_write_paths=[source_artifact_path],
    scratch_path="tmp/aioffice/operator-decision-surface-rehearsal",
    forbidden_paths=["projects/aioffice/governance", "projects/aioffice/execution/protected"],
    forbidden_actions=["self_accept", "self_promote"],
    required_artifact_outputs=[source_artifact_path],
    required_validations=["pytest tests/test_operator_api.py -k bundle_decision"],
    expected_return_bundle_contents=["produced artifacts", "evidence receipts"],
    failure_reporting_expectations=["report blockers", "report open risks"],
    workflow_run_id=workflow["id"],
    stage_run_id=stage["id"],
    issued_by="Project Orchestrator",
    provenance_note="AIO-042 bounded operator decision surface rehearsal packet",
)
bundle = store.ingest_execution_bundle(
    packet["packet_id"],
    produced_artifact_ids=[artifact["id"]],
    diff_refs=[source_artifact_path],
    commands_run=["python scripts/operator_api.py bundle-decision ..."],
    test_results=[{"command": "pytest tests/test_operator_api.py -k bundle_decision", "status": "passed"}],
    self_report_summary="Pending review bundle is ready for one supervised operator CLI decision rehearsal.",
    open_risks=["AIO-042 does not prove concurrency or later-stage workflow."],
    evidence_receipts=[{"kind": "setup_fixture", "provider": "manual_harness", "status": "captured"}],
)
destination_path = "projects/aioffice/execution/approved/operator_decision_surface_rehearsal.md"
payload = {
    "workspace_root": str(workspace_root),
    "workflow_run_id": workflow["id"],
    "stage_run_id": stage["id"],
    "packet_id": packet["packet_id"],
    "bundle_id": bundle["bundle_id"],
    "artifact_id": artifact["id"],
    "source_artifact_path": source_artifact_path,
    "source_artifact_file": str(source_artifact_file),
    "source_sha256": store.file_metadata(source_artifact_path)["artifact_sha256"],
    "destination_path": destination_path,
    "acceptance_state": bundle["acceptance_state"],
}
print(json.dumps(payload, indent=2))
'@ | .\venv\Scripts\python.exe -
```

3. Before-decision inspection:
```powershell
.\venv\Scripts\python.exe scripts/operator_api.py control-kernel-details --bundle-id bundle_3a2728c38467 --workspace-root "C:\Users\rodne\OneDrive\Desktop\_AIStudio_POC\projects\aioffice\artifacts\m7_operator_decision_surface_rehearsal_20260415_run01\workspace"
```

4. First direct shell attempt at `bundle-decision`:
```powershell
.\venv\Scripts\python.exe scripts/operator_api.py bundle-decision --bundle-id bundle_3a2728c38467 --action apply --approved-by "Project Orchestrator" --destination-mappings '[{"source_artifact_id":"wf_artifact_9678c457ab77","destination_path":"projects/aioffice/execution/approved/operator_decision_surface_rehearsal.md"}]' --decision-note "Supervised AIO-042 apply rehearsal via operator bundle-decision CLI." --workspace-root "C:\Users\rodne\OneDrive\Desktop\_AIStudio_POC\projects\aioffice\artifacts\m7_operator_decision_surface_rehearsal_20260415_run01\workspace"
```
- result: failed closed before persisted mutation with `{"error": "destination_mappings must be valid JSON.", "error_type": "ValueError"}`

5. Second direct shell attempt at `bundle-decision`:
```powershell
$json = @'
[{"source_artifact_id":"wf_artifact_9678c457ab77","destination_path":"projects/aioffice/execution/approved/operator_decision_surface_rehearsal.md"}]
'@; .\venv\Scripts\python.exe scripts/operator_api.py bundle-decision --bundle-id bundle_3a2728c38467 --action apply --approved-by "Project Orchestrator" --destination-mappings $json --decision-note "Supervised AIO-042 apply rehearsal via operator bundle-decision CLI." --workspace-root "C:\Users\rodne\OneDrive\Desktop\_AIStudio_POC\projects\aioffice\artifacts\m7_operator_decision_surface_rehearsal_20260415_run01\workspace"
```
- result: failed closed before persisted mutation with `{"error": "destination_mappings must be valid JSON.", "error_type": "ValueError"}`

6. Successful operator-facing decision step through the CLI wrapper:
```powershell
@'
import json
import subprocess
from pathlib import Path
repo_root = Path(r"C:\Users\rodne\OneDrive\Desktop\_AIStudio_POC")
command = [
    str(repo_root / "venv" / "Scripts" / "python.exe"),
    "scripts/operator_api.py",
    "bundle-decision",
    "--bundle-id",
    "bundle_3a2728c38467",
    "--action",
    "apply",
    "--approved-by",
    "project_orchestrator",
    "--destination-mappings",
    json.dumps([
        {
            "source_artifact_id": "wf_artifact_9678c457ab77",
            "destination_path": "projects/aioffice/execution/approved/operator_decision_surface_rehearsal.md",
        }
    ]),
    "--decision-note",
    "Supervised AIO-042 apply rehearsal via operator bundle-decision CLI.",
    "--workspace-root",
    r"C:\Users\rodne\OneDrive\Desktop\_AIStudio_POC\projects\aioffice\artifacts\m7_operator_decision_surface_rehearsal_20260415_run01\workspace",
]
completed = subprocess.run(command, cwd=repo_root, capture_output=True, text=True)
print(json.dumps({
    "command": command,
    "returncode": completed.returncode,
    "stdout": completed.stdout.strip(),
    "stderr": completed.stderr.strip(),
}, indent=2))
raise SystemExit(completed.returncode)
'@ | .\venv\Scripts\python.exe -
```

7. After-decision inspection:
```powershell
.\venv\Scripts\python.exe scripts/operator_api.py control-kernel-details --bundle-id bundle_3a2728c38467 --workspace-root "C:\Users\rodne\OneDrive\Desktop\_AIStudio_POC\projects\aioffice\artifacts\m7_operator_decision_surface_rehearsal_20260415_run01\workspace"
```

8. Narrow verification pass:
```powershell
@'
import json
from pathlib import Path
from sessions import SessionStore

repo_root = Path(r"C:\Users\rodne\OneDrive\Desktop\_AIStudio_POC")
workspace_root = repo_root / "projects" / "aioffice" / "artifacts" / "m7_operator_decision_surface_rehearsal_20260415_run01" / "workspace"
store = SessionStore(workspace_root, bootstrap_legacy_defaults=False)
bundle = store.get_execution_bundle("bundle_3a2728c38467")
artifact = store.get_workflow_artifact("wf_artifact_9678c457ab77")
destination_path = Path("projects/aioffice/execution/approved/operator_decision_surface_rehearsal.md")
destination_file = workspace_root / destination_path
source_file = workspace_root / Path(artifact["artifact_path"])
source_text = source_file.read_text(encoding="utf-8")
destination_text = destination_file.read_text(encoding="utf-8")
workspace_files = sorted(
    str(path.relative_to(workspace_root)).replace("\\", "/")
    for path in workspace_root.rglob("*")
    if path.is_file()
)
result = {
    "bundle_id": bundle["bundle_id"],
    "acceptance_state": bundle["acceptance_state"],
    "evidence_receipt_kinds": [receipt.get("kind") for receipt in bundle.get("evidence_receipts", []) if isinstance(receipt, dict)],
    "destination_exists": destination_file.exists(),
    "source_destination_match": source_text == destination_text,
    "source_sha256": store.file_metadata(artifact["artifact_path"])["artifact_sha256"],
    "destination_sha256": store.file_metadata(str(destination_path).replace("\\","/"))["artifact_sha256"],
    "workspace_files": workspace_files,
}
print(json.dumps(result, indent=2))
'@ | .\venv\Scripts\python.exe -
```

## 6. Exact Identifiers Used
- workspace root:
  - `C:\Users\rodne\OneDrive\Desktop\_AIStudio_POC\projects\aioffice\artifacts\m7_operator_decision_surface_rehearsal_20260415_run01\workspace`
- workflow_run_id:
  - `workflow_ae689f52af22`
- stage_run_id:
  - `stage_e97dc146f13e`
- packet_id:
  - `packet_6f38c6668213`
- bundle_id:
  - `bundle_3a2728c38467`
- produced artifact id:
  - `wf_artifact_9678c457ab77`
- source artifact path:
  - `projects/aioffice/artifacts/m7_operator_decision_surface_rehearsal/workflow_review/architect/operator_decision_surface_rehearsal.md`
- destination path:
  - `projects/aioffice/execution/approved/operator_decision_surface_rehearsal.md`
- source sha256 before decision:
  - `49f17ccb645e3c39065cba00165b360a648c1473ae7a5741038f9fec97953933`
- destination sha256 after decision:
  - `49f17ccb645e3c39065cba00165b360a648c1473ae7a5741038f9fec97953933`

## 7. Before-Decision Inspection Result
- `control-kernel-details` resolved the persisted bundle, packet, workflow, and stage context.
- `execution_bundle.acceptance_state` was `pending_review`.
- `inspection_workspace_root` matched the transient rehearsal workspace.
- the bundle contained one produced artifact:
  - `wf_artifact_9678c457ab77`
- evidence receipt kinds before decision were:
  - `setup_fixture`

## 8. Decision Command Result
- the successful decision step executed through `scripts/operator_api.py bundle-decision`.
- successful command return code:
  - `0`
- command payload reported:
  - `command = bundle-decision`
  - `bundle_id = bundle_3a2728c38467`
  - `approved_decision.decision = approved`
  - `approved_decision.action = apply`
  - `approved_decision.approved_by = project_orchestrator`
  - `approved_decision.decision_note = Supervised AIO-042 apply rehearsal via operator bundle-decision CLI.`
- decision receipt kinds after the successful command were:
  - `setup_fixture`
  - `apply_promotion_decision`
  - `authoritative_destination_write`
- two earlier shell-only attempts failed closed at JSON parsing before persisted mutation. The successful decision was still the only persisted bundle decision executed in this rehearsal.

## 9. After-Decision Inspection Result
- `control-kernel-details` continued to resolve the same persisted bundle, packet, workflow, and stage identifiers.
- `execution_bundle.acceptance_state` changed to `applied`.
- the persisted bundle retained the original produced artifact id:
  - `wf_artifact_9678c457ab77`
- evidence receipts now included both the decision receipt and the authoritative destination write receipt.
- the authoritative destination write receipt recorded:
  - `action = apply`
  - `destination_path = projects/aioffice/execution/approved/operator_decision_surface_rehearsal.md`
  - `source_artifact_id = wf_artifact_9678c457ab77`
  - `source_artifact_sha256 = 49f17ccb645e3c39065cba00165b360a648c1473ae7a5741038f9fec97953933`
  - `destination_artifact_sha256 = 49f17ccb645e3c39065cba00165b360a648c1473ae7a5741038f9fec97953933`

## 10. Verification Results
- setup verification:
  - one persisted bundle existed before the decision and it was `pending_review`
- decision-surface verification:
  - the actual persisted decision step was driven through `scripts/operator_api.py bundle-decision`
  - the decision wrapper routed through persisted state and returned pre/post inspection snapshots
- state-transition verification:
  - before decision: `pending_review`
  - after decision: `applied`
- destination-write verification:
  - destination file existed after the decision
  - destination content matched source content
  - source and destination sha256 values matched exactly
- workspace file tree observed before cleanup:
  - `.workspace_authority.json`
  - `projects/aioffice/artifacts/m7_operator_decision_surface_rehearsal/workflow_review/architect/operator_decision_surface_rehearsal.md`
  - `projects/aioffice/execution/approved/operator_decision_surface_rehearsal.md`
  - `projects/aioffice/governance/PROJECT_BRIEF.md`
  - `sessions/studio.db`
- failed-attempt verification:
  - the two direct PowerShell invocations failed at CLI input parsing with `destination_mappings must be valid JSON`
  - the successful command payload still reported `inspection_before.bundle_acceptance_state = pending_review`
  - this supports that the failed attempts did not mutate persisted bundle state

## 11. Manual Glue Reduced
- the operator no longer needed to call `SessionStore.execute_apply_promotion_decision(...)` directly for the decision step.
- the operator-facing wrapper now provided:
  - one bundle-scoped decision command
  - explicit approval input capture
  - persisted-state inspection snapshots before and after the decision
  - persisted evidence receipts tied to the resulting authoritative write

## 12. Remaining Manual Glue And Limits
- setup of the rehearsal bundle remained manual and helper-driven; packet issuance and bundle creation are not part of the operator decision surface.
- the operator still had to supply explicit `destination_mappings`.
- PowerShell argument quoting around JSON remained awkward enough that two direct shell invocations failed closed before the successful subprocess-backed CLI invocation.
- this surface still handles one bundle at a time only.
- this surface does not reduce manual review responsibility; the operator still decides the destination mapping and approval input explicitly.
- this surface does not advance the live workflow proof beyond `architect`.

## 13. Residual Risks
- concurrent contention handling remains unproven.
- later-stage workflow remains unproven.
- real multi-agent maturity remains unproven.
- UAT readiness remains unproven.
- previously observed last-write-wins behavior for reused authoritative destination paths was not re-tested away here; this rehearsal used one unique destination path only.

## 14. Final Conclusion
- This rehearsal proved one narrow thing only: the operator-facing `bundle-decision` wrapper can inspect one persisted `pending_review` bundle and drive one sanctioned `apply` decision against persisted state under supervision.
- Inspection before and after the decision remained tied to persisted control-kernel state.
- The resulting authoritative destination write was recorded with provenance and matched the source artifact content exactly.
- The proof boundary remains narrow and supervised.

## 15. Explicit Non-Claims
- This artifact does not claim concurrency safety.
- This artifact does not claim later-stage workflow proof.
- This artifact does not claim real PM / Architect / Dev / QA / Art runtime separation.
- This artifact does not claim unattended, overnight, or semi-autonomous readiness.
- This artifact does not claim UAT readiness.
