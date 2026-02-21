"""
Interactive tester for VAJRA API — with formatted, readable terminal output.
Starts the FastAPI server automatically in a background thread.
"""
# ── Venv auto-bootstrap (run with any Python, always uses venv) ──────────────
import sys, os as _os
_venv_py = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "venv", "Scripts", "python.exe")
if _os.path.isfile(_venv_py) and _venv_py != sys.executable:
    import subprocess as _sp; sys.exit(_sp.run([_venv_py] + sys.argv).returncode)
# ─────────────────────────────────────────────────────────────────────────────

import urllib.request
import urllib.error
import json
import uuid
import mimetypes
import subprocess
import time
import sys
import os
import atexit
import logging # Keep this for other logging configurations

# ── Silence uvicorn & other library noise ────────────────────────────────────
logging.getLogger("uvicorn").setLevel(logging.CRITICAL)
logging.getLogger("uvicorn.access").setLevel(logging.CRITICAL)
logging.getLogger("uvicorn.error").setLevel(logging.CRITICAL)
logging.getLogger("httpx").setLevel(logging.CRITICAL)
logging.getLogger("google").setLevel(logging.CRITICAL)

BASE_URL = "http://127.0.0.1:8000"


# ── ANSI colour helpers ───────────────────────────────────────────────────────
class C:
    RESET  = "\033[0m"
    BOLD   = "\033[1m"
    CYAN   = "\033[96m"
    GREEN  = "\033[92m"
    YELLOW = "\033[93m"
    RED    = "\033[91m"
    BLUE   = "\033[94m"
    MAGENTA= "\033[95m"
    WHITE  = "\033[97m"
    DIM    = "\033[2m"

def h1(text):   print(f"\n{C.BOLD}{C.CYAN}{'━'*54}{C.RESET}")
def rule():     print(f"{C.DIM}{'─'*54}{C.RESET}")
def ok(msg):    print(f"  {C.GREEN}✔{C.RESET}  {msg}")
def warn(msg):  print(f"  {C.YELLOW}⚠{C.RESET}  {msg}")
def err(msg):   print(f"  {C.RED}✖{C.RESET}  {msg}")
def label(k, v, color=C.WHITE): print(f"  {C.DIM}{k:<30}{C.RESET}{color}{v}{C.RESET}")
def section(title): print(f"\n  {C.BOLD}{C.YELLOW}▸ {title}{C.RESET}")


# ── Embedded server (subprocess with silenced output) ─────────────────────
_DEVNULL = open(os.devnull, 'wb')
_server_proc = subprocess.Popen(
    [sys.executable, "-m", "uvicorn", "main:app",
     "--host", "127.0.0.1", "--port", "8000",
     "--log-level", "critical", "--no-access-log"],
    stdout=_DEVNULL, stderr=_DEVNULL
)
atexit.register(lambda: _server_proc.terminate())

print(f"\n{C.BOLD}{C.CYAN}  VAJRA — Conversation Intelligence{C.RESET}")
print(f"  Starting API server ", end="", flush=True)
for _ in range(30):
    try:
        urllib.request.urlopen(f"{BASE_URL}/health", timeout=1)
        break
    except Exception:
        time.sleep(0.5)
        print("·", end="", flush=True)
else:
    print(f"\n{C.RED}  Server failed to start. Exiting.{C.RESET}")
    sys.exit(1)
print(f" {C.GREEN}Ready ✔{C.RESET}\n")


# ── HTTP helpers ──────────────────────────────────────────────────────────────
def encode_multipart(fields, files):
    boundary = uuid.uuid4().hex
    body = []
    for key, value in fields.items():
        body.extend([
            f'--{boundary}'.encode(),
            f'Content-Disposition: form-data; name="{key}"'.encode(),
            b'', value.encode()
        ])
    for key, filepath in files.items():
        try:
            with open(filepath, 'rb') as f:
                fc = f.read()
            fname = os.path.basename(filepath)
            mime = mimetypes.guess_type(fname)[0] or 'application/octet-stream'
            body.extend([
                f'--{boundary}'.encode(),
                f'Content-Disposition: form-data; name="{key}"; filename="{fname}"'.encode(),
                f'Content-Type: {mime}'.encode(),
                b'', fc
            ])
        except Exception as e:
            err(f"Error reading file: {e}")
            return None, None
    body += [f'--{boundary}--'.encode(), b'']
    return b'\r\n'.join(body), f'multipart/form-data; boundary={boundary}'


def _call(req):
    try:
        with urllib.request.urlopen(req, timeout=180) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        return json.loads(e.read().decode())
    except urllib.error.URLError as e:
        return {"error": f"Connection error: {e.reason}"}


def analyze_text(transcript):
    data = json.dumps({"client_id": "test_client", "transcript": transcript}).encode()
    req  = urllib.request.Request(f"{BASE_URL}/api/v1/analyze/text", data=data,
                                   method="POST", headers={"Content-Type": "application/json"})
    return _call(req)


def analyze_audio(filepath):
    body, ct = encode_multipart({"client_id": "test_client"}, {"audio_file": filepath})
    if not body:
        return {"error": "Failed to load file"}
    req = urllib.request.Request(f"{BASE_URL}/api/v1/analyze/audio", data=body,
                                  method="POST", headers={"Content-Type": ct})
    return _call(req)


# ── Pretty-print result ───────────────────────────────────────────────────────
def print_result(result):
    if "error" in result and len(result) == 1:
        err(result["error"])
        return

    print(f"\n{C.BOLD}{C.CYAN}{'━'*54}{C.RESET}")
    print(f"  {C.BOLD}VAJRA ANALYSIS REPORT{C.RESET}")
    print(f"{C.BOLD}{C.CYAN}{'━'*54}{C.RESET}")

    # ── Overview ─────────────────────────────────────────────────────────────
    section("Overview")
    status = result.get("status", "?")
    color  = C.GREEN if status == "completed" else C.RED
    label("Status",         status,                               color)
    label("Input Type",     result.get("input_type", "?"),        C.WHITE)
    label("Language",       result.get("language_detected", "?"), C.WHITE)
    if result.get("languages_all"):
        label("All Languages", ", ".join(result["languages_all"]),C.DIM)
    label("Processing Time",
          f"{result.get('processing_time_ms', '?')} ms",          C.DIM)
    label("Conversation ID", result.get("conversation_id","?")[:8]+"…", C.DIM)

    # ── Summary ───────────────────────────────────────────────────────────────
    section("Summary")
    summary = result.get("summary", "")
    for line in _wrap(summary, 50):
        print(f"  {C.WHITE}{line}{C.RESET}")

    # ── Sentiment ─────────────────────────────────────────────────────────────
    sentiment = result.get("sentiment", {})
    if sentiment:
        section("Sentiment")
        overall = sentiment.get("overall","?")
        score   = sentiment.get("sentiment_score", 0)
        sc_col  = C.GREEN if score >= 0.2 else (C.RED if score <= -0.2 else C.YELLOW)
        label("Overall",          overall)
        label("Score",            f"{score:+.2f}", sc_col)
        label("Customer Mood",    sentiment.get("customer_sentiment","?"))
        label("Agent Tone",       sentiment.get("agent_sentiment","?"))
        label("Frustration",
              "YES" if sentiment.get("frustration_detected") else "No",
              C.RED if sentiment.get("frustration_detected") else C.GREEN)
        arc = sentiment.get("emotional_arc", [])
        if arc:
            label("Emotional Arc", " → ".join(arc))

    # ── Intent & Topics ───────────────────────────────────────────────────────
    section("Intent & Topics")
    label("Primary Intent", result.get("primary_intent","?"), C.CYAN)
    si = result.get("secondary_intents", [])
    if si:
        label("Secondary Intents", ", ".join(si))
    topics = result.get("topics_discussed", [])
    if topics:
        label("Topics", ", ".join(topics))

    # ── Entities ──────────────────────────────────────────────────────────────
    entities = result.get("entities", {})
    if entities:
        section("Extracted Entities")
        fields = [
            ("Amounts",  "amounts_mentioned"),
            ("Dates",    "dates_mentioned"),
            ("Accounts", "account_references"),
            ("Products", "products_mentioned"),
            ("Locations","locations_mentioned"),
            ("People",   "people_mentioned"),
        ]
        for display, key in fields:
            val = entities.get(key, [])
            if val:
                label(display, ", ".join(val))

    # ── Compliance (Gemini) ───────────────────────────────────────────────────
    compliance = result.get("compliance", {})
    if compliance:
        section("Compliance (AI)")
        risk_level = compliance.get("risk_level","?")
        rc = C.RED if risk_level in ("high","critical") else (C.YELLOW if risk_level=="medium" else C.GREEN)
        label("Risk Level", risk_level.upper(), rc)
        label("Escalation Required",
              "YES" if compliance.get("escalation_required") else "No",
              C.RED if compliance.get("escalation_required") else C.GREEN)
        viols = compliance.get("violations_detected", [])
        if viols:
            label("Violations", "")
            for v in viols:
                print(f"    {C.RED}• {v}{C.RESET}")
        rflags = compliance.get("risk_flags", [])
        if rflags:
            label("Risk Flags", ", ".join(rflags), C.YELLOW)

    # ── Phase 4: Deterministic Compliance ────────────────────────────────────
    det = result.get("deterministic_compliance")
    if det:
        section("Phase 4 — Deterministic Compliance Engine")
        det_score = det.get("compliance_risk_score", 0)
        ds_col    = C.RED if det_score >= 0.7 else (C.YELLOW if det_score >= 0.4 else C.GREEN)
        label("Risk Score",     f"{det_score:.2f} / 1.00", ds_col)
        label("Total Flags",    str(det.get("total_flags", 0)),
              C.RED if det.get("total_flags",0) > 0 else C.GREEN)
        label("Auto-Escalate",
              "YES — Supervisor Required" if det.get("auto_escalate") else "No",
              C.RED if det.get("auto_escalate") else C.GREEN)
        flags = det.get("flags", [])
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

    # ── Agent Performance ─────────────────────────────────────────────────────
    perf = result.get("agent_performance", {})
    if perf:
        section("Agent Performance")
        score  = perf.get("score", 0)
        sc_col = C.GREEN if score>=80 else (C.YELLOW if score>=60 else C.RED)
        print(f"  {C.BOLD}Score: {sc_col}{score}/100{C.RESET}")
        label("Greeting Proper", "✔" if perf.get("greeting_proper") else "✖",
              C.GREEN if perf.get("greeting_proper") else C.RED)
        label("Empathy Shown",   "✔" if perf.get("empathy_shown")   else "✖",
              C.GREEN if perf.get("empathy_shown")   else C.RED)
        label("Issue Resolved",  "✔" if perf.get("issue_resolved")  else "✖",
              C.GREEN if perf.get("issue_resolved")  else C.RED)
        label("Call Outcome",    perf.get("call_outcome","?"),       C.CYAN)
        strengths = perf.get("strengths", [])
        if strengths:
            print(f"\n  {C.DIM}Strengths:{C.RESET}")
            for s in strengths: print(f"    {C.GREEN}+ {s}{C.RESET}")
        improvements = perf.get("improvements", [])
        if improvements:
            print(f"\n  {C.DIM}Improvements:{C.RESET}")
            for i in improvements: print(f"    {C.YELLOW}△ {i}{C.RESET}")

    # ── Phase 3 RAG Actions ───────────────────────────────────────────────────
    rag = result.get("rag_actions")
    if rag:
        section("Phase 3 — RAG Action Plan")
        priority = rag.get("priority","?")
        pc = C.RED if "P1" in priority else (C.YELLOW if "P2" in priority else C.GREEN)
        label("Priority",       priority, pc)
        label("Human Review",
              "Required" if rag.get("human_review_needed") else "Not required",
              C.RED if rag.get("human_review_needed") else C.GREEN)
        actions = rag.get("suggested_actions", [])
        if actions:
            print(f"\n  {C.DIM}Suggested Actions:{C.RESET}")
            for i, a in enumerate(actions, 1):
                print(f"    {C.CYAN}{i}.{C.RESET} {a}")
        notes = rag.get("coaching_notes","")
        if notes:
            print(f"\n  {C.DIM}Coaching Notes:{C.RESET}")
            for line in _wrap(notes, 50):
                print(f"    {C.WHITE}{line}{C.RESET}")

    print(f"\n{C.BOLD}{C.CYAN}{'━'*54}{C.RESET}\n")


def _wrap(text, width):
    """Word-wrap text to `width` characters."""
    words, lines, line = text.split(), [], ""
    for w in words:
        if len(line) + len(w) + 1 > width:
            lines.append(line)
            line = w
        else:
            line = (line + " " + w).strip()
    if line:
        lines.append(line)
    return lines


# ── Main loop ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print(f"{C.BOLD}{C.CYAN}{'━'*54}")
    print(f"  VAJRA   INTERACTIVE TESTER")
    print(f"{'━'*54}{C.RESET}")

    while True:
        print(f"\n  {C.BOLD}What would you like to test?{C.RESET}")
        print(f"  {C.CYAN}1.{C.RESET} Text Transcript")
        print(f"  {C.CYAN}2.{C.RESET} Audio File")
        print(f"  {C.CYAN}3.{C.RESET} Exit")

        choice = input(f"\n  {C.BOLD}Choice (1/2/3): {C.RESET}").strip()

        if choice == '1':
            rule()
            filepath = input(f"  Path to .txt transcript: ").strip()
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    text = f.read()
            except Exception as e:
                err(f"Cannot read file: {e}")
                continue
            if len(text.strip()) < 10:
                warn("Transcript must be at least 10 characters.")
                continue
            print(f"\n  {C.DIM}Sending to Gemini, please wait…{C.RESET}")
            result = analyze_text(text)
            print_result(result)

        elif choice == '2':
            rule()
            filepath = input(f"  Path to audio file: ").strip()
            print(f"\n  {C.DIM}Uploading & analysing audio, please wait…{C.RESET}")
            result = analyze_audio(filepath)
            print_result(result)

        elif choice == '3':
            print(f"\n  {C.DIM}Goodbye!{C.RESET}\n")
            break
        else:
            warn("Invalid choice. Please enter 1, 2, or 3.")
