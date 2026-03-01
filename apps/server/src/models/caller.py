from __future__ import annotations
from pydantic import BaseModel, Field

class TranscriptSegment(BaseModel):
    caller_id: str
    caller_label: str | None = None
    language: str
    original_text: str
    translated_text: str | None = None
    entities: list[str] = Field(default_factory=list)
    confidence: float | None = None
    segment_index: int

class IntakeFacts(BaseModel):
    """Structured output from the intake agent. Mistral extracts these from a transcript."""
    location_raw: str | None = Field(None, description="Raw location mentioned by caller")
    incident_type_candidate: str | None = Field(None, description="vehicle_crash | fire | medical | etc")
    possible_trapped_person: bool = Field(False, description="Is someone reported trapped?")
    child_present: bool = Field(False, description="Is a child mentioned?")
    additional_victim: bool = Field(False, description="Does this add new victim info?")
    injury_description: str | None = Field(None, description="Description of injuries mentioned")
    hazard_description: str | None = Field(None, description="Smoke, fire, leaking fuel, etc")
    urgency_keywords: list[str] = Field(default_factory=list, description="Urgent words: 'trapped', 'bleeding', 'fire'")

class CallerRecord(BaseModel):
    caller_id: str
    label: str
    language: str
    audio_path: str
    start_delay_s: float
    status: str = "queued"  # queued | active | completed
