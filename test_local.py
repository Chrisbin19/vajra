"""
VAJRA Local Test Suite
Run with: python test_local.py (server must be running: uvicorn main:app --reload)

FIXES applied:
  - API_KEY constant added
  - AUTH_HEADERS injected into request() helper for ALL POST calls
  - Test 6: compliance check added (Phase 4)
  - Test 7: 403 without API key (verifies auth is working)
"""
import urllib.request
import urllib.error
import json
import uuid
import mimetypes
import time

BASE_URL    = "http://localhost:8000"
API_KEY     = "vajra-demo-key-2026"        # FIX: was missing entirely
AUTH_HEADERS = {"X-API-Key": API_KEY}      # injected into every POST


def request(method, path, data=None, headers=None):
    if headers is None:
        headers = {}
    # Always inject auth header for non-GET requests
    if method != "GET":
        headers.update(AUTH_HEADERS)
    url = f"{BASE_URL}{path}"
    if data is not None and not isinstance(data, bytes):
        data = json.dumps(data).encode('utf-8')
        if 'Content-Type' not in headers:
            headers['Content-Type'] = 'application/json'
    req = urllib.request.Request(url, data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        try:
            return json.loads(e.read().decode('utf-8'))
        except Exception:
            return {"status_code": e.code, "error": str(e)}
    except urllib.error.URLError as e:
        return {"error": str(e.reason)}
    except Exception as e:
        return {"error": str(e)}


def encode_multipart_formdata(fields, files):
    boundary = uuid.uuid4().hex
    body = []
    for key, value in fields.items():
        body.extend([
            f'--{boundary}'.encode('utf-8'),
            f'Content-Disposition: form-data; name="{key}"'.encode('utf-8'),
            b'',
            value.encode('utf-8')
        ])
    for key, (filename, file_content) in files.items():
        mime_type = mimetypes.guess_type(filename)[0] or 'application/octet-stream'
        body.extend([
            f'--{boundary}'.encode('utf-8'),
            f'Content-Disposition: form-data; name="{key}"; filename="{filename}"'.encode('utf-8'),
            f'Content-Type: {mime_type}'.encode('utf-8'),
            b'',
            file_content if isinstance(file_content, bytes) else file_content.encode('utf-8')
        ])
    body.append(f'--{boundary}--'.encode('utf-8'))
    body.append(b'')
    return b'\r\n'.join(body), f'multipart/form-data; boundary={boundary}'


# ── Wait for server ──
print("Waiting for server...")
for i in range(10):
    try:
        req = urllib.request.Request(f"{BASE_URL}/health")
        with urllib.request.urlopen(req) as r:
            if r.status == 200:
                print("Server ready.\n")
                break
    except Exception:
        time.sleep(1)


print("=== TEST 1: Health Check (no auth needed) ===")
print(json.dumps(request("GET", "/health"), indent=2))


print("\n=== TEST 2: Text Input (banking_client_01) ===")
try:
    with open("sample_transcript.txt", "r", encoding="utf-8") as f:
        transcript_content = f.read()
    print(json.dumps(request("POST", "/api/v1/analyze/text", data={
        "client_id": "banking_client_01",
        "transcript": transcript_content
    }), indent=2))
except FileNotFoundError:
    print("sample_transcript.txt not found — skipping")


print("\n=== TEST 3: Audio Input (MP3 file) ===")
try:
    with open("sample_call.mp3", "rb") as f:
        audio_content = f.read()
    body, content_type = encode_multipart_formdata(
        {"client_id": "banking_client_01"},
        {"audio_file": ("sample_call.mp3", audio_content)}
    )
    headers = {"Content-Type": content_type}
    headers.update(AUTH_HEADERS)
    print(json.dumps(request("POST", "/api/v1/analyze/audio", data=body, headers=headers), indent=2))
except FileNotFoundError:
    print("sample_call.mp3 not found — skipping (audio test is optional)")


print("\n=== TEST 4: Reject Invalid File Type ===")
body, content_type = encode_multipart_formdata(
    {"client_id": "banking_client_01"},
    {"audio_file": ("document.pdf", b"dummy pdf content")}
)
headers = {"Content-Type": content_type}
headers.update(AUTH_HEADERS)
result = request("POST", "/api/v1/analyze/audio", data=body, headers=headers)
print(json.dumps(result, indent=2))
if "Unsupported" in str(result.get("detail", "")):
    print("✅ Invalid file type correctly rejected")
else:
    print("⚠️  Check result above")


print("\n=== TEST 5: Reject Short Transcript ===")
result = request("POST", "/api/v1/analyze/text", data={
    "client_id": "banking_client_01",
    "transcript": "hi"
})
print(json.dumps(result, indent=2))
if "detail" in result or "error" in result:
    print("✅ Short transcript correctly rejected")


print("\n=== TEST 6: Phase 4 Compliance Check ===")
result = request("POST", "/api/v1/compliance/check", data={
    "client_id": "banking_client_01",
    "transcript": "Agent: Good morning. Customer: I shared my OTP with someone and Rs.85000 was transferred.",
    "domain": "banking"
})
print(json.dumps(result, indent=2))
if result.get("violation_count", 0) >= 1 and result.get("overall_risk_level") == "critical":
    print("✅ Phase 4 correctly flagged OTP sharing as critical violation")
else:
    print("⚠️  Check compliance result above")


print("\n=== TEST 7: 403 Without API Key ===")
req_no_auth = urllib.request.Request(
    f"{BASE_URL}/api/v1/compliance/check",
    data=json.dumps({
        "client_id": "banking_client_01",
        "transcript": "test transcript text here"
    }).encode('utf-8'),
    method="POST",
    headers={"Content-Type": "application/json"}   # intentionally NO X-API-Key
)
try:
    with urllib.request.urlopen(req_no_auth) as r:
        print("❌ Should have been rejected without API key!")
except urllib.error.HTTPError as e:
    resp = json.loads(e.read().decode('utf-8'))
    if e.code == 403:
        print(f"✅ 403 Forbidden returned correctly: {resp.get('detail', '')}")
    else:
        print(f"Got {e.code}: {resp}")