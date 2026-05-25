"""
agent.py
Handles LLM interaction: builds the system prompt from the knowledge base,
maintains conversation history, and calls the local Ollama model.

Falls back to a stub response if Ollama is unreachable, so the rest of
the pipeline can still be tested without a local LLM running.
"""

import json
import os
from pathlib import Path

import httpx
from fastapi import HTTPException

import asyncio

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "mistral")

# Load knowledge base once at import time
_KB_PATH = Path(__file__).parent / "dealership.json"
_KB: dict = json.loads(_KB_PATH.read_text())


async def _warmup():
    try:
        await chat([{"role": "user", "content": "hi"}])
        print("✓ Ollama warmed up")
    except Exception:
        pass

asyncio.ensure_future(_warmup())

def _build_system_prompt() -> str:
    d = _KB["dealership"]
    inventory_lines = "\n".join(
        f"  - {v['model']} ({v['year']}) — €{v['price_eur']:,} — {v['fuel']} — "
        f"{'In stock' if v['available'] else 'Order only'}"
        for v in _KB["inventory"]
    )
    faq_lines = "\n".join(
        f"  Q: {f['q']}\n  A: {f['a']}" for f in _KB["faqs"]
    )

    return f"""You are Alex, a friendly and professional voice assistant for {d['name']}, \
an authorised {' and '.join(d['brands'])} dealership in Madrid.

Your job is to help customers with questions about inventory, test drives, \
financing, opening hours, and general dealership enquiries.

IMPORTANT RULES:
- This is a VOICE interface. Keep every response to 2–3 short sentences maximum.
- Never make up prices, availability, or policies — only use the information below.
- If you cannot answer, say: "Let me connect you with one of our team members who can help."
- Respond in the same language the customer uses.
- Be warm and helpful, not salesy.

DEALERSHIP INFORMATION:
  Name:    {d['name']}
  Brands:  {', '.join(d['brands'])}
  Hours:   {d['hours']}
  Address: {d['address']}
  Phone:   {d['phone']}
  Email:   {d['email']}

CURRENT INVENTORY:
{inventory_lines}

FREQUENTLY ASKED QUESTIONS:
{faq_lines}
"""


# Build system prompt once
SYSTEM_PROMPT = _build_system_prompt()


async def chat(messages: list[dict]) -> str:
    """
    Send conversation history to the local Ollama model and return the reply.
    `messages` is a list of {"role": "user"|"assistant", "content": "..."} dicts.
    The system prompt is prepended automatically.
    """
    payload = {
        "model": OLLAMA_MODEL,
        "messages": [{"role": "system", "content": SYSTEM_PROMPT}] + messages,
        "stream": False,
        "options": {
            "temperature": 0.4,   # low = more consistent, less hallucination
            "num_predict": 120,   # keep responses short for voice
        },
    }

    try:
        async with httpx.AsyncClient(timeout=120) as client:
            response = await client.post(
                f"{OLLAMA_URL}/api/chat",
                json=payload,
            )
        if response.status_code != 200:
            raise HTTPException(
                status_code=502,
                detail=f"Ollama error {response.status_code}: {response.text}",
            )
        data = response.json()
        return data["message"]["content"].strip()

    except httpx.ConnectError:
        # Graceful fallback so the pipeline can still be demoed without Ollama
        return (
            "I'm sorry, our AI assistant is temporarily unavailable. "
            "Please call us at +34 91 000 0000 and one of our team will be happy to help."
        )
