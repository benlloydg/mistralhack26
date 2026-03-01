# Implementation Plan: After-Action Report (Backend)

**Branch**: `004-after-action-report` | **Date**: 2026-03-01 | **Spec**: `specs/004-after-action-report/spec.md`

## Summary

Add a pre-structured JSON report endpoint (`POST/GET /api/v1/cases/{case_id}/report`) that assembles all 8 report sections from existing Supabase tables, generates a Mistral executive summary (cached), and serves saved vision frames. The orchestrator is updated to persist extracted video frames to disk during the demo. This backend serves as the API contract for the frontend team (Gemini) building the report UI.

## Technical Context

**Language/Version**: Python 3.12, uv package manager
**Primary Dependencies**: FastAPI, pydantic, mistralai, supabase
**Storage**: Supabase (PostgreSQL + Realtime) — read-only for report; disk for frames
**Testing**: pytest + pytest-asyncio, timed steps
**Project Type**: Web service (backend API)
**Performance Goals**: <5s first report generation, <500ms cached
**Constraints**: No new DB tables; in-memory summary cache only

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Gate | Status | Notes |
|------|--------|-------|
| Spec-driven development | PASS | Ran /speckit.specify, now /speckit.plan |
| Pydantic-AI rules | PASS | No new agents — uses direct Mistral client for summary (same as translate_to_english) |
| Architecture pattern (agents → Supabase → frontend) | PASS | Report reads from Supabase, returns JSON for frontend |
| E2E testing with timestamps | WILL COMPLY | Test plan includes timed report generation |
| Simplicity / YAGNI | PASS | No new tables, no new agents, in-memory cache |

## Project Structure

### Documentation (this feature)

```text
specs/004-after-action-report/
├── spec.md
├── plan.md              # This file
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── report-api.md    # JSON API contract for frontend team
└── checklists/
    └── requirements.md
```

### Source Code Changes

```text
apps/server/src/
├── routes/
│   └── report.py          # MODIFY — add JSON report endpoints
├── services/
│   ├── orchestrator.py    # MODIFY — save frames to disk in _run_vision()
│   └── report_builder.py  # NEW — assembles all 8 report sections
├── models/
│   └── report.py          # NEW — Pydantic models for report response
└── main.py                # MODIFY — add /frames static mount

apps/server/assets/
└── frames/                # NEW directory — saved vision frame JPEGs
```

**Structure Decision**: Feature adds 2 new files (`report_builder.py`, `models/report.py`), modifies 3 existing files. No new packages or directories beyond `assets/frames/`.

## Files to Modify/Create

### NEW files:

| File | Purpose |
|------|---------|
| `apps/server/src/models/report.py` | Pydantic models: ReportData, ReportHeader, TimelineEntry, EvidenceSources, ConvergenceTrack, ResponseAction, AgentStats, KeyFrame |
| `apps/server/src/services/report_builder.py` | ReportBuilder class: queries Supabase, assembles all 8 sections, generates executive summary, caches result |

### MODIFIED files:

| File | Change |
|------|--------|
| `apps/server/src/routes/report.py` | Add `POST /api/v1/cases/{case_id}/report` and `GET /api/v1/cases/{case_id}/report` JSON endpoints |
| `apps/server/src/services/orchestrator.py` | In `_run_vision()`: save frame bytes to `assets/frames/{case_id}_t{ts}s.jpg` after extraction |
| `apps/server/src/main.py` | Add `/frames` static mount for `assets/frames/` directory |

### UNCHANGED files:

- All agents, models (except new report.py), deps, config, state, tts, media, scribe_realtime
- All existing routes (demo.py, health.py)
- Existing HTML report route (preserved as legacy)

## Detailed Design

### 1. `models/report.py` — Pydantic Models

Full response schema matching `contracts/report-api.md`. All models are Pydantic BaseModel with serialization support. See `data-model.md` for complete field definitions.

### 2. `report_builder.py` — Report Assembly

```
ReportBuilder
├── __init__(supabase, mistral_client)
├── build(case_id) → ReportData
│   ├── _build_header(state, transcripts, logs)
│   ├── _build_timeline(logs)
│   ├── _build_evidence_sources(transcripts, state)
│   ├── _build_convergence_tracks(logs, transcripts, state)
│   ├── _build_response_actions(dispatches, logs)
│   ├── _build_agent_stats(logs, state)
│   ├── _build_key_frames(case_id, state)
│   └── _generate_executive_summary(state, transcripts, dispatches)
└── _summary_cache: dict[str, str]  # case_id → summary text
```

Each `_build_*` method reads from the Supabase query results passed in — single batch of 4 queries at the top of `build()`.

Key implementation details:
- **Timeline**: Transform `agent_logs` rows → `TimelineEntry` objects. Map agent names to severity indicators: `evidence_fusion/CROSS_MODAL*` → critical, `orchestrator/approved` → operator, everything else → regular.
- **Convergence tracks**: Group `transcripts` by language → audio tracks. Extract vision events from `agent_logs` where agent="vision". Build fused track from triage state changes.
- **Agent stats**: Group `agent_logs` by agent, count rows, estimate latency from timestamp gaps.
- **Key frames**: Glob `assets/frames/{case_id}_*.jpg`, match with `vision_detections` from state, flag the fire detection frame as hero.
- **Executive summary**: Prompt Mistral Large with full state + transcript + dispatch context. Cache result.

### 3. `orchestrator.py` — Frame Saving

Two additions in `_run_vision()`:

```python
# After frame extraction, before vision analysis:
frame_path = f"assets/frames/{self.deps.case_id}_t{int(timestamp_s)}s.jpg"
os.makedirs("assets/frames", exist_ok=True)
with open(frame_path, "wb") as f:
    f.write(frame_bytes)
```

Added at both Frame 1 and Frame 2 extraction points. No other changes to orchestrator logic.

### 4. `main.py` — Static Mount

```python
FRAMES_DIR = os.path.join(os.path.dirname(__file__), "..", "assets", "frames")
os.makedirs(FRAMES_DIR, exist_ok=True)
app.mount("/frames", StaticFiles(directory=FRAMES_DIR), name="frames")
```

Same pattern as the existing `/audio` mount.

### 5. `routes/report.py` — New Endpoints

Add two new endpoints to the existing report router (keeping the legacy HTML route):

```python
@router.post("/api/v1/cases/{case_id}/report")
async def generate_report(case_id: str) -> dict:
    # Build report (includes Mistral summary generation on first call)
    builder = ReportBuilder(get_supabase(), get_mistral())
    report = await builder.build(case_id)
    return report.model_dump()

@router.get("/api/v1/cases/{case_id}/report")
async def get_report(case_id: str) -> dict:
    # Return cached report or 404
    ...
```

## Implementation Sequence

| Phase | Tasks | Files | Risk |
|-------|-------|-------|------|
| A. Models | Create Pydantic report models | `models/report.py` | Low |
| B. Frame saving | Update orchestrator + main.py mount | `orchestrator.py`, `main.py` | Low |
| C. Report builder | Create report assembly service | `report_builder.py` | Medium — most logic |
| D. Routes | Add JSON endpoints | `routes/report.py` | Low |
| E. Testing | E2E test with timing | `tests/` | Low |

## Verification

1. `uv run python -c "from src.models.report import ReportData; print('OK')"` — models import
2. Run a demo → verify `assets/frames/` contains JPEG files
3. `curl http://localhost:8000/frames/TN-..._t38s.jpg` → 200 with image/jpeg
4. `curl -X POST http://localhost:8000/api/v1/cases/TN-.../report | python -m json.tool` → full JSON with 8 sections
5. Second `curl` → faster response (cached summary)
6. `PYTHONPATH=. uv run pytest src/tests/ -v` → all tests pass
