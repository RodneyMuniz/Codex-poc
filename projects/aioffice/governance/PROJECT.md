# AIOffice Founding Charter

Charter status:
- drafted under AIO-001 for operator review
- intended to replace the bootstrap stub
- not a later-task kickoff

## 1. Project Identity
- name: AIOffice
- slug: `aioffice`
- project type: governance-first orchestration-integrity project inside the existing monorepo
- repo location: `C:\Users\rodne\OneDrive\Desktop\_AIStudio_POC\projects\aioffice`
- authoritative workspace root: `C:\Users\rodne\OneDrive\Desktop\_AIStudio_POC`
- relationship to ProjectKanban as donor system:
  - ProjectKanban is a donor and reference system, not the architectural authority for AIOffice.
  - AIOffice may reuse selected enforcement, inspection, and store patterns from ProjectKanban.
  - AIOffice does not inherit the old runtime role model as proof of orchestration integrity.

## 2. Problem Statement
ProjectKanban was useful as a proving ground for store patterns, inspection surfaces, and trust concepts, but it was insufficient as proof of orchestration integrity. It could demonstrate structured behavior and richer visibility while still allowing too much ambiguity between narrated workflow and enforced workflow.

In this context, `credible theater` means a system can sound disciplined, produce plausible role labels, emit logs, and narrate staged execution while still lacking code-enforced authority boundaries. A workflow can look organized and still fail the integrity test if the enforcement surface is soft, bypassable, or dependent on prompt compliance.

Authority placement is the core issue because the component that can mutate canonical state decides what is real. If an untrusted model, a prompt-defined role, or an unconstrained executor can directly shape workflow truth, then the system has theater instead of control. AIOffice exists to place authority in sanctioned code paths and make every other component subordinate to that control plane.

## 3. Core Doctrine
- LLMs are untrusted.
  Treat model output as proposal material, not workflow truth.
- control must be enforced in code, not prompts.
  Prompts may describe policy; they do not enforce it.
- fail-closed > fail-open.
  If stage evidence, packet integrity, or authority checks are missing, the system stops.
- internal logs are claims.
  Internal traces are useful, but they are not proof by themselves.
- external/provider signals are proof.
  Provider-facing or other external system signals are the first proof surface for execution claims.
- reconciliation is trust.
  Trust is established only after claims and proof are reconciled.
- role labels are not evidence.
  Naming something `Architect`, `Reviewer`, or `Executor` does not prove stage separation.
- separate stages require separate artifacts, traces, and handoffs.
  A stage boundary is only real if it leaves distinct outputs and transfer records.
- final output without stage artifacts is workflow failure.
  If the system reaches a final deliverable without the required stage evidence, the run failed even if the deliverable looks useful.
- Codex cannot be the control plane.
  Codex may execute bounded work, but it cannot own workflow state, authority, or acceptance.

## 4. Product Thesis
AIOffice is a thin outer control kernel around untrusted models.

It provides:
- a controlled chat plane for operator interaction
- an executor airlock for bounded artifact production
- a verification and apply gate before canonical state changes
- an operator workspace centered on inspection, control, and traceable handoff

The product thesis is not that models become trustworthy. The thesis is that useful model work can be contained inside a stronger outer system that defines packet boundaries, evaluates evidence, and decides what becomes real.

## 5. Non-Goals
AIOffice is not:
- a free-form multi-agent theater
- a prompt-only office simulation
- a UI-first rebuild detached from enforcement
- a direct-write Codex workflow
- a blanket rewrite of ProjectKanban
- proof of separate executors merely because role names exist
- a system where chat narration can substitute for canonical stage artifacts
- a license to weaken fail-closed behavior for convenience

## 6. Scope of the First Implementation Wave
The first implementation wave is intentionally narrow. It focuses on:
- the project shell
- sanctioned project registration
- founding governance artifacts
- workflow and stage contract design
- control-kernel protocol definition
- a manual packet-out / bundle-back airlock
- the first orchestration-integrity slice through architect

This wave is about proving control placement and stage separation, not scaling execution lanes or building presentation-heavy surfaces.

## 7. Reuse Strategy
### Keep as donors
- authority enforcement patterns
- canonical root and authoritative workspace rules
- deterministic registration and store patterns
- trust, proof, and reconciliation concepts

### Adapt
- board and task conventions
- inspection and read-model patterns
- milestone framing and governance artifact organization

### Do not inherit
- the old runtime role architecture as proof of orchestration
- prompt-defined role separation as a control guarantee
- any assumption that narrated multi-role behavior is equivalent to enforced workflow integrity

Reuse is selective. A donor pattern is acceptable only if it strengthens code-enforced control and survives audit under AIOffice doctrine.

## 8. Authority Model
Power order in AIOffice:
1. operator gives direction and approval
2. control kernel owns workflow state, acceptance, and canonical transitions
3. reasoning model can propose, question, analyze, and review
4. Codex can execute bounded packets only
5. only sanctioned code paths may change canonical state

Implications:
- chat may suggest a next step, but the control kernel decides whether the workflow may advance
- executors do not self-authorize stage completion
- canonical state changes require sanctioned code, not direct model action

## 9. Success Definition
Near-term AIOffice success means:
- a bounded executor model exists
- a packet-out / bundle-back flow exists
- invalid bundles can be rejected
- workflow state is inspectable
- the golden task can stop at architect with distinct artifacts
- later stages remain blocked until required artifacts and handoffs exist

The first success bar is integrity, not throughput. AIOffice succeeds early if it can prove controlled stopping, controlled handoff, and controlled rejection.

## 10. Known Constraints And Risks
- the current canonical task schema cannot yet preserve all desired durable AIO fields such as `dependencies`
- donor reuse must remain selective or AIOffice will inherit ambiguity instead of discipline
- strong narration pressure from LLMs remains a design risk because convincing language can mask weak enforcement
- proof standards must stay higher than implementation convenience
- inspection surfaces are only as trustworthy as the sanctioned code that feeds them
- if Codex or any other executor gains direct canonical write power outside sanctioned paths, the architecture regresses immediately

## 11. Immediate Next Milestones
- `M1 - AIOffice Founding And Governance Reset`
  Ratify the founding charter, donor policy, workspace boundaries, and core governance set.
- `M2 - Workflow Contract And Stage Separation`
  Define the workflow contract, stage artifacts, traces, and handoff requirements.
- `M3 - Control Kernel And Airlock Baseline`
  Establish the control-kernel protocol and manual packet-out / bundle-back airlock.
- `M4 - First Orchestration Integrity Proof Slice`
  Prove the first bounded architect slice with distinct artifacts, inspectable workflow state, and fail-closed stage blocking.
