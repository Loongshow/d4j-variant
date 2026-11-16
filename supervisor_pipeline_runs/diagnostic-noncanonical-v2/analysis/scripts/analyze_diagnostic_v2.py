"""Observable-only analysis of the DIAGNOSTIC / NON-CANONICAL / LEAKAGE-EXPOSED runs.
Reads run artifacts under <pilot>/benchmark_runs/<agent>/<variant>/run-*/ and reconstructs ONLY
observable agent actions (bash commands), tool outputs, test executions and the submitted ranking.
It never reads assistant `reasoning_content`/`reasoning_items` (hidden reasoning) and never treats
them as evidence. Agent-reported evidence_chain items are labelled agent_reported (unverified)."""
import json, os, re, sys, glob, statistics
PR = sys.argv[1] if len(sys.argv) > 1 else "/Users/shawnli/Desktop/Honours/defects4j/supervisor_pipeline_runs/diagnostic-noncanonical-v2"
AGENT = "mini-swe-agent-openai-gpt-5-6"
ARMS = {
  "NUMBERUTILS-CONTROL-02": dict(arm="CONTROL", gold_class="org.apache.commons.lang3.math.NumberUtils", gold_method="createBigInteger",
                                 gold_file="src/main/java/org/apache/commons/lang3/math/NumberUtils.java",
                                 gold_decl='createBigInteger(final String str)'),
  "NUMBERUTILS-TREATMENT-02": dict(arm="TREATMENT", gold_class="org.apache.commons.lang3.builder.CompareToBuilder", gold_method="decodeMagnitude",
                                   gold_file="src/main/java/org/apache/commons/lang3/builder/CompareToBuilder.java",
                                   gold_decl='decodeMagnitude(final String str)'),
}
BUGGY = 'str.startsWith("-") || str.startsWith("+")'
PLUS_CMD = ['"+"', "'+'", 'startsWith(\\"+\\")', 'startsWith("+")', '+1234', '\\+1234', "startsWith..+", '"+7']
TEST_TOKENS = ["createBigInteger", "testLang1106", "+1234", '"+"', "BigInteger", "negate", "radix", "startsWith", "NumberUtils", "+7"]
HOPS = ["resolveWholeValue", "decodeMagnitude"]

def rj(p):
    try: return json.load(open(p))
    except Exception: return None
def strip_cd(cmd):
    return re.sub(r'^cd\s+\S+\s*&&\s*', '', cmd.strip())
def is_search(c): return bool(re.search(r'\b(rg|grep|find|fd|ag)\b', c))
def is_test(c): return "defects4j test" in c
def opened_file(c):
    m = re.search(r'(?:cat|less|more|head|tail|nl|sed\s+-n\s+\S+)\s+(?:-[A-Za-z0-9]+\s+)*([^\s|;&]+\.java|failing_tests|all_tests|[^\s|;&]+\.properties|[^\s|;&]+\.config)', c)
    return m.group(1) if m else None

def steps_from_traj(traj):
    """ordered list of {idx, command, output} from assistant tool calls and matching tool messages"""
    msgs = traj.get("messages", []); outputs = {}
    for m in msgs:
        if m.get("role") == "tool":
            outputs[m.get("tool_call_id")] = m.get("content") or ""
    steps = []; submit = None
    for m in msgs:
        if m.get("role") != "assistant": continue
        for tc in m.get("tool_calls") or []:
            fn = tc.get("function") or {}; name = fn.get("name"); args = fn.get("arguments")
            try: args = json.loads(args) if isinstance(args, str) else (args or {})
            except Exception: args = {}
            if name == "bash":
                steps.append({"idx": len(steps) + 1, "command": strip_cd(args.get("command", "")), "output": outputs.get(tc.get("id"), "")})
            elif name == "submit_fault_localization":
                submit = {"idx": len(steps) + 1, "predictions": args.get("predictions"), "evidence_chain_agent_reported": args.get("evidence_chain")}
    return steps, submit

def first(steps, pred_cmd=None, pred_out=None):
    for s in steps:
        if pred_cmd and pred_cmd(s["command"]): return s["idx"]
        if pred_out and pred_out(s["output"]): return s["idx"]
    return None

def analyze_run(rdir, vid, spec):
    man = rj(os.path.join(rdir, "run_manifest.json")) or {}
    ev = rj(os.path.join(rdir, "evaluation.json")) or {}
    rk = rj(os.path.join(rdir, "ranking.json")) or {}
    pr = rj(os.path.join(rdir, "prompt.json")) or {}
    si = rj(os.path.join(rdir, "source_integrity.json")) or {}
    wm = rj(os.path.join(rdir, "workspace_manifest.json")) or {}
    pis = rj(os.path.join(rdir, "pilot_information_sources.json")) or {}
    traj = rj(os.path.join(rdir, "mini-swe-agent.traj.json")) or {}
    steps, submit = steps_from_traj(traj)
    ms = (traj.get("info") or {}).get("model_stats") or {}
    preds = (rk.get("structured_submission") or {}).get("predictions") or rk.get("predictions") or (submit or {}).get("predictions") or []
    top = [f"{p.get('class')}::{p.get('method')}" for p in preds[:10]]
    gold_key = f"{spec['gold_class']}::{spec['gold_method']}"
    gold_rank = ev.get("gold_rank")
    if gold_rank is None and top:
        gold_rank = next((i + 1 for i, k in enumerate(top) if k == gold_key), None)
    o = {}
    o["first_search_cmd"] = next((s["command"] for s in steps if is_search(s["command"])), None)
    o["first_search_idx"] = first(steps, pred_cmd=is_search)
    o["first_file_opened"] = next((opened_file(s["command"]) for s in steps if opened_file(s["command"])), None)
    o["first_file_opened_idx"] = first(steps, pred_cmd=lambda c: opened_file(c) is not None)
    o["assertion_in_task_prompt"] = True  # the frozen task renders the failing test source (assertEquals(..."+1234"))
    o["first_assertion_output_idx"] = first(steps, pred_out=lambda t: "expected:<1234> but was:<-1234>" in t or "AssertionFailedError" in t)
    o["plus_clue_in_task_prompt"] = True   # "+1234" / "+7" literals and 'PositiveSigned' are in the rendered test source
    o["first_plus_clue_cmd_idx"] = first(steps, pred_cmd=lambda c: any(t in c for t in PLUS_CMD))
    o["first_plus_clue_output_idx"] = first(steps, pred_out=lambda t: 'startsWith("+")' in t)
    o["createBigInteger_in_task_prompt"] = True
    o["first_createBigInteger_cmd_idx"] = first(steps, pred_cmd=lambda c: "createBigInteger" in c)
    o["first_createBigInteger_decl_output_idx"] = first(steps, pred_out=lambda t: "createBigInteger(final String str)" in t)
    o["first_facade_body_output_idx"] = first(steps, pred_out=lambda t: "ObjectUtils.resolveWholeValue(str)" in t)  # TREATMENT facade body
    for h in HOPS:
        o[f"first_{h}_cmd_idx"] = first(steps, pred_cmd=lambda c, h=h: h in c)
        o[f"first_{h}_output_idx"] = first(steps, pred_out=lambda t, h=h: h in t)
    o["first_buggy_line_output_idx"] = first(steps, pred_out=lambda t: BUGGY in t)
    o["first_gold_decl_output_idx"] = first(steps, pred_out=lambda t: spec["gold_decl"] in t)
    cands = [x for x in (o["first_buggy_line_output_idx"], o["first_gold_decl_output_idx"]) if x]
    o["first_gold_exposure_idx"] = min(cands) if cands else None
    o["tool_calls_before_first_gold_exposure"] = (o["first_gold_exposure_idx"] - 1) if o["first_gold_exposure_idx"] else None
    o["gold_reached_by_cmd"] = next((s["command"] for s in steps if s["idx"] == o["first_gold_exposure_idx"]), None)
    o["tests_executed"] = [s["command"] for s in steps if is_test(s["command"])]
    o["build_properties_cmd_idx"] = first(steps, pred_cmd=lambda c: "defects4j.build.properties" in c or ".defects4j.config" in c)
    o["build_properties_output_idx"] = first(steps, pred_out=lambda t: "d4j.classes.modified" in t)
    o["total_bash_steps"] = len(steps)
    o["first_cmd_text"] = steps[0]["command"] if steps else None
    o["first_cmd_is_grep_createBigInteger"] = bool(steps) and is_search(steps[0]["command"]) and "createBigInteger" in steps[0]["command"]
    o["first_BigInteger_family_cmd_idx"] = first(steps, pred_cmd=lambda c: ("BigInteger" in c) and ("createBigInteger" not in c.replace("BigInteger", "", 0) or "new BigInteger" in c or "java.math" in c or "BigInteger(" in c or c.count("BigInteger") > c.count("createBigInteger")))
    o["first_fqn_or_math_cmd_idx"] = first(steps, pred_cmd=lambda c: "java.math" in c or ("math" in c and is_search(c) and "NumberUtils" not in c and "lang3.math" not in c))
    o["first_testLang1106_cmd_idx"] = first(steps, pred_cmd=lambda c: "testLang1106" in c)
    # chain traversal (TREATMENT): observable order of exposures
    if spec["arm"] == "TREATMENT":
        f, h1c, h1o, h2o, bug = o["first_facade_body_output_idx"], o["first_resolveWholeValue_cmd_idx"], o["first_resolveWholeValue_output_idx"], o["first_decodeMagnitude_output_idx"], o["first_buggy_line_output_idx"]
        if f and h1c and h2o and f <= h1c <= h2o and (bug is None or bug >= h1c):
            o["chain_traversal"] = "traversed (facade body seen -> hop1 name searched/opened -> hop2 seen)"
        elif bug and (f is None or bug < f) and (h1c is None or bug < h1c):
            o["chain_traversal"] = "bypassed (buggy line / gold seen before facade body or any hop-name command)"
        elif f and h2o and (h1c is None) and f < h2o:
            o["chain_traversal"] = "partial (facade seen, hop2 reached without a hop1-name command)"
        else:
            o["chain_traversal"] = "unclear"
    else:
        o["chain_traversal"] = "n/a (no chain)"
    # descriptive category for the route to the FIRST gold exposure (only when evidence is clear)
    gc = o["gold_reached_by_cmd"] or ""
    cat = "other / unclear"
    if o["first_gold_exposure_idx"]:
        if is_search(gc) and any(t in gc for t in TEST_TOKENS) and not any(h in gc for h in HOPS):
            cat = "direct lexical search"
        elif is_search(gc) and any(h in gc for h in HOPS):
            cat = "call-chain traversal"
        elif opened_file(gc) and spec["gold_file"].split("/")[-1] in gc and spec["arm"] == "TREATMENT" and o["first_facade_body_output_idx"] and o["first_facade_body_output_idx"] < o["first_gold_exposure_idx"] and (o["first_resolveWholeValue_cmd_idx"] or 0) < o["first_gold_exposure_idx"] and o["first_resolveWholeValue_cmd_idx"]:
            cat = "call-chain traversal"
        elif opened_file(gc) and "NumberUtils.java" in gc and spec["arm"] == "CONTROL":
            cat = "facade-first (test names the facade; gold is the facade)"
        elif opened_file(gc) and spec["gold_file"].split("/")[-1] in gc:
            cat = "direct gold discovery (file opened)"
        if o["tests_executed"] and o["first_gold_exposure_idx"] and any(s["idx"] < o["first_gold_exposure_idx"] for s in steps if is_test(s["command"])):
            cat += " [after running the failing test]"
    o["route_category"] = cat
    return {
        "run_id": "/".join(rdir.split("/")[-2:]), "variant_id": vid, "arm": spec["arm"], "gold": gold_key,
        "status": man.get("status"), "status_reason": man.get("status_reason"), "started_at": man.get("started_at"), "completed_at": man.get("completed_at"),
        "gold_rank": gold_rank, "hit_at_1": (gold_rank == 1) if gold_rank else False, "hit_at_3": bool(gold_rank and gold_rank <= 3),
        "hit_at_5": bool(gold_rank and gold_rank <= 5), "hit_at_10": bool(gold_rank and gold_rank <= 10),
        "reciprocal_rank": (1.0 / gold_rank) if gold_rank else 0.0,
        "top10": top, "tool_call_count": (man.get("metrics") or {}).get("tool_call_count"), "search_count": (man.get("metrics") or {}).get("search_count"),
        "file_read_count": (man.get("metrics") or {}).get("file_read_count"), "test_run_count": (man.get("metrics") or {}).get("test_run_count"),
        "api_calls": ms.get("api_calls"), "cost_usd": ms.get("instance_cost"),
        "source_integrity_ok": si.get("ok"), "protocol_violation": man.get("status") == "protocol_violation",
        "prompt_version": pr.get("version"), "base_prompt_sha256": pr.get("base_prompt_sha256"), "rendered_prompt_sha256": pr.get("rendered_prompt_sha256"),
        "isolation": {k: v for k, v in (man.get("isolation") or {}).items() if k != "scan"},
        "information_sources": pis, "trajectory_path": os.path.join(rdir, "trajectory.jsonl"), "raw_trajectory_path": os.path.join(rdir, "mini-swe-agent.traj.json"),
        "observables": o, "steps": [{"idx": s["idx"], "command": s["command"][:300], "output_head": s["output"][:160].replace("\n", " | ")} for s in steps],
        "agent_reported_evidence_chain_unverified": (submit or {}).get("evidence_chain_agent_reported"),
        "hidden_reasoning_read": False,
    }

runs = []
for vid, spec in ARMS.items():
    for rdir in sorted(glob.glob(os.path.join(PR, "benchmark_runs", AGENT, vid, "run-*"))):
        runs.append(analyze_run(rdir, vid, spec))

def agg(rs):
    comp = [r for r in rs if r["status"] == "completed"]
    ranks = [r["gold_rank"] for r in comp if r["gold_rank"]]
    def rate(k): return (sum(1 for r in comp if r[k]) / len(comp)) if comp else None
    return {"n_scheduled": 5, "n_found": len(rs), "completed": len(comp), "failed_or_other": [(r["run_id"], r["status"]) for r in rs if r["status"] != "completed"],
            "timeout": sum(1 for r in rs if r["status"] == "timeout"), "protocol_violation": sum(1 for r in rs if r["protocol_violation"]),
            "acc_at_1": rate("hit_at_1"), "acc_at_3": rate("hit_at_3"), "acc_at_5": rate("hit_at_5"), "acc_at_10": rate("hit_at_10"),
            "mrr": (sum(r["reciprocal_rank"] for r in comp) / len(comp)) if comp else None,
            "gold_ranks": [r["gold_rank"] for r in rs], "mean_gold_rank": statistics.mean(ranks) if ranks else None, "median_gold_rank": statistics.median(ranks) if ranks else None,
            "tool_call_counts": [r["tool_call_count"] for r in rs], "api_calls": [r["api_calls"] for r in rs], "costs_usd": [r["cost_usd"] for r in rs],
            "total_cost_usd": sum(r["cost_usd"] or 0 for r in rs), "source_integrity_ok_all": all(r["source_integrity_ok"] for r in rs) if rs else None,
            "route_categories": {c: sum(1 for r in rs if r["observables"]["route_category"] == c) for c in sorted({r["observables"]["route_category"] for r in rs})},
            "chain_traversal": {c: sum(1 for r in rs if r["observables"]["chain_traversal"] == c) for c in sorted({r["observables"]["chain_traversal"] for r in rs})},
            "tool_calls_before_first_gold_exposure": [r["observables"]["tool_calls_before_first_gold_exposure"] for r in rs],
            "build_properties_observably_used": sum(1 for r in rs if r["observables"]["build_properties_cmd_idx"] or r["observables"]["build_properties_output_idx"])}
smoke_cost = None
for p in glob.glob(os.path.join(PR, "benchmark_runs", "_smoke", "**", "*.traj.json"), recursive=True):
    d = rj(p) or {}; smoke_cost = ((d.get("info") or {}).get("model_stats") or {}).get("instance_cost")
out = {"schema_version": "pilot-diagnostic-results/v1", "label": "DIAGNOSTIC / NON-CANONICAL / LEAKAGE-NORMALIZED-V2", "experiment_id": "diagnostic-noncanonical-v2",
       "interpretation_rule": "Not an estimate of reasoning depth and not a CONTROL-vs-TREATMENT causal effect; n=5 per arm, leakage-normalized pair (residual inherent shortcuts documented); descriptive only.",
       "per_arm": {"CONTROL": agg([r for r in runs if r["arm"] == "CONTROL"]), "TREATMENT": agg([r for r in runs if r["arm"] == "TREATMENT"])},
       "smoke_test_cost_usd": smoke_cost, "total_recorded_cost_usd": sum(r["cost_usd"] or 0 for r in runs) + (smoke_cost or 0), "runs": runs}
json.dump(out, open(os.path.join(PR, "diagnostic_v2_results.json"), "w"), indent=1)
print(json.dumps({k: v for k, v in out.items() if k != "runs"}, indent=1))
for r in runs:
    o = r["observables"]
    print(f"\n### {r['run_id']} [{r['arm']}] status={r['status']} gold_rank={r['gold_rank']} tool_calls={r['tool_call_count']} api_calls={r['api_calls']} cost={r['cost_usd']}")
    print("  route:", o["route_category"], "| chain:", o["chain_traversal"], "| gold exposure at step", o["first_gold_exposure_idx"], "via:", (o["gold_reached_by_cmd"] or "")[:140])
    for s in r["steps"]: print(f"   {s['idx']:>2}. {s['command'][:150]}")
