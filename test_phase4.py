import requests
import json

BASE_URL = "http://localhost:8000"
API_KEY = "vajra-2024-hackathon-transight"

print("--- Test 1: Health Check ---")
r1 = requests.get(f"{BASE_URL}/health")
print(f"Status: {r1.status_code}")
print(json.dumps(r1.json(), indent=2))

print("\n--- Test 2: Compliance Check (With API Key) ---")
r2 = requests.post(
    f"{BASE_URL}/api/v1/compliance/check",
    headers={"X-API-Key": API_KEY, "Content-Type": "application/json"},
    json={
        "client_id": "banking_client_01",
        "transcript": "Agent: Good morning. Customer: I shared my OTP with someone and Rs.85000 was transferred.",
        "domain": "banking"
    }
)
print(f"Status: {r2.status_code}")
if r2.status_code == 200:
    data = r2.json()
    print("Violations:", data.get("violation_count"))
    print("Overall Risk:", data.get("overall_risk_level"))
else:
    print(r2.text)

print("\n--- Test 3: Compliance Check (Missing API Key) ---")
r3 = requests.post(
    f"{BASE_URL}/api/v1/compliance/check",
    json={"client_id": "banking_client_01", "transcript": "test transcript here"}
)
print(f"Status: {r3.status_code}")
if r3.status_code != 200:
    print(r3.text)

print("\n--- Test 4: Analyze Text (With API Key) ---")
r4 = requests.post(
    f"{BASE_URL}/api/v1/analyze/text",
    headers={"X-API-Key": API_KEY, "Content-Type": "application/json"},
    json={
        "client_id": "banking_client_01",
        "transcript": "Agent: Good morning State Bank support. Customer: There is an unauthorized transaction of Rs.4200 on my account."
    }
)
print(f"Status: {r4.status_code}")
if r4.status_code == 200:
    data = r4.json()
    print("Status Result:", data.get("status"))
    print("Risk Level:", data.get("compliance", {}).get("risk_level", "None"))
    print("Has RAG actions:", bool(data.get("rag_actions")))
else:
    print(r4.text)
