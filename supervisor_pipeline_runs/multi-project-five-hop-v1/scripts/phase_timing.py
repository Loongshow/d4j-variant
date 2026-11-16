"""Per-run phase timing from artifacts only: harness preparation (started_at -> prompt.json), agent phase (execution_timer_started_at ->
first model response; process duration_ms; timed_out flag), response count, retry lines. Usage: phase_timing.py <runs_root> <out.json> <out.md> TARGET[:a-b] ..."""
import json, os, glob, datetime, re, sys
RUNS, OUTJ, OUTM = sys.argv[1], sys.argv[2], sys.argv[3]
def iso(s): return datetime.datetime.fromisoformat(s.replace("Z", "+00:00")).timestamp()
rows = []
for spec in sys.argv[4:]:
    V, _, rng = spec.partition(":"); lo, hi = (1, 999)
    if rng: lo, hi = [int(x) for x in rng.split("-")]
    for rd in sorted(glob.glob(os.path.join(RUNS, V, "run-*"))):
        n = int(os.path.basename(rd).split("-")[-1])
        if not (lo <= n <= hi): continue
        try: m = json.load(open(rd + "/run_manifest.json")); st = iso(m["started_at"]); status = m.get("status")
        except Exception: st = os.path.getmtime(rd); status = "(in progress)"
        p = rd + "/prompt.json"; prep = round(os.path.getmtime(p) - st) if os.path.exists(p) else None
        cl = open(rd + "/commands.log").read() if os.path.exists(rd + "/commands.log") else ""
        ag = re.search(r"execution_timer_started_at: (\S+)", cl); dur = re.search(r"duration_ms: (\d+)", cl); to = "timed_out: true" in cl
        try: t = json.load(open(rd + "/mini-swe-agent.traj.json")); ts = [x.get("extra", {}).get("timestamp") for x in t.get("messages", []) if x.get("role") == "assistant"]; ts = [x for x in ts if x]
        except Exception: ts = []
        raw = open(rd + "/raw_agent_output.txt", errors="replace").read() if os.path.exists(rd + "/raw_agent_output.txt") else ""
        first = round(ts[0] - iso(ag.group(1))) if (ts and ag) else None; gaps = [round(b - a) for a, b in zip(ts, ts[1:])]
        ev = rd + "/evaluation.json"; wall = round(os.path.getmtime(ev) - st) if os.path.exists(ev) else None
        kind = ("none" if status == "completed" and (first or 0) <= 60 and max(gaps or [0]) <= 60 else
                "slow first model response, completed" if status == "completed" and (first or 0) > 60 else
                "slow mid-run response, completed" if status == "completed" else
                "startup_timeout (adapter init)" if status == "startup_timeout" else
                "unreturned model request -> harness timeout" if status == "timeout" else status)
        rows.append({"run": f"{V}/run-{n:03d}", "status": status, "preparation_s": prep, "preparation_stalled": bool(prep and prep > 60), "agent_to_first_response_s": first, "max_gap_s": max(gaps) if gaps else None,
                     "agent_process_s": round(int(dur.group(1)) / 1000) if dur else None, "harness_timed_out": to, "responses": len(ts), "retry_lines": raw.count("Retrying"), "dns_error_lines": raw.count("nodename nor servname"), "wall_clock_s": wall, "agent_phase_kind": kind})
json.dump(rows, open(OUTJ, "w"), indent=1)
md = ["| Run | Status | Preparation s (harness, before the agent) | Agent → first response s | Max gap s | Agent process s | Harness timed_out | Responses | litellm retries | DNS error lines | Wall clock s | Agent-phase classification |", "|---|---|---|---|---|---|---|---|---|---|---|---|"]
for r in rows: md.append("| " + " | ".join(str(r[k]) if r[k] is not None else "-" for k in ("run", "status", "preparation_s", "agent_to_first_response_s", "max_gap_s", "agent_process_s", "harness_timed_out", "responses", "retry_lines", "dns_error_lines", "wall_clock_s", "agent_phase_kind")) + " |")
open(OUTM, "w").write("\n".join(md) + "\n"); print("\n".join(md))
