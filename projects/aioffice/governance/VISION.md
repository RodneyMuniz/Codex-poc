# AIOffice Vision

Vision status:
- accepted constitutional product baseline for AIOffice
- faithful promotion of the accepted product spec into project-local governance
- not an operational backlog, run log, or milestone-status ledger

Non-commitment rule:
- ideas in this document do not become backlog commitments until they are explicitly accepted into `execution/KANBAN.md` and, where needed, ratified in `governance/DECISION_LOG.md`

## 1. Target Users And User Posture

Primary user:
- the operator who is responsible for direction, approval, risk posture, and what becomes real

Supporting users:
- planners, architects, reviewers, and bounded executors working under operator and control-kernel authority

Required user posture:
- skeptical rather than credulous
- evidence-seeking rather than narration-seeking
- approval-aware rather than assumption-driven
- willing to trade some speed for bounded, reviewable, fail-closed work

AIOffice is for users who need controlled progress under ambiguity. It is not aimed at users who want hidden autonomy, prompt-only theater, or direct executor authority over canonical state.

## 2. Product Vision / North-Star

The north-star outcome is an operating system for governed work in which an operator can begin in free-form chat and still end with bounded execution, reviewable evidence, and deliberate durable state change without granting workflow authority to untrusted models.

AIOffice should make the following feel normal:
- chat is useful but not authoritative
- structured collaboration produces durable artifacts instead of role-play summaries
- execution is bounded and subordinate
- evidence outranks self-report
- apply, reject, and promotion decisions are explicit
- continuity survives pauses, reviews, and later re-entry

## 3. Core Product Principles

- fail-closed over fail-open
- authority in sanctioned code paths, not in prompts
- artifacts over narration
- evidence over claims
- explicit approval over implied permission
- one authoritative truth surface per concern
- bounded execution over free-form agent improvisation
- preserved provenance over convenience rewriting
- inspection and review before durable mutation
- product refinement without silent backlog creation

## 4. Harness Model

AIOffice is a thin outer harness around untrusted reasoning and execution tools.

The harness exists to:
- capture intent
- determine whether work is ready for governed handling
- constrain execution with explicit packets and boundaries
- preserve stage artifacts, handoffs, blockers, and review state
- separate claims from proof
- decide what is accepted, rejected, applied, or promoted

The harness is the product. The models inside it are subordinate tools, not the source of workflow truth.

## 5. Operating Model

The intended AIOffice operating model is:
1. free-form operator chat
2. readiness detection
3. structured PM, architecture, and design collaboration
4. operator approval for consequential action
5. bounded execution
6. evidence return
7. review, apply, reject, or promote
8. durable state update

Operating model rules:
- chat may carry intent, but not hidden authority
- structured collaboration must produce durable artifacts
- consequential work must be reviewable before it becomes real
- the workflow may stop safely when evidence is insufficient
- later implementation convenience does not outrank this control model

## 6. Product Boundaries And Authority Model

AIOffice boundaries are explicit:
- the operator gives direction and approval
- the control kernel owns workflow interpretation, review state, and controlled mutation
- reasoning systems may propose and assist, but do not self-authorize
- executors may produce bounded output, but do not decide stage sufficiency or acceptance
- projections, summaries, and logs remain derived or evidentiary unless governance explicitly says otherwise

Authority order:
1. operator
2. sanctioned control kernel
3. reasoning/orchestration assistance
4. bounded execution tools

Boundary rules:
- no chat-only authority
- no executor self-acceptance
- no executor self-promotion
- no silent second truth surface
- no weakening of governance by richer models, higher spend, or UI convenience

## 7. Product Lanes

AIOffice is organized around linked product lanes rather than one blended conversation surface:

- `chat lane`
  - captures free-form intent, clarification, and operator-facing interaction
- `structured collaboration lane`
  - produces PM, context, architecture, and later design artifacts
- `execution lane`
  - issues bounded packets and receives bounded output
- `evidence lane`
  - preserves artifacts, receipts, provenance, blockers, and review context
- `decision lane`
  - handles approval, rejection, apply, and promotion decisions
- `continuity lane`
  - preserves durable state so work can resume without relying on chat memory alone

These lanes may share surfaces, but they must remain conceptually distinct so authority and proof do not collapse together.

## 8. Domain Harnesses

The same control harness should apply across the canonical work domains:
- `intake`
- `pm`
- `context_audit`
- `architect`
- `design`
- `build_or_write`
- `qa`
- `publish`

Domain-harness rules:
- each domain must have explicit artifacts, handoffs, and review expectations
- later domains do not self-authorize because earlier domains existed
- the broader canonical domain set is constitutional even where live proof is still narrower

Current proof boundary:
- the currently proven live workflow slice stops at `architect`
- `design`, `build_or_write`, `qa`, and `publish` remain constitutional domains but are not yet proven as live workflow stages

## 9. Memory And Session Continuity Model

AIOffice continuity must come from sanctioned durable state, not from model recall alone.

Continuity requirements:
- workflow context should survive pauses, approval boundaries, and later resumption
- stage state, artifacts, handoffs, blockers, and assumptions should remain reviewable across sessions
- chat history may assist interpretation, but it must not be the only continuity surface
- authoritative operational status remains anchored to `execution/KANBAN.md`
- derived views and summaries remain non-authoritative unless governance explicitly changes that rule

The continuity model must preserve enough durable structure that a fresh summon can recover the true posture without replaying an entire transcript.

## 10. Execution Modes / Profiles / Budget Governance

AIOffice should support execution modes and profiles only as governed routing choices, never as governance exceptions.

Conceptual execution-mode families:
- interactive bounded execution for short supervised work
- background supervised execution for longer bounded work
- batch-style execution for repeated non-urgent bounded work
- scarce higher-spend escalation for ambiguity, architecture risk, or repeated lower-tier failure

Governance rules for execution modes:
- mode selection must remain subordinate to stage governance
- approval thresholds may rise with cost, ambiguity, or blast radius
- budget posture must be explicit rather than hidden inside runtime heuristics
- expensive lanes that do not outperform cheaper lanes should be demoted
- execution-profile or spend choices may not waive artifact, handoff, approval, or proof requirements

This section defines the constitutional requirement for budget-aware governance. It does not by itself create implementation commitments for a specific mode engine.

## 11. Functional Requirements

AIOffice must support the following functional outcomes at the product level:
- accept free-form operator requests without letting free-form chat become hidden authority
- detect when work is ready for governed handling
- create durable workflow containers and stage-specific artifacts
- preserve explicit questions, assumptions, blockers, and handoffs
- issue bounded execution packets with scoped constraints
- ingest return bundles without letting them self-accept
- separate evidence receipts from self-reported completion
- support controlled review, rejection, apply, and promotion decisions
- preserve inspectable workflow and provenance state
- reconcile conflicting claims against authoritative truth surfaces
- maintain continuity across pauses, reviews, and later re-entry

Current-proof rule:
- these are product requirements, not blanket claims that every requirement is already fully proven in current implementation

## 12. UX / UI Requirements

Any AIOffice user-facing surface must:
- distinguish advisory interaction from authoritative action
- show current stage position and stop points clearly
- expose blockers, assumptions, and missing proof instead of hiding them
- show provenance and evidence alongside claims
- make approval and review decisions explicit
- make authoritative versus derived surfaces obvious
- show current proof boundaries honestly, including where later-stage workflow remains unproven

UI rules:
- no interface may imply that later-stage workflow proof already exists when it does not
- no interface may imply that an operator workspace alpha already exists unless evidence says so
- polished presentation must not outrank governance clarity

## 13. Security And Governance Requirements

AIOffice must remain:
- fail-closed when state, evidence, or scope is ambiguous
- limited to sanctioned mutation paths for authoritative state
- exact-path and bounded in execution scope
- provenance-preserving for artifacts and decisions
- explicit about authoritative versus non-authoritative outputs
- reviewable by an operator without trusting conversational tone

It must prevent:
- chat-only authority
- executor self-acceptance
- executor self-promotion
- silent status mutation through projections
- silent divergence between evidence and accepted state
- governance weakening through execution profile, model class, or budget pressure

## 14. Success Metrics

Success should be measured by metric families such as:
- artifact completeness and stage-proof completeness
- rate of correctly blocked ambiguous or under-evidenced work
- approval fidelity for consequential actions
- provenance completeness for applied or promoted outputs
- continuity quality across pause, review, and resume boundaries
- operator inspection clarity and trust in the visible workflow state
- cost per successful bounded artifact by lane or profile family
- reduction in false progress claims, silent assumption collapse, and theater-like workflow narration

This defines what should be measured. It does not itself set operational thresholds or backlog commitments.

## 15. Risks And Open Questions

Known risks:
- persuasive narration can still mask weak enforcement if surfaces are not explicit
- donor reuse can import ambiguity if not tightly governed
- later-stage workflow proof remains unproven beyond `architect`
- safe migration away from markdown-first backlog truth remains unresolved until durable canonical-state preservation is ready
- budget-aware routing can become a governance hazard if cost optimization outranks proof requirements

Open questions:
- what exact readiness-detection implementation should govern the chat-to-work transition
- how far the operator-facing workspace should go before it risks becoming a misleading authority surface
- when and how later-stage domains should be proven live without over-claiming capability
- what long-horizon continuity model is sufficient once more workflow state is persisted formally

## 16. Roadmap Relationship

- the original `M1` through `M10` roadmap remains the strategic backbone
- `execution/KANBAN.md` remains the authoritative operational status source
- this vision may refine intended product direction, but it does not by itself create backlog commitments
- where current accepted execution has diverged, that divergence must remain explicit rather than silently folded back into roadmap wording
- constitutional product breadth is allowed to exceed the currently proven implementation slice

## 17. Change Protocol

Changes to this vision require:
- explicit review of the constitutional wording being changed
- preservation of the non-commitment rule
- preservation of fail-closed doctrine and authority boundaries
- explicit acceptance before new ideas become backlog commitments
- explicit divergence recording when product direction, roadmap wording, and operational truth no longer align automatically

Interpretation protocol:
- `VISION.md` governs product framing
- `execution/KANBAN.md` governs operational status truth
- `DECISION_LOG.md` records accepted divergence and re-baseline decisions where needed

## 18. Closing Definition

AIOffice is a governed harness for turning operator intent into bounded, evidence-backed work. It is successful when it makes trustworthy controlled progress possible without pretending that untrusted models, polished narration, or executor confidence are enough to define what is real.
