from fastapi import APIRouter, BackgroundTasks
from ..services.orchestrator import DemoOrchestrator
from ..services.state import StateManager
from ..agents.shared_deps import TriageNetDeps
from ..deps import get_supabase, get_mistral
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
    mistral = get_mistral()
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
    try:
        result = supabase.table("incident_state") \
            .select("*").eq("case_id", "TN-2026-00417").single().execute()
        return result.data
    except Exception:
        return {"status": "no_demo_found"}
