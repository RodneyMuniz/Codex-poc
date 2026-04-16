# Product Change Governance

## 1. Purpose
- Define the narrow governance boundary for which AIOffice product-change and self-modification actions are admin-only.
- Keep admin-only product/self-change approval distinct from ordinary persisted execution-bundle decisions.
- Provide a concrete boundary that later implementation, UI constraints, and recovery work can follow without widening workflow proof or changing current readiness.

## 2. Current Committed Reality This Boundary Must Fit
- `M1` through `M11` are complete and `M12` is the active milestone.
- Current readiness remains `ready only for narrow supervised bounded operation`.
- AIOffice is not ready for a bounded supervised semi-autonomous cycle.
- Current live workflow proof still stops at `architect`.
- The currently real operator decision surfaces are narrow and bundle-scoped:
  - `scripts/operator_api.py control-kernel-details`
  - `scripts/operator_api.py bundle-decision`
  - `sessions/store.py execute_apply_promotion_decision(...)`
- `OPERATOR_DECISION_SURFACE.md` and `OPERATOR_DECISION_INPUT_CONTRACT.md` define explicit, fail-closed approval of persisted execution bundles with explicit destination mappings.
- No committed implementation currently provides:
  - an admin identity system
  - a separate admin-only mutation lane in code
  - product/self-change enforcement beyond governance and review discipline
- This artifact therefore defines governance law and approval boundaries only. It does not claim that admin-only enforcement already exists in runtime code.

## 3. Why Ordinary Execution-Bundle Approval Is Not Enough For Product/Self-Change
- Ordinary execution-bundle approval is designed for bounded artifact disposition within already-sanctioned product behavior.
- The current `bundle-decision` surface proves explicit approval inputs, exact destination mapping, persisted-state inspection, and fail-closed path enforcement.
- It does not classify whether a proposed artifact changes AIOffice's own governance, control law, mutation authority, milestone truth surfaces, or self-modifying behavior.
- Product/self-change therefore cannot lawfully ride the same approval lane as routine execution outputs, because:
  - the blast radius is wider than one accepted bundle disposition
  - the change may alter future authority boundaries or truth surfaces
  - the change may affect recovery, review, and audit requirements beyond a single bundle write

## 4. Definition Of Product-Change Scope
- Product-change scope means a proposed change that modifies AIOffice's own accepted product behavior, governance law, control surfaces, or authoritative state surfaces.
- Product-change scope includes changes to:
  - governance and policy artifacts that define accepted posture, stage law, or review boundaries
  - control-kernel rules, authority boundaries, or gate semantics
  - sanctioned mutation paths or approval-routing rules
  - milestone, task, and accepted-state truth surfaces
  - the product's own core operator-facing guardrails or constraints
- A proposed change is in product-change scope even if the artifact is documentation-only, if that documentation changes accepted control law or accepted operational truth.

## 5. Definition Of Self-Modification Scope
- Self-modification scope is the subset of product-change scope where AIOffice proposes to change the code, rules, or accepted state that govern AIOffice itself.
- Self-modification scope includes proposed changes to:
  - `scripts/operator_api.py` when the change alters AIOffice control or approval behavior
  - `sessions/store.py` when the change alters sanctioned mutation law, authority checks, or accepted state handling for AIOffice
  - governance artifacts that redefine how AIOffice may change itself
  - milestone/task/state surfaces that alter what AIOffice treats as accepted truth about its own roadmap or readiness
- Self-modification does not mean every generated file in the repo. It means changes that alter the product's own governing behavior, guardrails, or accepted truth surfaces.

## 6. Admin-Only Action Classes
- The following action classes are admin-only and must not be treated as ordinary bundle approval:
  - changes to governance or policy files that redefine readiness, workflow proof, authority boundaries, or review law
  - changes to control-kernel rules, gate rules, approval requirements, or operator authority boundaries
  - changes to sanctioned mutation paths, bundle-decision semantics, or canonical-state mutation law
  - changes to milestone/task/state truth surfaces that alter accepted roadmap or active-state truth
  - changes to AIOffice core guardrails, fail-closed rules, or product self-change boundaries
  - changes that enable or authorize broader writable surfaces, UI authority, art-pipeline authority, later-stage workflow authority, or self-modifying behavior
- For the current repo state, admin-only surfaces include at least:
  - `projects/aioffice/governance/*.md` when the file changes accepted product law or accepted posture
  - `projects/aioffice/execution/KANBAN.md`
  - `projects/aioffice/governance/ACTIVE_STATE.md`
  - control-path code such as `scripts/operator_api.py` and `sessions/store.py` when AIOffice control behavior is changed

## 7. Non-Admin Action Classes That Remain Ordinary Execution Decisions
- The following remain ordinary persisted execution-bundle decisions when they stay inside already-sanctioned behavior:
  - approving or promoting a pending-review execution bundle that writes bounded output artifacts to explicitly mapped sanctioned destinations
  - accepting content or delivery artifacts that do not change AIOffice control law, readiness claims, milestone truth, or operator authority boundaries
  - routine artifact disposition under the existing `bundle-decision` surface where explicit destination mappings and current store validations already apply
- Ordinary execution decisions do not become admin-only solely because they are important or user-visible. They become admin-only when they change AIOffice's own governing behavior or authoritative truth surfaces.

## 8. Required Proposal Path For Admin-Only Changes
- Admin-only changes require an explicit proposal path before any approval decision is lawful.
- The minimum proposal package is:
  - a named governance task or review artifact defining the proposed change
  - a clear statement of why the change is product-change or self-modification scope
  - the exact files or control surfaces affected
  - the intended effect on authority, guardrails, or accepted truth
  - explicit non-claims so the proposal does not silently widen readiness or workflow proof
  - explicit audit evidence showing the current committed reality the proposal is changing
- Until a dedicated admin implementation exists, that proposal path remains governance-first and manual. A proposal is not lawfully created by ordinary bundle approval alone.

## 9. Required Approval Path And Authority Boundary
- Admin-only changes require explicit administrator approval from the operator authority acting in an admin capacity, not merely in the ordinary execution-bundle approval lane.
- Ordinary `bundle-decision` approval is insufficient for admin-only changes, even if the bundle is `pending_review` and the destination mapping is explicit.
- Required approval boundary:
  - ordinary operator approval may approve bounded execution outputs inside existing product law
  - admin approval is required for changes that alter product law, accepted truth surfaces, or AIOffice's own governing behavior
- Until a dedicated admin-only control surface exists, admin-only changes remain governed by explicit review artifacts, explicit operator-admin approval, and GitHub-visible committed evidence rather than by the ordinary `bundle-decision` command.

## 10. Audit And Evidence Requirements
- Every admin-only change must leave GitHub-visible evidence that includes:
  - the proposal artifact
  - the accepted rationale for why the change is admin-only
  - the exact files or control surfaces changed
  - the exact branch, commit, and review anchor used
  - explicit statement of what remains unproven after the change
- Admin-only changes must preserve a clear distinction between:
  - current committed reality before the change
  - proposed product/self-change boundary
  - accepted result after the change
- Audit evidence must be sufficient for a reviewer to determine whether the change altered product law rather than merely approving a routine execution output.

## 11. Fail-Closed Rules
- If a proposed change falls into an admin-only action class and no explicit admin proposal artifact exists, the change fails closed.
- If a proposed change falls into an admin-only action class and approval is attempted only through the ordinary execution-bundle lane, the change fails closed.
- If the proposal does not identify the affected truth surfaces, authority boundaries, or control surfaces, the change fails closed.
- If the change would alter readiness, workflow proof, UI authority, art-pipeline authority, later-stage workflow claims, or self-modifying scope without explicit governance review, the change fails closed.
- If classification is ambiguous between ordinary execution output and product/self-change, it is treated as admin-only until explicitly resolved.
- No convenience fallback is allowed from admin-only product/self-change into the ordinary `bundle-decision` lane.

## 12. Exact Out-Of-Scope Boundaries
- This artifact does not implement admin-only enforcement in code.
- This artifact does not create a new UI, admin console, or writable client surface.
- This artifact does not change `bundle-decision` semantics for ordinary bounded execution outputs.
- This artifact does not authorize later-stage workflow, concurrency safety, real multi-agent maturity, semi-autonomous operation, or UAT readiness.
- This artifact does not define recovery, snapshot, restore, or rollback mechanics in full.
- This artifact does not define the full feature-isolation or code-review contract for future Codex-delivered changes.

## 13. Relationship To Future Recovery/Rollback Work In AIO-051
- `AIO-051` should define the recovery contract that admin-only product/self-change work must eventually obey.
- This artifact establishes which changes are sensitive enough to require that recovery discipline.
- It does not assume recovery discipline already exists; it only states that admin-only product/self-change must remain separate from ordinary bundle decisions before broader writable surfaces are considered.

## 14. Relationship To Future Change-Isolation/Code-Review Work In AIO-052
- `AIO-052` should define how future Codex-delivered changes touching shared or mixed control surfaces are isolated, reviewed, and kept maintainable.
- This artifact establishes which changes require that stronger review lane because they alter product law or AIOffice self-governance.
- It does not yet define file-level isolation or review mechanics; it defines the authority boundary those mechanics must protect.
