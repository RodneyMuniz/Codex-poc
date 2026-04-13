# AIOffice PM Discipline

Policy status:
- drafted under AIO-013 for operator review
- governs PM clarification and assumption discipline for AIOffice
- defines PM obligations without claiming a PM runtime or automation layer already exists

## 1. Purpose And Scope

This document defines how PM must handle uncertainty in AIOffice. The purpose is to prevent silent assumption collapse and ensure that non-trivial work does not pass through PM as if planning certainty already exists when it does not.

PM is not allowed to smooth over ambiguity by tone, confidence, or narrative compression. PM must produce durable outputs that preserve what is known, what is assumed, and what still requires clarification.

This policy applies to governed AIOffice PM work in the first integrity slice and is intended to support later enforcement.

## 2. Core Discipline Rules

Rules:
- no silent assumption collapse
- PM must produce `pm_plan_v1`
- for non-trivial work, PM must also produce either clarification questions or an assumption register
- PM may not claim a request is clear when important uncertainty remains undocumented
- PM may not hide unresolved ambiguity inside a confident plan summary

If uncertainty is present, PM must expose it in durable form.

## 3. Required PM Output Set

### Mandatory Output
- `pm_plan_v1`

Minimum contents for `pm_plan_v1`:
- problem framing
- scope
- `out_of_scope`
- decomposition
- intended stage path

### Required Branch Output For Non-Trivial Work
PM must also produce one of the following:
- `pm_clarification_questions_v1`
- `pm_assumption_register_v1`

This document does not define a trivial-work bypass. For current governed AIOffice workflow work, the safe default is to treat work as non-trivial unless future policy explicitly narrows that rule.

## 4. When Clarification Is Preferred Over Assumptions

Clarification is preferred when:
- operator intent is materially ambiguous
- multiple interpretations would change scope, acceptance, or stage path
- authoritative workspace or path boundaries are unclear
- donor reuse or dependency choices would differ based on the answer
- downstream architecture would otherwise depend on speculation
- the risk of being wrong is higher than the cost of pausing for an answer

Rules:
- clarification is the default response when missing information changes the shape of the work
- PM must not convert missing operator intent into assumptions merely to keep momentum
- questions must state why each unresolved point matters and what cannot be decided safely without an answer

## 5. When Assumptions Are Allowed

Assumptions are allowed only when:
- bounded continuation is still possible
- the assumption can be stated explicitly
- the impact or risk is visible
- the open implications are visible
- the assumption does not override explicit operator direction
- the assumption does not hide a blocker that should stop progression

Rules:
- assumptions are provisional, not silent truth
- assumptions permit bounded continuation only within their declared limits
- downstream stages must be able to see which parts of the work rest on assumptions

## 6. Effect Of Unresolved Ambiguity On Downstream Readiness

Unresolved ambiguity affects downstream readiness directly.

Rules:
- no `pm_plan_v1` means PM is not complete
- for non-trivial work, no clarification artifact and no assumption register means PM is not complete
- unresolved questions may block downstream readiness if they prevent safe context audit or architectural choice
- assumptions may allow downstream progression only when they are explicit and bounded
- downstream stages must not infer that PM is complete if the PM branch artifact is missing

Interpretation:
- `context_audit` may start only when PM outputs are sufficient for a bounded audit
- `architect` may not treat unresolved ambiguity as settled merely because PM produced a plan

## 7. PM Anti-Patterns

The following PM behaviors are invalid:
- passing work downstream with only a polished plan and no assumption or question branch
- burying uncertainty in prose without a governed artifact
- inventing answers to operator questions without recording them as assumptions
- labeling work as clear when scope or acceptance is still ambiguous
- using assumptions to bypass a blocker that should stop the workflow

## 8. Minimal Examples

### Valid PM Behavior: Clarification Path

- PM produces `pm_plan_v1`
- PM also produces `pm_clarification_questions_v1`
- each question explains why it matters and what cannot be decided safely without an answer

Why valid:
- PM exposed uncertainty explicitly instead of hiding it
- downstream stages can see what remains unresolved

### Valid PM Behavior: Assumption Path

- PM produces `pm_plan_v1`
- PM also produces `pm_assumption_register_v1`
- each assumption includes impact or risk and open implications

Why valid:
- PM preserved uncertainty in durable form
- downstream work can see the provisional basis for continuation

### Invalid PM Behavior: Silent Assumption Collapse

- PM produces `pm_plan_v1`
- ambiguous operator intent remains
- no clarification artifact or assumption register exists

Why invalid:
- PM hid unresolved ambiguity
- downstream work would have to guess what PM meant

### Invalid PM Behavior: False Confidence

- PM writes `scope is clear` in a summary
- the request still leaves major dependency or workspace questions unanswered
- no governed question artifact exists

Why invalid:
- narrative confidence does not satisfy PM discipline
- unresolved ambiguity was not preserved in the required artifact form

## 9. Deferred Implementation Notes

The following are intentionally not implemented yet:
- no PM automation or agent runtime
- no automatic PM sufficiency validator
- no persisted PM branch state model
- no automatic escalation engine for unanswered clarification questions

This policy still governs now because later code and tests must derive PM sufficiency and readiness logic from it.
