"""Stage B GPT-5.6 replication: does a chain-cell submission's evidence chain repeat the facade lie? Keyword scan (case-insensitive) of the
submitted evidence chain (fault-localization-submission.json; the agent's own output, no hidden field) for phrases distinctive of each bug's
lie sentence (construction/stageB/designs/B*_*.py "lie"). A crude indicator: it detects quotation or close paraphrase, not use.
Writes stageB-gpt56/lie_scan.json."""
import json, os, re
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
PHRASES = {"B1": [r"from its end", r"end towards", r"trailing run", r"forward pass", r"scann\w* backward", r"backward scan", r"scans? from the end"],
           "B3": [r"single pass over the series", r"running total", r"each series carr", r"extreme running"],
           "B4": [r"sorted in place", r"scanned once", r"run of equal values", r"longest run"]}
SV = json.load(open(f"{ROOT}/models/servers.json"))
PR = [r for r in json.load(open(f"{ROOT}/analysis/per_run.json")) if r.get("tier") == "STAGE_B" and r.get("included") and r["server"] in ("w55", "w56") and r["instance_id"].split("-")[-1] in ("C10", "C11")]
rows = []
for r in PR:
    bug = r["instance_id"].split("-")[1]
    p = f"{ROOT}/models/{r['server']}/benchmark_runs/{SV[r['server']]['agent_id']}/{r['variant_id']}/{r['run']}/fault-localization-submission.json"
    try: sub = json.load(open(p)); txt = json.dumps(sub.get("evidence_chain") or sub.get("submission", {}).get("evidence_chain") or sub)
    except Exception: txt = ""
    hits = [ph for ph in PHRASES[bug] if re.search(ph, txt, re.I)]
    rows.append({"server": r["server"], "run": f"{r['variant_id']}/{r['run']}", "instance": r["instance_id"], "acc1": r["acc1"], "lie_phrase_hits": hits})
summ = {}
for s in ("w55", "w56"):
    for ok in (True, False):
        rs = [x for x in rows if x["server"] == s and bool(x["acc1"]) == ok]
        summ[f"{s} {'correct' if ok else 'wrong'}"] = {"n": len(rs), "with_lie_phrase": sum(1 for x in rs if x["lie_phrase_hits"]), "runs": [x["run"] for x in rs if x["lie_phrase_hits"]]}
json.dump({"phrases": PHRASES, "summary": summ, "rows": rows}, open(f"{ROOT}/stageB-gpt56/lie_scan.json", "w"), indent=1)
print(json.dumps(summ, indent=1))
for x in rows:
    if x["lie_phrase_hits"]: print(x)
