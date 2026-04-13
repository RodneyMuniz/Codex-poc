# AIOffice Apply And Promotion Policy

Policy status:
- drafted under AIO-018 for operator review
- governs apply, reject, and promotion decisions for non-authoritative outputs in AIOffice
- defines decision boundaries without claiming an apply engine, promotion service, or automated reviewer already exists

## 1. Purpose And Scope

This document defines how non-authoritative outputs may be applied, rejected, or promoted in AIOffice. Its purpose is to keep produced output, authoritative state, and authoritative backlog truth from collapsing into one ambiguous surface.

Apply and promotion are control decisions, not executor claims. Rejection is also a governed decision. None of these outcomes may be inferred from bundle narration alone.

## 2. Non-Authoritative Versus Authoritative Output

### Non-Authoritative Output
Non-authoritative output includes:
- scratch output
- executor-produced drafts
- packet outputs not yet accepted through a controlled path
- bundle contents that remain under review

Rules:
- non-authoritative output never self-promotes
- non-authoritative output may be useful, reviewable, and evidence-bearing without becoming authoritative
- non-authoritative output may inform decisions, but it does not become authoritative state by existence alone

### Authoritative Output
Authoritative output is output that has been accepted through a controlled path into an explicit authoritative destination.

Rules:
- authoritative status attaches through governed decision, not through production
- authoritative output must have an explicit destination path or authoritative state reference
- authoritative output must preserve provenance back to the packet, bundle, and source artifacts that produced it

## 3. Apply Concept

Apply is the controlled decision to take a non-authoritative output and write or merge it into an explicit authoritative destination.

Rules:
- apply requires an explicit destination path
- apply requires preserved provenance
- apply does not imply stage acceptance by default
- apply is valid only when the destination is governed and reviewable

Apply is appropriate when:
- the output should become part of an authoritative governed file path
- the operator or control path accepts the specific bounded change
- the apply action can be traced to a packet and bundle context

## 4. Reject Concept

Reject is the controlled decision that a non-authoritative output does not become authoritative state.

Rules:
- rejected output does not become authoritative
- rejected output may still remain useful as evidence, audit material, or defect context
- rejection must not silently erase provenance
- rejection must not be treated as if the output never existed

Reject is appropriate when:
- required artifacts are missing
- required receipts are missing
- output exceeds packet scope
- output conflicts with governance or destination-path constraints
- self-report and proof materially disagree

## 5. Promotion Concept

Promotion is the controlled decision to recognize a bounded output as the authoritative version for a named destination or state reference.

Rules:
- promotion requires an explicit authoritative destination
- promotion requires preserved provenance
- promotion does not occur because an executor says the output is ready
- promotion must not create a second truth surface

Promotion is appropriate when:
- the authoritative destination is explicit
- the output has passed the required review decision
- the authoritative system needs to recognize the output as the accepted version

## 6. Preconditions For Apply Or Promotion

Apply or promotion is valid only when all required preconditions are satisfied:
- the relevant packet and bundle context is identifiable
- the destination path or destination state is explicit
- required artifacts exist
- required receipts or equivalent proof exist
- scope boundaries were respected
- acceptance authority is exercised through a controlled decision path

Additional rules:
- if provenance is incomplete, apply or promotion is invalid
- if the destination path is ambiguous, apply or promotion is invalid
- if the bundle remains insufficient, apply or promotion is invalid
- if authoritative backlog truth would become inconsistent, apply or promotion is invalid

## 7. Rejection Conditions

Rejection conditions include:
- missing required artifacts
- missing required receipts
- missing or ambiguous destination path
- scope violations
- unauthorized path mutation
- unresolved blocker that prevents safe acceptance
- self-report claiming success without proof
- output that would create or reinforce a second truth surface

Rejection rules:
- rejection may preserve the output as evidence
- rejection does not permit silent reuse of the output as authoritative state later
- a later apply or promotion requires an explicit new controlled decision

## 8. Provenance And Destination-Path Requirements

Provenance and destination clarity are mandatory.

Required provenance elements include:
- the originating task
- the originating packet if present
- the originating bundle if present
- the produced artifact reference or references
- the review or decision context that authorized apply, rejection, or promotion

Required destination elements include:
- explicit destination path or authoritative state target
- confirmation that the destination is governed
- confirmation that the destination does not compete with another authoritative surface

Rules:
- destination path must be explicit
- provenance must be preserved
- a destination may not be implied from conversational convenience
- no second truth surface may be introduced

## 9. Relationship To Packets, Bundles, Artifacts, And Backlog Truth

Relationship rules:
- packets define what output may be produced
- bundles report what output was actually produced and what proof exists
- artifacts carry the durable output
- apply, reject, and promotion decisions determine whether those outputs become authoritative
- backlog truth records authoritative current task state, not self-reported executor authority

Interpretation:
- a packet does not pre-authorize promotion
- a bundle does not self-accept
- an artifact may exist without being authoritative
- authoritative backlog truth may record that a task reached `in_review` or `completed`, but that does not replace the need for explicit apply or promotion decisions where authoritative content changes are involved

## 10. Minimal Examples

### Valid Apply Example

- packet scope allows writing `projects/aioffice/governance/EXECUTION_PACKET_SPEC.md`
- a bundle returns the drafted file plus receipts
- operator accepts the change and the file is applied at that exact governed destination

Why valid:
- destination path is explicit
- provenance is preserved
- apply occurred through controlled decision rather than executor claim

### Valid Rejection Example

- a bundle returns a draft artifact and a self-report summary
- required receipts are missing
- the output is kept as review evidence, but not accepted into authoritative state

Why valid:
- rejected output remains useful as evidence
- rejection preserved provenance without granting authority

### Invalid Promotion Example

- an executor produces a scratch draft and says `this is now the official version`

Why invalid:
- non-authoritative output never self-promotes
- no controlled promotion decision occurred
- no explicit authoritative destination was accepted

## 11. Deferred Implementation Notes

The following are intentionally not implemented yet:
- no apply engine
- no promotion service
- no automated rejection workflow
- no persisted provenance graph beyond future control-kernel design

This policy still governs now because later code, persistence, and tests must derive authoritative-state mutation rules from it.
