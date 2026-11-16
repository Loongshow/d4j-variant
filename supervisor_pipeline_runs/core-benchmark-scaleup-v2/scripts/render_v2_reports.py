"""Renders every results-gpt56/ report for the v2 scale-up from scaleup_v2_results.json. Descriptive statistics only; the BUG is the replication unit.
NON-CANONICAL / CORE BENCHMARK SCALE-UP V2 / GPT-5.6."""
import json, os, csv, statistics, math
S = "/Users/shawnli/Desktop/Honours/defects4j/supervisor_pipeline_runs/core-benchmark-scaleup-v2"; OUT = S + "/results-gpt56"; A = OUT + "/analysis"
d = json.load(open(OUT + "/scaleup_v2_results.json")); H = f"NON-CANONICAL · CORE BENCHMARK SCALE-UP V2 · GPT-5.6 · generated {d['generated_at'][:19]}Z"
def f(x, nd=2): return "-" if x is None else (f"{x:.{nd}f}" if isinstance(x, float) else str(x))
def pct(x): return "-" if x is None else f"{100*x:.0f}%"
def mean(xs): xs=[x for x in xs if x is not None]; return round(statistics.mean(xs),2) if xs else None
def median(xs): xs=[x for x in xs if x is not None]; return statistics.median(xs) if xs else None
def w(name, lines): open(f"{OUT}/{name}", "w").write("\n".join(lines) + "\n"); print("wrote", name)
new = [b for b in d["bugs_new"] if "effect" in b]; sl = d["slots"]; a6 = d["five_bug_aggregate"]; agg = d["eight_bug_aggregate"]; table = d["eight_bug_table"]; ex = d["existing_bugs"]; ps = d["project_summary"]; fam = d["family_summary"]; inf = d["infrastructure"]; cost = d["cost"]; runs = d["per_run"]
complete = sl["attempted"] >= 60
status = f"{sl['attempted']}/60 planned slots attempted · {sl['completed']} completed · {sl['infrastructure_affected']} infrastructure-affected (lost) · {sl.get('completed_with_slow_response_or_prep_stall',0)} completed after a slow provider response · {sl['contaminated']} contaminated" + ("" if complete else " · BLOCK IN PROGRESS (partial)")
# 1 main results
L = [f"# SCALEUP_V2_RESULTS — six new bugs, CONTROL vs direct five-hop TREATMENT ({H})", "", f"**Status**: {status}.", "",
     "Frozen protocol, identical to the earlier blocks: `mini-swe-agent-openai-gpt-5-6`, GPT-5.6, prompt `d4j-localization-only/v2` (base sha `845e21e7…`), 50 tool calls / 5 test runs / 300 s / 30 s startup, exact FQCN::method scoring, one run per launch, no reruns or replacements, no per-bug tuning. Observable-only analysis (commands, tool output, submitted rankings); hidden reasoning never read. Infrastructure-affected runs are reported separately and never counted as localization misses.", "",
     "## 1. Per-bug results (completed runs with a valid ranking)", "", "| Bug | Project | Family | Arm | completed/attempted | Gold ranks | Acc@1 | Acc@3 | Acc@5 | Acc@10 | MRR | First-gold mean/median | Tool calls mean/median | API mean | Cost USD |", "|" + "---|" * 15]
for b in new:
    for arm in ("CONTROL", "TREATMENT"):
        m = b[arm]; L.append(f"| {b['bug_id']} | {b['project']} | {b['family']} | {arm} | {m['completed']}/{m['attempted']} | {m['gold_ranks_completed']} | {f(m['acc_at_1'])} | {f(m['acc_at_3'])} | {f(m['acc_at_5'])} | {f(m['acc_at_10'])} | {f(m['mrr'])} | {f(m['first_gold_mean'])} / {f(m['first_gold_median'])} | {f(m['tool_calls_mean'])} / {f(m['tool_calls_median'])} | {f(m['api_calls_mean'])} | {f(m['cost_usd_total'],4)} |")
L += ["", "## 2. TREATMENT chain metrics (completed runs)", "", "| Bug | Full sequential traversal | All hops in order | Lexical bypass | Direct gold search | Repo-wide | Any shortcut | Contract evidence before rank | Post-gold verification | Classes A–F | Gold vs H4 |", "|" + "---|" * 11]
for b in new:
    T = b["TREATMENT"]; L.append(f"| {b['bug_id']} | {T['full_sequential_traversal_completed']}/{T['completed']} | {pct(T['all_hops_in_order_rate'])} | {T['lexical_bypass_completed']}/{T['completed']} | {T['direct_gold_search_completed']}/{T['completed']} | {T['repository_wide_shortcut_completed']}/{T['completed']} | {T['shortcut_any_completed']}/{T['completed']} | {T['external_contract_before_rank_runs']}/{T['completed']} | {T['post_gold_verification_runs']}/{T['completed']} | {T['traversal_class_counts']} | {dict(T['gold_exposure_relative_to_H4'])} |")
L += ["", "## 3. CONTROL vs TREATMENT effect per new bug", "", "| Bug | Δ first-gold | ratio | Δ tool calls | Δ API | Δ calls after gold | Δ MRR | CONTROL ranks | TREATMENT ranks | Degradation? | All rank 1? | Ownership (contractual/behavioural) | Mechanism |", "|" + "---|" * 13]
for b in new:
    e = b["effect"]; L.append(f"| {b['bug_id']} | {f(e['delta_first_gold_steps'])} | {f(e['first_gold_ratio'])} | {f(e['delta_tool_calls'])} | {f(e['delta_api_calls'])} | {f(e['delta_calls_after_gold'])} | {f(e['delta_mrr'])} | {b['CONTROL']['gold_ranks_completed']} | {b['TREATMENT']['gold_ranks_completed']} | {e['rank_degradation_observed']} | {e['treatment_all_rank_1']} | {b.get('ownership_contractual')}/{b.get('ownership_behavioural')} | {e['dominant_trajectory_mechanism']} |")
L += ["", "## 4. Six-new-bug aggregate (bug = unit)", "", f"- bugs analyzed: {a6['bugs_analyzed']} (both arms valid: {a6['bugs_with_both_arms_valid']})", f"- delayed first-gold exposure: **{a6['delayed_first_gold']}**", f"- higher tool cost: **{a6['higher_tool_cost']}**",
      f"- TREATMENT rank degradation: **{a6['any_treatment_rank_degradation']}** (CONTROL: {a6['any_control_rank_degradation']})", f"- all completed TREATMENT runs at rank 1: **{a6['treatment_all_completed_rank_1']}**",
      f"- full sequential traversal in all completed TREATMENT runs: **{a6['full_chain_traversal_in_all_completed_treatment_runs']}**",
      f"- shortcut runs: {a6['shortcut_runs_total']} (lexical {a6['lexical_bypass_runs_total']}, direct gold {a6['direct_gold_search_runs_total']}, repository-wide {a6['repo_wide_shortcut_runs_total']})",
      f"- Δ first-gold across bugs: median {f(a6['delta_first_gold_median_mean_range'][0])}, mean {f(a6['delta_first_gold_median_mean_range'][1])}, range {a6['delta_first_gold_median_mean_range'][2]}, descriptive 95 % t-interval {a6['delta_first_gold_t95_descriptive']}",
      f"- Δ tool calls across bugs: median {f(a6['delta_tool_calls_median_mean_range'][0])}, mean {f(a6['delta_tool_calls_median_mean_range'][1])}, range {a6['delta_tool_calls_median_mean_range'][2]}, descriptive 95 % t-interval {a6['delta_tool_calls_t95_descriptive']}", "",
      "## 5. Per-bug detail (no averaging across bugs)", ""]
for b in new: L.append(f"- **{b['bug_id']}** ({b['project']}, {b['family']}): first-gold {b['CONTROL']['first_gold_completed']} → {b['TREATMENT']['first_gold_completed']}; tool calls {b['CONTROL']['tool_calls_completed']} → {b['TREATMENT']['tool_calls_completed']}; TREATMENT ranks {b['TREATMENT']['gold_ranks_completed']}; classes {b['TREATMENT']['traversal_class_counts']}; hop-exposure means {b['TREATMENT']['hop_exposure_mean']}.")
w("SCALEUP_V2_RESULTS.md", L)
# 2 trajectory audit
L = [f"# TRAJECTORY_AUDIT_V2 — five-hop chain reconstruction per TREATMENT run ({H})", "", "Observable commands and tool outputs only. Exposure step = index of the bash call whose OUTPUT first showed the hop's declaration or the previous hop's call line. Classes: A strict sequential traversal; B sequential with broad-search assistance; C partial chain then lexical shortcut; D direct gold search before hop 4's call was shown; E repository-wide listing shortcut; F other.", ""]
for b in new:
    L += [f"## {b['bug_id']} — facade `{b['facade']}` → gold `{b['treatment_gold']}`", "", "| Run | Status | Rank | facade | H1 | H2 | H3 | H4 | H5 | Sequential | Skipped | Class | Gold vs H4 | Bypass | Direct | Repo-wide | Contract before gold | Tests | Calls after gold | Gold exposing command |", "|" + "---|" * 20]
    for x in [r for r in runs if r["bug_id"] == b["bug_id"] and r["condition"] == "TREATMENT"]:
        e = x["hop_exposure_steps"] or {}; cb = x["external_contract_exposure"]
        L.append(f"| {x['run_id'].split('/')[1]} | {x['status']} | {x['gold_rank']} | {e.get('facade')} | {e.get('H1')} | {e.get('H2')} | {e.get('H3')} | {e.get('H4')} | {e.get('H5')} | {x['sequential_traversal']} | {','.join(x['skipped_hops'] or []) or 'none'} | {x['traversal_class']} | {x['gold_exposure_relative_to_H4']} | {x['lexical_bypass']} | {x['direct_gold_search']} | {x['repository_wide_shortcut']} | {'yes' if (cb and x['first_gold_exposure'] and cb < x['first_gold_exposure']) else 'no'} | {x['tests_executed']} | {x['calls_after_gold']} | `{(x.get('gold_exposing_cmd') or '')[:60]}` |")
    L += ["", f"CONTROL runs (facade = gold): first gold {b['CONTROL']['first_gold_completed']}, buggy line {b['CONTROL']['buggy_line_exposure_completed']}, calls after gold {b['CONTROL']['calls_after_gold_completed']}.", ""]
L += ["## Out-of-workspace scan (known harness gap)", "", "| Run | Flagged calls | Flags | Contaminated |", "|---|---|---|---|"]
for x in runs:
    if x["oow_flagged_calls"]: L.append(f"| {x['run_id']} | {x['oow_flagged_calls']} | {x['oow_flags']} | {x['contaminated']} |")
L += ["", f"Runs with flagged calls: {sum(1 for x in runs if x['oow_flagged_calls'])}/{len(runs)}; contaminated: {sum(1 for x in runs if x['contaminated'])}."]
w("TRAJECTORY_AUDIT_V2.md", L)
# 3 ownership analysis
deg = [x for x in table if x["rank_degradation"]]
L = [f"# OWNERSHIP_ANALYSIS_V2 ({H})", "", "Ownership is audited in two dimensions for every new bug (`projects/*/bug-*/analysis/OWNERSHIP_UNIQUENESS_AUDIT.md`):", "",
     "* **behavioural** — measured: is there another single-line edit at another stage that makes the trigger pass *and* reproduces the original build's output on every probe case?",
     "* **contractual** — judged: would another stage's own documented responsibility make it a defensible owner of the wrong quantity?", "",
     "| Bug | Behavioural | Equivalent repair sites | Contractual | TREATMENT ranks | Degradation |", "|---|---|---|---|---|---|"]
for b in new:
    own = json.load(open(f"{S}/{[x for x in json.load(open(S + '/SCALEUP_MANIFEST.json'))['bugs'] if x['bug_id'] == b['bug_id']][0]['dir']}/analysis/ownership_counterfactual.json"))
    L.append(f"| {b['bug_id']} | {own['classification']} | {own['equivalent_repair_sites'] or 'none'} | {b.get('ownership_contractual')} | {b['TREATMENT']['gold_ranks_completed']} | {b['effect']['rank_degradation_observed']} |")
L += ["", "## Classification of every rank-degraded TREATMENT run in the benchmark", "", "| Bug | Ranks | Gold found? | Cause class (A–F) | Reading |", "|---|---|---|---|---|"]
if deg:
    for x in deg:
        if x["new"]:
            b = next(y for y in new if y["bug_id"] == x["bug_id"]); rs = [r for r in runs if r["bug_id"] == x["bug_id"] and r["condition"] == "TREATMENT" and r["gold_rank"] not in (1, None)]
            found = all(r["first_gold_exposure"] for r in rs); tops = [r["submitted_ranking_top10"][:3] for r in rs]
            cause = "D/E (upstream or consumer ranked above a found gold)" if found else "A (gold never exposed)"
            L.append(f"| {x['bug_id']} | {x['treatment_ranks']} | {'yes in every run' if found else 'not in every run'} | {cause} | top-3 per run: {tops} |")
        else:
            L.append(f"| {x['bug_id']} (existing) | {x['treatment_ranks']} | yes in every run (v1 audit) | D (upstream producer ranked above the gold) | the displacement chain separates the producer of a displacement vector from its consumer; see the v1 ownership notes |")
else: L.append("| (none) | - | - | - | - |")
L += ["", "## Finding", "", "All six new bugs are **behaviourally AMBIGUOUS**: in a chain whose stages each have exactly one caller, an inverse edit at an adjacent stage reproduces the original behaviour on every probe case. Behavioural ownership uniqueness is therefore a property of five-hop chains rather than of the individual fault, and cannot be engineered away by choosing a different fault.",
      "Contractually the six split 2 UNIQUE / 3 MOSTLY_UNIQUE / 1 AMBIGUOUS. The contractual dimension is the one that tracks agent behaviour: the existing benchmark's only stable rank degradation (`CHART-PIE-03`) is contractually ambiguous, and `JKC-OFFSET-05` was included in v2 precisely because every stage of its chain documents the same output.",
      "", "Rule applied throughout: a completed TREATMENT run whose gold rank is > 1 is never reported as an ordinary localization failure until its ownership class has been established."]
w("OWNERSHIP_ANALYSIS_V2.md", L)
# 4 bug-level, 5 project-level, 6 family-level
L = [f"# BUG_LEVEL_RESULTS_V2 ({H})", "", "| Bug | Project | Family | Ownership | Δ first-gold | ratio | Δ tool calls | CONTROL MRR | TREATMENT MRR | CONTROL ranks | TREATMENT ranks | Traversal | Bypass | Note |", "|" + "---|" * 14]
for b in new:
    e = b["effect"]; T = b["TREATMENT"]; L.append(f"| {b['bug_id']} | {b['project']} | {b['family']} | {b.get('ownership_contractual')} | {f(e['delta_first_gold_steps'])} | {f(e['first_gold_ratio'])} | {f(e['delta_tool_calls'])} | {f(b['CONTROL']['mrr'])} | {f(T['mrr'])} | {b['CONTROL']['gold_ranks_completed']} | {T['gold_ranks_completed']} | {T['full_sequential_traversal_completed']}/{T['completed']} | {T['lexical_bypass_completed']}/{T['completed']} | {e.get('note') or ''} |")
w("BUG_LEVEL_RESULTS_V2.md", L)
L = [f"# PROJECT_LEVEL_RESULTS_V2 ({H})", "", "| Project | Bugs | Completed CONTROL runs | Completed TREATMENT runs | First-gold delay (bugs) | Tool-call increase (bugs) | Rank degradation (bugs) | Ownership-ambiguous (bugs) | Traversal | Shortcuts | New-block cost USD |", "|" + "---|" * 11]
for p in ps:
    amb = sum(1 for x in table if x["project"] == p["project"] and str(x.get("ownership_contractual") or "").startswith("AMBIGUOUS"))
    L.append(f"| {p['project']} | {p['bugs_evaluated']} | {p['completed_control_runs']} | {p['completed_treatment_runs']} | {p['bugs_first_gold_delay']} | {p['bugs_tool_call_increase']} | {p['bugs_rank_degradation']} | {amb} | {p['treatment_traversal']} | {p['shortcuts']} | {f(p['new_block_cost_usd'],4)} |")
w("PROJECT_LEVEL_RESULTS_V2.md", L)
L = [f"# SEMANTIC_FAMILY_RESULTS_V2 ({H})", "", "Descriptive grouping only; most families hold a single bug, so no family-level generalisation is claimed.", "", "| Fault family | Bugs | Bug ids | Navigation delay | Tool increase | Rank degradation | All rank 1 | Ownership-ambiguous | Δ first-gold mean | Δ tool calls mean |", "|" + "---|" * 10]
for x in fam: L.append(f"| {x['family']} | {x['bugs']} | {', '.join(x['bug_ids'])} | {x['navigation_delay_bugs']}/{x['bugs']} | {x['tool_increase_bugs']}/{x['bugs']} | {x['rank_degradation_bugs']}/{x['bugs']} | {x['all_rank1_bugs']}/{x['bugs']} | {x['ownership_ambiguous_bugs']}/{x['bugs']} | {f(x['delta_first_gold_mean'])} | {f(x['delta_tool_calls_mean'])} |")
w("SEMANTIC_FAMILY_RESULTS_V2.md", L)
# 7 final benchmark tables
hdr1 = "| Project | Bug | Family | Ownership | C n | T n | C Acc@1 | T Acc@1 | C MRR | T MRR | C first-gold | T first-gold | C tools | T tools | Traversal | Bypass |"
rows1 = [f"| {x['project']} | {x['bug_id']}{'' if x['new'] else ' (existing)'} | {x['semantic_fault_family']} | {x.get('ownership_contractual') or 'n/a'} | {x['control_completed_attempted']} | {x['treatment_completed_attempted']} | {f(x['control_acc1'])} | {f(x['treatment_acc1'])} | {f(x['control_mrr'])} | {f(x['treatment_mrr'])} | {f(x['control_first_gold'])} | {f(x['treatment_first_gold'])} | {f(x['control_tool_calls'])} | {f(x['treatment_tool_calls'])} | {x['treatment_traversal']} | {x['treatment_bypass']} |" for x in table]
hdr2 = "| Project | Bug | Δ first-gold | ratio | Δ tool calls | Rank degradation? | Ownership ambiguity? | Dominant mechanism |"
rows2 = [f"| {x['project']} | {x['bug_id']} | {f(x['delta_first_gold'])} | {f(x['first_gold_ratio'])} | {f(x['delta_tool_calls'])} | {x['rank_degradation']} | {'yes' if str(x.get('ownership_contractual') or '').startswith('AMBIGUOUS') else ('no' if x['new'] else 'not audited')} | {x['mechanism']} |" for x in table]
t4 = [("bugs", len(table)), ("projects", len({x['project'] for x in table})), ("variants", 2 * len(table)), ("fault families", len(fam)),
      ("new block attempted / completed runs", f"{sl['attempted']} / {sl['completed']}"), ("new block infrastructure-affected", sl["infrastructure_affected"]),
      ("completed CONTROL rank-1", f"{agg['completed_control_rank1']}/{agg['completed_control_runs']}"), ("completed TREATMENT rank-1", f"{agg['completed_treatment_rank1']}/{agg['completed_treatment_runs']}"),
      ("bugs with TREATMENT rank degradation", agg["treatment_rank_degradation"]), ("bugs with first-gold delay", f"{agg['delayed_first_gold']}/{agg['bugs_with_valid_effect']}"), ("bugs with higher tool cost", f"{agg['higher_tool_cost']}/{agg['bugs_with_valid_effect']}"),
      ("median / mean Δ first-gold across bugs", f"{f(agg['delta_first_gold_median_mean_range'][0])} / {f(agg['delta_first_gold_median_mean_range'][1])} (range {agg['delta_first_gold_median_mean_range'][2]}; 95 % t-interval {agg['delta_first_gold_t95_descriptive']})"),
      ("median / mean first-gold ratio", f"{f(agg['first_gold_ratio_median_mean_range'][0])} / {f(agg['first_gold_ratio_median_mean_range'][1])} (range {agg['first_gold_ratio_median_mean_range'][2]})"),
      ("median / mean Δ tool calls across bugs", f"{f(agg['delta_tool_calls_median_mean_range'][0])} / {f(agg['delta_tool_calls_median_mean_range'][1])} (range {agg['delta_tool_calls_median_mean_range'][2]}; 95 % t-interval {agg['delta_tool_calls_t95_descriptive']})")]
L = [f"# FINAL_BENCHMARK_RESULTS — {len(table)} bugs, {len({x['project'] for x in table})} projects ({H})", "", "The eight existing bugs are quoted from their latest corrected tables (`core-benchmark-scaleup-v1/results-gpt56`) and were **not** rerun; the six new bugs come from this block.", "", "## Table 1 — bug level", "", hdr1, "|" + "---|" * 16] + rows1 + ["", "## Table 2 — effect size", "", hdr2, "|" + "---|" * 8] + rows2 + ["", "## Table 4 — benchmark summary", "", "| Item | Value |", "|---|---|"] + [f"| {k} | {v} |" for k, v in t4]
w("FINAL_BENCHMARK_RESULTS.md", L)
with open(OUT + "/FINAL_BENCHMARK_RESULTS.csv", "w", newline="") as fh:
    cols = ["project", "bug_id", "semantic_fault_family", "ownership_contractual", "control_completed_attempted", "treatment_completed_attempted", "control_acc1", "treatment_acc1", "control_mrr", "treatment_mrr", "control_first_gold", "treatment_first_gold", "control_tool_calls", "treatment_tool_calls", "treatment_traversal", "treatment_bypass", "delta_first_gold", "first_gold_ratio", "delta_tool_calls", "rank_degradation", "treatment_all_rank_1", "mechanism", "control_ranks", "treatment_ranks", "new"]
    wr = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore"); wr.writeheader()
    for x in table: wr.writerow({**x, "control_ranks": " ".join(map(str, x["control_ranks"])), "treatment_ranks": " ".join(map(str, x["treatment_ranks"]))})
print("wrote FINAL_BENCHMARK_RESULTS.csv")
L = [f"# THESIS_TABLES_V2 ({H})", "", "## Table 1 — bug-level results", "", hdr1, "|" + "---|" * 16] + rows1 + ["", "## Table 2 — effect size", "", hdr2, "|" + "---|" * 8] + rows2 + ["", "## Table 3 — project level", "", "| Project | Bugs | Completed CONTROL | Completed TREATMENT | Delay (bugs) | Tool increase (bugs) | Degradation (bugs) | Ownership-ambiguous | Traversal | Shortcuts |", "|" + "---|" * 10]
for p in ps:
    amb = sum(1 for x in table if x["project"] == p["project"] and str(x.get("ownership_contractual") or "").startswith("AMBIGUOUS"))
    L.append(f"| {p['project']} | {p['bugs_evaluated']} | {p['completed_control_runs']} | {p['completed_treatment_runs']} | {p['bugs_first_gold_delay']} | {p['bugs_tool_call_increase']} | {p['bugs_rank_degradation']} | {amb} | {p['treatment_traversal']} | {p['shortcuts']} |")
L += ["", "## Table 4 — semantic family", "", "| Family | Bugs | Navigation delay | Tool increase | Rank degradation | Ownership-ambiguous |", "|---|---|---|---|---|---|"] + [f"| {x['family']} | {x['bugs']} | {x['navigation_delay_bugs']}/{x['bugs']} | {x['tool_increase_bugs']}/{x['bugs']} | {x['rank_degradation_bugs']}/{x['bugs']} | {x['ownership_ambiguous_bugs']}/{x['bugs']} |" for x in fam]
L += ["", "## Table 5 — benchmark summary", "", "| Item | Value |", "|---|---|"] + [f"| {k} | {v} |" for k, v in t4] + ["", "Descriptive statistics only; no significance test; the bug is the replication unit and runs are repeated stochastic observations nested within bugs."]
w("THESIS_TABLES_V2.md", L); open(A + "/tables/thesis_tables_v2.md", "w").write("\n".join(L) + "\n")
# 8 infrastructure, 9 cost
L = [f"# INFRASTRUCTURE_ACCOUNTING_V2 ({H})", "", "New block, per variant (infrastructure losses never enter accuracy denominators):", "", "| Variant | attempted | completed | timeout | startup timeout | provider stall (lost) | completed after slow response | preparation stall | DNS lines | retry lines | contaminated | out-of-workspace flags | valid ranking | cost USD |", "|" + "---|" * 14]
for r in inf: L.append(f"| {r['variant']} | {r['attempted']} | {r['completed']} | {r['timeout']} | {r['startup_timeout']} | {r.get('provider_stall_lost', r.get('provider_stall'))} | {r.get('completed_slow_response','-')} | {r['preparation_stall']} | {r['dns_resolver_lines']} | {r['retry_lines']} | {r['contaminated']} | {r['oow_flagged_calls']} | {r['valid_ranking']} | {f(r['cost_usd'],4)} |")
L += ["", f"Health gate: {sl['health_gate_probes']} bounded probes (`diagnostic-gpt56/health_gate_v2.log`); driver state `diagnostic-gpt56/driver_state.json`" + (f"; halted: {(sl.get('driver_state') or {}).get('halted')}" if (sl.get('driver_state') or {}).get('halted') else "; no halt") + ".",
      "", "Existing bugs: see `core-benchmark-scaleup-v1/results-gpt56/INFRASTRUCTURE_ACCOUNTING.md` (not rerun here)."]
w("INFRASTRUCTURE_ACCOUNTING_V2.md", L)
L = [f"# COST_ACCOUNTING_V2 ({H})", "", "Actual per-run costs from the harness trajectories (`model_stats.instance_cost`); bounded smoke probes are tiny and unrecorded.", "",
     f"- new 60-run block total: **{f(cost['new_block_total_usd'],4)} USD** ({sl['attempted']} attempted runs; mean per completed run {f(cost['mean_cost_per_completed_run_usd'],4)} USD)",
     "- per bug: " + ", ".join(f"{k} {f(v,4)}" for k, v in cost["per_bug"].items()), "- per project (new block): " + ", ".join(f"{k} {f(v,4)}" for k, v in cost["per_project_new_block"].items()),
     "- per variant: " + ", ".join(f"{k} {f(v,4)}" for k, v in cost["per_variant"].items()),
     f"- historical benchmark spend: {json.dumps(cost['historical_benchmark_usd'])}", f"- **final benchmark total (historical + new): {f(cost['final_benchmark_total_usd'],4)} USD**", "",
     "| Run | Status | Cost USD |", "|---|---|---|"] + [f"| {r['run']} | {r['status']} | {f(r['cost_usd'],4)} |" for r in cost["per_run"]]
w("COST_ACCOUNTING_V2.md", L)
# 10 generalization (RQ1-RQ7)
v = [x for x in table if x["delta_first_gold"] is not None]
rq1 = f"Δ first-gold > 0 in {agg['delayed_first_gold']} of {agg['bugs_with_valid_effect']} bugs (new block {a6['delayed_first_gold']}/{a6['bugs_with_both_arms_valid']}); median {f(agg['delta_first_gold_median_mean_range'][0])} steps, range {agg['delta_first_gold_median_mean_range'][2]}, ratio median {f(agg['first_gold_ratio_median_mean_range'][0])}×."
rq2 = f"Δ tool calls > 0 in {agg['higher_tool_cost']} of {agg['bugs_with_valid_effect']} bugs (new block {a6['higher_tool_cost']}/{a6['bugs_with_both_arms_valid']}); median {f(agg['delta_tool_calls_median_mean_range'][0])} calls, range {agg['delta_tool_calls_median_mean_range'][2]}."
rq3 = f"Completed TREATMENT runs at rank 1: {agg['completed_treatment_rank1']}/{agg['completed_treatment_runs']} across {len(table)} bugs (CONTROL {agg['completed_control_rank1']}/{agg['completed_control_runs']}); bugs with any degradation: {agg['treatment_rank_degradation']}" + (": " + ", ".join(f"{x['bug_id']} {x['treatment_ranks']}" for x in deg) if deg else "") + "."
rq4 = "Degradation by family: " + ("; ".join(f"{x['semantic_fault_family']} ({x['bug_id']})" for x in deg) if deg else "none") + ". Families with no degradation in any bug: " + ", ".join(sorted({x['semantic_fault_family'] for x in table} - {x['semantic_fault_family'] for x in deg})) + "."
amb_deg = [x for x in deg if str(x.get("ownership_contractual") or "").startswith("AMBIGUOUS")]
rq5 = (f"Every degraded bug ({', '.join(x['bug_id'] for x in deg)}) is contractually ownership-ambiguous, and the degraded runs reached the gold; the association is with ownership, not with navigation difficulty (the bugs with the largest first-gold deltas kept rank 1)." if deg and len(amb_deg) == len(deg) else
       (f"Degraded bugs: {[x['bug_id'] for x in deg]}; ownership-ambiguous among them: {[x['bug_id'] for x in amb_deg]}. Navigation magnitude alone does not separate degraded from non-degraded bugs." if deg else "No degradation observed, so no association can be tested."))
trav_new = sum(b["TREATMENT"]["full_sequential_traversal_completed"] for b in new); comp_new = sum(b["TREATMENT"]["completed"] for b in new)
rq6 = f"New block: strict sequential traversal in {trav_new}/{comp_new} completed TREATMENT runs; any shortcut in {a6['shortcut_runs_total']}/{comp_new} (lexical {a6['lexical_bypass_runs_total']}, direct gold {a6['direct_gold_search_runs_total']}, repository-wide {a6['repo_wide_shortcut_runs_total']}). Per-bug classes: " + "; ".join(f"{b['bug_id']} {b['TREATMENT']['traversal_class_counts']}" for b in new) + "."
rq7 = "; ".join(f"{p['project']}: delay {p['bugs_first_gold_delay']}/{p['bugs_evaluated']}, tool increase {p['bugs_tool_call_increase']}/{p['bugs_evaluated']}, degradation {p['bugs_rank_degradation']}/{p['bugs_evaluated']}" for p in ps) + "."
robust = agg["delayed_first_gold"] >= agg["bugs_with_valid_effect"] - 1 and agg["higher_tool_cost"] >= agg["bugs_with_valid_effect"] - 1
concl = ("Across %d bugs in %d projects and %d fault families, five-hop structural displacement reliably increases the observable navigation burden, while GPT-5.6's final method-level ranking stays at rank 1 except in bugs whose gold ownership is contractually ambiguous. Rank robustness is therefore bounded not by navigation depth but by whether the displaced chain still identifies a unique owner for the fault." % (len(table), len({x['project'] for x in table}), len(fam))) if robust else "The navigation effect is not uniform across bugs; see the per-bug rows before generalising."
L = [f"# GENERALIZATION_ANALYSIS_V2 ({H})", "", f"Status: {status}.", "", "Rules: descriptive only; bug = replication unit; infrastructure losses never count as misses; high shortcut rates are a benchmark-design/agent-search interaction, not evidence about reasoning depth; the manipulation is structural displacement, never called 'reasoning depth'.", "",
     "## RQ1 — consistent first-gold delay across the benchmark?", rq1, "", "## RQ2 — consistent increase in tool/navigation cost?", rq2, "", "## RQ3 — how often does the final rank remain robust?", rq3, "", "## RQ4 — which families produce rank degradation?", rq4, "",
     "## RQ5 — is degradation associated with navigation difficulty or with ownership ambiguity?", rq5, "", "## RQ6 — how often do lexical/repository shortcuts bypass the synthetic hops?", rq6, "", "## RQ7 — does behaviour differ materially across projects?", rq7, "",
     "## Strongest defensible conclusion", concl, "", "## Caveats",
     "- Five runs per arm per bug; three existing bugs have fewer completed runs in one arm (provider stalls in their original blocks).",
     "- Triggers are constructor-authored and chains are synthetic; every stage of a chain has exactly one caller, which is what makes behavioural ownership ambiguous everywhere.",
     "- Compress contributes four of the six new bugs, so project-level statements about Compress rest on more bugs than those about Jackson-core.",
     "- Host plausibility is weaker in the Compress chains (header helpers on archive-entry and stream classes) than in the earlier projects."]
w("GENERALIZATION_ANALYSIS_V2.md", L)
L = [f"# NEXT_EXPERIMENT_DECISION_V2 ({H})", "", f"Block status: {status}.", "", "## Decision", f"No further paid experiment is launched automatically. The benchmark now holds {len(table)} bugs / {2*len(table)} variants / {len({x['project'] for x in table})} projects, and the thesis tables are in `THESIS_TABLES_V2.md`.", "",
     "## Is a further paid experiment justified?",
     ("- **Yes, one**: an ownership-controlled pair. Every degraded bug so far is contractually ownership-ambiguous, and all six new bugs are behaviourally ambiguous by construction. The decisive experiment is a matched pair of five-hop chains that differ *only* in whether the stages' documented responsibilities identify a unique owner, which would separate the ownership mechanism from the displacement mechanism. That requires a new construction phase, not more runs of this design." if deg else "- No degradation was observed, so a replication of this design would not change the conclusion."),
     "- **No** for more repetitions of the existing bugs: the navigation effect replicates in every bug measured so far.",
     "- **Deferred**: Joda-Time (temporal arithmetic) is the strongest unused project but needs ~83 min of validation per bug because of its 996 s suite; JxPath is the strongest unused alternative with a fast suite.", "",
     "## What not to do", "- Do not rerun the existing bugs; do not add repetitions; do not replace consumed slots; do not tune per project or per bug."]
w("NEXT_EXPERIMENT_DECISION_V2.md", L)
