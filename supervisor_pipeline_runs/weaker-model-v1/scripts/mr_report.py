"""Main run: KPI report from the frozen per-run measures. Run mx_metrics.py first (it writes analysis/per_run.json).
KPI (Hong Jin, 2026-10-16; main-run/MAIN_RUN_PLAN.md):
  SHIFT            a run that submitted a ranking whose gold rank is not 1 (absent from the top 10 = rank 11).
  INSTANCE_SUCCESS at least one of the instance's first 5 valid runs (by run number) is a SHIFT.
  Runs without a ranking (timeouts, no answer) are reported separately and never count as a shift.
  FLAGGED instances (audit FLAG_AMBIGUOUS) are reported separately and never counted in M.
Failure-mode label (mechanical, from frozen mx_metrics fields; not blind-coded):
  GOLD_FIRST          answered, gold rank 1 (the transformation did not shift this run)
  ENTRY_POINT_BIAS    shifted; the facade (entry point) is ranked first and a gold fault line was displayed
  UPSTREAM_HOP_FIRST  shifted; a non-gold hop of the chain is ranked first and a gold fault line was displayed
  OTHER_FIRST         shifted; some other method is ranked first and a gold fault line was displayed
  GOLD_NOT_REACHED    shifted; no gold fault line was ever displayed
  NO_ANSWER_<status>  no ranking submitted (timeout etc.)
Reads analysis/per_run.json, review/VARIANT_KEY.json, main-run/INSTANCE_BUILD_LOG.csv, main-run/INSTANCE_PROVENANCE.csv,
diagnostic/run_MR_*.out (probe counts). Writes main-run/MAIN_RUN_RUNS.csv, MAIN_RUN_RESULTS.csv, SHIFTED_INSTANCES.md,
FAILED_TO_TRANSFER.md, COST_LEDGER.csv and main-run/analysis/main_run_summary.json. Usage: mr_report.py"""
import csv, glob, json, os, re, statistics as st
from collections import Counter, defaultdict
HERE = os.path.dirname(os.path.abspath(__file__)); WM = os.path.dirname(HERE); MR = f"{WM}/main-run"
os.makedirs(f"{MR}/analysis", exist_ok=True)
ABSENT = 11; PROBE_USD = 0.008; PRIOR_RECORDED = 64.10; PRIOR_WITH_EST = 66.25
runno = lambda s: int(re.search(r"run-(\d+)", s).group(1))
key = json.load(open(f"{WM}/review/VARIANT_KEY.json"))
build = {r["instance"]: r for r in csv.DictReader(open(f"{MR}/INSTANCE_BUILD_LOG.csv"))}
prov = {r["instance_id"]: r for r in csv.DictReader(open(f"{MR}/INSTANCE_PROVENANCE.csv"))}
batch_of = {f"MR-{k}": r["batch"] for k, r in build.items()}
recs = [r for r in json.load(open(f"{WM}/analysis/per_run.json")) if r.get("tier") == "MAIN_RUN" and r.get("server") == "w55"]
# the driver ledger keeps the gold rank of excluded records (mx_metrics blanks it); used only to list exclusions, never counted
LEDGER = {}
for l in open(f"{WM}/diagnostic/block_w55.jsonl"):
    if l.strip(): x = json.loads(l); LEDGER[x["run"]] = x

def mode(r):
    if not r.get("answered"): return f"NO_ANSWER_{(r.get('status') or 'unknown').upper()}"
    g = r["gold_rank"] if r["gold_rank"] is not None else ABSENT
    if g == 1: return "GOLD_FIRST"
    if not r.get("gold_exposed"): return "GOLD_NOT_REACHED"
    return {"ENTRY_POINT": "ENTRY_POINT_BIAS", "DECOY": "UPSTREAM_HOP_FIRST"}.get(r.get("rank1_category"), "OTHER_FIRST")

run_rows = []
for r in sorted(recs, key=lambda r: (r["instance_id"], runno(r["run"]))):
    g = (r["gold_rank"] if r["gold_rank"] is not None else ABSENT) if r.get("answered") else None
    p = prov.get(r["instance_id"], {})
    run_rows.append({"instance_id": r["instance_id"], "batch": batch_of.get(r["instance_id"], ""), "project": r["project"],
        "bug_id": p.get("bug_id", ""), "variant_id": r["variant_id"], "run": r["run"], "included": r.get("included"),
        "driver_verdict": r.get("driver_verdict"), "status": r.get("status"), "answered": r.get("answered"), "gold_rank": g,
        "ledger_gold_rank": (LEDGER.get(f"{r['variant_id']}/{r['run']}") or {}).get("gold_rank"),
        "shift": bool(r.get("included") and r.get("answered") and g != 1), "rank1": r.get("rank1"), "rank1_category": r.get("rank1_category"),
        "failure_mode": mode(r) if r.get("included") else "EXCLUDED", "gold_exposed": r.get("gold_exposed"),
        "full_gold_read": r.get("full_gold_read"), "evidence_displayed": r.get("evidence_displayed"), "tests_executed": r.get("test_executions"),
        "tool_calls": r.get("tool_calls"), "model_calls": r.get("model_calls"), "total_tokens": r.get("total_tokens"),
        "cost_usd": round(r.get("cost_usd") or 0, 6), "wall_time_s": r.get("wall_time_s")})

by = defaultdict(list)
for x in run_rows: by[x["instance_id"]].append(x)
inst_rows = []
for iid in sorted(by):
    allr = by[iid]; valid = sorted([x for x in allr if x["included"]], key=lambda x: runno(x["run"]))[:5]
    ans = [x for x in valid if x["answered"]]; shifted = [x for x in ans if x["gold_rank"] != 1]
    b = build.get(iid[3:], {}); p = prov.get(iid, {})
    flagged = b.get("status") == "FLAGGED"
    inst_rows.append({"instance_id": iid, "instance": iid[3:], "batch": batch_of.get(iid, ""), "project": p.get("project", ""), "bug_id": p.get("bug_id", ""),
        "variant_id": p.get("variant_id", ""), "build_status": b.get("status", ""), "audit_verdict": b.get("audit_verdict", ""),
        "counted_in_kpi": not flagged, "valid_runs": len(valid), "answered": len(ans), "no_answer": len(valid) - len(ans),
        "shifted_runs": len(shifted), "shifted_over_answered": f"{len(shifted)}/{len(ans)}",
        "instance_success": bool(shifted), "gold_ranks": " ".join(str(x["gold_rank"]) if x["gold_rank"] is not None else "NA" for x in valid),
        "failure_modes": "; ".join(f"{k} {v}" for k, v in Counter(x["failure_mode"] for x in valid).most_common()),
        "rank1_categories": "; ".join(f"{k} {v}" for k, v in Counter(x["rank1_category"] for x in valid).most_common()),
        "gold_exposed_runs": sum(1 for x in valid if x["gold_exposed"]), "full_gold_read_runs": sum(1 for x in valid if x["full_gold_read"]),
        "timeouts": sum(1 for x in valid if x["status"] == "timeout"), "excluded_records": len(allr) - sum(1 for x in allr if x["included"]),
        "cost_usd_all_records": round(sum(x["cost_usd"] for x in allr), 4),
        "median_tool_calls": st.median([x["tool_calls"] for x in valid]) if valid else "",
        "median_wall_s": round(st.median([x["wall_time_s"] for x in valid]), 1) if valid else "",
        "facade": p.get("facade", ""), "gold": p.get("gold", "")})

def write(path, rows):
    if not rows: return
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
write(f"{MR}/MAIN_RUN_RUNS.csv", run_rows); write(f"{MR}/MAIN_RUN_RESULTS.csv", inst_rows)

counted = [x for x in inst_rows if x["counted_in_kpi"]]
N = len(counted); M = sum(1 for x in counted if x["instance_success"])
ans_n = sum(x["answered"] for x in counted); sh_n = sum(x["shifted_runs"] for x in counted)
per_project = defaultdict(lambda: [0, 0])
for x in counted: per_project[x["project"]][0] += 1; per_project[x["project"]][1] += int(x["instance_success"])
modes = Counter(x["failure_mode"] for x in run_rows if x["included"])

# cost: run records (all, including excluded) + probe estimate per batch; construction has no OpenAI spend
probes = {}
for f in glob.glob(f"{WM}/diagnostic/run_MR_*.out"):
    probes[os.path.basename(f)[4:-4]] = sum(1 for l in open(f) if "probe: " in l)
batches = sorted({x["batch"] for x in inst_rows})
cost_rows, cum_rec, cum_est = [], PRIOR_RECORDED, PRIOR_WITH_EST
cost_rows.append({"item": "Before the main run (root COST_LEDGER.csv)", "batch": "", "records": "", "cost_usd": "", "cumulative_recorded_usd": PRIOR_RECORDED,
                  "cumulative_incl_estimates_usd": PRIOR_WITH_EST, "validated_instances": "", "successful_instances": "", "usd_per_validated_instance": "",
                  "usd_per_successful_instance": "", "note": "recorded run cost $64.10; $66.25 including replay and probe estimates"})
for b in batches:
    bi = [x for x in inst_rows if x["batch"] == b]; brecs = [x for x in run_rows if x["batch"] == b]
    run_cost = round(sum(x["cost_usd"] for x in brecs), 4)
    nprobe = sum(v for k, v in probes.items() if k.startswith(f"MR_{b}")); probe_cost = round(nprobe * PROBE_USD, 3)
    nval = sum(1 for x in bi if x["counted_in_kpi"]); nsucc = sum(1 for x in bi if x["counted_in_kpi"] and x["instance_success"])
    cum_rec = round(cum_rec + run_cost, 2); cum_est = round(cum_est + run_cost + probe_cost, 2)
    nb = sum(1 for r in build.values() if r["batch"] == b); na = sum(1 for r in build.values() if r["batch"] == b and r["validation"] == "READY")
    agents = f"{nb} builder + {na} auditor agents"
    if os.path.exists(f"{MR}/{b}_build_audit_results.json"):
        br = json.load(open(f"{MR}/{b}_build_audit_results.json"))
        if br and "versions" in br[0]:   # batch-3 pipeline: builders, redesigns, audits and blind trace checks
            vs = [v for r in br for v in r["versions"]]
            agents = (f"{sum(1 for v in vs if v['v'] == 1)} builders + {sum(1 for v in vs if v['v'] == 2)} redesigns + "
                      f"{sum(1 for v in vs if v.get('audit'))} audits + {sum(1 for v in vs if v.get('trace'))} trace checks")
    cost_rows.append({"item": f"Main run {b} construction ({agents}; {nval} validated, {nb - nval} not validated)", "batch": b, "records": "", "cost_usd": 0.0,
                      "cumulative_recorded_usd": "", "cumulative_incl_estimates_usd": "", "validated_instances": nval, "successful_instances": "",
                      "usd_per_validated_instance": 0.0, "usd_per_successful_instance": "", "note": "no OpenAI spend; agent time only (INSTANCE_BUILD_LOG.csv builder_minutes)"})
    cost_rows.append({"item": f"Main run {b} gpt-5.5 runs (w55)", "batch": b, "records": len(brecs), "cost_usd": run_cost,
                      "cumulative_recorded_usd": cum_rec, "cumulative_incl_estimates_usd": "", "validated_instances": nval, "successful_instances": nsucc,
                      "usd_per_validated_instance": round(run_cost / nval, 3) if nval else "", "usd_per_successful_instance": round(run_cost / nsucc, 3) if nsucc else "",
                      "note": "sum of cost_usd over every record of the batch, excluded ones included (diagnostic/block_w55.jsonl via mx_metrics)"})
    cost_rows.append({"item": f"Main run {b} health probes (estimate)", "batch": b, "records": nprobe, "cost_usd": probe_cost,
                      "cumulative_recorded_usd": "", "cumulative_incl_estimates_usd": cum_est, "validated_instances": "", "successful_instances": "",
                      "usd_per_validated_instance": "", "usd_per_successful_instance": "", "note": f"{nprobe} probes at about ${PROBE_USD} each; probe cost is not recorded"})
write(f"{MR}/COST_LEDGER.csv", cost_rows)

summary = {"rule": __doc__.split("Reads ")[0].strip(), "validated_instances_tested": N, "instances_with_shift": M,
           "shifted_runs": sh_n, "answered_runs": ans_n, "flagged_instances": [x["instance_id"] for x in inst_rows if not x["counted_in_kpi"]],
           "per_project": {k: {"tested": v[0], "with_shift": v[1]} for k, v in sorted(per_project.items())},
           "failure_modes_valid_runs": dict(modes), "excluded_records": sum(x["excluded_records"] for x in inst_rows),
           "timeouts": sum(x["timeouts"] for x in inst_rows), "run_cost_usd": round(sum(x["cost_usd"] for x in run_rows), 4),
           "cumulative_recorded_usd": cum_rec, "cumulative_incl_estimates_usd": cum_est, "probes": probes}
json.dump({"summary": summary, "instances": inst_rows}, open(f"{MR}/analysis/main_run_summary.json", "w"), indent=1)

NOTES = json.load(open(f"{MR}/analysis/diagnosis_notes.json")) if os.path.exists(f"{MR}/analysis/diagnosis_notes.json") else {}
for _f in sorted(glob.glob(f"{MR}/analysis/diagnosis_notes_batch*.json")):   # batch 4 on: notes in their own file, so the batch-1-3 notes stay frozen
    _b = os.path.basename(_f)[len("diagnosis_notes_"):-len(".json")]
    for _k, _v in json.load(open(_f)).items():   # only that batch's own keys; anything else is an error, never a silent addition
        assert _k in ("_about", "_" + _b) or batch_of.get("MR-" + _k) == _b, f"{_f}: key {_k} does not belong to {_b}"
        if _k != "_about": NOTES[_k] = _v
def section(x):
    rs = sorted([r for r in by[x["instance_id"]] if r["included"]], key=lambda r: runno(r["run"]))[:5]
    lines = [f"### {x['instance']} ({x['variant_id']}): {x['shifted_over_answered']} answered runs shifted",
             "", f"- Facade (entry point): `{x['facade']}`", f"- Gold: `{x['gold']}`",
             f"- Gold ranks by run: {x['gold_ranks']}; gold fault line displayed in {x['gold_exposed_runs']}/{x['valid_runs']} runs, "
             f"gold read in full in {x['full_gold_read_runs']}/{x['valid_runs']}", "", "| Run | Gold rank | Ranked first | Category | Failure mode | Tool calls | Wall s | Cost $ |", "|---|---|---|---|---|---|---|---|"]
    for r in rs:
        lines.append(f"| {r['run']} | {r['gold_rank'] if r['gold_rank'] is not None else 'no answer'} | `{r['rank1'] or '-'}` | {r['rank1_category']} | {r['failure_mode']} | {r['tool_calls']} | {r['wall_time_s']:.0f} | {r['cost_usd']:.3f} |")
    if NOTES.get(x["instance"]): lines += ["", f"Diagnosis (coordinator, hypothesis): {NOTES[x['instance']]}"]
    return "\n".join(lines) + "\n"

hdr = (f"Generated by `scripts/mr_report.py` from the frozen per-run measures (`analysis/per_run.json`). KPI rule: a run is a SHIFT when it "
       f"submitted a ranking and the gold is not ranked first; an instance succeeds when at least one of its first 5 valid runs shifts. "
       f"Failure modes are mechanical labels from frozen fields (rules in the script docstring), not blind-coded.\n")
succ = [x for x in inst_rows if x["instance_success"] and x["counted_in_kpi"]]
fail = [x for x in inst_rows if not x["instance_success"] and x["counted_in_kpi"]]
flag = [x for x in inst_rows if not x["counted_in_kpi"]]
with open(f"{MR}/SHIFTED_INSTANCES.md", "w") as f:
    f.write(f"# Shifted instances (at least one gpt-5.5 run ranks the gold below first)\n\n{hdr}\n**{M} of {N}** validated instances tested have at least one shifted run "
            f"({sh_n}/{ans_n} answered runs shifted).\n\n" + "".join(f"**Pattern across {b} (coordinator, hypothesis).** {NOTES['_' + b]}\n\n" for b in batches if NOTES.get('_' + b)) + "\n".join(section(x) for x in succ))
    if flag: f.write("\n## Flagged (ambiguous ownership): reported separately, not counted\n\n" + "\n".join(section(x) for x in flag))
    exc = [r for r in run_rows if not r["included"]]
    if exc:
        f.write("\n## Excluded records (not counted)\n\nExcluded by a frozen driver rule; each slot received its single replacement. The gold rank is the driver ledger's and is shown for transparency only.\n\n| Instance | Run | Driver verdict | Ledger gold rank |\n|---|---|---|---|\n")
        f.write("\n".join(f"| {r['instance_id'][3:]} | {r['run']} | {r['driver_verdict']} | {r['ledger_gold_rank']} |" for r in exc) + "\n")
with open(f"{MR}/FAILED_TO_TRANSFER.md", "w") as f:
    f.write(f"# Instances where the method did not transfer (every valid run ranks the gold first)\n\n{hdr}\n**{len(fail)} of {N}** validated instances tested.\n\n"
            + ("\n".join(section(x) for x in fail) if fail else "None in the batches run so far.\n"))
print(f"{N} validated instances tested; {M} with >=1 shift | shifted/answered runs {sh_n}/{ans_n} | per project {dict(summary['per_project'])}")
print("failure modes:", dict(modes), "| timeouts", summary["timeouts"], "| excluded records", summary["excluded_records"])
print(f"run cost ${summary['run_cost_usd']} | cumulative recorded ${cum_rec} | incl. estimates ${cum_est}")
for x in inst_rows: print(f"  {x['instance']:9s} {x['shifted_over_answered']:>5s} ranks [{x['gold_ranks']}] {x['failure_modes']} | ${x['cost_usd_all_records']}")
