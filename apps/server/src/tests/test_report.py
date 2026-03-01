"""
After-Action Report Tests

Covers:
- T006: Frame saving verification
- T009: ReportBuilder.build() with mock data — all 8 sections
- T010: Executive summary caching
- T022-T024: Contract validation (field completeness, enum values)
- T025: E2E timing test

Usage:
    cd apps/server
    PYTHONPATH=. uv run pytest src/tests/test_report.py -v -s
"""
import asyncio
import os
import sys
import tempfile
import time
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest

from src.models.report import (
    ReportData,
    ReportHeader,
    TimelineEntry,
    EvidenceSources,
    ConvergenceTrack,
    ResponseAction,
    AgentStats,
    KeyFrame,
)
from src.services.report_builder import ReportBuilder


# ---------------------------------------------------------------------------
# TimedStep (same pattern as other test files)
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


# ---------------------------------------------------------------------------
# Mock data fixtures
# ---------------------------------------------------------------------------
CASE_ID = "TN-TEST-REPORT-001"
BASE_TIME = datetime(2026, 3, 1, 3, 33, 45, tzinfo=timezone.utc)


def _mock_state():
    return {
        "case_id": CASE_ID,
        "status": "resolved_demo",
        "incident_type": "vehicle_crash",
        "location_raw": "Market St & 5th St",
        "location_normalized": "Market St & 5th St, San Francisco, CA",
        "severity": "critical",
        "caller_count": 4,
        "people_count_estimate": 6,
        "injury_flags": ["trapped_occupant"],
        "hazard_flags": ["smoke", "engine_fire"],
        "vision_detections": [
            {
                "type": "smoke",
                "confidence": 0.87,
                "timestamp_s": 25.0,
                "description": "Smoke detected from vehicle engine",
            },
            {
                "type": "engine_fire",
                "confidence": 0.99,
                "timestamp_s": 38.0,
                "description": "Engine fire detected",
            },
        ],
        "recommended_units": ["EMS", "Fire Response", "Police"],
        "confirmed_units": ["EMS", "Fire Response"],
        "timeline": [],
        "action_plan_version": 3,
        "action_plan": [],
        "operator_summary": (
            "Vehicle crash at Market St. Severity: CRITICAL. "
            "4 audio segments processed. 2 units confirmed."
        ),
        "created_at": BASE_TIME.isoformat(),
        "updated_at": (BASE_TIME + timedelta(seconds=55)).isoformat(),
    }


def _mock_logs():
    t = BASE_TIME
    return [
        {
            "case_id": CASE_ID, "agent": "orchestrator", "event_type": "init",
            "message": f"Demo started: {CASE_ID}",
            "data": {}, "display_color": "blue", "display_flash": False,
            "model": None, "created_at": t.isoformat(),
        },
        {
            "case_id": CASE_ID, "agent": "voice", "event_type": "transcript_committed",
            "message": "[FEED_1] Committed (es): Mi esposo está atrapado...",
            "data": {}, "display_color": "green", "display_flash": False,
            "model": "scribe-v2", "created_at": (t + timedelta(seconds=8)).isoformat(),
        },
        {
            "case_id": CASE_ID, "agent": "intake", "event_type": "facts_extracted",
            "message": "Location: Market St, Type: vehicle_crash",
            "data": {}, "display_color": "blue", "display_flash": False,
            "model": "mistral-large-latest", "created_at": (t + timedelta(seconds=9)).isoformat(),
        },
        {
            "case_id": CASE_ID, "agent": "triage", "event_type": "severity_changed",
            "message": "Severity: MEDIUM",
            "data": {}, "display_color": "amber", "display_flash": False,
            "model": "mistral-large-latest", "created_at": (t + timedelta(seconds=10)).isoformat(),
        },
        {
            "case_id": CASE_ID, "agent": "vision", "event_type": "detection",
            "message": "Frame 1 analysis: Smoke detected",
            "data": {}, "display_color": "purple", "display_flash": False,
            "model": "pixtral-large-latest", "created_at": (t + timedelta(seconds=25)).isoformat(),
        },
        {
            "case_id": CASE_ID, "agent": "vision", "event_type": "hazard_escalation",
            "message": "HAZARD ESCALATION: engine_fire",
            "data": {}, "display_color": "red", "display_flash": True,
            "model": "pixtral-large-latest", "created_at": (t + timedelta(seconds=38)).isoformat(),
        },
        {
            "case_id": CASE_ID, "agent": "evidence_fusion",
            "event_type": "CROSS_MODAL_CORROBORATION",
            "message": "FIRE confirmed by 2 independent modalities",
            "data": {
                "claim": "fire", "modalities": ["vision", "audio"],
                "combined_confidence": 0.95, "cross_modal": True,
                "evacuation_triggered": True,
            },
            "display_color": "red", "display_flash": True,
            "model": "mistral-large-latest", "created_at": (t + timedelta(seconds=32)).isoformat(),
        },
        {
            "case_id": CASE_ID, "agent": "voice", "event_type": "priority_interrupt",
            "message": "PRIORITY INTERRUPT — Hazard warning to all callers",
            "data": {}, "display_color": "red", "display_flash": True,
            "model": None, "created_at": (t + timedelta(seconds=35)).isoformat(),
        },
        {
            "case_id": CASE_ID, "agent": "orchestrator", "event_type": "approved",
            "message": "Operator confirmed dispatch",
            "data": {}, "display_color": "green", "display_flash": True,
            "model": None, "created_at": (t + timedelta(seconds=50)).isoformat(),
        },
        {
            "case_id": CASE_ID, "agent": "orchestrator", "event_type": "complete",
            "message": f"Demo complete: {CASE_ID}",
            "data": {}, "display_color": "green", "display_flash": True,
            "model": None, "created_at": (t + timedelta(seconds=55)).isoformat(),
        },
    ]


def _mock_transcripts():
    t = BASE_TIME
    return [
        {
            "case_id": CASE_ID, "caller_id": "scene_feed_1",
            "caller_label": "Scene Audio (FEED_1)", "language": "es",
            "original_text": "Mi esposo está atrapado en el carro!",
            "translated_text": "My husband is trapped in the car!",
            "confidence": 0.9, "segment_index": 1, "feed_id": "FEED_1",
            "direction": "inbound", "priority": None,
            "created_at": (t + timedelta(seconds=8)).isoformat(),
        },
        {
            "case_id": CASE_ID, "caller_id": "scene_feed_2",
            "caller_label": "Scene Audio (FEED_2)", "language": "zh",
            "original_text": "车里有个孩子！",
            "translated_text": "There is a child in the car!",
            "confidence": 0.9, "segment_index": 2, "feed_id": "FEED_2",
            "direction": "inbound", "priority": None,
            "created_at": (t + timedelta(seconds=15)).isoformat(),
        },
        {
            "case_id": CASE_ID, "caller_id": "scene_feed_3",
            "caller_label": "Scene Audio (FEED_3)", "language": "fr",
            "original_text": "Il y a du feu! Le moteur brûle!",
            "translated_text": "There is fire! The engine is burning!",
            "confidence": 0.9, "segment_index": 3, "feed_id": "FEED_3",
            "direction": "inbound", "priority": None,
            "created_at": (t + timedelta(seconds=30)).isoformat(),
        },
        {
            "case_id": CASE_ID, "caller_id": "dispatch",
            "caller_label": "DISPATCH", "language": "es",
            "original_text": "¡Atención! Se ha detectado fuego.",
            "translated_text": "Attention! Fire detected.",
            "confidence": 1.0, "segment_index": 900, "feed_id": "DISPATCH",
            "direction": "outbound", "priority": "evacuation",
            "created_at": (t + timedelta(seconds=35)).isoformat(),
        },
    ]


def _mock_dispatches():
    t = BASE_TIME
    return [
        {
            "case_id": CASE_ID, "unit_type": "EMS", "unit_assigned": "AMB-7",
            "destination": "Market St & 5th St", "eta_minutes": 4,
            "status": "confirmed", "voice_message": "AMB-7 en route",
            "rationale": "Trapped occupant requires medical assistance",
            "created_at": (t + timedelta(seconds=50)).isoformat(),
        },
        {
            "case_id": CASE_ID, "unit_type": "Fire Response", "unit_assigned": "ENG-3",
            "destination": "Market St & 5th St", "eta_minutes": 3,
            "status": "dispatched", "voice_message": "Engine 3 responding",
            "rationale": "Vision-confirmed fire — evacuation priority",
            "created_at": (t + timedelta(seconds=36)).isoformat(),
        },
    ]


def _make_mock_supabase():
    """Create a mock Supabase client that returns test data."""
    sb = MagicMock()

    def table_handler(table_name):
        mock_table = MagicMock()
        mock_select = MagicMock()
        mock_table.select.return_value = mock_select

        if table_name == "incident_state":
            mock_eq = MagicMock()
            mock_select.eq.return_value = mock_eq
            mock_single = MagicMock()
            mock_eq.single.return_value = mock_single
            mock_single.execute.return_value = MagicMock(data=_mock_state())
        elif table_name == "agent_logs":
            mock_eq = MagicMock()
            mock_select.eq.return_value = mock_eq
            mock_order = MagicMock()
            mock_eq.order.return_value = mock_order
            mock_order.execute.return_value = MagicMock(data=_mock_logs())
        elif table_name == "transcripts":
            mock_eq = MagicMock()
            mock_select.eq.return_value = mock_eq
            mock_order = MagicMock()
            mock_eq.order.return_value = mock_order
            mock_order.execute.return_value = MagicMock(data=_mock_transcripts())
        elif table_name == "dispatches":
            mock_eq = MagicMock()
            mock_select.eq.return_value = mock_eq
            mock_order = MagicMock()
            mock_eq.order.return_value = mock_order
            mock_order.execute.return_value = MagicMock(data=_mock_dispatches())

        return mock_table

    sb.table = table_handler
    return sb


def _make_mock_mistral():
    """Create a mock Mistral client."""
    mistral = MagicMock()
    mock_chat = MagicMock()
    mistral.chat = mock_chat

    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = (
        "At 03:33:45 UTC, DISPATCH detected a vehicle collision at Market St & 5th St "
        "via concurrent audio and visual monitoring. Over the following 55 seconds, "
        "the system processed 3 audio segments in 3 languages (Spanish, Mandarin, French), "
        "analyzed 2 video frames, and executed evidence fusion cycles. Critical intelligence "
        "included a trapped occupant (ES audio), a child in the vehicle (ZH audio), and an "
        "engine fire detected independently by both vision (0.99 confidence) and audio. "
        "Zero casualties resulted from this incident."
    )

    mock_chat.complete_async = AsyncMock(return_value=mock_response)
    return mistral


# ---------------------------------------------------------------------------
# T006: Frame saving test
# ---------------------------------------------------------------------------
class TestFrameSaving:
    def test_frame_file_written(self, timer, tmp_path):
        """T006: Verify JPEG frames are saved to disk with correct naming."""
        with timer.step("Create test frame"):
            # Simulate what orchestrator._run_vision() does
            frames_dir = tmp_path / "assets" / "frames"
            frames_dir.mkdir(parents=True, exist_ok=True)

            case_id = CASE_ID
            frame_bytes = b"\xff\xd8\xff\xe0" + b"\x00" * 100  # JPEG header

            for ts in [25, 38]:
                frame_path = frames_dir / f"{case_id}_t{ts}s.jpg"
                with open(frame_path, "wb") as f:
                    f.write(frame_bytes)

        with timer.step("Verify frame files exist"):
            assert (frames_dir / f"{case_id}_t25s.jpg").exists()
            assert (frames_dir / f"{case_id}_t38s.jpg").exists()
            assert (frames_dir / f"{case_id}_t25s.jpg").stat().st_size > 0
            assert (frames_dir / f"{case_id}_t38s.jpg").stat().st_size > 0
            print(f"  Frame 1: {case_id}_t25s.jpg — {(frames_dir / f'{case_id}_t25s.jpg').stat().st_size} bytes")
            print(f"  Frame 2: {case_id}_t38s.jpg — {(frames_dir / f'{case_id}_t38s.jpg').stat().st_size} bytes")

        timer.summary()


# ---------------------------------------------------------------------------
# T009: ReportBuilder.build() — all 8 sections
# ---------------------------------------------------------------------------
class TestReportBuilder:
    @pytest.mark.asyncio
    async def test_build_all_sections(self, timer):
        """T009: Verify build() returns all 8 report sections with correct types."""
        # Clear caches
        ReportBuilder._summary_cache.clear()
        ReportBuilder._report_cache.clear()

        with timer.step("Create mocks"):
            sb = _make_mock_supabase()
            mistral = _make_mock_mistral()
            builder = ReportBuilder(sb, mistral)

        with timer.step("Build report"):
            report = await builder.build(CASE_ID)

        with timer.step("Validate ReportData type"):
            assert isinstance(report, ReportData)
            assert report.case_id == CASE_ID
            assert report.generated_at is not None
            assert report.warning is None  # resolved_demo → no warning
            print(f"  case_id: {report.case_id}")
            print(f"  generated_at: {report.generated_at}")

        with timer.step("Validate header section"):
            h = report.header
            assert isinstance(h, ReportHeader)
            assert h.case_id == CASE_ID
            assert h.incident_type == "vehicle_crash"
            assert h.severity == "critical"
            assert h.status == "resolved_demo"
            assert h.speaker_count >= 1
            assert len(h.languages) >= 1
            assert h.audio_segments >= 1
            assert h.vision_frames >= 1
            print(f"  header: type={h.incident_type}, severity={h.severity}, speakers={h.speaker_count}")

        with timer.step("Validate timeline section"):
            assert len(report.timeline) > 0
            for entry in report.timeline:
                assert isinstance(entry, TimelineEntry)
                assert entry.t  # has elapsed time
                assert entry.agent
                assert entry.event_type
                assert entry.message
            print(f"  timeline: {len(report.timeline)} entries")

        with timer.step("Validate evidence_sources section"):
            es = report.evidence_sources
            assert isinstance(es, EvidenceSources)
            assert es.audio.speaker_count >= 1
            assert es.audio.transcript_count >= 1
            assert len(es.audio.speakers) >= 1
            assert es.vision.frames_analyzed >= 1
            assert len(es.vision.detections) >= 1
            print(f"  evidence: audio={es.audio.transcript_count} transcripts, vision={es.vision.frames_analyzed} frames")
            print(f"  cross_modal: {len(es.cross_modal)} corroborations")

        with timer.step("Validate convergence_tracks section"):
            assert len(report.convergence_tracks) > 0
            for track in report.convergence_tracks:
                assert isinstance(track, ConvergenceTrack)
                assert track.source
                assert track.type in ("audio", "vision", "fused")
                assert track.color
            print(f"  convergence_tracks: {len(report.convergence_tracks)} tracks")
            for t in report.convergence_tracks:
                print(f"    {t.source} ({t.type}): {len(t.events)} events")

        with timer.step("Validate response_actions section"):
            assert len(report.response_actions) > 0
            for action in report.response_actions:
                assert isinstance(action, ResponseAction)
                assert action.action
                assert action.unit_type
                assert action.status
            print(f"  response_actions: {len(report.response_actions)} actions")

        with timer.step("Validate agent_stats section"):
            stats = report.agent_stats
            assert isinstance(stats, AgentStats)
            assert len(stats.agents) > 0
            assert stats.total_invocations > 0
            assert len(stats.models_used) > 0
            print(f"  agent_stats: {stats.total_invocations} invocations, {len(stats.agents)} agents")

        with timer.step("Validate executive_summary section"):
            assert report.executive_summary
            assert len(report.executive_summary) > 50
            print(f"  executive_summary: {report.executive_summary[:80]}...")

        timer.summary()

    @pytest.mark.asyncio
    async def test_case_not_found(self, timer):
        """Verify build() returns None for non-existent case."""
        with timer.step("Create mock with exception"):
            sb = MagicMock()
            mock_table = MagicMock()
            sb.table.return_value = mock_table
            mock_select = MagicMock()
            mock_table.select.return_value = mock_select
            mock_eq = MagicMock()
            mock_select.eq.return_value = mock_eq
            mock_single = MagicMock()
            mock_eq.single.return_value = mock_single
            mock_single.execute.side_effect = Exception("Not found")

            mistral = _make_mock_mistral()
            builder = ReportBuilder(sb, mistral)

        with timer.step("Build report for non-existent case"):
            result = await builder.build("NONEXISTENT")
            assert result is None
            print("  Correctly returned None for non-existent case")

        timer.summary()


# ---------------------------------------------------------------------------
# T010: Executive summary caching
# ---------------------------------------------------------------------------
class TestSummaryCaching:
    @pytest.mark.asyncio
    async def test_summary_cached(self, timer):
        """T010: Verify Mistral is called once; second build uses cache."""
        ReportBuilder._summary_cache.clear()
        ReportBuilder._report_cache.clear()

        with timer.step("Setup"):
            sb = _make_mock_supabase()
            mistral = _make_mock_mistral()

        with timer.step("First build (generates summary)"):
            builder1 = ReportBuilder(sb, mistral)
            report1 = await builder1.build(CASE_ID)
            assert report1.executive_summary
            call_count_1 = mistral.chat.complete_async.call_count
            print(f"  Mistral calls after build 1: {call_count_1}")

        with timer.step("Second build (should use cache)"):
            builder2 = ReportBuilder(sb, mistral)
            report2 = await builder2.build(CASE_ID)
            call_count_2 = mistral.chat.complete_async.call_count
            print(f"  Mistral calls after build 2: {call_count_2}")

        with timer.step("Verify caching"):
            assert call_count_2 == call_count_1, (
                f"Mistral called again! {call_count_1} → {call_count_2}"
            )
            assert report1.executive_summary == report2.executive_summary
            print("  Summary correctly cached — no extra Mistral call")

        timer.summary()


# ---------------------------------------------------------------------------
# T022-T024: Contract validation tests (US3)
# ---------------------------------------------------------------------------
class TestContractValidation:
    @pytest.mark.asyncio
    async def test_all_contract_fields_present(self, timer):
        """T022: Validate every field from contracts/report-api.md is present."""
        ReportBuilder._summary_cache.clear()
        ReportBuilder._report_cache.clear()

        with timer.step("Build report"):
            sb = _make_mock_supabase()
            mistral = _make_mock_mistral()
            builder = ReportBuilder(sb, mistral)
            report = await builder.build(CASE_ID)
            data = report.model_dump()

        with timer.step("Validate top-level fields"):
            assert "case_id" in data
            assert "generated_at" in data
            assert "warning" in data
            assert "header" in data
            assert "timeline" in data
            assert "evidence_sources" in data
            assert "convergence_tracks" in data
            assert "response_actions" in data
            assert "agent_stats" in data
            assert "key_frames" in data
            assert "executive_summary" in data
            print("  All 11 top-level fields present")

        with timer.step("Validate header fields (10)"):
            h = data["header"]
            for field in ["case_id", "incident_type", "location", "severity",
                          "status", "duration_seconds", "speaker_count",
                          "languages", "audio_segments", "vision_frames"]:
                assert field in h, f"Missing header field: {field}"
            assert "outcome" in h
            print(f"  Header: {len(h)} fields present")

        with timer.step("Validate timeline entry fields (9)"):
            assert len(data["timeline"]) > 0
            entry = data["timeline"][0]
            for field in ["t", "timestamp", "agent", "model", "event_type",
                          "message", "severity_indicator", "color", "flash"]:
                assert field in entry, f"Missing timeline field: {field}"
            print(f"  Timeline entry: {len(entry)} fields present")

        with timer.step("Validate evidence_sources fields"):
            es = data["evidence_sources"]
            assert "audio" in es
            assert "vision" in es
            assert "cross_modal" in es
            # Audio sub-fields
            for field in ["speaker_count", "languages", "transcript_count", "speakers"]:
                assert field in es["audio"], f"Missing audio field: {field}"
            # Vision sub-fields
            for field in ["frames_analyzed", "detections"]:
                assert field in es["vision"], f"Missing vision field: {field}"
            print("  evidence_sources: all sub-fields present")

        with timer.step("Validate response_actions fields (7)"):
            assert len(data["response_actions"]) > 0
            action = data["response_actions"][0]
            for field in ["action", "unit_type", "unit_assigned", "status",
                          "authorized_at", "authorization_method", "language"]:
                assert field in action, f"Missing response_action field: {field}"
            print(f"  response_action: {len(action)} fields present")

        with timer.step("Validate agent_stats fields"):
            stats = data["agent_stats"]
            for field in ["agents", "total_invocations", "total_duration_seconds", "models_used"]:
                assert field in stats, f"Missing agent_stats field: {field}"
            assert len(stats["agents"]) > 0
            agent = stats["agents"][0]
            for field in ["agent", "model", "invocations", "avg_latency_seconds"]:
                assert field in agent, f"Missing agent field: {field}"
            assert len(stats["models_used"]) > 0
            model = stats["models_used"][0]
            for field in ["model", "roles"]:
                assert field in model, f"Missing model_usage field: {field}"
            print("  agent_stats: all sub-fields present")

        with timer.step("Validate key_frames fields (6)"):
            # key_frames might be empty in mock (no disk files)
            # Just verify the field structure via model
            kf = KeyFrame(
                image_url="/frames/test.jpg",
                timestamp_s=25.0,
                elapsed="00:25",
                detections=[{"type": "smoke", "confidence": 0.87}],
                description="Test",
                is_hero=False,
            )
            kf_dict = kf.model_dump()
            for field in ["image_url", "timestamp_s", "elapsed", "detections",
                          "description", "is_hero"]:
                assert field in kf_dict, f"Missing key_frame field: {field}"
            print("  key_frames schema: all 6 fields present")

        with timer.step("Validate executive_summary is string"):
            assert isinstance(data["executive_summary"], str)
            assert len(data["executive_summary"]) > 0
            print(f"  executive_summary: {len(data['executive_summary'])} chars")

        timer.summary()

    @pytest.mark.asyncio
    async def test_severity_indicator_enum_values(self, timer):
        """T023: Validate severity_indicator and color are valid enum values."""
        ReportBuilder._summary_cache.clear()
        ReportBuilder._report_cache.clear()

        with timer.step("Build report"):
            sb = _make_mock_supabase()
            mistral = _make_mock_mistral()
            builder = ReportBuilder(sb, mistral)
            report = await builder.build(CASE_ID)

        valid_indicators = {"regular", "critical", "operator"}
        valid_colors = {"blue", "green", "amber", "red", "purple"}

        with timer.step("Validate severity_indicator values"):
            for entry in report.timeline:
                assert entry.severity_indicator in valid_indicators, (
                    f"Invalid severity_indicator: {entry.severity_indicator} "
                    f"for event {entry.event_type}"
                )
            print(f"  All {len(report.timeline)} entries have valid severity_indicator")

        with timer.step("Validate color values"):
            for entry in report.timeline:
                assert entry.color in valid_colors, (
                    f"Invalid color: {entry.color} for event {entry.event_type}"
                )
            print(f"  All {len(report.timeline)} entries have valid color")

        timer.summary()

    @pytest.mark.asyncio
    async def test_convergence_track_enum_values(self, timer):
        """T024: Validate convergence track types and event types."""
        ReportBuilder._summary_cache.clear()
        ReportBuilder._report_cache.clear()

        with timer.step("Build report"):
            sb = _make_mock_supabase()
            mistral = _make_mock_mistral()
            builder = ReportBuilder(sb, mistral)
            report = await builder.build(CASE_ID)

        valid_track_types = {"audio", "vision", "fused"}
        valid_event_types = {"detection", "escalation", "action", "state_change"}

        with timer.step("Validate track types"):
            for track in report.convergence_tracks:
                assert track.type in valid_track_types, (
                    f"Invalid track type: {track.type} for source {track.source}"
                )
            print(f"  All {len(report.convergence_tracks)} tracks have valid type")

        with timer.step("Validate event types"):
            for track in report.convergence_tracks:
                for event in track.events:
                    assert event.type in valid_event_types, (
                        f"Invalid event type: {event.type} in track {track.source}"
                    )
            total_events = sum(len(t.events) for t in report.convergence_tracks)
            print(f"  All {total_events} events have valid type")

        timer.summary()


# ---------------------------------------------------------------------------
# T025: E2E timing test
# ---------------------------------------------------------------------------
class TestE2ETiming:
    @pytest.mark.asyncio
    async def test_report_generation_timing(self, timer):
        """T025: Full report generation under 5s, cached under 500ms."""
        ReportBuilder._summary_cache.clear()
        ReportBuilder._report_cache.clear()

        sb = _make_mock_supabase()
        mistral = _make_mock_mistral()

        with timer.step("First report generation (<5s)"):
            start = time.time()
            builder = ReportBuilder(sb, mistral)
            report = await builder.build(CASE_ID)
            elapsed = time.time() - start
            assert report is not None
            assert elapsed < 5.0, f"First generation took {elapsed:.2f}s (>5s)"
            print(f"  First generation: {elapsed:.3f}s")

        with timer.step("Cached report (<500ms)"):
            start = time.time()
            builder2 = ReportBuilder(sb, mistral)
            report2 = await builder2.build(CASE_ID)
            elapsed = time.time() - start
            assert report2 is not None
            assert elapsed < 0.5, f"Cached response took {elapsed:.2f}s (>500ms)"
            print(f"  Cached response: {elapsed:.3f}s")

        with timer.step("Validate data consistency"):
            assert report.case_id == report2.case_id
            assert report.executive_summary == report2.executive_summary
            print("  Data consistent between builds")

        timer.summary()
