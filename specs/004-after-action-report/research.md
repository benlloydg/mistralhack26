# Research: After-Action Report (Backend)

**Feature**: 004-after-action-report
**Date**: 2026-03-01

## R1: Existing Report Route

**Decision**: Replace the current HTML report at `/report/{case_id}` with a new JSON API endpoint at `/api/v1/cases/{case_id}/report`.

**Rationale**: The existing `report.py` renders a self-contained HTML page server-side. For the new design, the frontend team (Gemini) builds the UI separately and needs a JSON contract. The old HTML route can remain as a fallback/judge artifact, but the new JSON endpoint is the primary API.

**Alternatives considered**: Extending the HTML route with JSON mode via `Accept` header — rejected because it complicates the route and mixes concerns.

## R2: Frame Storage Pattern

**Decision**: Save JPEG frames to `assets/frames/` during demo, serve via `/frames` static mount in `main.py`. Same pattern as TTS audio at `/audio`.

**Rationale**: Already proven pattern in the codebase. Frames are extracted as bytes by `extract_frame()` in the orchestrator — just needs a `with open(..., 'wb')` after extraction. No new dependencies.

**Alternatives considered**:
- Supabase Storage bucket — adds bucket setup complexity, not needed for single-machine demo
- Base64 in JSONB — bloats incident_state rows, slows queries

## R3: Executive Summary Generation

**Decision**: Use `mistral_client.chat.complete_async()` with the full case state, all transcripts, and dispatch data as context. Cache result in an in-memory dict keyed by case_id.

**Rationale**: The existing `translate_to_english()` function already uses this pattern. A 3-4 sentence summary is a simple prompt completion. In-memory cache is sufficient — the demo runs once, then the report is requested multiple times by judges.

**Alternatives considered**:
- Pydantic-AI agent for summary — overkill for a single prompt completion, adds agent overhead
- Persistent cache in Supabase — unnecessary for hackathon, adds a table

## R4: Convergence Tracks Data Shape

**Decision**: Build convergence tracks by iterating `agent_logs` and `transcripts`, grouping events by source (language for audio, "vision" for vision, "fused" for triage/fusion events). Each track is an array of `{t: float, label: str, type: str}` entries.

**Rationale**: All the data already exists in `agent_logs` (with timestamps from `created_at`) and `transcripts` (with `language` and `feed_id`). No new data collection needed — it's a read-time transformation.

**Alternatives considered**: Pre-computing tracks during the demo and storing in a dedicated table — rejected for simplicity (YAGNI).

## R5: Agent Stats Computation

**Decision**: Compute agent invocation counts and latency from `agent_logs` table at report time. Group by `agent` field, count rows, compute timing from `created_at` gaps.

**Rationale**: All agent invocations are already logged via `state.log()`. The `model` field was recently added to `AgentLogEntry`. Average latency can be approximated from timestamp gaps between sequential logs from the same agent.

**Alternatives considered**: Tracking explicit start/end times per agent invocation — would require modifying every agent call site, violates simplicity principle.
