"""Held-out (Phase 5) verdicts per mechanism from the frozen per-run measures. Run after mx_metrics.py.
Usage: mx_heldout_report.py  -> analysis/heldout/summary.json (+ printed table)
STABLE = all six PREREGISTRATION criteria; SUPPORTED / PARTIALLY_SUPPORTED / NOT_SUPPORTED as operationalised in AMENDMENTS X8
(fixed 2026-10-11T04:26Z, before any held-out run):
  C1 pooled held-out Acc@1 <= 0.60          C2 >= 2 of 3 instances with Acc@1 <= 0.60
  C3 no-answers < half of the misses (infrastructure attempts are excluded+replaced by the driver and reported separately)
  C4 >= half of the wrong answered runs exposed the gold
  C5 no STOP_CONTAMINATION / STOP_INTEGRITY / STOP_SCAN_FAILED record on the mechanism's held-out runs; every instance READY
  C6 every instance's independent audit verdict is CONFIRMED
  PARTIALLY_SUPPORTED = not STABLE and (pooled <= 0.80 or some instance Acc@1 <= 0.60); NOT_SUPPORTED otherwise."""
import json, os, sys, glob, math, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ct_lib as C
MX = C.V3
RECIPE = {"M10": "HA entry-point ranking", "M19": "HB sink blame", "M3": "HC convention attribution"}
def wilson(k, n, z=1.96):
    if not n: return (None, None)
    p = k / n; d = 1 + z * z / n; c = (p + z * z / (2 * n)) / d; h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (round(c - h, 3), round(c + h, 3))
key = json.load(open(f"{MX}/review/VARIANT_KEY.json"))
ho = {v: k for v, k in key.items() if k.get("tier") == "HELDOUT"}
runs = [r for r in json.load(open(f"{MX}/analysis/per_run.json")) if r["variant_id"] in ho]
last = {}
for l in open(f"{MX}/diagnostic/block_mxF0.jsonl"):
    r = json.loads(l); last[r["run"]] = r
recs = {run: r for run, r in last.items() if run.split("/")[0] in ho}
out = {}
for mech in sorted({k["mechanism"] for k in ho.values()}):
    vids = sorted(v for v, k in ho.items() if k["mechanism"] == mech)
    inst = []
    for v in vids:
        rr = [r for r in runs if r["variant_id"] == v and r["included"]]
        iid = ho[v]["instance_id"]
        val = json.load(open(f"{MX}/instances/{iid}/validation.json")).get("overall")
        aud = json.load(open(f"{MX}/instances/{iid}/audit.json")).get("verdict")
        stops = [f"{run}:{r['verdict']}" for run, r in recs.items() if run.startswith(v) and r["verdict"] in ("STOP_CONTAMINATION", "STOP_INTEGRITY", "STOP_SCAN_FAILED")]
        infra = [run for run, r in recs.items() if run.startswith(v) and r["verdict"] == "infrastructure"]
        n = len(rr); k = sum(r["acc1"] == 1 for r in rr)
        inst.append({"iid": iid, "variant_id": v, "project": ho[v]["project"], "n": n, "correct": k, "acc1": round(k / n, 3) if n else None,
                     "gold_ranks": [r["gold_rank"] for r in rr], "rank1_categories": [r["rank1_category"] for r in rr],
                     "rank1": [r["rank1"] for r in rr], "gold_exposed": sum(bool(r["gold_exposed"]) for r in rr),
                     "full_gold_read": sum(bool(r["full_gold_read"]) for r in rr),
                     "wrong_answered": sum(r["answered"] and r["acc1"] == 0 for r in rr),
                     "wrong_answered_exposed": sum(r["answered"] and r["acc1"] == 0 and bool(r["gold_exposed"]) for r in rr),
                     "no_answer": sum(r["rank1_category"] == "NO_ANSWER" for r in rr), "infrastructure_attempts": len(infra),
                     "stops": stops, "validation": val, "audit": aud, "cost_usd": round(sum(float(r["cost_usd"] or 0) for r in rr), 4)})
    N = sum(i["n"] for i in inst); K = sum(i["correct"] for i in inst); pooled = round(K / N, 3) if N else None
    misses = N - K; na = sum(i["no_answer"] for i in inst); wa = sum(i["wrong_answered"] for i in inst); wae = sum(i["wrong_answered_exposed"] for i in inst)
    crit = {"C1_pooled_le_0.60": pooled is not None and pooled <= 0.60,
            "C2_two_of_three_le_0.60": sum(i["acc1"] is not None and i["acc1"] <= 0.60 for i in inst) >= 2,
            "C3_no_answers_under_half_of_misses": misses > 0 and na < misses / 2,
            "C4_half_wrong_answered_exposed_gold": wa > 0 and wae >= wa / 2,
            "C5_scanner_clean_and_valid": all(not i["stops"] and i["validation"] == "READY" for i in inst),
            "C6_audits_confirmed": all(i["audit"] == "CONFIRMED" for i in inst)}
    stable = all(crit.values())
    partial = (not stable) and pooled is not None and (pooled <= 0.80 or any(i["acc1"] is not None and i["acc1"] <= 0.60 for i in inst))
    out[mech] = {"recipe": RECIPE.get(mech, mech), "instances": inst, "n": N, "correct": K, "pooled_acc1": pooled, "pooled_acc1_wilson95": wilson(K, N),
                 "misses": misses, "no_answers": na, "wrong_answered": wa, "wrong_answered_exposed_gold": wae, "criteria": crit, "STABLE": stable,
                 "preferred_pooled_le_0.50": pooled is not None and pooled <= 0.50,
                 "label": "SUPPORTED" if stable else ("PARTIALLY_SUPPORTED" if partial else "NOT_SUPPORTED")}
os.makedirs(f"{MX}/analysis/heldout", exist_ok=True)
json.dump(out, open(f"{MX}/analysis/heldout/summary.json", "w"), indent=1)
for m, o in out.items():
    print(f"{m:4s} {o['recipe']:28s} n={o['n']:2d} pooled Acc@1={o['pooled_acc1']} CI={o['pooled_acc1_wilson95']} label={o['label']}")
    for i in o["instances"]: print(f"     {i['iid']:22s} n={i['n']} Acc@1={i['acc1']} ranks={i['gold_ranks']} cats={i['rank1_categories']}")
    print("     " + " ".join(f"{c}={'Y' if v else 'n'}" for c, v in o["criteria"].items()))
