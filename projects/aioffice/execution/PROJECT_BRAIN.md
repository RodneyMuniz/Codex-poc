# AIOffice Project Brain Stub

Bootstrap status:
- temporary working memory
- intended to keep early assumptions visible

## Current Understanding
- AIOffice is a new project shell inside the existing monorepo.
- Bootstrap scope is governance-first and excludes UI.
- The authoritative root is the Desktop repo, not the Documents duplicate.
- The current multi-role runtime must not become the AIOffice planning engine.
- sanctioned project registration now exists through deterministic store code and the CLI `projects ensure` path.
- canonical AIO task import remains deferred because the current `tasks` schema does not preserve durable `dependencies`.

## Open Questions
- what concrete capability waves follow M1
- which donor patterns are truly reusable after audit
- whether later task tracking should mirror into the canonical store once durable `dependencies` support exists
- what review cadence should govern AIOffice artifacts

## Immediate References
- `governance/PROJECT.md`
- `governance/BOARD_RULES.md`
- `governance/ARTIFACT_MAP.md`
- `governance/DONOR_LEDGER.md`
- `governance/WORKSPACE_BOUNDARIES.md`
- `execution/KANBAN.md`

## TODO
- replace bootstrap assumptions with reviewed facts
- add decision-log cross-references
- capture later milestone hypotheses only after donor audit closes
- trim anything that becomes duplicated by approved governance artifacts
