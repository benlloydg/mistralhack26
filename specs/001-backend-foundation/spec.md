# Feature Specification: Backend Foundation

**Feature Branch**: `001-backend-foundation`
**Created**: 2026-02-28
**Status**: Draft
**Input**: User description: "Backend foundation: models, config, Supabase state manager, Mistral and ElevenLabs API connectivity"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Data Models Validate Correctly (Priority: P1)

As a developer building TriageNet agents, I need a complete set of domain models (incident state, callers, vision detections, triage results, dispatches, agent logs) so that all data flowing through the system has a shared, validated schema.

**Why this priority**: Every other component (agents, orchestrator, frontend) depends on these models. Without them, nothing can be built.

**Independent Test**: Can be fully tested by instantiating each model with valid and invalid data and verifying validation passes/fails as expected.

**Acceptance Scenarios**:

1. **Given** a valid incident payload, **When** creating an IncidentState model, **Then** all fields are correctly typed and defaults are applied
2. **Given** an invalid severity value, **When** creating an IncidentState, **Then** a validation error is raised
3. **Given** a caller record with transcript segments, **When** serialized to JSON, **Then** it produces the schema expected by the database

---

### User Story 2 - Supabase State Management (Priority: P1)

As the orchestrator, I need to read and write incident state to the database so that state changes are persisted and broadcast to the frontend in real-time.

**Why this priority**: The database is the central data bus — agents write, frontend reads. Without this, the system has no persistence or real-time capability.

**Independent Test**: Can be tested by writing an incident state row, reading it back, updating it, and verifying the round-trip with timestamps.

**Acceptance Scenarios**:

1. **Given** a new demo session, **When** the state manager creates an incident record, **Then** the record appears in the database with correct defaults
2. **Given** an existing incident, **When** the state manager updates severity, **Then** the updated_at timestamp auto-updates and the new severity is persisted
3. **Given** the state manager, **When** writing an agent log entry, **Then** the entry appears in the agent_logs table with correct case_id linkage

---

### User Story 3 - Mistral API Connectivity (Priority: P2)

As an agent developer, I need verified connectivity to Mistral models (Large for triage, Small for vision) so that agents can call the LLM for inference.

**Why this priority**: Agents depend on Mistral connectivity. Testing it early prevents debugging API issues during agent development.

**Independent Test**: Can be tested by sending a simple prompt to Mistral and verifying a structured response is returned, with timing recorded.

**Acceptance Scenarios**:

1. **Given** valid Mistral API credentials, **When** sending a test prompt, **Then** a response is returned within 10 seconds
2. **Given** a pydantic-ai agent configured with Mistral, **When** running with a structured output type, **Then** the response validates against the output schema

---

### User Story 4 - ElevenLabs API Connectivity (Priority: P2)

As an agent developer, I need verified connectivity to ElevenLabs for transcription and text-to-speech so that voice processing works during the demo.

**Why this priority**: Voice processing is a core demo feature but is testable independently from the main agent logic.

**Independent Test**: Can be tested by transcribing a short audio clip and generating a TTS audio response, with timing recorded.

**Acceptance Scenarios**:

1. **Given** valid ElevenLabs credentials and an audio file, **When** submitting for transcription, **Then** transcribed text is returned
2. **Given** valid ElevenLabs credentials and text input, **When** requesting TTS generation, **Then** audio bytes are returned

---

### Edge Cases

- What happens when the database is unreachable? The state manager should raise a clear connection error.
- What happens when API keys are missing or invalid? Config validation should fail at startup with descriptive errors naming the missing variables.
- What happens when Mistral returns an unexpected response format? The agent framework's built-in retry mechanism should handle validation failures.
- What happens when a duplicate case_id is inserted? The database's UNIQUE constraint should reject it with a clear error.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST define validated data models for all domain entities: incidents, callers, vision detections, triage results, dispatches, and agent log entries
- **FR-002**: System MUST load configuration from environment variables with validation at startup — missing required values must cause an immediate, descriptive error
- **FR-003**: System MUST provide a state management service that can create, read, and update incident state records in the database
- **FR-004**: System MUST provide an agent logging service that writes structured log entries to the database, linked to a case_id
- **FR-005**: System MUST provide a transcription service that accepts audio files and returns transcribed text
- **FR-006**: System MUST provide a text-to-speech service that accepts text and returns generated audio
- **FR-007**: System MUST establish verified connectivity to Mistral models (Large and Small) via both the agent framework and native client
- **FR-008**: System MUST define a shared agent dependencies bundle that combines database client, Mistral client, and session context for injection into agents
- **FR-009**: System MUST generate database migration scripts for 4 tables (incident_state, agent_logs, transcripts, dispatches) plus real-time subscription enablement
- **FR-010**: All tests MUST log timestamps and elapsed time for each operation, with a total summary at the end

### Key Entities

- **IncidentState**: The central record for a case — tracks severity, status, location, caller count, hazard/injury flags, vision detections, recommended/confirmed units, action plan, and timeline events
- **CallerRecord / TranscriptSegment / IntakeFacts**: Represent individual callers, their transcript segments (bilingual), and extracted facts (entities, injuries, locations)
- **VisionDetection / FrameAnalysis**: Represent objects detected in CCTV footage with confidence scores and scene-level analysis
- **TriageResult / ActionPlan / ActionItem**: Represent the triage agent's severity assessment, corroboration reasoning, and recommended action items
- **DispatchRecord / DispatchBrief**: Represent dispatched units with type, assignment, destination, ETA, status, and voice message
- **AgentLogEntry / TimelineEvent**: Represent structured log entries from agents and timeline events on the incident

### Assumptions

- Supabase project is pre-provisioned and Realtime is enabled by the user
- API keys for Mistral and ElevenLabs are valid and have sufficient quota
- Python 3.12+ is available on the development machine
- uv package manager is installed

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All domain models can be instantiated with valid data and correctly reject invalid data — 100% of model tests pass
- **SC-002**: State manager can complete a create-read-update cycle on the database in under 2 seconds
- **SC-003**: Mistral connectivity test returns a valid response within 10 seconds
- **SC-004**: ElevenLabs transcription returns text from a test audio file within 15 seconds
- **SC-005**: ElevenLabs TTS returns audio bytes from test text within 10 seconds
- **SC-006**: Configuration validation catches missing environment variables at startup and reports which ones are missing
- **SC-007**: All 4 phase test suites (models, database, mistral, elevenlabs) pass in a single test run with timing logged for every operation
