"""Study 1: timeout vs completed comparison for gpt-5 (w50), pooled and matched by instance. Descriptive only (n = 10 vs 17).
Reads gpt5-timeouts/timeline_runs.json (scripts/gpt5_timeline.py). Writes gpt5-timeouts/compare.json and prints tables."""
import json, statistics as st, os, collections
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
R = json.load(open(f"{ROOT}/gpt5-timeouts/timeline_runs.json"))
TO = [r for r in R if r["outcome"] == "TIMEOUT"]; CO = [r for r in R if r["outcome"] != "TIMEOUT"]
def med(xs): xs = [x for x in xs if x is not None]; return round(st.median(xs), 1) if xs else None
def cliffs(a, b):
    a = [x for x in a if x is not None]; b = [x for x in b if x is not None]
    if not a or not b: return None
    gt = sum(1 for x in a for y in b if x > y); lt = sum(1 for x in a for y in b if x < y); return round((gt - lt) / (len(a) * len(b)), 2)
for r in R:   # derived quantities
    r["gold_to_commit_s"] = round(r["submit_call_created_s"] - r["t_gold_any"], 1) if (r["submit_call_created_s"] is not None and r["t_gold_any"] is not None) else None
    r["gold_to_end_s"] = round(r["wall_s"] - r["t_gold_any"], 1) if r["t_gold_any"] is not None else None
    r["calls_per_min"] = round(r["tool_calls"] / (r["wall_s"] / 60), 2)
    r["exploration_calls"] = r["tool_outputs"]   # tool calls excluding the submission
    r["post_gold_exploration_calls"] = r["calls_after_gold"]
MEAS = [("model_calls", "model calls"), ("exploration_calls", "exploration tool calls (excl. submission)"), ("t_gold_any", "time to first gold display (s)"),
        ("t_fault_line", "time to faulty-line display (s)"), ("t_gold_full", "time to full gold read (s)"), ("t_evidence", "time to decisive evidence (s)"),
        ("t_first_test", "time to first test (s)"), ("calls_before_gold", "calls before gold"), ("post_gold_exploration_calls", "calls after gold"),
        ("searches_after_gold", "searches after gold"), ("reads_after_gold", "reads after gold"), ("tests_after_gold", "tests after gold"),
        ("methods_inspected_after_gold", "methods newly inspected after gold"), ("declared_alternatives_after_gold", "declared alternatives inspected after gold"),
        ("revisit_reads", "revisit reads"), ("repeated_cmds", "repeated identical commands"), ("latency_median_s", "median per-call wait (s, non-test)"),
        ("latency_max_s", "longest single wait (s)"), ("test_step_time_s", "time in test steps (s)"), ("reasoning_tokens_total", "reasoning tokens (total)"),
        ("reasoning_tokens_median", "reasoning tokens per call (median)"), ("seconds_per_1k_completion_tokens", "seconds per 1k output tokens"),
        ("probe_wall_median_s", "provider probe wall before launch (s)"), ("calls_per_min", "tool calls per minute")]
pooled = []
for k, lab in MEAS:
    a = [r[k] for r in TO]; b = [r[k] for r in CO]
    pooled.append({"measure": lab, "key": k, "timeout_median": med(a), "completed_median": med(b), "cliffs_delta_timeout_vs_completed": cliffs(a, b),
                   "timeout_n": sum(1 for x in a if x is not None), "completed_n": sum(1 for x in b if x is not None)})
print("POOLED (timeouts n=10 vs completed n=17)"); [print(f"  {p['measure']:46s} TO {str(p['timeout_median']):>7s}  CO {str(p['completed_median']):>7s}  delta {p['cliffs_delta_timeout_vs_completed']}") for p in pooled]
# matched by instance
inst = sorted({r["instance_id"] for r in TO}); matched = []
for i in inst:
    t = [r for r in TO if r["instance_id"] == i]; c = [r for r in CO if r["instance_id"] == i]
    for r in t:
        matched.append({"instance_id": i, "timeout_run": r["run_id"], "completed_runs": [x["run_id"] for x in c],
                        **{f"TO_{k}": r[k] for k in ("exploration_calls", "t_gold_any", "post_gold_exploration_calls", "methods_inspected_after_gold", "latency_median_s", "probe_wall_median_s", "final_gap_s", "test_step_time_s")},
                        **{f"CO_{k}": med([x[k] for x in c]) for k in ("exploration_calls", "t_gold_any", "post_gold_exploration_calls", "methods_inspected_after_gold", "latency_median_s", "probe_wall_median_s", "gold_to_commit_s", "submit_call_to_end_s", "test_step_time_s")}})
print("\nMATCHED (timeout vs completed runs on the same instance; completed values are medians)")
for m in matched:
    print(f"  {m['instance_id']:22s} {m['timeout_run']:20s} calls {m['TO_exploration_calls']:>3} vs {m['CO_exploration_calls']:>5} | gold@ {m['TO_t_gold_any']} vs {m['CO_t_gold_any']} | post-gold calls {m['TO_post_gold_exploration_calls']} vs {m['CO_post_gold_exploration_calls']} | methods after gold {m['TO_methods_inspected_after_gold']} vs {m['CO_methods_inspected_after_gold']} | wait med {m['TO_latency_median_s']} vs {m['CO_latency_median_s']} | probe {m['TO_probe_wall_median_s']} vs {m['CO_probe_wall_median_s']} | TO final pending {m['TO_final_gap_s']} | CO gold->commit {m['CO_gold_to_commit_s']} + submit {m['CO_submit_call_to_end_s']}")
# time ordering
print("\nRUN ORDER (slot, start, outcome, probe wall, median wait)")
for r in sorted(R, key=lambda r: r["start_utc"]):
    print(f"  {r['start_utc']} slot {r['slot_index']:>2} {r['outcome']:8s} {r['instance_id']:22s} probe {r['probe_wall_median_s']} wait {r['latency_median_s']} calls {r['tool_calls']}")
json.dump({"pooled": pooled, "matched": matched, "runs": R}, open(f"{ROOT}/gpt5-timeouts/compare.json", "w"), indent=1)
