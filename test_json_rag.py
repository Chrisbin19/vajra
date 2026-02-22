"""
VAJRA Phase 3 RAG Test
Tests the /analyze/json_rag endpoint directly with a pre-built Phase 2 payload.

FIX applied:
  - Added headers={"X-API-Key": API_KEY} to requests.post()
  - Was getting 401/403 without it
"""
import json
import requests

BASE_URL = "http://127.0.0.1:8000"
API_KEY  = "vajra-demo-key-2026"     # FIX: header was completely missing

# Pre-built Phase 2 JSON representing a real analysis output
sample_payload = {
  "conversation_id": "45524148-563b-4281-a5a9-4f3c98d7faa7",
  "client_id": "banking_client_01",
  "input_type": "audio",
  "status": "completed",
  "processing_time_ms": 14201,
  "summary": "The conversation begins with an agent's greeting, which is immediately interrupted by a highly frustrated customer demanding to speak with a supervisor 'ASAP'. The call is very short and ends with the customer's unresolved demand for escalation.",
  "language_detected": "en",
  "languages_all": ["en"],
  "sentiment": {
    "overall": "negative",
    "sentiment_score": -0.8,
    "customer_sentiment": "Extremely negative and frustrated, demanding immediate escalation.",
    "agent_sentiment": "Neutral, attempting to be helpful but cut off.",
    "emotional_arc": ["neutral", "frustrated", "angry"],
    "frustration_detected": True
  },
  "primary_intent": "demand_supervisor",
  "secondary_intents": ["express_frustration"],
  "topics_discussed": ["escalation", "supervisor request"],
  "entities": {
    "amounts_mentioned": [],
    "dates_mentioned": [],
    "account_references": [],
    "products_mentioned": [],
    "locations_mentioned": [],
    "people_mentioned": []
  },
  "compliance": {
    "violations_detected": [],
    "policies_checked": [
      "Always acknowledge customer concern before providing solutions.",
      "Escalate unresolved issues after 10 minutes to supervisor."
    ],
    "risk_level": "high",
    "escalation_required": True,
    "risk_flags": ["escalation_requested", "customer_frustration"]
  },
  "agent_performance": {
    "score": 50,
    "greeting_proper": True,
    "empathy_shown": False,
    "issue_resolved": False,
    "call_outcome": "escalated",
    "strengths": ["Proper greeting initiated"],
    "improvements": ["N/A due to immediate customer escalation"]
  },
  "speakers": {
    "speakers_detected": 2,
    "speaker_labels": ["Speaker 1", "Speaker 2"],
    "language_per_speaker": {"Speaker 1": "en", "Speaker 2": "en"}
  },
  "rag_policies_used": [
    "Always acknowledge customer concern before providing solutions.",
    "Escalate unresolved issues after 10 minutes to supervisor."
  ],
  "error": None
}

request_body = {
    "client_id": "banking_client_01",
    "analysis_data": sample_payload
}

print("=" * 55)
print("VAJRA — Phase 3 RAG Test")
print(f"Endpoint: POST {BASE_URL}/api/v1/analyze/json_rag")
print(f"API Key:  {API_KEY}")
print("=" * 55)

print("\nSending Phase 2 JSON to Phase 3 RAG endpoint...")
response = requests.post(
    f"{BASE_URL}/api/v1/analyze/json_rag",
    json=request_body,
    headers={"X-API-Key": API_KEY}    # FIX: was missing, caused 401/403
)

if response.status_code == 200:
    data = response.json()
    print("\n✅ SUCCESS!")
    print("\nRAG Actions:")
    print(json.dumps(data.get('rag_actions'), indent=2, ensure_ascii=False))
else:
    print(f"\n❌ FAILED: HTTP {response.status_code}")
    print(response.text)