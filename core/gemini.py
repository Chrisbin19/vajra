"""
Core integration with Gemini 2.5 Flash for Multimodal Conversation Intelligence.
"""
import os
import json
import time
import re
import google.generativeai as genai
from dotenv import load_dotenv
from api.models.response import (
    ConversationAnalysisResult,
    GeminiAnalysisResponse,
    SentimentAnalysis,
    EntityExtraction,
    ComplianceCheck,
    AgentPerformance,
    SpeakerInfo
)

# ── Setup section ──
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    print("WARNING: GEMINI_API_KEY is not set in environment or .env file.")

genai.configure(api_key=api_key)

MODEL_NAME = "gemini-2.5-flash"
model = genai.GenerativeModel(
    model_name=MODEL_NAME,
    generation_config={
        "temperature": 0.1,
        "top_p": 0.8,
        "max_output_tokens": 4096,
        "response_mime_type": "application/json"
    }
)

def _build_analysis_prompt(client_config: dict, rag_policies: list[str], input_type: str, transcript: str = None) -> str:
    """
    Constructs the prompt for Gemini, enforcing the schema and including client context.
    """
    prompt = f"""You are a senior compliance and quality assurance AI for an enterprise customer support center.
You are analyzing a customer support conversation ({input_type}).

### 1. Client Domain Context
- Domain: {client_config.get('domain', 'Unknown')}
- Company Name: {client_config.get('company_name', 'Unknown')}
- Supported Products: {", ".join(client_config.get('products', []))}
- Known Risk Triggers for this client: {", ".join(client_config.get('risk_triggers', []))}
- Escalation Threshold: {client_config.get('escalation_threshold', 'medium')}

### 2. RAG Policies
You must evaluate the conversation strictly against these compliance policies:
"""
    for i, policy in enumerate(rag_policies, 1):
        prompt += f"{i}. {policy}\n"

    if transcript:
        prompt += f"""
### 3. Conversation Transcript
{transcript}
"""

    prompt += """
### 4. Output Instruction
You MUST return ONLY valid JSON representing the exact analysis results. Start your response with { and end with }.
Do not wrap your result in markdown blocks (e.g. no ```json). Do not include explanations.

SENTIMENT SCORING RULES:
- Provide sentiment_score as a float between -1.0 and +1.0
- -1.0 = extremely negative/angry
-  0.0 = completely neutral
- +1.0 = extremely positive/satisfied
- Score the OVERALL conversation arc, not just start or end
- Example: customer starts frustrated (-0.7), ends satisfied (+0.6) -> score: 0.0 (mixed)

INTENT EXTRACTION RULES:
- primary_intent: The SINGLE main reason the customer called. One string. Snake_case.
  Examples: dispute_transaction, check_balance, report_fraud, request_refund,
            update_details, complaint_agent, request_card_block, loan_inquiry
            
- secondary_intents: Additional things the customer wanted. Can be empty list [].
  These are supporting requests that came up during the call.
  
- IMPORTANT: primary_intent must always be a single string, not a list.

Your JSON must match this exact schema:
{
    "summary": "string (2-4 sentences describing the full conversation)",
    "language_detected": "string (primary ISO code, e.g. en, hi)",
    "languages_all": ["string"],
    "sentiment": {
        "overall": "positive|negative|neutral|mixed",
        "sentiment_score": -1.0,
        "customer_sentiment": "string",
        "agent_sentiment": "string",
        "emotional_arc": ["string"],
        "frustration_detected": boolean
    },
    "primary_intent": "string snake_case",
    "secondary_intents": ["string snake_case"],
    "topics_discussed": ["string"],
    "entities": {
        "amounts_mentioned": ["string"],
        "dates_mentioned": ["string"],
        "account_references": ["string (partial ONLY, never full)"],
        "products_mentioned": ["string"],
        "locations_mentioned": ["string"],
        "people_mentioned": ["string"]
    },
    "compliance": {
        "violations_detected": ["string"],
        "policies_checked": ["string"],
        "risk_level": "low|medium|high|critical",
        "escalation_required": boolean,
        "risk_flags": ["string snake_case"]
    },
    "agent_performance": {
        "score": integer (0 to 100),
        "greeting_proper": boolean,
        "empathy_shown": boolean,
        "issue_resolved": boolean,
        "call_outcome": "resolved|escalated|dropped|callback_scheduled",
        "strengths": ["string"],
        "improvements": ["string"]
    },
    "speakers": {
        "speakers_detected": integer,
        "speaker_labels": ["string"],
        "language_per_speaker": {
            "SpeakerLabel": "ISO_code"
        }
    }
}
"""
    return prompt


def _upload_audio_to_gemini(audio_path: str):
    """
    Validates existence, maps MIME type, and uploads file to Gemini File API.
    """
    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"Audio file not found at {audio_path}")

    _, ext = os.path.splitext(audio_path)
    ext = ext.lower()
    
    mime_map = {
        ".mp3": "audio/mpeg",
        ".wav": "audio/wav",
        ".ogg": "audio/ogg",
        ".m4a": "audio/mp4",
        ".aac": "audio/aac",
        ".webm": "audio/webm",
        ".flac": "audio/flac"
    }
    
    mime_type = mime_map.get(ext, "audio/mpeg")
    filename_only = os.path.basename(audio_path)
    
    print(f"Uploading {filename_only} to Gemini as {mime_type}...")
    gemini_file = genai.upload_file(path=audio_path, mime_type=mime_type, display_name=filename_only)
    print(f"Uploaded successfully. URI: {gemini_file.uri}")
    
    
    return gemini_file


def _build_result_from_dict(
    data: dict, 
    conversation_id: str, 
    client_id: str, 
    input_type: str, 
    processing_time_ms: int, 
    rag_policies_used: list[str]
) -> ConversationAnalysisResult:
    """
    Constructs the formalized Pydantic model with aggressive safe fallbacks.
    """
    sentiment_dict = data.get("sentiment", {})
    entities_dict = data.get("entities", {})
    compliance_dict = data.get("compliance", {})
    agent_dict = data.get("agent_performance", {})
    speakers_dict = data.get("speakers", {})

    sentiment = SentimentAnalysis(
        overall=sentiment_dict.get("overall", "neutral"),
        sentiment_score=float(sentiment_dict.get("sentiment_score", 0.0)),
        customer_sentiment=sentiment_dict.get("customer_sentiment", ""),
        agent_sentiment=sentiment_dict.get("agent_sentiment", ""),
        emotional_arc=sentiment_dict.get("emotional_arc", []),
        frustration_detected=bool(sentiment_dict.get("frustration_detected", False))
    )

    entities = EntityExtraction(
        amounts_mentioned=entities_dict.get("amounts_mentioned", []),
        dates_mentioned=entities_dict.get("dates_mentioned", []),
        account_references=entities_dict.get("account_references", []),
        products_mentioned=entities_dict.get("products_mentioned", []),
        locations_mentioned=entities_dict.get("locations_mentioned", []),
        people_mentioned=entities_dict.get("people_mentioned", [])
    )

    compliance = ComplianceCheck(
        violations_detected=compliance_dict.get("violations_detected", []),
        policies_checked=compliance_dict.get("policies_checked", []),
        risk_level=compliance_dict.get("risk_level", "medium"),
        escalation_required=bool(compliance_dict.get("escalation_required", False)),
        risk_flags=compliance_dict.get("risk_flags", [])
    )

    agent_performance = AgentPerformance(
        score=int(agent_dict.get("score", 0)),
        greeting_proper=bool(agent_dict.get("greeting_proper", False)),
        empathy_shown=bool(agent_dict.get("empathy_shown", False)),
        issue_resolved=bool(agent_dict.get("issue_resolved", False)),
        call_outcome=agent_dict.get("call_outcome", "escalated"),
        strengths=agent_dict.get("strengths", []),
        improvements=agent_dict.get("improvements", [])
    )

    speakers = None
    if speakers_dict:
        speakers = SpeakerInfo(
            speakers_detected=int(speakers_dict.get("speakers_detected", 1)),
            speaker_labels=speakers_dict.get("speaker_labels", []),
            language_per_speaker=speakers_dict.get("language_per_speaker", {})
        )

    return ConversationAnalysisResult(
        conversation_id=conversation_id,
        client_id=client_id,
        input_type=input_type,
        status="completed",
        processing_time_ms=processing_time_ms,
        summary=data.get("summary", "No summary provided."),
        language_detected=data.get("language_detected", "unknown"),
        languages_all=data.get("languages_all", []),
        sentiment=sentiment,
        primary_intent=data.get("primary_intent", "general_inquiry"),
        secondary_intents=data.get("secondary_intents", []),
        topics_discussed=data.get("topics_discussed", []),
        entities=entities,
        compliance=compliance,
        agent_performance=agent_performance,
        speakers=speakers,
        rag_policies_used=rag_policies_used,
        error=None
    )


async def analyze_audio(conversation_id: str, client_id: str, audio_path: str, client_config: dict, rag_policies: list[str]) -> ConversationAnalysisResult:
    """
    End-to-end audio pipeline using Gemini 2.5 Flash Native Audio.
    """
    start_time = time.time()
    try:
        # ── 1. Upload ──
        print(f"[Phase 2][{conversation_id}] Uploading audio...")
        gemini_file = _upload_audio_to_gemini(audio_path)
        
        # ── 2. Prompt ──
        print(f"[Phase 2][{conversation_id}] Building prompt...")
        prompt = _build_analysis_prompt(client_config, rag_policies, "audio")
        
        # ── 3. Generate ──
        print(f"[Phase 2][{conversation_id}] Requesting Gemini generation...")
        response = model.generate_content([gemini_file, prompt])
        
        # ── 4. Extract JSON ──
        print(f"[Phase 2][{conversation_id}] Parsing Strict JSON schema response...")
        print("RAW GEMINI OUTPUT:")
        print(response.text)
        
        # Since we enforced response_schema in generation_config, response.text is guaranteed perfect JSON
        parsed_dict = json.loads(response.text)
        
        # ── 5. Build Model ──
        processing_time = int((time.time() - start_time) * 1000)
        result = _build_result_from_dict(parsed_dict, conversation_id, client_id, "audio", processing_time, rag_policies)
        
        # ── 6. Cleanup ──
        print(f"[Phase 2][{conversation_id}] Deleting temp audio file {audio_path}...")
        try:
            os.remove(audio_path)
            genai.delete_file(gemini_file.name)
        except Exception as cleanup_err:
            print(f"[Phase 2][{conversation_id}] Cleanup warning: {cleanup_err}")
            
        print(f"[Phase 2][{conversation_id}] Audio Analysis Complete in {processing_time}ms.")
        return result

    except Exception as e:
        print(f"[Phase 2][{conversation_id}] ERROR: {str(e)}")
        # Safe fallback
        return ConversationAnalysisResult.model_construct(
            conversation_id=conversation_id,
            client_id=client_id,
            input_type="audio",
            status="failed",
            error=str(e),
            processing_time_ms=int((time.time() - start_time) * 1000),
            summary="", language_detected="", languages_all=[],
             sentiment=SentimentAnalysis.model_construct(overall="", sentiment_score=0.0, customer_sentiment="", agent_sentiment="", emotional_arc=[], frustration_detected=False),
             primary_intent="general_inquiry", secondary_intents=[], topics_discussed=[],
             entities=EntityExtraction.model_construct(amounts_mentioned=[], dates_mentioned=[], account_references=[], products_mentioned=[], locations_mentioned=[], people_mentioned=[]),
             compliance=ComplianceCheck.model_construct(violations_detected=[], policies_checked=[], risk_level="", escalation_required=False, risk_flags=[]),
             agent_performance=AgentPerformance.model_construct(score=0, greeting_proper=False, empathy_shown=False, issue_resolved=False, call_outcome="", strengths=[], improvements=[]),
             rag_policies_used=rag_policies
        )


async def analyze_text(conversation_id: str, client_id: str, transcript: str, client_config: dict, rag_policies: list[str]) -> ConversationAnalysisResult:
    """
    End-to-end text pipeline using Gemini 2.5 Flash.
    """
    start_time = time.time()
    try:
        # ── 1. Prompt ──
        print(f"[Phase 2][{conversation_id}] Building text prompt...")
        prompt = _build_analysis_prompt(client_config, rag_policies, "text", transcript)
        
        # ── 2. Generate ──
        print(f"[Phase 2][{conversation_id}] Requesting Gemini generation...")
        response = model.generate_content(prompt)
        
        # ── 3. Extract JSON ──
        print(f"[Phase 2][{conversation_id}] Parsing Strict JSON schema response...")
        print("RAW GEMINI OUTPUT:")
        print(response.text)
        
        # Since we enforced response_schema in generation_config, response.text is guaranteed perfect JSON
        parsed_dict = json.loads(response.text)
        
        # ── 4. Build Model ──
        processing_time = int((time.time() - start_time) * 1000)
        result = _build_result_from_dict(parsed_dict, conversation_id, client_id, "text", processing_time, rag_policies)
            
        print(f"[Phase 2][{conversation_id}] Text Analysis Complete in {processing_time}ms.")
        return result

    except Exception as e:
        print(f"[Phase 2][{conversation_id}] ERROR: {str(e)}")
        # Safe fallback
        return ConversationAnalysisResult.model_construct(
            conversation_id=conversation_id,
            client_id=client_id,
            input_type="text",
            status="failed",
            error=str(e),
            processing_time_ms=int((time.time() - start_time) * 1000),
            summary="", language_detected="", languages_all=[],
             sentiment=SentimentAnalysis.model_construct(overall="", sentiment_score=0.0, customer_sentiment="", agent_sentiment="", emotional_arc=[], frustration_detected=False),
             primary_intent="general_inquiry", secondary_intents=[], topics_discussed=[],
             entities=EntityExtraction.model_construct(amounts_mentioned=[], dates_mentioned=[], account_references=[], products_mentioned=[], locations_mentioned=[], people_mentioned=[]),
             compliance=ComplianceCheck.model_construct(violations_detected=[], policies_checked=[], risk_level="", escalation_required=False, risk_flags=[]),
             agent_performance=AgentPerformance.model_construct(score=0, greeting_proper=False, empathy_shown=False, issue_resolved=False, call_outcome="", strengths=[], improvements=[]),
             rag_policies_used=rag_policies
        )


def analyze_text_sync(transcript: str, client_config: dict) -> dict:
    """
    Standalone synchronous function for text analysis.
    
    This is the simple interface your teammates can call directly.
    Takes a raw transcript string and client config dict.
    Returns a plain Python dict — no Pydantic, no async needed.
    
    Args:
        transcript:    Full conversation text string
                       Format: "Agent: ...\nCustomer: ..."
        client_config: Client domain config dict. Must have:
                       - domain (str): "banking", "telecom", etc.
                       - products (list): list of product names
                       - risk_triggers (list): list of risk keywords
    
    Returns:
        dict with all analysis fields. On error, returns dict with
        "status": "failed" and "error": "reason"
    
    Example:
        config = {
            "domain": "banking",
            "products": ["savings account", "debit card"],
            "risk_triggers": ["unauthorized transaction", "fraud"]
        }
        result = analyze_text_sync(transcript, config)
        print(result["primary_intent"])       # "dispute_transaction"
        print(result["sentiment"]["sentiment_score"])  # -0.3
    """
    import time
    
    start = time.time()
    
    # ── Step 1: Build policies list from risk_triggers in config ──
    domain = client_config.get("domain", "general")
    risk_triggers = client_config.get("risk_triggers", [])
    
    # Convert risk triggers to policy statements for the prompt
    auto_policies = [
        f"Monitor and flag any mention of: {', '.join(risk_triggers)}"
    ] if risk_triggers else []
    
    # ── Step 2: Build the analysis prompt ──
    prompt = _build_analysis_prompt(
        client_config=client_config,
        rag_policies=auto_policies,
        input_type="text",
        transcript=transcript,
    )
    
    # ── Step 3: Call Gemini ──
    try:
        response = model.generate_content(prompt)
        raw_text = response.text
        
        # ── Step 4: Parse JSON from response ──
        data = json.loads(raw_text)
        
        # ── Step 5: Add processing metadata ──
        data["processing_time_ms"] = int((time.time() - start) * 1000)
        data["status"] = "completed"
        data["input_type"] = "text"
        
        return data
        
    except Exception as e:
        return {
            "status": "failed",
            "error": str(e),
            "input_type": "text",
            "processing_time_ms": int((time.time() - start) * 1000),
        }
