"""
Hybrid Phase 4 Deterministic Compliance Engine.

Layer 1 (Deterministic): Scans transcript for configured high-risk keywords.
Layer 2 (AI Corroboration): When keyword scan finds nothing but the Gemini AI
    already flagged a HIGH/CRITICAL risk, synthesizes flags from the AI's
    risk_flags list so the output is never contradictory with Phase 2.
"""

# ── Severity weights for risk score calculation ───────────────────────────────
_SEVERITY_WEIGHTS = {"high": 1.0, "medium": 0.5, "low": 0.2}

# ── Built-in universal fallback keywords (used when client config has none) ───
_UNIVERSAL_KEYWORDS = [
    {"keyword": "lawsuit",      "severity": "high",   "policy_reference": "Legal Threat Policy"},
    {"keyword": "lawyer",       "severity": "high",   "policy_reference": "Legal Threat Policy"},
    {"keyword": "legal action", "severity": "high",   "policy_reference": "Legal Threat Policy"},
    {"keyword": "sue",          "severity": "high",   "policy_reference": "Legal Threat Policy"},
    {"keyword": "court",        "severity": "high",   "policy_reference": "Legal Threat Policy"},
    {"keyword": "fraud",        "severity": "high",   "policy_reference": "Fraud Reporting Policy"},
    {"keyword": "scam",         "severity": "high",   "policy_reference": "Fraud Reporting Policy"},
    {"keyword": "stolen",       "severity": "high",   "policy_reference": "Security Incident Policy"},
    {"keyword": "unauthorized", "severity": "high",   "policy_reference": "Security Incident Policy"},
    {"keyword": "hacked",       "severity": "high",   "policy_reference": "Cybersecurity Policy"},
    {"keyword": "ombudsman",    "severity": "high",   "policy_reference": "Regulatory Complaint Policy"},
    {"keyword": "supervisor",   "severity": "medium", "policy_reference": "Escalation Request Policy"},
    {"keyword": "manager",      "severity": "medium", "policy_reference": "Escalation Request Policy"},
    {"keyword": "complaint",    "severity": "medium", "policy_reference": "Complaint Handling Policy"},
    {"keyword": "threaten",     "severity": "high",   "policy_reference": "Abuse & Threat Policy"},
    {"keyword": "abuse",        "severity": "high",   "policy_reference": "Abuse & Threat Policy"},
    {"keyword": "demand",       "severity": "medium", "policy_reference": "Customer Escalation Policy"},
    {"keyword": "refund",       "severity": "low",    "policy_reference": "Refund Processing Policy"},
    {"keyword": "cancel",       "severity": "low",    "policy_reference": "Cancellation Policy"},
]


def _scan_keywords(transcript_lower: str, sentences: list, keyword_list: list) -> list:
    """Scan a transcript against a list of keyword objects, return triggered flags."""
    triggered = []
    for kw_obj in keyword_list:
        if isinstance(kw_obj, dict):
            keyword     = kw_obj.get("keyword", "").lower()
            severity    = kw_obj.get("severity", "medium")
            policy_ref  = kw_obj.get("policy_reference", "General Compliance Policy")
        else:
            keyword     = str(kw_obj).lower()
            severity    = "medium"
            policy_ref  = "General Compliance Policy"

        if not keyword or keyword not in transcript_lower:
            continue

        context_line = next(
            (s.strip() for s in sentences if keyword in s.lower()),
            "Context unavailable"
        )

        triggered.append({
            "keyword":          keyword,
            "severity":         severity,
            "context":          context_line,
            "policy_reference": policy_ref,
            "action_required":  severity == "high",
            "source":           "deterministic",
        })

    return triggered


def _score(flags: list, total_keywords: int) -> float:
    """Normalised risk score 0.0–1.0 based on triggered flag severities."""
    total_risk = sum(_SEVERITY_WEIGHTS.get(f["severity"], 0.3) for f in flags)
    return min(round(total_risk / max(total_keywords, 1), 2), 1.0)


def apply_compliance_triggers(
    transcript: str,
    client_config: dict,
    ai_result: dict = None,
) -> dict:
    """
    Hybrid Phase 4 compliance engine.

    Args:
        transcript:    The raw conversation text to scan.
        client_config: Client-specific domain config (contains keyword lists).
        ai_result:     Optional Phase 2 Gemini result dict.  When provided and
                       the deterministic scan finds nothing, the engine falls
                       back to AI-detected risk flags so results are never
                       contradictory with the AI layer.

    Returns:
        dict with keys: flags, total_flags, compliance_risk_score, auto_escalate
    """
    # ── Guard: empty transcript ───────────────────────────────────────────────
    if not transcript:
        return _empty_result()

    transcript_lower = transcript.lower()
    sentences        = transcript.replace("\r\n", "\n").split("\n")

    # ── Layer 1: Deterministic keyword scan ───────────────────────────────────
    configured_keywords = (
        client_config.get("escalation_rules", {}).get("high_risk_keywords", [])
    )

    # Merge configured keywords with universal fallback list (deduplicated)
    configured_words = {
        (kw.get("keyword", "") if isinstance(kw, dict) else kw).lower()
        for kw in configured_keywords
    }
    extra_universal = [
        k for k in _UNIVERSAL_KEYWORDS
        if k["keyword"] not in configured_words
    ]
    all_keywords = configured_keywords + extra_universal

    triggered_flags = _scan_keywords(transcript_lower, sentences, all_keywords)

    # ── Layer 2: AI-corroboration fallback ────────────────────────────────────
    # Triggered ONLY when deterministic scan finds nothing AND the AI has
    # already signalled HIGH or CRITICAL risk.
    if not triggered_flags and ai_result:
        ai_compliance   = ai_result.get("compliance", {})
        ai_risk_level   = ai_compliance.get("risk_level", "low")
        ai_escalate     = ai_compliance.get("escalation_required", False)
        ai_risk_flags   = ai_compliance.get("risk_flags", [])
        ai_violations   = ai_compliance.get("violations_detected", [])
        ai_sentiment    = ai_result.get("sentiment", {})
        ai_frustration  = ai_sentiment.get("frustration_detected", False)
        ai_score        = ai_sentiment.get("sentiment_score", 0.0)

        should_corroborate = (
            ai_risk_level in ("high", "critical")
            or ai_escalate
            or (ai_frustration and ai_score <= -0.6)
        )

        if should_corroborate:
            # Build synthetic flags from AI risk_flags and violations
            ai_sources = list(dict.fromkeys(ai_risk_flags + ai_violations))  # unique, ordered
            for rf in ai_sources:
                rf_clean = str(rf).replace("_", " ").lower()
                # Map common AI risk flag names to severity
                if any(w in rf_clean for w in ("legal", "lawsuit", "fraud", "critical", "threat", "hack")):
                    sev = "high"
                elif any(w in rf_clean for w in ("escalat", "complaint", "unauthoriz", "scam")):
                    sev = "high"
                else:
                    sev = "medium"

                triggered_flags.append({
                    "keyword":          rf_clean,
                    "severity":         sev,
                    "context":          f"AI-detected risk pattern: '{rf}'",
                    "policy_reference": f"AI Compliance Analysis — {ai_risk_level.upper()} risk as per Phase 2 Gemini scan",
                    "action_required":  sev == "high",
                    "source":           "ai_corroborated",
                })

            # If AI said escalate but has no specific flags, add a generic one
            if not triggered_flags and ai_escalate:
                triggered_flags.append({
                    "keyword":          "supervisor escalation required",
                    "severity":         "high",
                    "context":          "AI analysis determined immediate escalation is required",
                    "policy_reference": f"Phase 2 AI Assessment — Risk: {ai_risk_level.upper()}",
                    "action_required":  True,
                    "source":           "ai_corroborated",
                })

    # ── Scoring ───────────────────────────────────────────────────────────────
    normalized_risk = _score(triggered_flags, max(len(all_keywords), 1))

    # If all flags are AI-corroborated, cap score at 0.65 to distinguish
    # from deterministic matches (which can reach 1.0)
    if triggered_flags and all(f.get("source") == "ai_corroborated" for f in triggered_flags):
        normalized_risk = min(normalized_risk, 0.65)

    return {
        "flags":                  triggered_flags,
        "total_flags":            len(triggered_flags),
        "compliance_risk_score":  normalized_risk,
        "auto_escalate":          any(f["severity"] == "high" for f in triggered_flags),
    }


def _empty_result() -> dict:
    return {
        "flags":                 [],
        "total_flags":           0,
        "compliance_risk_score": 0.0,
        "auto_escalate":         False,
    }
