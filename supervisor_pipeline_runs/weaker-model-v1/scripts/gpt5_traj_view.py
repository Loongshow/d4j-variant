"""Copy of mx_traj_view.py that also handles runs without a submission (timeouts); otherwise identical. Safe, read-only view of one run for failure-mode labelling. Usage: mx_traj_view.py <run_dir> [--max N]
Prints the final submission (ranked predictions + evidence chain) and the visible conversation of mini-swe-agent.traj.json:
for each assistant turn its text and tool-call arguments, for each tool turn its output (truncated to N chars, default 1500).
Never prints the system prompt, any key whose name contains 'reason', 'think' or 'encrypt' (hidden reasoning), and never opens
raw_agent_output.txt, probe files or any credential file."""
import json, sys, os
rd = sys.argv[1]; N = int(sys.argv[sys.argv.index("--max") + 1]) if "--max" in sys.argv else 1500
HIDE = ("reason", "think", "encrypt")
def txt(c):
    if isinstance(c, str): return c
    if isinstance(c, list): return " ".join(x.get("text", "") for x in c if isinstance(x, dict) and not any(h in str(x.get("type", "")).lower() for h in HIDE))
    return ""
_sp = os.path.join(rd, "fault-localization-submission.json")
sub = json.load(open(_sp)) if os.path.exists(_sp) else {}
if not sub: print("=== NO SUBMISSION (the run ended without submitting)")
print("=== SUBMISSION (final ranking)")
for p in sub.get("predictions", []): print(f"  {p['rank']:2d}. {p['class']}::{p['method']}")
print("=== EVIDENCE CHAIN")
for e in sub.get("evidence_chain", []):
    print(" - evidence:", e.get("evidence", "")); print("   inference:", e.get("inference_summary", ""))
t = json.load(open(os.path.join(rd, "mini-swe-agent.traj.json")))
print("=== VISIBLE TRAJECTORY")
step = 0
for m in t.get("messages", []):
    role = m.get("role")
    if role == "system": continue
    if role == "user" and step == 0: print("[task prompt omitted]"); step += 1; continue
    body = txt(m.get("content"))
    if role == "assistant":
        step += 1
        if body.strip(): print(f"--- assistant {step}: {body[:N]}")
        for c in m.get("tool_calls") or []:
            a = (c.get("function") or {}).get("arguments", "")
            print(f"    call: {a[:N]}")
    elif role in ("tool", "user"):
        print(f"    output: {body[:N]}")
