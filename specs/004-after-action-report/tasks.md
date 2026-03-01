# Tasks: After-Action Report (Backend)

**Input**: Design documents from `/specs/004-after-action-report/`
**Prerequisites**: plan.md, spec.md, data-model.md, contracts/report-api.md, research.md, quickstart.md

**Tests**: Included — spec requires E2E tests with timestamps per CLAUDE.md.

**Organization**: Tasks grouped by user story for independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup

**Purpose**: Create project structure for report feature — new files and directories only.

- [x] T001 Create `apps/server/assets/frames/` directory with `.gitkeep`
- [x] T002 [P] Create empty `apps/server/src/models/report.py` module
- [x] T003 [P] Create empty `apps/server/src/services/report_builder.py` module

---

## Phase 2: Foundational (Pydantic Models)

**Purpose**: Define all Pydantic models for the report response. These are used by every user story.

**CRITICAL**: No user story work can begin until models are complete.

- [x] T004 Define all Pydantic report models in `apps/server/src/models/report.py`: ReportData, ReportHeader, TimelineEntry, AudioSummary, SpeakerSummary, VisionSummary, VisionDetectionEntry, CrossModalSummary, EvidenceSources, ConvergenceTrack, TrackEvent, ResponseAction, AgentStats, AgentUtilization, ModelUsage, KeyFrame — per `data-model.md`
- [x] T005 Verify models import correctly: `uv run python -c "from src.models.report import ReportData; print('OK')"`

**Checkpoint**: All 15+ Pydantic models defined and importable.

---

## Phase 3: User Story 2 — Vision Frames Saved During Demo (Priority: P1)

**Goal**: Save JPEG frames to disk during demo so the report can display them as key frame images.

**Independent Test**: Run a demo, verify JPEG files appear in `assets/frames/` directory.

### Tests for User Story 2

- [x] T006 [US2] Write test for frame saving in `apps/server/src/tests/test_report.py` — mock `extract_frame()` return bytes, verify file written to `assets/frames/{case_id}_t{ts}s.jpg`

### Implementation for User Story 2

- [x] T007 [US2] Modify `apps/server/src/services/orchestrator.py` `_run_vision()` — after `extract_frame()` at both Frame 1 and Frame 2 extraction points, save JPEG bytes to `assets/frames/{case_id}_t{int(timestamp_s)}s.jpg` with `os.makedirs("assets/frames", exist_ok=True)`
- [x] T008 [US2] Add `/frames` static mount in `apps/server/src/main.py` — `app.mount("/frames", StaticFiles(directory=FRAMES_DIR), name="frames")` following the existing `/audio` mount pattern

**Checkpoint**: Frame saving works independently — demo produces JPEGs in `assets/frames/`, accessible via `/frames/` URL.

---

## Phase 4: User Story 1 — Generate Complete Case Report (Priority: P1)

**Goal**: Build the report assembly service and endpoints that produce a full structured JSON report from Supabase data.

**Independent Test**: Call `POST /cases/{case_id}/report` after a demo, verify all 8 sections populated.

### Tests for User Story 1

- [x] T009 [US1] Write test for `ReportBuilder.build()` in `apps/server/src/tests/test_report.py` — mock Supabase queries (incident_state, agent_logs, transcripts, dispatches), verify all 8 sections returned with correct types
- [x] T010 [US1] Write test for executive summary caching in `apps/server/src/tests/test_report.py` — verify Mistral called once, second `build()` returns cached summary without API call

### Implementation for User Story 1

- [x] T011 [US1] Implement `ReportBuilder.__init__()` and `build()` method in `apps/server/src/services/report_builder.py` — accept supabase client and mistral client, run 4 Supabase queries (incident_state, agent_logs, transcripts, dispatches), delegate to `_build_*` methods
- [x] T012 [US1] Implement `_build_header()` in `apps/server/src/services/report_builder.py` — extract case_id, incident_type, location, severity, status, duration, speaker_count, languages, audio_segments, vision_frames, outcome from state and transcripts
- [x] T013 [US1] Implement `_build_timeline()` in `apps/server/src/services/report_builder.py` — transform agent_logs rows to TimelineEntry objects with elapsed time, severity_indicator mapping (evidence_fusion/CROSS_MODAL* → critical, orchestrator/approved → operator, else regular), color assignment
- [x] T014 [US1] Implement `_build_evidence_sources()` in `apps/server/src/services/report_builder.py` — build AudioSummary (group transcripts by feed_id/language, count segments, extract key_intelligence) and VisionSummary (from vision_detections in state) and CrossModalSummary (from CROSS_MODAL logs)
- [x] T015 [US1] Implement `_build_convergence_tracks()` in `apps/server/src/services/report_builder.py` — group transcripts by language → audio tracks, extract vision events from agent_logs where agent="vision", build fused track from triage state changes
- [x] T016 [US1] Implement `_build_response_actions()` in `apps/server/src/services/report_builder.py` — transform dispatches rows to ResponseAction objects with action, unit_type, unit_assigned, status, authorized_at (elapsed), authorization_method
- [x] T017 [US1] Implement `_build_agent_stats()` in `apps/server/src/services/report_builder.py` — group agent_logs by agent, count rows, estimate avg latency from timestamp gaps, build models_used list
- [x] T018 [US1] Implement `_build_key_frames()` in `apps/server/src/services/report_builder.py` — glob `assets/frames/{case_id}_*.jpg`, match with vision_detections from state, flag fire detection frame as is_hero=True
- [x] T019 [US1] Implement `_generate_executive_summary()` in `apps/server/src/services/report_builder.py` — prompt Mistral Large with full state + transcript + dispatch context, cache result in `_summary_cache` dict keyed by case_id, fallback to operator_summary if Mistral fails
- [x] T020 [US1] Add `POST /api/v1/cases/{case_id}/report` endpoint in `apps/server/src/routes/report.py` — instantiate ReportBuilder, call `build()`, return `report.model_dump()`. Return 404 if case not found.
- [x] T021 [US1] Add `GET /api/v1/cases/{case_id}/report` endpoint in `apps/server/src/routes/report.py` — return cached report if exists, 404 otherwise

**Checkpoint**: Full report JSON returned from endpoint with all 8 sections populated from real demo data.

---

## Phase 5: User Story 3 — API Contract Validation (Priority: P2)

**Goal**: Validate the report JSON structure matches the contract in `contracts/report-api.md` so the frontend team can render without additional API calls.

**Independent Test**: Validate JSON schema completeness against the contract document.

### Implementation for User Story 3

- [x] T022 [US3] Write contract validation test in `apps/server/src/tests/test_report.py` — generate a report from mock data, validate every field defined in `contracts/report-api.md` is present: header (10 fields), timeline entries (9 fields each), evidence_sources (audio/vision/cross_modal), convergence_tracks (4 fields + events), response_actions (7 fields each), agent_stats (4 top-level + agent/model arrays), key_frames (6 fields each), executive_summary (string)
- [x] T023 [US3] Validate timeline entry severity_indicator values are one of ["regular", "critical", "operator"] and color values are one of ["blue", "green", "amber", "red", "purple"] in test
- [x] T024 [US3] Validate convergence_tracks event types are one of ["detection", "escalation", "action", "state_change"] and track types are one of ["audio", "vision", "fused"] in test

**Checkpoint**: Contract tests prove the JSON schema is complete and correct for frontend consumption.

---

## Phase 6: E2E Testing & Polish

**Purpose**: End-to-end test with timing, cross-story validation, and test result logging.

- [x] T025 Write E2E test in `apps/server/src/tests/test_report.py` — full integration: mock a completed case in Supabase, call POST endpoint, verify <5s first response, call again, verify <500ms cached response. Print elapsed time per step per CLAUDE.md requirements.
- [x] T026 Run all report tests via `PYTHONPATH=. uv run pytest src/tests/test_report.py -v -s` and save output to `apps/server/test-results/` with naming format `YYYYMMDD_HHMMSS_report_e2e.log`
- [x] T027 Run full test suite `PYTHONPATH=. uv run pytest src/tests/ -v` to verify no regressions

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 — BLOCKS all user stories
- **US2 — Frame Saving (Phase 3)**: Depends on Phase 2. Can run in parallel with US1.
- **US1 — Report Generation (Phase 4)**: Depends on Phase 2. Can run in parallel with US2.
- **US3 — Contract Validation (Phase 5)**: Depends on Phase 4 (needs working report builder)
- **E2E & Polish (Phase 6)**: Depends on Phases 3, 4, and 5

### User Story Dependencies

- **US2 (Frame Saving)**: Independent — only modifies orchestrator.py and main.py
- **US1 (Report Generation)**: Independent — US2 enhances key_frames section but US1 works with empty key_frames if US2 not done
- **US3 (Contract Validation)**: Depends on US1 — validates the output of the report builder

### Within Each User Story

- Models (Phase 2) before services
- Services before endpoints
- Tests written alongside implementation (not strict TDD — practical hackathon pace)

### Parallel Opportunities

- T002 and T003 (empty file creation) can run in parallel
- T007 and T008 (frame saving + static mount) are in different files, can run in parallel
- US1 (Phase 4) and US2 (Phase 3) can run in parallel after Phase 2
- T012–T019 (_build_* methods) are independent methods in the same file — implement sequentially but each is self-contained

---

## Parallel Example: Phase 3 + Phase 4 After Foundational

```bash
# After Phase 2 models are complete, launch US2 and US1 in parallel:

# US2 — Frame saving (different files from US1):
Task: "Modify orchestrator.py _run_vision() to save frames"
Task: "Add /frames static mount in main.py"

# US1 — Report builder (different files from US2):
Task: "Implement ReportBuilder.build() in report_builder.py"
Task: "Add POST/GET report endpoints in routes/report.py"
```

---

## Implementation Strategy

### MVP First (US1 + US2 Together)

1. Complete Phase 1: Setup (create files/dirs)
2. Complete Phase 2: Foundational (Pydantic models)
3. Complete Phase 3: US2 (frame saving) — quick, 2 tasks
4. Complete Phase 4: US1 (report builder + endpoints) — main work
5. **STOP and VALIDATE**: `curl -X POST .../report` returns full JSON
6. Complete Phase 5: US3 (contract validation tests)
7. Complete Phase 6: E2E tests + logging

### Estimated Task Distribution

- **Phase 1**: 3 tasks (trivial)
- **Phase 2**: 2 tasks (models — medium complexity)
- **Phase 3 (US2)**: 3 tasks (frame saving — low complexity)
- **Phase 4 (US1)**: 13 tasks (report builder — high complexity, most logic)
- **Phase 5 (US3)**: 3 tasks (contract validation — medium complexity)
- **Phase 6**: 3 tasks (E2E + regression)
- **Total**: 27 tasks

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- US2 is listed before US1 because frame saving is simpler and enhances US1's key_frames section
- Report builder (T011–T019) is the largest chunk — 9 methods implementing the 8 report sections + caching
- No new database tables — all data read from existing incident_state, agent_logs, transcripts, dispatches
- Executive summary cache is in-memory dict — resets on server restart (acceptable for hackathon)
