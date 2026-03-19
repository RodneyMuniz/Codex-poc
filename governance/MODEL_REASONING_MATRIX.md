# Model Reasoning Matrix

Phase 1 favors safe runtime defaults that are already proven in the current environment, while leaving room to promote roles to higher-capability models through environment overrides.

| Role | Phase 1 Runtime Default | Preferred Upgrade Path | Reasoning Depth | Cost Posture | Primary Responsibility | Fallback |
| --- | --- | --- | --- | --- | --- | --- |
| Program Orchestrator | `gpt-4.1-mini` | `gpt-5-mini` | Low | Low | Route work, load governance, manage runs | `gpt-4.1-mini` |
| Project PO | `gpt-4.1-mini` | `gpt-5-mini` | Medium | Low to medium | Manage queue, delegate, request approvals, close work | `gpt-4.1-mini` |
| Architect | `gpt-4.1-mini` | `gpt-5` | High | Medium to high | Architecture tradeoffs, risks, acceptance framing | `gpt-4.1-mini` |
| Developer | `gpt-4.1-mini` | `gpt-5.1-codex-mini` when available | Medium | Low to medium | Implementation planning, code-oriented reasoning, validation steps | `gpt-4.1-mini` |
| Kanban / Summary Tasks | `gpt-4.1-mini` | `gpt-5-mini` | Low | Low | Short updates, summaries, board hygiene | `gpt-4.1-mini` |
| Telemetry / Validation Review | `gpt-4.1-mini` | `gpt-5-mini` | Low | Low | Brief health checks and outcome summaries | `gpt-4.1-mini` |

## Policy Notes

- Runtime defaults stay on `gpt-4.1-mini` in Phase 1 to reduce failure risk while the framework is still stabilizing.
- Higher-cost roles are activated through environment overrides only after access and spend expectations are confirmed.
- Developer-role upgrades should favor coding-tuned models that remain compatible with the team runtime used by the framework.
