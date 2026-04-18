# Copy Manifest

This is a selective donor import manifest for the new clean repo.
It is intentionally minimal.

## COPY_AS_IS
- `projects/aioffice/handoffs/rebaseline_2026_04/RESET_START_HERE.md`
- `projects/aioffice/handoffs/rebaseline_2026_04/REBASELINE_DECISION.md`
- `projects/aioffice/handoffs/rebaseline_2026_04/REBASELINE_SOURCE_MAP.md`
- `projects/aioffice/handoffs/rebaseline_2026_04/PRESERVED_PATTERNS.md`
- `projects/aioffice/handoffs/rebaseline_2026_04/COPY_MANIFEST.md`

## ADAPT_FROM_PATTERN
- `projects/aioffice/governance/VISION.md`
  - adapt the product thesis, doctrine, harness framing, and proof-honesty pattern
- `projects/aioffice/governance/PROJECT.md`
  - adapt the document hierarchy and authority model without old status history
- `projects/aioffice/governance/WORKFLOW_VISION.md`
  - adapt the canonical workflow shape and first-proof boundary
- `projects/aioffice/governance/STAGE_GOVERNANCE.md`
  - adapt stage order, artifact expectations, and blocked-state rules
- `projects/aioffice/governance/REPO_MILESTONE_LOOP_DISCIPLINE.md`
  - adapt the publication, verification, and fail-closed reporting discipline
- `projects/aioffice/governance/DESIGN_LANE_CONTRACT.md`
  - adapt only the boundary-pattern logic if later needed, not as an initial implementation commitment
- `projects/aioffice/governance/SYSTEM_REALITY_MAP.md`
  - adapt the system-reality versus target-state distinction

## REFERENCE_ONLY
- `projects/aioffice/handoffs/rebaseline_2026_04/OLD_REPO_FREEZE.md`
- `projects/aioffice/governance/M13_STRUCTURAL_TRUTH_REVIEW.md`
- `projects/aioffice/governance/M14_HOOK_AND_AUTOMATION_REVIEW.md`
- `projects/aioffice/governance/M15_DESIGN_LANE_REVIEW.md`
- `sessions/store.py`
- `state_machine.py`
- `scripts/operator_api.py`
- `tests/test_control_kernel_store.py`

## DO_NOT_CARRY
- `projects/aioffice/execution/KANBAN.md`
  - do not migrate legacy backlog or milestone history
- `projects/aioffice/governance/ACTIVE_STATE.md`
  - do not carry the old repo posture into the new repo
- `projects/aioffice/governance/DECISION_LOG.md`
  - do not carry old milestone-ratification history as active reset authority
- old task ids, milestone ids, and planning-state chains
- stale donor defaults, mixed multi-project leftovers, and noisy historical scaffolding
