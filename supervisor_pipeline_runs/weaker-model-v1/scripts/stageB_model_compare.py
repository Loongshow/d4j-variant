"""Stage B cross-model comparison: gpt-5.5 (w55) against GPT-5.6 (w56) on the identical 12 variants.
Reads analysis/per_run.json (frozen measures; run scripts/mx_metrics.py first), stageB-gpt56/timeline_w5{5,6}_runs.json and each
run's ranking.json (facade rank). Writes stageB-gpt56/GPT55_VS_GPT56_STAGE_B.csv (Acc@1 by cell, project, pooled arm, with Wilson 95%
intervals and Fisher two-sided p), stageB-gpt56/GPT55_VS_GPT56_PROCESS.csv (process measures by model x cell) and
stageB-gpt56/model_compare.json. Descriptive; two models do not support causal capability claims."""
import json, math, os, sys, csv, statistics as st
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); OUT = f"{ROOT}/stageB-gpt56"
K = json.load(open(f"{ROOT}/review/VARIANT_KEY.json")); SV = json.load(open(f"{ROOT}/models/servers.json"))
PR = [r for r in json.load(open(f"{ROOT}/analysis/per_run.json")) if r.get("tier") == "STAGE_B" and r.get("included") and r.get("server") in ("w55", "w56")]
TL = {}
for s in ("w55", "w56"):
    p = f"{OUT}/timeline_{s}_runs.json"
    if os.path.exists(p): TL.update({(s, r["run_id"]): r for r in json.load(open(p))})
PROJ = {"B1": "Lang", "B3": "Chart", "B4": "Math"}; CELLS = ["C00", "C01", "C10", "C11"]; MODEL = {"w55": "gpt-5.5", "w56": "GPT-5.6"}
def wilson(k, n, z=1.96):
    if not n: return (None, None)
    p = k / n; d = 1 + z * z / n; c = p + z * z / (2 * n); h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)); return (round((c - h) / d, 3), round((c + h) / d, 3))
def fisher(a, b, c, d):
    n = a + b + c + d; r1, c1 = a + b, a + c
    if n == 0: return None
    def pr(x): return math.comb(r1, x) * math.comb(n - r1, c1 - x) / math.comb(n, c1)
    p0 = pr(a); return float("%.3g" % sum(pr(x) for x in range(max(0, c1 - (n - r1)), min(r1, c1) + 1) if pr(x) <= p0 * (1 + 1e-9)))
def facade_rank(r):
    agent = SV[r["server"]]["agent_id"]; rd = f"{ROOT}/models/{r['server']}/benchmark_runs/{agent}/{r['variant_id']}/{r['run']}"
    try: rk = json.load(open(f"{rd}/ranking.json"))
    except Exception: return None
    preds = ((rk.get("structured_submission") or {}).get("predictions") or rk.get("predictions") or []); keys = [f"{p.get('class')}::{p.get('method')}" for p in preds]
    ents = K[r["variant_id"]].get("entry_points") or []
    return min([keys.index(e) + 1 for e in ents if e in keys] or [None]) if keys else None
for r in PR:
    bug, cell = r["instance_id"].split("-")[1], r["instance_id"].split("-")[2]; r["bug"], r["cell"], r["project_name"] = bug, cell, PROJ[bug]
    r["facade_rank"] = facade_rank(r); t = TL.get((r["server"], f"{r['variant_id']}/{r['run']}")) or {}
    r["t_gold_any"] = t.get("t_gold_any"); r["t_fault_line"] = t.get("t_fault_line"); r["calls_after_gold"] = t.get("calls_after_gold"); r["latency_median_s"] = t.get("latency_median_s")
def sel(server, cells=None, bug=None): return [r for r in PR if r["server"] == server and (cells is None or r["cell"] in cells) and (bug is None or r["bug"] == bug)]
def acc(rs): return sum(r["acc1"] for r in rs), len(rs)
scopes = [(f"cell {c}", [c], None) for c in CELLS] + [(f"{PROJ[b]} {c}", [c], b) for b in ("B1", "B4", "B3") for c in CELLS] + \
         [(f"{PROJ[b]} 1-hop", ["C00", "C01"], b) for b in ("B1", "B4", "B3")] + [(f"{PROJ[b]} 5-hop+lie", ["C10", "C11"], b) for b in ("B1", "B4", "B3")] + \
         [("pooled 1-hop (C00+C01)", ["C00", "C01"], None), ("pooled 5-hop+lie (C10+C11)", ["C10", "C11"], None), ("pooled odd (C01+C11)", ["C01", "C11"], None), ("pooled plain (C00+C10)", ["C00", "C10"], None), ("all", CELLS, None)]
rows = []
for name, cells, bug in scopes:
    k5, n5 = acc(sel("w55", cells, bug)); k6, n6 = acc(sel("w56", cells, bug))
    rows.append({"scope": name, "gpt55_k": k5, "gpt55_n": n5, "gpt55_acc1": round(k5 / n5, 3) if n5 else None, "gpt55_wilson95": wilson(k5, n5),
                 "gpt56_k": k6, "gpt56_n": n6, "gpt56_acc1": round(k6 / n6, 3) if n6 else None, "gpt56_wilson95": wilson(k6, n6),
                 "difference_gpt56_minus_gpt55": round(k6 / n6 - k5 / n5, 3) if (n5 and n6) else None, "fisher_p_two_sided": fisher(k6, n6 - k6, k5, n5 - k5) if (n5 and n6) else None})
with open(f"{OUT}/GPT55_VS_GPT56_STAGE_B.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); [w.writerow({**r, "gpt55_wilson95": "-".join(map(str, r["gpt55_wilson95"])), "gpt56_wilson95": "-".join(map(str, r["gpt56_wilson95"]))}) for r in rows]
# within-model contrasts (preregistered P1-P3 and secondaries)
def contrast(server, a, b):
    ka, na = acc(sel(server, a)); kb, nb = acc(sel(server, b))
    return {"a": a, "b": b, "a_k": ka, "a_n": na, "b_k": kb, "b_n": nb, "diff_b_minus_a": round(kb / nb - ka / na, 3) if (na and nb) else None, "fisher_p": fisher(kb, nb - kb, ka, na - ka) if (na and nb) else None}
contr = {MODEL[s]: {"P1 C00 vs C10": contrast(s, ["C00"], ["C10"]), "P2 C01 vs C11": contrast(s, ["C01"], ["C11"]), "P3 1-hop vs 5-hop+lie": contrast(s, ["C00", "C01"], ["C10", "C11"]),
                    "S1 C00 vs C01": contrast(s, ["C00"], ["C01"]), "S2 C10 vs C11": contrast(s, ["C10"], ["C11"])} for s in ("w55", "w56")}
inter = {}
for s in ("w55", "w56"):
    rate = lambda c: (acc(sel(s, [c]))[0] / acc(sel(s, [c]))[1]) if acc(sel(s, [c]))[1] else None
    inter[MODEL[s]] = {c: rate(c) for c in CELLS}
# model x cell pattern: change in the chain contrast between models (difference of differences), descriptive
dod = None
if all(inter[m][c] is not None for m in inter for c in CELLS):
    chain = lambda m: ((inter[m]["C10"] + inter[m]["C11"]) - (inter[m]["C00"] + inter[m]["C01"])) / 2
    dod = round(chain("GPT-5.6") - chain("gpt-5.5"), 3)
# process measures by model x cell
def med(xs): xs = [x for x in xs if x is not None]; return round(st.median(xs), 1) if xs else None
proc = []
for s in ("w55", "w56"):
    for c in CELLS + ["1-hop", "5-hop+lie"]:
        cells = {"1-hop": ["C00", "C01"], "5-hop+lie": ["C10", "C11"]}.get(c, [c]); rs = sel(s, cells); n = len(rs)
        if not n: continue
        miss = [r for r in rs if not r["acc1"]]
        proc.append({"model": MODEL[s], "cell": c, "n": n, "acc1": round(sum(r["acc1"] for r in rs) / n, 3), "mrr": round(st.mean(r["rr"] for r in rs), 3),
                     "median_gold_rank": med([r["gold_rank"] for r in rs]), "gold_exposed": sum(1 for r in rs if r["gold_exposed"]), "full_gold_read": sum(1 for r in rs if r["full_gold_read"]),
                     "gold_exposed_misranked": sum(1 for r in rs if r["gold_exposed_misranked"]), "facade_rank1": sum(1 for r in rs if r["facade_rank"] == 1),
                     "facade_rank1_among_misses": sum(1 for r in miss if r["facade_rank"] == 1), "misses": len(miss),
                     "median_tool_calls": med([r["tool_calls"] for r in rs]), "median_tests": med([r["test_executions"] for r in rs]), "median_reasoning_tokens": med([r["reasoning_tokens"] for r in rs]),
                     "median_first_gold_s": med([r["t_gold_any"] for r in rs]), "median_wall_s": med([r["wall_time_s"] for r in rs]), "median_cost_usd": round(st.median([r["cost_usd"] for r in rs if r.get("cost_usd") is not None]), 3),
                     "evidence_displayed": sum(1 for r in rs if r.get("evidence_displayed"))})
with open(f"{OUT}/GPT55_VS_GPT56_PROCESS.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(proc[0])); w.writeheader(); [w.writerow(p) for p in proc]
json.dump({"acc_rows": rows, "contrasts": contr, "cell_rates": inter, "chain_contrast_change_gpt56_minus_gpt55": dod, "process": proc,
           "runs": [{k: r[k] for k in ("server", "variant_id", "run", "instance_id", "bug", "cell", "acc1", "gold_rank", "rank1", "rank1_category", "facade_rank", "gold_exposed", "full_gold_read", "tool_calls", "reasoning_tokens", "test_executions", "t_gold_any", "wall_time_s", "cost_usd")} for r in PR]},
          open(f"{OUT}/model_compare.json", "w"), indent=1)
print(f"{'scope':30s} {'gpt-5.5':>12s} {'GPT-5.6':>12s} {'diff':>7s} {'p':>8s}")
for r in rows: print(f"{r['scope']:30s} {r['gpt55_k']:>4}/{r['gpt55_n']:<3} {str(r['gpt55_acc1']):>5s} {r['gpt56_k']:>4}/{r['gpt56_n']:<3} {str(r['gpt56_acc1']):>5s} {str(r['difference_gpt56_minus_gpt55']):>7s} {str(r['fisher_p_two_sided']):>8s}")
print("contrasts:", json.dumps(contr["GPT-5.6"]) if "GPT-5.6" in contr else "")
print("chain-contrast change (GPT-5.6 minus gpt-5.5):", dod)
