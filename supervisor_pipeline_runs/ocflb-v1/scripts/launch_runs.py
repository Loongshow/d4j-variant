#!/usr/bin/env python
"""Plan and launch the OCFLB run blocks. Usage:
  launch_runs.py plan                      -> prints the assignment (pairs -> servers) without launching
  launch_runs.py sonnet                    -> starts two Sonnet drivers (sonnetA, sonnetB) over disjoint pair sets, 5 planned runs per arm
  launch_runs.py opus                      -> starts the Opus driver on the pre-registered subset, 3 planned runs per arm
  launch_runs.py topup <server> [cap]      -> relaunch variants on that server until each has 5 (Sonnet) / 3 (Opus) valid attempts, at most `cap` extra per variant
Drivers run one slot per server; each server has its own benchmark_runs root. Logs in diagnostic-*/driver_<server>.log"""
import json, os, sys, subprocess, glob
O = "/Users/shawnli/Desktop/Honours/defects4j/supervisor_pipeline_runs/ocflb-v1"; PY = "/opt/miniconda3/bin/python"
man = json.load(open(f"{O}/BENCHMARK_MANIFEST.json")); pairs = man["pairs"]; ORDER = sorted(pairs, key=lambda k: (pairs[k]["project"], pairs[k]["bug"]))
def variants(pids): return [pairs[p]["arms"][a]["variant_id"] for p in pids for a in ("DEFINER_FAULT", "ADAPTER_FAULT")]
# balanced split by project across the two Sonnet servers: alternate pairs within the ordered list
A = [p for i, p in enumerate(ORDER) if i % 2 == 0]; B = [p for i, p in enumerate(ORDER) if i % 2 == 1]
OPUS = man.get("opus_subset") or []
PLAN = {"sonnetA": (variants(A), 5), "sonnetB": (variants(B), 5), "opusA": (variants(OPUS), 3)}
def launch(server, vids, planned):
    env = dict(os.environ); log = open(f"{O}/diagnostic-{'opus' if server.startswith('opus') else 'sonnet'}/driver_{server}.out", "a")
    p = subprocess.Popen([PY, f"{O}/scripts/ocflb_driver.py", "--model", server, "--variants", ",".join(vids), "--planned", str(planned)], stdout=log, stderr=subprocess.STDOUT, env=env, start_new_session=True)
    open(f"{O}/diagnostic-{'opus' if server.startswith('opus') else 'sonnet'}/driver_{server}.pid", "w").write(str(p.pid)); print(f"launched {server} pid {p.pid}: {len(vids)} variants x {planned}")
cmd = sys.argv[1]
if cmd == "plan":
    for s, (v, n) in PLAN.items(): print(s, n, "per variant:", v)
elif cmd == "sonnet":
    for s in ("sonnetA", "sonnetB"): launch(s, *PLAN[s])
elif cmd == "opus":
    launch("opusA", *PLAN["opusA"])
elif cmd == "topup":
    server = sys.argv[2]; cap = int(sys.argv[3]) if len(sys.argv) > 3 else 4
    subprocess.run([PY, f"{O}/scripts/ocflb_metrics.py"], check=True, capture_output=True); rows = json.load(open(f"{O}/analysis/per_run/run_metrics.json"))
    vids, target = PLAN[server]; todo = []
    for v in vids:
        rs = [r for r in rows if r["server"] == server and r["variant_id"] == v]; valid = sum(1 for r in rs if r["status"] not in ("provider_stall", "provider_error"))
        existing = len(glob.glob(f"{O}/models/{server}/benchmark_runs/mini-swe-claude/{v}/run-*")); need = min(max(target - valid, 0), cap)
        print(f"{v}: existing={existing} valid={valid} extra={need}")
        if need: todo.append((v, existing + need))
    for v, planned in todo: subprocess.run([PY, f"{O}/scripts/ocflb_driver.py", "--model", server, "--variants", v, "--planned", str(planned)])
    print("topup finished for", server)
