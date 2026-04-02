# Test Results

Date:
- `2026-04-02`

Status:
- `Phase 5 complete`

## Controlled Scenario Validation

| Scenario | Expected Tier | Actual Tier | Approval Expected | Result |
| --- | --- | --- | --- | --- |
| small bounded task | `tier_3_junior` | `tier_3_junior` | no | pass |
| medium structured task | `tier_2_mid` | `tier_2_mid` | no | pass |
| ambiguous architecture task | `tier_1_senior` | `tier_1_senior` | yes | pass |

Source tests:
- `tests/test_tiered_execution.py`

## API Router Validation

Validated:
- tier-to-model routing
- usage normalization
- cached-token-aware cost estimation
- artifact write path
- usage recording into canonical store

Source tests:
- `tests/test_api_router.py`

## Focused Suite

Command:

```powershell
.\venv\Scripts\python.exe -m pytest tests\test_pm_flow.py tests\test_api_router.py tests\test_tiered_execution.py tests\test_orchestrator.py
```

Result:
- `33 passed`

## Broader Regression Suite

Command:

```powershell
.\venv\Scripts\python.exe -m pytest tests\test_specialist_prompt_hardening.py tests\test_pm_flow.py tests\test_store.py tests\test_orchestrator.py tests\test_import_legacy_projects.py tests\test_operator_wall_snapshot.py tests\test_cli.py tests\test_operator_api.py tests\test_api_router.py tests\test_tiered_execution.py
```

Result:
- `59 passed`
