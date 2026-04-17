# AIOffice Decision Log

## Decisions

### AIO-D-001
- date: 2026-04-13
- status: seeded
- decision: the authoritative repository root for AIOffice bootstrap is `C:\Users\rodne\OneDrive\Desktop\_AIStudio_POC`.
- rationale: the duplicate Documents root is explicitly non-authoritative for this project.

### AIO-D-002
- date: 2026-04-13
- status: seeded
- decision: the bootstrap scope is governance-only and excludes UI, old orchestration changes, and worker execution changes.
- rationale: the founding pass needs clarity without disturbing existing runtime behavior.

### AIO-D-003
- date: 2026-04-13
- status: seeded
- decision: project registration may use the minimal store/read-model path, but backlog planning stays in project-local artifacts until a later sync decision is approved.
- rationale: this keeps AIOffice visible as a project without binding the founding backlog to the current runtime planning path.

### AIO-D-004
- date: 2026-04-13
- status: seeded
- decision: AIOffice project registration must occur through sanctioned code, using the deterministic store helper surfaced by the CLI project-registration path rather than ad hoc SQL.
- rationale: the sanctioned path is idempotent, testable, and avoids unrelated `KANBAN.md` rewrites during registration.

### AIO-D-005
- date: 2026-04-13
- status: seeded
- decision: canonical import of `AIO-001` through `AIO-007` remains deferred because the current `tasks` schema does not preserve a durable `dependencies` field safely.
- rationale: AIOffice backlog truth must not be degraded by importing work items into canonical task rows that cannot store one of the required durable fields.

### AIO-D-006
- date: 2026-04-13
- status: reviewed
- decision: the observed defect was that bundled `KANBAN.md` normalization recorded end states that bypassed the declared lifecycle transitions. AIOffice will treat `KANBAN.md` as authoritative current-state ledger truth and allow condensed end-of-bundle state recording only for operator-authorized bounded bundles with explicit scope, dependency handling, reviewable execution order, required artifacts, and preserved provenance.
- rationale: this policy keeps current backlog truth aligned with accepted board law without inventing a second authoritative surface. It is acceptable in the current model because `KANBAN.md` is a current-state ledger, not a sanctioned event-history log. What remains deferred is a future canonical state or event model that can preserve both authoritative snapshot truth and first-class transition history without requiring condensed recording exceptions.

### AIO-D-007
- date: 2026-04-15
- status: reviewed
- decision: the AIOffice documentation baseline is re-ratified as follows:
  - current status truth comes from the local `execution/KANBAN.md`
  - the original `M1` through `M10` roadmap remains the strategic backbone unless accepted execution has already diverged
  - the updated AIOffice product spec is accepted as the constitutional product baseline and is promoted through `governance/VISION.md`
  - original `M3` operator-design work is explicitly deferred rather than silently collapsed
  - control-kernel, protocol, persistence, inspection, and supervised-control work are accepted as having been pulled forward into current `M3` through `M5`
  - original `M6` through `M10` are preserved with refinements rather than replaced
  - current accepted execution truth is `M1` through `M4` complete and `M5` partial, with `AIO-029`, `AIO-030`, and `AIO-031` complete and `AIO-032`, `AIO-033`, and `AIO-034` remaining
- rationale:
  - the local KANBAN now carries the accepted operational truth and must outrank stale roadmap wording for status claims
  - the strategic backbone still matters because re-baselining is a reconciliation pass, not permission to invent a new roadmap
  - the constitutional product baseline needs a stable home that is separate from run logs and backlog movement
  - approved divergence must be explicit so later readers do not confuse deferral with deletion or mistake pulled-forward control work for original sequencing
- thin-control-kernel ADR treatment:
  - the thin-control-kernel framing is absorbed into this re-baseline across `PROJECT.md`, `VISION.md`, and this decision entry
  - this entry does not claim that a separate standalone ADR artifact has been completed
  - if a dedicated ADR is still desired later, it remains outstanding and must be tracked explicitly rather than implied here

### AIO-D-008
- date: 2026-04-15
- status: reviewed
- decision: after `M5` closeout, the next operational slice is ratified as a narrow post-`M5` proof slice focused on supervised proof of the separate `apply` branch and bounded proof of same-workspace repeated-run or shared-store contention behavior. Later-stage workflow expansion remains deferred as an operational next step until those current-boundary gaps are reviewed explicitly.
- rationale:
  - the accepted `M5` readiness review identified the separate `apply` branch and same-workspace or shared-store behavior as explicit missing proof inside the current sanctioned boundary
  - the accepted readiness posture remains `ready only for narrow supervised bounded operation`, not ready for a bounded supervised semi-autonomous cycle
  - proving unresolved behavior inside the already implemented boundary is safer and more reviewable than widening the workflow claim into later stages at the same time
  - this ratifies `M6` as a planned narrow proof slice, not as proof that later-stage workflow, unattended operation, or broader semi-autonomous readiness has been achieved

### AIO-D-009
- date: 2026-04-15
- status: reviewed
- decision: before additional `M6` proof rehearsals, AIOffice will establish a narrow GitHub-visible remote review anchor for the current accepted state using the current working branch, the accepted post-`M5` baseline tag, and a project-local `governance/ACTIVE_STATE.md` file. GitHub is the external review surface for audit; the local repository remains the implementation workspace.
- rationale:
  - current `M6` proof work benefits from an external review anchor that is stronger than local-only state when later audit or review is needed
  - this is a narrow proof-auditability step inside `M6`, not a separate infrastructure initiative
  - the task does not change the accepted readiness posture and does not imply later-stage workflow proof, autonomy readiness, or real multi-agent maturity
  - grounding later `M6` artifacts on pushed branch, tag, and file evidence makes future proof review more conservative and reviewable

### AIO-D-010
- date: 2026-04-16
- status: reviewed
- decision: after `AIO-052` closed `M10`, the authoritative review anchor is re-anchored from the `M9` closeout refs to dedicated `M10` closeout refs:
  - checkpoint tag: `aioffice-m10-closeout-2026-04-16`
  - snapshot branch: `snapshot/aioffice-m10-closeout-2026-04-16`
  - working branch remains: `feature/aioffice-m10-change-governance-hardening`
- rationale:
  - `KANBAN.md` and `ACTIVE_STATE.md` now both record `M10` as complete, so the externally reviewable checkpoint/snapshot anchor should match that accepted closeout boundary
  - this is checkpoint and review-anchor hygiene only
  - the historical `M9` tag and `M9` snapshot branch remain preserved as prior accepted anchors and are not rewritten, moved, or deleted
  - this decision does not imply any readiness change, workflow-proof expansion, UI expansion, autonomy expansion, or later-stage workflow claim

### AIO-D-011
- date: 2026-04-16
- status: reviewed
- decision: after `M10` closeout, the next conservative slice is recovery-first, and `M11 - Recovery Discipline Operationalization` is ratified as the active milestone.
- rationale:
  - recovery discipline is chosen first because `RECOVERY_AND_ROLLBACK_CONTRACT.md` is defined, but no committed artifact yet proves automated snapshot/version/restore/rollback discipline in practice and no restore or rollback rehearsal has been executed
  - protected core product/state surfaces enforcement remains the next likely priority after recovery, but it is not ratified or authorized for implementation in this decision
  - workflow breadth beyond `architect` remains important, but it should begin later with one lane only, starting with `design`
  - this decision does not authorize readiness upgrades, UI implementation, later-stage workflow proof, serious multi-agent parallelism, protected-surface enforcement implementation yet, or design-lane implementation yet

### AIO-D-012
- date: 2026-04-16
- status: reviewed
- decision: after the post-`M11` recovery review, `M11 - Recovery Discipline Operationalization` is complete and `M12 - Protected Core Surfaces Enforcement` is ratified as the next active conservative slice.
- rationale:
  - committed `M11` evidence now proves checkpoint naming and snapshot packaging are more real, recovery preflight is fail-closed, backup/restore/rollback routines are materially real on the sanctioned store path, and one bounded restore and rollback rehearsal was executed in a disposable target without changing accepted authoritative truth
  - protected core product/state surfaces enforcement now outranks workflow breadth and UI work because ordinary mutation paths still need code-level fail-closed blocking on core accepted-truth surfaces before broader writable or review-sensitive surface area is added
  - workflow breadth beyond `architect` remains important, but it should still begin later with one lane only, starting with `design`, after protected-surface enforcement is reviewed
  - this decision does not authorize readiness upgrades, later-stage workflow proof, design-lane implementation yet, UI implementation, or serious multi-agent parallelism

### AIO-D-013
- date: 2026-04-16
- status: reviewed
- decision: after the post-`M12` protected-surface enforcement review, `M12 - Protected Core Surfaces Enforcement` is complete and `M13 - Design Lane Operationalization` is ratified as the next active conservative slice.
- rationale:
  - committed `M12` evidence now proves protected core surface classes are explicit in governance, the current sanctioned ordinary mutation path fails closed on protected targets, and one bounded blocked-attempt rehearsal was executed without changing accepted truth or advancing the exercised bundle beyond `pending_review`
  - design-lane operationalization now outranks UI work because current repo truth already has the conservative protected-surface boundary it needed first, while broader UI work still does not reduce the next highest-value gap in bounded workflow breadth
  - design-lane operationalization also outranks broader workflow expansion because breadth should still begin with one lane only, and `design` remains the accepted recommended first lane rather than attempting multi-lane expansion all at once
  - this decision does not authorize readiness upgrades, later-stage workflow proof beyond what the `M13` slice will actually prove, UI implementation, serious multi-agent parallelism, or multi-lane breadth all at once

### AIO-D-014
- date: 2026-04-16
- status: reviewed
- decision: after `M13 - Design Lane Operationalization` was ratified in `AIO-D-013` but before `AIO-064` through `AIO-067` began implementation, the operator explicitly rebaselined `M13` to `M13 - Structural Truth Layer Baseline` and preserved `AIO-064` through `AIO-067` as the seeded task ids under the new scope.
- rationale:
  - traceability, dependency-impact, and system-map maturity are still materially behind current control-surface maturity
  - current governance hygiene is still weak enough that workflow breadth should not expand before dependency and impact truth improve
  - the `AIO-061` protected-surface caution exposed that current enforcement remains intentionally conservative and is not yet supported by a stronger deterministic structural map
  - design-lane work is deferred, not canceled
- accepted anchor facts at rebaseline time:
  - active planning branch: `feature/aioffice-m13-design-lane-operationalization`
  - accepted pre-rebaseline source commit: `c5a3da56f89b9b45265ec885207153978ae9bf9f`
  - preserved accepted snapshot branch: `snapshot/aioffice-m12-closeout-2026-04-16`
- directional queue only:
  - likely next slice after `M13`: hook and automation discipline for the repo-governed milestone loop
  - later likely breadth slice: design-lane operationalization
- non-claims:
  - no readiness or workflow-proof upgrade is authorized
  - this decision does not ratify a post-`M13` milestone
  - this decision does not authorize design-lane, hook, automation, or graph-runtime implementation by itself

### AIO-D-015
- date: 2026-04-17
- status: reviewed
- decision: after the post-`M13` structural-truth review, `M13 - Structural Truth Layer Baseline` is complete and `M14 - Hook And Automation Discipline For The Repo-Governed Milestone Loop` is ratified as the next active conservative slice.
- rationale:
  - committed `M13` evidence now proves the structural-truth layer contract, source-of-truth precedence, and maturity rubric are explicit; a deterministic bounded-input baseline can be generated without inventing unsupported links; and one bounded review-usable rehearsal path exists with explicit proven and unproven boundaries
  - the committed `M13` rehearsal also proved that source-of-truth precedence behaved fail-closed in practice when the derived baseline drifted behind authoritative task truth, which makes the repo-governed milestone publication and verification loop a narrower safer next hardening target than resuming workflow breadth immediately
  - hook and automation discipline for the repo-governed milestone loop now outranks design-lane breadth because the recent operational failures were about publication and verification discipline rather than repo corruption, while design-lane operationalization remains deferred, not canceled, as a later likely breadth slice
  - this decision does not authorize readiness upgrades, workflow proof beyond `architect`, design-lane implementation yet, graph-runtime implementation, or broad automation deployment by itself
- accepted review anchor facts:
  - active planning branch: `feature/aioffice-m13-design-lane-operationalization`
  - accepted structural-truth closeout commit: `db7b78a67ac40cca6d8379026623bd75698b04ac`
  - accepted post-`M13` review evidence commit: `3edce9d6add13996a1ae2eda0b5e6b41869c2ee9`
- non-claims:
  - no readiness or workflow-proof upgrade is authorized
  - this decision does not ratify a post-`M14` milestone
  - this decision does not claim that the structural-truth layer is authoritative over source systems
  - this decision does not authorize design-lane implementation, graph-runtime implementation, or broad hook or automation rollout by itself

### AIO-D-016
- date: 2026-04-17
- status: reviewed
- decision: after the post-`M14` hook and automation discipline review, `M14 - Hook And Automation Discipline For The Repo-Governed Milestone Loop` is complete and `M15 - Design Lane Operationalization` is ratified as the next active conservative slice.
- rationale:
  - committed `M14` evidence now proves the repo-governed milestone publication and verification law is explicit in governance, one bounded helper exists over the authoritative branch and remote review surface, and one bounded rehearsal path was executed with both an aligned `ok` result and a fail-closed `blocked_missing_remote_commit` result
  - the operational failure that outranked workflow breadth after `M13` was publication and verification discipline rather than repo corruption, and `M14` has now narrowed that gap enough to resume one conservative breadth lane
  - design-lane operationalization remains the accepted first workflow-breadth lane from earlier directional context, and resuming one lane is narrower and safer than ratifying broader automation rollout or multi-lane workflow expansion
  - this decision does not authorize readiness upgrades, workflow proof beyond `architect`, broad automation rollout, milestone auto-ratification, or any claim that helper output outranks GitHub or governance source systems
- accepted review anchor facts:
  - active planning branch: `feature/aioffice-m13-design-lane-operationalization`
  - accepted `M14` ratification commit: `78a37c7359eae8abe024219031a749627e992545`
  - accepted repo-loop discipline commit: `3bf4385f034df8a7219159345d48e7a0befa7222`
  - accepted repo publication helper commit: `ff71704e7fcd01644a5849649f140c518a7ce3b6`
  - accepted `M14` rehearsal evidence commit: `a8ce415ea0a4f843128b815a3669944c46b138fb`
- non-claims:
  - no readiness or workflow-proof upgrade is authorized
  - this decision does not ratify a post-`M15` milestone
  - this decision does not authorize broad automation rollout or generic CI/CD strategy
  - this decision does not claim that helper output outranks GitHub or governance source systems
  - this decision does not claim that design-lane breadth is already proven
