"""
Vision Pipeline Test — Real Crash Video

Tests the full vision pipeline against a real crash video:
1. Extract frames at multiple timestamps via ffmpeg
2. Send each frame to Pixtral (mistral vision model) via vision_agent
3. Compute scene deltas between consecutive frames
4. Log all detections, descriptions, and escalations

Usage:
    uv run pytest src/tests/test_vision_real.py -v -s
"""
import time
import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.config import settings

os.environ.setdefault("MISTRAL_API_KEY", settings.mistral_api_key)


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


# Real crash video from frontend assets
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
REAL_VIDEO = os.path.join(REPO_ROOT, "apps", "web", "public", "video", "crash_01.mp4")
# Timestamps to sample across the 15s video
TIMESTAMPS = [0, 3, 5, 7, 10, 13]


class TestVisionRealVideo:
    @pytest.mark.asyncio
    async def test_extract_and_analyze_frames(self, timer):
        """Extract frames from real crash video and analyze with Pixtral."""
        from src.services.media import extract_frame
        from src.agents.vision_agent import analyze_frame, compute_scene_delta
        from mistralai import Mistral

        assert os.path.exists(REAL_VIDEO), f"Video not found: {REAL_VIDEO}"
        video_size = os.path.getsize(REAL_VIDEO)

        print(f"\n=== VISION PIPELINE TEST — REAL CRASH VIDEO ===")
        print(f"Video: crash_01.mp4 ({video_size:,} bytes)")
        print(f"Model: {settings.mistral_vision_model}")
        print(f"Timestamps: {TIMESTAMPS}")
        print()

        client = Mistral(api_key=settings.mistral_api_key)
        prev_analysis = None
        all_analyses = []

        for i, ts in enumerate(TIMESTAMPS):
            # Extract frame
            with timer.step(f"Extract frame {i+1} (t={ts}s)"):
                frame = await extract_frame(REAL_VIDEO, timestamp_s=ts)
                print(f"  Size: {len(frame):,} bytes")
                if len(frame) < 1000:
                    # extract_frame silently fell back to placeholder — try direct ffmpeg
                    import subprocess
                    result = subprocess.run([
                        "ffmpeg", "-ss", str(ts), "-i", REAL_VIDEO,
                        "-frames:v", "1", "-f", "image2", "-c:v", "mjpeg", "-q:v", "2", "pipe:1",
                    ], capture_output=True, timeout=10)
                    frame = result.stdout
                    print(f"  Direct ffmpeg: {len(frame):,} bytes")
                assert len(frame) > 1000, f"Frame too small ({len(frame)} bytes)"

            # Analyze with Pixtral
            with timer.step(f"Pixtral analyze frame {i+1} (t={ts}s)"):
                analysis = await analyze_frame(client, frame, frame_id=i + 1)
                print(f"  Description: {analysis.overall_description}")
                print(f"  Smoke: {analysis.smoke_visible}")
                print(f"  Fire: {analysis.fire_visible}")
                print(f"  Damage: {analysis.vehicle_damage_severity}")
                for d in analysis.detections:
                    print(f"    Detection: {d.type} (confidence={d.confidence})")

            # Scene delta
            if prev_analysis:
                delta = compute_scene_delta(prev_analysis, analysis)
                if delta["hazard_escalation"]:
                    print(f"  ** ESCALATION: {delta['new_hazard']} **")
                print(f"  Delta: {delta['description']}")

            prev_analysis = analysis
            all_analyses.append(analysis)
            print()

        # Assertions
        assert len(all_analyses) == len(TIMESTAMPS), "Not all frames analyzed"
        descriptions = [a.overall_description for a in all_analyses]
        print("=== ALL DESCRIPTIONS ===")
        for i, desc in enumerate(descriptions):
            print(f"  t={TIMESTAMPS[i]}s: {desc}")

        timer.summary()
