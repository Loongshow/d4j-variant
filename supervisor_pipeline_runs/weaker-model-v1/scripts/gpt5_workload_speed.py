"""Study 1 (revision after verification): separate MODEL-SIDE workload (calls, output and reasoning tokens; independent of serving speed)
from PROVIDER-SIDE serving speed (output tokens per second on long calls; latency of short calls), for all 27 valid gpt-5 runs.
Also produces the per-category time decomposition (previously computed inline) with categories assigned by a stated rule, and a
model-based counterfactual: each run's waits re-timed at the pre-window serving speed. Writes gpt5-timeouts/workload_speed.json,
time_decomposition.json, call_waits.json, malformed_commands.json, post_gold_reasoning.json (all previously inline; now reproducible)."""
import json, re, os, statistics as st, datetime
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); D = f"{ROOT}/gpt5-timeouts"
R = {r["run_id"]: r for r in json.load(open(f"{D}/timeline_runs.json"))}; S = json.load(open(f"{D}/timeline_steps.json"))
AG = f"{ROOT}/models/w50/benchmark_runs/mini-swe-agent-openai-gpt-5"
WINDOW_START = "2026-10-13T13:47:00Z"   # slot 13 onward (where 9 of the 10 timeouts fall)
BRACE = re.compile(r"['\"]\s*\}\s*$")
def cmds_of(rid):
    t = json.load(open(f"{AG}/{rid}/mini-swe-agent.traj.json")); msgs = t["messages"]; calls = {}
    for m in msgs:
        if m.get("role") == "assistant":
            for tc in m.get("tool_calls") or []:
                fn = tc.get("function") or {}
                try: a = json.loads(fn.get("arguments") or "{}")
                except Exception: a = {}
                calls[tc.get("id")] = (fn.get("name"), a.get("command", ""))
    out = []
    for m in msgs:
        if m.get("role") == "tool":
            name, cmd = calls.get(m.get("tool_call_id"), ("", "")); c = m.get("content") if isinstance(m.get("content"), str) else json.dumps(m.get("content"))
            out.append({"name": name, "cmd": cmd, "rc": (m.get("extra") or {}).get("returncode"), "java_fail": "Failed to parse Java version" in c, "test": "defects4j test" in cmd})
    return out
runs = {}; waits = []; malformed = {}; postgold = {}; decomp = {}
for rid, r in R.items():
    steps = S[rid]; tc = cmds_of(rid); window = r["start_utc"] >= WINDOW_START
    long_calls = [s for s in steps if s["latency"] and (s["completion_tokens"] or 0) >= 500 and "TEST" not in s["kinds"]]
    short_calls = [s for s in steps if s["latency"] and (s["completion_tokens"] or 0) < 100 and "TEST" not in s["kinds"]]
    speed = st.median([(s["completion_tokens"] or 0) / s["latency"] for s in long_calls]) if long_calls else None
    out_tok = sum(s["completion_tokens"] or 0 for s in steps if s["latency"] is not None) + (r["submit_call_completion_tokens"] or 0)
    reas_tok = sum(s["reasoning_tokens"] or 0 for s in steps if s["latency"] is not None) + (r["submit_call_reasoning_tokens"] or 0)
    g = next((s["k"] for s in steps if s["gold_cov"] > 0 or s["gold_sig"]), None)
    post = [s for s in steps if g is not None and s["k"] > g and s["latency"] is not None]
    # exclusive decomposition, categories checked in the stated order; plus non-exclusive totals so order effects are visible
    cats = {"malformed_command": 0.0, "test_or_build": 0.0, "slow_serving": 0.0, "deliberation": 0.0, "ordinary_steps": 0.0}
    nonexcl = {"malformed_any": 0.0, "slow_serving_any": 0.0, "deliberation_any": 0.0}
    for s, c in zip(steps, tc):
        w = s["latency"] or 0.0; mal = bool(BRACE.search(c["cmd"].strip())); slow = (s["completion_tokens"] or 0) < 300 and w >= 20 and "TEST" not in s["kinds"]; delib = (s["reasoning_tokens"] or 0) >= 1500
        nonexcl["malformed_any"] += w if mal else 0; nonexcl["slow_serving_any"] += w if slow else 0; nonexcl["deliberation_any"] += w if delib else 0
        if mal: cats["malformed_command"] += w
        elif "TEST" in s["kinds"]: cats["test_or_build"] += w
        elif slow: cats["slow_serving"] += w
        elif delib: cats["deliberation"] += w
        else: cats["ordinary_steps"] += w
        waits.append({"run_id": rid, "outcome": r["outcome"], "k": s["k"], "wait_s": s["latency"], "reasoning_tokens": s["reasoning_tokens"] or 0, "output_tokens": s["completion_tokens"] or 0,
                      "prompt_tokens": s["prompt_tokens"] or 0, "malformed": mal, "test": "TEST" in s["kinds"], "in_window": window})
    end = {"final_pending_request": r["final_gap_s"] if r["outcome"] == "TIMEOUT" else 0.0, "submission_call": r["submit_call_to_end_s"] or 0.0, "startup": steps[0]["created"] if steps else 0.0}
    decomp[rid] = {**{k: round(v, 1) for k, v in cats.items()}, **{k: round(v, 1) for k, v in nonexcl.items()}, **{k: round(v, 1) for k, v in end.items()},
                   "accounted_s": round(sum(cats.values()) + sum(end.values()), 1), "wall_s": r["wall_s"], "outcome": r["outcome"]}
    mal_n = sum(1 for c in tc if BRACE.search(c["cmd"].strip())); fail_n = sum(1 for c in tc if c["rc"] not in (0, None))
    malformed[rid] = {"outcome": r["outcome"], "brace_cmds": mal_n, "brace_cmds_failed": sum(1 for c in tc if BRACE.search(c["cmd"].strip()) and c["rc"] not in (0, None)),
                      "failed_cmds": fail_n, "brace_time_s": round(sum((s["latency"] or 0) for s, c in zip(steps, tc) if BRACE.search(c["cmd"].strip())), 1),
                      "test_calls": sum(1 for c in tc if c["test"]), "test_calls_java_fail": sum(1 for c in tc if c["test"] and c["java_fail"]),
                      "test_calls_login_shell": sum(1 for c in tc if c["test"] and re.match(r"^\s*bash\s+-l", c["cmd"].strip())), "steps": len(steps)}
    postgold[rid] = {"outcome": r["outcome"], "instance": r["instance_id"], "reached_gold": g is not None, "post_gold_reasoning": sum(s["reasoning_tokens"] or 0 for s in post),
                     "post_gold_output_tokens": sum(s["completion_tokens"] or 0 for s in post), "post_gold_delib_calls": sum(1 for s in post if (s["reasoning_tokens"] or 0) >= 1500),
                     "post_gold_calls": len(post), "post_gold_model_time": round(sum(s["latency"] for s in post if "TEST" not in s["kinds"]), 1)}
    # counterfactual: each non-test wait re-timed at pre-window speed (computed below), never longer than observed
    runs[rid] = {"outcome": r["outcome"], "instance": r["instance_id"], "recipe": r["recipe"], "start_utc": r["start_utc"], "slot": r["slot_index"], "in_window": window,
                 "tool_calls": r["tool_calls"], "output_tokens_total": out_tok, "reasoning_tokens_total": reas_tok, "speed_tok_s_long_calls": round(speed, 1) if speed else None,
                 "short_call_wait_median_s": round(st.median([s["latency"] for s in short_calls]), 1) if short_calls else None, "wall_s": r["wall_s"],
                 "submit_call_s": r["submit_call_to_end_s"], "submit_out_tokens": r["submit_call_completion_tokens"]}
pre = [v for v in runs.values() if not v["in_window"] and v["speed_tok_s_long_calls"]]
PRE_SPEED = st.median([v["speed_tok_s_long_calls"] for v in pre]); PRE_SHORT = st.median([v["short_call_wait_median_s"] for v in pre if v["short_call_wait_median_s"]])
SUBMIT_TOK = st.median([v["submit_out_tokens"] for v in runs.values() if v["submit_out_tokens"]])
for rid, v in runs.items():
    steps = S[rid]; t = steps[0]["created"] if steps else 0.0
    for s in steps:
        w = s["latency"] or 0.0
        if "TEST" in s["kinds"]: t += w; continue
        t += min(w, PRE_SHORT + (s["completion_tokens"] or 0) / PRE_SPEED)
    v["counterfactual_exploration_end_s"] = round(t, 1)
    v["counterfactual_with_submission_s"] = round(t + PRE_SHORT + SUBMIT_TOK / PRE_SPEED, 1) if v["outcome"] == "TIMEOUT" else None
json.dump({"window_start": WINDOW_START, "pre_window_speed_tok_s": PRE_SPEED, "pre_window_short_wait_s": PRE_SHORT, "median_submission_tokens": SUBMIT_TOK, "runs": runs},
          open(f"{D}/workload_speed.json", "w"), indent=1)
json.dump(decomp, open(f"{D}/time_decomposition.json", "w"), indent=1); json.dump(waits, open(f"{D}/call_waits.json", "w"), indent=1)
json.dump(malformed, open(f"{D}/malformed_commands.json", "w"), indent=1); json.dump(postgold, open(f"{D}/post_gold_reasoning.json", "w"), indent=1)
print("pre-window speed", PRE_SPEED, "tok/s; pre-window short wait", PRE_SHORT, "s; median submission tokens", SUBMIT_TOK)
