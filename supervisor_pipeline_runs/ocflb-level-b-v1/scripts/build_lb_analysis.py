#!/usr/bin/env python
"""Level-B specific analysis: EVIDENCE_RETRIEVAL_ANALYSIS.md, PER_PAIR_ANALYSIS.md, LEVEL_A_B_C_COMPARISON.md, FAILURE_TAXONOMY.md (analysis/),
RUN_METRICS.json copy, THESIS_FIGURE_DATA (accuracy vs specification level). Usage: build_lb_analysis.py"""
import json, os, glob, collections, statistics as st, shutil
SP = "/Users/shawnli/Desktop/Honours/defects4j/supervisor_pipeline_runs"; L = f"{SP}/ocflb-level-b-v1"; AN = f"{L}/analysis"; RS = f"{L}/results"; os.makedirs(AN, exist_ok=True); os.makedirs(RS, exist_ok=True)
rows = json.load(open(f"{L}/analysis/per_run/run_metrics.json")); shutil.copyfile(f"{L}/analysis/per_run/run_metrics.json", f"{AN}/RUN_METRICS.json")
V = lambda r: r.get("valid", r["status"] in ("completed", "timeout", "invalid_ranking", "context_overflow")); C = lambda r: r["status"] == "completed"
pairs = {json.load(open(p))["pair_id"]: json.load(open(p)) for p in glob.glob(f"{L}/projects/*/bug-*/pair.json")}
def acc(rs): return round(sum(r["acc_at_1"] for r in rs) / len(rs), 3) if rs else None
def mrr(rs): return round(sum(r["mrr"] for r in rs) / len(rs), 3) if rs else None
# ---- evidence retrieval analysis
E = ["# Evidence-retrieval analysis (Level B)", "", "External ownership evidence = the production second caller or its test, or the unit pin, appearing in any command or tool output before submission. Groups are valid attempts (provider stalls excluded); no-answers count as misses.", "",
     "| Model | Arm | Group | n | Acc@1 | MRR | Misattribution (definer/adapter attribution) | Gold discovered but misranked (answered) | Definer-attribution rate | No-answer |", "|" + "---|" * 10]
EXT = lambda r: r.get("any_external_evidence_retrieved", r["external_evidence_retrieved"] or r["second_caller_evidence_retrieved"])
GROUPS = {}
for model in ("sonnet", "opus"):
    for arm in ("ADAPTER_FAULT", "DEFINER_FAULT", "both"):
        base = [r for r in rows if r["model"] == model and V(r) and (arm == "both" or r["arm"] == arm)]
        for name, cond in (("E: retrieved external evidence", lambda r: EXT(r)), ("N: did not retrieve", lambda r: not EXT(r))):
            g = [r for r in base if cond(r)]; gc = [r for r in g if C(r)]
            if g:
                E.append(f"| {model} | {arm} | {name} | {len(g)} | {acc(g)} | {mrr(g)} | {sum(1 for r in g if r['classification'] in ('DEFINER_ATTRIBUTION','ADAPTER_ATTRIBUTION'))}/{len(g)} | {sum(1 for r in gc if r['gold_discovered'] and r['gold_rank']!=1)}/{len(gc)} | {round(sum(1 for r in g if r['classification']=='DEFINER_ATTRIBUTION')/len(g),3)} | {sum(1 for r in g if r['no_answer'])} |")
                GROUPS[f"{model}|{arm}|{name[0]}"] = {"n": len(g), "acc1": acc(g), "mrr": mrr(g), "answered": len(gc), "discovered_misranked": sum(1 for r in gc if r['gold_discovered'] and r['gold_rank']!=1), "misattribution": sum(1 for r in g if r['classification'] in ('DEFINER_ATTRIBUTION','ADAPTER_ATTRIBUTION')), "definer_attribution": sum(1 for r in g if r['classification']=='DEFINER_ATTRIBUTION')}
E += ["", "## Gold discovered but misranked (answered runs only)", "", "| Model | Arm | Answered | Gold opened | Gold opened and misranked | H2 opened | H3 opened | External evidence opened | Definer-first on adapter arm | Adapter-first on definer arm |", "|" + "---|" * 10]
for model in ("sonnet", "opus"):
    for arm in ("ADAPTER_FAULT", "DEFINER_FAULT"):
        c = [r for r in rows if r["model"] == model and C(r) and r["arm"] == arm]
        if c: E.append(f"| {model} | {arm} | {len(c)} | {sum(1 for r in c if r['gold_discovered'])} | {sum(1 for r in c if r['gold_discovered'] and r['gold_rank'] != 1)} | {sum(1 for r in c if r['h2_exposure'])} | {sum(1 for r in c if r['h3_exposure'])} | {sum(1 for r in c if r['external_evidence_retrieved'] or r['second_caller_evidence_retrieved'])} | {sum(1 for r in c if r['rank1_role']=='H2') if arm=='ADAPTER_FAULT' else '-'} | {sum(1 for r in c if r['rank1_role']=='H3') if arm=='DEFINER_FAULT' else '-'} |")
E += ["", "## Every answered wrong run", "", "| Pair | Arm | Model | Run | Gold rank | Rank-1 | Gold opened (step) | H2 / H3 opened | External evidence opened (step) | Class | Evidence subclass |", "|" + "---|" * 11]
for r in sorted(rows, key=lambda r: (r["pair_id"], r["arm"], r["model"], r["run"])):
    if C(r) and r["gold_rank"] != 1: E.append(f"| `{r['pair_id']}` | {r['arm']} | {r['model']} | {r['run']} | {r['gold_rank']} | {r['rank1']} ({r['rank1_role']}) | {'yes' if r['gold_discovered'] else 'no'} ({r['first_gold_exposure']}) | {r['h2_exposure']} / {r['h3_exposure']} | {'yes' if (r['external_evidence_retrieved'] or r['second_caller_evidence_retrieved']) else 'no'} ({r['external_evidence_step'] or r['pin_seen_step']}) | **{r['classification']}** | {r['evidence_subclass'] or '-'} |")
open(f"{AN}/EVIDENCE_RETRIEVAL_ANALYSIS.md", "w").write("\n".join(E) + "\n")
# ---- per pair analysis
P = ["# Per-pair analysis (Level B)", ""]
for pid in sorted(pairs):
    P.append(f"## {pid} ({pairs[pid]['family']})\n\n| Model | Arm | valid | answered | Acc@1 | MRR | gold ranks | rank-1 roles | external evidence opened | pin opened | no-answer | classes |\n|" + "---|" * 12)
    for model in ("sonnet", "opus"):
        for arm in ("DEFINER_FAULT", "ADAPTER_FAULT"):
            v = [r for r in rows if r["pair_id"] == pid and r["model"] == model and r["arm"] == arm and V(r)]; c = [r for r in v if C(r)]
            if v: P.append(f"| {model} | {arm} | {len(v)} | {len(c)} | {acc(v)} | {mrr(v)} | {[r['gold_rank'] for r in c]} | {dict(collections.Counter(r['rank1_role'] for r in c))} | {sum(1 for r in v if r['external_evidence_retrieved'])}/{len(v)} | {sum(1 for r in v if r['second_caller_evidence_retrieved'])}/{len(v)} | {sum(1 for r in v if r['no_answer'])} | {dict(collections.Counter(r['classification'] for r in v))} |")
    P.append("")
open(f"{AN}/PER_PAIR_ANALYSIS.md", "w").write("\n".join(P) + "\n")
# ---- failure taxonomy (Level B classes; no-answers separately)
F = ["# Failure taxonomy (Level B)", "", "Answered wrong runs by class (misranking only):", "", "| Model | Arm | Class | Evidence subclass | Runs |", "|---|---|---|---|---|"]
cnt = collections.Counter((r["model"], r["arm"], r["classification"], r["evidence_subclass"] or "-") for r in rows if C(r) and r["gold_rank"] != 1)
F += [f"| {m} | {a} | {c} | {e} | {n} |" for (m, a, c, e), n in sorted(cnt.items())]
F += ["", "No-answers and infrastructure (separate from misranking):", "", "| Model | Arm | Subclass | Runs |", "|---|---|---|---|"]
cnt2 = collections.Counter((r["model"], r["arm"], r["no_answer_subclass"] or r["status"]) for r in rows if not C(r))
F += [f"| {m} | {a} | {c} | {n} |" for (m, a, c), n in sorted(cnt2.items())]
# graded mechanism (analysis/mechanism/mechanism_grading.json, produced by the blinded grading workflow + assemble_mechanism.py)
mg_path = f"{AN}/mechanism/mechanism_grading.json"
if os.path.exists(mg_path):
    mg = json.load(open(mg_path)); byrun = {k.replace(".md", ""): v for k, v in mg.items()}
    F += ["", "## Graded primary mechanism of every answered wrong run (two blinded graders per run, third adjudicates; `analysis/MECHANISM_GRADING.md`)", "", "| Model | Arm | Graded mechanism | Runs |", "|---|---|---|---|"]
    cm = collections.Counter()
    for r in rows:
        if C(r) and r["gold_rank"] != 1:
            v = byrun.get(f"{r['model']}__{r['variant_id']}__{r['run']}"); cm[(r["model"], r["arm"], v["final"] if v else "not graded")] += 1
    F += [f"| {m} | {a} | {k} | {n} |" for (m, a, k), n in sorted(cm.items())]
    F += ["", "Mechanism definitions: LOCAL_ODDNESS = the blamed hop's body looked wrong under a convention the agent assumed; DEPTH_PRIOR = blamed by chain position; EXTERNAL_EVIDENCE_NOT_RETRIEVED = trace-based choice of hop with no oddness claim and no external evidence opened; EXTERNAL_EVIDENCE_MISREAD = the second caller, its test or the pin was opened and the wrong hop was still blamed; OFF_CHAIN_ERROR; OTHER."]
open(f"{AN}/FAILURE_TAXONOMY.md", "w").write("\n".join(F) + "\n")
# ---- Level A / B / C comparison
adv = json.load(open(f"{SP}/adversarial-break-v1/analysis/per_run/attack_run_metrics.json")); oc = json.load(open(f"{SP}/ocflb-v1/analysis/per_run/run_metrics.json"))
diffx = json.load(open(f"{SP}/ocflb-differential-analysis-v1/analysis/trajectory_differential.json"))
def mean(xs): xs = [x for x in xs if x is not None]; return round(st.mean(xs), 1) if xs else None
VALID_ST = ("completed", "timeout", "invalid_ranking", "context_overflow")
def pilot_anchor_rows(model):
    """ADV-DEFINER-01 (V0) anchor runs of the differential pilot (same variant, protocol v2+runner, run in the Level-B session)."""
    p_ = f"{SP}/ocflb-differential-analysis-v1/analysis/cf_run_metrics.json"
    if not os.path.exists(p_): return []
    out = []
    for r in json.load(open(p_)):
        if r["variant"] != "ADV-DEFINER-01" or r["model"] != model: continue
        top = r.get("top5") or []; gr = r.get("gold_rank")
        out.append({"status": r["status"], "gold_rank": gr, "acc_at_1": gr == 1, "mrr": (1 / gr) if gr else 0.0, "tool_calls": r.get("tool_calls"), "gold_first_exposed_step": None, "submitted_top10": top, "gold_discovered": None, "file_reads": None, "searches": None, "pin_test_opened": r.get("pin_seen"), "source": "pilot-anchor"})
    return out
def lvA(model):
    srvs = ("sonnet46", "sonnet46t") if model == "sonnet" else ("opus55", "opus55t")      # protocol v2 and v2+runner pooled
    rs = [dict(r, source=r["model"]) for r in adv if r["attack"] == "CMB-01" and r["model"] in srvs and r["status"] in VALID_ST] + pilot_anchor_rows(model)
    c = [r for r in rs if r["status"] == "completed"]
    tx = [t for t in diffx if any(t["label"].startswith(f"ADV/{x}/") for x in srvs)]
    ext_hits = sum(1 for t in tx if t["pin_test_opened"]) + sum(1 for r in rs if r.get("source") == "pilot-anchor" and r.get("pin_test_opened")); ext_n = len(tx) + sum(1 for r in rs if r.get("source") == "pilot-anchor")
    def drift_above_gold(r):
        top = r.get("submitted_top10") or []; gr = r.get("gold_rank")
        return ("PlotUtilities::drift" in top) and (gr is None or top.index("PlotUtilities::drift") + 1 < gr)
    return {"n_valid": len(rs), "acc1": acc(rs), "mrr": mrr(rs), "ext_rate": round(ext_hits / ext_n, 3) if ext_n else None, "misranked": sum(1 for r in c if r["gold_rank"] != 1 and r.get("gold_discovered") is not False), "answered": len(c),
            "tool_calls": mean([r["tool_calls"] for r in rs]), "first_gold": mean([r.get("gold_first_exposed_step") for r in c]), "attribution_errors": sum(1 for r in c if drift_above_gold(r)), "ranks": sorted([r["gold_rank"] for r in c if r["gold_rank"]]), "absent": sum(1 for r in c if not r["gold_rank"]), "no_answer": sum(1 for r in rs if r["status"] != "completed"),
            "file_reads": mean([r.get("file_reads") for r in rs]), "searches": mean([r.get("searches") for r in rs]), "sources": dict(collections.Counter(r.get("source") for r in rs))}
def lvC(model):
    rs = [r for r in oc if r["model"] == model and r["arm"] == "ADAPTER_FAULT" and r["status"] in VALID_ST]; c = [r for r in rs if r["status"] == "completed"]
    return {"n_valid": len(rs), "acc1": acc(rs), "mrr": mrr(rs), "ext_rate": round(sum(1 for r in rs if r["second_caller_evidence_retrieved"]) / len(rs), 3) if rs else None, "misranked": sum(1 for r in c if r["gold_discovered"] and r["gold_rank"] != 1), "answered": len(c),
            "tool_calls": mean([r["tool_calls"] for r in rs]), "first_gold": mean([r.get("first_gold_exposure") for r in c]), "attribution_errors": sum(1 for r in c if r["classification"] == "DEFINER_ATTRIBUTION"), "ranks": sorted([r["gold_rank"] for r in c if r["gold_rank"]]), "absent": sum(1 for r in c if not r["gold_rank"]), "no_answer": sum(1 for r in rs if r["status"] != "completed"),
            "file_reads": mean([r.get("file_reads") for r in rs]), "searches": mean([r.get("repository_searches") for r in rs])}
def lvB(model):
    rs = [r for r in rows if r["model"] == model and r["arm"] == "ADAPTER_FAULT" and V(r)]; c = [r for r in rs if C(r)]
    return {"n_valid": len(rs), "acc1": acc(rs), "mrr": mrr(rs), "ext_rate": round(sum(1 for r in rs if EXT(r)) / len(rs), 3) if rs else None, "misranked": sum(1 for r in c if r["gold_discovered"] and r["gold_rank"] != 1), "answered": len(c),
            "tool_calls": mean([r["tool_calls"] for r in rs]), "first_gold": mean([r.get("first_gold_exposure") for r in c]), "attribution_errors": sum(1 for r in c if r["classification"] == "DEFINER_ATTRIBUTION"), "ranks": sorted([r["gold_rank"] for r in c if r["gold_rank"]]), "absent": sum(1 for r in c if not r["gold_rank"]), "no_answer": sum(1 for r in rs if r["status"] != "completed"),
            "file_reads": mean([r.get("file_reads") for r in rs]), "searches": mean([r.get("repository_searches") for r in rs])}
LOCAL = {"A": "ambiguous (javadocs silent; correct hop looks odd, gold is an omission)", "B": "ambiguous (V15 pass, V16 LOCAL_AMBIGUOUS, 60/60 blinded graders)", "C": "explicit (H2 javadoc states the convention; faulty hop contradicts its own doc)"}
GLOBAL = {"A": "weak (unit pin only; no production second caller)", "B": "decisive (production second caller + its test + unit pin; PINNED_UNIQUE)", "C": "decisive (unit pin; PINNED_UNIQUE)"}
levels = {m: {"A": lvA(m), "B": lvB(m), "C": lvC(m)} for m in ("sonnet", "opus")}
json.dump(levels, open(f"{AN}/level_abc.json", "w"), indent=1)
K = ["# Level A vs B vs C comparison (adapter-fault arms: the ownership question is posed at H3)", "", "Level A = adversarial pair ADV-DEFINER-01 (local ambiguity, unit-test pin only, no production second caller); Level B = this benchmark (local ambiguity, production second caller + pin); Level C = OCFLB v1 adapter arms (locally explicit, pin). Acc@1 over valid attempts; misranked = answered runs with gold rank > 1.", "",
     "| Level | Local ownership evidence | Global ownership evidence | Model | Valid runs | Answered | No-answer | Acc@1 | MRR | Gold discovered but misranked (answered) | Attribution errors (definer blamed, answered) | External-evidence retrieval rate | Mean tool calls | Mean first-gold exposure step | Mean file reads | Mean searches | Gold ranks (answered) |", "|" + "---|" * 17]
for lv in ("A", "B", "C"):
    for m in ("sonnet", "opus"):
        d = levels[m][lv]; K.append(f"| {lv} | {LOCAL[lv]} | {GLOBAL[lv]} | {m} | {d['n_valid']} | {d['answered']} | {d['no_answer']} | {d['acc1']} | {d['mrr']} | {d['misranked']}/{d['answered']} | {d['attribution_errors']}/{d['answered']} | {d['ext_rate']} | {d['tool_calls']} | {d['first_gold']} | {d['file_reads']} | {d['searches']} | {d['ranks']} |")
K += ["", f"Level A rows = every valid ADV-DEFINER-01 (attack CMB-01) run: adversarial root protocol v2 (sonnet46 / opus55) and v2+runner (sonnet46t / opus55t) pooled, plus the V0 anchor runs of the differential pilot (same variant, protocol v2+runner, run in the Level-B session); sources per model: sonnet {levels['sonnet']['A'].get('sources')}, opus {levels['opus']['A'].get('sources')}. 'Attribution errors' = answered runs that ranked the definer hop above the gold (Level A: `PlotUtilities.drift` above `Plot.nudge`; Levels B/C: classification DEFINER_ATTRIBUTION). 'Gold discovered but misranked' requires the gold body to have been exposed in a tool output (Level A pilot-anchor rows lack the exposure field and are counted by rank only). 'Mean first-gold exposure step' averages the answered runs that exposed the gold. Level C rows = every OCFLB v1 adapter-fault arm (10 pairs). Level B = this benchmark's adapter-fault arms (5 pairs)."]
open(f"{AN}/LEVEL_A_B_C_COMPARISON.md", "w").write("\n".join(K) + "\n")
# Table 5 appended to THESIS_TABLES.md (build_results.py writes the first four tables before this script runs)
T5 = ["", "## Table 5 - Level A / B / C (adapter-fault arms; Acc@1 and MRR over valid attempts)", "", "| Level | Local ownership evidence | Global ownership evidence | Model | Runs (valid) | Acc@1 | MRR | Gold discovered but misranked | External-evidence retrieval |", "|" + "---|" * 9]
for lv in ("A", "B", "C"):
    for m in ("sonnet", "opus"):
        d = levels[m][lv]; T5.append(f"| {lv} | {LOCAL[lv].split(' (')[0]} | {GLOBAL[lv].split(' (')[0]} | {m} | {d['n_valid']} | {d['acc1']} | {d['mrr']} | {d['misranked']}/{d['answered']} | {d['ext_rate']} |")
tt = open(f"{RS}/THESIS_TABLES.md").read(); tt = tt.split("\n## Table 5 - Level A / B / C")[0].rstrip("\n"); open(f"{RS}/THESIS_TABLES.md", "w").write(tt + "\n" + "\n".join(T5) + "\n")
FD = ["# Thesis figure data", "", "## Figure 1 - Acc@1 by ownership-specification level (adapter-fault arms; valid attempts)", "", "| Level | Specification | Model | Acc@1 (adapter-fault arm) | MRR | External-evidence retrieval rate | n valid |", "|---|---|---|---|---|---|---|"]
desc = {"A": "under-specified (local ambiguity, weak external ownership)", "B": "globally specified, locally ambiguous", "C": "locally explicit"}
for lv in ("A", "B", "C"):
    for m in ("sonnet", "opus"):
        d = levels[m][lv]; FD.append(f"| {lv} | {desc[lv]} | {m} | {d['acc1']} | {d['mrr']} | {d['ext_rate']} | {d['n_valid']} |")
FD += ["", "Level B and C definer-fault arms (for completeness):", "", "| Level | Model | Acc@1 | MRR | n valid |", "|---|---|---|---|---|"]
for m in ("sonnet", "opus"):
    rs = [r for r in rows if r["model"] == m and r["arm"] == "DEFINER_FAULT" and V(r)]; FD.append(f"| B | {m} | {acc(rs)} | {mrr(rs)} | {len(rs)} |")
    rc = [r for r in oc if r["model"] == m and r["arm"] == "DEFINER_FAULT" and r["status"] not in ("provider_stall", "provider_error")]; FD.append(f"| C | {m} | {acc(rc)} | {mrr(rc)} | {len(rc)} |")
FIG = {"figure1_acc_by_level": levels}
# Figure 2: Acc@1 conditional on external-evidence retrieval (Level B, by model and arm)
FD += ["", "## Figure 2 - Acc@1 conditional on external-evidence retrieval (Level B; valid attempts)", "", "| Model | Arm | Retrieved (E) n | E Acc@1 | E MRR | Not retrieved (N) n | N Acc@1 | N MRR |", "|" + "---|" * 8]
for m in ("sonnet", "opus"):
    for arm in ("ADAPTER_FAULT", "DEFINER_FAULT", "both"):
        e = GROUPS.get(f"{m}|{arm}|E", {}); n_ = GROUPS.get(f"{m}|{arm}|N", {})
        if e or n_: FD.append(f"| {m} | {arm} | {e.get('n',0)} | {e.get('acc1')} | {e.get('mrr')} | {n_.get('n',0)} | {n_.get('acc1')} | {n_.get('mrr')} |")
FIG["figure2_acc_by_evidence_retrieval"] = GROUPS
# Figure 3: gold-rank distribution by level (answered runs; no-answers listed separately)
def dist(ranks, n_absent, n_no):
    cnt = collections.Counter(min(r, 6) for r in ranks); return {"1": cnt.get(1, 0), "2": cnt.get(2, 0), "3": cnt.get(3, 0), "4": cnt.get(4, 0), "5": cnt.get(5, 0), "6+": cnt.get(6, 0), "absent": n_absent, "no_answer": n_no}
FD += ["", "## Figure 3 - gold-rank distribution by level (adapter-fault arms; counts of answered runs by gold rank; 'absent' = answered but the gold is not in the submitted list; no-answers separate)", "", "| Level | Model | rank 1 | rank 2 | rank 3 | rank 4 | rank 5 | rank 6+ | absent | no-answer | n valid |", "|" + "---|" * 11]
FIG["figure3_rank_distribution"] = {}
for lv in ("A", "B", "C"):
    for m in ("sonnet", "opus"):
        d = levels[m][lv]; ds = dist(d["ranks"], d.get("absent", 0), d["no_answer"]); FIG["figure3_rank_distribution"][f"{lv}|{m}"] = ds
        FD.append(f"| {lv} | {m} | {ds['1']} | {ds['2']} | {ds['3']} | {ds['4']} | {ds['5']} | {ds['6+']} | {ds['absent']} | {ds['no_answer']} | {d['n_valid']} |")
# Figure 4: search effort vs final attribution correctness (Level B, per model; plus per-run points)
FD += ["", "## Figure 4 - search effort versus final attribution correctness (Level B; valid attempts grouped by outcome)", "", "| Model | Outcome | n | Mean tool calls | Mean file reads | Mean searches | Mean test executions | Mean first-gold exposure step (runs that exposed it) | External evidence retrieved |", "|" + "---|" * 9]
FIG["figure4_effort_vs_outcome"] = {}; FIG["figure4_points"] = []
for m in ("sonnet", "opus"):
    v = [r for r in rows if r["model"] == m and V(r)]
    for name, cond in (("correct (gold rank 1)", lambda r: C(r) and r["gold_rank"] == 1), ("answered wrong", lambda r: C(r) and r["gold_rank"] != 1), ("no-answer", lambda r: not C(r))):
        g = [r for r in v if cond(r)]
        if g:
            rec = {"n": len(g), "tool_calls": mean([r["tool_calls"] for r in g]), "file_reads": mean([r["file_reads"] for r in g]), "searches": mean([r["repository_searches"] for r in g]), "tests": mean([r["test_executions"] for r in g]), "first_gold": mean([r["first_gold_exposure"] for r in g]), "ext": f"{sum(1 for r in g if EXT(r))}/{len(g)}"}
            FIG["figure4_effort_vs_outcome"][f"{m}|{name}"] = rec; FD.append(f"| {m} | {name} | {rec['n']} | {rec['tool_calls']} | {rec['file_reads']} | {rec['searches']} | {rec['tests']} | {rec['first_gold']} | {rec['ext']} |")
    FIG["figure4_points"] += [{"model": m, "pair": r["pair_id"], "arm": r["arm"], "run": r["run"], "tool_calls": r["tool_calls"], "file_reads": r["file_reads"], "searches": r["repository_searches"], "first_gold": r["first_gold_exposure"], "gold_rank": r["gold_rank"], "correct": bool(r["acc_at_1"]), "status": r["status"], "ext": bool(EXT(r))} for r in v]
open(f"{RS}/THESIS_FIGURE_DATA.md", "w").write("\n".join(FD) + "\n"); json.dump(FIG, open(f"{RS}/thesis_figure_data.json", "w"), indent=1)
print("level-B analysis built:", {m: {lv: levels[m][lv]["acc1"] for lv in "ABC"} for m in levels})
