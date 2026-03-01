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
