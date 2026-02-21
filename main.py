"""
NEXUS — Multimodal Conversation Intelligence Backend
Main FastAPI application entry point.

Auth approach: FastAPI Security/Depends on each endpoint (NOT middleware).
  - Adds "Authorize 🔒" button to /docs Swagger UI automatically
  - Judges click Authorize, enter key once, all /docs requests work
  - /health and /docs remain public (no Depends on those routes)

Demo API Key : vajra-demo-key-2026
Header       : X-API-Key
"""
import os
import json
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from api.routes.analyze import router as analyze_router
from api.routes.compliance import router as compliance_router


class UnicodeJSONResponse(JSONResponse):
    """Ensures Tamil/Hindi characters are not escaped as \\uXXXX in responses."""
    def render(self, content) -> bytes:
        return json.dumps(
            content,
            ensure_ascii=False,
            allow_nan=False,
            indent=None,
            separators=(",", ":"),
        ).encode("utf-8")


app = FastAPI(
    title="VAJRA — Conversation Intelligence API",
    default_response_class=UnicodeJSONResponse,
    description="""
## Multimodal Conversation Intelligence Backend

Analyzes customer support conversations (audio or text) using **Gemini 2.5 Flash**
natively — no traditional speech-to-text or language-specific pipeline required.

---

### 🔑 Authentication

All endpoints require an **X-API-Key** header.

**Demo key:** `vajra-demo-key-2026`

> Click the **Authorize 🔒** button at the top-right of this page,
> enter the key, and all requests from /docs will include it automatically.

Override via `.env`: set `VAJRA_API_KEY=your-key`

---

### How It Works

| Phase | What happens |
|-------|-------------|
| **Phase 1** | FastAPI validates input, assigns `conversation_id` |
| **Phase 2** | Gemini 2.5 Flash analyzes natively — language, sentiment, intent, entities, compliance |
| **Phase 3** | Phase 2 JSON fed back to Gemini for RAG compliance action plan |
| **Phase 4** | Rule-based compliance engine — instant, zero API cost, <100ms |

---

### Supported Inputs
- **Audio:** MP3, WAV, OGG, M4A, FLAC, AAC, WebM (max 25MB)
- **Text:** JSON transcript (min 10 characters)

### Supported Clients
- `banking_client_01` — Banking domain (RBI compliance rules)
- `insurance_enterprise_v1` — Insurance domain (IRDAI compliance rules)
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS — allow all origins for hackathon/demo
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers — auth is on individual endpoints via Depends(verify_api_key)
app.include_router(analyze_router, prefix="/api/v1", tags=["Conversation Analysis"])
app.include_router(compliance_router, prefix="/api/v1", tags=["Compliance"])


@app.get("/health", tags=["System"])
def health_check():
    """
    System health check — **no API key required**.
    Returns service status, model info, and all supported endpoints.
    """
    demo_key = "vajra-demo-key-2026"
    env_key_set = bool(os.getenv("VAJRA_API_KEY"))
    return {
        "status": "healthy",
        "service": "NEXUS Conversation Intelligence",
        "model": "gemini-2.5-flash",
        "version": "1.0.0",
        "auth": {
            "required": True,
            "header": "X-API-Key",
            "demo_key": demo_key,
            "env_override_set": env_key_set,
            "note": "Use the Authorize button in /docs to set your key once",
        },
        "phases": {
            "phase_1": "Input validation + UUID assignment",
            "phase_2": "Gemini 2.5 Flash native multimodal analysis",
            "phase_3": "RAG compliance action plan",
            "phase_4": "Rule-based compliance violation detection",
        },
        "endpoints": {
            "text_analysis":    "POST /api/v1/analyze/text",
            "audio_analysis":   "POST /api/v1/analyze/audio",
            "rag_only":         "POST /api/v1/analyze/json_rag",
            "compliance_check": "POST /api/v1/compliance/check",
            "docs":             "GET  /docs",
            "health":           "GET  /health  (no auth)",
        },
        "supported_inputs": [
            "audio/mp3", "audio/wav", "audio/ogg",
            "audio/m4a", "audio/flac", "audio/aac", "audio/webm",
            "text/plain",
        ],
        "supported_clients": ["banking_client_01", "insurance_enterprise_v1"],
    }