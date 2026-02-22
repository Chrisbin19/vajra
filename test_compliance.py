import requests
import json

url = "http://localhost:8000/api/v1/analyze/text"
headers = {
    "X-API-Key": "vajra-demo-key-2026",
    "Content-Type": "application/json"
}
data = {
    "client_id": "banking_client_01",
    "transcript": "Agent: Good morning, how can I help you today?\nCustomer: I have a question about my balance. Everything is resolved, thank you."
}

response = requests.post(url, headers=headers, json=data)
print(f"Status Code: {response.status_code}")
with open("test_compliance_output.json", "w") as f:
    json.dump(response.json(), f, indent=2)
