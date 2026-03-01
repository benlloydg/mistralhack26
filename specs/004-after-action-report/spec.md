# Feature Specification: After-Action Report (Backend)

**Feature Branch**: `004-after-action-report`
**Created**: 2026-03-01
**Status**: Draft
**Input**: After-action report backend — pre-structured report data endpoint, executive summary generation via Mistral, vision frame persistence. Frontend built separately by another team.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Generate and view a complete case report (Priority: P1)

After the demo completes, the presenter clicks GENERATE REPORT. The backend produces a fully structured report JSON containing all 8 sections (header, timeline, evidence sources, convergence data, response actions, agent stats, key frames, executive summary). The frontend renders this as a polished after-action report at a shareable URL.

**Why this priority**: This is the core deliverable — the mic-drop moment at the end of the demo and the artifact judges examine independently.

**Independent Test**: Call `POST /cases/{case_id}/report` after a demo run, verify it returns a complete JSON with all sections populated, including a Mistral-generated executive summary.

**Acceptance Scenarios**:

1. **Given** a completed demo with case_id in resolved_demo status, **When** `POST /cases/{case_id}/report` is called, **Then** the endpoint returns a structured JSON containing header, timeline, evidence_sources, convergence_tracks, response_actions, agent_stats, key_frames, and executive_summary sections.
2. **Given** a completed demo, **When** the report is generated for the first time, **Then** Mistral Large generates a 3-4 sentence executive summary emphasizing cross-modal fusion and evacuation outcome, and the summary is cached for subsequent requests.
3. **Given** a report has already been generated for a case, **When** `POST /cases/{case_id}/report` is called again, **Then** the cached executive summary is returned without re-invoking Mistral.

---

### User Story 2 - Vision frames saved during demo for report rendering (Priority: P1)

During the demo, whenever the vision agent extracts and analyzes a video frame, the JPEG bytes are saved to disk so the report page can display them as key frame images with detection annotations.

**Why this priority**: The key frames section — especially the fire detection frame with the 0.99 confidence — is the hero visual of the report. Without saved frames, this section is empty.

**Independent Test**: Run a demo, verify JPEG files appear in `assets/frames/` at each vision extraction timestamp, and verify the report JSON includes URLs pointing to those frames.

**Acceptance Scenarios**:

1. **Given** the orchestrator extracts a video frame for vision analysis, **When** the frame is sent to the vision agent, **Then** the JPEG is also saved to `assets/frames/{case_id}_t{timestamp}s.jpg`.
2. **Given** saved frames exist for a case, **When** the report endpoint is called, **Then** the `key_frames` section includes entries with `image_url`, `timestamp`, `detections`, and `description` for each frame.
3. **Given** no frames were saved (e.g., video unavailable), **When** the report is called, **Then** the `key_frames` section returns empty array and the report is still valid.

---

### User Story 3 - Report data serves as contract for frontend team (Priority: P2)

The report JSON structure serves as a clear API contract so the frontend team can build the report page independently. Every section is pre-computed — the frontend only needs to render, not compute.

**Why this priority**: Enables parallel development. The frontend team should never need to query Supabase directly or do data transformation for the report page.

**Independent Test**: Validate the JSON schema includes all fields the frontend needs for every section defined in the PRD (header metadata, timeline events with icons/colors, evidence breakdown, agent invocation counts, frame URLs, summary text).

**Acceptance Scenarios**:

1. **Given** the report JSON, **When** the frontend renders each section, **Then** no additional API calls or data transformations are required.
2. **Given** the report JSON timeline section, **When** the frontend renders it, **Then** each event includes timestamp, source, agent/model name, event type, message, severity level, and icon hint (regular/critical/operator).

---

### Edge Cases

- What happens when `POST /cases/{case_id}/report` is called for a case that doesn't exist? Return 404.
- What happens when the report is requested for an in-progress (not yet resolved) demo? Return the report with current data and a warning field indicating the demo is still running.
- What happens when Mistral is unavailable for executive summary generation? Return the report with a fallback summary from the operator_summary field in incident_state.
- What happens when no transcripts or dispatches exist? Return the report with empty arrays — the structure remains valid.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST provide a `POST /cases/{case_id}/report` endpoint that returns a pre-structured JSON containing all 8 report sections.
- **FR-002**: System MUST generate an executive summary via Mistral Large (3-4 sentences, factual, emphasizing cross-modal fusion and outcome).
- **FR-003**: System MUST cache the generated executive summary so subsequent requests don't re-invoke Mistral. Cache keyed by case_id.
- **FR-004**: System MUST save vision frame JPEGs to disk during the demo at `assets/frames/{case_id}_t{timestamp}s.jpg`.
- **FR-005**: System MUST serve saved frames via a static file mount at `/frames/{filename}`.
- **FR-006**: The `header` section MUST include: case_id, incident_type, location, severity, status, duration, speaker_count, languages list, evidence counts (audio segments, vision frames), outcome text, and generation timestamp.
- **FR-007**: The `timeline` section MUST include chronologically ordered events, each with: elapsed timestamp, source agent, model name, event type, message, severity indicator (regular/critical/operator), and display color.
- **FR-008**: The `evidence_sources` section MUST include: audio summary (speaker count, languages, transcript count, key intelligence per speaker) and vision summary (frames analyzed, detections with timestamps and confidences).
- **FR-009**: The `convergence_tracks` section MUST include per-source event tracks (one per language + one for vision + one fused) with event markers at timestamps, for the frontend to render a multi-track visualization.
- **FR-010**: The `response_actions` section MUST include: each action with type, status, authorization timestamp, authorization method (operator vs autonomous), and unit details.
- **FR-011**: The `agent_stats` section MUST include: per-agent invocation count, model used, and average latency. Also total invocations and models-used list.
- **FR-012**: The `key_frames` section MUST include: image URL, extraction timestamp, detection list with types and confidences, and overall description for each saved frame.
- **FR-013**: The `executive_summary` section MUST include the Mistral-generated text.
- **FR-014**: A `GET /cases/{case_id}/report` endpoint MUST also work (returns cached report or 404 if not yet generated).

### Key Entities

- **ReportData**: The top-level structured response containing all 8 sections, assembled on-demand from existing data.
- **ExecutiveSummary**: A cached text blob generated by Mistral, stored per case_id.
- **KeyFrame**: A saved JPEG image with associated detection metadata and timestamp.
- **ConvergenceTrack**: A per-source event list with timestamps and labels, used for the multi-track visualization.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Report endpoint returns complete structured JSON within 5 seconds for any completed demo case (including first-time summary generation).
- **SC-002**: Subsequent report requests for the same case return within 500ms (cached summary, no Mistral call).
- **SC-003**: All 8 report sections are populated with real data from a completed demo — no empty sections except key_frames when video is unavailable.
- **SC-004**: Vision frames saved during demo are accessible via URL and render correctly.
- **SC-005**: Executive summary accurately references the actual incident data (correct casualty count, language count, hazard types, outcome).

## Assumptions

- Frontend team builds the report page UI independently, consuming the JSON contract this backend provides.
- Frame storage uses local disk + static file mount (same pattern as TTS audio), not cloud storage.
- Executive summary cache is in-memory (dict keyed by case_id) — sufficient for hackathon demo, no persistence across restarts.
- Convergence tracks section provides raw event data; the frontend renders the visualization.
- The report reads from existing tables (incident_state, agent_logs, transcripts, dispatches) — no new database tables required.
