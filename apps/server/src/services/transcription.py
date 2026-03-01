"""
Wraps ElevenLabs transcription API.
For the demo, we transcribe pre-recorded audio files.
"""
import httpx
from ..config import settings

ELEVENLABS_TRANSCRIBE_URL = "https://api.elevenlabs.io/v1/speech-to-text"


async def transcribe_audio(audio_path: str) -> dict:
    """
    Send audio file to ElevenLabs for transcription.
    Returns: {language_code: str, text: str, confidence: float}
    """
    async with httpx.AsyncClient(timeout=30.0) as client:
        with open(audio_path, "rb") as f:
            response = await client.post(
                ELEVENLABS_TRANSCRIBE_URL,
                headers={"xi-api-key": settings.elevenlabs_api_key},
                files={"file": (audio_path, f, "audio/mpeg")},
                data={"model_id": "scribe_v1"},
            )
        response.raise_for_status()
        data = response.json()
        return {
            "language_code": data.get("language_code", "unknown"),
            "text": data.get("text", ""),
            "confidence": data.get("confidence", 0.0),
        }
