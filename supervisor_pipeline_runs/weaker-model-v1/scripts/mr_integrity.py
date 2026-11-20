"""Main run, batch 3: protect batch-1 and batch-2 artefacts (main-run/BATCH3_PREREGISTRATION.md).
--record : write main-run/analysis/b12_integrity_manifest.json with sha256 of every batch-1/2 artefact.
--verify : recompute and report every mismatch (exit 1 on any mismatch).
Covered, for each batch-1/2 instance key (from main-run/batch1_tasks.json and batch2_tasks.json):
  instances/MR-<key>/** ; construction/mainrun/{specs/MR-<key>.json, designs/<key>.py, audits/MR-<key>.json} (if present) ;
  new_bug_variants/<P>/bug-<id>/L20/<variant>/** ; review/VARIANT_KEY.json entry ; plans/MR_batch1*.json, MR_batch2*.json ;
  driver-ledger lines of those plans ; analysis/per_run.json rows (tier MAIN_RUN) ; rows of main-run/MAIN_RUN_RUNS.csv,
  MAIN_RUN_RESULTS.csv, INSTANCE_BUILD_LOG.csv, INSTANCE_PROVENANCE.csv whose instance is batch 1/2."""
import csv, glob, hashlib, json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); WM = os.path.dirname(HERE); MR = f"{WM}/main-run"
BATCHES = sys.argv[sys.argv.index("--batches") + 1].split(",") if "--batches" in sys.argv else ["batch1", "batch2"]
OUT = f"{MR}/analysis/" + (sys.argv[sys.argv.index("--manifest") + 1] if "--manifest" in sys.argv else "b12_integrity_manifest.json")
PLANPAT = {"batch1": ["MR_batch1*.json"], "batch2": ["MR_batch2*.json"], "batch3": ["MR_batch3_*.json"], "batch4": ["MR_batch4_*.json"], "batch5": ["MR_batch5_*.json"],
           "batch6": ["MR_batch6_*.json"], "batch7": ["MR_batch7_*.json"], "batch8": ["MR_batch8_*.json"], "batch9": ["MR_batch9a_*.json", "MR_batch9b_*.json"]}   # batch 5 (W42); batch 6 and 7 (W51); batch 8 (W56)
sha = lambda b: hashlib.sha256(b).hexdigest()
fsha = lambda p: sha(open(p, "rb").read())
jsha = lambda o: sha(json.dumps(o, sort_keys=True).encode())

TASKFILE = lambda b: f"{MR}/bridge7_tasks.json" if b == "batch7" else f"{MR}/{b}_tasks.json"   # batch 7 (W53): the C10i task file

def keys():
    """[(task key, instance id)]: MR-<key> for static-facade tasks; MI-<fixture_key> for C10i tasks (<key>__i with fixture_key; batches 7 and 8, W53/W56)."""
    ks = []
    for b in BATCHES:
        ks += [(t["key"], f"MI-{t['fixture_key']}" if t.get("fixture_key") else f"MR-{t['key']}") for t in json.load(open(TASKFILE(b)))]
    return ks

def snapshot():
    kp = keys(); iid_of = dict(kp); iids = set(iid_of.values()); g = {}
    vkey = json.load(open(f"{WM}/review/VARIANT_KEY.json"))
    by_iid = {v["instance_id"]: (vid, v) for vid, v in vkey.items()}
    for k, iid in kp:
        for p in sorted(glob.glob(f"{WM}/instances/{iid}/**", recursive=True)):
            if os.path.isfile(p): g[os.path.relpath(p, WM)] = fsha(p)
        hist = sorted(os.path.relpath(p, WM) for p in glob.glob(f"{WM}/construction/mainrun/history/{k}/**", recursive=True) if os.path.isfile(p))
        for p in [f"construction/mainrun/specs/{iid}.json", f"construction/mainrun/designs/{k}.py", f"construction/mainrun/audits/{iid}.json"] + hist:
            if os.path.exists(f"{WM}/{p}"): g[p] = fsha(f"{WM}/{p}")
        if iid in by_iid:
            vid, v = by_iid[iid]; g[f"VARIANT_KEY[{vid}]"] = jsha(v)
            d = f"{WM}/new_bug_variants/{v['project']}/bug-{v['bug_id']}/L20/{vid}"
            for p in sorted(glob.glob(f"{d}/**", recursive=True)):
                if os.path.isfile(p): g[os.path.relpath(p, WM)] = fsha(p)
    plans = sorted(p for b in BATCHES for pat in PLANPAT[b] for p in glob.glob(f"{WM}/plans/{pat}"))
    psha = {}
    for p in plans: psha[fsha(p)] = p; g[os.path.relpath(p, WM)] = fsha(p)
    for n, l in enumerate(open(f"{WM}/diagnostic/block_w55.jsonl")):
        if l.strip() and json.loads(l).get("plan_sha256") in psha: g[f"ledger_line[{json.loads(l)['run']}]"] = sha(l.rstrip("\n").encode())
    for r in json.load(open(f"{WM}/analysis/per_run.json")):
        if r.get("instance_id") in iids: g[f"per_run[{r['variant_id']}/{r['run']}]"] = jsha(r)
    for f, col in (("MAIN_RUN_RUNS.csv", "instance_id"), ("MAIN_RUN_RESULTS.csv", "instance_id"), ("INSTANCE_BUILD_LOG.csv", "instance"), ("INSTANCE_PROVENANCE.csv", "instance"),
                   ("MAIN_RUN_C10F_RUNS.csv", "instance_id"), ("MAIN_RUN_C10F_RESULTS.csv", "instance_id"),   # batch 6 (W51): the C10f cell's files (mr2_report.py); no batch-1-5 instance has a row there
                   ("INSTANCE_BUILD_LOG_C10I.csv", "instance"), ("INSTANCE_PROVENANCE_C10I.csv", "instance"),   # batch 7 (W53): the C10i cell's files (mr3_build_records.py, mr3_report.py);
                   ("MAIN_RUN_C10I_RUNS.csv", "instance_id"), ("MAIN_RUN_C10I_RESULTS.csv", "instance_id")):    # their instance column is the task key <key>__i, mapped to MI-<key>
        if not os.path.exists(f"{MR}/{f}"): continue
        for r in csv.DictReader(open(f"{MR}/{f}")):
            name = r[col] if r[col].startswith(("MR-", "MI-")) else iid_of.get(r[col], f"MR-{r[col]}")
            if name in iids: g[f"{f}[{r[col]}|{r.get('run', '')}]"] = jsha(r)
    return g

def verify_frozen(path):
    """Batch 4 (W34): every file listed in a frozen-hash file must still have its recorded sha256."""
    spec = json.load(open(path)); fz = spec["sha256"]; bad = []
    for rel, h in sorted(fz.items()):
        p = f"{WM}/{rel}"
        if not os.path.exists(p) or fsha(p) != h: bad.append(rel)
    for rel, snap in sorted(spec.get("prefix_of", {}).items()):   # an append-only file must still begin with its pinned snapshot
        if not open(f"{WM}/{rel}", "rb").read().startswith(open(f"{WM}/{snap}", "rb").read()): bad.append(f"prefix:{rel}")
    print(json.dumps({"frozen_file": os.path.relpath(path, WM), "entries": len(fz) + len(spec.get("prefix_of", {})), "mismatches": len(bad), "first": bad[:20]}, indent=1))
    return bad

if __name__ == "__main__":
    if "--verify-frozen" in sys.argv:
        sys.exit(1 if verify_frozen(f"{MR}/analysis/" + sys.argv[sys.argv.index("--verify-frozen") + 1]) else 0)
    if "--record" in sys.argv:
        assert not os.path.exists(OUT), f"{OUT} exists; never re-record over it"
        g = snapshot(); json.dump(g, open(OUT, "w"), indent=1, sort_keys=True)
        print("recorded", len(g), "entries; manifest sha256", fsha(OUT))
    elif "--verify" in sys.argv:
        want = json.load(open(OUT)); have = snapshot()
        bad = sorted(k for k in set(want) | set(have) if want.get(k) != have.get(k))
        print(json.dumps({"entries": len(want), "mismatches": len(bad), "first": bad[:20]}, indent=1))
        sys.exit(1 if bad else 0)
