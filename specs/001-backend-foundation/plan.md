# Implementation Plan: Backend Foundation

**Branch**: `001-backend-foundation` | **Date**: 2026-02-28 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/001-backend-foundation/spec.md`

## Summary

Build the backend infrastructure for TriageNet: validated Pydantic domain models for all entities (incidents, callers, vision, triage, dispatch, events), pydantic-settings config loading, Supabase state manager + agent logger, ElevenLabs transcription/TTS services, Mistral API connectivity, shared agent dependencies dataclass, and SQL migrations. All verified by 4 phased test suites with timestamps/timing.

## Technical Context

**Language/Version**: Python 3.12
**Primary Dependencies**: FastAPI 0.115+, pydantic 2.10+, pydantic-settings 2.6+, pydantic-ai[mistral] 0.2+, mistralai 1.12+, supabase 2.11+, httpx 0.28+, python-dotenv 1.0+
**Storage**: Supabase (Postgres + Realtime) — 4 tables: incident_state, agent_logs, transcripts, dispatches
**Testing**: pytest 8.3+, pytest-asyncio 0.24+ (asyncio_mode = "auto"), tests log timestamps per operation
**Target Platform**: Linux/macOS server, development machine
**Project Type**: Web service (FastAPI backend)
**Performance Goals**: Agent calls < 10s, Supabase round-trips < 2s, ElevenLabs calls < 15s
**Constraints**: Requires valid API keys for Mistral, ElevenLabs, and Supabase; user must run SQL migrations manually
**Scale/Scope**: Single demo session, 3 concurrent callers, 1 CCTV feed

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Gate | Status | Notes |
|------|--------|-------|
| I. Spec-Driven Development | PASS | Running through /speckit.specify → /speckit.plan now |
| II. Repository Structure | PASS | All files go in /apps/server per constitution |
| III. Frontend Stack | N/A | This feature is backend only |
| IV. Backend Stack | PASS | Python + uv + FastAPI + pydantic-ai + Supabase |
| IV-A. Pydantic-AI Rules | PASS | Using Agent(model, deps_type, output_type), @agent.tool, RunContext, result.output |
| V. Architecture Pattern | PASS | Agents write to Supabase, frontend reads via Realtime |
| VI. Test-First | PASS | 4 phased test files with per-operation timing |
| VI-A. E2E Testing w/ Timestamps | PASS | All tests log elapsed time per operation + total summary |
| VII. Simplicity | PASS | Direct implementations, no unnecessary abstractions |

## Project Structure

### Documentation (this feature)

```text
specs/001-backend-foundation/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (/speckit.tasks)
```

### Source Code (repository root)

```text
apps/server/
├── pyproject.toml
├── .python-version
├── .env
├── assets/                      # Demo media (user-provided)
│   ├── caller_1_spanish.mp3
│   ├── caller_2_mandarin.mp3
│   ├── caller_3_french.mp3
│   └── crash_video.mp4
└── src/
    ├── config.py                # pydantic-settings Settings
    ├── deps.py                  # Supabase/Mistral client initialization
    ├── models/
    │   ├── __init__.py
    │   ├── incident.py          # IncidentState, Severity, IncidentStatus, TimelineEvent, ActionItem
    │   ├── caller.py            # CallerRecord, TranscriptSegment, IntakeFacts
    │   ├── vision.py            # VisionDetection, FrameAnalysis, SceneDelta
    │   ├── triage.py            # TriageResult, Corroboration, EvidenceFusionResult
    │   ├── dispatch.py          # DispatchBrief
    │   └── events.py            # AgentLogEntry
    ├── agents/
    │   └── shared_deps.py       # TriageNetDeps dataclass
    ├── services/
    │   ├── __init__.py
    │   ├── state.py             # StateManager (Supabase CRUD + agent logging)
    │   ├── logger.py            # Standalone logging helpers
    │   ├── transcription.py     # ElevenLabs transcription wrapper
    │   └── tts.py               # ElevenLabs TTS wrapper
    └── tests/
        ├── __init__.py
        ├── test_phase1_models.py
        ├── test_phase2_supabase.py
        ├── test_phase3_mistral.py
        └── test_phase4_elevenlabs.py

supabase/migrations/
├── 001_incident_state.sql
├── 002_agent_logs.sql
├── 003_transcripts.sql
├── 004_dispatches.sql
└── 005_enable_realtime.sql
```

**Structure Decision**: Monorepo with `/apps/server` for Python backend. All source code under `src/` with `models/`, `agents/`, `services/`, `routes/`, `tests/` subpackages. SQL migrations in `/supabase/migrations/` for user to paste into Supabase dashboard.
