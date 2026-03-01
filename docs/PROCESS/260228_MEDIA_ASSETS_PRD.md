# Media Assets PRD — TriageNet Demo

> **Purpose**: Create 4 pre-recorded media files for the 120-second TriageNet demo.
> These are consumed by the backend orchestrator. They must exist before the demo can run.

---

## Output Location

```
apps/server/assets/
├── caller_1_spanish.mp3    # Spanish wife reporting crash
├── caller_2_mandarin.mp3   # Mandarin bystander reporting child
├── caller_3_french.mp3     # French shopkeeper reporting smoke/fire
└── crash_video.mp4         # CCTV footage of vehicle collision
```

---

## 1. Audio Files (3 Caller Recordings)

All audio files are sent to ElevenLabs Scribe v1 for transcription. The orchestrator expects the transcription to return meaningful emergency content in the caller's language.

### Option A: Generate with ElevenLabs TTS (Recommended)

Use ElevenLabs TTS API to generate realistic caller audio. This guarantees the transcription will work perfectly since ElevenLabs generated it.

**API Endpoint**: `POST https://api.elevenlabs.io/v1/text-to-speech/{voice_id}`

**Voice IDs** (from our `services/tts.py`):
- Spanish: `pFZP5JQG7iQjIQuC4Bku` (Lily)
- Chinese: `nPczCjzI2devNBz1zQrb` (Brian)
- French: `XB0fDUnXU5powFXDhCwa` (Charlotte)

### Option B: Use free TTS tools

Google Translate TTS, macOS `say` command, or any other TTS tool. Just ensure the audio is clear enough for Scribe v1 to transcribe.

---

### caller_1_spanish.mp3 — "The Wife"

**Language**: Spanish (es)
**Character**: Distressed wife, calling from the crash scene
**Duration**: 8-15 seconds
**Emotional tone**: Panicked, urgent

**Script (Spanish)**:
```
¡Ayuda! ¡Por favor, ayuda! Hubo un choque terrible en la calle Market con la Quinta.
Mi esposo está atrapado en el carro. No puede salir. Hay humo saliendo del motor.
¡Por favor, manden una ambulancia rápido!
```

**Translation (for reference)**:
```
Help! Please, help! There was a terrible crash at Market Street and 5th.
My husband is trapped in the car. He can't get out. There's smoke coming from the engine.
Please, send an ambulance quickly!
```

**What the intake agent must extract**:
- `location_raw`: "Market con la Quinta" or similar
- `incident_type_candidate`: "vehicle_crash"
- `possible_trapped_person`: true
- `hazard_description`: smoke from engine
- `urgency_keywords`: ["atrapado", "humo", "ambulancia"]

---

### caller_2_mandarin.mp3 — "The Bystander"

**Language**: Mandarin Chinese (zh)
**Character**: Bystander who sees a child in the backseat
**Duration**: 8-15 seconds
**Emotional tone**: Concerned, reporting facts

**Script (Mandarin Chinese)**:
```
喂，我要报警。Market街和第五街路口发生了严重的车祸。
我看到后座有一个小孩在哭。车里好像有两个人受伤了。
路上到处都是碎片，请快点派人来。
```

**Translation (for reference)**:
```
Hello, I need to report an emergency. There's a serious car crash at
Market Street and 5th Street intersection. I can see a child crying
in the backseat. It looks like two people are injured in the car.
There's debris all over the road, please send someone quickly.
```

**What the intake agent must extract**:
- `location_raw`: "Market街和第五街" or similar
- `child_present`: true
- `additional_victim`: true
- `injury_description`: two people injured
- `urgency_keywords`: ["车祸", "小孩", "受伤"]

---

### caller_3_french.mp3 — "The Shopkeeper"

**Language**: French (fr)
**Character**: Shopkeeper across the street, sees smoke turning to fire
**Duration**: 8-15 seconds
**Emotional tone**: Alarmed, escalating urgency

**Script (French)**:
```
Allô, je suis le propriétaire du magasin en face. Il y a un accident grave
sur Market Street. Je vois de la fumée qui sort du moteur, et maintenant
je crois que ça prend feu! Il y a des gens qui essaient de sortir de la voiture.
Envoyez les pompiers immédiatement!
```

**Translation (for reference)**:
```
Hello, I'm the shop owner across the street. There's a serious accident
on Market Street. I can see smoke coming from the engine, and now I think
it's catching fire! There are people trying to get out of the car.
Send the fire department immediately!
```

**What the intake agent must extract**:
- `hazard_description`: smoke, fire
- `incident_type_candidate`: "vehicle_crash" with fire
- `urgency_keywords`: ["feu", "fumée", "pompiers"]

---

## 2. Video File

### crash_video.mp4 — CCTV Footage

**Duration**: ~90 seconds (the orchestrator extracts frames at specific timestamps)
**Resolution**: 720p or higher
**Format**: MP4 (H.264)

The orchestrator extracts frames at:
- **t=58s** — Should show: vehicle collision scene with smoke
- **t=66s** — Should show: same scene but now with visible fire/flames

**Option A: Use stock footage**

Search for "car crash CCTV footage" on free stock video sites:
- Pexels: https://www.pexels.com/search/videos/car%20crash/
- Pixabay: https://pixabay.com/videos/search/car%20accident/
- Coverr: https://coverr.co

Requirements:
- Must show a vehicle collision from a fixed/overhead camera angle
- Bonus if smoke or fire is visible in later frames
- No watermarks

**Option B: Create a synthetic video**

Use AI video generation (Runway, Pika, etc.) to create:
1. A fixed CCTV angle of an intersection
2. A vehicle collision occurs
3. Smoke appears from the engine
4. Smoke intensifies / small fire visible

**Option C: Use a placeholder**

If no suitable video is found, create a simple placeholder:
- Use ffmpeg to generate a 90-second video with text overlays:
  - Frame 1-57: "CCTV FEED — Market St & 5th — Normal traffic"
  - Frame 58-65: "CCTV FEED — SMOKE DETECTED"
  - Frame 66+: "CCTV FEED — FIRE DETECTED"

```bash
# Placeholder video with ffmpeg (fallback)
ffmpeg -f lavfi -i color=c=black:s=1280x720:d=90 \
  -vf "drawtext=text='CCTV FEED - Market St':fontsize=36:fontcolor=white:x=(w-text_w)/2:y=(h-text_h)/2" \
  -c:v libx264 -pix_fmt yuv420p apps/server/assets/crash_video.mp4
```

**Note**: The vision agent (Pixtral) will analyze whatever frame it receives. If the frame is just text, it will describe what it sees. The orchestrator will still run — the vision results just won't be as dramatic for the demo.

---

## 3. Validation

After creating all files, verify:

```bash
# Check files exist and have reasonable sizes
ls -la apps/server/assets/
# Expected:
# caller_1_spanish.mp3   — 50KB-500KB
# caller_2_mandarin.mp3  — 50KB-500KB
# caller_3_french.mp3    — 50KB-500KB
# crash_video.mp4        — 1MB-50MB

# Test transcription works on caller 1
cd apps/server
.venv/bin/python -c "
import asyncio
from src.services.transcription import transcribe_audio
result = asyncio.run(transcribe_audio('assets/caller_1_spanish.mp3'))
print(f'Language: {result[\"language_code\"]}')
print(f'Text: {result[\"text\"]}')
print(f'Confidence: {result[\"confidence\"]}')
"
```

---

## 4. Test Storage

After creating assets and validating, save test output:

```bash
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
# Run transcription tests and save logs
.venv/bin/python -m pytest src/tests/test_phase4_elevenlabs.py -v -s 2>&1 | \
  tee "test-results/${TIMESTAMP}_media_assets_validation.log"
```

See `docs/MASTER/TEST_STORAGE_STANDARD.md` for the full test logging standard.

---

## 5. Timeline Integration

These files are consumed by the orchestrator at these demo timestamps:

| Demo Time | File | Action |
|-----------|------|--------|
| 0:12 | `caller_1_spanish.mp3` | Transcribe → Intake → Triage |
| 0:38 | `caller_2_mandarin.mp3` | Transcribe → Intake → Fusion → Re-triage |
| 0:56 | `caller_3_french.mp3` | Transcribe → Intake (corroborates fire) |
| 0:58 | `crash_video.mp4` @ 58s | Extract frame → Vision (smoke) |
| 1:06 | `crash_video.mp4` @ 66s | Extract frame → Vision (fire) |
