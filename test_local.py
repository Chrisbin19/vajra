import urllib.request
import urllib.error
import json
import uuid
import mimetypes
import time

BASE_URL = "http://localhost:8000"

def request(method, path, data=None, headers=None):
    if headers is None:
        headers = {}
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
        except:
            return {"status": e.code, "error": str(e)}
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
    content_type = f'multipart/form-data; boundary={boundary}'
    return b'\r\n'.join(body), content_type

# Simple wait for server to be up
for i in range(10):
    try:
        req = urllib.request.Request("http://localhost:8000/health")
        with urllib.request.urlopen(req) as r:
            if r.status == 200:
                break
    except:
        time.sleep(1)

print("=== TEST 1: Health Check ===")
print(json.dumps(request("GET", "/health"), indent=2))

print("\n=== TEST 2: Text Input (File-based Transcript) ===")
try:
    with open("sample_transcript.txt", "r", encoding="utf-8") as f:
        transcript_content = f.read()
    print(json.dumps(request("POST", "/api/v1/analyze/text", data={
        "client_id": "banking_client_01",
        "transcript": transcript_content
    }), indent=2))
except Exception as e:
    print(f"Error reading sample_transcript.txt: {e}")

print("\n=== TEST 3: Audio Input (Actual MP3 File) ===")
try:
    with open("sample_call.mp3", "rb") as f:
        audio_content = f.read()
    body, content_type = encode_multipart_formdata({"client_id": "banking_client_01"}, {"audio_file": ("sample_call.mp3", audio_content)})
    print(json.dumps(request("POST", "/api/v1/analyze/audio", data=body, headers={"Content-Type": content_type}), indent=2))
except Exception as e:
    print(f"Error reading sample_call.mp3: {e}")

print("\n=== TEST 4: Reject Invalid File Type ===")
body, content_type = encode_multipart_formdata({"client_id": "banking_client_01"}, {"audio_file": ("document.pdf", b"dummy pdf content")})
print(json.dumps(request("POST", "/api/v1/analyze/audio", data=body, headers={"Content-Type": content_type}), indent=2))

print("\n=== TEST 5: Reject Empty Transcript ===")
print(json.dumps(request("POST", "/api/v1/analyze/text", data={
    "client_id": "banking_client_01",
    "transcript": "hi"
}), indent=2))
