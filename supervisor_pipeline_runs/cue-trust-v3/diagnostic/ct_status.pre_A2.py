"""Uniform run-status classification for cue-trust-v3, shared by ct_driver.py (replacement decisions) and ct_metrics.py (analysis).
It applies the existing uniform provider-failure rule from adversarial-break-v1 (diagnostic/PROVIDER_STALL_RULE.md, rules 1-3) unchanged:
  rule 1  harness `timeout` with <= 2 model calls and <= 2 executed commands                    -> provider_stall
  rule 2  harness `timeout`, last recorded event is a tool result, > 60 s left before the kill   -> provider_stall
  rule 3  harness `provider_error` caused by an oversized request (context window)               -> context_overflow
INFRASTRUCTURE statuses are excluded from every Acc@1 denominator and may be replaced (one replacement per slot; a second
infrastructure failure on the same slot halts the driver). BEHAVIOURAL statuses are outcomes: counted (intention to treat), never re-run.
INTEGRITY (harness `protocol_violation`: production or test source changed) is excluded and halts the driver. Any other status halts for review."""
import json, os, re, datetime
INFRASTRUCTURE = {"provider_error", "provider_stall", "startup_timeout", "agent_not_installed", "provider_not_configured"}
BEHAVIOURAL = {"completed", "timeout", "context_overflow"}
INTEGRITY = {"protocol_violation"}   # source changed during the run: excluded (pre-registered exclusion) and the driver halts
def _rj(p):
    try: return json.load(open(p))
    except Exception: return {}
def classify(rd, budget_seconds=300):
    man = _rj(f"{rd}/run_manifest.json"); traj = _rj(f"{rd}/mini-swe-agent.traj.json")
    harness = man.get("status"); st = harness; final_gap = last_role = None
    msgs = traj.get("messages") or []; ms = ((traj.get("info") or {}).get("model_stats") or {})
    commands = sum(len(m.get("tool_calls") or []) for m in msgs if m.get("role") == "assistant")
    if st == "timeout":
        stall = (ms.get("api_calls") or 0) <= 2 and commands <= 2
        try:
            cl = open(f"{rd}/commands.log").read(); t0 = re.search(r"execution_timer_started_at: (\S+)", cl).group(1)
            t0 = datetime.datetime.fromisoformat(t0.replace("Z", "+00:00")).timestamp()
            ev = [(m["role"], float(m["extra"]["timestamp"])) for m in msgs if m.get("role") in ("assistant", "tool") and (m.get("extra") or {}).get("timestamp") is not None]
            if ev: last_role = ev[-1][0]; final_gap = round(t0 + budget_seconds - ev[-1][1], 1)
        except Exception: pass
        if last_role == "tool" and final_gap is not None and final_gap > 60: stall = True
        if stall: st = "provider_stall"
    if st == "provider_error":
        try: raw = open(f"{rd}/raw_agent_output.txt", errors="replace").read()
        except Exception: raw = ""
        if "prompt is too long" in raw or "ContextWindowExceededError" in raw or "context_length_exceeded" in raw: st = "context_overflow"
    kind = ("infrastructure" if st in INFRASTRUCTURE else "behavioural" if st in BEHAVIOURAL else "integrity" if st in INTEGRITY else "unknown")
    return {"status": st, "harness_status": harness, "kind": kind, "final_gap_s": final_gap, "last_event_role": last_role,
            "api_calls": ms.get("api_calls"), "commands": commands}
