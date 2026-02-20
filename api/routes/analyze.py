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


def _get_client_config(client_id: str) -> dict:
    """
    Returns client domain config. 
    Phase 3 replaces this with a real SQLite query.
    """
    configs = {
        "banking_client_01": {
            "domain": "banking",
            "company_name": "State Bank",
            "products": ["savings account", "credit card", "debit card", "personal loan"],
            "risk_triggers": ["unauthorized transaction", "fraud", "OTP shared", "large transfer"],
            "escalation_threshold": "high",
        },
        "telecom_client_01": {
            "domain": "telecom", 
            "company_name": "Airtel",
            "products": ["prepaid", "postpaid", "broadband", "DTH"],
            "risk_triggers": ["SIM swap", "billing dispute", "service outage"],
            "escalation_threshold": "medium",
        }
    }
    return configs.get(client_id, {
        "domain": "customer support",
        "company_name": client_id,
        "products": [],
        "risk_triggers": ["fraud", "escalation", "complaint"],
        "escalation_threshold": "medium",
    })


def _get_rag_policies(client_id: str) -> list[str]:
    """
    Returns compliance policies for the client.
    Phase 3 replaces this with a real ChromaDB query.
    """
    banking_policies = [
        "Identity Verification: Verify customer with account number + OTP before sharing account details.",
        "Call Recording Disclosure: Inform customer about call recording within first 30 seconds.",
        "Fraud Dispute SLA: Escalate unauthorized transaction disputes above Rs.10,000 within 24 hours.",
        "Card Blocking Protocol: Offer immediate card blocking for unauthorized transaction reports.",
        "Data Privacy: Never read full account numbers over phone — only last 4 digits.",
        "Chargeback Policy: Customer has 30 days from transaction to raise dispute.",
        "Empathy Requirement: Acknowledge frustration and apologize before technical resolution.",
    ]
    telecom_policies = [
        "SIM Swap Verification: Require 3 forms of ID for SIM swap requests.",
        "Billing Dispute SLA: Acknowledge within 24 hours, resolve within 7 days.",
        "Outage Communication: Proactively inform of known outages and ETA.",
    ]
    if "banking" in client_id.lower():
        return banking_policies
    elif "telecom" in client_id.lower():
        return telecom_policies
    return ["Always acknowledge customer concern before providing solutions.",
            "Escalate unresolved issues after 10 minutes to supervisor."]


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
        
    return result
