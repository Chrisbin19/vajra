# VAJRA API Documentation

Version 1.0 | Built at Transight Hackathon 2026

## Base URL

```
http://localhost:8000/api/v1
```

## Endpoints

---

### POST /api/v1/analyze/text

Analyze a text conversation transcript through the full 4-phase pipeline.

**Request Headers:**

| Header | Value | Required |
|--------|-------|----------|
| Content-Type | application/json | Yes |

**Request Body:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `client_id` | string | Yes | Client identifier — maps to `data/config/{client_id}.json` |
| `transcript` | string | Yes | Full conversation text (min 10 chars). Format: `"Agent: ...\nCustomer: ..."` |
| `metadata` | object | No | Optional call metadata (channel, call_date, agent_id) |

**Example Request — Banking Fraud Detection:**
```bash
curl -X POST http://localhost:8000/api/v1/analyze/text \
  -H "Content-Type: application/json" \
  -d '{
    "client_id": "banking",
    "transcript": "Customer: Hi, I lost my credit card today. I need to block it immediately before any fraudulent transactions happen."
  }'
```

**Example Request — Insurance Mis-selling (Hinglish):**
```bash
curl -X POST http://localhost:8000/api/v1/analyze/text \
  -H "Content-Type: application/json" \
  -d '{
    "client_id": "banking",
    "transcript": "Agent: Namaste, main Suresh bol raha hoon SecureLife Insurance se. Aapko ek bahut achha investment plan batana tha.\nCustomer: Haan bataiye, kya hai?\nAgent: Sir yeh plan mein aapko guaranteed returns milenge, 12% fixed every year. Bilkul FD jaisa, bas insurance ka wrapper hai.\nCustomer: Achha? Guaranteed hai? Koi risk toh nahi?\nAgent: Haan sir, 100% guaranteed. Risk free hai. Aur tax free bhi. Tension mat lo, bas sign karo.\nCustomer: Free look period ke baare mein kuch batao.\nAgent: Arre sir, free look ka jhanjhat mat karo. Yeh sirf formality hai. Trust karo mujhe.\nCustomer: Premium kitna hoga?\nAgent: Sirf 50,000 per year. 10 saal mein double ho jayega guaranteed. Aaj decide karo, offer kal khatam ho raha hai. Manager ka special quota hai.\nCustomer: Theek hai sochta hoon.\nAgent: Sir please abhi decide karo. Kal tak yeh rate nahi milega."
  }'
```

**Example Request — E-commerce Complaint:**
```bash
curl -X POST http://localhost:8000/api/v1/analyze/text \
  -H "Content-Type: application/json" \
  -d '{
    "client_id": "banking",
    "transcript": "Customer: Hi, I am really upset right now. I placed an order three days ago, the money was deducted from my account, but I have not received the product yet.\nAgent: I am very sorry to hear that. Let me look into this for you right away.\nCustomer: I paid 8,499 for a wireless headset, and the amount was debited immediately. Your app says processing.\nAgent: May I please have your order ID?\nCustomer: Yes, the order ID is ORD4589217. Payment was made using my debit card ending with 7834.\nAgent: The order is scheduled for dispatch within the next 24 hours.\nCustomer: If I dont get it tomorrow, I want a full refund immediately.",
    "metadata": {"channel": "phone", "call_date": "2026-02-21"}
  }'
```

---

### POST /api/v1/analyze/audio

Upload an audio file for full 4-phase analysis. Gemini processes audio natively — no speech-to-text preprocessing.

**Request Headers:**

| Header | Value | Required |
|--------|-------|----------|
| Content-Type | multipart/form-data | Yes |

**Request Body (Form Data):**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `audio_file` | file | Yes | Audio file (MP3, WAV, OGG, M4A, FLAC, AAC, WebM). Max 25MB |
| `client_id` | string | Yes | Client identifier |

**Example Request:**
```bash
curl -X POST http://localhost:8000/api/v1/analyze/audio \
  -F "audio_file=@sample_call.mp3" \
  -F "client_id=banking"
```

---

### POST /api/v1/analyze/json_rag

Feed Phase 2 JSON output through Phase 3 RAG independently. Useful for re-running compliance analysis with different domain rules.

**Request Headers:**

| Header | Value | Required |
|--------|-------|----------|
| Content-Type | application/json | Yes |

**Request Body:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `client_id` | string | Yes | Client identifier |
| `analysis_data` | object | Yes | Full Phase 2 JSON output (ConversationAnalysisResult format) |

**Example Request:**
```bash
curl -X POST http://localhost:8000/api/v1/analyze/json_rag \
  -H "Content-Type: application/json" \
  -d '{
    "client_id": "banking",
    "analysis_data": {
      "summary": "Customer reports lost card...",
      "compliance": {"risk_level": "high", "risk_flags": ["lost_wallet"]},
      "primary_intent": "block_card"
    }
  }'
```

**Response:**
```json
{
  "status": "success",
  "client_id": "banking",
  "rag_actions": {
    "suggested_actions": ["Immediately block the card", "Initiate fraud investigation"],
    "priority": "P1 - Critical",
    "policy_justifications": ["PCI-DSS requires immediate action on compromised cards"],
    "human_review_needed": true,
    "coaching_notes": "Agent should acknowledge urgency before asking verification questions"
  }
}
```

---

### GET /health

System health check.

**Response:**
```json
{
  "status": "healthy",
  "service": "VAJRA Conversation Intelligence",
  "model": "gemini-2.5-flash",
  "version": "1.0.0",
  "supported_inputs": ["audio/mp3", "audio/wav", "audio/ogg", "audio/m4a", "text/plain"]
}
```

---

## Error Responses

| Code | Meaning |
|------|---------|
| 400 | Unsupported file type or missing required fields |
| 413 | Audio file exceeds 25MB limit |
| 422 | Pydantic validation error (transcript too short, empty client_id) |
| 500 | Gemini API failure or internal server error |

**Error format:**
```json
{
  "detail": "Analysis failed: 429 RESOURCE_EXHAUSTED..."
}
```

---

## Response Schema Reference

Full response from `/analyze/text` and `/analyze/audio`:

| Field | Type | Description |
|-------|------|-------------|
| `conversation_id` | string | UUID assigned to this analysis |
| `client_id` | string | Echoed from request |
| `input_type` | string | `"text"` or `"audio"` |
| `status` | string | `"completed"` or `"failed"` |
| `processing_time_ms` | integer | Total processing time in milliseconds |
| `summary` | string | 2-4 sentence conversation synopsis |
| `language_detected` | string | Primary ISO language code (e.g. `"en"`, `"hi"`) |
| `languages_all` | string[] | All detected languages including code-switching |
| `sentiment.overall` | string | `"positive"`, `"negative"`, `"neutral"`, `"mixed"` |
| `sentiment.sentiment_score` | float | -1.0 (very negative) to +1.0 (very positive) |
| `sentiment.customer_sentiment` | string | Customer emotional state description |
| `sentiment.agent_sentiment` | string | Agent tone description |
| `sentiment.emotional_arc` | string[] | Emotional progression, e.g. `["frustrated", "neutral", "satisfied"]` |
| `sentiment.frustration_detected` | boolean | True if anger/intense frustration detected |
| `primary_intent` | string | Main customer intent (e.g. `"block_card"`, `"report_fraud"`) |
| `secondary_intents` | string[] | Additional intents |
| `topics_discussed` | string[] | Conversation themes |
| `entities.amounts_mentioned` | string[] | Currency amounts (e.g. `["Rs.4200"]`) |
| `entities.dates_mentioned` | string[] | Dates/timelines referenced |
| `entities.account_references` | string[] | Partial account numbers |
| `entities.products_mentioned` | string[] | Products discussed |
| `entities.locations_mentioned` | string[] | Locations referenced |
| `entities.people_mentioned` | string[] | Names referenced |
| `compliance.violations_detected` | string[] | Specific violations found |
| `compliance.policies_checked` | string[] | RAG policies evaluated |
| `compliance.risk_level` | string | `"low"`, `"medium"`, `"high"`, `"critical"` |
| `compliance.escalation_required` | boolean | True if supervisor review needed |
| `compliance.risk_flags` | string[] | High-level risk indicators |
| `agent_performance.score` | integer | 0-100 performance score |
| `agent_performance.greeting_proper` | boolean | Compliant greeting given |
| `agent_performance.empathy_shown` | boolean | Frustration acknowledged |
| `agent_performance.issue_resolved` | boolean | Core issue fully resolved |
| `agent_performance.call_outcome` | string | `"resolved"`, `"escalated"`, `"dropped"`, `"callback_scheduled"` |
| `agent_performance.strengths` | string[] | Areas of strong performance |
| `agent_performance.improvements` | string[] | Coaching recommendations |
| `speakers.speakers_detected` | integer | Number of distinct speakers |
| `speakers.speaker_labels` | string[] | e.g. `["Agent", "Customer"]` |
| `speakers.language_per_speaker` | object | Speaker → language mapping |
| `rag_policies_used` | string[] | Policies injected into the analysis prompt |
| `rag_actions.suggested_actions` | string[] | Recommended next steps |
| `rag_actions.priority` | string | `"P1 - Critical"` through `"P4 - Low"` |
| `rag_actions.policy_justifications` | string[] | Policy citations for actions |
| `rag_actions.human_review_needed` | boolean | Manual review required |
| `rag_actions.coaching_notes` | string | Agent improvement advice |
| `deterministic_compliance.compliance_risk_score` | float | Normalized risk score 0.0-1.0 |
| `deterministic_compliance.total_flags` | integer | Number of triggered rules |
| `deterministic_compliance.auto_escalate` | boolean | Auto-escalation triggered |
| `deterministic_compliance.flags` | object[] | Triggered rule details (keyword, severity, context, policy_reference, source) |
| `error` | string/null | Error message if status is `"failed"` |

---

## Configuration Schema

### Client Config — `data/config/{client_id}.json`

| Field | Type | Required | Description | Example |
|-------|------|----------|-------------|---------|
| `business_domain` | string | Yes | Industry vertical | `"banking"` |
| `products_services` | string[] | Yes | Products the client supports | `["Credit Cards", "Savings Accounts"]` |
| `policies` | string[] | Yes | High-level compliance policies | `["Must verify user identity before discussing account details."]` |
| `escalation_rules.high_risk_keywords` | object[] | No | Custom keywords for deterministic scan | See example below |

**Keyword object format:**
```json
{
  "keyword": "guaranteed returns",
  "severity": "high",
  "policy_reference": "IRDAI PPI Reg 15(1)"
}
```

Severity values: `"high"` (weight 1.0), `"medium"` (weight 0.5), `"low"` (weight 0.2).

### Domain Knowledge — `data/domain_knowledge/{client_id}_rules.txt`

Plain text file with one compliance rule per line. These are injected directly into the Gemini prompt for contextual evaluation.

**Current files:**

| File | Purpose |
|------|---------|
| `banking_rules.txt` | PCI-DSS data retention rules, fraud trigger definitions |

---

## Adding New Domains

**Step 1** — Create config file `data/config/insurance.json`:
```json
{
  "business_domain": "insurance",
  "products_services": ["Term Life", "Health Insurance", "ULIPs"],
  "policies": ["Must disclose free look period.", "Cannot promise guaranteed returns on ULIPs."],
  "escalation_rules": {
    "high_risk_keywords": [
      {"keyword": "guaranteed returns", "severity": "high", "policy_reference": "IRDAI PPI Reg 15(1)"},
      {"keyword": "no risk", "severity": "high", "policy_reference": "IRDAI Mis-selling Guidelines"},
      {"keyword": "tax free", "severity": "medium", "policy_reference": "Income Tax Act Sec 10(10D)"}
    ]
  }
}
```

**Step 2** — Create rules file `data/domain_knowledge/insurance_rules.txt`:
```
IRDAI PPI Regulation 15(1): No insurance product shall be marketed with guaranteed return claims unless explicitly approved by IRDAI.
Mis-selling Guidelines: Agents must disclose all risks, charges, lock-in periods, and the free look period during every sales call.
IGMS 2024: All customer grievances must be acknowledged within 24 hours and resolved within 15 days.
```

**Step 3** — Call the API:
```bash
curl -X POST http://localhost:8000/api/v1/analyze/text \
  -H "Content-Type: application/json" \
  -d '{"client_id": "insurance", "transcript": "..."}'
```

No code changes. No server restart. The new domain is live immediately.

---

## Sample Output

Real output from analyzing a banking card block request:

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
    "dates_mentioned": [],
    "account_references": [],
    "products_mentioned": ["card"],
    "locations_mentioned": [],
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
    "call_outcome": "dropped",
    "strengths": [],
    "improvements": []
  },
  "speakers": {
    "speakers_detected": 1,
    "speaker_labels": ["customer"],
    "language_per_speaker": {"customer": "en"}
  },
  "rag_policies_used": [
    "PCI-DSS Requirement: Sensitive authentication data cannot be retained.",
    "Fraud Triggers: Flag any conversation where the customer mentions \"unauthorized transaction\", \"stolen card\", or \"hacked account\"."
  ],
  "error": null
}
```
