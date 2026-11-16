"""PHASE 2 helper (no LLM): for every public static method (numeric params, arithmetic body), collect QUALIFIED test calls Class.method(...)
and report parameter positions whose test values are a single literal (an untested regime). Usage: static_regimes.py <checkout> <src> <tests>"""
import os, re, sys
co, src, tst = sys.argv[1], sys.argv[2], sys.argv[3]
def read_all(root):
    out = {}
    for dp, _, fs in os.walk(root):
        for f in fs:
            if f.endswith(".java"): p = os.path.join(dp, f); out[p] = open(p, errors="replace").read()
    return out
prod = read_all(os.path.join(co, src)); tests = read_all(os.path.join(co, tst))
DECL = re.compile(r"^    public static (?:final )?(?:<[^>]+>\s*)?([\w\.\[\]<>,\s\?]+?)\s+(\w+)\s*\(([^)]*)\)\s*(?:throws [\w\., ]+)?\s*\{", re.M)
NUMLIT = re.compile(r"^-?\d+(\.\d+)?(e-?\d+)?[dDfFlL]?$|^0x[0-9A-Fa-f]+L?$|^(true|false|null)$|^-?\d+ \* \d+$")
def split_args(s):
    args = []; depth = 0; cur = ""
    for ch in s:
        if ch in "([{<": depth += 1
        elif ch in ")]}>": depth -= 1
        if ch == "," and depth == 0: args.append(cur.strip()); cur = ""
        else: cur += ch
    if cur.strip(): args.append(cur.strip())
    return args
def qcalls(cls, name):
    pat = re.compile(r"\b" + re.escape(cls) + r"\s*\.\s*" + re.escape(name) + r"\s*\(")
    res = []
    for p, t in tests.items():
        for m in pat.finditer(t):
            i = m.end(); depth = 1
            while i < len(t) and depth > 0:
                depth += (t[i] == "(") - (t[i] == ")"); i += 1
            res.append(split_args(t[m.end():i - 1]))
    return res
rows = []
for p, t in prod.items():
    cls = os.path.basename(p)[:-5]; rel = os.path.relpath(p, co)
    for m in DECL.finditer(t):
        name, params = m.group(2), [x.strip() for x in m.group(3).replace("\n", " ").split(",") if x.strip()]
        if not any(re.search(r"\b(int|long|double|float)\b", x) for x in params): continue
        start = m.end(); depth = 1; i = start
        while i < len(t) and depth > 0:
            depth += (t[i] == "{") - (t[i] == "}"); i += 1
        body = re.sub(r"/\*.*?\*/|//[^\n]*", "", t[start:i - 1], flags=re.S); bl = [l for l in body.split("\n") if l.strip()]
        if len(bl) < 4 or not re.search(r"[-+*/%]\s*[\w(]|<<|>>", body): continue
        calls = [a for a in qcalls(cls, name) if len(a) == len(params)]
        if len(calls) < 2: continue
        fixed = []
        for k, pn in enumerate(params):
            vals = [c[k] for c in calls]; ds = set(vals)
            if len(ds) == 1 and NUMLIT.match(vals[0]): fixed.append(f"{pn.split()[-1]}={vals[0]}")
        if fixed: rows.append((len(calls), rel, t[:m.start()].count("\n") + 1, name, ", ".join(params)[:80], len(bl), fixed))
rows.sort(key=lambda r: -r[0])
for r in rows: print(f"calls={r[0]:>3} {r[1]}:{r[2]} {r[3]}({r[4]}) body={r[5]} FIXED {r[6]}")
print(len(rows), "methods with a fixed test regime")
