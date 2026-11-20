"""Regenerate COST_LEDGER.csv and INSTANCE_PROVENANCE.csv from primary records. Run after mx_screen_report.py.
COST_LEDGER: one row per (server, plan): runs attempted and valid and their summed cost from the driver ledgers (block_<server>.jsonl,
last record per run); health probes counted from the driver logs (lines 'probe:' while that plan was active) and costed at an ESTIMATE
of USD 0.008 each (the cue-trust-v3 pilot's probe residual; probe records carry no cost). The stand-in row is kept.
INSTANCE_PROVENANCE: existing rows keep their hand-written fields; every key instance without a row is added from its spec; the
screening_class and first_behavioural_run columns are refreshed from MECHANISM_SCREENING_MATRIX.csv and the ledger."""
import json, os, sys, glob, csv, hashlib, re, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ct_lib as C
MX = C.V3; PROBE_USD = 0.008
h = lambda p: hashlib.sha256(open(p, "rb").read()).hexdigest()
plans = {h(p): os.path.relpath(p, MX) for p in glob.glob(f"{MX}/plans/*.json")}
key = json.load(open(f"{MX}/review/VARIANT_KEY.json")); iid_of = {v: k["instance_id"] for v, k in key.items()}
BLOCK = {"plans/smoke.json": "smoke", "plans/S1.json": "S1", "plans/S2.json": "S2", "plans/S2_cont.json": "S2 (continuation)", "plans/P4.json": "P4 diagnostics", "plans/HO.json": "HO held-out", "plans/HO_cont.json": "HO held-out (continuation)", "plans/HO_top.json": "HO held-out (top-up)"}
rows = []; first_run = {}
for lf in sorted(glob.glob(f"{MX}/diagnostic/block_*.jsonl")):
    server = os.path.basename(lf)[6:-6]
    last = {}
    for l in open(lf):
        r = json.loads(l); last[r["run"]] = r
    by = collections.defaultdict(list)
    for run, r in last.items():
        by[plans.get(r.get("plan_sha256"), "?")].append(r)
        i = iid_of.get(run.split("/")[0])
        if i and r["verdict"] == "valid": first_run[i] = min(first_run.get(i, r["checked_at"]), r["checked_at"])
    probes = collections.Counter(); cur = None
    log = f"{MX}/diagnostic/driver_{server}.log"
    for l in open(log, errors="replace") if os.path.exists(log) else []:
        m = re.search(r"plan (plans/\S+\.json) bound to", l)
        if m: cur = m.group(1)
        if "  probe:" in l and cur: probes[cur] += 1
    for p in sorted(set(by) | set(probes)):
        rs = by.get(p, []); runcost = sum(float(r.get("cost_usd") or 0) for r in rs)
        mech = sorted({key[r["run"].split("/")[0]]["mechanism"] for r in rs if r["run"].split("/")[0] in key})
        rows.append({"_t": min((r["checked_at"] for r in rs), default="9"), "date_utc": (min((r["checked_at"] for r in rs), default="") or "")[:10], "block": BLOCK.get(p, p), "plan": p, "server": server,
                     "runs_attempted": len(rs), "runs_valid": sum(r["verdict"] == "valid" for r in rs),
                     "cost_usd": round(runcost + probes[p] * PROBE_USD, 4), "mechanism": "|".join(m for m in mech if m),
                     "instance": f"{len({r['run'].split('/')[0] for r in rs})} variants",
                     "notes": f"runs USD {runcost:.4f} (ledger) + {probes[p]} health probes x USD {PROBE_USD} (estimate)"
                              + ("; excluded: " + ", ".join(f"{r['run']} {r['verdict']}" for r in rs if r["verdict"] != "valid") if any(r["verdict"] != "valid" for r in rs) else "")})
rows.sort(key=lambda r: r["_t"])
old = list(csv.DictReader(open(f"{MX}/COST_LEDGER.csv")))
stand = [r for r in old if r["block"] == "stand-in proof"]
cum = 0.0; out = []
for r in stand + [r for r in rows if r["server"] != "mxStub"]:
    cum += float(r["cost_usd"]); r["cumulative_usd"] = round(cum, 4); out.append(r)
cols = ["date_utc", "block", "plan", "server", "runs_attempted", "runs_valid", "cost_usd", "cumulative_usd", "mechanism", "instance", "notes"]
with open(f"{MX}/COST_LEDGER.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore"); w.writeheader(); w.writerows(out)
print(f"COST_LEDGER: {len(out)} rows, cumulative USD {cum:.2f}")
# provenance
pp = f"{MX}/INSTANCE_PROVENANCE.csv"; prov = list(csv.DictReader(open(pp))); pcols = list(prov[0].keys()); have = {r["iid"] for r in prov}
mat = {r["iid"]: r for r in csv.DictReader(open(f"{MX}/MECHANISM_SCREENING_MATRIX.csv"))} if os.path.exists(f"{MX}/MECHANISM_SCREENING_MATRIX.csv") else {}
for v, k in sorted(key.items(), key=lambda x: x[1]["instance_id"]):
    i = k["instance_id"]
    if i in have: continue
    sp = json.load(open(f"{MX}/instances/{i}/spec.json")) if os.path.exists(f"{MX}/instances/{i}/spec.json") else {}
    kind = sp.get("kind", "new"); br = f"{MX}/instances/{i}/builder_report.json"
    prov.append({"iid": i, "variant_id": v, "mechanism": k.get("mechanism"), "tags": "|".join(k.get("tags") or []), "project": k.get("project"),
                 "tier": k.get("tier"), "kind": kind, "prototype_of": "", "revision": str(sp.get("revision", 0)), "parent_iid": sp.get("parent_iid", ""),
                 "source": ("derived revision (scripts/mx_derive.py) of " + sp.get("parent_iid", "")) if kind == "derived" else
                           ("recipe build by an independent builder agent (scripts/mx_build_validate.py)" if os.path.exists(br) else "scripts/mx_build_validate.py"),
                 "built_from_recipe": "n/a" if kind == "derived" else (sp.get("recipe") or (i.split("-")[1] if i.startswith("NEW-R") else "n/a")),
                 "first_behavioural_run": "", "screening_class": "", "notes": (sp.get("purpose") or "")[:300]})
for r in prov:
    i = r["iid"]
    if i in first_run: r["first_behavioural_run"] = first_run[i]
    if i in mat: r["screening_class"] = mat[i]["screening_class"]
    if r.get("tier") == "HELDOUT" and i in mat:   # confirmation instances: record held-out accuracy, not a screening class
        n = int(mat[i]["n_valid"] or 0); k = round(float(mat[i]["acc1"] or 0) * n)
        r["screening_class"] = f"HELDOUT Acc@1 {k}/{n}"
with open(pp, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=pcols); w.writeheader(); w.writerows(prov)
print(f"INSTANCE_PROVENANCE: {len(prov)} rows")
