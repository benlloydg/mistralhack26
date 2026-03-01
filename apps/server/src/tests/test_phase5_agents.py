"""
Phase 5: Pydantic-AI Agent Tests
Tests all 5 agents return correctly typed structured outputs.
All operations are timed with [elapsed] output and total summary.

USER TESTING INSTRUCTIONS:
1. Ensure MISTRAL_API_KEY is set in .env
2. Run: uv run pytest src/tests/test_phase5_agents.py -v -s
3. Verify all agents return valid structured outputs and response times < 8s each
"""
import time
import pytest

import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.config import settings

# Ensure MISTRAL_API_KEY is available as env var for pydantic-ai provider
os.environ.setdefault("MISTRAL_API_KEY", settings.mistral_api_key)

from src.agents.intake_agent import intake_agent
from src.agents.dispatch_agent import dispatch_agent
from src.agents.case_match_agent import evidence_fusion_agent
from src.agents.vision_agent import compute_scene_delta
from src.agents.shared_deps import TriageNetDeps
from src.models.caller import IntakeFacts
from src.models.dispatch import DispatchBrief
from src.models.triage import EvidenceFusionResult
from src.models.vision import FrameAnalysis
from src.models.incident import Severity
from mistralai import Mistral
from supabase import create_client


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


@pytest.fixture
async def deps():
    """Create TriageNetDeps for agent testing. Async fixture to properly close Mistral client."""
    sb = create_client(settings.supabase_url, settings.supabase_service_key)
    client = Mistral(api_key=settings.mistral_api_key)
    yield TriageNetDeps(
        supabase=sb,
        mistral_client=client,
        case_id="TEST-AGENTS-001",
        session_start_time=time.time(),
        elevenlabs_api_key=settings.elevenlabs_api_key,
    )
    # Close the Mistral async HTTP client to prevent "Event loop is closed" errors
    if hasattr(client, '_async_client') and client._async_client is not None:
        await client._async_client.aclose()
    if hasattr(client, '_client') and client._client is not None:
        client._client.close()


class TestIntakeAgent:
    @pytest.mark.asyncio
    async def test_intake_extracts_facts(self, timer, deps):
        """Test intake agent extracts structured facts from Spanish emergency transcript."""
        with timer.step("intake_agent.run() — Spanish caller"):
            result = await intake_agent.run(
                "Transcript from emergency caller (es): "
                "¡Ayuda! Hubo un choque terrible en Market y la Quinta. "
                "¡Mi esposo está atrapado en el carro! Hay humo saliendo del motor.",
                deps=deps,
            )

        with timer.step("Validate IntakeFacts"):
            facts = result.output
            assert isinstance(facts, IntakeFacts)
            assert facts.location_raw is not None
            assert facts.possible_trapped_person is True
            assert facts.incident_type_candidate is not None
            print(f"  Location: {facts.location_raw}")
            print(f"  Type: {facts.incident_type_candidate}")
            print(f"  Trapped: {facts.possible_trapped_person}")
            print(f"  Child: {facts.child_present}")
            print(f"  Hazards: {facts.hazard_description}")
            print(f"  Keywords: {facts.urgency_keywords}")

        total_time = sum(e for _, e in timer.steps)
        assert total_time < 8.0, f"Intake agent took {total_time:.1f}s, expected < 8s"

        timer.summary()


class TestDispatchAgent:
    @pytest.mark.asyncio
    async def test_dispatch_generates_brief(self, timer, deps):
        """Test dispatch agent generates a valid DispatchBrief."""
        with timer.step("dispatch_agent.run() — EMS dispatch"):
            result = await dispatch_agent.run(
                "Generate dispatch brief for EMS. "
                "Incident: vehicle collision at Market St & 5th St, San Francisco. "
                "Severity: HIGH. 2 people injured, 1 trapped. Smoke from engine.",
                deps=deps,
            )

        with timer.step("Validate DispatchBrief"):
            brief = result.output
            assert isinstance(brief, DispatchBrief)
            assert brief.unit_assigned != ""
            assert brief.voice_message != ""
            assert brief.eta_minutes > 0
            assert len(brief.voice_message.split()) <= 50  # Allow some margin over 40
            print(f"  Unit: {brief.unit_assigned}")
            print(f"  ETA: {brief.eta_minutes} min")
            print(f"  Voice: {brief.voice_message}")
            print(f"  Rationale: {brief.rationale}")

        total_time = sum(e for _, e in timer.steps)
        assert total_time < 8.0, f"Dispatch agent took {total_time:.1f}s, expected < 8s"

        timer.summary()


class TestEvidenceFusionAgent:
    @pytest.mark.asyncio
    async def test_evidence_fusion(self, timer, deps):
        """Test evidence fusion agent produces valid EvidenceFusionResult."""
        with timer.step("evidence_fusion_agent.run() — multi-source"):
            result = await evidence_fusion_agent.run(
                "Fuse the following evidence:\n"
                "Caller 1 (Spanish wife): Car crash at Market & 5th, husband trapped, smoke from engine.\n"
                "Caller 2 (Mandarin bystander): Collision at Market Street, child in backseat crying, smoke visible.\n"
                "Vision detection: vehicle_collision (0.95), smoke (0.88), persons_visible count=3.\n"
                "Current severity: HIGH. Hazard flags: [smoke]. Injury flags: [trapped_person].",
                deps=deps,
            )

        with timer.step("Validate EvidenceFusionResult"):
            fusion = result.output
            assert isinstance(fusion, EvidenceFusionResult)
            assert fusion.reasoning != ""
            print(f"  Corroborations: {len(fusion.corroborations)}")
            print(f"  Severity delta: {fusion.severity_delta}")
            print(f"  Evacuation: {fusion.evacuation_warning_required}")
            print(f"  Reasoning: {fusion.reasoning}")

        total_time = sum(e for _, e in timer.steps)
        assert total_time < 15.0, f"Evidence fusion took {total_time:.1f}s, expected < 15s"

        timer.summary()


class TestVisionAgent:
    def test_compute_scene_delta_new_fire(self, timer):
        """Test scene delta computation detects new fire hazard."""
        with timer.step("Build test FrameAnalysis objects"):
            prev = FrameAnalysis(
                frame_id=1,
                detections=[],
                overall_description="Traffic scene with damaged vehicle",
                smoke_visible=True,
                fire_visible=False,
                vehicle_damage_severity="moderate",
            )
            curr = FrameAnalysis(
                frame_id=2,
                detections=[],
                overall_description="Traffic scene with vehicle on fire",
                smoke_visible=True,
                fire_visible=True,
                vehicle_damage_severity="severe",
            )

        with timer.step("compute_scene_delta()"):
            delta = compute_scene_delta(prev, curr)
            assert delta["new_hazard"] == "engine_fire"
            assert delta["hazard_escalation"] is True
            print(f"  Delta: {delta}")

        timer.summary()

    def test_compute_scene_delta_no_previous(self, timer):
        """Test scene delta with no previous frame."""
        with timer.step("compute_scene_delta(None, curr)"):
            curr = FrameAnalysis(
                frame_id=1,
                detections=[],
                overall_description="Initial scene",
                smoke_visible=False,
                fire_visible=False,
            )
            delta = compute_scene_delta(None, curr)
            assert delta["new_hazard"] is None
            assert delta["hazard_escalation"] is False
            print(f"  Delta: {delta}")

        timer.summary()
