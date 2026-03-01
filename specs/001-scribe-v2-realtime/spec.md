# Feature Specification: Scribe v2 Realtime Integration

**Feature Branch**: `001-scribe-v2-realtime`
**Created**: 2026-02-28
**Status**: Draft
**Input**: Replace pre-recorded audio files with real-time audio extraction from the demo video, using continuous speech-to-text with automatic language detection. Committed transcripts feed the existing agent pipeline. Vision runs in parallel. Evacuation warnings generated via text-to-speech when hazards detected.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Live Audio Transcription from Video (Priority: P1)

When a demo operator starts the demo, the system extracts the audio track from the single demo video file and streams it to a real-time speech-to-text service. The service performs continuous transcription with automatic language detection (Spanish, Mandarin, French). Each completed speech segment is committed as a transcript and passed to the existing agent pipeline for fact extraction, evidence fusion, and severity computation. The operator sees transcripts appear in the dashboard as they are spoken in the video — not all at once from pre-recorded files.

**Why this priority**: This is the core value of the feature — replacing simulated pre-recorded audio with a real-time streaming pipeline. Without this, the demo cannot show live transcription from a single video source.

**Independent Test**: Can be fully tested by starting the demo, letting the video play, and verifying that transcripts appear progressively in the dashboard with correct language labels and translated text. The agent pipeline updates severity and action plans as each transcript arrives.

**Acceptance Scenarios**:

1. **Given** a demo video file containing embedded multilingual audio, **When** the operator starts the demo, **Then** the audio track is extracted and streamed to the transcription service in real time (synchronized to video playback speed).
2. **Given** audio is streaming, **When** the transcription service detects a completed speech segment, **Then** a committed transcript is written to the database with the detected language and original text.
3. **Given** a committed transcript in a non-English language, **When** processed by the agent pipeline, **Then** it is translated to English, structured facts are extracted, and the case state is updated (severity, injury flags, hazard flags, recommended units).
4. **Given** multiple speech segments across different languages, **When** all are processed, **Then** each unique language is assigned a distinct feed identifier (first Spanish segment = Feed 1, first Mandarin segment = Feed 2, etc.).

---

### User Story 2 - Live Partial Transcript Display (Priority: P2)

While audio is being streamed and transcribed, the dashboard displays partial (in-progress) transcripts as a "shimmer" or typing effect. This gives the operator immediate visual feedback that the system is actively listening, even before a speech segment is fully committed.

**Why this priority**: Enhances the demo experience by showing real-time activity. Without this, there would be gaps between committed transcripts where the UI appears idle.

**Independent Test**: Can be tested by starting the demo and observing the transcript panel — partial text should appear and update progressively before being replaced by the final committed transcript.

**Acceptance Scenarios**:

1. **Given** audio is being streamed, **When** the transcription service detects ongoing speech, **Then** partial transcript text appears in the dashboard transcript panel with a visual "in-progress" indicator.
2. **Given** a partial transcript is being displayed, **When** the speech segment is committed, **Then** the partial is replaced by the final committed transcript.

---

### User Story 3 - Parallel Vision Pipeline (Priority: P2)

While audio transcription runs, the system independently extracts video frames at scheduled timestamps and analyzes them for hazards (smoke, fire, vehicle damage). Vision detections are written to the same shared case state and trigger the same evidence fusion logic. The audio and vision pipelines do not wait for each other.

**Why this priority**: Demonstrates multi-modal intelligence — the system processes both audio and visual evidence concurrently, fusing them into a unified case picture. This is a key differentiator for the demo.

**Independent Test**: Can be tested by starting the demo and verifying that vision detections appear in the dashboard at the expected video timestamps, independently of when transcripts arrive.

**Acceptance Scenarios**:

1. **Given** a demo is running, **When** the video reaches a scheduled frame extraction timestamp, **Then** a frame is extracted and sent for visual analysis.
2. **Given** a vision analysis detects a hazard (e.g., smoke or fire), **Then** the hazard is logged, the case state is updated with hazard flags, and evidence fusion re-evaluates severity.
3. **Given** both audio and vision pipelines are running, **When** one pipeline detects evidence, **Then** it updates the shared case state without waiting for the other pipeline.

---

### User Story 4 - Automated Evacuation Warnings (Priority: P3)

When evidence fusion determines that an evacuation is warranted (e.g., fire detected combined with people at risk), the system automatically generates text-to-speech evacuation warnings in all languages detected during the demo. These warnings are played/served as audio files and logged as outbound dispatch transcripts.

**Why this priority**: Demonstrates the end-to-end loop — from passive listening to active intervention. This is the "wow moment" of the demo but depends on the transcription and vision pipelines being functional first.

**Independent Test**: Can be tested by running the demo through to the point where fire is detected, then verifying that evacuation warning audio files are generated in each detected language and appear as outbound transcripts in the dashboard.

**Acceptance Scenarios**:

1. **Given** fire has been detected (via vision or audio evidence) and people are known to be at risk, **When** evidence fusion evaluates the combined state, **Then** evacuation warnings are generated as audio in all languages detected during the demo.
2. **Given** an evacuation warning is generated, **Then** it is logged as an outbound dispatch transcript with both the original-language text and an English translation.
3. **Given** evacuation warnings have been generated, **Then** the operator can review them in the dashboard transcript panel, styled distinctly from inbound caller transcripts.

---

### Edge Cases

- What happens when the transcription service returns an empty or whitespace-only transcript? The system ignores it and does not pass it to the agent pipeline.
- What happens when the transcription service connection drops mid-demo? The system attempts to reconnect once. If reconnection fails, the demo continues with vision-only intelligence and logs a connection error to the agent terminal.
- What happens when the video file has no audio track or the audio is silent? The transcription service receives silence, no transcripts are committed, and the demo proceeds with vision-only analysis.
- What happens when the transcription service detects an unsupported language? The system logs the transcript with the detected language code and attempts translation to English as normal.
- What happens when the video file is shorter than expected frame extraction timestamps? Frame extraction at timestamps beyond the video duration is skipped and an informational log is recorded.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST extract the audio track from the demo video file as 16kHz 16-bit mono PCM format before or at demo start.
- **FR-002**: System MUST stream the extracted audio to the transcription service in chunks synchronized to real-time video playback (each chunk represents 250ms of audio).
- **FR-003**: System MUST automatically detect the language of each speech segment (at minimum: Spanish, Mandarin, French).
- **FR-004**: System MUST assign a unique feed identifier to each detected language (first occurrence of a new language creates a new feed).
- **FR-005**: System MUST pass each committed transcript through the agent pipeline: translate to English, extract structured facts, update case state, fuse evidence, compute severity, rebuild action plan.
- **FR-006**: System MUST write partial (in-progress) transcripts to the database so the frontend can display them in real time.
- **FR-007**: System MUST run the vision pipeline (frame extraction + analysis) in parallel with the audio pipeline, without blocking or waiting for audio results.
- **FR-008**: System MUST generate text-to-speech evacuation warnings in all detected languages when fire + people-at-risk conditions are met.
- **FR-009**: System MUST log all agent actions (transcription, fact extraction, severity changes, vision detections, warnings) to the agent activity log with the originating model name.
- **FR-010**: System MUST preserve all demo run data for post-demo report generation (no data is deleted between runs).
- **FR-011**: System MUST support operator approval of recommended dispatch units during the demo via a dedicated approval action.
- **FR-012**: System MUST attempt one reconnection if the transcription service connection drops, then fall back to vision-only mode if reconnection fails.

### Key Entities

- **Transcript**: A speech segment from the audio stream — contains original text, detected language, feed identifier, optional English translation, extracted facts, and direction (inbound from audio vs outbound from dispatch).
- **Feed**: A logical grouping of transcripts by detected language. Each unique language detected creates one feed (e.g., Feed 1 = Spanish, Feed 2 = Mandarin, Feed 3 = French).
- **Partial Transcript**: An in-progress speech segment not yet committed — ephemeral, used only for live display.
- **Case State**: The shared incident state that both audio and vision pipelines write to — includes severity, hazard flags, injury flags, recommended units, vision detections, and action plan version.
- **Vision Detection**: A hazard or object detected in a video frame — type, confidence score, source frame identifier.
- **Dispatch**: A recommended or confirmed emergency response unit — type, callsign, status, rationale.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All three languages (Spanish, Mandarin, French) are correctly detected and labeled during a single demo run, with at least one committed transcript per language.
- **SC-002**: Committed transcripts appear in the dashboard within 3 seconds of the corresponding speech ending in the video.
- **SC-003**: Partial transcripts (in-progress text) update in the dashboard at least once per second while speech is active.
- **SC-004**: Severity escalates correctly through the expected progression (unknown to medium to high to critical) as evidence accumulates from both audio and vision sources.
- **SC-005**: Evacuation warnings are generated in all detected languages within 5 seconds of the fire + people-at-risk condition being met.
- **SC-006**: The full demo completes in under 60 seconds of video playback time.
- **SC-007**: A post-demo report shows the complete audit trail: all transcripts, vision detections, severity changes, dispatches, and agent actions.
- **SC-008**: The demo can be started, completed, and restarted multiple times without data loss from previous runs.

## Assumptions

- The demo video file (`scene.mp4`) contains a pre-produced audio track with multilingual speech segments at known intervals. The audio quality is sufficient for speech-to-text recognition.
- `ffmpeg` is available on the host system for audio extraction and frame extraction.
- The transcription service supports real-time streaming via WebSocket with auto-commit (detecting speech boundaries automatically).
- The system uses different voice profiles for dispatch/outbound messages than for caller/inbound audio, so they are clearly distinguishable.
- The existing agent pipeline (intake agent, triage agent, evidence fusion agent, dispatch agent) is already functional and does not need modification — only the trigger mechanism changes from pre-recorded files to real-time streaming.
- The frontend already has Supabase Realtime subscriptions in place and will react to database changes automatically.

## Scope Boundaries

**In scope**:
- Audio extraction from video to PCM
- Real-time audio streaming to transcription service
- Language detection and feed assignment
- Committed transcript processing through existing agent pipeline
- Partial transcript display support
- Parallel vision pipeline execution
- Evacuation TTS warning generation
- Operator approval flow
- Data preservation across demo runs

**Out of scope**:
- Modifying the frontend dashboard components (they already react to Supabase Realtime)
- Creating new agent types (existing agents are reused)
- Supporting live microphone input (audio comes only from the video file)
- Multi-camera or multi-video support (single video file only)
- Real-time video streaming to the frontend (frontend plays the video file directly)
