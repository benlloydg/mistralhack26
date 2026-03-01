"""
Phase 2: Supabase State Management Tests
Tests CRUD operations on incident_state and agent_logs tables.
All operations are timed with [elapsed] output and total summary.

USER TESTING INSTRUCTIONS:
1. Ensure SQL migrations 001-005 have been run in Supabase SQL Editor
2. Ensure Realtime is enabled on all 4 tables
3. Run: uv run pytest src/tests/test_phase2_supabase.py -v -s
4. Verify in Supabase dashboard that test data was created and cleaned up
"""
import time
import uuid
import pytest
from supabase import create_client

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.config import settings
from src.models.incident import IncidentState, Severity, IncidentStatus
from src.models.events import AgentLogEntry
from src.services.state import StateManager


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
def supabase():
    return create_client(settings.supabase_url, settings.supabase_service_key)


@pytest.fixture
def test_case_id():
    return f"TEST-{uuid.uuid4().hex[:8]}"


@pytest.fixture
def state_manager(supabase, test_case_id):
    return StateManager(supabase, test_case_id, time.time())


@pytest.fixture(autouse=True)
def cleanup(supabase, test_case_id):
    """Clean up test data after each test."""
    yield
    # Delete in order due to foreign key constraints
    supabase.table("agent_logs").delete().eq("case_id", test_case_id).execute()
    supabase.table("transcripts").delete().eq("case_id", test_case_id).execute()
    supabase.table("dispatches").delete().eq("case_id", test_case_id).execute()
    supabase.table("incident_state").delete().eq("case_id", test_case_id).execute()


class TestSupabaseStateManager:
    def test_create_and_read_incident(self, supabase, test_case_id, state_manager, timer):
        with timer.step("Create incident record"):
            supabase.table("incident_state").insert({
                "case_id": test_case_id,
                "status": "intake",
                "severity": "unknown",
                "caller_count": 0,
            }).execute()

        with timer.step("Read incident back"):
            state = state_manager.get_state()
            assert state.case_id == test_case_id
            assert state.status == IncidentStatus.INTAKE
            assert state.severity == Severity.UNKNOWN
            assert state.caller_count == 0

        timer.summary()

    def test_update_severity(self, supabase, test_case_id, state_manager, timer):
        with timer.step("Create incident"):
            supabase.table("incident_state").insert({
                "case_id": test_case_id,
                "status": "intake",
                "severity": "unknown",
            }).execute()

        with timer.step("Read initial state"):
            initial = state_manager.get_state()
            initial_updated = initial.model_dump().get("updated_at")

        # Small delay to ensure updated_at changes
        time.sleep(0.1)

        with timer.step("Update severity to HIGH"):
            updated = state_manager.update_state(severity="high")
            assert updated.severity == Severity.HIGH

        with timer.step("Verify state persisted"):
            reread = state_manager.get_state()
            assert reread.severity == Severity.HIGH

        timer.summary()

    def test_write_agent_log(self, supabase, test_case_id, state_manager, timer):
        with timer.step("Create incident for log test"):
            supabase.table("incident_state").insert({
                "case_id": test_case_id,
                "status": "intake",
                "severity": "unknown",
            }).execute()

        with timer.step("Write agent log entry"):
            entry = AgentLogEntry(
                case_id=test_case_id,
                agent="triage",
                event_type="severity_changed",
                message="Severity changed to HIGH",
                data={"old": "unknown", "new": "high"},
                display_color="amber",
                display_flash=True,
            )
            state_manager.log_agent(entry)

        with timer.step("Verify log in database"):
            result = supabase.table("agent_logs") \
                .select("*").eq("case_id", test_case_id).execute()
            assert len(result.data) == 1
            log = result.data[0]
            assert log["agent"] == "triage"
            assert log["event_type"] == "severity_changed"
            assert log["display_flash"] is True

        timer.summary()

    def test_append_timeline(self, supabase, test_case_id, state_manager, timer):
        with timer.step("Create incident for timeline test"):
            supabase.table("incident_state").insert({
                "case_id": test_case_id,
                "status": "intake",
                "severity": "unknown",
            }).execute()

        with timer.step("Append timeline event"):
            state_manager.append_timeline("orchestrator", "Demo started")

        with timer.step("Verify timeline in state"):
            state = state_manager.get_state()
            assert len(state.timeline) == 1
            assert state.timeline[0].agent == "orchestrator"
            assert state.timeline[0].event == "Demo started"

        timer.summary()

    def test_convenience_log(self, supabase, test_case_id, state_manager, timer):
        with timer.step("Create incident for convenience log test"):
            supabase.table("incident_state").insert({
                "case_id": test_case_id,
                "status": "intake",
                "severity": "unknown",
            }).execute()

        with timer.step("Use log() convenience method"):
            state_manager.log(
                agent="vision",
                event_type="detection",
                message="Vehicle collision detected",
                data={"confidence": 0.92},
                color="red",
                flash=True,
            )

        with timer.step("Verify both log and timeline"):
            # Check agent_logs
            logs = supabase.table("agent_logs") \
                .select("*").eq("case_id", test_case_id).execute()
            assert len(logs.data) == 1
            assert logs.data[0]["display_color"] == "red"

            # Check timeline
            state = state_manager.get_state()
            assert len(state.timeline) == 1
            assert "Vehicle collision detected" in state.timeline[0].event

        timer.summary()
