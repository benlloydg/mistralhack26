"""
Phase 6: Orchestrator & API Tests
Tests FastAPI server startup, health check, and demo endpoints.
All operations are timed with [elapsed] output and total summary.

USER TESTING INSTRUCTIONS:
1. Ensure all env vars are set in .env (MISTRAL_API_KEY, ELEVENLABS_API_KEY, SUPABASE_URL, SUPABASE_SERVICE_KEY)
2. Ensure SQL migrations have been run in Supabase
3. Run: uv run pytest src/tests/test_phase6_orchestrator.py -v -s
4. For manual testing:
   - Start server: uv run uvicorn src.main:app --reload
   - Health check: curl http://localhost:8000/api/v1/health
   - Start demo: curl -X POST http://localhost:8000/api/v1/demo/start
   - Approve: curl -X POST http://localhost:8000/api/v1/demo/approve
   - Status: curl http://localhost:8000/api/v1/demo/status
"""
import time
import pytest
from fastapi.testclient import TestClient

import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.config import settings

# Ensure MISTRAL_API_KEY is available for pydantic-ai
os.environ.setdefault("MISTRAL_API_KEY", settings.mistral_api_key)

from src.main import app


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
def client():
    return TestClient(app)


class TestFastAPIServer:
    def test_app_loads(self, timer, client):
        """Test that the FastAPI app loads and routes are registered."""
        with timer.step("Verify app loads"):
            routes = [r.path for r in app.routes]
            assert "/api/v1/health" in routes
            assert "/api/v1/demo/start" in routes
            assert "/api/v1/demo/approve" in routes
            assert "/api/v1/demo/status" in routes
            print(f"  Routes: {routes}")

        timer.summary()

    def test_health_check(self, timer, client):
        """Test health endpoint returns API connectivity status."""
        with timer.step("GET /api/v1/health"):
            response = client.get("/api/v1/health")

        with timer.step("Validate health response"):
            assert response.status_code == 200
            data = response.json()
            assert "status" in data
            assert "checks" in data
            print(f"  Status: {data['status']}")
            for service, check in data["checks"].items():
                status = check.get("status", "unknown")
                latency = check.get("latency_ms", "N/A")
                print(f"  {service}: {status} ({latency}ms)")

        timer.summary()

    def test_demo_status_no_active(self, timer, client):
        """Test demo status when no demo is running."""
        with timer.step("GET /api/v1/demo/status"):
            response = client.get("/api/v1/demo/status")

        with timer.step("Validate response"):
            assert response.status_code == 200
            data = response.json()
            print(f"  Response: {data}")

        timer.summary()

    def test_demo_approve_no_active(self, timer, client):
        """Test approve when no demo is running."""
        with timer.step("POST /api/v1/demo/approve"):
            response = client.post("/api/v1/demo/approve")

        with timer.step("Validate response"):
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "no_active_demo"
            print(f"  Response: {data}")

        timer.summary()
