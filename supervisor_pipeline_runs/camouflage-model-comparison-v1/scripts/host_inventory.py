#!/usr/bin/env python
"""Rank every .java file in a source tree by LOC and declared-method count, so LOW
and HIGH camouflage hosts can be chosen on measured size rather than impression.
Usage: host_inventory.py <src-dir> <out.json> [--min-loc N] [--max-loc N]"""
import argparse, json, os, sys
sys.path.insert(0, "/Users/shawnli/Desktop/Honours/defects4j/supervisor_pipeline_runs/shim")
from callgraph import extract_methods_from_file

ap = argparse.ArgumentParser(); ap.add_argument("src"); ap.add_argument("out")
ap.add_argument("--min-loc", type=int, default=0); ap.add_argument("--max-loc", type=int, default=10**9)
a = ap.parse_args()
rows = []
for dp, _dn, fn in os.walk(a.src):
    if "/test" in dp or "/tests" in dp:
        continue
    for f in sorted(fn):
        if not f.endswith(".java"):
            continue
        p = os.path.join(dp, f)
        try:
            lines = open(p, "rb").read().decode("utf-8", "replace").replace("\r\n", "\n").split("\n")
            ms = extract_methods_from_file(p)
        except Exception as e:
            continue
        loc = len(lines)
        if not (a.min_loc <= loc <= a.max_loc):
            continue
        statics = 0
        for m in ms:
            h = lines[m["start_line"] - 1] if 0 < m["start_line"] <= loc else ""
            statics += 1 if " static " in h else 0
        rows.append({"file": os.path.relpath(p, a.src), "loc": loc, "methods": len(ms),
                     "static_methods": statics,
                     "methods_per_1k_loc": round(1000.0 * len(ms) / max(1, loc), 1)})
rows.sort(key=lambda r: -r["loc"])
json.dump(rows, open(a.out, "w"), indent=1)
print(f"{len(rows)} files; largest: " + ", ".join(f"{r['file'].split('/')[-1]}({r['loc']}L/{r['methods']}m)" for r in rows[:6]))
print("smallest: " + ", ".join(f"{r['file'].split('/')[-1]}({r['loc']}L/{r['methods']}m)" for r in rows[-6:]))
