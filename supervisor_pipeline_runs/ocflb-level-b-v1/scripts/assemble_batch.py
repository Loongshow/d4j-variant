#!/usr/bin/env python
"""Split a batch grading journal into per-pair grader_results.json files and assemble verdicts. Usage: assemble_batch.py <journal.jsonl>"""
import json, sys, subprocess, collections, os
L = "/Users/shawnli/Desktop/Honours/defects4j/supervisor_pipeline_runs/ocflb-level-b-v1"; by = collections.defaultdict(list)
for l in open(sys.argv[1]):
    e = json.loads(l)
    if e.get("type") == "result" and isinstance(e.get("result"), dict) and "packet" in e["result"]: by[e["result"]["pair"]].append(e["result"])
for pair, res in by.items():
    pd = f"{L}/projects/{pair}"; os.makedirs(f"{pd}/blindness", exist_ok=True); json.dump(res, open(f"{pd}/blindness/grader_results.json", "w"), indent=1)
    subprocess.run(["/opt/miniconda3/bin/python", f"{L}/scripts/assemble_blindness.py", f"{pd}/blindness/grader_results.json", pd])
