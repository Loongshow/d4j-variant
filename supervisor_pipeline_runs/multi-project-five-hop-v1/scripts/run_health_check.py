"""Per-run post-launch health check (observable artifacts only). Usage: run_health_check.py <run_dir>
Prints: harness status, gold rank, tool/model calls, wall clock, start-to-first-response, largest inter-response gap, whether the last
assistant message was the submission (i.e. the final provider request returned), provider retry/error lines in raw output, source integrity."""
import json, os, sys, datetime
R = sys.argv[1].rstrip("/")
def rj(p):
    try: return json.load(open(p))
    except Exception: return {}
man = rj(os.path.join(R, "run_manifest.json")); ev = rj(os.path.join(R, "evaluation.json")); si = rj(os.path.join(R, "source_integrity.json"))
traj = rj(os.path.join(R, "mini-swe-agent.traj.json")); msgs = traj.get("messages", [])
ts = [m.get("extra", {}).get("timestamp") for m in msgs if m.get("role") == "assistant"]; ts = [t for t in ts if isinstance(t, (int, float))]
st = None
try: st = datetime.datetime.fromisoformat(man["started_at"].replace("Z", "+00:00")).timestamp()
except Exception: pass
end = os.path.getmtime(os.path.join(R, "evaluation.json")) if os.path.exists(os.path.join(R, "evaluation.json")) else None
gaps = [round(b - a) for a, b in zip(ts, ts[1:])]
last = next((m for m in reversed(msgs) if m.get("role") == "assistant"), {})
last_tools = [(tc.get("function") or {}).get("name") for tc in (last.get("tool_calls") or [])]
raw = open(os.path.join(R, "raw_agent_output.txt"), errors="replace").read() if os.path.exists(os.path.join(R, "raw_agent_output.txt")) else ""
tc = sum(1 for m in msgs if m.get("role") == "assistant" for t in (m.get("tool_calls") or []) if (t.get("function") or {}).get("name") == "bash")
out = {"run": "/".join(R.split("/")[-2:]), "status": man.get("status"), "status_reason": (man.get("status_reason") or "")[:100], "gold_rank": ev.get("gold_rank"), "tool_calls": tc, "model_responses": len(ts),
       "wall_clock_s": round(end - st) if (end and st) else None, "start_to_first_response_s": round(ts[0] - st) if (ts and st) else None, "max_inter_response_gap_s": max(gaps) if gaps else None,
       "final_request_returned_with_submission": "submit_fault_localization" in last_tools, "retry_lines": raw.count("Retrying"), "provider_error_lines": sum(1 for l in raw.splitlines() if "Error" in l and ("litellm" in l or "OpenAI" in l or "APIConnection" in l or "Timeout" in l)),
       "source_integrity_ok": si.get("ok", si.get("production_and_test_source_unchanged")), "cost_usd": ((traj.get("info") or {}).get("model_stats") or {}).get("cost")}
out["verdict"] = "normal completion" if (out["status"] == "completed" and out["final_request_returned_with_submission"] and (out["wall_clock_s"] or 0) <= 300 and (out["max_inter_response_gap_s"] or 0) <= 60 and (out["start_to_first_response_s"] or 0) <= 60) else ("completed but stalled/over budget (see fields)" if out["status"] == "completed" else f"{out['status']} (provider stall/harness event)")
print(json.dumps(out, indent=1))
