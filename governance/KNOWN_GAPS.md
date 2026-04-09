# Known Gaps

This file records current known limitations discovered during the baseline assessment. It does not propose fixes.

## 1. Workspace-Root Authority Is Operational, Not Mechanical

- Gap: The repository enforces repo-relative control once the correct root is opened, but it does not mechanically prevent an operator from working in a duplicate folder outside the repo.
- Current impact: A second `_AIStudio_POC` tree exists under `OneDrive\\Documentos`, and its wiki content already diverges from the authoritative Desktop repo. That creates real drift risk.
- Why it is not being fixed in Phase 0: Solving cross-workspace authority requires operator-environment and repository-management changes, not baseline documentation.

## 2. Duplicate Mirror Contains Unique Content

- Gap: The duplicate `OneDrive\\Documentos\\_AIStudio_POC` tree is not a Git repo and does not contain runtime code, but it does contain content that is not byte-identical to the authoritative repo.
- Current impact:
  - `projects/program-kanban/governance/wiki/PROGRAM_KANBAN_STUDIO_OPERATIONS_WIKI.html` exists in both locations but hashes differ
  - `.codex/environments/environment.toml` exists only in the duplicate tree
- Why it is not being fixed in Phase 0: Reconciling or deleting duplicate content would require a separate controlled cleanup decision.

## 3. Disabled SDK Path Remains in Code as Dead/Blocked Path

- Gap: SDK-oriented branches still appear in runtime code even though `sdk` mode is fail-closed disabled.
- Current impact: The enforcement model is fail-closed, but code readers still encounter disabled `sdk` branches in files like `agents/orchestrator.py` and `scripts/worker.py`, which can make the runtime shape look broader than it actually is.
- Why it is not being fixed in Phase 0: Removing dead or disabled branches is refactor work, and Phase 0 is a control freeze only.

## 4. External Board Integration Is Conditional

- Gap: `kanban/board.py` can drive a GitHub Project only when project/token/repository configuration is present; otherwise it uses the local store-backed board.
- Current impact: The control model is enforced locally in the repository, but external board synchronization is environment-dependent.
- Why it is not being fixed in Phase 0: Moving to a different board authority model would be architectural change outside the baseline scope.

## 5. Baseline Git Freeze Scope Is Ambiguous Because the Working Tree Is Already Dirty

- Gap: The authoritative Desktop repo contains substantial pre-existing modified and untracked files before Phase 0 baseline docs are added.
- Current impact: A fail-closed Git freeze cannot safely assume which existing uncommitted files should be included in a Phase 0 baseline commit without an explicit staging decision.
- Why it is not being fixed in Phase 0: Selecting or excluding pre-existing dirty-tree content would be a repository triage decision, not a documentation-only baseline action.
