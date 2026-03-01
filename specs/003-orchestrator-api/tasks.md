# Tasks: Orchestrator & API

## Phase 1: Core Files

- [x] T001 [P] Create `apps/server/src/services/media.py` — extract_frame() for video frame extraction
- [x] T002 [P] Create `apps/server/src/services/orchestrator.py` — DemoOrchestrator with all 7 phases
- [x] T003 [P] Create `apps/server/src/routes/health.py` — health check endpoint (Supabase, Mistral, ElevenLabs)
- [x] T004 [P] Create `apps/server/src/routes/demo.py` — /demo/start, /demo/approve, /demo/status
- [x] T005 Create `apps/server/src/main.py` — FastAPI app with CORS + router includes

## Phase 2: Tests

- [x] T006 Create `apps/server/src/tests/test_phase6_orchestrator.py` — 4/4 passed (health check all services ok)
- [x] T007 Run tests and save logs to test-results/
