"""PHASE 2 helper (no LLM): public static methods with numeric parameters and arithmetic bodies, with the number of QUALIFIED test calls
(Class.method( ) and unqualified calls inside the class's own test file. Lists the least-tested first. Usage: static_untested.py <checkout> <src> <tests>"""
import os, re, sys
co, src, tst = sys.argv[1], sys.argv[2], sys.argv[3]
def read_all(root):
    out = {}
    for dp, _, fs in os.walk(root):
        for f in fs:
            if f.endswith(".java"): p = os.path.join(dp, f); out[p] = open(p, errors="replace").read()
    return out
prod = read_all(os.path.join(co, src)); tests = read_all(os.path.join(co, tst)); tall = "\n".join(tests.values())
DECL = re.compile(r"^    public static (?:final )?(?:synchronized )?(?:<[^>]+>\s*)?([\w\.\[\]<>,\s\?]+?)\s+(\w+)\s*\(([^)]*)\)\s*(?:throws [\w\., ]+)?\s*\{", re.M)
rows = []
for p, t in prod.items():
    cls = os.path.basename(p)[:-5]; rel = os.path.relpath(p, co)
    own = [v for k, v in tests.items() if re.search(r"(^|/)(Test%s|%sTest|%sTests)\.java$" % (cls, cls, cls), k)]
    own_text = "\n".join(own)
    for m in DECL.finditer(t):
        ret, name, params = m.group(1).strip(), m.group(2), m.group(3)
        if not re.search(r"\b(int|long|double|float)\b", params): continue
        start = m.end(); depth = 1; i = start
        while i < len(t) and depth > 0:
            depth += (t[i] == "{") - (t[i] == "}"); i += 1
        body = re.sub(r"/\*.*?\*/|//[^\n]*", "", t[start:i - 1], flags=re.S); bl = [l for l in body.split("\n") if l.strip()]
        if len(bl) < 4 or not re.search(r"[-+*/%]\s*[\w(]|<<|>>", body): continue
        jd = re.search(r"/\*\*(?:(?!\*/).)*\*/\s*(?:@\w+(?:\([^)]*\))?\s*)*$", t[:m.start()], re.S); jd = jd.group(0) if jd else ""
        q = len(re.findall(r"\b" + re.escape(cls) + r"\s*\.\s*" + re.escape(name) + r"\s*\(", tall)); u = len(re.findall(r"(?<![\w.])" + re.escape(name) + r"\s*\(", own_text))
        loops = len(re.findall(r"\b(for|while)\s*\(", body)); nparam = len([x for x in params.split(",") if x.strip()])
        rows.append((q + u, q, u, rel, t[:m.start()].count("\n") + 1, ret, name, params.replace("\n", " ")[:90], len(bl), loops, nparam, len(jd)))
rows.sort(key=lambda r: (r[0], -r[8]))
print(f"{len(rows)} public static numeric-arithmetic methods; least-tested first (total=qualified+own-file calls):")
for r in rows[:70]: print(f"tests={r[0]:>3} (q{r[1]}/o{r[2]}) {r[3]}:{r[4]} {r[5]} {r[6]}({r[7]}) body={r[8]} loops={r[9]} jd={r[11]}")
