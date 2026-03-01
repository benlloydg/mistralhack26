# Feature Specification: Pydantic-AI Agent Definitions

**Feature Branch**: `002-pydantic-agents`
**Created**: 2026-02-28
**Status**: Draft
**Input**: Pydantic-AI agent definitions for TriageNet: triage, intake, vision, dispatch, case-match agents with structured outputs

## User Scenarios & Testing

### User Story 1 - Intake Agent Extracts Facts from Caller Transcripts (Priority: P1)

When a caller's transcript (in any language) is passed to the intake agent, it extracts structured emergency facts: location, incident type, whether someone is trapped, child presence, injuries, hazards, and urgency keywords.

**Why this priority**: The intake agent is the entry point for all caller data. Without it, no facts flow into the system.

**Independent Test**: Run `uv run pytest src/tests/test_phase5_agents.py -v -s -k intake` — intake agent returns valid IntakeFacts with correct fields populated.

**Acceptance Scenarios**:

1. **Given** a Spanish emergency transcript mentioning a crash with trapped person, **When** intake agent processes it, **Then** it returns IntakeFacts with `possible_trapped_person=True` and a valid `location_raw`
2. **Given** a transcript with no child mentioned, **When** intake agent processes it, **Then** `child_present=False`

---

### User Story 2 - Triage Agent Classifies Severity (Priority: P1)

The triage agent reads incident state from Supabase (via tools) and produces a TriageResult with severity classification, recommended units, and action plan.

**Why this priority**: Triage is the core decision engine. All dispatch depends on its output.

**Independent Test**: Run `uv run pytest src/tests/test_phase5_agents.py -v -s -k triage` — returns valid TriageResult with severity HIGH or CRITICAL for a crash scenario.

**Acceptance Scenarios**:

1. **Given** incident state with a vehicle crash and injuries, **When** triage runs, **Then** severity is HIGH or CRITICAL and recommended_units includes EMS
2. **Given** a trapped person report, **When** triage runs, **Then** severity NEVER downgrades

---

### User Story 3 - Dispatch Agent Generates Briefings (Priority: P1)

Given incident details, the dispatch agent generates a DispatchBrief with unit callsign, ETA, voice message (under 40 words for TTS), and rationale.

**Why this priority**: Dispatch briefs are visible to judges and generate TTS audio.

**Independent Test**: Run `uv run pytest src/tests/test_phase5_agents.py -v -s -k dispatch` — returns valid DispatchBrief.

**Acceptance Scenarios**:

1. **Given** incident type and location, **When** dispatch agent runs, **Then** returns non-empty unit_assigned, voice_message, and eta_minutes > 0

---

### User Story 4 - Vision Agent Analyzes CCTV Frames (Priority: P2)

The vision agent uses the native Mistral SDK (not pydantic-ai) to analyze CCTV frames via Pixtral and returns typed FrameAnalysis with detections, hazard info, and scene description.

**Why this priority**: Vision adds corroboration but isn't on the critical path for the first demo phase.

**Independent Test**: Run `uv run pytest src/tests/test_phase5_agents.py -v -s -k vision` — returns valid FrameAnalysis from a test image.

**Acceptance Scenarios**:

1. **Given** a JPEG frame of a traffic scene, **When** vision agent analyzes it, **Then** returns FrameAnalysis with detections list and overall_description

---

### User Story 5 - Evidence Fusion Agent Corroborates Claims (Priority: P2)

The evidence fusion agent cross-references all caller transcripts and vision detections to find corroborated facts and determine if severity should change or evacuation is needed.

**Why this priority**: Adds depth to the demo but depends on other agents running first.

**Independent Test**: Run `uv run pytest src/tests/test_phase5_agents.py -v -s -k evidence` — returns valid EvidenceFusionResult.

**Acceptance Scenarios**:

1. **Given** multiple evidence sources, **When** fusion agent runs, **Then** returns EvidenceFusionResult with reasoning

---

### Edge Cases

- What happens when Mistral returns malformed JSON? pydantic-ai retries automatically with validation error feedback
- What happens when Supabase is unreachable during tool call? Tool raises exception, agent surfaces error
- What happens when vision model receives non-image input? Mistral returns error, caught in try/except

## Requirements

### Functional Requirements

- **FR-001**: System MUST define 5 agents (triage, intake, vision, dispatch, case_match) with correct output types
- **FR-002**: All pydantic-ai agents MUST use `TriageNetDeps` as `deps_type`
- **FR-003**: Agents with tools MUST use `RunContext[TriageNetDeps]` for Supabase access
- **FR-004**: Vision agent MUST use native `mistralai` client (NOT pydantic-ai) for multimodal content
- **FR-005**: All agents MUST return typed Pydantic models as structured output
- **FR-006**: Agent results MUST be accessed via `result.output` (NOT `result.data`)
- **FR-007**: System MUST include test suite with timing/timestamps per operation
- **FR-008**: Each agent call MUST complete in under 8 seconds

### Key Entities

- **TriageResult**: Severity, incident type, reasoning, recommended units, action plan
- **IntakeFacts**: Location, incident type, trapped person, child present, injuries, hazards
- **FrameAnalysis**: Detections list, scene description, hazard escalation, smoke/fire flags
- **DispatchBrief**: Unit callsign, ETA, voice message, rationale
- **EvidenceFusionResult**: Corroborations, severity delta, evacuation warning

## Success Criteria

### Measurable Outcomes

- **SC-001**: All 5 agent test cases pass with structured output validation
- **SC-002**: Each agent call completes in under 8 seconds
- **SC-003**: Intake agent correctly identifies trapped persons when mentioned in transcript
- **SC-004**: Triage agent classifies crash-with-injuries as HIGH or CRITICAL severity
- **SC-005**: Dispatch agent generates voice messages under 40 words
