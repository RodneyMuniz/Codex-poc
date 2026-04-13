# AIOffice Workspace Boundaries

Boundary status:
- drafted under AIO-005 for operator review
- governing containment draft for AIOffice
- intended to support later enforcement, not replace it

## 1. Purpose And Scope
Workspace boundaries are central to AIOffice because authority depends on where work may be read, written, staged, and promoted. If the system does not control its roots and write surfaces, it cannot prove whether a result came from sanctioned workflow or uncontrolled mutation.

Containment is part of governance, not an implementation detail. Path rules, scratch rules, import rules, and canonical state protections define what may become real inside the project.

Uncontrolled writes are workflow failures. A useful output written to the wrong place, promoted without review, or applied outside sanctioned paths does not count as valid AIOffice work.

This document defines:
- which roots are authoritative
- which roots are non-authoritative or duplicate
- which spaces are scratch-only
- what may be read, written, adapted, copied, referenced, or rejected
- how Codex work must be contained
- how non-authoritative work may later be promoted into canonical state
- what must never be modified directly

## 2. Root Authority Model
Root authority determines whether a filesystem location may host governed AIOffice truth.

| Root type | Current location or pattern | Status | Trust level | Permitted use | Forbidden use |
| --- | --- | --- | --- | --- | --- |
| Authoritative repo root | `C:\Users\rodne\OneDrive\Desktop\_AIStudio_POC` | Active and binding | High, but only through sanctioned paths | Read governed repo state, write governed AIOffice artifacts, run sanctioned registration and control flows | Treat every path under the root as automatically canonical for AIOffice |
| Known duplicate / non-authoritative root | `C:\Users\rodne\OneDrive\Documentos\_AIStudio_POC` | Explicitly non-authoritative | None for governed state | Read only if a future decision explicitly allows comparison or recovery work | Any governed write, promotion, registration, or canonical-state mutation |
| Imported historical/reference roots | Any external donor, archive, export, or historical snapshot later admitted for inspection | Reference-only unless later promoted through sanctioned import | Low to medium, depending on provenance | Read, compare, quote, and classify for later donor decisions | Treat as live authority, write back as canonical AIOffice work, or import without provenance |
| Future scratch/worktree/sandbox roots | Temporary work areas under the authoritative repo or later managed worktrees/sandboxes | Non-authoritative by default | Low until reviewed and applied | Draft, experiment, generate temporary bundles, stage bounded executor output | Self-promote outputs into canonical truth or bypass review/apply gates |

Rules:
- Being inside the authoritative repo root does not make a path authoritative for AIOffice by itself.
- For this project, the governed canonical project path is `projects/aioffice/...`.
- Any future worktree, sandbox, or scratch root is non-authoritative until an explicit controlled promotion occurs.

## 3. Workspace Classes
Workspace classes define how a location may be used inside the authoritative root and around it.

| Workspace class | Purpose | Who may read | Who may write | Authoritative output | Promotion requirements |
| --- | --- | --- | --- | --- | --- |
| Authoritative workspace | Host the canonical repo and sanctioned code paths | Operator, control kernel, reasoning model, executor within task scope | Sanctioned code paths and bounded executor work within allowed paths | Only when written through governed paths and rules | Not applicable; this is the containing root, not a blanket promotion grant |
| Project-local governed paths | Hold canonical AIOffice artifacts and governed project files, normally under `projects/aioffice/` | Operator, control kernel, reasoning model, executor within task scope | Bounded task execution only when the path is declared and allowed | Yes, if the write is task-scoped and path-governed | Not applicable once correctly written under the declared governed path |
| Scratch workspace | Hold temporary notes, packets, staging output, experiments, or bundle assembly | Operator, control kernel, reasoning model, executor if the task assigns it | Bounded executor work and controlled tooling | No | Explicit review, explicit destination path, preserved provenance, and controlled apply are required |
| Imported donor/reference workspace | Hold donor materials, copied historical references, and external context admitted for inspection | Operator, control kernel, reasoning model, executor if needed for bounded comparison | Normally no writes to the source; only controlled ingestion into new AIOffice-owned paths | No | Must use an allowed import mode with provenance and explicit destination |
| Generated outputs / temporary workspace | Hold generated reports, exports, caches, and transient outputs | Operator, control kernel, reasoning model, executor if task-scoped | Task-bounded tools and executors | No by default | Same as scratch: explicit review and controlled promotion are required |
| Canonical state stores | Hold operational truth for registration, workflow state, or other sanctioned state models | Operator, control kernel, sanctioned store/control code; executor only if explicitly routed through sanctioned code | Sanctioned code paths only | Yes | No direct promotion from files; state changes must occur through sanctioned code |

Rules:
- Outputs from scratch, donor/reference, and generated temporary spaces are non-authoritative by default.
- Authoritative output requires both the correct destination path and the correct controlled write path.
- A rendered file, report, or board snapshot does not outrank canonical state if canonical state exists elsewhere.

## 4. Write Boundary Rules
- Canonical AIOffice work happens only under governed project paths in the authoritative root, normally `projects/aioffice/...`.
- Every governed task must declare one canonical `expected_artifact_path`.
- The declared artifact path is a write boundary, not a suggestion.
- Write access outside governed paths is forbidden unless a later explicit decision creates a sanctioned exception.
- Duplicate roots must never receive governed writes.
- Executor-produced scratch output is not authoritative by default.
- A file written under the authoritative root but outside the governed AIOffice path is not canonical AIOffice truth unless an explicit later rule says otherwise.
- Direct writes into canonical state stores are forbidden unless they occur through sanctioned code paths.

## 5. Import And Reuse Modes
These modes define the only allowed import patterns for future donor work.

### Reference only
- appropriate when:
  - the source is being inspected, compared, or quoted
  - no AIOffice-owned copy is needed yet
- required proof or logging:
  - source location must be named in task or decision context
  - reasoning about reuse must remain reviewable
- source remains authoritative:
  - no; it remains only a reference input
- provenance required:
  - yes

### Copy as historical reference
- appropriate when:
  - a frozen snapshot is needed for later audit or comparison
  - the copied material is not being treated as live AIOffice-owned logic
- required proof or logging:
  - copy action must record source path and reason for retention
  - copied material must be clearly marked as historical/reference-only
- source remains authoritative:
  - no for AIOffice; the copy is still non-canonical reference material
- provenance required:
  - yes

### Adapt under new AIOffice-owned path
- appropriate when:
  - donor material is being selectively reused and rewritten under AIOffice control
  - the resulting file becomes AIOffice-owned work rather than donor truth
- required proof or logging:
  - source provenance must be recorded
  - the new destination path must be explicit
  - the adaptation decision must be reviewable
- source remains authoritative:
  - no; the adapted result becomes authoritative only in its new governed AIOffice path
- provenance required:
  - yes

### Reject / defer
- appropriate when:
  - the donor material is unsafe, ambiguous, premature, or outside current scope
  - there is not enough proof to import or adapt it safely
- required proof or logging:
  - reason for rejection or deferral must be recorded in the appropriate governance context
- source remains authoritative:
  - no for AIOffice
- provenance required:
  - yes, at least enough to identify what was rejected or deferred

Rules:
- Import mode must be explicit; silent reuse is forbidden.
- Provenance must survive copying or adaptation.
- Donor material is never authoritative for AIOffice merely because it exists in the repo.

## 6. Canonical State Protection Rules
Canonical state requires stricter protection than ordinary files.

- `sessions/studio.db` is canonical operational state and must not be edited ad hoc.
- Canonical state changes must occur only through sanctioned code paths.
- Rendered project files, views, or boards do not outrank canonical state when canonical state is the declared source of truth.
- Scratch outputs, copied references, and generated reports must not self-promote into canonical truth.
- A one-off shell mutation, manual SQL upsert, or direct file edit into canonical state is outside policy unless it is performed by the sanctioned control path itself.
- If canonical state and a rendered artifact disagree, the discrepancy must be reconciled through controlled review, not resolved by whichever file is more convenient.

## 7. Executor Containment Rules
In this phase, Codex containment is strict.

- Codex is an executor, not an authority.
- Codex may work only inside bounded paths or scratch spaces assigned by task.
- Codex may return artifacts, diffs, and reports.
- Codex may not declare canonical acceptance.
- Codex may not decide promotion to authoritative state.
- Codex may not widen its own write scope because a nearby path looks related.
- Local repo instructions, helper scripts, and conventions are advisory unless enforced by the sanctioned control path.
- If the task boundary and the local environment conflict, the tighter explicit task boundary wins.

## 8. Promotion / Apply Rules
Non-authoritative outputs may become authoritative later only through explicit controlled promotion.

- Scratch work requires explicit review before any promotion.
- Acceptance requires controlled apply or promotion, not mere existence of a candidate output.
- Provenance must be preserved from source location to final authoritative destination.
- The destination path must be explicit before promotion occurs.
- Promotion without task or stage context is forbidden.
- Promotion must not overwrite unrelated authoritative files silently.
- Promotion may be rejected even if the scratch output looks useful.

Minimum promotion contract:
- source path is known
- destination path is known
- task or stage context is known
- reviewer or control path accepts the promotion
- provenance is retained

## 9. Path Declaration And Logging Rules
- Every governed artifact must have one canonical path.
- Path changes require explicit logging or decision capture.
- Import and adapt actions must preserve source provenance.
- No duplicate truth may persist across uncontrolled files.
- If a task needs supporting files in addition to its canonical artifact path, the supporting files must remain subordinate to the declared canonical artifact.
- If two paths appear to hold the same governed truth, one must be demoted, archived as reference, or removed through controlled decision.

## 10. Minimal Examples
### Valid scratch-to-authoritative promotion
- Task declares `expected_artifact_path: projects/aioffice/governance/CONTROL_KERNEL_PROTOCOL.md`.
- Executor drafts `projects/aioffice/_scratch/run-001/CONTROL_KERNEL_PROTOCOL.md`.
- Review confirms the draft is in scope and preserves provenance.
- Controlled apply promotes the reviewed content into `projects/aioffice/governance/CONTROL_KERNEL_PROTOCOL.md`.
- Result: valid because the scratch output did not self-promote and the destination path was explicit.

### Valid donor adaptation
- Donor source is read from a ProjectKanban reference file.
- AIOffice records the donor source path and adapts the material into `projects/aioffice/governance/<new-file>.md`.
- The new file is reviewed as AIOffice-owned content, not accepted as donor truth.
- Result: valid because provenance is preserved and authority moves only to the new governed AIOffice path.

### Invalid duplicate-root write
- Executor writes governed AIOffice content into `C:\Users\rodne\OneDrive\Documentos\_AIStudio_POC\projects\aioffice\...`.
- Result: invalid because the known duplicate root is non-authoritative and must never receive governed writes.

### Invalid direct canonical-state mutation
- Someone opens `sessions/studio.db` and edits rows manually to force a project or workflow state change.
- Result: invalid because canonical state must change only through sanctioned code paths, not ad hoc mutation.

## 11. Deferred Implementation Notes
The following are intentionally not implemented yet:
- no automated path-enforcement engine yet
- no sandbox or worktree manager yet
- no controlled apply engine yet
- no donor import workflow yet

This document still matters now because it defines the containment contract later code must enforce.
