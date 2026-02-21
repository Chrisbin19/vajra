"""
VAJRA — Multimodal Conversation Intelligence Backend
Main FastAPI application entry point.

Phase 4 additions:
  - API key authentication via X-API-Key header
  - Compliance router registered at /api/v1/compliance/
  - UnicodeJSONResponse for Tamil/Hindi text support
"""
import os
import json
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from api.routes.analyze import router as analyze_router
from api.routes.compliance import router as compliance_router


class UnicodeJSONResponse(JSONResponse):
    def render(self, content) -> bytes:
        return json.dumps(
            content, ensure_ascii=False, allow_nan=False,
            indent=None, separators=(",", ":"),
        ).encode("utf-8")


EXEMPT_PATHS = {"/health", "/docs", "/redoc", "/openapi.json", "/favicon.ico"}

class APIKeyMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        if request.url.path in EXEMPT_PATHS or request.url.path.startswith("/docs"):
            return await call_next(request)
        expected_key = os.getenv("VAJRA_API_KEY")
        if not expected_key:
            return await call_next(request)
        provided_key = request.headers.get("X-API-Key")
        if provided_key != expected_key:
            return UnicodeJSONResponse(
                status_code=401,
                content={
                    "error": "Unauthorized",
                    "detail": "Invalid or missing API key. Include your key as 'X-API-Key' header.",
                    "docs": "Visit /docs to see all available endpoints."
                }
            )
        return await call_next(request)


app = FastAPI(
    title="VAJRA — Conversation Intelligence API",
    default_response_class=UnicodeJSONResponse,
    description="""
## Multimodal Conversation Intelligence Backend

Analyzes customer support conversations (audio or text) using **Gemini 2.5 Flash**
natively — no traditional speech-to-text or language-specific pipeline required.

### Authentication
All endpoints require an **X-API-Key** header.
```
X-API-Key: your-api-key-here
```

### How It Works
1. **Phase 1** — Input validation + UUID assignment
2. **Phase 2** — Gemini 2.5 Flash native analysis
3. **Phase 3** — RAG compliance action plan
4. **Phase 4** — Rule-based compliance violation detection

### Supported Clients
- `banking_client_01` — Banking domain (RBI compliance)
- `insurance_enterprise_v1` — Insurance domain (IRDAI compliance)
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(APIKeyMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_methods=["*"], allow_headers=["*"],
)

app.include_router(analyze_router, prefix="/api/v1", tags=["Conversation Analysis"])
app.include_router(compliance_router, prefix="/api/v1", tags=["Compliance"])


@app.get("/health", tags=["System"])
def health_check():
    """Health check — no API key required."""
    api_key_configured = bool(os.getenv("VAJRA_API_KEY"))
    return {
        "status": "healthy",
        "service": "VAJRA Conversation Intelligence",
        "model": "gemini-2.5-flash",
        "version": "1.0.0",
        "auth": {
            "required": api_key_configured,
            "header": "X-API-Key",
            "mode": "enforced" if api_key_configured else "dev_mode_disabled"
        },
        "phases": {
            "phase_1": "input validation + UUID assignment",
            "phase_2": "Gemini 2.5 Flash native multimodal analysis",
            "phase_3": "RAG compliance action plan",
            "phase_4": "Rule-based compliance violation detection",
        },
        "endpoints": {
            "text_analysis": "POST /api/v1/analyze/text",
            "audio_analysis": "POST /api/v1/analyze/audio",
            "rag_only": "POST /api/v1/analyze/json_rag",
            "compliance_check": "POST /api/v1/compliance/check",
            "docs": "GET /docs",
        },
        "supported_inputs": [
            "audio/mp3", "audio/wav", "audio/ogg",
            "audio/m4a", "audio/flac", "audio/aac", "audio/webm",
            "text/plain"
        ],
        "supported_clients": ["banking_client_01", "insurance_enterprise_v1"],
    }