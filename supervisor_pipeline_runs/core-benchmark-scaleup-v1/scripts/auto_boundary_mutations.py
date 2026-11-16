#!/opt/miniconda3/bin/python
"""Generate comparison-boundary mutations (< <-> <=, > <-> >=) inside method bodies of the given production files (no LLM).
Each mutation's anchor is the target line plus its previous line (must be unique in the file). Usage:
auto_boundary_mutations.py <checkout> <src_root> <test_root> <out.json> --cap N file1 file2 ... (paths relative to src_root)"""
import os, re, sys, json, argparse
ap = argparse.ArgumentParser(); ap.add_argument("checkout"); ap.add_argument("src"); ap.add_argument("tests"); ap.add_argument("out"); ap.add_argument("--cap", type=int, default=12); ap.add_argument("files", nargs="+"); a = ap.parse_args()
COND = re.compile(r"^\s*(if|while|for|\}?\s*else if)\b|\?\s*|return\s")
OPS = [("<=", "<"), (">=", ">"), ("<", "<="), (">", ">=")]
def test_classes(simple):
    hits = []
    for dp, _, fs in os.walk(os.path.join(a.checkout, a.tests)):
        for f in fs:
            if f == simple + "Test.java" or f == simple + "Tests.java": hits.insert(0, os.path.join(dp, f))
    if not hits:
        for dp, _, fs in os.walk(os.path.join(a.checkout, a.tests)):
            for f in fs:
                if f.endswith(".java") and simple in open(os.path.join(dp, f), errors="replace").read(): hits.append(os.path.join(dp, f))
    out = []
    for h in hits[:4]:
        rel = os.path.relpath(h, os.path.join(a.checkout, a.tests))[:-5].replace("/", "."); out.append(rel)
    return out
muts = []
for rel in a.files:
    path = os.path.join(a.src, rel); full = os.path.join(a.checkout, path)
    if not os.path.exists(full): print("missing", rel); continue
    lines = open(full, "rb").read().decode("utf-8").replace("\r\n", "\n").split("\n"); text = "\n".join(lines)
    simple = os.path.basename(rel)[:-5]; tests = test_classes(simple); n = 0
    for i, line in enumerate(lines):
        s = line.strip()
        if not s or s.startswith(("*", "/", "//")) or "\"" in s or "'" in s: continue
        if not COND.search(line) and not re.search(r"\b(min|max)\s*\(", line): continue
        if "null" in line or "instanceof" in line: continue
        for old_op, new_op in OPS:
            for m in re.finditer(r"(?<![<>=!])" + re.escape(old_op) + r"(?![=>])", line):
                if old_op in ("<", ">") and line[m.end():m.end() + 1] == "=": continue
                new_line = line[:m.start()] + new_op + line[m.end():]
                ctx_old = (lines[i - 1] + "\n" + line) if i > 0 else line; ctx_new = (lines[i - 1] + "\n" + new_line) if i > 0 else new_line
                if text.count(ctx_old) != 1: continue
                muts.append({"id": f"{simple}:L{i + 1}:{old_op}->{new_op}:{len(muts)}", "file": path, "old": ctx_old, "new": ctx_new, "tests": tests, "line": line.strip()[:120]}); n += 1
                if n >= a.cap: break
            if n >= a.cap: break
        if n >= a.cap: break
    print(simple, n, "mutations; tests:", [t.split(".")[-1] for t in tests])
json.dump(muts, open(a.out, "w"), indent=1); print("total", len(muts))
