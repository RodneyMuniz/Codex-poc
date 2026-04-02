# PK-075 API Usage Root Cause Review

Date:
- `2026-04-02`

Task:
- `PK-075`

Status:
- `slice delivered`

## What We Verified

- the most recent historical `usage_events` before this review were on `2026-03-24`
- there were no fresh usage rows from `2026-04-02` before this slice
- a live tracked prompt-specialist call tied to `PK-075` now produced a new `usage_events` row on `2026-04-02`
- follow-on tracked runs on `2026-04-02` continued to produce fresh `usage_events`, confirming this is not limited to one synthetic proof row

Live audit evidence:
- run: `run_1fa9ecfd4271`
- usage event: `usage_cb96f2338228`
- source: `PromptSpecialist`
- prompt tokens: `322`
- completion tokens: `146`
- created at: `2026-04-02T03:23:37+00:00`

## Root Cause

The problem was not that the repo had no API-capable path.

The real issue was a split runtime model:

- the new `APIRouter` and `CostTracker` were implemented, but they were mainly exercised by controlled tests and not yet wired in as the default live execution path
- the intake and preview lane still used the older prompt-specialist client path
- that prompt-specialist path only left canonical `usage_events` when it ran inside a tracked `run_id` and `task_id`
- the operator preview flow usually happened before a run existed, so the preview lane could use an API-backed model without leaving the newer usage evidence the operator expected
- a Program Kanban task could still hit a task-gate failure after API usage succeeded if execution started before milestone normalization, which made the operator experience look broken even when the API call itself had worked

In short:
- API capability existed
- live M11 and milestone-governance work mostly did not invoke it
- when prompt-specialist intake did run, it was often outside a tracked run and therefore invisible to the new usage evidence lane
- one board/task gate could still turn a successful tracked intake into a failed run receipt, leaking trust even though the API-backed call had already been recorded

## Bounded Fix

The first safe fix was:

- keep the existing prompt-specialist runtime
- add a tracked prompt-specialist intake call inside `start_task()` for request tasks with a `raw_request`
- record a trace event when that tracked intake usage succeeds or fails
- normalize Program Kanban milestone assignment before delegated execution starts so request-preview runs do not fail after the API-backed intake already completed

This avoids a risky runtime rewrite while making the intake lane observable in canonical run evidence.

## Meaning For The Studio

- the studio can now prove fresh API-backed intake usage on a real tracked run
- the studio no longer relies on a milestone-normalization race for this request-preview path
- the new API-first model is still not fully adopted as the one default execution path
- the larger follow-on remains: unify the split between the older prompt-specialist path, the SDK specialist bridge, and the newer `APIRouter` cost/usage model

## Recommended Next Step

`PK-075` is now complete. The next migration slice should decide whether to:

1. move more intake and planning work onto the `APIRouter`, or
2. keep the current runtimes and expand canonical usage and cost evidence until the split runtime can be simplified safely
