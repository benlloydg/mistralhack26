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
