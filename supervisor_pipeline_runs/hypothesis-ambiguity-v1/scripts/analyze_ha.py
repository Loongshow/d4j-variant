"""Observable-only trajectory analysis for the hypothesis-ambiguity runs (Phase: TRAJECTORY ANALYSIS / DISCOVERY VS DISCRIMINATION / HYPOTHESIS METRICS).
Usage: analyze_ha.py <spec.json> <runs_root> <out.json> [--runs a-b]
Reads bash commands + tool outputs + the submission from mini-swe-agent.traj.json; never reads reasoning content."""
import json, os, re, sys, glob, argparse, statistics, datetime
ap = argparse.ArgumentParser(); ap.add_argument("spec"); ap.add_argument("runs_root"); ap.add_argument("out"); ap.add_argument("--runs", default="1-5"); a = ap.parse_args()
S = json.load(open(a.spec)); LO, HI = [int(x) for x in a.runs.split("-")]
def rj(p):
    try: return json.load(open(p))
    except Exception: return None
def strip_cd(c): return re.sub(r"^\s*cd\s+'?[^'&;]*'?\s*&&\s*", "", c)
def steps_from(traj):
    msgs = traj.get("messages", []) if traj else []; outs = {}
    for m in msgs:
        if m.get("role") == "tool": outs[m.get("tool_call_id")] = m.get("content") if isinstance(m.get("content"), str) else json.dumps(m.get("content"))
    steps, submit = [], None
    for m in msgs:
        if m.get("role") != "assistant": continue
        for tc in m.get("tool_calls") or []:
            fn = tc.get("function") or {}; name = fn.get("name"); args = fn.get("arguments")
            try: args = json.loads(args) if isinstance(args, str) else (args or {})
            except Exception: args = {}
            if name == "bash": steps.append({"idx": len(steps) + 1, "raw": args.get("command", ""), "command": strip_cd(args.get("command", "")), "output": outs.get(tc.get("id"), "") or ""})
            elif name == "submit_fault_localization": submit = {"idx": len(steps) + 1, "predictions": args.get("predictions"), "evidence_chain": args.get("evidence_chain")}
    return steps, submit, msgs
SEARCH = re.compile(r"\b(grep|rg|ag|find|ack|awk)\b"); EXEC = re.compile(r"(?:^|[\s;&|(])(python3?|jshell|javac|java|bc|perl|node)\b(?!/)")
def is_search(c): return bool(SEARCH.search(c)) and "defects4j test" not in c
def first_out(steps, needle): return next((s["idx"] for s in steps if needle and needle in s["output"]), None)
def analyze(rdir, vid):
    man = rj(os.path.join(rdir, "run_manifest.json")) or {}; ev = rj(os.path.join(rdir, "evaluation.json")) or {}; rk = rj(os.path.join(rdir, "ranking.json")) or {}
    traj = rj(os.path.join(rdir, "mini-swe-agent.traj.json")) or {}; steps, submit, msgs = steps_from(traj); ms = (traj.get("info") or {}).get("model_stats") or {}
    preds = (rk.get("structured_submission") or {}).get("predictions") or rk.get("predictions") or (submit or {}).get("predictions") or []
    top = [f"{p.get('class')}::{p.get('method')}" for p in preds[:10]]; gold_key = S["gold"]["key"]; gold_rank = ev.get("gold_rank")
    if gold_rank is None and top: gold_rank = next((i + 1 for i, k in enumerate(top) if k == gold_key), None)
    cands = S["candidates"][vid]; G = S["gold"]; H1 = S["hop1"]; F = S["facade"]
    nodes = {"facade": F, "pack": H1, "gold": G, **{c["name"]: c for c in cands}}
    # exposure per node: declaration shown / body shown / any
    expo = {}
    for n, spec in nodes.items():
        body = spec.get("body") or spec.get("body_low" if vid.endswith("LOW-01") else "body_high")
        d = first_out(steps, spec["decl"]); b = first_out(steps, body); any_ = min([x for x in (d, b) if x] or [None]) if (d or b) else None
        shown_steps = sorted({s["idx"] for s in steps if (spec["decl"] in s["output"]) or (body and body in s["output"])})
        name_searches = [s["idx"] for s in steps if is_search(s["command"]) and re.search(r"\b%s\b" % re.escape(spec["name"]), s["command"])]
        usage_searches = [i for i in name_searches if any_ and i > any_]
        execs = [s["idx"] for s in steps if EXEC.search(s["command"]) and re.search(r"\b%s\b" % re.escape(spec["name"]), s["command"]) and "defects4j" not in s["command"]]
        targeted = [i for i in shown_steps if re.search(r"\b%s\b" % re.escape(spec["name"]), next(st["command"] for st in steps if st["idx"] == i))]
        expo[n] = {"decl_first_shown": d, "body_first_shown": b, "first_exposed": any_, "shown_steps": shown_steps, "targeted_views": targeted, "revisits": max(0, len(shown_steps) - 1), "name_searches": name_searches, "usage_searches_after_exposure": usage_searches, "executions": execs,
                   "seriously_investigated": bool(any_ and (usage_searches or execs or len(targeted) >= 2)), "final_rank": next((i + 1 for i, k in enumerate(top) if k == spec["key"]), None)}
    gold_step = expo["gold"]["first_exposed"]; buggy = first_out(steps, G["body"])
    non_gold = [n for n in nodes if n != "gold"]; cand_names = [c["name"] for c in cands]
    inspected = [n for n in nodes if expo[n]["first_exposed"]]; order = sorted(inspected, key=lambda n: expo[n]["first_exposed"])
    first_cand = min([expo[n]["first_exposed"] for n in inspected] or [None]) if inspected else None
    wrong_serious = [n for n in non_gold if expo[n]["seriously_investigated"]]; wrong_serious_after_gold = [n for n in non_gold if gold_step and (any(i > gold_step for i in expo[n]["usage_searches_after_exposure"] + expo[n]["executions"]) or any(i > gold_step for i in expo[n]["shown_steps"][1:]))]
    wrong_above_gold = [n for n in non_gold if expo[n]["final_rank"] and gold_rank and expo[n]["final_rank"] < gold_rank]
    # backtracking: returning to an earlier-inspected node after a different node was inspected later
    seq = sorted([(i, n) for n in inspected for i in (expo[n]["targeted_views"] or expo[n]["shown_steps"][:1])]); back = 0; seen_order = []
    for i, n in seq:
        if n in seen_order and seen_order[-1] != n: back += 1
        if not seen_order or seen_order[-1] != n: seen_order.append(n)
    # contract evidence
    contract = {k: first_out(steps, v) for k, v in S["contract_markers"].items()}; contract["E6_trigger_second_assertion"] = 0  # in the prompt (test source) from step 0
    tests_run = [s["idx"] for s in steps if "defects4j test" in s["command"]]; other_tests = [s["command"][:120] for s in steps if "defects4j test" in s["command"] and S["trigger"] not in s["command"]]
    scripted = [{"step": s["idx"], "kind": ("jshell" if "jshell" in s["command"] else "java" if re.search(r"\bjavac?\b", s["command"]) else "python" if "python" in s["command"] else "other"), "mentions": [n for n in nodes if re.search(r"\b%s\b" % re.escape(nodes[n]["name"]), s["command"])],
                 "alt_arithmetic": {k: any(m in s["command"] for m in (v if isinstance(v, list) else [v])) for k, v in S["alt_hypothesis_markers"].items()}, "head": s["command"][:160]} for s in steps if EXEC.search(s["command"]) and "defects4j" not in s["command"]]
    repairs_considered = [x for x in scripted if x["alt_arithmetic"]["floor_alt"] or x["alt_arithmetic"]["shift_five"] or x["alt_arithmetic"]["ceil_idiom"] or "lane" in x["mentions"]]
    # leakage / shortcut: gold exposed by a search not naming lane before pack was displayed
    gold_cmd = next((s["command"] for s in steps if s["idx"] == gold_step), "") if gold_step else ""
    shortcut = bool(gold_step and is_search(gold_cmd) and not re.search(r"\blane\b", gold_cmd) and (expo["pack"]["first_exposed"] is None or expo["pack"]["first_exposed"] > gold_step))
    # CED: last observable touch of any non-gold candidate (body shown / usage search / execution) before submission
    touches = [i for n in cand_names + ["pack", "facade"] for i in expo[n]["targeted_views"] + expo[n]["usage_searches_after_exposure"] + expo[n]["executions"]]
    ced = max(touches) if touches else None
    status = man.get("status"); tool_calls = len(steps)
    if status == "completed":
        cls = ("B. gold discovered, wrong candidate ranked above gold" if (gold_rank and gold_rank > 1 and wrong_above_gold) else "A. gold not discovered" if not gold_step else
               "C. gold discovered and ranked first after eliminating decoys (non-gold candidate seriously investigated)" if (gold_rank == 1 and (wrong_serious_after_gold or [n for n in cand_names if expo[n]["seriously_investigated"]])) else
               "D. gold discovered and immediately dominant" if gold_rank == 1 else "B'. gold discovered, ranked below rank 1 without a candidate above it")
    else: cls = f"n/a ({status})"
    if shortcut: cls += " + E. lexical shortcut flag"
    return {"run_id": f"{vid}/{os.path.basename(rdir)}", "arm": "LOW" if vid.endswith("LOW-01") else "HIGH", "status": status, "gold_rank": gold_rank, "reciprocal_rank": (1 / gold_rank) if gold_rank else 0, "hit_at_1": gold_rank == 1, "hit_at_3": bool(gold_rank and gold_rank <= 3), "hit_at_5": bool(gold_rank and gold_rank <= 5),
            "tool_call_count": tool_calls, "api_calls": ms.get("api_calls"), "cost_usd": (ms.get("cost") if ms.get("cost") is not None else ms.get("instance_cost")), "top10": top, "exposure": expo, "gold_first_exposed_step": gold_step, "buggy_line_first_shown": buggy, "gold_exposing_cmd": gold_cmd[:200],
            "first_candidate_exposed": {"step": first_cand, "which": [n for n in order if expo[n]["first_exposed"] == first_cand]}, "candidates_inspected": inspected, "inspection_order": order, "n_candidate_methods_inspected": len(inspected),
            "wrong_candidates_seriously_investigated": wrong_serious, "wrong_candidates_seriously_investigated_after_gold": wrong_serious_after_gold, "wrong_candidates_ranked_above_gold": wrong_above_gold,
            "calls_from_first_candidate_to_ranking": (tool_calls - first_cand + 1) if first_cand else None, "calls_after_gold": (tool_calls - gold_step) if gold_step else None, "backtracking_events": back,
            "contract_first_shown": contract, "external_evidence_sources_used": sorted(k for k, v in contract.items() if v is not None and k != "E6_trigger_second_assertion"), "tests_executed": tests_run, "other_tests_executed": other_tests,
            "scripted_computations": scripted, "counterfactual_repairs_considered_observable": repairs_considered, "candidate_elimination_depth_step": ced, "ced_calls_before_ranking": (tool_calls - ced) if ced else None,
            "lexical_shortcut_flag": shortcut, "discrimination_class": cls, "candidate_final_ranks": {n: expo[n]["final_rank"] for n in nodes},
            "agent_reported_evidence_chain_unverified": (submit or {}).get("evidence_chain"), "steps": [{"idx": s["idx"], "command": s["command"][:220]} for s in steps]}
def mm(xs): xs = [x for x in xs if x is not None]; return [round(statistics.mean(xs), 2), statistics.median(xs)] if xs else [None, None]
runs = []
for vid in ("HA-LOW-01", "HA-HIGH-01"):
    for rdir in sorted(glob.glob(os.path.join(a.runs_root, vid, "run-*"))):
        if LO <= int(os.path.basename(rdir).split("-")[-1]) <= HI: runs.append(analyze(rdir, vid))
def agg(rs):
    comp = [r for r in rs if r["status"] == "completed"]; act = [r for r in rs if r["tool_call_count"] > 0]
    rate = lambda k: (sum(1 for r in comp if r[k]) / len(comp)) if comp else None
    cls = {}
    for r in rs: cls[r["discrimination_class"]] = cls.get(r["discrimination_class"], 0) + 1
    ev = {}
    for r in rs:
        for k in r["external_evidence_sources_used"]: ev[k] = ev.get(k, 0) + 1
    return {"n": len(rs), "completed": len(comp), "timeout": sum(1 for r in rs if r["status"] == "timeout"), "other_status": [(r["run_id"], r["status"]) for r in rs if r["status"] not in ("completed", "timeout")],
            "gold_ranks": [r["gold_rank"] for r in rs], "acc_at_1": rate("hit_at_1"), "acc_at_3": rate("hit_at_3"), "acc_at_5": rate("hit_at_5"), "mrr": (sum(r["reciprocal_rank"] for r in comp) / len(comp)) if comp else None,
            "tool_calls": [r["tool_call_count"] for r in rs], "tool_calls_mean_completed": mm([r["tool_call_count"] for r in comp])[0], "api_calls": [r["api_calls"] for r in rs], "cost_usd": round(sum(r["cost_usd"] or 0 for r in rs), 4),
            "gold_first_exposed": [r["gold_first_exposed_step"] for r in rs], "gold_first_exposed_mean": mm([r["gold_first_exposed_step"] for r in rs])[0], "first_candidate_exposed": [r["first_candidate_exposed"]["step"] for r in rs],
            "n_candidate_methods_inspected": [r["n_candidate_methods_inspected"] for r in rs], "n_candidate_methods_inspected_mean": mm([r["n_candidate_methods_inspected"] for r in rs])[0],
            "wrong_candidates_seriously_investigated": [len(r["wrong_candidates_seriously_investigated"]) for r in rs], "wrong_candidates_seriously_investigated_mean": mm([len(r["wrong_candidates_seriously_investigated"]) for r in rs])[0],
            "wrong_candidates_seriously_investigated_after_gold": [len(r["wrong_candidates_seriously_investigated_after_gold"]) for r in rs], "wrong_candidates_ranked_above_gold": [len(r["wrong_candidates_ranked_above_gold"]) for r in rs],
            "calls_from_first_candidate_to_ranking": [r["calls_from_first_candidate_to_ranking"] for r in rs], "calls_from_first_candidate_to_ranking_mean": mm([r["calls_from_first_candidate_to_ranking"] for r in comp])[0], "calls_after_gold": [r["calls_after_gold"] for r in rs], "calls_after_gold_mean_completed": mm([r["calls_after_gold"] for r in comp])[0],
            "backtracking_events": [r["backtracking_events"] for r in rs], "backtracking_mean": mm([r["backtracking_events"] for r in rs])[0], "external_evidence_sources_used_counts": ev, "external_evidence_sources_per_run": [len(r["external_evidence_sources_used"]) for r in rs],
            "other_tests_executed_runs": sum(1 for r in rs if r["other_tests_executed"]), "scripted_computation_runs": sum(1 for r in rs if r["scripted_computations"]), "counterfactual_repairs_considered_runs": sum(1 for r in rs if r["counterfactual_repairs_considered_observable"]),
            "ced_step": [r["candidate_elimination_depth_step"] for r in rs], "ced_calls_before_ranking": [r["ced_calls_before_ranking"] for r in rs], "lexical_shortcut_runs": sum(1 for r in rs if r["lexical_shortcut_flag"]), "discrimination_classes": cls,
            "candidate_final_ranks": {n: [r["candidate_final_ranks"].get(n) for r in rs] for n in (rs[0]["candidate_final_ranks"] if rs else {})}, "inspection_orders": [r["inspection_order"] for r in rs]}
out = {"schema_version": "hypothesis-ambiguity-results/v1", "label": S["label"], "run_range": a.runs, "interpretation_rule": "Observable trajectory evidence only; n = 5 per arm; descriptive; timeouts are provider/harness events, never localization misses; classes A-E per run.",
       "per_arm": {"LOW": agg([r for r in runs if r["arm"] == "LOW"]), "HIGH": agg([r for r in runs if r["arm"] == "HIGH"])}, "total_recorded_cost_usd": round(sum(r["cost_usd"] or 0 for r in runs), 4), "runs": runs}
json.dump(out, open(a.out, "w"), indent=1)
for r in runs: print(r["run_id"], r["status"], "rank", r["gold_rank"], "| tc", r["tool_call_count"], "| gold@", r["gold_first_exposed_step"], "| inspected", r["inspection_order"], "| serious wrong", r["wrong_candidates_seriously_investigated"], "| above gold", r["wrong_candidates_ranked_above_gold"], "| back", r["backtracking_events"], "| evidence", r["external_evidence_sources_used"], "| CED", r["candidate_elimination_depth_step"], "|", r["discrimination_class"][:60])
print(json.dumps({k: v for k, v in out["per_arm"].items()}, indent=1)[:3000])
