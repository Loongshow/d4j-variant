"""Write diagnostic/HALT_EVIDENCE.json: structured facts about the provider-credit halt, taken from the raw smoke and diagnostic run
outputs, which stay on disk only. Raw provider output can carry credential fragments inside traceback locals, so this script copies
counts and fixed fields only, never free text.
Usage: halt_evidence.py"""
import json, os, re, glob
import ct_lib as C
CREDIT = "credit balance is too low"
def rj(p):
    try: return json.load(open(p))
    except Exception: return {}
def facts(run_dir, traj_name, extra):
    raw_p = os.path.join(run_dir, "raw_agent_output.txt"); raw = open(raw_p, errors="replace").read() if os.path.exists(raw_p) else ""
    t = rj(os.path.join(run_dir, traj_name)); info = t.get("info") or {}; ms = info.get("model_stats") or {}
    return {"run": os.path.relpath(run_dir, C.V3), **extra,
            "model": ((info.get("config") or {}).get("model") or {}).get("model_name"), "agent_exit_status": info.get("exit_status"),
            "api_calls": ms.get("api_calls"), "cost_usd": ms.get("instance_cost"),
            "retry_waits_seconds": [int(x) for x in re.findall(r"Retrying <unknown> in (\d+) seconds", raw)],
            "credit_message_occurrences": raw.count(CREDIT)}
out = []
for sd in sorted(glob.glob(f"{C.V3}/models/*/benchmark_runs/_smoke/mini-swe-agent/smoke-*")):
    out.append(facts(sd, "mini-swe-agent-smoke.traj.json", {"kind": "health-gate smoke probe", "smoke_status": rj(f"{sd}/smoke_result.json").get("status")}))
for rd in sorted(glob.glob(f"{C.V3}/models/*/benchmark_runs/mini-swe-claude/CTV-*/run-*")):
    m = rj(f"{rd}/run_manifest.json")
    out.append(facts(rd, "mini-swe-agent.traj.json", {"kind": "diagnostic benchmark run", "run_status": m.get("status"), "started_at": m.get("started_at")}))
json.dump({"note": "Extracted counts and fixed fields only; the raw outputs are not published.", "sources": out},
          open(f"{C.V3}/diagnostic/HALT_EVIDENCE.json", "w"), indent=1)
for o in out: print(o["run"].split("/")[-1], o.get("smoke_status") or o.get("run_status"), o["model"], o["agent_exit_status"], "retries", len(o["retry_waits_seconds"]), "credit_msgs", o["credit_message_occurrences"], "cost", o["cost_usd"])
