# test_gemini.py
# Run with: python test_gemini.py

import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, ".")

from core.gemini import analyze_text_sync

# Banking fraud transcript
TRANSCRIPT = """Agent: Good morning, State Bank support, I'm Priya. How can I help?
Customer: Hi Priya, I'm really worried. There's an unauthorized transaction of Rs.4200 
on my account from January 14th. I never made this payment.
Agent: I understand your concern and I apologize. Let me verify your identity first. 
Can you give me the last 4 digits of your account?
Customer: It's 7823.
Agent: Thank you. I can see the suspicious transaction. I'm raising a dispute ticket 
and blocking your card right now. You'll get an SMS confirmation.
Customer: Thank you so much, that's a huge relief."""

CLIENT_CONFIG = {
    "domain": "banking",
    "company_name": "State Bank",
    "products": ["savings account", "debit card", "credit card", "personal loan"],
    "risk_triggers": ["unauthorized transaction", "fraud", "OTP shared", "large transfer"]
}

print("Running Phase 2 analysis...")
print("=" * 60)

result = analyze_text_sync(TRANSCRIPT, CLIENT_CONFIG)

# Check every required field
checks = [
    ("status", result.get("status") == "completed", result.get("status")),
    ("summary", bool(result.get("summary")), result.get("summary", "")[:80]),
    ("language_detected", bool(result.get("language_detected")), result.get("language_detected")),
    ("sentiment_score in [-1, 1]", -1.0 <= float(result.get("sentiment", {}).get("sentiment_score", 999)) <= 1.0,
     result.get("sentiment", {}).get("sentiment_score")),
    ("primary_intent (string)", isinstance(result.get("primary_intent"), str), result.get("primary_intent")),
    ("secondary_intents (list)", isinstance(result.get("secondary_intents"), list), result.get("secondary_intents")),
    ("entities.amounts_mentioned", "Rs.4200" in str(result.get("entities", {}).get("amounts_mentioned", [])),
     result.get("entities", {}).get("amounts_mentioned")),
    ("topics_discussed (list)", isinstance(result.get("topics_discussed"), list) and len(result.get("topics_discussed", [])) > 0,
     result.get("topics_discussed")),
    ("processing_time_ms", bool(result.get("processing_time_ms")), f"{result.get('processing_time_ms')}ms"),
]

all_passed = True
for name, passed, value in checks:
    status = "✅ PASS" if passed else "❌ FAIL"
    if not passed:
        all_passed = False
    print(f"{status} | {name}: {value}")

print("=" * 60)
if all_passed:
    print("✅ ALL CHECKS PASSED — Phase 2 deliverable complete!")
else:
    print("❌ SOME CHECKS FAILED — fix the failures above")

print("\nFull result JSON:")
import json
print(json.dumps(result, indent=2, default=str))
