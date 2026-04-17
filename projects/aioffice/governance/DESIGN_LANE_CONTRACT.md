# Design Lane Contract

## 1. Purpose
- Define the narrow constitutional contract for the first resumed post-`architect` workflow-breadth lane.
- Resume design-lane work now because:
  - `M15 - Design Lane Operationalization` is the ratified next conservative slice
  - `M14` narrowed the repo publication and verification discipline gap that previously outranked breadth
  - design-lane operationalization was deferred earlier, not canceled, and is now being resumed deliberately
- Keep this slice conservative:
  - define the design-lane boundary before any sanctioned design-path implementation exists
  - define explicit inputs, outputs, handoffs, and blocked conditions
  - do not claim that later-stage workflow is already proven
- This contract does not imply workflow proof beyond `architect`.
  - it defines the lane constitutionally
  - it does not prove live design-stage execution, design-stage acceptance, or downstream implementation truth

## 2. Current Committed Reality This Contract Must Fit
- `M15` is active as `Design Lane Operationalization`.
- Current live workflow proof still stops at `architect`.
- Current readiness remains `ready only for narrow supervised bounded operation`.
- Repo publication and verification discipline is now explicit in committed governance, but helper or hook outputs remain subordinate to GitHub-visible review truth and accepted governance surfaces.
- Design-lane breadth was previously deferred and is now being resumed only because the narrower publication and verification discipline slice has closed from committed evidence.
- The current design-lane task is governance-definition only.
  - no sanctioned design-artifact path exists yet in code
  - no design-lane rehearsal has been executed yet
  - no downstream stage proof is authorized by this artifact

## 3. Lane Definition
- The design lane exists to translate accepted architect-stage direction into implementation-ready design or content-planning artifacts without collapsing structure, approval, and execution into one step.
- The design lane is for:
  - shaping accepted architecture into reviewable design artifacts
  - making implementation shape explicit enough for later bounded execution planning
  - surfacing open questions, assumptions, blockers, and handoff boundaries before implementation begins
- The design lane may produce:
  - design plan artifacts
  - structured design notes
  - explicit assumptions, blockers, or open-question lists attached to the design work
  - bounded proposal surfaces for later review
- The design lane is not allowed to claim:
  - that design is already a live proven workflow stage
  - that downstream implementation is authorized automatically
  - that a design artifact is accepted merely because it exists
  - that a design artifact changes milestone truth, readiness posture, workflow proof, or product law on its own

## 4. Allowed Inputs To The Design Lane
- Allowed design-lane inputs are explicit and bounded:
  - accepted architect-stage inputs:
    - the durable architect artifact or equivalent accepted architecture decision surface
    - explicit architect-stage constraints, tradeoffs, and declared downstream implications
  - sanctioned governance inputs:
    - `projects/aioffice/governance/STAGE_GOVERNANCE.md`
    - `projects/aioffice/governance/WORKFLOW_VISION.md`
    - `projects/aioffice/governance/PROJECT.md`
    - `projects/aioffice/governance/PRODUCT_CHANGE_GOVERNANCE.md` where protected-surface or approval-law boundaries matter
    - `projects/aioffice/governance/REPO_MILESTONE_LOOP_DISCIPLINE.md` where publication and verification discipline matters
  - authoritative planning inputs:
    - `projects/aioffice/execution/KANBAN.md`
    - `projects/aioffice/governance/ACTIVE_STATE.md`
    - `projects/aioffice/governance/DECISION_LOG.md`
  - explicit upstream assumptions, open questions, blockers, or handoffs when they are preserved in durable artifacts rather than inferred from narration
- Allowed-input rule:
  - if the design lane cannot identify its accepted architect basis and governing planning context, it must fail closed rather than invent upstream truth

## 5. Forbidden Or Non-Authoritative Inputs
- The following are forbidden as authority inputs to the design lane:
  - freeform narration treated as accepted truth by itself
  - unstaged or otherwise unpublished local draft state treated as accepted repo truth
  - non-ratified milestone claims
  - implied downstream approval
  - silent carry-forward of ambiguous context
  - helper or hook output treated as a peer authority surface
  - chat memory or summary text that cannot identify its durable upstream artifact basis
- The following are non-authoritative even when they may assist interpretation:
  - local scratch notes
  - draft design ideas not yet preserved in sanctioned artifact form
  - derived summaries or projections that do not outrank governance, planning, architect artifacts, code, or tests
- Forbidden-input rule:
  - if the input basis is ambiguous, conflicting, or unsupported, the design lane is blocked rather than allowed to proceed by convenience

## 6. Allowed Outputs
- Allowed design-lane outputs are narrow and reviewable:
  - one or more durable design artifact files
  - structured design notes that make the implementation shape explicit
  - explicit open questions, assumptions, blockers, and handoff notes attached to the design output
  - reviewable proposal surfaces that remain subordinate to governance and approval law
- Required properties of an allowed design-lane output:
  - it identifies the accepted architect-stage basis it is derived from
  - it states any explicit assumptions or blockers rather than hiding them
  - it stays bounded to the current milestone and task scope
  - it is reviewable without relying on chat narration alone
- A design-lane output may not:
  - silently mutate accepted truth surfaces
  - claim implemented behavior
  - claim test coverage or runtime proof
  - claim downstream acceptance or publish-ready status

## 7. Approval And Handoff Boundary
- A design-lane output counts as a design-lane artifact only when:
  - it exists in durable form
  - it identifies its accepted architect input basis
  - its assumptions, blockers, and open issues are explicit
  - its intended downstream handoff boundary is explicit
- A design-lane artifact does not count as:
  - approval
  - downstream implementation authorization
  - QA evidence
  - publish authorization
  - workflow proof beyond `architect`
- Before any later downstream implementation path may use a design artifact, the following must exist:
  - the design artifact itself in durable form
  - an explicit review or approval path appropriate to the later slice
  - any later sanctioned implementation path defined by its own governance and code surfaces
- This contract does not authorize downstream stage proof.
  - it defines what a design-lane handoff must preserve
  - it does not claim that the next stage is live or satisfied

## 8. Source-Of-Truth Precedence
- Source-of-truth precedence for the design lane is fail-closed and concern-specific:
  - governance and planning surfaces are authoritative for accepted milestone, task, posture, review law, and approval boundaries
  - accepted architect-stage artifacts are authoritative for the structural intent entering the design lane
  - committed review artifacts are authoritative for what has actually been rehearsed or proved
  - code and tests are authoritative for implemented behavior and verification reality whenever a design artifact is later compared against implementation
  - design artifacts are authoritative only for the design proposal content they explicitly carry; they do not outrank governance, planning, architect truth, review truth, code, or tests
  - local draft state is non-authoritative implementation workspace state only
- If governance or planning surfaces, architect inputs, design artifacts, review artifacts, code, tests, or local draft state disagree, the lane must fail closed rather than choose a convenient interpretation.

## 9. Explicit Non-Claims
- This contract does not upgrade readiness.
- This contract does not widen live workflow proof beyond `architect`.
- This contract does not claim that design is already a live proven lane.
- This contract does not authorize automatic downstream implementation.
- This contract does not authorize auto-approval.
- This contract does not create a second truth surface.
- This contract does not authorize broad workflow expansion, broad automation rollout, or `M16`.
