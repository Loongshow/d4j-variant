"""Stage A (AMENDMENTS W5) per-instance comparison: gpt-5.5 on the re-hosted frozen breakers vs the GPT-5.6 reference.
Run after mx_metrics.py. Usage: wm_stageA_report.py -> analysis/stageA_by_instance.json (+ printed table)
Reference sources (never re-run): RH-* instances -> mechanism-search-v1/analysis/per_run.json (S1, 3 runs each);
FZ-CHART-PIE-* and FZ-CLOSURE-* -> mechanism-search-v1/mining/run_data.json (frozen earlier blocks, GPT-5.6 behavioural runs).
For every wrong gpt-5.5 run: mechanical split NO_ANSWER / SEARCH_FAILURE / DISCOVERY_WITHOUT_INSPECTION / ATTRIBUTION_FAILURE."""
import json, os, sys, math, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ct_lib as C
WM = C.V3; MX = WM.replace("weaker-model-v1", "mechanism-search-v1")
def wilson(k, n, z=1.96):
    if not n: return None
    p = k / n; d = 1 + z * z / n; c = (p + z * z / (2 * n)) / d; h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (round(c - h, 3), round(c + h, 3))
def split(r):
    if not r["answered"]: return "NO_ANSWER"
    if not r["gold_exposed"]: return "SEARCH_FAILURE"
    if not r["full_gold_read"]: return "DISCOVERY_WITHOUT_INSPECTION"
    return "ATTRIBUTION_FAILURE"
SRC = {"FZ-CHART-PIE-TREATMENT-03": "CHART-PIE-TREATMENT-03", "FZ-CHART-PIE-CONTROL-03": "CHART-PIE-CONTROL-03",
       "FZ-CLOSURE-12-OWN-001": "CLOSURE-12-OWN-001", "FZ-CLOSURE-131-OWN-001": "CLOSURE-131-OWN-001"}
ref = collections.defaultdict(list)
for r in json.load(open(f"{MX}/analysis/per_run.json")):
    if r["included"] and r["instance_id"].startswith("RH-"): ref[r["instance_id"]].append(r["acc1"])
for r in json.load(open(f"{MX}/mining/run_data.json")):
    if "gpt" in str(r["model"]).lower() and r["status_kind"] == "behavioural" and r.get("acc1") is not None and r["variant"] in SRC.values():
        ref[[k for k, v in SRC.items() if v == r["variant"]][0]].append(r["acc1"])
key = json.load(open(f"{WM}/review/VARIANT_KEY.json"))
runs = [r for r in json.load(open(f"{WM}/analysis/per_run.json")) if r["included"] and r["instance_id"] in ref]
by = collections.defaultdict(list)
for r in runs: by[(r["server"], r["instance_id"])].append(r)
out = []
for (sv, iid), rs in sorted(by.items()):
    n = len(rs); k = sum(r["acc1"] == 1 for r in rs); wrong = [r for r in rs if r["acc1"] == 0]
    rk = ref[iid]; mech = next(v["mechanism"] for v in key.values() if v["instance_id"] == iid)
    out.append({"server": sv, "instance": iid, "mechanism": mech, "n": n, "correct": k, "acc1": round(k / n, 3), "wilson95": wilson(k, n),
                "gold_ranks": [r["gold_rank"] for r in rs], "rank1_categories": [r["rank1_category"] for r in rs],
                "top1_wrong": [r["rank1"].split(".")[-1] if r.get("rank1") else None for r in wrong],
                "split": dict(collections.Counter(split(r) for r in wrong)), "gold_read_misranked": sum(1 for r in wrong if r["answered"] and r["gold_exposed"] and r["full_gold_read"]),
                "tests_executed": sum(bool(r["tests_executed"]) for r in rs), "median_tool_calls": sorted(r["tool_calls"] for r in rs)[n // 2],
                "cost_usd": round(sum(float(r["cost_usd"] or 0) for r in rs), 3),
                "gpt56_reference": {"n": len(rk), "acc1": round(sum(rk) / len(rk), 3) if rk else None}})
json.dump(out, open(f"{WM}/analysis/stageA_by_instance.json", "w"), indent=1)
print(f"{'instance':28s}{'mech':6s}{'gpt-5.5':>10s}{'ref 5.6':>10s}  ranks / split")
for o in out:
    print(f"{o['instance']:28s}{o['mechanism']:6s}{str(o['correct'])+'/'+str(o['n']):>10s}{str(o['gpt56_reference']['acc1']):>10s}  {o['gold_ranks']} {o['split']} goldReadMis={o['gold_read_misranked']}")
N = sum(o["n"] for o in out); K = sum(o["correct"] for o in out)
if N: print(f"pooled gpt-5.5 on this set: {K}/{N} = {K/N:.3f} {wilson(K, N)}")
