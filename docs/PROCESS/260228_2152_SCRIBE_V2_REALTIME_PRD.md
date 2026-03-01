# DISPATCH — Scribe v2 Realtime Integration PRD

## Overview

The DISPATCH demo plays a single pre-produced video file (`scene.mp4`) that contains both the visual feed (CCTV intersection footage) and embedded multilingual audio (bystanders speaking Spanish, Mandarin, and French at different moments). The backend extracts the audio track from this video and streams it in real time to ElevenLabs Scribe v2 Realtime, which performs continuous speech-to-text with automatic language detection. Each committed transcript is passed to the agent pipeline, which extracts facts, updates the shared case state, and triggers downstream actions (severity changes, dispatch recommendations, evacuation warnings).

The video plays once. The system listens, watches, reasons, and acts.

---

## Architecture

```
scene.mp4 (video + audio)
    │
    ├──► Frontend: plays video in CCTV panel (visual only)
    │
    └──► Backend: extracts audio track
              │
              ▼
         Scribe v2 Realtime (WebSocket)
              │
              ├── PARTIAL_TRANSCRIPT ──► Frontend: live transcript shimmer
              │
              └── COMMITTED_TRANSCRIPT ──► IntakeAgent pipeline
                      │
                      ├── language detection (es/zh/fr)
                      ├── extract_intake_facts() ──► Mistral Large
                      ├── resolve_incident_match() ──► Case Match Agent
                      ├── fuse_evidence() ──► Evidence Fusion Agent
                      ├── compute_severity_delta()
                      ├── rebuild_action_plan() ──► Triage Agent
                      │
                      └──► write to Supabase ──► Frontend reacts via Realtime
```

### Parallel pipeline: Vision

The orchestrator also extracts video frames at hardcoded timestamps and sends them to the Vision Agent (Pixtral). Vision and audio pipelines write to the same shared case state and trigger the same evidence fusion logic. They are independent — neither waits for the other.

---

## Scribe v2 Realtime — Implementation Spec

### Connection setup

Use **server-side manual audio chunking** via the Python SDK. The orchestrator runs on the backend (FastAPI), has direct access to the ElevenLabs API key, and needs precise timing control.

```python
from elevenlabs import (
    ElevenLabs,
    AudioFormat,
    CommitStrategy,
    RealtimeEvents,
    RealtimeAudioOptions,
)

elevenlabs = ElevenLabs(api_key=os.getenv("ELEVENLABS_API_KEY"))

connection = await elevenlabs.speech_to_text.realtime.connect(
    RealtimeAudioOptions(
        model_id="scribe_v2_realtime",
        audio_format=AudioFormat.PCM_16000,
        sample_rate=16000,
        commit_strategy=CommitStrategy.AUTO,
        include_timestamps=True,
        language_detection=True,
    )
)
```

### Key configuration choices

| Setting | Value | Rationale |
|---------|-------|-----------|
| `model_id` | `scribe_v2_realtime` | Realtime model with language detection |
| `audio_format` | `PCM_16000` | 16-bit PCM, 16kHz mono — standard for STT |
| `sample_rate` | `16000` | Matches PCM format |
| `commit_strategy` | `AUTO` | Let Scribe detect speech boundaries and commit automatically. The audio has natural pauses between speakers. If AUTO doesn't segment cleanly between speakers, fall back to `MANUAL` and commit after each known speech segment based on hardcoded timestamps. |
| `include_timestamps` | `True` | Word-level timestamps for transcript display |
| `language_detection` | `True` | Auto-detect es/zh/fr — core demo feature |

### Audio extraction from video

Before the demo runs, or at demo start time, extract the audio track from `scene.mp4` to PCM format:

```python
import subprocess

def extract_audio_pcm(video_path: str, output_path: str):
    """Extract audio from video as 16kHz 16-bit mono PCM."""
    subprocess.run([
        "ffmpeg", "-y",
        "-i", video_path,
        "-vn",                    # no video
        "-acodec", "pcm_s16le",   # 16-bit signed little-endian PCM
        "-ar", "16000",           # 16kHz sample rate
        "-ac", "1",               # mono
        output_path
    ], check=True)

# Run once at startup or as part of asset prep
extract_audio_pcm("assets/scene.mp4", "assets/scene_audio.pcm")
```

This produces a raw PCM file that maps 1:1 to the video timeline. Byte offset = timestamp. At 16kHz 16-bit mono: 32,000 bytes = 1 second of audio.

### Streaming audio to Scribe

The orchestrator streams the PCM audio to Scribe in real time, synchronized to video playback. The audio must arrive at Scribe at approximately the same rate the video plays — otherwise transcripts will arrive too early or too late relative to the visual events.

```python
import asyncio
import base64

SAMPLE_RATE = 16000
BYTES_PER_SECOND = SAMPLE_RATE * 2  # 16-bit = 2 bytes per sample
CHUNK_DURATION_MS = 250             # send chunks every 250ms
CHUNK_SIZE = int(BYTES_PER_SECOND * CHUNK_DURATION_MS / 1000)  # 8000 bytes

async def stream_audio_to_scribe(connection, pcm_path: str):
    """Stream PCM audio to Scribe in real time, synchronized to playback."""
    with open(pcm_path, "rb") as f:
        audio_data = f.read()

    total_chunks = len(audio_data) // CHUNK_SIZE
    
    for i in range(0, len(audio_data), CHUNK_SIZE):
        chunk = audio_data[i:i + CHUNK_SIZE]
        chunk_b64 = base64.b64encode(chunk).decode("utf-8")

        await connection.send({
            "audio_base_64": chunk_b64,
            "sample_rate": SAMPLE_RATE,
        })

        # Pace to real time — 250ms of audio per chunk
        await asyncio.sleep(CHUNK_DURATION_MS / 1000)
    
    # Final commit if using MANUAL strategy
    # await connection.commit()
```

**Why 250ms chunks?** Smaller chunks = lower latency for partial transcripts. Scribe starts returning partials as soon as it detects speech. 250ms gives responsive feel without excessive WebSocket traffic.

### Event handling

```python
transcript_buffer = []

def on_session_started(data):
    logger.info(f"Scribe session started: {data}")

def on_partial_transcript(data):
    """Show live "typing" effect in the UI."""
    text = data.get("text", "")
    if text.strip():
        # Write to Supabase for frontend to show as shimmer/partial
        await supabase.table("live_partials").upsert({
            "case_id": case_id,
            "text": text,
            "timestamp": time.time(),
        }).execute()

async def on_committed_transcript(data):
    """A complete speech segment. This is the trigger for the agent pipeline."""
    text = data.get("text", "").strip()
    language = data.get("language", "unknown")
    
    if not text:
        return
    
    logger.info(f"Scribe committed [{language}]: {text}")
    
    # Assign a feed/source ID based on language (first occurrence)
    feed_id = assign_feed_id(language)
    
    # Write raw transcript to Supabase
    await supabase.table("transcripts").insert({
        "case_id": case_id,
        "feed_id": feed_id,
        "language": language,
        "original_text": text,
        "timestamp": time.time(),
    }).execute()
    
    # >>> THIS IS WHERE THE AGENT PIPELINE STARTS <<<
    await process_transcript(case_id, feed_id, language, text)

async def on_committed_transcript_with_timestamps(data):
    """Same as committed but with word-level timing. Store for report page."""
    words = data.get("words", [])
    await supabase.table("transcript_timestamps").insert({
        "case_id": case_id,
        "words": words,
        "timestamp": time.time(),
    }).execute()

def on_error(error):
    logger.error(f"Scribe error: {error}")

def on_close():
    logger.info("Scribe connection closed")

# Register handlers
connection.on(RealtimeEvents.SESSION_STARTED, on_session_started)
connection.on(RealtimeEvents.PARTIAL_TRANSCRIPT, on_partial_transcript)
connection.on(RealtimeEvents.COMMITTED_TRANSCRIPT, on_committed_transcript)
connection.on(RealtimeEvents.COMMITTED_TRANSCRIPT_WITH_TIMESTAMPS, on_committed_transcript_with_timestamps)
connection.on(RealtimeEvents.ERROR, on_error)
connection.on(RealtimeEvents.CLOSE, on_close)
```

### Feed ID assignment

Since the audio is a single mixed track, Scribe will commit transcripts as it detects speech segments. We assign feed IDs based on detected language (each language = one bystander = one feed):

```python
feed_registry = {}
feed_counter = 0

def assign_feed_id(language: str) -> str:
    global feed_counter
    if language not in feed_registry:
        feed_counter += 1
        feed_registry[language] = f"FEED_{feed_counter}"
    return feed_registry[language]

# Result:
# First Spanish segment  → "FEED_1"
# First Mandarin segment → "FEED_2"  
# First French segment   → "FEED_3"
```

---

## Agent pipeline — triggered per committed transcript

When `on_committed_transcript` fires, the following pipeline runs:

### Step 1: Translate (if needed)

```python
async def translate_to_english(text: str, source_lang: str) -> str:
    """Use Mistral Large to translate to English."""
    if source_lang == "en":
        return text
    
    response = await mistral.chat.complete(
        model="mistral-large-latest",
        messages=[{
            "role": "user",
            "content": f"Translate the following {source_lang} text to English. "
                       f"Return ONLY the translation, nothing else.\n\n{text}"
        }],
        temperature=0.1,
    )
    return response.choices[0].message.content.strip()
```

### Step 2: Extract structured facts

```python
async def extract_intake_facts(case_id: str, text_en: str, language: str) -> dict:
    """Use Mistral Large with structured output to extract incident facts."""
    response = await mistral.chat.complete(
        model="mistral-large-latest",
        messages=[{
            "role": "system",
            "content": "You are an incident intelligence intake agent. Extract structured facts from bystander audio captured at an incident scene."
        }, {
            "role": "user", 
            "content": f"Extract facts from this bystander statement:\n\"{text_en}\""
        }],
        response_format={
            "type": "json_object",
            "schema": {
                "type": "object",
                "properties": {
                    "incident_type_candidate": {"type": "string"},
                    "location_mentioned": {"type": "string", "nullable": True},
                    "trapped_person": {"type": "boolean"},
                    "child_present": {"type": "boolean"},
                    "injury_mentioned": {"type": "boolean"},
                    "fire_or_smoke": {"type": "boolean"},
                    "victim_count_estimate": {"type": "integer", "nullable": True},
                    "urgency": {"type": "string", "enum": ["low", "medium", "high", "critical"]},
                    "key_facts": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["incident_type_candidate", "trapped_person", "child_present", "fire_or_smoke", "urgency", "key_facts"]
            }
        },
        temperature=0.0,
    )
    return json.loads(response.choices[0].message.content)
```

### Step 3: Update case state + fuse evidence

```python
async def process_transcript(case_id: str, feed_id: str, language: str, original_text: str):
    """Full pipeline from raw transcript to case state update."""
    
    # 1. Translate
    text_en = await translate_to_english(original_text, language)
    
    # 2. Write translated transcript to Supabase
    await supabase.table("transcripts").update({
        "translated_text": text_en,
    }).eq("case_id", case_id).eq("original_text", original_text).execute()
    
    # 3. Extract structured facts
    facts = await extract_intake_facts(case_id, text_en, language)
    
    # 4. Log to agent terminal
    await log_agent_event(case_id, {
        "agent": "INTAKEAGENT",
        "model": "elevenlabs-scribe",
        "event_type": "TRANSCRIPTION",
        "detail": f"Feed {feed_id} ({language.upper()}): \"{original_text[:50]}...\"",
    })
    await log_agent_event(case_id, {
        "agent": "INTAKEAGENT",
        "model": "mistral-large",
        "event_type": "FACTS_EXTRACTED",
        "detail": f"Extracted: {', '.join(facts['key_facts'])}",
    })
    
    # 5. Merge facts into case state
    current_state = await get_case_state(case_id)
    updated_state = merge_facts(current_state, facts, feed_id)
    
    # 6. Compute severity
    new_severity = compute_severity(updated_state)
    if new_severity != current_state["severity"]:
        await log_agent_event(case_id, {
            "agent": "EVIDENCEFUSION",
            "model": "mistral-large",
            "event_type": "SEVERITY_DELTA",
            "detail": f"{current_state['severity'].upper()} → {new_severity.upper()}",
        })
        updated_state["severity"] = new_severity
    
    # 7. Rebuild action plan
    action_plan = await rebuild_action_plan(case_id, updated_state)
    updated_state["recommended_units"] = action_plan["recommended_units"]
    updated_state["current_action_plan_version"] += 1
    
    # 8. Write updated state to Supabase (frontend reacts automatically)
    await supabase.table("incident_state").update(
        updated_state
    ).eq("case_id", case_id).execute()
```

### Step 4: Severity computation logic

```python
def compute_severity(state: dict) -> str:
    """Deterministic severity based on accumulated evidence."""
    hazards = state.get("hazard_flags", [])
    injuries = state.get("injury_flags", [])
    
    # Critical if: fire + trapped person, or fire + child, or 3+ hazards
    if "engine_fire" in hazards and ("trapped_occupant" in injuries or "child_present" in injuries):
        return "critical"
    if len(hazards) >= 3:
        return "critical"
    
    # High if: trapped person, or child, or fire alone
    if "trapped_occupant" in injuries or "child_present" in injuries or "engine_fire" in hazards:
        return "high"
    
    # Medium if: vehicle collision confirmed
    if state.get("incident_type") == "vehicle_collision":
        return "medium"
    
    return "low"
```

### Step 5: Action plan / dispatch recommendations

```python
DISPATCH_RULES = {
    "vehicle_collision": ["EMS", "Traffic Control"],
    "trapped_occupant": ["Heavy Rescue"],
    "child_present": ["Pediatric EMS"],
    "engine_fire": ["Fire Response"],
    "explosion_risk": ["HazMat", "Evacuation Team"],
}

async def rebuild_action_plan(case_id: str, state: dict) -> dict:
    """Determine recommended dispatch units based on accumulated evidence."""
    units = set()
    
    if state.get("incident_type") in ("vehicle_collision", "vehicle_collision_fire"):
        units.update(DISPATCH_RULES["vehicle_collision"])
    
    for flag in state.get("injury_flags", []):
        if flag in DISPATCH_RULES:
            units.update(DISPATCH_RULES[flag])
    
    for flag in state.get("hazard_flags", []):
        if flag in DISPATCH_RULES:
            units.update(DISPATCH_RULES[flag])
    
    new_units = units - set(state.get("recommended_units", []))
    for unit in new_units:
        await log_agent_event(case_id, {
            "agent": "TRIAGEAGENT",
            "model": "mistral-large",
            "event_type": "DISPATCH_RECOMMENDED",
            "detail": f"New recommendation: {unit}",
        })
    
    return {"recommended_units": list(units)}
```

---

## Vision pipeline (parallel, independent)

The vision agent runs on its own schedule, extracting frames at hardcoded timestamps:

```python
FRAME_EXTRACTION_SCHEDULE = [
    {"video_time_s": 25, "description": "Post-crash smoke check"},
    {"video_time_s": 38, "description": "Fire detection check"},
]

async def run_vision_pipeline(case_id: str, video_path: str):
    """Extract frames at scheduled times and analyze with Pixtral."""
    for schedule in FRAME_EXTRACTION_SCHEDULE:
        # Wait until video playback reaches this timestamp
        await wait_until_video_time(schedule["video_time_s"])
        
        # Extract frame
        frame_b64 = extract_frame(video_path, schedule["video_time_s"])
        
        # Analyze with Pixtral
        analysis = await analyze_scene(frame_b64)
        
        # Log and update state
        await log_agent_event(case_id, {
            "agent": "VISIONAGENT",
            "model": "pixtral-12b",
            "event_type": "SCENE_ANALYSIS" if not analysis.get("fire_visible") else "HAZARD_DETECTED",
            "detail": format_vision_result(analysis),
        })
        
        # Write to case state (triggers same evidence fusion)
        await update_case_with_vision(case_id, analysis)
```

---

## Evacuation warning generation (ElevenLabs TTS)

When the evidence fusion agent determines `evacuation_warning_required = true` (fire detected + people at risk), the system generates TTS warnings in all detected languages:

```python
VOICE_MAP = {
    "es": "voice_id_spanish_female",   # Replace with actual ElevenLabs voice IDs
    "zh": "voice_id_mandarin_female",
    "fr": "voice_id_french_male",
    "en": "voice_id_english_male",
}

EVACUATION_MESSAGES = {
    "es": "¡Atención! Se ha detectado fuego en el vehículo. ¡Aléjense inmediatamente del área!",
    "zh": "注意！车辆检测到起火。请立即远离该区域！",
    "fr": "Attention ! Un incendie a été détecté dans le véhicule. Éloignez-vous immédiatement de la zone !",
    "en": "Attention! Fire detected in vehicle. Evacuate the area immediately!",
}

async def generate_evacuation_warnings(case_id: str, detected_languages: list[str]):
    """Generate and play TTS evacuation warnings in all detected languages."""
    for lang in detected_languages:
        message = EVACUATION_MESSAGES.get(lang, EVACUATION_MESSAGES["en"])
        voice_id = VOICE_MAP.get(lang, VOICE_MAP["en"])
        
        # Generate TTS audio
        audio = await elevenlabs.text_to_speech.convert(
            voice_id=voice_id,
            text=message,
            model_id="eleven_multilingual_v2",
        )
        
        # Save to file for playback
        output_path = f"assets/generated/evacuation_{lang}.mp3"
        with open(output_path, "wb") as f:
            for chunk in audio:
                f.write(chunk)
        
        # Log the event
        await log_agent_event(case_id, {
            "agent": "VOICEAGENT",
            "model": "elevenlabs-tts",
            "event_type": "EVACUATION_WARNING",
            "detail": f"Warning broadcast in {lang.upper()}: \"{message[:40]}...\"",
        })
        
        # Write to transcripts table so frontend shows outbound message
        await supabase.table("transcripts").insert({
            "case_id": case_id,
            "feed_id": "DISPATCH",
            "language": lang,
            "original_text": message,
            "translated_text": EVACUATION_MESSAGES["en"],
            "direction": "outbound",
            "priority": "evacuation",
            "audio_url": output_path,
            "timestamp": time.time(),
        }).execute()
```

### Pre-generation option for demo reliability

For bulletproof demo, pre-generate all evacuation audio files once:

```python
# Run once before demo day
async def pre_generate_tts_assets():
    for lang, message in EVACUATION_MESSAGES.items():
        audio = await elevenlabs.text_to_speech.convert(
            voice_id=VOICE_MAP[lang],
            text=message,
            model_id="eleven_multilingual_v2",
        )
        with open(f"assets/tts/evacuation_{lang}.mp3", "wb") as f:
            for chunk in audio:
                f.write(chunk)
    print("All TTS assets pre-generated.")
```

Then during the demo, play from cache instead of calling the API live. The agent terminal still logs `VOICEAGENT · elevenlabs-tts · EVACUATION_WARNING` — judges can't tell the difference.

---

## Orchestrator — master timeline

The orchestrator coordinates video playback, audio streaming, and vision extraction:

```python
async def run_demo(case_id: str):
    """Master orchestrator — drives the entire 45-second demo."""
    
    # 1. Init
    await init_case(case_id)
    
    # 2. Start Scribe connection
    scribe_conn = await connect_scribe()
    register_scribe_handlers(scribe_conn, case_id)
    
    # 3. Signal frontend to start video playback
    await supabase.table("demo_control").update({
        "status": "playing",
        "video_url": "/assets/scene.mp4",
    }).eq("case_id", case_id).execute()
    
    # 4. Start streaming audio to Scribe (runs for full video duration)
    audio_task = asyncio.create_task(
        stream_audio_to_scribe(scribe_conn, "assets/scene_audio.pcm")
    )
    
    # 5. Start vision pipeline (extracts frames at scheduled timestamps)
    vision_task = asyncio.create_task(
        run_vision_pipeline(case_id, "assets/scene.mp4")
    )
    
    # 6. Wait for human approval (frontend sends POST /demo/approve)
    # This happens asynchronously — the approval endpoint updates state
    
    # 7. Wait for audio + vision to complete
    await asyncio.gather(audio_task, vision_task)
    
    # 8. Check if evacuation was triggered (by evidence fusion)
    state = await get_case_state(case_id)
    if "engine_fire" in state.get("hazard_flags", []):
        detected_langs = list(feed_registry.keys())
        await generate_evacuation_warnings(case_id, detected_langs)
    
    # 9. Generate final case summary
    await generate_case_summary(case_id)
    
    # 10. Signal demo complete
    await supabase.table("demo_control").update({
        "status": "complete",
    }).eq("case_id", case_id).execute()
```

---

## Supabase tables

### `incident_state`
Primary case state. One row per demo run.

| Column | Type | Notes |
|--------|------|-------|
| case_id | text PK | e.g. "TN-2026-00417" |
| status | text | intake → active → escalated → critical → resolved_demo |
| incident_type | text | vehicle_collision → vehicle_collision_fire |
| severity | text | unknown → medium → high → critical |
| location_normalized | text | "Market St & 5th St" |
| caller_count | int | Count of unique audio feeds |
| people_count_estimate | int | |
| injury_flags | text[] | ["trapped_occupant", "child_present"] |
| hazard_flags | text[] | ["engine_fire"] |
| vision_detections | jsonb[] | Raw Pixtral outputs |
| recommended_units | text[] | ["EMS", "Traffic Control", ...] |
| confirmed_units | text[] | Operator-approved units |
| current_action_plan_version | int | Increments on each rebuild |
| operator_summary | text | Generated at demo end |
| updated_at | timestamptz | |

### `transcripts`
Every speech segment from Scribe + outbound TTS messages.

| Column | Type | Notes |
|--------|------|-------|
| id | uuid PK | |
| case_id | text FK | |
| feed_id | text | FEED_1, FEED_2, FEED_3, DISPATCH |
| language | text | es, zh, fr, en |
| original_text | text | Original language text |
| translated_text | text | English translation |
| direction | text | "inbound" or "outbound" |
| priority | text | null or "evacuation" |
| audio_url | text | Path to audio file if outbound |
| facts_extracted | jsonb | Structured facts from intake agent |
| timestamp | float | |

### `agent_logs`
Every agent action for the terminal display.

| Column | Type | Notes |
|--------|------|-------|
| id | uuid PK | |
| case_id | text FK | |
| agent | text | INTAKEAGENT, TRIAGEAGENT, VISIONAGENT, etc. |
| model | text | mistral-large, pixtral-12b, elevenlabs-scribe, elevenlabs-tts |
| event_type | text | TRANSCRIPTION, FACTS_EXTRACTED, SEVERITY_DELTA, etc. |
| detail | text | Human-readable description |
| timestamp | float | |

### `dispatches`
Recommended and confirmed dispatch units.

| Column | Type | Notes |
|--------|------|-------|
| id | uuid PK | |
| case_id | text FK | |
| unit_type | text | EMS, Traffic Control, Pediatric EMS, Fire Response |
| unit_callsign | text | AMB-7, TC-3, PEDS-1, ENG-4 |
| status | text | recommended → confirmed → dispatched |
| rationale | text | Why this unit was recommended |
| timestamp | float | |

### `demo_control`
Coordinates frontend playback state.

| Column | Type | Notes |
|--------|------|-------|
| case_id | text PK | |
| status | text | ready → playing → complete |
| video_url | text | Path to scene.mp4 |
| approve_enabled | boolean | When true, frontend shows pulsing button |
| approve_clicked | boolean | Set by frontend POST /demo/approve |

---

## API endpoints

### `POST /demo/start`
Creates a new case, initializes all state, starts audio streaming and vision pipeline.

**Response:**
```json
{
  "case_id": "TN-2026-00417",
  "status": "playing"
}
```

### `POST /demo/approve`
Operator confirms the current recommended dispatch units.

**Request:**
```json
{
  "case_id": "TN-2026-00417"
}
```

**Effect:** Moves all `recommended` dispatches to `confirmed`. Logs operator approval event. Disables the approve button via `demo_control`.

### `GET /cases/{case_id}`
Returns the complete frozen case state for the post-demo report page. Joins incident_state + transcripts + agent_logs + dispatches.

---

## Error handling

| Failure | Mitigation |
|---------|------------|
| Scribe WebSocket drops | Reconnect once. If it fails again, continue demo with vision-only intelligence. Log error to agent terminal as `SCRIBE CONNECTION LOST`. |
| Scribe returns empty transcript | Ignore. Don't pass to agent pipeline. |
| Mistral call takes >5s | The demo still works — the UI just waits for the next Supabase update. No timeout needed. |
| Pixtral call fails | Log error. The audio pipeline continues independently. |
| ElevenLabs TTS fails | Play pre-generated cached audio instead. |

---

## Testing checklist

- [ ] `ffmpeg` extracts clean PCM from scene.mp4
- [ ] Scribe WebSocket connects and returns `SESSION_STARTED`
- [ ] Scribe detects Spanish, Mandarin, and French correctly from the mixed audio
- [ ] Committed transcripts arrive within 1-2s of speech ending
- [ ] Partial transcripts show live in the frontend transcript panel
- [ ] Each committed transcript triggers the full agent pipeline
- [ ] Severity escalates correctly: unknown → medium → high → critical
- [ ] Vision detections at t=25s and t=38s produce correct hazard flags
- [ ] Evidence fusion correctly combines audio + vision sources
- [ ] Evacuation warnings generate (or play from cache) in all 3 languages
- [ ] Agent terminal shows model names on every log line
- [ ] Post-demo report page loads at `/cases/TN-2026-00417`
- [ ] Full demo runs in ≤50 seconds
- [ ] Demo can be reset and re-run cleanly