"""
main.py
FastAPI backend for the AutoPrime voice agent.

Endpoints:
  POST /transcribe  — audio bytes → transcript text (ElevenLabs STT)
  POST /chat        — transcript + history → LLM reply text (Ollama)
  POST /speak       — text → MP3 audio bytes (ElevenLabs TTS)
  POST /conversation — full pipeline in one call (STT → LLM → TTS)
  GET  /health      — sanity check
"""
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel
from contextlib import asynccontextmanager

import agent
import elevenlabs_client as el

@asynccontextmanager
async def lifespan(app):
    await agent._warmup()
    yield

app = FastAPI(
    title="AutoPrime Voice Agent",
    lifespan=lifespan,
)

# Allow the HTML frontend (served from a different port in dev) to call the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # tighten this in production
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Request / Response models ─────────────────────────────────────────────────

class ChatRequest(BaseModel):
    messages: list[dict]
    """
    Full conversation history as a list of:
      {"role": "user"|"assistant", "content": "..."}
    The latest user message should be the last item.
    """

class ChatResponse(BaseModel):
    reply: str

class TranscriptResponse(BaseModel):
    transcript: str


# ── Endpoints ─────────────────────────────────────────────────────────────────

@app.get("/health")
async def health():
    return {"status": "ok", "agent": agent.OLLAMA_MODEL}


@app.post("/transcribe", response_model=TranscriptResponse)
async def transcribe(audio: UploadFile = File(...)):
    """
    Accepts an audio file (webm/mp3/wav) and returns the transcript.
    The browser records in audio/webm by default.
    """
    audio_bytes = await audio.read()
    if not audio_bytes:
        raise HTTPException(status_code=400, detail="Empty audio file")

    transcript = await el.transcribe(audio_bytes, mime_type=audio.content_type or "audio/webm")
    return {"transcript": transcript}


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Accepts conversation history and returns the agent's next reply.
    The caller is responsible for appending the reply to history client-side.
    """
    if not request.messages:
        raise HTTPException(status_code=400, detail="messages list is empty")

    reply = await agent.chat(request.messages)
    return {"reply": reply}


@app.post("/speak")
async def speak(request: ChatResponse):
    """
    Accepts a text string and returns MP3 audio bytes.
    Re-uses ChatResponse model (field: reply) to keep the client simple.
    """
    if not request.reply.strip():
        raise HTTPException(status_code=400, detail="reply text is empty")

    audio_bytes = await el.synthesise(request.reply)
    return Response(content=audio_bytes, media_type="audio/mpeg")


@app.post("/conversation")
async def conversation(
    audio: UploadFile = File(...),
    history: str = "",   # JSON-encoded list[dict], passed as form field
):
    """
    Full pipeline in a single HTTP call:
      1. Transcribe uploaded audio (ElevenLabs STT)
      2. Generate reply (Ollama LLM)
      3. Synthesise reply (ElevenLabs TTS)

    Returns JSON with transcript + reply text, plus the MP3 audio as a
    base64-encoded field so the browser can play it without a second request.

    `history` is a JSON string: '[{"role":"user","content":"..."},...]'
    The latest user turn is appended from the transcript automatically.
    """
    import json, base64

    # Step 1 — STT
    audio_bytes = await audio.read()
    transcript = await el.transcribe(audio_bytes, mime_type=audio.content_type or "audio/webm")

    # Step 2 — LLM
    try:
        messages = json.loads(history) if history else []
    except json.JSONDecodeError:
        messages = []

    messages.append({"role": "user", "content": transcript})
    reply = await agent.chat(messages)

    # Step 3 — TTS
    mp3_bytes = await el.synthesise(reply)

    return {
        "transcript": transcript,
        "reply": reply,
        "audio_b64": base64.b64encode(mp3_bytes).decode(),
    }
