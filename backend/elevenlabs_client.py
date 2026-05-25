"""
elevenlabs_client.py
Thin wrappers around ElevenLabs STT (Scribe) and TTS endpoints.
All I/O is raw bytes so the FastAPI layer stays clean.
"""

import os
import httpx
from fastapi import HTTPException

ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "")
BASE_URL = "https://api.elevenlabs.io/v1"

# Voice ID to use for TTS.  "Rachel" is a warm, professional English voice
# available on the free tier.  Override via env var to try other voices.
# Browse voices at: https://elevenlabs.io/voice-library
VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "pNInz6obpgDQGcFmaJgB")

# TTS model — "eleven_multilingual_v2" supports ES/EN/DE/IT on free tier
TTS_MODEL = "eleven_multilingual_v2"

# STT model
STT_MODEL = "scribe_v1"


def _headers() -> dict:
    if not ELEVENLABS_API_KEY:
        raise HTTPException(status_code=500, detail="ELEVENLABS_API_KEY not set")
    return {"xi-api-key": ELEVENLABS_API_KEY}


async def transcribe(audio_bytes: bytes, mime_type: str = "audio/webm") -> str:
    """
    Send raw audio bytes to ElevenLabs Scribe STT.
    Returns the transcript as a string.
    """
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(
            f"{BASE_URL}/speech-to-text",
            headers=_headers(),
            files={"file": ("audio.webm", audio_bytes, mime_type)},
            data={"model_id": STT_MODEL},
        )

    if response.status_code != 200:
        raise HTTPException(
            status_code=502,
            detail=f"ElevenLabs STT error {response.status_code}: {response.text}",
        )

    data = response.json()
    return data.get("text", "").strip()


async def synthesise(text: str) -> bytes:
    """
    Send text to ElevenLabs TTS.
    Returns raw MP3 audio bytes.
    """
    payload = {
        "text": text,
        "model_id": TTS_MODEL,
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.75,
            "style": 0.0,
            "use_speaker_boost": True,
        },
    }

    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(
            f"{BASE_URL}/text-to-speech/{VOICE_ID}",
            headers={**_headers(), "Content-Type": "application/json"},
            json=payload,
        )

    if response.status_code != 200:
        raise HTTPException(
            status_code=502,
            detail=f"ElevenLabs TTS error {response.status_code}: {response.text}",
        )

    return response.content
