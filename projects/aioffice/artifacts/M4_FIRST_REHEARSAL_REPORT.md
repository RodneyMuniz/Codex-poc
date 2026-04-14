# M4 First Rehearsal Report

## Purpose And Scope
- This rehearsal was run to verify the first implemented AIOffice control-kernel slice under supervision.
- The goal was orchestration integrity, not throughput or unattended execution.
- The rehearsal stayed inside the first slice through `architect` and did not claim apply/promotion, publish, or overnight readiness.

## Rehearsal Task Definition
- Bounded task: prepare an architect-stage decision for a one-paragraph authoritative-root reminder note.
- Why this task was chosen: it is low risk, documentary, narrow, and sufficient to exercise persisted workflow state, packet issuance, bundle return, read-only inspection, and fail-closed stage checks without triggering UI or broad implementation work.

## Preconditions
- Branch at execution time: `work/aioffice-post-m3-curation-2026-04-14`.
- Accepted prerequisites already existed for:
  - persisted control-kernel entities and store helpers
  - packet issuance and bundle ingestion
  - read-only inspection
  - fail-closed first-slice transition checks
- The rehearsal used an isolated persisted workspace under `projects/aioffice/artifacts/m4_rehearsal_workspace/` to avoid mutating the repo's main runtime state.
- Raw evidence snapshot was recorded at `projects/aioffice/artifacts/M4_FIRST_REHEARSAL_EVIDENCE.json`.

## Packet Issuance Summary
- `workflow_run_id`: `workflow_10021285208c`
- `packet_id`: `packet_4aff81cd6cde`
- Packet objective: create the architect-stage reminder note artifact and return a bounded evidence bundle.
- Authoritative workspace root in packet: `projects/aioffice`
- Allowed write path: `projects/aioffice/artifacts/rehearsal_authoritative_root_note.md`
- Forbidden paths: `projects/aioffice/governance`, `scripts`, `app`
- Forbidden actions: `self_accept`, `self_promote`, `publish`
- Required output path: `projects/aioffice/artifacts/rehearsal_authoritative_root_note.md`
- Provenance note: `Supervised M4 first rehearsal packet`

## Workflow/Stage State Created
- One persisted `workflow_run` was created for `AIO-027`.
- Four persisted `stage_run` records were created in the first slice:
  - `intake`: `stage_73a25dc91a77`
  - `pm`: `stage_e5442d89ad73`
  - `context_audit`: `stage_2642cfb065ec`
  - `architect`: `stage_ddb9ad3533b2`
- Persisted first-slice artifacts created:
  - `intake_request_v1`
  - `pm_plan_v1`
  - `pm_assumption_register_v1`
  - `context_audit_report_v1`
  - `architecture_decision_v1`
- Persisted handoffs created:
  - `intake -> pm`
  - `pm -> context_audit`
  - `context_audit -> architect`
- Persisted support records created:
  - one blocker
  - one question
  - one assumption
  - three orchestration traces

## Bundle Return Summary
- `bundle_id`: `bundle_355f9a95a5da`
- Produced artifact id: `wf_artifact_92d4c52e03c2`
- Returned diff/reference path: `projects/aioffice/artifacts/rehearsal_authoritative_root_note.md`
- Returned evidence receipts included:
  - file write receipt
  - inspection receipt
  - gate-check receipt
- Bundle `acceptance_state` remained `pending_review`
- No self-acceptance path was used or implied

## Inspection Path Used
- Read-only inspection was exercised through `scripts/operator_api.py` by calling the control-kernel details path (`_control_kernel_details`) against the persisted rehearsal store.
- Inspection returned the expected persisted state for:
  - the workflow run
  - all four stage runs
  - five workflow artifacts
  - three handoffs
  - one blocker
  - two question/assumption records
  - three orchestration traces
  - the issued control execution packet
  - the returned execution bundle

## Gate Checks Exercised
- `intake` completion passed with `intake_request_v1`
- `pm` start passed only after `intake -> pm` handoff and intake artifact were present
- `pm` completion passed only after `pm_plan_v1` and `pm_assumption_register_v1` were present
- `context_audit` start passed only after PM outputs and `pm -> context_audit` handoff were present
- Controlled fail-closed probe:
  - `architect` start failed before `context_audit_report_v1` and `context_audit -> architect` handoff existed
  - recorded failure message: `architect start requires handoff context_audit->architect for attempt 1. architect start requires context_audit_report_v1.`
- `context_audit` completion passed after `context_audit_report_v1`
- `architect` start passed after the missing context audit artifact and handoff were added
- `architect` completion passed only after `architecture_decision_v1`

## Observed Successes
- The persisted first-slice workflow model worked end-to-end for one supervised low-risk task.
- Packet issuance and bundle ingestion both succeeded against persisted state.
- The bundle remained review-pending, which preserved the no-self-acceptance rule.
- The read-only inspection path returned workflow, stage, packet, bundle, and evidence state without introducing a writable surface.
- The fail-closed architect start probe behaved as intended before prerequisites existed.

## Observed Failures Or Gaps
- No unexpected runtime failure occurred during the bounded rehearsal.
- One expected fail-closed checkpoint was observed and is treated as proof of gate enforcement, not as a defect.
- One real gap was observed:
  - the isolated `SessionStore` bootstrap created unrelated side files inside the rehearsal workspace, including `projects/tactics-game/execution/KANBAN.md`, alongside memory bootstrap files
  - this means the current store bootstrap is still coupled to legacy project defaults in a way that is broader than the rehearsal task required

## What Was Proven
- A supervised first-slice workflow can be persisted without using canonical task rows.
- Multiple first-slice stage records can be created and checked in order.
- Packet issuance can be recorded against a stage-specific workflow context.
- Bundle return can be recorded with receipts and remain pending review.
- Read-only inspection can surface persisted workflow, packet, bundle, and evidence state.
- First-slice gate checks can fail closed before prerequisites exist and pass after the required artifacts and handoffs are present.

## What Remains Unproven
- Full end-to-end operator CLI invocation was not used in this rehearsal; the read-only helper path was exercised directly.
- Apply/promotion remains unproven.
- Any later-stage flow after `architect` remains unproven.
- Unattended or overnight operation remains unproven.
- Rehearsal review was supervised and documentary; no autonomy claim is supported by this result.

## Recommended Next Fixes Before AIO-028
- Remove or isolate legacy store bootstrap side effects so bounded AIOffice rehearsals do not create unrelated project files.
- Decide whether the next supervised rehearsal should exercise the full operator CLI wrapper, not just the read-only helper path.
- Preserve the current `pending_review` bundle behavior and keep apply/promotion out of scope until explicitly implemented and reviewed.
- Use the evidence snapshot from this rehearsal to drive the M4 implementation review, including the remaining unproven areas above.
