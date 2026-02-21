# VAJRA — Sample API Requests & Responses

## Quick Demo Commands (cURL)

### 1. Health Check
```bash
curl http://localhost:8000/health
```

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

### 2. Analyze Text Transcript
```bash
curl -X POST http://localhost:8000/api/v1/analyze/text \
  -H "Content-Type: application/json" \
  -d '{
    "client_id": "banking",
    "transcript": "Agent: Good morning, State Bank support, I am Priya. How can I help?\nCustomer: Hi Priya, there is an unauthorized transaction of Rs.4200 on my account from January 14th. I never made this!\nAgent: I understand and apologize. Let me verify your identity. Last 4 digits of your account?\nCustomer: 7823.\nAgent: Thank you. I can see the suspicious transaction. I am raising a dispute ticket and blocking your card now. You will get an SMS confirmation.\nCustomer: Thank you so much, that is a huge relief.",
    "metadata": {
      "channel": "phone",
      "agent_id": "AGT_042",
      "call_date": "2024-01-15"
    }
  }'
```

**Full Response:**
```json
{
  "conversation_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "client_id": "banking",
  "input_type": "text",
  "status": "completed",
  "processing_time_ms": 1450,
  "summary": "A banking customer called to report an unauthorized transaction of Rs.4200 dated January 14th. Agent Priya verified the customer's identity using the last 4 digits of their account number. The agent immediately blocked the debit card and raised a dispute ticket, resolving the issue on the call.",
  "language_detected": "en",
  "languages_all": ["en"],
  "sentiment": {
    "overall": "mixed",
    "sentiment_score": 0.2,
    "customer_sentiment": "Initially panicked and worried, became relieved after resolution",
    "agent_sentiment": "Professional, empathetic, and action-oriented",
    "emotional_arc": ["worried", "anxious", "relieved", "satisfied"],
    "frustration_detected": false
  },
  "primary_intent": "dispute_transaction",
  "secondary_intents": ["block_card"],
  "topics_discussed": ["unauthorized_transaction", "identity_verification", "card_blocking", "dispute_resolution"],
  "entities": {
    "amounts_mentioned": ["Rs.4200"],
    "dates_mentioned": ["January 14th"],
    "account_references": ["7823"],
    "products_mentioned": ["debit card", "account"],
    "locations_mentioned": [],
    "people_mentioned": ["Priya"]
  },
  "compliance": {
    "violations_detected": [],
    "policies_checked": [
      "Identity Verification via last 4 digits",
      "Immediate Card Blocking Protocol",
      "Dispute Ticket Raising within 3 minutes"
    ],
    "risk_level": "medium",
    "escalation_required": false,
    "risk_flags": ["unauthorized_transaction"]
  },
  "agent_performance": {
    "score": 95,
    "greeting_proper": true,
    "empathy_shown": true,
    "issue_resolved": true,
    "call_outcome": "resolved",
    "strengths": ["Swift card blocking", "Empathetic tone", "Clear next-steps given to customer"],
    "improvements": ["Could have asked customer to check for other suspicious transactions proactively"]
  },
  "speakers": {
    "speakers_detected": 2,
    "speaker_labels": ["Agent", "Customer"],
    "language_per_speaker": {
      "Agent": "en",
      "Customer": "en"
    }
  },
  "rag_policies_used": [
    "Always verify customer identity before discussing account details.",
    "Block debit card immediately upon receiving an unauthorized transaction report.",
    "Raise a dispute ticket within 3 minutes of call start.",
    "Escalate to supervisor if issue remains unresolved after 10 minutes."
  ],
  "rag_actions": {
    "suggested_actions": [
      "Confirm dispute ticket DIS-2024-XXXXX is logged in the fraud management system",
      "Schedule automated follow-up SMS to customer in 24 hours with dispute status",
      "Flag merchant ID associated with Rs.4200 transaction for fraud team review"
    ],
    "priority": "P2 - High",
    "policy_justifications": [
      "Per Rule 2: Identity verified correctly via last 4 digits — compliant",
      "Per Rule 3: Card blocked and dispute raised immediately — compliant",
      "Per Rule 8: Customer informed of next steps before call end — compliant"
    ],
    "human_review_needed": false,
    "coaching_notes": "Excellent call. Agent Priya demonstrated empathy, followed all protocols, and resolved the issue efficiently. Consider proactively asking customers to check for other suspicious transactions in future fraud calls."
  }
}
```

---

### 3. Analyze Audio File
```bash
curl -X POST http://localhost:8000/api/v1/analyze/audio \
  -F "audio_file=@sample_call.mp3" \
  -F "client_id=banking"
```

*(Response format identical to text analysis above)*

---

### 4. Phase 3 RAG Only (Standalone)
```bash
curl -X POST http://localhost:8000/api/v1/analyze/json_rag \
  -H "Content-Type: application/json" \
  -d '{
    "client_id": "banking",
    "analysis_data": {
      "conversation_id": "abc-123",
      "client_id": "banking",
      "input_type": "audio",
      "status": "completed",
      "primary_intent": "demand_supervisor",
      "sentiment": {
        "overall": "negative",
        "sentiment_score": -0.9,
        "frustration_detected": true,
        "emotional_arc": ["angry", "frustrated"],
        "customer_sentiment": "Extremely frustrated",
        "agent_sentiment": "Neutral"
      },
      "compliance": {
        "risk_level": "high",
        "escalation_required": true,
        "violations_detected": [],
        "risk_flags": ["escalation_requested", "customer_frustration"],
        "policies_checked": []
      },
      "agent_performance": {
        "score": 50,
        "issue_resolved": false,
        "call_outcome": "escalated",
        "greeting_proper": true,
        "empathy_shown": false,
        "strengths": ["Proper greeting"],
        "improvements": ["Show empathy", "Attempt resolution before escalation"]
      }
    }
  }'
```

**Response:**
```json
{
  "status": "success",
  "client_id": "banking",
  "rag_actions": {
    "suggested_actions": [
      "Immediately transfer call to senior supervisor",
      "Log incident with risk_level = HIGH",
      "Send written follow-up to customer within 2 hours"
    ],
    "priority": "P1 - Critical",
    "policy_justifications": [
      "Per Rule 5: Customer explicitly requested escalation — immediate supervisor transfer required",
      "Per Rule 10: Frustration-related flags mandate high risk logging"
    ],
    "human_review_needed": true,
    "coaching_notes": "Agent did not attempt empathy or resolution before escalation. Coaching needed on de-escalation techniques and active listening."
  }
}
```

---

### 5. Error Handling Examples

**Invalid file type:**
```bash
curl -X POST http://localhost:8000/api/v1/analyze/audio \
  -F "audio_file=@document.pdf" \
  -F "client_id=banking"
```
```json
{
  "detail": "Unsupported file type: '.pdf'. Allowed formats: ['.aac', '.flac', '.m4a', '.mp3', '.ogg', '.wav', '.webm']"
}
```

**Transcript too short:**
```bash
curl -X POST http://localhost:8000/api/v1/analyze/text \
  -H "Content-Type: application/json" \
  -d '{"client_id": "banking", "transcript": "hi"}'
```
```json
{
  "detail": [{"msg": "transcript must be at least 10 chars after stripping whitespace"}]
}
```
