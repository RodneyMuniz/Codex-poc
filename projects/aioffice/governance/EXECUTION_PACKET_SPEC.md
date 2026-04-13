# AIOffice Execution Packet Spec

Spec status:
- drafted under AIO-016 for operator review
- governs bounded packet issuance for Codex execution in AIOffice
- defines the packet contract without claiming an issuance engine or automated validator already exists

## 1. Purpose And Scope

This document defines the packet-out contract used to delegate bounded work to Codex. The packet exists to constrain executor activity to an explicit task, scope, path boundary, and evidence requirement.

An execution packet is not a conversational suggestion. It is the governed instruction container for bounded executor work. Issuing a packet does not grant stage authority, acceptance authority, or canonical state authority.

## 2. Packet Concept

An execution packet is one bounded authorization envelope for one unit of executor work.

Rules:
- a packet is tied to a specific task
- a packet may include workflow or stage context when relevant
- a packet defines where work may happen, what must be produced, and what is forbidden
- a packet does not authorize unbounded exploration, self-promotion, or state mutation outside its declared rules

## 3. Minimum Packet Fields

| Field | Purpose |
| --- | --- |
| `packet_id` | Uniquely identifies the packet issuance. |
| `task_id` | Ties the packet to the governed work item. |
| `workflow_or_stage_context` | Identifies the relevant workflow or stage boundary if present. |
| `objective` | States the bounded outcome the executor is being asked to produce. |
| `authoritative_workspace_root` | Names the authoritative root that governs the work. |
| `allowed_write_paths` | Declares the exact governed paths the executor may write. |
| `scratch_path_or_non_authoritative_working_path` | Declares any scratch or non-authoritative workspace if relevant. |
| `forbidden_paths_or_actions` | Declares explicit path and behavior prohibitions. |
| `required_artifact_outputs` | Declares the required produced artifacts or output surfaces. |
| `required_validations_or_checks` | Declares the required verification actions or expected checks. |
| `expected_return_bundle_contents` | Declares what the executor must return in the bundle. |
| `failure_reporting_expectations` | Declares how blockers, questions, assumptions, and failures must be reported. |

Rules:
- a packet missing any minimum field is invalid
- empty scope declarations do not count as valid packet boundaries
- a packet must be reviewable without relying on chat memory alone

## 4. Path And Scope Controls

Path and scope controls are mandatory.

Rules:
- the authoritative workspace root must be explicit
- allowed write paths must be explicit and bounded
- any scratch or non-authoritative working path must be explicit if used
- writes outside the allowed paths are forbidden
- paths outside the authoritative repo must not be treated as valid unless future governed policy explicitly allows them
- scope expansion by executor discretion is forbidden

Interpretation:
- if a path is not allowed, it is forbidden
- if a write boundary is ambiguous, the packet is insufficient
- scratch output is not authoritative merely because it was produced during packet execution

## 5. Forbidden Actions

The packet must explicitly forbid at least the following classes of behavior:

- modifying paths outside the declared allowed write scope
- mutating authoritative state outside sanctioned paths
- changing task or milestone status by executor self-assertion
- accepting stage sufficiency or bundle sufficiency
- issuing follow-on packets or expanding the scope unilaterally
- treating scratch output as self-promoted authoritative output
- bypassing required validations or checks

## 6. Required Output Artifacts

A valid packet must name the required output artifacts or output surfaces.

Rules:
- required artifact outputs must be explicit
- output paths must be reviewable against the task scope
- a packet may require zero code changes but it may not require zero declared outputs
- absence of a required output artifact is grounds for bundle rejection

## 7. Validation Expectations

Validation expectations define what the executor must attempt, report, or preserve.

Rules:
- required validations or checks must be explicit
- the packet must identify whether checks are expected, optional, unavailable, or not applicable
- skipped validations must be reported rather than implied away
- a packet does not become valid simply because validation is inconvenient

Examples of validation expectation classes:
- file-existence checks
- formatting or lint checks
- test execution
- manual inspection steps
- reconciliation against expected artifact paths

## 8. Issuance And Provenance Rules

Packet issuance must preserve provenance.

Rules:
- a packet must be traceable to a task and issuing authority
- the packet must preserve what was asked, by whom, and under what boundaries
- a packet may be revised only through a new or explicitly superseding governed issuance
- conversational restatements do not replace the packet as the execution boundary
- packet issuance does not grant stage authority

## 9. Minimal Examples

### Valid Packet Example

```yaml
packet_id: pkt_aio_016_001
task_id: AIO-016
workflow_or_stage_context: M3 protocol tranche
objective: define the bounded execution packet contract artifact
authoritative_workspace_root: C:\Users\rodne\OneDrive\Desktop\_AIStudio_POC
allowed_write_paths:
  - projects/aioffice/governance/EXECUTION_PACKET_SPEC.md
scratch_path_or_non_authoritative_working_path: none
forbidden_paths_or_actions:
  - projects/program-kanban/**
  - sessions/studio.db direct mutation
  - task status changes
required_artifact_outputs:
  - projects/aioffice/governance/EXECUTION_PACKET_SPEC.md
required_validations_or_checks:
  - reread final artifact for section completeness
expected_return_bundle_contents:
  - produced artifact reference
  - diff summary
  - self-report summary
  - evidence receipts
failure_reporting_expectations:
  - blockers
  - questions
  - assumptions
```

Why valid:
- scope is explicit
- write boundaries are explicit
- forbidden actions are explicit
- required outputs and return contents are explicit

### Invalid Packet Example

```yaml
task_id: AIO-016
objective: improve the system
allowed_write_paths:
  - .
```

Why invalid:
- `packet_id` is missing
- authoritative root is missing
- forbidden paths or actions are missing
- output and validation expectations are missing
- scope is effectively unbounded

## 10. Deferred Implementation Notes

The following are intentionally not implemented yet:
- no packet issuance engine
- no packet-signing or attestation mechanism
- no automated packet validator
- no packet registry or persistence model

This spec still governs now because later code and tests must derive executor boundary behavior from it.
