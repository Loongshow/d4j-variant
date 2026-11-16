"""Builds results-gpt56/: scaleup_gpt56_results.json + all markdown/CSV reports from the per-bug analyzer outputs (observable artifacts only), the driver/post-run
records, phase timing, out-of-workspace scans, and the existing three bugs' latest corrected final tables. Descriptive statistics only; the BUG is the unit for
cross-benchmark statements; infrastructure-affected runs are never counted as localization misses. NON-CANONICAL / CORE BENCHMARK SCALE-UP / GPT-5.6 EXECUTION."""
import json, os, glob, csv, statistics, datetime, math, re
S = "/Users/shawnli/Desktop/Honours/defects4j/supervisor_pipeline_runs/core-benchmark-scaleup-v1"; R = os.path.dirname(S); A = S + "/results-gpt56/analysis"; OUT = S + "/results-gpt56"; SU = S + "/diagnostic-gpt56"
LABEL = "NON-CANONICAL / CORE BENCHMARK SCALE-UP / GPT-5.6 EXECUTION"
BUGS = [("CHART-POLAR-02", "Chart", "PolarPlot#translateValueThetaRadiusToJava2D", "denominator choice / normalization", "LineUtilities#stretch"),
        ("CHART-PIE-03", "Chart", "PiePlot#getArcBounds", "offset direction (sign)", "ShapeUtilities#shift"),
        ("MATH-BICUBIC-02", "Math", "BicubicSplineInterpolator#interpolate", "scale factor (x4 denominator)", "DividedDifferenceInterpolator#warp"),
        ("MATH-HARMONIC-03", "Math", "HarmonicFitter$ParameterGuesser#guessAOmega", "offset vs absolute (span)", "SummaryStatistics#span"),
        ("LANG-FOLD-02", "Lang", "CharSequenceUtils#regionMatches", "normalization (case folding)", "CharSet#akin")]
def rj(p):
    try: return json.load(open(p))
    except Exception: return None
def mean(xs): xs = [x for x in xs if x is not None]; return round(statistics.mean(xs), 2) if xs else None
def median(xs): xs = [x for x in xs if x is not None]; return statistics.median(xs) if xs else None
def f(x, nd=2): return "-" if x is None else (f"{x:.{nd}f}" if isinstance(x, float) else str(x))
def wilson(k, n, z=1.96):
    if not n: return None
    p = k / n; d = 1 + z * z / n; c = p + z * z / (2 * n); h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)); return [round((c - h) / d, 3), round((c + h) / d, 3)]
def tci(xs):  # descriptive 95% t-interval on bug-level values
    xs = [x for x in xs if x is not None]; n = len(xs)
    if n < 2: return None
    tq = {2: 12.706, 3: 4.303, 4: 3.182, 5: 2.776, 6: 2.571, 7: 2.447, 8: 2.365, 9: 2.306, 10: 2.262}.get(n, 2.0); m = statistics.mean(xs); s = statistics.stdev(xs); return [round(m - tq * s / math.sqrt(n), 2), round(m + tq * s / math.sqrt(n), 2)]
post = {}
for l in open(SU + "/block_su.log") if os.path.exists(SU + "/block_su.log") else []:
    try: r = json.loads(l); post[r["run"]] = r
    except Exception: pass
timing = {t["run"]: t for t in (rj(A + "/per_run/phase_timing_su.json") or [])}
oow = rj(A + "/per_run/out_of_workspace_scan_su.json") or {"runs": {}, "summary": {}}
def route_class(r):
    """Map the analyzer's route label to the brief's classes A-F (+ n/a)."""
    if r["arm"] != "TREATMENT": return "n/a"
    c = r["chain"]; lab = c.get("route", ""); reached = c.get("reached", {}); hops_reached = sum(1 for t in ("H1", "H2", "H3", "H4") if reached.get(t))
    if r["gold_first_exposed_step"] is None: return "n/a (no gold exposure: %s)" % ("timeout" if r["status"] == "timeout" else r["status"])
    if lab.startswith("A."): return "A"
    if lab.startswith("A'"): return "B"
    if lab.startswith("B/C"): return "E" if (c.get("repository_wide_shortcut") and hops_reached < 2) else "C"
    if lab.startswith("D."): return "D"
    return "F"
def gold_vs_h4(r):
    if r["arm"] != "TREATMENT" or r["gold_first_exposed_step"] is None: return None
    e = r["chain"]["exposure_steps"]; h4 = e.get("H4"); g = r["gold_first_exposed_step"]; via = (r["chain"].get("via_chain_per_hop") or {}).get("H5")
    if h4 is None or g < h4: return "before H4"
    if r["gold_decl_first_shown"] == g and via: return "strictly through H5 declaration (after H4's call line)"
    return "after H4"
def per_run_row(r, pair, proj, family):
    i = r["info_distance"]; c = r["chain"]; pr = post.get(r["run_id"], {}); tm = timing.get(r["run_id"], {}); ow = (oow.get("runs") or {}).get(r["run_id"]) or {}
    lost = r["status"] != "completed"; slow = (r["status"] == "completed") and (bool(r["timing"].get("stalled_request")) or bool(tm.get("preparation_stalled"))); infra = lost
    return {"project": proj, "bug_id": pair, "condition": r["arm"], "run_id": r["run_id"], "status": r["status"], "completed": r["status"] == "completed", "infrastructure_affected": infra,
            "stall_kind": r["timing"].get("stall_kind"), "completed_with_slow_response_or_prep_stall": slow, "max_gap_s": r["timing"].get("max_inter_response_gap_s"), "preparation_s": tm.get("preparation_s"), "gold_method": r["gold"], "submitted_ranking_top10": r["top10"], "ranking_submitted": bool(r["top10"]), "gold_rank": r["gold_rank"],
            "acc_at_1": r["hit_at_1"], "acc_at_3": r["hit_at_3"], "acc_at_5": r["hit_at_5"], "acc_at_10": r["hit_at_10"], "reciprocal_rank": r["reciprocal_rank"], "tool_calls": r["tool_call_count"], "api_calls": r["api_calls"],
            "wall_time_s": r["timing"].get("wall_clock_s"), "agent_process_s": round((r["timing"].get("duration_ms") or 0) / 1000) or None, "cost_usd": r["cost_usd"], "first_command": i.get("first_command"), "first_search": i.get("first_search"), "first_search_step": i.get("first_search_idx"),
            "first_facade_exposure": (r["nodes"].get("facade") or {}).get("first_exposed") if r["arm"] == "TREATMENT" else r["gold_first_exposed_step"], "first_gold_exposure": r["gold_first_exposed_step"], "buggy_line_exposure": r["buggy_line_first_shown"], "gold_decl_exposure": r["gold_decl_first_shown"],
            "external_contract_exposure": r["first_contract_step"], "contract_markers_seen": {k: v for k, v in r["contract_first_shown"].items() if v}, "contract_markers_after_gold": i.get("contract_markers_after_gold"), "calls_after_gold": i.get("calls_after_first_gold"),
            "tests_executed": i.get("tests_executed_count"), "source_files_opened": len(i.get("source_files_opened") or []), "source_files_opened_list": i.get("source_files_opened"), "unique_search_queries": i.get("unique_search_queries"), "javap_jshell_steps": i.get("javap_jshell_steps"),
            "hop_exposure_steps": c.get("exposure_steps"), "route_label_analyzer": c.get("route"), "traversal_class": route_class(r), "gold_exposure_relative_to_H4": gold_vs_h4(r), "sequential_traversal": c.get("followed_all_five_sequentially"), "all_hops_in_order": c.get("sequential_order"),
            "skipped_hops": c.get("skipped_hops"), "lexical_bypass": c.get("lexical_bypass"), "repository_wide_shortcut": c.get("repository_wide_shortcut"), "direct_gold_search": c.get("direct_gold_search"), "gold_exposed_by_name": c.get("gold_exposed_by_name"), "via_chain_per_hop": c.get("via_chain_per_hop"),
            "post_gold_searches": i.get("post_gold_searches"), "post_gold_opens": i.get("post_gold_opens"), "novel_search_vocabulary": r["novel_search_vocabulary"], "source_integrity_ok": r["source_integrity_ok"], "protocol_identity_ok": pr.get("protocol_identity_ok"), "prompt_version": r["prompt_version"],
            "retry_lines": r["timing"].get("provider_retry_lines"), "dns_error_lines": tm.get("dns_error_lines"), "oow_flagged_calls": len(ow.get("flagged_calls") or []), "oow_flags": [x.get("flags") for x in (ow.get("flagged_calls") or [])][:6], "contaminated": bool(ow.get("contaminated")), "post_run_verdict": pr.get("verdict"),
            "agent_reported_evidence_chain_unverified": r.get("agent_reported_evidence_chain_unverified")}
def arm_metrics(rows, arm):
    rs = [x for x in rows if x["condition"] == arm]; comp = [x for x in rs if x["completed"]]; valid = [x for x in comp if x["ranking_submitted"]]; infra = [x for x in rs if x["infrastructure_affected"]]
    ranks = [x["gold_rank"] for x in valid]; n = len(valid)
    m = {"attempted": len(rs), "completed": len(comp), "completed_with_valid_ranking": n, "infrastructure_affected_lost": len(infra), "completed_with_slow_response_or_prep_stall": sum(1 for x in comp if x["completed_with_slow_response_or_prep_stall"]),
         "statuses": [x["status"] for x in rs], "gold_ranks_completed": ranks, "gold_ranks_all": [x["gold_rank"] for x in rs],
         "acc_at_1": (sum(1 for r in ranks if r == 1) / n) if n else None, "acc_at_3": (sum(1 for r in ranks if r and r <= 3) / n) if n else None, "acc_at_5": (sum(1 for r in ranks if r and r <= 5) / n) if n else None, "acc_at_10": (sum(1 for r in ranks if r and r <= 10) / n) if n else None,
         "mrr": (sum((1 / r) if r else 0 for r in ranks) / n) if n else None, "acc_at_1_wilson95": wilson(sum(1 for r in ranks if r == 1), n),
         "first_gold_completed": [x["first_gold_exposure"] for x in comp], "first_gold_mean": mean([x["first_gold_exposure"] for x in comp]), "first_gold_median": median([x["first_gold_exposure"] for x in comp]), "first_gold_all_runs": [x["first_gold_exposure"] for x in rs],
         "tool_calls_completed": [x["tool_calls"] for x in comp], "tool_calls_mean": mean([x["tool_calls"] for x in comp]), "tool_calls_median": median([x["tool_calls"] for x in comp]), "tool_calls_all_runs": [x["tool_calls"] for x in rs],
         "api_calls_completed": [x["api_calls"] for x in comp], "api_calls_mean": mean([x["api_calls"] for x in comp]), "wall_time_completed": [x["wall_time_s"] for x in comp], "wall_time_mean": mean([x["wall_time_s"] for x in comp]),
         "calls_after_gold_completed": [x["calls_after_gold"] for x in comp], "calls_after_gold_mean": mean([x["calls_after_gold"] for x in comp]), "buggy_line_exposure_completed": [x["buggy_line_exposure"] for x in comp],
         "external_contract_before_rank_runs": sum(1 for x in comp if x["external_contract_exposure"]), "external_contract_evidence_rate": (sum(1 for x in comp if x["external_contract_exposure"]) / len(comp)) if comp else None, "contract_markers_after_gold_runs": sum(1 for x in comp if x["contract_markers_after_gold"]),
         "tests_executed_completed": [x["tests_executed"] for x in comp], "source_files_opened_completed": [x["source_files_opened"] for x in comp], "unique_search_queries_completed": [x["unique_search_queries"] for x in comp],
         "cost_usd_total": round(sum(x["cost_usd"] or 0 for x in rs), 4), "cost_usd_per_run": [x["cost_usd"] for x in rs], "cost_usd_mean_completed": mean([x["cost_usd"] for x in comp]),
         "source_integrity_ok_all": all(x["source_integrity_ok"] for x in rs) if rs else None, "protocol_identity_ok_all": all(x["protocol_identity_ok"] for x in rs if x["post_run_verdict"]) if rs else None, "contaminated_runs": [x["run_id"] for x in rs if x["contaminated"]], "oow_flagged_calls_total": sum(x["oow_flagged_calls"] for x in rs),
         "provider_retry_lines_total": sum(x["retry_lines"] or 0 for x in rs), "dns_error_lines_total": sum(x["dns_error_lines"] or 0 for x in rs)}
    if arm == "TREATMENT":
        m.update({"traversal_classes": {x["run_id"].split("/")[1]: x["traversal_class"] for x in rs}, "traversal_class_counts": {k: sum(1 for x in rs if x["traversal_class"] == k) for k in sorted({x["traversal_class"] for x in rs})},
                  "full_sequential_traversal_completed": sum(1 for x in comp if x["sequential_traversal"]), "full_sequential_traversal_rate": (sum(1 for x in comp if x["sequential_traversal"]) / len(comp)) if comp else None,
                  "all_hops_in_order_rate": (sum(1 for x in comp if x["all_hops_in_order"]) / len(comp)) if comp else None, "lexical_bypass_completed": sum(1 for x in comp if x["lexical_bypass"]), "lexical_bypass_rate": (sum(1 for x in comp if x["lexical_bypass"]) / len(comp)) if comp else None,
                  "direct_gold_search_completed": sum(1 for x in comp if x["direct_gold_search"]), "direct_gold_search_rate": (sum(1 for x in comp if x["direct_gold_search"]) / len(comp)) if comp else None,
                  "repository_wide_shortcut_completed": sum(1 for x in comp if x["repository_wide_shortcut"]), "shortcut_any_completed": sum(1 for x in comp if x["lexical_bypass"] or x["repository_wide_shortcut"] or x["direct_gold_search"]), "shortcut_rate": (sum(1 for x in comp if x["lexical_bypass"] or x["repository_wide_shortcut"] or x["direct_gold_search"]) / len(comp)) if comp else None,
                  "gold_exposure_relative_to_H4": {x["run_id"].split("/")[1]: x["gold_exposure_relative_to_H4"] for x in rs}, "hop_exposure_mean": {t: mean([(x["hop_exposure_steps"] or {}).get(t) for x in comp]) for t in ("facade", "H1", "H2", "H3", "H4", "H5")},
                  "skipped_hops_completed": [x["skipped_hops"] for x in comp], "post_gold_verification_runs": sum(1 for x in comp if (x["post_gold_searches"] or x["post_gold_opens"] or x["tests_executed"])), "novel_vocab_events": sum(len(x["novel_search_vocabulary"] or []) for x in rs)})
    return m
bugs_out = []; all_rows = []
for pair, proj, facade, family, tgold in BUGS:
    d = rj(f"{A}/per_bug/{pair}_results.json")
    if not d: bugs_out.append({"bug_id": pair, "project": proj, "facade": facade, "family": family, "treatment_gold": tgold, "note": "no analysis yet"}); continue
    rows = [per_run_row(r, pair, proj, family) for r in d["runs"]]; all_rows += rows
    C = arm_metrics(rows, "CONTROL"); T = arm_metrics(rows, "TREATMENT")
    def eff(a, b, key): return round(b[key] - a[key], 2) if (a.get(key) is not None and b.get(key) is not None) else None
    effect = {"delta_first_gold_steps": eff(C, T, "first_gold_mean"), "first_gold_ratio": (round(T["first_gold_mean"] / C["first_gold_mean"], 2) if (C.get("first_gold_mean") and T.get("first_gold_mean")) else None),
              "delta_tool_calls": eff(C, T, "tool_calls_mean"), "delta_api_calls": eff(C, T, "api_calls_mean"), "delta_calls_after_gold": eff(C, T, "calls_after_gold_mean"), "delta_mrr": eff(C, T, "mrr"),
              "rank_degradation_observed": bool(any(r != 1 for r in T["gold_ranks_completed"])) if T["gold_ranks_completed"] else None, "control_rank_degradation_observed": bool(any(r != 1 for r in C["gold_ranks_completed"])) if C["gold_ranks_completed"] else None,
              "treatment_all_rank_1": (all(r == 1 for r in T["gold_ranks_completed"]) if T["gold_ranks_completed"] else None), "dominant_trajectory_mechanism": (max(T["traversal_class_counts"].items(), key=lambda kv: kv[1])[0] if T.get("traversal_class_counts") else None),
              "valid": bool(C["completed_with_valid_ranking"] and T["completed_with_valid_ranking"]), "note": None if (C["completed_with_valid_ranking"] and T["completed_with_valid_ranking"]) else "effect undefined: one arm has no completed run with a valid ranking"}
    bugs_out.append({"bug_id": pair, "project": proj, "facade": facade, "family": family, "treatment_gold": tgold, "control_gold": facade, "CONTROL": C, "TREATMENT": T, "effect": effect})
done = [b for b in bugs_out if "effect" in b]; valid_bugs = [b for b in done if b["effect"]["valid"]]
agg5 = {"bugs_analyzed": len(done), "bugs_with_both_arms_valid": len(valid_bugs), "delayed_first_gold": sum(1 for b in valid_bugs if (b["effect"]["delta_first_gold_steps"] or 0) > 0), "higher_tool_cost": sum(1 for b in valid_bugs if (b["effect"]["delta_tool_calls"] or 0) > 0),
        "any_treatment_rank_degradation": sum(1 for b in done if b["effect"]["rank_degradation_observed"]), "any_control_rank_degradation": sum(1 for b in done if b["effect"]["control_rank_degradation_observed"]), "treatment_all_completed_rank_1": sum(1 for b in done if b["effect"]["treatment_all_rank_1"]),
        "full_chain_traversal_in_all_completed_treatment_runs": sum(1 for b in done if b["TREATMENT"]["completed"] and b["TREATMENT"]["full_sequential_traversal_completed"] == b["TREATMENT"]["completed"]),
        "shortcut_runs_total": sum(b["TREATMENT"]["shortcut_any_completed"] for b in done), "lexical_bypass_runs_total": sum(b["TREATMENT"]["lexical_bypass_completed"] for b in done), "direct_gold_search_runs_total": sum(b["TREATMENT"]["direct_gold_search_completed"] for b in done), "repo_wide_shortcut_runs_total": sum(b["TREATMENT"]["repository_wide_shortcut_completed"] for b in done),
        "delta_first_gold_per_bug": {b["bug_id"]: b["effect"]["delta_first_gold_steps"] for b in done}, "delta_tool_calls_per_bug": {b["bug_id"]: b["effect"]["delta_tool_calls"] for b in done},
        "delta_first_gold_median_mean_range": [median([b["effect"]["delta_first_gold_steps"] for b in valid_bugs]), mean([b["effect"]["delta_first_gold_steps"] for b in valid_bugs]), [min([b["effect"]["delta_first_gold_steps"] for b in valid_bugs], default=None), max([b["effect"]["delta_first_gold_steps"] for b in valid_bugs], default=None)]],
        "delta_tool_calls_median_mean_range": [median([b["effect"]["delta_tool_calls"] for b in valid_bugs]), mean([b["effect"]["delta_tool_calls"] for b in valid_bugs]), [min([b["effect"]["delta_tool_calls"] for b in valid_bugs], default=None), max([b["effect"]["delta_tool_calls"] for b in valid_bugs], default=None)]],
        "delta_first_gold_t95_descriptive": tci([b["effect"]["delta_first_gold_steps"] for b in valid_bugs]), "delta_tool_calls_t95_descriptive": tci([b["effect"]["delta_tool_calls"] for b in valid_bugs])}
# ---- existing three bugs (latest corrected final tables) ----
t1 = list(csv.DictReader(open(R + "/thesis-results-current/TABLE1_CROSS_PROJECT_MAIN.csv"))); t5 = list(csv.DictReader(open(R + "/thesis-results-current/TABLE5_INFRASTRUCTURE_ACCOUNTING.csv")))
def ex_row(project, cond):
    r = next(x for x in t1 if x["project"] == project and x["condition"].startswith(cond)); ranks = [int(v) for v in r["gold_ranks"].split()]; fg = [int(v) for v in r["first_gold_steps"].split()]; tc = [int(v) for v in r["tool_calls"].split()]
    return {"attempted": int(r["attempted_runs"]), "completed": int(r["completed_runs"]), "completed_with_valid_ranking": int(r["completed_runs"]), "gold_ranks_completed": ranks, "acc_at_1": float(r["acc_at_1"]), "mrr": float(r["mrr"]), "first_gold_mean": float(r["mean_first_gold_step"]), "first_gold_completed": fg, "tool_calls_mean": float(r["mean_tool_calls_completed"]), "tool_calls_completed": tc,
            "full_sequential_traversal": r["full_sequential_traversal"], "lexical_bypass": r["strict_lexical_bypass"], "target": r["target_method"]}
lang_c = rj(R + "/conversion-long-chain-v1/long_chain_results.json"); ms = rj(R + "/multi-project-five-hop-v1/math_supplementary_results.json"); ch = rj(R + "/multi-project-five-hop-v1/analysis/chart/chart_results.json"); mfb = rj(R + "/multi-project-five-hop-v1/analysis/math/math_results.json")
existing = [{"bug_id": "LANG-1-CONVERSION-LONG-01", "project": "Lang", "facade": "Conversion#intArrayToLong", "family": "units of the destination offset", "treatment_gold": "NumberUtils#overlay", "CONTROL": ex_row("Commons Lang", "CONTROL"), "TREATMENT": ex_row("Commons Lang", "FIVE-HOP"),
             "cost_usd_total": round(lang_c["total_recorded_cost_usd"], 4) if lang_c else None, "infra": {"CONTROL": next(x for x in t5 if x["block"] == "Lang CONTROL"), "TREATMENT": next(x for x in t5 if x["block"] == "Lang FIVE-HOP")}, "source": "conversion-long-chain-v1/long_chain_results.json; thesis-results-current/TABLE1"},
            {"bug_id": "MATH-NORM-01", "project": "Math", "facade": "MathArrays#safeNorm", "family": "scale-units merge", "treatment_gold": "FastMath#merge", "CONTROL": ex_row("Commons Math", "CONTROL"), "TREATMENT": ex_row("Commons Math", "FIVE-HOP"),
             "cost_usd_total": (round(sum(v for v in ms["total_cost_usd"].values() if isinstance(v, (int, float))), 4) if isinstance(ms.get("total_cost_usd"), dict) else round(ms["total_cost_usd"], 4)) if ms else None, "infra": {"CONTROL": next(x for x in t5 if x["block"] == "Math CONTROL"), "TREATMENT": next(x for x in t5 if x["block"] == "Math FIVE-HOP")}, "source": "multi-project-five-hop-v1/math_supplementary_results.json (supplementary block run-006..010 as in TABLE1; first block stall-damaged, in infrastructure accounting only)"},
            {"bug_id": "CHART-AXIS-01", "project": "Chart", "facade": "CategoryAxis#getCategoryStart", "family": "boundary count", "treatment_gold": "RectangleAnchor#place", "CONTROL": ex_row("JFreeChart", "CONTROL"), "TREATMENT": ex_row("JFreeChart", "FIVE-HOP"),
             "cost_usd_total": round(ch["total_recorded_cost_usd"], 4) if ch else None, "infra": {"CONTROL": next(x for x in t5 if x["block"] == "Chart CONTROL"), "TREATMENT": next(x for x in t5 if x["block"] == "Chart FIVE-HOP")}, "source": "multi-project-five-hop-v1/analysis/chart/chart_results.json; thesis-results-current/TABLE1"}]
for b in existing:
    C, T = b["CONTROL"], b["TREATMENT"]
    b["effect"] = {"delta_first_gold_steps": round(T["first_gold_mean"] - C["first_gold_mean"], 2), "first_gold_ratio": round(T["first_gold_mean"] / C["first_gold_mean"], 2), "delta_tool_calls": round(T["tool_calls_mean"] - C["tool_calls_mean"], 2), "rank_degradation_observed": any(r != 1 for r in T["gold_ranks_completed"]), "treatment_all_rank_1": all(r == 1 for r in T["gold_ranks_completed"]),
                   "dominant_trajectory_mechanism": "A (full sequential traversal in %s completed runs)" % T["full_sequential_traversal"], "valid": True}
def bug_table_row(b, new):
    C, T, e = b["CONTROL"], b["TREATMENT"], b["effect"]
    trav = (f"{T['full_sequential_traversal_completed']}/{T['completed']}" if new else T["full_sequential_traversal"]); byp = (f"{T['lexical_bypass_completed']}/{T['completed']}" if new else T["lexical_bypass"])
    return {"project": b["project"], "bug_id": b["bug_id"], "original_target": b["facade"], "semantic_fault_family": b["family"], "control_completed_attempted": f"{C['completed']}/{C['attempted']}", "treatment_completed_attempted": f"{T['completed']}/{T['attempted']}",
            "control_acc1": C["acc_at_1"], "treatment_acc1": T["acc_at_1"], "control_mrr": C["mrr"], "treatment_mrr": T["mrr"], "control_first_gold": C["first_gold_mean"], "treatment_first_gold": T["first_gold_mean"], "control_tool_calls": C["tool_calls_mean"], "treatment_tool_calls": T["tool_calls_mean"],
            "treatment_traversal": trav, "treatment_bypass": byp, "control_ranks": C["gold_ranks_completed"], "treatment_ranks": T["gold_ranks_completed"], "delta_first_gold": e["delta_first_gold_steps"], "first_gold_ratio": e["first_gold_ratio"], "delta_tool_calls": e["delta_tool_calls"], "rank_degradation": e["rank_degradation_observed"], "treatment_all_rank_1": e["treatment_all_rank_1"], "mechanism": e["dominant_trajectory_mechanism"], "new": new}
eight = [bug_table_row(b, False) for b in existing] + [bug_table_row(b, True) for b in done]
order = {"Lang": 0, "Math": 1, "Chart": 2}; eight.sort(key=lambda x: (order[x["project"]], x["new"], x["bug_id"]))
v8 = [x for x in eight if x["delta_first_gold"] is not None]
agg8 = {"bugs": len(eight), "bugs_with_valid_effect": len(v8), "delayed_first_gold": sum(1 for x in v8 if x["delta_first_gold"] > 0), "higher_tool_cost": sum(1 for x in v8 if (x["delta_tool_calls"] or 0) > 0), "treatment_rank_degradation": sum(1 for x in eight if x["rank_degradation"]),
        "treatment_all_rank_1": sum(1 for x in eight if x["treatment_all_rank_1"]), "delta_first_gold_median_mean_range": [median([x["delta_first_gold"] for x in v8]), mean([x["delta_first_gold"] for x in v8]), [min([x["delta_first_gold"] for x in v8], default=None), max([x["delta_first_gold"] for x in v8], default=None)]],
        "delta_tool_calls_median_mean_range": [median([x["delta_tool_calls"] for x in v8]), mean([x["delta_tool_calls"] for x in v8]), [min([x["delta_tool_calls"] for x in v8], default=None), max([x["delta_tool_calls"] for x in v8], default=None)]],
        "first_gold_ratio_median_mean_range": [median([x["first_gold_ratio"] for x in v8]), mean([x["first_gold_ratio"] for x in v8]), [min([x["first_gold_ratio"] for x in v8], default=None), max([x["first_gold_ratio"] for x in v8], default=None)]],
        "delta_first_gold_t95_descriptive": tci([x["delta_first_gold"] for x in v8]), "delta_tool_calls_t95_descriptive": tci([x["delta_tool_calls"] for x in v8]),
        "completed_control_rank1": sum(1 for x in eight for r in x["control_ranks"] if r == 1), "completed_control_runs": sum(len(x["control_ranks"]) for x in eight), "completed_treatment_rank1": sum(1 for x in eight for r in x["treatment_ranks"] if r == 1), "completed_treatment_runs": sum(len(x["treatment_ranks"]) for x in eight)}
# ---- project summary ----
proj_sum = []
for P in ("Lang", "Math", "Chart"):
    xs = [x for x in eight if x["project"] == P]; newb = [b for b in done if b["project"] == P]
    proj_sum.append({"project": P, "bugs_evaluated": len(xs), "completed_control_runs": sum(len(x["control_ranks"]) for x in xs), "completed_treatment_runs": sum(len(x["treatment_ranks"]) for x in xs), "bugs_first_gold_delay": sum(1 for x in xs if (x["delta_first_gold"] or 0) > 0), "bugs_tool_call_increase": sum(1 for x in xs if (x["delta_tool_calls"] or 0) > 0),
                     "bugs_rank_degradation": sum(1 for x in xs if x["rank_degradation"]), "treatment_traversal": "; ".join(f"{x['bug_id']}: {x['treatment_traversal']}" for x in xs), "shortcuts": "; ".join(f"{x['bug_id']}: bypass {x['treatment_bypass']}" + (f", classes {b['TREATMENT']['traversal_class_counts']}" if (b := next((bb for bb in newb if bb['bug_id'] == x['bug_id']), None)) else "") for x in xs),
                     "new_block_cost_usd": round(sum(b["CONTROL"]["cost_usd_total"] + b["TREATMENT"]["cost_usd_total"] for b in newb), 4)})
# ---- infrastructure + cost ----
infra_rows = []
for b in done:
    for arm in ("CONTROL", "TREATMENT"):
        rs = [x for x in all_rows if x["bug_id"] == b["bug_id"] and x["condition"] == arm]
        infra_rows.append({"variant": f"{b['bug_id']}/{arm}", "attempted": len(rs), "completed": sum(1 for x in rs if x["completed"]), "timeout": sum(1 for x in rs if x["status"] == "timeout"), "startup_timeout": sum(1 for x in rs if x["status"] == "startup_timeout"),
                           "provider_stall_lost": sum(1 for x in rs if x["status"] in ("timeout", "startup_timeout")), "completed_slow_response": sum(1 for x in rs if x["completed_with_slow_response_or_prep_stall"]), "preparation_stall": sum(1 for x in rs if x.get("preparation_s") and x["preparation_s"] > 60), "dns_resolver_lines": sum(x["dns_error_lines"] or 0 for x in rs), "retry_lines": sum(x["retry_lines"] or 0 for x in rs),
                           "contaminated": sum(1 for x in rs if x["contaminated"]), "oow_flagged_calls": sum(x["oow_flagged_calls"] for x in rs), "valid_ranking": sum(1 for x in rs if x["completed"] and x["ranking_submitted"]), "cost_usd": round(sum(x["cost_usd"] or 0 for x in rs), 4)})
new_cost = round(sum(x["cost_usd"] or 0 for x in all_rows), 4)
cost = {"per_run": [{"run": x["run_id"], "cost_usd": x["cost_usd"], "status": x["status"]} for x in all_rows], "per_variant": {r["variant"]: r["cost_usd"] for r in infra_rows}, "per_bug": {b["bug_id"]: round(b["CONTROL"]["cost_usd_total"] + b["TREATMENT"]["cost_usd_total"], 4) for b in done},
        "per_project_new_block": {p["project"]: p["new_block_cost_usd"] for p in proj_sum}, "new_block_total_usd": new_cost, "mean_cost_per_completed_run_usd": mean([x["cost_usd"] for x in all_rows if x["completed"]]),
        "historical_core_benchmark_usd": {"Lang (conversion-long-chain-v1, 10 runs)": existing[0]["cost_usd_total"], "Math (multi-project-five-hop-v1, 20 runs incl. first block)": existing[1]["cost_usd_total"], "Chart (multi-project-five-hop-v1, 10 runs)": existing[2]["cost_usd_total"]},
        "final_benchmark_total_usd": round(new_cost + sum(v for v in (existing[0]["cost_usd_total"], existing[1]["cost_usd_total"], existing[2]["cost_usd_total"]) if v), 4), "probe_cost_note": "bounded smoke probes (tiny, unrecorded by the harness) are not included", "actual_records": "per-run cost from mini-swe-agent.traj.json model_stats (instance cost) — actual, not estimated"}
slots = {"planned": 50, "attempted": len(all_rows), "completed": sum(1 for x in all_rows if x["completed"]), "infrastructure_affected": sum(1 for x in all_rows if x["infrastructure_affected"]), "completed_with_slow_response_or_prep_stall": sum(1 for x in all_rows if x["completed_with_slow_response_or_prep_stall"]), "completed_with_valid_ranking": sum(1 for x in all_rows if x["completed"] and x["ranking_submitted"]), "contaminated": sum(1 for x in all_rows if x["contaminated"]),
         "per_variant": {r["variant"]: f"{r['completed']}/{r['attempted']} completed" for r in infra_rows}, "driver_state": rj(SU + "/driver_state.json"), "health_gate_probes": sum(1 for _ in open(SU + "/health_gate_su.log")) if os.path.exists(SU + "/health_gate_su.log") else 0}
res = {"schema_version": "core-benchmark-scaleup-v1/results/v1", "label": LABEL, "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(), "protocol": rj(SU + "/execution_root_record.json"), "slots": slots, "bugs_new": bugs_out, "five_bug_aggregate": agg5, "existing_bugs": existing, "eight_bug_table": eight, "eight_bug_aggregate": agg8,
       "project_summary": proj_sum, "infrastructure": infra_rows, "cost": cost, "per_run": all_rows, "interpretation_rule": "descriptive only; the bug is the replication unit; runs nested within bugs are not independent replicates; infrastructure-affected runs excluded from accuracy denominators; hidden reasoning never read"}
json.dump(res, open(OUT + "/scaleup_gpt56_results.json", "w"), indent=1); json.dump(all_rows, open(A + "/per_run/per_run_primary_data.json", "w"), indent=1)
for b in done: json.dump(b, open(f"{A}/per_bug/{b['bug_id']}_metrics.json", "w"), indent=1)
with open(A + "/per_run/per_run_primary_data.csv", "w", newline="") as fh:
    cols = ["project", "bug_id", "condition", "run_id", "status", "completed", "infrastructure_affected", "gold_method", "gold_rank", "reciprocal_rank", "tool_calls", "api_calls", "wall_time_s", "cost_usd", "first_command", "first_search", "first_facade_exposure", "first_gold_exposure", "buggy_line_exposure", "external_contract_exposure", "calls_after_gold", "tests_executed", "source_files_opened", "unique_search_queries", "traversal_class", "gold_exposure_relative_to_H4", "lexical_bypass", "direct_gold_search", "repository_wide_shortcut", "oow_flagged_calls", "contaminated"]
    w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore"); w.writeheader(); [w.writerow(x) for x in all_rows]
# ---- figures data ----
with open(A + "/figures_data/first_gold_and_tool_calls_by_bug.csv", "w", newline="") as fh:
    w = csv.writer(fh); w.writerow(["bug_id", "project", "new", "condition", "run", "gold_rank", "first_gold", "tool_calls"])
    for b in existing:
        for arm in ("CONTROL", "TREATMENT"):
            for i, (r, g, t) in enumerate(zip(b[arm]["gold_ranks_completed"], b[arm]["first_gold_completed"], b[arm]["tool_calls_completed"]), 1): w.writerow([b["bug_id"], b["project"], 0, arm, i, r, g, t])
    for x in all_rows: w.writerow([x["bug_id"], x["project"], 1, x["condition"], x["run_id"].split("/")[1], x["gold_rank"], x["first_gold_exposure"], x["tool_calls"]])
print(json.dumps({"slots": {k: v for k, v in slots.items() if k not in ("driver_state", "per_variant")}, "five_bug_aggregate": {k: v for k, v in agg5.items() if not k.endswith("per_bug")}, "eight_bug_aggregate": agg8, "new_block_cost": new_cost}, indent=1))
