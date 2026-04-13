# AIOffice Execution Bundle Spec

Spec status:
- drafted under AIO-017 for operator review
- governs bundle-back returns from bounded executor work in AIOffice
- defines the bundle contract without claiming automated review or acceptance machinery already exists

## 1. Purpose And Scope

This document defines the return-bundle contract for executor work in AIOffice. The bundle exists to separate what the executor claims from what the executor can prove.

A bundle is a governed return package, not an acceptance event. A returned bundle may be sufficient, insufficient, or rejected. It never self-accepts.

## 2. Bundle Concept

An execution bundle is the bounded return package associated with one issued execution packet.

Rules:
- a bundle must reference the packet that produced it
- a bundle must distinguish produced artifacts from commentary about those artifacts
- a bundle may contain blockers, questions, and assumptions in addition to produced outputs
- a bundle is a review input, not authoritative acceptance

## 3. Minimum Bundle Fields

| Field | Purpose |
| --- | --- |
| `bundle_id` | Uniquely identifies the return bundle. |
| `packet_id` | Ties the bundle to the issued packet. |
| `produced_artifacts` | Lists the artifacts produced or updated. |
| `diff_or_patch_references` | Points to the code or document changes associated with the bundle. |
| `commands_run` | Records the commands the executor claims to have run. |
| `test_results_if_any` | Records observed test or check results when applicable. |
| `blockers` | Records any blocking conditions encountered. |
| `questions` | Records unresolved questions surfaced during execution. |
| `assumptions` | Records assumptions used during execution. |
| `self_report_summary` | Summarizes what the executor believes happened. |
| `open_risks` | Records risks that remain after the work. |
| `evidence_receipts` | Records the evidence trail supporting the bundle contents. |

Rules:
- a bundle missing any minimum field is insufficient
- empty placeholders do not satisfy these fields
- missing `produced_artifacts` is allowed only when the packet explicitly permitted a no-change result and the bundle proves why

## 4. Evidence Receipts And Provenance

Evidence receipts preserve proof and provenance for the bundle.

Receipt classes may include:
- artifact receipts
- diff or patch receipts
- command receipts
- test receipts
- review receipts

Rules:
- receipts must be specific enough to trace what evidence exists
- provenance must preserve where an artifact came from and under which packet it was produced
- a receipt must not be implied from self-report text alone
- if a required receipt is missing, the bundle may be rejected

## 5. Self-Report Limits

Self-report is allowed, but it is limited.

Rules:
- self-report is claim, not proof
- self-report may summarize work, blockers, questions, assumptions, and perceived outcomes
- self-report may not declare the bundle accepted
- self-report may not declare a stage satisfied
- self-report may not override missing receipts or missing artifacts

Bundle rule:
- a bundle never self-accepts

## 6. Claim / Proof Separation

Bundles must preserve a clean separation between claims and proof.

Claims include:
- what the executor believes was changed
- what the executor believes passed
- what the executor believes remains risky

Proof includes:
- produced artifact references
- diff or patch references
- command receipts
- test receipts
- other evidence receipts preserved in durable form

If claim and proof disagree, proof governs and the discrepancy must be reviewed explicitly.

## 7. Insufficiency And Rejection Conditions

The bundle is insufficient or rejectable if any of the following occur:
- missing required artifacts
- missing required receipts
- missing packet reference
- missing diff or patch references when changes were made
- self-report claims completion with no supporting proof
- blockers, questions, or assumptions are hidden instead of surfaced
- bundle contents exceed the packet scope without explicit reauthorization

Missing receipts or missing required artifacts are grounds for rejection.

## 8. Minimal Examples

### Valid Bundle Example

```yaml
bundle_id: bundle_aio_017_001
packet_id: pkt_aio_017_001
produced_artifacts:
  - projects/aioffice/governance/EXECUTION_BUNDLE_SPEC.md
diff_or_patch_references:
  - patch_ref_001
commands_run:
  - Get-Content -Raw projects/aioffice/governance/EXECUTION_PACKET_SPEC.md
test_results_if_any:
  - not_applicable
blockers: []
questions: []
assumptions:
  - packet examples remain governance-level, not implementation-specific
self_report_summary: Drafted the bundle spec and reread it for section completeness.
open_risks:
  - later implementation may require stricter receipt normalization
evidence_receipts:
  - artifact_receipt: projects/aioffice/governance/EXECUTION_BUNDLE_SPEC.md
  - patch_receipt: patch_ref_001
  - command_receipt: readback complete
```

Why valid:
- the bundle points to its packet
- claims and evidence are both visible
- the bundle does not self-accept

### Invalid Bundle Example

```yaml
packet_id: pkt_aio_017_001
self_report_summary: Everything is done and approved.
```

Why invalid:
- `bundle_id` is missing
- produced artifacts are missing
- diff or patch references are missing
- evidence receipts are missing
- the self-report tries to self-accept

## 9. Deferred Implementation Notes

The following are intentionally not implemented yet:
- no bundle registry
- no automated receipt validator
- no automated acceptance or rejection engine
- no persisted provenance model beyond future control-kernel design

This spec still governs now because later code and tests must derive bundle sufficiency and rejection behavior from it.
