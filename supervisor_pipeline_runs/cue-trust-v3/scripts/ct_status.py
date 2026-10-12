"""Uniform run-status classification for cue-trust-v3, shared by ct_driver.py (replacement decisions) and ct_metrics.py (analysis).
It applies the existing uniform provider-failure rule from adversarial-break-v1 (diagnostic/PROVIDER_STALL_RULE.md, rules 1-3) unchanged:
  rule 1  harness `timeout` with <= 2 model calls and <= 2 executed commands                    -> provider_stall
  rule 2  harness `timeout`, last recorded event is a tool result, > 60 s left before the kill   -> provider_stall
  rule 3  provider failure caused by an oversized request (context window)                     -> context_overflow
Amendment A2 (pre-run correction, readiness review): the harness labels a non-answer `invalid_ranking` or `agent_protocol_error`,
and labels ANY run `provider_error` when its raw output merely contains "litellm." (e.g. a retry that later recovered). The agent's
own recorded exit reason decides: if mini-swe-agent's loop ended for an agent reason (AGENT_END: Submitted, LimitsExceeded,
TimeExceeded, RepeatedFormatError) and no valid ranking exists, the run is `no_answer` (behavioural, scored NO_ANSWER), whatever the
harness label. A harness `provider_error` whose agent exit is a provider exception stays infrastructure (rule 3 aside).
A3: a harness `failed` run with no model call (setup error, e.g. catalog timeout) is `setup_failure` (infrastructure).
Kinds: INFRASTRUCTURE (excluded; one replacement per slot), BEHAVIOURAL (counted, never re-run), INTEGRITY (`protocol_violation`:
source changed; excluded, driver halts), anything else UNKNOWN (driver halts for review)."""
import json, re, datetime
INFRASTRUCTURE = {"provider_error", "provider_stall", "startup_timeout", "agent_not_installed", "provider_not_configured", "setup_failure"}
BEHAVIOURAL = {"completed", "timeout", "context_overflow", "no_answer"}
INTEGRITY = {"protocol_violation"}
AGENT_END = {"Submitted", "LimitsExceeded", "TimeExceeded", "RepeatedFormatError"}
CONTEXT = re.compile(r"prompt is too long|ContextWindowExceededError|context_length_exceeded")
def _rj(p):
    try: return json.load(open(p))
    except Exception: return {}
def exit_status(traj):
    s = (traj.get("info") or {}).get("exit_status")
    if s: return s
    ex = [m for m in traj.get("messages") or [] if m.get("role") == "exit"]
    return ((ex[-1].get("extra") or {}).get("exit_status") if ex else "") or ""
def classify(rd, budget_seconds=300):
    man = _rj(f"{rd}/run_manifest.json"); traj = _rj(f"{rd}/mini-swe-agent.traj.json")
    harness = man.get("status"); st = harness; final_gap = last_role = None
    msgs = traj.get("messages") or []; ms = ((traj.get("info") or {}).get("model_stats") or {}); xs = exit_status(traj)
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
    if st == "failed" and not (ms.get("api_calls") or 0) and not any(m.get("role") == "assistant" for m in msgs):
        st = "setup_failure"   # A3: harness setup error before any model call (start-up failure, infrastructure)
    if st in ("invalid_ranking", "agent_protocol_error", "provider_error") and xs in AGENT_END:
        st = "no_answer"
    if st == "provider_error":
        try: raw = open(f"{rd}/raw_agent_output.txt", errors="replace").read()
        except Exception: raw = ""
        if CONTEXT.search(raw) or CONTEXT.search(xs or ""): st = "context_overflow"
    kind = ("infrastructure" if st in INFRASTRUCTURE else "behavioural" if st in BEHAVIOURAL else "integrity" if st in INTEGRITY else "unknown")
    return {"status": st, "harness_status": harness, "kind": kind, "final_gap_s": final_gap, "last_event_role": last_role,
            "agent_exit_status": xs, "api_calls": ms.get("api_calls"), "commands": commands}
