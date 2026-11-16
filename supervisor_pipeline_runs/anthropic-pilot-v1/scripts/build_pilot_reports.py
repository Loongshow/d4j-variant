#!/usr/bin/env python
"""Build every results deliverable for the Claude pilot from the provider-independent per-run metrics.
Descriptive statistics only. The bug/arm is the unit; runs are repeated observations nested within it.
Usage: build_pilot_reports.py"""
import json, os, statistics as st, datetime, glob, collections

SP = "/Users/shawnli/Desktop/Honours/defects4j/supervisor_pipeline_runs"
R = f"{SP}/anthropic-pilot-v1"; A = f"{R}/analysis"
rows = json.load(open(f"{A}/per_run/pilot_run_metrics.json"))
CLAUDE, GPT = "claude-opus-5-5", "gpt-5.6"
UNITS = [("CONVERSION-LONG-01", ["CONTROL", "TREATMENT"]), ("CHART-PIE-03", ["CONTROL", "TREATMENT"]),
         ("CMP-LAYOUT-02", ["CONTROL", "TREATMENT"]), ("LANG-CONV-CAMO", ["LOW", "HIGH"])]
os.makedirs(f"{A}/tables", exist_ok=True); os.makedirs(f"{A}/per_bug", exist_ok=True); os.makedirs(f"{A}/figures_data", exist_ok=True)


def mean(xs):
    xs = [x for x in xs if x is not None]
    return round(st.mean(xs), 2) if xs else None


def f(x, nd=2):
    if x is None:
        return "-"
    return f"{x:.{nd}f}" if isinstance(x, float) else str(x)


def sel(model, unit, arm):
    return [r for r in rows if r["model"] == model and r["unit"] == unit and r["arm"] == arm]


def agg(rs):
    comp = [r for r in rs if r["status"] == "completed" and r["gold_rank"] is not None]
    n = len(comp)
    return {
        "attempted": len(rs), "completed": n,
        "infrastructure_affected": sum(1 for r in rs if r["status"] != "completed"),
        "gold_ranks": [r["gold_rank"] for r in comp],
        "acc1": round(sum(r["acc_at_1"] for r in comp) / n, 3) if n else None,
        "acc3": round(sum(r["acc_at_3"] for r in comp) / n, 3) if n else None,
        "acc5": round(sum(r["acc_at_5"] for r in comp) / n, 3) if n else None,
        "acc10": round(sum(r["acc_at_10"] for r in comp) / n, 3) if n else None,
        "mrr": round(st.mean([r["mrr"] for r in comp]), 3) if n else None,
        "first_gold": mean([r["first_gold_step"] for r in comp]),
        "first_facade": mean([r["first_facade_step"] for r in comp]),
        "hops_exposed": mean([r["hops_exposed"] for r in comp]),
        "tool_calls": mean([r["tool_calls"] for r in comp]),
        "api_calls": mean([r["api_calls"] for r in comp]),
        "file_reads": mean([r["file_reads"] for r in comp]),
        "searches": mean([r["searches"] for r in comp]),
        "repo_searches": mean([r["repository_wide_searches"] for r in comp]),
        "full_scans": mean([r["full_file_scans"] for r in comp]),
        "ranged_reads": mean([r["targeted_line_range_reads"] for r in comp]),
        "test_runs": mean([r["test_runs"] for r in comp]),
        "direct_gold_searches": sum(1 for r in comp if r["direct_gold_search_step"]),
        "lexical_shortcuts": sum(1 for r in comp if r["lexical_shortcut"]),
        "gold_search_before_any_hop": sum(1 for r in comp if r.get("gold_search_before_any_hop")),
        "calls_after_gold": mean([r["calls_after_first_gold"] for r in comp]),
        "candidates_before_gold": mean([r["candidate_methods_seen_before_gold"] for r in comp]),
        "deepest_stage_rank": [r["deepest_stage_rank"] for r in comp],
        "tau": mean([r["kendall_tau_vs_reverse_depth"] for r in comp]),
        "exact_reverse_depth": sum(1 for r in comp if r["exact_reverse_depth"]),
        "chain_in_top6": mean([r["chain_members_in_top6"] for r in comp]),
        "rank1_gold": sum(1 for r in comp if r["rank1_is_gold"]),
        "rank1_labels": dict(collections.Counter(r["rank1_chain_label"] or "off-chain" for r in comp)),
        "host_opens": mean([r["host_file_opens"] for r in comp]),
        "host_lines_read": mean([r["host_lines_read"] for r in comp]),
        "host_lines_seen_total": mean([r.get("host_lines_seen_total") for r in comp]),
        "host_methods_inspected": mean([r["host_methods_inspected"] for r in comp]),
        "cost_usd": round(sum(r["cost_usd"] or 0 for r in rs), 4),
        "wall_s": mean([r["wall_clock_s"] for r in comp]),
    }


res = {"schema_version": "anthropic-pilot-v1/results/v1",
       "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
       "claude_model": CLAUDE, "gpt_model": GPT,
       "statistical_unit": "bug/arm; runs are repeated observations nested within arm",
       "per_arm": {}, "per_run": rows}
for unit, arms in UNITS:
    for arm in arms:
        for m in (CLAUDE, GPT):
            res["per_arm"][f"{m}|{unit}|{arm}"] = agg(sel(m, unit, arm))
cl = [r for r in rows if r["model"] == CLAUDE]
clc = [r for r in cl if r["status"] == "completed" and r["gold_rank"] is not None]
res["block"] = {"claude_runs_attempted": len(cl), "claude_runs_completed": len(clc),
                "claude_infrastructure_affected": sum(1 for r in cl if r["status"] != "completed"),
                "claude_total_cost_usd": round(sum(r["cost_usd"] or 0 for r in cl), 4),
                "claude_acc1_overall": round(sum(r["acc_at_1"] for r in clc) / len(clc), 3) if clc else None,
                "gpt_reference_runs": len([r for r in rows if r["model"] == GPT])}
json.dump(res, open(f"{R}/claude_pilot_results.json", "w"), indent=1)

# ---------------------------------------------------------------- CLAUDE_PILOT_RESULTS.md
L = [f"# Claude pilot results ({CLAUDE})", "",
     f"{res['block']['claude_runs_completed']}/{res['block']['claude_runs_attempted']} Claude runs completed"
     f" ({res['block']['claude_infrastructure_affected']} infrastructure-affected, preserved and never replaced);"
     f" total Anthropic spend {res['block']['claude_total_cost_usd']} USD.", "",
     "All runs used the frozen protocol: prompt `d4j-localization-only/v2` (base sha256 `845e21e7…`),",
     "50 tool calls, 5 test runs, 300 s execution, 30 s startup, exact `FQCN::method` scoring. Metrics are",
     "computed by `scripts/pilot_run_metrics.py`, the same code applied to the GPT-5.6 reference runs.", "",
     "## Per-arm summary", "",
     "| Unit | Arm | n | gold ranks | Acc@1 | Acc@3 | MRR | first gold | first facade | hops seen | tool calls | API calls | file reads | repo searches | tests | calls after gold | cost USD |",
     "|" + "---|" * 17]
for unit, arms in UNITS:
    for arm in arms:
        v = res["per_arm"][f"{CLAUDE}|{unit}|{arm}"]
        if not v["attempted"]:
            continue
        L.append(f"| `{unit}` | {arm} | {v['completed']}/{v['attempted']} | {v['gold_ranks']} | {f(v['acc1'])} | {f(v['acc3'])} | "
                 f"{f(v['mrr'])} | {f(v['first_gold'])} | {f(v['first_facade'])} | {f(v['hops_exposed'])} | {f(v['tool_calls'])} | "
                 f"{f(v['api_calls'])} | {f(v['file_reads'])} | {f(v['repo_searches'])} | {f(v['test_runs'])} | "
                 f"{f(v['calls_after_gold'])} | {v['cost_usd']} |")
L += ["", "## Per-run record", "",
      "| Unit | Arm | Run | Status | Gold rank | Rank-1 prediction | Tool calls | API calls | First gold | Hops seen | Repo searches | Direct gold search | tau | Cost USD |",
      "|" + "---|" * 14]
for r in [x for x in rows if x["model"] == CLAUDE]:
    L.append(f"| `{r['unit']}` | {r['arm']} | {r['run']} | {r['status']} | {r['gold_rank']} | `{r['rank1_prediction']}` | "
             f"{r['tool_calls']} | {r['api_calls']} | {r['first_gold_step']} | {r['hops_exposed']} | "
             f"{r['repository_wide_searches']} | {r['direct_gold_search_step']} | {r['kendall_tau_vs_reverse_depth']} | "
             f"{f(r['cost_usd'], 4)} |")
open(f"{R}/CLAUDE_PILOT_RESULTS.md", "w").write("\n".join(L) + "\n")

# ---------------------------------------------------------------- GPT56_VS_CLAUDE.md
G = ["# GPT-5.6 versus Claude on identical frozen instances", "",
     "GPT-5.6 was not rerun. Its numbers come from the frozen run artifacts on disk, re-measured with the",
     "same script that measured Claude, so both columns use one set of metric definitions.", "",
     "| Unit | Arm | model | n | gold ranks | Acc@1 | MRR | first gold | tool calls | API calls | file reads | repo searches | hops seen | calls after gold | tau | cost USD |",
     "|" + "---|" * 16]
for unit, arms in UNITS:
    for arm in arms:
        for m in (GPT, CLAUDE):
            v = res["per_arm"][f"{m}|{unit}|{arm}"]
            if not v["attempted"]:
                continue
            G.append(f"| `{unit}` | {arm} | {m} | {v['completed']}/{v['attempted']} | {v['gold_ranks']} | {f(v['acc1'])} | "
                     f"{f(v['mrr'])} | {f(v['first_gold'])} | {f(v['tool_calls'])} | {f(v['api_calls'])} | {f(v['file_reads'])} | "
                     f"{f(v['repo_searches'])} | {f(v['hops_exposed'])} | {f(v['calls_after_gold'])} | {f(v['tau'])} | {v['cost_usd']} |")
G += ["", "## Claude minus GPT-5.6, per arm", "",
      "| Unit | Arm | d Acc@1 | d MRR | d first gold | d tool calls | d file reads | d repo searches | d calls after gold |",
      "|" + "---|" * 9]
for unit, arms in UNITS:
    for arm in arms:
        a, b = res["per_arm"][f"{CLAUDE}|{unit}|{arm}"], res["per_arm"][f"{GPT}|{unit}|{arm}"]
        if not a["completed"] or not b["completed"]:
            G.append(f"| `{unit}` | {arm} | not comparable: Claude n={a['completed']}, GPT-5.6 n={b['completed']} | | | | | | |")
            continue
        d = lambda k: None if (a[k] is None or b[k] is None) else round(a[k] - b[k], 2)
        G.append(f"| `{unit}` | {arm} | {f(d('acc1'))} | {f(d('mrr'))} | {f(d('first_gold'))} | {f(d('tool_calls'))} | "
                 f"{f(d('file_reads'))} | {f(d('repo_searches'))} | {f(d('calls_after_gold'))} |")
open(f"{R}/GPT56_VS_CLAUDE.md", "w").write("\n".join(G) + "\n")

# ---------------------------------------------------------------- OWNERSHIP_CROSS_MODEL.md
O = ["# Ownership attribution across models", "",
     "For every completed run: which method the model ranked first, and whether that is the gold, another",
     "chain stage, or a method off the chain entirely.", "",
     "| Unit | Arm | model | n | rank-1 is gold | rank-1 distribution (chain label) | gold ranks |",
     "|" + "---|" * 7]
for unit, arms in UNITS:
    for arm in arms:
        for m in (GPT, CLAUDE):
            v = res["per_arm"][f"{m}|{unit}|{arm}"]
            if not v["completed"]:
                continue
            O.append(f"| `{unit}` | {arm} | {m} | {v['completed']} | {v['rank1_gold']}/{v['completed']} | "
                     f"{json.dumps(v['rank1_labels'])} | {v['gold_ranks']} |")
open(f"{R}/OWNERSHIP_CROSS_MODEL.md", "w").write("\n".join(O) + "\n")

# ---------------------------------------------------------------- DEPTH_PRIOR_CROSS_MODEL.md
D_ = ["# Depth prior across models (descriptive only)", "",
      "In every variant used here the gold is the terminal chain stage, so gold rank and deepest-stage rank are",
      "the same number by construction. This table reports how closely each model's submitted chain order",
      "follows reverse chain depth. It does not resolve the depth confound.", "",
      "| Unit | Arm | model | n | deepest-stage ranks | mean tau vs reverse depth | exact reverse-depth runs | chain members in top 6 |",
      "|" + "---|" * 8]
for unit, arms in UNITS:
    for arm in arms:
        for m in (GPT, CLAUDE):
            v = res["per_arm"][f"{m}|{unit}|{arm}"]
            if not v["completed"] or arm == "CONTROL":
                continue
            D_.append(f"| `{unit}` | {arm} | {m} | {v['completed']} | {v['deepest_stage_rank']} | {f(v['tau'])} | "
                      f"{v['exact_reverse_depth']}/{v['completed']} | {f(v['chain_in_top6'])}/6 |")
open(f"{R}/DEPTH_PRIOR_CROSS_MODEL.md", "w").write("\n".join(D_) + "\n")

# ---------------------------------------------------------------- CAMOUFLAGE_CROSS_MODEL.md
C_ = ["# Large-file camouflage across models", "",
      "The camouflage pair holds the fault, the chain, the trigger, the failure and the gold body fixed and",
      "changes only which production class hosts the gold: `LocaleUtils` (341 lines, 10 methods) for LOW,",
      "`StringUtils` (7373 lines, 187 methods) for HIGH.", ""]
lo_c, hi_c = res["per_arm"][f"{CLAUDE}|LANG-CONV-CAMO|LOW"], res["per_arm"][f"{CLAUDE}|LANG-CONV-CAMO|HIGH"]
lo_g, hi_g = res["per_arm"][f"{GPT}|LANG-CONV-CAMO|LOW"], res["per_arm"][f"{GPT}|LANG-CONV-CAMO|HIGH"]
C_ += ["| Metric | Claude LOW | Claude HIGH | GPT-5.6 LOW | GPT-5.6 HIGH |", "|" + "---|" * 5]
for label, key in [("completed runs", "completed"), ("gold ranks", "gold_ranks"), ("Acc@1", "acc1"), ("MRR", "mrr"),
                   ("first gold step", "first_gold"), ("tool calls", "tool_calls"), ("file reads", "file_reads"),
                   ("host file opens", "host_opens"), ("host lines read via sed ranges", "host_lines_read"),
                   ("host lines seen incl. grep context", "host_lines_seen_total"),
                   ("host methods inspected", "host_methods_inspected"),
                   ("candidate methods before gold", "candidates_before_gold"),
                   ("full-file scans", "full_scans"), ("targeted line-range reads", "ranged_reads"),
                   ("repo-wide searches", "repo_searches"), ("direct gold searches", "direct_gold_searches"),
                   ("cost USD", "cost_usd")]:
    C_.append(f"| {label} | {f(lo_c.get(key))} | {f(hi_c.get(key))} | {f(lo_g.get(key))} | {f(hi_g.get(key))} |")
C_ += ["", "**The GPT-5.6 side of this pair is incomplete by 28 runs.** Its camouflage block was stopped by OpenAI",
       "credit exhaustion after 2 of 30 slots, so GPT-5.6 has one completed LOW run and no HIGH run. The LOW/HIGH",
       "contrast reported here is therefore *within Claude only*; no cross-model camouflage claim is made."]
open(f"{R}/CAMOUFLAGE_CROSS_MODEL.md", "w").write("\n".join(C_) + "\n")
json.dump(res["per_arm"], open(f"{A}/tables/per_arm_summary.json", "w"), indent=1)
with open(f"{A}/figures_data/per_run.csv", "w") as fh:
    cols = ["model", "unit", "arm", "run", "status", "gold_rank", "tool_calls", "api_calls", "first_gold_step",
            "file_reads", "repository_wide_searches", "hops_exposed", "calls_after_first_gold",
            "kendall_tau_vs_reverse_depth", "cost_usd"]
    fh.write(",".join(cols) + "\n")
    for r in rows:
        fh.write(",".join(str(r.get(c)) for c in cols) + "\n")
print(json.dumps(res["block"], indent=1))
for k, v in res["per_arm"].items():
    if v["attempted"]:
        print(f"  {k:46s} n={v['completed']}/{v['attempted']} ranks={v['gold_ranks']} acc1={v['acc1']} fg={v['first_gold']} tc={v['tool_calls']}")
