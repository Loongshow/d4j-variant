#!/usr/bin/env python
"""Per-run metrics + mechanical failure taxonomy for every adversarial run of every model.
Reads attack.json (gold, roles, candidates, chain) and run artifacts only (never reasoning traces).
Usage: attack_run_metrics.py <out.json>"""
import glob, json, os, re, sys, itertools
R = "/Users/shawnli/Desktop/Honours/defects4j/supervisor_pipeline_runs/adversarial-break-v1"
MODELS = {"opus55": "claude-opus-5-5", "sonnet46": "claude-sonnet-4-6", "haiku45": "claude-haiku-4-5-20251001", "opus55t": "claude-opus-5-5", "sonnet46t": "claude-sonnet-4-6"}
PROTOCOL = {"opus55t": "v2+runner", "sonnet46t": "v2+runner"}   # servers started with PERL5LIB so defects4j test executes; all other servers: v2 (no executable test)
out_path = sys.argv[1] if len(sys.argv) > 1 else f"{R}/analysis/per_run/attack_run_metrics.json"
DECL = re.compile(r"^\s*(?:public|protected|private)?\s*(?:static\s+|final\s+|synchronized\s+|abstract\s+)*[\w.$<>\[\],?]+\s+([A-Za-z_$][\w$]*)\s*\([^;{)]*\)\s*(?:throws [\w.,\s]+)?\s*\{?\s*$")
SEARCH = re.compile(r"\b(grep|rg|ack|ag)\b"); REPO_WIDE = re.compile(r"-r\b|-R\b|--include|\bsrc/main\b|\bsrc\b\s*$|\*\*|-l\b.*\bsrc\b")
READ = re.compile(r"\b(?:cat|sed|head|tail|awk|nl|less|more)\b[^|;]*\.java")

def rj(p):
    try: return json.load(open(p))
    except Exception: return {}
def strip_cd(c):
    m = re.match(r"^cd\s+\S+\s*(?:&&|;)\s*(.*)$", c.strip(), re.S); return m.group(1).strip() if m else c.strip()
def steps_of(traj):
    cmds, outs = [], []
    for m in traj.get("messages") or []:
        if m.get("role") == "assistant":
            for a in ((m.get("extra") or {}).get("actions") or []):
                if a.get("command"): cmds.append(a["command"])
                elif a.get("tool"): cmds.append("TOOL:" + str(a.get("tool")))
        elif m.get("role") == "tool": outs.append(str(m.get("content") or ""))
    return [(i + 1, cmds[i], outs[i]) for i in range(min(len(cmds), len(outs)))]
def tau(a, b):
    if len(a) < 3: return None
    c = d = 0
    for i, j in itertools.combinations(range(len(a)), 2):
        s = (a[i] - a[j]) * (b[i] - b[j]); c += s > 0; d += s < 0
    return (c - d) / (len(a) * (len(a) - 1) / 2)

rows = []
for aj in sorted(glob.glob(f"{R}/construction/packages/*/attack.json")):
    cfg = rj(aj); V = cfg["variant_id"]; G = cfg["gold"]
    if not os.path.exists(f"{R}/new_bug_variants/{cfg['project']}/bug-1/L20/{V}"): continue
    gold_key = f"{G['class'].split('.')[-1]}::{G['method']}"; gold_fq = f"{G['class']}::{G['method']}"
    roles = {k.replace("#", "::"): v for k, v in (cfg.get("roles") or {}).items()}          # FQCN::method -> role
    roles_simple = {k.split("::")[0].split(".")[-1] + "::" + k.split("::")[1]: v for k, v in roles.items()}
    chain = cfg.get("chain") or []                                                            # [{"tag","class","method","decl"}]
    labels = {f"{h['class'].split('.')[-1]}::{h['method']}": h["tag"] for h in chain}
    depth_order = [h["tag"] for h in chain][::-1]                                            # deepest first
    for name, mid in MODELS.items():
        for rd in sorted(glob.glob(f"{R}/models/{name}/benchmark_runs/mini-swe-claude/{V}/run-*")):
            man = rj(f"{rd}/run_manifest.json"); traj = rj(f"{rd}/mini-swe-agent.traj.json"); ev = rj(f"{rd}/evaluation.json"); rk = rj(f"{rd}/ranking.json")
            if not man: continue
            steps = steps_of(traj)
            preds = ((rk.get("structured_submission") or {}).get("predictions") or rk.get("predictions") or [])
            top = [f"{(p.get('class') or '').split('.')[-1]}::{p.get('method')}" for p in preds[:10]]
            gold_rank = ev.get("gold_rank")
            gold_step = next((i for i, c, o in steps if (G["decl"] in o) or (G["bug_line"].strip() in o)), None)
            reads = searches = repo = tests = 0; direct_gold = None
            for i, c, o in steps:
                cc = strip_cd(c)
                if READ.search(cc): reads += 1
                if SEARCH.search(cc):
                    searches += 1
                    if REPO_WIDE.search(cc): repo += 1
                    if direct_gold is None and re.search(r"\b%s\b" % re.escape(G["method"]), cc): direct_gold = i
                if "defects4j test" in cc: tests += 1
            # rejected structured submissions (schema-valid payload refused by the harness, e.g. a filler method that does not exist)
            rejected, rej_gold = 0, None
            for m_i, m in enumerate(traj.get("messages") or []):
                if m.get("role") != "assistant": continue
                for a in ((m.get("extra") or {}).get("actions") or []):
                    if a.get("tool") == "submit_fault_localization" and m_i + 1 < len(traj["messages"]):
                        res = str((traj["messages"][m_i + 1].get("extra") or {}).get("raw_output") or traj["messages"][m_i + 1].get("content") or "")
                        if '"ok": false' in res:
                            rejected += 1
                            pl = [f"{str(q.get('class')).split('.')[-1]}::{q.get('method')}" for q in (a.get("predictions") or [])]
                            rej_gold = pl.index(gold_key) + 1 if gold_key in pl else None
            alltext = "\n".join(o for _, _, o in steps)
            decls_seen = {m.group(1) for line in alltext.split("\n") for m in [DECL.match(line)] if m}
            ms = (traj.get("info") or {}).get("model_stats") or {}
            rank1 = top[0] if top else None
            r1role = roles_simple.get(rank1) or ("gold" if rank1 == gold_key else ("chain:" + labels[rank1] if rank1 in labels else "other"))
            order = [t for t in top if t in labels]; pos = {labels[t]: k for k, t in enumerate(order)}
            common = [t for t in depth_order if t in pos]; t_ = tau([pos[x] for x in common], [depth_order.index(x) for x in common]) if len(common) >= 3 else None
            # mechanical taxonomy (pre-registered from the attack's declared roles)
            st_ = man.get("status")
            stall = st_ == "timeout" and (ms.get("api_calls") or 0) <= 2 and len(steps) <= 2   # rule 1: <=2 model calls in 300 s: the provider hung, the agent never worked
            final_gap, last_role = None, None
            if st_ == "timeout":                                                                  # rule 2: the last recorded event is a tool result and the next model reply never came for > 60 s
                try:
                    import re as _re
                    cl = open(f"{rd}/commands.log").read(); t0 = _re.search(r"execution_timer_started_at: (\S+)", cl).group(1)
                    t0 = __import__("datetime").datetime.fromisoformat(t0.replace("Z", "+00:00")).timestamp()
                    ev = [(m["role"], float(m["extra"]["timestamp"])) for m in (traj.get("messages") or []) if m.get("role") in ("assistant", "tool") and (m.get("extra") or {}).get("timestamp") is not None]
                    if ev: last_role = ev[-1][0]; final_gap = round(t0 + 300 - ev[-1][1], 1)
                except Exception: pass
                if last_role == "tool" and final_gap is not None and final_gap > 60: stall = True
            if stall: st_ = "provider_stall"
            if st_ == "provider_error":                                                            # rule 3: the API refused a request the agent itself made too large -> agent failure, not infrastructure
                try: raw = open(f"{rd}/raw_agent_output.txt", errors="replace").read()
                except Exception: raw = ""
                if "prompt is too long" in raw or "ContextWindowExceededError" in raw: st_ = "context_overflow"
            if st_ == "provider_error": tax = "INFRASTRUCTURE"
            elif st_ == "context_overflow": tax = "CONTEXT_LOSS"
            elif st_ == "provider_stall": tax = "INFRASTRUCTURE"
            elif st_ == "timeout": tax = "NO_VALID_RANKING_TIMEOUT"          # agent still working at 300 s: exhaustion, not a stall
            elif st_ == "invalid_ranking": tax = "NO_VALID_RANKING_BUDGET"    # 50 tool calls used without a schema-valid submission
            elif st_ != "completed": tax = "INFRASTRUCTURE"
            elif gold_rank == 1: tax = "CORRECT"
            elif gold_step is None: tax = "DISCOVERY_FAILURE"
            elif gold_rank is None: tax = "CANDIDATE_OVERLOAD" if len(preds) >= 10 else "SEARCH_DIVERSION"
            else:
                tax = {"decoy-lexical": "LEXICAL_MISATTRIBUTION", "deeper-stage": "DEPTH_PRIOR", "shallower-stage": "OWNERSHIP_MISATTRIBUTION",
                       "producer": "OWNERSHIP_MISATTRIBUTION", "consumer": "OWNERSHIP_MISATTRIBUTION", "validator": "OWNERSHIP_MISATTRIBUTION", "transformer": "OWNERSHIP_MISATTRIBUTION",
                       "facade": "OWNERSHIP_MISATTRIBUTION", "sibling": "CANDIDATE_OVERLOAD", "implementation-sibling": "CANDIDATE_OVERLOAD",
                       "registry": "SEARCH_DIVERSION", "writer": "OWNERSHIP_MISATTRIBUTION", "reader": "OWNERSHIP_MISATTRIBUTION"}.get(r1role.split(":")[0], None)
                if tax is None: tax = "DEPTH_PRIOR" if (rank1 in labels and depth_order.index(labels[rank1]) < depth_order.index(labels.get(gold_key, "")) if gold_key in labels else False) else "OTHER"
            rows.append({"attack": cfg.get("attack_id"), "variant_id": V, "model": name, "model_id": mid, "protocol": PROTOCOL.get(name, "v2"), "run": os.path.basename(rd), "status": st_, "harness_status": man.get("status"), "final_gap_s": final_gap, "last_event_role": last_role,
                         "gold": gold_fq, "gold_rank": gold_rank, "acc_at_1": gold_rank == 1, "acc_at_3": bool(gold_rank and gold_rank <= 3), "acc_at_5": bool(gold_rank and gold_rank <= 5),
                         "acc_at_10": bool(gold_rank and gold_rank <= 10), "mrr": round(1.0 / gold_rank, 4) if gold_rank else 0.0,
                         "submitted_top10": top, "n_predictions": len(preds), "rank1": rank1, "rank1_role": r1role,
                         "gold_in_top10": gold_key in top, "answered": st_ == "completed", "agent_exhausted": st_ in ("timeout", "invalid_ranking", "context_overflow"), "gold_first_exposed_step": gold_step, "gold_discovered": gold_step is not None,
                         "tool_calls": len(steps), "api_calls": ms.get("api_calls"), "rejected_submissions": rejected, "rejected_gold_rank": rej_gold, "file_reads": reads, "searches": searches, "repo_wide_searches": repo, "test_runs": tests,
                         "direct_gold_search_step": direct_gold, "declarations_seen": len(decls_seen),
                         "declared_candidates_in_top10": sum(1 for t in top if t in roles_simple), "chain_tau_vs_depth": round(t_, 3) if t_ is not None else None,
                         "taxonomy": tax, "cost_usd": ms.get("instance_cost"), "wall_ms": man.get("duration_ms")})
json.dump(rows, open(out_path, "w"), indent=1)
agg = {}
for r in rows: agg.setdefault((r["attack"], r["model"]), []).append(r)
print(f"{len(rows)} runs")
for (a, m), rs in sorted(agg.items()):
    comp = [r for r in rs if r["status"] == "completed"]
    acc1 = sum(r["acc_at_1"] for r in comp) / len(comp) if comp else None; mrr = sum(r["mrr"] for r in comp) / len(comp) if comp else None
    print(f"  {a:14s} {m:9s} n={len(comp)}/{len(rs)} acc1={acc1 if acc1 is None else round(acc1,2)} mrr={mrr if mrr is None else round(mrr,2)} ranks={[r['gold_rank'] for r in comp]} tax={[r['taxonomy'][:6] for r in comp if r['taxonomy']!='CORRECT']}")
