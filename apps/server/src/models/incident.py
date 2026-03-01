from __future__ import annotations
from pydantic import BaseModel, Field
from enum import Enum
from datetime import datetime

class Severity(str, Enum):
    UNKNOWN = "unknown"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class IncidentStatus(str, Enum):
    INTAKE = "intake"
    ACTIVE = "active"
    ESCALATED = "escalated"
    CRITICAL = "critical"
    RESOLVED_DEMO = "resolved_demo"

class TimelineEvent(BaseModel):
    t: str = Field(description="Elapsed time, e.g. '00:15'")
    agent: str = Field(description="Agent that produced this event")
    event: str = Field(description="Human-readable event description")

class ActionItem(BaseModel):
    status: str = Field(description="completed | pending | recommended")
    action: str = Field(description="Human-readable action description")

class IncidentState(BaseModel):
    """The single source of truth. Maps 1:1 to the incident_state Supabase table."""
    case_id: str
    status: IncidentStatus = IncidentStatus.INTAKE
    incident_type: str | None = None
    location_raw: str | None = None
    location_normalized: str | None = None
    severity: Severity = Severity.UNKNOWN
    caller_count: int = 0
    people_count_estimate: int = 0
    injury_flags: list[str] = Field(default_factory=list)
    hazard_flags: list[str] = Field(default_factory=list)
    vision_detections: list[dict] = Field(default_factory=list)
    recommended_units: list[str] = Field(default_factory=list)
    confirmed_units: list[str] = Field(default_factory=list)
    timeline: list[TimelineEvent] = Field(default_factory=list)
    action_plan_version: int = 0
    action_plan: list[ActionItem] = Field(default_factory=list)
    match_confidence: float | None = None
    operator_summary: str | None = None
    confidence_scores: dict = Field(default_factory=dict)
