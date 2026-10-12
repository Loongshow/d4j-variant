"""Screening matrix (one row per instance) from the frozen per-run measures. Run after mx_metrics.py.
Usage: mx_screen_report.py  -> MECHANISM_SCREENING_MATRIX.csv, analysis/screening/family_summary.json
Blocks come from the ledger's plan_sha256 (plans/*.json hashed); S2_cont rows count as S2. Excluded runs (non-valid ledger verdicts:
contamination, integrity, infrastructure) are counted per instance but never scored. analysis/validity_overrides.json marks instances
whose gold is invalid (class INVALID, excluded from family conclusions) or that carry a caveat. The screening class is the
pre-registered rule as computed by mx_metrics.py (summary_by_instance.json); this script only adds blocks, exclusions and validity."""
import json, os, sys, glob, csv, hashlib, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ct_lib as C
MX = C.V3
h = lambda p: hashlib.sha256(open(p, "rb").read()).hexdigest()
plans = {h(p): os.path.basename(p)[:-5] for p in glob.glob(f"{MX}/plans/*.json")}
BLOCK = {"S2_cont": "S2"}
ledger = [json.loads(l) for l in open(f"{MX}/diagnostic/block_mxF0.jsonl")]
key = json.load(open(f"{MX}/review/VARIANT_KEY.json"))
summ = {s["instance_id"]: s for s in json.load(open(f"{MX}/analysis/summary_by_instance.json"))}
over = json.load(open(f"{MX}/analysis/validity_overrides.json")) if os.path.exists(f"{MX}/analysis/validity_overrides.json") else {}
prov = {r["iid"]: r for r in csv.DictReader(open(f"{MX}/INSTANCE_PROVENANCE.csv"))}
# last record per run (a release row supersedes)
last = {}
for r in ledger: last[r["run"]] = r
blocks = collections.defaultdict(set); excluded = collections.defaultdict(list)
for run, r in last.items():
    v = run.split("/")[0]; iid = key.get(v, {}).get("instance_id")
    if not iid: continue
    b = plans.get(r.get("plan_sha256"), "?"); b = BLOCK.get(b, b); blocks[iid].add(b)
    if r["verdict"] != "valid": excluded[iid].append(f"{run}:{r['verdict']}")
rows = []
for iid in sorted(set(summ) | set(excluded)):
    s = summ.get(iid, {}); k = next((x for x in key.values() if x["instance_id"] == iid), {}); o = over.get(iid, {})
    cls = "INVALID" if o.get("invalid") else s.get("screening_class", "")
    rows.append({"iid": iid, "variant_id": s.get("variant_id") or next((v for v, x in key.items() if x["instance_id"] == iid), ""),
                 "mechanism": k.get("mechanism"), "tags": "|".join(k.get("tags") or []), "project": k.get("project"), "tier": k.get("tier"),
                 "kind": (prov.get(iid) or {}).get("kind", ""), "parent_iid": (prov.get(iid) or {}).get("parent_iid", ""),
                 "block": "+".join(sorted(blocks.get(iid, []))), "n_valid": s.get("n", 0), "n_excluded": len(excluded[iid]),
                 "excluded_runs": ";".join(excluded[iid]), "acc1": s.get("acc1"), "mrr": s.get("mrr"),
                 "gold_ranks": " ".join(str(x) for x in s.get("gold_ranks", [])), "rank1_categories": " ".join(s.get("rank1_categories", [])),
                 "gold_exposed": s.get("gold_exposed"), "gold_exposed_misranked": s.get("gold_exposed_misranked"),
                 "most_common_wrong_top": s.get("most_common_wrong_top") or "", "same_wrong_count": s.get("same_wrong_count"),
                 "full_gold_read": s.get("full_gold_read"), "tests_executed": s.get("tests_executed"), "cost_usd": s.get("cost_usd"),
                 "screening_class": cls, "validity": o.get("flag", ""), "validity_note": o.get("note", "")})
cols = list(rows[0].keys())
with open(f"{MX}/MECHANISM_SCREENING_MATRIX.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=cols); w.writeheader(); w.writerows(rows)
# family summary over screening instances (S1/S2; P4 diagnostics and HELDOUT reported separately)
fam = collections.defaultdict(lambda: {"instances": [], "classes": [], "n": 0, "correct": 0})
order = {"PROMISING": 3, "WEAK": 2, "NULL": 1, "INVALID": 0, "": 0}
for r in rows:
    if r["block"] not in ("S1", "S2") or r["screening_class"] == "INVALID": continue
    F = fam[r["mechanism"]]; F["instances"].append(r["iid"]); F["classes"].append(r["screening_class"])
    F["n"] += r["n_valid"] or 0; F["correct"] += round((r["acc1"] or 0) * (r["n_valid"] or 0))
for m, F in fam.items():
    F["family_class"] = max(F["classes"], key=lambda c: order[c]); F["pooled_acc1"] = round(F["correct"] / F["n"], 3) if F["n"] else None
os.makedirs(f"{MX}/analysis/screening", exist_ok=True)
json.dump(dict(sorted(fam.items())), open(f"{MX}/analysis/screening/family_summary.json", "w"), indent=1)
print(f"{len(rows)} instance rows -> MECHANISM_SCREENING_MATRIX.csv; {len(fam)} screening families")
for m, F in sorted(fam.items(), key=lambda x: (x[1]['pooled_acc1'] if x[1]['pooled_acc1'] is not None else 9)):
    print(f"  {m:12s} {F['family_class']:9s} pooled Acc@1 {F['pooled_acc1']} (n {F['n']}, {len(F['instances'])} inst)")
