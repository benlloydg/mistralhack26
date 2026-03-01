from __future__ import annotations
from pydantic import BaseModel, Field
from .incident import Severity, ActionItem

class TriageResult(BaseModel):
    """Structured output from the triage agent. Mistral Large returns this."""
    severity: Severity
    incident_type: str
    reasoning: str = Field(description="1-2 sentence explanation of severity assessment")
    recommended_units: list[str] = Field(description="Units to dispatch: EMS, Fire Response, Pediatric EMS, Traffic Control, Police")
    hazards: list[str] = Field(default_factory=list)
    people_count_estimate: int = 0
    injury_flags: list[str] = Field(default_factory=list)
    dispatch_triggers: list[str] = Field(default_factory=list, description="Specific triggers: pediatric_trauma, hazmat, etc")
    action_plan: list[ActionItem] = Field(default_factory=list)

class Corroboration(BaseModel):
    """When multiple sources confirm the same fact."""
    claim: str
    sources: list[dict] = Field(description="[{type: 'vision'|'caller_N', confidence: float}]")
    status: str = "corroborated"  # corroborated | conflicting | unconfirmed
    combined_confidence: float

class EvidenceFusionResult(BaseModel):
    """Output of fusing caller reports + vision detections."""
    corroborations: list[Corroboration] = Field(default_factory=list)
    severity_delta: str | None = Field(None, description="e.g. 'HIGH -> CRITICAL'")
    new_severity: Severity | None = None
    evacuation_warning_required: bool = False
    reasoning: str = ""
