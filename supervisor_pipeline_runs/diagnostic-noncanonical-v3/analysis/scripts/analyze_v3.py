"""Observable-only analysis of DIAGNOSTIC / NON-CANONICAL / LOCALLY-COHERENT-CONVERSION-V1 runs.
Reads only bash commands, tool outputs, test executions and submitted rankings from mini-swe-agent.traj.json and run artifacts.
Never reads assistant reasoning_content / reasoning_items. Agent-reported evidence_chain items are labelled agent_reported (unverified)."""
import json, os, re, sys, glob, statistics, argparse
_ap = argparse.ArgumentParser(); _ap.add_argument("PR", nargs="?", default="/Users/shawnli/Desktop/Honours/defects4j/supervisor_pipeline_runs/diagnostic-noncanonical-v3")
_ap.add_argument("--runs", default="1-5", help="inclusive run index range, e.g. 1-5 (first block, default) or 6-10 (supplementary)")
_ap.add_argument("--arms", default="CONTROL,TREATMENT"); _ap.add_argument("--out", default="diagnostic_v3_results.json"); _ap.add_argument("--label", default="DIAGNOSTIC / NON-CANONICAL / LOCALLY-COHERENT-CONVERSION-V1"); _ap.add_argument("--experiment-id", default="diagnostic-noncanonical-v3")
_args = _ap.parse_args(); PR = _args.PR; _lo, _hi = (int(x) for x in _args.runs.split("-")); _ARMS_SEL = set(_args.arms.split(","))
def _run_index(rdir): return int(os.path.basename(rdir).split("-")[-1])
AGENT = "mini-swe-agent-openai-gpt-5-6"
ARMS = {"CONVERSION-CONTROL-01": dict(arm="CONTROL", gold_class="org.apache.commons.lang3.Conversion", gold_method="intArrayToLong", gold_file="Conversion.java", gold_decl="intArrayToLong(final int[] src", buggy='shift = (i + dstPos) * 32;'),
        "CONVERSION-TREATMENT-01": dict(arm="TREATMENT", gold_class="org.apache.commons.lang3.math.Fraction", gold_method="assemble", gold_file="Fraction.java", gold_decl="assemble(final int[] values", buggy='shift = (i + at) * 32;')}
# Observable markers (first occurrence in a tool OUTPUT); commands are checked separately
MARK = {"A_testLang1112": "testLang1112", "B_ConversionTest": "ConversionTest", "C_intArrayToLong": "intArrayToLong", "D_Conversion_java": "Conversion.java",
        "E_ArrayUtils_foldValues": "foldValues", "F_Fraction_assemble": "assemble(", "G_dstPos": "dstPos", "H_in_bits": "in bits", "I_longToIntArray": "longToIntArray",
        "J_sibling_pattern_i32_dstPos": "i * 32 + dstPos", "J2_sibling_pattern_short_width": "i * 16 + dstPos", "J3_sibling_pattern_byte_width": "i * 8 + dstPos", "J4_inverse_longToIntArray_pattern": "i * 32 + srcPos", "K_buggy_pattern_facade": "(i + dstPos) * 32", "K2_buggy_pattern_hop": "(i + at) * 32",
        "L_0xffffffffL": "0xffffffffL", "L_shift_left": "<< shift", "M_sibling_test_dstPos_24": "0x123456789ABCDEF0L, 24, 1", "M_sibling_test_dstPos_16": "0x123456789ABCDEF0L, 16, 2", "M_sibling_test_dstPos_8": "0x123456789ABCDEF0L, 8, 2",
        "facade_delegate_call": "return ArrayUtils.foldValues(src, srcPos, dstInit, dstPos, nInts);", "hop1_body_call": "return Fraction.assemble(values, from, initial, at, count);", "facade_guard": "(nInts - 1) * 32 + dstPos >= 64", "assertion_msg": "expected:<64729929216> but was:<252851286>",
        "d4j_modified_class_output": "d4j.classes.modified"}
CONTRACT_KEYS = ["H_in_bits", "facade_guard", "J_sibling_pattern_i32_dstPos", "J2_sibling_pattern_short_width", "J3_sibling_pattern_byte_width", "J4_inverse_longToIntArray_pattern", "I_longToIntArray", "M_sibling_test_dstPos_24", "M_sibling_test_dstPos_16", "M_sibling_test_dstPos_8"]
PAYLOAD_TOKENS = {"testLang1112", "ConversionTest", "Conversion", "intArrayToLong", "src", "assertEquals", "int", "new", "final", "Test"}
NOVEL_WATCH = ["dstPos", "srcPos", "nInts", "dstInit", "shift", "longToIntArray", "0xffffffffL", "i * 32 + dstPos", "shortArrayToLong", "byteArrayToLong", "intToLong", "binaryToLong", "endian", "Lsb0", "mask", "bits", "foldValues", "assemble", "Fraction", "ArrayUtils", "0xffffffff"]
def rj(p):
    try: return json.load(open(p))
    except Exception: return None
def strip_cd(c):
    c = re.sub(r'^cd\s+\S+\s*&&\s*', '', c.strip())
    c = re.sub(r"^ROOT='[^']*'\s*;?\s*(cd\s+\"?\$ROOT\"?\s*&&\s*)?", '', c)  # run-007 style: ROOT='<workspace>'; cd "$ROOT" && ...
    return c.replace('$ROOT/', '')
def is_search(c): return bool(re.search(r'\b(rg|grep|find|fd|ag)\b', c))
def is_test(c): return "defects4j test" in c
def opened_files(c): return re.findall(r'(?:cat|less|more|head|tail|nl -ba|nl|sed -n \S+)\s+(?:-[A-Za-z0-9]+\s+)*([^\s|;&]+\.java)', c)
def steps_from(traj):
    msgs = traj.get("messages", []); outs = {m.get("tool_call_id"): (m.get("content") or "") for m in msgs if m.get("role") == "tool"}
    steps = []; submit = None
    for m in msgs:
        if m.get("role") != "assistant": continue
        for tc in m.get("tool_calls") or []:
            fn = tc.get("function") or {}; name = fn.get("name"); args = fn.get("arguments")
            try: args = json.loads(args) if isinstance(args, str) else (args or {})
            except Exception: args = {}
            if name == "bash": steps.append({"idx": len(steps) + 1, "command": strip_cd(args.get("command", "")), "output": outs.get(tc.get("id"), "")})
            elif name == "submit_fault_localization": submit = {"idx": len(steps) + 1, "predictions": args.get("predictions"), "evidence_chain": args.get("evidence_chain")}
    return steps, submit
def first_out(steps, needle): return next((s["idx"] for s in steps if needle in s["output"]), None)
def first_cmd(steps, pred): return next((s["idx"] for s in steps if pred(s["command"])), None)
def analyze(rdir, vid, spec):
    man = rj(os.path.join(rdir, "run_manifest.json")) or {}; ev = rj(os.path.join(rdir, "evaluation.json")) or {}; rk = rj(os.path.join(rdir, "ranking.json")) or {}; pr = rj(os.path.join(rdir, "prompt.json")) or {}; si = rj(os.path.join(rdir, "source_integrity.json")) or {}; pis = rj(os.path.join(rdir, "pilot_information_sources.json")) or {}
    traj = rj(os.path.join(rdir, "mini-swe-agent.traj.json")) or {}; steps, submit = steps_from(traj); ms = (traj.get("info") or {}).get("model_stats") or {}
    preds = (rk.get("structured_submission") or {}).get("predictions") or rk.get("predictions") or (submit or {}).get("predictions") or []
    top = [f"{p.get('class')}::{p.get('method')}" for p in preds[:10]]; gold_key = f"{spec['gold_class']}::{spec['gold_method']}"
    gold_rank = ev.get("gold_rank");
    if gold_rank is None and top: gold_rank = next((i + 1 for i, k in enumerate(top) if k == gold_key), None)
    fo = {k: first_out(steps, v) for k, v in MARK.items()}
    fc = {"first_command": steps[0]["command"][:160] if steps else None, "first_search_idx": first_cmd(steps, is_search), "first_search_cmd": next((s["command"][:160] for s in steps if is_search(s["command"])), None),
          "first_file_opened": next((opened_files(s["command"])[0] for s in steps if opened_files(s["command"])), None), "first_file_opened_idx": first_cmd(steps, lambda c: bool(opened_files(c))),
          "first_action_is_test_run": bool(steps) and is_test(steps[0]["command"]), "tests_executed": [s["command"][:100] for s in steps if is_test(s["command"])],
          "foldValues_cmd_idx": first_cmd(steps, lambda c: "foldValues" in c), "assemble_cmd_idx": first_cmd(steps, lambda c: "assemble" in c), "Fraction_cmd_idx": first_cmd(steps, lambda c: "Fraction" in c),
          "dstPos_cmd_idx": first_cmd(steps, lambda c: "dstPos" in c), "sibling_method_cmd_idx": first_cmd(steps, lambda c: bool(re.search(r'shortArrayToLong|byteArrayToLong|longToIntArray|shortArrayToInt|byteArrayToInt|intToLong|binaryToLong', c))),
          "build_properties_cmd_idx": first_cmd(steps, lambda c: "defects4j.build.properties" in c or ".defects4j.config" in c or "classes.modified" in c), "javap_jshell_idx": [s["idx"] for s in steps if re.search(r'\bjshell\b|\bjavap\b', s["command"])],
          "failing_tests_read_idx": first_cmd(steps, lambda c: bool(re.search(r'\bcat failing_tests', c)))}
    # gold exposure = gold declaration or buggy line first shown in an output
    gold_decl_idx = first_out(steps, spec["gold_decl"]); buggy_idx = first_out(steps, spec["buggy"]); cands = [x for x in (gold_decl_idx, buggy_idx) if x]
    gold_idx = min(cands) if cands else None; gold_cmd = next((s["command"] for s in steps if s["idx"] == gold_idx), None)
    n_after_gold = (len(steps) - gold_idx) if gold_idx else None
    # contract evidence: first output showing any contract marker; (for CONTROL the facade javadoc/guard sit in the gold method itself)
    contract_steps = {k: fo[k] for k in CONTRACT_KEYS if fo[k]}
    first_contract = min(contract_steps.values()) if contract_steps else None
    contract_after_gold = sorted(k for k, v in contract_steps.items() if gold_idx and v > gold_idx)
    # search commands after gold exposure (post-gold investigation)
    post_gold_cmds = [s for s in steps if gold_idx and s["idx"] > gold_idx]
    post_gold_searches = [s["command"][:120] for s in post_gold_cmds if is_search(s["command"])]; post_gold_opens = [s["command"][:120] for s in post_gold_cmds if opened_files(s["command"])]
    # novel search vocabulary: tokens in a search command that had not appeared in the payload or any EARLIER tool output
    novel = []
    for s in steps:
        if not is_search(s["command"]): continue
        earlier = "\n".join(x["output"] for x in steps if x["idx"] < s["idx"]) + "\n" + "\n".join(x["command"] for x in steps if x["idx"] < s["idx"])
        for w in NOVEL_WATCH:
            if w in s["command"] and w not in earlier and w not in PAYLOAD_TOKENS:
                novel.append({"step": s["idx"], "token": w, "command": s["command"][:140]})
    # traversal classification (TREATMENT)
    if spec["arm"] == "TREATMENT":
        f, h1c, h1b, g = fo["facade_delegate_call"], fc["foldValues_cmd_idx"], fo["hop1_body_call"], gold_idx
        if g is None: trav = "gold never exposed"
        elif f and h1b and f < g and h1b <= g and ("assemble" in (gold_cmd or "") or "Fraction" in (gold_cmd or "")): trav = "A. explicit facade->foldValues->assemble traversal"
        elif f and h1b and f < g and h1b <= g: trav = "A'. traversal (facade and hop1 body seen before gold; gold exposed by a non-name command)"
        elif g and (h1b is None or g < h1b) and is_search(gold_cmd or "") and not any(t in (gold_cmd or "") for t in ("assemble", "foldValues", "Fraction")): trav = "B/C. lexical or pattern search reached the gold before hop1's call was seen"
        elif f and g and f < g and h1b is None: trav = "E. facade seen, hop1 body never shown, gold reached otherwise"
        else: trav = "E. other / unclear"
    else: trav = "n/a"
    coherence = {"gold_seen_before_contract_evidence": bool(gold_idx and (first_contract is None or gold_idx < first_contract)),
                 "contract_evidence_seen_before_final_rank": bool(first_contract), "contract_evidence_after_gold_before_rank": contract_after_gold,
                 "external_evidence_types": sorted(contract_steps.keys()), "post_gold_search_count": len(post_gold_searches), "post_gold_open_count": len(post_gold_opens),
                 "post_gold_searches": post_gold_searches[:8], "post_gold_opens": post_gold_opens[:8]}
    cl = open(os.path.join(rdir, "commands.log")).read() if os.path.exists(os.path.join(rdir, "commands.log")) else ""
    raw = open(os.path.join(rdir, "raw_agent_output.txt"), errors="replace").read() if os.path.exists(os.path.join(rdir, "raw_agent_output.txt")) else ""
    timing = {"execution_timer_started_at": (re.search(r"execution_timer_started_at: (\S+)", cl) or [None, None])[1], "duration_ms": int((re.search(r"duration_ms: (\d+)", cl) or [None, "0"])[1]) or None, "timed_out": "timed_out: true" in cl, "signal": (re.search(r"signal: (\S+)", cl) or [None, None])[1],
              "provider_retry_lines": raw.count("Retrying"), "provider_error_excerpt": (re.search(r"raised ([^\n]{0,160})", raw) or [None, None])[1],
              "blocked_on": ("model response (last tool result was delivered; no further assistant message)" if (steps and traj.get("messages") and traj["messages"][-1].get("role") == "tool" and man.get("status") == "timeout") else ("n/a" if man.get("status") != "timeout" else "unclear"))}
    return {"run_id": "/".join(rdir.split("/")[-2:]), "variant_id": vid, "arm": spec["arm"], "gold": gold_key, "status": man.get("status"), "status_reason": man.get("status_reason"), "timing": timing,
            "gold_rank": gold_rank, "hit_at_1": gold_rank == 1, "hit_at_3": bool(gold_rank and gold_rank <= 3), "hit_at_5": bool(gold_rank and gold_rank <= 5), "hit_at_10": bool(gold_rank and gold_rank <= 10), "reciprocal_rank": (1.0 / gold_rank) if gold_rank else 0.0,
            "top10": top, "tool_call_count": (man.get("metrics") or {}).get("tool_call_count"), "search_count": (man.get("metrics") or {}).get("search_count"), "test_run_count": (man.get("metrics") or {}).get("test_run_count"),
            "api_calls": ms.get("api_calls"), "cost_usd": ms.get("instance_cost"), "source_integrity_ok": si.get("ok"), "protocol_violation": man.get("status") == "protocol_violation",
            "prompt_version": pr.get("version"), "base_prompt_sha256": pr.get("base_prompt_sha256"), "rendered_prompt_sha256": pr.get("rendered_prompt_sha256"), "information_sources": pis,
            "trajectory_path": os.path.join(rdir, "trajectory.jsonl"), "raw_trajectory_path": os.path.join(rdir, "mini-swe-agent.traj.json"),
            "first_exposure_output": fo, "first_commands": fc, "gold_first_exposed_step": gold_idx, "gold_exposing_cmd": (gold_cmd or "")[:200], "tool_calls_before_gold": (gold_idx - 1) if gold_idx else None, "tool_calls_after_gold": n_after_gold,
            "traversal": trav, "coherence": coherence, "novel_search_vocabulary": novel, "total_bash_steps": len(steps),
            "steps": [{"idx": s["idx"], "command": s["command"][:300], "output_head": s["output"][:160].replace("\n", " | ")} for s in steps],
            "agent_reported_evidence_chain_unverified": (submit or {}).get("evidence_chain"), "hidden_reasoning_read": False}
runs = []
for vid, spec in ARMS.items():
    if spec["arm"] not in _ARMS_SEL: continue
    for rdir in sorted(glob.glob(os.path.join(PR, "benchmark_runs", AGENT, vid, "run-*"))):
        if _lo <= _run_index(rdir) <= _hi: runs.append(analyze(rdir, vid, spec))
def mm(xs): xs = [x for x in xs if x is not None]; return (statistics.mean(xs), statistics.median(xs)) if xs else (None, None)
def agg(rs):
    comp = [r for r in rs if r["status"] == "completed"]; ranks = [r["gold_rank"] for r in rs if r["gold_rank"]]
    rate = lambda k: (sum(1 for r in comp if r[k]) / len(comp)) if comp else None
    rate_all = lambda k: (sum(1 for r in rs if r[k]) / len(rs)) if rs else None
    return {"n_found": len(rs), "completed": len(comp), "metric_basis_note": "acc_at_k / mrr are over COMPLETED runs only; *_all_runs count timeouts and non-submissions as misses (rank None -> 0).",
            "acc_at_1_all_runs": rate_all("hit_at_1"), "acc_at_3_all_runs": rate_all("hit_at_3"), "acc_at_5_all_runs": rate_all("hit_at_5"), "acc_at_10_all_runs": rate_all("hit_at_10"), "mrr_all_runs": (sum(r["reciprocal_rank"] for r in rs) / len(rs)) if rs else None, "failed_or_other": [(r["run_id"], r["status"]) for r in rs if r["status"] != "completed"], "timeout": sum(1 for r in rs if r["status"] == "timeout"), "protocol_violation": sum(1 for r in rs if r["protocol_violation"]),
            "acc_at_1": rate("hit_at_1"), "acc_at_3": rate("hit_at_3"), "acc_at_5": rate("hit_at_5"), "acc_at_10": rate("hit_at_10"), "mrr": (sum(r["reciprocal_rank"] for r in comp) / len(comp)) if comp else None,
            "gold_ranks": [r["gold_rank"] for r in rs], "gold_rank_mean_median": mm(ranks), "tool_calls": [r["tool_call_count"] for r in rs], "tool_calls_mean_median": mm([r["tool_call_count"] for r in rs]),
            "api_calls": [r["api_calls"] for r in rs], "api_calls_mean_median": mm([r["api_calls"] for r in rs]), "first_gold_step": [r["gold_first_exposed_step"] for r in rs], "first_gold_step_mean_median": mm([r["gold_first_exposed_step"] for r in rs]),
            "calls_after_gold": [r["tool_calls_after_gold"] for r in rs], "calls_after_gold_mean_median": mm([r["tool_calls_after_gold"] for r in rs]), "costs": [r["cost_usd"] for r in rs], "total_cost_usd": sum(r["cost_usd"] or 0 for r in rs),
            "traversal": {t: sum(1 for r in rs if r["traversal"] == t) for t in sorted({r["traversal"] for r in rs})},
            "full_chain_traversal_rate": (sum(1 for r in rs if r["traversal"].startswith("A")) / len(rs)) if rs and rs[0]["arm"] == "TREATMENT" else None,
            "lexical_bypass_rate": (sum(1 for r in rs if r["traversal"].startswith("B")) / len(rs)) if rs and rs[0]["arm"] == "TREATMENT" else None,
            "external_contract_retrieval_rate": (sum(1 for r in rs if r["coherence"]["contract_evidence_seen_before_final_rank"]) / len(rs)) if rs else None,
            "contract_after_gold_rate": (sum(1 for r in rs if r["coherence"]["contract_evidence_after_gold_before_rank"]) / len(rs)) if rs else None,
            "novel_vocab_events": sum(len(r["novel_search_vocabulary"]) for r in rs), "runs_with_novel_vocab": sum(1 for r in rs if r["novel_search_vocabulary"]),
            "build_properties_observably_used": sum(1 for r in rs if r["first_commands"]["build_properties_cmd_idx"] or r["first_exposure_output"]["d4j_modified_class_output"]), "source_integrity_ok_all": all(r["source_integrity_ok"] for r in rs) if rs else None}
smoke = None
_smokes = sorted(glob.glob(os.path.join(PR, "benchmark_runs", "_smoke", "**", "*.traj.json"), recursive=True))
_pick = _smokes[:1] if _lo == 1 else _smokes[1:2]  # first smoke belongs to the first block; second to the supplementary block
for p in _pick: smoke = ((rj(p) or {}).get("info") or {}).get("model_stats", {}).get("instance_cost")
out = {"schema_version": "pilot-diagnostic-results/v3", "label": _args.label, "experiment_id": _args.experiment_id, "run_range": _args.runs, "arms_selected": sorted(_ARMS_SEL),
       "interpretation_rule": "Not an L20 / reasoning-depth estimate and not a causal CONTROL-vs-TREATMENT effect; n=5 per arm; descriptive only.",
       "per_arm": {"CONTROL": agg([r for r in runs if r["arm"] == "CONTROL"]), "TREATMENT": agg([r for r in runs if r["arm"] == "TREATMENT"])}, "smoke_test_cost_usd": smoke, "total_recorded_cost_usd": sum(r["cost_usd"] or 0 for r in runs) + (smoke or 0), "runs": runs}
json.dump(out, open(os.path.join(PR, _args.out), "w"), indent=1)
print(json.dumps({k: v for k, v in out.items() if k != "runs"}, indent=1))
for r in runs:
    print(f"\n### {r['run_id']} [{r['arm']}] status={r['status']} gold_rank={r['gold_rank']} tool_calls={r['tool_call_count']} api={r['api_calls']} cost={r['cost_usd']}")
    print("  traversal:", r["traversal"], "| gold at", r["gold_first_exposed_step"], "via:", r["gold_exposing_cmd"][:120]); print("  coherence:", {k: v for k, v in r["coherence"].items() if k not in ("post_gold_searches", "post_gold_opens")}); print("  novel:", r["novel_search_vocabulary"][:6]); print("  top3:", r["top10"][:3])
    for s in r["steps"]: print(f"   {s['idx']:>2}. {s['command'][:150]}")
