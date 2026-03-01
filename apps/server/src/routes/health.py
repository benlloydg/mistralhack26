from fastapi import APIRouter
from ..config import settings
from ..deps import get_supabase, get_mistral
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
        client = get_mistral()
        client.chat.complete(
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
