"""
VAJRA Interactive Tester
Run against live server: python test_interactive.py
Server must be running: uvicorn main:app --reload

FIXES applied:
  - client_id changed from "test_client" to "banking_client_01" (config file exists)
  - X-API-Key header added to all requests
"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import urllib.request
import urllib.error
import json
import uuid
import mimetypes
import copy

BASE_URL = "http://localhost:8000"
API_KEY  = "vajra-demo-key-2026"     # matches DEMO_KEY in api/dependencies.py


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
    for key, filepath in files.items():
        try:
            with open(filepath, 'rb') as f:
                file_content = f.read()
            filename = filepath.split('/')[-1].split('\\')[-1]
            mime_type = mimetypes.guess_type(filename)[0] or 'application/octet-stream'
            body.extend([
                f'--{boundary}'.encode('utf-8'),
                f'Content-Disposition: form-data; name="{key}"; filename="{filename}"'.encode('utf-8'),
                f'Content-Type: {mime_type}'.encode('utf-8'),
                b'',
                file_content
            ])
        except Exception as e:
            print(f"Error reading file {filepath}: {e}")
            return None, None
    body.append(f'--{boundary}--'.encode('utf-8'))
    body.append(b'')
    return b'\r\n'.join(body), f'multipart/form-data; boundary={boundary}'


def analyze_text(transcript):
    """Send transcript to /analyze/text — banking_client_01 + API key."""
    url = f"{BASE_URL}/api/v1/analyze/text"
    data = json.dumps({
        "client_id": "banking_client_01",     # FIX: was "test_client", no config exists
        "transcript": transcript
    }).encode('utf-8')
    req = urllib.request.Request(
        url, data=data, method="POST",
        headers={
            'Content-Type': 'application/json',
            'X-API-Key': API_KEY,             # FIX: auth header was missing
        }
    )
    try:
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        return json.loads(e.read().decode('utf-8'))


def analyze_audio(filepath):
    """Send audio file to /analyze/audio — banking_client_01 + API key."""
    url = f"{BASE_URL}/api/v1/analyze/audio"
    body, content_type = encode_multipart_formdata(
        {"client_id": "banking_client_01"},   # FIX: was "test_client", no config exists
        {"audio_file": filepath}
    )
    if not body:
        return {"error": "Failed to load file"}
    req = urllib.request.Request(
        url, data=body, method="POST",
        headers={
            'Content-Type': content_type,
            'X-API-Key': API_KEY,             # FIX: auth header was missing
        }
    )
    try:
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        return json.loads(e.read().decode('utf-8'))


def print_result(result):
    """Prints Phase 2 analysis and Phase 3 RAG report separately."""
    phase2 = copy.deepcopy(result)
    rag_data = phase2.pop('rag_actions', None)

    print("\n" + "=" * 50)
    print("API RESPONSE — PHASE 2 (CONVERSATION ANALYSIS):")
    print("=" * 50)
    print(json.dumps(phase2, indent=2, ensure_ascii=False))

    if rag_data:
        print("\n" + "=" * 50)
        print("PHASE 3 — RAG COMPLIANCE ACTION PLAN:")
        print("=" * 50)
        print(json.dumps(rag_data, indent=2, ensure_ascii=False))
    print("=" * 50)


if __name__ == "__main__":
    print("=" * 50)
    print(" VAJRA — INTERACTIVE TESTER")
    print(f" Server : {BASE_URL}")
    print(f" API Key: {API_KEY}")
    print("=" * 50)

    while True:
        print("\nOptions:")
        print("1. Analyze text transcript from file")
        print("2. Analyze audio file")
        print("3. Exit")

        choice = input("\nChoice (1/2/3): ").strip()

        if choice == '1':
            filepath = input("\nText file path (e.g. sample_transcript.txt): ").strip()
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    text = f.read()
                if len(text.strip()) < 10:
                    print("Error: transcript must be at least 10 characters.")
                    continue
                print(f"\nSending '{filepath}'...")
                print_result(analyze_text(text))
            except Exception as e:
                print(f"Error: {e}")

        elif choice == '2':
            filepath = input("\nAudio file path (e.g. sample_call.mp3): ").strip()
            print("\nUploading (may take 5-15 seconds for Gemini File API)...")
            print_result(analyze_audio(filepath))

        elif choice == '3':
            print("Done.")
            break
        else:
            print("Invalid choice.")