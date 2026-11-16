#!/usr/bin/env python
"""Build every OCFLB results artifact from analysis/per_run/run_metrics.json (+ pair.json, BENCHMARK_MANIFEST.json).
Usage: build_results.py   Writes results/*.md, results/*.csv, results/ocflb_results.json, analysis/tables/*.json"""
import json, glob, os, csv, statistics as st, collections
O = "/Users/shawnli/Desktop/Honours/defects4j/supervisor_pipeline_runs/ocflb-v1"; RS = f"{O}/results"; os.makedirs(RS, exist_ok=True); os.makedirs(f"{O}/analysis/tables", exist_ok=True)
rows = json.load(open(f"{O}/analysis/per_run/run_metrics.json")); man = json.load(open(f"{O}/BENCHMARK_MANIFEST.json")) if os.path.exists(f"{O}/BENCHMARK_MANIFEST.json") else {"pairs": {}}
pairs = {json.load(open(p))["pair_id"]: json.load(open(p)) for p in glob.glob(f"{O}/projects/*/bug-*/pair.json")}
ORDER = sorted(man["pairs"].keys() or pairs.keys(), key=lambda k: (pairs[k]["project"], pairs[k]["bug"]))
VALID = lambda r: r["status"] not in ("provider_stall", "provider_error")     # attempts the agent was allowed to finish
def agg(rs):
    v = [r for r in rs if VALID(r)]; c = [r for r in v if r["status"] == "completed"]
    if not v: return {"attempted": len(rs), "valid": 0}
    return {"attempted": len(rs), "valid": len(v), "answered": len(c), "no_answer": sum(1 for r in v if r["no_answer"]), "stalls": sum(1 for r in rs if r["status"] == "provider_stall"),
            "acc1": round(sum(r["acc_at_1"] for r in v) / len(v), 3), "acc1_answered": round(sum(r["acc_at_1"] for r in c) / len(c), 3) if c else None,
            "acc3": round(sum(r["acc_at_3"] for r in v) / len(v), 3), "acc5": round(sum(r["acc_at_5"] for r in v) / len(v), 3), "acc10": round(sum(r["acc_at_10"] for r in v) / len(v), 3),
            "mrr": round(sum(r["mrr"] for r in v) / len(v), 3), "ranks": [r["gold_rank"] for r in c], "gold_discovered": sum(1 for r in c if r["gold_discovered"]),
            "discovered_misranked": sum(1 for r in c if r["gold_discovered"] and r["gold_rank"] != 1), "pin_seen": sum(1 for r in v if r["second_caller_evidence_retrieved"]),
            "contract_seen": sum(1 for r in v if r["contract_evidence_retrieved"]), "post_gold_test": sum(1 for r in v if r["post_gold_verification"]),
            "classes": dict(collections.Counter(r["classification"] for r in v)), "tool_calls": round(st.mean(r["tool_calls"] for r in v), 1), "cost": round(sum(r["cost_usd"] or 0 for r in rs), 4),
            "h2_rank_when_h3_gold": [r["role_ranks"].get("H2") for r in c if r["gold_role"] == "H3"], "h3_rank_when_h2_gold": [r["role_ranks"].get("H3") for r in c if r["gold_role"] == "H2"]}

def emit(name, body):
    """Write results/<name>.md; append results/narratives/<name>.md (hand-written reading) when present."""
    nar = f"{RS}/narratives/{name}.md"
    if os.path.exists(nar): body = body.rstrip("\n") + "\n\n" + open(nar).read().rstrip("\n") + "\n"
    open(f"{RS}/{name}.md", "w").write(body)

T = {}
for pid in ORDER:
    for model in ("sonnet", "opus"):
        for arm in ("DEFINER_FAULT", "ADAPTER_FAULT"):
            T[(pid, model, arm)] = agg([r for r in rows if r["pair_id"] == pid and r["model"] == model and r["arm"] == arm])
json.dump({f"{k[0]}|{k[1]}|{k[2]}": v for k, v in T.items()}, open(f"{O}/analysis/tables/pair_model_arm.json", "w"), indent=1)
def gap(pid, model):
    d, a = T[(pid, model, "DEFINER_FAULT")], T[(pid, model, "ADAPTER_FAULT")]
    return round(d["acc1"] - a["acc1"], 3) if d.get("valid") and a.get("valid") else None
# ---- run-level and pair-level CSV
with open(f"{RS}/RUN_LEVEL_RESULTS.csv", "w", newline="") as f:
    keys = ["pair_id", "project", "bug", "family", "arm", "variant_id", "server", "model", "model_id", "run", "status", "harness_status", "gold", "gold_role", "gold_rank", "acc_at_1", "acc_at_3", "acc_at_5", "acc_at_10", "mrr", "rank1", "rank1_role",
            "first_facade_exposure", "first_hop_exposure", "first_gold_exposure", "h2_exposure", "h3_exposure", "gold_discovered", "contract_evidence_retrieved", "second_caller_evidence_retrieved", "post_gold_verification",
            "tool_calls", "api_calls", "test_executions", "file_reads", "repository_searches", "deepest_stage_rank", "reverse_depth_tau", "classification", "cost_usd", "wall_ms", "submitted_top10"]
    w = csv.DictWriter(f, fieldnames=keys, extrasaction="ignore"); w.writeheader()
    for r in rows: w.writerow({**r, "submitted_top10": " > ".join(r["submitted_top10"])})
with open(f"{RS}/BUG_PAIR_RESULTS.csv", "w", newline="") as f:
    w = csv.writer(f); w.writerow(["pair_id", "project", "bug", "family", "model", "definer_acc1", "adapter_acc1", "definer_mrr", "adapter_mrr", "attribution_gap", "definer_ranks", "adapter_ranks", "definer_valid", "adapter_valid", "definer_no_answer", "adapter_no_answer", "stalls"])
    for pid in ORDER:
        for model in ("sonnet", "opus"):
            d, a = T[(pid, model, "DEFINER_FAULT")], T[(pid, model, "ADAPTER_FAULT")]
            if not d.get("valid") and not a.get("valid"): continue
            w.writerow([pid, pairs[pid]["project"], pairs[pid]["bug"], pairs[pid]["family"], model, d.get("acc1"), a.get("acc1"), d.get("mrr"), a.get("mrr"), gap(pid, model), d.get("ranks"), a.get("ranks"), d.get("valid"), a.get("valid"), d.get("no_answer"), a.get("no_answer"), (d.get("stalls", 0) or 0) + (a.get("stalls", 0) or 0)])
# ---- benchmark-wide summaries
def wide(model):
    ps = [p for p in ORDER if T[(p, model, "DEFINER_FAULT")].get("valid") and T[(p, model, "ADAPTER_FAULT")].get("valid")]
    gaps = [gap(p, model) for p in ps]; v = [r for r in rows if r["model"] == model and VALID(r)]; c = [r for r in v if r["status"] == "completed"]
    return {"pairs": len(ps), "definer_gt_adapter": sum(1 for g in gaps if g > 0), "equal": sum(1 for g in gaps if g == 0), "reversed": sum(1 for g in gaps if g < 0),
            "median_gap": round(st.median(gaps), 3) if gaps else None, "mean_gap": round(st.mean(gaps), 3) if gaps else None,
            "definer_acc1": round(st.mean(T[(p, model, "DEFINER_FAULT")]["acc1"] for p in ps), 3) if ps else None, "adapter_acc1": round(st.mean(T[(p, model, "ADAPTER_FAULT")]["acc1"] for p in ps), 3) if ps else None,
            "gold_discovered_misranked_rate": round(sum(1 for r in c if r["gold_discovered"] and r["gold_rank"] != 1) / len(c), 3) if c else None,
            "second_caller_retrieval_rate": round(sum(1 for r in v if r["second_caller_evidence_retrieved"]) / len(v), 3) if v else None,
            "depth_prior_rate": round(sum(1 for r in v if r["classification"] == "DEPTH_PRIOR") / len(v), 3) if v else None,
            "no_answer_rate": round(sum(1 for r in v if r["no_answer"]) / len(v), 3) if v else None,
            "definer_attribution_rate_on_adapter_arm": round(sum(1 for r in v if r["arm"] == "ADAPTER_FAULT" and r["classification"] == "DEFINER_ATTRIBUTION") / max(1, sum(1 for r in v if r["arm"] == "ADAPTER_FAULT")), 3),
            "adapter_attribution_rate_on_definer_arm": round(sum(1 for r in v if r["arm"] == "DEFINER_FAULT" and r["classification"] == "ADAPTER_ATTRIBUTION") / max(1, sum(1 for r in v if r["arm"] == "DEFINER_FAULT")), 3),
            "runs_valid": len(v), "runs_attempted": len([r for r in rows if r["model"] == model]), "stalls": sum(1 for r in rows if r["model"] == model and r["status"] == "provider_stall"), "cost_usd": round(sum(r["cost_usd"] or 0 for r in rows if r["model"] == model), 2)}
W = {m: wide(m) for m in ("sonnet", "opus")}
json.dump({"pair_model_arm": {f"{k[0]}|{k[1]}|{k[2]}": v for k, v in T.items()}, "benchmark_wide": W, "n_runs": len(rows)}, open(f"{RS}/ocflb_results.json", "w"), indent=1)
fam = lambda p: pairs[p]["family"].split("(")[0].strip()
# ---- THESIS TABLES
L = ["# OCFLB thesis tables (NON-CANONICAL RESEARCH BENCHMARK; Acc@1 and MRR over valid attempts = every run the agent was allowed to finish; provider stalls excluded)", ""]
L += ["## Table 1 - per pair (primary model claude-sonnet-4-6, 5 runs per arm)", "", "| Project | Bug | Fault family | H2 role | H3 role | Definer Acc@1 | Adapter Acc@1 | Definer MRR | Adapter MRR | Attribution Gap | Definer gold ranks | Adapter gold ranks |", "|" + "---|" * 12]
for p in ORDER:
    d, a = T[(p, "sonnet", "DEFINER_FAULT")], T[(p, "sonnet", "ADAPTER_FAULT")]; ch = pairs[p]["chain"]
    L.append(f"| {pairs[p]['project']} | {pairs[p]['bug']} | {fam(p)} | `{ch['H2']['method']}` | `{ch['H3']['method']}` | {d.get('acc1','-')} | {a.get('acc1','-')} | {d.get('mrr','-')} | {a.get('mrr','-')} | {gap(p,'sonnet')} | {d.get('ranks','-')} | {a.get('ranks','-')} |")
L += ["", "## Table 2 - mechanism (Sonnet; counts over valid attempts of both arms)", "", "| Project | Bug | Gold discovered rate | Definer selected when correct (Acc@1 definer arm) | Definer selected when wrong (H2 first on adapter arm) | Second-caller evidence retrieved | Depth-prior errors | Other errors |", "|" + "---|" * 8]
for p in ORDER:
    v = [r for r in rows if r["pair_id"] == p and r["model"] == "sonnet" and VALID(r)]; c = [r for r in v if r["status"] == "completed"]
    if not v: continue
    dw = sum(1 for r in v if r["arm"] == "ADAPTER_FAULT" and r["rank1_role"] == "H2"); na = sum(1 for r in v if r["arm"] == "ADAPTER_FAULT")
    L.append(f"| {pairs[p]['project']} | {pairs[p]['bug']} | {sum(1 for r in c if r['gold_discovered'])}/{len(c)} | {T[(p,'sonnet','DEFINER_FAULT')].get('acc1','-')} | {dw}/{na} | {sum(1 for r in v if r['second_caller_evidence_retrieved'])}/{len(v)} | {sum(1 for r in v if r['classification']=='DEPTH_PRIOR')} | {sum(1 for r in v if r['classification'] in ('FACADE_ATTRIBUTION','OTHER_CHAIN_ATTRIBUTION','OFF_CHAIN_ERROR','DISCOVERY_FAILURE'))} |")
L += ["", "## Table 3 - project level (Sonnet)", "", "| Project | Pairs | Runs (valid) | Definer Acc@1 | Adapter Acc@1 | Attribution Gap | Misattribution rate (definer blamed on adapter arm) |", "|" + "---|" * 7]
for proj in sorted({pairs[p]["project"] for p in ORDER}):
    ps = [p for p in ORDER if pairs[p]["project"] == proj and T[(p, "sonnet", "DEFINER_FAULT")].get("valid") and T[(p, "sonnet", "ADAPTER_FAULT")].get("valid")]
    if not ps: continue
    v = [r for r in rows if r["project"] == proj and r["model"] == "sonnet" and VALID(r)]; ad = [r for r in v if r["arm"] == "ADAPTER_FAULT"]
    da = st.mean(T[(p, "sonnet", "DEFINER_FAULT")]["acc1"] for p in ps); aa = st.mean(T[(p, "sonnet", "ADAPTER_FAULT")]["acc1"] for p in ps)
    L.append(f"| {proj} | {len(ps)} | {len(v)} | {round(da,3)} | {round(aa,3)} | {round(da-aa,3)} | {round(sum(1 for r in ad if r['classification']=='DEFINER_ATTRIBUTION')/len(ad),3) if ad else '-'} |")
L += ["", "## Table 4 - cross-model representative subset (Acc@1 / MRR / gold ranks over valid attempts)", "", "| Bug | Sonnet Definer | Sonnet Adapter | Opus Definer | Opus Adapter |", "|---|---|---|---|---|"]
for p in ORDER:
    if not T[(p, "opus", "DEFINER_FAULT")].get("valid"): continue
    cell = lambda m, a: f"{T[(p,m,a)].get('acc1','-')} / {T[(p,m,a)].get('mrr','-')} / {T[(p,m,a)].get('ranks','-')}"
    L.append(f"| {p} | {cell('sonnet','DEFINER_FAULT')} | {cell('sonnet','ADAPTER_FAULT')} | {cell('opus','DEFINER_FAULT')} | {cell('opus','ADAPTER_FAULT')} |")
L += ["", "## Benchmark-wide (pair = replication unit)", "", "| Model | Pairs | Definer > Adapter | Equal | Reversed | Median gap | Mean gap | Definer Acc@1 | Adapter Acc@1 | Gold discovered but misranked | Second-caller retrieval | Depth-prior rate | No-answer rate | Valid/attempted runs | Stalls | Cost USD |", "|" + "---|" * 16]
for m, w_ in W.items(): L.append(f"| {m} | {w_['pairs']} | {w_['definer_gt_adapter']} | {w_['equal']} | {w_['reversed']} | {w_['median_gap']} | {w_['mean_gap']} | {w_['definer_acc1']} | {w_['adapter_acc1']} | {w_['gold_discovered_misranked_rate']} | {w_['second_caller_retrieval_rate']} | {w_['depth_prior_rate']} | {w_['no_answer_rate']} | {w_['runs_valid']}/{w_['runs_attempted']} | {w_['stalls']} | {w_['cost_usd']} |")
emit("THESIS_TABLES", "\n".join(L) + "\n")
# ---- per-model results, taxonomy, project summary, ownership analysis
def model_md(model, title):
    M = [f"# {title}", "", "Acc@1 over valid attempts (no-answers count as misses; provider stalls excluded). Per arm: answered/valid, Acc@1 (valid), Acc@1 (answered), Acc@3, Acc@5, MRR, gold ranks, classes.", "",
         "| Pair | Arm | answered/valid | Acc@1 | Acc@1 answered | Acc@3 | Acc@5 | MRR | gold ranks | H2 rank (H3 gold) / H3 rank (H2 gold) | pin seen | post-gold test | classes | stalls | cost |", "|" + "---|" * 15]
    for p in ORDER:
        for arm in ("DEFINER_FAULT", "ADAPTER_FAULT"):
            v = T[(p, model, arm)]
            if not v.get("valid"): continue
            other = v["h2_rank_when_h3_gold"] if arm == "ADAPTER_FAULT" else v["h3_rank_when_h2_gold"]
            M.append(f"| `{p}` | {arm} | {v['answered']}/{v['valid']} | **{v['acc1']}** | {v['acc1_answered']} | {v['acc3']} | {v['acc5']} | {v['mrr']} | {v['ranks']} | {other} | {v['pin_seen']}/{v['valid']} | {v['post_gold_test']}/{v['valid']} | {json.dumps(v['classes'])} | {v['stalls']} | {v['cost']} |")
    return "\n".join(M) + "\n"
emit("SONNET_RESULTS", model_md("sonnet", "Sonnet results (claude-sonnet-4-6, primary model)"))
emit("OPUS_REPLICATION", model_md("opus", "Opus replication (claude-opus-5-5, pre-registered five-pair subset)"))
Fx = ["# Failure classification (every valid run with gold rank != 1, plus no-answers)", "", "| Pair | Arm | Model | Run | Status | Gold rank | Rank-1 role | H2/H3 ranks | Gold discovered (step) | Pin seen | Tool calls | Class |", "|" + "---|" * 12]
for r in sorted(rows, key=lambda r: (r["pair_id"], r["arm"], r["model"], r["run"])):
    if VALID(r) and r["gold_rank"] != 1: Fx.append(f"| `{r['pair_id']}` | {r['arm']} | {r['model']} | {r['run']} | {r['status']} | {r['gold_rank']} | {r['rank1_role']} | H2={r['role_ranks'].get('H2')} H3={r['role_ranks'].get('H3')} | {'yes' if r['gold_discovered'] else 'no'} ({r['first_gold_exposure']}) | {'yes' if r['second_caller_evidence_retrieved'] else 'no'} | {r['tool_calls']} | **{r['classification']}** |")
cnt = collections.Counter((r["model"], r["arm"], r["classification"]) for r in rows if VALID(r))
Fx += ["", "## Counts (valid runs)", "", "| Model | Arm | Class | Runs |", "|---|---|---|---|"] + [f"| {m} | {a} | {c} | {n} |" for (m, a, c), n in sorted(cnt.items())]
emit("FAILURE_TAXONOMY", "\n".join(Fx) + "\n")
P = ["# Project summary", "", "| Project | Pairs | Sonnet valid runs | Sonnet Definer Acc@1 | Sonnet Adapter Acc@1 | Gap | Opus valid runs | Opus Definer Acc@1 | Opus Adapter Acc@1 |", "|" + "---|" * 9]
for proj in sorted({pairs[p]["project"] for p in ORDER}):
    ps = [p for p in ORDER if pairs[p]["project"] == proj]
    def pm(model):
        q = [p for p in ps if T[(p, model, "DEFINER_FAULT")].get("valid") and T[(p, model, "ADAPTER_FAULT")].get("valid")]
        if not q: return ("-", "-", "-", 0)
        return (round(st.mean(T[(p, model, "DEFINER_FAULT")]["acc1"] for p in q), 3), round(st.mean(T[(p, model, "ADAPTER_FAULT")]["acc1"] for p in q), 3), round(st.mean(gap(p, model) for p in q), 3), sum(T[(p, model, a)]["valid"] for p in q for a in ("DEFINER_FAULT", "ADAPTER_FAULT")))
    s_, o_ = pm("sonnet"), pm("opus"); P.append(f"| {proj} | {len(ps)} | {s_[3]} | {s_[0]} | {s_[1]} | {s_[2]} | {o_[3]} | {o_[0]} | {o_[1]} |")
emit("PROJECT_SUMMARY", "\n".join(P) + "\n")
OA = ["# Ownership analysis", "", "Every pair carries PINNED_UNIQUE ownership in both arms (validator gates V11/V12; see each `projects/*/bug-XX/analysis/OWNERSHIP_PROOF.md`).", "",
      "| Pair | Model | Adapter-arm runs blaming H2 first | Adapter-arm runs that opened the pin | Adapter-arm runs opening the pin AND correct | Definer-arm runs blaming H3 first |", "|" + "---|" * 6]
for p in ORDER:
    for model in ("sonnet", "opus"):
        v = [r for r in rows if r["pair_id"] == p and r["model"] == model and VALID(r)]
        if not v: continue
        ad = [r for r in v if r["arm"] == "ADAPTER_FAULT"]; de = [r for r in v if r["arm"] == "DEFINER_FAULT"]
        OA.append(f"| `{p}` | {model} | {sum(1 for r in ad if r['rank1_role']=='H2')}/{len(ad)} | {sum(1 for r in ad if r['second_caller_evidence_retrieved'])}/{len(ad)} | {sum(1 for r in ad if r['second_caller_evidence_retrieved'] and r['acc_at_1'])}/{max(1,sum(1 for r in ad if r['second_caller_evidence_retrieved']))} | {sum(1 for r in de if r['rank1_role']=='H3')}/{len(de)} |")
emit("OWNERSHIP_ANALYSIS", "\n".join(OA) + "\n")
# ---- figure data
FD = ["# Logic-chain figure data", "", "```", "Facade", "  |", "  v", "H1  input preparation / extraction", "  |", "  v", "H2  DEFINER  (semantic convention)      <-- Arm A: fault here      <-- second caller (pin test) -> H2", "  |", "  v", "H3  ADAPTER  (transformation)           <-- Arm B: fault here", "  |", "  v", "H4  consumer / application", "  |", "  v", "H5  final combination / output", "```", "",
      "| Pair | Facade | H1 | H2 (definer) | H3 (adapter) | H4 | H5 | Pin (second caller) | Family |", "|" + "---|" * 9]
for p in ORDER:
    ch = pairs[p]["chain"]; n = lambda r: f"`{ch[r]['class'].split('.')[-1]}.{ch[r]['method']}`"
    FD.append(f"| {p} | {n('facade')} | {n('H1')} | {n('H2')} | {n('H3')} | {n('H4')} | {n('H5')} | `{pairs[p]['pin_test'].split('::')[0].split('.')[-1]}::{pairs[p]['pin_test'].split('::')[1]}` | {fam(p)} |")
json.dump({p: {"chain": {r: f"{pairs[p]['chain'][r]['class']}#{pairs[p]['chain'][r]['method']}" for r in ("facade", "H1", "H2", "H3", "H4", "H5")}, "pin": pairs[p]["pin_test"], "family": pairs[p]["family"], "arm_A_fault": "H2", "arm_B_fault": "H3"} for p in ORDER}, open(f"{O}/analysis/tables/figure_data.json", "w"), indent=1)
open(f"{RS}/THESIS_FIGURE_DATA.md", "w").write("\n".join(FD) + "\n")
# ---- accounting
IA = ["# Infrastructure accounting", "", "| Server | Model | Runs attempted | Completed | No-answer (budget/time/context) | Provider stalls | Other |", "|" + "---|" * 7]
for srv in ("sonnetA", "sonnetB", "opusA"):
    rs = [r for r in rows if r["server"] == srv]
    if rs: IA.append(f"| {srv} | {rs[0]['model_id']} | {len(rs)} | {sum(1 for r in rs if r['status']=='completed')} | {sum(1 for r in rs if r['no_answer'])} | {sum(1 for r in rs if r['status']=='provider_stall')} | {sum(1 for r in rs if r['status'] not in ('completed','provider_stall') and not r['no_answer'])} |")
IA += ["", "Stall rule (uniform, from adversarial-break-v1): harness `timeout` with <= 2 model calls, or with the last event a tool result and > 60 s of silence to the deadline, is a hung provider request and is excluded from every denominator; `provider_error` with a context-overflow message is a no-answer (agent-made). Stalled attempts are topped up to the planned count per arm."]
emit("INFRASTRUCTURE_ACCOUNTING", "\n".join(IA) + "\n")
CA = ["# Cost accounting", "", "| Model | Runs | Cost USD | Mean per run |", "|---|---|---|---|"]
for m in ("sonnet", "opus"):
    rs = [r for r in rows if r["model"] == m]; c = sum(r["cost_usd"] or 0 for r in rs)
    if rs: CA.append(f"| {m} | {len(rs)} | {round(c,2)} | {round(c/len(rs),3)} |")
CA.append(f"| **total** | {len(rows)} | {round(sum(r['cost_usd'] or 0 for r in rows),2)} | |")
open(f"{RS}/COST_ACCOUNTING.md", "w").write("\n".join(CA) + "\n")
print("results built:", len(rows), "runs;", {m: (W[m]["pairs"], W[m]["definer_acc1"], W[m]["adapter_acc1"], W[m]["mean_gap"]) for m in W})

# ---- consolidated overview
OV = ["# OCFLB v1 results (NON-CANONICAL RESEARCH BENCHMARK)", "", f"{len(ORDER)} matched pairs, {2*len(ORDER)} variants, five projects; {len(rows)} paid runs. Acc@1 and MRR over valid attempts (provider stalls excluded; no-answers counted as misses).", "",
      "| Model | Pairs | Definer Acc@1 (mean of pairs) | Adapter Acc@1 (mean of pairs) | Mean attribution gap | Pairs definer > adapter / equal / reversed | Gold discovered but misranked | Second-caller retrieval | No-answer rate | Valid/attempted | Cost USD |", "|" + "---|" * 11]
for m, w_ in W.items(): OV.append(f"| {m} | {w_['pairs']} | {w_['definer_acc1']} | {w_['adapter_acc1']} | {w_['mean_gap']} | {w_['definer_gt_adapter']} / {w_['equal']} / {w_['reversed']} | {w_['gold_discovered_misranked_rate']} | {w_['second_caller_retrieval_rate']} | {w_['no_answer_rate']} | {w_['runs_valid']}/{w_['runs_attempted']} | {w_['cost_usd']} |")
OV += ["", "## Per pair (primary model)", "", "| Pair | Family | Definer Acc@1 | Adapter Acc@1 | Gap | Definer ranks | Adapter ranks | Definer no-answer | Adapter no-answer |", "|" + "---|" * 9]
for p in ORDER:
    d, a = T[(p, "sonnet", "DEFINER_FAULT")], T[(p, "sonnet", "ADAPTER_FAULT")]
    OV.append(f"| `{p}` | {fam(p)} | {d.get('acc1','-')} | {a.get('acc1','-')} | {gap(p,'sonnet')} | {d.get('ranks','-')} | {a.get('ranks','-')} | {d.get('no_answer','-')}/{d.get('valid','-')} | {a.get('no_answer','-')}/{a.get('valid','-')} |")
OV += ["", "Files: `THESIS_TABLES.md` (Tables 1-4), `SONNET_RESULTS.md`, `OPUS_REPLICATION.md`, `FAILURE_TAXONOMY.md`, `PROJECT_SUMMARY.md`, `OWNERSHIP_ANALYSIS.md`, `THESIS_FIGURE_DATA.md`, `INFRASTRUCTURE_ACCOUNTING.md`, `COST_ACCOUNTING.md`, `THREATS_TO_VALIDITY.md`, `FINAL_THESIS_INTERPRETATION.md`; data `ocflb_results.json`, `BUG_PAIR_RESULTS.csv`, `RUN_LEVEL_RESULTS.csv`."]
emit("OCFLB_RESULTS", "\n".join(OV) + "\n")
