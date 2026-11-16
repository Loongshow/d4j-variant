#!/usr/bin/env python
"""Build the combined-analysis deliverables from the camouflage results plus the existing GPT-5.6
reference results. Descriptive statistics only. Usage: build_master.py"""
import json, os, statistics as st, datetime

SP = "/Users/shawnli/Desktop/Honours/defects4j/supervisor_pipeline_runs"
R = f"{SP}/camouflage-model-comparison-v1"; A = f"{R}/experiment-a-camouflage"; C = f"{R}/combined-analysis"
cam = json.load(open(f"{A}/results/camouflage_results.json"))
v2 = json.load(open(f"{SP}/core-benchmark-scaleup-v2/results-gpt56/scaleup_v2_results.json"))
hist = {b["bug_id"]: b for b in (v2.get("existing_bugs") or []) + (v2.get("bugs_new") or [])}
os.makedirs(f"{C}/tables", exist_ok=True)

PANEL = [("LANG-1-CONVERSION-LONG-01", "rank-stable"), ("MATH-NORM-01", "rank-stable"),
         ("JKC-SURR-04", "rank-stable"), ("CHART-PIE-03", "attribution-sensitive"),
         ("CMP-LAYOUT-02", "occasional alternate owner")]

def f(x):
    return "-" if x is None else (f"{x}" if not isinstance(x, float) else f"{x:.2f}")

# ---------------------------------------------------------------- master_results.json
master = {
 "schema_version": "camouflage-model-comparison-v1/master/v1",
 "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
 "label": "CONTROLLED LARGE-FILE CAMOUFLAGE + MODEL COMPARISON (A executed, B and C blocked)",
 "experiments": {
   "A_camouflage": {"status": "PARTIALLY_EXECUTED_BLOCKED_PROVIDER_QUOTA", "pairs": len(cam["pairs"]), "runs_attempted": cam["block"]["runs_attempted"],
                    "runs_completed": cam["block"]["runs_completed"],
                    "infrastructure_affected": cam["block"]["infrastructure_affected"],
                    "cost_usd": cam["block"]["total_cost_usd"]},
   "B_model_strength": {"status": "BLOCKED_MODEL_AVAILABILITY", "runs": 0, "cost_usd": 0.0,
                        "evidence": "experiment-b-model-strength/review/MODEL_SELECTION.md"},
   "C_anthropic": {"status": "BLOCKED_ADAPTER_SUPPORT", "runs": 0, "cost_usd": 0.0,
                   "comparability": "NOT_COMPARABLE",
                   "evidence": "experiment-c-anthropic/review/MODEL_SELECTION.md"}},
 "statistical_unit": "bug / matched pair; runs are repeated observations nested within arm",
 "camouflage": cam["pairs"], "per_arm": cam["per_arm"],
 "gpt56_reference_panel": {k: {"treatment_gold_ranks": (hist.get(k, {}).get("TREATMENT") or {}).get("gold_ranks_completed"),
                               "treatment_first_gold_mean": (hist.get(k, {}).get("TREATMENT") or {}).get("first_gold_mean"),
                               "treatment_tool_calls_mean": (hist.get(k, {}).get("TREATMENT") or {}).get("tool_calls_mean"),
                               "control_gold_ranks": (hist.get(k, {}).get("CONTROL") or {}).get("gold_ranks_completed"),
                               "class": cls} for k, cls in PANEL},
}
json.dump(master, open(f"{C}/master_results.json", "w"), indent=1)

# ---------------------------------------------------------------- CROSS_MODEL_TABLES.md (Master Table 2)
L = ["# Master Table 2 - model comparison", "",
     "Columns for the weaker GPT model and for Claude are present and empty by design: those experiments",
     "are blocked (see `MODEL_STRENGTH_RESULTS.md`, `ANTHROPIC_REPLICATION_RESULTS.md`). Nothing is",
     "imputed, and no cross-model claim is made.", "",
     "| Benchmark unit | Condition | GPT-5.6 completed n | GPT-5.6 gold ranks | GPT-5.6 Acc@1 | GPT-5.6 MRR | GPT-5.6 first gold | GPT-5.6 tool calls | weaker GPT | Claude |",
     "|" + "---|" * 10]
for k, cls in PANEL:
    b = hist.get(k, {})
    for cond in ("CONTROL", "TREATMENT"):
        d = b.get(cond) or {}
        ranks = d.get("gold_ranks_completed")
        acc = d.get("acc_at_1"); mrr = d.get("mrr")
        L.append(f"| `{k}` ({cls}) | {cond} | {d.get('completed', '-')} | {ranks} | {f(acc)} | {f(mrr)} | "
                 f"{f(d.get('first_gold_mean'))} | {f(d.get('tool_calls_mean'))} | BLOCKED | BLOCKED |")
for pair, p in cam["pairs"].items():
    for arm in ("LOW", "HIGH"):
        a = cam["per_arm"][f"{pair}/{arm}"]
        L.append(f"| `{pair}` (camouflage) | {arm} | {a['completed']} | {a['gold_ranks']} | {f(a['acc1'])} | "
                 f"{f(a['mrr'])} | {f(a['first_gold'])} | {f(a['tool_calls'])} | BLOCKED | BLOCKED |")
open(f"{C}/CROSS_MODEL_TABLES.md", "w").write("\n".join(L) + "\n")

# ---------------------------------------------------------------- DEPTH_PRIOR_ANALYSIS.md
rows = cam["per_run"]
comp = [r for r in rows if r["status"] == "completed" and r["gold_rank"] is not None]
taus = [r["kendall_tau_vs_reverse_depth"] for r in comp if r["kendall_tau_vs_reverse_depth"] is not None]
D = ["# Depth-prior analysis (descriptive evidence only)", "",
     "Every variant ever built in this programme places the gold at the **terminal** stage of the chain,",
     "so \"ranks the gold first\" and \"ranks the deepest stage first\" have always made the same prediction.",
     "This section reports what the camouflage runs show about that confound. **It does not resolve the",
     "confound.** A dedicated non-terminal-gold experiment remains a separate, unrun experiment.", "",
     "| Pair / arm | n | gold rank | gold rank within chain | deepest-stage rank | chain members in top 6 | mean tau vs reverse depth | runs with exactly reverse-depth order |",
     "|" + "---|" * 8]
for k, v in cam["per_arm"].items():
    D.append(f"| `{k}` | {v['completed']} | {v['gold_ranks']} | {v['gold_rank_in_chain']} | {v['deepest_stage_rank']} | "
             f"{f(v['chain_in_top6'])}/6 | {f(v['tau'])} | {v['exact_reverse_depth']}/{v['completed']} |")
D += ["", "## Summary", "",
      f"- Completed runs analysed: {len(comp)}.",
      f"- Mean Kendall tau against reverse-depth order: {round(st.mean(taus), 3) if taus else '-'}"
      f" (median {round(st.median(taus), 3) if taus else '-'}).",
      f"- Runs whose submitted chain order is exactly H5 > H4 > H3 > H2 > H1 > facade: "
      f"{sum(1 for r in comp if r['exact_reverse_depth'])}/{len(comp)}.",
      f"- In this block the gold is the deepest stage in both arms of every pair, so the gold's rank and the",
      "  deepest stage's rank are the same number by construction; the table reports both to make that",
      "  identity explicit rather than to imply independent measurement.", "",
      "Reading: the submitted permutations continue to track reverse chain depth. Because camouflage was",
      "manipulated while depth was held fixed, this block adds evidence that the depth prior is *stable",
      "under a large change in host environment*, and no evidence about whether the prior or genuine",
      "localization drives the ranking."]
open(f"{C}/DEPTH_PRIOR_ANALYSIS.md", "w").write("\n".join(D) + "\n")

# ---------------------------------------------------------------- SEARCH_STRATEGY_AUDIT.md
S_ = ["# Search-strategy audit", "",
      "How the agent actually navigated, per arm, from run artifacts only (commands and tool outputs;",
      "reasoning traces are never read). Definitions are in `experiment-a-camouflage/review/CAMOUFLAGE_METRICS.md`",
      "and `scripts/camouflage_run_metrics.py`.", "",
      "| Pair / arm | n | first host-file step | first gold step | steps host->gold | full-file scans | line-range reads (of host) | same-file methods inspected / available | candidate methods seen before gold | in-host greps | repo-wide searches | test runs | tool calls | lexical shortcuts |",
      "|" + "---|" * 14]
for pair in cam["pairs"]:
    for arm in ("LOW", "HIGH"):
        v = cam["per_arm"][f"{pair}/{arm}"]
        avail = cam["pairs"][pair][f"host_{arm.lower()}"]["methods"]
        S_.append(f"| `{pair}` {arm} | {v['completed']} | {f(v['first_host_file'])} | {f(v['first_gold'])} | "
                  f"{f(v['host_to_gold'])} | {f(v['full_scans'])} | {f(v['ranged_reads'])} ({f(v['ranged_reads_host'])}) | "
                  f"{f(v['methods_inspected'])} / {avail} | {f(v['candidates_before_gold'])} | {f(v['host_greps'])} | "
                  f"{f(v['repo_searches'])} | {f(v['test_runs'])} | {f(v['tool_calls'])} | {v['lexical_shortcuts']} |")
S_ += ["", "## Failure-class separation (B5's categories, applied to GPT-5.6 here)", "",
       "| Class | Definition | Count in this block |", "|---|---|---|"]
disc = sum(1 for r in comp if r["first_gold_exposure_step"] is None)
attr = sum(1 for r in comp if r["gold_rank"] and r["gold_rank"] > 1 and r["first_gold_exposure_step"])
short = sum(1 for r in comp if r["lexical_shortcut"])
S_ += [f"| DISCOVERY FAILURE | gold source never exposed in any tool output | {disc}/{len(comp)} |",
       f"| ATTRIBUTION FAILURE | gold exposed but ranked below another method | {attr}/{len(comp)} |",
       "| SEARCH INEFFICIENCY | same final rank, materially larger navigation burden | see the per-arm table above; the HIGH-minus-LOW deltas in `CAMOUFLAGE_RESULTS.md` are the measurement |",
       f"| SHORTCUT SUCCESS | gold found by searching its own name rather than walking the chain | {short}/{len(comp)} |"]
open(f"{C}/SEARCH_STRATEGY_AUDIT.md", "w").write("\n".join(S_) + "\n")

# ---------------------------------------------------------------- MASTER_RESULTS.md (+ Master Table 3)
def dirn(x, inv=False):
    if x is None:
        return "-"
    if abs(x) < 1e-9:
        return "0"
    up = x > 0
    return ("higher" if up else "lower") + f" ({x:+})"

M = ["# Master results", "",
     f"Generated {master['generated_at']}. One continuous task, three experiments; A executed, B and C blocked.", "",
     "| Experiment | Status | Runs attempted | Runs completed | Cost USD |", "|---|---|---|---|---|",
     f"| A controlled large-file camouflage | PARTIAL: BLOCKED_PROVIDER_QUOTA (2 of 30 slots) | {cam['block']['runs_attempted']} | {cam['block']['runs_completed']} | {cam['block']['total_cost_usd']} |",
     "| B GPT model strength | BLOCKED_MODEL_AVAILABILITY | 0 | 0 | 0.0 |",
     "| C Anthropic replication | BLOCKED_ADAPTER_SUPPORT (NOT_COMPARABLE) | 0 | 0 | 0.0 |", "",
     "Statistical unit: the bug / matched pair. Runs are repeated observations nested within arm. Descriptive",
     "statistics only; no significance tests were added.", "",
     "## Experiment A at a glance", "",
     "| Pair | Project | LOC ratio HIGH/LOW | method ratio | LOW Acc@1 | HIGH Acc@1 | LOW MRR | HIGH MRR | d first-gold | d tool calls | d methods inspected | d candidates before gold | d host lines read |",
     "|" + "---|" * 13]
for pair, p_ in cam["pairs"].items():
    lo = cam["per_arm"][f"{pair}/LOW"]; hi = cam["per_arm"][f"{pair}/HIGH"]; d = p_["delta"]
    M.append(f"| `{pair}` | {p_['project']} | {p_['loc_ratio']}x | {p_['method_ratio']}x | {f(lo['acc1'])} | {f(hi['acc1'])} | "
             f"{f(lo['mrr'])} | {f(hi['mrr'])} | {dirn(d['first_gold'])} | {dirn(d['tool_calls'])} | "
             f"{dirn(d['methods_inspected'])} | {dirn(d['candidates_before_gold'])} | {dirn(d.get('host_lines_read'))} |")
M += ["", "## Master Table 3 - mechanism", "",
      "Each cell separates the three effects the brief asks to keep apart: navigation (how much searching),",
      "ranking (where the gold lands), attribution (which method is blamed).", "",
      "| Difficulty dimension | GPT-5.6 effect | weaker-GPT effect | Claude effect |", "|---|---|---|---|",
      "| **structural distance** (0 vs 5 hops, historical blocks) | navigation: large (first-gold 1.0-1.5 -> 21-23 tool calls; tool calls 12-14 -> 22-30). ranking: none (gold rank 1 in every completed displaced run of the rank-stable bugs). attribution: none. | BLOCKED | BLOCKED |",
      f"| **large-file camouflage** (this block, distance held at 5 hops) | navigation: see the per-pair deltas above. ranking: Acc@1 {f(cam['per_arm'][list(cam['per_arm'])[0]]['acc1'])} vs {f(cam['per_arm'][list(cam['per_arm'])[1]]['acc1'])} in the first pair and the table above for the rest. attribution: no pair changed which method was blamed except as recorded in CAMOUFLAGE_RESULTS.md. | BLOCKED | BLOCKED |",
      "| **ownership ambiguity** (CHART-PIE-03, CMP-LAYOUT-02, historical) | navigation: unchanged. ranking: gold ranked 6th in 5/5 CHART-PIE-03 treatment runs. attribution: the producer stage that defines the wrong quantity is blamed instead of the gold; CMP-LAYOUT-02 shows one run ranking the pre-registered alternate owner second. | BLOCKED | BLOCKED |", "",
      "## Where the numbers live", "",
      "- Experiment A per-run and per-arm tables: `../experiment-a-camouflage/results/CAMOUFLAGE_RESULTS.md`",
      "- Camouflage metric definitions and host separation: `../experiment-a-camouflage/review/CAMOUFLAGE_METRICS.md`",
      "- Search behaviour and failure-class separation: `SEARCH_STRATEGY_AUDIT.md`",
      "- Depth prior: `DEPTH_PRIOR_ANALYSIS.md` (descriptive only)",
      "- Cross-model table with the blocked columns: `CROSS_MODEL_TABLES.md`",
      "- Blocked-experiment records: `MODEL_STRENGTH_RESULTS.md`, `ANTHROPIC_REPLICATION_RESULTS.md`"]
open(f"{C}/MASTER_RESULTS.md", "w").write("\n".join(M) + "\n")

print("wrote master_results.json, CROSS_MODEL_TABLES.md, DEPTH_PRIOR_ANALYSIS.md, SEARCH_STRATEGY_AUDIT.md, MASTER_RESULTS.md")
print(json.dumps(master["experiments"], indent=1))
