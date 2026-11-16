"""cue-trust-v3 per-run metrics and per-cell summary (observable trajectory data only; reasoning content is never read).
Usage: ct_metrics.py   -> analysis/per_run.json, analysis/per_run.csv, analysis/summary_by_cell.json, prints the cell table.
Per run: status, gold rank, rank-1 category (gold / decoy / entry / other), Acc@1, effort (tool calls, characters displayed,
completion and prompt tokens, cost), FaultLineExposed, DecoyExposed, CueExposed (the run's own cue tokens shown), Verification
(a defects4j test / java probe actually executed), F1 compliance (declarations of the submitted top-3 displayed), and the
evidence-sufficiency class at commitment (sufficient = faulty line, decoy and the observed failure value all displayed): efficient (sufficient, correct), cue-override (sufficient, wrong), premature
(insufficient, wrong), guess (insufficient, correct). Non-completed runs count as not correct (intention to treat)."""
import json, os, re, sys, glob, csv
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ct_lib as C
KEY = json.load(open(f"{C.V3}/review/VARIANT_KEY.json")); SPECS = {}
SERVERS = json.load(open(f"{C.V3}/models/servers.json"))
def spec(iid):
    if iid not in SPECS: SPECS[iid] = json.load(open(f"{C.V3}/instances/{iid}/spec.json"))
    return SPECS[iid]
def norm(s): return re.sub(r"\s+", " ", s).strip()
def strip_prefix(out):
    out = out.replace("\r\n", "\n")
    return "\n".join(re.sub(r"^\s*(?:\S+?:)?\d+[:\t-]\s?", "", l) for l in out.split("\n"))
def level_tokens(sp, level):
    lv = sp["levels"][level]; toks = set()
    for r in lv.get("renames", []):
        if r["scope"] == "method": toks |= set(r["map"].values())
        else: toks |= {f"this.{v}" for v in r["map"].values()}
    return toks, norm(lv["comment"].lstrip("/ "))
rows = []
for server, cfg in SERVERS.items():
    for rd in sorted(glob.glob(f"{C.V3}/models/{server}/benchmark_runs/mini-swe-claude/CTV-*/run-*")):
        V = os.path.basename(os.path.dirname(rd)); K = KEY.get(V)
        if not K: continue
        sp = spec(K["instance_id"]); man = json.load(open(f"{rd}/run_manifest.json")) if os.path.exists(f"{rd}/run_manifest.json") else {}
        ev = json.load(open(f"{rd}/evaluation.json")) if os.path.exists(f"{rd}/evaluation.json") else {}
        rk = json.load(open(f"{rd}/ranking.json")) if os.path.exists(f"{rd}/ranking.json") else {}
        try: traj = json.load(open(f"{rd}/mini-swe-agent.traj.json"))
        except Exception: traj = {"messages": [], "info": {}}
        preds = ((rk.get("structured_submission") or {}).get("predictions") or rk.get("predictions") or [])
        keys = [f"{p.get('class')}::{p.get('method')}" for p in preds]
        top1 = keys[0] if keys else None
        cat = "none" if not top1 else ("gold" if top1 == K["gold"] else "decoy" if top1 in K["decoys"] else "entry" if top1 in K.get("facade", []) else "other")
        msgs = traj.get("messages", []); outs = [m.get("content") if isinstance(m.get("content"), str) else json.dumps(m.get("content")) for m in msgs if m.get("role") == "tool"]
        cmds = []
        for m in msgs:
            if m.get("role") == "assistant":
                for tc in m.get("tool_calls") or []:
                    try: cmds.append(json.loads((tc.get("function") or {}).get("arguments") or "{}").get("command", ""))
                    except Exception: pass
        allout = strip_prefix("\n".join(outs)); allout_n = norm(allout)
        comp = sum(int(x) for x in re.findall(r'"completion_tokens": (\d+)', json.dumps([m.get("extra") for m in msgs])))
        prom = sum(int(x) for x in re.findall(r'"prompt_tokens": (\d+)', json.dumps([m.get("extra") for m in msgs])))
        fault_exp = norm(sp["gold"]["bug_line"]) in allout_n
        decoy_exp = any(re.search(r"\b%s\s*\(" % re.escape(d["method"]), allout) and d["method"] in allout for d in sp["decoys"])
        toks, cmt = level_tokens(sp, K["level"]); cue_exp = (K["level"] != "C0") and (any(t in allout for t in toks) or (cmt and cmt in allout_n))
        verif = any(re.search(r"defects4j\s+test|(^|[\s;&|])(java|javac|jshell)\s", re.sub(r"/\S+", "/P", c)) for c in cmds)
        top3_shown = all(re.search(r"\b%s\s*\(" % re.escape(k.split("::")[1]), allout) for k in keys[:3]) if keys else False
        correct = man.get("status") == "completed" and ev.get("gold_rank") == 1
        witness_seen = bool(re.search(r"expected:<[^>]*> but was:<", allout))
        sufficient = fault_exp and decoy_exp and witness_seen
        cls = ("efficient" if correct else "cue_override") if sufficient else ("guess" if correct else "premature")
        rows.append({"server": server, "model": cfg["model"], "F": "F1" if cfg["inspection"] == "1" else "F0", "variant_id": V, "run": os.path.basename(rd),
                     "instance_id": K["instance_id"], "level": K["level"], "condition": "C0" if K["level"] == "C0" else K["level"][:2], "stratum": K["stratum"],
                     "status": man.get("status"), "gold_rank": ev.get("gold_rank"), "acc1": int(bool(correct)), "rank1": top1, "rank1_category": cat,
                     "tool_calls": len(cmds), "chars_displayed": len("\n".join(outs)), "completion_tokens": comp, "prompt_tokens": prom,
                     "cost_usd": ((traj.get("info") or {}).get("model_stats") or {}).get("instance_cost"),
                     "fault_line_exposed": fault_exp, "decoy_exposed": decoy_exp, "cue_exposed": cue_exp, "verification": verif,
                     "top3_declarations_shown": top3_shown, "failure_value_seen": witness_seen, "sufficiency_class": cls})
os.makedirs(f"{C.V3}/analysis", exist_ok=True)
json.dump(rows, open(f"{C.V3}/analysis/per_run.json", "w"), indent=1)
if rows:
    with open(f"{C.V3}/analysis/per_run.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
cells = {}
for r in rows:
    k = (r["model"], r["F"], r["instance_id"], r["condition"]); c = cells.setdefault(k, {"n": 0, "acc1": 0, "decoy1": 0, "fault_exp": 0, "cue_exp": 0, "verif": 0, "cost": 0.0, "classes": {}})
    c["n"] += 1; c["acc1"] += r["acc1"]; c["decoy1"] += int(r["rank1_category"] == "decoy"); c["fault_exp"] += int(r["fault_line_exposed"])
    c["cue_exp"] += int(r["cue_exposed"]); c["verif"] += int(r["verification"]); c["cost"] += float(r["cost_usd"] or 0)
    c["classes"][r["sufficiency_class"]] = c["classes"].get(r["sufficiency_class"], 0) + 1
out = [{"model": k[0], "F": k[1], "instance_id": k[2], "condition": k[3], **v} for k, v in sorted(cells.items())]
json.dump(out, open(f"{C.V3}/analysis/summary_by_cell.json", "w"), indent=1)
print(f"{len(rows)} runs")
for c in out:
    print(f"{c['model']:18s} {c['F']} {c['instance_id']:12s} {c['condition']:3s} n={c['n']} Acc@1={c['acc1']}/{c['n']} decoy@1={c['decoy1']} faultExp={c['fault_exp']} cueExp={c['cue_exp']} verif={c['verif']} classes={c['classes']} cost=${c['cost']:.2f}")
