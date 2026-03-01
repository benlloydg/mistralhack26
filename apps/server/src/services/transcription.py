"""
Wraps ElevenLabs transcription API and Mistral translation.
For the demo, we transcribe pre-recorded audio files.
"""
import httpx
from mistralai import Mistral
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


async def translate_to_english(
    text: str,
    source_language: str,
    mistral_client: Mistral,
) -> str:
    """
    Translate text to English using Mistral. Returns the English translation.
    If source_language is already 'en', returns the text unchanged.
    """
    if source_language == "en":
        return text

    response = await mistral_client.chat.complete_async(
        model=settings.mistral_triage_model,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a precise translator. Translate the following text to English. "
                    "Return ONLY the English translation, no explanation or preamble."
                ),
            },
            {
                "role": "user",
                "content": f"Translate from {source_language} to English:\n\n{text}",
            },
        ],
        max_tokens=500,
    )
    return response.choices[0].message.content.strip()
