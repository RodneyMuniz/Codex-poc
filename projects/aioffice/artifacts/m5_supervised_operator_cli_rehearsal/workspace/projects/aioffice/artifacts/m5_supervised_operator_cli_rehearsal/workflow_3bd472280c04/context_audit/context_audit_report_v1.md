# Context Audit Report

- sources_checked: sessions/store.py, scripts/operator_api.py, state_machine.py
- relevant_context_found: persisted workflow entities, packet/bundle path, read-only inspection path
- gaps: no apply/promotion, no unattended scheduling, no later-stage proof
- risks: missing provider proof or stale stage evidence must fail closed
