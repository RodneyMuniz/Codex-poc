# M13 Structural Truth Rehearsal

## 1. Rehearsal Target
- reviewed target: `scripts/operator_api.py`
- reviewed command surface: `bundle-decision` at `scripts/operator_api.py:1096-1102`
- reviewed execution path:
  - `_execute_control_kernel_bundle_decision(...)` at `scripts/operator_api.py:330-389`
  - CLI dispatch branch at `scripts/operator_api.py:1183-1193`
- why this target was selected:
  - `command:bundle-decision` already exists in the committed structural-truth baseline as a `command_or_function` node sourced from `scripts/operator_api.py:1096`
  - the committed baseline explicitly classifies it as a `protected operator/control surface`
  - the committed baseline explicitly surfaces `unresolved:test_link:command:bundle-decision`
  - this makes the target suitable for one bounded review of impact, linked tests, missing coverage, and protected-surface classification without widening scope

## 2. Structural Truth Inputs Used
- committed structural-truth artifact:
  - `projects/aioffice/artifacts/M13_STRUCTURAL_TRUTH_BASELINE.json`
- structural-truth generator and bounded-input contract:
  - `scripts/generate_structural_truth.py:15-28`
  - `scripts/generate_structural_truth.py:222-223`
  - `scripts/generate_structural_truth.py:515-563`
- authoritative task and posture surfaces:
  - `projects/aioffice/execution/KANBAN.md:1468-1484`
  - `projects/aioffice/governance/ACTIVE_STATE.md:19-27`
  - `projects/aioffice/governance/ACTIVE_STATE.md:86-88`
- ratification and rebaseline surfaces:
  - `projects/aioffice/governance/DECISION_LOG.md:125-136`
  - `projects/aioffice/governance/M13_SCOPE_REBASELINE.md:8-18`
  - `projects/aioffice/governance/M13_SCOPE_REBASELINE.md:27-46`
- structural-truth contract and protected-surface law:
  - `projects/aioffice/governance/STRUCTURAL_TRUTH_LAYER_CONTRACT.md:16-27`
  - `projects/aioffice/governance/STRUCTURAL_TRUTH_LAYER_CONTRACT.md:29-86`
  - `projects/aioffice/governance/STRUCTURAL_TRUTH_LAYER_CONTRACT.md:88-110`
  - `projects/aioffice/governance/PRODUCT_CHANGE_GOVERNANCE.md:68-74`
  - `projects/aioffice/governance/PRODUCT_CHANGE_GOVERNANCE.md:156-164`
- target implementation sources:
  - `scripts/operator_api.py:330-389`
  - `scripts/operator_api.py:1089-1102`
  - `scripts/operator_api.py:1183-1193`
  - `sessions/store.py:3073-3265`
- linked and nearby test surfaces:
  - `tests/test_generate_structural_truth.py:80-108`
  - `tests/test_control_kernel_store.py:796-867`
- manual review surface outside the committed bounded input set:
  - `tests/test_operator_api.py:743-829`
  - `tests/test_operator_api.py:836-1058`

## 3. Impact Assessment
- direct structural-truth links from the committed baseline for `command:bundle-decision`:
  - `defined_in -> file:scripts/operator_api.py`
  - `classifies <- protected_surface_class:protected_operator_control_surfaces`
- adjacent structural-truth context grounded in the same committed baseline:
  - `file:scripts/operator_api.py` is also classified as `protected_control_path_code_surfaces`
  - `protected_surface_class:protected_operator_control_surfaces` is touched by `task:AIO-065`
  - `task:AIO-066` depends on `task:AIO-065`
  - `task:AIO-066` is ratified by `decision:AIO-D-014`
  - `decision:AIO-D-014` records the `M13` rebaseline to `Structural Truth Layer Baseline`
- impact that required manual source review beyond the explicit graph:
  - `bundle-decision` routes into `_execute_control_kernel_bundle_decision(...)`
  - that handler calls `decision_store.execute_apply_promotion_decision(...)`
  - the committed structural-truth baseline does not currently encode a direct relationship from `command:bundle-decision` to `function:execute_apply_promotion_decision`
- impacted artifacts and files reviewed in this rehearsal:
  - `projects/aioffice/artifacts/M13_STRUCTURAL_TRUTH_BASELINE.json`
  - `scripts/generate_structural_truth.py`
  - `scripts/operator_api.py`
  - `sessions/store.py`
  - `tests/test_control_kernel_store.py`
  - `tests/test_operator_api.py`

## 4. Linked Tests Assessment
- explicitly linked to the target in the committed structural-truth baseline:
  - none
- explicitly linked nearby in the committed structural-truth baseline:
  - `function:execute_apply_promotion_decision` is linked to store tests in `tests/test_control_kernel_store.py`
  - `protected_surface_class:protected_control_path_code_surfaces` is explicitly `verified_by` `test:test_store_rejects_apply_promotion_into_protected_control_path_code_surface`
- expected links that are explicitly missing in the committed structural-truth baseline:
  - `unresolved:test_link:command:bundle-decision`
- manual repo review found repo tests for the target outside the bounded structural-truth input set:
  - `test_operator_api_bundle_decision_executes_controlled_apply`
  - `test_operator_api_bundle_decision_rejects_blank_approved_by`
  - `test_operator_api_bundle_decision_rejects_missing_destination_mappings_file`
  - `test_operator_api_bundle_decision_rejects_invalid_destination_mappings_file_json`
  - `test_operator_api_bundle_decision_rejects_destination_outside_authoritative_workspace`
- bounded conclusion:
  - the missing explicit link is a structural-truth coverage gap, not proof that the repo lacks `bundle-decision` tests entirely

## 5. Missing Coverage / Gap Assessment
- the committed baseline correctly surfaced these unresolved gaps relevant to the bounded review:
  - `unresolved:test_link:command:bundle-decision`
  - related operator-surface gap nearby: `unresolved:test_link:command:control-kernel-details`
  - broader bounded-input gaps still present:
    - `unresolved:test_file:tests/test_store.py`
    - `unresolved:classification:projects/aioffice/governance/M13_SCOPE_REBASELINE.md`
    - `unresolved:classification:projects/aioffice/governance/STRUCTURAL_TRUTH_LAYER_CONTRACT.md`
    - `unresolved:test_link:function:ensure_first_slice_stage_start`
    - `unresolved:test_link:function:ensure_first_slice_stage_completion`
- the baseline also correctly preserves these warnings:
  - generation is limited to the explicit bounded input set
  - readiness is unchanged
  - workflow proof still stops at `architect`
- manual reviewer judgment was still required for:
  - following the call path from the CLI command to `_execute_control_kernel_bundle_decision(...)`
  - noticing that `bundle-decision` delegates into `execute_apply_promotion_decision(...)`
  - noticing that `tests/test_operator_api.py` contains relevant target tests outside the bounded input set
- source-of-truth precedence check in this pass:
  - before publication, the previously committed baseline JSON still recorded `task:AIO-065` as `backlog` while `KANBAN.md` recorded `AIO-065` as `completed`
  - per the structural-truth contract, the authoritative source system won and the derived baseline had to be regenerated rather than trusted over `KANBAN.md`

## 6. Protected-Surface Classification Assessment
- explicit and grounded classification for the selected target:
  - `command:bundle-decision` is explicitly classified as `protected operator/control surfaces`
  - the containing file `scripts/operator_api.py` is explicitly classified as `protected control-path code surfaces`
- why the classification is grounded:
  - both classifications are anchored to explicit `PRODUCT_CHANGE_GOVERNANCE.md` source refs and are carried into the structural-truth baseline as explicit `classifies` edges
- remaining classification gap:
  - no direct target-classification gap was found for `bundle-decision` as an operator/control surface
  - the remaining modeling gap is not the command classification itself; it is the absence of a direct structural-truth edge from the command node to the lower-layer store function and its linked tests

## 7. Proven Boundaries
- this rehearsal proves that one bounded protected/control review can use the structural-truth layer to:
  - locate the reviewed command by stable id and source ref
  - confirm explicit protected-surface classification
  - identify adjacent impacted repo surfaces through explicit graph edges
  - surface missing explicit test links without guessing
  - force manual reviewer attention onto gaps instead of silently suppressing them
- this rehearsal also proves that source-of-truth precedence is workable in practice:
  - when the derived baseline drifted from authoritative task truth, the source systems remained authoritative and the derived artifact had to be reconciled
- this is sufficient to treat the structural-truth layer as review-usable for one bounded rehearsal path under the current `M13` contract

## 8. Unproven Boundaries
- this rehearsal does not prove:
  - exhaustive command-to-test linking across `scripts/operator_api.py`
  - automatic call-chain mapping between command nodes and lower-layer store functions
  - exhaustive protected-surface classification completeness across every bounded input file
  - hook or automation use of the structural-truth layer
  - graph-runtime or graph-database adoption
  - workflow proof beyond `architect`
  - any readiness upgrade beyond narrow supervised bounded operation

## 9. Non-Claims
- no readiness upgrade is claimed
- no workflow-proof expansion beyond `architect` is claimed
- no claim is made that the structural-truth layer is authoritative over `KANBAN.md`, `ACTIVE_STATE.md`, `DECISION_LOG.md`, governance law, code, or tests
- no claim is made that every relevant repo test is already represented in the bounded structural-truth input set
- no claim is made that design-lane work, hook work, automation work, or any post-`M13` milestone is authorized by this rehearsal
