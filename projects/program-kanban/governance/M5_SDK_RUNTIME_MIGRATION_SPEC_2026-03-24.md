# Program Kanban M5 SDK-Native Runtime Migration Spec

This document captures the next concrete migration milestone for aligning the studio runtime with the official OpenAI Agents SDK guidance while preserving the existing board, control-room, and safety model.

Decision date:
- `2026-03-24`

Decision source:
- Studio Lead request after reviewing the official OpenAI Agents SDK quickstart, multi-agent, sessions, tracing, and human-in-the-loop guidance

Official references:
- `https://openai.github.io/openai-agents-python/quickstart/`
- `https://openai.github.io/openai-agents-python/multi_agent/`
- `https://openai.github.io/openai-agents-python/tools/`
- `https://openai.github.io/openai-agents-python/sessions/`
- `https://openai.github.io/openai-agents-python/tracing/`
- `https://openai.github.io/openai-agents-python/human_in_the_loop/`

## Goal

Replace the custom agent-runtime core with an SDK-native orchestration path without discarding the current operator wall, SQLite control plane, approvals, artifact governance, or safety boundaries.

## Why This Milestone Exists

The current framework is strongest as:
- a local control room
- a canonical task and evidence store
- a safety-oriented approval and validation surface

The main drift from current OpenAI best practices is in the execution runtime:
- agent calls are still driven through the custom role classes and AutoGen model clients
- approvals and traces are persisted locally, but not yet powered by the SDK's native run model
- the control-room web app is useful, but the actual multi-agent execution path is still custom

This milestone corrects that without restarting the studio from scratch.

## Target Operating Model

### Chat-first operator flow

The Studio Lead continues to use chat as the primary natural-language interface.

The framework should treat chat-originated requests as the preferred orchestration entry point.

### Control-room responsibilities

The Program Kanban app remains the trusted control room for:
- approvals
- traces
- artifacts
- validations
- run inspection
- board and milestone state

### SDK-native runtime responsibilities

The new runtime path should use the official Agents SDK for:
- specialist delegation
- per-specialist session persistence
- tracing
- human-in-the-loop pauses and resumes where specialist work is approval-sensitive

## Core Design Rules

1. The Studio Lead uses chat as the primary Orchestrator surface, and the framework must not create a second conversational Orchestrator role inside the SDK runtime.
2. Architect, Developer, and Design are the first SDK-native specialist roles.
3. PM is optional in this migration. If used at all, it should behave as a deterministic internal planning helper rather than a second conversational manager.
4. Specialist delegation should stay bounded and invisible to the user unless the operator explicitly requests a handoff.
5. Direct board-control actions stay deterministic code paths, not delegated agent work.
6. SDK trace and session data must be mirrored into the canonical SQLite store so the control room remains trustworthy.
7. Existing write-boundary and backup protections remain in force.

## Success Criteria

This milestone is complete only when all of the following are true:
- at least one production orchestration path uses the official Agents SDK runtime instead of the current custom specialist loop
- chat remains the primary Orchestrator surface for that path
- at least one specialist is invoked through an SDK-native bounded delegation pattern
- specialist sessions are isolated by role and run, so Architect, Developer, and Design do not share one mixed context window
- session continuity and pause/resume work across approval boundaries
- SDK trace evidence is mirrored into the canonical SQLite store and visible in the Program Kanban control room
- direct board actions are still handled deterministically outside the agent runtime
- a proof run demonstrates a chat-led request completing through SDK specialist execution and appearing in the control room

## Non-Goals For This Pass

This milestone does not require:
- replacing the board or milestone UI
- removing the existing custom runtime immediately
- true parallel execution
- role-prompt editing from the UI
- external hosting
- authentication

## Derived Task Queue

Foundation:
- `TGD-057` add the official Agents SDK dependency and an isolated runtime adapter path
- `TGD-058` implement shared SDK specialist-session support without creating a second Orchestrator role
- `TGD-059` implement direct specialist delegation through SDK-native bounded agent calls

Control and evidence:
- `TGD-060` bridge SDK human-in-the-loop pauses and resumes into the canonical approval model for specialist delegation
- `TGD-061` mirror SDK traces and session evidence into the SQLite control store and run inspector
- `TGD-062` preserve deterministic board-control actions outside the agent runtime and route only generative work into the SDK path

Proof:
- `TGD-063` prove a chat-led Orchestrator flow that delegates to SDK specialists and is fully visible in the control room
