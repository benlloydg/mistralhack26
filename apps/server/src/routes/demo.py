import os
import shutil
import time
from datetime import datetime, timezone

from fastapi import APIRouter, BackgroundTasks
from ..services.orchestrator import DemoOrchestrator, detect_video
from ..services.state import StateManager
from ..services.tts import GENERATED_AUDIO_DIR
from ..agents.shared_deps import TriageNetDeps
from ..deps import get_supabase, get_mistral
from ..config import settings

router = APIRouter(prefix="/demo", tags=["demo"])

# Module-level reference to active demo
_active_orchestrator: DemoOrchestrator | None = None
_active_case_id: str | None = None


def _generate_case_id() -> str:
    """Generate a unique case ID: TN-YYYYMMDD-HHMMSS."""
    now = datetime.now(timezone.utc)
    return f"TN-{now.strftime('%Y%m%d')}-{now.strftime('%H%M%S')}"


@router.post("/start")
async def start_demo(background_tasks: BackgroundTasks):
    """Create a new case and start the event-driven demo. Previous runs are preserved."""
    global _active_orchestrator, _active_case_id
    supabase = get_supabase()
    mistral = get_mistral()
    start_time = time.time()

    case_id = _generate_case_id()
    _active_case_id = case_id

    # Clean generated audio from previous run (audio files are ephemeral)
    if os.path.exists(GENERATED_AUDIO_DIR):
        shutil.rmtree(GENERATED_AUDIO_DIR)

    # Create new incident_state row — previous runs stay in the DB
    supabase.table("incident_state").insert({
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

    # Create demo_control row for frontend coordination
    supabase.table("demo_control").insert({
        "case_id": case_id,
        "status": "starting",
        "approve_enabled": False,
        "approve_clicked": False,
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

    # Detect video so frontend can play the same file
    video_path = detect_video()
    # Cache-bust so browser always fetches the latest video file
    video_url = f"http://localhost:8000/assets/{os.path.basename(video_path)}?t={int(time.time())}" if video_path else None

    return {"case_id": case_id, "status": "started", "video_url": video_url}


@router.post("/feed")
async def start_feed():
    """Frontend signals that video playback has started. Unblocks audio streaming + vision."""
    if _active_orchestrator:
        _active_orchestrator.begin_feed()
        return {"status": "feed_started", "case_id": _active_case_id}
    return {"status": "no_active_demo"}


@router.post("/approve")
async def approve_response():
    """Operator approves dispatch. Unblocks dispatch generation in orchestrator."""
    if _active_orchestrator:
        _active_orchestrator.approve()
        # Update demo_control
        if _active_case_id:
            try:
                supabase = get_supabase()
                supabase.table("demo_control").update({
                    "approve_clicked": True,
                }).eq("case_id", _active_case_id).execute()
            except Exception:
                pass
        return {"status": "approved", "case_id": _active_case_id}
    return {"status": "no_active_demo"}


@router.get("/status")
async def demo_status():
    """Get current active demo state."""
    if not _active_case_id:
        return {"status": "no_active_demo"}
    supabase = get_supabase()
    try:
        result = supabase.table("incident_state") \
            .select("*").eq("case_id", _active_case_id).single().execute()
        return result.data
    except Exception:
        return {"status": "no_demo_found"}


@router.get("/cases")
async def list_cases():
    """List all past demo runs, newest first."""
    supabase = get_supabase()
    result = supabase.table("incident_state") \
        .select("case_id, status, severity, created_at, updated_at") \
        .order("created_at", desc=True) \
        .execute()
    return {"cases": result.data, "active_case_id": _active_case_id}


@router.get("/cases/{case_id}")
async def get_case_report(case_id: str):
    """Full case report — incident state, logs, transcripts, dispatches."""
    supabase = get_supabase()
    state = supabase.table("incident_state") \
        .select("*").eq("case_id", case_id).single().execute()
    logs = supabase.table("agent_logs") \
        .select("*").eq("case_id", case_id) \
        .order("created_at").execute()
    transcripts = supabase.table("transcripts") \
        .select("*").eq("case_id", case_id) \
        .order("created_at").execute()
    dispatches = supabase.table("dispatches") \
        .select("*").eq("case_id", case_id) \
        .order("created_at").execute()
    return {
        "case_id": case_id,
        "incident_state": state.data,
        "agent_logs": logs.data,
        "transcripts": transcripts.data,
        "dispatches": dispatches.data,
    }


@router.post("/reset")
async def reset_demo():
    """Stop any active demo. Does NOT delete historical runs."""
    global _active_orchestrator, _active_case_id

    if _active_orchestrator:
        _active_orchestrator.cancel()

    # Update demo_control status
    if _active_case_id:
        try:
            supabase = get_supabase()
            supabase.table("demo_control").update({
                "status": "reset",
            }).eq("case_id", _active_case_id).execute()
        except Exception:
            pass

    _active_orchestrator = None
    old_case_id = _active_case_id
    _active_case_id = None
    # Clean generated audio (ephemeral)
    if os.path.exists(GENERATED_AUDIO_DIR):
        shutil.rmtree(GENERATED_AUDIO_DIR)
    return {"status": "reset", "previous_case_id": old_case_id}
