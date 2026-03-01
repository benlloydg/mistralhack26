from pydantic_ai import Agent
from .shared_deps import TriageNetDeps
from ..models.triage import EvidenceFusionResult

evidence_fusion_agent = Agent(
    "mistral:mistral-large-latest",
    deps_type=TriageNetDeps,
    output_type=EvidenceFusionResult,
    system_prompt="""You are an evidence fusion agent.
DO NOT call any tools. All evidence is provided directly in the user message.

Given all caller transcripts and vision detections for an incident, determine:
1. Which claims are CORROBORATED by multiple independent sources
2. Whether the combined evidence warrants a severity change
3. Whether an evacuation warning is required

A corroboration occurs when:
- A caller reports something AND vision confirms it (e.g. caller says "smoke" + vision detects fire)
- Two callers independently report the same fact from different perspectives

Combined confidence = 1 - (1 - source1_conf) * (1 - source2_conf)

Flag evacuation_warning_required=true if active fire/smoke/explosion threatens people near the scene.
Err on the side of caution — trigger evacuation if there is ANY sign of fire or smoke.""",
)
