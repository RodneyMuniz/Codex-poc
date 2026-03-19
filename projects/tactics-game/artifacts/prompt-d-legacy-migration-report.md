# Prompt D Legacy Migration & Recovery Plan

## Scope

This report evaluates the two legacy sources named in the prompt:

- prior kanban board website at `C:\Users\rodne\OneDrive\Documentos\_Codex Projects\Program Kanban`
- prior TacticsGame POC at `C:\Users\rodne\OneDrive\Documentos\_Codex Projects\TacticsGame`

The current repository remains the compliance target. This report is intentionally non-destructive: it proposes an archive-first migration path so the original legacy folders remain untouched and recoverable.

## Recovery-First Migration Rules

1. Do not edit the original legacy folders in place.
2. Import by copy, not by move.
3. Exclude generated runtime folders on first import.
4. Commit after each migration slice so rollback is one Git step away.
5. Keep any ambiguous or low-value artifact in `archive/` until it proves useful.
6. Treat the new repo's canonical structure as authoritative:
   - studio-wide governance in `governance/`
   - project-specific governance in `projects/tactics-game/governance/`
   - active project execution material in `projects/tactics-game/execution/`
   - scenario outputs in `projects/tactics-game/artifacts/`

## Legacy Source Summary

### 1. Program Kanban

Observed modules and support files:

- `app.js`
  - browser-side operator dashboard logic with board rendering and local state
- `server.mjs`
  - lightweight Node HTTP server that parses markdown artifacts and exposes snapshot-style data
- `index.html`, `styles.css`, `package.json`
  - minimal static frontend shell
- documentation set
  - `PROJECT.md`, `HANDOFF.md`, `MILESTONES.md`, `MILESTONE_PRIORITY_CONTRACT.md`, design and review packets
- runtime files
  - `dashboard-err.log`, `dashboard-out.log`
- historical board content
  - `KANBAN.md`

Assessment:

- This is not the new source of truth for task state.
- It is still valuable as a prototype operator wall and as a UI/UX reference for a future dashboard over SQLite and logs.

### 2. Legacy TacticsGame POC

Observed modules and support files:

- application code
  - `src/main.tsx`
  - `src/styles.css`
  - `src/ui/react/App.tsx`
  - `src/app/presentation/*`
- game engine
  - `src/engine/actions/*`
  - `src/engine/data/*`
  - `src/engine/model/*`
  - `src/engine/queries/*`
  - `src/engine/setup/*`
  - `src/engine/systems/*`
- tests
  - `src/engine/actions/battleActions.test.ts`
  - `src/engine/setup/createSandboxBattle.test.ts`
- configuration
  - `package.json`, `package-lock.json`, `vite.config.ts`, `tsconfig.json`, `tsconfig.app.json`, `index.html`, `.gitignore`
- governance and design docs
  - `ARCHITECTURE.md`, `DATA_MODEL.md`, `VISION.md`, `WORKFLOW_VISION.md`, `ARTIFACT_STRUCTURE.md`, `DECISION_LOG.md`, `DECISIONS.md`, `UX_PLAYER_EXPERIENCE.md`, `ASSETS.md`, and multiple feature packets
- execution docs
  - `KANBAN.md`, `HANDOFF.md`, `IMPLEMENTATION_BRIEF.md`, `PROJECT_BRAIN.md`, `MILESTONES.md`, milestone dispatch packets
- generated/runtime artifacts
  - `dist/`, `node_modules/`, `devserver.out.log`, `devserver.err.log`, `tsconfig.app.tsbuildinfo`

Assessment:

- The POC contains substantial reusable design work and engine code.
- The documentation set is rich but mixed; it needs classification and selective normalization before it becomes active again.
- The generated/runtime artifacts should not be migrated.

## Classification Matrix

| Source Artifact or Group | Decision | Why | Proposed Destination |
| --- | --- | --- | --- |
| `Program Kanban/app.js` | adapt | Useful operator-wall UI logic, but it currently assumes markdown-derived board state rather than SQLite-backed runtime state. | `scripts/operator_wall/app.js` after rewriting its data source |
| `Program Kanban/server.mjs` | adapt | Good starting point for a lightweight operator-wall server, but its parser must be replaced with a SQLite or CLI-backed session API. | `scripts/operator_wall/server.mjs` |
| `Program Kanban/index.html` and `styles.css` | adapt | Reusable shell and visual ideas for an operator wall. | `scripts/operator_wall/` |
| `Program Kanban/package.json` | adapt | Useful only if the operator wall is revived in Node. | `scripts/operator_wall/package.json` |
| `Program Kanban/PROJECT.md`, `HANDOFF.md`, `MILESTONES.md`, review packets | adapt selectively | Some product intent and wall-design decisions are useful, but they are not canonical in their current form. | Active insights into `governance/DECISION_LOG.md` or `scripts/operator_wall/README.md`; remainder archived under `archive/legacy-imports/program-kanban/docs/` |
| `Program Kanban/KANBAN.md` | discard as active source, archive as reference | The new framework uses SQLite as source of truth, so the markdown board should not be revived as canonical state. | `archive/legacy-imports/program-kanban/KANBAN.md` |
| `Program Kanban/*.log` | discard | Generated runtime output with no lasting migration value. | Do not import |
| `TacticsGame/src/engine/model/*` | reuse | Core domain types and battle state structures align with the TacticsGame brief and are the highest-value reusable code. | `projects/tactics-game/execution/game-client/src/engine/model/` |
| `TacticsGame/src/engine/data/*` | reuse | Seed content and rules defaults are directly relevant to the tactics sandbox. | `projects/tactics-game/execution/game-client/src/engine/data/` |
| `TacticsGame/src/engine/setup/*` | reuse | Battle creation and validation logic are already aligned with the documented architecture. | `projects/tactics-game/execution/game-client/src/engine/setup/` |
| `TacticsGame/src/engine/queries/*` | reuse | Query logic is core engine value and fits the engine-first design. | `projects/tactics-game/execution/game-client/src/engine/queries/` |
| `TacticsGame/src/engine/actions/*` and `src/engine/systems/*` | adapt | Strong reusable logic, but should be checked against the newer governance rules and testing expectations before activation. | `projects/tactics-game/execution/game-client/src/engine/actions/` and `projects/tactics-game/execution/game-client/src/engine/systems/` |
| `TacticsGame` engine tests | reuse | Existing tests provide immediate regression protection for migrated engine code. | `projects/tactics-game/execution/game-client/src/**/*.test.ts` |
| `TacticsGame/src/app/presentation/*`, `src/ui/react/App.tsx`, `src/main.tsx`, `src/styles.css` | adapt | Good UI shell and presentation logic, but they should be rewired to the canonical project structure and refreshed after code migration. | `projects/tactics-game/execution/game-client/src/` |
| `TacticsGame/package.json`, `package-lock.json`, `vite.config.ts`, `tsconfig*.json`, `index.html`, `.gitignore` | adapt | Required to run the migrated TS client, but should be slimmed down and aligned with the new repo. | `projects/tactics-game/execution/game-client/` |
| `TacticsGame/ARCHITECTURE.md` and `DATA_MODEL.md` | adapt | High-value design docs that should become active project governance/reference documents again. | `projects/tactics-game/governance/ARCHITECTURE.md` and `projects/tactics-game/governance/DATA_MODEL.md` |
| `TacticsGame/VISION.md`, `WORKFLOW_VISION.md`, `UX_PLAYER_EXPERIENCE.md`, `ASSETS.md` | adapt selectively | Useful project-facing design intent, but some content overlaps with current governance and needs consolidation. | `projects/tactics-game/governance/` with archived superseded copies in `archive/legacy-imports/tacticsgame/docs/` |
| `TacticsGame/DECISION_LOG.md` | adapt | Valuable project-specific decisions should survive, but they belong in project governance, not in the studio-wide root decision log. | `projects/tactics-game/governance/DECISION_LOG.md` |
| `TacticsGame/DECISIONS.md` | discard after merge | Already marked legacy by the old project and superseded by `DECISION_LOG.md`. | `archive/legacy-imports/tacticsgame/DECISIONS.md` only |
| `TacticsGame/ARTIFACT_STRUCTURE.md` | adapt | Strong migration guidance that already distinguishes canonical from legacy artifacts. | `projects/tactics-game/governance/ARTIFACT_STRUCTURE.md` |
| `TacticsGame/KANBAN.md`, `PROJECT_BRAIN.md`, `HANDOFF.md`, `IMPLEMENTATION_BRIEF.md`, milestone and packet docs | adapt selectively | Useful for backlog recovery and feature decomposition, but many items are stale or mixed-concern and should not become canonical verbatim. | Active work items into `projects/tactics-game/execution/`; archival copies into `archive/legacy-imports/tacticsgame/docs/` |
| `TacticsGame/dist/`, `node_modules/`, logs, `tsconfig.app.tsbuildinfo` | discard | Generated or environment-specific artifacts that add noise and risk. | Do not import |

## Recommended Destination Layout

Short-term target layout for migrated legacy assets:

- `archive/legacy-imports/program-kanban/`
  - read-only imported snapshot, excluding logs if desired
- `archive/legacy-imports/tacticsgame/`
  - read-only imported snapshot, excluding `dist/`, `node_modules/`, and other generated output
- `projects/tactics-game/governance/`
  - normalized project docs such as `PROJECT_BRIEF.md`, `DECISION_LOG.md`, `ARCHITECTURE.md`, `DATA_MODEL.md`, `ARTIFACT_STRUCTURE.md`
- `projects/tactics-game/execution/game-client/`
  - adapted TypeScript/React/Vite game client
- `projects/tactics-game/execution/`
  - current rendered kanban plus any normalized active work packets
- `scripts/operator_wall/`
  - any revived dashboard code adapted from Program Kanban

## Ordered Migration Plan

1. Create a migration checkpoint.
   - Commit the current repo before any import work.

2. Record an import manifest.
   - Capture source paths, excluded folders, and a file inventory for both legacy roots.
   - This gives us a recovery baseline without touching the originals.

3. Copy legacy sources into `archive/legacy-imports/`.
   - Exclude `node_modules/`, `dist/`, logs, and other generated artifacts on first import.
   - Keep copied snapshots read-only by convention.

4. Normalize project governance first.
   - Create `projects/tactics-game/governance/DECISION_LOG.md`.
   - Merge useful entries from the legacy TacticsGame decision log.
   - Adapt `ARCHITECTURE.md`, `DATA_MODEL.md`, and `ARTIFACT_STRUCTURE.md` into the new project-governance folder.
   - Keep studio-level decisions in `governance/DECISION_LOG.md` and move game-only decisions to the project folder.

5. Recover actionable execution docs second.
   - Review legacy `KANBAN.md`, `IMPLEMENTATION_BRIEF.md`, milestone packets, and `PROJECT_BRAIN.md`.
   - Convert active items into current framework tasks rather than copying the old board verbatim.
   - Archive stale or superseded packets under `archive/legacy-imports/tacticsgame/docs/`.

6. Stage the game client code into `projects/tactics-game/execution/game-client/`.
   - Import engine modules first.
   - Import tests next.
   - Import UI and presentation code last.
   - Keep each slice on a separate commit.

7. Validate the migrated client before any refactor.
   - Install dependencies in the staged client folder.
   - Run the existing tests and a build.
   - Fix only portability issues required to get the baseline running.

8. Refactor migrated code to fit the new framework.
   - Keep the orchestrator and the game client decoupled.
   - Expose build, test, and diff actions through the skill system instead of ad hoc shell habits.
   - Add project-specific skills later for TS test runs, build validation, and artifact capture if the game client becomes active work.

9. Adapt the Program Kanban code into an operator wall only after the session model is stable.
   - Replace markdown parsing with a read-only view over `sessions/studio.db`, CLI JSON, or a thin Python API.
   - Keep the old markdown board as historical reference only.

10. Update links and references.
   - Rewrite docs to point to the canonical new paths.
   - Add compatibility notes where old filenames such as `DECISIONS.md` are mentioned.

11. Archive the remainder.
   - Anything not chosen for active reuse or adaptation stays under `archive/legacy-imports/`.
   - Do not delete the original external folders; they remain the final recovery source.

## Refactor Notes For Skill-System Alignment

- Add project-specific skills only after the TypeScript client is staged.
- Highest-value new skills:
  - `run_game_client_tests`
  - `run_game_client_build`
  - `list_project_artifacts`
  - `apply_text_patch_to_artifact` or another restricted editing tool
- Keep these skills scoped to the migrated `game-client` folder so they do not interfere with the Python orchestration layer.

## Documentation Update Strategy

- Studio framework rules stay in `governance/`.
- TacticsGame-specific architecture, data model, and decisions move under `projects/tactics-game/governance/`.
- Execution packets that still drive active implementation move under `projects/tactics-game/execution/`.
- Stale packets and historical snapshots stay archived.
- Any imported markdown should be link-normalized after relocation so references do not silently break.

## Quick Wins Codex Can Automate

1. `scripts/import_legacy_manifest.py`
   - Generate a file inventory and exclusion report for both legacy roots.

2. `scripts/merge_decision_logs.py`
   - Convert legacy `DECISIONS.md` and `DECISION_LOG.md` entries into the canonical project decision-log format.

3. `scripts/rewrite_markdown_links.py`
   - Update old relative links after files move into `projects/tactics-game/governance/` and `projects/tactics-game/execution/`.

4. `scripts/import_legacy_tasks.py`
   - Parse legacy TacticsGame markdown board items and emit current CLI task-creation commands or direct SQLite inserts.

5. `scripts/stage_game_client.ps1`
   - Copy only reusable code and config from the legacy TacticsGame source while excluding generated directories.

## Recommended Next Developer Tasks

1. Create a Git checkpoint and import manifest.
2. Copy both legacy roots into `archive/legacy-imports/` with exclusions.
3. Migrate and normalize project governance docs.
4. Stage the TacticsGame engine and tests into `projects/tactics-game/execution/game-client/`.
5. Validate the staged client with build and test commands.
6. Convert active legacy work items into the current SQLite-backed task queue.
7. Revisit the Program Kanban dashboard only after the queue and telemetry models are stabilized.
