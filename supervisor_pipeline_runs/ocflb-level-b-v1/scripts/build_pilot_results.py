#!/usr/bin/env python
"""PILOT_RESULTS.md for the Level-B root from the differential pilot (ocflb-differential-analysis-v1/analysis/cf_run_metrics.json).
Applies the pre-registered decision mapping (COUNTERFACTUAL_DESIGN.md): V1 alone restores -> CASE A; V1/V2 do not but V3 or V4 do -> CASE B;
only V5 restores -> CASE C; V2 restores -> CASE D; none -> CASE E. 'Restores' = Sonnet Acc@1 over valid attempts >= 0.67 (2 of 3) on that
condition while the V0 anchor stays <= 0.33; a condition with 0.33 < Acc@1 < 0.67 or with fewer than 2 valid attempts is 'partial'.
Usage: build_pilot_results.py [narrative.md]"""
import json, os, sys, collections
SP = "/Users/shawnli/Desktop/Honours/defects4j/supervisor_pipeline_runs"; D = f"{SP}/ocflb-differential-analysis-v1"; L = f"{SP}/ocflb-level-b-v1"
rows = json.load(open(f"{D}/analysis/cf_run_metrics.json")); VALID = ("completed", "timeout", "invalid_ranking", "context_overflow")
COND = {"ADV-DEFINER-01": "V0 anchor (no change)", "CF-V1": "V1 production second caller + test (second-caller pinning)", "CF-V2": "V2 sibling implementation + test (external correctness reference)", "CF-V3": "V3 explicit H2 javadoc (local definer documentation)", "CF-V4": "V4 explicit H3 javadoc (local adapter documentation)", "CF-V5": "V5 explicit adapter self-incrimination (unary minus at the gold; definer convention natural)"}
def cell(v, m):
    q = [r for r in rows if r["variant"] == v and r["model"] == m and r["status"] in VALID]; c = [r for r in q if r["status"] == "completed"]
    if not q: return None
    return {"n_valid": len(q), "answered": len(c), "acc1": round(sum(r["acc_at_1"] for r in q) / len(q), 3), "mrr": round(sum(r["mrr"] for r in q) / len(q), 3), "ranks": [r["gold_rank"] for r in c], "drift_ranks": [r["drift_rank"] for r in c],
            "no_answer": sum(1 for r in q if r["status"] != "completed"), "stalls": sum(1 for r in rows if r["variant"] == v and r["model"] == m and r["status"] == "provider_stall"), "pin_seen": sum(1 for r in q if r["pin_seen"]), "tests": sum(r["tests_run"] for r in q), "cost": round(sum(r["cost_usd"] or 0 for r in rows if r["variant"] == v and r["model"] == m), 3), "tool_calls": round(sum(r["tool_calls"] for r in q) / len(q), 1)}
T = {v: {m: cell(v, m) for m in ("sonnet", "opus")} for v in COND}
def status(v):
    c = T[v]["sonnet"]
    if not c or c["n_valid"] < 2: return "insufficient"
    return "restores" if c["acc1"] >= 0.67 else ("partial" if c["acc1"] > 0.33 else "no")
S = {v: status(v) for v in COND}; anchor_ok = T["ADV-DEFINER-01"]["sonnet"] and T["ADV-DEFINER-01"]["sonnet"]["acc1"] <= 0.34
if S["CF-V1"] == "restores": case = "CASE A (second-caller pinning alone restores)"
elif S["CF-V2"] == "restores": case = "CASE D (any global correctness reference restores)"
elif S["CF-V3"] == "restores" or S["CF-V4"] == "restores": case = "CASE B (local specification leakage)"
elif S["CF-V5"] == "restores": case = "CASE C (local self-incrimination)"
else: case = "CASE E (nothing alone restores)"
M = ["# Differential pilot results (Phase 1; run 2026-10-01 before any Level-B run)", "", "Base V0 = ADV-DEFINER-01 (gold `Plot.nudge`, H3). Each condition changes exactly one thing (design: `ocflb-differential-analysis-v1/COUNTERFACTUAL_DESIGN.md`). Acc@1 and MRR over valid attempts (no-answers count as misses; provider stalls excluded); Sonnet 3 planned runs per condition, Opus 3 on the two pre-registered conditions (V3, V5). Servers sonnetCF (8811) / opusCF (8812) with the corrected runner environment (proofs in `ocflb-differential-analysis-v1/diagnostic/RUNNER_ENV_PROOF_*.md`).", "",
     "| Condition | Sonnet valid | Sonnet Acc@1 | Sonnet MRR | Sonnet gold ranks | Sonnet drift ranks | Sonnet no-answer | Opus valid | Opus Acc@1 | Opus MRR | Opus gold ranks | Pin opened (S/O) | Status vs V0 |", "|" + "---|" * 13]
for v, name in COND.items():
    s_, o_ = T[v]["sonnet"], T[v]["opus"]
    f = lambda c, k: c[k] if c else "-"
    M.append(f"| {name} | {f(s_,'n_valid')} | **{f(s_,'acc1')}** | {f(s_,'mrr')} | {f(s_,'ranks')} | {f(s_,'drift_ranks')} | {f(s_,'no_answer')} | {f(o_,'n_valid')} | **{f(o_,'acc1')}** | {f(o_,'mrr')} | {f(o_,'ranks')} | {f(s_,'pin_seen')}/{f(o_,'pin_seen')} | {S[v] if v != 'ADV-DEFINER-01' else ('anchor holds' if anchor_ok else 'ANCHOR DRIFTED')} |")
M += ["", f"Pre-registered decision mapping applied to the Sonnet results: **{case}**. Condition statuses: " + ", ".join(f"{v}={S[v]}" for v in COND if v != "ADV-DEFINER-01") + ".", "",
      "## Per run", "", "| Condition | Model | Run | Status | Gold rank | drift rank | Tool calls | Tests | Pin | Cost | Rationale (evidence chain) |", "|" + "---|" * 11]
for r in sorted(rows, key=lambda r: (list(COND).index(r["variant"]) if r["variant"] in COND else 9, r["model"], r["run"])):
    M.append(f"| {r['variant']} | {r['model']} | {r['run']} | {r['status']} | {r['gold_rank']} | {r['drift_rank']} | {r['tool_calls']} | {r['tests_run']} | {'yes' if r['pin_seen'] else 'no'} | {round(r['cost_usd'] or 0, 3)} | {(r['rationale'] or '')[:220].replace('|', '/')} |")
tot = {m: (len([r for r in rows if r["model"] == m]), round(sum(r["cost_usd"] or 0 for r in rows if r["model"] == m), 2)) for m in ("sonnet", "opus")}
M += ["", f"Runs: Sonnet {tot['sonnet'][0]} ({tot['sonnet'][1]} USD), Opus {tot['opus'][0]} ({tot['opus'][1]} USD)."]
nar = sys.argv[1] if len(sys.argv) > 1 else f"{L}/analysis/narratives/PILOT_RESULTS.md"
if os.path.exists(nar): M += ["", open(nar).read().rstrip("\n")]
open(f"{L}/PILOT_RESULTS.md", "w").write("\n".join(M) + "\n"); json.dump({"cells": T, "statuses": S, "case": case, "anchor_ok": anchor_ok}, open(f"{L}/analysis/pilot_results.json", "w"), indent=1); print("PILOT_RESULTS.md:", case, S)
