from __future__ import annotations

import json
from pathlib import Path

from scripts.generate_structural_truth import DEFAULT_OUTPUT_PATH, INPUT_FILES, build_structural_truth

REPO_ROOT = Path(__file__).resolve().parents[1]
FIXED_GENERATED_AT = "2026-04-17T00:00:00+00:00"


def test_generate_structural_truth_runs_over_bounded_inputs() -> None:
    artifact = build_structural_truth(REPO_ROOT, generated_at=FIXED_GENERATED_AT)

    assert artifact["metadata"]["input_files"] == list(INPUT_FILES)
    assert artifact["metadata"]["generated_at"] == FIXED_GENERATED_AT
    assert artifact["metadata"]["schema_version"] == "1.0"


def test_generate_structural_truth_includes_required_nodes_and_edges() -> None:
    artifact = build_structural_truth(REPO_ROOT, generated_at=FIXED_GENERATED_AT)

    node_classes = {node["node_class"] for node in artifact["nodes"]}
    relationship_classes = {edge["relationship_class"] for edge in artifact["edges"]}
    node_ids = {node["id"] for node in artifact["nodes"]}

    assert {
        "requirement",
        "decision",
        "task",
        "protected_surface_class",
        "file",
        "command_or_function",
        "artifact",
        "test",
    }.issubset(node_classes)
    assert {
        "depends_on",
        "ratified_by",
        "defined_in",
        "implemented_by",
        "verified_by",
        "exercised_by",
        "classifies",
        "touches",
    }.issubset(relationship_classes)
    assert {
        "task:AIO-064",
        "task:AIO-065",
        "task:AIO-066",
        "task:AIO-067",
        "decision:AIO-D-013",
        "decision:AIO-D-014",
        "file:projects/aioffice/execution/KANBAN.md",
        "file:projects/aioffice/governance/ACTIVE_STATE.md",
        "file:projects/aioffice/governance/DECISION_LOG.md",
        "file:projects/aioffice/governance/PRODUCT_CHANGE_GOVERNANCE.md",
        "file:projects/aioffice/governance/STRUCTURAL_TRUTH_LAYER_CONTRACT.md",
        "file:projects/aioffice/governance/VISION.md",
        "file:scripts/operator_api.py",
        "file:sessions/store.py",
        "file:state_machine.py",
        "file:tests/test_control_kernel_store.py",
        "file:tests/test_store.py",
        "command:control-kernel-details",
        "command:bundle-decision",
        "function:execute_apply_promotion_decision",
        "function:ensure_first_slice_stage_start",
        "function:ensure_first_slice_stage_completion",
    }.issubset(node_ids)


def test_generate_structural_truth_is_deterministic_for_same_inputs() -> None:
    first = build_structural_truth(REPO_ROOT, generated_at=FIXED_GENERATED_AT)
    second = build_structural_truth(REPO_ROOT, generated_at=FIXED_GENERATED_AT)

    assert first == second


def test_generate_structural_truth_surfaces_unresolved_gaps_without_guessing() -> None:
    artifact = build_structural_truth(REPO_ROOT, generated_at=FIXED_GENERATED_AT)

    unresolved_ids = {item["id"] for item in artifact["diagnostics"]["unresolved_references"]}
    exercised_edges = {
        (edge["from"], edge["to"])
        for edge in artifact["edges"]
        if edge["relationship_class"] == "exercised_by"
    }
    verified_edges = {
        (edge["from"], edge["to"])
        for edge in artifact["edges"]
        if edge["relationship_class"] == "verified_by"
    }

    assert "unresolved:test_link:command:control-kernel-details" in unresolved_ids
    assert "unresolved:test_link:command:bundle-decision" in unresolved_ids
    assert "unresolved:test_link:function:ensure_first_slice_stage_start" in unresolved_ids
    assert "unresolved:test_link:function:ensure_first_slice_stage_completion" in unresolved_ids
    assert "unresolved:test_file:tests/test_store.py" in unresolved_ids
    assert ("command:bundle-decision", "test:test_store_can_execute_controlled_apply_promotion_with_explicit_approved_decision") not in exercised_edges
    assert ("protected_surface_class:protected_operator_control_surfaces", "test:test_store_rejects_apply_promotion_into_protected_control_path_code_surface") not in verified_edges


def test_generate_structural_truth_matches_committed_baseline_artifact() -> None:
    generated = build_structural_truth(REPO_ROOT, generated_at=FIXED_GENERATED_AT)
    committed = json.loads((REPO_ROOT / DEFAULT_OUTPUT_PATH).read_text(encoding="utf-8"))

    assert committed == generated
