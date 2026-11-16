"""PHASE 2 helper (no LLM): public/protected INSTANCE methods with numeric params and arithmetic bodies whose name never appears in the class's
own test file(s) (and rarely anywhere in tests). Usage: instance_untested.py <checkout> <src> <tests> [min_body_lines]"""
import os, re, sys
co, src, tst = sys.argv[1], sys.argv[2], sys.argv[3]; minb = int(sys.argv[4]) if len(sys.argv) > 4 else 6
def read_all(root):
    out = {}
    for dp, _, fs in os.walk(root):
        for f in fs:
            if f.endswith(".java"): p = os.path.join(dp, f); out[p] = open(p, errors="replace").read()
    return out
prod = read_all(os.path.join(co, src)); tests = read_all(os.path.join(co, tst)); tall = "\n".join(tests.values())
from collections import Counter
CALLS = Counter(re.findall(r"\b([A-Za-z_]\w*)\s*\(", tall))
DECL = re.compile(r"^(?:    |        )(public|protected) (?!static)(?:final )?(?:synchronized )?(?:<[^>]+>\s*)?([\w\.\[\]<>,\s\?]+?)\s+(\w+)\s*\(([^)]*)\)\s*(?:throws [\w\., ]+)?\s*\{", re.M)
rows = []
for p, t in prod.items():
    cls = os.path.basename(p)[:-5]; rel = os.path.relpath(p, co)
    if "abstract class" in t[:t.find("{")] and False: pass
    own = [v for k, v in tests.items() if re.search(r"(^|/)(Test%s|%sTest|%sTests|Abstract%sTest)\.java$" % (cls, cls, cls, cls), k)]
    own_text = "\n".join(own)
    for m in DECL.finditer(t):
        vis, ret, name, params = m.group(1), m.group(2).strip(), m.group(3), m.group(4)
        if name in ("equals", "hashCode", "toString", "clone", "compareTo") or ret in ("new",): continue
        if not re.search(r"\b(int|long|double|float)\b", params): continue
        start = m.end(); depth = 1; i = start
        while i < len(t) and depth > 0:
            depth += (t[i] == "{") - (t[i] == "}"); i += 1
        body = re.sub(r"/\*.*?\*/|//[^\n]*", "", t[start:i - 1], flags=re.S); bl = [l for l in body.split("\n") if l.strip()]
        if len(bl) < minb or not re.search(r"[-+*/%]\s*[\w(]|<<|>>", body): continue
        jd = re.search(r"/\*\*(?:(?!\*/).)*\*/\s*(?:@\w+(?:\([^)]*\))?\s*)*$", t[:m.start()], re.S); jd = jd.group(0) if jd else ""
        o = len(re.findall(r"(?<![\w.])" + re.escape(name) + r"\s*\(|\." + re.escape(name) + r"\s*\(", own_text)); a = CALLS.get(name, 0)
        loops = len(re.findall(r"\b(for|while)\s*\(", body))
        rows.append((o, a, rel, t[:m.start()].count("\n") + 1, vis, ret, name, params.replace("\n", " ")[:80], len(bl), loops, len(jd), bool(own)))
rows.sort(key=lambda r: (r[0], r[1], -r[8]))
print(f"{len(rows)} instance methods (numeric params, arithmetic, body >= {minb}); untested-in-own-test-file first:")
for r in rows[:80]: print(f"own={r[0]:>2} all={r[1]:>4} testfile={'y' if r[11] else 'n'} {r[2]}:{r[3]} {r[4]} {r[5]} {r[6]}({r[7]}) body={r[8]} loops={r[9]} jd={r[10]}")
