"""
Wraps ElevenLabs TTS API for generating voice responses and dispatch briefs.
"""
import httpx
from ..config import settings

ELEVENLABS_TTS_URL = "https://api.elevenlabs.io/v1/text-to-speech"

# Voice IDs — configure per language. Use ElevenLabs preset voices or clone.
VOICE_MAP = {
    "es": "pFZP5JQG7iQjIQuC4Bku",  # Spanish female voice (Lily)
    "zh": "nPczCjzI2devNBz1zQrb",  # Chinese voice (Brian)
    "fr": "XB0fDUnXU5powFXDhCwa",  # French voice (Charlotte)
    "en": "JBFqnCBsd6RMkjVDRZzb",  # English dispatch voice (George)
}


async def generate_speech(text: str, language: str = "en") -> bytes:
    """
    Generate speech audio from text. Returns MP3 bytes.
    """
    voice_id = VOICE_MAP.get(language, VOICE_MAP["en"])
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{ELEVENLABS_TTS_URL}/{voice_id}",
            headers={
                "xi-api-key": settings.elevenlabs_api_key,
                "Content-Type": "application/json",
            },
            json={
                "text": text,
                "model_id": "eleven_turbo_v2_5",
                "voice_settings": {
                    "stability": 0.7,
                    "similarity_boost": 0.8,
                },
            },
        )
        response.raise_for_status()
        return response.content
