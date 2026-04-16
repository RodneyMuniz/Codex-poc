from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "1.0"
GENERATOR_VERSION = "aioffice-structural-truth-baseline-v1"
DEFAULT_OUTPUT_PATH = "projects/aioffice/artifacts/M13_STRUCTURAL_TRUTH_BASELINE.json"
REPO_ROOT = Path(__file__).resolve().parents[1]

INPUT_FILES = (
    "projects/aioffice/governance/VISION.md",
    "projects/aioffice/governance/PRODUCT_CHANGE_GOVERNANCE.md",
    "projects/aioffice/governance/ACTIVE_STATE.md",
    "projects/aioffice/governance/DECISION_LOG.md",
    "projects/aioffice/governance/STRUCTURAL_TRUTH_LAYER_CONTRACT.md",
    "projects/aioffice/governance/M13_SCOPE_REBASELINE.md",
    "projects/aioffice/execution/KANBAN.md",
    "scripts/operator_api.py",
    "sessions/store.py",
    "state_machine.py",
    "tests/test_control_kernel_store.py",
    "tests/test_store.py",
)

REQUIRED_NODE_CLASSES = {
    "requirement",
    "decision",
    "task",
    "protected_surface_class",
    "file",
    "command_or_function",
    "artifact",
    "test",
}

REQUIRED_RELATIONSHIP_CLASSES = {
    "depends_on",
    "ratified_by",
    "defined_in",
    "implemented_by",
    "verified_by",
    "exercised_by",
    "classifies",
    "touches",
}


def _read_lines(repo_root: Path, relative_path: str) -> list[str]:
    path = repo_root / relative_path
    if not path.exists():
        raise ValueError(f"Required input file not found: {relative_path}")
    return path.read_text(encoding="utf-8").splitlines()


def _source_ref(path: str, line: int) -> dict[str, Any]:
    return {"path": path, "line": line}


def _find_exact_line(lines: list[str], text: str, path: str) -> int:
    for index, line in enumerate(lines, start=1):
        if line == text or line.strip() == text.strip():
            return index
    raise ValueError(f"Expected exact line not found in {path}: {text}")


def _parse_task_sections(lines: list[str], path: str) -> dict[str, dict[str, Any]]:
    tasks: dict[str, dict[str, Any]] = {}
    index = 0
    while index < len(lines):
        if not lines[index].startswith("### "):
            index += 1
            continue

        heading = lines[index][4:].strip()
        section_line = index + 1
        fields: dict[str, str] = {}
        field_lines: dict[str, int] = {}
        acceptance: list[dict[str, Any]] = []
        dependencies: list[dict[str, Any]] = []
        active_list: str | None = None
        index += 1

        while index < len(lines):
            current = lines[index]
            if current.startswith("### ") or current.startswith("## "):
                break
            if not current.strip():
                active_list = None
                index += 1
                continue
            if current.startswith("  - "):
                item = {"text": current[4:].strip(), "line": index + 1}
                if active_list == "acceptance":
                    acceptance.append(item)
                elif active_list == "dependencies":
                    dependencies.append(item)
                else:
                    index += 1
                    continue
                index += 1
                continue
            if current.startswith("- "):
                key, value = current[2:].split(":", 1)
                key = key.strip()
                value = value.strip()
                fields[key] = value
                field_lines[key] = index + 1
                active_list = key if not value else None
                index += 1
                continue
            raise ValueError(f"Unrecognized task line in {path}:{index + 1}: {current}")

        if fields.get("item_type") == "task" and fields.get("id"):
            tasks[fields["id"]] = {
                "id": fields["id"],
                "heading": heading,
                "line": section_line,
                "fields": fields,
                "field_lines": field_lines,
                "acceptance": acceptance,
                "dependencies": dependencies,
            }

    return tasks


def _parse_decisions(lines: list[str], path: str) -> dict[str, dict[str, Any]]:
    decisions: dict[str, dict[str, Any]] = {}
    index = 0
    while index < len(lines):
        if not lines[index].startswith("### AIO-D-"):
            index += 1
            continue

        decision_id = lines[index][4:].strip()
        section_line = index + 1
        fields: dict[str, str] = {}
        field_lines: dict[str, int] = {}
        active_list: str | None = None
        index += 1

        while index < len(lines):
            current = lines[index]
            if current.startswith("### ") or current.startswith("## "):
                break
            if not current.strip():
                active_list = None
                index += 1
                continue
            if current.startswith("- rationale:"):
                field_lines["rationale"] = index + 1
                active_list = "rationale"
                index += 1
                continue
            if current.startswith("- "):
                key, value = current[2:].split(":", 1)
                fields[key.strip()] = value.strip()
                field_lines[key.strip()] = index + 1
                active_list = None
                index += 1
                continue
            if current.startswith("  - "):
                index += 1
                continue
            raise ValueError(f"Unrecognized decision line in {path}:{index + 1}: {current}")

        decisions[decision_id] = {
            "id": decision_id,
            "line": section_line,
            "fields": fields,
            "field_lines": field_lines,
        }

    return decisions


def _parse_test_functions(lines: list[str]) -> list[dict[str, Any]]:
    tests: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    for index, line in enumerate(lines, start=1):
        match = re.match(r"^def (test_[A-Za-z0-9_]+)\(", line)
        if match:
            if current is not None:
                tests.append(current)
            current = {"name": match.group(1), "line": index, "body": [(index, line)]}
            continue
        if current is not None and re.match(r"^def [A-Za-z0-9_]+\(", line):
            tests.append(current)
            current = None
        if current is not None:
            current["body"].append((index, line))
    if current is not None:
        tests.append(current)
    return tests


def _artifact() -> dict[str, Any]:
    return {
        "metadata": {},
        "nodes": [],
        "edges": [],
        "diagnostics": {
            "unresolved_references": [],
            "orphan_nodes": [],
            "warnings": [],
        },
    }


def build_structural_truth(repo_root: Path | None = None, *, generated_at: str | None = None) -> dict[str, Any]:
    repo_root = repo_root or REPO_ROOT
    timestamp = generated_at or datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    lines = {path: _read_lines(repo_root, path) for path in INPUT_FILES}
    tasks = _parse_task_sections(lines["projects/aioffice/execution/KANBAN.md"], "projects/aioffice/execution/KANBAN.md")
    decisions = _parse_decisions(lines["projects/aioffice/governance/DECISION_LOG.md"], "projects/aioffice/governance/DECISION_LOG.md")

    required_tasks = ("AIO-063", "AIO-064", "AIO-065", "AIO-066", "AIO-067")
    required_decisions = ("AIO-D-013", "AIO-D-014")
    for task_id in required_tasks:
        if task_id not in tasks:
            raise ValueError(f"Required task missing from KANBAN: {task_id}")
    for decision_id in required_decisions:
        if decision_id not in decisions:
            raise ValueError(f"Required decision missing from DECISION_LOG: {decision_id}")

    data = _artifact()
    nodes_by_id: dict[str, dict[str, Any]] = {}

    def add_node(node_id: str, node_class: str, label: str, source_path: str, source_line: int, **attributes: Any) -> None:
        if node_id in nodes_by_id:
            raise ValueError(f"Duplicate node id: {node_id}")
        node = {
            "id": node_id,
            "node_class": node_class,
            "label": label,
            "source_ref": _source_ref(source_path, source_line),
        }
        if attributes:
            node["attributes"] = attributes
        nodes_by_id[node_id] = node

    def add_edge(from_id: str, to_id: str, relationship_class: str, source_path: str, source_line: int) -> None:
        if from_id not in nodes_by_id or to_id not in nodes_by_id:
            raise ValueError(f"Missing node for edge {relationship_class}: {from_id} -> {to_id}")
        data["edges"].append(
            {
                "from": from_id,
                "to": to_id,
                "relationship_class": relationship_class,
                "source_ref": _source_ref(source_path, source_line),
            }
        )

    def add_unresolved(item_id: str, kind: str, message: str, source_path: str, source_line: int) -> None:
        data["diagnostics"]["unresolved_references"].append(
            {
                "id": item_id,
                "kind": kind,
                "message": message,
                "source_ref": _source_ref(source_path, source_line),
            }
        )

    def add_warning(item_id: str, message: str, source_path: str, source_line: int) -> None:
        data["diagnostics"]["warnings"].append(
            {
                "id": item_id,
                "message": message,
                "source_ref": _source_ref(source_path, source_line),
            }
        )

    for path in INPUT_FILES:
        add_node(f"file:{path}", "file", path, path, 1)

    for task_id in required_tasks:
        task = tasks[task_id]
        fields = task["fields"]
        field_lines = task["field_lines"]
        add_node(
            f"task:{task_id}",
            "task",
            f"{task_id}: {fields['title']}",
            "projects/aioffice/execution/KANBAN.md",
            field_lines["id"],
            milestone=fields["milestone"],
            status=fields["status"],
            expected_artifact_path=fields["expected_artifact_path"],
        )
        add_edge(
            f"task:{task_id}",
            "file:projects/aioffice/execution/KANBAN.md",
            "defined_in",
            "projects/aioffice/execution/KANBAN.md",
            field_lines["id"],
        )
        artifact_path = fields["expected_artifact_path"]
        add_node(
            f"artifact:{artifact_path}",
            "artifact",
            artifact_path,
            "projects/aioffice/execution/KANBAN.md",
            field_lines["expected_artifact_path"],
            task_id=task_id,
            exists_in_bounded_inputs=artifact_path in INPUT_FILES,
            exists_in_repo=(repo_root / artifact_path).exists(),
        )
        add_edge(
            f"task:{task_id}",
            f"artifact:{artifact_path}",
            "implemented_by",
            "projects/aioffice/execution/KANBAN.md",
            field_lines["expected_artifact_path"],
        )
        if artifact_path in INPUT_FILES:
            add_edge(
                f"artifact:{artifact_path}",
                f"file:{artifact_path}",
                "defined_in",
                "projects/aioffice/execution/KANBAN.md",
                field_lines["expected_artifact_path"],
            )
        for dependency in task["dependencies"]:
            dependency_id = dependency["text"]
            if f"task:{dependency_id}" not in nodes_by_id:
                if dependency_id not in tasks:
                    add_unresolved(
                        f"unresolved:missing_task:{task_id}:{dependency_id}",
                        "missing_dependency_task",
                        f"{task_id} depends on {dependency_id}, but that task was not found in the bounded KANBAN parse.",
                        "projects/aioffice/execution/KANBAN.md",
                        dependency["line"],
                    )
                    continue
                dependency_task = tasks[dependency_id]
                dependency_fields = dependency_task["fields"]
                dependency_lines = dependency_task["field_lines"]
                add_node(
                    f"task:{dependency_id}",
                    "task",
                    f"{dependency_id}: {dependency_fields['title']}",
                    "projects/aioffice/execution/KANBAN.md",
                    dependency_lines["id"],
                    milestone=dependency_fields["milestone"],
                    status=dependency_fields["status"],
                    expected_artifact_path=dependency_fields["expected_artifact_path"],
                )
                add_edge(
                    f"task:{dependency_id}",
                    "file:projects/aioffice/execution/KANBAN.md",
                    "defined_in",
                    "projects/aioffice/execution/KANBAN.md",
                    dependency_lines["id"],
                )
            add_edge(
                f"task:{task_id}",
                f"task:{dependency_id}",
                "depends_on",
                "projects/aioffice/execution/KANBAN.md",
                dependency["line"],
            )

    for decision_id in required_decisions:
        decision = decisions[decision_id]
        add_node(
            f"decision:{decision_id}",
            "decision",
            f"{decision_id}: {decision['fields']['decision']}",
            "projects/aioffice/governance/DECISION_LOG.md",
            decision["line"],
            date=decision["fields"]["date"],
            status=decision["fields"]["status"],
        )
        add_edge(
            f"decision:{decision_id}",
            "file:projects/aioffice/governance/DECISION_LOG.md",
            "defined_in",
            "projects/aioffice/governance/DECISION_LOG.md",
            decision["line"],
        )

    add_edge(
        "decision:AIO-D-014",
        "decision:AIO-D-013",
        "depends_on",
        "projects/aioffice/governance/DECISION_LOG.md",
        decisions["AIO-D-014"]["field_lines"]["decision"],
    )
    for task_id in ("AIO-064", "AIO-065", "AIO-066", "AIO-067"):
        add_edge(
            f"task:{task_id}",
            "decision:AIO-D-014",
            "ratified_by",
            "projects/aioffice/governance/DECISION_LOG.md",
            decisions["AIO-D-014"]["field_lines"]["decision"],
        )

    requirement_specs = (
        ("requirement:source_of_truth_precedence", "Source-Of-Truth Precedence", "projects/aioffice/governance/STRUCTURAL_TRUTH_LAYER_CONTRACT.md", "## 4. Source-Of-Truth Precedence"),
        ("requirement:minimum_schema", "Minimum Schema", "projects/aioffice/governance/STRUCTURAL_TRUTH_LAYER_CONTRACT.md", "## 5. Minimum Schema"),
        ("requirement:deterministic_ingestion_rules", "Deterministic Ingestion Rules", "projects/aioffice/governance/STRUCTURAL_TRUTH_LAYER_CONTRACT.md", "## 6. Deterministic Ingestion Rules"),
        ("requirement:sanctioned_enforcement_and_review_points", "Sanctioned Enforcement And Review Points", "projects/aioffice/governance/STRUCTURAL_TRUTH_LAYER_CONTRACT.md", "## 7. Sanctioned Enforcement And Review Points"),
        ("requirement:gold_standard_maturity_rubric", "Gold-Standard Maturity Rubric", "projects/aioffice/governance/STRUCTURAL_TRUTH_LAYER_CONTRACT.md", "## 8. Gold-Standard Maturity Rubric"),
        ("requirement:explicit_non_claims", "Explicit Non-Claims", "projects/aioffice/governance/STRUCTURAL_TRUTH_LAYER_CONTRACT.md", "## 9. Explicit Non-Claims"),
        ("requirement:vision_derived_structural_truth_layer", "Derived Structural Truth Layer", "projects/aioffice/governance/VISION.md", "## 9A. Derived Structural Truth Layer"),
    )
    for node_id, label, path, heading in requirement_specs:
        line = _find_exact_line(lines[path], heading, path)
        add_node(node_id, "requirement", label, path, line)
        add_edge(node_id, f"file:{path}", "defined_in", path, line)

    surface_specs = (
        ("protected_surface_class:governance_law_surfaces", "governance law surfaces", "- `governance law surfaces`"),
        ("protected_surface_class:accepted_truth_surfaces", "accepted truth surfaces", "- `accepted truth surfaces`"),
        ("protected_surface_class:protected_control_path_code_surfaces", "protected control-path code surfaces", "- `protected control-path code surfaces`"),
        ("protected_surface_class:protected_operator_control_surfaces", "protected operator/control surfaces", "- `protected operator/control surfaces`"),
    )
    for node_id, label, bullet in surface_specs:
        line = _find_exact_line(lines["projects/aioffice/governance/PRODUCT_CHANGE_GOVERNANCE.md"], bullet, "projects/aioffice/governance/PRODUCT_CHANGE_GOVERNANCE.md")
        add_node(node_id, "protected_surface_class", label, "projects/aioffice/governance/PRODUCT_CHANGE_GOVERNANCE.md", line)
        add_edge(node_id, "file:projects/aioffice/governance/PRODUCT_CHANGE_GOVERNANCE.md", "defined_in", "projects/aioffice/governance/PRODUCT_CHANGE_GOVERNANCE.md", line)

    add_node(
        "artifact:projects/aioffice/governance/M13_SCOPE_REBASELINE.md",
        "artifact",
        "projects/aioffice/governance/M13_SCOPE_REBASELINE.md",
        "projects/aioffice/governance/M13_SCOPE_REBASELINE.md",
        1,
    )
    add_edge(
        "artifact:projects/aioffice/governance/M13_SCOPE_REBASELINE.md",
        "file:projects/aioffice/governance/M13_SCOPE_REBASELINE.md",
        "defined_in",
        "projects/aioffice/governance/M13_SCOPE_REBASELINE.md",
        1,
    )

    symbol_specs = (
        ("command:control-kernel-details", "control-kernel-details", "scripts/operator_api.py", '    control_kernel_details = subparsers.add_parser("control-kernel-details")', "command"),
        ("command:bundle-decision", "bundle-decision", "scripts/operator_api.py", '    bundle_decision = subparsers.add_parser("bundle-decision")', "command"),
        ("function:execute_apply_promotion_decision", "execute_apply_promotion_decision", "sessions/store.py", "    def execute_apply_promotion_decision(", "function"),
        ("function:ensure_first_slice_stage_start", "ensure_first_slice_stage_start", "state_machine.py", "def ensure_first_slice_stage_start(", "function"),
        ("function:ensure_first_slice_stage_completion", "ensure_first_slice_stage_completion", "state_machine.py", "def ensure_first_slice_stage_completion(", "function"),
    )
    for node_id, label, path, needle, kind in symbol_specs:
        line = _find_exact_line(lines[path], needle, path)
        add_node(node_id, "command_or_function", label, path, line, symbol_kind=kind)
        add_edge(node_id, f"file:{path}", "defined_in", path, line)

    touch_specs = (
        ("task:AIO-064", "requirement:source_of_truth_precedence", tasks["AIO-064"]["acceptance"][0]["line"]),
        ("task:AIO-064", "requirement:minimum_schema", tasks["AIO-064"]["acceptance"][1]["line"]),
        ("task:AIO-064", "requirement:deterministic_ingestion_rules", tasks["AIO-064"]["acceptance"][2]["line"]),
        ("task:AIO-064", "requirement:sanctioned_enforcement_and_review_points", tasks["AIO-064"]["acceptance"][2]["line"]),
        ("task:AIO-064", "requirement:gold_standard_maturity_rubric", tasks["AIO-064"]["line"]),
        ("task:AIO-064", "requirement:explicit_non_claims", tasks["AIO-064"]["acceptance"][3]["line"]),
        ("task:AIO-065", "requirement:deterministic_ingestion_rules", tasks["AIO-065"]["acceptance"][0]["line"]),
        ("task:AIO-065", "requirement:explicit_non_claims", tasks["AIO-065"]["acceptance"][2]["line"]),
        ("task:AIO-065", "protected_surface_class:governance_law_surfaces", tasks["AIO-065"]["field_lines"]["details"]),
        ("task:AIO-065", "protected_surface_class:accepted_truth_surfaces", tasks["AIO-065"]["field_lines"]["details"]),
        ("task:AIO-065", "protected_surface_class:protected_control_path_code_surfaces", tasks["AIO-065"]["field_lines"]["details"]),
        ("task:AIO-065", "protected_surface_class:protected_operator_control_surfaces", tasks["AIO-065"]["field_lines"]["details"]),
    )
    for from_id, to_id, line in touch_specs:
        add_edge(from_id, to_id, "touches", "projects/aioffice/execution/KANBAN.md", line)

    classifies_specs = (
        ("protected_surface_class:governance_law_surfaces", "file:projects/aioffice/governance/VISION.md", "    - `projects/aioffice/governance/VISION.md`"),
        ("protected_surface_class:governance_law_surfaces", "file:projects/aioffice/governance/PRODUCT_CHANGE_GOVERNANCE.md", "    - `projects/aioffice/governance/PRODUCT_CHANGE_GOVERNANCE.md`"),
        ("protected_surface_class:accepted_truth_surfaces", "file:projects/aioffice/execution/KANBAN.md", "    - `projects/aioffice/execution/KANBAN.md`"),
        ("protected_surface_class:accepted_truth_surfaces", "file:projects/aioffice/governance/ACTIVE_STATE.md", "    - `projects/aioffice/governance/ACTIVE_STATE.md`"),
        ("protected_surface_class:accepted_truth_surfaces", "file:projects/aioffice/governance/DECISION_LOG.md", "    - `projects/aioffice/governance/DECISION_LOG.md` when it ratifies accepted divergence or milestone selection"),
        ("protected_surface_class:protected_control_path_code_surfaces", "file:sessions/store.py", "    - `sessions/store.py`"),
        ("protected_surface_class:protected_control_path_code_surfaces", "file:scripts/operator_api.py", "    - `scripts/operator_api.py`"),
        ("protected_surface_class:protected_operator_control_surfaces", "command:control-kernel-details", "    - the `control-kernel-details` and `bundle-decision` command surfaces"),
        ("protected_surface_class:protected_operator_control_surfaces", "command:bundle-decision", "    - the `control-kernel-details` and `bundle-decision` command surfaces"),
    )
    product_path = "projects/aioffice/governance/PRODUCT_CHANGE_GOVERNANCE.md"
    for from_id, to_id, bullet in classifies_specs:
        add_edge(from_id, to_id, "classifies", product_path, _find_exact_line(lines[product_path], bullet, product_path))

    tests = _parse_test_functions(lines["tests/test_control_kernel_store.py"])
    relevant_tests = [test for test in tests if "execute_apply_promotion_decision(" in "\n".join(text for _, text in test["body"])]
    test_lookup = {test["name"]: test for test in relevant_tests}
    for test in relevant_tests:
        add_node(f"test:{test['name']}", "test", test["name"], "tests/test_control_kernel_store.py", test["line"])
        add_edge(f"test:{test['name']}", "file:tests/test_control_kernel_store.py", "defined_in", "tests/test_control_kernel_store.py", test["line"])
        add_edge("function:execute_apply_promotion_decision", f"test:{test['name']}", "exercised_by", "tests/test_control_kernel_store.py", test["line"])

    accepted_truth_body = test_lookup["test_store_rejects_apply_promotion_into_accepted_truth_surface"]["body"]
    accepted_truth_line = next(line for line, text in accepted_truth_body if '"accepted truth surface"' in text)
    add_edge(
        "protected_surface_class:accepted_truth_surfaces",
        "test:test_store_rejects_apply_promotion_into_accepted_truth_surface",
        "verified_by",
        "tests/test_control_kernel_store.py",
        accepted_truth_line,
    )

    protected_code_body = test_lookup["test_store_rejects_apply_promotion_into_protected_control_path_code_surface"]["body"]
    protected_code_line = next(line for line, text in protected_code_body if '"protected control-path code surface"' in text)
    add_edge(
        "protected_surface_class:protected_control_path_code_surfaces",
        "test:test_store_rejects_apply_promotion_into_protected_control_path_code_surface",
        "verified_by",
        "tests/test_control_kernel_store.py",
        protected_code_line,
    )

    store_tests = _parse_test_functions(lines["tests/test_store.py"])
    if not any("execute_apply_promotion_decision(" in "\n".join(text for _, text in test["body"]) for test in store_tests):
        add_unresolved(
            "unresolved:test_file:tests/test_store.py",
            "missing_bounded_linked_test",
            "tests/test_store.py is in the bounded input set, but no explicit structural-truth link to the current protected/control surfaces was detected safely.",
            "tests/test_store.py",
            1,
        )

    for node_id, message in (
        ("command:control-kernel-details", "No explicit linked test for control-kernel-details was detected in the bounded input set."),
        ("command:bundle-decision", "No explicit linked test for bundle-decision was detected in the bounded input set."),
        ("function:ensure_first_slice_stage_start", "No explicit linked test for ensure_first_slice_stage_start was detected in the bounded input set."),
        ("function:ensure_first_slice_stage_completion", "No explicit linked test for ensure_first_slice_stage_completion was detected in the bounded input set."),
    ):
        ref = nodes_by_id[node_id]["source_ref"]
        add_unresolved(f"unresolved:test_link:{node_id}", "missing_test_link", message, ref["path"], ref["line"])

    for node_id, path in (
        ("file:projects/aioffice/governance/STRUCTURAL_TRUTH_LAYER_CONTRACT.md", "projects/aioffice/governance/STRUCTURAL_TRUTH_LAYER_CONTRACT.md"),
        ("file:projects/aioffice/governance/M13_SCOPE_REBASELINE.md", "projects/aioffice/governance/M13_SCOPE_REBASELINE.md"),
    ):
        if not any(edge["relationship_class"] == "classifies" and edge["to"] == node_id for edge in data["edges"]):
            add_unresolved(
                f"unresolved:classification:{path}",
                "missing_surface_classification",
                f"{Path(path).name} is in the bounded input set, but no explicit protected-surface class mapping was found in the bounded governance sources.",
                path,
                1,
            )

    contract_path = "projects/aioffice/governance/STRUCTURAL_TRUTH_LAYER_CONTRACT.md"
    active_state_path = "projects/aioffice/governance/ACTIVE_STATE.md"
    add_warning(
        "warning:bounded_input_set_only",
        "Generation is limited to the explicit bounded input set; no open-ended repo crawl or inferred relationships were used.",
        contract_path,
        _find_exact_line(lines[contract_path], "- Ingestion must run from an explicit committed input set rather than an open-ended file crawl.", contract_path),
    )
    add_warning(
        "warning:readiness_boundary_unchanged",
        "This baseline artifact does not upgrade readiness or widen workflow proof beyond architect.",
        active_state_path,
        _find_exact_line(lines[active_state_path], "- Current readiness is `ready only for narrow supervised bounded operation`.", active_state_path),
    )
    add_warning(
        "warning:workflow_boundary_architect",
        "Current live workflow proof still stops at architect.",
        active_state_path,
        _find_exact_line(lines[active_state_path], "- Current live workflow proof stops at `architect`.", active_state_path),
    )

    incidence = {node_id: 0 for node_id in nodes_by_id}
    for edge in data["edges"]:
        incidence[edge["from"]] += 1
        incidence[edge["to"]] += 1
    for node_id, count in sorted(incidence.items()):
        if count == 0:
            data["diagnostics"]["orphan_nodes"].append(
                {
                    "node_id": node_id,
                    "message": "No explicit structural-truth relationships were established safely for this node in the bounded baseline.",
                    "source_ref": nodes_by_id[node_id]["source_ref"],
                }
            )

    data["nodes"] = sorted(nodes_by_id.values(), key=lambda item: item["id"])
    data["edges"].sort(
        key=lambda item: (
            item["relationship_class"],
            item["from"],
            item["to"],
            item["source_ref"]["path"],
            item["source_ref"]["line"],
        )
    )
    data["diagnostics"]["unresolved_references"].sort(key=lambda item: (item["kind"], item["id"]))
    data["diagnostics"]["warnings"].sort(key=lambda item: item["id"])
    data["metadata"] = {
        "schema_version": SCHEMA_VERSION,
        "generated_at": timestamp,
        "generator_version": GENERATOR_VERSION,
        "input_files": list(INPUT_FILES),
    }

    node_classes = {node["node_class"] for node in data["nodes"]}
    relationship_classes = {edge["relationship_class"] for edge in data["edges"]}
    missing_node_classes = REQUIRED_NODE_CLASSES - node_classes
    missing_relationship_classes = REQUIRED_RELATIONSHIP_CLASSES - relationship_classes
    if missing_node_classes:
        raise ValueError(f"Missing required node classes: {sorted(missing_node_classes)}")
    if missing_relationship_classes:
        raise ValueError(f"Missing required relationship classes: {sorted(missing_relationship_classes)}")
    return data


def write_structural_truth(
    *,
    repo_root: Path | None = None,
    output_path: str = DEFAULT_OUTPUT_PATH,
    generated_at: str | None = None,
) -> dict[str, Any]:
    repo_root = repo_root or REPO_ROOT
    artifact = build_structural_truth(repo_root, generated_at=generated_at)
    absolute_output = repo_root / output_path
    absolute_output.parent.mkdir(parents=True, exist_ok=True)
    absolute_output.write_text(json.dumps(artifact, indent=2) + "\n", encoding="utf-8")
    return artifact


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate the bounded AIOffice structural truth baseline artifact.")
    parser.add_argument("--repo-root", default=str(REPO_ROOT))
    parser.add_argument("--output", default=DEFAULT_OUTPUT_PATH)
    parser.add_argument("--generated-at", default=None)
    args = parser.parse_args()
    artifact = write_structural_truth(
        repo_root=Path(args.repo_root),
        output_path=args.output,
        generated_at=args.generated_at,
    )
    print(json.dumps(artifact, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
