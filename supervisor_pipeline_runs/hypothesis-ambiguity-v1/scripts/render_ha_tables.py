"""Render markdown tables from hypothesis_ambiguity_results.json. Usage: render_ha_tables.py <results.json> <out.md>"""
import json, sys
d = json.load(open(sys.argv[1])); runs = d["runs"]; A = d["per_arm"]
def f(x, nd=2): return "-" if x is None else (f"{x:.{nd}f}" if isinstance(x, float) else str(x))
out = ["## T1. Per-run outcomes and hypothesis metrics (observable only)", "", "| Run | Arm | Status | Gold rank | Tool calls | Model calls | Cost USD | First candidate exposed (step) | Gold first exposed | Candidates inspected (order) | Wrong candidates seriously investigated | Wrong ranked above gold | Backtracking | External evidence used | Calls first-candidate→ranking | CED step (calls before ranking) | Class |", "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
for r in runs:
    out.append(f"| {r['run_id'].split('/')[1]} | {r['arm']} | {r['status']} | {r['gold_rank']} | {r['tool_call_count']} | {r['api_calls']} | {f(r['cost_usd'],4)} | {r['first_candidate_exposed']['step']} ({', '.join(r['first_candidate_exposed']['which'])}) | {r['gold_first_exposed_step']} | {' → '.join(r['inspection_order'])} | {', '.join(r['wrong_candidates_seriously_investigated']) or 'none'} | {', '.join(r['wrong_candidates_ranked_above_gold']) or 'none'} | {r['backtracking_events']} | {', '.join(k.split('_')[0] for k in r['external_evidence_sources_used']) or 'none'} | {r['calls_from_first_candidate_to_ranking']} | {r['candidate_elimination_depth_step']} ({r['ced_calls_before_ranking']}) | {r['discrimination_class']} |")
out += ["", "## T2. Per-arm aggregates (n = 5 launched each; descriptive only)", "", "| Metric | LOW | HIGH |", "|---|---|---|"]
keys = [("Completed / timeout / other", lambda a: f"{a['completed']} / {a['timeout']} / {len(a['other_status'])}"), ("Gold ranks", lambda a: str(a["gold_ranks"])), ("Acc@1 / @3 / @5 (completed)", lambda a: " / ".join(f(a[k]) for k in ("acc_at_1", "acc_at_3", "acc_at_5"))), ("MRR (completed)", lambda a: f(a["mrr"], 3)),
        ("Tool calls (list); mean completed", lambda a: f"{a['tool_calls']}; {f(a['tool_calls_mean_completed'])}"), ("Model calls", lambda a: str(a["api_calls"])), ("Gold first exposed (list); mean", lambda a: f"{a['gold_first_exposed']}; {f(a['gold_first_exposed_mean'])}"), ("First candidate exposed (step)", lambda a: str(a["first_candidate_exposed"])),
        ("Candidate methods inspected (list); mean", lambda a: f"{a['n_candidate_methods_inspected']}; {f(a['n_candidate_methods_inspected_mean'])}"), ("Wrong candidates seriously investigated (list); mean", lambda a: f"{a['wrong_candidates_seriously_investigated']}; {f(a['wrong_candidates_seriously_investigated_mean'])}"), ("… after the gold was exposed", lambda a: str(a["wrong_candidates_seriously_investigated_after_gold"])),
        ("Wrong candidates ranked above gold", lambda a: str(a["wrong_candidates_ranked_above_gold"])), ("Calls from first candidate exposure to ranking (list); mean completed", lambda a: f"{a['calls_from_first_candidate_to_ranking']}; {f(a['calls_from_first_candidate_to_ranking_mean'])}"), ("Calls after gold (list); mean completed", lambda a: f"{a['calls_after_gold']}; {f(a['calls_after_gold_mean_completed'])}"),
        ("Backtracking events (list); mean", lambda a: f"{a['backtracking_events']}; {f(a['backtracking_mean'])}"), ("External evidence sources per run", lambda a: str(a["external_evidence_sources_per_run"])), ("Evidence source counts", lambda a: str(a["external_evidence_sources_used_counts"])), ("Runs executing other tests / scripted computations / observable alternative-arithmetic checks", lambda a: f"{a['other_tests_executed_runs']} / {a['scripted_computation_runs']} / {a['counterfactual_repairs_considered_runs']}"),
        ("Candidate elimination depth (step list; calls before ranking)", lambda a: f"{a['ced_step']}; {a['ced_calls_before_ranking']}"), ("Lexical shortcut runs", lambda a: str(a["lexical_shortcut_runs"])), ("Discrimination classes", lambda a: str(a["discrimination_classes"])), ("Cost USD", lambda a: f(a["cost_usd"], 4))]
for lab, g in keys: out.append(f"| {lab} | {g(A['LOW'])} | {g(A['HIGH'])} |")
out += ["", "## T3. Final rank of every candidate method per run", ""]
for arm in ("LOW", "HIGH"):
    cr = A[arm]["candidate_final_ranks"]; names = list(cr)
    out += [f"**{arm}**", "", "| Run | " + " | ".join(names) + " |", "|---|" + "---|" * len(names)]
    rs = [r for r in runs if r["arm"] == arm]
    for i, r in enumerate(rs): out.append(f"| {r['run_id'].split('/')[1]} | " + " | ".join(f(r["candidate_final_ranks"].get(n)) for n in names) + " |")
    out.append("")
out += ["## T4. Contract-evidence markers: first exposure step per run (tool output; E6 is in the prompt)", ""]
marks = list(runs[0]["contract_first_shown"].keys()) if runs else []
out += ["| Marker | " + " | ".join(r["run_id"].split("-")[1][:1] + "/" + r["run_id"].split("/")[1].replace("run-", "") for r in runs) + " |", "|---|" + "---|" * len(runs)]
for m in marks: out.append(f"| `{m}` | " + " | ".join(f(r["contract_first_shown"].get(m)) for r in runs) + " |")
out += ["", "## T5. Submitted top-5 per run", "", "| Run | Arm | 1 | 2 | 3 | 4 | 5 |", "|---|---|---|---|---|---|---|"]
for r in runs: t = r["top10"] + [""] * 5; out.append(f"| {r['run_id'].split('/')[1]} | {r['arm']} | " + " | ".join(f"`{x.split('.')[-1]}`" if x else "-" for x in t[:5]) + " |")
open(sys.argv[2], "w").write("\n".join(out) + "\n"); print("\n".join(out[:6]))
