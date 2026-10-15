"""Study 1 (GPT-5 timeouts): per-run, per-step timeline of every gpt-5 (server w50) held-out run, from the recorded timestamps.
Reuses the FROZEN display-matching and command-classification code of scripts/mx_metrics.py verbatim (the function definitions are
executed from that file; nothing in it is changed) and adds timing: t0 = the harness execution timer start (commands.log); each tool
result carries extra.timestamp; each model request carries response.created (request time, 1 s resolution).
Per step k: latency_k = tool_ts_k - created_k (model response time + command execution); the final gap = t0 + duration - last
tool_ts (the model request pending at the kill, or a command still executing). Never opens raw_agent_output.txt, probe files or
credentials; never prints hidden reasoning (reasoning token COUNTS only).
Usage: gpt5_timeline.py  -> gpt5-timeouts/timeline_runs.json, timeline_steps.json, GPT5_TIMEOUT_TIMELINES.csv, GPT5_TIMEOUT_RUN_INDEX.csv
       gpt5_timeline.py --server w55 --tier STAGE_B --out stageB-gpt56/timeline_w55   (same measures for any server/tier; no CSVs)"""
import json, os, re, sys, glob, csv, datetime, statistics as st, subprocess
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
src = open(f"{HERE}/mx_metrics.py").read(); NS = {"__file__": f"{HERE}/mx_metrics.py"}
exec(compile(src[:src.index("rows, diag_rows = [], []")], "mx_metrics_frozen_defs", "exec"), NS)   # frozen helper definitions only
Shown, coverage, signature_shown, classify_command, tool_text, parse_line, norm, as_list, rj, substantive, file_lines = (NS[k] for k in
    ("Shown", "coverage", "signature_shown", "classify_command", "tool_text", "parse_line", "norm", "as_list", "rj", "substantive", "file_lines"))
KEY = NS["KEY"]; S = NS["S"]
A = sys.argv; SERVER = A[A.index("--server") + 1] if "--server" in A else "w50"; TIER = A[A.index("--tier") + 1] if "--tier" in A else None
OUT = f"{ROOT}/" + (A[A.index("--out") + 1] if "--out" in A else "gpt5-timeouts"); DEFAULT = "--out" not in A
os.makedirs(OUT if DEFAULT else os.path.dirname(OUT), exist_ok=True)
AG = f"{ROOT}/models/{SERVER}/benchmark_runs/" + json.load(open(f"{ROOT}/models/servers.json"))[SERVER]["agent_id"]
PR = {(r["variant_id"], r["run"]): r for r in json.load(open(f"{ROOT}/analysis/per_run.json")) if r.get("server") == SERVER and (TIER is None or r.get("tier") == TIER)}
LED = {r["run"]: r for r in (json.loads(l) for l in open(f"{ROOT}/diagnostic/block_{SERVER}.jsonl") if l.strip())}
iso = lambda s: datetime.datetime.fromisoformat(s.replace("Z", "+00:00")).timestamp()
# health probes and launches from the driver log
LOG = [l.rstrip("\n") for l in open(f"{ROOT}/diagnostic/driver_{SERVER}.log")] if os.path.exists(f"{ROOT}/diagnostic/driver_{SERVER}.log") else []
def probes_before(V, run_name):
    """Wall times of the passing probes in the gate immediately before this run's launch, and the launch time."""
    rec = LED.get(f"{V}/{run_name}") or {}; slot, att = rec.get("slot_index"), rec.get("attempt")
    idx = [i for i, l in enumerate(LOG) if f"-> {V} (attempt {att})" in l and f"launch slot {slot} " in l]
    if not idx: return None, []
    i = idx[-1]; walls = []
    j = i - 1
    while j >= 0 and "gate:" not in LOG[j]:
        m = re.search(r"probe: http=(\d+) status=(\w+) wall=([\d.]+)s", LOG[j])
        if m: walls.append((m.group(2), float(m.group(3))))
        j -= 1
    t = re.match(r"\[(\S+)\]", LOG[i]).group(1); return iso(t), list(reversed(walls))
# macOS power log: sleep / wake events (local time with offset)
try: PM = subprocess.run(["pmset", "-g", "log"], capture_output=True, text=True, timeout=120).stdout.split("\n")
except Exception: PM = []
SLEEPEV = []
for l in PM:
    m = re.match(r"^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) ([+-]\d{4}) (Sleep|DarkWake|Wake)\b", l)
    if m: SLEEPEV.append((datetime.datetime.strptime(m.group(1) + " " + m.group(2), "%Y-%m-%d %H:%M:%S %z").timestamp(), m.group(3)))
def sleep_events(a, b): return [(round(t - a, 1), k) for t, k in SLEEPEV if a - 1 <= t <= b + 1]
def catalog(rd):
    return [e for e in rj(f"{rd}/method_catalog.json").get("methods", []) if e.get("file")]
rows, steps_all = [], {}
for rd in sorted(glob.glob(f"{AG}/CTV-*/run-*")):
    V = os.path.basename(os.path.dirname(rd)); run = os.path.basename(rd); pr = PR.get((V, run)); K = KEY.get(V)
    if not pr or not K or not pr.get("included"): continue                     # valid behavioural runs only (27)
    log = open(f"{rd}/commands.log").read()
    t0 = iso(re.search(r"execution_timer_started_at: (\S+)", log).group(1)); dur = int(re.search(r"duration_ms: (\d+)", log).group(1)) / 1000
    traj = rj(f"{rd}/mini-swe-agent.traj.json"); msgs = traj.get("messages", [])
    golds = as_list(K["gold"]); decoys = as_list(K.get("decoys")); entries = as_list(K.get("entry_points")); evid = [e for e in as_list(K.get("evidence")) if "::" in e]
    trig = K.get("trigger", ""); faults = [norm(f) for f in as_list(K.get("fault_lines")) if norm(f)]; sig = norm(K.get("expected_signature") or "")
    cat = catalog(rd); bybase = {}
    for e in cat: bybase.setdefault(os.path.basename(e["file"]), []).append(e)
    shown = Shown(); outs = []; steps = []; pending = {}; cur = None; seen_cmds = []; seen_files = set(); method_first = {}
    for m in msgs:
        if m.get("role") == "assistant":
            r = (m.get("extra") or {}).get("response") or {}; u = r.get("usage") or {}
            cur = {"created": (r.get("created") or 0) - t0, "prompt_tokens": u.get("prompt_tokens"), "completion_tokens": u.get("completion_tokens"),
                   "reasoning_tokens": (u.get("completion_tokens_details") or {}).get("reasoning_tokens"), "visible_chars": len(m.get("content") or ""), "first_tool": True}
            for tc in m.get("tool_calls") or []:
                fn = tc.get("function") or {}
                try: args = json.loads(fn.get("arguments") or "{}")
                except Exception: args = {}
                cmd = args.get("command", "") if fn.get("name") == "bash" else f"<{fn.get('name')}>"
                kinds = sorted({k for k, _ in classify_command(cmd, trig)}) if fn.get("name") == "bash" else ["SUBMIT"]
                files = {os.path.basename(x) for x in re.findall(r"[\w./-]+\.(?:java|xml|txt|properties)", cmd)}
                pending[tc.get("id")] = (cmd, kinds, files, cur)
        elif m.get("role") == "tool":
            cmd, kinds, files, req = pending.get(m.get("tool_call_id"), ("", [], set(), cur or {}))
            ts = ((m.get("extra") or {}).get("timestamp") or t0) - t0
            txt = tool_text(m.get("content")); outs.append(txt); shown.add_output(txt, files)
            shown_text = norm(" ".join(parse_line(l)[2] for l in "\n".join(outs).replace("\r", "").split("\n")))
            ncmd = norm(cmd); repeat = ncmd in seen_cmds; seen_cmds.append(ncmd)
            revisit = ("READ" in kinds) and bool(files) and files <= seen_files
            out_bases = {os.path.basename(p) for p in re.findall(r"([\w./-]+\.java)[:-]\d", txt)} | files
            seen_files |= files
            # methods newly inspected at this step (catalog spans in files touched, coverage >= 0.3)
            for b in out_bases:
                for e in bybase.get(b, []):
                    kk = f"{e['class']}::{e['method']}"
                    if kk in method_first: continue
                    L = file_lines(rd, V, e["file"])
                    if not L: continue
                    idx = [i for i in range(e["line_start"], e["line_end"] + 1) if 0 < i <= len(L) and substantive(L[i - 1])]
                    if idx and sum(1 for i in idx if shown.displayed(L, e["file"], i)) / len(idx) >= 0.3: method_first[kk] = len(steps)
            st_ = {"k": len(steps), "created": round(req.get("created", 0), 1), "ts": round(ts, 1), "latency": round(ts - req.get("created", 0), 1) if req.get("first_tool", True) else None,
                   "kinds": kinds, "repeat_cmd": repeat, "revisit_read": revisit, "prompt_tokens": req.get("prompt_tokens"), "completion_tokens": req.get("completion_tokens"),
                   "reasoning_tokens": req.get("reasoning_tokens"), "out_chars": len(txt),
                   "gold_cov": max([coverage(rd, V, g, shown) for g in golds] or [0]), "gold_sig": any(signature_shown(rd, V, g, shown) for g in golds),
                   "fault_line": any(f in shown_text for f in faults), "decoy_sig": any(signature_shown(rd, V, d, shown) for d in decoys),
                   "entry_cov": max([coverage(rd, V, e, shown) for e in entries] or [0]), "evid_cov": max([coverage(rd, V, e, shown) for e in evid] or [0]),
                   "failure_values": bool(sig) and sig in shown_text}
            if req: req["first_tool"] = False
            steps.append(st_)
    # a final assistant request with no tool output: the submission call of a completed run (or a call the kill interrupted)
    last_asst = next((mm for mm in reversed(msgs) if mm.get("role") in ("assistant", "tool")), None)
    submit_call = None
    if last_asst is not None and last_asst.get("role") == "assistant":
        r = (last_asst.get("extra") or {}).get("response") or {}; u = r.get("usage") or {}
        names = [((tc.get("function") or {}).get("name")) for tc in (last_asst.get("tool_calls") or [])]
        submit_call = {"created": round((r.get("created") or 0) - t0, 1), "duration_to_end_s": round(dur - ((r.get("created") or 0) - t0), 1),
                       "completion_tokens": u.get("completion_tokens"), "reasoning_tokens": (u.get("completion_tokens_details") or {}).get("reasoning_tokens"),
                       "tool_names": names}
    def first(pred):
        for s in steps:
            if pred(s): return s
        return None
    def t_of(s): return s["ts"] if s else None
    g_any = first(lambda s: s["gold_cov"] > 0 or s["gold_sig"]); g_mean = first(lambda s: s["gold_cov"] >= 0.5); g_full = first(lambda s: s["gold_cov"] >= 0.9)
    fl = first(lambda s: s["fault_line"]); dec = first(lambda s: s["decoy_sig"]); ev = first(lambda s: s["evid_cov"] >= 0.5); fv = first(lambda s: s["failure_values"])
    test1 = first(lambda s: "TEST" in s["kinds"])
    anchor = g_any["k"] if g_any else None
    after = [s for s in steps if anchor is not None and s["k"] > anchor]; after_fl = [s for s in steps if fl and s["k"] > fl["k"]]
    decisive = [x for x in (fl, ev) if x]; dk = max(x["k"] for x in decisive) if len(decisive) == 2 else (fl["k"] if fl and not evid else None)
    after_dec = [s for s in steps if dk is not None and s["k"] > dk]
    lat = [s["latency"] for s in steps if s["latency"] is not None and "TEST" not in s["kinds"]]
    lat_test = [s["latency"] for s in steps if s["latency"] is not None and "TEST" in s["kinds"]]
    last_ts = steps[-1]["ts"] if steps else 0.0; final_gap = round(dur - last_ts, 1)
    last_role = next((mm.get("role") for mm in reversed(msgs) if mm.get("role") in ("assistant", "tool")), None)
    timeout = pr["status"] == "timeout"
    gold_key = golds[0]; others_after = sorted(k for k, s0 in method_first.items() if anchor is not None and s0 > anchor and k not in golds)
    declared = set(decoys) | set(entries) | set(evid)
    launch_t, probe_walls = probes_before(V, run)
    man = rj(f"{rd}/run_manifest.json"); si = rj(f"{rd}/source_integrity.json")
    reas = [s["reasoning_tokens"] for s in steps if s["reasoning_tokens"] is not None and s["latency"] is not None]
    comp = [s["completion_tokens"] for s in steps if s["completion_tokens"] is not None and s["latency"] is not None]
    row = {"run_id": f"{V}/{run}", "variant_id": V, "run": run, "instance_id": K["instance_id"], "recipe": K["instance_id"].split("-")[1], "project": K.get("project"),
           "outcome": "TIMEOUT" if timeout else ("CORRECT" if pr.get("acc1") else "WRONG"), "gold_rank": pr.get("gold_rank"), "rank1": pr.get("rank1"),
           "start_utc": datetime.datetime.fromtimestamp(t0, datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
           "end_utc": datetime.datetime.fromtimestamp(t0 + dur, datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "wall_s": dur,
           "model_calls": pr.get("model_calls"), "tool_calls": len(steps) + (1 if submit_call else 0), "tool_outputs": len(steps),
           "submit_call_created_s": submit_call["created"] if submit_call else None, "submit_call_to_end_s": submit_call["duration_to_end_s"] if submit_call else None,
           "submit_call_completion_tokens": submit_call["completion_tokens"] if submit_call else None, "submit_call_reasoning_tokens": submit_call["reasoning_tokens"] if submit_call else None,
           "commitment_delay_s": round(submit_call["created"] - fl["ts"], 1) if (submit_call and fl) else None,
           "calls_fault_line_to_submit": len(after_fl) if submit_call else None,
           "t_first_test": t_of(test1), "t_gold_any": t_of(g_any), "t_gold_meaningful": t_of(g_mean), "t_gold_full": t_of(g_full), "t_fault_line": t_of(fl),
           "t_decoy": t_of(dec), "t_evidence": t_of(ev), "t_failure_values": t_of(fv),
           "calls_before_gold": (anchor + 1) if anchor is not None else len(steps), "calls_after_gold": len(after),
           "searches_after_gold": sum(1 for s in after if "SEARCH" in s["kinds"]), "reads_after_gold": sum(1 for s in after if "READ" in s["kinds"]),
           "tests_after_gold": sum(1 for s in after if "TEST" in s["kinds"]), "probes_after_gold": sum(1 for s in after if "PROBE" in s["kinds"]),
           "calls_after_fault_line": len(after_fl), "calls_after_decisive": len(after_dec) if dk is not None else None,
           "tests_after_decisive": sum(1 for s in after_dec if "TEST" in s["kinds"] or "PROBE" in s["kinds"]) if dk is not None else None,
           "time_after_gold_s": round(dur - g_any["ts"], 1) if g_any else None, "time_after_fault_line_s": round(dur - fl["ts"], 1) if fl else None,
           "time_after_decisive_s": round(dur - steps[dk]["ts"], 1) if dk is not None else None,
           "revisit_reads": sum(1 for s in steps if s["revisit_read"]), "repeated_cmds": sum(1 for s in steps if s["repeat_cmd"]),
           "repeated_searches": sum(1 for s in steps if s["repeat_cmd"] and "SEARCH" in s["kinds"]),
           "revisit_reads_after_gold": sum(1 for s in after if s["revisit_read"]),
           "methods_inspected_total": len(method_first), "methods_inspected_after_gold": len(others_after),
           "declared_alternatives_after_gold": len([k for k in others_after if k in declared]),
           "latency_median_s": round(st.median(lat), 1) if lat else None, "latency_mean_s": round(st.mean(lat), 1) if lat else None, "latency_max_s": max(lat) if lat else None,
           "model_time_s": round(sum(lat) + (final_gap if last_role == "tool" else 0), 1), "test_step_time_s": round(sum(lat_test), 1),
           "reasoning_tokens_total": sum(reas), "reasoning_tokens_median": st.median(reas) if reas else None, "completion_tokens_total": sum(comp),
           "seconds_per_1k_completion_tokens": round(sum(lat) / (sum(comp) / 1000), 1) if comp and sum(comp) else None,
           "final_prompt_tokens": next((s["prompt_tokens"] for s in reversed(steps) if s["prompt_tokens"]), None),
           "final_gap_s": final_gap, "last_event_role": last_role, "last_step_kinds": "+".join(steps[-1]["kinds"]) if steps else None,
           "last_step_ts": last_ts, "submitted": not timeout,
           "launch_probe_walls_s": [w for s_, w in probe_walls], "probe_wall_median_s": round(st.median([w for s_, w in probe_walls]), 1) if probe_walls else None,
           "sleep_events_in_run": sleep_events(t0, t0 + dur), "source_integrity_ok": (LED.get(f"{V}/{run}") or {}).get("source_integrity_ok"),
           "workspace_isolation_ok": (LED.get(f"{V}/{run}") or {}).get("workspace_isolation_ok"), "ledger_verdict": (LED.get(f"{V}/{run}") or {}).get("verdict"),
           "classified_status": (LED.get(f"{V}/{run}") or {}).get("classified_status"), "ledger_final_gap_s": (LED.get(f"{V}/{run}") or {}).get("final_gap_s"),
           "slot_index": (LED.get(f"{V}/{run}") or {}).get("slot_index"), "attempt": (LED.get(f"{V}/{run}") or {}).get("attempt"),
           "frozen_gold_exposed": pr.get("gold_exposed"), "frozen_full_gold_read": pr.get("full_gold_read"), "frozen_evidence_displayed": pr.get("evidence_displayed"),
           "frozen_tests_executed": pr.get("tests_executed"), "cost_usd": pr.get("cost_usd")}
    inv = {}
    for kk, s0 in method_first.items(): inv.setdefault(s0, []).append(kk.split(".")[-1])
    for s_ in steps: s_["new_methods"] = sorted(inv.get(s_["k"], []))
    rows.append(row); steps_all[row["run_id"]] = steps
if not DEFAULT:
    json.dump(rows, open(f"{OUT}_runs.json", "w"), indent=1); json.dump(steps_all, open(f"{OUT}_steps.json", "w")); print(len(rows), "runs ->", OUT); sys.exit(0)
json.dump(rows, open(f"{OUT}/timeline_runs.json", "w"), indent=1); json.dump(steps_all, open(f"{OUT}/timeline_steps.json", "w"))
cols = [k for k in rows[0] if k not in ("launch_probe_walls_s", "sleep_events_in_run")]
with open(f"{OUT}/GPT5_TIMEOUT_TIMELINES.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=cols + ["n_sleep_events_in_run"]); w.writeheader()
    for r in sorted(rows, key=lambda r: (r["instance_id"], r["outcome"] != "TIMEOUT", r["run"])):
        w.writerow({**{k: r[k] for k in cols}, "n_sleep_events_in_run": len(r["sleep_events_in_run"])})
idx_cols = ["run_id", "instance_id", "recipe", "project", "slot_index", "attempt", "start_utc", "end_utc", "wall_s", "ledger_verdict", "classified_status",
            "ledger_final_gap_s", "source_integrity_ok", "workspace_isolation_ok", "probe_wall_median_s", "n_sleep_events_in_run", "machine_sleep_ruled_out"]
with open(f"{OUT}/GPT5_TIMEOUT_RUN_INDEX.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=idx_cols); w.writeheader()
    for r in sorted([r for r in rows if r["outcome"] == "TIMEOUT"], key=lambda r: r["slot_index"]):
        w.writerow({**{k: r.get(k) for k in idx_cols if k not in ("n_sleep_events_in_run", "machine_sleep_ruled_out")}, "n_sleep_events_in_run": len(r["sleep_events_in_run"]),
                    "machine_sleep_ruled_out": (len(r["sleep_events_in_run"]) == 0 and abs(r["wall_s"] - 300) < 2)})
print(len(rows), "valid runs;", sum(1 for r in rows if r["outcome"] == "TIMEOUT"), "timeouts; pmset events parsed:", len(SLEEPEV))
