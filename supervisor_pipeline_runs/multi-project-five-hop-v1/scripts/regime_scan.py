"""PHASE 2 helper (no LLM): for candidate methods, collect the argument lists of every call in the test sources and report numeric
parameter positions that tests exercise with a single constant value (an 'untested regime', G2). Usage: regime_scan.py <checkout> <src> <tests> <candidates.json> <out.json> [--min-tests 1]"""
import os, re, sys, json, argparse
ap = argparse.ArgumentParser(); ap.add_argument("checkout"); ap.add_argument("src"); ap.add_argument("tests"); ap.add_argument("cands"); ap.add_argument("out"); ap.add_argument("--min-tests", type=int, default=1); ap.add_argument("--max", type=int, default=400); a = ap.parse_args()
def read_all(root):
    out = {}
    for dp, _, fs in os.walk(root):
        for f in fs:
            if f.endswith(".java"): p = os.path.join(dp, f); out[p] = open(p, errors="replace").read()
    return out
tests = read_all(os.path.join(a.checkout, a.tests)); prod = read_all(os.path.join(a.checkout, a.src))
def split_args(s):
    args = []; depth = 0; cur = ""
    for ch in s:
        if ch in "([{<": depth += 1
        elif ch in ")]}>": depth -= 1
        if ch == "," and depth == 0: args.append(cur.strip()); cur = ""
        else: cur += ch
    if cur.strip(): args.append(cur.strip())
    return args
def calls_of(name, texts):
    pat = re.compile(r"\b" + re.escape(name) + r"\s*\(")
    res = []
    for p, t in texts.items():
        for m in pat.finditer(t):
            # skip declarations
            pre = t[max(0, m.start() - 40):m.start()]
            if re.search(r"(public|private|protected|static|void|int|long|double|float|boolean|String|[A-Z]\w*)\s+$", pre) and not re.search(r"(return|=|\(|,|\.)\s*$", pre): continue
            i = m.end(); depth = 1
            while i < len(t) and depth > 0:
                if t[i] == "(": depth += 1
                elif t[i] == ")": depth -= 1
                i += 1
            res.append((os.path.relpath(p, a.checkout), t[:m.start()].count("\n") + 1, split_args(t[m.end():i - 1])))
    return res
C = json.load(open(a.cands))["top"]
out = []
NUMLIT = re.compile(r"^-?\d+(\.\d+)?[dDfFlL]?$|^0x[0-9A-Fa-f]+L?$|^(true|false|null)$")
for c in C[:a.max]:
    tc = calls_of(c["name"], tests); pc = calls_of(c["name"], prod)
    if len(tc) < a.min_tests: continue
    params = [x.strip() for x in c["params"].split(",") if x.strip()]; npar = len(params)
    pos = {}
    for i, pn in enumerate(params):
        vals = [args[i] for _, _, args in tc if len(args) == npar]
        lits = [v for v in vals if NUMLIT.match(v)]
        pos[i] = {"param": pn, "n_calls": len(vals), "distinct": sorted(set(vals))[:8], "n_distinct": len(set(vals)), "all_same_literal": (len(vals) > 0 and len(set(vals)) == 1 and NUMLIT.match(vals[0]) is not None), "literal_share": round(len(lits) / len(vals), 2) if vals else None}
    fixed = [pos[i]["param"] + "=" + pos[i]["distinct"][0] for i in pos if pos[i]["all_same_literal"]]
    out.append({"name": c["name"], "file": c["file"], "line": c["line"], "params": c["params"], "score": c["score"], "test_calls": len(tc), "prod_calls": len(pc), "test_arg_positions": pos, "fixed_regimes": fixed, "prod_call_examples": [f"{f}:{l} {name}({', '.join(args)[:80]})" for (f, l, args) in pc[:4] for name in [c["name"]]], "test_call_examples": [f"{f}:{l} ({', '.join(args)[:80]})" for (f, l, args) in tc[:5]]})
out.sort(key=lambda r: (-len(r["fixed_regimes"]), -r["score"]))
json.dump(out, open(a.out, "w"), indent=1)
print(f"{len(out)} candidates with >= {a.min_tests} test calls; those with a fixed-regime parameter first:")
for r in out[:60]:
    if not r["fixed_regimes"]: continue
    print(f"{r['score']:>3} {r['file'].split('/')[-1]}:{r['line']} {r['name']}({r['params'][:70]}) tests={r['test_calls']} prod={r['prod_calls']} FIXED: {r['fixed_regimes']}")
