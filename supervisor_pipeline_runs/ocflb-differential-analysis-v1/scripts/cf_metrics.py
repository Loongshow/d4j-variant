#!/usr/bin/env python
"""Per-run metrics for the counterfactual pilot (same rules as ocflb_metrics: stall rule, no-answers counted). Writes analysis/cf_run_metrics.json."""
import glob, json, os, re, datetime
D = "/Users/shawnli/Desktop/Honours/defects4j/supervisor_pipeline_runs/ocflb-differential-analysis-v1"; SERVERS = {"sonnetCF": "sonnet", "opusCF": "opus"}
def rj(p):
    try: return json.load(open(p))
    except Exception: return {}
rows = []
CFS = [rj(p) for p in sorted(glob.glob(f"{D}/counterfactuals/packages/CF-*/cf.json"))] + [{"variant_id": "ADV-DEFINER-01", "gold": {"class": "org.jfree.chart.plot.Plot", "method": "nudge"}}]   # V0 anchor
for cf in CFS:
    V = cf["variant_id"]; gold_key = f"{cf['gold']['class'].split('.')[-1]}::{cf['gold']['method']}"
    for srv, model in SERVERS.items():
        for rd in sorted(glob.glob(f"{D}/models/{srv}/benchmark_runs/mini-swe-claude/{V}/run-*")):
            man = rj(f"{rd}/run_manifest.json"); traj = rj(f"{rd}/mini-swe-agent.traj.json"); ev = rj(f"{rd}/evaluation.json"); rk = rj(f"{rd}/ranking.json")
            if not man: continue
            msgs = traj.get("messages") or []; ms = (traj.get("info") or {}).get("model_stats") or {}
            cmds = [a.get("command") or "TOOL" for m in msgs if m.get("role") == "assistant" for a in ((m.get("extra") or {}).get("actions") or [])]
            outs = [str((m.get("extra") or {}).get("raw_output") or m.get("content") or "") for m in msgs if m.get("role") == "tool"]
            preds = ((rk.get("structured_submission") or {}).get("predictions") or rk.get("predictions") or []); top = [f"{p['class'].split('.')[-1]}::{p['method']}" for p in preds[:10]]
            st_ = man.get("status"); stall = st_ == "timeout" and (ms.get("api_calls") or 0) <= 2 and len(cmds) <= 2
            if st_ == "timeout":
                try:
                    t0 = datetime.datetime.fromisoformat(re.search(r"execution_timer_started_at: (\S+)", open(f"{rd}/commands.log").read()).group(1).replace("Z", "+00:00")).timestamp()
                    evs = [(m["role"], float(m["extra"]["timestamp"])) for m in msgs if m.get("role") in ("assistant", "tool") and (m.get("extra") or {}).get("timestamp") is not None]
                    if evs and evs[-1][0] == "tool" and t0 + 300 - evs[-1][1] > 60: stall = True
                except Exception: pass
            if stall: st_ = "provider_stall"
            pin_seen = any("PlotUtilitiesTests" in c or "testDrift" in c for c in cmds) or any("PlotUtilitiesTests" in o for o in outs)
            ec = (rk.get("structured_submission") or {}).get("evidence_chain") or []; rationale = " | ".join(e.get("evidence", "") + " => " + e.get("inference_summary", "") for e in ec)[:600]
            rows.append({"variant": V, "server": srv, "model": model, "run": os.path.basename(rd), "status": st_, "harness_status": man.get("status"), "gold_rank": ev.get("gold_rank"), "acc_at_1": ev.get("gold_rank") == 1, "mrr": round(1 / ev["gold_rank"], 3) if ev.get("gold_rank") else 0.0,
                         "top5": top[:5], "drift_rank": (top.index("PlotUtilities::drift") + 1) if "PlotUtilities::drift" in top else None, "tool_calls": len(cmds), "tests_run": sum(1 for c in cmds if "defects4j test" in c), "pin_seen": pin_seen, "rationale": rationale, "cost_usd": ms.get("instance_cost")})
os.makedirs(f"{D}/analysis", exist_ok=True); json.dump(rows, open(f"{D}/analysis/cf_run_metrics.json", "w"), indent=1); print(len(rows), "runs")
