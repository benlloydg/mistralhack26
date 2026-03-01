from __future__ import annotations
from pydantic import BaseModel, Field

class VisionDetection(BaseModel):
    type: str = Field(description="vehicle_collision | smoke | engine_fire | persons_visible | etc")
    confidence: float
    bbox: list[int] | None = Field(None, description="[x1, y1, x2, y2] if applicable")
    count: int | None = Field(None, description="Person count if type is persons_visible")

class FrameAnalysis(BaseModel):
    """Structured output from Pixtral vision analysis."""
    frame_id: int
    detections: list[VisionDetection]
    overall_description: str = Field(description="One-line scene summary")
    hazard_escalation: str | None = Field(None, description="New hazard type if detected")
    smoke_visible: bool = False
    fire_visible: bool = False
    vehicle_damage_severity: str | None = None  # none | minor | moderate | severe

class SceneDelta(BaseModel):
    """Computed difference between consecutive frame analyses."""
    new_hazard: str | None = None
    hazard_escalation: bool = False
    confidence_change: float = 0.0
    description: str = ""
