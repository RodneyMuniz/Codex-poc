# Thin Manager API-First Slice 1

Date:
- `2026-04-02`

Status:
- `implemented`
- `validated`

Scope:
- fastest-savings-first enforcement slice
- budget truth for active model mix
- lane-aware compiled packets
- API-router default for tracked bounded specialist execution
- removal of the duplicate intake call when preview usage evidence is already available

## Delivered

- Added live-model pricing entries for the current `gpt-4.1*` defaults in [config.py](C:\Users\rodne\Dev\_AIStudio_worktrees\studio-control\agents\config.py).
- Extended the packet schema with:
  - `execution_lane`
  - `route_family`
  - `cache_policy`
  - `budget_policy`
  in [schemas.py](C:\Users\rodne\Dev\_AIStudio_worktrees\studio-control\agents\schemas.py).
- Made the Orchestrator compile lane-aware request packets and persist lane/cache/budget metadata into task acceptance and run team state in [orchestrator.py](C:\Users\rodne\Dev\_AIStudio_worktrees\studio-control\agents\orchestrator.py).
- Reused preview-time prompt-specialist usage evidence during `start_task(...)` instead of always paying for a second tracked intake call in [orchestrator.py](C:\Users\rodne\Dev\_AIStudio_worktrees\studio-control\agents\orchestrator.py).
- Propagated lane and route-family metadata into PM-created subtasks in [pm.py](C:\Users\rodne\Dev\_AIStudio_worktrees\studio-control\agents\pm.py).
- Made `APIRouter` lane-aware and ensured lane metadata is recorded into usage evidence in [api_router.py](C:\Users\rodne\Dev\_AIStudio_worktrees\studio-control\agents\api_router.py).
- Confirmed `usage_events` now carry:
  - `model`
  - `tier`
  - `lane`
  - `cached_input_tokens`
  - `reasoning_tokens`
  - `estimated_cost_usd`
  via [store.py](C:\Users\rodne\Dev\_AIStudio_worktrees\studio-control\sessions\store.py) and [cost_tracker.py](C:\Users\rodne\Dev\_AIStudio_worktrees\studio-control\agents\cost_tracker.py).
- Kept `StudioRoleAgent` on `APIRouter` by default for tracked bounded execution, with the legacy client left as compatibility fallback for untracked paths, in [role_base.py](C:\Users\rodne\Dev\_AIStudio_worktrees\studio-control\agents\role_base.py).

## Verified

Focused regression:

```powershell
.\venv\Scripts\python.exe -m pytest tests\test_tiered_execution.py tests\test_orchestrator.py tests\test_pm_flow.py tests\test_role_base_usage.py tests\test_api_router.py tests\test_store.py -q
```

Result:
- `58 passed`

Broader control-room and evidence regression:

```powershell
.\venv\Scripts\python.exe -m pytest tests\test_specialist_prompt_hardening.py tests\test_pm_flow.py tests\test_store.py tests\test_orchestrator.py tests\test_import_legacy_projects.py tests\test_operator_wall_snapshot.py tests\test_cli.py tests\test_operator_api.py tests\test_api_router.py tests\test_tiered_execution.py tests\test_role_base_usage.py -q
```

Result:
- `72 passed`

## Remaining Follow-On

- `background_api` and `batch_api` are now first-class packet concepts, but `Batch API` is not yet an operational live path.
- approval packets still need explicit estimated cost impact and cheaper-alternative evidence before the governor is fully trusted.
- operator surfaces still need richer lane, latency, cache, and retry summaries before the budget governor can optimize from evidence instead of logs alone.
