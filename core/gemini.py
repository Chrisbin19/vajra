"""
Core integration with Gemini 2.5 Flash for Multimodal Conversation Intelligence.

BUGS FIXED IN THIS VERSION:
  FIX 1: MODEL_NAME corrected to stable preview string
  FIX 2: response_mime_type REMOVED from main model — it breaks audio input
  FIX 3: JSON parsing now uses 3-layer fallback (handles markdown wrapping)
  FIX 4: genai.delete_file replaced with safe try/except cleanup
"""
import os
import json
import time
import re
import google.generativeai as genai
from dotenv import load_dotenv
from api.models.response import (
    ConversationAnalysisResult,
    SentimentAnalysis,
    EntityExtraction,
    ComplianceCheck,
    AgentPerformance,
    SpeakerInfo,
    RagActions,
)
from typing import Optional

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    print("WARNING: GEMINI_API_KEY is not set in .env file.")

genai.configure(api_key=api_key)

# FIX 1: Use the standard 2.5 flash model name
MODEL_NAME = "gemini-2.5-flash"

# FIX 2: NO response_mime_type in the main model config.
# response_mime_type="application/json" BREAKS audio analysis because
# Gemini cannot enforce JSON output when the input contains an audio File object.
# We handle JSON extraction manually via _extract_json_from_response().
model = genai.GenerativeModel(
    model_name=MODEL_NAME,
    generation_config={
        "temperature": 0.1,
        "top_p": 0.8,
        "max_output_tokens": 4096,
        # DO NOT add response_mime_type here — breaks audio
    }
)


def _build_analysis_prompt(
    client_config: dict,
    rag_policies: list[str],
    input_type: str,
    transcript: str = None
) -> str:
    """
    Builds the master Gemini prompt with client domain context + RAG policies.

    Structure:
      Section 1 — Client context (domain, products, risk triggers)
      Section 2 — RAG compliance policies (numbered for reference)
      Section 3 — Conversation transcript (text input only)
      Section 4 — Strict JSON output schema with rules
    """
    domain = client_config.get('domain', 'customer support')
    company = client_config.get('company_name', 'Unknown Company')
    products = ", ".join(client_config.get('products', []))
    risk_triggers = ", ".join(client_config.get('risk_triggers', []))
    escalation_threshold = client_config.get('escalation_threshold', 'medium')

    policies_block = ""
    for i, policy in enumerate(rag_policies, 1):
        policies_block += f"{i}. {policy}\n"

    domain = client_config.get("industry", client_config.get("domain", "general"))
    domain_instruction = ""
    if domain == "insurance":
        domain_instruction = """
### Insurance Compliance Layer
This is an insurance sales or support call. Apply these additional checks:
1. Did agent disclose free-look period? If not, flag as IRDAI PPI Reg 7(5) violation.
2. Did agent promise guaranteed or fixed returns? Flag as IRDAI PPI Reg 15(1) violation.
3. Did agent describe investment product as risk-free? Flag as Suitability Rule violation.
4. Did agent use urgency pressure tactics? Flag as IRDAI Pressure Tactics violation.
5. Did agent disclose exclusions and pre-existing condition waiting periods?
For each violation: include verbatim_quote from transcript, regulation reference, severity.
Agent score for calls with 3+ violations must be in 10-35 range.
"""

    transcript_block = ""
    if transcript and input_type == "text":
        transcript_block = f"\n### 3. Conversation Transcript\n{transcript}\n"

    prompt = f"""You are a senior compliance and quality assurance AI for an enterprise customer support center.
You are analyzing a customer support conversation ({input_type} input).

### 1. Client Domain Context
- Domain: {domain}
- Company Name: {company}
- Supported Products: {products}
- Known Risk Triggers: {risk_triggers}
- Escalation Threshold: {escalation_threshold}

### 2. Compliance Policies (RAG Retrieved — check conversation against EACH one)
{policies_block}{domain_instruction}{transcript_block}

### 4. Analysis Instructions

SENTIMENT SCORING:
- sentiment_score: float -1.0 to +1.0
- -1.0 = extremely negative/angry, 0.0 = neutral, +1.0 = extremely positive
- Score the OVERALL arc of the conversation
- emotional_arc: list of words e.g. ["frustrated", "neutral", "satisfied"]

INTENT EXTRACTION:
- primary_intent: ONE snake_case string — single main reason customer called
  Examples: dispute_transaction, check_balance, report_fraud, request_refund,
            update_details, complaint_agent, request_card_block, loan_inquiry
- secondary_intents: list of additional requests ([] if none)
- primary_intent MUST be a single string, never a list

COMPLIANCE CHECK:
- Review EVERY numbered policy above against what happened
- violations_detected: quote the policy number and what was breached
- risk_flags: snake_case e.g. unauthorized_transaction, fraud_mention

### 5. Required Output
Return ONLY valid JSON. No markdown. No explanation. No code blocks.
Start your response with {{ and end with }}.

{{
    "summary": "2-4 sentence factual summary of the full conversation",
    "language_detected": "ISO code e.g. en, hi, ta",
    "languages_all": ["en"],
    "sentiment": {{
        "overall": "positive|negative|neutral|mixed",
        "sentiment_score": 0.0,
        "customer_sentiment": "description of customer emotional state",
        "agent_sentiment": "description of agent tone",
        "emotional_arc": ["word1", "word2"],
        "frustration_detected": false
    }},
    "primary_intent": "snake_case_string",
    "secondary_intents": ["snake_case"],
    "topics_discussed": ["topic1", "topic2"],
    "entities": {{
        "amounts_mentioned": ["Rs.4200"],
        "dates_mentioned": ["January 14th"],
        "account_references": ["xxxx7823"],
        "products_mentioned": ["debit card"],
        "locations_mentioned": [],
        "people_mentioned": ["Priya"]
    }},
    "compliance": {{
        "violations_detected": [],
        "policies_checked": ["policy name"],
        "risk_level": "low|medium|high|critical",
        "escalation_required": false,
        "risk_flags": ["snake_case_flag"]
    }},
    "agent_performance": {{
        "score": 85,
        "greeting_proper": true,
        "empathy_shown": true,
        "issue_resolved": true,
        "call_outcome": "resolved|escalated|dropped|callback_scheduled",
        "strengths": ["specific strength"],
        "improvements": ["specific area"]
    }},
    "speakers": {{
        "speakers_detected": 2,
        "speaker_labels": ["Agent", "Customer"],
        "language_per_speaker": {{"Agent": "en", "Customer": "en"}}
    }}
}}

CRITICAL RULES:
- Never hallucinate. Use [] for data not present in the conversation.
- Never include full account numbers — only last 4 digits with xxxx prefix.
- score must be integer 0-100.
- risk_level must be exactly: low, medium, high, or critical.
- call_outcome must be exactly: resolved, escalated, dropped, or callback_scheduled.
"""
    return prompt


# FIX 3: 3-layer JSON fallback parser
def _extract_json_from_response(raw_text: str) -> dict:
    """
    Safely extracts and parses JSON from Gemini's response.

    Why needed: Even with "return ONLY JSON" instructions, Gemini sometimes
    wraps output in ```json ... ``` markdown blocks. This handles all cases.

    Strategy 1: Direct json.loads — ideal case
    Strategy 2: Strip markdown ```json ... ``` code block
    Strategy 3: Regex extract first { ... } object
    """
    # Strategy 1: Direct parse
    try:
        return json.loads(raw_text.strip())
    except json.JSONDecodeError:
        pass

    # Strategy 2: Strip markdown code block
    code_block = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", raw_text, re.DOTALL)
    if code_block:
        try:
            return json.loads(code_block.group(1))
        except json.JSONDecodeError:
            pass

    # Strategy 3: Extract first { to last }
    brace_match = re.search(r"\{.*\}", raw_text, re.DOTALL)
    if brace_match:
        try:
            return json.loads(brace_match.group())
        except json.JSONDecodeError:
            pass

    raise ValueError(
        f"Could not parse JSON from Gemini response. "
        f"First 300 chars: {raw_text[:300]}"
    )


def _upload_audio_to_gemini(audio_path: str):
    """
    Uploads audio file to Gemini File API with correct MIME type mapping.
    Returns the Gemini File object used in generate_content().
    """
    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"Audio file not found at: {audio_path}")

    _, ext = os.path.splitext(audio_path)
    mime_map = {
        ".mp3": "audio/mpeg",
        ".wav": "audio/wav",
        ".ogg": "audio/ogg",
        ".m4a": "audio/mp4",
        ".aac": "audio/aac",
        ".webm": "audio/webm",
        ".flac": "audio/flac",
    }
    mime_type = mime_map.get(ext.lower(), "audio/mpeg")
    filename = os.path.basename(audio_path)

    print(f"[Gemini] Uploading {filename} ({mime_type})...")
    gemini_file = genai.upload_file(
        path=audio_path,
        mime_type=mime_type,
        display_name=filename,
    )
    print(f"[Gemini] Uploaded. URI: {gemini_file.uri}")
    return gemini_file


def _build_result_from_dict(
    data: dict,
    conversation_id: str,
    client_id: str,
    input_type: str,
    processing_time_ms: int,
    rag_policies_used: list[str],
) -> ConversationAnalysisResult:
    """
    Converts raw Gemini JSON dict → validated ConversationAnalysisResult.
    Uses .get() with safe defaults everywhere — never crashes on missing fields.
    """
    s = data.get("sentiment", {})
    e = data.get("entities", {})
    c = data.get("compliance", {})
    a = data.get("agent_performance", {})
    sp = data.get("speakers", {})

    sentiment = SentimentAnalysis(
        overall=s.get("overall", "neutral"),
        sentiment_score=float(s.get("sentiment_score", 0.0)),
        customer_sentiment=s.get("customer_sentiment", ""),
        agent_sentiment=s.get("agent_sentiment", ""),
        emotional_arc=s.get("emotional_arc", []),
        frustration_detected=bool(s.get("frustration_detected", False)),
    )
    entities = EntityExtraction(
        amounts_mentioned=e.get("amounts_mentioned", []),
        dates_mentioned=e.get("dates_mentioned", []),
        account_references=e.get("account_references", []),
        products_mentioned=e.get("products_mentioned", []),
        locations_mentioned=e.get("locations_mentioned", []),
        people_mentioned=e.get("people_mentioned", []),
    )
    compliance = ComplianceCheck(
        violations_detected=c.get("violations_detected", []),
        policies_checked=c.get("policies_checked", []),
        risk_level=c.get("risk_level", "low"),
        escalation_required=bool(c.get("escalation_required", False)),
        risk_flags=c.get("risk_flags", []),
    )
    agent_performance = AgentPerformance(
        score=int(a.get("score", 0)),
        greeting_proper=bool(a.get("greeting_proper", False)),
        empathy_shown=bool(a.get("empathy_shown", False)),
        issue_resolved=bool(a.get("issue_resolved", False)),
        call_outcome=a.get("call_outcome", "escalated"),
        strengths=a.get("strengths", []),
        improvements=a.get("improvements", []),
    )
    speakers = None
    if sp:
        speakers = SpeakerInfo(
            speakers_detected=int(sp.get("speakers_detected", 2)),
            speaker_labels=sp.get("speaker_labels", ["Agent", "Customer"]),
            language_per_speaker=sp.get("language_per_speaker", {}),
        )

    return ConversationAnalysisResult(
        conversation_id=conversation_id,
        client_id=client_id,
        input_type=input_type,
        status="completed",
        processing_time_ms=processing_time_ms,
        summary=data.get("summary", "No summary available."),
        language_detected=data.get("language_detected", "en"),
        languages_all=data.get("languages_all", ["en"]),
        sentiment=sentiment,
        primary_intent=data.get("primary_intent", "general_inquiry"),
        secondary_intents=data.get("secondary_intents", []),
        topics_discussed=data.get("topics_discussed", []),
        entities=entities,
        compliance=compliance,
        agent_performance=agent_performance,
        speakers=speakers,
        rag_policies_used=rag_policies_used,
        error=None,
    )


def _make_failed_result(conversation_id, client_id, input_type, start_time, rag_policies, error):
    """Safe fallback result — server never crashes, always returns a valid response."""
    return ConversationAnalysisResult(
        conversation_id=conversation_id,
        client_id=client_id,
        input_type=input_type,
        status="failed",
        processing_time_ms=int((time.time() - start_time) * 1000),
        summary="",
        language_detected="",
        languages_all=[],
        sentiment=SentimentAnalysis(
            overall="neutral", sentiment_score=0.0,
            customer_sentiment="", agent_sentiment="",
            emotional_arc=[], frustration_detected=False,
        ),
        primary_intent="general_inquiry",
        secondary_intents=[],
        topics_discussed=[],
        entities=EntityExtraction(
            amounts_mentioned=[], dates_mentioned=[], account_references=[],
            products_mentioned=[], locations_mentioned=[], people_mentioned=[],
        ),
        compliance=ComplianceCheck(
            violations_detected=[], policies_checked=[],
            risk_level="low", escalation_required=False, risk_flags=[],
        ),
        agent_performance=AgentPerformance(
            score=0, greeting_proper=False, empathy_shown=False,
            issue_resolved=False, call_outcome="dropped",
            strengths=[], improvements=[],
        ),
        rag_policies_used=rag_policies,
        error=str(error),
    )


async def analyze_audio(
    conversation_id: str,
    client_id: str,
    audio_path: str,
    client_config: dict,
    rag_policies: list[str],
) -> ConversationAnalysisResult:
    """
    Full audio pipeline:
    1. Upload audio to Gemini File API
    2. Build prompt with client context + RAG policies
    3. Call model.generate_content([audio_file, prompt]) — native audio
    4. Parse JSON with 3-layer fallback
    5. Return validated ConversationAnalysisResult
    6. Cleanup temp files safely
    """
    start_time = time.time()
    print(f"\n[Phase 2][{conversation_id}] Starting AUDIO analysis...")
    gemini_file = None

    try:
        # 1. Upload
        gemini_file = _upload_audio_to_gemini(audio_path)

        # 2. Prompt
        prompt = _build_analysis_prompt(client_config, rag_policies, "audio")
        print(f"[Phase 2][{conversation_id}] Sending to {MODEL_NAME}...")

        # 3. Generate — audio file + text prompt together
        response = model.generate_content([gemini_file, prompt])
        print(f"[Phase 2][{conversation_id}] Response received. Parsing...")

        # 4. FIX 3: Parse with 3-layer fallback
        data = _extract_json_from_response(response.text)

        # 5. Build result
        processing_time_ms = int((time.time() - start_time) * 1000)
        result = _build_result_from_dict(
            data, conversation_id, client_id, "audio",
            processing_time_ms, rag_policies
        )

        # 6. FIX 4: Safe cleanup — genai.delete_file doesn't always exist
        try:
            if os.path.exists(audio_path):
                os.remove(audio_path)
        except Exception:
            pass
        try:
            gemini_file.delete()  # preferred method in current SDK
        except AttributeError:
            try:
                genai.delete_file(gemini_file.name)  # older SDK fallback
            except Exception:
                pass  # cleanup is best-effort, never crash on it

        print(f"[Phase 2][{conversation_id}] AUDIO complete in {processing_time_ms}ms.")
        return result

    except Exception as e:
        print(f"[Phase 2][{conversation_id}] ERROR: {str(e)}")
        return _make_failed_result(
            conversation_id, client_id, "audio", start_time, rag_policies, e
        )


async def analyze_text(
    conversation_id: str,
    client_id: str,
    transcript: str,
    client_config: dict,
    rag_policies: list[str],
) -> ConversationAnalysisResult:
    """
    Full text pipeline:
    1. Build prompt with transcript inline + client context + RAG policies
    2. Call model.generate_content(prompt) — text only, no file upload
    3. Parse JSON with 3-layer fallback
    4. Return validated ConversationAnalysisResult
    """
    start_time = time.time()
    print(f"\n[Phase 2][{conversation_id}] Starting TEXT analysis...")

    try:
        # 1. Build prompt with transcript included
        prompt = _build_analysis_prompt(client_config, rag_policies, "text", transcript)
        print(f"[Phase 2][{conversation_id}] Sending to {MODEL_NAME}...")

        # 2. Generate
        response = model.generate_content(prompt)
        print(f"[Phase 2][{conversation_id}] Response received. Parsing...")

        # 3. FIX 3: Parse with 3-layer fallback
        data = _extract_json_from_response(response.text)

        # 4. Build result
        processing_time_ms = int((time.time() - start_time) * 1000)
        result = _build_result_from_dict(
            data, conversation_id, client_id, "text",
            processing_time_ms, rag_policies
        )

        print(f"[Phase 2][{conversation_id}] TEXT complete in {processing_time_ms}ms.")
        return result

    except Exception as e:
        print(f"[Phase 2][{conversation_id}] ERROR: {str(e)}")
        return _make_failed_result(
            conversation_id, client_id, "text", start_time, rag_policies, e
        )


async def analyze_json_for_rag(
    client_id: str,
    analysis_json: dict,
    client_config: dict,
    rag_policies: list[str],
) -> Optional[RagActions]:
    """
    Phase 3 RAG: Takes Phase 2 JSON output and generates a structured action plan.
    Uses response_schema=RagActions (structured JSON mode — SAFE here, no audio input).
    """
    start_time = time.time()
    print(f"\n[Phase 3] Building RAG action plan for: {client_id}")

    try:
        policies_block = "\n".join([f"{i}. {p}" for i, p in enumerate(rag_policies, 1)])

        prompt = f"""You are a senior compliance and quality assurance AI.
Review this conversation analysis and generate a specific, actionable compliance report.

### Client Context
- Domain: {client_config.get('domain', 'Unknown')}
- Company: {client_config.get('company_name', 'Unknown')}
- Supported Products: {", ".join(client_config.get('products', []))}
- Known Risk Triggers: {", ".join(client_config.get('risk_triggers', []))}
- Escalation Threshold: {client_config.get('escalation_threshold', 'medium')}

### Compliance Policies
{policies_block}

### Conversation Analysis
{json.dumps(analysis_json, indent=2, ensure_ascii=False)}

Generate a structured action plan. Reference specific policy numbers.
Priority must be exactly one of: P1 - Critical, P2 - High, P3 - Nominal
"""
        # Structured output mode is safe here — input is text only, no audio file
        structured_model = genai.GenerativeModel(
            model_name=MODEL_NAME,
            generation_config=genai.GenerationConfig(
                response_mime_type="application/json",
                response_schema=RagActions,
                temperature=0.1,
            )
        )

        response = structured_model.generate_content(prompt)
        processing_time_ms = int((time.time() - start_time) * 1000)
        print(f"[Phase 3] RAG complete in {processing_time_ms}ms.")

        parsed = json.loads(response.text)
        return RagActions(**parsed)

    except Exception as e:
        print(f"[Phase 3] ERROR: {str(e)}")
        return RagActions(
            suggested_actions=["Manual review required — automated analysis failed"],
            priority="P2 - High",
            policy_justifications=[f"Analysis error: {str(e)}"],
            human_review_needed=True,
            coaching_notes="Unable to generate coaching notes due to error.",
        )


def analyze_text_sync(transcript: str, client_config: dict) -> dict:
    """
    Synchronous function for direct testing (used by test_gemini.py).
    Takes transcript + config, returns plain dict.

    Uses FIX 3: 3-layer JSON fallback parsing.
    """
    start = time.time()
    risk_triggers = client_config.get("risk_triggers", [])
    auto_policies = [
        f"Monitor and flag: {', '.join(risk_triggers)}"
    ] if risk_triggers else []

    prompt = _build_analysis_prompt(client_config, auto_policies, "text", transcript)

    try:
        response = model.generate_content(prompt)
        # FIX 3: Use fallback parser instead of raw json.loads
        data = _extract_json_from_response(response.text)
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