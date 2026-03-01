"""
Phase 4: ElevenLabs API Connectivity Tests
Tests TTS generation via ElevenLabs API.
All operations are timed with [elapsed] output and total summary.

USER TESTING INSTRUCTIONS:
1. Ensure ELEVENLABS_API_KEY is set in .env
2. Run: uv run pytest src/tests/test_phase4_elevenlabs.py -v -s
3. Verify TTS returns audio bytes and response time is < 10s
"""
import time
import pytest
import httpx

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.services.tts import generate_speech


class TimedStep:
    def __init__(self):
        self.steps: list[tuple[str, float]] = []
        self.total_start = time.time()

    def step(self, label: str):
        return _StepCtx(self, label)

    def summary(self):
        total = time.time() - self.total_start
        print(f"\n{'='*60}")
        print(f"TOTAL ELAPSED: [{total:.3f}s]")
        for label, elapsed in self.steps:
            print(f"  [{elapsed:.3f}s] {label}")
        print(f"{'='*60}")


class _StepCtx:
    def __init__(self, timer: TimedStep, label: str):
        self.timer = timer
        self.label = label

    def __enter__(self):
        self.start = time.time()
        return self

    def __exit__(self, *args):
        elapsed = time.time() - self.start
        self.timer.steps.append((self.label, elapsed))
        print(f"[{elapsed:.3f}s] {self.label}")


@pytest.fixture
def timer():
    return TimedStep()


class TestElevenLabsTTS:
    @pytest.mark.asyncio
    async def test_tts_generates_audio_bytes(self, timer):
        """Test that ElevenLabs TTS returns audio bytes for English text."""
        with timer.step("ElevenLabs TTS generate_speech()"):
            try:
                audio_bytes = await generate_speech(
                    text="Ambulance 7 dispatched to Market and 5th Street. ETA 8 minutes.",
                    language="en",
                )
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 401 and "quota_exceeded" in e.response.text:
                    pytest.skip("ElevenLabs API quota exceeded")
                raise

        with timer.step("Validate audio bytes"):
            assert isinstance(audio_bytes, bytes)
            assert len(audio_bytes) > 1000  # Should be a reasonable audio file
            print(f"  Audio size: {len(audio_bytes)} bytes")

        # Verify timing
        total_time = sum(e for _, e in timer.steps)
        assert total_time < 15.0, f"TTS took {total_time:.1f}s, expected < 15s"

        timer.summary()
