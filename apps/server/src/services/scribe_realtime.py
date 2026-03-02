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
CHUNK_DURATION_MS = 100  # Send audio in 100ms chunks for lower latency
CHUNK_SIZE = SAMPLE_RATE * BYTES_PER_SAMPLE * CHUNK_DURATION_MS // 1000  # 3200 bytes per chunk

# Streaming speed multiplier: 1.0 = real-time, 2.0 = double speed
# Faster streaming gives Scribe more audio to work with sooner
STREAM_SPEED_MULTIPLIER = 2.0


def detect_language_heuristic(text: str) -> str:
    """
    Fast heuristic language detection from text content.
    Used as fallback when Scribe doesn't return language_code.
    No API calls — runs in microseconds.
    """
    if not text or len(text.strip()) < 3:
        return "unknown"

    # Check for CJK characters (Chinese/Japanese/Korean)
    cjk_count = sum(1 for c in text if '\u4e00' <= c <= '\u9fff' or '\u3400' <= c <= '\u4dbf')
    if cjk_count > len(text) * 0.2:
        # Distinguish Chinese vs Japanese (presence of hiragana/katakana)
        jp_count = sum(1 for c in text if '\u3040' <= c <= '\u309f' or '\u30a0' <= c <= '\u30ff')
        return "ja" if jp_count > 0 else "zh"

    # Check for Arabic script
    arabic_count = sum(1 for c in text if '\u0600' <= c <= '\u06ff')
    if arabic_count > len(text) * 0.2:
        return "ar"

    # Check for Cyrillic script
    cyrillic_count = sum(1 for c in text if '\u0400' <= c <= '\u04ff')
    if cyrillic_count > len(text) * 0.2:
        return "ru"

    # Check for Korean-specific (Hangul)
    hangul_count = sum(1 for c in text if '\uac00' <= c <= '\ud7af')
    if hangul_count > len(text) * 0.2:
        return "ko"

    # Latin-script languages — check common words
    lower = text.lower()

    # Spanish indicators
    es_words = {"el", "la", "los", "las", "de", "del", "en", "que", "por", "con",
                "un", "una", "es", "se", "no", "hay", "está", "están", "fue",
                "fuego", "ayuda", "accidente", "persona", "coche", "carro",
                "herido", "atención", "emergencia", "bomberos", "aquí"}
    es_score = sum(1 for w in lower.split() if w in es_words)

    # French indicators — unique words that don't overlap with Spanish
    fr_words = {"le", "les", "des", "du", "une", "est", "il",
                "ce", "qui", "dans", "pour", "avec", "sur", "pas", "sont",
                "feu", "personne", "voiture", "blessé", "attention",
                "urgence", "pompiers", "ici", "deux", "aussi", "très",
                "nous", "vous", "leur", "cette", "ces", "mais", "ou"}
    fr_score = sum(1 for w in lower.split() if w in fr_words)
    # French-unique bigrams
    if " y a " in lower or " il y " in lower or " c'est " in lower or " n'est " in lower:
        fr_score += 3

    # English indicators
    en_words = {"the", "is", "are", "was", "were", "in", "on", "at", "to", "for",
                "and", "but", "or", "not", "with", "from", "this", "that", "have",
                "fire", "help", "accident", "person", "car", "injured", "here",
                "emergency", "please", "there"}
    en_score = sum(1 for w in lower.split() if w in en_words)

    # Spanish-specific characters
    if any(c in lower for c in "ñáéíóú¿¡"):
        es_score += 3

    # French-specific characters
    if any(c in lower for c in "çàâêëîôùûüÿœæ"):
        fr_score += 3

    scores = {"es": es_score, "fr": fr_score, "en": en_score}
    best = max(scores, key=scores.get)
    if scores[best] >= 2:
        return best

    return "unknown"


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
        self._stream_start: float = 0  # Set when audio streaming begins

    async def connect(self):
        """Connect to Scribe v2 Realtime WebSocket via SDK."""
        t0 = time.time()
        print("[SCRIBE] Connecting to Scribe v2 Realtime...")
        client = ElevenLabs(api_key=settings.elevenlabs_api_key)
        t1 = time.time()
        print(f"[SCRIBE] Client created ({(t1-t0)*1000:.0f}ms)")

        self._connection = await client.speech_to_text.realtime.connect(
            RealtimeAudioOptions(
                model_id="scribe_v2_realtime",
                audio_format=AudioFormat.PCM_16000,
                sample_rate=SAMPLE_RATE,
                commit_strategy=CommitStrategy.VAD,
                vad_silence_threshold_secs=0.8,  # Commit faster (default 1.5s)
                vad_threshold=0.3,  # More sensitive speech detection (default 0.4)
                min_silence_duration_ms=50,  # Detect shorter pauses
                include_timestamps=True,
            )
        )
        t2 = time.time()
        print(f"[SCRIBE] WebSocket connected ({(t2-t1)*1000:.0f}ms)")

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

        print(f"[SCRIBE] Ready — total connect time: {(time.time()-t0)*1000:.0f}ms")
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
        commit_time = time.time()
        self._transcript_count += 1
        if isinstance(data, dict):
            text = data.get("text", "")
            language = data.get("language_code") or data.get("language") or None
        else:
            text = getattr(data, "text", "")
            language = getattr(data, "language_code", None) or getattr(data, "language", None)

        # Scribe often returns None for language_code — detect from text content
        if not language or language == "unknown":
            language = detect_language_heuristic(text)
            print(f"[SCRIBE] Language detected via heuristic: {language} (Scribe returned None)")

        feed_id = self.feed_registry.get_feed_id(language)
        print(f"[SCRIBE] *** COMMITTED #{self._transcript_count} [{feed_id}] ({language}) "
              f"at T+{commit_time - self._stream_start:.1f}s: {text[:100]}" if self._stream_start else
              f"[SCRIBE] *** COMMITTED #{self._transcript_count} [{feed_id}] ({language}): {text[:100]}")
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
        Stream PCM file to Scribe v2 in small chunks, faster than real-time.
        Scribe VAD handles commits automatically based on speech pauses.

        Speed multiplier (STREAM_SPEED_MULTIPLIER) controls how fast audio is sent:
        - 1.0 = real-time (1s of audio takes 1s to send)
        - 2.0 = double speed (1s of audio takes 0.5s to send)
        This reduces time-to-first-transcript significantly.
        """
        await self._connected.wait()

        file_size = os.path.getsize(pcm_path)
        total_duration = file_size / (SAMPLE_RATE * BYTES_PER_SAMPLE)
        total_chunks = file_size // CHUNK_SIZE
        effective_duration = total_duration / STREAM_SPEED_MULTIPLIER
        print(f"[SCRIBE] Streaming audio: {pcm_path} ({file_size} bytes, "
              f"{total_duration:.1f}s audio at {STREAM_SPEED_MULTIPLIER}x = "
              f"{effective_duration:.1f}s wall time, {total_chunks} chunks)")
        logger.info(f"Streaming audio: {pcm_path} at {STREAM_SPEED_MULTIPLIER}x speed")

        stream_start = time.time()
        self._stream_start = stream_start
        chunk_index = 0
        # How many chunks per log line (roughly 1 second of audio)
        log_interval = max(1, int(1000 / CHUNK_DURATION_MS))

        with open(pcm_path, "rb") as f:
            while True:
                chunk = f.read(CHUNK_SIZE)
                if not chunk:
                    break
                if self._closed:
                    logger.info("Scribe connection closed mid-stream, stopping")
                    break

                chunk_index += 1

                # Pace with speed multiplier: at 2x, wait half the real-time duration
                paced_interval = CHUNK_DURATION_MS / 1000 / STREAM_SPEED_MULTIPLIER
                expected_time = stream_start + (chunk_index * paced_interval)
                now = time.time()
                if expected_time > now:
                    await asyncio.sleep(expected_time - now)

                # Send chunk — handle server closing connection gracefully
                try:
                    chunk_b64 = base64.b64encode(chunk).decode("utf-8")
                    await self._connection.send({
                        "audio_base_64": chunk_b64,
                        "sample_rate": SAMPLE_RATE,
                    })
                except Exception as e:
                    if "1000" in str(e):
                        logger.info("Scribe server closed connection (normal)")
                    else:
                        logger.warning(f"Scribe send error: {e}")
                    break

                # Log every ~1 second of audio
                if chunk_index % log_interval == 0:
                    elapsed = time.time() - stream_start
                    audio_time = chunk_index * CHUNK_DURATION_MS / 1000
                    print(f"[SCRIBE] Chunk {chunk_index}/{total_chunks} "
                          f"(audio T+{audio_time:.1f}s, wall T+{elapsed:.1f}s)")

        total_time = time.time() - stream_start
        print(f"[SCRIBE] Audio streaming complete: {chunk_index} chunks in {total_time:.1f}s "
              f"({total_duration:.1f}s audio at {STREAM_SPEED_MULTIPLIER}x)")
        logger.info(f"Audio streaming complete. {chunk_index} chunks sent in {total_time:.1f}s")

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
