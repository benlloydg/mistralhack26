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
