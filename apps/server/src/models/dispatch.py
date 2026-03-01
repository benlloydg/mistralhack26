from __future__ import annotations
from pydantic import BaseModel, Field

class DispatchBrief(BaseModel):
    """Structured output from the dispatch agent. Mistral generates the voice message."""
    unit_type: str
    unit_assigned: str = Field(description="Unit callsign e.g. AMB-7, ENG-4")
    destination: str
    eta_minutes: int
    voice_message: str = Field(description="Full dispatch message to be spoken via TTS")
    rationale: str = Field(description="Why this unit is being dispatched")
