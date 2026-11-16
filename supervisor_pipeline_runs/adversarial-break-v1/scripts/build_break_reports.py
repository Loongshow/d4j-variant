#!/usr/bin/env python
"""Screening / confirmation / model-comparison / taxonomy reports from attack_run_metrics.json.
Usage: build_break_reports.py [--phase screening|confirmation|all]"""
import json, os, sys, collections, statistics as st
R = "/Users/shawnli/Desktop/Honours/defects4j/supervisor_pipeline_runs/adversarial-break-v1"; A = f"{R}/analysis"
rows = json.load(open(f"{A}/per_run/attack_run_metrics.json"))
MODELS = ["haiku45", "sonnet46", "opus55"]; VALID = ["sonnet46t", "opus55t"]
MID = {"haiku45": "claude-haiku-4-5", "sonnet46": "claude-sonnet-4-6", "opus55": "claude-opus-5-5", "sonnet46t": "claude-sonnet-4-6 (v2+runner)", "opus55t": "claude-opus-5-5 (v2+runner)"}
all_rows = rows; rows = [r for r in all_rows if r["model"] in MODELS]          # main (pre-registered) analysis: protocol v2 only
vrows = [r for r in all_rows if r["model"] in VALID]
def label(acc1):
    if acc1 is None: return "-"
    return "VERY STRONG" if acc1 <= 0.30 else "STRONG" if acc1 <= 0.50 else "MODERATE" if acc1 <= 0.70 else "WEAK" if acc1 <= 0.90 else "NULL"
def agg(rs):
    comp = [r for r in rs if r["status"] == "completed"]; n = len(comp)
    valid = [r for r in rs if r["status"] not in ("provider_error", "provider_stall")]          # every attempt the agent was allowed to finish
    if not n and not valid: return {"n": 0, "attempted": len(rs)}
    if not n: return {"n": 0, "attempted": len(rs), "n_valid": len(valid), "acc1_all": 0.0, "exhausted": sum(1 for r in rs if r.get("agent_exhausted")), "infra": sum(1 for r in rs if r["status"] in ("provider_error", "provider_stall")), "cost": round(sum(r["cost_usd"] or 0 for r in rs), 4), "ranks": []}
    return {"n": n, "attempted": len(rs), "n_valid": len(valid), "acc1": round(sum(r["acc_at_1"] for r in comp) / n, 3),
            "acc1_all": round(sum(r["acc_at_1"] for r in valid) / len(valid), 3), "exhausted": sum(1 for r in rs if r.get("agent_exhausted")), "acc3": round(sum(r["acc_at_3"] for r in comp) / n, 3),
            "acc5": round(sum(r["acc_at_5"] for r in comp) / n, 3), "acc10": round(sum(r["acc_at_10"] for r in comp) / n, 3), "mrr": round(st.mean(r["mrr"] for r in comp), 3),
            "ranks": [r["gold_rank"] for r in comp], "gold_in_top10": sum(1 for r in comp if r["gold_in_top10"]), "gold_discovered": sum(1 for r in comp if r["gold_discovered"]),
            "tool_calls": round(st.mean(r["tool_calls"] for r in comp), 1), "first_gold": round(st.mean([r["gold_first_exposed_step"] for r in comp if r["gold_first_exposed_step"]]), 1) if any(r["gold_first_exposed_step"] for r in comp) else None,
            "rank1_roles": dict(collections.Counter(r["rank1_role"] for r in comp)), "taxonomy": dict(collections.Counter(r["taxonomy"] for r in comp if r["taxonomy"] != "CORRECT")),
            "cost": round(sum(r["cost_usd"] or 0 for r in rs), 4), "infra": sum(1 for r in rs if r["status"] in ("provider_error", "provider_stall"))}
attacks = sorted({r["attack"] for r in rows}, key=lambda a: a or "")
table = {(a, m): agg([r for r in rows if r["attack"] == a and r["model"] == m]) for a in attacks for m in MODELS}
json.dump({f"{a}|{m}": v for (a, m), v in table.items()}, open(f"{A}/tables/attack_by_model.json", "w"), indent=1)
os.makedirs(f"{A}/per_attack", exist_ok=True)
for a in attacks:
    json.dump({"attack": a, "per_model": {m: table[(a, m)] for m in MODELS}, "runs": [r for r in rows if r["attack"] == a]}, open(f"{A}/per_attack/{a}.json", "w"), indent=1)


def emit(name, lines):
    """Write a generated report; append the hand-written reading in analysis/narratives/<name>.md when present."""
    nar = f"{A}/narratives/{name}.md"
    body = "\n".join(lines) + "\n"
    if os.path.exists(nar): body += "\n" + open(nar).read().rstrip("\n") + "\n"
    open(f"{R}/{name}.md", "w").write(body)

PROTO_NOTE = "Protocol v2 (frozen prompt, 50 tool calls, 5 test runs, 300 s, structured submission) with one deviation from the GPT-5.6 runs: `defects4j test` could not execute for the Claude agents (`diagnostic/PROTOCOL_DEVIATION_TEST_RUNNER.md`). Provider errors and provider stalls are excluded from every denominator (`diagnostic/PROVIDER_STALL_RULE.md`)."
def md_table(models, title, atts=None):
    L = [f"# {title}", "", PROTO_NOTE, "", "| Attack | Model | answered / attempted | Acc@1 (answered) | Acc@1 (all attempts) | label (all) | no-answer (budget/time) | provider errors | MRR | gold ranks | gold discovered | gold in top-10 | tool calls | first gold | rank-1 roles | failure taxonomy | cost USD |", "|" + "---|" * 17]
    for a in (atts if atts is not None else attacks):
        for m in models:
            v = table[(a, m)]
            if not v.get("attempted"): continue
            if not v.get("n"):
                L.append(f"| `{a}` | {MID[m]} | 0/{v['attempted']} | - | **{v.get('acc1_all')}** | {label(v.get('acc1_all'))} | {v.get('exhausted')} | {v.get('infra')} | - | [] | - | - | - | - | - | - | {v.get('cost')} |"); continue
            L.append(f"| `{a}` | {MID[m]} | {v['n']}/{v['attempted']} | {v['acc1']} | **{v['acc1_all']}** | {label(v['acc1_all'])} | {v['exhausted']} | {v['infra']} | {v['mrr']} | {v['ranks']} | {v['gold_discovered']}/{v['n']} | {v['gold_in_top10']}/{v['n']} | {v['tool_calls']} | {v['first_gold']} | {json.dumps(v['rank1_roles'])} | {json.dumps(v['taxonomy'])} | {v['cost']} |")
    return L
phase = sys.argv[sys.argv.index("--phase") + 1] if "--phase" in sys.argv else "all"
S = md_table(["sonnet46", "haiku45"], "Screening results (weaker Claude, 3 runs per attack)")
S += ["", "Ranking by observed Acc@1 on the primary weaker model (claude-sonnet-4-6), lowest first:", ""]
ranked = sorted([a for a in attacks if table[(a, "sonnet46")].get("attempted")], key=lambda a: (table[(a, "sonnet46")].get("acc1_all", 1.0), table[(a, "sonnet46")].get("mrr", 1.0)))
for i, a in enumerate(ranked, 1):
    v = table[(a, "sonnet46")]; h = table[(a, "haiku45")]
    S.append(f"{i}. `{a}`: Acc@1 over all attempts {v.get('acc1_all')} ({label(v.get('acc1_all'))}); over answered {v.get('acc1')}; no-answer {v.get('exhausted')}/{v.get('n_valid')}; ranks {v.get('ranks')}" + (f"; haiku Acc@1(all) {h.get('acc1_all')}" if h.get("attempted") else ""))
emit("SCREENING_RESULTS", S)
C = md_table(MODELS, "Confirmation results (all models, all runs to date)")
emit("CONFIRMATION_RESULTS", C)
M = ["# Model comparison", "", PROTO_NOTE, "", "| Attack | " + " | ".join(f"{MID[m]} Acc@1 all (answered/attempted)" for m in MODELS) + " | " + " | ".join(f"{MID[m]} MRR" for m in MODELS) + " | transfers to Opus? |", "|" + "---|" * (2 + 2 * len(MODELS))]
for a in attacks:
    cells = []; mrrs = []
    for m in MODELS:
        v = table[(a, m)]; cells.append(f"{v.get('acc1_all')} ({v.get('n',0)}/{v['attempted']})" if v.get("attempted") else "-"); mrrs.append(f"{v['mrr']}" if v.get("n") else "-")
    w, o = table[(a, "sonnet46")], table[(a, "opus55")]
    tr = "-" if not (w.get("attempted") and o.get("attempted")) else ("yes" if o.get("acc1_all",1) <= 0.7 and w.get("acc1_all",1) <= 0.7 else "weaker-only" if w.get("acc1_all",1) <= 0.7 < o.get("acc1_all",1) else "no (both robust)" if w.get("acc1_all",1) > 0.7 and o.get("acc1_all",1) > 0.7 else "opus-only")
    M.append(f"| `{a}` | " + " | ".join(cells) + " | " + " | ".join(mrrs) + f" | {tr} |")
emit("MODEL_COMPARISON", M)
T = ["# Failure taxonomy (every incorrect completed run)", "", PROTO_NOTE, "", "Mechanically assigned from the attack's pre-registered roles: rank-1 role -> class; gold never exposed -> DISCOVERY_FAILURE;",
     "gold exposed but absent from the ranking -> CANDIDATE_OVERLOAD (when 10 predictions were submitted) else SEARCH_DIVERSION.", "",
     "| Attack | Model | Run | Gold rank | Rank-1 | Rank-1 role | Gold discovered (step) | Tool calls | Class |", "|" + "---|" * 9]
for r in rows:
    if r["status"] not in ("provider_error", "provider_stall") and r["gold_rank"] != 1:
        T.append(f"| `{r['attack']}` | {MID[r['model']]} | {r['run']} | {r['gold_rank']} | `{r['rank1']}` | {r['rank1_role']} | {'yes' if r['gold_discovered'] else 'no'} ({r['gold_first_exposed_step']}) | {r['tool_calls']} | **{r['taxonomy']}** |")
cnt = collections.Counter(r["taxonomy"] for r in rows if r["status"] not in ("provider_error", "provider_stall") and r["gold_rank"] != 1)
T += ["", "## Counts", "", "| Class | Runs |", "|---|---|"] + [f"| {k} | {v} |" for k, v in cnt.most_common()]
emit("FAILURE_TAXONOMY", T)
print("reports written;", len(rows), "runs")
for a in attacks:
    print(" ", a, {m: (table[(a, m)].get("acc1"), table[(a, m)].get("n")) for m in MODELS if table[(a, m)].get("n")})

# ---- Part 17: maximum-difficulty composite -------------------------------------------------------------------
COMP, BASE = "MAX-01", "CMB-01"   # attack ids of ADV-COMPOSITE-01 and ADV-DEFINER-01 (rows are keyed by attack_id)
X = ["# Maximum-difficulty composite (Part 17): ADV-COMPOSITE-01", "", PROTO_NOTE, "",
     "Design and pre-registered gold: `TOP5_ATTACKS.md` (last section) and `construction/packages/ADV-COMPOSITE-01/attack.json`.",
     "The composite is `ADV-DEFINER-01` plus gold witness removal, guard padding, a loud correct terminal and boolean-only trigger assertions.",
     "Plan: claude-sonnet-4-6 x10, claude-opus-5-5 x5. Acc@1 is reported over answered runs and over all attempts the agent was allowed",
     "to finish (timeouts and budget exhaustion count as misses; provider errors are excluded).", ""]
if COMP in attacks:
    X += md_table(MODELS, "Composite results", [COMP])[2:]
    X += ["", "## Composite (MAX-01 = ADV-COMPOSITE-01) versus its clean core (CMB-01 = ADV-DEFINER-01)", "", "| Model | attack | answered/attempted | Acc@1 all | MRR | gold ranks | rank-1 roles | mean tool calls |", "|---|---|---|---|---|---|---|---|"]
    for m in MODELS:
        for a in (BASE, COMP):
            v = table[(a, m)]
            if not v.get("attempted"): continue
            X.append(f"| {MID[m]} | `{a}` | {v.get('n',0)}/{v['attempted']} | {v.get('acc1_all')} | {v.get('mrr','-')} | {v.get('ranks')} | {json.dumps(v.get('rank1_roles',{}))} | {v.get('tool_calls','-')} |")
    X += ["", "## Per-run detail", "", "| Model | Run | status | gold rank | rank-1 | rank-1 role | gold first exposed (step) | tool calls | cost USD | class |", "|" + "---|" * 10]
    for r in sorted([r for r in rows if r["attack"] == COMP], key=lambda r: (r["model"], r["run"])):
        X.append(f"| {MID[r['model']]} | {r['run']} | {r['status']} | {r['gold_rank']} | `{r['rank1']}` | {r['rank1_role']} | {r['gold_first_exposed_step']} | {r['tool_calls']} | {r['cost_usd']} | **{r['taxonomy']}** |")
else:
    X.append("No composite runs recorded yet.")
emit("MAX_DIFFICULTY_RESULTS", X)

# ---- validity block: headline attack under a working test runner (protocol v2+runner) ----------------------------
vt = {(a, m): agg([r for r in vrows if r["attack"] == a and r["model"] == m]) for a in attacks for m in VALID}
Y = ["# Validity block: `ADV-DEFINER-01` with an executable `defects4j test` (protocol v2+runner)", "",
     "Why this exists: every Claude run in the main tables (and in the pilot) could not execute `defects4j test` because the servers lacked",
     "`PERL5LIB`; the frozen GPT-5.6 runs could. See `diagnostic/PROTOCOL_DEVIATION_TEST_RUNNER.md`. This block re-runs only the headline",
     "attack with the runner fixed (servers `opus55t`, `sonnet46t`), Opus x5 and Sonnet x5, and is never mixed into the main tables.", "",
     "| Attack | Model | protocol | answered / attempted | Acc@1 (answered) | Acc@1 (all attempts) | MRR | gold ranks | rank-1 roles | test runs executed (mean) | tool calls | provider stalls |", "|" + "---|" * 12]
for a in attacks:
    for m, v, proto in [(m, table[(a, m)], "v2") for m in ("sonnet46", "opus55")] + [(m, vt[(a, m)], "v2+runner") for m in VALID]:
        src = rows if proto == "v2" else vrows
        rs = [r for r in src if r["attack"] == a and r["model"] == m and r["status"] == "completed"]
        if not v.get("attempted") or not any(vt[(a, mm)].get("attempted") for mm in VALID): continue
        tr = round(st.mean(r["test_runs"] for r in rs), 1) if rs else "-"
        Y.append(f"| `{a}` | {MID[m]} | {proto} | {v.get('n',0)}/{v['attempted']} | {v.get('acc1','-')} | **{v.get('acc1_all')}** | {v.get('mrr','-')} | {v.get('ranks')} | {json.dumps(v.get('rank1_roles',{}))} | {tr} | {v.get('tool_calls','-')} | {v.get('infra',0)} |")
if len(Y) == 8: Y.append("No validity runs recorded yet.")
Y += ["", "## Per-run detail (v2+runner)", "", "| Model | Run | status | gold rank | rank-1 | test runs | gold first exposed (step) | tool calls | cost USD | class |", "|" + "---|" * 10]
for r in sorted(vrows, key=lambda r: (r["attack"], r["model"], r["run"])):
    Y.append(f"| {MID[r['model']]} | {r['run']} | {r['status']} | {r['gold_rank']} | `{r['rank1']}` | {r['test_runs']} | {r['gold_first_exposed_step']} | {r['tool_calls']} | {r['cost_usd']} | **{r['taxonomy']}** |")
emit("VALIDITY_TEST_RUNNER", Y)
