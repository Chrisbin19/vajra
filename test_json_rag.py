import json
import requests

# Load the dummy JSON explicitly representing a Phase 2 output
sample_payload = {
  "conversation_id": "45524148-563b-4281-a5a9-4f3c98d7faa7",
  "client_id": "banking",
  "input_type": "audio",
  "status": "completed",
  "processing_time_ms": 14201,
  "summary": "The conversation begins with an agent's greeting, which is immediately interrupted by a highly frustrated customer demanding to speak with a supervisor 'ASAP'. The call is very short and ends with the customer's unresolved demand for escalation.",
  "language_detected": "en",
  "languages_all": [
    "en"
  ],
  "sentiment": {
    "overall": "negative",
    "customer_sentiment": "Extremely negative and frustrated, demanding immediate escalation.",
    "agent_sentiment": "Neutral, attempting to be helpful but cut off.",
    "emotional_arc": [
      "neutral",
      "frustrated",
      "angry"
    ],
    "frustration_detected": True
  },
  "customer_intents": [
    "demand_supervisor",
    "express_frustration"
  ],
  "topics_discussed": [
    "escalation",
    "supervisor request"
  ],
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
    "risk_flags": [
      "escalation_requested",
      "customer_frustration"
    ]
  },
  "agent_performance": {
    "score": 50,
    "greeting_proper": True,
    "empathy_shown": False,
    "issue_resolved": False,
    "call_outcome": "escalated",
    "strengths": [
      "Proper greeting initiated"
    ],
    "improvements": [
      "N/A due to immediate customer escalation"
    ]
  },
  "speakers": {
    "speakers_detected": 2,
    "speaker_labels": [
      "Speaker 1",
      "Speaker 2"
    ],
    "language_per_speaker": {
      "Speaker 1": "en",
      "Speaker 2": "en"
    }
  },
  "rag_policies_used": [
    "Always acknowledge customer concern before providing solutions.",
    "Escalate unresolved issues after 10 minutes to supervisor."
  ],
  "error": None
}

# The Request Body mapping to JsonRagRequest model
request_body = {
    "client_id": "banking",  # Using banking so it pulls real config files
    "analysis_data": sample_payload
}

print("Sending Phase 2 JSON output to Phase 3 RAG endpoint...")
response = requests.post("http://127.0.0.1:8000/api/v1/analyze/json_rag", json=request_body)

if response.status_code == 200:
    print("\nSUCCESS!")
    print(response.json().get('rag_recommendation'))
else:
    print(f"\nFAILED: {response.status_code}")
    print(response.text)
