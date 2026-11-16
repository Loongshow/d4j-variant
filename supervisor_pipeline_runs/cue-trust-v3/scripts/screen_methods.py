"""Screen long methods in large files: length, overload collapse, production callers, test references."""
import sys, os, re, json, subprocess
sys.path.insert(0, "/Users/shawnli/Desktop/Honours/defects4j/supervisor_pipeline_runs/shim")
from callgraph import extract_methods_from_file
proj, root, srcdir, testdir = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
MINFILE, MINLEN = int(sys.argv[5]) if len(sys.argv) > 5 else 2500, 40
files = []
for d, _, fs in os.walk(os.path.join(root, srcdir)):
    for f in fs:
        if f.endswith(".java"):
            p = os.path.join(d, f); n = sum(1 for _ in open(p, errors="replace"))
            if n >= MINFILE: files.append((p, n))
src_all = subprocess.run(["grep", "-rhoE", r"\b[a-zA-Z_][a-zA-Z0-9_]*\s*\(", os.path.join(root, srcdir)], capture_output=True, text=True).stdout
calls = {}
for m in re.findall(r"([a-zA-Z_][a-zA-Z0-9_]*)\s*\(", src_all): calls[m] = calls.get(m, 0) + 1
tests_all = subprocess.run(["grep", "-rhoE", r"\b[a-zA-Z_][a-zA-Z0-9_]*\s*\(", os.path.join(root, testdir)], capture_output=True, text=True).stdout
tcalls = {}
for m in re.findall(r"([a-zA-Z_][a-zA-Z0-9_]*)\s*\(", tests_all): tcalls[m] = tcalls.get(m, 0) + 1
rows = []
for p, n in files:
    ms = extract_methods_from_file(p); cls = os.path.basename(p)[:-5]
    names = [m["name"] for m in ms]
    for m in ms:
        L = m["end_line"] - m["start_line"] + 1
        if L < MINLEN: continue
        rows.append({"file": os.path.relpath(p, root), "file_lines": n, "class": cls, "method": m["name"], "start": m["start_line"], "len": L,
                     "overloads": names.count(m["name"]), "src_call_sites": calls.get(m["name"], 0) - 1, "test_refs": tcalls.get(m["name"], 0)})
rows.sort(key=lambda r: (-r["file_lines"], -r["len"]))
json.dump(rows, open(f"construction/screen_{proj}.json", "w"), indent=1)
for r in rows: print(f'{r["class"]:28s} {r["method"]:36s} L{r["start"]:<5d} len={r["len"]:<4d} ov={r["overloads"]} srcCalls={r["src_call_sites"]:<3d} testRefs={r["test_refs"]:<3d} file={r["file_lines"]}')
