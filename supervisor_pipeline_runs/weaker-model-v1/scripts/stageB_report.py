"""Stage B cell report from the frozen per-run measures (analysis/per_run.json, produced by mx_metrics.py).
Usage: stageB_report.py [--server w55] -> analysis/stageB_cells.json and a markdown summary on stdout.
Cells: C00 1-hop plain, C01 1-hop odd, C10 5-hop+lie plain, C11 5-hop+lie odd. Primary: Acc@1 per cell pooled over bugs (Wilson 95%),
chain main effect (C10+C11 vs C00+C01), odd-hop main effect (C01+C11 vs C00+C10), interaction (C11-C01)-(C10-C00); Fisher two-sided
p for the two main effects. Mechanical split of misses: NO_ANSWER / SEARCH_FAILURE (gold never displayed) /
DISCOVERY_WITHOUT_INSPECTION (displayed, not fully read) / ATTRIBUTION_FAILURE (fully read, ranked elsewhere)."""
import json, math, os, sys, statistics
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ct_lib as C
WM = C.V3; server = sys.argv[sys.argv.index("--server") + 1] if "--server" in sys.argv else "w55"
rows = [r for r in json.load(open(f"{WM}/analysis/per_run.json")) if r.get("tier") == "STAGE_B" and r.get("included") and r.get("server") == server]
def wilson(k, n, z=1.96):
    if n == 0: return (None, None)
    p = k / n; d = 1 + z * z / n; c = p + z * z / (2 * n); h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return (round((c - h) / d, 3), round((c + h) / d, 3))
def fisher(a, b, c, d):   # two-sided, table [[a,b],[c,d]]
    n = a + b + c + d; r1, c1 = a + b, a + c
    def pr(x): return math.comb(r1, x) * math.comb(n - r1, c1 - x) / math.comb(n, c1)
    p0 = pr(a); return float('%.3g' % sum(pr(x) for x in range(max(0, c1 - (n - r1)), min(r1, c1) + 1) if pr(x) <= p0 + 1e-12))
def split(r):
    if not r.get("answered"): return "NO_ANSWER"
    if r.get("acc1"): return "CORRECT"
    if not r.get("gold_exposed"): return "SEARCH_FAILURE"
    if not r.get("full_gold_read"): return "DISCOVERY_WITHOUT_INSPECTION"
    return "ATTRIBUTION_FAILURE"
cells = {}
BUGS = sorted({r["instance_id"].split("-")[1] for r in rows})
for r in rows:
    iid = r["instance_id"]; bug, cell = iid.split("-")[1], iid.split("-")[2]
    cells.setdefault(cell, {}).setdefault(bug, []).append(r)
out = {"server": server, "n_runs": len(rows), "cells": {}, "effects": {}}
lines = ["| Cell | n | answered | Acc@1 | Wilson 95% | per bug (" + "/".join(BUGS) + ") | median gold rank (misses) | median tool calls | misses: NA/SF/DWI/AF |", "|---|---|---|---|---|---|---|---|---|"]
tot = {}
for cell in ["C00", "C01", "C10", "C11"]:
    runs = [r for b in cells.get(cell, {}).values() for r in b]; n = len(runs); k = sum(1 for r in runs if r.get("acc1"))
    per_bug = "/".join(f"{sum(1 for r in cells.get(cell, {}).get(b, []) if r.get('acc1'))}:{len(cells.get(cell, {}).get(b, []))}" for b in BUGS)
    sp = {s: sum(1 for r in runs if split(r) == s) for s in ["NO_ANSWER", "SEARCH_FAILURE", "DISCOVERY_WITHOUT_INSPECTION", "ATTRIBUTION_FAILURE"]}
    ranks = [r["gold_rank"] for r in runs if r.get("answered") and not r.get("acc1") and isinstance(r.get("gold_rank"), (int, float))]
    tc = [r["tool_calls"] for r in runs if isinstance(r.get("tool_calls"), (int, float))]
    tot[cell] = (k, n)
    out["cells"][cell] = {"n": n, "answered": sum(1 for r in runs if r.get("answered")), "acc1": k, "rate": round(k / n, 3) if n else None, "wilson": wilson(k, n), "per_bug": per_bug,
                          "split": sp, "median_gold_rank_misses": statistics.median(ranks) if ranks else None, "median_tool_calls": statistics.median(tc) if tc else None,
                          "runs": [{"iid": r["instance_id"], "run": r["run"], "acc1": r.get("acc1"), "gold_rank": r.get("gold_rank"), "rank1": r.get("rank1"), "rank1_category": r.get("rank1_category"), "split": split(r)} for r in runs]}
    lines.append(f"| {cell} | {n} | {out['cells'][cell]['answered']} | {k}/{n} | {wilson(k, n)} | {per_bug} | {out['cells'][cell]['median_gold_rank_misses']} | {out['cells'][cell]['median_tool_calls']} | {sp['NO_ANSWER']}/{sp['SEARCH_FAILURE']}/{sp['DISCOVERY_WITHOUT_INSPECTION']}/{sp['ATTRIBUTION_FAILURE']} |")
def pool(*cs): return sum(tot[c][0] for c in cs if c in tot), sum(tot[c][1] for c in cs if c in tot)
ch1, ch0 = pool("C10", "C11"), pool("C00", "C01"); od1, od0 = pool("C01", "C11"), pool("C00", "C10")
rate = lambda kn: round(kn[0] / kn[1], 3) if kn[1] else None
out["effects"] = {"chain": {"with": ch1, "without": ch0, "diff": (rate(ch1) or 0) - (rate(ch0) or 0) if ch1[1] and ch0[1] else None, "fisher_p": fisher(ch1[0], ch1[1] - ch1[0], ch0[0], ch0[1] - ch0[0]) if ch1[1] and ch0[1] else None},
                  "odd": {"with": od1, "without": od0, "diff": (rate(od1) or 0) - (rate(od0) or 0) if od1[1] and od0[1] else None, "fisher_p": fisher(od1[0], od1[1] - od1[0], od0[0], od0[1] - od0[0]) if od1[1] and od0[1] else None}}
if all(c in tot and tot[c][1] for c in ["C00", "C01", "C10", "C11"]):
    out["effects"]["interaction"] = round((rate(tot["C11"]) - rate(tot["C01"])) - (rate(tot["C10"]) - rate(tot["C00"])), 3)
# gpt-5.5 (w55) keeps its original output path; any other server writes a separate file so the gpt-5.5 record is never overwritten
json.dump(out, open(f"{WM}/analysis/stageB_cells.json" if server == "w55" else f"{WM}/analysis/stageB_cells_{server}.json", "w"), indent=1)
print("\n".join(lines)); print("\neffects:", json.dumps(out["effects"]))
