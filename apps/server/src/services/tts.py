"""
Wraps ElevenLabs TTS API for generating voice responses and dispatch briefs.

Two voice maps:
- CALLER_VOICE_MAP: Voices used to generate inbound caller audio (used by media asset generation)
- DISPATCH_VOICE_MAP: Voices used for operator/dispatch responses — intentionally different
  so the response doesn't sound like the same person calling back.
"""
import os
import httpx
from ..config import settings

ELEVENLABS_TTS_URL = "https://api.elevenlabs.io/v1/text-to-speech"

# Caller voices — used for generating inbound caller audio
CALLER_VOICE_MAP = {
    "es": "pFZP5JQG7iQjIQuC4Bku",  # Lily (Spanish female) — The Wife
    "zh": "nPczCjzI2devNBz1zQrb",  # Brian (Chinese) — The Bystander
    "fr": "XB0fDUnXU5powFXDhCwa",  # Charlotte (French) — The Shopkeeper
    "en": "JBFqnCBsd6RMkjVDRZzb",  # George (English) — default
}

# Dispatch/operator voices — different from callers so responses sound like a dispatcher
DISPATCH_VOICE_MAP = {
    "es": "ErXwobaYiN019PkySvjV",  # Antoni — dispatch operator for Spanish callers
    "zh": "JBFqnCBsd6RMkjVDRZzb",  # George — dispatch operator for Chinese callers
    "fr": "21m00Tcm4TlvDq8ikWAM",  # Rachel — dispatch operator for French callers
    "en": "JBFqnCBsd6RMkjVDRZzb",  # George — English dispatch
}

# Legacy alias
VOICE_MAP = CALLER_VOICE_MAP

GENERATED_AUDIO_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "assets", "generated")


async def generate_speech(text: str, language: str = "en", dispatch: bool = False) -> bytes:
    """
    Generate speech audio from text. Returns MP3 bytes.

    Args:
        text: Text to convert to speech.
        language: Language code (en, es, zh, fr).
        dispatch: If True, use the dispatch operator voice (different from caller voice).
    """
    voice_map = DISPATCH_VOICE_MAP if dispatch else CALLER_VOICE_MAP
    voice_id = voice_map.get(language, voice_map["en"])
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


async def generate_and_save(text: str, language: str, filename: str) -> str:
    """
    Generate dispatch speech and save to assets/generated/{filename}.
    Returns the URL path for the frontend to fetch.
    """
    os.makedirs(GENERATED_AUDIO_DIR, exist_ok=True)
    audio_bytes = await generate_speech(text, language, dispatch=True)
    filepath = os.path.join(GENERATED_AUDIO_DIR, filename)
    with open(filepath, "wb") as f:
        f.write(audio_bytes)
    return f"/audio/{filename}"
