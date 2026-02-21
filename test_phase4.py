"""
Phase 4 test — starts server automatically, runs analysis, saves phase4_out.json
and prints a formatted summary to the terminal.
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
import sys
import time
import subprocess
import os
import atexit

BASE_URL = "http://127.0.0.1:8000"

# ── ANSI colours ──────────────────────────────────────────────────────────────
class C:
    RESET = "\033[0m"; BOLD = "\033[1m"; DIM = "\033[2m"
    CYAN = "\033[96m"; GREEN = "\033[92m"; YELLOW = "\033[93m"
    RED = "\033[91m";  WHITE = "\033[97m"

def label(k, v, color=C.WHITE):
    print(f"  {C.DIM}{k:<30}{C.RESET}{color}{v}{C.RESET}")

def section(t):
    print(f"\n  {C.BOLD}{C.YELLOW}▸ {t}{C.RESET}")

def _wrap(text, w=50):
    words, lines, line = text.split(), [], ""
    for wd in words:
        if len(line) + len(wd) + 1 > w:
            lines.append(line); line = wd
        else:
            line = (line + " " + wd).strip()
    if line: lines.append(line)
    return lines

# ── Embedded server (subprocess with silenced output) ─────────────────────
# First check if a server is already running on port 8000
_server_proc = None
try:
    urllib.request.urlopen(f"{BASE_URL}/health", timeout=1)
    _existing_server = True
except Exception:
    _existing_server = False

if not _existing_server:
    _DEVNULL = open(os.devnull, 'wb')
    _server_proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "main:app",
         "--host", "127.0.0.1", "--port", "8000",
         "--log-level", "critical", "--no-access-log"],
        stdout=_DEVNULL, stderr=_DEVNULL
    )
    atexit.register(lambda: _server_proc.terminate() if _server_proc else None)

print(f"\n{C.BOLD}{C.CYAN}  VAJRA Phase 4 — Deterministic Compliance Test{C.RESET}")
print(f"  Starting API server ", end="", flush=True)
for _ in range(30):
    try:
        urllib.request.urlopen(f"{BASE_URL}/health", timeout=1)
        break
    except Exception:
        time.sleep(0.5)
        print("·", end="", flush=True)
else:
    print(f"\n{C.RED}  Server failed to start.{C.RESET}")
    sys.exit(1)
print(f" {C.GREEN}Ready ✔{C.RESET}\n")

# ── Run test ──────────────────────────────────────────────────────────────────
TRANSCRIPT = (
    "Hello, I am very upset. I demand to speak to a supervisor now. "
    "If this isn't fixed, I will file a lawsuit!"
)

print(f"  {C.DIM}Transcript: \"{TRANSCRIPT[:60]}…\"{C.RESET}")
print(f"  {C.DIM}Sending to Gemini, please wait…{C.RESET}\n")

req = urllib.request.Request(
    f"{BASE_URL}/api/v1/analyze/text",
    data=json.dumps({"client_id": "banking", "transcript": TRANSCRIPT}).encode(),
    headers={"Content-Type": "application/json"},
    method="POST"
)

try:
    with urllib.request.urlopen(req, timeout=180) as response:
        result = json.loads(response.read().decode("utf-8"))
except urllib.error.HTTPError as e:
    result = json.loads(e.read().decode("utf-8"))
except urllib.error.URLError as e:
    print(f"  {C.RED}✖  Connection Error: {e.reason}{C.RESET}")
    sys.exit(1)
except Exception as e:
    print(f"  {C.RED}✖  Error: {e}{C.RESET}")
    sys.exit(1)

# ── Save JSON ─────────────────────────────────────────────────────────────────
with open("phase4_out.json", "w", encoding="utf-8") as f:
    json.dump(result, f, indent=2, ensure_ascii=False)
print(f"  {C.GREEN}✔  Output saved to phase4_out.json{C.RESET}")

# ── Print formatted summary ───────────────────────────────────────────────────
print(f"\n{C.BOLD}{C.CYAN}{'━'*54}")
print(f"  VAJRA PHASE 4 ANALYSIS REPORT")
print(f"{'━'*54}{C.RESET}")

# Overview
section("Overview")
status = result.get("status","?")
label("Status", status, C.GREEN if status=="completed" else C.RED)
label("Language", result.get("language_detected","?"))
label("Processing Time", f"{result.get('processing_time_ms','?')} ms")

# Summary
section("Summary")
for line in _wrap(result.get("summary",""), 50):
    print(f"  {C.WHITE}{line}{C.RESET}")

# Sentiment
s = result.get("sentiment",{})
if s:
    section("Sentiment")
    score = s.get("sentiment_score", 0)
    sc = C.RED if score <= -0.2 else (C.GREEN if score >= 0.2 else C.YELLOW)
    label("Overall", s.get("overall","?"))
    label("Score", f"{score:+.2f}", sc)
    label("Customer Mood", s.get("customer_sentiment","?"))
    label("Frustration Detected",
          "YES" if s.get("frustration_detected") else "No",
          C.RED if s.get("frustration_detected") else C.GREEN)

# Compliance AI
c = result.get("compliance",{})
if c:
    section("Compliance (Gemini AI)")
    rl = c.get("risk_level","?")
    rc = C.RED if rl in ("high","critical") else (C.YELLOW if rl=="medium" else C.GREEN)
    label("Risk Level", rl.upper(), rc)
    label("Escalation Required",
          "YES" if c.get("escalation_required") else "No",
          C.RED if c.get("escalation_required") else C.GREEN)
    if c.get("risk_flags"):
        label("Risk Flags", ", ".join(c["risk_flags"]), C.YELLOW)
    if c.get("violations_detected"):
        label("Violations","")
        for v in c["violations_detected"]:
            print(f"    {C.RED}• {v}{C.RESET}")

# Phase 4 Deterministic
det = result.get("deterministic_compliance")
if det:
    section("Phase 4 — Deterministic Compliance Engine")
    ds  = det.get("compliance_risk_score", 0)
    dsc = C.RED if ds >= 0.7 else (C.YELLOW if ds >= 0.4 else C.GREEN)
    label("Risk Score",   f"{ds:.2f} / 1.00", dsc)
    label("Total Flags",  str(det.get("total_flags",0)),
          C.RED if det.get("total_flags",0) > 0 else C.GREEN)
    label("Auto-Escalate",
          "YES — Supervisor Required" if det.get("auto_escalate") else "No",
          C.RED if det.get("auto_escalate") else C.GREEN)
    flags = det.get("flags",[])
    if flags:
        print()
        for flag in flags:
            sev = flag.get("severity","?")
            fc  = C.RED if sev=="high" else (C.YELLOW if sev=="medium" else C.DIM)
            print(f"    {fc}[{sev.upper()}]{C.RESET} Keyword: {C.BOLD}{flag.get('keyword','')}{C.RESET}")
            ctx = flag.get("context","")
            print(f"    {C.DIM}Context : {ctx[:80]}{C.RESET}")
            print(f"    {C.DIM}Policy  : {flag.get('policy_reference','')}{C.RESET}")
            if flag.get("action_required"):
                print(f"    {C.RED}⚠  Immediate action required{C.RESET}")
            print()

# Agent Performance
p = result.get("agent_performance",{})
if p:
    section("Agent Performance")
    sc  = p.get("score",0)
    scc = C.GREEN if sc>=80 else (C.YELLOW if sc>=60 else C.RED)
    print(f"  {C.BOLD}Score: {scc}{sc}/100{C.RESET}")
    label("Call Outcome", p.get("call_outcome","?"), C.CYAN)
    label("Issue Resolved",
          "✔" if p.get("issue_resolved") else "✖",
          C.GREEN if p.get("issue_resolved") else C.RED)

# RAG Actions
rag = result.get("rag_actions")
if rag:
    section("Phase 3 — RAG Action Plan")
    pri = rag.get("priority","?")
    pc  = C.RED if "P1" in pri else (C.YELLOW if "P2" in pri else C.GREEN)
    label("Priority", pri, pc)
    label("Human Review",
          "Required" if rag.get("human_review_needed") else "Not required",
          C.RED if rag.get("human_review_needed") else C.GREEN)
    actions = rag.get("suggested_actions",[])
    if actions:
        print(f"\n  {C.DIM}Suggested Actions:{C.RESET}")
        for i, a in enumerate(actions,1):
            print(f"    {C.CYAN}{i}.{C.RESET} {a}")
    notes = rag.get("coaching_notes","")
    if notes:
        print(f"\n  {C.DIM}Coaching Notes:{C.RESET}")
        for line in _wrap(notes, 50):
            print(f"    {C.WHITE}{line}{C.RESET}")

print(f"\n{C.BOLD}{C.CYAN}{'━'*54}{C.RESET}\n")
