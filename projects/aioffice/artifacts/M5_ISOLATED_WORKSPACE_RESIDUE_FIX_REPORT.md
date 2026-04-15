# M5 Isolated Workspace Residue Fix Report

## Purpose
- Remediate `AIO-035` narrowly by stopping isolated AIOffice rehearsal workspaces from creating unrelated bootstrap residue after `AIO-029`.
- Keep the fix store-scoped, fail-closed, and test-backed without starting `AIO-033` or changing broader workflow claims.

## Root Cause
- `SessionStore.__init__(...)` defaulted `bootstrap_legacy_defaults=True` for every root.
- That default treated an isolated rehearsal workspace root as if it were a full legacy repo root.
- During initialization, the store therefore:
  - created `memory/framework_health.json` and `memory/session_summaries.json` through `ensure_memory_files()`
  - created `projects/tactics-game/execution/KANBAN.md` through `_ensure_project(PROJECT_NAME)` and `render_kanban(PROJECT_NAME)` where `PROJECT_NAME` is `tactics-game`
- Result: isolated AIOffice rehearsal workspaces only stayed clean when every caller remembered to pass `bootstrap_legacy_defaults=False` explicitly.

## Exact Files Changed
- `sessions/store.py`
- `tests/test_control_kernel_store.py`
- `tests/test_operator_api.py`

## Exact Validation Performed
1. Reproduced the defect on a fresh isolated workspace-shaped root under `projects/aioffice/artifacts/m5_aio035_repro_before/workspace` using direct `SessionStore(workspace_root)` before the fix.
   - observed files:
     - `memory/framework_health.json`
     - `memory/session_summaries.json`
     - `projects/tactics-game/execution/KANBAN.md`
     - `sessions/studio.db`
2. Applied a narrow store fix so AIOffice isolated rehearsal workspace roots under `projects/aioffice/artifacts/*/workspace` auto-skip legacy bootstrap defaults unless explicitly overridden.
3. Re-ran the isolated-root validation on a fresh workspace-shaped root after the fix using direct `SessionStore(workspace_root)` plus one bounded `create_workflow_run(...)`.
   - observed files:
     - `sessions/studio.db`
4. Ran focused regression coverage for isolated-workspace behavior and the sanctioned CLI rehearsal path:
   - command:
     - `.\venv\Scripts\python.exe -m pytest tests/test_control_kernel_store.py tests/test_operator_api.py -k "isolated_rehearsal or aioffice_supervised_architect_rehearsal_succeeds"`
   - observed result:
     - `3 passed, 33 deselected`
5. Ran a focused regression guard on the controlled apply/promotion path to confirm the bootstrap hardening change did not disturb the previously proven M5 path:
   - command:
     - `.\venv\Scripts\python.exe -m pytest tests/test_control_kernel_store.py -k "controlled_apply_promotion"`
   - observed result:
     - `1 passed, 15 deselected`

## Before / After Residue State
### Before
- Direct isolated-root store initialization created unrelated bootstrap residue:
  - `memory/framework_health.json`
  - `memory/session_summaries.json`
  - `projects/tactics-game/execution/KANBAN.md`

### After
- Direct isolated-root store initialization no longer created unrelated bootstrap residue.
- The bounded isolated-root validation retained only the required persisted store file:
  - `sessions/studio.db`
- The sanctioned operator CLI rehearsal path still produced its expected AIOffice artifact set only, with no unrelated `memory/*.json` files and no non-AIOffice project ledger file.

## Remaining Limitations
- The auto-skip is intentionally narrow to AIOffice isolated rehearsal workspace roots under `projects/aioffice/artifacts/*/workspace`.
- Explicit legacy bootstrap remains available when a caller intentionally passes `bootstrap_legacy_defaults=True`; this preserves narrowness and avoids changing unrelated store consumers silently.
- This pass does not prove unattended readiness, later-stage workflow, or broader multi-run stability.
- `M5` remains open and `AIO-033` remains separate work.

## Whether AIO-035 Is Now Satisfied
- Yes on remediation evidence:
  - the residue was reproduced factually
  - the root cause was narrowed to legacy bootstrap defaults in `SessionStore`
  - the fix removed the unrelated residue for isolated rehearsal workspace roots
  - focused tests passed
  - equivalent sanctioned rehearsal validation still passed and showed only justified files
- This pass should still record `AIO-035` as `in_review`, not `completed`, to preserve lawful closeout discipline.

## Immediate Next Step
- Keep `AIO-035` visible in review for closeout.
- `AIO-033` can begin after this remediation review because the specific isolated-workspace residue blocker is no longer active on the validated path.
