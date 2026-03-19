# AI Studio POC

This repository is being rebuilt from a manual markdown-driven studio into a persistent multi-agent framework.

## Purpose

The repository is the foundation for:

- governance-driven orchestration
- project-specific execution
- reusable agent skills
- durable session state
- observable, Git-backed delivery loops

## Active Structure

- `governance/` global studio policy, rules, vision, and decision records
- `projects/tactics-game/` the first active project, with project governance and execution views
- `agents/` active orchestrator and crew agent modules
- `skills/` reusable Python tools and helper functions
- `sessions/` runtime state and persistent stores
- `logs/` runtime logs and telemetry outputs
- `scripts/` launchers, utilities, and upcoming CLI entry points
- `archive/legacy-manual-studio/` preserved snapshot of the original manual prototype

## Current Status

Phase 0 has normalized the repository layout, archived the legacy manual prototype, and prepared the project for a persistent AutoGen-based rebuild on Python 3.14.

The next implementation phase will replace markdown-only orchestration with:

- a persistent session store
- approval pause and resume gates
- a real Project PO, Architect, and Developer crew
- observability and token-usage tracking

