# Feature Specification: Orchestrator & API

**Feature Branch**: N/A (hackathon mode — working on main)
**Created**: 2026-02-28
**Status**: Draft

## User Scenarios & Testing

### User Story 1 - FastAPI Server Starts and Health Check Passes (Priority: P1)

The server starts with `uvicorn` and responds to health checks that verify Supabase, Mistral, and ElevenLabs connectivity.

**Independent Test**: `curl http://localhost:8000/api/v1/health` returns all checks "ok"

### User Story 2 - Demo Orchestrator Runs Full Sequence (Priority: P1)

POST to `/api/v1/demo/start` kicks off the 120-second choreographed demo. The orchestrator drives all timed events, calling agents and writing state to Supabase.

**Independent Test**: Start server, POST `/demo/start`, verify state changes in Supabase

### User Story 3 - Operator Approval Flow (Priority: P1)

POST to `/api/v1/demo/approve` unblocks the orchestrator's Phase 2, confirming dispatch of recommended units.

## Requirements

- **FR-001**: System MUST provide FastAPI app with CORS for localhost:3000
- **FR-002**: System MUST provide /health, /demo/start, /demo/approve, /demo/status endpoints
- **FR-003**: Orchestrator MUST use `result.output` (NOT `result.data`) for all agent calls
- **FR-004**: Orchestrator MUST run as background task (non-blocking /demo/start)
- **FR-005**: System MUST provide media.py for frame extraction from video files

## Success Criteria

- **SC-001**: Server starts without errors
- **SC-002**: Health check returns all services "ok"
- **SC-003**: Demo start returns case_id and status "started"
