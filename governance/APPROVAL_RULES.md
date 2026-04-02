# Approval Rules

Date:
- `2026-04-02`

Status:
- `Implemented baseline`

## Approval Gates

Approval is required for:
- Tier 1 usage
- large tasks
- architecture changes
- retries that materially increase cost or risk

## Why These Gates Exist

- Tier 1 is the expensive scarce lane
- large tasks are where uncontrolled spend and drift usually start
- architecture changes affect multiple future tasks, not just one run
- retry loops can silently become the real cost leak

## Required Approval Packet Fields

Every approval request for the hybrid execution model must include:
- why this tier is needed
- expected cost impact
- risk of not proceeding

Optional but recommended:
- fallback path if approval is denied
- cheaper tier attempted first
- expected artifact or decision output

## Approval Decisions

### Approve

Use when:
- the requested tier is justified by ambiguity, system risk, or architecture impact
- no cheaper safe path is available

### Reject

Use when:
- the same work can safely run at Tier 2 or Tier 3
- the task should be decomposed further first
- the request is exploratory but not decision-critical

### Revise

Use when:
- the request is valid but still too broad
- the cost estimate is missing
- the output format or acceptance criteria are unclear

## Prohibited Approval Anti-Patterns

- approving Tier 1 because it feels safer
- hiding repeated retries inside Tier 2 or Tier 3 without surfacing cost
- using architecture approval to cover routine implementation
- allowing a worker to self-approve escalation

## Current Implementation Notes

The orchestrator now computes approval triggers from the classified task profile and tier assignment. The approval model is intentionally conservative:
- Tier 1 implies approval
- large work implies approval
- architecture-change language implies approval

This is the first rule set, not the final one.
