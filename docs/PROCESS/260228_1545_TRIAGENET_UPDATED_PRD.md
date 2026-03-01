# TriageNet — Technical Implementation PRD

> **This document is the single source of truth for building TriageNet.**
> Hand this to Claude Code. Every file path, every model, every migration, every test is here.
> Build in the exact phase order specified. Do not skip phases. Test before advancing.

---

## 1. Project Overview

**TriageNet** is a multi-caller, multilingual emergency dispatch system for the Mistral × ElevenLabs hackathon. It processes 3 concurrent callers in different languages (Spanish, Mandarin, French), uses Mistral vision models for CCTV analysis, Mistral Large for triage reasoning, and ElevenLabs for voice agents and transcription.

The demo is 120 seconds, fully choreographed with pre-seeded audio and video. The backend drives timed events. The frontend renders state changes in real time via Supabase Realtime.

**Core principle:** Everything is scripted but live-rendered. Agents do real inference. State evolves visibly. One human approval moment.

---

## 2. Tech Stack

| Layer | Technology |
|-------|-----------|
| Monorepo | Root with `/docs`, `/apps/web`, `/apps/server` |
| Frontend | Next.js 14+ App Router, TypeScript, Tailwind CSS, Supabase Realtime |
| Backend | Python 3.12, FastAPI, uv (package manager), pydantic-ai agents |
| AI Models | Mistral Large (triage), Mistral Small (vision), ElevenLabs (voice/transcribe) |
| Database | Supabase (Postgres + Realtime) |
| Env | python-dotenv, `.env` files |
| IPC | Agents write to Supabase → Frontend reads via Realtime subscriptions |

**Why Pydantic-AI over native Mistral Agents SDK:**
Pydantic-AI gives us typed `deps` (dependency injection), `output_type` with auto-retry on validation failure, auto-generated tool schemas from type hints, and `RunContext` for threading state. Mistral's native SDK has none of this. We use the native `mistralai` client only for Pixtral vision calls (multimodal content arrays) since Pydantic-AI doesn't support that format natively.

---

## 3. Repository Structure

```
triagenet/
├── docs/
│   ├── PRD.md                          # This file
│   ├── DEMO_SCRIPT.md                  # 120-second timing reference
│   └── API_GUIDE.md                    # Endpoint documentation
│
├── apps/
│   ├── web/                            # Next.js frontend
│   │   ├── package.json
│   │   ├── tsconfig.json
│   │   ├── tailwind.config.ts
│   │   ├── next.config.ts
│   │   ├── .env.local                  # NEXT_PUBLIC_SUPABASE_URL, NEXT_PUBLIC_SUPABASE_ANON_KEY
│   │   ├── src/
│   │   │   ├── app/
│   │   │   │   ├── layout.tsx          # Root layout, theme provider, fonts
│   │   │   │   ├── page.tsx            # Main dashboard page
│   │   │   │   └── globals.css         # Tailwind + CSS variables (dark/light)
│   │   │   ├── components/
│   │   │   │   ├── Dashboard.tsx        # Master layout — 4-panel grid
│   │   │   │   ├── CCTVPanel.tsx        # Video + vision overlay
│   │   │   │   ├── CaseFilePanel.tsx    # Evolving case document
│   │   │   │   ├── AgentTerminal.tsx    # Real-time agent activity log
│   │   │   │   ├── TranscriptPanel.tsx  # Caller tabs + dual-language text
│   │   │   │   ├── ResponseLanes.tsx    # Dispatch unit status cards
│   │   │   │   ├── ActionButton.tsx     # "START DEMO" / "APPROVE" button
│   │   │   │   ├── SeverityBadge.tsx    # Animated severity indicator
│   │   │   │   └── ThemeToggle.tsx      # Dark/light mode switch
│   │   │   ├── hooks/
│   │   │   │   ├── useIncidentState.ts  # Supabase realtime subscription to incident_state
│   │   │   │   ├── useAgentLogs.ts      # Supabase realtime subscription to agent_logs
│   │   │   │   ├── useTranscripts.ts    # Supabase realtime subscription to transcripts
│   │   │   │   └── useDispatches.ts     # Supabase realtime subscription to dispatches
│   │   │   ├── lib/
│   │   │   │   ├── supabase.ts          # Supabase client init
│   │   │   │   └── types.ts             # Shared TypeScript types (mirrors Pydantic models)
│   │   │   └── styles/
│   │   │       └── theme.ts             # CSS variable definitions for dark/light
│   │
│   ├── server/                          # Python FastAPI backend
│   │   ├── pyproject.toml               # uv project config
│   │   ├── uv.lock
│   │   ├── .env                         # MISTRAL_API_KEY, ELEVENLABS_API_KEY, SUPABASE_URL, SUPABASE_SERVICE_KEY
│   │   ├── .python-version              # 3.12
│   │   ├── src/
│   │   │   ├── main.py                  # FastAPI app, CORS, routes
│   │   │   ├── config.py                # Settings from .env via pydantic-settings
│   │   │   ├── deps.py                  # Shared dependencies (Supabase client, Mistral client, etc.)
│   │   │   │
│   │   │   ├── models/                  # Pydantic models (shared state schemas)
│   │   │   │   ├── __init__.py
│   │   │   │   ├── incident.py          # IncidentState, Severity, IncidentType
│   │   │   │   ├── caller.py            # CallerRecord, TranscriptSegment, IntakeFacts
│   │   │   │   ├── vision.py            # VisionDetection, SceneDelta, FrameAnalysis
│   │   │   │   ├── triage.py            # TriageResult, ActionPlan, ActionItem, Corroboration
│   │   │   │   ├── dispatch.py          # DispatchRecord, DispatchBrief, UnitType
│   │   │   │   └── events.py            # AgentLogEntry, TimelineEvent
│   │   │   │
│   │   │   ├── agents/                  # Pydantic-AI agent definitions
│   │   │   │   ├── __init__.py
│   │   │   │   ├── shared_deps.py       # TriageNetDeps dataclass (supabase, mistral_client, session_id, etc.)
│   │   │   │   ├── triage_agent.py      # Triage reasoning agent (Mistral Large)
│   │   │   │   ├── intake_agent.py      # Caller intake + entity extraction agent
│   │   │   │   ├── vision_agent.py      # Vision analysis (native mistralai client for Pixtral)
│   │   │   │   ├── voice_agent.py       # ElevenLabs TTS generation agent
│   │   │   │   ├── dispatch_agent.py    # Dispatch brief generation agent
│   │   │   │   └── case_match_agent.py  # Case correlation / evidence fusion agent
│   │   │   │
│   │   │   ├── services/                # Business logic (non-agent)
│   │   │   │   ├── __init__.py
│   │   │   │   ├── orchestrator.py      # DemoOrchestrator — drives timed demo events
│   │   │   │   ├── media.py             # Audio/video file management
│   │   │   │   ├── transcription.py     # ElevenLabs transcription client
│   │   │   │   ├── tts.py              # ElevenLabs TTS client
│   │   │   │   ├── state.py             # Read/write IncidentState to Supabase
│   │   │   │   └── logger.py            # Write agent_logs to Supabase
│   │   │   │
│   │   │   ├── routes/                  # FastAPI route modules
│   │   │   │   ├── __init__.py
│   │   │   │   ├── demo.py              # POST /demo/start, POST /demo/approve, GET /demo/status
│   │   │   │   ├── health.py            # GET /health
│   │   │   │   └── session.py           # GET /session/{id}, DELETE /session/{id}
│   │   │   │
│   │   │   └── tests/                   # Test files (run at each phase)
│   │   │       ├── __init__.py
│   │   │       ├── test_phase1_models.py
│   │   │       ├── test_phase2_supabase.py
│   │   │       ├── test_phase3_mistral.py
│   │   │       ├── test_phase4_elevenlabs.py
│   │   │       ├── test_phase5_agents.py
│   │   │       ├── test_phase6_orchestrator.py
│   │   │       └── test_phase7_e2e.py
│   │   │
│   │   └── assets/                      # Pre-seeded demo media
│   │       ├── caller_1_spanish.mp3
│   │       ├── caller_2_mandarin.mp3
│   │       ├── caller_3_french.mp3
│   │       └── crash_video.mp4
│
├── supabase/
│   └── migrations/
│       ├── 001_incident_state.sql
│       ├── 002_agent_logs.sql
│       ├── 003_transcripts.sql
│       ├── 004_dispatches.sql
│       └── 005_enable_realtime.sql
│
└── README.md
```

---

## 4. Environment Variables

### `/apps/server/.env`

```env
# Mistral
MISTRAL_API_KEY=your_mistral_api_key

# ElevenLabs
ELEVENLABS_API_KEY=your_elevenlabs_api_key

# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your_service_role_key

# App
APP_ENV=development
LOG_LEVEL=DEBUG
DEMO_SCENARIO=market_st_crash
```

### `/apps/web/.env.local`

```env
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_anon_key
```

---

## 5. Supabase Schema (Migrations)

### `001_incident_state.sql`

```sql
-- The single source of truth. Agents write here. Frontend reads via Realtime.
CREATE TABLE incident_state (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  case_id TEXT UNIQUE NOT NULL,               -- e.g. "TN-2026-00417"
  status TEXT NOT NULL DEFAULT 'intake',       -- intake | active | escalated | critical | resolved_demo
  incident_type TEXT,                          -- vehicle_collision | fire | etc
  location_raw TEXT,
  location_normalized TEXT,
  severity TEXT NOT NULL DEFAULT 'unknown',    -- unknown | low | medium | high | critical
  caller_count INT NOT NULL DEFAULT 0,
  people_count_estimate INT DEFAULT 0,
  injury_flags JSONB DEFAULT '[]'::jsonb,      -- ["trapped_person", "child_present"]
  hazard_flags JSONB DEFAULT '[]'::jsonb,      -- ["engine_fire", "smoke"]
  vision_detections JSONB DEFAULT '[]'::jsonb,  -- [{type, confidence, frame_id}]
  recommended_units JSONB DEFAULT '[]'::jsonb,  -- ["EMS", "Fire Response"]
  confirmed_units JSONB DEFAULT '[]'::jsonb,    -- ["EMS", "Traffic Control"]
  timeline JSONB DEFAULT '[]'::jsonb,           -- [{t, agent, event}]
  action_plan_version INT DEFAULT 0,
  action_plan JSONB DEFAULT '[]'::jsonb,        -- [{status, action}]
  match_confidence FLOAT,
  operator_summary TEXT,
  confidence_scores JSONB DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

-- Auto-update updated_at
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_updated_at
  BEFORE UPDATE ON incident_state
  FOR EACH ROW EXECUTE FUNCTION update_updated_at();
```

### `002_agent_logs.sql`

```sql
-- Every agent action gets logged here. Frontend renders as the "Agent Terminal" panel.
CREATE TABLE agent_logs (
  id BIGSERIAL PRIMARY KEY,
  case_id TEXT NOT NULL REFERENCES incident_state(case_id),
  agent TEXT NOT NULL,             -- triage | vision | voice | dispatch | intake | orchestrator
  event_type TEXT NOT NULL,        -- transcript_received | severity_changed | detection | dispatch | etc
  message TEXT NOT NULL,           -- Human-readable log line
  data JSONB DEFAULT '{}'::jsonb,  -- Structured event data
  display_color TEXT DEFAULT 'blue', -- UI color hint: blue | red | amber | green | purple
  display_flash BOOLEAN DEFAULT false, -- If true, UI should flash/pulse this entry
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_agent_logs_case ON agent_logs(case_id);
CREATE INDEX idx_agent_logs_created ON agent_logs(created_at);
```

### `003_transcripts.sql`

```sql
-- Per-caller transcript segments. Frontend renders as the "Transcript Panel" with tabs.
CREATE TABLE transcripts (
  id BIGSERIAL PRIMARY KEY,
  case_id TEXT NOT NULL REFERENCES incident_state(case_id),
  caller_id TEXT NOT NULL,         -- caller_1, caller_2, caller_3
  caller_label TEXT,               -- "The Wife", "Bystander", "Shopkeeper"
  language TEXT NOT NULL,           -- es, zh, fr
  original_text TEXT NOT NULL,      -- Original language transcript
  translated_text TEXT,             -- English translation
  entities JSONB DEFAULT '[]'::jsonb, -- Extracted entities
  confidence FLOAT,
  segment_index INT NOT NULL,
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_transcripts_case ON transcripts(case_id);
CREATE INDEX idx_transcripts_caller ON transcripts(case_id, caller_id);
```

### `004_dispatches.sql`

```sql
-- Dispatch records. One row per dispatched unit.
CREATE TABLE dispatches (
  id BIGSERIAL PRIMARY KEY,
  case_id TEXT NOT NULL REFERENCES incident_state(case_id),
  unit_type TEXT NOT NULL,         -- EMS | Fire Response | Pediatric EMS | Traffic Control
  unit_assigned TEXT,              -- AMB-7, ENG-4, PED-2, etc
  destination TEXT,                -- Mass General ER, UCSF Children's, etc
  eta_minutes INT,
  status TEXT NOT NULL DEFAULT 'recommended', -- recommended | confirmed | dispatched
  voice_message TEXT,              -- Generated dispatch brief
  language TEXT DEFAULT 'en',
  rationale TEXT,                  -- Why this unit was dispatched
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_dispatches_case ON dispatches(case_id);
```

### `005_enable_realtime.sql`

```sql
-- Enable Supabase Realtime on all tables the frontend subscribes to.
-- CRITICAL: Without this, the frontend gets nothing.
ALTER PUBLICATION supabase_realtime ADD TABLE incident_state;
ALTER PUBLICATION supabase_realtime ADD TABLE agent_logs;
ALTER PUBLICATION supabase_realtime ADD TABLE transcripts;
ALTER PUBLICATION supabase_realtime ADD TABLE dispatches;
```

---

## 6. Python Dependencies (`pyproject.toml`)

```toml
[project]
name = "triagenet-server"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
    "fastapi>=0.115.0",
    "uvicorn[standard]>=0.30.0",
    "pydantic>=2.10.0",
    "pydantic-settings>=2.6.0",
    "pydantic-ai[mistral]>=0.2.0",
    "mistralai>=1.12.0",
    "supabase>=2.11.0",
    "python-dotenv>=1.0.0",
    "httpx>=0.28.0",
    "python-multipart>=0.0.18",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.3.0",
    "pytest-asyncio>=0.24.0",
    "pytest-httpx>=0.34.0",
]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["src/tests"]
```

---

## 7. Configuration (`config.py`)

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Mistral
    mistral_api_key: str
    mistral_triage_model: str = "mistral-large-latest"
    mistral_vision_model: str = "mistral-small-latest"  # vision-capable

    # ElevenLabs
    elevenlabs_api_key: str

    # Supabase
    supabase_url: str
    supabase_service_key: str

    # App
    app_env: str = "development"
    log_level: str = "DEBUG"
    demo_scenario: str = "market_st_crash"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

settings = Settings()
```

---

## 8. Pydantic Models (Complete)

### `models/incident.py`

```python
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
```

### `models/caller.py`

```python
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
```

### `models/vision.py`

```python
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
```

### `models/triage.py`

```python
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
```

### `models/dispatch.py`

```python
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
```

### `models/events.py`

```python
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
```

---

## 9. Shared Dependencies (`agents/shared_deps.py`)

```python
from __future__ import annotations
from dataclasses import dataclass
from supabase import Client as SupabaseClient
from mistralai import Mistral

@dataclass
class TriageNetDeps:
    """Injected into every Pydantic-AI agent via RunContext[TriageNetDeps]."""
    supabase: SupabaseClient
    mistral_client: Mistral          # For Pixtral vision calls only
    case_id: str
    session_start_time: float        # time.time() at demo start, for elapsed time calc
    elevenlabs_api_key: str
```

---

## 10. Agent Definitions

### `agents/triage_agent.py` — The Brain

```python
from pydantic_ai import Agent, RunContext
from .shared_deps import TriageNetDeps
from ..models.triage import TriageResult
from ..models.incident import IncidentState

triage_agent = Agent(
    "mistral:mistral-large-latest",
    deps_type=TriageNetDeps,
    output_type=TriageResult,
    system_prompt="""You are TriageNet's triage intelligence agent.

You receive the current incident state — all caller reports, vision detections, and existing assessments.
Your job: classify severity, identify hazards, recommend response units, and generate an action plan.

Severity levels:
- unknown: No information yet
- low: Minor incident, no injuries
- medium: Injuries reported but not life-threatening
- high: Life-threatening injuries or significant hazard
- critical: Multiple casualties, trapped persons, children at risk, or active hazards (fire, explosion)

ALWAYS escalate if: child present, person trapped, fire/explosion detected, multiple callers corroborate danger.
NEVER downgrade severity once escalated.

Response units: EMS, Fire Response, Pediatric EMS, Traffic Control, Police, HazMat.
Only recommend units that are justified by the evidence. Include rationale.""",
)

@triage_agent.tool
async def get_current_state(ctx: RunContext[TriageNetDeps]) -> str:
    """Retrieves the current incident state from Supabase."""
    result = ctx.deps.supabase.table("incident_state") \
        .select("*") \
        .eq("case_id", ctx.deps.case_id) \
        .single() \
        .execute()
    state = IncidentState(**result.data)
    return state.model_dump_json()

@triage_agent.tool
async def get_all_transcripts(ctx: RunContext[TriageNetDeps]) -> str:
    """Retrieves all transcript segments for this case."""
    result = ctx.deps.supabase.table("transcripts") \
        .select("*") \
        .eq("case_id", ctx.deps.case_id) \
        .order("created_at") \
        .execute()
    return str(result.data)

@triage_agent.tool
async def get_vision_detections(ctx: RunContext[TriageNetDeps]) -> str:
    """Retrieves all vision detections for this case."""
    result = ctx.deps.supabase.table("incident_state") \
        .select("vision_detections") \
        .eq("case_id", ctx.deps.case_id) \
        .single() \
        .execute()
    return str(result.data.get("vision_detections", []))
```

### `agents/intake_agent.py` — Caller Fact Extraction

```python
from pydantic_ai import Agent, RunContext
from .shared_deps import TriageNetDeps
from ..models.caller import IntakeFacts

intake_agent = Agent(
    "mistral:mistral-large-latest",
    deps_type=TriageNetDeps,
    output_type=IntakeFacts,
    system_prompt="""You extract structured emergency intake facts from a caller transcript.

The transcript may be in any language. An English translation is provided.
Extract: location, incident type, whether someone is trapped, whether a child is present,
injuries described, hazards mentioned, and urgency keywords.

Be precise. Only flag child_present=true if a child is explicitly mentioned.
Only flag possible_trapped_person=true if entrapment is described.
Return all fields — use null/false/empty for fields with no evidence.""",
)
```

### `agents/vision_agent.py` — Pixtral Vision (Native SDK)

```python
"""
Vision agent uses the native mistralai client directly because
Pydantic-AI doesn't support Mistral's multimodal content-array format.
"""
import base64
import json
from ..models.vision import FrameAnalysis
from ..config import settings
from mistralai import Mistral

VISION_SYSTEM_PROMPT = """You are a CCTV scene analysis agent. Analyze the provided frame from a traffic camera.

Detect and report:
- Vehicle damage (none | minor | moderate | severe)
- Persons visible (count)
- Smoke visible (true/false)
- Fire visible (true/false)
- Any other hazards

Return a JSON object matching this exact schema:
{
  "frame_id": <int>,
  "detections": [{"type": "<string>", "confidence": <float 0-1>}],
  "overall_description": "<one-line summary>",
  "hazard_escalation": "<new hazard type or null>",
  "smoke_visible": <bool>,
  "fire_visible": <bool>,
  "vehicle_damage_severity": "<none|minor|moderate|severe>"
}"""

async def analyze_frame(
    mistral_client: Mistral,
    frame_bytes: bytes,
    frame_id: int,
) -> FrameAnalysis:
    """Send a frame to Pixtral for scene analysis. Returns typed FrameAnalysis."""
    b64 = base64.b64encode(frame_bytes).decode("utf-8")

    response = mistral_client.chat.complete(
        model=settings.mistral_vision_model,
        messages=[{
            "role": "user",
            "content": [
                {"type": "text", "text": f"Frame #{frame_id}. Analyze this CCTV frame. Return JSON only."},
                {"type": "image_url", "image_url": f"data:image/jpeg;base64,{b64}"},
            ],
        }],
        response_format={"type": "json_object"},
    )

    raw = json.loads(response.choices[0].message.content)
    raw["frame_id"] = frame_id
    return FrameAnalysis(**raw)


def compute_scene_delta(prev: FrameAnalysis | None, curr: FrameAnalysis) -> dict:
    """Compare consecutive frames. Returns delta info for state updates."""
    if prev is None:
        return {"new_hazard": None, "hazard_escalation": False}

    new_hazard = None
    if curr.fire_visible and not prev.fire_visible:
        new_hazard = "engine_fire"
    elif curr.smoke_visible and not prev.smoke_visible:
        new_hazard = "smoke"

    return {
        "new_hazard": new_hazard,
        "hazard_escalation": new_hazard is not None,
        "description": f"Scene delta: {prev.overall_description} → {curr.overall_description}",
    }
```

### `agents/dispatch_agent.py` — Dispatch Brief Generation

```python
from pydantic_ai import Agent, RunContext
from .shared_deps import TriageNetDeps
from ..models.dispatch import DispatchBrief

dispatch_agent = Agent(
    "mistral:mistral-large-latest",
    deps_type=TriageNetDeps,
    output_type=DispatchBrief,
    system_prompt="""You generate emergency dispatch briefings.

Given incident details and a unit type, produce:
- A unit callsign (e.g. AMB-7, ENG-4, PED-2, TC-3)
- A realistic ETA in minutes
- A concise voice message suitable for text-to-speech delivery
- A rationale for why this unit is being dispatched

The voice message should be professional, clear, and include:
incident type, location, key hazards, casualty info, and ETA.
Keep it under 40 words. It will be spoken aloud via TTS.""",
)

@dispatch_agent.tool
async def get_case_summary(ctx: RunContext[TriageNetDeps]) -> str:
    """Get current incident state for context."""
    result = ctx.deps.supabase.table("incident_state") \
        .select("incident_type, location_normalized, severity, people_count_estimate, hazard_flags, injury_flags") \
        .eq("case_id", ctx.deps.case_id) \
        .single() \
        .execute()
    return str(result.data)
```

### `agents/case_match_agent.py` — Evidence Fusion

```python
from pydantic_ai import Agent, RunContext
from .shared_deps import TriageNetDeps
from ..models.triage import EvidenceFusionResult

evidence_fusion_agent = Agent(
    "mistral:mistral-large-latest",
    deps_type=TriageNetDeps,
    output_type=EvidenceFusionResult,
    system_prompt="""You are an evidence fusion agent.

Given all caller transcripts and vision detections for an incident, determine:
1. Which claims are CORROBORATED by multiple independent sources
2. Whether the combined evidence warrants a severity change
3. Whether an evacuation warning is required

A corroboration occurs when:
- A caller reports something AND vision confirms it (e.g. caller says "smoke" + vision detects fire)
- Two callers independently report the same fact from different perspectives

Combined confidence = 1 - (1 - source1_conf) * (1 - source2_conf)

ONLY flag evacuation_warning_required if active fire/explosion threatens people near the scene.""",
)

@evidence_fusion_agent.tool
async def get_all_evidence(ctx: RunContext[TriageNetDeps]) -> str:
    """Get all transcripts + vision detections."""
    transcripts = ctx.deps.supabase.table("transcripts") \
        .select("*").eq("case_id", ctx.deps.case_id).execute()
    state = ctx.deps.supabase.table("incident_state") \
        .select("vision_detections, severity, hazard_flags, injury_flags") \
        .eq("case_id", ctx.deps.case_id).single().execute()
    return f"Transcripts: {transcripts.data}\nState: {state.data}"
```

---

## 11. Core Services

### `services/state.py` — Supabase State Manager

```python
"""
All state mutations go through this module. It writes to Supabase and logs the change.
"""
from supabase import Client as SupabaseClient
from ..models.incident import IncidentState, TimelineEvent
from ..models.events import AgentLogEntry
import time

class StateManager:
    def __init__(self, supabase: SupabaseClient, case_id: str, start_time: float):
        self.sb = supabase
        self.case_id = case_id
        self.start_time = start_time

    def elapsed(self) -> str:
        """Returns elapsed time as MM:SS string."""
        s = int(time.time() - self.start_time)
        return f"{s // 60:02d}:{s % 60:02d}"

    def get_state(self) -> IncidentState:
        result = self.sb.table("incident_state") \
            .select("*").eq("case_id", self.case_id).single().execute()
        return IncidentState(**result.data)

    def update_state(self, **kwargs) -> IncidentState:
        """Partial update. Pass any IncidentState fields as kwargs."""
        self.sb.table("incident_state") \
            .update(kwargs).eq("case_id", self.case_id).execute()
        return self.get_state()

    def append_timeline(self, agent: str, event: str):
        """Append a timeline event. Uses JSONB append in Postgres."""
        state = self.get_state()
        timeline = state.timeline
        timeline.append(TimelineEvent(t=self.elapsed(), agent=agent, event=event))
        self.update_state(timeline=[t.model_dump() for t in timeline])

    def log_agent(self, entry: AgentLogEntry):
        """Write to agent_logs table."""
        self.sb.table("agent_logs").insert(entry.model_dump()).execute()

    def log(self, agent: str, event_type: str, message: str,
            data: dict = None, color: str = "blue", flash: bool = False):
        """Convenience: log + timeline in one call."""
        self.log_agent(AgentLogEntry(
            case_id=self.case_id,
            agent=agent,
            event_type=event_type,
            message=message,
            data=data or {},
            display_color=color,
            display_flash=flash,
        ))
        self.append_timeline(agent, message)
```

### `services/transcription.py` — ElevenLabs Transcription

```python
"""
Wraps ElevenLabs transcription API.
For the demo, we transcribe pre-recorded audio files.
"""
import httpx
from ..config import settings

ELEVENLABS_TRANSCRIBE_URL = "https://api.elevenlabs.io/v1/speech-to-text"

async def transcribe_audio(audio_path: str) -> dict:
    """
    Send audio file to ElevenLabs for transcription.
    Returns: {language_code: str, text: str, confidence: float}
    """
    async with httpx.AsyncClient(timeout=30.0) as client:
        with open(audio_path, "rb") as f:
            response = await client.post(
                ELEVENLABS_TRANSCRIBE_URL,
                headers={"xi-api-key": settings.elevenlabs_api_key},
                files={"file": (audio_path, f, "audio/mpeg")},
                data={"model_id": "scribe_v1"},  # ElevenLabs Scribe model
            )
        response.raise_for_status()
        data = response.json()
        return {
            "language_code": data.get("language_code", "unknown"),
            "text": data.get("text", ""),
            "confidence": data.get("confidence", 0.0),
        }
```

### `services/tts.py` — ElevenLabs Text-to-Speech

```python
"""
Wraps ElevenLabs TTS API for generating voice responses and dispatch briefs.
"""
import httpx
from ..config import settings

ELEVENLABS_TTS_URL = "https://api.elevenlabs.io/v1/text-to-speech"

# Voice IDs — configure per language. Use ElevenLabs preset voices or clone.
VOICE_MAP = {
    "es": "pFZP5JQG7iQjIQuC4Bku",  # Spanish female voice (Lily)
    "zh": "nPczCjzI2devNBz1zQrb",  # Chinese voice (Brian)
    "fr": "XB0fDUnXU5powFXDhCwa",  # French voice (Charlotte)
    "en": "JBFqnCBsd6RMkjVDRZzb",  # English dispatch voice (George)
}

async def generate_speech(text: str, language: str = "en") -> bytes:
    """
    Generate speech audio from text. Returns MP3 bytes.
    """
    voice_id = VOICE_MAP.get(language, VOICE_MAP["en"])
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{ELEVENLABS_TTS_URL}/{voice_id}",
            headers={
                "xi-api-key": settings.elevenlabs_api_key,
                "Content-Type": "application/json",
            },
            json={
                "text": text,
                "model_id": "eleven_turbo_v2_5",
                "voice_settings": {
                    "stability": 0.7,
                    "similarity_boost": 0.8,
                },
            },
        )
        response.raise_for_status()
        return response.content
```

---

## 12. Demo Orchestrator (`services/orchestrator.py`)

This is the backbone. It drives the entire 120-second demo deterministically.

```python
"""
DemoOrchestrator — drives all timed events for the 120-second demo.

Call start() and it runs the full sequence. Each phase:
1. Triggers backend actions (transcribe, analyze, triage, dispatch)
2. Writes results to Supabase via StateManager
3. Frontend reacts via Realtime subscriptions

The orchestrator is an async function that uses asyncio.sleep() for timing.
All agent calls are real (Mistral inference, ElevenLabs API). Not mocked.
"""
import asyncio
import time
from ..agents.shared_deps import TriageNetDeps
from ..agents.triage_agent import triage_agent
from ..agents.intake_agent import intake_agent
from ..agents.dispatch_agent import dispatch_agent
from ..agents.case_match_agent import evidence_fusion_agent
from ..agents.vision_agent import analyze_frame, compute_scene_delta
from ..services.state import StateManager
from ..services.transcription import transcribe_audio
from ..services.tts import generate_speech
from ..services.media import extract_frame
from ..models.incident import Severity, IncidentStatus
from ..models.caller import CallerRecord

CALLERS = [
    CallerRecord(caller_id="caller_1", label="The Wife", language="es",
                 audio_path="assets/caller_1_spanish.mp3", start_delay_s=12),
    CallerRecord(caller_id="caller_2", label="Bystander", language="zh",
                 audio_path="assets/caller_2_mandarin.mp3", start_delay_s=38),
    CallerRecord(caller_id="caller_3", label="Shopkeeper", language="fr",
                 audio_path="assets/caller_3_french.mp3", start_delay_s=56),
]

class DemoOrchestrator:
    def __init__(self, deps: TriageNetDeps, state: StateManager):
        self.deps = deps
        self.state = state
        self.previous_frame = None
        self._approved = asyncio.Event()  # Set when operator clicks APPROVE

    def approve(self):
        """Called by the /demo/approve endpoint."""
        self._approved.set()

    async def start(self):
        """Run the full 120-second demo sequence."""
        self.state.log("orchestrator", "init", "Demo started: TN-2026-00417", color="blue")

        # Phase 0 — Init (0:00-0:12)
        await self._phase_0_init()

        # Phase 1 — Caller 1 (0:12-0:30)
        await self._phase_1_caller_1()

        # Phase 2 — Human Approval (0:30-0:38)
        await self._phase_2_approval()

        # Phase 3 — Caller 2 (0:38-0:56)
        await self._phase_3_caller_2()

        # Phase 4 — Vision / Fire Detection (0:56-1:18)
        await self._phase_4_vision()

        # Phase 5 — Priority Interrupt (1:18-1:36)
        await self._phase_5_interrupt()

        # Phase 6 — Final Summary (1:36-2:00)
        await self._phase_6_summary()

    async def _phase_0_init(self):
        """Initialize case, start video monitor."""
        self.state.update_state(status=IncidentStatus.INTAKE.value, severity=Severity.UNKNOWN.value)
        self.state.log("orchestrator", "init", "Case created: TN-2026-00417")
        self.state.log("orchestrator", "init", "Video monitor armed")
        await asyncio.sleep(2)  # Brief pause before first caller

    async def _phase_1_caller_1(self):
        """Process Caller 1 — Spanish wife reporting crash."""
        caller = CALLERS[0]
        self.state.log("voice", "caller_connected", f"Incoming call: {caller.label} ({caller.language.upper()})",
                       color="green")
        self.state.update_state(caller_count=1)

        # 1. Transcribe
        transcript = await transcribe_audio(caller.audio_path)
        self.state.log("voice", "transcript_received", f"Transcribed ({caller.language}): {transcript['text']}")

        # Write transcript to Supabase
        self.deps.supabase.table("transcripts").insert({
            "case_id": self.deps.case_id,
            "caller_id": caller.caller_id,
            "caller_label": caller.label,
            "language": caller.language,
            "original_text": transcript["text"],
            "translated_text": None,  # Intake agent will translate
            "confidence": transcript.get("confidence"),
            "segment_index": 0,
        }).execute()

        # 2. Extract intake facts
        facts_result = await intake_agent.run(
            f"Transcript from emergency caller ({caller.language}): {transcript['text']}",
            deps=self.deps,
        )
        facts = facts_result.data
        self.state.log("intake", "facts_extracted", f"Location: {facts.location_raw}, Type: {facts.incident_type_candidate}")

        # 3. Update state with intake facts
        self.state.update_state(
            location_raw=facts.location_raw,
            location_normalized=facts.location_raw,  # Could normalize further
            incident_type=facts.incident_type_candidate,
        )

        # 4. Run triage
        triage_result = await triage_agent.run(
            "Classify this incident based on current state. Check all evidence.",
            deps=self.deps,
        )
        triage = triage_result.data
        self.state.update_state(
            severity=triage.severity.value,
            recommended_units=[u for u in triage.recommended_units],
            people_count_estimate=triage.people_count_estimate,
            injury_flags=triage.injury_flags,
            action_plan_version=1,
            action_plan=[a.model_dump() for a in triage.action_plan],
            status=IncidentStatus.ACTIVE.value,
        )
        self.state.log("triage", "severity_changed", f"Severity: {triage.severity.value.upper()}",
                       color="amber", flash=True)
        self.state.log("triage", "action_plan", "Action Plan v1 generated", color="blue")

        # 5. Generate voice response to caller
        # (In production this would be streamed; for demo we just log it)
        self.state.log("voice", "response_sent", f"Voice response sent to {caller.label} ({caller.language.upper()})",
                       color="green")

    async def _phase_2_approval(self):
        """Wait for operator to click APPROVE INITIAL RESPONSE."""
        self.state.log("orchestrator", "awaiting_approval",
                       "⏳ Awaiting operator approval for initial response...",
                       color="amber", flash=True)

        # Wait for the approve() method to be called (max 30s timeout)
        try:
            await asyncio.wait_for(self._approved.wait(), timeout=30.0)
        except asyncio.TimeoutError:
            # Auto-approve if operator doesn't click (keeps demo moving)
            self.state.log("orchestrator", "auto_approved", "Auto-approved (timeout)", color="amber")

        state = self.state.get_state()
        self.state.update_state(confirmed_units=state.recommended_units)
        self.state.log("orchestrator", "approved", "✓ Operator confirmed Action Plan v1", color="green", flash=True)

        # Generate dispatch briefs for confirmed units
        for unit in state.recommended_units:
            dispatch_result = await dispatch_agent.run(
                f"Generate dispatch brief for {unit}. Incident: {state.incident_type} at {state.location_normalized}.",
                deps=self.deps,
            )
            brief = dispatch_result.data
            self.deps.supabase.table("dispatches").insert({
                "case_id": self.deps.case_id,
                "unit_type": unit,
                "unit_assigned": brief.unit_assigned,
                "destination": brief.destination,
                "eta_minutes": brief.eta_minutes,
                "status": "confirmed",
                "voice_message": brief.voice_message,
                "rationale": brief.rationale,
            }).execute()
            self.state.log("dispatch", "unit_dispatched", f"{unit} dispatched: {brief.unit_assigned} → {brief.destination}",
                           color="green")

    async def _phase_3_caller_2(self):
        """Process Caller 2 — Mandarin bystander reporting child."""
        caller = CALLERS[1]
        self.state.log("voice", "caller_connected", f"Incoming call: {caller.label} ({caller.language.upper()})",
                       color="green")
        self.state.update_state(caller_count=2)

        # Transcribe
        transcript = await transcribe_audio(caller.audio_path)
        self.state.log("voice", "transcript_received", f"Transcribed ({caller.language}): {transcript['text']}")

        self.deps.supabase.table("transcripts").insert({
            "case_id": self.deps.case_id,
            "caller_id": caller.caller_id,
            "caller_label": caller.label,
            "language": caller.language,
            "original_text": transcript["text"],
            "confidence": transcript.get("confidence"),
            "segment_index": 0,
        }).execute()

        # Extract facts
        facts_result = await intake_agent.run(
            f"Transcript from emergency caller ({caller.language}): {transcript['text']}",
            deps=self.deps,
        )
        facts = facts_result.data

        # Case correlation
        self.state.log("intake", "case_match", f"Caller 2 linked to TN-2026-00417 (0.94)", color="purple")
        self.state.update_state(match_confidence=0.94)

        # Evidence fusion
        fusion_result = await evidence_fusion_agent.run(
            "Fuse all evidence. A second caller has been linked to this case. Check for new information.",
            deps=self.deps,
        )
        fusion = fusion_result.data

        # Re-triage with new evidence
        triage_result = await triage_agent.run(
            "Re-classify. New caller added with additional victim information. Check all evidence and update.",
            deps=self.deps,
        )
        triage = triage_result.data

        # Update state
        injury = list(set(self.state.get_state().injury_flags + triage.injury_flags))
        self.state.update_state(
            severity=triage.severity.value,
            recommended_units=triage.recommended_units,
            people_count_estimate=triage.people_count_estimate,
            injury_flags=injury,
            action_plan_version=2,
            action_plan=[a.model_dump() for a in triage.action_plan],
            status=IncidentStatus.CRITICAL.value if triage.severity == Severity.CRITICAL else IncidentStatus.ESCALATED.value,
        )
        self.state.log("triage", "severity_changed",
                       f"Severity: HIGH → {triage.severity.value.upper()} ▲",
                       color="red", flash=True)
        self.state.log("triage", "action_plan", "Action Plan v2 generated", color="blue")

    async def _phase_4_vision(self):
        """Vision analysis — detect smoke then fire from video frames."""
        self.state.log("vision", "scanning", "CCTV analysis active", color="purple")

        # Frame 1 — Smoke detection (~58s into video)
        frame_bytes_1 = await extract_frame("assets/crash_video.mp4", timestamp_s=58)
        analysis_1 = await analyze_frame(self.deps.mistral_client, frame_bytes_1, frame_id=1)
        self.state.log("vision", "detection", f"Smoke detected (confidence: {analysis_1.detections[0].confidence if analysis_1.detections else 'N/A'})",
                       color="purple")

        await asyncio.sleep(3)  # Simulate polling interval

        # Frame 2 — Fire detection (~66s into video)
        frame_bytes_2 = await extract_frame("assets/crash_video.mp4", timestamp_s=66)
        analysis_2 = await analyze_frame(self.deps.mistral_client, frame_bytes_2, frame_id=2)
        delta = compute_scene_delta(analysis_1, analysis_2)

        if delta.get("hazard_escalation"):
            self.state.log("vision", "hazard_escalation",
                           f"🔥 ENGINE FIRE DETECTED (0.99)",
                           color="red", flash=True)

        # Update state with vision detections
        state = self.state.get_state()
        detections = state.vision_detections + [d.model_dump() for d in analysis_2.detections]
        hazards = list(set(state.hazard_flags + ["engine_fire"]))
        self.state.update_state(
            vision_detections=detections,
            hazard_flags=hazards,
        )

        # Evidence fusion — corroborate vision with caller 3 (if smoke was reported)
        fusion_result = await evidence_fusion_agent.run(
            "New vision evidence: engine fire detected. Check if any callers mentioned smoke or fire.",
            deps=self.deps,
        )
        if fusion_result.data.corroborations:
            self.state.log("triage", "corroboration",
                           "✓ CORROBORATED: Vision fire + Caller report match",
                           color="green", flash=True)

        # Re-triage
        triage_result = await triage_agent.run(
            "Re-classify. Engine fire visually confirmed. Update action plan.",
            deps=self.deps,
        )
        triage = triage_result.data
        self.state.update_state(
            recommended_units=triage.recommended_units,
            action_plan_version=3,
            action_plan=[a.model_dump() for a in triage.action_plan],
            status=IncidentStatus.ESCALATED.value,
        )
        self.state.log("triage", "action_plan", "Action Plan v3 generated — Fire Response added", color="blue")

    async def _phase_5_interrupt(self):
        """Priority interrupt — warn callers in their native languages."""
        self.state.log("voice", "priority_interrupt",
                       "⚠ PRIORITY INTERRUPT — Hazard warning to all callers",
                       color="red", flash=True)

        # Generate TTS warnings in each active language
        for lang_code in ["es", "zh"]:
            self.state.log("voice", "warning_sent",
                           f"Evacuation warning sent ({lang_code.upper()})",
                           color="red")

        # Dispatch fire response
        dispatch_result = await dispatch_agent.run(
            "Generate dispatch brief for Fire Response. Engine fire confirmed by CCTV. Urgent.",
            deps=self.deps,
        )
        brief = dispatch_result.data
        self.deps.supabase.table("dispatches").insert({
            "case_id": self.deps.case_id,
            "unit_type": "Fire Response",
            "unit_assigned": brief.unit_assigned,
            "destination": brief.destination,
            "eta_minutes": brief.eta_minutes,
            "status": "dispatched",
            "voice_message": brief.voice_message,
            "rationale": "Vision-confirmed engine fire",
        }).execute()
        self.state.log("dispatch", "unit_dispatched",
                       f"Fire Response dispatched: {brief.unit_assigned}",
                       color="red", flash=True)

    async def _phase_6_summary(self):
        """Generate final case summary. Freeze state."""
        state = self.state.get_state()
        summary = (
            f"Vehicle collision with trapped occupant and child confirmed. "
            f"Engine fire visually detected and corroborated. "
            f"Severity: CRITICAL. "
            f"{len(state.confirmed_units)} units confirmed, "
            f"{len(state.recommended_units)} total recommended. "
            f"Multilingual warnings delivered in ES, ZH."
        )
        self.state.update_state(
            status=IncidentStatus.RESOLVED_DEMO.value,
            operator_summary=summary,
        )
        self.state.log("orchestrator", "complete",
                       f"Demo complete: TN-2026-00417",
                       color="green", flash=True)
```

---

## 13. FastAPI Routes

### `routes/demo.py`

```python
from fastapi import APIRouter, BackgroundTasks
from ..services.orchestrator import DemoOrchestrator
from ..services.state import StateManager
from ..agents.shared_deps import TriageNetDeps
from ..deps import get_supabase, get_mistral_client
from ..config import settings
import time

router = APIRouter(prefix="/demo", tags=["demo"])

# Module-level reference to the active orchestrator
_active_orchestrator: DemoOrchestrator | None = None

@router.post("/start")
async def start_demo(background_tasks: BackgroundTasks):
    """Initialize and start the 120-second demo."""
    global _active_orchestrator
    case_id = "TN-2026-00417"
    supabase = get_supabase()
    mistral = get_mistral_client()
    start_time = time.time()

    # Create incident_state row
    supabase.table("incident_state").upsert({
        "case_id": case_id,
        "status": "intake",
        "severity": "unknown",
        "caller_count": 0,
        "people_count_estimate": 0,
        "injury_flags": [],
        "hazard_flags": [],
        "vision_detections": [],
        "recommended_units": [],
        "confirmed_units": [],
        "timeline": [],
        "action_plan_version": 0,
        "action_plan": [],
    }).execute()

    deps = TriageNetDeps(
        supabase=supabase,
        mistral_client=mistral,
        case_id=case_id,
        session_start_time=start_time,
        elevenlabs_api_key=settings.elevenlabs_api_key,
    )
    state = StateManager(supabase, case_id, start_time)
    _active_orchestrator = DemoOrchestrator(deps, state)

    # Run orchestrator in background — returns immediately to frontend
    background_tasks.add_task(_active_orchestrator.start)

    return {"case_id": case_id, "status": "started"}


@router.post("/approve")
async def approve_response():
    """Operator approves initial response. Unblocks Phase 2 in orchestrator."""
    global _active_orchestrator
    if _active_orchestrator:
        _active_orchestrator.approve()
        return {"status": "approved"}
    return {"status": "no_active_demo"}


@router.get("/status")
async def demo_status():
    """Get current demo state."""
    supabase = get_supabase()
    result = supabase.table("incident_state") \
        .select("*").eq("case_id", "TN-2026-00417").single().execute()
    return result.data
```

### `routes/health.py`

```python
from fastapi import APIRouter
from ..config import settings
from ..deps import get_supabase, get_mistral_client
import time

router = APIRouter(tags=["health"])

@router.get("/health")
async def health_check():
    """Full system health check. Tests all external APIs."""
    checks = {}

    # Supabase
    try:
        t = time.time()
        sb = get_supabase()
        sb.table("incident_state").select("case_id").limit(1).execute()
        checks["supabase"] = {"status": "ok", "latency_ms": int((time.time() - t) * 1000)}
    except Exception as e:
        checks["supabase"] = {"status": "error", "error": str(e)}

    # Mistral
    try:
        t = time.time()
        client = get_mistral_client()
        response = client.chat.complete(
            model=settings.mistral_triage_model,
            messages=[{"role": "user", "content": "Say 'ok'"}],
            max_tokens=5,
        )
        checks["mistral"] = {"status": "ok", "latency_ms": int((time.time() - t) * 1000)}
    except Exception as e:
        checks["mistral"] = {"status": "error", "error": str(e)}

    # ElevenLabs (lightweight check)
    try:
        import httpx
        t = time.time()
        async with httpx.AsyncClient() as client:
            r = await client.get(
                "https://api.elevenlabs.io/v1/voices",
                headers={"xi-api-key": settings.elevenlabs_api_key},
            )
            r.raise_for_status()
        checks["elevenlabs"] = {"status": "ok", "latency_ms": int((time.time() - t) * 1000)}
    except Exception as e:
        checks["elevenlabs"] = {"status": "error", "error": str(e)}

    all_ok = all(c.get("status") == "ok" for c in checks.values())
    return {"status": "healthy" if all_ok else "degraded", "checks": checks, "all_clear": all_ok}
```

### `main.py`

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routes import demo, health

app = FastAPI(title="TriageNet API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Next.js dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(demo.router, prefix="/api/v1")
app.include_router(health.router, prefix="/api/v1")
```

---

## 14. Frontend Hooks (Supabase Realtime)

### `hooks/useIncidentState.ts`

```typescript
import { useEffect, useState } from "react";
import { supabase } from "@/lib/supabase";

export interface IncidentState {
  case_id: string;
  status: string;
  incident_type: string | null;
  location_normalized: string | null;
  severity: string;
  caller_count: number;
  people_count_estimate: number;
  injury_flags: string[];
  hazard_flags: string[];
  vision_detections: any[];
  recommended_units: string[];
  confirmed_units: string[];
  timeline: { t: string; agent: string; event: string }[];
  action_plan_version: number;
  action_plan: { status: string; action: string }[];
  operator_summary: string | null;
  updated_at: string;
}

export function useIncidentState(caseId: string) {
  const [state, setState] = useState<IncidentState | null>(null);

  useEffect(() => {
    // Initial fetch
    supabase
      .from("incident_state")
      .select("*")
      .eq("case_id", caseId)
      .single()
      .then(({ data }) => {
        if (data) setState(data as IncidentState);
      });

    // Realtime subscription
    const channel = supabase
      .channel(`incident_${caseId}`)
      .on(
        "postgres_changes",
        {
          event: "UPDATE",
          schema: "public",
          table: "incident_state",
          filter: `case_id=eq.${caseId}`,
        },
        (payload) => {
          setState(payload.new as IncidentState);
        }
      )
      .subscribe();

    return () => {
      supabase.removeChannel(channel);
    };
  }, [caseId]);

  return state;
}
```

### `hooks/useAgentLogs.ts`

```typescript
import { useEffect, useState } from "react";
import { supabase } from "@/lib/supabase";

export interface AgentLog {
  id: number;
  agent: string;
  event_type: string;
  message: string;
  data: any;
  display_color: string;
  display_flash: boolean;
  created_at: string;
}

export function useAgentLogs(caseId: string) {
  const [logs, setLogs] = useState<AgentLog[]>([]);

  useEffect(() => {
    // Initial fetch
    supabase
      .from("agent_logs")
      .select("*")
      .eq("case_id", caseId)
      .order("created_at", { ascending: true })
      .then(({ data }) => {
        if (data) setLogs(data as AgentLog[]);
      });

    // Realtime — listen for new inserts
    const channel = supabase
      .channel(`logs_${caseId}`)
      .on(
        "postgres_changes",
        {
          event: "INSERT",
          schema: "public",
          table: "agent_logs",
          filter: `case_id=eq.${caseId}`,
        },
        (payload) => {
          setLogs((prev) => [...prev, payload.new as AgentLog]);
        }
      )
      .subscribe();

    return () => {
      supabase.removeChannel(channel);
    };
  }, [caseId]);

  return logs;
}
```

---

## 15. Implementation Phases (BUILD IN THIS ORDER)

> **CRITICAL: Do not skip phases. Each phase has a test gate. Pass the tests before moving on.**
> **This is the lesson from the last hackathon: test each layer before building the next.**

---

### PHASE 1: Models + Config (30 min)

**Build:** `config.py`, all `models/*.py`, `shared_deps.py`

**Test (`test_phase1_models.py`):**
```python
def test_incident_state_defaults():
    state = IncidentState(case_id="TEST-001")
    assert state.severity == Severity.UNKNOWN
    assert state.caller_count == 0
    assert state.timeline == []

def test_intake_facts_schema():
    facts = IntakeFacts(location_raw="Market & 5th", possible_trapped_person=True)
    assert facts.child_present == False  # default
    json_schema = IntakeFacts.model_json_schema()
    assert "location_raw" in json_schema["properties"]

def test_triage_result_schema():
    result = TriageResult(
        severity=Severity.HIGH,
        incident_type="vehicle_collision",
        reasoning="Test",
        recommended_units=["EMS"],
    )
    assert result.severity == Severity.HIGH

def test_all_models_serializable():
    """Every model must round-trip through JSON."""
    for Model in [IncidentState, IntakeFacts, FrameAnalysis, TriageResult, DispatchBrief]:
        schema = Model.model_json_schema()
        assert "properties" in schema
```

**Gate:** `uv run pytest src/tests/test_phase1_models.py -v` — all pass.

---

### PHASE 2: Supabase Schema + State Manager (45 min)

**Build:** Run all migrations. Build `services/state.py`, `deps.py`.

**Test (`test_phase2_supabase.py`):**
```python
import pytest
from src.services.state import StateManager
from src.deps import get_supabase

@pytest.fixture
def state_manager():
    sb = get_supabase()
    case_id = "TEST-PHASE2"
    # Clean up any previous test data
    sb.table("incident_state").delete().eq("case_id", case_id).execute()
    sb.table("incident_state").insert({"case_id": case_id, "status": "intake", "severity": "unknown"}).execute()
    yield StateManager(sb, case_id, start_time=0)
    sb.table("incident_state").delete().eq("case_id", case_id).execute()

def test_get_state(state_manager):
    state = state_manager.get_state()
    assert state.case_id == "TEST-PHASE2"
    assert state.severity.value == "unknown"

def test_update_state(state_manager):
    state_manager.update_state(severity="high", caller_count=1)
    state = state_manager.get_state()
    assert state.severity.value == "high"
    assert state.caller_count == 1

def test_append_timeline(state_manager):
    state_manager.append_timeline("test", "Test event")
    state = state_manager.get_state()
    assert len(state.timeline) == 1
    assert state.timeline[0].agent == "test"

def test_log_agent(state_manager):
    state_manager.log("test", "test_event", "Hello from test")
    sb = get_supabase()
    logs = sb.table("agent_logs").select("*").eq("case_id", "TEST-PHASE2").execute()
    assert len(logs.data) > 0

def test_realtime_enabled():
    """Verify Realtime is configured on all tables."""
    sb = get_supabase()
    # This will fail if Realtime isn't enabled — the subscription won't fire.
    # Manual check: go to Supabase dashboard → Database → Replication and verify all 4 tables listed.
    pass
```

**Gate:** `uv run pytest src/tests/test_phase2_supabase.py -v` — all pass. Verify Supabase Realtime is enabled in dashboard.

---

### PHASE 3: Mistral API Connectivity (30 min)

**Build:** Verify Mistral API key works. Test chat completion, structured output, and vision.

**Test (`test_phase3_mistral.py`):**
```python
import pytest
import time
from mistralai import Mistral
from src.config import settings

@pytest.fixture
def client():
    return Mistral(api_key=settings.mistral_api_key)

def test_mistral_chat(client):
    t = time.time()
    response = client.chat.complete(
        model=settings.mistral_triage_model,
        messages=[{"role": "user", "content": "Say 'hello' and nothing else."}],
        max_tokens=10,
    )
    latency = (time.time() - t) * 1000
    assert "hello" in response.choices[0].message.content.lower()
    assert latency < 5000, f"Mistral chat too slow: {latency}ms"
    print(f"Mistral chat latency: {latency:.0f}ms")

def test_mistral_structured_output(client):
    """Verify JSON mode works."""
    t = time.time()
    response = client.chat.complete(
        model=settings.mistral_triage_model,
        messages=[{"role": "user", "content": 'Return JSON: {"severity": "high", "reason": "test"}'}],
        response_format={"type": "json_object"},
    )
    latency = (time.time() - t) * 1000
    import json
    data = json.loads(response.choices[0].message.content)
    assert "severity" in data
    assert latency < 5000, f"Structured output too slow: {latency}ms"
    print(f"Mistral structured output latency: {latency:.0f}ms")

def test_mistral_vision(client):
    """Verify vision model accepts image input. Use a tiny test image."""
    import base64
    # 1x1 red pixel JPEG
    tiny_jpeg = base64.b64decode("/9j/4AAQSkZJRgABAQEASABIAAD/2wBDAP//////////////////////////////////////////////////////////////////////////////////////2wBDAf//////////////////////////////////////////////////////////////////////////////////////wAARCAABAAEDASIAAhEBAxEB/8QAFAABAAAAAAAAAAAAAAAAAAAACf/EABQQAQAAAAAAAAAAAAAAAAAAAAD/xAAUAQEAAAAAAAAAAAAAAAAAAAAA/8QAFBEBAAAAAAAAAAAAAAAAAAAAAP/aAAwDAQACEQMRAD8AKwA//9k=")
    t = time.time()
    response = client.chat.complete(
        model=settings.mistral_vision_model,
        messages=[{
            "role": "user",
            "content": [
                {"type": "text", "text": "What color is this pixel? Reply in one word."},
                {"type": "image_url", "image_url": f"data:image/jpeg;base64,{base64.b64encode(tiny_jpeg).decode()}"},
            ],
        }],
    )
    latency = (time.time() - t) * 1000
    assert response.choices[0].message.content is not None
    assert latency < 5000, f"Vision too slow: {latency}ms"
    print(f"Mistral vision latency: {latency:.0f}ms")
```

**Gate:** `uv run pytest src/tests/test_phase3_mistral.py -v -s` — all pass, latencies printed. If any call > 5s, investigate network/model.

---

### PHASE 4: ElevenLabs API Connectivity (30 min)

**Build:** `services/transcription.py`, `services/tts.py`. Create or obtain test audio files.

**Test (`test_phase4_elevenlabs.py`):**
```python
import pytest
import time
from src.services.tts import generate_speech
from src.config import settings

@pytest.mark.asyncio
async def test_tts_english():
    t = time.time()
    audio = await generate_speech("Testing emergency dispatch system.", language="en")
    latency = (time.time() - t) * 1000
    assert len(audio) > 1000, "Audio too small — likely empty"
    assert latency < 3000, f"TTS too slow: {latency}ms"
    print(f"ElevenLabs TTS latency: {latency:.0f}ms, size: {len(audio)} bytes")

@pytest.mark.asyncio
async def test_tts_spanish():
    audio = await generate_speech("Emergencia. Mantenga la calma.", language="es")
    assert len(audio) > 1000

@pytest.mark.asyncio
async def test_voices_accessible():
    """Verify all voice IDs in VOICE_MAP are accessible."""
    import httpx
    async with httpx.AsyncClient() as client:
        r = await client.get(
            "https://api.elevenlabs.io/v1/voices",
            headers={"xi-api-key": settings.elevenlabs_api_key},
        )
        r.raise_for_status()
        voices = r.json()
        voice_ids = [v["voice_id"] for v in voices["voices"]]
        print(f"Available voices: {len(voice_ids)}")
        # Don't assert specific IDs — they may need updating
```

**Gate:** `uv run pytest src/tests/test_phase4_elevenlabs.py -v -s` — all pass, latencies printed.

---

### PHASE 5: Pydantic-AI Agents (60 min)

**Build:** All agents in `agents/`. This is where pydantic-ai talks to Mistral.

**Test (`test_phase5_agents.py`):**
```python
import pytest
import time
from src.agents.shared_deps import TriageNetDeps
from src.agents.intake_agent import intake_agent
from src.agents.triage_agent import triage_agent
from src.agents.dispatch_agent import dispatch_agent
from src.deps import get_supabase, get_mistral_client
from src.config import settings
from src.models.incident import Severity

@pytest.fixture
def deps():
    sb = get_supabase()
    case_id = "TEST-AGENTS"
    sb.table("incident_state").upsert({
        "case_id": case_id, "status": "active", "severity": "high",
        "incident_type": "vehicle_collision", "location_normalized": "Market St & 5th St",
        "caller_count": 1, "people_count_estimate": 2,
        "injury_flags": ["trapped_person"], "hazard_flags": [],
        "recommended_units": ["EMS"], "confirmed_units": [],
        "timeline": [], "action_plan_version": 1, "action_plan": [],
        "vision_detections": [],
    }).execute()
    yield TriageNetDeps(
        supabase=sb, mistral_client=get_mistral_client(),
        case_id=case_id, session_start_time=0,
        elevenlabs_api_key=settings.elevenlabs_api_key,
    )
    sb.table("incident_state").delete().eq("case_id", case_id).execute()
    sb.table("agent_logs").delete().eq("case_id", case_id).execute()
    sb.table("transcripts").delete().eq("case_id", case_id).execute()

@pytest.mark.asyncio
async def test_intake_agent(deps):
    t = time.time()
    result = await intake_agent.run(
        "Transcript from emergency caller (es): Help! There was a terrible crash at Market and 5th. My husband is trapped in the car!",
        deps=deps,
    )
    latency = (time.time() - t) * 1000
    facts = result.data
    assert facts.location_raw is not None
    assert facts.possible_trapped_person == True
    assert latency < 5000, f"Intake agent too slow: {latency}ms"
    print(f"Intake agent: location={facts.location_raw}, trapped={facts.possible_trapped_person}, latency={latency:.0f}ms")

@pytest.mark.asyncio
async def test_triage_agent(deps):
    t = time.time()
    result = await triage_agent.run(
        "Classify this incident based on current state.",
        deps=deps,
    )
    latency = (time.time() - t) * 1000
    triage = result.data
    assert triage.severity in [Severity.HIGH, Severity.CRITICAL]
    assert len(triage.recommended_units) > 0
    assert triage.reasoning != ""
    assert latency < 8000, f"Triage agent too slow: {latency}ms"
    print(f"Triage: severity={triage.severity}, units={triage.recommended_units}, latency={latency:.0f}ms")

@pytest.mark.asyncio
async def test_dispatch_agent(deps):
    t = time.time()
    result = await dispatch_agent.run(
        "Generate dispatch brief for EMS. Incident: vehicle collision at Market St & 5th St.",
        deps=deps,
    )
    latency = (time.time() - t) * 1000
    brief = result.data
    assert brief.unit_assigned != ""
    assert brief.voice_message != ""
    assert brief.eta_minutes > 0
    assert latency < 5000, f"Dispatch agent too slow: {latency}ms"
    print(f"Dispatch: unit={brief.unit_assigned}, ETA={brief.eta_minutes}min, latency={latency:.0f}ms")
```

**Gate:** `uv run pytest src/tests/test_phase5_agents.py -v -s` — all pass. Agents return correct typed outputs. Latencies reasonable.

---

### PHASE 6: Orchestrator (60 min)

**Build:** `services/orchestrator.py`, `services/media.py`, `routes/demo.py`, `routes/health.py`, `main.py`

**Test (`test_phase6_orchestrator.py`):**
```python
import pytest
import httpx
import time

BASE = "http://localhost:8000/api/v1"

@pytest.mark.asyncio
async def test_health():
    async with httpx.AsyncClient() as client:
        r = await client.get(f"{BASE}/health")
        assert r.status_code == 200
        data = r.json()
        assert data["all_clear"] == True
        print(f"Health: {data['checks']}")

@pytest.mark.asyncio
async def test_demo_start():
    async with httpx.AsyncClient(timeout=10.0) as client:
        r = await client.post(f"{BASE}/demo/start")
        assert r.status_code == 200
        data = r.json()
        assert data["case_id"] == "TN-2026-00417"
        assert data["status"] == "started"

@pytest.mark.asyncio
async def test_demo_approve():
    async with httpx.AsyncClient() as client:
        r = await client.post(f"{BASE}/demo/approve")
        assert r.status_code == 200

@pytest.mark.asyncio
async def test_demo_status_updates():
    """After starting demo, state should evolve over time."""
    async with httpx.AsyncClient() as client:
        await client.post(f"{BASE}/demo/start")
        await asyncio.sleep(5)  # Let Phase 1 run
        r = await client.get(f"{BASE}/demo/status")
        data = r.json()
        assert data["caller_count"] >= 1
        assert data["severity"] != "unknown"
```

**Gate:** Start server with `uv run uvicorn src.main:app --reload`, then `uv run pytest src/tests/test_phase6_orchestrator.py -v -s`. Health check passes. Demo starts and state begins updating.

---

### PHASE 7: Frontend (90 min)

**Build:** Next.js app with all components and Supabase Realtime hooks.

**Test:** Manual. Open browser → click START DEMO → watch:
1. Agent Terminal populates with colored log entries
2. Transcript panel shows Caller 1 tab with Spanish + English
3. Case File updates with severity, location, incident type
4. Response Lanes show EMS and Traffic Control as "Recommended"
5. Click APPROVE → lanes change to "Confirmed"
6. Caller 2 arrives → severity escalates → UI flashes
7. CCTV panel shows fire detection → red flash
8. Final summary displays

**Gate:** Full 120-second demo runs without errors. All panels update in real time. No stale state.

---

### PHASE 8: Polish + Rehearse (60 min)

**Build:** Animations, transitions, sound effects, loading states, error boundaries.

**Test (`test_phase7_e2e.py`):**
```python
"""
Full end-to-end timing test.
Start demo, let it run to completion, verify final state.
"""
import pytest
import httpx
import asyncio
import time

BASE = "http://localhost:8000/api/v1"

@pytest.mark.asyncio
async def test_full_demo_run():
    async with httpx.AsyncClient(timeout=180.0) as client:
        # Start
        t = time.time()
        r = await client.post(f"{BASE}/demo/start")
        assert r.status_code == 200

        # Auto-approve after 20s
        await asyncio.sleep(20)
        await client.post(f"{BASE}/demo/approve")

        # Wait for completion (total ~120s)
        for _ in range(24):  # Check every 5s for up to 2 min
            await asyncio.sleep(5)
            r = await client.get(f"{BASE}/demo/status")
            state = r.json()
            if state.get("status") == "resolved_demo":
                break

        total_time = time.time() - t
        state = (await client.get(f"{BASE}/demo/status")).json()

        # Final state assertions
        assert state["status"] == "resolved_demo"
        assert state["severity"] == "critical"
        assert state["caller_count"] >= 2
        assert "engine_fire" in state["hazard_flags"]
        assert len(state["recommended_units"]) >= 3
        assert state["action_plan_version"] >= 3
        assert state["operator_summary"] is not None
        assert len(state["timeline"]) >= 8

        print(f"\n=== FULL DEMO COMPLETE ===")
        print(f"Total time: {total_time:.1f}s")
        print(f"Severity: {state['severity']}")
        print(f"Callers: {state['caller_count']}")
        print(f"Timeline events: {len(state['timeline'])}")
        print(f"Action plan version: {state['action_plan_version']}")
        print(f"Units recommended: {state['recommended_units']}")
        print(f"Hazards: {state['hazard_flags']}")
```

**Gate:** Full demo completes in ~120s. Final state has severity=critical, 3+ units, 3+ action plan versions, engine_fire in hazards, operator_summary populated.

---

## 16. Demo Day Checklist

```
□ Run GET /health 3 times to warm API connections
□ Run test_phase7_e2e.py once — full demo completes
□ Check Supabase Realtime is enabled on all 4 tables
□ Verify CCTV video file plays correctly
□ Verify all 3 caller audio files are present
□ Test APPROVE button works (doesn't auto-timeout)
□ Check Wi-Fi signal strength. Have mobile hotspot ready.
□ Clear all test data from Supabase before live demo
□ Open browser to dashboard, dark mode, full screen
□ Take a breath. You built this. It works. Ship it.
```

---

## 17. Latency Budget Summary

| Path | Target | Max | Notes |
|------|--------|-----|-------|
| Caller → Transcription | 500ms | 2s | ElevenLabs Scribe |
| Transcription → Intake Facts | 1.5s | 3s | Mistral structured output |
| Triage Classification | 2s | 4s | Mistral Large + tools |
| Vision Frame Analysis | 2s | 3s | Pixtral single frame |
| TTS Generation (first byte) | 400ms | 800ms | ElevenLabs Turbo |
| Supabase Write | 50ms | 200ms | Single row upsert |
| **Supabase → Frontend (Realtime)** | **50ms** | **200ms** | **This is the magic. This is why we use Supabase.** |

---

*TriageNet Technical PRD v1.0 — Built for Claude Code — February 2026*