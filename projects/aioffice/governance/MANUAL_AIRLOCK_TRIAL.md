# AIOffice Manual Airlock Trial

- Status: draft under `AIO-020` for operator review.
- Governs the first manual packet-out / bundle-back rehearsal procedure for bounded executor work.
- Defines a manual control procedure only; it does not claim automation, runtime enforcement, or authoritative-state mutation by default.

## 1. Purpose And Scope

The manual airlock trial exists to rehearse bounded executor work before a control-kernel implementation exists. Its purpose is to prove packet-out and bundle-back discipline under AIOffice governance, not to maximize work volume or simulate a complete automated workflow.

This procedure is an orchestration-control rehearsal. It tests whether a governed task can be scoped, issued, executed, returned, and reviewed without granting authority to the executor. Any work produced through this procedure remains subject to separate review and apply or promotion decisions.

## 2. Trial Preconditions

A manual airlock trial may begin only when all of the following are explicit:

- the authoritative workspace root is known
- the governed task is identified by task ID and expected artifact path
- the bounded objective is written in operational terms
- allowed write paths are explicit
- expected artifact outputs are explicit
- review authority is explicit
- relevant governing packet, bundle, apply or promotion, and backlog rules are identified

At minimum, the trial packet must reference the governing rules in:

- `projects/aioffice/governance/EXECUTION_PACKET_SPEC.md`
- `projects/aioffice/governance/EXECUTION_BUNDLE_SPEC.md`
- `projects/aioffice/governance/APPLY_PROMOTION_POLICY.md`
- `projects/aioffice/governance/BOARD_RULES.md`
- `projects/aioffice/governance/BOARD_STATE_POLICY.md`

If any prerequisite is missing, the trial does not start. Missing preconditions are a fail-closed stop, not an invitation to improvise.

## 3. Packet-Out Procedure

Manual packet issuance follows this order:

1. Identify the governed task and confirm the task ID, objective, and expected artifact path.
2. Define the bounded objective in terms that can be checked after return.
3. Define the authoritative workspace root and the allowed write paths.
4. Define forbidden paths and forbidden actions, including any canonical-state mutation that is out of scope.
5. Define the required artifact outputs that the executor must return.
6. Define the required validations or checks, if any.
7. Define the expected return-bundle contents.
8. Record issuance provenance for the packet, including who authorized it, when it was issued, and which governance rules controlled it.

At minimum, a manual packet record must preserve:

- `packet_id`
- `task_id`
- bounded objective
- authoritative workspace root
- allowed write paths
- optional scratch or non-authoritative working path, if relevant
- forbidden paths or actions
- required artifact outputs
- required validations or checks
- expected return bundle contents
- failure reporting expectations
- issuance provenance

## 4. Executor Work Boundaries

During the trial, the executor:

- may work only within declared scope and allowed paths
- may return artifacts, blockers, questions, assumptions, and receipts
- may stop and report failure or ambiguity instead of guessing

During the trial, the executor may not:

- write outside declared allowed paths
- widen task scope without explicit operator authorization
- self-accept the work
- self-promote output to authoritative state
- mutate canonical state outside sanctioned apply or promotion paths
- treat self-report text as proof that the task is satisfied

The executor remains a bounded producer. It is not the review authority, the apply authority, or the backlog authority.

## 5. Bundle-Back Procedure

The manual return bundle must include all of the following, when applicable:

- `bundle_id`
- `packet_id`
- produced artifacts
- diff or patch references
- commands run
- test or check results, if any
- blockers
- questions
- assumptions
- self-report summary
- open risks
- evidence receipts

Manual bundle return follows this order:

1. Return the produced artifacts and identify their paths.
2. Return diff or patch references if any file changes were made.
3. Return the commands run.
4. Return the test or check results if any were requested or performed.
5. Return blockers, questions, and assumptions that affected the work.
6. Return a concise self-report summary.
7. Return the evidence receipts needed to review the work.

If a required bundle field is missing, the bundle is incomplete and must not be treated as sufficient by default.

## 6. Review And Rejection Checkpoints

The operator or control path reviews the returned bundle against the issued packet. Review must confirm:

- the bundle references its packet
- the required artifacts exist
- the required receipts and provenance exist
- declared scope boundaries were respected
- no unauthorized path or state mutation occurred
- the self-report does not substitute for proof

The bundle must be rejected or returned when any of the following is true:

- packet and bundle identifiers do not match
- a required artifact is missing
- a required receipt is missing
- the executor wrote outside allowed paths
- canonical state was mutated without sanctioned apply or promotion
- the bundle relies on narration instead of reviewable evidence
- the bundle omits required blockers, questions, or assumptions that materially affected the work

Rejected output may remain useful as evidence of what happened, but it is not authoritative state and it does not satisfy the governed task by default.

## 7. Apply / Promotion Checkpoint

Bundle acceptance is not the same as apply or promotion.

If a returned bundle is accepted as sufficient and reviewable, the next decision is separate:

- whether any output should be applied to an explicit authoritative destination path
- whether any output should be promoted into authoritative state
- whether the output should remain non-authoritative evidence only

Any later apply or promotion decision requires:

- an explicit destination path
- preserved provenance
- a controlled decision path

Rejected outputs may still remain attached to the bundle as evidence, but they do not become authoritative merely because they were returned.

## 8. Trial Outcomes

The manual airlock trial may end in one of these states:

- bundle sufficient and reviewable
- bundle insufficient and returned or rejected
- bundle blocked pending resolution
- output accepted for a later apply or promotion decision

The procedure alone never implies authoritative-state mutation. A completed manual trial is still only a reviewed control event unless a separate sanctioned apply or promotion decision occurs.

## 9. Minimal Examples

### Valid Example

A packet is issued for a governed documentation task with:

- an explicit `packet_id`
- allowed write path limited to `projects/aioffice/governance/`
- required artifact output `projects/aioffice/governance/MANUAL_AIRLOCK_TRIAL.md`
- expected bundle contents including the returned file path, commands run, and evidence receipts

The executor returns the drafted file, the commands used to inspect source governance docs, a concise self-report, and receipts showing the allowed path was respected. The bundle is reviewable, but the file still requires a separate apply or promotion decision if any non-authoritative working path was used.

### Invalid Example: Path Scope Violation

The packet allows writes only under `projects/aioffice/governance/`, but the executor also edits `sessions/store.py`. The bundle must be rejected because the executor exceeded declared path scope.

### Invalid Example: Self-Report Treated As Proof

The bundle says the task is done and summarizes the intended content, but it does not return the required artifact or supporting receipts. The bundle must be rejected because self-report is claim, not proof.

### Invalid Example: Bundle Accepted As Automatic Apply

The returned bundle includes a usable draft artifact, and the reviewer says the bundle looks good. The output is then treated as authoritative without an explicit destination-path and promotion decision. This is invalid because bundle acceptance does not automatically apply or promote outputs.

## 10. Deferred Implementation Notes

This procedure does not yet implement:

- an automated packet issuance engine
- an automated bundle validator
- an automated apply or promotion service
- a persisted workflow engine required by this task
- an operator UI required by this task
