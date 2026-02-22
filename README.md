# NEXUS — Conversation Intelligence API

Enterprise backend that analyzes customer support conversations (voice and text) using a two-layer compliance engine — deterministic keyword matching plus Gemini 2.5 Flash contextual reasoning — and returns structured JSON intelligence consumable by any frontend, mobile app, or dashboard.

## Overview

NEXUS is a domain-agnostic conversation intelligence API built for regulated industries. It accepts raw audio recordings or text transcripts, runs them through a hybrid AI + deterministic compliance pipeline, and returns a single structured JSON response covering sentiment analysis, entity extraction, compliance violations, agent performance scoring, and actionable recommendations. The system is configured entirely through JSON files — banking, insurance, telecom, or any new industry can be onboarded without code changes. Built with FastAPI and Google Gemini 2.5 Flash.

## Architecture

```
Request (audio/text + client_id)
              ↓
      ┌───────────────┐
      │   FastAPI      │ ← Pydantic validation, UUID assignment
      │   Phase 1      │
      └───────┬───────┘
              ↓
┌─────────────────────────────────┐
│  Phase 2: Gemini 2.5 Flash     │
│  Native multimodal analysis →  │
│  sentiment, entities, intent,  │
│  compliance, agent scoring     │
└─────────────┬───────────────────┘
              ↓
┌─────────────────────────────────┐
│  Phase 3: RAG Action Engine    │
│  Phase 2 JSON + domain rules → │
│  structured action plan,       │
│  policy justifications,        │
│  coaching recommendations      │
└─────────────┬───────────────────┘
              ↓
┌─────────────────────────────────┐
│  Phase 4: Deterministic Engine │
│  Layer 1: Keyword scan →       │
│     flags + policy citations   │
│  Layer 2: AI corroboration →   │
│     fallback when keywords     │
│     miss but AI flagged risk   │
└─────────────┬───────────────────┘
              ↓
    Structured JSON Response
    (all phases combined)
```

## AI Approach

NEXUS uses a **two-layer compliance system** designed for auditability in regulated environments:

### Layer 1 — Deterministic Keyword Engine (`core/compliance.py`)
- Scans raw transcript against configurable high-risk keywords
- Each keyword has a defined severity (`high`, `medium`, `low`) and policy reference
- Returns exact context line where keyword was found
- 20 built-in universal keywords covering legal threats, fraud, abuse, escalation requests
- Client configs can define additional domain-specific keywords
- Output is fully auditable: every flag traces back to a specific keyword, line, and policy

### Layer 2 — Gemini 2.5 Flash Multimodal Reasoning (`core/gemini.py`)
- Processes audio natively — no separate speech-to-text pipeline needed
- Domain knowledge and RAG policies injected directly into the prompt
- Extracts: sentiment arc, named entities, compliance violations, agent performance score (0-100)
- Phase 3 feeds Phase 2 output back into Gemini with compliance policies for structured action plans
- Uses `response_schema` parameter for schema-constrained JSON generation via Pydantic models

### Why Two Layers
Deterministic matching catches known violations with 100% recall — if "lawsuit" appears in the transcript, it is always flagged. LLM reasoning catches contextual violations that keywords miss — a customer saying "I'll take this further" is a veiled escalation threat that no keyword list covers. When deterministic finds nothing but AI has flagged HIGH/CRITICAL risk, Layer 2 synthesizes AI-corroborated flags so the output is never contradictory between phases.

## Supported Domains

| Domain | Config File | Regulatory Framework |
|--------|-------------|---------------------|
| Banking | `data/config/banking.json` | RBI Guidelines, PCI-DSS, Fraud Triggers |

New domains are added by creating two files — no code changes required (see Configuration Guide below).

## API Endpoints

### POST /api/v1/analyze/text
Analyze a text transcript.

**Request Body:**
```json
{
  "client_id": "banking",
  "transcript": "Customer: Hi, I lost my credit card today. I need to block it immediately before any fraudulent transactions happen."
}
```

**With inline metadata:**
```json
{
  "client_id": "banking",
  "transcript": "Agent: Namaste, main Suresh bol raha hoon...\nCustomer: Haan bataiye, kya hai?",
  "metadata": {
    "channel": "phone",
    "call_date": "2026-02-21",
    "agent_id": "AGT_042"
  }
}
```

### POST /api/v1/analyze/audio
Upload audio file for analysis.

```bash
curl -X POST http://localhost:8000/api/v1/analyze/audio \
  -F "audio_file=@sample_call.mp3" \
  -F "client_id=banking"
```

Supported formats: MP3, WAV, OGG, M4A, FLAC, AAC, WebM (max 25MB).

### POST /api/v1/analyze/json_rag
Feed Phase 2 JSON output through Phase 3 RAG independently.

```json
{
  "client_id": "banking",
  "analysis_data": { "...Phase 2 output..." }
}
```

### GET /health
Health check. Returns:
```json
{
  "status": "healthy",
  "service": "NEXUS Conversation Intelligence",
  "model": "gemini-2.5-flash",
  "version": "1.0.0"
}
```

## Configuration Guide

Add a new domain in 3 steps — zero code changes:

**Step 1** — Create `data/config/yourdomain.json`:
```json
{
  "business_domain": "insurance",
  "products_services": ["Term Life", "Health Insurance", "ULIPs"],
  "policies": ["Must disclose free look period.", "Cannot promise guaranteed returns on ULIPs."],
  "escalation_rules": {
    "high_risk_keywords": [
      {"keyword": "guaranteed returns", "severity": "high", "policy_reference": "IRDAI PPI Reg 15(1)"},
      {"keyword": "no risk", "severity": "high", "policy_reference": "IRDAI Mis-selling Guidelines"}
    ]
  }
}
```

**Step 2** — Create `data/domain_knowledge/yourdomain_rules.txt`:
```
IRDAI PPI Regulation 15(1): No insurance product shall be marketed with guaranteed return claims unless explicitly approved.
Mis-selling Guidelines: Agents must disclose all risks, charges, and the free look period during every sales call.
```

**Step 3** — Call the API with `"client_id": "yourdomain"`. Done.

If a `client_id` has no matching config, NEXUS falls back to a universal default configuration with generic risk triggers (`fraud`, `escalation`, `complaint`).

## Demo Transcript Files

Test the API immediately with these included files:

| File | Description |
|------|-------------|
| `sample_transcript.txt` | English e-commerce support call — customer upset about delayed ₹8,499 headset order, payment deducted but order stuck in "processing" |
| `sam.txt` | Hinglish insurance mis-selling call — agent promises "guaranteed 12% returns", dismisses free look period, uses pressure tactics |
| `sample_call.mp3` | Audio recording for testing the `/analyze/audio` endpoint |

## How To Run

```bash
pip install -r requirements.txt
python main.py
```

Select `[1]` to start the API server at `http://localhost:8000` (Swagger docs at `/docs`).
Select `[2]` to launch the interactive terminal tester.

**Environment setup:**
Create `.env` in the project root:
```
GEMINI_API_KEY=your_google_ai_studio_key
```

## Sample Output

Real output from NEXUS analyzing a banking fraud call:
```json
{
  "conversation_id": "551c717f-5ba4-4a06-86fc-677cdcbf3968",
  "client_id": "banking",
  "input_type": "text",
  "status": "completed",
  "processing_time_ms": 8265,
  "summary": "The customer reports a lost wallet and requests immediate blocking of their card. This is a critical security request requiring prompt action.",
  "language_detected": "en",
  "languages_all": ["en"],
  "sentiment": {
    "overall": "neutral",
    "customer_sentiment": "neutral",
    "agent_sentiment": "neutral",
    "emotional_arc": ["neutral_start"],
    "frustration_detected": false
  },
  "primary_intent": "block_card",
  "topics_discussed": ["card_security", "lost_items"],
  "entities": {
    "amounts_mentioned": [],
    "products_mentioned": ["card"],
    "people_mentioned": []
  },
  "compliance": {
    "violations_detected": [],
    "policies_checked": ["PCI-DSS Requirement", "Fraud Triggers"],
    "risk_level": "high",
    "escalation_required": false,
    "risk_flags": ["lost_wallet"]
  },
  "agent_performance": {
    "score": 0,
    "greeting_proper": false,
    "empathy_shown": false,
    "issue_resolved": false,
    "call_outcome": "dropped"
  },
  "rag_policies_used": [
    "PCI-DSS Requirement: Sensitive authentication data cannot be retained.",
    "Fraud Triggers: Flag any conversation where the customer mentions \"unauthorized transaction\", \"stolen card\", or \"hacked account\"."
  ],
  "deterministic_compliance": {
    "compliance_risk_score": 0.05,
    "total_flags": 1,
    "auto_escalate": true,
    "flags": [
      {
        "keyword": "fraud",
        "severity": "high",
        "context": "I need to block it immediately before any fraudulent transactions happen.",
        "policy_reference": "Fraud Reporting Policy",
        "action_required": true,
        "source": "deterministic"
      }
    ]
  }
}
```

## Features

- **Native multimodal** — Gemini processes audio directly, no STT pipeline
- **Multilingual** — Handles Hindi, English, Tamil, Hinglish code-switching natively
- **Multi-speaker diarization** — Detects and labels speakers (Agent, Customer)
- **Emotional arc tracking** — Timeline sentiment progression per conversation
- **Hybrid compliance** — Deterministic keyword scan + AI corroboration fallback
- **Domain-agnostic** — New industries added via JSON config only
- **Schema-validated** — All inputs/outputs validated through Pydantic v2

## Project Structure

```
nexus/
├── main.py                        # Entry point + launch menu
├── requirements.txt               # Dependencies
├── .env                           # GEMINI_API_KEY
├── api/
│   ├── models/
│   │   ├── request.py             # TextAnalysisRequest, JsonRagRequest
│   │   └── response.py            # ConversationAnalysisResult, RagActions, DeterministicCompliance
│   └── routes/
│       └── analyze.py             # 3 endpoints, 4-phase orchestration
├── core/
│   ├── gemini.py                  # Gemini 2.5 Flash integration (google.genai SDK)
│   └── compliance.py              # Hybrid deterministic engine (Layer 1 + Layer 2)
├── data/
│   ├── config/
│   │   └── banking.json           # Banking domain config
│   └── domain_knowledge/
│       └── banking_rules.txt      # PCI-DSS and fraud detection rules
├── test_interactive.py            # Interactive CLI tester (auto-starts server)
├── sample_transcript.txt          # E-commerce support call transcript
├── sam.txt                        # Insurance mis-selling Hinglish transcript
└── sample_call.mp3                # Audio test file
```

## Limitations & Future Improvements

| Current Limitation | Planned Improvement |
|--------------------|-------------------|
| Processing time ~8-15 seconds per request (Gemini API latency) | Async batch processing with job queue |
| Audio Phase 4 runs AI fallback only (no intermediate transcript for keyword scan) | Post-Gemini transcript extraction for full deterministic scan on audio |
| Free tier rate limits (15 RPM) | Production API key with higher quotas |
| File-based config storage | Database-backed config with admin API |
| No authentication middleware | OAuth2 / API key middleware |
| Single-request processing | WebSocket streaming for live call monitoring |
| No persistent storage of results | PostgreSQL result store with search |

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Backend | FastAPI (async, ASGI) |
| AI Engine | Google Gemini 2.5 Flash (`google.genai` SDK) |
| Compliance Engine | Custom hybrid deterministic + AI corroboration |
| Validation | Pydantic v2 |
| Server | Uvicorn |
| Configuration | File-based JSON + TXT per client |

## Team

Built at Transight Hackathon 2026
