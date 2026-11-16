#!/usr/bin/env python
"""Independent re-derivation of the execution facts from RAW run artifacts + the frozen manifest only (never from run_metrics.json),
then a comparison against results/ocflb_results.json and analysis/per_run/run_metrics.json. Writes results/VERIFICATION.md + .json.
Checks: installed package hashes == frozen; every run's variant is frozen; model id / budget / prompt hash per run; gold of every run ==
frozen gold; ranking.json gold rank == evaluation.json gold rank; run counts per variant/server; stall classification recount (uniform rule);
cost sums; stated Acc@1/MRR per variant recomputed from raw evaluation.json."""
import json, glob, os, hashlib, re, datetime, collections, sys
O = "/Users/shawnli/Desktop/Honours/defects4j/supervisor_pipeline_runs/ocflb-level-b-v1"; h = lambda p: hashlib.sha256(open(p, "rb").read()).hexdigest()
def rj(p):
    try: return json.load(open(p))
    except Exception: return {}
man = rj(f"{O}/BENCHMARK_MANIFEST.json"); problems = []; facts = {"runs": [], "per_variant": {}, "per_server": {}}
frozen = {}
for pid, P in man["pairs"].items():
    for arm, A in P["arms"].items():
        d = f"{O}/new_bug_variants/{P['project']}/bug-1/L20/{A['variant_id']}"
        for f, hv in A["hashes"].items():
            if not os.path.exists(f"{d}/{f}"): problems.append(f"missing installed file {A['variant_id']}/{f}")
            elif h(f"{d}/{f}") != hv: problems.append(f"HASH MISMATCH {A['variant_id']}/{f}")
        frozen[A["variant_id"]] = {"gold": A["gold"], "pair": pid, "arm": arm}
PROTO = man["protocol"]; SERVERS = {"sonnetA": "claude-sonnet-4-6", "sonnetB": "claude-sonnet-4-6", "opusA": "claude-opus-5-5"}
for srv, mid in SERVERS.items():
    for rd in sorted(glob.glob(f"{O}/models/{srv}/benchmark_runs/mini-swe-claude/*/run-*")):
        V = rd.split("/")[-2]; run = os.path.basename(rd); m = rj(f"{rd}/run_manifest.json"); ev = rj(f"{rd}/evaluation.json"); rk = rj(f"{rd}/ranking.json"); traj = rj(f"{rd}/mini-swe-agent.traj.json")
        if not m: problems.append(f"{srv}/{V}/{run}: no run_manifest"); continue
        if V not in frozen: problems.append(f"{srv}/{V}/{run}: variant not frozen")
        ag = m.get("agent") or {}; bd = m.get("budget") or {}; pr = m.get("prompt") or {}
        if ag.get("model") != mid: problems.append(f"{srv}/{V}/{run}: model {ag.get('model')} != {mid}")
        if (bd.get("max_tool_calls"), bd.get("max_test_runs"), bd.get("timeout_seconds")) != (PROTO["max_tool_calls"], PROTO["max_test_runs"], PROTO["timeout_seconds"]): problems.append(f"{srv}/{V}/{run}: budget {bd}")
        if pr.get("base_prompt_sha256") and pr.get("base_prompt_sha256") != PROTO["base_prompt_sha256"]: problems.append(f"{srv}/{V}/{run}: prompt hash differs")
        # gold identity: the run's gold (evaluation.json / manifest) must equal the frozen gold
        fg = frozen.get(V, {}).get("gold", ""); fcls, fm = fg.split("#")[0], fg.split("#")[-1]
        gms = ev.get("gold_methods") or []
        if m.get("status") == "completed" and not gms: problems.append(f"{srv}/{V}/{run}: evaluation.json carries no gold_methods")
        if gms and not any(g.get("class") == fcls and g.get("method") == fm for g in gms): problems.append(f"{srv}/{V}/{run}: evaluated gold {gms} != frozen {fg}")
        # ranking vs evaluation: recompute the gold rank from the submitted predictions (fully qualified class + method, as the harness evaluates)
        preds = ((rk.get("structured_submission") or {}).get("predictions") or rk.get("predictions") or [])
        rr = next((i + 1 for i, p in enumerate(preds) if p.get("class") == fcls and p.get("method") == fm), None)
        if m.get("status") == "completed" and preds and rr != ev.get("gold_rank"): problems.append(f"{srv}/{V}/{run}: recomputed gold rank {rr} != evaluation {ev.get('gold_rank')}")
        # stall recount (uniform rule; command count = completed steps, as in ocflb_metrics.py)
        ms = (traj.get("info") or {}).get("model_stats") or {}; msgs = traj.get("messages") or []
        ncmd = min(sum(len(((x.get("extra") or {}).get("actions") or [])) for x in msgs if x.get("role") == "assistant"), sum(1 for x in msgs if x.get("role") == "tool"))
        st = m.get("status"); stall = st == "timeout" and (ms.get("api_calls") or 0) <= 2 and ncmd <= 2; gap = None
        if st == "timeout":
            try:
                t0 = datetime.datetime.fromisoformat(re.search(r"execution_timer_started_at: (\S+)", open(f"{rd}/commands.log").read()).group(1).replace("Z", "+00:00")).timestamp()
                evs = [(x["role"], float(x["extra"]["timestamp"])) for x in msgs if x.get("role") in ("assistant", "tool") and (x.get("extra") or {}).get("timestamp") is not None]
                if evs: gap = round(t0 + 300 - evs[-1][1], 1); stall = stall or (evs[-1][0] == "tool" and gap > 60)
            except Exception: pass
        status = "provider_stall" if stall else st
        if st == "provider_error":
            raw = open(f"{rd}/raw_agent_output.txt", errors="replace").read() if os.path.exists(f"{rd}/raw_agent_output.txt") else ""
            if "prompt is too long" in raw or "ContextWindowExceededError" in raw: status = "context_overflow"
        facts["runs"].append({"server": srv, "variant": V, "run": run, "harness_status": st, "status": status, "valid": status in ("completed", "timeout", "invalid_ranking", "context_overflow"), "gold_rank": ev.get("gold_rank") if st == "completed" else None, "cost": ms.get("instance_cost"), "api_calls": ms.get("api_calls"), "model": ag.get("model"), "final_gap_s": gap, "started_at": m.get("started_at")})
for r in facts["runs"]:
    facts["per_variant"].setdefault(r["variant"], []).append(r); facts["per_server"].setdefault(r["server"], []).append(r)
summary = {}
for V, rs in sorted(facts["per_variant"].items()):
    valid = [r for r in rs if r["valid"]]; ans = [r for r in valid if r["harness_status"] == "completed"]
    summary[V] = {"attempted": len(rs), "valid": len(valid), "answered": len(ans), "stalls": sum(1 for r in rs if r["status"] == "provider_stall"), "acc1": round(sum(1 for r in ans if r["gold_rank"] == 1) / len(valid), 3) if valid else None,
                  "mrr": round(sum((1 / r["gold_rank"]) for r in ans if r["gold_rank"]) / len(valid), 3) if valid else None, "ranks": [r["gold_rank"] for r in ans], "cost": round(sum(r["cost"] or 0 for r in rs), 4), "models": sorted({r["model"] for r in rs})}
# compare against the pipeline's numbers
rm = rj(f"{O}/analysis/per_run/run_metrics.json") or []; res = rj(f"{O}/results/ocflb_results.json") or {}
by = collections.defaultdict(list); [by[r["variant_id"]].append(r) for r in rm]
cmp_problems = []
for V, sm in summary.items():
    pr = by.get(V, []); pv = [r for r in pr if r.get("valid", r["status"] in ("completed", "timeout", "invalid_ranking", "context_overflow"))]
    pipe = {"attempted": len(pr), "valid": len(pv), "stalls": sum(1 for r in pr if r["status"] == "provider_stall"), "acc1": round(sum(r["acc_at_1"] for r in pv) / len(pv), 3) if pv else None, "mrr": round(sum(r["mrr"] for r in pv) / len(pv), 3) if pv else None, "cost": round(sum(r["cost_usd"] or 0 for r in pr), 4)}
    for k in pipe:
        a, b = pipe[k], sm[k]
        if isinstance(a, float) and isinstance(b, float):
            if abs(a - b) > 0.002: cmp_problems.append(f"{V}: {k} raw={b} pipeline={a}")
        elif a != b: cmp_problems.append(f"{V}: {k} raw={b} pipeline={a}")
# planned coverage (reported; a shortfall is a problem only with --expect-complete)
EXPECT = {}
for pid, P in man["pairs"].items():
    for arm, A in P["arms"].items(): EXPECT[A["variant_id"]] = {"sonnet": 5, "opus": 3 if pid in (man.get("opus_subset") or []) else 0}
coverage = {}
for V, e in EXPECT.items():
    rs = facts["per_variant"].get(V, []); sv = sum(1 for r in rs if r["server"].startswith("sonnet") and r["valid"]); ov = sum(1 for r in rs if r["server"].startswith("opus") and r["valid"])
    coverage[V] = {"sonnet_valid": sv, "sonnet_planned": e["sonnet"], "opus_valid": ov, "opus_planned": e["opus"]}
    if "--expect-complete" in sys.argv and (sv < e["sonnet"] or ov < e["opus"]): cmp_problems.append(f"{V}: coverage sonnet {sv}/{e['sonnet']} opus {ov}/{e['opus']}")
# manifest self-hash and freeze-before-run ordering
body = json.dumps({k: v for k, v in man.items() if k != "sha256_of_this_manifest_excluding_itself"}, sort_keys=True).encode()
if hashlib.sha256(body).hexdigest() != man.get("sha256_of_this_manifest_excluding_itself"): problems.append("BENCHMARK_MANIFEST.json self-hash does not match its content")
starts = sorted(r["started_at"] for r in facts["runs"] if r.get("started_at"))
if starts and starts[0] < man["frozen_at"]: problems.append(f"earliest run {starts[0]} precedes the freeze {man['frozen_at']}")
if len(rm) != len(facts["runs"]): cmp_problems.append(f"run count raw={len(facts['runs'])} pipeline={len(rm)}")
# per (variant, model) comparison against the pipeline's per-model aggregates
MODEL_OF = {"sonnetA": "sonnet", "sonnetB": "sonnet", "opusA": "opus"}
for V in summary:
    for model in ("sonnet", "opus"):
        raw = [r for r in facts["per_variant"][V] if MODEL_OF[r["server"]] == model]; rv = [r for r in raw if r["valid"]]; ra = [r for r in rv if r["harness_status"] == "completed"]
        pp = [r for r in by.get(V, []) if r["model"] == model]; pv = [r for r in pp if r.get("valid", r["status"] in ("completed", "timeout", "invalid_ranking", "context_overflow"))]
        for k, a, b in (("attempted", len(raw), len(pp)), ("valid", len(rv), len(pv)), ("acc1", round(sum(1 for r in ra if r["gold_rank"] == 1) / len(rv), 3) if rv else None, round(sum(r["acc_at_1"] for r in pv) / len(pv), 3) if pv else None)):
            if a != b and not (isinstance(a, float) and isinstance(b, float) and abs(a - b) <= 0.002): cmp_problems.append(f"{V}/{model}: {k} raw={a} pipeline={b}")
tot_cost_raw = round(sum(r["cost"] or 0 for r in facts["runs"]), 2); tot_cost_pipe = round(sum(r["cost_usd"] or 0 for r in rm), 2)
out = {"checked_at": datetime.datetime.now(datetime.timezone.utc).isoformat(), "frozen_variants": len(frozen), "runs_raw": len(facts["runs"]), "runs_pipeline": len(rm), "total_cost_raw": tot_cost_raw, "total_cost_pipeline": tot_cost_pipe, "coverage": coverage, "earliest_run_started_at": starts[0] if starts else None, "frozen_at": man["frozen_at"],
       "per_server": {s: {"attempted": len(rs), "completed": sum(1 for r in rs if r["harness_status"] == "completed"), "stalls": sum(1 for r in rs if r["status"] == "provider_stall"), "models": sorted({r["model"] for r in rs})} for s, rs in facts["per_server"].items()},
       "per_variant": summary, "artifact_problems": problems, "comparison_problems": cmp_problems, "verdict": ("NO_RUNS" if not facts["runs"] else "PASS") if not problems and not cmp_problems else "FAIL"}
json.dump(out, open(f"{O}/results/VERIFICATION.json", "w"), indent=1)
M = [f"# Independent verification ({out['checked_at']})", "", f"Re-derived from raw run artifacts and the frozen manifest only. Verdict: **{out['verdict']}**.", "", f"- frozen variants: {len(frozen)}; installed package hashes equal the manifest: {'yes' if not any('HASH' in p for p in problems) else 'NO'}", f"- runs (raw / pipeline): {len(facts['runs'])} / {len(rm)}; total cost USD (raw / pipeline): {tot_cost_raw} / {tot_cost_pipe}", "",
     "| Server | Attempted | Completed | Provider stalls | Model ids seen |", "|---|---|---|---|---|"] + [f"| {s} | {d['attempted']} | {d['completed']} | {d['stalls']} | {d['models']} |" for s, d in out["per_server"].items()]
M += ["", "| Variant | Attempted | Valid | Answered | Stalls | Acc@1 (raw) | MRR (raw) | Gold ranks | Cost | Models |", "|" + "---|" * 10] + [f"| `{V}` | {d['attempted']} | {d['valid']} | {d['answered']} | {d['stalls']} | {d['acc1']} | {d['mrr']} | {d['ranks']} | {d['cost']} | {d['models']} |" for V, d in summary.items()]
M += ["", "## Planned coverage (valid attempts / planned)", "", "| Variant | Sonnet | Opus |", "|---|---|---|"] + [f"| `{V}` | {c['sonnet_valid']}/{c['sonnet_planned']} | {c['opus_valid']}/{c['opus_planned']} |" for V, c in coverage.items()]
M += ["", f"Freeze {man['frozen_at']}; earliest run started {starts[0] if starts else 'n/a'}; manifest self-hash verified: {'yes' if not any('self-hash' in p for p in problems) else 'NO'}.", "", "## Artifact problems", ""] + ([f"- {p}" for p in problems] or ["none"]) + ["", "## Raw-vs-pipeline disagreements", ""] + ([f"- {p}" for p in cmp_problems] or ["none"])
open(f"{O}/results/VERIFICATION.md", "w").write("\n".join(M) + "\n"); print("verification:", out["verdict"], "runs", len(facts["runs"]), "problems", len(problems), "disagreements", len(cmp_problems))
