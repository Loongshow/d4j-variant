"""Main run, batch 3: the pre-registered cost guard (main-run/BATCH3_PREREGISTRATION.md).
C = pre-main-run total including estimates ($66.25, root COST_LEDGER.csv before W24)
    + sum of cost_usd over every driver-ledger record (diagnostic/block_w55.jsonl) whose plan is a main-run plan (plans/MR_*.json)
    + $0.008 x health probes counted in the main-run driver logs (diagnostic/run_MR_*.out; every 'probe: ' line, hangs included).
M = highest single-run cost_usd among those main-run ledger records.
k = the largest integer <= min(5, left) with  C + 10k*M + (120k + 12)*0.008 <= 147.00.
    10k = 5k slots x at most 2 runs (one replacement) under the frozen driver; 120k + 12 = the frozen driver's worst-case probe count
    (3-probe gates after every non-valid attempt, each gate tolerating 5 resetting failures). Re-run before every driver (re)start.
Safety check: fails (exit 2) if any ledger record written after the first main-run record belongs to no plans/MR_*.json plan,
since such spend would be missing from C. Batch-3 plans must be named plans/MR_batch3_*.json (driver log run_MR_batch3_*.out).
Batch 4 (W34): --cap 199.00 for the user's $200 ceiling (same $1 margin); default 147.00 keeps the batch-3 behaviour.
Read-only. Usage: mr_cost_guard.py [--left N] [--cap X]   -> prints C, M and k (JSON)"""
import glob, hashlib, json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); WM = os.path.dirname(HERE)
PRE = 66.25; PROBE = 0.008
CAP = float(sys.argv[sys.argv.index("--cap") + 1]) if "--cap" in sys.argv else 147.00
mr_plans = {hashlib.sha256(open(p, "rb").read()).hexdigest(): os.path.basename(p) for p in glob.glob(f"{WM}/plans/MR_*.json")}
LEDGERS = sorted(os.path.basename(p) for p in glob.glob(f"{WM}/diagnostic/block_*.jsonl"))   # W34: spend on any other server must not escape C
if LEDGERS != ["block_w50.jsonl", "block_w55.jsonl", "block_w56.jsonl", "block_wmDiag.jsonl"]:
    print(json.dumps({"ERROR": "unexpected set of server ledgers", "ledgers": LEDGERS})); sys.exit(2)
allrecs = [json.loads(l) for l in open(f"{WM}/diagnostic/block_w55.jsonl") if l.strip()]
first = min(i for i, r in enumerate(allrecs) if r.get("plan_sha256") in mr_plans)
stray = [r.get("run") for r in allrecs[first:] if r.get("plan_sha256") not in mr_plans]
if stray: print(json.dumps({"ERROR": "ledger records after the main run began that belong to no MR plan", "runs": stray[:10]})); sys.exit(2)
recs = [r for r in allrecs if r.get("plan_sha256") in mr_plans]
run_cost = sum(float(r.get("cost_usd") or 0) for r in recs)
M = max(float(r.get("cost_usd") or 0) for r in recs)
probes = sum(sum(1 for l in open(f) if "probe: " in l) for f in glob.glob(f"{WM}/diagnostic/run_MR_*.out"))
C = PRE + run_cost + PROBE * probes
left = int(sys.argv[sys.argv.index("--left") + 1]) if "--left" in sys.argv else 5
k = 0
for cand in range(min(5, left), 0, -1):
    if C + 10 * cand * M + (120 * cand + 12) * PROBE <= CAP: k = cand; break
print(json.dumps({"C": round(C, 4), "M": round(M, 6), "main_run_records": len(recs), "main_run_run_cost": round(run_cost, 4),
                  "main_run_probes": probes, "cap": CAP, "left": left, "k": k, "worst_case_after_block": round(C + 10 * k * M + (120 * k + 12) * PROBE, 4) if k else None,
                  "plans": sorted(set(mr_plans.values()))}, indent=1))
