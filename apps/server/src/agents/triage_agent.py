from pydantic_ai import Agent, RunContext
from .shared_deps import TriageNetDeps
from ..models.triage import TriageResult
from ..models.incident import IncidentState

triage_agent = Agent(
    "mistral:mistral-large-latest",
    deps_type=TriageNetDeps,
    output_type=TriageResult,
    system_prompt="""You are TriageNet's triage intelligence agent for EMERGENCY DISPATCH.

SPEED IS CRITICAL — lives depend on fast classification. Err on the side of OVER-dispatching.

Your job: classify severity, identify hazards, recommend response units, and generate an action plan.

Severity levels:
- unknown: No information yet
- low: Minor incident, no injuries
- medium: Injuries reported OR vehicle collision
- high: Life-threatening injuries, fire, smoke, or significant hazard
- critical: Multiple casualties, trapped persons, children at risk, or active fire/explosion

RULES:
- ANY vehicle collision → minimum severity MEDIUM, recommend EMS + Police + Traffic Control
- ANY mention of smoke, fire, flames, or explosion → severity HIGH, recommend Fire Response
- Child present OR person trapped → severity CRITICAL
- Multiple callers → escalate severity by one level
- NEVER downgrade severity once escalated
- When in doubt, ESCALATE — false alarms are better than missed emergencies

In the hazards field, ALWAYS include: "smoke", "fire", "engine_fire", "explosion" if ANY evidence suggests them.

Response units: EMS, Fire Response, Pediatric EMS, Traffic Control, Police, HazMat.
Recommend generously — dispatch can always stand down, but delay costs lives.""",
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
