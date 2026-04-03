# AI Studio POC

This repository is being rebuilt from a manual markdown-driven studio into a persistent multi-agent framework with governance-gated model access, task-state routing, and durable execution evidence.

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
- `wrappers/` governance-gated LLM wrapper and call logging
- `kanban/` board adapters and local/GitHub-backed task-state helpers
- `memory/` lightweight interaction memory and metrics store
- `scripts/` launchers, utilities, and upcoming CLI entry points
- `archive/legacy-manual-studio/` preserved snapshot of the original manual prototype

## Current Status

Phase 0 has normalized the repository layout, archived the legacy manual prototype, and prepared the project for a persistent AutoGen-based rebuild on Python 3.14.

The current governance slice adds:

- a governance-gated LLM wrapper with prompt and tool checks
- a task-state machine for `Idea -> Spec -> Todo -> In Progress -> Review -> Done`
- a lightweight Kanban adapter that can use the local store or a GitHub Project
- interaction memory, hook-based metrics, and a weekly policy review workflow

## Phase 1 CLI

The current Phase 1 slice is driven from `scripts/cli.py`.

Examples:

- `python scripts/cli.py task create --title "Add turn order tracker" --description "Plan and delegate the turn order tracker task."`
- `python scripts/cli.py run --project tactics-game`
- `python scripts/cli.py approvals list`
- `python scripts/cli.py approve <approval-id>`
- `python scripts/cli.py resume <run-id>`

## Governance Runtime

Key modules:

- `governance/rules.py` and `governance/rules.yml` load policy, role, tool, and prompt rules
- `wrappers/llm_wrapper.py` gates LLM calls before they reach provider runtimes
- `runtime.py` abstracts provider-specific response calls
- `state_machine.py` defines task states and legal transitions
- `kanban/board.py` reads and moves tasks through the board model
- `memory/memory_store.py` persists interactions and metrics
- `hooks.py` records lightweight pre/post task telemetry

## Setup

Create the environment and install dependencies:

- `python -m venv .venv`
- `.venv\Scripts\activate`
- `pip install -e .[dev]`

Optional GitHub Project settings for `kanban/board.py`:

- `GITHUB_TOKEN` or `AISTUDIO_GITHUB_TOKEN`
- `GITHUB_REPOSITORY` or `AISTUDIO_GITHUB_REPO`
- `AISTUDIO_GITHUB_PROJECT_ID`

Without those variables, the board adapter uses the local `SessionStore` task board.

## Policy Review

The weekly review workflow lives at `.github/workflows/policy-review.yml`.

Run it locally with:

- `python scripts/policy_review.py`

