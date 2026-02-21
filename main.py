"""
VAJRA — Multimodal Conversation Intelligence Backend
Main FastAPI application entry point.
"""
import json
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from api.routes.analyze import router as analyze_router

class UnicodeJSONResponse(JSONResponse):
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

### How It Works
1. POST audio or text to `/api/v1/analyze/*`
2. **Phase 1:** FastAPI validates input, assigns conversation_id
3. **Phase 2:** Gemini 2.5 Flash analyzes natively — detects language, extracts insights, checks compliance against client RAG policies
4. **Phase 3:** Phase 2 JSON fed back into Gemini for structured compliance action plan
5. Returns complete enterprise-grade JSON

### Supported Inputs
- **Audio:** MP3, WAV, OGG, M4A, FLAC, AAC, WebM (max 25MB)
- **Text:** JSON transcript (min 10 characters)

### Supported Clients
- `banking_client_01` — Core banking operations (RBI compliance)
- `insurance_enterprise_v1` — Insurance sales (IRDAI compliance)
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(analyze_router, prefix="/api/v1", tags=["Conversation Analysis"])


@app.get("/health", tags=["System"])
def health_check():
    """System health check — confirms server is running and model config is loaded."""
    return {
        "status": "healthy",
        "service": "VAJRA Conversation Intelligence",
        "model": "gemini-2.5-flash",
        "version": "1.0.0",
        "phases": {
            "phase_1": "input validation + UUID assignment",
            "phase_2": "Gemini 2.5 Flash native analysis",
            "phase_3": "RAG compliance action plan",
        },
        "supported_inputs": [
            "audio/mp3", "audio/wav", "audio/ogg",
            "audio/m4a", "audio/flac", "audio/aac", "audio/webm",
            "text/plain"
        ],
        "supported_clients": ["banking_client_01", "insurance_enterprise_v1"],
    }