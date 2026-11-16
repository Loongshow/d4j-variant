"""Observable-only, spec-driven analysis of one project's CONTROL / five-hop TREATMENT runs (multi-project replication).
Reads bash commands, tool outputs, test executions and submitted rankings from mini-swe-agent.traj.json + run artifacts. Never reads
reasoning_content / reasoning_items. Usage: analyze_multiproject.py <spec.json> <runs_root (.../benchmark_runs/<agent>)> <out_json> [--runs 1-5]"""
import json, os, re, sys, glob, statistics, argparse
ap = argparse.ArgumentParser(); ap.add_argument("spec"); ap.add_argument("runs_root"); ap.add_argument("out"); ap.add_argument("--runs", default="1-5"); a = ap.parse_args()
S = json.load(open(a.spec)); LO, HI = (int(x) for x in a.runs.split("-"))
CHAIN = [tuple(x) for x in S["chain"]]; ARMS = S["arms"]; CONTRACT = S["contract"]; OTHER = S["other"]; PAYLOAD_TOKENS = set(S["payload_tokens"]); NOVEL_WATCH = S["novel_watch"]; GOLD_NAMES = S["gold_name_tokens"]
def rj(p):
    try: return json.load(open(p))
    except Exception: return None
def strip_cd(c):
    c = c.strip()
    for _ in range(2):
        c = re.sub(r"""^cd\s+(?:'[^']*'|"[^"]*"|\S+)\s*(?:&&|;)\s*""", '', c)
        c = re.sub(r"""^ROOT=(?:'[^']*'|"[^"]*"|\S+)\s*;?\s*(?:cd\s+"?\$ROOT"?\s*(?:&&|;)\s*)?""", '', c)
    return c.replace('$ROOT/', '').replace('"$ROOT"/', '')
def is_search(c): return bool(re.search(r'\b(rg|grep|find|fd|ag)\b', c))
def is_repo_wide(c): return bool(re.search(r'\bgrep\b[^|;]*\s-[a-zA-Z]*[rR]', c)) or bool(re.search(r'\brg\b', c))
def is_test(c): return "defects4j test" in c
def opened_files(c): return re.findall(r'(?:cat|less|more|head|tail|nl|sed -n \S+|awk)\b[^|;&]*?([A-Za-z0-9_/.-]+\.java)', c)
def steps_from(traj):
    msgs = traj.get("messages", []); outs = {m.get("tool_call_id"): (m.get("content") or "") for m in msgs if m.get("role") == "tool"}; steps = []; submit = None
    for m in msgs:
        if m.get("role") != "assistant": continue
        for tc in m.get("tool_calls") or []:
            fn = tc.get("function") or {}; name = fn.get("name"); args = fn.get("arguments")
            try: args = json.loads(args) if isinstance(args, str) else (args or {})
            except Exception: args = {}
            if name == "bash": steps.append({"idx": len(steps) + 1, "command": strip_cd(args.get("command", "")), "output": outs.get(tc.get("id"), "")})
            elif name == "submit_fault_localization": submit = {"idx": len(steps) + 1, "predictions": args.get("predictions"), "evidence_chain": args.get("evidence_chain")}
    return steps, submit, msgs
def first_out(steps, needle): return next((s["idx"] for s in steps if needle in s["output"]), None)
def first_cmd(steps, pred): return next((s["idx"] for s in steps if pred(s["command"])), None)
def analyze(rdir, vid, spec):
    man = rj(os.path.join(rdir, "run_manifest.json")) or {}; ev = rj(os.path.join(rdir, "evaluation.json")) or {}; rk = rj(os.path.join(rdir, "ranking.json")) or {}; pr = rj(os.path.join(rdir, "prompt.json")) or {}; si = rj(os.path.join(rdir, "source_integrity.json")) or {}
    traj = rj(os.path.join(rdir, "mini-swe-agent.traj.json")) or {}; steps, submit, msgs = steps_from(traj); ms = (traj.get("info") or {}).get("model_stats") or {}
    preds = (rk.get("structured_submission") or {}).get("predictions") or rk.get("predictions") or (submit or {}).get("predictions") or []
    top = [f"{p.get('class')}::{p.get('method')}" for p in preds[:10]]; gold_key = f"{spec['gold_class']}::{spec['gold_method']}"; gold_rank = ev.get("gold_rank")
    if gold_rank is None and top: gold_rank = next((i + 1 for i, k in enumerate(top) if k == gold_key), None)
    cl = open(os.path.join(rdir, "commands.log")).read() if os.path.exists(os.path.join(rdir, "commands.log")) else ""; raw = open(os.path.join(rdir, "raw_agent_output.txt"), errors="replace").read() if os.path.exists(os.path.join(rdir, "raw_agent_output.txt")) else ""
    timing = {"execution_timer_started_at": (re.search(r"execution_timer_started_at: (\S+)", cl) or [None, None])[1], "duration_ms": int((re.search(r"duration_ms: (\d+)", cl) or [None, "0"])[1]) or None, "timed_out": "timed_out: true" in cl, "provider_retry_lines": raw.count("Retrying"), "provider_error_excerpt": (re.search(r"raised ([^\n]{0,160})", raw) or [None, None])[1],
              "blocked_on": ("model response" if (steps and msgs and msgs[-1].get("role") == "tool" and man.get("status") == "timeout") else ("n/a" if man.get("status") != "timeout" else "unclear"))}
    # provider request-stall observables (wall clock from the harness start stamp, per-response timestamps from the trajectory, end from evaluation.json mtime)
    from datetime import datetime as _dt
    _ts = [((x.get("extra") or {}).get("timestamp")) for x in msgs if x.get("role") == "assistant"]; _ts = [t for t in _ts if isinstance(t, (int, float))]
    try: _st_s = _dt.fromisoformat(man["started_at"].replace("Z", "+00:00")).timestamp() if man.get("started_at") else None
    except Exception: _st_s = None
    _evp = os.path.join(rdir, "evaluation.json"); _end = os.path.getmtime(_evp) if os.path.exists(_evp) else None
    _gaps = [round(b - a) for a, b in zip(_ts, _ts[1:])]
    timing.update({"response_count": len(_ts), "start_to_first_response_s": (round(_ts[0] - _st_s) if (_ts and _st_s) else None), "max_inter_response_gap_s": (max(_gaps) if _gaps else None),
                   "wall_clock_s": (round(_end - _st_s) if (_end and _st_s) else None), "response_span_s": (round(_ts[-1] - _ts[0]) if len(_ts) > 1 else None)})
    timing["stalled_request"] = bool(man.get("status") in ("timeout", "startup_timeout") or (timing["start_to_first_response_s"] or 0) > 60 or (timing["max_inter_response_gap_s"] or 0) > 60)
    timing["stall_kind"] = ("startup_timeout" if man.get("status") == "startup_timeout" else "unreturned request -> harness timeout" if man.get("status") == "timeout" else "stalled then recovered (completed)" if timing["stalled_request"] else "none")
    nodes = {}
    for tag, cls, meth, decl, call in CHAIN:
        d = first_out(steps, decl); c = first_out(steps, call) if call else None
        e = min([x for x in (d, c) if x] or [None]) if (d or c) else None
        cmd = next((s["command"] for s in steps if s["idx"] == e), "") if e else ""
        nodes[tag] = {"class": cls, "method": meth, "decl_first_shown": d, "call_to_next_first_shown": c, "first_exposed": e, "exposing_cmd": cmd[:200], "name_searched_first_at": first_cmd(steps, lambda x, m=meth: m in x and is_search(x)), "class_searched_or_opened_first_at": first_cmd(steps, lambda x, k=cls: k in x)}
    gold_decl = first_out(steps, spec["gold_decl"]); buggy = first_out(steps, spec["buggy"]); gold_step = min([x for x in (gold_decl, buggy) if x] or [None]) if (gold_decl or buggy) else None
    gold_cmd = next((s["command"] for s in steps if s["idx"] == gold_step), "") if gold_step else ""
    contract = {k: first_out(steps, v) for k, v in CONTRACT.items()}; other = {k: first_out(steps, v) for k, v in OTHER.items()}
    first_contract = min([v for v in contract.values() if v] or [None]) if any(contract.values()) else None
    contract_after_gold = sorted(k for k, v in contract.items() if v and gold_step and v > gold_step)
    post = [s for s in steps if gold_step and s["idx"] > gold_step]
    novel = []
    for s in steps:
        if not is_search(s["command"]): continue
        earlier = "\n".join(x["output"] for x in steps if x["idx"] < s["idx"]) + "\n" + "\n".join(x["command"] for x in steps if x["idx"] < s["idx"])
        for w in NOVEL_WATCH:
            if w in s["command"] and w not in earlier and w not in PAYLOAD_TOKENS: novel.append({"step": s["idx"], "token": w, "command": s["command"][:140]})
    cc = {}
    if spec["arm"] == "TREATMENT":
        exp = {t: nodes[t]["first_exposed"] for t in ("facade", "H1", "H2", "H3", "H4")}; exp["H5"] = gold_step
        reached = {t: exp[t] is not None for t in ("H1", "H2", "H3", "H4", "H5")}
        order = [exp[t] for t in ("facade", "H1", "H2", "H3", "H4", "H5")]
        sequential = all(order) and all(order[i] < order[i + 1] for i in range(len(order) - 1))
        via_chain = {}
        for i, t in enumerate(("H1", "H2", "H3", "H4", "H5")):
            prev = ("facade", "H1", "H2", "H3", "H4")[i]; m = nodes[t]["method"]; k = nodes[t]["class"]; e = exp[t]; pc = nodes[prev]["call_to_next_first_shown"]; cmd = nodes[t]["exposing_cmd"] if t != "H5" else gold_cmd
            via_chain[t] = bool(e and pc and pc <= e and (m in cmd or k in cmd))
        skipped = [t for t in ("H1", "H2", "H3", "H4") if gold_step and (exp[t] is None or exp[t] > gold_step)]
        gold_by_name = bool(gold_step and any(g in gold_cmd for g in GOLD_NAMES))
        h4_call_seen_before_gold = bool(nodes["H4"]["call_to_next_first_shown"] and gold_step and nodes["H4"]["call_to_next_first_shown"] <= gold_step)
        lexical_bypass = bool(gold_step and is_search(gold_cmd) and not gold_by_name)
        repo_wide_shortcut = bool(gold_step and is_repo_wide(gold_cmd) and not h4_call_seen_before_gold)
        direct_gold_search = bool(gold_step and gold_by_name and not h4_call_seen_before_gold)
        last_reached = max([i + 1 for i, t in enumerate(("H1", "H2", "H3", "H4", "H5")) if reached[t]] or [0])
        abandoned = bool(man.get("status") == "completed" and gold_step is None); timeout_before_gold = bool(man.get("status") == "timeout" and gold_step is None)
        path = " -> ".join([f"facade({exp['facade']})"] + [f"{t}({exp[t]})" if exp[t] else f"{t}(-)" for t in ("H1", "H2", "H3", "H4", "H5")] + [f"rank {gold_rank}" if gold_rank else ("timeout" if man.get("status") == "timeout" else "no gold in ranking")])
        if gold_step is None: route = "timeout before gold" if man.get("status") == "timeout" else (("n/a (no agent activity: %s)" % man.get("status")) if not steps else "abandoned chain (submitted without exposing the gold)")
        elif sequential and all(via_chain.values()): route = "A. explicit five-hop traversal (each hop found by name after the previous hop's call was shown)"
        elif not skipped and h4_call_seen_before_gold and gold_by_name: route = "A'. full traversal (all hops shown in order; some hop exposed by a non-name command)"
        elif not skipped and h4_call_seen_before_gold and lexical_bypass: route = "A''. full traversal; gold exposed by a name-free search issued after hop 4's call line was on screen"
        elif lexical_bypass or repo_wide_shortcut: route = "B/C. lexical or repository-wide shortcut to the gold (hop(s) skipped: %s)" % (",".join(skipped) or "none")
        elif direct_gold_search: route = "D. direct gold search before hop 4's call was shown"
        else: route = "E. other / unclear (skipped: %s)" % (",".join(skipped) or "none")
        inc = {}; prevstep = 0
        for t in ("H1", "H2", "H3", "H4", "H5"):
            inc[f"calls_to_{t}"] = (exp[t] - 1) if exp[t] else None; inc[f"incremental_to_{t}"] = (exp[t] - prevstep) if exp[t] else None; prevstep = exp[t] or prevstep
        cc = {"exposure_steps": exp, "reached": reached, "followed_all_five_sequentially": sequential and all(via_chain.values()), "sequential_order": sequential, "via_chain_per_hop": via_chain, "skipped_hops": skipped, "lexical_bypass": lexical_bypass, "repository_wide_shortcut": repo_wide_shortcut, "direct_gold_search": direct_gold_search, "abandoned_chain": abandoned, "timeout_before_gold": timeout_before_gold, "h4_call_step": nodes["H4"]["call_to_next_first_shown"], "buggy_line_shown_after_h4_call": bool(buggy and nodes["H4"]["call_to_next_first_shown"] and buggy > nodes["H4"]["call_to_next_first_shown"]), "last_hop_reached": last_reached, "gold_exposed_by_name": gold_by_name, "h4_call_seen_before_gold": h4_call_seen_before_gold, "chain_path": path, "route": route, "increments": inc}
    else:
        cc = {"chain_path": f"facade/gold({gold_step}) -> rank {gold_rank}", "route": "n/a (0-hop)", "exposure_steps": {"facade": gold_step}}
    exec_ev = [{"step": s["idx"], "kind": ("javap" if re.search(r"\bjavap\b", s["command"]) else "jshell" if re.search(r"\bjshell\b", s["command"]) else "script"), "after_gold": bool(gold_step and s["idx"] > gold_step), "command": s["command"][:160]} for s in steps if re.search(r"\bjavap\b|\bjshell\b", s["command"]) or (re.search(r"\bpython3?\b|\bperl\b|\bbc\b|\bnode\b", s["command"]) and re.search(r"sqrt|\*\s*[\w(]|/\s*[\w(]", re.sub(r"<<-?\s*'?\w+'?", " ", s["command"])))]
    info = {"tool_calls_to_first_gold": (gold_step - 1) if gold_step else None, "calls_after_first_gold": (len(steps) - gold_step) if gold_step else None, "external_contract_retrieval_count": sum(1 for v in contract.values() if v), "contract_markers_after_gold": contract_after_gold,
            "tests_executed": [s["command"][:110] for s in steps if is_test(s["command"])], "tests_executed_count": sum(1 for s in steps if is_test(s["command"])),
            "source_files_opened": sorted({os.path.basename(f) for s in steps for f in opened_files(s["command"])}), "unique_search_queries": len({s["command"] for s in steps if is_search(s["command"])}), "search_count": sum(1 for s in steps if is_search(s["command"])),
            "post_gold_searches": [s["command"][:110] for s in post if is_search(s["command"])], "post_gold_opens": [s["command"][:110] for s in post if opened_files(s["command"])], "javap_jshell_steps": [s["idx"] for s in steps if re.search(r'\bjshell\b|\bjavap\b', s["command"])], "execution_evidence": exec_ev,
            "build_properties_cmd": first_cmd(steps, lambda c: "defects4j.build.properties" in c or ".defects4j.config" in c or "classes.modified" in c), "recency_heuristic_cmd": first_cmd(steps, lambda c: bool(re.search(r"-newer|-mmin|-mtime|ls -lt", c))), "first_command": steps[0]["command"][:160] if steps else None, "first_search": next((s["command"][:160] for s in steps if is_search(s["command"])), None), "first_search_idx": first_cmd(steps, is_search), "first_action_is_test_run": bool(steps) and is_test(steps[0]["command"])}
    return {"run_id": "/".join(rdir.split("/")[-2:]), "variant_id": vid, "arm": spec["arm"], "gold": gold_key, "status": man.get("status"), "status_reason": man.get("status_reason"), "timing": timing,
            "gold_rank": gold_rank, "hit_at_1": gold_rank == 1, "hit_at_3": bool(gold_rank and gold_rank <= 3), "hit_at_5": bool(gold_rank and gold_rank <= 5), "hit_at_10": bool(gold_rank and gold_rank <= 10), "reciprocal_rank": (1.0 / gold_rank) if gold_rank else 0.0,
            "top10": top, "tool_call_count": (man.get("metrics") or {}).get("tool_call_count") or len(steps), "api_calls": ms.get("api_calls"), "cost_usd": ms.get("instance_cost"), "source_integrity_ok": si.get("ok"), "prompt_version": pr.get("version"), "base_prompt_sha256": pr.get("base_prompt_sha256"),
            "nodes": nodes, "gold_first_exposed_step": gold_step, "gold_exposing_cmd": gold_cmd[:200], "buggy_line_first_shown": buggy, "gold_decl_first_shown": gold_decl, "contract_first_shown": contract, "first_contract_step": first_contract, "other_markers": other,
            "chain": cc, "info_distance": info, "novel_search_vocabulary": novel, "total_bash_steps": len(steps), "steps": [{"idx": s["idx"], "command": s["command"][:300], "output_head": s["output"][:120].replace("\n", " | ")} for s in steps],
            "agent_reported_evidence_chain_unverified": (submit or {}).get("evidence_chain"), "hidden_reasoning_read": False}
runs = []
for vid, spec in ARMS.items():
    for rdir in sorted(glob.glob(os.path.join(a.runs_root, vid, "run-*"))):
        if LO <= int(os.path.basename(rdir).split("-")[-1]) <= HI: runs.append(analyze(rdir, vid, spec))
def mm(xs): xs = [x for x in xs if x is not None]; return [round(statistics.mean(xs), 2), statistics.median(xs)] if xs else [None, None]
def agg(rs):
    comp = [r for r in rs if r["status"] == "completed"]; T = bool(rs) and rs[0]["arm"] == "TREATMENT"
    rate = lambda k: (sum(1 for r in comp if r[k]) / len(comp)) if comp else None; rate_all = lambda k: (sum(1 for r in rs if r[k]) / len(rs)) if rs else None
    out = {"n": len(rs), "completed": len(comp), "timeout": sum(1 for r in rs if r["status"] == "timeout"), "other_status": [(r["run_id"], r["status"]) for r in rs if r["status"] not in ("completed", "timeout")],
           "acc_at_1": rate("hit_at_1"), "acc_at_3": rate("hit_at_3"), "acc_at_5": rate("hit_at_5"), "acc_at_10": rate("hit_at_10"), "mrr": (sum(r["reciprocal_rank"] for r in comp) / len(comp)) if comp else None,
           "acc_at_1_all_runs": rate_all("hit_at_1"), "mrr_all_runs": (sum(r["reciprocal_rank"] for r in rs) / len(rs)) if rs else None, "gold_ranks": [r["gold_rank"] for r in rs], "tool_calls": [r["tool_call_count"] for r in rs], "tool_calls_mean_median": mm([r["tool_call_count"] for r in rs]), "api_calls": [r["api_calls"] for r in rs], "api_calls_mean_median": mm([r["api_calls"] for r in rs]),
           "first_gold_step": [r["gold_first_exposed_step"] for r in rs], "first_gold_step_mean_median": mm([r["gold_first_exposed_step"] for r in rs]), "buggy_line_step": [r["buggy_line_first_shown"] for r in rs], "calls_to_first_gold": [r["info_distance"]["tool_calls_to_first_gold"] for r in rs], "calls_after_gold": [r["info_distance"]["calls_after_first_gold"] for r in rs], "calls_after_gold_mean_median": mm([r["info_distance"]["calls_after_first_gold"] for r in rs]),
           "costs": [r["cost_usd"] for r in rs], "total_cost_usd": sum(r["cost_usd"] or 0 for r in rs), "contract_retrieval_count": [r["info_distance"]["external_contract_retrieval_count"] for r in rs], "runs_with_contract_evidence_before_rank": sum(1 for r in rs if r["first_contract_step"]), "runs_with_new_contract_evidence_after_gold": sum(1 for r in rs if r["info_distance"]["contract_markers_after_gold"]),
           "tests_executed": [r["info_distance"]["tests_executed_count"] for r in rs], "source_files_opened": [len(r["info_distance"]["source_files_opened"]) for r in rs], "unique_search_queries": [r["info_distance"]["unique_search_queries"] for r in rs], "novel_vocab_events": sum(len(r["novel_search_vocabulary"]) for r in rs), "runs_with_novel_vocab": sum(1 for r in rs if r["novel_search_vocabulary"]),
           "build_properties_observably_used": sum(1 for r in rs if r["info_distance"]["build_properties_cmd"] or r["other_markers"]["d4j_modified_class_output"]), "recency_heuristic_runs": sum(1 for r in rs if r["info_distance"]["recency_heuristic_cmd"]), "javap_jshell_used": sum(1 for r in rs if r["info_distance"]["javap_jshell_steps"]), "gold_executed_or_emulated_after_exposure": sum(1 for r in rs if any(e["after_gold"] for e in r["info_distance"]["execution_evidence"])),
           "source_integrity_ok_all": all(r["source_integrity_ok"] for r in rs) if rs else None, "provider_retry_lines_total": sum(r["timing"]["provider_retry_lines"] for r in rs), "durations_s": [round((r["timing"]["duration_ms"] or 0) / 1000) for r in rs], "wall_clock_s": [r["timing"].get("wall_clock_s") for r in rs], "start_to_first_response_s": [r["timing"].get("start_to_first_response_s") for r in rs], "max_inter_response_gap_s": [r["timing"].get("max_inter_response_gap_s") for r in rs], "stalled_request_runs": sum(1 for r in rs if r["timing"].get("stalled_request")), "stall_kinds": [r["timing"].get("stall_kind") for r in rs], "startup_timeout": sum(1 for r in rs if r["status"] == "startup_timeout"), "facade_rank": [next((i + 1 for i, k in enumerate(r["top10"]) if k.endswith("::" + CHAIN[0][2])), None) for r in rs]}
    if T:
        out.update({"routes": {t: sum(1 for r in rs if r["chain"]["route"] == t) for t in sorted({r["chain"]["route"] for r in rs})}, "full_five_hop_traversal_rate": sum(1 for r in rs if r["chain"].get("followed_all_five_sequentially")) / len(rs), "all_hops_shown_in_order_rate": sum(1 for r in rs if r["chain"].get("sequential_order")) / len(rs),
                    "lexical_bypass_rate": sum(1 for r in rs if r["chain"].get("lexical_bypass")) / len(rs), "repository_wide_shortcut_rate": sum(1 for r in rs if r["chain"].get("repository_wide_shortcut")) / len(rs), "direct_gold_search_rate": sum(1 for r in rs if r["chain"].get("direct_gold_search")) / len(rs),
                    "abandoned_chain": sum(1 for r in rs if r["chain"].get("abandoned_chain")), "timeout_before_gold": sum(1 for r in rs if r["chain"].get("timeout_before_gold")), "reached_per_hop": {t: sum(1 for r in rs if r["chain"]["reached"].get(t)) for t in ("H1", "H2", "H3", "H4", "H5")}, "skipped_hops": [r["chain"]["skipped_hops"] for r in rs],
                    "hop_exposure_steps": {t: [r["chain"]["exposure_steps"].get(t) for r in rs] for t in ("facade", "H1", "H2", "H3", "H4", "H5")}, "hop_exposure_mean": {t: mm([r["chain"]["exposure_steps"].get(t) for r in rs]) for t in ("facade", "H1", "H2", "H3", "H4", "H5")},
                    "increments_mean": {k: mm([r["chain"]["increments"].get(k) for r in rs if r["chain"].get("increments")]) for k in ("incremental_to_H1", "incremental_to_H2", "incremental_to_H3", "incremental_to_H4", "incremental_to_H5")}, "ranked_facade_first": sum(1 for r in rs if r["top10"] and r["top10"][0].endswith("::" + CHAIN[0][2]))})
    act = [r for r in rs if (r["tool_call_count"] or 0) > 0]
    out.update({"runs_with_agent_activity": len(act), "tool_calls_mean_active": mm([r["tool_call_count"] for r in act])[0], "tool_calls_mean_completed": mm([r["tool_call_count"] for r in comp])[0], "api_calls_mean_active": mm([r["api_calls"] for r in act])[0], "first_gold_step_mean_completed": mm([r["gold_first_exposed_step"] for r in comp])[0], "cost_mean_active": mm([r["cost_usd"] for r in act])[0], "gold_reached_active": sum(1 for r in act if r["gold_first_exposed_step"])})
    if T and act: out.update({"full_five_hop_traversal_rate_active": sum(1 for r in act if r["chain"].get("followed_all_five_sequentially")) / len(act), "all_hops_shown_in_order_rate_active": sum(1 for r in act if r["chain"].get("sequential_order")) / len(act), "lexical_bypass_rate_active": sum(1 for r in act if r["chain"].get("lexical_bypass")) / len(act), "repository_wide_shortcut_rate_active": sum(1 for r in act if r["chain"].get("repository_wide_shortcut")) / len(act), "buggy_line_after_h4_call_runs": sum(1 for r in act if r["chain"].get("buggy_line_shown_after_h4_call"))})
    return out
out = {"schema_version": "multi-project-five-hop-results/v1", "project": S["project"], "label": S["label"], "run_range": a.runs, "interpretation_rule": "Not an L-level / reasoning-depth estimate and not a causal CONTROL-vs-TREATMENT effect; n=5 per arm; descriptive only; timeouts are reported separately and never treated as localization misses.",
       "per_arm": {"CONTROL": agg([r for r in runs if r["arm"] == "CONTROL"]), "TREATMENT": agg([r for r in runs if r["arm"] == "TREATMENT"])}, "total_recorded_cost_usd": sum(r["cost_usd"] or 0 for r in runs), "runs": runs}
json.dump(out, open(a.out, "w"), indent=1)
print(json.dumps({k: v for k, v in out.items() if k != "runs"}, indent=1))
for r in runs:
    print(f"\n### {r['run_id']} [{r['arm']}] status={r['status']} rank={r['gold_rank']} tc={r['tool_call_count']} api={r['api_calls']} cost={r['cost_usd']} dur={r['timing']['duration_ms']} retries={r['timing']['provider_retry_lines']}")
    print("  path:", r["chain"]["chain_path"], "|", r["chain"]["route"]); print("  gold at", r["gold_first_exposed_step"], "via:", r["gold_exposing_cmd"][:120]); print("  contract:", {k: v for k, v in r["contract_first_shown"].items() if v}, "| after gold:", r["info_distance"]["contract_markers_after_gold"]); print("  novel:", r["novel_search_vocabulary"][:4]); print("  top5:", [x.split(".")[-1] for x in r["top10"][:5]])
    for s in r["steps"]: print(f"   {s['idx']:>2}. {s['command'][:170]}")
