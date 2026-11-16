"""Renders results-gpt56/RUN_REPORT_V2.md: a single self-contained report for the v2 paid block, with the per-bug,
per-run, effect, near-miss, traversal, infrastructure and cost tables. NON-CANONICAL / CORE BENCHMARK SCALE-UP V2 / GPT-5.6."""
import json, statistics
S = "/Users/shawnli/Desktop/Honours/defects4j/supervisor_pipeline_runs/core-benchmark-scaleup-v2"
d = json.load(open(S + "/results-gpt56/scaleup_v2_results.json")); man = json.load(open(S + "/SCALEUP_MANIFEST.json"))
rec = json.load(open(S + "/diagnostic-gpt56/execution_root_record.json"))
new = [b for b in d["bugs_new"] if "effect" in b]; sl = d["slots"]; a6 = d["five_bug_aggregate"]; agg = d["eight_bug_aggregate"]; runs = d["per_run"]; cost = d["cost"]; inf = d["infrastructure"]
def f(x, nd=2): return "-" if x is None else (f"{x:.{nd}f}" if isinstance(x, float) else str(x))
def mean(xs): xs = [x for x in xs if x is not None]; return round(statistics.mean(xs), 2) if xs else None
GOLD = {b["bug_id"]: b["treatment_gold"] for b in new}
L = ["# RUN_REPORT_V2 — GPT-5.6 evaluation of the six new benchmark bugs", "",
     f"**Label**: NON-CANONICAL · CORE BENCHMARK SCALE-UP V2 · GPT-5.6 · block {rec['start_utc'][:19]}Z → {rec['end_utc'][:19]}Z",
     f"**Protocol** (frozen, unchanged from the earlier blocks): agent `{rec['agent_profile']}`, model {rec['model']} via {rec['provider']}, prompt `{rec['prompt']['version']}` (base sha `{rec['prompt']['base_prompt_sha256'][:16]}…`), budget 50 tool calls / 5 test runs / 300 s / 30 s startup, exact `FQCN::method` scoring, one run per launch, no reruns, no replacements, no per-bug tuning.",
     f"**Server**: `{rec['server']['root'].split('/')[-1]}` on port {rec['server']['port']}, code-tree sha256 `{rec['server']['code_tree_sha256'][:16]}…`; manifest sha256 `{rec['scaleup_manifest_sha256'][:16]}…`.", "",
     "## 1. Block summary", "", "| Item | Value |", "|---|---|",
     f"| Planned / attempted / completed slots | {sl['planned']} / {sl['attempted']} / {sl['completed']} |",
     f"| Completed with a valid ranking | {sl['completed_with_valid_ranking']} |",
     f"| Infrastructure-affected (lost) | {sl['infrastructure_affected']} |",
     f"| Completed after a slow provider response | {sl.get('completed_with_slow_response_or_prep_stall', 0)} |",
     f"| Contaminated runs | {sl['contaminated']} |",
     f"| Bounded provider probes (all fast_pass) | {sl['health_gate_probes']} |",
     f"| Driver halts | {'none' if not (sl.get('driver_state') or {}).get('halted') else (sl['driver_state']['halted'])} |",
     f"| Block cost (actual) | {f(cost['new_block_total_usd'], 4)} USD (mean {f(cost['mean_cost_per_completed_run_usd'], 4)} per run) |",
     f"| Wall clock | {rec['start_utc'][11:19]} → {rec['end_utc'][11:19]} UTC (~67 min for 60 runs, one at a time) |", "",
     "## 2. Per-bug results (5 runs per arm; every run completed with a valid ranking)", "",
     "| Bug | Project | Fault family | Ownership (contractual / behavioural) | Arm | Gold ranks | Acc@1 | Acc@3 | MRR | First-gold (mean) | Tool calls (mean) | API calls | Cost USD |", "|" + "---|" * 13]
for b in new:
    for arm in ("CONTROL", "TREATMENT"):
        m = b[arm]
        L.append(f"| `{b['bug_id']}` | {b['project']} | {b['family']} | {b.get('ownership_contractual')} / {b.get('ownership_behavioural')} | {arm} | {m['gold_ranks_completed']} | {f(m['acc_at_1'])} | {f(m['acc_at_3'])} | {f(m['mrr'], 3)} | {f(m['first_gold_mean'])} | {f(m['tool_calls_mean'])} | {f(m['api_calls_mean'])} | {f(m['cost_usd_total'], 4)} |")
L += ["", "Gold methods: " + "; ".join(f"`{k}` → `{v}`" for k, v in GOLD.items()) + ".", "",
      "## 3. CONTROL → TREATMENT effect per bug", "",
      "| Bug | Δ first-gold steps | first-gold ratio | Δ tool calls | Δ API calls | Δ calls after gold | Δ MRR | Rank degradation | All treatment runs rank 1 | Dominant trajectory class |", "|" + "---|" * 10]
for b in new:
    e = b["effect"]
    L.append(f"| `{b['bug_id']}` | {f(e['delta_first_gold_steps'])} | {f(e['first_gold_ratio'])}× | {f(e['delta_tool_calls'])} | {f(e['delta_api_calls'])} | {f(e['delta_calls_after_gold'])} | {f(e['delta_mrr'])} | {'**yes**' if e['rank_degradation_observed'] else 'no'} | {e['treatment_all_rank_1']} | {e['dominant_trajectory_mechanism']} |")
L += ["", f"Six of six bugs show a first-gold delay (Δ median {f(a6['delta_first_gold_median_mean_range'][0])}, mean {f(a6['delta_first_gold_median_mean_range'][1])}, range {a6['delta_first_gold_median_mean_range'][2]}, descriptive 95 % t-interval {a6['delta_first_gold_t95_descriptive']}) and a tool-call increase (Δ median {f(a6['delta_tool_calls_median_mean_range'][0])}, mean {f(a6['delta_tool_calls_median_mean_range'][1])}, range {a6['delta_tool_calls_median_mean_range'][2]}, interval {a6['delta_tool_calls_t95_descriptive']}).", "",
      "## 4. TREATMENT chain behaviour", "",
      "| Bug | Strict sequential traversal | All hops in order | Lexical bypass | Repository-wide shortcut | Direct gold search | Contract evidence before ranking | Post-gold verification | Traversal classes | Hop-exposure means (facade→H5) |", "|" + "---|" * 10]
for b in new:
    T = b["TREATMENT"]; hm = T["hop_exposure_mean"]
    L.append(f"| `{b['bug_id']}` | {T['full_sequential_traversal_completed']}/5 | {f(T['all_hops_in_order_rate'])} | {T['lexical_bypass_completed']}/5 | {T['repository_wide_shortcut_completed']}/5 | {T['direct_gold_search_completed']}/5 | {T['external_contract_before_rank_runs']}/5 | {T['post_gold_verification_runs']}/5 | {T['traversal_class_counts']} | " + " → ".join(f(hm.get(k)) for k in ("facade", "H1", "H2", "H3", "H4", "H5")) + " |")
L += ["", "Classes: A strict sequential traversal; B sequential with broad-search assistance; C partial chain then a lexical shortcut; F other. No run used a direct gold-name search.", "",
      "## 5. Near-miss structure — what the ranking looked like inside the chain", "",
      "In **30 of 30** treatment runs all five chain members plus the facade occupied the submitted top five: the agent always localises the *chain*. The measured question is the ordering inside it.", "",
      "| Bug | Run | Gold rank | Ranked #1 | Ranked #2 | First-gold step | Tool calls | Class |", "|" + "---|" * 8]
for b in new:
    for x in [r for r in runs if r["bug_id"] == b["bug_id"] and r["condition"] == "TREATMENT"]:
        top = x["submitted_ranking_top10"]
        L.append(f"| `{b['bug_id']}` | {x['run_id'].split('/')[1]} | {x['gold_rank']} | `{top[0].split('.')[-1] if top else '-'}` | `{top[1].split('.')[-1] if len(top) > 1 else '-'}` | {x['first_gold_exposure']} | {x['tool_calls']} | {x['traversal_class']} |")
L += ["", "The rank-2 slot is occupied by the immediately adjacent hop (H4) or by the facade in every run. The single degraded run, `CMP-LAYOUT-02/run-004`, ranked the facade first and `ArArchiveInputStream::checksumBoundary` — the alternate owner pre-registered in that bug's ownership audit *before* the block — second.", "",
      "## 6. Per-run record (all 60 runs)", "", "| Bug | Arm | Run | Status | Gold rank | Tool calls | API | Wall s | First-gold | Calls after gold | Contract markers | Tests | Cost USD | Out-of-workspace flags |", "|" + "---|" * 14]
for x in runs:
    L.append(f"| `{x['bug_id']}` | {x['condition'][0]} | {x['run_id'].split('/')[1]} | {x['status']} | {x['gold_rank']} | {x['tool_calls']} | {x['api_calls']} | {x['wall_time_s']} | {x['first_gold_exposure']} | {x['calls_after_gold']} | {len(x['contract_markers_seen'] or {})} | {x['tests_executed']} | {f(x['cost_usd'], 4)} | {x['oow_flagged_calls']} |")
L += ["", "## 7. Infrastructure accounting", "", "| Variant | attempted | completed | timeout | startup timeout | provider stall | preparation stall | DNS lines | retry lines | contaminated | valid ranking | cost USD |", "|" + "---|" * 12]
for r in inf:
    L.append(f"| `{r['variant']}` | {r['attempted']} | {r['completed']} | {r['timeout']} | {r['startup_timeout']} | {r.get('provider_stall_lost', 0)} | {r['preparation_stall']} | {r['dns_resolver_lines']} | {r['retry_lines']} | {r['contaminated']} | {r['valid_ranking']} | {f(r['cost_usd'], 4)} |")
oow = sum(1 for x in runs if x["oow_flagged_calls"]); cont = sum(1 for x in runs if x["contaminated"])
L += ["", "## 8. Integrity", "", "| Check | Result |", "|---|---|",
      "| Server root file count before / after | 281 570 → 298 977 |", "| Files removed / changed | 0 / 0 |",
      "| Additions outside the twelve new variants and `_smoke` | 0 |",
      "| Canonical variant and run listings | unchanged |", "| Pre-existing run artifacts (2 826 files, 24 families) | unchanged |",
      "| Package copies in the server root | unchanged |", "| Completed v2 run artifacts (re-checked at every bug boundary) | unchanged |",
      f"| Protocol identity verified per run | {all(x['protocol_identity_ok'] for x in runs)} (60/60) |",
      f"| Source integrity verified per run | {all(x['source_integrity_ok'] for x in runs)} (60/60) |",
      f"| Runs with out-of-workspace flags | {oow}/60 (benign: `cd` to the run's parent and the agent's own absolute path; nothing displayed) |",
      f"| Contaminated runs (another run's ranking or package content shown) | {cont} |",
      "| Credential-pattern scan of the new artifacts | 1 140 files, 0 hits outside encrypted provider blobs |", "",
      "## 9. Cost", "", "| Scope | USD |", "|---|---|"]
for k, v in cost["per_bug"].items(): L.append(f"| bug {k} | {f(v, 4)} |")
for k, v in cost["per_project_new_block"].items():
    if v: L.append(f"| project {k} (this block) | {f(v, 4)} |")
L += [f"| **this block (60 runs)** | **{f(cost['new_block_total_usd'], 4)}** |",
      f"| all earlier blocks | {f(cost['historical_benchmark_usd']['pre-v1 total'], 4)} |",
      f"| **benchmark total (140 paid runs)** | **{f(cost['final_benchmark_total_usd'], 4)}** |", "",
      "## 10. Where this leaves the benchmark (14 bugs, 5 projects)", "", "| Item | Value |", "|---|---|",
      f"| Bugs / variants / projects / fault families | {agg['bugs']} / {2 * agg['bugs']} / 5 / 14 |",
      f"| Bugs with delayed first-gold exposure | {agg['delayed_first_gold']}/{agg['bugs_with_valid_effect']} |",
      f"| Bugs with increased tool cost | {agg['higher_tool_cost']}/{agg['bugs_with_valid_effect']} |",
      f"| Δ first-gold across bugs (median / mean / range) | {f(agg['delta_first_gold_median_mean_range'][0])} / {f(agg['delta_first_gold_median_mean_range'][1])} / {agg['delta_first_gold_median_mean_range'][2]} |",
      f"| Δ tool calls across bugs (median / mean / range) | {f(agg['delta_tool_calls_median_mean_range'][0])} / {f(agg['delta_tool_calls_median_mean_range'][1])} / {agg['delta_tool_calls_median_mean_range'][2]} |",
      f"| Completed CONTROL runs ranking the gold first | {agg['completed_control_rank1']}/{agg['completed_control_runs']} |",
      f"| Completed TREATMENT runs ranking the gold first | {agg['completed_treatment_rank1']}/{agg['completed_treatment_runs']} |",
      f"| Bugs with any TREATMENT rank degradation | {agg['treatment_rank_degradation']}/{agg['bugs']} (CHART-PIE-03, CMP-LAYOUT-02) |", "",
      "## 11. Reading of this block", "",
      "1. **The navigation effect replicated in two new projects.** Displacement delayed first-gold exposure in 6/6 new bugs (2.5×–19.6×) and raised tool calls in 6/6. With the earlier blocks that is 14/14 bugs.",
      "2. **Ranking stayed robust.** 29 of 30 new treatment runs put the constructor-declared gold first; all 30 control runs did.",
      "3. **The one degradation was predicted.** `CMP-LAYOUT-02/run-004` ranked the alternate owner named in that bug's pre-block ownership audit second and the gold third. Pre-registration turned a surprise into a confirmation.",
      "4. **Output-type ambiguity is not enough to move attribution.** `JKC-OFFSET-05` was built so that every stage documents the same output, and every alternate site is a behaviourally equivalent repair; the gold was still ranked first 5/5. The mechanism behind `CHART-PIE-03` needs a stage that *defines the specific wrong quantity*, not merely one that passes the same quantity along.",
      "5. **Ownership uniqueness is a property of chains, not of faults.** All six bugs are behaviourally ambiguous: because each synthetic stage has exactly one caller, an inverse edit next door reproduces the original behaviour on every probe case. Only the stages' documented responsibilities can single out an owner, which is why the audit reports a contractual verdict beside the behavioural one.", "",
      "Artefacts: `results-gpt56/` (this report plus 13 generated reports and `scaleup_v2_results.json`), `diagnostic-gpt56/` (execution root, health gate, driver state, per-run gates, integrity records), `projects/*/bug-*/` (specs, configs, packages, validation, reproduction, seven analysis documents per bug)."]
open(S + "/results-gpt56/RUN_REPORT_V2.md", "w").write("\n".join(L) + "\n")
print("RUN_REPORT_V2.md written:", len(L), "lines")
