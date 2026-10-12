"""Phase 1 (free, read-only): reproducible effort/accuracy profile of every earlier mini-swe-agent run, per experiment family and
model, so later cue-trust-v3 results can be set beside them descriptively (never pooled into a confirmatory test).
Usage: phase1_retrospective.py -> analysis/phase1_runs.csv, analysis/phase1_summary.json, prints the per-family table.
Effort units are tool calls and characters displayed (not model calls). 'Verification' = a test or Java probe executed.
Claude runs before the PERL5LIB launcher could not execute defects4j test; runs whose outputs show the Perl module error are
marked runner_broken and their verification is not interpreted."""
import json, os, re, glob, csv, statistics as st
SP = "/Users/shawnli/Desktop/Honours/defects4j/supervisor_pipeline_runs"
V3 = "/Users/shawnli/Desktop/Honours/defects4j/.claude/worktrees/strict-depth-experiment-run-524113/supervisor_pipeline_runs/cue-trust-v3"
rows = []
for tp in glob.glob(f"{SP}/**/mini-swe-agent.traj.json", recursive=True):
    if "/_smoke/" in tp or "smoke-" in tp: continue
    rd = os.path.dirname(tp); fam = os.path.relpath(tp, SP).split("/")[0]
    try: t = json.load(open(tp))
    except Exception: continue
    model = (((t.get("info") or {}).get("config") or {}).get("model") or {}).get("model_name") or "?"
    ev = {}
    if os.path.exists(f"{rd}/evaluation.json"):
        try: ev = json.load(open(f"{rd}/evaluation.json"))
        except Exception: ev = {}
    msgs = t.get("messages", []); cmds, outs = [], []
    for m in msgs:
        if m.get("role") == "assistant":
            for tc in m.get("tool_calls") or []:
                try: cmds.append(json.loads((tc.get("function") or {}).get("arguments") or "{}").get("command", ""))
                except Exception: pass
        elif m.get("role") == "tool":
            outs.append(m.get("content") if isinstance(m.get("content"), str) else json.dumps(m.get("content")))
    extra = json.dumps([m.get("extra") for m in msgs])
    allout = "\n".join(outs)
    verif = any(re.search(r"defects4j\s+test|(^|[\s;&|])(java|javac|jshell)\s", re.sub(r"/\S+", "/P", c)) for c in cmds)
    rows.append({"family": fam, "model": model, "run_dir": os.path.relpath(rd, SP), "gold_rank": ev.get("gold_rank"), "acc1": int(ev.get("gold_rank") == 1),
                 "answered": int(ev.get("gold_rank") is not None), "tool_calls": len(cmds), "chars_displayed": len(allout),
                 "reasoning_tokens": sum(int(x) for x in re.findall(r'"reasoning_tokens": (\d+)', extra)),
                 "completion_tokens": sum(int(x) for x in re.findall(r'"completion_tokens": (\d+)', extra)),
                 "verification": int(verif), "runner_broken": int("String/Interpolate.pm" in allout or "Can't locate" in allout),
                 "cost_usd": ((t.get("info") or {}).get("model_stats") or {}).get("instance_cost")})
os.makedirs(f"{V3}/analysis", exist_ok=True)
with open(f"{V3}/analysis/phase1_runs.csv", "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
summ = {}
for r in rows:
    k = (r["family"], r["model"]); summ.setdefault(k, []).append(r)
out = []
for (fam, model), rs in sorted(summ.items()):
    med = lambda f: st.median([x[f] for x in rs])
    out.append({"family": fam, "model": model, "runs": len(rs), "acc1": round(sum(x["acc1"] for x in rs) / len(rs), 3), "answered": sum(x["answered"] for x in rs),
                "median_tool_calls": med("tool_calls"), "median_chars_displayed": med("chars_displayed"), "median_reasoning_tokens": med("reasoning_tokens"),
                "verification_rate": round(sum(x["verification"] for x in rs) / len(rs), 3), "runner_broken_runs": sum(x["runner_broken"] for x in rs)})
json.dump({"generated_from": SP, "runs": len(rows), "by_family_model": out}, open(f"{V3}/analysis/phase1_summary.json", "w"), indent=1)
print(f"{len(rows)} runs")
for o in out: print(f"{o['family'][:34]:34s} {o['model'].split('/')[-1][:24]:24s} n={o['runs']:<4d} Acc@1={o['acc1']:.2f} tools~{o['median_tool_calls']:<5} chars~{int(o['median_chars_displayed']):<7d} reasonTok~{o['median_reasoning_tokens']:<6} verif={o['verification_rate']:.2f} runnerBroken={o['runner_broken_runs']}")
