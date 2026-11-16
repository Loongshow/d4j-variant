"""Table generator for the GPT-5.6 pilot reports (formatting only; every number comes from ct_metrics.py outputs).
Usage: gpt56_tables.py [--F F0|F1]  -> analysis/gpt56_tables_<F>.md and GPT56_RUN_LEVEL_RESULTS.csv (F0 analysis runs, all columns)."""
import json, sys, os, csv, statistics as st
V3 = "/Users/shawnli/Desktop/Honours/defects4j/.claude/worktrees/strict-depth-experiment-run-524113/supervisor_pipeline_runs/cue-trust-v3"
F = sys.argv[sys.argv.index("--F") + 1] if "--F" in sys.argv else "F0"
rows = [r for r in json.load(open(f"{V3}/analysis/per_run.json")) if r["model"] == "gpt-5.6" and r["F"] == F]
cells = [c for c in json.load(open(f"{V3}/analysis/summary_by_cell.json")) if c["model"] == "gpt-5.6" and c["F"] == F]
cons = [c for c in json.load(open(f"{V3}/analysis/contrasts.json")) if c["model"] == "gpt-5.6" and c["F"] == F]
ORDER = {"C0": 0, "CG": 1, "CD": 2}; INST = ["CT-CHART-01", "CT-LANG-01", "CT-CHART-03", "CT-CHART-02"]
def fmt(x, nd=2):
    if x is None: return "–"
    if isinstance(x, float): return f"{x:.{nd}f}"
    return str(x)
def q(xs):
    xs = sorted(x for x in xs if x is not None)
    if not xs: return "–"
    if len(xs) == 1: return f"{xs[0]}"
    qs = st.quantiles(xs, n=4, method="inclusive"); return f"{xs[0]} / {qs[0]:.0f} / {st.median(xs):.0f} / {qs[2]:.0f} / {xs[-1]}"
out = []
out.append(f"## Per-instance results ({F})\n")
out.append("| Instance | Condition | n (valid/attempted) | Answered | Acc@1 | MRR | Gold ranks | Decoy first | Gold exposed, misranked | Full gold read | Top-3 full read | Tests run | Median tools | Median reasoning tok | Median cost (USD) |")
out.append("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
for c in sorted(cells, key=lambda c: (INST.index(c["instance_id"]) if c["instance_id"] in INST else 9, ORDER[c["condition"]])):
    out.append(f"| {c['instance_id']} | {c['condition']} | {c['n']}/{c['attempted']} | {c['answered']} | {fmt(c['acc1'])} | {fmt(c['mrr'])} | "
               f"{', '.join('–' if g is None else str(g) for g in c['gold_ranks'])} | {c['decoy_first']} | {c['gold_exposed_misranked']} | {fmt(c['full_gold_read_rate'])} | "
               f"{fmt(c['top3_full_read_rate'])} | {fmt(c['test_execution_rate'])} | {fmt(c['median_tool_calls'], 0)} | {fmt(c['median_reasoning_tokens'], 0)} | {fmt(c['median_cost_usd'], 3)} |")
out.append(f"\n## Condition totals ({F}, pooled over instances; descriptive)\n")
out.append("| Condition | n | Answered | Acc@1 | MRR | Decoy first | Entry first | Other first | No answer | Gold exposed, misranked | Strong signal | Cue exposed |")
out.append("|---|---|---|---|---|---|---|---|---|---|---|---|")
for cond in ("C0", "CG", "CD"):
    b = [r for r in rows if r["condition"] == cond and r["included"]]; n = len(b)
    if not n: continue
    cnt = lambda cat: sum(1 for r in b if r["rank1_category"] == cat)
    cue = "–" if cond == "C0" else f"{sum(1 for r in b if r['cue_exposed'])}/{n}"
    out.append(f"| {cond} | {n} | {sum(r['answered'] for r in b)} | {sum(r['acc1'] for r in b) / n:.2f} | {sum(r['rr'] for r in b) / n:.2f} | {cnt('DECOY')} | {cnt('ENTRY_POINT')} | "
               f"{cnt('OTHER')} | {cnt('NO_ANSWER')} | {sum(r['gold_exposed_misranked'] for r in b)} | {sum(r['strong_signal'] for r in b)} | {cue} |")
out.append(f"\n## Pre-specified contrasts ({F})\n")
out.append("| Instance | Contrast | Delta | Class | Baseline flag | n flag | Acc@1 C0 → cue | Decoy first C0 → cue |")
out.append("|---|---|---|---|---|---|---|---|")
for c in sorted(cons, key=lambda c: (INST.index(c["instance_id"]) if c["instance_id"] in INST else 9, c["contrast"])):
    k = c["contrast"].split()[-1]
    out.append(f"| {c['instance_id']} | {c['contrast']} | {c['delta']:+.2f} | {c['class']} | {c['baseline_flag'] or '–'} | {c.get('n_flag') or '–'} | {c['acc1_C0']:.2f} → {c['acc1_' + k]:.2f} | {c['decoy_first_C0']} → {c['decoy_first_' + k]} |")
out.append(f"\n## Trajectory measures by condition ({F}, valid runs; counts of runs)\n")
meas = [("gold_exposed", "Gold faulty line shown"), ("decoy_exposed", "Decoy signature shown"), ("full_gold_read", "Full gold method read"), ("full_decoy_read", "Full decoy method read"),
        ("top3_full_read", "Top-3 bodies fully read"), ("tests_executed", "Tests executed"), ("independent_probe_executed", "Independent probe"),
        ("decisive_evidence_exposed", "Failure values shown"), ("cue_exposed", "Cue line shown")]
out.append("| Measure | C0 | CG | CD |"); out.append("|---|---|---|---|")
for k, lab in meas:
    cells_ = []
    for cond in ("C0", "CG", "CD"):
        b = [r for r in rows if r["condition"] == cond and r["included"]]
        cells_.append("–" if (k == "cue_exposed" and cond == "C0") or not b else f"{sum(1 for r in b if r[k])}/{len(b)}")
    out.append(f"| {lab} | " + " | ".join(cells_) + " |")
out.append("\n| Sufficiency class | C0 | CG | CD |"); out.append("|---|---|---|---|")
for k in ("efficient", "cue_override", "premature", "guess"):
    out.append(f"| {k} | " + " | ".join(str(sum(1 for r in rows if r["condition"] == cond and r["included"] and r["sufficiency_class"] == k)) for cond in ("C0", "CG", "CD")) + " |")
out.append(f"\n## Effort and token distributions ({F}; min / Q1 / median / Q3 / max over valid runs)\n")
out.append("| Condition | Tool calls | Model calls | Files read | Lines read | Searches | Test runs | Reasoning tokens | Output tokens | Input tokens | Cost (USD, total) | Wall time (s) |")
out.append("|---|---|---|---|---|---|---|---|---|---|---|---|")
for cond in ("C0", "CG", "CD"):
    b = [r for r in rows if r["condition"] == cond and r["included"]]
    if not b: continue
    out.append(f"| {cond} | {q([r['tool_calls'] for r in b])} | {q([r['model_calls'] for r in b])} | {q([r['file_reads'] for r in b])} | {q([r['lines_read'] for r in b])} | "
               f"{q([r['searches'] for r in b])} | {q([r['test_executions'] for r in b])} | {q([r['reasoning_tokens'] for r in b])} | {q([r['output_tokens'] for r in b])} | "
               f"{q([r['input_tokens'] for r in b])} | {sum(float(r['cost_usd'] or 0) for r in b):.2f} | {q([round(r['wall_time_s']) if r['wall_time_s'] else None for r in b])} |")
out.append(f"\n## Reasoning tokens by outcome ({F}; observational only)\n")
out.append("| Rank-1 category | n | Reasoning tokens (min / Q1 / median / Q3 / max) | Tool calls (median) |"); out.append("|---|---|---|---|")
for cat in ("GOLD", "DECOY", "ENTRY_POINT", "OTHER", "NO_ANSWER"):
    b = [r for r in rows if r["rank1_category"] == cat and r["included"]]
    if b: out.append(f"| {cat} | {len(b)} | {q([r['reasoning_tokens'] for r in b])} | {st.median([r['tool_calls'] for r in b]):.0f} |")
ex = [r for r in rows if not r["included"]]
LED = {}
for sv in {r["server"] for r in rows}:
    pth = f"{V3}/diagnostic/block_{sv}.jsonl"
    if os.path.exists(pth):
        for l in open(pth):
            try: x = json.loads(l); LED[(sv, x["run"])] = x
            except Exception: pass
def why(r):
    x = LED.get((r["server"], f"{r['variant_id']}/{r['run']}"), {})
    detail = x.get("scan_reasons") or x.get("identity_diff") or x.get("halt_reason") or x.get("release_reason") or ""
    return f"{r['status_kind']} (driver verdict {r['driver_verdict']}; status {r['status']}, harness {r['harness_status']}) {str(detail)[:160]}"
out.append(f"\n## Excluded runs ({F})\n")
out.append("None." if not ex else "\n".join(f"- {r['variant_id']}/{r['run']} {r['instance_id']} {r['level']}: {why(r)}" for r in ex))
inc = [r for r in rows if r["included"]]; cue_runs = [r for r in inc if r["condition"] != "C0"]
gate = [("Cue displayed in CG/CD runs", f"{sum(1 for r in cue_runs if r['cue_exposed'])}/{len(cue_runs)}", ">= 80%",
         (sum(1 for r in cue_runs if r['cue_exposed']) / len(cue_runs) >= 0.8) if cue_runs else None),
        ("Cost per run (max, USD)", f"{max([float(r['cost_usd'] or 0) for r in rows] or [0]):.3f}", "<= 1.00",
         (max([float(r['cost_usd'] or 0) for r in rows] or [0]) <= 1.0) if rows else None),
        ("Timeout rate (behavioural timeouts / counted runs)", f"{sum(1 for r in inc if r['status'] == 'timeout')}/{len(inc)}", "<= 20%",
         (sum(1 for r in inc if r['status'] == 'timeout') / len(inc) <= 0.2) if inc else None),
        ("Provider stalls/errors (excluded, reported)", str(sum(1 for r in rows if r["status_kind"] == "infrastructure")), "reported", None),
        ("Metrics agree with hand labels on 5 runs", "manual", "5/5", None)]
out.append(f"\n## Pre-registered pilot gate ({F})\n")
out.append("| Check | Observed | Criterion | Met |"); out.append("|---|---|---|---|")
for k, o, c_, m_ in gate: out.append(f"| {k} | {o} | {c_} | {'–' if m_ is None else ('yes' if m_ else 'NO')} |")
open(f"{V3}/analysis/gpt56_tables_{F}.md", "w").write("\n".join(out) + "\n")
if F == "F0" and rows:
    with open(f"{V3}/GPT56_RUN_LEVEL_RESULTS.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
print(f"{len(rows)} {F} runs -> analysis/gpt56_tables_{F}.md")
