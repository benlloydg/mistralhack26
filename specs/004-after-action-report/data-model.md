# Data Model: After-Action Report

**Feature**: 004-after-action-report
**Date**: 2026-03-01

## Entities

### ReportData (top-level response)

The complete report response returned by `POST /api/v1/cases/{case_id}/report`.

| Field | Type | Description |
|-------|------|-------------|
| case_id | string | Incident identifier (e.g., TN-20260301-033345) |
| generated_at | string (ISO 8601) | When this report was generated |
| warning | string? | Set if demo is still in progress |
| header | ReportHeader | Section 1: case metadata |
| timeline | TimelineEntry[] | Section 2: chronological event list |
| evidence_sources | EvidenceSources | Section 3: audio + vision summaries |
| convergence_tracks | ConvergenceTrack[] | Section 4: per-source event tracks |
| response_actions | ResponseAction[] | Section 5: dispatch actions |
| agent_stats | AgentStats | Section 6: agent utilization |
| key_frames | KeyFrame[] | Section 7: saved vision frames |
| executive_summary | string | Section 8: Mistral-generated summary |

### ReportHeader

| Field | Type | Description |
|-------|------|-------------|
| case_id | string | Case identifier |
| incident_type | string? | e.g., "vehicle_crash" |
| location | string? | Normalized location |
| severity | string | unknown/low/medium/high/critical |
| status | string | intake/active/escalated/critical/resolved_demo |
| duration_seconds | float | Time from case creation to resolution |
| speaker_count | int | Number of detected audio speakers/feeds |
| languages | string[] | Language codes detected (e.g., ["es", "zh", "fr"]) |
| audio_segments | int | Total committed transcript count |
| vision_frames | int | Total frames analyzed |
| outcome | string | Human-readable outcome (e.g., "ZERO CASUALTIES — ALL PERSONS EVACUATED") |

### TimelineEntry

| Field | Type | Description |
|-------|------|-------------|
| t | string | Elapsed time (e.g., "00:12") |
| timestamp | string (ISO 8601) | Absolute timestamp from created_at |
| agent | string | Source agent (voice, vision, triage, evidence_fusion, orchestrator, dispatch) |
| model | string? | Model name if applicable (mistral-large-latest, pixtral-large-latest, scribe-v2) |
| event_type | string | Event classification |
| message | string | Human-readable description |
| severity_indicator | string | "regular" / "critical" / "operator" |
| color | string | Display color (blue, green, amber, red, purple) |
| flash | boolean | Whether this was a flash-worthy event |

### EvidenceSources

| Field | Type | Description |
|-------|------|-------------|
| audio | AudioSummary | Audio stream summary |
| vision | VisionSummary | Visual feed summary |
| cross_modal | CrossModalSummary[] | Cross-modal corroboration entries |

### AudioSummary

| Field | Type | Description |
|-------|------|-------------|
| speaker_count | int | Number of distinct speakers/feeds |
| languages | string[] | Language codes |
| transcript_count | int | Total committed segments |
| speakers | SpeakerSummary[] | Per-speaker key intelligence |

### SpeakerSummary

| Field | Type | Description |
|-------|------|-------------|
| feed_id | string | e.g., "FEED_1" |
| language | string | Language code |
| label | string? | e.g., "Scene Audio (FEED_1)" |
| key_intelligence | string | Summary of what this speaker contributed |
| segment_count | int | Number of segments from this speaker |

### VisionSummary

| Field | Type | Description |
|-------|------|-------------|
| frames_analyzed | int | Total frames processed |
| detections | VisionDetectionEntry[] | Key detections with timestamps |

### VisionDetectionEntry

| Field | Type | Description |
|-------|------|-------------|
| timestamp_s | float | Seconds into video |
| type | string | Detection type (smoke, engine_fire, etc.) |
| confidence | float | Detection confidence |
| description | string | Human-readable description |

### CrossModalSummary

| Field | Type | Description |
|-------|------|-------------|
| claim | string | What was corroborated |
| modalities | string[] | ["vision", "audio"] |
| details | string | Human-readable explanation |

### ConvergenceTrack

| Field | Type | Description |
|-------|------|-------------|
| source | string | Track identifier (e.g., "ES", "ZH", "FR", "EN", "CAM", "FUSED") |
| type | string | "audio" / "vision" / "fused" |
| color | string | Display color for this track |
| events | TrackEvent[] | Ordered events on this track |

### TrackEvent

| Field | Type | Description |
|-------|------|-------------|
| t_seconds | float | Seconds from demo start |
| label | string | Short label (e.g., "trapped", "FIRE", "evac sent") |
| type | string | "detection" / "escalation" / "action" / "state_change" |

### ResponseAction

| Field | Type | Description |
|-------|------|-------------|
| action | string | Action description (e.g., "EMS (AMB-7)") |
| unit_type | string | Unit type |
| unit_assigned | string? | Unit callsign |
| status | string | recommended/confirmed/dispatched/broadcast |
| authorized_at | string? | Elapsed timestamp |
| authorization_method | string | "operator" / "autonomous" |
| language | string? | For evacuation broadcasts |

### AgentStats

| Field | Type | Description |
|-------|------|-------------|
| agents | AgentUtilization[] | Per-agent stats |
| total_invocations | int | Sum of all invocations |
| total_duration_seconds | float | Demo duration |
| models_used | ModelUsage[] | List of models and their roles |

### AgentUtilization

| Field | Type | Description |
|-------|------|-------------|
| agent | string | Agent name |
| model | string | Model used |
| invocations | int | Number of calls |
| avg_latency_seconds | float | Average time per invocation |

### ModelUsage

| Field | Type | Description |
|-------|------|-------------|
| model | string | Model identifier |
| roles | string[] | What this model is used for |

### KeyFrame

| Field | Type | Description |
|-------|------|-------------|
| image_url | string | URL to JPEG (e.g., /frames/TN-..._t38s.jpg) |
| timestamp_s | float | Seconds into video |
| elapsed | string | MM:SS from demo start |
| detections | object[] | Detection results from vision agent |
| description | string | Overall scene description |
| is_hero | boolean | Whether this is the hero frame (e.g., fire detection) |

## Relationships

- ReportData assembles data from 4 Supabase tables: `incident_state`, `agent_logs`, `transcripts`, `dispatches`
- KeyFrame images are served from disk via `/frames` static mount
- ExecutiveSummary is generated by Mistral and cached in-memory
- ConvergenceTracks are computed from `agent_logs` + `transcripts` at report time

## No New Database Tables

All data is read from existing tables. The only new storage is:
- JPEG files on disk (`assets/frames/`)
- In-memory executive summary cache (Python dict)
