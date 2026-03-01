# Tasks: Backend Foundation

**Input**: Design documents from `/specs/001-backend-foundation/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: YES — spec requires 4 phased test suites (FR-010) with timestamps/timing per operation.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization, directory structure, dependency installation

- [x] T001 Create directory structure: `apps/server/src/models/`, `apps/server/src/agents/`, `apps/server/src/services/`, `apps/server/src/routes/`, `apps/server/src/tests/`, `apps/server/assets/`, `supabase/migrations/`
- [x] T002 Create `apps/server/pyproject.toml` with all dependencies (fastapi, pydantic, pydantic-settings, pydantic-ai[mistral], mistralai, supabase, httpx, python-dotenv, python-multipart, pytest, pytest-asyncio)
- [x] T003 Create `apps/server/.python-version` with `3.12`
- [x] T004 Create `apps/server/.env` template (placeholder values — user provides real keys)
- [x] T005 Run `uv sync --dev` in `apps/server/` to install dependencies
- [x] T006 Create all `__init__.py` files: `apps/server/src/models/__init__.py`, `apps/server/src/agents/__init__.py`, `apps/server/src/services/__init__.py`, `apps/server/src/routes/__init__.py`, `apps/server/src/tests/__init__.py`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Config, shared deps, and SQL migrations that ALL user stories depend on

**CRITICAL**: No user story work can begin until this phase is complete

- [x] T007 Create `apps/server/src/config.py` — pydantic-settings Settings class loading from `.env` (mistral_api_key, elevenlabs_api_key, supabase_url, supabase_service_key, model names, app_env, log_level, demo_scenario)
- [x] T008 Create `apps/server/src/deps.py` — Supabase client + Mistral client initialization from Settings
- [x] T009 Create `apps/server/src/agents/shared_deps.py` — TriageNetDeps dataclass (supabase, mistral_client, case_id, session_start_time, elevenlabs_api_key)
- [x] T010 [P] Create `supabase/migrations/001_incident_state.sql` — incident_state table with all columns, updated_at trigger
- [x] T011 [P] Create `supabase/migrations/002_agent_logs.sql` — agent_logs table with indexes
- [x] T012 [P] Create `supabase/migrations/003_transcripts.sql` — transcripts table with indexes
- [x] T013 [P] Create `supabase/migrations/004_dispatches.sql` — dispatches table with indexes
- [x] T014 [P] Create `supabase/migrations/005_enable_realtime.sql` — ALTER PUBLICATION for all 4 tables
- [x] T015 **USER ACTION**: Provide env values (MISTRAL_API_KEY, ELEVENLABS_API_KEY, SUPABASE_URL, SUPABASE_SERVICE_KEY) and paste into `apps/server/.env`
- [ ] T016 **USER ACTION**: Run SQL migrations 001-005 in Supabase SQL Editor, confirm Realtime enabled on all 4 tables

**Checkpoint**: Config loads, clients initialize, database tables exist

---

## Phase 3: User Story 1 — Data Models Validate Correctly (Priority: P1)

**Goal**: Complete set of validated Pydantic domain models for all entities

**Independent Test**: `uv run pytest src/tests/test_phase1_models.py -v -s` — all model instantiation, validation, and serialization tests pass with timing

### Implementation for User Story 1

- [x] T017 [P] [US1] Create incident models in `apps/server/src/models/incident.py` — Severity enum, IncidentStatus enum, TimelineEvent, ActionItem, IncidentState
- [x] T018 [P] [US1] Create caller models in `apps/server/src/models/caller.py` — TranscriptSegment, IntakeFacts, CallerRecord
- [x] T019 [P] [US1] Create vision models in `apps/server/src/models/vision.py` — VisionDetection, FrameAnalysis, SceneDelta
- [x] T020 [P] [US1] Create triage models in `apps/server/src/models/triage.py` — TriageResult, Corroboration, EvidenceFusionResult
- [x] T021 [P] [US1] Create dispatch models in `apps/server/src/models/dispatch.py` — DispatchBrief
- [x] T022 [P] [US1] Create event models in `apps/server/src/models/events.py` — AgentLogEntry
- [x] T023 [US1] Update `apps/server/src/models/__init__.py` — re-export all models
- [x] T024 [US1] Create `apps/server/src/tests/test_phase1_models.py` — 23/23 tests PASSED

**Checkpoint**: All models validate correctly. `uv run pytest src/tests/test_phase1_models.py -v -s` passes.

---

## Phase 4: User Story 2 — Supabase State Management (Priority: P1)

**Goal**: StateManager service that creates, reads, updates incident state and logs agent events to Supabase

**Independent Test**: `uv run pytest src/tests/test_phase2_supabase.py -v -s` — CRUD round-trip + agent logging tests pass with timing

### Implementation for User Story 2

- [x] T025 [US2] Create `apps/server/src/services/state.py` — StateManager class with get_state(), update_state(), append_timeline(), log_agent(), log() convenience method
- [x] T026 [P] [US2] Create `apps/server/src/services/logger.py` — standalone logging helpers for agent_logs writes
- [x] T027 [US2] Create `apps/server/src/tests/test_phase2_supabase.py` — awaiting SQL migrations from user

**Checkpoint**: StateManager CRUD works end-to-end. `uv run pytest src/tests/test_phase2_supabase.py -v -s` passes.

---

## Phase 5: User Story 3 — Mistral API Connectivity (Priority: P2)

**Goal**: Verified connectivity to Mistral Large and Small models via pydantic-ai

**Independent Test**: `uv run pytest src/tests/test_phase3_mistral.py -v -s` — structured output from Mistral validates against Pydantic model, with timing

### Implementation for User Story 3

- [x] T028 [US3] Create `apps/server/src/tests/test_phase3_mistral.py` — created, ready to run

**Checkpoint**: Mistral returns valid structured output. `uv run pytest src/tests/test_phase3_mistral.py -v -s` passes.

---

## Phase 6: User Story 4 — ElevenLabs API Connectivity (Priority: P2)

**Goal**: Verified transcription and TTS connectivity to ElevenLabs

**Independent Test**: `uv run pytest src/tests/test_phase4_elevenlabs.py -v -s` — TTS returns audio bytes, with timing

### Implementation for User Story 4

- [x] T029 [P] [US4] Create `apps/server/src/services/transcription.py` — transcribe_audio() async function using httpx POST to ElevenLabs /v1/speech-to-text with Scribe v1 model
- [x] T030 [P] [US4] Create `apps/server/src/services/tts.py` — generate_speech() async function using httpx POST to ElevenLabs /v1/text-to-speech/{voice_id} with voice map for es/zh/fr/en
- [x] T031 [US4] Create `apps/server/src/tests/test_phase4_elevenlabs.py` — created, ready to run

**Checkpoint**: ElevenLabs TTS returns audio. `uv run pytest src/tests/test_phase4_elevenlabs.py -v -s` passes.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Final validation across all stories

- [ ] T032 Run all 4 test suites together: `uv run pytest src/tests/ -v -s -k "phase1 or phase2 or phase3 or phase4"` — all pass with timestamps
- [ ] T033 Validate quickstart.md instructions by running manual verification steps

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies — start immediately
- **Phase 2 (Foundational)**: Depends on Phase 1 — BLOCKS all user stories
- **Phase 3 (US1 - Models)**: Depends on Phase 2 — no other story dependencies
- **Phase 4 (US2 - Supabase)**: Depends on Phase 2 + Phase 3 (models used by StateManager)
- **Phase 5 (US3 - Mistral)**: Depends on Phase 2 only — can run in parallel with US1/US2
- **Phase 6 (US4 - ElevenLabs)**: Depends on Phase 2 only — can run in parallel with US1/US2/US3
- **Phase 7 (Polish)**: Depends on all user stories complete

### User Story Dependencies

- **US1 (Models)**: Depends on Phase 2 only. No dependencies on other stories.
- **US2 (Supabase)**: Depends on US1 (models used by StateManager).
- **US3 (Mistral)**: Independent of other stories. Only needs Phase 2 config.
- **US4 (ElevenLabs)**: Independent of other stories. Only needs Phase 2 config.

### Parallel Opportunities

- T010-T014: All 5 SQL migration files can be created in parallel
- T017-T022: All 6 model files can be created in parallel
- T025-T026: StateManager and logger can be created in parallel
- T029-T030: Transcription and TTS services can be created in parallel
- US3 and US4 can run in parallel with each other (and with US2 if models are done)

---

## Parallel Example: User Story 1 (Models)

```bash
# Launch all model files in parallel:
Task: "Create incident models in apps/server/src/models/incident.py"
Task: "Create caller models in apps/server/src/models/caller.py"
Task: "Create vision models in apps/server/src/models/vision.py"
Task: "Create triage models in apps/server/src/models/triage.py"
Task: "Create dispatch models in apps/server/src/models/dispatch.py"
Task: "Create event models in apps/server/src/models/events.py"
```

## Parallel Example: User Story 4 (ElevenLabs)

```bash
# Launch both services in parallel:
Task: "Create transcription service in apps/server/src/services/transcription.py"
Task: "Create TTS service in apps/server/src/services/tts.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (user provides env values + runs SQL)
3. Complete Phase 3: US1 (Models) — all models validate
4. **STOP and VALIDATE**: `uv run pytest src/tests/test_phase1_models.py -v -s`

### Incremental Delivery

1. Setup + Foundational → Foundation ready
2. US1 (Models) → Test → First checkpoint
3. US2 (Supabase) → Test → State management working
4. US3 (Mistral) + US4 (ElevenLabs) in parallel → Test → All APIs connected
5. Polish → Full test suite passes

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- T015 and T016 are USER ACTION tasks — implementation pauses until user provides env values and runs SQL
- All test files must log `[elapsed]` timestamps per operation and total summary at the end
- Use `result.output` (NOT `result.data`) when accessing pydantic-ai agent results
- Follow exact code from PRD `docs/PROCESS/260228_1545_TRIAGENET_UPDATED_PRD.md` for all models and services
