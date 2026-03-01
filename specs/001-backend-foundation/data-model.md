# Data Model: Backend Foundation

## Entity Relationship Overview

```
IncidentState (1) ←──── (N) AgentLogEntry      [via case_id]
IncidentState (1) ←──── (N) TranscriptSegment   [via case_id]
IncidentState (1) ←──── (N) DispatchRecord       [via case_id in dispatches table]
IncidentState (1) ──── embeds: TimelineEvent[], ActionItem[], VisionDetection[]
CallerRecord ──── references: TranscriptSegment [via caller_id]
TriageResult ──── produces: ActionItem[], recommended_units[]
EvidenceFusionResult ──── produces: Corroboration[]
```

## Entities

### IncidentState
The central record for a case. Maps 1:1 to the `incident_state` Supabase table.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| case_id | str | required | Unique case identifier, e.g. "TN-2026-00417" |
| status | IncidentStatus | intake | intake, active, escalated, critical, resolved_demo |
| incident_type | str? | None | vehicle_collision, fire, etc. |
| location_raw | str? | None | Raw location from caller |
| location_normalized | str? | None | Normalized/geocoded location |
| severity | Severity | unknown | unknown, low, medium, high, critical |
| caller_count | int | 0 | Number of connected callers |
| people_count_estimate | int | 0 | Estimated people at scene |
| injury_flags | list[str] | [] | e.g. ["trapped_person", "child_present"] |
| hazard_flags | list[str] | [] | e.g. ["engine_fire", "smoke"] |
| vision_detections | list[dict] | [] | Raw vision detection results |
| recommended_units | list[str] | [] | e.g. ["EMS", "Fire Response"] |
| confirmed_units | list[str] | [] | Operator-confirmed units |
| timeline | list[TimelineEvent] | [] | Chronological event log |
| action_plan_version | int | 0 | Incrementing version counter |
| action_plan | list[ActionItem] | [] | Current action items |
| match_confidence | float? | None | Evidence fusion confidence |
| operator_summary | str? | None | Generated summary text |
| confidence_scores | dict | {} | Per-source confidence scores |

**Validation**: severity must be a valid Severity enum value. status must be a valid IncidentStatus enum value.

### Severity (Enum)
Values: unknown, low, medium, high, critical.
Rule: NEVER downgrade once escalated.

### IncidentStatus (Enum)
Values: intake, active, escalated, critical, resolved_demo.
Transitions: intake → active → escalated → critical → resolved_demo (forward only in demo).

### TimelineEvent
Embedded in IncidentState.timeline.

| Field | Type | Description |
|-------|------|-------------|
| t | str | Elapsed time, e.g. "00:15" |
| agent | str | Agent that produced this event |
| event | str | Human-readable description |

### ActionItem
Embedded in IncidentState.action_plan.

| Field | Type | Description |
|-------|------|-------------|
| status | str | completed, pending, recommended |
| action | str | Human-readable action description |

### TranscriptSegment
Maps to `transcripts` table.

| Field | Type | Description |
|-------|------|-------------|
| caller_id | str | caller_1, caller_2, caller_3 |
| caller_label | str? | "The Wife", "Bystander", "Shopkeeper" |
| language | str | es, zh, fr |
| original_text | str | Original language transcript |
| translated_text | str? | English translation |
| entities | list[str] | Extracted entity strings |
| confidence | float? | Transcription confidence |
| segment_index | int | Order within caller's transcript |

### IntakeFacts
Structured output from intake agent. Not persisted directly — used to update IncidentState.

| Field | Type | Description |
|-------|------|-------------|
| location_raw | str? | Raw location from caller |
| incident_type_candidate | str? | vehicle_crash, fire, medical, etc. |
| possible_trapped_person | bool | Is someone reported trapped? |
| child_present | bool | Is a child mentioned? |
| additional_victim | bool | Does this add new victim info? |
| injury_description | str? | Description of injuries |
| hazard_description | str? | Smoke, fire, fuel leak, etc. |
| urgency_keywords | list[str] | trapped, bleeding, fire, etc. |

### CallerRecord
Configuration record for demo callers. Not persisted to DB.

| Field | Type | Description |
|-------|------|-------------|
| caller_id | str | caller_1, caller_2, caller_3 |
| label | str | Human-readable label |
| language | str | es, zh, fr |
| audio_path | str | Path to pre-recorded audio |
| start_delay_s | float | Seconds into demo when caller connects |
| status | str | queued, active, completed |

### VisionDetection
Embedded in FrameAnalysis.detections.

| Field | Type | Description |
|-------|------|-------------|
| type | str | vehicle_collision, smoke, engine_fire, persons_visible |
| confidence | float | 0.0 - 1.0 |
| bbox | list[int]? | [x1, y1, x2, y2] bounding box |
| count | int? | Person count if persons_visible |

### FrameAnalysis
Structured output from vision agent.

| Field | Type | Description |
|-------|------|-------------|
| frame_id | int | Frame sequence number |
| detections | list[VisionDetection] | All detections in frame |
| overall_description | str | One-line scene summary |
| hazard_escalation | str? | New hazard type if detected |
| smoke_visible | bool | Smoke in frame |
| fire_visible | bool | Fire in frame |
| vehicle_damage_severity | str? | none, minor, moderate, severe |

### SceneDelta
Computed difference between consecutive frames.

| Field | Type | Description |
|-------|------|-------------|
| new_hazard | str? | Newly detected hazard type |
| hazard_escalation | bool | Whether hazard level increased |
| confidence_change | float | Change in overall confidence |
| description | str | Human-readable delta description |

### TriageResult
Structured output from triage agent.

| Field | Type | Description |
|-------|------|-------------|
| severity | Severity | Assessed severity level |
| incident_type | str | Classification |
| reasoning | str | 1-2 sentence explanation |
| recommended_units | list[str] | Units to dispatch |
| hazards | list[str] | Identified hazards |
| people_count_estimate | int | Estimated people count |
| injury_flags | list[str] | Injury indicators |
| dispatch_triggers | list[str] | Specific triggers (pediatric_trauma, hazmat) |
| action_plan | list[ActionItem] | Recommended actions |

### Corroboration
When multiple sources confirm the same fact.

| Field | Type | Description |
|-------|------|-------------|
| claim | str | The corroborated claim |
| sources | list[dict] | [{type: vision|caller_N, confidence: float}] |
| status | str | corroborated, conflicting, unconfirmed |
| combined_confidence | float | 1 - product(1 - source_conf) |

### EvidenceFusionResult
Output of evidence fusion agent.

| Field | Type | Description |
|-------|------|-------------|
| corroborations | list[Corroboration] | Confirmed claims |
| severity_delta | str? | e.g. "HIGH -> CRITICAL" |
| new_severity | Severity? | Updated severity if changed |
| evacuation_warning_required | bool | Active fire/explosion near people |
| reasoning | str | Explanation |

### DispatchBrief
Structured output from dispatch agent. Maps to `dispatches` table.

| Field | Type | Description |
|-------|------|-------------|
| unit_type | str | EMS, Fire Response, Pediatric EMS, Traffic Control |
| unit_assigned | str | Callsign: AMB-7, ENG-4, PED-2, TC-3 |
| destination | str | Hospital or location |
| eta_minutes | int | Estimated arrival time |
| voice_message | str | TTS dispatch message (< 40 words) |
| rationale | str | Why this unit is dispatched |

### AgentLogEntry
Maps to `agent_logs` table.

| Field | Type | Description |
|-------|------|-------------|
| case_id | str | Links to incident_state |
| agent | str | triage, vision, voice, dispatch, intake, orchestrator |
| event_type | str | transcript_received, severity_changed, detection, etc. |
| message | str | Human-readable log line |
| data | dict | Structured event data |
| display_color | str | blue, red, amber, green, purple |
| display_flash | bool | Whether UI should flash this entry |

## State Transitions

### Severity (monotonically increasing during demo)
```
unknown → low → medium → high → critical
```
Rule: NEVER downgrade. Escalation triggers: child present, person trapped, fire/explosion, corroborated danger from multiple callers.

### IncidentStatus (linear progression in demo)
```
intake → active → escalated → critical → resolved_demo
```
