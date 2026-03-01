"""
Scribe v2 Realtime — streams PCM audio to ElevenLabs WebSocket,
dispatches partial and committed transcript events to callbacks.

Design goal: MINIMAL LATENCY. Each committed transcript chunk fires
the on_committed callback immediately so the agent pipeline can begin
processing while audio is still streaming.

Uses the ElevenLabs Python SDK's realtime speech-to-text connection.
"""
import asyncio
import base64
import logging
import os
import struct
import time
from typing import Callable, Awaitable

from elevenlabs import (
    ElevenLabs,
    RealtimeEvents,
    RealtimeAudioOptions,
    AudioFormat,
    CommitStrategy,
)

from ..config import settings

logger = logging.getLogger(__name__)

# PCM constants: 16kHz, 16-bit, mono → 32,000 bytes/sec
SAMPLE_RATE = 16000
BYTES_PER_SAMPLE = 2  # 16-bit
CHUNK_DURATION_MS = 250  # Send audio in 250ms chunks
CHUNK_SIZE = SAMPLE_RATE * BYTES_PER_SAMPLE * CHUNK_DURATION_MS // 1000  # 8000 bytes per chunk

# Silence detection: if all samples in a chunk are below threshold, it's silence
SILENCE_THRESHOLD = 300  # amplitude threshold for silence detection
SILENCE_CHUNKS_FOR_COMMIT = 4  # 4 × 250ms = 1 second of silence triggers commit


class FeedRegistry:
    """Maps detected languages to sequential feed IDs (FEED_1, FEED_2, etc.)."""

    def __init__(self):
        self._lang_to_feed: dict[str, str] = {}
        self._counter = 0

    def get_feed_id(self, language_code: str) -> str:
        if language_code not in self._lang_to_feed:
            self._counter += 1
            self._lang_to_feed[language_code] = f"FEED_{self._counter}"
        return self._lang_to_feed[language_code]

    @property
    def languages(self) -> list[str]:
        return list(self._lang_to_feed.keys())


class ScribeRealtimeService:
    """
    Streams PCM audio to ElevenLabs Scribe v2 Realtime WebSocket.

    Events:
    - on_partial: called with partial transcript text (for UI shimmer)
    - on_committed: called with committed transcript data (triggers agent pipeline)

    The on_committed callback is the critical path — it should immediately
    trigger translate → intake → triage → dispatch for minimal latency.
    """

    def __init__(
        self,
        on_partial: Callable[[str, float], Awaitable[None]] | None = None,
        on_committed: Callable[[dict], Awaitable[None]] | None = None,
    ):
        self._on_partial = on_partial
        self._on_committed = on_committed
        self._connection = None
        self._connected = asyncio.Event()
        self._closed = False
        self.feed_registry = FeedRegistry()
        self._transcript_count = 0

    async def connect(self):
        """Connect to Scribe v2 Realtime WebSocket via SDK."""
        print("[SCRIBE] Connecting to Scribe v2 Realtime...")
        client = ElevenLabs(api_key=settings.elevenlabs_api_key)

        self._connection = await client.speech_to_text.realtime.connect(
            RealtimeAudioOptions(
                model_id="scribe_v2_realtime",
                audio_format=AudioFormat.PCM_16000,
                sample_rate=SAMPLE_RATE,
                commit_strategy=CommitStrategy.MANUAL,
                include_timestamps=True,
            )
        )
        print(f"[SCRIBE] Connection object: {type(self._connection).__name__}")

        # Capture the running event loop for scheduling async callbacks
        self._loop = asyncio.get_running_loop()

        # Register event handlers — SDK calls these synchronously,
        # so async handlers need sync wrappers that schedule coroutines.
        # NOTE: Only listen to COMMITTED_TRANSCRIPT_WITH_TIMESTAMPS (not plain
        # COMMITTED_TRANSCRIPT) to avoid processing the same transcript twice.
        self._connection.on(RealtimeEvents.SESSION_STARTED, self._handle_session_started)
        self._connection.on(RealtimeEvents.PARTIAL_TRANSCRIPT, self._wrap_async(self._handle_partial))
        self._connection.on(RealtimeEvents.COMMITTED_TRANSCRIPT_WITH_TIMESTAMPS, self._wrap_async(self._handle_committed))
        self._connection.on(RealtimeEvents.ERROR, self._handle_error)
        self._connection.on(RealtimeEvents.CLOSE, self._handle_close)

        print("[SCRIBE] Event handlers registered, connection ready")
        logger.info("Scribe v2 Realtime: connected")
        self._connected.set()

    def _wrap_async(self, coro_fn):
        """Wrap an async handler so the SDK can call it synchronously."""
        def wrapper(*args, **kwargs):
            asyncio.run_coroutine_threadsafe(coro_fn(*args, **kwargs), self._loop)
        return wrapper

    def _handle_session_started(self, data):
        print(f"[SCRIBE] SESSION STARTED: {data}")
        logger.info(f"Scribe v2 session started: {data}")

    async def _handle_partial(self, data):
        """Partial transcript — write to live_partials for UI shimmer."""
        text = data.get("text", "") if isinstance(data, dict) else getattr(data, "text", "")
        print(f"[SCRIBE] PARTIAL: '{text[:60]}...' " if len(str(text)) > 60 else f"[SCRIBE] PARTIAL: '{text}'")
        if text and self._on_partial:
            await self._on_partial(text, time.time())

    async def _handle_committed(self, data):
        """
        Committed transcript — this is the critical low-latency path.
        Immediately fires the callback so agents can start processing.
        """
        self._transcript_count += 1
        if isinstance(data, dict):
            text = data.get("text", "")
            language = data.get("language_code") or data.get("language") or "unknown"
        else:
            text = getattr(data, "text", "")
            language = getattr(data, "language_code", None) or getattr(data, "language", None) or "unknown"

        feed_id = self.feed_registry.get_feed_id(language)
        print(f"[SCRIBE] *** COMMITTED #{self._transcript_count} [{feed_id}] ({language}): {text[:100]}")
        logger.info(f"Scribe v2 committed [{feed_id}] ({language}): {text[:80]}...")

        if text and self._on_committed:
            await self._on_committed({
                "text": text,
                "language_code": language,
                "feed_id": feed_id,
                "segment_index": self._transcript_count,
                "timestamp": time.time(),
            })

    def _handle_error(self, data):
        print(f"[SCRIBE] ERROR: {data}")
        logger.error(f"Scribe v2 error: {data}")

    def _handle_close(self, data=None):
        print(f"[SCRIBE] CONNECTION CLOSED: {data}")
        logger.info("Scribe v2 connection closed")
        self._closed = True

    async def stream_audio(self, pcm_path: str):
        """
        Stream PCM file to Scribe v2 in 250ms chunks, paced to real-time.
        Commits after detecting silence gaps in the audio.
        """
        await self._connected.wait()

        file_size = os.path.getsize(pcm_path)
        total_duration = file_size / (SAMPLE_RATE * BYTES_PER_SAMPLE)
        total_chunks = file_size // CHUNK_SIZE
        print(f"[SCRIBE] Streaming audio: {pcm_path} ({file_size} bytes, {total_duration:.1f}s, {total_chunks} chunks)")
        logger.info(f"Streaming audio: {pcm_path}")

        silence_count = 0
        has_speech_since_commit = False
        stream_start = time.time()
        chunk_index = 0
        commit_count = 0

        with open(pcm_path, "rb") as f:
            while True:
                chunk = f.read(CHUNK_SIZE)
                if not chunk:
                    break

                chunk_index += 1

                # Pace to real-time: wait until the wall clock catches up
                expected_time = stream_start + (chunk_index * CHUNK_DURATION_MS / 1000)
                now = time.time()
                if expected_time > now:
                    await asyncio.sleep(expected_time - now)

                # Send chunk
                chunk_b64 = base64.b64encode(chunk).decode("utf-8")
                await self._connection.send({
                    "audio_base_64": chunk_b64,
                    "sample_rate": SAMPLE_RATE,
                })

                # Log every 4th chunk (1 second intervals)
                elapsed = time.time() - stream_start
                if chunk_index % 4 == 0:
                    print(f"[SCRIBE] Chunk {chunk_index}/{total_chunks} sent (T+{elapsed:.1f}s)")

                # Silence detection for manual commit
                is_silent = _is_silence(chunk)
                if is_silent:
                    silence_count += 1
                else:
                    silence_count = 0
                    has_speech_since_commit = True

                # Commit after sustained silence following speech
                if silence_count >= SILENCE_CHUNKS_FOR_COMMIT and has_speech_since_commit:
                    commit_count += 1
                    print(f"[SCRIBE] >>> COMMIT #{commit_count} at chunk {chunk_index} (T+{elapsed:.1f}s) — silence detected after speech")
                    await self._connection.commit()
                    has_speech_since_commit = False
                    silence_count = 0

        # Final commit for any remaining audio
        if has_speech_since_commit:
            commit_count += 1
            print(f"[SCRIBE] >>> FINAL COMMIT #{commit_count} — end of audio")
            await self._connection.commit()

        total_time = time.time() - stream_start
        print(f"[SCRIBE] Audio streaming complete: {chunk_index} chunks, {commit_count} commits in {total_time:.1f}s")

        logger.info(f"Audio streaming complete. {chunk_index} chunks sent in {time.time() - stream_start:.1f}s")

    async def disconnect(self):
        """Close the WebSocket connection."""
        self._closed = True
        if self._connection:
            await self._connection.close()
        logger.info("Scribe v2 disconnected")


def _is_silence(chunk: bytes) -> bool:
    """Check if a PCM chunk is silence (all samples below threshold)."""
    if len(chunk) < 2:
        return True
    # Unpack as signed 16-bit little-endian samples
    num_samples = len(chunk) // 2
    samples = struct.unpack(f"<{num_samples}h", chunk[:num_samples * 2])
    # Check if RMS is below threshold
    rms = (sum(s * s for s in samples) / num_samples) ** 0.5
    return rms < SILENCE_THRESHOLD
