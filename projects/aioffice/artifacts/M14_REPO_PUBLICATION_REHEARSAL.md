# M14 Repo Publication Rehearsal

## 1. Rehearsal Purpose
- exercise one bounded repo-governed milestone publication and verification path against the authoritative branch
- test the committed governance law and the committed helper together without widening into generic CI/CD or broad automation
- keep the rehearsal bounded:
  - use read-only helper invocations only
  - use one aligned published-truth scenario and one blocked missing-remote-evidence scenario
  - do not treat helper output as an authority surface
  - do not mutate repo truth beyond the evidence artifact and narrow closeout surfaces for `AIO-070`

## 2. Inputs Used
- authoritative branch:
  - `feature/aioffice-m13-design-lane-operationalization`
- authoritative published SHA observed during rehearsal:
  - local `HEAD`: `ff71704e7fcd01644a5849649f140c518a7ce3b6`
  - remote branch head: `ff71704e7fcd01644a5849649f140c518a7ce3b6`
  - GitHub-visible reported SHA relied on for the matched scenario: `ff71704e7fcd01644a5849649f140c518a7ce3b6`
- helper commands executed:
  - `py -3 scripts/verify_repo_publication.py --target-branch feature/aioffice-m13-design-lane-operationalization`
  - `py -3 scripts/verify_repo_publication.py --target-branch feature/aioffice-m13-design-lane-operationalization --reported-sha 0000000000000000000000000000000000000000`
- reported SHAs used:
  - `ff71704e7fcd01644a5849649f140c518a7ce3b6`
  - `0000000000000000000000000000000000000000`
- committed governance and review surfaces used:
  - `projects/aioffice/governance/REPO_MILESTONE_LOOP_DISCIPLINE.md`
  - `projects/aioffice/execution/KANBAN.md`
  - `projects/aioffice/governance/ACTIVE_STATE.md`
  - `projects/aioffice/governance/DECISION_LOG.md`
  - `projects/aioffice/governance/M13_STRUCTURAL_TRUTH_REVIEW.md`
- committed helper and focused test surfaces used:
  - `scripts/verify_repo_publication.py`
  - `tests/test_verify_repo_publication.py`

## 3. Scenario 1: Matched Published Truth
- command:
  - `py -3 scripts/verify_repo_publication.py --target-branch feature/aioffice-m13-design-lane-operationalization`
- observed output:

```json
{
  "branch_name": "feature/aioffice-m13-design-lane-operationalization",
  "local_head_sha": "ff71704e7fcd01644a5849649f140c518a7ce3b6",
  "remote_head_sha": "ff71704e7fcd01644a5849649f140c518a7ce3b6",
  "reported_sha": "ff71704e7fcd01644a5849649f140c518a7ce3b6",
  "reported_sha_visible_remotely": true,
  "worktree_clean": true,
  "status": "ok",
  "reason": "reported SHA is visible remotely and local and remote heads match"
}
```

- output summary:
  - branch, local `HEAD`, remote branch head, and reported SHA all matched `ff71704e7fcd01644a5849649f140c518a7ce3b6`
  - the reported SHA was visible remotely on the authoritative branch
  - the worktree was clean at the time of the rehearsal run
  - the helper returned `status: ok` exactly where the governance law says completion-state publication evidence may proceed

## 4. Scenario 2: Fail-Closed Missing Publication Truth
- command:
  - `py -3 scripts/verify_repo_publication.py --target-branch feature/aioffice-m13-design-lane-operationalization --reported-sha 0000000000000000000000000000000000000000`
- observed output:

```json
{
  "branch_name": "feature/aioffice-m13-design-lane-operationalization",
  "local_head_sha": "ff71704e7fcd01644a5849649f140c518a7ce3b6",
  "remote_head_sha": "ff71704e7fcd01644a5849649f140c518a7ce3b6",
  "reported_sha": "0000000000000000000000000000000000000000",
  "reported_sha_visible_remotely": false,
  "worktree_clean": true,
  "status": "blocked_missing_remote_commit",
  "reason": "reported SHA '0000000000000000000000000000000000000000' is not visible on remote branch 'origin/feature/aioffice-m13-design-lane-operationalization'"
}
```

- output summary:
  - local and remote branch truth still matched the authoritative published SHA
  - the deliberately reported SHA was not remotely visible on the authoritative branch
  - the helper returned `status: blocked_missing_remote_commit`
  - this is the expected fail-closed path when remote commit evidence is missing

## 5. What The Rehearsal Proved
- one bounded rehearsal can exercise the committed repo milestone-loop discipline directly against authoritative branch truth
- the committed helper reports exact branch name, local `HEAD`, remote branch head, reported SHA, remote visibility, worktree cleanliness, status, and reason in machine-readable form
- the committed helper returns `ok` only when the reported SHA is visible remotely and local and remote heads match on the authoritative branch
- the committed helper fails closed on missing remote commit evidence rather than narrating around absent publication proof
- the helper remains a subordinate diagnostic surface:
  - it observed Git truth
  - it did not replace GitHub, governance, planning, code, or tests as authority surfaces

## 6. What The Rehearsal Did Not Prove
- this rehearsal did not exercise a live local-versus-remote branch-head mismatch against the authoritative branch; that path remains code-and-test evidence only in this slice
- this rehearsal did not prove automatic task or milestone closeout
- this rehearsal did not prove broad hook rollout, broad automation rollout, or generic CI/CD orchestration
- this rehearsal did not prove readiness beyond `ready only for narrow supervised bounded operation`
- this rehearsal did not prove workflow breadth beyond `architect`
- this rehearsal did not prove that helper output outranks GitHub or governance source systems

## 7. Non-Claims
- no readiness upgrade is claimed
- no workflow-proof expansion beyond `architect` is claimed
- no broad automation rollout is claimed
- no milestone auto-ratification is claimed
- no claim is made that helper output outranks GitHub, governance, planning surfaces, code, or tests
- no claim is made that `AIO-071` is closed or that any post-`M14` milestone is ratified
