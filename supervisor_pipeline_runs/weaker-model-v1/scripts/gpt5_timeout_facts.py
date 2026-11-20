"""Study 1 (revision after verification): every count quoted in the revised gpt5-timeouts/*.md that is not already a field of
timeline_runs.json, workload_speed.json, time_decomposition.json, malformed_commands.json or post_gold_reasoning.json.
Reads only those files, the frozen per_run.json, the gpt-5 ledger (block_w50.jsonl) and the gpt-5.5 held-out trajectories' tool-call
command strings (to check login-shell test use). Writes gpt5-timeouts/facts.json."""
import json, re, os, statistics as st
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); D = f"{ROOT}/gpt5-timeouts"
R = {r["run_id"]: r for r in json.load(open(f"{D}/timeline_runs.json"))}; S = json.load(open(f"{D}/timeline_steps.json"))
W = json.load(open(f"{D}/workload_speed.json")); WR = W["runs"]; TD = json.load(open(f"{D}/time_decomposition.json"))
MC = json.load(open(f"{D}/malformed_commands.json")); PG = json.load(open(f"{D}/post_gold_reasoning.json"))
PR = json.load(open(f"{ROOT}/analysis/per_run.json"))
TO = sorted(k for k, r in R.items() if r["outcome"] == "TIMEOUT"); CO = sorted(k for k, r in R.items() if r["outcome"] != "TIMEOUT")
med = lambda xs: round(st.median(xs), 1) if xs else None
def cliff(a, b):
    return round(sum((x > y) - (x < y) for x in a for y in b) / (len(a) * len(b)), 2) if a and b else None
F = {}
# 1. ledger: excluded records and their day / window
led = [json.loads(l) for l in open(f"{ROOT}/diagnostic/block_w50.jsonl")]
F["excluded_records"] = [{"run": x["run"], "verdict": x.get("verdict"), "final_gap_s": x.get("final_gap_s")} for x in led if x.get("verdict") != "valid"]
# 2. probes recorded before launch, per timeout
F["timeout_probe_counts"] = {k: len(R[k]["launch_probe_walls_s"] or []) for k in TO}
F["probe_walls_by_slot"] = sorted([(R[k]["slot_index"], k, R[k]["outcome"], R[k]["probe_wall_median_s"], WR[k]["in_window"]) for k in R])
# 3. final pending request at the kill
F["timeout_final_gap_s"] = {k: R[k]["final_gap_s"] for k in TO}
# 4. completed submission call duration, before / in window
F["completed_submit_call_s"] = {"pre_window": med([WR[k]["submit_call_s"] for k in CO if not WR[k]["in_window"]]),
                                 "in_window": med([WR[k]["submit_call_s"] for k in CO if WR[k]["in_window"]]),
                                 "pre_n": sum(1 for k in CO if not WR[k]["in_window"]), "in_n": sum(1 for k in CO if WR[k]["in_window"]),
                                 "range_all": [min(WR[k]["submit_call_s"] for k in CO), max(WR[k]["submit_call_s"] for k in CO)]}
F["speed_tok_s"] = {g: med([WR[k]["speed_tok_s_long_calls"] for k in ks if WR[k]["speed_tok_s_long_calls"]]) for g, ks in
                    {"pre_completed": [k for k in CO if not WR[k]["in_window"]], "in_completed": [k for k in CO if WR[k]["in_window"]],
                     "in_timeouts": [k for k in TO if WR[k]["in_window"]], "pre_timeouts": [k for k in TO if not WR[k]["in_window"]]}.items()}
# 5. outcomes by window x instance group
TI = sorted({R[k]["instance_id"] for k in TO})
F["outcomes_by_window"] = {f"{grp}_{w}": f"{sum(1 for k in R if (R[k]['instance_id'] in TI) == (grp == 'timeout_instances') and WR[k]['in_window'] == (w == 'in') and R[k]['outcome'] == 'TIMEOUT')}"
                           f"/{sum(1 for k in R if (R[k]['instance_id'] in TI) == (grp == 'timeout_instances') and WR[k]['in_window'] == (w == 'in'))}"
                           for grp in ("timeout_instances", "other_instances") for w in ("pre", "in")}
F["in_window_other_instance_output_tokens_median"] = med([WR[k]["output_tokens_total"] for k in R if R[k]["instance_id"] not in TI and WR[k]["in_window"]])
F["matched_comparators_in_window"] = sum(1 for k in CO if R[k]["instance_id"] in TI and WR[k]["in_window"])
F["counterfactual_with_submission_s"] = {k: WR[k]["counterfactual_with_submission_s"] for k in TO}
# 6. commitment delay (fault line -> submission request), completed runs, per instance
cd = {}
for k in CO: cd.setdefault(R[k]["instance_id"], []).append(R[k]["commitment_delay_s"])
F["commitment_delay_completed"] = {"all_range": [round(min(v for x in cd.values() for v in x), 1), round(max(v for x in cd.values() for v in x), 1)],
                                   "all_median": med([v for x in cd.values() for v in x]), "per_instance_median": {i: med(v) for i, v in sorted(cd.items())},
                                   "timeout_instance_medians_range": [min(med(cd[i]) for i in TI), max(med(cd[i]) for i in TI)]}
# gold -> kill vs comparator gold -> submission request
g2c = {}
for k in CO: g2c.setdefault(R[k]["instance_id"], []).append(R[k]["submit_call_created_s"] - R[k]["t_gold_any"])
F["gold_to_kill_vs_comparator_gold_to_commit"] = {k: (round(R[k]["wall_s"] - R[k]["t_gold_any"], 1), med(g2c[R[k]["instance_id"]])) for k in TO if R[k]["t_gold_any"] is not None}
# 7. tests: frozen TEST steps vs commands mentioning defects4j test; runs without a successful test
F["tests"] = {"frozen_test_executions_sum": sum(x["test_executions"] or 0 for x in PR if x["server"] == "w50" and x["tier"] == "HELDOUT" and x["included"]),
              "frozen_TEST_steps": sum(1 for k in R for s in S[k] if "TEST" in s["kinds"]),
              "commands_mentioning_defects4j_test": sum(MC[k]["test_calls"] for k in R), "login_shell_test_commands": sum(MC[k]["test_calls_login_shell"] for k in R),
              "java_version_failures": sum(MC[k]["test_calls_java_fail"] for k in R),
              "runs_no_test": {g: sum(1 for k in ks if MC[k]["test_calls"] == 0) for g, ks in (("TO", TO), ("CO", CO))},
              "runs_tests_all_failed": {g: sum(1 for k in ks if MC[k]["test_calls"] > 0 and MC[k]["test_calls"] == MC[k]["test_calls_java_fail"]) for g, ks in (("TO", TO), ("CO", CO))}}
F["tests"]["runs_no_successful_test"] = {g: F["tests"]["runs_no_test"][g] + F["tests"]["runs_tests_all_failed"][g] for g in ("TO", "CO")}
# gpt-5.5 held-out: any login-shell test command?
AG55 = f"{ROOT}/models/w55/benchmark_runs/mini-swe-agent-openai-gpt-5-5"; n55 = l55 = 0
VID = {r["instance_id"]: r["variant_id"] for r in R.values()}   # held-out instances share their variant ids across servers
for x in PR:
    if x["server"] == "w55" and x["tier"] == "HELDOUT" and x["included"]:
        t = json.load(open(f"{AG55}/{VID[x['instance_id']]}/{x['run']}/mini-swe-agent.traj.json"))
        for m in t["messages"]:
            for tc in (m.get("tool_calls") or []) if m.get("role") == "assistant" else []:
                try: c = json.loads((tc.get("function") or {}).get("arguments") or "{}").get("command", "")
                except Exception: c = ""
                if "defects4j test" in c: n55 += 1; l55 += bool(re.match(r"^\s*bash\s+-l", c.strip()))
F["gpt55_heldout_test_commands"] = {"commands": n55, "login_shell": l55}
# 8. brace commands
F["brace"] = {g: {"runs_with": sum(1 for k in ks if MC[k]["brace_cmds"]), "cmds": sum(MC[k]["brace_cmds"] for k in ks), "failed": sum(MC[k]["brace_cmds_failed"] for k in ks)} for g, ks in (("TO", TO), ("CO", CO))}
# 9. pace, with and without the submission call
def per_min(k, with_sub):
    r = R[k]; n = r["tool_calls"] - (0 if with_sub else (1 if r["submitted"] else 0)); return n / (r["wall_s"] / 60)
F["calls_per_minute"] = {"with_submission": {"TO": med([per_min(k, 1) for k in TO]), "CO": med([per_min(k, 1) for k in CO]), "delta": cliff([per_min(k, 1) for k in TO], [per_min(k, 1) for k in CO])},
                         "without_submission": {"TO": med([per_min(k, 0) for k in TO]), "CO": med([per_min(k, 0) for k in CO]), "delta": cliff([per_min(k, 0) for k in TO], [per_min(k, 0) for k in CO])}}
# 10. long calls: deliberation (>=1500 reasoning) and slow serving (<300 output, >=20 s), speed ranges among calls of >= 30 s
dl = [(s["completion_tokens"] or 0) / s["latency"] for k in R for s in S[k] if s["latency"] and s["latency"] >= 30 and (s["reasoning_tokens"] or 0) >= 1500]
sl = [(k, s["k"], s["latency"], s["completion_tokens"] or 0) for k in R for s in S[k] if s["latency"] and s["latency"] >= 20 and (s["completion_tokens"] or 0) < 300 and "TEST" not in s["kinds"]]
F["deliberation_calls_ge30s_tok_s_range"] = [round(min(dl), 1), round(max(dl), 1)] if dl else None
F["slow_serving_calls"] = {"n": len(sl), "by_run": {k: sum(1 for x in sl if x[0] == k) for k in sorted({x[0] for x in sl})},
                           "wait_range_s": [round(min(x[2] for x in sl), 1), round(max(x[2] for x in sl), 1)],
                           "tok_s_range": [round(min(x[3] / x[2] for x in sl), 2), round(max(x[3] / x[2] for x in sl), 1)], "outcomes": sorted({R[x[0]]["outcome"] for x in sl})}
# 11. non-exclusive deliberation per recipe (median over valid runs)
F["deliberation_any_by_recipe_median_s"] = {rc: med([TD[k]["deliberation_any"] for k in R if R[k]["recipe"] == rc]) for rc in ("HA", "HB", "HC")}
F["deliberation_any_timeouts"] = {k: TD[k]["deliberation_any"] for k in TO}
F["deliberation_any_completed_top"] = sorted(((TD[k]["deliberation_any"], k) for k in CO), reverse=True)[:5]
# 12. post-gold model-side measures (excluding runs that never reached the gold) and the matched comparison
pg_to = [k for k in TO if PG[k]["reached_gold"]]
F["post_gold"] = {m: {"TO": med([PG[k][m] for k in pg_to]), "CO": med([PG[k][m] for k in CO]), "delta": cliff([PG[k][m] for k in pg_to], [PG[k][m] for k in CO])}
                  for m in ("post_gold_calls", "post_gold_reasoning", "post_gold_output_tokens", "post_gold_delib_calls", "post_gold_model_time")}
mi = {k: R[k]["methods_inspected_after_gold"] for k in R}
F["post_gold"]["methods_inspected_after_gold"] = {"TO": med([mi[k] for k in pg_to]), "CO": med([mi[k] for k in CO]), "delta": cliff([mi[k] for k in pg_to], [mi[k] for k in CO])}
match = {}
for k in pg_to:
    comp = [c for c in CO if R[c]["instance_id"] == R[k]["instance_id"]]
    cr = st.median([PG[c]["post_gold_reasoning"] for c in comp]); cm = st.median([mi[c] for c in comp])
    match[k] = {"reasoning": PG[k]["post_gold_reasoning"], "comparator_reasoning": cr, "pct_more": round(100 * (PG[k]["post_gold_reasoning"] / cr - 1)) if cr else None,
                "methods": mi[k], "comparator_methods": cm, "n_comparators": len(comp)}
F["post_gold_matched"] = match
F["post_gold_matched_counts"] = {"more_reasoning": sum(1 for v in match.values() if v["reasoning"] > v["comparator_reasoning"]),
                                 "more_methods": sum(1 for v in match.values() if v["methods"] > v["comparator_methods"]), "n": len(match)}
F["decomposition_max_overshoot_s"] = max((round(TD[k]["accounted_s"] - TD[k]["wall_s"], 2), k) for k in R)
json.dump(F, open(f"{D}/facts.json", "w"), indent=1)
print(json.dumps(F, indent=1))
# 13. headroom: completed runs' wall time by instance group (how close to 300 s gpt-5 runs even when it completes)
F["completed_wall_s"] = {"timeout_instances": sorted(round(R[k]["wall_s"], 1) for k in CO if R[k]["instance_id"] in TI),
                         "other_instances": sorted(round(R[k]["wall_s"], 1) for k in CO if R[k]["instance_id"] not in TI)}
# 14. rule-based grouping of the timeouts. POST HOC: the rule was chosen after inspecting the per-run speeds and workloads; it is
#     stated so the grouping is reproducible, not because it was fixed in advance. It uses model-side output only:
#     WORKLOAD = output before the kill more than 10% above the comparators' median output before their submission call;
#     SERVING  = otherwise (the run had done no more work than a completed run, so the time it lacked went to slower serving).
#     Speed is reported alongside as corroboration, not used by the rule. Any threshold from 0% to +29% gives the same groups.
slow_runs = {x for x in F["slow_serving_calls"]["by_run"]}
grp = {}
for k in TO:
    comp = [c for c in CO if R[c]["instance_id"] == R[k]["instance_id"]]
    comp_pre = st.median([WR[c]["output_tokens_total"] - (WR[c]["submit_out_tokens"] or 0) for c in comp]); own = WR[k]["output_tokens_total"]
    sp = WR[k]["speed_tok_s_long_calls"]; slow = (sp is not None and sp < 50) or k in slow_runs
    grp[k] = {"group": "WORKLOAD" if own > 1.10 * comp_pre else "SERVING", "slow_speed_or_slow_call": slow, "speed_tok_s": sp, "output_before_kill": own,
              "comparator_output_before_submission": comp_pre, "pct_vs_comparator": round(100 * (own / comp_pre - 1)),
              "counterfactual_with_submission_s": WR[k]["counterfactual_with_submission_s"], "in_window": WR[k]["in_window"]}
F["timeout_groups"] = grp
F["timeout_group_speed_ranges"] = {g: [min(v["speed_tok_s"] for v in grp.values() if v["group"] == g), max(v["speed_tok_s"] for v in grp.values() if v["group"] == g)] for g in ("SERVING", "WORKLOAD")}
F["timeout_group_counts"] = {g: sorted(k for k, v in grp.items() if v["group"] == g) for g in ("SERVING", "WORKLOAD")}
json.dump(F, open(f"{D}/facts.json", "w"), indent=1)
print(json.dumps({k: F[k] for k in ("completed_wall_s", "timeout_group_speed_ranges", "timeout_group_counts")}, indent=1))
# 15. (round-2 verification) long waits by kind; slow-call token range; in-window completed submission range
lw = [(k, s) for k in R for s in S[k] if s["latency"] is not None and s["latency"] >= 30 and "TEST" not in s["kinds"]]
kind = lambda s: "deliberation" if (s["reasoning_tokens"] or 0) >= 1500 else ("slow_serving" if (s["completion_tokens"] or 0) < 300 else "neither")
F["long_waits_ge30s"] = {"non_test_calls": sum(1 for k in R for s in S[k] if s["latency"] is not None and "TEST" not in s["kinds"]), "n": len(lw),
                         "in_timeouts": sum(1 for k, s in lw if R[k]["outcome"] == "TIMEOUT"), "by_kind": {x: sum(1 for k, s in lw if kind(s) == x) for x in ("deliberation", "slow_serving", "neither")},
                         "neither_runs": sorted(f"{k} k{s['k']}" for k, s in lw if kind(s) == "neither"),
                         "neither_output_tokens_range": [min((s["completion_tokens"] or 0) for k, s in lw if kind(s) == "neither"), max((s["completion_tokens"] or 0) for k, s in lw if kind(s) == "neither")],
                         "neither_tok_s_range": [round(min((s["completion_tokens"] or 0) / s["latency"] for k, s in lw if kind(s) == "neither"), 1), round(max((s["completion_tokens"] or 0) / s["latency"] for k, s in lw if kind(s) == "neither"), 1)],
                         "neither_in_window": sum(1 for k, s in lw if kind(s) == "neither" and WR[k]["in_window"])}
F["slow_serving_calls"]["output_tokens_range"] = [min(x[3] for x in sl), max(x[3] for x in sl)]
iw = sorted(WR[k]["submit_call_s"] for k in CO if WR[k]["in_window"]); F["completed_submit_call_s"]["in_window_values"] = iw
# 16. visible assistant text (the message 'content' field only; no reasoning field is read) and validator rejections
AG50 = f"{ROOT}/models/w50/benchmark_runs/mini-swe-agent-openai-gpt-5"; vis = {}; rej = {}
for k in R:
    t = json.load(open(f"{AG50}/{k}/mini-swe-agent.traj.json"))
    vis[k] = sum(1 for m in t["messages"] if m.get("role") == "assistant" and isinstance(m.get("content"), str) and m["content"].strip())
    for m in t["messages"]:
        c = m.get("content") if isinstance(m.get("content"), str) else ""
        if m.get("role") == "tool" and "submission rejected" in c and "<output>" in c:
            body = c[c.index("<output>") + 8:]; body = body[:body.rindex("}") + 1]
            try: rej.setdefault(k, []).append([e.get("code") for e in json.loads(body).get("errors", [])])
            except Exception: rej.setdefault(k, []).append(["unparsed"])
F["assistant_messages_with_visible_text"] = {"runs_with_any": sum(1 for v in vis.values() if v), "n_runs": len(vis)}
F["validator_rejections"] = rej
# 17. CTV-E04F64/run-004: failed malformed commands and whole-file python prints (why its methods-after-gold count is large)
F["E04F64_run004_brace"] = {"brace_cmds": MC["CTV-E04F64/run-004"]["brace_cmds"], "brace_failed": MC["CTV-E04F64/run-004"]["brace_cmds_failed"]}
json.dump(F, open(f"{D}/facts.json", "w"), indent=1)
print(json.dumps({k: F[k] for k in ("long_waits_ge30s", "assistant_messages_with_visible_text", "validator_rejections")}, indent=1)); print(F["slow_serving_calls"], F["completed_submit_call_s"])
# 18. (round-2 inference verification)
# (a) slow period defined by measured speed, not by where the timeouts fall: the span of slots whose long-call speed was < 50 tok/s
sp_slots = sorted(WR[k]["slot"] for k in R if WR[k]["speed_tok_s_long_calls"] is not None and WR[k]["speed_tok_s_long_calls"] < 50)
lo, hi = min(sp_slots), max(sp_slots); inP = lambda k: lo <= WR[k]["slot"] <= hi
F["slow_period_by_speed"] = {"slots": [lo, hi], "start_utc": min(WR[k]["start_utc"] for k in R if inP(k)), "last_start_utc": max(WR[k]["start_utc"] for k in R if inP(k)),
    "speeds_in_period": sorted((WR[k]["slot"], WR[k]["speed_tok_s_long_calls"]) for k in R if inP(k)),
    "timeout_instances_in": f"{sum(1 for k in R if R[k]['instance_id'] in TI and inP(k) and R[k]['outcome'] == 'TIMEOUT')}/{sum(1 for k in R if R[k]['instance_id'] in TI and inP(k))}",
    "timeout_instances_out": f"{sum(1 for k in R if R[k]['instance_id'] in TI and not inP(k) and R[k]['outcome'] == 'TIMEOUT')}/{sum(1 for k in R if R[k]['instance_id'] in TI and not inP(k))}",
    "other_instances_in": f"{sum(1 for k in R if R[k]['instance_id'] not in TI and inP(k) and R[k]['outcome'] == 'TIMEOUT')}/{sum(1 for k in R if R[k]['instance_id'] not in TI and inP(k))}",
    "normal_speed_timeouts": sorted(k for k in TO if not inP(k)), "slow_period_timeouts": sorted(k for k in TO if inP(k))}
# (b) counterfactual calibration on completed pre-window runs: counterfactual exploration end + median submission vs actual wall
cal = [WR[k]["counterfactual_exploration_end_s"] + W["pre_window_short_wait_s"] + W["median_submission_tokens"] / W["pre_window_speed_tok_s"] - WR[k]["wall_s"] for k in CO if not WR[k]["in_window"]]
F["counterfactual_calibration_pre_window_completed"] = {"n": len(cal), "median_s": round(st.median(cal), 1), "range_s": [round(min(cal), 1), round(max(cal), 1)]}
# (c) post-gold model time re-timed at pre-window speed (same rule as the counterfactual)
def retimed_post(k):
    g = next((s["k"] for s in S[k] if s["gold_cov"] > 0 or s["gold_sig"]), None)
    return None if g is None else sum(min(s["latency"], W["pre_window_short_wait_s"] + (s["completion_tokens"] or 0) / W["pre_window_speed_tok_s"]) for s in S[k] if s["k"] > g and s["latency"] is not None and "TEST" not in s["kinds"])
rt_to = [retimed_post(k) for k in pg_to]; rt_co = [retimed_post(k) for k in CO]
F["post_gold_model_time_retimed"] = {"TO": med(rt_to), "CO": med(rt_co), "delta": cliff(rt_to, rt_co)}
# (d) cheap failed brace calls vs post-gold heavy-reasoning calls, per timeout (call_waits.json logic, from the steps directly)
CW = json.load(open(f"{D}/call_waits.json")); cwk = {}
for c in CW: cwk.setdefault(c["run_id"], []).append(c)
F["brace_cheap_vs_heavy"] = {}
for k in TO:
    g = next((s["k"] for s in S[k] if s["gold_cov"] > 0 or s["gold_sig"]), None)
    rows = cwk.get(k, [])
    F["brace_cheap_vs_heavy"][k] = {"cheap_brace_calls": sum(1 for c in rows if c["malformed"] and c["reasoning_tokens"] < 1000),
                                    "cheap_brace_s": round(sum(c["wait_s"] or 0 for c in rows if c["malformed"] and c["reasoning_tokens"] < 1000), 1),
                                    "post_gold_heavy_s": round(sum(c["wait_s"] or 0 for c in rows if g is not None and c["k"] > g and c["reasoning_tokens"] >= 1000 and not c["test"]), 1),
                                    "post_gold_heavy_brace_s": round(sum(c["wait_s"] or 0 for c in rows if g is not None and c["k"] > g and c["reasoning_tokens"] >= 1000 and c["malformed"]), 1)}
# (e) sensitivity of the output rule to the baseline: pooled median output before submission over all 17 completed runs
pool = st.median([WR[c]["output_tokens_total"] - (WR[c]["submit_out_tokens"] or 0) for c in CO])
F["output_rule_pooled_baseline"] = {"pooled_median": pool, "workload_if_pooled": sorted(k for k in TO if WR[k]["output_tokens_total"] > 1.10 * pool),
                                    "max_completed_pre_submission_output": max(WR[c]["output_tokens_total"] - (WR[c]["submit_out_tokens"] or 0) for c in CO)}
# (f) CTV-E04F64/run-005: gold to its (rejected) first submission
r5 = R["CTV-E04F64/run-005"]; sub = next((s for s in S["CTV-E04F64/run-005"] if "SUBMIT" in s["kinds"]), None)
F["E04F64_run005_gold_to_first_submission_s"] = round(sub["created"] - r5["t_gold_any"], 1) if sub else None
json.dump(F, open(f"{D}/facts.json", "w"), indent=1)
print(json.dumps({k: F[k] for k in ("slow_period_by_speed", "counterfactual_calibration_pre_window_completed", "post_gold_model_time_retimed", "brace_cheap_vs_heavy", "output_rule_pooled_baseline", "E04F64_run005_gold_to_first_submission_s")}, indent=1))
# 19. post-gold heavy-reasoning (>= 1,000 reasoning tokens) call time for the completed comparators, excluding the submission call
F["comparator_post_gold_heavy_s"] = {}
for c in CO:
    g = next((s["k"] for s in S[c] if s["gold_cov"] > 0 or s["gold_sig"]), None)
    F["comparator_post_gold_heavy_s"][c] = round(sum(x["wait_s"] or 0 for x in cwk.get(c, []) if g is not None and x["k"] > g and x["reasoning_tokens"] >= 1000 and not x["test"]), 1)
json.dump(F, open(f"{D}/facts.json", "w"), indent=1)
print({c: v for c, v in F["comparator_post_gold_heavy_s"].items() if R[c]["instance_id"] in TI})
