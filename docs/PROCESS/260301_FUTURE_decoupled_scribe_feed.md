# Future Feature: Decoupled Scribe Listener + Feed Source

**Shelved**: 2026-03-01

## Concept

Decouple Scribe v2 "listening" from the audio playback source:

1. **Phase 1**: `POST /demo/start` → init case, connect Scribe WebSocket → LISTENING
2. **Phase 2**: `POST /demo/feed` → start streaming audio (scene.mp4, mic, live feed)

## Why

- Can demo Scribe is live before playing video
- Could speak into mic to show real-time processing
- Could swap in a live camera feed
- Frontend "INITIATE FEED" button triggers feed independently

## Implementation Notes

- Split orchestrator `start()` into `_init_and_listen()` + `begin_feed()`
- Add `POST /demo/feed` endpoint
- Store `_video_path` and `_pcm_path` as instance vars between phases
- `demo_control` status flow: `starting → listening → ready → playing → complete`
