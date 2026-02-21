# VAJRA — Multimodal Conversation Intelligence Backend

Analyzes customer support conversations (audio or text) using **Gemini 2.5 Flash** natively — no traditional speech-to-text or language-specific pipeline required.

## Quick Start
1. `pip install -r requirements.txt`
2. Configure `.env` with `GEMINI_API_KEY` and `VAJRA_API_KEY`
3. `uvicorn main:app --reload`

## Authentication
All endpoints require an **X-API-Key** header.
```
X-API-Key: vajra-2024-hackathon-transight
```

## Architecture Phases
- **Phase 1** — Input validation + UUID assignment
- **Phase 2** — Gemini 2.5 Flash native analysis
- **Phase 3** — RAG compliance action plan
- **Phase 4** — Rule-based compliance violation detection

## API Endpoints
| Endpoint | Method | Auth Required | Description |
| --- | --- | --- | --- |
| `/health` | GET | No | System health check |
| `/api/v1/analyze/audio` | POST | Yes | Analyze audio recording with Gemini |
| `/api/v1/analyze/text` | POST | Yes | Analyze text transcript with Gemini |
| `/api/v1/analyze/json_rag` | POST | Yes | Process via Phase 3 RAG |
| `/api/v1/compliance/check` | POST | Yes | Rule-based instant compliance check |
| `/docs` | GET | No | OpenAPI interactive documentation |

## Project Structure
```text
project/
├── api/
│   ├── models/
│   │   ├── request.py
│   │   └── response.py
│   └── routes/
│       ├── analyze.py
│       └── compliance.py
├── core/
│   ├── gemini.py
│   └── compliance_engine.py
├── data/
│   ├── config/
│   │   ├── banking_client_01.json
│   │   └── insurance_enterprise_v1.json
│   └── domain_knowledge/
│       ├── banking_rules.txt
│       └── insurance_rules.txt
├── main.py
└── .env.example
```

## Configuration Mechanism
The system adapts per enterprise via the `data/` directory configuration:
- `data/config/*.json` sets rules, severities, and expected domains.
- `data/domain_knowledge/*.txt` sets the specific compliance strings passed to the rule-based compliance engine and the Phase 3 RAG logic.

## Sample Requests

### Rule-based Compliance Check
```bash
curl -X POST "http://localhost:8000/api/v1/compliance/check" \
  -H "X-API-Key: vajra-2024-hackathon-transight" \
  -H "Content-Type: application/json" \
  -d '{
    "client_id": "banking_client_01",
    "transcript": "Agent: Good morning. Customer: I shared my OTP with someone and Rs.85000 was transferred.",
    "domain": "banking"
  }'
```

### Full AI Analysis (Text)
```bash
curl -X POST "http://localhost:8000/api/v1/analyze/text" \
  -H "X-API-Key: vajra-2024-hackathon-transight" \
  -H "Content-Type: application/json" \
  -d '{
    "client_id": "banking_client_01",
    "transcript": "Agent: Good morning State Bank support. Customer: There is an unauthorized transaction of Rs.4200 on my account."
  }'
```

## Bugs Fixed (Phase 4)
| Component | Issue | Fix |
| --- | --- | --- |
| `api/routes/analyze.py` | Crash when `client_id` is None | Resolved `client_id` inside explicit if/elif configuration check, avoiding `.strip()` on None. |
| `README.md` | Erroneously contained Python code | Replaced with robust Markdown documentation. |

## Limitations and Future Improvements
- Expand rule engine syntax.
- Extend test coverage.