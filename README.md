# VAJRA — Multimodal Conversation Intelligence API

> **V**oice and **A**udio to **J**SON **R**easoning **A**gent  
> Powered by **Gemini 2.5 Flash** | Built for the Transight Hackathon

---

## What is VAJRA?

VAJRA is a backend-only, API-first enterprise conversation intelligence system that analyzes customer support calls — either as **audio recordings** or **text transcripts** — and returns deep, structured insights: sentiment, intent, compliance violations, agent performance scores, and automated action recommendations.

No traditional speech-to-text pipeline. No language preprocessing. **Gemini 2.5 Flash handles everything natively.**

---

## Architecture Overview

```
                         ┌─────────────────────────────────────┐
                         │           CLIENT APPLICATION         │
                         │    (Mobile App / Web Dashboard)      │
                         └──────────────┬──────────────────────┘
                                        │ HTTP POST
                                        ▼
                         ┌─────────────────────────────────────┐
                         │         FastAPI Backend              │
                         │    /api/v1/analyze/audio             │
                         │    /api/v1/analyze/text              │
                         │    /api/v1/analyze/json_rag          │
                         └──────────────┬──────────────────────┘
                                        │
                   ┌────────────────────┼────────────────────┐
                   ▼                    ▼                    ▼
         ┌─────────────────┐  ┌─────────────────┐  ┌──────────────────┐
         │  PHASE 2        │  │  CLIENT CONFIG   │  │  RAG POLICIES    │
         │  Gemini 2.5     │  │  data/config/    │  │  data/domain_    │
         │  Flash Analysis │  │  {client}.json   │  │  knowledge/      │
         └────────┬────────┘  └─────────────────┘  └──────────────────┘
                  │
                  ▼
         ┌─────────────────┐
         │  PHASE 3        │
         │  Gemini RAG     │
         │  Action Engine  │
         └────────┬────────┘
                  │
                  ▼
         ┌─────────────────┐
         │  Structured     │
         │  JSON Response  │
         │  (Pydantic)     │
         └─────────────────┘
```

### Three-Phase Pipeline

| Phase | Name | Description |
|-------|------|-------------|
| **Phase 1** | Input Ingestion | Validates audio/text, generates conversation UUID |
| **Phase 2** | Gemini Analysis | Extracts sentiment, intent, entities, compliance, agent score |
| **Phase 3** | RAG Action Engine | Feeds Phase 2 JSON back into Gemini with domain policies to generate a prioritized action plan |

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **API Framework** | FastAPI (async) |
| **AI Model** | Google Gemini 2.5 Flash (Multimodal) |
| **Data Validation** | Pydantic v2 |
| **File Handling** | aiofiles (async I/O) |
| **Config Format** | JSON files per client |
| **Language** | Python 3.11+ |

---

## Project Structure

```
vajra/
├── main.py                          # FastAPI app entry point
├── api/
│   ├── routes/
│   │   └── analyze.py               # All 3 API endpoints
│   └── models/
│       ├── request.py               # Input validation models
│       └── response.py              # Output schema (Pydantic)
├── core/
│   └── gemini.py                    # Gemini integration + prompt engine
├── data/
│   ├── config/
│   │   └── banking.json             # Client domain configuration
│   └── domain_knowledge/
│       └── banking_rules.txt        # RAG compliance policies
├── temp_audio/                      # Temporary upload storage (auto-cleaned)
├── requirements.txt
└── .env                             # GEMINI_API_KEY
```

---

## Setup & Installation

### Prerequisites
- Python 3.11+
- A valid [Google Gemini API Key](https://aistudio.google.com/app/apikey)

### 1. Clone & Install

```bash
git clone <your-repo-url>
cd vajra
pip install -r requirements.txt
```

### 2. Configure Environment

Create a `.env` file in the project root:

```env
GEMINI_API_KEY=your_gemini_api_key_here
```

### 3. Add Client Configuration

Create `data/config/banking.json`:

```json
{
  "domain": "banking",
  "company_name": "State Bank",
  "products": ["savings account", "debit card", "credit card", "personal loan"],
  "risk_triggers": ["unauthorized transaction", "fraud", "OTP shared", "large transfer"],
  "escalation_threshold": "medium"
}
```

Create `data/domain_knowledge/banking_rules.txt`:

```
Always verify customer identity before discussing account details.
Block debit cards immediately upon fraud report.
Raise a dispute ticket for any unauthorized transaction within 3 minutes.
Escalate to supervisor if customer requests it or issue is unresolved after 10 minutes.
Never share full account numbers over phone.
```

### 4. Start the Server

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

API docs available at: **http://localhost:8000/docs**

---

## API Endpoints

### `GET /health`
System health check.

**Response:**
```json
{
  "status": "healthy",
  "service": "VAJRA Conversation Intelligence",
  "model": "gemini-2.5-flash",
  "version": "1.0.0"
}
```

---

### `POST /api/v1/analyze/text`
Analyze a text conversation transcript.

**Request Body:**
```json
{
  "client_id": "banking",
  "transcript": "Agent: Good morning, State Bank support, I'm Priya.\nCustomer: Hi, there's an unauthorized transaction of Rs.4200 on my account.",
  "metadata": {
    "channel": "phone",
    "agent_id": "AGT_042"
  }
}
```

**Response:** Full `ConversationAnalysisResult` JSON (see Response Schema below)

---

### `POST /api/v1/analyze/audio`
Analyze a customer call audio recording.

**Form Data:**
| Field | Type | Description |
|-------|------|-------------|
| `audio_file` | File | MP3, WAV, OGG, M4A, FLAC (max 25MB) |
| `client_id` | String | Client identifier |

**cURL Example:**
```bash
curl -X POST http://localhost:8000/api/v1/analyze/audio \
  -F "audio_file=@sample_call.mp3" \
  -F "client_id=banking"
```

---

### `POST /api/v1/analyze/json_rag`
Feed existing Phase 2 JSON output through the Phase 3 RAG action engine standalone.

**Request Body:**
```json
{
  "client_id": "banking",
  "analysis_data": { ... }
}
```

---

## Response Schema

Every analysis endpoint returns a `ConversationAnalysisResult`:

```json
{
  "conversation_id": "uuid-v4",
  "client_id": "banking",
  "input_type": "text | audio",
  "status": "completed | failed | partial",
  "processing_time_ms": 1450,

  "summary": "2-4 sentence summary of the call",
  "language_detected": "en",
  "languages_all": ["en", "hi"],

  "sentiment": {
    "overall": "positive | negative | neutral | mixed",
    "sentiment_score": -0.3,
    "customer_sentiment": "worried but relieved",
    "agent_sentiment": "professional and empathetic",
    "emotional_arc": ["frustrated", "neutral", "satisfied"],
    "frustration_detected": false
  },

  "primary_intent": "dispute_transaction",
  "secondary_intents": ["block_card"],
  "topics_discussed": ["unauthorized_transaction", "card_blocking"],

  "entities": {
    "amounts_mentioned": ["Rs.4200"],
    "dates_mentioned": ["January 14th"],
    "account_references": ["7823"],
    "products_mentioned": ["debit card"],
    "locations_mentioned": [],
    "people_mentioned": ["Priya"]
  },

  "compliance": {
    "violations_detected": [],
    "policies_checked": ["Identity Verification", "Card Blocking Protocol"],
    "risk_level": "medium",
    "escalation_required": false,
    "risk_flags": ["unauthorized_transaction"]
  },

  "agent_performance": {
    "score": 95,
    "greeting_proper": true,
    "empathy_shown": true,
    "issue_resolved": true,
    "call_outcome": "resolved | escalated | dropped | callback_scheduled",
    "strengths": ["Empathy", "Swift resolution"],
    "improvements": []
  },

  "speakers": {
    "speakers_detected": 2,
    "speaker_labels": ["Agent", "Customer"],
    "language_per_speaker": { "Agent": "en", "Customer": "en" }
  },

  "rag_policies_used": ["Policy 1...", "Policy 2..."],

  "rag_actions": {
    "suggested_actions": ["Immediately escalate to Fraud Department"],
    "priority": "P1 - Critical",
    "policy_justifications": ["Per Rule 3: Raise dispute within 3 minutes"],
    "human_review_needed": false,
    "coaching_notes": "Agent performed excellently. No coaching needed."
  }
}
```

---

## Design Decisions & Assumptions

### Why Gemini 2.5 Flash?
- **Native multimodal**: Processes audio directly — no STT pipeline needed
- **Structured JSON output**: `response_mime_type: application/json` enforces schema compliance
- **Multilingual**: Auto-detects language including code-switching (e.g., Hinglish)
- **Speed**: Flash variant gives fast inference suitable for real-time enterprise use

### Client Configuration
Each client gets their own JSON config file and rules `.txt`. This makes VAJRA horizontally scalable — adding a new enterprise client requires only two files, no code changes.

### Two-Stage AI Design (Phase 2 → Phase 3)
Phase 2 extracts raw intelligence. Phase 3 feeds that JSON back into Gemini with domain-specific policies to generate actionable recommendations. This separation of concerns means:
- Phase 2 output is reusable and auditable
- Phase 3 reasoning is policy-grounded, not hallucinated

### Pydantic v2 Validation
All inputs and outputs are fully validated via Pydantic. Invalid requests return structured `ErrorResponse` objects — never raw Python exceptions.

### Async Architecture
All I/O operations (file upload, Gemini API calls) are async, making the API non-blocking and production-ready under concurrent load.

---

## Supported Languages

VAJRA auto-detects language — no configuration needed. Tested with:
- English (`en`)
- Hindi (`hi`)
- Tamil (`ta`)
- Telugu (`te`)
- Hinglish (code-switched `en`/`hi`)

---

## Limitations & Future Improvements

| Limitation | Planned Improvement |
|-----------|---------------------|
| Client configs stored as flat JSON files | Migrate to PostgreSQL with per-tenant schema |
| Audio temp files stored on local disk | Use cloud storage (GCS / S3) |
| No authentication on endpoints | Add API key middleware or JWT auth |
| Single Gemini model for all clients | Allow per-client model selection |
| Phase 3 runs synchronously post-Phase 2 | Make Phase 3 async/background task with webhooks |
| No call recording metadata (duration, hold time) | Extend `metadata` schema and pass into prompt |

---

## Running Tests

```bash
# Test Gemini integration directly
python test_gemini.py

# Test all API endpoints (requires server running)
python test_local.py

# Interactive mode for manual testing
python test_interactive.py

# Test Phase 3 RAG pipeline specifically
python test_json_rag.py
```

---

## Sample Output

**Input:** "Agent: Good morning. Customer: There's an unauthorized Rs.4200 transaction!"

**Output highlights:**
```
primary_intent     → dispute_transaction
risk_level         → medium
agent_performance  → 95/100
call_outcome       → resolved
rag priority       → P2 - High
human_review       → false
```

---

## Team

**Project:** VAJRA  
**Event:** Transight Hackathon — Multimodal Omni-Channel Conversation Intelligence  
**Powered by:** Gemini 2.5 Flash + FastAPI

---

*"Simplicity, clarity, and correctness over complexity."*
