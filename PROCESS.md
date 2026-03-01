# TriageNet Latency Optimization — Process Log

## Problem Statement

In an emergency dispatch system, delays cost lives. Two critical latency issues identified:

1. **Scribe transcripts take 8-12s to appear on screen**
2. **Vision intelligence takes 25-30s to appear on screen**

---

## Root Cause Analysis

### Audio/Scribe Pipeline — Before

| Step | Latency | Blocking? |
|---|---|---|
| Audio chunks: 250ms, real-time paced (1x) | 250ms first chunk | Yes |
| Scribe VAD accumulation (1.5s silence threshold) | 5-10s | Inherent |
| Raw transcript → Supabase INSERT | 100-300ms | **Yes — blocked callback** |
| Supabase Realtime → Frontend | ~200ms | Inherent |
| Translation (Mistral API) | 500-1000ms | **Yes — sequential** |
| Intake agent (Mistral API) | 800-1500ms | **Yes — sequential after translate** |
| Supabase UPDATE (translation + facts) | 100-200ms | **Yes — blocked pipeline** |
| Triage agent (Mistral API + 3 Supabase reads) | 1-2s | **Yes — sequential** |
| Evidence fusion agent | 1-2s | **Yes — sequential** |
| **Total: raw transcript on screen** | **8-12s** | |
| **Total: translation on screen** | **12-16s** | |

### Vision Pipeline — Before

| Step | Latency | Issue |
|---|---|---|
| `asyncio.sleep(25.0)` before Frame 1 | **25 seconds** | Hardcoded wait |
| `analyze_frame()` — synchronous Mistral call | 2-5s | Blocked event loop |
| `asyncio.sleep(13.0)` before Frame 2 | 13 seconds | Hardcoded wait |
| Only 2 frames total | N/A | Minimal coverage |
| **Total: first vision result** | **~27-30s** | |

---

## Optimizations Applied

### 1. Parallel Agent Execution (orchestrator.py)

**Before:** translate → intake → update → triage → fusion (all sequential)

**After:**
```
Phase 1: translate + intake  ← IN PARALLEL (asyncio.gather)
Phase 2: Supabase UPDATE     ← FIRE-AND-FORGET (asyncio.create_task)
Phase 3: triage              ← Still sequential (needs facts from intake)
Phase 4: evidence fusion     ← DEFERRED TO BACKGROUND
```

Savings: ~1-2s per transcript (translate + intake overlap instead of sequential)

### 2. Fire-and-Forget Supabase Writes (orchestrator.py)

**Before:** All Supabase writes awaited on critical path
**After:** Raw insert + translation update are `asyncio.create_task` — don't block pipeline

Savings: ~200-400ms off critical path

### 3. Faster Audio Streaming (scribe_realtime.py)

**Before:** 250ms chunks, 1x real-time pacing
**After:** 100ms chunks, 2x speed (`STREAM_SPEED_MULTIPLIER = 2.0`)

Scribe gets audio faster → accumulates enough speech to commit sooner.

### 4. Tuned VAD Parameters (scribe_realtime.py)

```python
vad_silence_threshold_secs=0.8   # Was 1.5s default
vad_threshold=0.3                # Was 0.4 default (more sensitive)
min_silence_duration_ms=50       # Detect shorter pauses
```

### 5. Live Partials for Instant Feedback (frontend)

- New `useLivePartials` hook subscribes to `live_partials` Supabase table
- TranscriptPanel shows green "LIVE" shimmer with partial text as Scribe detects speech
- User sees activity immediately — before Scribe commits

### 6. Continuous Vision Analysis (orchestrator.py)

**Before:** 2 fixed frames at t=25s and t=38s
**After:** Frame every 3 seconds starting at t=3s, running until video ends

```python
VISION_START_S = 3.0       # First frame at 3s (was 25s)
VISION_INTERVAL_S = 3.0    # Every 3 seconds (was 2 fixed frames)
```

- Frames analyzed concurrently (overlapping API calls)
- Auto-detects video duration via ffprobe
- No max frame cap — covers entire video

### 7. Async Vision API (vision_agent.py)

**Before:** `mistral_client.chat.complete()` — synchronous, blocks event loop
**After:** `mistral_client.chat.complete_async()` — non-blocking

### 8. Evidence Fusion Deferred (orchestrator.py)

**Before:** Awaited on critical path (1-2s per transcript after the 2nd)
**After:** `asyncio.create_task()` — runs in background, evacuation warnings still fire

---

## Predicted Latency — After

### Audio/Scribe Pipeline

| Step | Latency | Notes |
|---|---|---|
| Audio chunks: 100ms, 2x speed | 50ms first chunk | Faster delivery |
| Scribe VAD (0.8s threshold, 2x audio) | ~2-4s | Gets audio faster |
| Raw transcript → Supabase (fire-and-forget) | 0ms on critical path | Background |
| Supabase Realtime → Frontend | ~200ms | Same |
| **Partial transcript (LIVE shimmer)** | **~1-2s** | New — instant feedback |
| **Raw transcript on screen** | **~3-5s** | Was 8-12s |
| Translate + Intake (parallel) | ~1-1.5s | Was 1.5-2.5s sequential |
| Supabase UPDATE (fire-and-forget) | 0ms on critical path | Background |
| **Translation on screen** | **~4-7s** | Was 12-16s |
| Triage | ~1-2s | Same |
| Evidence fusion | 0ms on critical path | Background |

### Vision Pipeline

| Step | Latency | Notes |
|---|---|---|
| First frame extraction | 3s + 100ms | Was 25s |
| Mistral vision API (async) | 2-5s | Non-blocking |
| **First vision on screen** | **~5-8s** | Was 27-30s |
| Subsequent frames | Every 3s | Continuous coverage |

---

## Why Scribe Has Inherent Latency

ElevenLabs Scribe v2 with VAD (Voice Activity Detection):

1. **Buffers incoming audio** — needs context for accurate transcription
2. **PARTIAL transcripts** stream almost immediately (~250ms) — shown as "LIVE" shimmer
3. **COMMITTED transcripts** fire only when VAD detects a **speech pause** (0.8s silence)
4. Continuous speech without pauses = longer buffer before commit
5. This is by design: accuracy over speed. Word-by-word streaming exists but is less accurate.

**Mitigation:** Live partials give instant visual feedback. Committed transcripts trigger the agent pipeline.

---

## Files Modified

| File | Change |
|---|---|
| `apps/server/src/services/orchestrator.py` | Parallel agents, fire-and-forget writes, continuous vision, deferred fusion |
| `apps/server/src/services/scribe_realtime.py` | 100ms chunks, 2x speed, timing instrumentation |
| `apps/server/src/services/media.py` | Added `get_video_duration()` |
| `apps/server/src/agents/vision_agent.py` | Async Mistral API call |
| `apps/web/src/hooks/useLivePartials.ts` | New — subscribes to live_partials table |
| `apps/web/src/hooks/useTranscripts.ts` | Listen for UPDATE events (translations) |
| `apps/web/src/components/TranscriptPanel.tsx` | Live partial shimmer indicator |
| `apps/web/src/components/Dashboard.tsx` | Wire up live partials |

---

## Summary

| Metric | Before | After | Improvement |
|---|---|---|---|
| Time to first visual feedback (partials) | N/A | ~1-2s | New |
| Time to raw transcript | 8-12s | 3-5s | **~60% faster** |
| Time to translation | 12-16s | 4-7s | **~60% faster** |
| Time to first vision | 27-30s | 5-8s | **~75% faster** |
| Vision frame coverage | 2 frames | Every 3s | **Continuous** |
| Evidence fusion on critical path | 1-2s | 0s | **100% off critical path** |
