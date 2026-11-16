"""Render markdown tables from diagnostic_v3_results.json (observable-only). Output: analysis/tables_v3.md"""
import json, sys, os, statistics
PR = sys.argv[1]; _in = sys.argv[2] if len(sys.argv) > 2 else "diagnostic_v3_results.json"; _outname = sys.argv[3] if len(sys.argv) > 3 else "tables_v3.md"; d = json.load(open(os.path.join(PR, _in))); runs = d["runs"]
def f(x, nd=2): return "-" if x is None else (f"{x:.{nd}f}" if isinstance(x, float) else str(x))
def mmed(xs): xs=[x for x in xs if x is not None]; return (f"{statistics.mean(xs):.1f} / {statistics.median(xs):g}") if xs else "-"
out=[]
out.append("## T1. Per-run summary (observable artifacts only)\n")
out.append("| Run | Arm | Status | Gold rank | Tool calls | API calls | Cost USD | First command | Gold first exposed (step) | Buggy line first shown (step) | Calls after gold | Traversal |")
out.append("|---|---|---|---|---|---|---|---|---|---|---|---|")
for r in runs:
    fe=r["first_exposure_output"]; bug=fe.get("K_buggy_pattern_facade") if r["arm"]=="CONTROL" else fe.get("K2_buggy_pattern_hop")
    out.append(f"| {r['run_id'].split('/')[1]} | {r['arm']} | {r['status']} | {r['gold_rank']} | {r['tool_call_count']} | {r['api_calls']} | {f(r['cost_usd'],4)} | `{(r['first_commands']['first_command'] or '')[:60]}` | {r['gold_first_exposed_step']} | {bug} | {r['tool_calls_after_gold']} | {r['traversal']} |")
out.append("\n## T2. Per-arm aggregates (n = 5 each; descriptive only)\n")
A=d["per_arm"]; keys=[("Completed", "completed"), ("Acc@1", "acc_at_1"), ("Acc@3", "acc_at_3"), ("Acc@5", "acc_at_5"), ("Acc@10", "acc_at_10"), ("MRR", "mrr"), ("Gold ranks", "gold_ranks"), ("Tool calls (list)", "tool_calls"), ("Tool calls mean / median", "tool_calls_mean_median"), ("API calls (list)", "api_calls"), ("API calls mean / median", "api_calls_mean_median"), ("Gold first exposed step (list)", "first_gold_step"), ("Gold first exposed mean / median", "first_gold_step_mean_median"), ("Calls after gold (list)", "calls_after_gold"), ("Calls after gold mean / median", "calls_after_gold_mean_median"), ("Total cost USD", "total_cost_usd"), ("Timeouts", "timeout"), ("Protocol violations", "protocol_violation"), ("Full-chain traversal rate (TREATMENT only)", "full_chain_traversal_rate"), ("Lexical bypass rate (TREATMENT only)", "lexical_bypass_rate"), ("Runs showing contract evidence before final rank", "external_contract_retrieval_rate"), ("Runs showing NEW contract evidence after gold exposure", "contract_after_gold_rate"), ("Novel-vocabulary search events / runs", "novel_vocab_events"), ("build.properties observably used", "build_properties_observably_used"), ("source_integrity ok (all)", "source_integrity_ok_all")]
_arms=[a for a in ("CONTROL","TREATMENT") if a in A and A[a].get("n_found")]; out.append("| Metric | " + " | ".join(_arms) + " |"); out.append("|---|" + "---|"*len(_arms))
for lab,k in keys:
    def g(arm):
        v=A[arm].get(k)
        if isinstance(v, tuple) or (isinstance(v, list) and len(v)==2 and k.endswith("mean_median")): return f"{f(v[0],1)} / {f(v[1],1)}"
        if isinstance(v,float): return f"{v:.3f}" if k!="total_cost_usd" else f"{v:.4f}"
        return f(v)
    out.append(f"| {lab} | " + " | ".join(g(a) for a in _arms) + " |")
out.append("\n## T3. First observable exposure step of each marker (tool OUTPUT), per run\n")
marks=sorted({k for r in runs for k in r["first_exposure_output"]})
out.append("| Marker | " + " | ".join(r["run_id"].replace("CONVERSION-","").replace("-01/run-","/") for r in runs) + " |"); out.append("|---|" + "---|"*len(runs))
for m in marks: out.append(f"| `{m}` | " + " | ".join(f(r["first_exposure_output"].get(m)) for r in runs) + " |")
out.append("\n## T4. Command-level observables, per run\n")
ck=["first_search_idx","first_file_opened_idx","first_action_is_test_run","foldValues_cmd_idx","assemble_cmd_idx","Fraction_cmd_idx","dstPos_cmd_idx","sibling_method_cmd_idx","build_properties_cmd_idx","javap_jshell_idx","failing_tests_read_idx"]
out.append("| Observable | " + " | ".join(r["run_id"].replace("CONVERSION-","").replace("-01/run-","/") for r in runs) + " |"); out.append("|---|" + "---|"*len(runs))
for k in ck: out.append(f"| `{k}` | " + " | ".join(f(r["first_commands"].get(k)) for r in runs) + " |")
out.append("| tests executed (count) | " + " | ".join(str(len(r["first_commands"]["tests_executed"])) for r in runs) + " |")
out.append("\n## T5. Local-coherence sequence after gold exposure, per run\n")
out.append("| Run | Arm | Gold step | First contract-evidence step | gold_seen_before_contract_evidence | contract evidence seen before final rank | NEW contract evidence after gold | evidence types (all) | post-gold searches | post-gold opens |"); out.append("|---|---|---|---|---|---|---|---|---|---|")
for r in runs:
    c=r["coherence"]; fe=r["first_exposure_output"]; ck2=["H_in_bits","facade_guard","J_sibling_pattern_i32_dstPos","J2_sibling_pattern_short_width","J3_sibling_pattern_byte_width","J4_inverse_longToIntArray_pattern","I_longToIntArray","M_sibling_test_dstPos_24","M_sibling_test_dstPos_16","M_sibling_test_dstPos_8"]
    fc=min([fe[k] for k in ck2 if fe.get(k)] or [None]) if any(fe.get(k) for k in ck2) else None
    out.append(f"| {r['run_id'].split('/')[1]} | {r['arm']} | {r['gold_first_exposed_step']} | {fc} | {c['gold_seen_before_contract_evidence']} | {c['contract_evidence_seen_before_final_rank']} | {', '.join(c['contract_evidence_after_gold_before_rank']) or 'none'} | {', '.join(c['external_evidence_types'])} | {c['post_gold_search_count']} | {c['post_gold_open_count']} |")
out.append("\n## T6. Novel search vocabulary events (token in a search command not present in payload or any earlier observable output)\n")
out.append("| Run | Step | Token | Command |"); out.append("|---|---|---|---|")
n=0
for r in runs:
    for e in r["novel_search_vocabulary"]: n+=1; out.append(f"| {r['run_id'].split('/')[1]} ({r['arm']}) | {e['step']} | `{e['token']}` | `{e['command'][:110]}` |")
if n==0: out.append("| (none) | - | - | - |")
out.append("\n## T7. Submitted top-5 per run\n")
out.append("| Run | Arm | 1 | 2 | 3 | 4 | 5 |"); out.append("|---|---|---|---|---|---|---|")
for r in runs:
    t=r["top10"]+[""]*5; out.append(f"| {r['run_id'].split('/')[1]} | {r['arm']} | " + " | ".join(f"`{x.split('.')[-1]}`" if x else "-" for x in t[:5]) + " |")
open(os.path.join(PR,"analysis",_outname),"w").write("\n".join(out)+"\n"); print("\n".join(out))
