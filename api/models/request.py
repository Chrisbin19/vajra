"""
Pydantic Request and Response Models for VAJRA Phase 1.
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional

class TextAnalysisRequest(BaseModel):
    """
    Request model for analyzing a text conversation transcript.
    """
    client_id: str = Field(
        ...,
        description="Client identifier — used to fetch domain config from SQLite",
        json_schema_extra={"example": "banking_client_01"}
    )
    transcript: str = Field(
        ...,
        min_length=10,
        description="Full conversation. Recommended format: 'Agent: ...\\nCustomer: ...'",
        json_schema_extra={"example": "Agent: Good morning.\\nCustomer: I have an unauthorized charge of Rs.4200."}
    )
    metadata: Optional[dict] = Field(
        default_factory=dict,
        description="Optional call metadata — channel, date, agent_id, duration",
        json_schema_extra={"example": {"channel": "phone", "call_date": "2024-01-15", "agent_id": "AGT_042"}}
    )

    @field_validator("client_id")
    @classmethod
    def validate_client_id(cls, v: str) -> str:
        """Strips whitespace and ensures client_id is not empty."""
        v = v.strip()
        if not v:
            raise ValueError("client_id must not be empty after stripping whitespace")
        return v

    @field_validator("transcript")
    @classmethod
    def validate_transcript(cls, v: str) -> str:
        """Strips whitespace and ensures transcript length >= 10."""
        v = v.strip()
        if len(v) < 10:
            raise ValueError("transcript must be at least 10 chars after stripping whitespace")
        return v


class AnalysisResponse(BaseModel):
    """
    Response model for both audio and text analysis endpoints.
    """
    conversation_id: str = Field(..., description="UUID for this conversation")
    client_id: str = Field(..., description="Echoed from request")
    input_type: str = Field(..., description="'audio' or 'text'")
    status: str = Field(..., description="Status string, e.g., 'received'")
    language_detected: Optional[str] = Field(
        None,
        description="None for audio (Gemini sets in Phase 2), hint string for text"
    )
    file_info: Optional[dict] = Field(
        None,
        description="None for text, file details dict for audio"
    )
    message: str = Field(..., description="Human-readable status message")

    model_config = {
        "json_schema_extra": {
            "example": {
                "conversation_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
                "client_id": "banking_client_01",
                "input_type": "text",
                "status": "received",
                "language_detected": "en",
                "file_info": None,
                "message": "Transcript received. Length: 124 characters. Language hint: 'en'."
            }
        }
    }


class ErrorResponse(BaseModel):
    """
    Standardized Error Response.
    """
    error: str = Field(..., description="High level error type")
    detail: str = Field(..., description="Detailed error description")
    conversation_id: Optional[str] = Field(None, description="UUID involved in error if available")
