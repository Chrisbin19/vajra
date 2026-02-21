"""
VAJRA Phase 4 — Compliance Check API Routes

POST /api/v1/compliance/check
  - Fast rule-based check, returns in <100ms
  - No Gemini API call — zero cost
  - Accepts transcript + client_id (loads policies from file)
    OR transcript + inline policies list
"""

import json
import os
import uuid
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List

from core.compliance_engine import check_compliance, compliance_report_to_dict

router = APIRouter()


class ComplianceCheckRequest(BaseModel):
    transcript: str = Field(
        ..., min_length=10,
        description="Full conversation transcript to check",
        json_schema_extra={"example": "Agent: Good morning. Customer: I shared my OTP and Rs.85000 was taken."}
    )
    client_id: Optional[str] = Field(
        None, description="Loads policies from data/domain_knowledge/ automatically",
        json_schema_extra={"example": "banking_client_01"}
    )
    policies: Optional[List[str]] = Field(
        None, description="Inline policy list (use this OR client_id, not both)"
    )
    domain: Optional[str] = Field(
        "general", description="Domain for domain-specific rules: banking, insurance, telecom",
        json_schema_extra={"example": "banking"}
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "transcript": "Agent: Good morning.\nCustomer: I shared my OTP with someone and Rs.85000 was transferred without my knowledge.",
                "client_id": "banking_client_01",
                "domain": "banking"
            }
        }
    }


def _load_policies(client_id: str) -> List[str]:
    base_id = client_id.split("_client")[0].split("_enterprise")[0].split("_provider")[0]
    rules_path = os.path.join("data", "domain_knowledge", f"{base_id}_rules.txt")
    try:
        with open(rules_path, "r") as f:
            return [line.strip() for line in f.read().split("\n") if line.strip()]
    except FileNotFoundError:
        return [
            "Always acknowledge customer concern before providing solutions.",
            "Escalate unresolved issues after 10 minutes to supervisor.",
        ]


def _load_config(client_id: str) -> dict:
    config_path = os.path.join("data", "config", f"{client_id}.json")
    try:
        with open(config_path, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {"domain": "general"}


@router.post(
    "/compliance/check",
    status_code=200,
    summary="Instant rule-based compliance violation check (no AI cost)",
    description=(
        "Checks transcript against all client compliance policies using a rule-based engine. "
        "Returns per-policy status (COMPLIED / VIOLATED / UNCLEAR), evidence snippets, "
        "severity levels, remediation guidance, and an overall compliance score 0-100. "
        "Zero Gemini API calls — results in under 100ms."
    ),
    tags=["Compliance"],
)
async def compliance_check(request: ComplianceCheckRequest):
    check_id = str(uuid.uuid4())

    if request.policies:
        policies = request.policies
        client_id = request.client_id or "custom"
        domain = request.domain or "general"
        policies_source = "inline"
    elif request.client_id:
        client_id = request.client_id.strip()
        policies = _load_policies(client_id)
        config = _load_config(client_id)
        domain = config.get("domain", request.domain or "general")
        base_id = client_id.split("_client")[0].split("_enterprise")[0]
        policies_source = f"data/domain_knowledge/{base_id}_rules.txt"
    else:
        raise HTTPException(
            status_code=400,
            detail="Either 'client_id' or 'policies' must be provided."
        )

    if not policies:
        raise HTTPException(
            status_code=422,
            detail="No policies found. Check client_id or provide policies inline."
        )

    report = check_compliance(
        transcript=request.transcript,
        policies=policies,
        domain=domain,
    )

    report_dict = compliance_report_to_dict(report)

    return {
        "check_id": check_id,
        "client_id": client_id,
        "engine": "rule_based",
        "analysis_type": "compliance_only",
        "policies_source": policies_source,
        **report_dict,
    }
