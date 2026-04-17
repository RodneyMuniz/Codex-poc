# Repo Milestone Loop Discipline

## 1. Purpose
- Define the narrow operating law for repo-governed milestone publication, verification, reporting, and bounded helper or hook use.
- Address the operational failure that was exposed in recent passes:
  - publication and verification discipline was weaker than the repo itself
  - local completion claims drifted ahead of authoritative remote GitHub truth
- Keep this slice narrower and safer than resuming design-lane breadth immediately:
  - harden the already accepted repo-governed review loop first
  - do not widen workflow breadth, runtime surface area, or readiness claims

## 2. Current Committed Reality This Contract Must Fit
- GitHub is the external review surface for published commit visibility on the authoritative branch.
- The local repo is the implementation workspace until work is staged, committed, pushed, and remotely verified.
- The recent exposed weakness was publication and verification discipline rather than repo corruption.
- Governance and planning surfaces remain the accepted law for task, milestone, and posture truth.
- Current readiness remains `ready only for narrow supervised bounded operation`.
- Current live workflow proof still stops at `architect`.

## 3. Source-Of-Truth Precedence
- Authority is split by concern area and must be resolved fail-closed rather than by narration:
  - governance and planning surfaces are authoritative for accepted milestone, task, and posture truth
  - code and tests are authoritative for implemented behavior and verification reality
  - local working state is draft implementation state only
  - local committed state is candidate publication state only
  - remote branch head is authoritative for what the target branch currently publishes
  - remote commit visibility on GitHub is authoritative for whether a reported SHA is externally reviewable on the accepted repo surface
- Accepted repo truth for review and closeout exists only when:
  - the relevant governance or planning claim is explicit in committed repo surfaces
  - the reported commit is visible on GitHub
  - the authoritative branch head and the reported SHA agree for the claimed completion state
- If local state, remote state, GitHub visibility, governance surfaces, or report language disagree, the pass must fail closed rather than silently choosing a convenient truth surface.

## 4. Mandatory Finish Sequence
- Every future milestone-loop pass must use this fixed finish routine:
  - implement or reconcile
  - run tests
  - commit
  - push
  - verify remote SHA
  - report
- Stopping before remote SHA verification is not completion.
- If remote verification fails, the only valid conclusion for that pass is `blocked`.

## 5. Completion Law
- Local commit existence is not completion.
- Local clean worktree state is not completion.
- Codex-reported push success is not completion by itself.
- Completion requires:
  - an exact reported local `HEAD` SHA
  - the same exact SHA at the authoritative remote branch head, or an explicitly verified published SHA for the reported pass
  - GitHub-visible remote evidence for the reported SHA
  - a report that keeps local state, remote state, and accepted repo truth separate
- No task, milestone, or review closeout may be treated as complete from local-only evidence.

## 6. Required Report Structure
- Every future Codex completion report must include at minimum:
  - decision
  - pass type
  - local `HEAD` SHA
  - remote `HEAD` SHA
  - exact files changed
  - exact tests run
  - authoritative repo truth confirmation
- The report must keep local status and remote status in separate sections.
- The report must state whether the reported change is present in authoritative repo truth.
- The report must not blur implementation-state observations and accepted closeout claims into one statement.

## 7. Pass Types
- `implementation commit`
  - introduces the primary artifact or narrow code or governance change for the current task
  - does not by itself close the task until remote verification succeeds
- `closeout commit`
  - reconciles authoritative planning or governance surfaces after completed work is already supported by committed evidence
  - may update `KANBAN.md`, `ACTIVE_STATE.md`, derived artifacts, or closely related review surfaces when the task warrants it
- `push-only publication pass`
  - publishes an already existing local commit without adding new content
  - is allowed only when the pass is strictly about making an existing local SHA visible on GitHub and verifying that exact SHA
- No pass type may:
  - auto-ratify a milestone
  - skip remote verification
  - convert local-only evidence into accepted repo truth

## 8. Fail-Closed Mismatch Rules
- If local SHA and remote SHA differ at report time, the pass is `blocked`.
- If the reported SHA does not resolve remotely on GitHub, the pass is `blocked`.
- If the authoritative branch head and the reported SHA disagree for the claimed completion state, the pass is `blocked`.
- If required remote evidence is missing, stale, or not independently verified, the pass is `blocked`.
- If local and remote status are blurred together in the report, the report is invalid and the pass must fail closed rather than being treated as complete.
- When blocked, the report must expose the mismatch explicitly rather than narrating around it.

## 9. Bounded Automation And Hook Discipline Law
- Later helpers or hooks may operate only within these narrow bounds:
  - read local branch, worktree, and `HEAD` state
  - read the authoritative remote branch head
  - query GitHub-visible commit truth for a reported SHA
  - compare those surfaces deterministically
  - emit explicit diagnostics, block conditions, or report scaffolding
- Later helpers or hooks may not:
  - create a second truth surface
  - outrank GitHub, governance, planning surfaces, code, or tests
  - auto-ratify tasks, reviews, or milestones
  - auto-upgrade readiness or workflow proof
  - replace human review of accepted repo truth
  - silently mutate governance or planning surfaces
  - widen into generic CI or CD architecture by default
- Helper or hook output is subordinate verification support only.
- A helper or hook may assist a milestone-loop pass, but it may not decide accepted truth on its own.

## 10. Explicit Non-Claims
- This contract does not upgrade readiness.
- This contract does not widen live workflow proof beyond `architect`.
- This contract does not authorize broad automation rollout.
- This contract does not authorize design-lane implementation.
- This contract does not authorize `AIO-069` implementation by itself.
- This contract does not claim that helper or hook outputs outrank GitHub or governance source systems.
- This contract does not create a second silent truth surface.
