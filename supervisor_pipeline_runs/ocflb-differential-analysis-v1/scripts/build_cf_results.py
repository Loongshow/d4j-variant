#!/usr/bin/env python
"""COUNTERFACTUAL_RESULTS.md from analysis/cf_run_metrics.json (+ V0 and V6 reference numbers)."""
import json, collections, os
D = "/Users/shawnli/Desktop/Honours/defects4j/supervisor_pipeline_runs/ocflb-differential-analysis-v1"; rows = json.load(open(f"{D}/analysis/cf_run_metrics.json")) if os.path.exists(f"{D}/analysis/cf_run_metrics.json") else []
REF = {"V0": {"sonnet": "0.0 (0/7 answered of 9 valid; ranks 5)", "opus": "0.0 v2 (5 runs, ranks 2,3,2,2,3); 0.2 v2+runner (ranks 2,2,2,2,1)"}, "V6": {"sonnet": "1.0 (5/5)", "opus": "0.8 (4/5)"}}
L = ["# Counterfactual results (Part 9 pilot)", "", "| Variant | Change | Sonnet Acc@1 (valid) | Sonnet ranks | Sonnet drift rank | Opus Acc@1 | Opus ranks | Pin opened | Status |", "|" + "---|" * 9]
v0 = [r for r in rows if r["variant"] == "ADV-DEFINER-01"]; v0s = [r for r in v0 if r["model"] == "sonnet" and r["status"] == "completed"]
L.append(f"| V0 | baseline (ADV-DEFINER-01) | {REF['V0']['sonnet']}; pilot anchor: {(str(sum(r['acc_at_1'] for r in v0s))+'/'+str(len(v0s))) if v0s else 'not yet run'} | {[r['gold_rank'] for r in v0s]} | 1 in every earlier miss | {REF['V0']['opus']} | - | 1/17 answered | measured 2026-09-27; anchor re-run in the pilot session |")
for v in ("V1", "V2", "V3", "V4", "V5"):
    cf = json.load(open(f"{D}/counterfactuals/packages/CF-{v}/cf.json")); rs = [r for r in rows if r["variant"] == f"CF-{v}"]
    cells = {}
    for m in ("sonnet", "opus"):
        q = [r for r in rs if r["model"] == m and r["status"] not in ("provider_stall", "provider_error")]; c = [r for r in q if r["status"] == "completed"]
        cells[m] = (f"{round(sum(r['acc_at_1'] for r in q)/len(q),2)} ({sum(r['acc_at_1'] for r in q)}/{len(q)})" if q else "not run", [r["gold_rank"] for r in c], [r["drift_rank"] for r in c])
    L.append(f"| {v} | {cf['changes']} | {cells['sonnet'][0]} | {cells['sonnet'][1]} | {cells['sonnet'][2]} | {cells['opus'][0]} | {cells['opus'][1]} | {sum(1 for r in rs if r['pin_seen'])}/{len(rs)} | {'run' if rs else 'BLOCKED_PROVIDER_QUOTA (validated, installed, not run)'} |")
L.append(f"| V6 | full OCFLB spec (= OCFLB-CHART-01-ADAPTER) | {REF['V6']['sonnet']} | [1,1,1,1,1] | 3-4 | {REF['V6']['opus']} | [1,2,1,1,1] | 0/10 | measured in ocflb-v1 |")
if rows:
    L += ["", "## Per-run", "", "| Variant | Model | Run | Status | Gold rank | drift rank | Tool calls | Tests | Pin | Rationale |", "|" + "---|" * 10]
    for r in rows: L.append(f"| {r['variant']} | {r['model']} | {r['run']} | {r['status']} | {r['gold_rank']} | {r['drift_rank']} | {r['tool_calls']} | {r['tests_run']} | {'yes' if r['pin_seen'] else 'no'} | {r['rationale'][:160]} |")
nar = f"{D}/analysis/narratives/COUNTERFACTUAL_RESULTS.md"
body = "\n".join(L) + "\n" + (("\n" + open(nar).read()) if os.path.exists(nar) else "")
open(f"{D}/COUNTERFACTUAL_RESULTS.md", "w").write(body); print("COUNTERFACTUAL_RESULTS.md written;", len(rows), "pilot runs")
