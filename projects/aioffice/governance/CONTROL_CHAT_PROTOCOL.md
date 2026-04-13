# AIOffice Control Chat Protocol

Protocol status:
- drafted under AIO-015 for operator review
- governs the operator-facing control-chat contract for AIOffice
- defines authoritative versus advisory chat behavior without claiming a runtime parser or command engine already exists

## 1. Purpose And Scope

This document defines the governed chat contract between the operator, the future control kernel, and reasoning systems. Its purpose is to keep chat useful without allowing chat narration to become hidden authority.

AIOffice uses chat as an interaction surface, not as a substitute for controlled state mutation. Chat may carry requests, clarifications, proposals, and decisions, but only controlled paths may authorize execution or mutate authoritative state.

This protocol defines:
- command classes
- operator-authorized decision verbs
- advisory versus authoritative actions
- governance-level command and result structure
- prohibited chat-only authority patterns

## 2. Command Classes

The governed command classes are:

| Command class | Purpose | Authority level |
| --- | --- | --- |
| `inspect` | Request current state, status, references, or bounded facts. | Advisory request; does not mutate state. |
| `propose` | Request options, plans, drafts, or reasoning support. | Advisory request; does not authorize execution or state change. |
| `clarify` | Request missing information, explain ambiguity, or resolve interpretation gaps. | Advisory request unless paired with an explicit decision verb. |
| `decide` | Record an operator decision about scope, priority, acceptance, or direction. | Authoritative only when applied through a controlled path. |
| `authorize_execution` | Permit bounded work against a defined task or packet. | Authoritative only through controlled issuance. |
| `review_or_accept` | Accept, reject, or return work for revision. | Authoritative only through controlled review paths. |
| `reconcile` | Correct conflicting records, stale projections, or mismatched claims. | Authoritative only when applied to the authoritative source through controlled paths. |

Rules:
- command class names describe intent, not automatic effect
- a command does not become authoritative merely because it sounds imperative
- an unclassified free-form statement must not be treated as implicit authorization

## 3. Operator-Authorized Decision Verbs

The following decision verbs define the operator-authority surface conceptually:

- `approve`
- `reject`
- `defer`
- `pause`
- `resume`
- `authorize`
- `revoke`
- `promote`
- `return_for_revision`
- `record`

Verb rules:
- decision verbs must target a named task, artifact, packet, bundle, or workflow element
- decision verbs must not rely on implied targets
- a decision verb may be expressed in natural language, but its controlled effect must still be explicit in the governed result
- absent an explicit decision verb, chat defaults to advisory interpretation

## 4. Advisory Versus Authoritative Actions

### Advisory Actions

Reasoning may:
- propose
- question
- summarize
- explain
- compare options
- identify risks or missing information

Advisory rules:
- advisory output does not change authoritative backlog state
- advisory output does not authorize execution
- advisory output does not accept artifacts or bundles
- advisory output may inform later decisions but does not replace them

### Authoritative Actions

Only controlled paths may:
- authorize execution
- change authoritative task or milestone state
- accept or reject stage outputs, bundles, or promotions
- promote non-authoritative output into authoritative state
- record binding decisions in canonical governed artifacts or future sanctioned control-plane state

Authoritative rules:
- chat alone is not granted execution or state authority
- authority attaches to controlled application of a decision, not to conversational tone
- reasoning may assist with the content of a decision, but not with its authority

## 5. Governance-Level Command Structure

At the governance level, a controlled chat command should be interpretable as having the following fields:

- `command_id`
- `issued_by`
- `command_class`
- `decision_verb` if applicable
- `target_ref`
- `objective_or_intent`
- `authority_level`
- `requested_effect`
- `constraints_or_scope`
- `timestamp_or_order_ref`

Rules:
- a valid command needs a target
- a valid authoritative command needs an explicit requested effect
- scope and constraint context must be visible for execution-oriented commands
- ambiguous conversational intent must not be silently upgraded into an authoritative command

## 6. Governance-Level Result Structure

At the governance level, a controlled command result should be interpretable as having the following fields:

- `result_id`
- `command_id`
- `result_type`
- `authoritative_or_advisory`
- `observed_effect`
- `produced_refs`
- `state_change_ref_or_none`
- `rejection_or_error_reason` if applicable

Rules:
- results must distinguish between observed effect and requested effect
- a result may confirm no state change occurred
- an advisory result must not pretend to be a state mutation result
- if a command was rejected, the rejection reason must be explicit

## 7. Prohibited Chat-Only Authority Patterns

The following patterns are forbidden:

- treating `go ahead` with no scoped target as implicit execution authority
- treating reasoning summaries as authoritative task-state changes
- treating persuasive architecture or planning prose as accepted state
- allowing a chat reply to self-issue an execution packet
- allowing a chat reply to self-accept a return bundle
- allowing projection surfaces to infer state changes from chat alone
- allowing natural-language ambiguity to mutate authoritative state silently

Reasoning may propose, question, and summarize. Only controlled paths may authorize state change or execution.

## 8. Minimal Examples

### Valid Advisory Example

Operator message:
`Propose options for the next M3 protocol artifact.`

Interpretation:
- command class: `propose`
- authority level: advisory
- effect: no state change, no execution authorization

### Valid Authoritative Example

Operator message:
`Approve AIO-015 for review and authorize the bounded execution packet for its artifact path only.`

Interpretation:
- decision verb: `approve` plus `authorize`
- target: `AIO-015`
- effect: authoritative only when applied through the controlled path that records the approval and issues the packet

### Invalid Authority Example

Reasoning message:
`I marked the task complete and started the next one.`

Why invalid:
- reasoning cannot self-authorize task-state change
- reasoning cannot self-start execution
- the message is a claim unless reflected through a controlled path

## 9. Deferred Implementation Notes

The following are intentionally not implemented yet:
- no command parser or grammar engine
- no authoritative chat-to-state mutation service
- no operator UI command palette requirement in this task
- no automatic result ledger tied to chat commands

This protocol still governs now because later code and tests must derive the separation between advisory reasoning and authoritative control from it.
