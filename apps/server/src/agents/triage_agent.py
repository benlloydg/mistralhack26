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
