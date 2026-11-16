#!/usr/bin/env python
"""Aggregate the camouflage block: per-arm and per-pair LOW vs HIGH summaries, Master Table 1, and
experiment-a-camouflage/results/CAMOUFLAGE_RESULTS.md. Descriptive statistics only; the matched PAIR is
the unit for any cross-pair statement; infrastructure-affected runs are never counted as localization
misses. Usage: build_camouflage_results.py"""
import json, os, statistics as st

R = "/Users/shawnli/Desktop/Honours/defects4j/supervisor_pipeline_runs/camouflage-model-comparison-v1"
A = f"{R}/experiment-a-camouflage"
rows = json.load(open(f"{A}/results/per_run_camouflage_metrics.json"))
PAIRS = [("LANG-CONV-CAMO", "lang_conv", "lang", "Lang", "bit-packing word offset"),
         ("MATH-NORM-CAMO", "math_norm", "math", "Math", "floating-point scale units"),
         ("JKC-SURR-CAMO", "jkc_surr", "jkc", "JacksonCore", "surrogate code-point width")]
host = {}
for pair, sname, key, proj, fam in PAIRS:
    for arm in ("low", "high"):
        m = json.load(open(f"{A}/review/metrics/{key}_{arm}.json"))
        cfg = json.load(open(f"{A}/construction/configs/{sname}/pair_config_{arm}.json"))
        host[(pair, arm.upper())] = {"host": cfg["treatment"]["gold_class"].split(".")[-1],
          "loc": m["file_loc_total"], "methods": m["declared_methods"],
          "pct": m["gold_percentile_in_file"], "w100": m["methods_within_100_lines"],
          "c3": m["candidates"]["C3_numeric_return_arith"], "c4": m["candidates"]["C4_any_arith"]}

def mean(xs):
    xs = [x for x in xs if x is not None]
    return round(st.mean(xs), 2) if xs else None
def med(xs):
    xs = [x for x in xs if x is not None]
    return st.median(xs) if xs else None

def agg(rs):
    comp = [r for r in rs if r["status"] == "completed" and r["gold_rank"] is not None]
    infra = [r for r in rs if r["status"] != "completed"]
    n = len(comp)
    return {"attempted": len(rs), "completed": n, "infrastructure_affected": len(infra),
      "gold_ranks": [r["gold_rank"] for r in comp],
      "acc1": round(sum(r["acc_at_1"] for r in comp) / n, 3) if n else None,
      "acc3": round(sum(r["acc_at_3"] for r in comp) / n, 3) if n else None,
      "acc5": round(sum(r["acc_at_5"] for r in comp) / n, 3) if n else None,
      "mrr": round(st.mean([r["mrr"] for r in comp]), 3) if n else None,
      "first_gold": mean([r["first_gold_exposure_step"] for r in comp]),
      "first_host_file": mean([r["first_host_file_step"] for r in comp]),
      "host_to_gold": mean([r["steps_from_host_to_gold"] for r in comp]),
      "full_scans": mean([r["full_file_scans"] for r in comp]),
      "ranged_reads": mean([r["targeted_line_range_reads"] for r in comp]),
      "ranged_reads_host": mean([r["targeted_line_range_reads_of_host"] for r in comp]),
      "host_lines_read": mean([r["host_lines_read"] for r in comp]),
      "host_lines_read_fraction": mean([r["host_lines_read_fraction"] for r in comp]),
      "methods_inspected": mean([r["same_file_methods_inspected"] for r in comp]),
      "candidates_before_gold": mean([r["candidate_methods_seen_before_gold"] for r in comp]),
      "host_greps": mean([r["greps_in_gold_host"] for r in comp]),
      "repo_searches": mean([r["repository_wide_searches"] for r in comp]),
      "tool_calls": mean([r["tool_calls"] for r in comp]), "tool_calls_median": med([r["tool_calls"] for r in comp]),
      "api_calls": mean([r["api_calls"] for r in comp]),
      "test_runs": mean([r["test_runs"] for r in comp]),
      "wall_s": mean([r["wall_clock_s"] for r in comp]),
      "cost_usd": round(sum(r["cost_usd"] or 0 for r in rs), 4),
      "lexical_shortcuts": sum(1 for r in comp if r["lexical_shortcut"]),
      "tau": mean([r["kendall_tau_vs_reverse_depth"] for r in comp]),
      "exact_reverse_depth": sum(1 for r in comp if r["exact_reverse_depth"]),
      "chain_in_top6": mean([r["chain_members_in_top6"] for r in comp]),
      "gold_rank_in_chain": [r["gold_rank_in_chain"] for r in comp],
      "deepest_stage_rank": [r["deepest_stage_rank"] for r in comp]}

res = {"label": "NON-CANONICAL / CONTROLLED LARGE-FILE CAMOUFLAGE / GPT-5.6 (EXPERIMENT A)",
       "unit_of_replication": "matched pair", "pairs": {}, "per_arm": {}, "per_run": rows}
for pair, *_ in PAIRS:
    for arm in ("LOW", "HIGH"):
        res["per_arm"][f"{pair}/{arm}"] = agg([r for r in rows if r["pair"] == pair and r["arm"] == arm])
for pair, sname, key, proj, fam in PAIRS:
    lo, hi = res["per_arm"][f"{pair}/LOW"], res["per_arm"][f"{pair}/HIGH"]
    d = lambda k: None if (lo[k] is None or hi[k] is None) else round(hi[k] - lo[k], 2)
    res["pairs"][pair] = {"project": proj, "family": fam,
      "host_low": host[(pair, "LOW")], "host_high": host[(pair, "HIGH")],
      "loc_ratio": round(host[(pair, "HIGH")]["loc"] / host[(pair, "LOW")]["loc"], 2),
      "method_ratio": round(host[(pair, "HIGH")]["methods"] / host[(pair, "LOW")]["methods"], 2),
      "delta": {k: d(k) for k in ("acc1", "mrr", "first_gold", "first_host_file", "host_to_gold", "full_scans",
                                  "ranged_reads", "ranged_reads_host", "methods_inspected", "candidates_before_gold",
                                  "host_greps", "repo_searches", "tool_calls", "api_calls", "wall_s", "tau",
                                  "host_lines_read", "host_lines_read_fraction")}}
allc = [r for r in rows if r["status"] == "completed" and r["gold_rank"] is not None]
res["block"] = {"runs_attempted": len(rows), "runs_completed": len(allc),
  "infrastructure_affected": sum(1 for r in rows if r["status"] != "completed"),
  "total_cost_usd": round(sum(r["cost_usd"] or 0 for r in rows), 4),
  "acc1_overall": round(sum(r["acc_at_1"] for r in allc) / len(allc), 3) if allc else None,
  "pairs_with_three_or_more_completed_runs_per_arm": sum(
      1 for pair in res["pairs"]
      if res["per_arm"][f"{pair}/LOW"]["completed"] >= 3 and res["per_arm"][f"{pair}/HIGH"]["completed"] >= 3)}
usable = res["block"]["pairs_with_three_or_more_completed_runs_per_arm"]
res["block"]["comparison_valid"] = usable >= 2
res["block"]["note"] = (
    "LOW vs HIGH comparison NOT valid: %d of %d pairs have at least three completed runs in both arms. "
    "Per the pre-registered rule in review/READINESS.md no outcome class is assigned and the HIGH-minus-LOW "
    "columns below are placeholders, not findings." % (usable, len(res["pairs"]))) if usable < 2 else (
    "LOW vs HIGH comparison valid on %d of %d pairs." % (usable, len(res["pairs"])))
if usable < 2:
    res["block"]["pairs_where_high_costs_more_tool_calls"] = None
    res["block"]["pairs_where_high_delays_first_gold"] = None
    res["block"]["pairs_where_high_lowers_acc1"] = None
else:
    res["block"]["pairs_where_high_costs_more_tool_calls"] = sum(1 for p in res["pairs"].values() if (p["delta"]["tool_calls"] or 0) > 0)
    res["block"]["pairs_where_high_delays_first_gold"] = sum(1 for p in res["pairs"].values() if (p["delta"]["first_gold"] or 0) > 0)
    res["block"]["pairs_where_high_lowers_acc1"] = sum(1 for p in res["pairs"].values() if (p["delta"]["acc1"] or 0) < 0)
json.dump(res, open(f"{A}/results/camouflage_results.json", "w"), indent=1)

L = ["# Experiment A results: controlled large-file camouflage (GPT-5.6)", "",
     f"{res['block']['runs_completed']}/{res['block']['runs_attempted']} runs completed"
     f" ({res['block']['infrastructure_affected']} infrastructure-affected, preserved and never replaced);"
     f" total provider cost {res['block']['total_cost_usd']} USD.", "",
     "The matched pair is the unit of replication. Within a pair the only difference is which existing",
     "production class hosts the gold method; the fault, chain, trigger, failure, gold body, prompt, model",
     "and budget are identical (see `review/CAMOUFLAGE_AUDIT.md`).", "",
     "## Master Table 1 - camouflage", "",
     "| Pair | LOW host | HIGH host | LOW LOC | HIGH LOC | LOW methods | HIGH methods | LOW arith-methods | HIGH arith-methods | LOW first-gold | HIGH first-gold | LOW scans | HIGH scans | LOW methods inspected | HIGH methods inspected | LOW Acc@1 | HIGH Acc@1 | LOW MRR | HIGH MRR |",
     "|" + "---|" * 19]
for pair, *_ in PAIRS:
    p = res["pairs"][pair]; lo = res["per_arm"][f"{pair}/LOW"]; hi = res["per_arm"][f"{pair}/HIGH"]
    L.append(f"| `{pair}` | {p['host_low']['host']} | {p['host_high']['host']} | {p['host_low']['loc']} | {p['host_high']['loc']} | "
             f"{p['host_low']['methods']} | {p['host_high']['methods']} | {p['host_low']['c4']} | {p['host_high']['c4']} | "
             f"{lo['first_gold']} | {hi['first_gold']} | {lo['ranged_reads']} | {hi['ranged_reads']} | "
             f"{lo['methods_inspected']} | {hi['methods_inspected']} | {lo['acc1']} | {hi['acc1']} | {lo['mrr']} | {hi['mrr']} |")
L += ["", "Scans column = targeted line-range reads per run (full-file `cat` of a host was used "
      f"{sum(r['full_file_scans'] for r in allc)} times in {len(allc)} completed runs).", "",
      "## Per-arm detail", "",
      "| Pair / arm | n | gold ranks | Acc@1 | MRR | first gold step | first host-file step | host->gold steps | line-range reads | of host | methods inspected | candidates before gold | in-host greps | repo-wide searches | tool calls | API calls | test runs | wall s | cost USD | lexical shortcuts | tau | exact reverse depth |",
      "|" + "---|" * 22]
for k, v in res["per_arm"].items():
    L.append(f"| `{k}` | {v['completed']}/{v['attempted']} | {v['gold_ranks']} | {v['acc1']} | {v['mrr']} | {v['first_gold']} | "
             f"{v['first_host_file']} | {v['host_to_gold']} | {v['ranged_reads']} | {v['ranged_reads_host']} | "
             f"{v['methods_inspected']} | {v['candidates_before_gold']} | {v['host_greps']} | {v['repo_searches']} | "
             f"{v['tool_calls']} | {v['api_calls']} | {v['test_runs']} | {v['wall_s']} | {v['cost_usd']} | "
             f"{v['lexical_shortcuts']} | {v['tau']} | {v['exact_reverse_depth']}/{v['completed']} |")
L += ["", "## HIGH minus LOW, per pair", "",
      "| Pair | LOC ratio | method ratio | d Acc@1 | d MRR | d first-gold | d first host-file | d host->gold | d line-range reads | d methods inspected | d candidates before gold | d in-host greps | d repo searches | d tool calls | d API calls | d wall s | d tau |",
      "|" + "---|" * 16]
for pair, *_ in PAIRS:
    p = res["pairs"][pair]; d = p["delta"]
    L.append(f"| `{pair}` | {p['loc_ratio']}x | {p['method_ratio']}x | {d['acc1']} | {d['mrr']} | {d['first_gold']} | "
             f"{d['first_host_file']} | {d['host_to_gold']} | {d['ranged_reads']} | {d['methods_inspected']} | "
             f"{d['candidates_before_gold']} | {d['host_greps']} | {d['repo_searches']} | {d['tool_calls']} | "
             f"{d['api_calls']} | {d['wall_s']} | {d['tau']} |")
L += ["", "## Per-run record", "",
      "| Pair | Arm | Run | Status | Gold rank | Rank in chain | Chain in top 6 | tau | Tool calls | First gold | First host file | Line-range reads | Methods inspected | Candidates before gold | Repo searches | Wall s | Cost USD |",
      "|" + "---|" * 17]
for r in rows:
    L.append(f"| `{r['pair']}` | {r['arm']} | {r['run']} | {r['status']} | {r['gold_rank']} | {r['gold_rank_in_chain']} | "
             f"{r['chain_members_in_top6']}/6 | {r['kendall_tau_vs_reverse_depth']} | {r['tool_calls']} | "
             f"{r['first_gold_exposure_step']} | {r['first_host_file_step']} | {r['targeted_line_range_reads']} | "
             f"{r['same_file_methods_inspected']} | {r['candidate_methods_seen_before_gold']} | "
             f"{r['repository_wide_searches']} | {r['wall_clock_s']} | {r['cost_usd']}")
open(f"{A}/results/CAMOUFLAGE_RESULTS.md", "w").write("\n".join(L) + "\n")
print(json.dumps(res["block"], indent=1))
for k, v in res["per_arm"].items():
    print(f"  {k:34s} n={v['completed']}/{v['attempted']} ranks={v['gold_ranks']} acc1={v['acc1']} first_gold={v['first_gold']} tc={v['tool_calls']} ranged={v['ranged_reads']} methods={v['methods_inspected']} cand={v['candidates_before_gold']} repo={v['repo_searches']}")
