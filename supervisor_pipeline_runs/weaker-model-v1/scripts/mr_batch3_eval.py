"""Main run, batch 3: the pre-registered prediction (main-run/BATCH3_PREREGISTRATION.md) and the W31 secondary subsets.
n = ACCEPTED batch-3 instances (main-run/analysis/batch3_dispositions.json) whose MAIN_RUN_RESULTS.csv row has batch = batch3 and
valid_runs = 5; s = share of n with >= 1 shifted run.  Reading: n < 5 -> INCONCLUSIVE; s >= 4/5 -> SUPPORTED; s <= 2/3 -> NOT SUPPORTED;
otherwise INCONCLUSIVE.  Secondary (W31, fixed before any batch-3 outcome was read): (a) majority of 3 raters NO_TRACE (drops Lang-46,
Lang-65), (b) all 3 raters NO_TRACE (also drops Lang-44, Lang-49), from main-run/analysis/batch3_trace_robustness.json.
Also reports built-but-not-run and partially run instances. Read-only except main-run/analysis/batch3_prediction.json."""
import csv, json, os
from fractions import Fraction as F
import sys
HERE = os.path.dirname(os.path.abspath(__file__)); WM = os.path.dirname(HERE); MR = f"{WM}/main-run"
B = sys.argv[sys.argv.index("--batch") + 1] if "--batch" in sys.argv else "batch3"   # batch 4 (W34): same rule, read as a replication
disp = json.load(open(f"{MR}/analysis/{B}_dispositions.json"))["dispositions"]
RES_FILE = f"{MR}/MAIN_RUN_C10F_RESULTS.csv" if B == "batch6" else f"{MR}/MAIN_RUN_C10I_RESULTS.csv" if B in ("batch8", "batch9") else f"{MR}/MAIN_RUN_RESULTS.csv"   # batch 6 (W48/W51): C10f rows are written by mr2_report.py; batch 8 (W56): C10i rows by mr3_report.py
res = {(r["instance"] + "__i" if B in ("batch8", "batch9") else r["instance"]): r for r in csv.DictReader(open(RES_FILE)) if r["batch"] == B}   # batch 8: disposition keys are the task keys <key>__i
rob = {r["instance"]: r for r in json.load(open(f"{MR}/analysis/{B}_trace_robustness.json"))["rows"]} if os.path.exists(f"{MR}/analysis/{B}_trace_robustness.json") else {}
accepted = sorted((k for k, v in disp.items() if v["status"] == "ACCEPTED"), key=lambda k: disp[k]["pool_rank"])
in_n = [k for k in accepted if k in res and int(res[k]["valid_runs"]) == 5]
not_run = [k for k in accepted if k not in res]
partial = [k for k in accepted if k in res and int(res[k]["valid_runs"]) < 5]

def reading(keys):
    n = len(keys); succ = [k for k in keys if res[k]["instance_success"] == "True"]
    sh = sum(int(res[k]["shifted_runs"]) for k in keys); ans = sum(int(res[k]["answered"]) for k in keys)
    yes, no = ("REPLICATES", "DOES NOT REPLICATE") if B in ("batch4", "batch5", "batch6", "batch8", "batch9") else ("SUPPORTED", "NOT SUPPORTED")   # batch 5 (W42): replication reading too   # batch 4: secondary replication reading (W34)
    if n < 5: r = "INCONCLUSIVE (n < 5)"
    elif F(len(succ), n) >= F(4, 5): r = yes
    elif F(len(succ), n) <= F(2, 3): r = no
    else: r = "INCONCLUSIVE"
    return {"n": n, "with_shift": len(succ), "s": round(len(succ) / n, 4) if n else None, "reading": r,
            "shifted_over_answered_runs": f"{sh}/{ans}", "instances_without_shift": [k for k in keys if k not in succ]}

maj = [k for k in in_n if k in rob and (1 + sum(v == "NO_TRACE" for v in rob[k]["extra_raters"])) >= 2]
una = [k for k in in_n if k in rob and all(v == "NO_TRACE" for v in rob[k]["extra_raters"])]
out = {"primary": reading(in_n), "secondary_a_majority_of_3_no_trace": reading(maj), "secondary_b_all_3_no_trace": reading(una),
       **({"per_project": {p: reading([k for k in in_n if k.rsplit("-", 1)[0] == p]) for p in sorted({k.rsplit("-", 1)[0] for k in in_n})}} if B != "batch3" else {}),   # batch 4 on (W34); batch-3 output stays byte-identical
       **({"c10f_primary_distinct_facade": reading([k for k in in_n if not disp[k].get("facade_reuse_effective")]),   # batch 6 (BATCH6_PREREGISTRATION.md section 5): primary over distinct facades,
          "c10f_secondary_recorded_reuse": reading([k for k in in_n if disp[k].get("facade_reuse_effective")]),     # secondary all / reuse / per host regime; batch-3-5 output stays byte-identical
          "c10f_per_host_regime": {m: reading([k for k in in_n if disp[k].get("host_mode") == m]) for m in sorted({str(disp[k].get("host_mode")) for k in in_n})}} if B == "batch6" else {}),
       **({"c10i_primary_distinct_facade": reading([k for k in in_n if not disp[k].get("facade_reuse_effective")]),   # batch 8 (BATCH8_PREREGISTRATION.md section 4): primary over distinct facades,
          "c10i_secondary_recorded_reuse": reading([k for k in in_n if disp[k].get("facade_reuse_effective")]),     # secondary all / reuse / per host regime / per facade variant
          "c10i_per_host_regime": {m: reading([k for k in in_n if disp[k].get("host_mode") == m]) for m in sorted({str(disp[k].get("host_mode")) for k in in_n})},
          "c10i_per_facade_variant": {v: reading([k for k in in_n if str(disp[k].get("facade_variant")) == v]) for v in sorted({str(disp[k].get("facade_variant")) for k in in_n})}} if B in ("batch8", "batch9") else {}),
       "built_not_run": not_run, "partially_run": partial,
       "per_instance": [{"instance": k, "pool_rank": disp[k]["pool_rank"], "shifted_over_answered": res[k]["shifted_over_answered"],
                         "gold_ranks": res[k]["gold_ranks"], "failure_modes": res[k]["failure_modes"], "redesigned": disp[k]["redesigned"],
                         "extra_raters": rob.get(k, {}).get("extra_raters"),
                         **({"host_mode": disp[k].get("host_mode"), "host_lines": disp[k].get("host_lines_builder") or disp[k].get("host_lines_task"),
                             "facade_reuse_effective": disp[k].get("facade_reuse_effective")} if B == "batch6" else {}),
                         **({"host_mode": disp[k].get("host_mode"), "host_lines": disp[k].get("host_lines_builder") or disp[k].get("host_lines_task"),
                             "facade_variant": disp[k].get("facade_variant"), "facade": disp[k].get("facade"),
                             "facade_reuse_effective": disp[k].get("facade_reuse_effective")} if B in ("batch8", "batch9") else {})} for k in in_n],   # batch 6: host-size covariates (W48); batch 8: C10i covariates (W56)
       "thresholds": ("n<5 INCONCLUSIVE; s>=4/5 REPLICATES; s<=2/3 DOES NOT REPLICATE; else INCONCLUSIVE (BATCH4_PREREGISTRATION.md)" if B == "batch4" else "n<5 INCONCLUSIVE; s>=4/5 REPLICATES; s<=2/3 DOES NOT REPLICATE; else INCONCLUSIVE (BATCH5_PREREGISTRATION.md)" if B == "batch5" else
                      "n<5 INCONCLUSIVE; s>=4/5 REPLICATES; s<=2/3 DOES NOT REPLICATE; else INCONCLUSIVE (BATCH6_PREREGISTRATION.md; C10f primary = distinct facades)" if B == "batch6" else
                      "n<5 INCONCLUSIVE; s>=4/5 REPLICATES; s<=2/3 DOES NOT REPLICATE; else INCONCLUSIVE (BATCH8_PREREGISTRATION.md, secondary reading; C10i primary = distinct facades)" if B == "batch8" else
                      "n<5 INCONCLUSIVE; s>=4/5 REPLICATES; s<=2/3 DOES NOT REPLICATE; else INCONCLUSIVE (BATCH9_PREREGISTRATION.md, secondary reading; C10i primary = distinct facades)" if B == "batch9" else
                      "n<5 INCONCLUSIVE; s>=4/5 SUPPORTED; s<=2/3 NOT SUPPORTED; else INCONCLUSIVE (BATCH3_PREREGISTRATION.md)")}
json.dump(out, open(f"{MR}/analysis/{B}_prediction.json", "w"), indent=1)
print(json.dumps({k: v for k, v in out.items() if k != "per_instance"}, indent=1))
for r in out["per_instance"]: print(f"  {r['pool_rank']:>3} {r['instance']:8s} {r['shifted_over_answered']:>4s} ranks [{r['gold_ranks']}] {r['failure_modes']} redesigned={r['redesigned']} extra={r['extra_raters']}")
