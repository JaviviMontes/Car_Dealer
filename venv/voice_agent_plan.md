# Voice AI Support Agent — Automotive Dealership Demo
### Project plan for ElevenLabs SE interview demo

---

## Concept

A voice-first support agent for automotive dealerships. A customer calls or visits the dealership website, speaks naturally, and the agent answers questions about inventory, test drives, financing, and opening hours — in any language.

**Why this framing works in an interview:**
- Automotive is your domain. You can speak credibly about the customer.
- Enterprise dealership groups (multi-brand, multi-country) are a realistic ElevenLabs target customer.
- The multilingual angle (ES/DE/IT/EN) maps directly to your background and to ElevenLabs' strength.
- It's a *contained*, explainable use case — not a vague "AI chatbot."

---

## Revised Tech Stack

| Layer | Tool | Why |
|---|---|---|
| **STT** | ElevenLabs STT (Scribe) | Stays in ecosystem; shows product knowledge |
| **LLM** | Ollama + Mistral-7B (local) | Zero cost; fallback: Claude API |
| **TTS** | ElevenLabs TTS (free tier) | Core product; tune voice for use case |
| **Frontend** | Single HTML/JS page | No framework overhead; demo-friendly |
| **Backend** | FastAPI (Python) | Clean API layer; shows architecture thinking |
| **Config** | JSON knowledge base | Simulates dealership FAQ/inventory data |
| **Deployment** | Docker Compose | "One command" enterprise readiness signal |

> **Drop:** Whisper.cpp, Vosk, Streamlit, Coqui — these dilute the ElevenLabs focus and add complexity without value.

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                   Browser (HTML/JS)                  │
│  [🎙 Hold to speak]  →  audio blob  →  /transcribe  │
│  ←  audio playback  ←  /speak  ←  text response     │
└─────────────────────────────────────────────────────┘
                          │
                    FastAPI Backend
                          │
         ┌────────────────┼────────────────┐
         ▼                ▼                ▼
  ElevenLabs STT    Ollama LLM       ElevenLabs TTS
   (Scribe API)   (Mistral-7B)      (free-tier API)
                          │
                   dealership.json
                 (KB: inventory, FAQs,
                  hours, financing)
```

---

## MVP Scope (1–2 evenings)

### Phase 1 — Core loop (~3–4 hours)
- [ ] FastAPI app with `/transcribe`, `/chat`, `/speak` endpoints
- [ ] ElevenLabs STT: send audio blob → get transcript
- [ ] Ollama LLM: send transcript + system prompt → get response
- [ ] ElevenLabs TTS: send response text → get audio → stream back
- [ ] `dealership.json` knowledge base (10–15 Q&A pairs)
- [ ] System prompt that gives the agent its persona and KB context

### Phase 2 — Frontend (~1–2 hours)
- [ ] Single HTML page: hold-to-talk button, transcript display, audio playback
- [ ] Show conversation history (user + agent turns)
- [ ] Dealership branding (logo placeholder, brand colours)

### Phase 3 — Polish for demo (~1 hour)
- [ ] Choose and tune an ElevenLabs voice (warm, professional — not robotic)
- [ ] Add language selector (ES / EN / DE / IT) — single prompt change
- [ ] `README.md` with architecture diagram + setup instructions
- [ ] `docker-compose.yml` for one-command startup
- [ ] Record a 60-second demo GIF

---

## Knowledge Base Structure (`dealership.json`)

```json
{
  "dealership": {
    "name": "AutoPrime Madrid",
    "brands": ["BMW", "MINI"],
    "hours": "Mon–Fri 9:00–19:00, Sat 10:00–14:00",
    "address": "Calle de Serrano 45, Madrid",
    "phone": "+34 91 000 0000"
  },
  "inventory": [
    { "model": "BMW 3 Series", "year": 2024, "price_eur": 45900, "available": true },
    { "model": "BMW X5", "year": 2024, "price_eur": 78500, "available": true },
    { "model": "MINI Cooper S", "year": 2024, "price_eur": 32400, "available": false }
  ],
  "faqs": [
    { "q": "Can I book a test drive?", "a": "Yes, test drives available Mon–Sat. Book via phone or ask me to schedule one." },
    { "q": "Do you offer financing?", "a": "Yes, BMW Financial Services with 0% APR on selected models through June 2025." },
    { "q": "Do you buy used cars?", "a": "Yes, we offer trade-in valuations. Bring your vehicle any weekday." }
  ]
}
```

---

## System Prompt

```
You are Alex, a friendly and professional voice assistant for AutoPrime Madrid,
an authorised BMW and MINI dealership. You help customers with questions about
inventory, test drives, financing, opening hours, and general enquiries.

Keep responses concise — this is a voice interface, so 2–3 sentences maximum.
Never make up prices or availability; only use the information provided.
If you cannot answer, offer to connect the customer with a human agent.

Respond in the same language the customer uses.
```

> The last line gives you multilingual support for free — no extra engineering needed.

---

## What to Say in the Interview

When demoing, frame it like a sales engineer would:

> *"This is a minimal proof-of-concept for a dealership group looking to automate first-line customer support. The full loop — speech in, AI response, speech out — runs in under 3 seconds. The voice is tuned for the brand. It handles Spanish, English, German and Italian with no code changes. The architecture is modular: swap the LLM for GPT-4, add a CRM integration, or deploy it on-premise — it's the same API surface."*

That's the SE mindset: you're not showing off code, you're selling a solution.

---

## File Structure

```
voice-agent-dealership/
├── backend/
│   ├── main.py              # FastAPI app
│   ├── agent.py             # LLM logic + KB injection
│   ├── elevenlabs_client.py # STT + TTS wrappers
│   └── dealership.json      # Knowledge base
├── frontend/
│   └── index.html           # Single-page UI
├── docker-compose.yml
├── requirements.txt
├── .env.example             # ELEVENLABS_API_KEY placeholder
└── README.md
```

---

## Cost Estimate

| Service | Free tier | Expected demo usage |
|---|---|---|
| ElevenLabs TTS | 10,000 chars/month | ~500 chars per full demo run |
| ElevenLabs STT | Included in free tier | ~20 short utterances |
| Ollama / Mistral | Free, runs locally | No cloud cost |

**Total: €0** for development and interview demo.

---

## Next Steps

1. Set up project folder and install dependencies
2. Build and test the three FastAPI endpoints
3. Wire up the HTML frontend
4. Load the KB and tune the system prompt
5. Pick your ElevenLabs voice and run a full loop test
6. Polish, README, Docker, demo GIF
