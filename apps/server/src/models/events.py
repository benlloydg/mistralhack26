from __future__ import annotations
from pydantic import BaseModel, Field
from datetime import datetime

class AgentLogEntry(BaseModel):
    case_id: str
    agent: str
    event_type: str
    message: str
    data: dict = Field(default_factory=dict)
    display_color: str = "blue"
    display_flash: bool = False
    model: str | None = None
