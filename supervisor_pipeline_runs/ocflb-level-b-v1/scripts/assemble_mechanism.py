#!/usr/bin/env python
"""Merge mechanism-grading workflow journals into analysis/mechanism/mechanism_grading.json (keyed by packet; later batches add, never overwrite
an existing packet verdict) and write analysis/MECHANISM_GRADING.md. Usage: assemble_mechanism.py <journal.jsonl> [...]"""
import json, sys, os, collections
L = "/Users/shawnli/Desktop/Honours/defects4j/supervisor_pipeline_runs/ocflb-level-b-v1"; out = f"{L}/analysis/mechanism/mechanism_grading.json"
db = json.load(open(out)) if os.path.exists(out) else {}
for J in sys.argv[1:]:
    by = collections.defaultdict(list)
    for l in open(J):
        e = json.loads(l)
        if e.get("type") != "result": continue
        r = e.get("result")
        if isinstance(r, dict) and "mechanism" in r and "packet" in r: by[r["packet"]].append(r)
        elif isinstance(r, list):
            for x in r:
                if isinstance(x, dict) and "final" in x and x["packet"] not in db: db[x["packet"]] = x
    for pk, gs in by.items():
        if pk in db: continue
        gs = sorted(gs, key=lambda g: g["grader"]); g12 = [g for g in gs if g["grader"] in (1, 2)]; g3 = [g for g in gs if g["grader"] == 3]
        if len(g12) == 2 and g12[0]["mechanism"] == g12[1]["mechanism"]: db[pk] = {"packet": pk, "graders": gs, "final": g12[0]["mechanism"], "agreement": True}
        elif g3: db[pk] = {"packet": pk, "graders": gs, "final": g3[-1]["mechanism"], "agreement": False}
        elif g12: db[pk] = {"packet": pk, "graders": gs, "final": g12[0]["mechanism"], "agreement": False, "note": "no adjudication recorded"}
json.dump(db, open(out, "w"), indent=1)
rows = {r["variant_id"] + "/" + r["run"] + "/" + r["model"]: r for r in json.load(open(f"{L}/analysis/per_run/run_metrics.json"))}
M = ["# Mechanism grading of answered wrong runs (two blinded graders per run; a third adjudicates disagreements)", "", "Primary mechanism per run: LOCAL_ODDNESS (the blamed hop's body looked wrong under an assumed convention), DEPTH_PRIOR (blamed by position), EXTERNAL_EVIDENCE_NOT_RETRIEVED (trace-based choice, no oddness claim, no evidence opened), EXTERNAL_EVIDENCE_MISREAD (evidence opened, still wrong), OFF_CHAIN_ERROR, OTHER. The automatic class (who was blamed) comes from `ocflb_metrics.py`.", "",
     "| Model | Pair | Arm | Run | Gold rank | Automatic class | Graded mechanism | Agreement | Evidence seen (graders) | Assumed convention (grader 1) |", "|" + "---|" * 10]
cnt = collections.Counter()
for pk, v in sorted(db.items()):
    model, vid, run = pk.replace(".md", "").split("__"); r = rows.get(f"{vid}/{run}/{model}", {})
    g1 = v["graders"][0] if v["graders"] else {}
    cnt[(model, r.get("arm"), v["final"])] += 1
    M.append(f"| {model} | `{r.get('pair_id')}` | {r.get('arm')} | {run} | {r.get('gold_rank')} | {r.get('classification')} | **{v['final']}** | {'yes' if v['agreement'] else 'adjudicated'} | {[g.get('external_evidence_seen_in_trajectory') for g in v['graders']]} | {(g1.get('assumed_convention') or '')[:140]} |")
M += ["", "## Counts", "", "| Model | Arm | Mechanism | Runs |", "|---|---|---|---|"] + [f"| {m} | {a} | {k} | {n} |" for (m, a, k), n in sorted(cnt.items(), key=lambda x: (x[0][0], str(x[0][1]), x[0][2]))]
open(f"{L}/analysis/MECHANISM_GRADING.md", "w").write("\n".join(M) + "\n"); print(len(db), "graded runs;", dict(cnt))
