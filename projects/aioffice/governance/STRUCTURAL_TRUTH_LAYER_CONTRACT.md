# Structural Truth Layer Contract

## 1. Purpose
- Define a narrow structural truth layer for AIOffice that improves dependency mapping, change-impact analysis, QA traceability, and verification of LLM claims.
- Keep that layer explicitly derived, deterministic, and subordinate to the source systems it summarizes.
- Make the minimum contract clear before any graph-backed enforcement, hook discipline, or broader workflow expansion is considered.

## 2. Current Committed Reality This Contract Must Fit
- `M1` through `M12` are complete.
- `M13` is the active milestone as `Structural Truth Layer Baseline`.
- current readiness remains `ready only for narrow supervised bounded operation`.
- current live workflow proof still stops at `architect`.
- current control-surface maturity now exceeds current dependency, impact, and traceability maturity.
- the current sanctioned ordinary mutation path already fails closed on protected targets, but that protection is still intentionally conservative and not yet backed by a stronger deterministic structural map.

## 3. Definition
- The structural truth layer is a derived control and verification layer that records explicit relationships between:
  - requirements
  - decisions
  - tasks
  - protected surface classes
  - files
  - commands/functions
  - artifacts
  - tests
- It exists to support bounded review, impact analysis, coverage review, and stronger claim verification.
- It is not an authoritative replacement for the source systems that define AIOffice truth.

## 4. Source-Of-Truth Precedence
- Source systems remain authoritative for their own concern areas:
  - `projects/aioffice/execution/KANBAN.md` for accepted task and milestone status truth
  - `projects/aioffice/governance/DECISION_LOG.md` for ratified decision truth
  - `projects/aioffice/governance/ACTIVE_STATE.md` for accepted current-posture and anchor truth
  - governance contracts and review artifacts for their stated boundary law and committed evidence
  - code, commands/functions, and tests for implemented behavior and verification reality
- The structural truth layer is subordinate to those source systems and must point back to them explicitly.
- If the derived structural truth layer and a source system disagree, the source system wins and the derived layer must record the mismatch as a gap rather than silently override it.
- No conversational summary, freeform memory, or LLM inference may outrank the source systems or silently populate the derived layer as accepted truth.

## 5. Minimum Schema
- Required node classes:
  - `requirement`
  - `decision`
  - `task`
  - `protected_surface_class`
  - `file`
  - `command_or_function`
  - `artifact`
  - `test`
- Required node fields:
  - stable id
  - node class
  - human-readable label
  - source reference
- Required relationship classes:
  - `depends_on`
  - `ratified_by`
  - `defined_in`
  - `implemented_by`
  - `verified_by`
  - `exercised_by`
  - `classifies`
  - `touches`
- Required relationship fields:
  - `from`
  - `to`
  - relationship class
  - source reference

## 6. Deterministic Ingestion Rules
- Ingestion must run from an explicit committed input set rather than an open-ended file crawl.
- Extraction must rely on explicit ids, file paths, command/function names, task ids, decision ids, test names, and other directly grounded tokens already present in committed source systems.
- Ambiguous references must be recorded as unresolved gaps rather than guessed.
- Missing links, orphaned nodes, and unverified claims must be surfaced explicitly rather than silently suppressed.
- Output ordering and serialization must be stable so repeated generation over unchanged inputs is deterministic.
- The generator must fail closed on malformed authoritative input that prevents trustworthy derivation, or emit an explicit diagnostic artifact rather than inventing structure.

## 7. Sanctioned Enforcement And Review Points
- The structural truth layer may be used in sanctioned workflows for:
  - protected-surface impact review
  - bounded change-impact analysis
  - QA traceability and linked-test review
  - bounded rehearsal planning and evidence review
  - stronger verification of LLM claims against committed repo truth
- Later hook or automation use is allowed only if a later slice explicitly ratifies it.
- The layer must not independently mutate accepted truth or approve work by itself.

## 8. Gold-Standard Maturity Rubric
- Level 0 - absent:
  - no derived structural truth layer exists
- Level 1 - seeded:
  - the contract, schema, and source-of-truth rules are explicit, but generation and review use are still mostly manual
- Level 2 - baseline:
  - deterministic generation exists for the current control kernel, protected surfaces, and linked tests
  - missing and orphaned links are surfaced explicitly
- Level 3 - review-usable:
  - at least one bounded review or rehearsal path uses the derived artifact for impact, coverage, and protected-surface reasoning
  - reviewers can trace claims back to explicit source references
- Gold standard:
  - sanctioned review and control workflows consistently require artifact-backed impact, coverage, and classification checks before sensitive control or protected-surface changes are treated as adequately reviewed
  - the layer remains subordinate to source systems and does not become an independent authority surface

## 9. Explicit Non-Claims
- This contract does not create a second silent truth surface.
- This contract does not authorize graph database adoption by itself.
- This contract does not authorize hook or automation code by itself.
- This contract does not authorize design-lane implementation by itself.
- This contract does not upgrade readiness.
- This contract does not widen live workflow proof beyond `architect`.
- This contract does not authorize later-stage workflow, semi-autonomous operation, or multi-lane breadth.
