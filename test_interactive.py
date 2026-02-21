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


class C:
    RESET = "\033[0m"; BOLD = "\033[1m"; DIM = "\033[2m"
    CYAN = "\033[96m"; GREEN = "\033[92m"; YELLOW = "\033[93m"
    RED = "\033[91m";  WHITE = "\033[97m"; MAGENTA = "\033[95m"

def print_result(result: dict):
    if result.get("status") == "failed" or "detail" in result:
        err = result.get('error') or result.get('detail')
        print(f"\n{C.RED}✖ API ERROR: {err}{C.RESET}\n")
        return

    # --- Phase 2: Core Analysis ---
    print(f"\n{C.BOLD}{C.CYAN}▸ Phase 2 — Core AI Analysis{C.RESET}")
    print(f"  {C.DIM}Summary: {result.get('summary', '')}{C.RESET}")
    
    intent = result.get('primary_intent', '')
    print(f"  {C.DIM}Intent : {C.RESET}{C.WHITE}{intent}{C.RESET}")
    
    sent = result.get('sentiment', {})
    score = sent.get('sentiment_score', 0)
    scol = C.GREEN if score > 0.2 else (C.RED if score < -0.2 else C.YELLOW)
    print(f"  {C.DIM}Sentiment: {C.RESET}{scol}{sent.get('overall', '').upper()} ({score}){C.RESET}")

    # --- Phase 3: RAG Action Plan ---
    rag = result.get("rag_actions")
    if rag:
        print(f"\n{C.BOLD}{C.MAGENTA}▸ Phase 3 — RAG Action Plan{C.RESET}")
        pri = rag.get('priority', '')
        pcol = C.RED if 'Critical' in pri or 'High' in pri else C.YELLOW
        print(f"  {C.DIM}Priority : {C.RESET}{pcol}{C.BOLD}{pri}{C.RESET}")
        
        print(f"  {C.DIM}Suggested Actions:{C.RESET}")
        for act in rag.get('suggested_actions', []):
            print(f"    • {C.WHITE}{act}{C.RESET}")
            
        print(f"  {C.DIM}Policy Justifications:{C.RESET}")
        for pol in rag.get('policy_justifications', []):
            print(f"    {C.DIM}↳ {pol}{C.RESET}")
            
        if rag.get('coaching_notes'):
            print(f"  {C.DIM}Coaching : {C.RESET}{C.YELLOW}{rag.get('coaching_notes')}{C.RESET}")

    # --- Phase 4: Deterministic Compliance ---
    det = result.get("deterministic_compliance")
    if det:
        print(f"\n{C.BOLD}{C.YELLOW}▸ Phase 4 — Deterministic Compliance Engine{C.RESET}")
        rscore = det.get("compliance_risk_score", 0)
        flags = det.get("flags", [])
        esc = det.get("auto_escalate", False)
        
        rcol = C.RED if rscore > 0.5 else (C.YELLOW if rscore > 0 else C.GREEN)
        print(f"  {C.DIM}Risk Score   : {C.RESET}{rcol}{rscore:.2f} / 1.00{C.RESET}")
        print(f"  {C.DIM}Total Flags  : {C.RESET}{C.WHITE}{det.get('total_flags', 0)}{C.RESET}")
        print(f"  {C.DIM}Auto-Escalate: {C.RESET}{C.RED if esc else C.GREEN}{'YES' if esc else 'NO'}{C.RESET}")

        if flags:
            print()
            for flag in flags:
                sev    = flag.get("severity","?")
                source = flag.get("source", "deterministic")
                fc     = C.RED if sev=="high" else (C.YELLOW if sev=="medium" else C.DIM)
                src_badge = (
                    f"{C.GREEN}✦ DETERMINISTIC{C.RESET}"
                    if source == "deterministic"
                    else f"{C.YELLOW}✧ AI-CORROBORATED{C.RESET}"
                )
                print(f"    {fc}[{sev.upper()}]{C.RESET} {src_badge}  {C.BOLD}{flag.get('keyword','')}{C.RESET}")
                print(f"    {C.DIM}Context : {flag.get('context','')[:80]}{C.RESET}")
                print(f"    {C.DIM}Policy  : {flag.get('policy_reference','')}{C.RESET}")
                if flag.get("action_required"):
                    print(f"    {C.RED}⚠  Immediate action required{C.RESET}")
                print()
    print("=" * 50)


if __name__ == "__main__":
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
                
            print("\nSending to API...")
            result = analyze_text(text)
            print_result(result)
            
        elif choice == '2':
            print("\n" + "-"*40)
            print("Enter the path to your audio file (e.g. sample_call.mp3)")
            filepath = input("> ")
            
            print("\nSending to API...")
            result = analyze_audio(filepath)
            print_result(result)
            
        elif choice == '3':
            print("Goodbye!")
            break
        else:
            print("Invalid choice. Try again.")
