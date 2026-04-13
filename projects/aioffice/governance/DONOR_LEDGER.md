# AIOffice Donor Ledger

Ledger status:
- drafted under AIO-004 for operator review
- governing donor audit draft for AIOffice
- advisory until implemented through sanctioned paths

## 1. Purpose And Audit Rule
ProjectKanban is a donor system, not the architectural authority for AIOffice. The current repo contains useful enforced patterns, useful inspection ideas, and also several failure modes that AIOffice must reject.

Donor reuse must follow AIOffice doctrine, artifact law, and workspace-boundary rules. A donor item is acceptable only if it strengthens code-enforced control, preserves artifact truth, and survives fail-closed review.

Reuse decisions in this ledger are provisional until they are implemented through controlled paths. This document does not approve copying code, moving files, adapting runtime behavior, or promoting any donor surface into canonical AIOffice truth by itself.

## 2. Classification Method
Each donor decision is evaluated against these dimensions:
- `donor_item`: the concrete concept, pattern, or subsystem being evaluated
- `source_path_or_area`: the exact file path or source area inspected in the current repo
- `donor_type`: governance rule, store helper, runtime pattern, UI shell, test evidence, or similar
- `reuse_mode`: `keep`, `adapt`, `do_not_inherit`, or `defer`
- `rationale`: why the item should or should not shape AIOffice
- `aioffice_target`: where the idea would land in AIOffice, or `none`
- `risks_constraints`: what must stay visible if the item is later implemented
- `provenance_note`: how this decision is tied back to the inspected source

Reuse modes mean:
- `keep`: preserve the concept or pattern with minimal conceptual change
- `adapt`: reuse selectively under new AIOffice ownership and constraints
- `do_not_inherit`: explicitly reject carrying it forward as architecture truth
- `defer`: not now; revisit only if later milestones justify it

Inspected source set for this audit:
- `workspace_root.py`
- `sessions/store.py`
- `sessions/governed_external_observability.py`
- `governance/ARCHITECTURE.md`
- `governance/AGENT_TIERS.md`
- `governance/CONTROL_INVARIANTS.md`
- `scripts/cli.py`
- `scripts/operator_api.py`
- `scripts/control_room_api.py`
- `scripts/sdk_runtime_bridge.py`
- `skills/tools.py`
- `agents/api_router.py`
- `agents/orchestrator.py`
- `agents/pm.py`
- `agents/sdk_runtime.py`
- `projects/program-kanban/`
- `projects/tactics-game/`
- `tests/test_store.py`
- `tests/test_project_registration.py`
- `tests/test_workspace_root.py`
- `tests/test_api_router.py`
- `tests/test_pm_flow.py`
- `tests/test_orchestrator.py`
- `tests/test_llm_wrapper.py`
- `tests/test_sdk_runtime.py`

## 3. Keep As Donors
These donor items should survive into AIOffice with minimal conceptual change.

### Authoritative root enforcement
- source: `workspace_root.py`, `tests/test_workspace_root.py`
- keep reason:
  - AIOffice needs explicit authoritative-root checks and known-duplicate rejection.
  - This is directly aligned with fail-closed workspace containment.

### Sanctioned, idempotent project registration
- source: `sessions/store.py` `SessionStore.ensure_project_registered(...)`, `scripts/cli.py` `projects ensure`, `tests/test_project_registration.py`
- keep reason:
  - AIOffice needs a sanctioned registration path instead of ad hoc database mutation.
  - The current pattern is deterministic, idempotent, and tested for no unrelated KANBAN rewrite side effects.

### Canonical operational state discipline
- source: `sessions/store.py`, rendered boards such as `projects/tactics-game/execution/KANBAN.md`
- keep reason:
  - Canonical state lives in sanctioned storage, while rendered files remain derived views.
  - This matches AIOffice doctrine that visible output does not outrank controlled state.

### Evidence, trust, and reconciliation model
- source: `sessions/governed_external_observability.py`, `sessions/store.py` `record_governed_external_reconciliation(...)`, `list_governed_external_trust_worklist(...)`
- keep reason:
  - Claim versus proof versus reconciliation is directly usable in AIOffice.
  - This supports the product thesis that proof and reconciliation outrank narration.

### Exact artifact-path discipline
- source: `skills/tools.py` `validate_worker_write_manifest(...)`, `validate_project_artifact_path(...)`, `validate_tool_access_from_manifest(...)`, `enforce_command_policy(...)`, `write_project_artifact(...)`, `tests/test_pm_flow.py`, `tests/test_store.py`
- keep reason:
  - AIOffice needs exact-path write boundaries for bounded execution.
  - The current pattern already treats allowed paths and allowed tools as enforceable constraints rather than advice.

### Deterministic inspection and read-model composition
- source: `sessions/store.py` `get_run_evidence(...)`, `scripts/operator_api.py`, `scripts/control_room_api.py`
- keep reason:
  - AIOffice needs sanctioned read paths that expose inspectable workflow truth without relying on chat memory.
  - The current pattern composes evidence from canonical state rather than from role narration alone.

## 4. Adapt For AIOffice
These donor items are useful, but only under new AIOffice ownership and stricter constraints.

### Board and task conventions
- source: `projects/program-kanban/governance/M1_BASIC_OPERATION_SPEC_2026-03-21.md`, `tests/test_store.py`
- adapt reason:
  - The lifecycle shape and ready-gate discipline are useful.
  - AIOffice already requires stricter durable fields, dependencies, and artifact law than the donor spec provides.

### CLI and admin helper patterns
- source: `scripts/operator_api.py`, `scripts/control_room_api.py`, `scripts/cli.py`
- adapt reason:
  - Thin wrappers around sanctioned store and orchestration actions are useful.
  - AIOffice should not inherit the old command set or the old runtime assumptions behind those commands.

### Operator inspection and control-room interaction ideas
- source: `projects/program-kanban/governance/M6_TRUST_RESTORE_OPERATOR_SPEED_SPEC_2026-03-24.md`, `projects/program-kanban/app/app.js`, `projects/program-kanban/app/index.html`
- adapt reason:
  - Visible provenance, trust worklists, timelines, density controls, and restore awareness are good operator-facing ideas.
  - AIOffice must treat them as inspection references only until a control kernel exists underneath them.

### Artifact and trace presentation patterns
- source: `projects/program-kanban/app/app.js`, `projects/program-kanban/artifacts/pk076_final_operator_wall_visibility.md`
- adapt reason:
  - Showing evidence, latest artifacts, and run context in one place is useful.
  - AIOffice should separate presentation from proof and avoid inheriting any UI surface as a truth source.

### Controlled chat plane versus execution plane framing
- source: `governance/ARCHITECTURE.md`
- adapt reason:
  - Separating operator interaction from bounded execution is directionally right.
  - AIOffice must replace `ChatGPT is the control room` with `the control kernel owns authority`.

### Read-only rendered board surfaces
- source: `projects/program-kanban/execution/KANBAN.md`, `projects/tactics-game/execution/KANBAN.md`, `sessions/store.py` `render_kanban(...)`
- adapt reason:
  - AIOffice may later want rendered read-only summaries.
  - Any rendered board must remain secondary to canonical state and stage artifacts.

## 5. Do Not Inherit
These items would recreate the old failure mode if carried forward as architectural truth.

### Runtime role architecture as proof of orchestration
- source: `agents/orchestrator.py`, `agents/pm.py`, `agents/api_router.py`, `governance/AGENT_TIERS.md`
- rejection:
  - AIOffice must not treat orchestrator, PM, specialist, or tier labels as proof that stages are genuinely separate.

### Prompt-only or wrapper-only control assumptions
- source: `governance/CONTROL_INVARIANTS.md`, `tests/test_llm_wrapper.py`
- rejection:
  - Wrapper checks and role/tool restrictions are useful defenses, but they are not sufficient proof of workflow integrity by themselves.
  - AIOffice must place authority in controlled state transitions and artifact gates, not in prompt compliance.

### Narrative stage completion
- source: `agents/pm.py` `execute_request(...)`, `agents/orchestrator.py` `_execute_run(...)`
- rejection:
  - Status updates, summaries, or internal approval flow are not enough to prove a stage is complete.
  - AIOffice requires distinct stage artifacts and handoffs before stage truth can advance.

### One executor chain impersonating separate stages
- source: `agents/orchestrator.py` `_execute_run(...)`, `agents/pm.py` `_run_subtask(...)`, `_review_parent_task(...)`
- rejection:
  - A single runtime chain may coordinate work, but it cannot count as separate stage proof unless distinct artifacts and handoffs exist.

### Direct database mutation outside sanctioned paths
- source: `sessions/studio.db` as canonical state area, plus the repo-wide risk documented by AIOffice bootstrap correction work
- rejection:
  - Manual SQL or direct state mutation bypasses the control path and is therefore not a reusable pattern.

### Imported project briefs as product truth
- source: `projects/program-kanban/governance/PROJECT_BRIEF.md`, `projects/tactics-game/governance/PROJECT_BRIEF.md`
- rejection:
  - These files describe imported project state, legacy roots, and project-specific direction.
  - They are useful provenance documents, but they are not AIOffice architecture inputs.

## 6. Defer
These items may matter later, but they should not shape the first AIOffice implementation wave.

### SDK bridge and specialist runtime paths
- source: `agents/sdk_runtime.py`, `scripts/sdk_runtime_bridge.py`, `tests/test_sdk_runtime.py`
- defer reason:
  - AIOffice first needs a control kernel and bounded executor airlock.
  - SDK specialist lanes would add a second execution model before the first one is proven.

### Batch, background, and lane policy ambitions
- source: `governance/ARCHITECTURE.md`, `agents/api_router.py`, `agents/orchestrator.py`, `agents/pm.py`
- defer reason:
  - Background routing, lane families, and reservation policy are useful later, but they are not needed to prove first-wave orchestration integrity.

### Prompt caching policy direction
- source: `agents/orchestrator.py` tier assignment and route-family logic, `agents/pm.py` subtask planning metadata
- defer reason:
  - Cache policy is an optimization concern.
  - It should not shape the first control-kernel slice.

### Current UI implementation specifics
- source: `projects/program-kanban/app/app.js`, `projects/program-kanban/app/index.html`
- defer reason:
  - Specific browser implementation details, local storage preferences, and wall layout choices are not bootstrap-critical.
  - Only the inspection concepts are relevant now.

### Example and game project assets
- source: `projects/tactics-game/app/`, `projects/tactics-game/governance/`, `projects/tactics-game/execution/KANBAN.md`
- defer reason:
  - These assets prove the framework can host another project, but they do not shape AIOffice governance or first-wave control.

### Milestone-specific artifact writeups with stale external path references
- source: `projects/program-kanban/artifacts/pk076_slice2_registration_path_evidence.md`, `projects/program-kanban/artifacts/pk076_final_operator_wall_visibility.md`
- defer reason:
  - These writeups may contain useful lessons, but they are milestone-specific evidence docs rather than durable contracts.
  - Some embedded absolute paths point at external worktrees and should not become AIOffice authority.

## 7. Donor Ledger Table
| donor_item | source_path_or_area | donor_type | reuse_mode | rationale | aioffice_target_or_none | risks_constraints | provenance_note |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Authoritative workspace root marker and duplicate-root rejection | `workspace_root.py`; `tests/test_workspace_root.py` | authority_enforcement | keep | AIOffice needs hard root checks and explicit rejection of non-authoritative duplicates. | future control-kernel root gate and workspace-boundary enforcement | Must remain fail-closed and path-exact; being inside the repo is not enough. | Live code and tests inspected in the authoritative repo. |
| Idempotent sanctioned project registration | `sessions/store.py` `SessionStore.ensure_project_registered(...)`; `scripts/cli.py` `projects ensure`; `tests/test_project_registration.py` | registration_store_path | keep | This is the smallest deterministic pattern for project registration without ad hoc SQL or unrelated file rewrites. | sanctioned AIOffice project registration path | Current helper registers projects only; it does not solve canonical AIO task import. | Helper and tests inspected directly. |
| Canonical state outranks rendered boards | `sessions/store.py`; `projects/tactics-game/execution/KANBAN.md`; `projects/program-kanban/execution/KANBAN.md` | canonical_state_discipline | keep | AIOffice needs the rule that rendered files are views, not truth. | AIOffice canonical-state doctrine and future derived views | Current task schema still lacks some AIO durable fields such as `dependencies`. | Rendered boards inspected and explicitly declare SQLite as source of truth. |
| Claim/proof/reconciliation trust model | `sessions/governed_external_observability.py`; `sessions/store.py` `record_governed_external_reconciliation(...)`; `list_governed_external_trust_worklist(...)` | trust_model | keep | This model directly supports AIOffice doctrine that internal claims are not enough and reconciliation creates trust. | future verification/apply gate and trust ledger | Provider-specific evidence fields may need generalization beyond current API usage. | Live code inspected; names and states are already explicit. |
| Exact-path write manifest discipline | `skills/tools.py` `validate_worker_write_manifest(...)`, `validate_project_artifact_path(...)`, `validate_tool_access_from_manifest(...)`, `enforce_command_policy(...)`, `write_project_artifact(...)`; `tests/test_pm_flow.py`; `tests/test_store.py` | bounded_write_contract | keep | AIOffice needs exact-path and allowed-tool execution constraints for bounded packets and airlocked outputs. | future packet-out / bundle-back executor contract | Current implementation is tied to `projects/<project>/artifacts/` and worker manifests, so path structure may need narrowing. | Source code and enforcement tests inspected. |
| Deterministic run evidence composition | `sessions/store.py` `get_run_evidence(...)`; `scripts/operator_api.py`; `scripts/control_room_api.py` | inspection_read_model | keep | AIOffice needs sanctioned read paths that compose inspectable truth from canonical state. | future operator inspection API and control-kernel read surfaces | Must not let inspection summaries outrank the underlying artifacts or canonical records. | Source code inspected directly. |
| Board lifecycle and ready-gate baseline | `projects/program-kanban/governance/M1_BASIC_OPERATION_SPEC_2026-03-21.md`; `tests/test_store.py` ready/complete gate tests | governance_spec | adapt | The lifecycle shape is useful, but AIOffice needs stricter durable fields, dependency declaration, and artifact law. | `projects/aioffice/governance/BOARD_RULES.md`; `projects/aioffice/execution/KANBAN.md` | Must not re-import Program Kanban IDs, status semantics, or weaker ready criteria unchanged. | Donor spec and enforcement-oriented tests inspected. |
| Thin admin and operator wrapper pattern | `scripts/operator_api.py`; `scripts/control_room_api.py`; `scripts/cli.py` | admin_interface_pattern | adapt | Narrow wrappers around sanctioned store/control code are useful for later AIOffice operator surfaces. | future AIOffice admin/inspection entrypoints | Current commands assume the old runtime and approval model. | Live scripts inspected. |
| Operator wall trust and restore ideas | `projects/program-kanban/governance/M6_TRUST_RESTORE_OPERATOR_SPEED_SPEC_2026-03-24.md` | operator_experience_spec | adapt | The ideas around restore flow, provenance visibility, timelines, and health strips are useful inspection goals. | future AIOffice operator workspace inspection features | These are UI-facing goals only; they do not prove control without stronger stage artifacts underneath. | Governance spec inspected directly. |
| Current operator wall shell concepts | `projects/program-kanban/app/app.js`; `projects/program-kanban/app/index.html` | ui_reference | adapt | Board tabs, project chips, run evidence selection, and provenance badges are useful as design references. | future operator workspace design references only | The current shell is Program-Kanban-specific and must not become AIOffice product truth. | Current app shell files inspected directly. |
| Controlled chat plane versus execution plane framing | `governance/ARCHITECTURE.md` | architecture_direction | adapt | Separating operator interaction from deterministic control and bounded execution is directionally useful. | future `WORKFLOW_VISION.md` and control-kernel protocol | The donor phrasing still centers the old control-room/runtime split and must be rewritten under AIOffice doctrine. | Governance doc inspected directly. |
| Read-only rendered board presentation | `sessions/store.py` `render_kanban(...)`; rendered boards under `projects/program-kanban/execution/` and `projects/tactics-game/execution/` | derived_view_pattern | adapt | AIOffice may later want rendered summaries derived from canonical state. | future read-only exports or review snapshots | Derived views must never outrank canonical state or stage artifacts. | Renderer path and rendered examples inspected. |
| Runtime role architecture as proof of orchestration | `agents/orchestrator.py`; `agents/pm.py`; `agents/api_router.py`; `governance/AGENT_TIERS.md` | runtime_role_model | do_not_inherit | Role names, tiers, and router lanes are not valid proof that stages are separate. | none | Inheriting this as truth would recreate credible theater. | Live runtime files and governance doc inspected. |
| Prompt-only or wrapper-only control assumptions | `governance/CONTROL_INVARIANTS.md`; `tests/test_llm_wrapper.py` | prompt_governance_pattern | do_not_inherit | Prompt and wrapper restrictions are useful controls, but they are not sufficient architectural proof for AIOffice. | none | AIOffice requires code-enforced workflow state and artifact sufficiency, not prompt compliance alone. | Governance doc and test evidence inspected. |
| Narrative stage completion via status and summary | `agents/pm.py` `execute_request(...)`; `agents/orchestrator.py` `_execute_run(...)` | completion_semantics | do_not_inherit | Status progression and summaries are not enough to prove stage completion. | none | AIOffice requires separate stage artifacts, traces, and handoffs before acceptance. | Live runtime files inspected. |
| One executor chain standing in for separate stages | `agents/orchestrator.py` `_execute_run(...)`; `agents/pm.py` `_run_subtask(...)`, `_review_parent_task(...)` | stage_separation_pattern | do_not_inherit | A single controlled chain may coordinate work, but it cannot count as multi-stage proof without distinct artifacts and handoffs. | none | Reusing this as stage proof would collapse architect, build, QA, and publish boundaries into theater. | Live runtime files inspected. |
| Direct canonical-state mutation outside sanctioned paths | `sessions/studio.db` as canonical state area; repo-wide ad hoc mutation risk | state_mutation_pattern | do_not_inherit | Manual SQL or direct database editing bypasses the control path and is therefore not a donor pattern. | none | Convenience writes would undermine fail-closed state authority immediately. | Canonical state location and prior correction context are known in this repo. |
| Imported project briefs as product truth | `projects/program-kanban/governance/PROJECT_BRIEF.md`; `projects/tactics-game/governance/PROJECT_BRIEF.md` | imported_project_context | do_not_inherit | These briefs are provenance and project-local context, not AIOffice architecture inputs. | none | They include imported legacy paths and project-specific assumptions. | Files inspected directly. |
| SDK specialist runtime and bridge | `agents/sdk_runtime.py`; `scripts/sdk_runtime_bridge.py`; `tests/test_sdk_runtime.py` | alternate_runtime_path | defer | AIOffice first needs a proven bounded executor and control kernel before a second runtime path is considered. | future specialist integration only if later justified | Adding SDK lanes early would increase complexity before first-wave proof exists. | Code and tests inspected directly. |
| Background, batch, and reservation lane policy | `agents/api_router.py`; `agents/orchestrator.py`; `agents/pm.py`; `governance/AGENT_TIERS.md` | scale_out_policy | defer | Useful later for throughput and cost control, but not required for first-wave orchestration integrity. | none in the first wave | Premature lane policy would distract from proving bounded stage control. | Runtime files and tier doc inspected. |
| Prompt caching policy direction | `agents/orchestrator.py` tier assignment and route metadata; `agents/pm.py` subtask planning metadata | optimization_policy | defer | Caching is an optimization problem, not a first-wave control proof requirement. | none in the first wave | It should not shape workflow truth or artifact law. | Source areas inspected directly. |
| Exact UI implementation specifics | `projects/program-kanban/app/app.js`; `projects/program-kanban/app/index.html` | current_ui_implementation | defer | The shell concepts are useful, but the concrete implementation details should not shape the first AIOffice wave. | none in the first wave | UI-first drift would weaken enforcement-first priorities. | Same paths inspected for interaction ideas. |
| Example and game-project assets | `projects/tactics-game/app/`; `projects/tactics-game/governance/`; `projects/tactics-game/execution/KANBAN.md` | example_project_surface | defer | These paths prove multi-project hosting, but they do not define AIOffice governance or control behavior. | none in the first wave | Game-specific content could distort AIOffice scope if treated as more than examples. | Current project paths inspected directly. |
| Milestone-specific artifact writeups with stale external path references | `projects/program-kanban/artifacts/pk076_final_operator_wall_visibility.md`; `projects/program-kanban/artifacts/pk076_slice2_registration_path_evidence.md` | artifact_writeup | defer | These artifacts may contain useful observations, but they are slice-specific evidence docs rather than durable contracts. | none in the first wave | Some embedded absolute paths point at external worktrees and should not become authority. | Files inspected directly in the authoritative repo. |

## 8. Recommended First-Wave Imports
These are the first donor items AIOffice should reuse next, in order, through controlled implementation only.

1. `workspace_root.py`
Reason: authoritative-root enforcement and duplicate-root rejection are already aligned with AIOffice containment doctrine.

2. `sessions/store.py` `SessionStore.ensure_project_registered(...)` and `scripts/cli.py` `projects ensure`
Reason: the sanctioned registration path is already deterministic, idempotent, and tested against unintended KANBAN rewrites.

3. `sessions/governed_external_observability.py` plus `sessions/store.py` trust/reconciliation helpers
Reason: AIOffice needs claim, proof, and reconciliation language early so packet-out / bundle-back acceptance does not rely on narration.

4. `skills/tools.py` exact-path manifest discipline
Reason: bounded executor output needs a concrete write-boundary model for future packet-out and controlled apply flows.

5. `projects/program-kanban/governance/M1_BASIC_OPERATION_SPEC_2026-03-21.md`
Reason: it is the clearest donor reference for milestone-linked board flow and ready-gate structure, even though AIOffice must strengthen it.

6. `sessions/store.py` `get_run_evidence(...)` and thin inspection wrappers in `scripts/operator_api.py`
Reason: AIOffice will need inspectable workflow truth before it needs richer presentation surfaces.

## 9. Guardrails And Open Risks
- Code and prose can drift. A donor spec is not proof that the current runtime still behaves exactly that way.
- Some inspected project docs and artifact writeups embed non-authoritative or external absolute paths. They are provenance clues, not authority.
- The current runtime can look more mature than its proof standard actually is. Visible roles, approvals, or summaries do not equal stage integrity.
- Runtime role surfaces should not be mistaken for proof of separate stages.
- The current canonical task schema still cannot safely preserve every AIOffice durable field, especially `dependencies`.
- Read models and rendered surfaces are useful only if they stay subordinate to canonical state and required artifacts.
- Donor decisions here remain provisional until implemented through sanctioned AIOffice code paths and reviewed against current doctrine.

## 10. Minimal Examples
### Good `keep` decision
- donor item: authoritative root enforcement
- source: `workspace_root.py`
- reason: it already encodes fail-closed authority checks that match AIOffice workspace doctrine

### Good `adapt` decision
- donor item: board lifecycle baseline
- source: `projects/program-kanban/governance/M1_BASIC_OPERATION_SPEC_2026-03-21.md`
- reason: the lifecycle shape is useful, but AIOffice must strengthen it with dependencies, artifact law, and stricter ready gating

### Good `do_not_inherit` decision
- donor item: runtime role architecture as proof
- source: `agents/orchestrator.py`, `agents/pm.py`, `agents/api_router.py`
- reason: carrying these role surfaces forward as architectural proof would recreate the same credible-theater failure mode AIOffice is meant to prevent

### Good `defer` decision
- donor item: SDK bridge runtime
- source: `agents/sdk_runtime.py`, `scripts/sdk_runtime_bridge.py`
- reason: it may matter later, but it would add a second execution model before the first bounded executor path is proven
