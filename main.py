"""
Main FastAPI application file for VAJRA Phase 1.
"""
# ── Venv auto-bootstrap ───────────────────────────────────────────────────────
# If run with the wrong Python (no uvicorn/fastapi), automatically re-launch
# using the project's venv Python so things always just work.
import sys, os as _os

_venv_python = _os.path.join(_os.path.dirname(__file__), "venv", "Scripts", "python.exe")

def _has_uvicorn():
    try:
        import uvicorn  # noqa
        return True
    except ImportError:
        return False

if not _has_uvicorn() and _os.path.isfile(_venv_python):
    import subprocess as _sp
    print(f"[VAJRA] Re-launching with venv Python: {_venv_python}")
    _result = _sp.run([_venv_python] + sys.argv)
    sys.exit(_result.returncode)
elif not _has_uvicorn():
    print("[VAJRA] ERROR: uvicorn not found and no venv detected.")
    print("  Please activate the venv first:  venv\\Scripts\\activate")
    print("  Then run:  python main.py")
    sys.exit(1)
# ─────────────────────────────────────────────────────────────────────────────

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

def print_menu():
    print("=" * 50)
    print(" VAJRA — CONVERSATION INTELLIGENCE API ")
    print("=" * 50)
    print("\nWhat would you like to do?")
    print("1. Start the API Server (for Browser/Postman access)")
    print("2. Run Interactive Terminal Tester (Text/Audio)")
    print("3. Exit")

if __name__ == "__main__":
    import uvicorn
    import sys
    import subprocess
    
    while True:
        print_menu()
        choice = input("\nEnter your choice (1/2/3): ").strip()
        
        if choice == '1':
            print("\nStarting Uvicorn Server on http://127.0.0.1:8000 ...")
            print("Access the API docs in your browser at: http://127.0.0.1:8000/docs")
            uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
            break
        elif choice == '2':
            print("\nLaunching Interactive Tester...")
            subprocess.run([sys.executable, "test_interactive.py"])
        elif choice == '3':
            print("Goodbye!")
            break
        else:
            print("Invalid choice. Please try again.")
