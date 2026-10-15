"""Stage B, GPT-5.6 replication: final failure-mode labels for the GPT-5.6 misses (set 2) and a cross-model tally against gpt-5.5.
Final label rule, as for the gpt-5.5 blocks: the adjudicator's decision where the two blind lenses disagreed on primary, secondary or
defensibility; otherwise the agreed values. Reads analysis/failure_modes/labels_set2_block*_raw.json (workflow outputs, GPT-5.6) and
analysis/failure_modes/labels_block{1,2}_final.json (gpt-5.5), plus analysis/per_run.json for frozen measures of each miss.
Writes analysis/failure_modes/labels_set2_final.json and stageB-gpt56/cross_model_labels.json."""
import json, os, glob, collections
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); FM = f"{ROOT}/analysis/failure_modes"
PR = {(r["server"], f"{r.get('variant_id')}/{r['run']}"): r for r in json.load(open(f"{ROOT}/analysis/per_run.json")) if r.get("tier") == "STAGE_B" and r.get("included")}
CELL = lambda iid: iid.split("-")[-1]
# GPT-5.6 finals
fin56 = []
for f in sorted(glob.glob(f"{FM}/labels_set2_block*_raw.json")):
    for r in json.load(open(f))["labels"]:
        p, a, adj = r["process"], r["argument"], r.get("adjudication")
        src = "adjudicated" if adj else "agreed"; base = adj or p
        pr = PR[("w56", r["run"])]
        fin56.append({"run_id": r["run"], "instance_id": pr["instance_id"], "cell": CELL(pr["instance_id"]), "project": pr["project"],
                      "final": {"primary": base["primary"], "secondary": base["secondary"], "defensible": base["defensible"], "source": src},
                      "gold_named_in_chain": "yes" if p["gold_named_in_chain"] == a["gold_named_in_chain"] == "yes" else ("split" if p["gold_named_in_chain"] != a["gold_named_in_chain"] else "no"),
                      "divergence_located_at_gold": (adj or {}).get("divergence_located_at_gold") or (p["divergence_located_at_gold"] if p["divergence_located_at_gold"] == a["divergence_located_at_gold"] else "split"),
                      "lie_cited": p["lie_cited"] if p["lie_cited"] == a["lie_cited"] else "split",
                      "rank1": (pr.get("rank1") or "").split("::")[-1], "gold_rank": pr["gold_rank"], "frozen_split": None,
                      "frozen": {k: pr.get(k) for k in ("gold_exposed", "full_gold_read", "evidence_displayed", "failure_values_seen", "independent_probe_executed", "tool_calls", "rank1_category")}})
json.dump({"server": "w56", "rule": "adjudicator where the lenses disagreed on primary/secondary/defensibility, else agreed", "final": fin56},
          open(f"{FM}/labels_set2_final.json", "w"), indent=1)
# gpt-5.5 finals
fin55 = []
for f in (f"{FM}/labels_block1_final.json", f"{FM}/labels_block2_final.json"):
    for r in json.load(open(f))["final"]:
        pr = PR[("w55", r["run_id"])]
        fin55.append({**r, "divergence_located_at_gold": r.get("divergence_located_at_gold") or r["final"].get("divergence_located_at_gold"), "project": pr["project"],
                      "frozen": {k: pr.get(k) for k in ("gold_exposed", "full_gold_read", "evidence_displayed", "failure_values_seen", "independent_probe_executed", "tool_calls", "rank1_category")}})
def tally(rows):
    C = lambda f: dict(collections.Counter(f(r) for r in rows))
    return {"n": len(rows), "primary": C(lambda r: r["final"]["primary"]), "secondary": C(lambda r: r["final"]["secondary"]), "defensible": C(lambda r: r["final"]["defensible"]),
            "gold_named": C(lambda r: r["gold_named_in_chain"]), "divergence_at_gold": C(lambda r: r["divergence_located_at_gold"]), "by_cell": C(lambda r: r["cell"]), "by_project": C(lambda r: r["project"]),
            "rank1": C(lambda r: r["rank1"]), "frozen_rank1_category": C(lambda r: r["frozen"]["rank1_category"]), "gold_rank": C(lambda r: r["gold_rank"]),
            "frozen_gold_exposed": C(lambda r: r["frozen"]["gold_exposed"]), "frozen_full_gold_read": C(lambda r: r["frozen"]["full_gold_read"]),
            "frozen_evidence_displayed": C(lambda r: r["frozen"]["evidence_displayed"]), "frozen_failure_values_seen": C(lambda r: r["frozen"]["failure_values_seen"]),
            "frozen_independent_probe": C(lambda r: r["frozen"]["independent_probe_executed"]), "lie_cited": C(lambda r: r.get("lie_cited", "not_recorded")),
            "agreement": C(lambda r: r["final"].get("source"))}
out = {"gpt-5.5": tally(fin55), "GPT-5.6": tally(fin56), "gpt55_runs": [r["run_id"] for r in fin55], "gpt56_runs": [r["run_id"] for r in fin56]}
json.dump(out, open(f"{ROOT}/stageB-gpt56/cross_model_labels.json", "w"), indent=1)
print(json.dumps({k: out[k] for k in ("gpt-5.5", "GPT-5.6")}, indent=1))
