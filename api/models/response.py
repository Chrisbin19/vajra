"""
Response models for Phase 2: Full JSON schema extraction from Gemini.
"""
from pydantic import BaseModel, Field
from typing import List, Optional

class SentimentAnalysis(BaseModel):
    overall: str = Field(..., description="'positive' | 'negative' | 'neutral' | 'mixed'")
    customer_sentiment: str = Field(..., description="Description of the customer emotional state")
    agent_sentiment: str = Field(..., description="Description of the agent tone")
    emotional_arc: List[str] = Field(..., description="Step-by-step emotional progression, e.g. ['frustrated', 'neutral', 'satisfied']")
    frustration_detected: bool = Field(..., description="True if anger or intense frustration was detected from the customer")

class EntityExtraction(BaseModel):
    amounts_mentioned: List[str] = Field(..., description="Currency amounts mentioned, e.g. ['Rs.4200']")
    dates_mentioned: List[str] = Field(..., description="Dates or timelines mentioned, e.g. ['January 14th', 'yesterday']")
    account_references: List[str] = Field(..., description="Partial account numbers or IDs referenced, e.g. ['7823']")
    products_mentioned: List[str] = Field(..., description="Products or services discussed, e.g. ['debit card', 'savings account']")
    locations_mentioned: List[str] = Field(..., description="Any branches, cities, or locations mentioned")
    people_mentioned: List[str] = Field(..., description="Names of people referenced in the call")

class ComplianceCheck(BaseModel):
    violations_detected: List[str] = Field(..., description="Specific compliance violations found during the call")
    policies_checked: List[str] = Field(..., description="Which RAG policies were actively evaluated against this conversation")
    risk_level: str = Field(..., description="'low' | 'medium' | 'high' | 'critical'")
    escalation_required: bool = Field(..., description="True if this call requires immediate human supervisor review")
    risk_flags: List[str] = Field(..., description="Specific high-level risks, e.g. ['unauthorized_transaction', 'fraud_mention']")

class AgentPerformance(BaseModel):
    score: int = Field(..., description="Overall performance score from 0 to 100")
    greeting_proper: bool = Field(..., description="True if the agent gave a compliant and friendly greeting")
    empathy_shown: bool = Field(..., description="True if the agent acknowledged frustration and apologized where appropriate")
    issue_resolved: bool = Field(..., description="True if the customer's core issue was fully resolved on this call")
    call_outcome: str = Field(..., description="'resolved' | 'escalated' | 'dropped' | 'callback_scheduled'")
    strengths: List[str] = Field(..., description="Areas where the agent performed exceptionally well")
    improvements: List[str] = Field(..., description="Areas where the agent needs coaching or improvement")

class SpeakerInfo(BaseModel):
    speakers_detected: int = Field(..., description="Total number of distinct speakers detected")
    speaker_labels: List[str] = Field(..., description="Predicted labels for the speakers, e.g. ['Agent', 'Customer']")
    language_per_speaker: dict = Field(..., description="Mapping of speaker label to ISO language code, e.g. {'Agent': 'en', 'Customer': 'ta'}")

class GeminiAnalysisResponse(BaseModel):
    summary: str = Field(..., description="A concise 2-4 sentence summary of the entire conversation")
    language_detected: str = Field(..., description="The primary ISO language code of the conversation")
    languages_all: List[str] = Field(..., description="All ISO language codes detected, including code-switching instances")
    sentiment: SentimentAnalysis = Field(..., description="In-depth sentiment and emotional analysis")
    customer_intents: List[str] = Field(..., description="Primary reasons for the customer's contact, e.g. ['dispute_transaction']")
    topics_discussed: List[str] = Field(..., description="Themes over the course of the call, e.g. ['unauthorized_charge']")
    entities: EntityExtraction = Field(..., description="Extracted PII, names, amounts, and locations")
    compliance: ComplianceCheck = Field(..., description="Adherence to client-specific RAG policies")
    agent_performance: AgentPerformance = Field(..., description="Coaching and resolution metrics for the agent")
    speakers: SpeakerInfo = Field(..., description="Speaker diarization and tracking")

class ConversationAnalysisResult(BaseModel):
    """
    Main response wrapper for Phase 2 containing all extracted intelligence.
    """
    # Metadata
    conversation_id: str = Field(..., description="Unique UUID for this analysis")
    client_id: str = Field(..., description="The client identifier handling this request")
    input_type: str = Field(..., description="'audio' or 'text'")
    status: str = Field(..., description="'completed' | 'failed' | 'partial'")
    processing_time_ms: Optional[int] = Field(None, description="Time taken by the AI in milliseconds")

    # MANDATORY Phase 2 fields
    summary: str = Field(..., description="A concise 2-4 sentence summary of the entire conversation")
    language_detected: str = Field(..., description="The primary ISO language code of the conversation")
    languages_all: List[str] = Field(..., description="All ISO language codes detected, including code-switching instances")
    sentiment: SentimentAnalysis = Field(..., description="In-depth sentiment and emotional analysis")
    customer_intents: List[str] = Field(..., description="Primary reasons for the customer's contact, e.g. ['dispute_transaction']")
    topics_discussed: List[str] = Field(..., description="Themes over the course of the call, e.g. ['unauthorized_charge']")
    entities: EntityExtraction = Field(..., description="Extracted PII, names, amounts, and locations")

    # Advanced analysis (Phase 3 elements included in schema)
    compliance: ComplianceCheck = Field(..., description="Adherence to client-specific RAG policies")
    agent_performance: AgentPerformance = Field(..., description="Coaching and resolution metrics for the agent")

    # Bonus / Meta
    speakers: Optional[SpeakerInfo] = Field(None, description="Speaker diarization and tracking")
    rag_policies_used: List[str] = Field(..., description="The specific policies passed into the prompt for transparency")
    error: Optional[str] = Field(None, description="Populated only if status == 'failed'")

    model_config = {
        "json_schema_extra": {
            "example": {
                "conversation_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
                "client_id": "banking_client_01",
                "input_type": "text",
                "status": "completed",
                "processing_time_ms": 1450,
                "summary": "Customer called to report an unauthorized transaction of Rs.4200 dated January 14th. Agent Priya verified the customer's identity using the last 4 digits of their account. The agent blocked the debit card and raised a dispute ticket successfully.",
                "language_detected": "en",
                "languages_all": ["en"],
                "sentiment": {
                    "overall": "mixed",
                    "customer_sentiment": "worried but relieved at the end",
                    "agent_sentiment": "professional and empathetic",
                    "emotional_arc": ["worried", "neutral", "relieved"],
                    "frustration_detected": False
                },
                "customer_intents": ["report_fraud", "block_card"],
                "topics_discussed": ["unauthorized_transaction", "card_blocking", "dispute_resolution"],
                "entities": {
                    "amounts_mentioned": ["Rs.4200"],
                    "dates_mentioned": ["January 14th"],
                    "account_references": ["7823"],
                    "products_mentioned": ["debit card", "account"],
                    "locations_mentioned": [],
                    "people_mentioned": ["Priya"]
                },
                "compliance": {
                    "violations_detected": [],
                    "policies_checked": ["Identity Verification", "Card Blocking Protocol"],
                    "risk_level": "medium",
                    "escalation_required": False,
                    "risk_flags": ["unauthorized_transaction"]
                },
                "agent_performance": {
                    "score": 95,
                    "greeting_proper": True,
                    "empathy_shown": True,
                    "issue_resolved": True,
                    "call_outcome": "resolved",
                    "strengths": ["Empathy", "Swift resolution"],
                    "improvements": ["None required"]
                },
                "speakers": {
                    "speakers_detected": 2,
                    "speaker_labels": ["Agent", "Customer"],
                    "language_per_speaker": {"Agent": "en", "Customer": "en"}
                },
                "rag_policies_used": [
                    "Identity Verification: Verify customer with account number + OTP before sharing account details.",
                    "Card Blocking Protocol: Offer immediate card blocking for unauthorized transaction reports."
                ],
                "error": None
            }
        }
    }

