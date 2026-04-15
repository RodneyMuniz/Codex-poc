# Operator Decision Input Contract

## 1. Purpose
- Define one narrow shell-safe operator input contract over the existing `bundle-decision` surface.
- Reduce the shell/JSON brittleness observed in committed `AIO-042` evidence without redesigning store semantics or weakening explicit destination-mapping control.
- Provide the exact bounded contract target for `AIO-045`.

## 2. Current Committed Reality This Contract Must Fit
- Current accepted posture remains:
  - `M1` through `M7` complete
  - `M8` active as a narrow operator decision input/ergonomics hardening slice
  - `ready only for narrow supervised bounded operation`
  - not ready for a bounded supervised semi-autonomous cycle
  - current live workflow proof still stops at `architect`
- The current operator-facing decision wrapper already exists in `scripts/operator_api.py` as `bundle-decision`.
- The current wrapper shape requires:
  - `--bundle-id`
  - `--action`
  - `--approved-by`
  - `--destination-mappings`
  - optional `--decision-note`
  - optional `--workspace-root`
- The current wrapper parses `--destination-mappings` by decoding raw CLI text as JSON in `_parse_destination_mappings_argument(...)`.
- The current wrapper routes through the sanctioned persisted mutation path:
  - `scripts/operator_api.py::_execute_control_kernel_bundle_decision(...)`
  - `sessions/store.py::SessionStore.execute_apply_promotion_decision(...)`
- The current store path already enforces:
  - missing bundle failure
  - `pending_review`-only bundle state
  - explicit `approved` decision
  - `apply` or `promote` only
  - non-empty `approved_by`
  - explicit non-empty `destination_mappings`
  - exact mapping coverage across bundle `produced_artifact_ids`
  - authoritative-root and forbidden-path enforcement for destination writes
- This contract must therefore change only the operator-facing transport of explicit destination mappings, not the underlying decision semantics.

## 3. Problem Statement From Committed M7 Evidence
- `AIO-042` proved the operator-facing `bundle-decision` surface works against persisted state, but it also recorded real operator-input friction on the currently exercised shell path.
- In the committed rehearsal:
  - two direct PowerShell invocations failed closed with `destination_mappings must be valid JSON.`
  - the successful decision still required a subprocess-backed invocation to keep the JSON payload intact
- The committed evidence therefore shows:
  - the decision surface is real
  - the brittle point is the shell transport of the inline JSON mapping payload
  - the problem is not lack of store validation
  - the problem is not lack of wrapper existence
- The next contract must reduce shell brittleness while keeping explicit destination mappings mandatory and fail-closed.

## 4. Selected Shell-Safe Input Path
- Selected input path:
  - file-based mapping input
- Selected operator-facing argument:
  - `--destination-mappings-file <path>`
- This contract selects one shell-safe path only.
- This contract does not define competing operator-facing transport modes such as:
  - inline JSON string mode
  - stdin mode
  - multiple equivalent mapping-input modes
- Rationale for the file-based path:
  - it avoids embedding structured JSON in the shell command line
  - it preserves the already-committed mapping schema exactly
  - it is narrow to implement over the existing wrapper
  - it supports operator review of the exact mapping payload before execution
  - it does not require any change to `SessionStore.execute_apply_promotion_decision(...)`

## 5. Exact Supported Invocation Shape
- Supported command shape for the shell-safe operator contract:

```powershell
.\venv\Scripts\python.exe scripts/operator_api.py bundle-decision `
  --bundle-id <bundle_id> `
  --action <apply|promote> `
  --approved-by <operator_id> `
  --destination-mappings-file <path-to-json-file> `
  [--decision-note <non-empty-text>] `
  [--workspace-root <sanctioned-workspace-root>]
```

- Scope rules for this invocation shape:
  - one bundle at a time only
  - one explicit approved decision at a time only
  - one mapping file at a time only
  - no batch mode
- This contract intentionally does not add any separate preflight command, approval mode, or workflow-stage action.

## 6. Required Explicit Input Fields
- `bundle_id`
  - required
  - must be non-empty
- `action`
  - required
  - must be exactly `apply` or `promote`
- `approved_by`
  - required
  - must be non-empty
- `destination_mappings_file`
  - required
  - must point to an existing readable JSON file
- `decision`
  - fixed to `approved` in this slice
  - not exposed as a free-form operator choice
- `decision_note`
  - optional
  - if supplied, must be non-empty
- `workspace_root`
  - optional
  - only for sanctioned non-default persisted store targeting
  - if supplied, it must resolve to a lawful workspace that already contains `sessions/studio.db`
- Explicit destination mappings remain required.
- The operator must still choose and provide the intended destination path for every produced artifact in the target bundle.

## 7. Destination-Mappings Data Contract
- The mapping file must decode to the same JSON array shape already accepted by the current `--destination-mappings` implementation.
- Expected top-level shape:
  - one JSON array
- Expected item shape:
  - each array item must be one JSON object with:
    - `source_artifact_id`
    - `destination_path`
- Expected example:

```json
[
  {
    "source_artifact_id": "wf_artifact_1234567890ab",
    "destination_path": "projects/aioffice/execution/approved/example_output.md"
  }
]
```

- Required data-contract properties:
  - the array must be non-empty
  - each item must be an object
  - `source_artifact_id` must be non-empty
  - `destination_path` must be non-empty
  - every produced artifact in the bundle must receive exactly one explicit mapping
  - mappings must not rely on implicit destination inference
- The following existing store-level validation remains authoritative and unchanged:
  - referenced artifact must exist
  - referenced artifact must belong to the bundle `produced_artifact_ids`
  - mapping coverage must be complete
  - duplicate `source_artifact_id` entries fail
  - duplicate `destination_path` entries fail
  - destination path must stay within the packet `authoritative_workspace_root`
  - governance-controlled, artifact-tree, forbidden, and out-of-root destinations fail

## 8. Fail-Closed Rules
- Missing `--destination-mappings-file`:
  - fail before any persisted mutation
- Mapping file path does not exist:
  - fail before any persisted mutation
- Mapping file path resolves to a directory instead of a file:
  - fail before any persisted mutation
- Mapping file is unreadable:
  - fail before any persisted mutation
- Mapping file does not decode as valid JSON:
  - fail before any persisted mutation
- Mapping file decodes to anything other than a JSON array:
  - fail before any persisted mutation
- Mapping file decodes to an empty array:
  - fail before any persisted mutation
- Mapping item is malformed:
  - fail before any persisted mutation
- Missing bundle:
  - fail before any write attempt
- Non-`pending_review` bundle state:
  - fail before any write attempt
- Invalid `action`:
  - fail
- Blank `approved_by`:
  - fail
- Blank optional `decision_note`:
  - fail
- Invalid optional `workspace_root`:
  - fail
- Incomplete mapping coverage:
  - fail
- Out-of-root or forbidden destination:
  - fail
- No fallback behavior:
  - no silent switch back to inline JSON
  - no implicit mapping inference
  - no partial mapping acceptance
  - no silent downgrade from `promote` to `apply`

## 9. Shell-Specific Considerations For The Currently Exercised Operator Path
- The currently exercised operator path in committed evidence is Windows PowerShell.
- The committed `AIO-042` rehearsal showed that embedding the JSON array directly in the CLI argument was brittle on this shell path.
- A file-path argument is shell-safer on this path because:
  - the shell only has to pass one path token
  - the structured JSON payload is not reinterpreted by shell quoting rules
  - the operator can inspect the file contents separately from the command line
- This contract therefore treats the mapping payload as file content, not shell-inline structure.
- Example current-path usage pattern:

```powershell
.\venv\Scripts\python.exe scripts/operator_api.py bundle-decision `
  --bundle-id bundle_example `
  --action apply `
  --approved-by project_orchestrator `
  --destination-mappings-file ".\tmp\bundle_decision_mappings.json"
```

- The contract does not assume the shell will preserve complex inline JSON reliably.
- The contract does assume the shell can pass a quoted file path reliably enough for one bounded operator decision command.

## 10. Relationship To The Existing Bundle-Decision Wrapper
- Command name remains:
  - `bundle-decision`
- Bundle-scoped decision behavior remains:
  - unchanged
- Before/after inspection behavior remains:
  - unchanged
- Store mutation path remains:
  - unchanged
- Decision semantics remain:
  - unchanged
- Destination-mapping schema remains:
  - unchanged
- The contract changes only the operator-facing transport of the explicit mapping payload:
  - from raw inline JSON text
  - to a JSON file read by the wrapper
- The implementation target for `AIO-045` should therefore:
  - read the file
  - decode the JSON array
  - pass the decoded list into the existing `_execute_control_kernel_bundle_decision(...)` flow
  - preserve all existing store fail-closed behavior

## 11. Exact Out-Of-Scope Boundaries
- Out of scope for this contract:
  - redesigning `apply` or `promote` semantics
  - changing `SessionStore.execute_apply_promotion_decision(...)`
  - automatic destination mapping
  - packet issuance
  - bundle creation
  - bundle rejection
  - multi-bundle batch decisions
  - stdin-based mapping transport
  - multiple operator-facing mapping input modes in the same slice
  - later-stage workflow proof
  - concurrency handling claims
  - operator workspace UI work
  - readiness upgrades
  - autonomy, overnight, semi-autonomous, or UAT readiness claims

## 12. Next Implementation Implications For AIO-045
- `AIO-045` should implement exactly one new operator-facing mapping input path:
  - `--destination-mappings-file`
- `AIO-045` should keep the command narrow:
  - one bundle
  - one decision
  - one mapping file
- `AIO-045` should decode the file into the same mapping list shape already consumed by the current wrapper/store path.
- `AIO-045` should add focused verification for at minimum:
  - one success path using a mapping file
  - one fail-closed missing-file or unreadable-file case
  - one fail-closed invalid-JSON or wrong-top-level-shape case
  - one preserved out-of-root or forbidden-destination failure case after file decoding
- `AIO-045` should not add:
  - stdin mode
  - implicit mapping generation
  - store semantic changes
  - later-stage workflow behavior
