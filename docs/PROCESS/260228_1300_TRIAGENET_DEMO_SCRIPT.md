Absolutely. Here’s the **revised 120-second technical script** with:

* **one human approval moment**
* explicit **CCTV / scene-monitoring**
* explicit **case correlation**
* explicit **evidence fusion**
* a clean **final payoff state**

This version is designed to be **light enough to ship** and **bulletproof as a demo**.

---

# TriageNet — 120-Second Technical Demo Script (Revised)

## Core demo principle

Everything is **scripted but live-rendered**.

You are not improvising a real emergency system.
You are running a **deterministic orchestrated simulation** that visibly exercises:

* multilingual intake
* shared state
* scene monitoring
* multi-agent coordination
* one human approval
* autonomous escalation after new evidence

---

# System architecture assumptions

## Backend components

* **DemoOrchestrator**: drives timed events
* **SharedState store**: canonical `IncidentState`
* **EventBus**: logs agent/tool events
* **WebSocket broadcaster**: pushes UI updates
* **MediaController**: plays pre-seeded caller audio + incident video
* **Triage Agent**: Mistral reasoning / structured outputs
* **Vision Agent**: frame analysis + scene delta
* **Voice Response Agent**: ElevenLabs speech generation
* **Response Coordinator**: creates recommendations + warnings

## Frontend panels

* **CCTV Panel**
* **Case File Panel**
* **Agent Terminal**
* **Response Lanes**
* **Caller Transcript Panel**
* **Action Button**

---

# Shared state model

Use one central object throughout:

`IncidentState`

* `case_id`
* `status` (`intake`, `active`, `escalated`, `critical`, `resolved_demo`)
* `incident_type`
* `location_raw`
* `location_normalized`
* `severity`
* `caller_count`
* `people_count_estimate`
* `injury_flags`
* `hazard_flags`
* `vision_detections`
* `recommended_units`
* `confirmed_units`
* `timeline_events`
* `current_action_plan_version`
* `operator_summary`
* `match_confidence`
* `confidence_scores`
* `last_updated_at`

---

# Technical timeline

## Phase 0 — Boot / Initialize (0:00–0:12)

### Frontend action

User clicks:

**START DEMO**

### Backend events

1. `start_demo()`
2. `create_case()` → returns `TN-2026-00417`
3. `init_incident_state(case_id)`
4. `open_websocket_session(case_id)`
5. `start_video_monitor(case_id, stream_id="crash_cam_01")`
6. `load_media_assets()`

   * `caller_1_spanish.mp3`
   * `caller_2_mandarin.mp3`
   * `caller_3_french.mp3`
   * `crash_video.mp4`

### Shared state after init

* `status = "intake"`
* `severity = "unknown"`
* `caller_count = 0`
* `recommended_units = []`
* `confirmed_units = []`
* `current_action_plan_version = 0`

### UI state

* CCTV Panel: `FEED READY`
* Case Panel: `Awaiting incoming call`
* Agent Terminal:

  * `DemoOrchestrator initialized`
  * `Case created: TN-2026-00417`
  * `Video monitor armed`

---

## Phase 1 — Caller 1 / Initial Intake (0:12–0:30)

### Backend events

1. `play_audio("caller_1_spanish.mp3")`

2. `transcribe_audio(audio_1, autodetect_language=True)`
   → returns:

   * language: `es`
   * text: `"Market and 5th. My husband is trapped in the car."`

3. `extract_intake_facts(transcript_1)`
   → structured:

   * `location_raw = "Market and 5th"`
   * `possible_trapped_person = true`
   * `incident_type_candidate = "vehicle_crash"`

4. `normalize_location("Market and 5th")`
   → `"Market St & 5th St"`

5. `resolve_incident_match(call_1, open_cases)`
   → no existing case match
   → attach to current demo case by default

6. `update_case_from_intake(case_id, facts_1)`

7. `triage_reason(case_id)`
   → returns:

   * `incident_type = "vehicle_collision"`
   * `severity = "high"`
   * `recommended_units = ["EMS", "Traffic Control"]`
   * `action_plan_version = 1`

8. `generate_voice_response(language="es", mode="caller_reassurance")`

### Shared state changes

* `caller_count = 1`
* `severity = "high"`
* `incident_type = "vehicle_collision"`
* `location_normalized = "Market St & 5th St"`
* `people_count_estimate = 2` (inferred)
* `recommended_units = ["EMS", "Traffic Control"]`
* `current_action_plan_version = 1`
* `status = "active"`

### UI state

* Caller Transcript panel shows Spanish + English summary
* Case File shows:

  * `Vehicle collision`
  * `Severity: HIGH`
  * `Possible trapped occupant`
* Response Lanes:

  * EMS → `Recommended`
  * Traffic Control → `Recommended`

### Agent terminal logs

* `IntakeAgent: transcript received (es)`
* `Location normalized`
* `TriageAgent: severity HIGH`
* `Action Plan v1 generated`

---

## Phase 2 — Human approval moment (0:30–0:38)

This is your **single live interaction**.

### Frontend action

You click:

## **Approve Initial Response**

### Backend events

1. `operator_confirm_action(case_id, action="approve_initial_response")`
2. `confirm_recommended_units(["EMS", "Traffic Control"])`
3. `queue_outbound_briefs(case_id, units=["EMS", "Traffic Control"])`
4. `generate_dispatch_brief(unit="EMS", language="en")`
5. `generate_dispatch_brief(unit="Traffic Control", language="en")`

### Shared state changes

* `confirmed_units = ["EMS", "Traffic Control"]`

### UI state

* EMS: `Recommended → Confirmed`
* Traffic Control: `Recommended → Confirmed`
* Button locks / disappears

### Agent terminal logs

* `Operator confirmed Action Plan v1`
* `EMS brief queued`
* `Traffic control brief queued`

This is the moment that proves:

* human remains in control
* system is decision support, not replacement

---

## Phase 3 — Caller 2 / Case Correlation + Escalation (0:38–0:56)

### Backend events

1. `play_audio("caller_2_mandarin.mp3")`

2. `transcribe_audio(audio_2, autodetect_language=True)`
   → returns:

   * language: `zh`
   * text: `"There is a child in the back seat!"`

3. `extract_intake_facts(transcript_2)`
   → structured:

   * `child_present = true`
   * `additional_victim = true`

4. `resolve_incident_match(call_2, open_cases=[TN-2026-00417])`
   → returns:

   * `matched_case = TN-2026-00417`
   * `match_confidence = 0.94`

5. `link_call_to_case(call_2, case_id, confidence=0.94)`

6. `merge_caller_intel(case_id, facts_2)`

7. `fuse_evidence(case_id)`
   → now combines:

   * trapped adult
   * child present
   * same location cluster

8. `compute_severity_delta(case_id)`
   → `HIGH → CRITICAL`

9. `rebuild_action_plan(case_id)`
   → returns:

   * `recommended_units += ["Pediatric EMS"]`
   * `action_plan_version = 2`

10. `generate_voice_response(language="zh", mode="caller_confirmation")`

### Shared state changes

* `caller_count = 2`
* `match_confidence = 0.94`
* `people_count_estimate = 3`
* `severity = "critical"`
* `recommended_units = ["EMS", "Traffic Control", "Pediatric EMS"]`
* `current_action_plan_version = 2`

### UI state

* New transcript appears in Mandarin + English
* Case File updates:

  * `Child detected in incident`
  * `Severity escalated to CRITICAL`
* Pediatric EMS lane appears as `Recommended`

### Agent terminal logs

* `CaseMatchAgent: Caller 2 linked to TN-2026-00417 (0.94)`
* `EvidenceFusion: victim count increased`
* `Severity delta: HIGH -> CRITICAL`
* `Action Plan v2 generated`

This is one of the best technical moments in the demo.

---

## Phase 4 — CCTV loop / Fire detection / Scene delta (0:56–1:18)

This is where the visual intelligence becomes undeniable.

### Backend events

1. `play_video("crash_video.mp4")` if not already rolling

2. `sample_frame(stream_id, t=58s)`

3. `analyze_scene(frame_t1)`
   → returns:

   * `smoke_visible = true`
   * `fire_visible = false`
   * `vehicle_damage = severe`

4. `write_vision_detection(case_id, frame_t1_result)`

5. `sample_frame(stream_id, t=66s)`

6. `analyze_scene(frame_t2)`
   → returns:

   * `engine_fire = true`
   * `confidence = 0.99`

7. `detect_scene_delta(previous=frame_t1_result, current=frame_t2_result)`
   → returns:

   * `new_hazard = "engine_fire"`
   * `hazard_escalation = true`

8. `write_vision_detection(case_id, frame_t2_result)`

9. `fuse_evidence(case_id)`
   → caller smoke report + visual engine fire now corroborate

10. `compute_severity_delta(case_id)`
    → remains `CRITICAL`, but raises hazard priority

11. `rebuild_action_plan(case_id)`
    → returns:

* `recommended_units += ["Fire Response"]`
* `evacuation_warning_required = true`
* `action_plan_version = 3`

### Shared state changes

* `hazard_flags += ["engine_fire"]`
* `vision_detections += [{"engine_fire": 0.99}]`
* `recommended_units += ["Fire Response"]`
* `current_action_plan_version = 3`
* `status = "escalated"`

### UI state

* CCTV panel flashes red overlay:

  * `ENGINE FIRE DETECTED (0.99)`
* Hazard badge appears
* Fire Response lane appears as `Recommended`
* Case File updates:

  * `Visual hazard escalation detected`
  * `Action Plan v3`

### Agent terminal logs

* `VisionAgent: smoke detected`
* `VisionAgent: engine fire detected (0.99)`
* `SceneDelta: new hazard introduced`
* `EvidenceFusion: caller report + vision corroborated`
* `Action Plan v3 generated`

This is the **hero technical sequence**.

---

## Phase 5 — Priority interruption + multilingual warning (1:18–1:36)

Now the system changes the course of the story automatically.

### Backend events

1. `interrupt_active_call(case_id, reason="hazard_escalation")`
2. `priority_broadcast(case_id, languages=["es", "zh"])`
3. `generate_voice_response(language="es", mode="evacuate_now")`
4. `generate_voice_response(language="zh", mode="evacuate_now")`
5. `recommend_dispatch(unit="Fire Response", rationale="vision-confirmed engine fire")`
6. `queue_outbound_brief(unit="Fire Response")`

### Shared state changes

* `recommended_units = ["EMS", "Traffic Control", "Pediatric EMS", "Fire Response"]`
* `timeline_events += priority warning event`

### UI state

* Agent terminal highlights:

  * `PRIORITY INTERRUPT TRIGGERED`
* Fire Response lane pulses as `Recommended`
* Activity log shows:

  * `Native-language evacuation warning issued`
  * `Fire response recommended due to corroborated engine fire`

### Agent terminal logs

* `VoiceInterrupter: active call interrupted`
* `PriorityBroadcast: ES + ZH warnings issued`
* `ResponseCoordinator: Fire Response recommendation queued`

This gives you the “the system changed the story” moment.

---

## Phase 6 — Final payoff / case summary (1:36–2:00)

The demo must end in a clean, resolved display state.

### Backend events

1. `generate_case_summary(case_id)`
2. `finalize_demo_state(case_id, status="resolved_demo")`

### Case summary output

* `Vehicle collision with trapped occupant and child confirmed`
* `Engine fire visually detected and corroborated`
* `Severity: CRITICAL`
* `Initial response confirmed by operator`
* `Fire response additionally recommended after hazard escalation`
* `Multilingual warnings delivered`

### Shared state changes

* `status = "resolved_demo"`
* `operator_summary` populated
* `last_updated_at` set

### UI state

Final screen should show:

## Case File

* Case ID
* Location
* Incident type
* Severity: `CRITICAL`
* Occupants: `3 estimated`
* Hazards:

  * trapped passenger
  * child present
  * engine fire

## Response Lanes

* EMS → `Confirmed`
* Traffic Control → `Confirmed`
* Pediatric EMS → `Recommended`
* Fire Response → `Recommended`

## Timeline

At least:

* case created
* caller 1 intake
* operator approved initial response
* caller 2 merged to same case
* severity escalated
* engine fire detected
* multilingual warning issued

### Agent terminal final lines

* `Case summary generated`
* `Demo complete: TN-2026-00417`

End there.

---

# Why this version is stronger

## It now clearly demonstrates:

* **shared-state memory**
* **multi-caller correlation**
* **vision + language evidence fusion**
* **one human-in-the-loop approval**
* **autonomous adaptation after new evidence**
* **a clean final outcome**

That is exactly what judges need to see.

---

# Minimum function list to implement

If you want the smallest real build, these are the core functions:

* `start_demo()`
* `create_case()`
* `init_incident_state()`
* `play_audio()`
* `transcribe_audio()`
* `extract_intake_facts()`
* `normalize_location()`
* `resolve_incident_match()`
* `link_call_to_case()`
* `merge_caller_intel()`
* `triage_reason()`
* `fuse_evidence()`
* `compute_severity_delta()`
* `rebuild_action_plan()`
* `start_video_monitor()`
* `sample_frame()`
* `analyze_scene()`
* `detect_scene_delta()`
* `operator_confirm_action()`
* `confirm_recommended_units()`
* `interrupt_active_call()`
* `priority_broadcast()`
* `generate_voice_response()`
* `generate_case_summary()`

---

# Build-light implementation note

To keep this bulletproof:

* Use **pre-seeded audio**
* Use **pre-seeded video**
* Use **scripted timestamps**
* Let the orchestrator trigger events deterministically
* Cache model outputs where possible
* If needed, fake some non-essential latency with controlled delays

The only thing that needs to feel “live” is the **state updating UI**.

---

# The single best UX detail to add

In the UI, whenever severity changes, show a tiny inline explanation:

> **CRITICAL**
> Triggered by: additional child confirmed + trapped passenger + corroborated engine fire

That one line makes the reasoning legible.

---

If you want, I’ll next turn this into:

1. the **exact JSON schema** for `IncidentState`, `TimelineEvent`, and `ResponseLane`, and
2. a **frontend wireframe spec** so the dashboard is fast to build.
