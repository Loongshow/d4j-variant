"""weaker-model-v1 per-model verdicts under PREREGISTRATION.md. Run after mx_metrics.py.
Usage: wm_report.py  -> analysis/model_summary.json, MODEL_CAPABILITY_COMPARISON.csv (+ printed table)
Per analysis server (= model): HA/HB/HC and pooled Acc@1 (Wilson 95%), answered rate, no-answers, the mechanical split of every
wrong run, and the gold-read-but-misranked count.
  NO_ANSWER: no submitted ranking of ten.
  SEARCH_FAILURE: the gold's fault line was never displayed.
  DISCOVERY_WITHOUT_INSPECTION: displayed but not read in full.
  ATTRIBUTION_FAILURE: displayed, read in full, still misranked.
Stage decision (pilot = n < 45):
  TOO_WEAK if answered < 70%; STEP_DOWN if Acc@1 >= 0.90; EXTEND if Acc@1 < 0.90 and at least one genuine misranking; otherwise STEP_DOWN.
Success (n >= 45): S1 pooled <= 0.80; S2 >= 2 recipes with >= 2 wrong runs; S3 answered >= 70%; S4 no-answers < half of misses;
S5 >= 1 wrong answered run that is gold exposed + read in full + misranked.
The GPT-5.6 reference row is read from mechanism-search-v1 (not re-run)."""
import json, os, sys, csv, math, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ct_lib as C
WM = C.V3; MX = WM.replace("weaker-model-v1", "mechanism-search-v1")
REC = {"M10": "HA", "M19": "HB", "M3": "HC"}
def wilson(k, n, z=1.96):
    if not n: return (None, None)
    p = k / n; d = 1 + z * z / n; c = (p + z * z / (2 * n)) / d; h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (round(c - h, 3), round(c + h, 3))
def mech_split(r):
    if not r["answered"]: return "NO_ANSWER"
    if not r["gold_exposed"]: return "SEARCH_FAILURE"
    if not r["full_gold_read"]: return "DISCOVERY_WITHOUT_INSPECTION"
    return "ATTRIBUTION_FAILURE"
def summarise(rows, label, model, server):
    inc = [r for r in rows if r["included"]]; n = len(inc); k = sum(r["acc1"] == 1 for r in inc)
    ans = [r for r in inc if r["answered"]]; wrong = [r for r in inc if r["acc1"] == 0]
    per = {}
    for mech, rec in REC.items():
        rr = [r for r in inc if r["mechanism"] == mech]; kk = sum(r["acc1"] == 1 for r in rr)
        per[rec] = {"n": len(rr), "correct": kk, "acc1": round(kk / len(rr), 3) if rr else None, "wilson95": wilson(kk, len(rr)), "wrong": len(rr) - kk}
    split = collections.Counter(mech_split(r) for r in wrong)
    grm = [r for r in wrong if r["answered"] and r["gold_exposed"] and r["full_gold_read"]]
    out = {"label": label, "model": model, "server": server, "n": n, "correct": k, "pooled_acc1": round(k / n, 3) if n else None,
           "pooled_wilson95": wilson(k, n), "per_recipe": per, "answered": len(ans), "answered_rate": round(len(ans) / n, 3) if n else None,
           "misses": len(wrong), "no_answers": split.get("NO_ANSWER", 0), "split": dict(split), "gold_read_misranked": len(grm),
           "gold_read_misranked_rate": round(len(grm) / n, 3) if n else None,
           "rank1_categories_of_wrong": dict(collections.Counter(r["rank1_category"] for r in wrong)),
           "tests_executed_rate": round(sum(bool(r["tests_executed"]) for r in inc) / n, 3) if n else None,
           "median_tool_calls": sorted(r["tool_calls"] for r in inc)[n // 2] if n else None,
           "cost_usd": round(sum(float(r["cost_usd"] or 0) for r in rows), 4)}
    if n and n < 45:
        if out["answered_rate"] < 0.70: d = "TOO_WEAK"
        elif out["pooled_acc1"] >= 0.90: d = "STEP_DOWN"
        elif any(r["answered"] and r["gold_rank"] != 1 for r in inc): d = "EXTEND_TO_45"
        else: d = "STEP_DOWN"
        out["decision"] = d
    elif n:
        crit = {"S1_pooled_le_0.80": out["pooled_acc1"] <= 0.80, "S2_two_recipes_repeated_errors": sum(v["wrong"] >= 2 for v in per.values()) >= 2,
                "S3_answered_ge_0.70": out["answered_rate"] >= 0.70, "S4_no_answers_under_half_misses": out["misses"] > 0 and out["no_answers"] < out["misses"] / 2,
                "S5_gold_read_misranked_ge_1": len(grm) >= 1}
        out["criteria"] = crit; out["decision"] = "USEFUL_REGIME" if all(crit.values()) else ("TOO_WEAK" if out["answered_rate"] < 0.70 else "STEP_DOWN")
        out["preferred_0.40_0.70"] = 0.40 <= out["pooled_acc1"] <= 0.70
    return out
servers = json.load(open(f"{WM}/models/servers.json"))
runs = [r for r in json.load(open(f"{WM}/analysis/per_run.json")) if r["instance_id"].startswith("HO-")]
models = []
ref = [r for r in json.load(open(f"{MX}/analysis/per_run.json")) if r["instance_id"].startswith("HO-")]
g56 = summarise(ref, "reference (mechanism-search-v1, not re-run)", "gpt-5.6", "mxF0"); g56.pop("decision", None); g56.pop("criteria", None)
models.append(g56)
for s, c in servers.items():
    if c.get("role") != "analysis": continue
    rr = [r for r in runs if r["server"] == s]
    if rr: models.append(summarise(rr, "weaker-model-v1", c["model"], s))
os.makedirs(f"{WM}/analysis", exist_ok=True); json.dump(models, open(f"{WM}/analysis/model_summary.json", "w"), indent=1)
cols = ["model", "server", "label", "n", "correct", "pooled_acc1", "pooled_wilson95", "HA_acc1", "HB_acc1", "HC_acc1", "answered_rate", "misses", "no_answers",
        "search_failures", "discovery_without_inspection", "attribution_failures", "gold_read_misranked", "gold_read_misranked_rate", "tests_executed_rate",
        "median_tool_calls", "cost_usd", "decision"]
with open(f"{WM}/MODEL_CAPABILITY_COMPARISON.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=cols); w.writeheader()
    for m in models:
        w.writerow({"model": m["model"], "server": m["server"], "label": m["label"], "n": m["n"], "correct": m["correct"], "pooled_acc1": m["pooled_acc1"],
                    "pooled_wilson95": m["pooled_wilson95"], "HA_acc1": m["per_recipe"]["HA"]["acc1"], "HB_acc1": m["per_recipe"]["HB"]["acc1"],
                    "HC_acc1": m["per_recipe"]["HC"]["acc1"], "answered_rate": m["answered_rate"], "misses": m["misses"], "no_answers": m["no_answers"],
                    "search_failures": m["split"].get("SEARCH_FAILURE", 0), "discovery_without_inspection": m["split"].get("DISCOVERY_WITHOUT_INSPECTION", 0),
                    "attribution_failures": m["split"].get("ATTRIBUTION_FAILURE", 0), "gold_read_misranked": m["gold_read_misranked"],
                    "gold_read_misranked_rate": m["gold_read_misranked_rate"], "tests_executed_rate": m["tests_executed_rate"],
                    "median_tool_calls": m["median_tool_calls"], "cost_usd": m["cost_usd"], "decision": m.get("decision", "reference")})
for m in models:
    pr = m["per_recipe"]
    print(f"{m['model']:13s} n={m['n']:2d} pooled={m['pooled_acc1']} {m['pooled_wilson95']} HA={pr['HA']['correct']}/{pr['HA']['n']} HB={pr['HB']['correct']}/{pr['HB']['n']} "
          f"HC={pr['HC']['correct']}/{pr['HC']['n']} answered={m['answered_rate']} split={m['split']} goldReadMis={m['gold_read_misranked']} decision={m.get('decision', 'reference')}")
