"""
VAJRA Phase 4 — Rule-Based Compliance Engine

This engine runs BEFORE Gemini on every call.
It does instant keyword + pattern matching against client policies.

Why two layers?
  - This engine: instant, zero API cost, catches obvious violations
  - Gemini (Phase 2): catches subtle, contextual, nuanced violations
  - Together: defense-in-depth compliance detection

Design:
  Each policy string is parsed into a PolicyRule.
  Each PolicyRule has compliance_signals (words that show rule was followed)
  and violation_signals (patterns that show rule was broken).
  The engine evaluates each rule against the transcript and returns
  a structured ComplianceReport.
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional
from enum import Enum


class PolicyStatus(str, Enum):
    COMPLIED = "complied"
    VIOLATED = "violated"
    UNCLEAR = "unclear"


@dataclass
class PolicyViolation:
    """A single detected compliance violation."""
    policy_index: int
    policy_name: str
    policy_text: str
    status: PolicyStatus
    severity: str                  # "critical" | "high" | "medium" | "low"
    evidence: List[str]
    remediation: str


@dataclass
class ComplianceReport:
    """Full compliance report for a transcript."""
    total_policies_checked: int
    violations: List[PolicyViolation]
    complied: List[PolicyViolation]
    unclear: List[PolicyViolation]
    overall_risk_level: str
    escalation_required: bool
    risk_flags: List[str]
    violation_count: int
    compliance_score: int
    summary: str


COMPLIANCE_SIGNALS = {
    "identity_verification": [
        r"\blast\s*4\s*digits?\b",
        r"\bdate of birth\b", r"\bDOB\b",
        r"\bregistered mobile\b", r"\bOTP\b", r"\bone.time.password\b",
        r"\bverif(y|ied|ication)\b.*\bidentity\b",
        r"\bidentity\b.*\bverif",
    ],
    "recording_disclosure": [
        r"\brecorded?\b", r"\brecording\b",
        r"\bquality\s*purposes?\b", r"\bmonitored?\b",
        r"\bquality\s*(and\s*)?compliance\b",
    ],
    "empathy": [
        r"\bsorry\b", r"\bapologe\b", r"\bapology\b",
        r"\bunderstand\b.*\bconcern\b", r"\bconcern\b.*\bunderstand\b",
        r"\binconvenience\b", r"\bfrustrat\b.*\bunderstand\b",
    ],
    "card_block_offered": [
        r"\bblock\b.*\bcard\b", r"\bcard\b.*\bblock\b",
        r"\bblock\b.*\bdebit\b", r"\bdebit\b.*\bblock\b",
        r"\bimmediately\b.*\bblock\b", r"\bblock\b.*\bimmediately\b",
    ],
    "dispute_ticket": [
        r"\bdispute\s*ticket\b", r"\bdispute\s*ref(erence)?\b",
        r"\bticket\s*(number|no|id|ref)\b", r"\bDSP-\d+\b",
        r"\braise[ds]?\s*(a\s*)?dispute\b",
    ],
    "refund_timeline": [
        r"\b7.10\s*working\s*days?\b", r"\b7\s*to\s*10\b.*\bdays?\b",
        r"\bRBI\s*guidelines?\b", r"\bworking\s*days?\b.*\brefund\b",
    ],
    "supervisor_transfer": [
        r"\btransfer(ring)?\b.*\bsupervisor\b", r"\bsupervisor\b.*\btransfer\b",
        r"\bput\b.*\bthrough\b.*\bsupervisor\b", r"\bescalate\b.*\bsupervisor\b",
        r"\bmanager\b",
    ],
    "free_look_period": [
        r"\bfree.look\b", r"\bfree\s*look\s*period\b",
        r"\b15.day\b", r"\b15\s*days?\b.*\breturn\b",
        r"\bcancell?\b.*\bfull\s*refund\b",
    ],
    "loan_disclosure": [
        r"\binterest\s*rate\b", r"\bprocessing\s*fee\b",
        r"\bprepayment\s*penalt(y|ies)\b", r"\bEMI\b",
    ],
}

VIOLATION_SIGNALS = {
    "full_account_number": [
        r"\b\d{12,16}\b",
        r"\b4[0-9]{15}\b",
        r"\b5[1-5][0-9]{14}\b",
    ],
    "otp_shared_by_customer": [
        r"(customer|i)\b.*\bshared?\b.*\bOTP\b",
        r"\bOTP\b.*\bgave\b",
        r"\bshared?\b.*\bone.time.password\b",
        r"\btold\b.*\bOTP\b",
    ],
    "guaranteed_returns": [
        r"\bguaranteed?\s*returns?\b",
        r"\bfixed\s*returns?\b",
        r"\bassured?\s*returns?\b",
        r"\b100%\s*returns?\b",
        r"\bno\s*risk\b.*\binvest\b",
        r"\brisk.free\b.*\binvest\b",
    ],
    "pressure_tactics": [
        r"\blast\s*chance\b", r"\boffer\s*expires?\b",
        r"\btoday\s*only\b", r"\blimited\s*time\b",
        r"\bact\s*now\b", r"\bdon.t\s*miss\b",
        r"\bexpires?\s*tonight\b", r"\bthis\s*week\s*only\b",
    ],
    "improper_refund_promise": [
        r"\b(24|48)\s*hours?\b.*\brefund\b", r"\brefund\b.*\b(24|48)\s*hours?\b",
        r"\bimmediately\b.*\brefund\b.*\baccount\b",
        r"\bsame\s*day\b.*\brefund\b",
        r"\btomorrow\b.*\brefund\b.*\baccount\b",
    ],
}

SEVERITY_MAP = {
    "full_account_number": "critical",
    "otp_shared_by_customer": "critical",
    "guaranteed_returns": "critical",
    "pressure_tactics": "high",
    "improper_refund_promise": "high",
    "identity_verification": "high",
    "recording_disclosure": "medium",
    "empathy": "low",
    "card_block_offered": "high",
    "dispute_ticket": "medium",
    "refund_timeline": "medium",
    "supervisor_transfer": "high",
    "free_look_period": "critical",
    "loan_disclosure": "medium",
}

REMEDIATION_MAP = {
    "full_account_number": "Never state full account or card numbers. Reference only the last 4 digits with 'xxxx' prefix.",
    "otp_shared_by_customer": "Immediately flag as phishing incident. Block card and escalate to fraud team regardless of amount.",
    "guaranteed_returns": "Never promise guaranteed or fixed returns on investment products. Disclose risks clearly per IRDAI regulations.",
    "pressure_tactics": "Remove all urgency language. Customer must not be pressured into a decision.",
    "improper_refund_promise": "Refund timelines are 7-10 working days per RBI. Never promise faster timelines.",
    "identity_verification": "Verify customer using two factors (account last 4 digits + date of birth or OTP) before discussing account details.",
    "recording_disclosure": "Inform customer that the call is being recorded within the first 60 seconds.",
    "empathy": "Acknowledge the customer concern explicitly and apologize before providing solutions.",
    "card_block_offered": "Proactively offer card block within 60 seconds of fraud report. Obtain verbal consent before blocking.",
    "dispute_ticket": "Always raise a dispute ticket and provide the reference number before ending the call.",
    "refund_timeline": "Clearly state that refunds take 7-10 working days as per RBI guidelines.",
    "supervisor_transfer": "Transfer to supervisor within 5 minutes of request. Do not attempt to re-resolve after supervisor request.",
    "free_look_period": "Disclose the free-look period (15 days) on all life insurance policies per IRDAI PPI Reg 7(5).",
    "loan_disclosure": "Disclose interest rate, processing fee, and prepayment penalty before accepting any loan application.",
}


def _find_signals(transcript_lower: str, patterns: List[str]) -> List[str]:
    found = []
    for pattern in patterns:
        match = re.search(pattern, transcript_lower, re.IGNORECASE | re.DOTALL)
        if match:
            start = max(0, match.start() - 30)
            end = min(len(transcript_lower), match.end() + 30)
            context = "..." + transcript_lower[start:end].strip() + "..."
            found.append(context)
    return found


def _map_policy_to_rules(policy_text: str, policy_index: int) -> Optional[list]:
    text_lower = policy_text.lower()
    mapping_candidates = []

    if any(k in text_lower for k in ["identit", "verif", "two factor", "account number", "otp", "date of birth"]):
        mapping_candidates.append("identity_verification")
    if any(k in text_lower for k in ["recorded", "recording", "monitored", "quality"]):
        mapping_candidates.append("recording_disclosure")
    if any(k in text_lower for k in ["acknowledge", "apologize", "empathy", "concern", "inconvenience"]):
        mapping_candidates.append("empathy")
    if any(k in text_lower for k in ["block", "card block", "card blocking"]):
        mapping_candidates.append("card_block_offered")
    if any(k in text_lower for k in ["dispute ticket", "reference number", "ticket", "chargeback"]):
        mapping_candidates.append("dispute_ticket")
    if any(k in text_lower for k in ["7-10", "7 to 10", "working days", "refund timeline", "rbi guideline"]):
        mapping_candidates.append("refund_timeline")
    if any(k in text_lower for k in ["supervisor", "escalate", "transfer", "5 minutes"]):
        mapping_candidates.append("supervisor_transfer")
    if any(k in text_lower for k in ["free look", "free-look", "15 day"]):
        mapping_candidates.append("free_look_period")
    if any(k in text_lower for k in ["interest rate", "processing fee", "prepayment", "loan"]):
        mapping_candidates.append("loan_disclosure")
    if any(k in text_lower for k in ["guaranteed return", "fixed return", "assured return", "risk-free"]):
        mapping_candidates.append("guaranteed_returns")
    if any(k in text_lower for k in ["pressure", "urgency", "last chance", "today only"]):
        mapping_candidates.append("pressure_tactics")
    if any(k in text_lower for k in ["full account", "full card", "cvv", "privacy", "data privacy"]):
        mapping_candidates.append("full_account_number")

    return mapping_candidates if mapping_candidates else None


def check_compliance(
    transcript: str,
    policies: List[str],
    domain: str = "general",
) -> ComplianceReport:
    """
    Main entry point — runs rule-based compliance check.

    Args:
        transcript:  Full conversation text
        policies:    List of policy strings from data/domain_knowledge/
        domain:      Client domain (banking, insurance, etc.)

    Returns:
        ComplianceReport with all violations, complied rules, and overall risk
    """
    transcript_lower = transcript.lower()
    violations = []
    complied = []
    unclear = []
    risk_flags = []

    for idx, policy_text in enumerate(policies, 1):
        short_name = policy_text.split(":")[0].strip() if ":" in policy_text else f"Policy {idx}"
        rule_keys = _map_policy_to_rules(policy_text, idx)

        if not rule_keys:
            unclear.append(PolicyViolation(
                policy_index=idx, policy_name=short_name, policy_text=policy_text,
                status=PolicyStatus.UNCLEAR, severity="low",
                evidence=["Policy could not be mapped to automated rules — requires AI or human review"],
                remediation="Review transcript manually against this policy."
            ))
            continue

        policy_violated = False
        policy_evidence_complied = []
        policy_evidence_violated = []
        highest_severity = "low"

        for rule_key in rule_keys:
            if rule_key in VIOLATION_SIGNALS:
                viol_evidence = _find_signals(transcript_lower, VIOLATION_SIGNALS[rule_key])
                if viol_evidence:
                    policy_violated = True
                    policy_evidence_violated.extend(viol_evidence)
                    sev = SEVERITY_MAP.get(rule_key, "medium")
                    if ["critical", "high", "medium", "low"].index(sev) < \
                       ["critical", "high", "medium", "low"].index(highest_severity):
                        highest_severity = sev
                    risk_flags.append(rule_key)

            if rule_key in COMPLIANCE_SIGNALS:
                comp_evidence = _find_signals(transcript_lower, COMPLIANCE_SIGNALS[rule_key])
                if comp_evidence:
                    policy_evidence_complied.extend(comp_evidence[:2])

        if policy_violated:
            violations.append(PolicyViolation(
                policy_index=idx, policy_name=short_name, policy_text=policy_text,
                status=PolicyStatus.VIOLATED, severity=highest_severity,
                evidence=policy_evidence_violated[:3],
                remediation=REMEDIATION_MAP.get(rule_keys[0], "Review and correct agent behavior per policy.")
            ))
        elif policy_evidence_complied:
            complied.append(PolicyViolation(
                policy_index=idx, policy_name=short_name, policy_text=policy_text,
                status=PolicyStatus.COMPLIED, severity="low",
                evidence=policy_evidence_complied, remediation=""
            ))
        else:
            unclear.append(PolicyViolation(
                policy_index=idx, policy_name=short_name, policy_text=policy_text,
                status=PolicyStatus.UNCLEAR, severity="low",
                evidence=["No clear evidence found in transcript — AI review recommended"],
                remediation="Manual or AI review required for this policy."
            ))

    for rule_key, patterns in VIOLATION_SIGNALS.items():
        if any(rule_key in (_map_policy_to_rules(p.policy_text, 0) or []) for p in violations):
            continue
        evidence = _find_signals(transcript_lower, patterns)
        if evidence:
            if rule_key in ["guaranteed_returns", "pressure_tactics", "free_look_period"] and domain not in ["insurance"]:
                continue
            if rule_key not in [v.policy_name for v in violations]:
                risk_flags.append(rule_key)
                violations.append(PolicyViolation(
                    policy_index=0,
                    policy_name=rule_key.replace("_", " ").title(),
                    policy_text=f"Universal rule: {rule_key}",
                    status=PolicyStatus.VIOLATED,
                    severity=SEVERITY_MAP.get(rule_key, "medium"),
                    evidence=evidence[:3],
                    remediation=REMEDIATION_MAP.get(rule_key, "Review and correct per policy.")
                ))

    has_critical = any(v.severity == "critical" for v in violations)
    has_high = any(v.severity == "high" for v in violations)
    vcount = len(violations)

    if has_critical or vcount >= 3:
        overall_risk = "critical"
        escalation_required = True
    elif has_high or vcount >= 2:
        overall_risk = "high"
        escalation_required = True
    elif vcount >= 1:
        overall_risk = "medium"
        escalation_required = False
    else:
        overall_risk = "low"
        escalation_required = False

    total = len(policies)
    if total == 0:
        compliance_score = 100
    else:
        penalty = len(violations) + (len(unclear) * 0.3)
        compliance_score = max(0, int(100 - (penalty / total * 100)))

    if vcount == 0:
        summary = f"No violations detected across {len(policies)} policies checked. Agent performed compliantly."
    elif vcount == 1:
        summary = f"1 compliance violation detected: {violations[0].policy_name}. Risk level: {overall_risk}."
    else:
        vnames = ", ".join(v.policy_name for v in violations[:3])
        summary = (
            f"{vcount} compliance violations detected across {len(policies)} policies. "
            f"Key issues: {vnames}. Risk level: {overall_risk}."
        )

    return ComplianceReport(
        total_policies_checked=len(policies),
        violations=violations, complied=complied, unclear=unclear,
        overall_risk_level=overall_risk, escalation_required=escalation_required,
        risk_flags=list(set(risk_flags)), violation_count=vcount,
        compliance_score=compliance_score, summary=summary,
    )


def compliance_report_to_dict(report: ComplianceReport) -> dict:
    """Converts ComplianceReport dataclass to JSON-serializable dict."""
    def v_to_dict(v: PolicyViolation) -> dict:
        return {
            "policy_index": v.policy_index, "policy_name": v.policy_name,
            "policy_text": v.policy_text, "status": v.status.value,
            "severity": v.severity, "evidence": v.evidence,
            "remediation": v.remediation,
        }
    return {
        "total_policies_checked": report.total_policies_checked,
        "violation_count": report.violation_count,
        "compliance_score": report.compliance_score,
        "overall_risk_level": report.overall_risk_level,
        "escalation_required": report.escalation_required,
        "risk_flags": report.risk_flags,
        "summary": report.summary,
        "violations": [v_to_dict(v) for v in report.violations],
        "complied": [v_to_dict(v) for v in report.complied],
        "unclear": [v_to_dict(v) for v in report.unclear],
    }
