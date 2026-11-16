"""Combine the Math first block (run-001..005) and the supplementary block (run-006..010) analyzer outputs into math_supplementary_results.json.
Blocks stay separate; a descriptive 'combined' section reports completed-run metrics, all-attempt infrastructure status and the number of
provider-affected observations. Timeouts are never localization misses. Usage: build_math_combined.py <block1.json> <supp.json> <scan_supp.json> <out.json>"""
import json, sys, statistics
b1, sp, scan = json.load(open(sys.argv[1])), json.load(open(sys.argv[2])), json.load(open(sys.argv[3]))
contam = set(scan.get("summary", {}).get("contaminated_runs", []))
def mean(xs): xs = [x for x in xs if x is not None]; return round(statistics.mean(xs), 2) if xs else None
def block(d, arm, label):
    rs = [r for r in d["runs"] if r["arm"] == arm]; A = d["per_arm"][arm]
    comp = [r for r in rs if r["status"] == "completed" and r["run_id"] not in contam]; act = [r for r in rs if (r["tool_call_count"] or 0) > 0]
    out = {"label": label, "n_launched": len(rs), "completed": len(comp), "contaminated_completed_excluded": [r["run_id"] for r in rs if r["status"] == "completed" and r["run_id"] in contam],
           "timeout": sum(1 for r in rs if r["status"] == "timeout"), "startup_timeout": sum(1 for r in rs if r["status"] == "startup_timeout"), "other_status": [(r["run_id"], r["status"]) for r in rs if r["status"] not in ("completed", "timeout", "startup_timeout")],
           "provider_affected_runs": sum(1 for r in rs if r["timing"].get("stalled_request")), "stall_kinds": [r["timing"].get("stall_kind") for r in rs],
           "gold_ranks_all": [r["gold_rank"] for r in rs], "gold_ranks_completed": [r["gold_rank"] for r in comp],
           "acc_at_1": (sum(1 for r in comp if r["gold_rank"] == 1) / len(comp)) if comp else None, "acc_at_3": (sum(1 for r in comp if r["gold_rank"] and r["gold_rank"] <= 3) / len(comp)) if comp else None,
           "acc_at_5": (sum(1 for r in comp if r["gold_rank"] and r["gold_rank"] <= 5) / len(comp)) if comp else None, "acc_at_10": (sum(1 for r in comp if r["gold_rank"] and r["gold_rank"] <= 10) / len(comp)) if comp else None,
           "mrr": (sum((1 / r["gold_rank"]) if r["gold_rank"] else 0 for r in comp) / len(comp)) if comp else None,
           "tool_calls_all": [r["tool_call_count"] for r in rs], "tool_calls_completed_mean": mean([r["tool_call_count"] for r in comp]), "tool_calls_active_mean": mean([r["tool_call_count"] for r in act]),
           "api_calls_all": [r["api_calls"] for r in rs], "api_calls_completed_mean": mean([r["api_calls"] for r in comp]),
           "first_gold_step_all": [r["gold_first_exposed_step"] for r in rs], "first_gold_step_mean_active": mean([r["gold_first_exposed_step"] for r in act]), "first_gold_step_mean_completed": mean([r["gold_first_exposed_step"] for r in comp]),
           "gold_exposed_runs": sum(1 for r in rs if r["gold_first_exposed_step"]), "runs_with_activity": len(act),
           "calls_after_gold_all": [r["info_distance"]["calls_after_first_gold"] for r in rs], "calls_after_gold_completed_mean": mean([r["info_distance"]["calls_after_first_gold"] for r in comp]),
           "contract_markers_all": [r["info_distance"]["external_contract_retrieval_count"] for r in rs], "runs_with_new_contract_evidence_after_gold": sum(1 for r in rs if r["info_distance"]["contract_markers_after_gold"]),
           "gold_executed_or_emulated_after_exposure": A.get("gold_executed_or_emulated_after_exposure"), "javap_jshell_runs": A.get("javap_jshell_used"), "recency_heuristic_runs": A.get("recency_heuristic_runs"),
           "source_integrity_ok_all": A.get("source_integrity_ok_all"), "wall_clock_s": A.get("wall_clock_s"), "start_to_first_response_s": A.get("start_to_first_response_s"), "max_inter_response_gap_s": A.get("max_inter_response_gap_s"),
           "cost_usd": round(A["total_cost_usd"], 4), "facade_rank": A.get("facade_rank")}
    if arm == "TREATMENT":
        out.update({"routes": A.get("routes"), "full_five_hop_traversal_all": A.get("full_five_hop_traversal_rate"), "full_five_hop_traversal_active": A.get("full_five_hop_traversal_rate_active"),
                    "lexical_bypass_strict_active": A.get("lexical_bypass_rate_active"), "repository_wide_shortcut_active": A.get("repository_wide_shortcut_rate_active"), "direct_gold_search_rate": A.get("direct_gold_search_rate"),
                    "buggy_line_after_h4_call_runs": A.get("buggy_line_after_h4_call_runs"), "hop_exposure_mean": A.get("hop_exposure_mean"), "increments_mean": A.get("increments_mean"), "reached_per_hop": A.get("reached_per_hop"), "skipped_hops": A.get("skipped_hops")})
    return out
out = {"schema_version": "math-supplementary-results/v1", "label": "NON-CANONICAL / MATH SUPPLEMENTARY BLOCK (run-006..010) + FIRST BLOCK (run-001..005), kept separate / GPT-5.6 DIAGNOSTIC",
       "interpretation_rule": "Descriptive; blocks reported separately; completed-run metrics vs all-attempt infrastructure status; provider timeouts are never localization misses; contaminated runs (out-of-workspace content shown) are excluded from metrics but preserved.",
       "contamination_scan_summary": scan.get("summary"),
       "first_block": {"CONTROL": block(b1, "CONTROL", "run-001..005"), "TREATMENT": block(b1, "TREATMENT", "run-001..005")},
       "supplementary_block": {"CONTROL": block(sp, "CONTROL", "run-006..010"), "TREATMENT": block(sp, "TREATMENT", "run-006..010")}}
def combined(arm):
    a, b = out["first_block"][arm], out["supplementary_block"][arm]
    comp_ranks = a["gold_ranks_completed"] + b["gold_ranks_completed"]
    return {"launched": a["n_launched"] + b["n_launched"], "completed": a["completed"] + b["completed"], "provider_affected": a["provider_affected_runs"] + b["provider_affected_runs"],
            "gold_ranks_completed_by_block": {"run-001..005": a["gold_ranks_completed"], "run-006..010": b["gold_ranks_completed"]},
            "acc_at_1_completed": (sum(1 for r in comp_ranks if r == 1) / len(comp_ranks)) if comp_ranks else None, "mrr_completed": (sum(1 / r for r in comp_ranks if r) / len(comp_ranks)) if comp_ranks else None,
            "first_gold_step_by_block": {"run-001..005": a["first_gold_step_all"], "run-006..010": b["first_gold_step_all"]}, "tool_calls_by_block": {"run-001..005": a["tool_calls_all"], "run-006..010": b["tool_calls_all"]},
            "note": "descriptive union of two separately reported blocks; no confirmatory statistic"}
out["combined_descriptive"] = {"CONTROL": combined("CONTROL"), "TREATMENT": combined("TREATMENT")}
out["total_cost_usd"] = {"first_block": round(b1["total_recorded_cost_usd"], 4), "supplementary_block": round(sp["total_recorded_cost_usd"], 4)}
json.dump(out, open(sys.argv[4], "w"), indent=1)
for blk in ("first_block", "supplementary_block"):
    for arm in ("CONTROL", "TREATMENT"):
        B = out[blk][arm]; print(blk, arm, "| launched", B["n_launched"], "completed", B["completed"], "timeout", B["timeout"], "startup_timeout", B["startup_timeout"], "| ranks", B["gold_ranks_all"], "| acc1", B["acc_at_1"], "mrr", B["mrr"], "| first gold", B["first_gold_step_all"], "| calls", B["tool_calls_all"], "| cost", B["cost_usd"])
