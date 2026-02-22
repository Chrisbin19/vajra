# NEXUS — Sample Requests & Responses

All responses below are **real, unmodified system output** captured from the live NEXUS API on 2026-02-21.

## How To Use These Samples

Start the server:
```bash
python main.py
# Select [1] to start API server
```

Copy any request below and run it directly:
```bash
curl -X POST http://localhost:8000/api/v1/analyze/text \
  -H "Content-Type: application/json" \
  -d '{ ... }'
```

---

## Sample 1 — Insurance Mis-selling Detection (Hinglish)

A Hinglish sales call where the agent promises "guaranteed 12% returns", dismisses the free look period, and uses high-pressure tactics.

### Request
```bash
curl -X POST http://localhost:8000/api/v1/analyze/text \
  -H "Content-Type: application/json" \
  -d '{
    "client_id": "banking",
    "transcript": "Agent: Namaste, main Suresh bol raha hoon SecureLife Insurance se. Aapko ek bahut achha investment plan batana tha.\nCustomer: Haan bataiye, kya hai?\nAgent: Sir yeh plan mein aapko guaranteed returns milenge, 12% fixed every year. Bilkul FD jaisa, bas insurance ka wrapper hai.\nCustomer: Achha? Guaranteed hai? Koi risk toh nahi?\nAgent: Haan sir, 100% guaranteed. Risk free hai. Aur tax free bhi. Tension mat lo, bas sign karo.\nCustomer: Free look period ke baare mein kuch batao.\nAgent: Arre sir, free look ka jhanjhat mat karo. Yeh sirf formality hai. Trust karo mujhe.\nCustomer: Premium kitna hoga?\nAgent: Sirf 50,000 per year. 10 saal mein double ho jayega guaranteed. Aaj decide karo, offer kal khatam ho raha hai. Manager ka special quota hai.\nCustomer: Theek hai sochta hoon.\nAgent: Sir please abhi decide karo. Kal tak yeh rate nahi milega."
  }'
```

### Response
```json
{
  "conversation_id": "d34579cd-b7f7-4fef-b541-091e57ca4e33",
  "client_id": "banking",
  "input_type": "text",
  "status": "completed",
  "processing_time_ms": 18519,
  "summary": "The conversation involves an agent from SecureLife Insurance attempting to sell an investment plan to a customer. The agent uses high-pressure sales tactics, makes misleading claims about guaranteed returns and risk-free nature, and discourages the customer from utilizing the free look period. The customer expresses interest but also hesitation, ultimately stating they need to think about it, while the agent continues to push for an immediate decision.",
  "language_detected": "hi",
  "languages_all": ["hi"],
  "sentiment": {
    "overall": "negative",
    "sentiment_score": -0.7,
    "customer_sentiment": "hesitant_pressured",
    "agent_sentiment": "aggressive_misleading",
    "emotional_arc": [
      "customer_curious_to_hesitant",
      "agent_aggressive_to_more_aggressive"
    ],
    "frustration_detected": true
  },
  "primary_intent": "investment_plan_inquiry",
  "secondary_intents": [
    "free_look_period_inquiry",
    "premium_inquiry"
  ],
  "topics_discussed": [
    "investment plan",
    "guaranteed returns",
    "risk",
    "tax benefits",
    "free look period",
    "premium",
    "sales offer",
    "decision making"
  ],
  "entities": {
    "amounts_mentioned": ["12%", "50,000"],
    "dates_mentioned": ["10 saal", "kal"],
    "account_references": [],
    "products_mentioned": ["investment plan", "FD", "insurance"],
    "locations_mentioned": [],
    "people_mentioned": ["Suresh"]
  },
  "compliance": {
    "violations_detected": [
      "Misrepresentation of product features (guaranteed, risk-free, 12% fixed returns for an insurance product)",
      "Discouraging customer from exercising statutory right (free look period)",
      "High-pressure sales tactics (urgency, limited-time offer, manager's quota)"
    ],
    "policies_checked": ["PCI-DSS Requirement", "Fraud Triggers"],
    "risk_level": "critical",
    "escalation_required": true,
    "risk_flags": [
      "misrepresentation_of_product",
      "discouraging_consumer_rights",
      "high_pressure_sales_tactics"
    ]
  },
  "agent_performance": {
    "score": 15,
    "greeting_proper": true,
    "empathy_shown": false,
    "issue_resolved": false,
    "call_outcome": "unresolved",
    "strengths": ["Proper greeting"],
    "improvements": [
      "Adherence to ethical sales practices",
      "Accurate product representation",
      "Respecting customer's decision-making time",
      "Not discouraging statutory consumer rights"
    ]
  },
  "speakers": {
    "speakers_detected": 2,
    "speaker_labels": ["Agent", "Customer"],
    "language_per_speaker": {
      "Agent": "hi",
      "Customer": "hi"
    }
  },
  "rag_policies_used": [
    "PCI-DSS Requirement: Sensitive authentication data cannot be retained.",
    "Fraud Triggers: Flag any conversation where the customer mentions \"unauthorized transaction\", \"stolen card\", or \"hacked account\"."
  ],
  "rag_actions": {
    "suggested_actions": [],
    "priority": "P3 - Nominal",
    "policy_justifications": [
      "No sensitive authentication data was retained, therefore PCI-DSS Requirement (1) was not violated.",
      "The customer did not mention 'unauthorized transaction', 'stolen card', or 'hacked account', therefore Fraud Triggers (2) were not activated."
    ],
    "human_review_needed": false,
    "coaching_notes": "Agent needs to improve adherence to ethical sales practices, including accurate product representation (avoiding misleading claims about guaranteed returns or risk-free nature). It is crucial to respect the customer's decision-making time and never discourage them from exercising statutory rights like the free look period. Avoid high-pressure sales tactics and creating false urgency."
  },
  "deterministic_compliance": {
    "compliance_risk_score": 0.03,
    "total_flags": 1,
    "auto_escalate": false,
    "flags": [
      {
        "keyword": "manager",
        "severity": "medium",
        "context": "Agent: Sirf 50,000 per year. 10 saal mein double ho jayega guaranteed. Aaj decide karo, offer kal khatam ho raha hai. Manager ka special quota hai.",
        "policy_reference": "Escalation Request Policy",
        "action_required": false,
        "source": "deterministic"
      }
    ]
  },
  "error": null
}
```

---

## Sample 2 — Banking Fraud / Lost Card (Text)

Customer reports a lost credit card and urgently requests blocking to prevent fraud.

### Request
```bash
curl -X POST http://localhost:8000/api/v1/analyze/text \
  -H "Content-Type: application/json" \
  -d '{
    "client_id": "banking",
    "transcript": "Hi, I lost my credit card today. I need to block it immediately before any fraudulent transactions happen."
  }'
```

### Response
```json
{
  "conversation_id": "8162dbea-28fb-4a4a-bd50-40ae433a9c33",
  "client_id": "banking",
  "input_type": "text",
  "status": "completed",
  "processing_time_ms": 6638,
  "summary": "The customer reports losing their credit card and urgently requests to block it to prevent any fraudulent transactions from occurring.",
  "language_detected": "en",
  "languages_all": ["en"],
  "sentiment": {
    "overall": "negative",
    "sentiment_score": -0.6,
    "customer_sentiment": "urgent and concerned",
    "agent_sentiment": "not applicable",
    "emotional_arc": ["concerned_to_urgent"],
    "frustration_detected": true
  },
  "primary_intent": "request_card_block",
  "secondary_intents": ["report_fraud_risk"],
  "topics_discussed": [
    "credit_card_loss",
    "fraud_prevention",
    "card_blocking"
  ],
  "entities": {
    "amounts_mentioned": [],
    "dates_mentioned": ["today"],
    "account_references": [],
    "products_mentioned": ["credit card"],
    "locations_mentioned": [],
    "people_mentioned": []
  },
  "compliance": {
    "violations_detected": [],
    "policies_checked": ["PCI-DSS Requirement", "Fraud Triggers"],
    "risk_level": "medium",
    "escalation_required": true,
    "risk_flags": ["unauthorized_transaction_risk"]
  },
  "agent_performance": {
    "score": 0,
    "greeting_proper": false,
    "empathy_shown": false,
    "issue_resolved": false,
    "call_outcome": "unknown",
    "strengths": [],
    "improvements": []
  },
  "speakers": {
    "speakers_detected": 1,
    "speaker_labels": ["Customer"],
    "language_per_speaker": {"Customer": "en"}
  },
  "rag_policies_used": [
    "PCI-DSS Requirement: Sensitive authentication data cannot be retained.",
    "Fraud Triggers: Flag any conversation where the customer mentions \"unauthorized transaction\", \"stolen card\", or \"hacked account\"."
  ],
  "rag_actions": {
    "suggested_actions": [
      "Immediately block the customer's lost credit card to prevent fraudulent transactions.",
      "Initiate the standard fraud prevention protocol for lost cards.",
      "Ensure the customer is contacted to confirm the card blockage and provide next steps for a replacement card.",
      "Review the agent's handling of the urgent card loss and fraud risk report."
    ],
    "priority": "P2 - High",
    "policy_justifications": [
      "Policy 2 (Fraud Triggers): The customer mentioned 'fraudulent transactions' and 'lost my credit card', which triggers the fraud policy requiring immediate action."
    ],
    "human_review_needed": true,
    "coaching_notes": "The agent did not resolve the customer's urgent request to block a lost card and prevent fraudulent transactions. It is critical to prioritize and resolve such high-risk issues immediately. Ensure proper protocol for lost cards and fraud prevention is followed, and confirm resolution with the customer."
  },
  "deterministic_compliance": {
    "compliance_risk_score": 0.05,
    "total_flags": 1,
    "auto_escalate": true,
    "flags": [
      {
        "keyword": "fraud",
        "severity": "high",
        "context": "Hi, I lost my credit card today. I need to block it immediately before any fraudulent transactions happen.",
        "policy_reference": "Fraud Reporting Policy",
        "action_required": true,
        "source": "deterministic"
      }
    ]
  },
  "error": null
}
```

---

## Sample 3 — E-commerce Complaint with Refund Demand (Text)

Customer angry about a delayed ₹8,499 order. Tests empathy detection, entity extraction, and refund keyword flagging.

### Request
```bash
curl -X POST http://localhost:8000/api/v1/analyze/text \
  -H "Content-Type: application/json" \
  -d '{
    "client_id": "banking",
    "transcript": "Customer:\nHi, I'\''m really upset right now. I placed an order three days ago, the money was deducted from my account, but I haven'\''t received the product yet. This is not acceptable.\n\nAgent:\nI'\''m very sorry to hear that you'\''re experiencing this. I understand how concerning it can be when money is deducted and the order hasn'\''t arrived. Let me look into this for you right away.\n\nCustomer:\nThis is the second time this has happened. I paid ₹8,499 for a wireless headset, and the amount was debited immediately. My bank shows the transaction was successful, but your app says \"processing.\"\n\nAgent:\nThank you for sharing those details. May I please have your order ID or the registered phone number so I can check the status?\n\nCustomer:\nYes, the order ID is ORD4589217. The payment was made using my debit card ending with 7834.\n\nAgent:\nThank you. Please allow me a moment while I check the system.\n\n(Short pause)\n\nI can see the order here. It appears the payment was received successfully, but there was a delay in warehouse dispatch due to a system update. I sincerely apologize for the inconvenience.\n\nCustomer:\nBut why wasn'\''t I informed? My money has been stuck for three days. What if I never receive it? I'\''m honestly worried I'\''ve lost my money.\n\nAgent:\nI completely understand your concern. Please be assured that your payment is secure and linked to your order. You have not lost your money. The order is scheduled for dispatch within the next 24 hours.\n\nCustomer:\nIf I don'\''t get it tomorrow, I want a full refund immediately. I can'\''t afford to just lose ₹8,499 like this.\n\nAgent:\nThat is absolutely fair. If the order is not dispatched within 24 hours, we will initiate a full refund to your original payment method. I will personally mark this order as high priority and send you a confirmation email shortly.\n\nCustomer:\nOkay… I just want this resolved quickly. I'\''ve had a stressful week already.\n\nAgent:\nI completely understand. Thank you for your patience. I'\''ve escalated the case to our logistics team, and you will receive a tracking update soon. Is there anything else I can assist you with today?\n\nCustomer:\nNo, that'\''s all. Please just make sure this gets fixed.\n\nAgent:\nAbsolutely. We appreciate your trust, and we'\''ll ensure this is resolved promptly. Have a good day, and please feel free to reach out if you need further assistance."
  }'
```

### Response
```json
{
  "conversation_id": "620b257a-1efb-4327-8caa-7244f25ae6fa",
  "client_id": "banking",
  "input_type": "text",
  "status": "completed",
  "processing_time_ms": 10941,
  "summary": "The customer contacted support expressing significant frustration and worry about a missing order for which payment was successfully deducted three days prior. The agent empathized with the customer's situation, investigated the order using the provided ID and partial card number, and identified a delay due to a system update. The agent assured the customer their payment was secure, committed to dispatch within 24 hours, and offered a full refund if the dispatch timeline was not met, successfully de-escalating the immediate concern.",
  "language_detected": "en",
  "languages_all": ["en"],
  "sentiment": {
    "overall": "mixed",
    "sentiment_score": -0.3,
    "customer_sentiment": "Starts angry and frustrated, transitions to worried, and ends cautiously accepting with a desire for quick resolution.",
    "agent_sentiment": "Consistently empathetic, apologetic, reassuring, and proactive in problem-solving.",
    "emotional_arc": [
      "Frustration",
      "Concern",
      "Worry",
      "Cautious Acceptance"
    ],
    "frustration_detected": true
  },
  "primary_intent": "missing_order_inquiry",
  "secondary_intents": [
    "request_refund",
    "express_dissatisfaction"
  ],
  "topics_discussed": [
    "order_status",
    "payment_status",
    "delivery_delay",
    "refund_policy",
    "customer_service_experience"
  ],
  "entities": {
    "amounts_mentioned": ["₹8,499"],
    "dates_mentioned": ["three days ago", "24 hours", "tomorrow"],
    "account_references": ["7834"],
    "products_mentioned": ["wireless headset"],
    "locations_mentioned": ["warehouse"],
    "people_mentioned": []
  },
  "compliance": {
    "violations_detected": [],
    "policies_checked": ["PCI-DSS Requirement", "Fraud Triggers"],
    "risk_level": "medium",
    "escalation_required": true,
    "risk_flags": []
  },
  "agent_performance": {
    "score": 95,
    "greeting_proper": true,
    "empathy_shown": true,
    "issue_resolved": true,
    "call_outcome": "resolved",
    "strengths": [
      "Demonstrated strong empathy and active listening.",
      "Provided clear explanation for the delay.",
      "Offered a proactive solution (dispatch or refund) and set clear expectations.",
      "Took ownership by escalating internally and promising follow-up."
    ],
    "improvements": [
      "Could have proactively offered a small goodwill gesture given the repeated issue and customer's stress, though not strictly necessary given the strong resolution path."
    ]
  },
  "speakers": {
    "speakers_detected": 2,
    "speaker_labels": ["Customer", "Agent"],
    "language_per_speaker": {
      "Customer": "en",
      "Agent": "en"
    }
  },
  "rag_policies_used": [
    "PCI-DSS Requirement: Sensitive authentication data cannot be retained.",
    "Fraud Triggers: Flag any conversation where the customer mentions \"unauthorized transaction\", \"stolen card\", or \"hacked account\"."
  ],
  "rag_actions": {
    "suggested_actions": [
      "No immediate compliance actions are required based on the provided RAG policies.",
      "Review agent's handling of partial card numbers to ensure no sensitive authentication data (e.g., CVV, full track data) was retained, aligning with RAG Policy 1.",
      "Acknowledge the agent's effective de-escalation and successful resolution of the customer's missing order concern."
    ],
    "priority": "P3 - Nominal",
    "policy_justifications": [
      "RAG Policy 1 ('PCI-DSS Requirement: Sensitive authentication data cannot be retained.') was not violated as the 'partial card number' (7834) used for investigation is not classified as sensitive authentication data under PCI-DSS.",
      "RAG Policy 2 ('Fraud Triggers: Flag any conversation where the customer mentions \"unauthorized transaction\", \"stolen card\", or \"hacked account\".') was not triggered as none of the specified keywords were mentioned by the customer."
    ],
    "human_review_needed": false,
    "coaching_notes": "The agent handled the customer's frustration effectively and provided a clear resolution path. Consider proactively offering a small goodwill gesture in similar situations of repeated issues and high customer stress, as noted in the agent performance analysis. Ensure continued adherence to data handling best practices, even when no direct PCI-DSS violation is identified."
  },
  "deterministic_compliance": {
    "compliance_risk_score": 0.01,
    "total_flags": 1,
    "auto_escalate": false,
    "flags": [
      {
        "keyword": "refund",
        "severity": "low",
        "context": "If I don't get it tomorrow, I want a full refund immediately. I can't afford to just lose ₹8,499 like this.",
        "policy_reference": "Refund Processing Policy",
        "action_required": false,
        "source": "deterministic"
      }
    ]
  },
  "error": null
}
```

---

## Sample 4 — Audio File Analysis

Upload an audio recording for native multimodal analysis (Gemini processes audio directly, no STT).

### Request
```bash
curl -X POST http://localhost:8000/api/v1/analyze/audio \
  -F "audio_file=@sample_call.mp3" \
  -F "client_id=banking"
```

### Response
Audio analysis returns the same JSON schema as text analysis. Processing time is typically 10-20 seconds depending on audio length.

---

## Sample 5 — Health Check

### Request
```bash
curl http://localhost:8000/health
```

### Response
```json
{
  "status": "healthy",
  "service": "NEXUS Conversation Intelligence",
  "model": "gemini-2.5-flash",
  "version": "1.0.0",
  "supported_inputs": [
    "audio/mp3",
    "audio/wav",
    "audio/ogg",
    "audio/m4a",
    "text/plain"
  ]
}
```

---

## Sample 6 — Phase 3 RAG Re-analysis

Feed any Phase 2 JSON output back through the RAG engine with different domain rules.

### Request
```bash
curl -X POST http://localhost:8000/api/v1/analyze/json_rag \
  -H "Content-Type: application/json" \
  -d '{
    "client_id": "banking",
    "analysis_data": {
      "summary": "Customer reports lost card and requests immediate blocking.",
      "compliance": {"risk_level": "high", "risk_flags": ["unauthorized_transaction_risk"]},
      "primary_intent": "request_card_block",
      "agent_performance": {"score": 0, "issue_resolved": false}
    }
  }'
```

### Response
Returns a structured action plan:
```json
{
  "status": "success",
  "client_id": "banking",
  "rag_actions": {
    "suggested_actions": [
      "Immediately block the customer's lost credit card to prevent fraudulent transactions.",
      "Initiate the standard fraud prevention protocol for lost cards."
    ],
    "priority": "P2 - High",
    "policy_justifications": [
      "Policy 2 (Fraud Triggers): The customer mentioned 'fraudulent transactions' and 'lost my credit card', which triggers the fraud policy requiring immediate action."
    ],
    "human_review_needed": true,
    "coaching_notes": "Ensure proper protocol for lost cards and fraud prevention is followed, and confirm resolution with the customer."
  }
}
```

---

## Key Observations From Real Outputs

| Sample | Risk Level | Agent Score | Deterministic Flags | AI Violations |
|--------|-----------|-------------|--------------------:|---------------|
| Insurance Mis-selling | **critical** | 15/100 | 1 (manager → medium) | 3 violations (misrepresentation, discouraging rights, pressure tactics) |
| Banking Fraud | medium | 0/100 | 1 (fraud → **high**, auto-escalate) | 0 |
| E-commerce Complaint | medium | **95/100** | 1 (refund → low) | 0 |

**Notice how the two-layer system works:**
- **Insurance mis-selling**: The deterministic engine caught "manager" as a medium keyword, but the **AI engine** caught the real violations (guaranteed returns, discouraging free look period) — things no keyword list could cover.
- **Banking fraud**: The deterministic engine immediately flagged "fraud" as high-severity and triggered `auto_escalate: true` — instant, reliable, no AI needed.
- **E-commerce complaint**: Agent scored 95/100 with detailed coaching — the AI recognized excellent empathy and resolution while the deterministic engine logged the refund mention as a low-priority flag for tracking.
