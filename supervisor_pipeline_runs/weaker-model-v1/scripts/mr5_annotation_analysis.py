"""W72: join the two annotators' labels with the withheld sample key; agreement (raw, Cohen's kappa) and results per stratum.
Consensus = both annotators agree; otherwise 'disagree' (not adjudicated). Output: annotation/annotation_results.json, merged.csv."""
import csv, json, glob, os, collections
HERE = os.path.dirname(os.path.abspath(__file__)); A = f"{os.path.dirname(HERE)}/main-run/analysis/exposure_check/annotation"
key = {r["rid"]: r for r in csv.DictReader(open(f"{A}/sample_key.csv"))}
lab = {"A": {}, "B": {}}
for f in glob.glob(f"{A}/labels/*_batch*.json"):
    t = os.path.basename(f)[0]
    for x in json.load(open(f)): lab[t][x["rid"]] = x
assert set(lab["A"]) == set(lab["B"]) == set(key), "label sets incomplete"
def norm(v): return str(v).strip().upper()
def kappa(a, b):
    n = len(a); po = sum(x == y for x, y in zip(a, b)) / n
    ca, cb = collections.Counter(a), collections.Counter(b); pe = sum(ca[k] * cb[k] for k in set(ca) | set(cb)) / n / n
    return round((po - pe) / (1 - pe), 3) if pe < 1 else 1.0
R = {"n_runs": len(key)}
rows = []
for rid in sorted(key):
    k = key[rid]; a, b = lab["A"][rid], lab["B"][rid]
    row = {"rid": rid, **{c: k[c] for c in ("stratum", "instance_id", "run", "shift", "failure_mode", "rank1_category", "frozen_gold_exposed", "location_bound_exposed")}}
    for q in ("q1", "q2", "q3", "q4"):
        va, vb = norm(a.get(q)), norm(b.get(q)); row[f"{q}_A"], row[f"{q}_B"] = va, vb; row[q] = va if va == vb else "DISAGREE"
    rows.append(row)
for q in ("q1", "q2", "q3", "q4"):
    sel = [r for r in rows if not (q == "q4" and r["shift"] != "True")]
    R[f"agreement_{q}"] = {"n": len(sel), "raw": round(sum(r[f"{q}_A"] == r[f"{q}_B"] for r in sel) / len(sel), 3), "kappa": kappa([r[f"{q}_A"] for r in sel], [r[f"{q}_B"] for r in sel])}
def tab(sel, q): return dict(collections.Counter(r[q] for r in sel))
groups = {"D_frozen_only": [r for r in rows if r["stratum"] == "D" and r["frozen_gold_exposed"] == "True"],
          "D_location_only": [r for r in rows if r["stratum"] == "D" and r["frozen_gold_exposed"] == "False"],
          "A1_shifted_both": [r for r in rows if r["stratum"] == "A1"], "A2_goldfirst_both": [r for r in rows if r["stratum"] == "A2"],
          "A3_neither": [r for r in rows if r["stratum"] == "A3"]}
R["q1_by_group"] = {g: {"n": len(v), "consensus": tab(v, "q1")} for g, v in groups.items()}
R["q1_by_group_shift_split"] = {g: {s: tab([r for r in v if r["shift"] == s], "q1") for s in ("True", "False")} for g, v in groups.items()}
shifted = [r for r in rows if r["shift"] == "True"]; goldfirst = [r for r in rows if r["failure_mode"] == "GOLD_FIRST"]
R["q3_shifted"] = {"n": len(shifted), "consensus": tab(shifted, "q3")}
R["q3_shifted_q1yes"] = {"n": sum(r["q1"] == "YES" for r in shifted), "consensus": tab([r for r in shifted if r["q1"] == "YES"], "q3")}
R["q3_A1"] = {"n": len(groups["A1_shifted_both"]), "consensus": tab(groups["A1_shifted_both"], "q3"), "A": tab(groups["A1_shifted_both"], "q3_A"), "B": tab(groups["A1_shifted_both"], "q3_B")}
R["q3_goldfirst"] = {"n": len(goldfirst), "consensus": tab(goldfirst, "q3")}
R["q4_shifted"] = {"n": len(shifted), "consensus": tab(shifted, "q4"), "A": tab(shifted, "q4_A"), "B": tab(shifted, "q4_B")}
R["q4_shifted_facade_first"] = {"n": sum(r["rank1_category"] == "ENTRY_POINT" for r in shifted), "consensus": tab([r for r in shifted if r["rank1_category"] == "ENTRY_POINT"], "q4")}
R["q2_shifted"] = tab(shifted, "q2"); R["q2_goldfirst"] = tab(goldfirst, "q2")
with open(f"{A}/merged.csv", "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
json.dump(R, open(f"{A}/annotation_results.json", "w"), indent=1); print(json.dumps(R, indent=1))
