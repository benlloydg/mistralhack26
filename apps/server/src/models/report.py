"""
Pydantic models for the After-Action Report JSON response.

Maps 1:1 to the API contract in specs/004-after-action-report/contracts/report-api.md.
All 8 report sections are represented as typed models.
"""
from __future__ import annotations

from pydantic import BaseModel, Field


class ReportHeader(BaseModel):
    case_id: str
    incident_type: str | None = None
    location: str | None = None
    severity: str = "unknown"
    status: str = "intake"
    duration_seconds: float = 0.0
    speaker_count: int = 0
    languages: list[str] = Field(default_factory=list)
    audio_segments: int = 0
    vision_frames: int = 0
    outcome: str = ""


class TimelineEntry(BaseModel):
    t: str
    timestamp: str | None = None
    agent: str
    model: str | None = None
    event_type: str
    message: str
    severity_indicator: str = "regular"
    color: str = "blue"
    flash: bool = False


class SpeakerSummary(BaseModel):
    feed_id: str
    language: str
    label: str | None = None
    key_intelligence: str = ""
    segment_count: int = 0


class AudioSummary(BaseModel):
    speaker_count: int = 0
    languages: list[str] = Field(default_factory=list)
    transcript_count: int = 0
    speakers: list[SpeakerSummary] = Field(default_factory=list)


class VisionDetectionEntry(BaseModel):
    timestamp_s: float
    type: str
    confidence: float
    description: str = ""


class VisionSummary(BaseModel):
    frames_analyzed: int = 0
    detections: list[VisionDetectionEntry] = Field(default_factory=list)


class CrossModalSummary(BaseModel):
    claim: str
    modalities: list[str] = Field(default_factory=list)
    details: str = ""


class EvidenceSources(BaseModel):
    audio: AudioSummary = Field(default_factory=AudioSummary)
    vision: VisionSummary = Field(default_factory=VisionSummary)
    cross_modal: list[CrossModalSummary] = Field(default_factory=list)


class TrackEvent(BaseModel):
    t_seconds: float
    label: str
    type: str


class ConvergenceTrack(BaseModel):
    source: str
    type: str
    color: str
    events: list[TrackEvent] = Field(default_factory=list)


class ResponseAction(BaseModel):
    action: str
    unit_type: str
    unit_assigned: str | None = None
    status: str = "recommended"
    authorized_at: str | None = None
    authorization_method: str = "operator"
    language: str | None = None


class AgentUtilization(BaseModel):
    agent: str
    model: str
    invocations: int = 0
    avg_latency_seconds: float = 0.0


class ModelUsage(BaseModel):
    model: str
    roles: list[str] = Field(default_factory=list)


class AgentStats(BaseModel):
    agents: list[AgentUtilization] = Field(default_factory=list)
    total_invocations: int = 0
    total_duration_seconds: float = 0.0
    models_used: list[ModelUsage] = Field(default_factory=list)


class KeyFrame(BaseModel):
    image_url: str
    timestamp_s: float
    elapsed: str
    detections: list[dict] = Field(default_factory=list)
    description: str = ""
    is_hero: bool = False


class ReportData(BaseModel):
    case_id: str
    generated_at: str
    warning: str | None = None
    header: ReportHeader
    timeline: list[TimelineEntry] = Field(default_factory=list)
    evidence_sources: EvidenceSources = Field(default_factory=EvidenceSources)
    convergence_tracks: list[ConvergenceTrack] = Field(default_factory=list)
    response_actions: list[ResponseAction] = Field(default_factory=list)
    agent_stats: AgentStats = Field(default_factory=AgentStats)
    key_frames: list[KeyFrame] = Field(default_factory=list)
    executive_summary: str = ""
