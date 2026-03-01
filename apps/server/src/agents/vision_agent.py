"""
Vision agent uses the native mistralai client directly because
Pydantic-AI doesn't support Mistral's multimodal content-array format.
"""
import base64
import json
from ..models.vision import FrameAnalysis
from ..config import settings
from mistralai import Mistral

VISION_SYSTEM_PROMPT = """You are a CCTV scene analysis agent. Analyze the provided frame from a traffic camera.

Detect and report:
- Vehicle damage (none | minor | moderate | severe)
- Persons visible (count)
- Smoke visible (true/false)
- Fire visible (true/false)
- Any other hazards

Return a JSON object matching this exact schema:
{
  "frame_id": <int>,
  "detections": [{"type": "<string>", "confidence": <float 0-1>}],
  "overall_description": "<one-line summary>",
  "hazard_escalation": "<new hazard type or null>",
  "smoke_visible": <bool>,
  "fire_visible": <bool>,
  "vehicle_damage_severity": "<none|minor|moderate|severe>"
}"""


async def analyze_frame(
    mistral_client: Mistral,
    frame_bytes: bytes,
    frame_id: int,
) -> FrameAnalysis:
    """Send a frame to Pixtral for scene analysis. Returns typed FrameAnalysis."""
    b64 = base64.b64encode(frame_bytes).decode("utf-8")

    response = mistral_client.chat.complete(
        model=settings.mistral_vision_model,
        messages=[{
            "role": "user",
            "content": [
                {"type": "text", "text": f"Frame #{frame_id}. Analyze this CCTV frame. Return JSON only."},
                {"type": "image_url", "image_url": f"data:image/jpeg;base64,{b64}"},
            ],
        }],
        response_format={"type": "json_object"},
    )

    raw = json.loads(response.choices[0].message.content)
    raw["frame_id"] = frame_id
    return FrameAnalysis(**raw)


def compute_scene_delta(prev: FrameAnalysis | None, curr: FrameAnalysis) -> dict:
    """Compare consecutive frames. Returns delta info for state updates."""
    if prev is None:
        return {"new_hazard": None, "hazard_escalation": False}

    new_hazard = None
    if curr.fire_visible and not prev.fire_visible:
        new_hazard = "engine_fire"
    elif curr.smoke_visible and not prev.smoke_visible:
        new_hazard = "smoke"

    return {
        "new_hazard": new_hazard,
        "hazard_escalation": new_hazard is not None,
        "description": f"Scene delta: {prev.overall_description} → {curr.overall_description}",
    }
