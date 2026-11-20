"""Stage B GPT-5.6 replication: extra process measures by model x arm (and GPT-5.6 C11 correct vs wrong), from the frozen per-run measures
(analysis/per_run.json) and the per-step timelines (stageB-gpt56/timeline_w5{5,6}_runs.json). Writes stageB-gpt56/process_extra.json."""
import json, os, statistics as st
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
PR = [r for r in json.load(open(f"{ROOT}/analysis/per_run.json")) if r.get("tier") == "STAGE_B" and r.get("included") and r["server"] in ("w55", "w56")]
TL = {}
for s in ("w55", "w56"):
    for r in json.load(open(f"{ROOT}/stageB-gpt56/timeline_{s}_runs.json")): TL[(s, r["run_id"])] = r
M = {"w55": "gpt-5.5", "w56": "GPT-5.6"}; cell = lambda r: r["instance_id"].split("-")[-1]
def med(xs):
    xs = [x for x in xs if x is not None]; return round(st.median(xs), 1) if xs else None
def summ(rows, s):
    t = [TL.get((s, f"{r['variant_id']}/{r['run']}")) or {} for r in rows]
    return {"n": len(rows), "acc1": sum(1 for r in rows if r["acc1"]),
            "median_tool_calls": med([r["tool_calls"] for r in rows]), "median_searches": med([r["searches"] for r in rows]), "median_file_reads": med([r["file_reads"] for r in rows]),
            "median_lines_read": med([r["lines_read"] for r in rows]), "independent_probe_runs": sum(1 for r in rows if r["independent_probe_executed"]),
            "failure_values_seen_runs": sum(1 for r in rows if r["failure_values_seen"]), "median_test_executions": med([r["test_executions"] for r in rows]),
            "median_reasoning_tokens": med([r["reasoning_tokens"] for r in rows]), "median_output_tokens": med([r["output_tokens"] for r in rows]),
            "median_first_gold_step": med([x.get("calls_before_gold") for x in t]), "median_first_gold_s": med([x.get("t_gold_any") for x in t]),
            "median_calls_after_gold": med([x.get("calls_after_gold") for x in t]), "median_methods_after_gold": med([x.get("methods_inspected_after_gold") for x in t]),
            "median_wall_s": med([x.get("wall_s") for x in t]), "median_cost_usd": round(st.median([r["cost_usd"] for r in rows]), 3)}
out = {}
for s in ("w55", "w56"):
    rs = [r for r in PR if r["server"] == s]
    for arm, cells in (("1-hop", ("C00", "C01")), ("5-hop+lie", ("C10", "C11")), ("C10", ("C10",)), ("C11", ("C11",))):
        out[f"{M[s]} {arm}"] = summ([r for r in rs if cell(r) in cells], s)
    out[f"{M[s]} 5-hop+lie correct"] = summ([r for r in rs if cell(r) in ("C10", "C11") and r["acc1"]], s)
    out[f"{M[s]} 5-hop+lie wrong"] = summ([r for r in rs if cell(r) in ("C10", "C11") and not r["acc1"]], s)
c11 = [r for r in PR if r["server"] == "w56" and cell(r) == "C11"]
out["GPT-5.6 C11 Lang+Chart correct"] = summ([r for r in c11 if r["acc1"] and r["project"] in ("Lang", "Chart")], "w56")
out["GPT-5.6 C11 Lang+Chart wrong"] = summ([r for r in c11 if not r["acc1"]], "w56")
json.dump(out, open(f"{ROOT}/stageB-gpt56/process_extra.json", "w"), indent=1)
keys = list(next(iter(out.values())).keys())
print("scope".ljust(34), " ".join(k.replace("median_", "")[:11].rjust(11) for k in keys))
for k, v in out.items(): print(k.ljust(34), " ".join(str(v[x]).rjust(11) for x in keys))
