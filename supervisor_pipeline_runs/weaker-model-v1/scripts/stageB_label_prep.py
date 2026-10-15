"""Prepare blind-labelling inputs for Stage B misses: safe trajectory views + per-run task files.
Usage: stageB_label_prep.py <tag> <instance-prefix> [--server w55]   e.g. stageB_label_prep.py block2 SB-B4
Reads analysis/per_run.json (run mx_metrics.py first); writes analysis/traj_views/<vid>/<run>.txt,
analysis/failure_modes/wrong_runs_stageB_<tag>.json and analysis/failure_modes/tasks_<tag>/<vid>_<run>.json."""
import json, os, sys, subprocess
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ct_lib as C
WM = C.V3; tag, prefix = sys.argv[1], sys.argv[2]; server = sys.argv[sys.argv.index("--server") + 1] if "--server" in sys.argv else "w55"
agent = json.load(open(f"{WM}/models/servers.json"))[server]["agent_id"]; K = json.load(open(f"{WM}/review/VARIANT_KEY.json"))
rows = [r for r in json.load(open(f"{WM}/analysis/per_run.json")) if r.get("tier") == "STAGE_B" and r.get("included") and r.get("server") == server and r["instance_id"].startswith(prefix)]
misses = [r for r in rows if not r.get("acc1")]; out = []; os.makedirs(f"{WM}/analysis/failure_modes/tasks_{tag}", exist_ok=True)
for r in misses:
    vid, run = r["variant_id"], r["run"]; rd = f"{WM}/models/{server}/benchmark_runs/{agent}/{vid}/{run}"
    # gpt-5.5 (w55) views keep their original path; any other server gets a neutral separate directory (same variant/run names would collide)
    vdir = "traj_views" if server == "w55" else "traj_views_set2"
    view = f"{WM}/analysis/{vdir}/{vid}/{run}.txt"; os.makedirs(os.path.dirname(view), exist_ok=True)
    p = subprocess.run([sys.executable, f"{WM}/scripts/mx_traj_view.py", rd, "--max", "1500"], capture_output=True, text=True); open(view, "w").write(p.stdout)
    w = {"run_id": f"{vid}/{run}", "instance_id": r["instance_id"], "project": r["project"], "gold_rank": r["gold_rank"], "rank1": r.get("rank1"), "rank1_category": r.get("rank1_category"),
         "gold_exposed": r.get("gold_exposed"), "full_gold_read": r.get("full_gold_read"), "evidence_displayed": r.get("evidence_displayed"), "tool_calls": r.get("tool_calls"), "view": view, "view_chars": len(p.stdout)}
    out.append(w); k = K[vid]
    task = {"run_id": w["run_id"], "project": r["project"], "trigger": k["trigger"], "expected_signature": k["expected_signature"], "gold": k["gold"], "decoys": k["decoys"], "entry_points": k["entry_points"],
            "evidence": k["evidence"], "fault_lines": k["fault_lines"], "safe_view": view, "variant_patch": f"{WM}/new_bug_variants/{k['project']}/bug-1/L20/{vid}/variant.patch",
            "frozen_measures": {kk: w[kk] for kk in ("gold_rank", "rank1", "gold_exposed", "full_gold_read", "evidence_displayed", "tool_calls")}}
    json.dump(task, open(f"{WM}/analysis/failure_modes/tasks_{tag}/{vid}_{run}.json", "w"), indent=1)
json.dump(out, open(f"{WM}/analysis/failure_modes/wrong_runs_stageB_{tag}.json", "w"), indent=1)
for w in out: print(w["run_id"], w["instance_id"], "rank", w["gold_rank"], "rank1", (w["rank1"] or "?").split("::")[-1], "exposed", w["gold_exposed"], "fullread", w["full_gold_read"])
print(len(rows), "runs,", len(misses), "misses; tasks in analysis/failure_modes/tasks_" + tag)
