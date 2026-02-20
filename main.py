"""
Main FastAPI application file for VAJRA Phase 1.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes.analyze import router as analyze_router

app = FastAPI(
    title="VAJRA — Conversation Intelligence API",
    description="""
## Multimodal Conversation Intelligence Backend

Analyzes customer support conversations (audio or text) using **Gemini 2.5 Flash**
natively — no traditional STT pipeline required.

### Supported Input Types
- **Audio:** MP3, WAV, OGG, M4A, FLAC (max 25MB)
- **Text:** Plain conversation transcript (JSON)

### How It Works
1. POST audio or text to `/api/v1/analyze/*`
2. System validates and queues for Gemini analysis
3. Gemini detects language, extracts insights, checks compliance
4. Returns structured enterprise JSON
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

app.include_router(analyze_router, prefix="/api/v1", tags=["Conversation Analysis"])

@app.get("/health", tags=["System"])
def health_check():
    """
    Simple health check endpoint returning system status.
    """
    return {
        "status": "healthy",
        "service": "VAJRA Conversation Intelligence",
        "model": "gemini-2.5-flash",
        "version": "1.0.0",
        "supported_inputs": ["audio/mp3", "audio/wav", "audio/ogg", "audio/m4a", "text/plain"]
    }
