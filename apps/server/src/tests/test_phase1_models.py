"""
Phase 1: Model Validation Tests
Tests all Pydantic models for correct instantiation, defaults, validation, and serialization.
All operations are timed with [elapsed] output and total summary.
"""
import time
import pytest
from pydantic import ValidationError

from src.models.incident import (
    Severity, IncidentStatus, TimelineEvent, ActionItem, IncidentState,
)
from src.models.caller import TranscriptSegment, IntakeFacts, CallerRecord
from src.models.vision import VisionDetection, FrameAnalysis, SceneDelta
from src.models.triage import TriageResult, Corroboration, EvidenceFusionResult
from src.models.dispatch import DispatchBrief
from src.models.events import AgentLogEntry


class TimedStep:
    """Context manager that prints elapsed time for each test operation."""
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


# --- IncidentState ---

class TestIncidentState:
    def test_valid_creation_with_defaults(self, timer):
        with timer.step("IncidentState with defaults"):
            state = IncidentState(case_id="TN-2026-00417")
            assert state.case_id == "TN-2026-00417"
            assert state.status == IncidentStatus.INTAKE
            assert state.severity == Severity.UNKNOWN
            assert state.caller_count == 0
            assert state.injury_flags == []
            assert state.hazard_flags == []
            assert state.vision_detections == []
            assert state.timeline == []
            assert state.action_plan == []
            assert state.confidence_scores == {}

    def test_valid_creation_with_all_fields(self, timer):
        with timer.step("IncidentState with all fields"):
            state = IncidentState(
                case_id="TN-2026-00417",
                status=IncidentStatus.ACTIVE,
                incident_type="vehicle_collision",
                location_raw="Market & 5th",
                location_normalized="Market St & 5th St, SF",
                severity=Severity.HIGH,
                caller_count=2,
                people_count_estimate=5,
                injury_flags=["trapped_person"],
                hazard_flags=["engine_fire"],
                recommended_units=["EMS", "Fire Response"],
                match_confidence=0.92,
            )
            assert state.severity == Severity.HIGH
            assert state.caller_count == 2
            assert "trapped_person" in state.injury_flags

    def test_invalid_severity_rejected(self, timer):
        with timer.step("IncidentState rejects invalid severity"):
            with pytest.raises(ValidationError):
                IncidentState(case_id="TN-001", severity="INVALID")

    def test_invalid_status_rejected(self, timer):
        with timer.step("IncidentState rejects invalid status"):
            with pytest.raises(ValidationError):
                IncidentState(case_id="TN-001", status="nonexistent")

    def test_json_serialization(self, timer):
        with timer.step("IncidentState JSON round-trip"):
            state = IncidentState(
                case_id="TN-2026-00417",
                severity=Severity.CRITICAL,
                timeline=[TimelineEvent(t="00:15", agent="triage", event="Severity escalated")],
                action_plan=[ActionItem(status="pending", action="Dispatch EMS")],
            )
            json_str = state.model_dump_json()
            restored = IncidentState.model_validate_json(json_str)
            assert restored.case_id == state.case_id
            assert restored.severity == Severity.CRITICAL
            assert len(restored.timeline) == 1
            assert restored.timeline[0].agent == "triage"

    def test_model_dump_for_supabase(self, timer):
        with timer.step("IncidentState model_dump for Supabase"):
            state = IncidentState(case_id="TN-001")
            d = state.model_dump()
            assert isinstance(d["injury_flags"], list)
            assert isinstance(d["confidence_scores"], dict)
            assert d["status"] == "intake"
            assert d["severity"] == "unknown"
        timer.summary()


# --- Severity & IncidentStatus Enums ---

class TestEnums:
    def test_severity_values(self, timer):
        with timer.step("Severity enum values"):
            assert Severity.UNKNOWN.value == "unknown"
            assert Severity.CRITICAL.value == "critical"
            assert len(Severity) == 5

    def test_incident_status_values(self, timer):
        with timer.step("IncidentStatus enum values"):
            assert IncidentStatus.INTAKE.value == "intake"
            assert IncidentStatus.RESOLVED_DEMO.value == "resolved_demo"
            assert len(IncidentStatus) == 5
        timer.summary()


# --- TimelineEvent & ActionItem ---

class TestEmbeddedModels:
    def test_timeline_event(self, timer):
        with timer.step("TimelineEvent creation"):
            event = TimelineEvent(t="00:15", agent="triage", event="Severity upgraded")
            assert event.t == "00:15"
            assert event.agent == "triage"

    def test_action_item(self, timer):
        with timer.step("ActionItem creation"):
            item = ActionItem(status="pending", action="Dispatch EMS unit")
            assert item.status == "pending"
        timer.summary()


# --- CallerRecord, TranscriptSegment, IntakeFacts ---

class TestCallerModels:
    def test_caller_record(self, timer):
        with timer.step("CallerRecord creation"):
            caller = CallerRecord(
                caller_id="caller_1", label="The Wife",
                language="es", audio_path="assets/caller_1_spanish.mp3",
                start_delay_s=12.0,
            )
            assert caller.status == "queued"
            assert caller.language == "es"

    def test_transcript_segment(self, timer):
        with timer.step("TranscriptSegment creation"):
            seg = TranscriptSegment(
                caller_id="caller_1", language="es",
                original_text="¡Ayuda! Hay un accidente.",
                segment_index=0, confidence=0.95,
            )
            assert seg.translated_text is None
            assert seg.entities == []

    def test_intake_facts_defaults(self, timer):
        with timer.step("IntakeFacts defaults"):
            facts = IntakeFacts()
            assert facts.possible_trapped_person is False
            assert facts.child_present is False
            assert facts.urgency_keywords == []

    def test_intake_facts_full(self, timer):
        with timer.step("IntakeFacts with all fields"):
            facts = IntakeFacts(
                location_raw="Market & 5th",
                incident_type_candidate="vehicle_crash",
                possible_trapped_person=True,
                child_present=True,
                urgency_keywords=["trapped", "child"],
            )
            assert facts.possible_trapped_person is True
            assert len(facts.urgency_keywords) == 2
        timer.summary()


# --- Vision Models ---

class TestVisionModels:
    def test_vision_detection(self, timer):
        with timer.step("VisionDetection creation"):
            det = VisionDetection(
                type="vehicle_collision", confidence=0.87,
                bbox=[100, 200, 300, 400],
            )
            assert det.confidence == 0.87
            assert det.count is None

    def test_frame_analysis(self, timer):
        with timer.step("FrameAnalysis creation"):
            fa = FrameAnalysis(
                frame_id=1,
                detections=[
                    VisionDetection(type="vehicle_collision", confidence=0.9),
                    VisionDetection(type="persons_visible", confidence=0.8, count=3),
                ],
                overall_description="Multi-vehicle collision at intersection",
                smoke_visible=True,
            )
            assert len(fa.detections) == 2
            assert fa.smoke_visible is True
            assert fa.fire_visible is False

    def test_scene_delta_defaults(self, timer):
        with timer.step("SceneDelta defaults"):
            delta = SceneDelta()
            assert delta.new_hazard is None
            assert delta.hazard_escalation is False
        timer.summary()


# --- Triage Models ---

class TestTriageModels:
    def test_triage_result(self, timer):
        with timer.step("TriageResult creation"):
            result = TriageResult(
                severity=Severity.HIGH,
                incident_type="vehicle_collision",
                reasoning="Multiple vehicles involved, person reported trapped",
                recommended_units=["EMS", "Fire Response"],
                people_count_estimate=4,
                injury_flags=["trapped_person"],
            )
            assert result.severity == Severity.HIGH
            assert "EMS" in result.recommended_units

    def test_corroboration(self, timer):
        with timer.step("Corroboration creation"):
            c = Corroboration(
                claim="Person trapped in vehicle",
                sources=[
                    {"type": "caller_1", "confidence": 0.9},
                    {"type": "vision", "confidence": 0.85},
                ],
                combined_confidence=0.985,
            )
            assert c.status == "corroborated"
            assert len(c.sources) == 2

    def test_evidence_fusion_result(self, timer):
        with timer.step("EvidenceFusionResult creation"):
            efr = EvidenceFusionResult(
                severity_delta="HIGH -> CRITICAL",
                new_severity=Severity.CRITICAL,
                evacuation_warning_required=True,
                reasoning="Fire confirmed by vision + caller reports",
            )
            assert efr.evacuation_warning_required is True
            assert efr.new_severity == Severity.CRITICAL
        timer.summary()


# --- Dispatch Models ---

class TestDispatchModels:
    def test_dispatch_brief(self, timer):
        with timer.step("DispatchBrief creation"):
            brief = DispatchBrief(
                unit_type="EMS",
                unit_assigned="AMB-7",
                destination="Mass General ER",
                eta_minutes=8,
                voice_message="AMB-7 dispatched to Market & 5th for vehicle collision. ETA 8 minutes.",
                rationale="Multiple injuries reported, trapped person confirmed",
            )
            assert brief.unit_assigned == "AMB-7"
            assert brief.eta_minutes == 8
        timer.summary()


# --- Event Models ---

class TestEventModels:
    def test_agent_log_entry(self, timer):
        with timer.step("AgentLogEntry creation"):
            entry = AgentLogEntry(
                case_id="TN-2026-00417",
                agent="triage",
                event_type="severity_changed",
                message="Severity upgraded to HIGH",
                data={"old": "medium", "new": "high"},
                display_color="amber",
                display_flash=True,
            )
            assert entry.agent == "triage"
            assert entry.display_flash is True

    def test_agent_log_entry_defaults(self, timer):
        with timer.step("AgentLogEntry defaults"):
            entry = AgentLogEntry(
                case_id="TN-001", agent="orchestrator",
                event_type="init", message="Demo started",
            )
            assert entry.display_color == "blue"
            assert entry.display_flash is False
            assert entry.data == {}
        timer.summary()
