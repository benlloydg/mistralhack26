"""
Vision agent uses the native mistralai client directly because
Pydantic-AI doesn't support Mistral's multimodal content-array format.

Uses pixtral-large-latest for image understanding.
"""
import base64
import json
from ..models.vision import FrameAnalysis, VisionDetection
from ..config import settings
from mistralai import Mistral

VISION_SYSTEM_PROMPT = """You are a CCTV scene analysis agent for an emergency dispatch system.
Analyze the provided frame from a traffic/security camera.

You MUST return a JSON object with EXACTLY this structure — no other keys:
{
  "detections": [
    {"type": "vehicle_collision", "confidence": 0.95},
    {"type": "smoke", "confidence": 0.8}
  ],
  "overall_description": "One-line scene summary describing what you see",
  "hazard_escalation": "engine_fire or smoke or null",
  "smoke_visible": true,
  "fire_visible": false,
  "vehicle_damage_severity": "severe"
}

Detection types: vehicle_collision, smoke, engine_fire, persons_visible, debris, hazmat
vehicle_damage_severity: none | minor | moderate | severe
hazard_escalation: null unless you see a NEW hazard (smoke, engine_fire, explosion)

If the image contains text overlays (e.g. "SMOKE DETECTED"), treat those as the scene description.
Always include at least one detection. Always include overall_description."""


async def analyze_frame(
    mistral_client: Mistral,
    frame_bytes: bytes,
    frame_id: int,
) -> FrameAnalysis:
    """Send a frame to Pixtral for scene analysis. Returns typed FrameAnalysis."""
    b64 = base64.b64encode(frame_bytes).decode("utf-8")

    response = await mistral_client.chat.complete_async(
        model=settings.mistral_vision_model,
        messages=[
            {"role": "system", "content": VISION_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": f"Analyze CCTV frame #{frame_id}. Return the JSON object only."},
                    {"type": "image_url", "image_url": f"data:image/jpeg;base64,{b64}"},
                ],
            },
        ],
        response_format={"type": "json_object"},
    )

    raw = json.loads(response.choices[0].message.content)
    raw["frame_id"] = frame_id

    # Normalize detections if model returned a different shape
    if "detections" not in raw:
        detections = []
        if raw.get("smoke_visible") or "smoke" in raw.get("message", "").lower():
            detections.append({"type": "smoke", "confidence": 0.85})
        if raw.get("fire_visible") or "fire" in raw.get("message", "").lower():
            detections.append({"type": "engine_fire", "confidence": 0.92})
        if not detections:
            detections.append({"type": "scene", "confidence": 0.5})
        raw["detections"] = detections

    if "overall_description" not in raw:
        raw["overall_description"] = raw.get("message", raw.get("details", {}).get("alert", "CCTV frame analyzed"))

    # Ensure boolean fields
    desc_lower = raw.get("overall_description", "").lower()
    raw.setdefault("smoke_visible", "smoke" in desc_lower)
    raw.setdefault("fire_visible", "fire" in desc_lower)
    raw.setdefault("vehicle_damage_severity", "none")

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
