"""
API routes for VAJRA Phase 2 (Gemini Integration).
"""
import os
import uuid
import aiofiles
from fastapi import APIRouter, File, UploadFile, Form, HTTPException
from api.models.request import TextAnalysisRequest
from api.models.response import ConversationAnalysisResult
import core.gemini as gemini_service

router = APIRouter()

ALLOWED_EXTENSIONS = {".mp3", ".wav", ".ogg", ".m4a", ".aac", ".webm", ".flac"}
MAX_FILE_SIZE_BYTES = 25 * 1024 * 1024  # 25MB — Gemini File API limit
TEMP_AUDIO_DIR = "temp_audio"
os.makedirs(TEMP_AUDIO_DIR, exist_ok=True)


import json

def _get_client_config(client_id: str) -> dict:
    """
    Returns client domain config from JSON file (migrated from transight).
    """
    config_path = os.path.join("data", "config", f"{client_id}.json")
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        # Default fallback if explicit config is not found
        return {
            "domain": "customer support",
            "company_name": client_id,
            "products": [],
            "risk_triggers": ["fraud", "escalation", "complaint"],
            "escalation_threshold": "medium",
        }


def _get_rag_policies(client_id: str) -> list[str]:
    """
    Returns compliance policies for the client from txt file (migrated from transight).
    """
    rules_path = os.path.join("data", "domain_knowledge", f"{client_id}_rules.txt")
    try:
        with open(rules_path, 'r') as f:
            content = f.read()
            # Split by newlines and filter out empty strings
            return [line.strip() for line in content.split('\n') if line.strip()]
    except FileNotFoundError:
        return [
            "Always acknowledge customer concern before providing solutions.",
            "Escalate unresolved issues after 10 minutes to supervisor."
        ]


def _validate_audio_file(filename: str, file_size: int) -> str:
    """
    Validates extension and size. Returns file_ext if valid.
    """
    _, ext = os.path.splitext(filename)
    file_ext = ext.lower()

    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: '{file_ext}'. Allowed formats: {sorted(list(ALLOWED_EXTENSIONS))}"
        )
    
    if file_size > MAX_FILE_SIZE_BYTES:
        mb_size = file_size / (1024 * 1024)
        raise HTTPException(
            status_code=413,
            detail=f"File too large: {mb_size:.2f}MB. Maximum allowed is {MAX_FILE_SIZE_BYTES / (1024*1024):.0f}MB."
        )

    return file_ext


@router.post(
    "/analyze/audio",
    response_model=ConversationAnalysisResult,
    status_code=200,
    summary="Analyze a customer call audio recording with Gemini",
    description="Uploads an audio file and returns a complete evaluation containing sentiment, entities, and agent performance."
)
async def analyze_audio(
    audio_file: UploadFile = File(...),
    client_id: str = Form(...),
):
    """
    Endpoint handling audio uploads. Validates the incoming audio file, saves it
    temporarily, and triggers Gemini analysis.
    """
    # ── Step 1: Read content and calculate size ──
    try:
        content = await audio_file.read()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read file: {str(e)}")
    
    file_size = len(content)
    await audio_file.seek(0)
    
    # ── Step 2: Validate extension and size ──
    file_ext = _validate_audio_file(audio_file.filename or "unknown", file_size)

    # ── Step 3: Generate ID ──
    conversation_id = str(uuid.uuid4())
    client_id_stripped = client_id.strip()

    # ── Step 4: Build path ──
    temp_path = os.path.join(TEMP_AUDIO_DIR, f"{conversation_id}{file_ext}")

    # ── Step 5: Save file ──
    try:
        async with aiofiles.open(temp_path, "wb") as f:
            await f.write(content)
    except Exception as e:
        print(f"Error saving file for {conversation_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to save audio to temp storage")

    # ── Step 6: Trigger Gemini Analysis (Phase 2) ──
    print(f"[Phase 2][{conversation_id}] Starting audio analysis pipeline...")
    client_config = _get_client_config(client_id_stripped)
    rag_policies = _get_rag_policies(client_id_stripped)
    
    result = await gemini_service.analyze_audio(
        conversation_id=conversation_id,
        client_id=client_id_stripped,
        audio_path=temp_path,
        client_config=client_config,
        rag_policies=rag_policies,
    )
    
    if result.status == "failed":
        raise HTTPException(status_code=500, detail=f"Analysis failed: {result.error}")
        
    # ── Step 7: Trigger Phase 3 RAG automatically ──
    print(f"[Phase 3][{conversation_id}] Automatically feeding Phase 2 JSON into Phase 3 RAG...")
    rag_actions = await gemini_service.analyze_json_for_rag(
        client_id=client_id_stripped,
        analysis_json=result.model_dump(),
        client_config=client_config,
        rag_policies=rag_policies
    )
    result.rag_actions = rag_actions
    
    return result


@router.post(
    "/analyze/text",
    response_model=ConversationAnalysisResult,
    status_code=200,
    summary="Analyze a text conversation transcript with Gemini",
    description="Accepts text-based customer transcripts and returns a complete evaluation containing sentiment, entities, and agent performance."
)
async def analyze_text(request: TextAnalysisRequest):
    """
    Endpoint handling text transcript submissions. Triggers Gemini analysis instantly.
    """
    # ── Step 1: Generate ID ──
    conversation_id = str(uuid.uuid4())
    client_id_stripped = request.client_id.strip()
    
    # ── Step 2: Trigger Gemini Analysis (Phase 2) ──
    print(f"[Phase 2][{conversation_id}] Starting text analysis pipeline...")
    client_config = _get_client_config(client_id_stripped)
    rag_policies = _get_rag_policies(client_id_stripped)
    
    result = await gemini_service.analyze_text(
        conversation_id=conversation_id,
        client_id=client_id_stripped,
        transcript=request.transcript,
        client_config=client_config,
        rag_policies=rag_policies,
    )
    
    
    if result.status == "failed":
        raise HTTPException(status_code=500, detail=f"Analysis failed: {result.error}")
        
    # ── Step 3: Trigger Phase 3 RAG automatically ──
    print(f"[Phase 3][{conversation_id}] Automatically feeding Phase 2 JSON into Phase 3 RAG...")
    rag_actions = await gemini_service.analyze_json_for_rag(
        client_id=client_id_stripped,
        analysis_json=result.model_dump(),
        client_config=client_config,
        rag_policies=rag_policies
    )
    result.rag_actions = rag_actions
        
    return result


from api.models.request import JsonRagRequest

@router.post(
    "/analyze/json_rag",
    status_code=200,
    summary="Process Phase 2 JSON output through Phase 3 RAG",
    description="Accepts the JSON output from a previous analysis and feeds it into the RAG system to generate a final recommendation based on domain rules."
)
async def analyze_json_rag(request: JsonRagRequest):
    """
    Endpoint handling JSON transcript submissions for Phase 3 RAG analysis.
    """
    client_id_stripped = request.client_id.strip()
    
    print(f"\n{'='*50}")
    print(f"[Phase 3] Starting Post-Analysis RAG for client: {client_id_stripped}")
    
    # Load domain config and rules
    client_config = _get_client_config(client_id_stripped)
    rag_policies = _get_rag_policies(client_id_stripped)
    
    # Call the new gemini service function
    result = await gemini_service.analyze_json_for_rag(
        client_id=client_id_stripped,
        analysis_json=request.analysis_data,
        client_config=client_config,
        rag_policies=rag_policies
    )
    
    # If the service returns the fallback error string, raise a 500
    if result.startswith("Phase 3 RAG Analysis Failed:"):
        raise HTTPException(status_code=500, detail=result)
        
    # Return the raw dict
    return {
        "status": "success",
        "client_id": client_id_stripped,
        "rag_actions": result.model_dump() if result else None
    }
