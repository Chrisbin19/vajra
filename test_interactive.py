# ── Venv auto-bootstrap (run with any Python, always uses venv) ──────────────
import sys, os as _os
_venv_py = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "venv", "Scripts", "python.exe")
if _os.path.isfile(_venv_py) and _venv_py != sys.executable:
    import subprocess as _sp; sys.exit(_sp.run([_venv_py] + sys.argv).returncode)
# ─────────────────────────────────────────────────────────────────────────────

import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import urllib.request
import urllib.error
import json
import uuid
import mimetypes
import time
import subprocess
import os
import atexit

BASE_URL = "http://localhost:8000"

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
    content_type = f'multipart/form-data; boundary={boundary}'
    return b'\r\n'.join(body), content_type

def analyze_text(transcript):
    url = f"{BASE_URL}/api/v1/analyze/text"
    data = json.dumps({
        "client_id": "test_client",
        "transcript": transcript
    }).encode('utf-8')
    
    req = urllib.request.Request(url, data=data, method="POST", headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        return json.loads(e.read().decode('utf-8'))

def analyze_audio(filepath):
    url = f"{BASE_URL}/api/v1/analyze/audio"
    body, content_type = encode_multipart_formdata({"client_id": "test_client"}, {"audio_file": filepath})
    
    if not body:
        return {"error": "Failed to load file"}
        
    req = urllib.request.Request(url, data=body, method="POST", headers={'Content-Type': content_type})
    try:
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        return json.loads(e.read().decode('utf-8'))


if __name__ == "__main__":
    # ── Embedded server (subprocess with silenced output) ─────────────────────
    # First check if a server is already running on port 8000
    print("Initializing test environment...")
    _server_proc = None
    try:
        urllib.request.urlopen(f"{BASE_URL}/health", timeout=1)
        _existing_server = True
    except Exception:
        _existing_server = False

    if not _existing_server:
        print("Starting local API server in background...")
        _DEVNULL = open(os.devnull, 'wb')
        _server_proc = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "main:app",
             "--host", "127.0.0.1", "--port", "8000",
             "--log-level", "critical", "--no-access-log"],
            stdout=_DEVNULL, stderr=_DEVNULL
        )
        atexit.register(lambda: _server_proc.terminate() if _server_proc else None)

        for _ in range(30):
            try:
                urllib.request.urlopen(f"{BASE_URL}/health", timeout=1)
                break
            except Exception:
                time.sleep(0.5)
        else:
            print("❌ Server failed to start.")
            sys.exit(1)

    print("=" * 50)
    print(" VAJRA PHASE 1 - INTERACTIVE TESTER ")
    print("=" * 50)
    
    while True:
        print("\nWhat would you like to test?")
        print("1. Text Transcript File Upload")
        print("2. Audio File Upload")
        print("3. Exit")
        
        choice = input("\nEnter your choice (1/2/3): ").strip()
        
        if choice == '1':
            print("\n" + "-"*40)
            print("Enter the path to your text transcript file (e.g. transcript.txt)")
            filepath = input("> ").strip()
            
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    text = f.read()
            except Exception as e:
                print(f"⚠️  Error reading file: {e}")
                continue
                
            if len(text.strip()) < 10:
                print("⚠️  Error: Transcript in file must be at least 10 characters!")
                continue
                
            print(f"\nSending '{filepath}' to API...")
            result = analyze_text(text)
            
            print("\n" + "="*40)
            print("API RESPONSE (PHASE 2 JSON):")
            
            # Make a copy to print Phase 2 separately
            import copy
            phase2 = copy.deepcopy(result)
            rag_data = phase2.pop('rag_actions', None)
            
            print(json.dumps(phase2, indent=2, ensure_ascii=False))
            
            if rag_data:
                print("\n" + "="*40)
                print("PHASE 3: ACTIONABLE RAG REPORT:")
                print(json.dumps(rag_data, indent=2, ensure_ascii=False))
                
            print("="*40)
            
        elif choice == '2':
            print("\n" + "-"*40)
            print("Enter the path to your audio file (e.g. sample_call.mp3)")
            filepath = input("> ")
            
            print("\nSending to API...")
            result = analyze_audio(filepath)
            
            print("\n" + "="*40)
            print("API RESPONSE (PHASE 2 JSON):")
            
            import copy
            phase2 = copy.deepcopy(result)
            rag_data = phase2.pop('rag_actions', None)
            
            print(json.dumps(phase2, indent=2, ensure_ascii=False))
            
            if rag_data:
                print("\n" + "="*40)
                print("PHASE 3: ACTIONABLE RAG REPORT:")
                print(json.dumps(rag_data, indent=2, ensure_ascii=False))
                
            print("="*40)
            
        elif choice == '3':
            print("Goodbye!")
            break
        else:
            print("Invalid choice. Try again.")
