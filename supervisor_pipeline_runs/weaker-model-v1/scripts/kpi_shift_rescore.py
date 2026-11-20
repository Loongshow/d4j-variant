"""Re-score every existing instance with the supervisor's KPI (meeting of 2026-10-16):
  "number of Defects4J bug instances where we can shift the gold method down in the rankings";
  5 runs per instance; an instance counts as a success if at least 1 run shows the gold shifted down.
Operational rule used here (stated so it can be changed): a run "shifts the gold down" when it submitted a ranking and the gold is
not ranked first (gold_rank >= 2, or absent from the top 10). Runs without a ranking (timeouts, no answer) are counted separately
and never count as a shift. Only the first 5 valid behavioural runs of an instance (by run number) are used; sets run with fewer
than 5 runs per instance are scored on the runs they have and labelled as such.
Reads: analysis/per_run.json (this root), ../mechanism-search-v1/analysis/per_run.json, ../mechanism-search-v1/mining/run_data.json.
Writes: kpi-shift/kpi_rescore.json. Read-only otherwise."""
import json, os, re
from collections import defaultdict
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); RUNS = os.path.dirname(ROOT)
os.makedirs(f"{ROOT}/kpi-shift", exist_ok=True)
runno = lambda s: int(re.search(r"run-(\d+)", s).group(1))

ABSENT = 11   # an answered run whose ranking omits the gold: rank = list length + 1 (top-10 lists)
def score(runs):
    """runs: list of (run_number, answered, gold_rank or None). Uses the first 5 by run number.
    Revision after the independent recount (2026-10-16): an answered run with gold_rank None means the gold is absent from the
    submitted ranking and counts as SHIFTED (rank 11); only runs that did not answer are no-answers."""
    first = sorted(runs)[:5]
    ranks = [(g if g is not None else ABSENT) for _, a, g in first if a]
    return {"runs_used": len(first), "answered": len(ranks), "no_answer": len(first) - len(ranks),
            "shifted_runs": sum(1 for g in ranks if g != 1), "success": any(g != 1 for g in ranks),
            "gold_ranks": [(g if g is not None else (ABSENT if a else None)) for _, a, g in first]}

sets = defaultdict(dict)   # set name -> instance -> score
# NEW-R4-M4 is INVALID (mechanism-search-v1 X1: its gold class ends in 'Test', so the validator rejects a gold-first answer)
INVALID = {"NEW-R4-M4"}
CTRL = "Sept. no-chain controls, 0-2 hops (GPT-5.6, pre-freeze)"
HOPS = "Sept. 5-6-hop treatments, approx. hops only (GPT-5.6, pre-freeze)"
PIE = "Sept. chain + odd-looking hop + ownership split (GPT-5.6, pre-freeze)"
meta = {}
# 1. this root: Stage B (w55, w56), held-out (w50, w55), Stage A (w55 REHOSTED_FROZEN + EXPLORATORY)
for r in json.load(open(f"{ROOT}/analysis/per_run.json")):
    if not r.get("included"): continue
    s, t, iid = r["server"], r["tier"], r["instance_id"]
    model = {"w50": "gpt-5", "w55": "gpt-5.5", "w56": "GPT-5.6"}.get(s)
    if t == "STAGE_B":
        cell = iid.split("-")[-1]; key = f"Stage B {cell} ({model})"
    elif t == "HELDOUT": key = f"Held-out set ({model})"
    elif t in ("REHOSTED_FROZEN", "EXPLORATORY") and s == "w55":
        key = "Stage A control (gpt-5.5)" if "CONTROL" in iid else "Stage A breakers (gpt-5.5)"
    else: continue
    sets[key].setdefault(iid, []).append((runno(r["run"]), bool(r.get("answered")), r["gold_rank"]))
# 2. mechanism-search-v1 (GPT-5.6, mxF0): held-out and exploratory screening (3 runs per instance)
for r in json.load(open(f"{RUNS}/mechanism-search-v1/analysis/per_run.json")):
    if not r.get("included") or r["instance_id"] in INVALID: continue
    key = "Held-out set (GPT-5.6, mechanism-search-v1 reference)" if r["tier"] == "HELDOUT" else "Mechanism screening (GPT-5.6, 3 runs each)"
    sets[key].setdefault(r["instance_id"], []).append((runno(r["run"]), bool(r.get("answered")), r["gold_rank"]))
# 3. September GPT-5.6 matched pairs (diagnostic-noncanonical-v3): CONTROL arms, hops-only TREATMENT arms, and the odd-hop treatment
for r in json.load(open(f"{RUNS}/mechanism-search-v1/mining/run_data.json")):
    if r["family"] != "diagnostic-noncanonical-v3" or r["status_kind"] != "behavioural": continue
    v = r["variant"]
    if "CONTROL" in v: key = CTRL
    elif "TREATMENT" in v and v == "CHART-PIE-TREATMENT-03": key = PIE
    elif "TREATMENT" in v and (r.get("search_depth_hops") or 0) >= 5: key = HOPS
    else: continue
    sets[key].setdefault(v, []).append((runno(r["run_dir"]), bool(r.get("answered")), r["gold_rank"]))
    meta[v] = r.get("search_depth_hops")
out = {}
for key, inst in sets.items():
    sc = {i: score(v) for i, v in inst.items()}
    out[key] = {"instances": len(sc), "instances_with_5_runs": sum(1 for x in sc.values() if x["runs_used"] >= 5),
                "successes": sum(1 for x in sc.values() if x["success"]), "successful_instances": sorted(i for i, x in sc.items() if x["success"]),
                "runs_used": sum(x["runs_used"] for x in sc.values()), "shifted_runs": sum(x["shifted_runs"] for x in sc.values()),
                "no_answer_runs": sum(x["no_answer"] for x in sc.values()), "per_instance": sc}
NOTES = {HOPS: "Approximate hops-only: several treatments also change non-hop features (CMP-LAYOUT adds an ownership split, ambiguity and a decoy cue; CONVERSION-DISPATCH and -BRANCH add dispatch; CMP-CKSUM, JKC-OFFSET and MATH-NORM carry an odd-looking correct hop). Three treatments (CONVERSION LONG, DISPATCH, BRANCH) share one fault. Gold differs from the control's gold.",
         CTRL: "Hop depth 0 (6 arms), 1 (9), 2 (1), unannotated (1); in 9 of 17 the gold is the method the test calls.",
         "Mechanism screening (GPT-5.6, 3 runs each)": "3 runs per instance, fewer than the KPI's 5; NEW-R4-M4 (invalid) excluded.",
         "Stage A breakers (gpt-5.5)": "Selected because GPT-5.6 missed them; 4 of 7 have 3 runs."}
for k in out: out[k]["note"] = NOTES.get(k, "")
json.dump({"rule": __doc__.split("Reads:")[0].strip(), "sets": out, "hops": meta}, open(f"{ROOT}/kpi-shift/kpi_rescore.json", "w"), indent=1)
order = [CTRL, HOPS, PIE] + \
        [f"Stage B {c} ({m})" for m in ("gpt-5.5", "GPT-5.6") for c in ("C00", "C01", "C10", "C11")] + \
        ["Stage A breakers (gpt-5.5)", "Stage A control (gpt-5.5)", "Mechanism screening (GPT-5.6, 3 runs each)",
         "Held-out set (gpt-5)", "Held-out set (gpt-5.5)", "Held-out set (GPT-5.6, mechanism-search-v1 reference)"]
for k in out: out[k]["note"] = NOTES.get(k, "")
print(f"{'set':58s} {'inst':>4s} {'5runs':>5s} {'success':>7s} {'shifted/runs':>13s} {'no-ans':>6s}  successful instances")
for k in order:
    if k not in out: continue
    v = out[k]; print(f"{k:58s} {v['instances']:4d} {v['instances_with_5_runs']:5d} {v['successes']:7d} {v['shifted_runs']:>6d}/{v['runs_used']:<6d} {v['no_answer_runs']:6d}  {', '.join(v['successful_instances'])}")
