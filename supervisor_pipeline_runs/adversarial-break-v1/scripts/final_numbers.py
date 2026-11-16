#!/usr/bin/env python
"""Compact per attack x model summary from analysis/tables/attack_by_model.json plus validity rows and spend, for the final report."""
import json, collections
R = "/Users/shawnli/Desktop/Honours/defects4j/supervisor_pipeline_runs/adversarial-break-v1"
T = json.load(open(f"{R}/analysis/tables/attack_by_model.json")); rows = json.load(open(f"{R}/analysis/per_run/attack_run_metrics.json"))
def lab(a):
    if a is None: return "-"
    return "VERY STRONG" if a <= 0.30 else "STRONG" if a <= 0.50 else "MODERATE" if a <= 0.70 else "WEAK" if a <= 0.90 else "NULL"
print(f"{'attack':10s} {'model':9s} {'ans/att':8s} {'valid':5s} {'acc1_ans':8s} {'acc1_all':8s} {'label':11s} {'mrr':5s} ranks / exhausted / stalls")
for k, v in sorted(T.items()):
    a, m = k.split("|")
    if not v.get("attempted"): continue
    print(f"{a:10s} {m:9s} {str(v.get('n',0))+'/'+str(v['attempted']):8s} {str(v.get('n_valid','-')):5s} {str(v.get('acc1','-')):8s} {str(v.get('acc1_all')):8s} {lab(v.get('acc1_all')):11s} {str(v.get('mrr','-')):5s} {v.get('ranks')} / {v.get('exhausted')} / {v.get('infra')}")
print("\nvalidity (v2+runner):")
for m in ("opus55t", "sonnet46t"):
    rs = [r for r in rows if r["model"] == m]
    comp = [r for r in rs if r["status"] == "completed"]; valid = [r for r in rs if r["status"] not in ("provider_error", "provider_stall")]
    if rs: print(f"  {m}: n={len(rs)} valid={len(valid)} ranks={[r['gold_rank'] for r in comp]} acc1_all={round(sum(r['acc_at_1'] for r in valid)/len(valid),3)} tests_executed={sum(r['test_runs']>0 for r in rs)}")
sp = collections.defaultdict(float); st = collections.Counter()
for r in rows: sp[r["model"]] += r["cost_usd"] or 0; st[r["status"]] += 1
print("\nruns:", len(rows), dict(st)); print("spend USD:", {k: round(v, 2) for k, v in sp.items()}, "total", round(sum(sp.values()), 2))
