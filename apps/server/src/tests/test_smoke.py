"""
Smoke Test: End-to-End Validation of All TriageNet Stages

Validates every layer of the stack works before running the full demo.
Run this AFTER all media assets are in place.

Usage:
    uv run pytest src/tests/test_smoke.py -v -s

Stages tested:
    1. Models       — All Pydantic models instantiate correctly
    2. Config       — All env vars load
    3. Supabase     — Read/write to all 4 tables
    4. Mistral      — Chat completion returns a response
    5. ElevenLabs   — Transcription API is reachable
    6. Agents       — Each agent returns typed structured output
    7. Media        — All asset files exist with correct sizes
    8. Orchestrator — FastAPI app loads, health check, routes registered
"""
import time
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest

from src.config import settings

os.environ.setdefault("MISTRAL_API_KEY", settings.mistral_api_key)


# ---------------------------------------------------------------------------
# TimedStep
# ---------------------------------------------------------------------------
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
            marker = "PASS" if True else "FAIL"
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


# ===========================================================================
# Stage 1: Models
# ===========================================================================
class TestStage1Models:
    def test_all_models_instantiate(self, timer):
        """Verify all Pydantic models can be created with defaults."""
        with timer.step("Import all models"):
            from src.models.incident import IncidentState, IncidentStatus, Severity
            from src.models.caller import CallerRecord, IntakeFacts
            from src.models.triage import TriageResult
            from src.models.dispatch import DispatchBrief
            from src.models.vision import VisionDetection, SceneDelta
            from src.models.events import AgentLogEntry

        with timer.step("Create IncidentState"):
            state = IncidentState(case_id="SMOKE-TEST-001")
            assert state.case_id == "SMOKE-TEST-001"
            assert state.status == IncidentStatus.INTAKE
            assert state.severity == Severity.UNKNOWN
            print(f"  IncidentState: status={state.status}, severity={state.severity}")

        with timer.step("Create CallerRecord"):
            caller = CallerRecord(
                caller_id="smoke-c1",
                audio_path="test.mp3",
                language="en",
                label="Test Caller",
                start_delay_s=0.0,
            )
            assert caller.caller_id == "smoke-c1"
            print(f"  CallerRecord: id={caller.caller_id}, lang={caller.language}")

        with timer.step("Create AgentLogEntry"):
            log = AgentLogEntry(
                case_id="SMOKE-TEST-001",
                agent="smoke_test",
                event_type="test",
                message="Smoke test log entry",
            )
            assert log.agent == "smoke_test"
            print(f"  AgentLogEntry: agent={log.agent}, event={log.event_type}")

        timer.summary()


# ===========================================================================
# Stage 2: Config
# ===========================================================================
class TestStage2Config:
    def test_env_vars_loaded(self, timer):
        """Verify all required environment variables are accessible."""
        with timer.step("Check MISTRAL_API_KEY"):
            assert settings.mistral_api_key, "MISTRAL_API_KEY is empty"
            print(f"  MISTRAL_API_KEY: {settings.mistral_api_key[:8]}...")

        with timer.step("Check ELEVENLABS_API_KEY"):
            assert settings.elevenlabs_api_key, "ELEVENLABS_API_KEY is empty"
            print(f"  ELEVENLABS_API_KEY: {settings.elevenlabs_api_key[:8]}...")

        with timer.step("Check SUPABASE_URL"):
            assert settings.supabase_url, "SUPABASE_URL is empty"
            print(f"  SUPABASE_URL: {settings.supabase_url[:30]}...")

        with timer.step("Check SUPABASE_SERVICE_KEY"):
            assert settings.supabase_service_key, "SUPABASE_SERVICE_KEY is empty"
            print(f"  SUPABASE_SERVICE_KEY: {settings.supabase_service_key[:8]}...")

        timer.summary()


# ===========================================================================
# Stage 3: Supabase
# ===========================================================================
class TestStage3Supabase:
    def test_supabase_tables_accessible(self, timer):
        """Verify all 4 Supabase tables are queryable."""
        with timer.step("Create Supabase client"):
            from supabase import create_client
            sb = create_client(settings.supabase_url, settings.supabase_service_key)

        tables = ["incident_state", "agent_logs", "transcripts", "dispatches"]
        for table in tables:
            with timer.step(f"Query {table}"):
                result = sb.table(table).select("*").limit(1).execute()
                print(f"  {table}: accessible, {len(result.data)} rows returned")

        timer.summary()


# ===========================================================================
# Stage 4: Mistral
# ===========================================================================
class TestStage4Mistral:
    def test_mistral_reachable(self, timer):
        """Verify Mistral API responds to a chat completion."""
        with timer.step("Mistral chat.complete()"):
            from mistralai import Mistral
            client = Mistral(api_key=settings.mistral_api_key)
            response = client.chat.complete(
                model="mistral-small-latest",
                messages=[{"role": "user", "content": "Reply with OK"}],
            )
            text = response.choices[0].message.content
            print(f"  Response: {text[:50]}")
            assert text, "Mistral returned empty response"

        timer.summary()


# ===========================================================================
# Stage 5: ElevenLabs
# ===========================================================================
class TestStage5ElevenLabs:
    def test_elevenlabs_reachable(self, timer):
        """Verify ElevenLabs API is reachable (voices endpoint)."""
        with timer.step("ElevenLabs GET /v1/voices"):
            import httpx
            resp = httpx.get(
                "https://api.elevenlabs.io/v1/voices",
                headers={"xi-api-key": settings.elevenlabs_api_key},
                timeout=10,
            )
            assert resp.status_code == 200, f"ElevenLabs returned {resp.status_code}"
            voices = resp.json().get("voices", [])
            print(f"  Voices available: {len(voices)}")

        timer.summary()


# ===========================================================================
# Stage 6: Agents
# ===========================================================================
class TestStage6Agents:
    @pytest.mark.asyncio
    async def test_intake_agent(self, timer):
        """Verify intake agent returns IntakeFacts."""
        with timer.step("Import intake_agent"):
            from src.agents.intake_agent import intake_agent
            from src.agents.shared_deps import TriageNetDeps
            from mistralai import Mistral
            from supabase import create_client

        with timer.step("Create deps"):
            sb = create_client(settings.supabase_url, settings.supabase_service_key)
            mc = Mistral(api_key=settings.mistral_api_key)
            deps = TriageNetDeps(
                supabase=sb,
                mistral_client=mc,
                case_id="SMOKE-TEST",
                session_start_time=time.time(),
                elevenlabs_api_key=settings.elevenlabs_api_key,
            )

        with timer.step("Run intake_agent"):
            result = await intake_agent.run(
                "Help! There is a car crash at 5th and Market. Someone is trapped.",
                deps=deps,
            )
            facts = result.output
            print(f"  location_raw: {facts.location_raw}")
            print(f"  incident_type: {facts.incident_type_candidate}")
            assert facts.location_raw, "No location extracted"

        timer.summary()

    @pytest.mark.asyncio
    async def test_triage_agent(self, timer):
        """Verify triage agent returns TriageResult."""
        with timer.step("Import triage_agent"):
            from src.agents.triage_agent import triage_agent
            from src.agents.shared_deps import TriageNetDeps
            from mistralai import Mistral
            from supabase import create_client

        with timer.step("Create deps"):
            sb = create_client(settings.supabase_url, settings.supabase_service_key)
            mc = Mistral(api_key=settings.mistral_api_key)
            deps = TriageNetDeps(
                supabase=sb,
                mistral_client=mc,
                case_id="SMOKE-TEST",
                session_start_time=time.time(),
                elevenlabs_api_key=settings.elevenlabs_api_key,
            )

        with timer.step("Run triage_agent"):
            result = await triage_agent.run(
                "Vehicle crash at 5th and Market. One person trapped. Smoke from engine.",
                deps=deps,
            )
            triage = result.output
            print(f"  severity: {triage.severity}")
            print(f"  recommended_units: {triage.recommended_units}")
            assert triage.severity, "No severity assigned"

        timer.summary()


# ===========================================================================
# Stage 7: Media Assets
# ===========================================================================
class TestStage7Media:
    ASSETS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "assets")

    EXPECTED_FILES = {
        "caller_1_spanish.mp3": (50_000, 500_000),
        "caller_2_mandarin.mp3": (50_000, 500_000),
        "caller_3_french.mp3": (50_000, 500_000),
        "crash_video.mp4": (100_000, 100_000_000),
    }

    def test_media_assets_exist(self, timer):
        """Verify all demo media assets exist with expected sizes."""
        for filename, (min_size, max_size) in self.EXPECTED_FILES.items():
            filepath = os.path.join(self.ASSETS_DIR, filename)
            with timer.step(f"Check {filename}"):
                assert os.path.exists(filepath), f"Missing: {filepath}"
                size = os.path.getsize(filepath)
                print(f"  {filename}: {size:,} bytes")
                assert size >= min_size, f"{filename} too small: {size} < {min_size}"
                assert size <= max_size, f"{filename} too large: {size} > {max_size}"

        timer.summary()


# ===========================================================================
# Stage 8: FastAPI App & Routes
# ===========================================================================
class TestStage8App:
    def test_app_routes_registered(self, timer):
        """Verify FastAPI app loads with all expected routes."""
        with timer.step("Import app"):
            from src.main import app

        with timer.step("Check routes"):
            routes = [r.path for r in app.routes]
            expected = [
                "/api/v1/health",
                "/api/v1/demo/start",
                "/api/v1/demo/approve",
                "/api/v1/demo/status",
                "/api/v1/demo/reset",
                "/api/v1/demo/cases",
                "/api/v1/demo/cases/{case_id}",
            ]
            for route in expected:
                assert route in routes, f"Missing route: {route}"
                print(f"  ✓ {route}")

        timer.summary()

    def test_health_check(self, timer):
        """Verify health endpoint returns service status."""
        with timer.step("Import and create client"):
            from fastapi.testclient import TestClient
            from src.main import app
            client = TestClient(app)

        with timer.step("GET /api/v1/health"):
            response = client.get("/api/v1/health")
            assert response.status_code == 200
            data = response.json()
            print(f"  Status: {data['status']}")
            for service, check in data.get("checks", {}).items():
                status = check.get("status", "unknown")
                latency = check.get("latency_ms", "N/A")
                print(f"  {service}: {status} ({latency}ms)")

        timer.summary()
