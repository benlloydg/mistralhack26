# Tasks: Pydantic-AI Agent Definitions

**Input**: Design documents from `/specs/002-pydantic-agents/`
**Prerequisites**: Feature 001-backend-foundation complete (models, config, shared_deps)

**Tests**: YES — test_phase5_agents.py with timestamps/timing per operation.

## Phase 1: Agent Implementations

- [x] T001 [P] [US1] Create `apps/server/src/agents/intake_agent.py` — pydantic-ai Agent with IntakeFacts output type, TriageNetDeps deps_type, system prompt for multilingual fact extraction
- [x] T002 [P] [US2] Create `apps/server/src/agents/triage_agent.py` — pydantic-ai Agent with TriageResult output type, 3 tools (get_current_state, get_all_transcripts, get_vision_detections)
- [x] T003 [P] [US3] Create `apps/server/src/agents/dispatch_agent.py` — pydantic-ai Agent with DispatchBrief output type, 1 tool (get_case_summary)
- [x] T004 [P] [US5] Create `apps/server/src/agents/case_match_agent.py` — pydantic-ai Agent with EvidenceFusionResult output type, 1 tool (get_all_evidence)
- [x] T005 [P] [US4] Create `apps/server/src/agents/vision_agent.py` — Native mistralai SDK for Pixtral vision: analyze_frame() and compute_scene_delta()

## Phase 2: Exports & Tests

- [x] T006 Update `apps/server/src/agents/__init__.py` — re-export all agents
- [x] T007 Create `apps/server/src/tests/test_phase5_agents.py` — 5 test cases (intake, triage, dispatch, vision, evidence fusion) with TimedStep timing

## Phase 3: Validation

- [x] T008 Run `uv run pytest src/tests/test_phase5_agents.py -v -s` — 5/5 tests passed (intake 1.9s, dispatch 3.2s, fusion 11s, vision deltas <1ms)
