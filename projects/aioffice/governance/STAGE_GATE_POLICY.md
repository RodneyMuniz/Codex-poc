# AIOffice Stage Gate Policy

Policy status:
- drafted under AIO-012 for operator review
- governs first-slice start and completion gates for AIOffice
- defines fail-closed gate rules without claiming a runtime gate engine already exists

## 1. Purpose And Scope

This policy defines the governance-level stage gates for the first AIOffice orchestration-integrity slice. Gates exist to prevent stage progression by narration, role claim, or missing proof. A stage may begin or complete only when its conceptual prerequisites are satisfied.

This version applies only to:
- `intake`
- `pm`
- `context_audit`
- `architect`

Later stages are intentionally out of scope for this policy version.

## 2. Gate Concepts

### Start Gate
A start gate defines what must exist before a stage may begin conceptually.

### Completion Gate
A completion gate defines what must exist before a stage may be treated as satisfied conceptually.

### Gate Failure
A gate failure exists when required proof, transfer state, or dependency conditions are missing, unresolved, or invalid.

### Fail-Closed Rule
If gate sufficiency is unclear, the stage does not pass. Ambiguity does not authorize progression.

## 3. First-Slice Start And Completion Gates

| Stage | Start gate | Completion gate | Common gate failures |
| --- | --- | --- | --- |
| `intake` | A governed request exists with a bounded objective and authoritative workspace context. | `intake_request_v1` exists and records the original request, explicit objective, and authoritative workspace path. | Missing request capture; missing objective; missing authoritative workspace path; no durable artifact. |
| `pm` | `intake_request_v1` exists and the requested work is bounded enough to plan. | `pm_plan_v1` exists and, for non-trivial work, either `pm_assumption_register_v1` or `pm_clarification_questions_v1` exists. Any required handoff or declared PM transfer state is present. | Missing `pm_plan_v1`; missing PM branch artifact; hidden assumptions; unresolved ambiguity not surfaced; missing handoff. |
| `context_audit` | PM completion gate is satisfied and the PM outputs identify enough scope to audit context. | `context_audit_report_v1` exists, records inspected sources, relevant findings, gaps, and risks, and the audit stage has a valid transfer record for `architect`. | Missing PM outputs; missing audit report; sources not identified; unresolved blocker ignored; missing handoff. |
| `architect` | PM completion gate is satisfied, `context_audit_report_v1` exists, and upstream artifacts plus transfer state are available. | `architecture_decision_v1` exists, references its upstream basis, and the first-slice stop-after-architect condition is explicit. | Missing PM outputs; missing context audit artifact; missing handoff; unresolved blocker or question that prevents architectural choice; no architecture artifact. |

## 4. Fail-Closed Dependency Rules

The first-slice dependency chain is strict:
- `pm` follows `intake`
- `context_audit` follows `pm`
- `architect` follows `pm` and `context_audit`

Dependency rules:
- `pm` cannot be treated as complete without `pm_plan_v1`
- for non-trivial work, `pm` also requires exactly one visible branch outcome: `pm_assumption_register_v1` or `pm_clarification_questions_v1`
- `context_audit` cannot start until PM completion requirements are met conceptually
- `architect` cannot start without PM and `context_audit` conceptual prerequisites
- `architect` cannot be treated as satisfied without `architecture_decision_v1`
- no stage may self-authorize because an upstream stage was implied in chat

## 5. Missing Artifacts, Handoffs, Questions, And Blockers

The following are gate failures:
- missing required artifact
- missing required handoff or equivalent transfer record
- unresolved question that materially affects safe downstream decision-making
- unresolved blocker that prevents truthful continuation
- assumption use where clarification is required
- ambiguous scope that makes the next stage unsafe to begin

Interpretation rules:
- missing artifacts are proof failures
- missing handoffs are transfer-state failures
- unresolved questions may be acceptable only when explicitly converted into governed assumptions
- unresolved blockers do not become acceptable through narration
- a downstream stage must not absorb or ignore an upstream gap silently

## 6. PM Branch Gate For Non-Trivial Work

This policy reserves the PM branch rule explicitly.

For non-trivial work:
- `pm_plan_v1` is mandatory
- PM must also produce either `pm_assumption_register_v1` or `pm_clarification_questions_v1`
- a PM output set with only `pm_plan_v1` fails completion

This version does not define a trivial-work bypass. Unless future policy says otherwise, first-slice governed work should be treated conservatively.

## 7. Architect Gate Constraints

Architect is the hardest boundary in the first slice because it depends on both planning and audited context.

Rules:
- architect does not start on PM output alone
- architect does not start on context audit narration alone
- architect requires PM outputs plus the context audit artifact and transfer context
- architect completion requires `architecture_decision_v1`
- the first integrity trial stops after architect and does not auto-authorize later stages

## 8. Out-Of-Scope Stages For This Policy Version

The following stages are out of scope for this policy version:
- `design`
- `build_or_write`
- `qa`
- `publish`

Rules:
- this document does not define their start or completion gates
- they may not be treated as governed by implication from first-slice gates
- first-slice completion does not claim readiness or completion for later stages automatically

## 9. Minimal Examples

### Valid First-Slice Progression

- `intake_request_v1` exists
- `pm_plan_v1` and `pm_assumption_register_v1` exist
- `context_audit_report_v1` exists
- `architecture_decision_v1` exists and references upstream artifacts
- the run stops after architect

This is valid because each stage passes its conceptual gate with durable proof.

### Invalid PM Gate Example

`pm_plan_v1` exists, but there is no assumption register and no clarification questions artifact.

This fails because non-trivial PM work did not emit the required branch artifact.

### Invalid Architect Start Example

PM outputs exist, but `architect` begins before `context_audit_report_v1` exists.

This fails because architect requires both PM and context audit conceptual prerequisites.

### Invalid Completion Example

A summary claims the first slice is complete, but the architect handoff exists without `architecture_decision_v1`.

This fails because handoff text does not replace the required architecture artifact.

## 10. Deferred Implementation Notes

The following are intentionally not implemented yet:
- no runtime gate engine
- no automated dependency evaluator
- no automatic artifact validator
- no automatic handoff validator
- no persisted stage gate state model

This policy still governs now because later code and tests must derive gate behavior from these fail-closed rules.
