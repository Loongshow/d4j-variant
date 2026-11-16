"""PHASE 2 static candidate search (no LLM). Enumerates production methods with a javadoc contract, numeric parameters and arithmetic bodies,
counts test references and production call sites, and scores candidates for G1-G8 review. Usage: find_targets.py <checkout> <src_dir> <test_dir> <out.json> [--top 60]"""
import os, re, sys, json, argparse
ap = argparse.ArgumentParser(); ap.add_argument("checkout"); ap.add_argument("src"); ap.add_argument("tests"); ap.add_argument("out"); ap.add_argument("--top", type=int, default=60); a = ap.parse_args()
CONTRACT = re.compile(r"\b(offset|position|index|indices|scale|period|range|inclusive|exclusive|wrap|modulo|degrees|radians|unit|units|in bits|in millis|milliseconds|seconds|minutes|hours|days|weeks|months|years|must be|between|greater than|less than|at least|at most|starting|start|end|length|width|height|count|number of|fraction|percent|normali|interpolat|round|truncat|clamp|bounded|lower|upper|first|last|shift|skip|stride|step|bin|bucket|weight|mean|average|sum|product|distance|angle|phase)\b", re.I)
ARITH = re.compile(r"[-+*/%]\s*[A-Za-z0-9_(]|<<|>>|Math\.|FastMath\.")
DECL = re.compile(r"^(\s*)((?:public|protected|private|static|final|synchronized|abstract|native|default|\s)+)\s*(?:<[^>]+>\s*)?([\w\.\[\]<>,\s\?]+?)\s+(\w+)\s*\(([^)]*)\)\s*(?:throws [\w\., ]+)?\s*\{", re.M)
def strip_comments(s): return re.sub(r"/\*.*?\*/|//[^\n]*", "", s, flags=re.S)
def methods(path, text):
    out = []
    for m in DECL.finditer(text):
        indent, mods, ret, name, params = m.group(1), m.group(2), m.group(3).strip(), m.group(4), m.group(5)
        if name in ("if", "for", "while", "switch", "catch", "synchronized", "try", "else") or ret in ("new", "return", "else", "throw"): continue
        if len(indent) != 4: continue  # top-level class members only (4-space indent); nested classes are skipped
        start = m.end(); depth = 1; i = start
        while i < len(text) and depth > 0:
            c = text[i]
            if c == "{": depth += 1
            elif c == "}": depth -= 1
            i += 1
        body = text[start:i - 1]; before = text[:m.start()]; jd = re.search(r"/\*\*(?:(?!\*/).)*\*/\s*(?:@\w+(?:\([^)]*\))?\s*)*$", before, re.S)
        javadoc = jd.group(0) if jd else ""
        out.append({"name": name, "ret": ret, "params": params.strip(), "mods": mods.strip(), "line": text[:m.start()].count("\n") + 1, "end_line": text[:i].count("\n") + 1, "javadoc": javadoc, "body": body})
    return out
src_root = os.path.join(a.checkout, a.src); test_root = os.path.join(a.checkout, a.tests)
test_text = ""; test_files = []
for dp, _, fs in os.walk(test_root):
    for f in fs:
        if f.endswith(".java"): p = os.path.join(dp, f); test_files.append(p); test_text += "\n" + open(p, errors="replace").read()
prod = {}
for dp, _, fs in os.walk(src_root):
    for f in fs:
        if f.endswith(".java"): p = os.path.join(dp, f); prod[p] = open(p, errors="replace").read()
prod_all = "\n".join(prod.values())
from collections import Counter
CALL = re.compile(r"\b([A-Za-z_]\w*)\s*\(")
test_calls = Counter(CALL.findall(test_text)); prod_calls = Counter(CALL.findall(prod_all))
decl_counts = Counter(re.findall(r"\b([A-Za-z_]\w*)\s*\([^)]*\)\s*(?:throws [\w\., ]+)?\s*\{", prod_all))
cands = []
for p, text in prod.items():
    rel = os.path.relpath(p, a.checkout); cls_lines = text.count("\n") + 1
    for m in methods(p, text):
        body = strip_comments(m["body"]); blines = [l for l in body.split("\n") if l.strip()]
        if not (4 <= len(blines) <= 60): continue
        nparams = len([x for x in m["params"].split(",") if x.strip()]); numeric = len(re.findall(r"\b(int|long|double|float|short|byte)\b", m["params"]))
        if numeric == 0 and not re.search(r"\b(int|long|double|float)\[\]", m["params"]): continue
        if not ARITH.search(body): continue
        jd = m["javadoc"]; cw = sorted(set(w.lower() for w in CONTRACT.findall(jd)))
        if not jd or not cw: continue
        loops = len(re.findall(r"\b(for|while)\s*\(", body)); throws = len(re.findall(r"\bthrow\b", body)); ifs = len(re.findall(r"\bif\s*\(", body))
        t_refs = test_calls.get(m["name"], 0); same_name_decls = decl_counts.get(m["name"], 0); p_refs = prod_calls.get(m["name"], 0) - same_name_decls
        score = (min(len(cw), 6) * 2 + (3 if loops else 0) + min(numeric, 4) + (2 if 6 <= len(blines) <= 30 else 0) + (3 if t_refs <= 6 else (1 if t_refs <= 15 else 0)) + (2 if 2 <= p_refs <= 12 else 0) + (2 if cls_lines >= 400 else 0) - (2 if throws > 2 else 0) - (3 if same_name_decls > 3 else 0))
        cands.append({"file": rel, "class_lines": cls_lines, "name": m["name"], "line": m["line"], "end_line": m["end_line"], "ret": m["ret"], "params": m["params"], "body_lines": len(blines), "numeric_params": numeric, "loops": loops, "ifs": ifs, "throws": throws, "contract_words": cw[:12], "test_refs": t_refs, "prod_call_sites": p_refs, "same_name_decls": same_name_decls, "score": score})
cands.sort(key=lambda c: -c["score"])
json.dump({"checkout": a.checkout, "n_candidates": len(cands), "n_prod_files": len(prod), "n_test_files": len(test_files), "top": cands[:a.top]}, open(a.out, "w"), indent=1)
print(f"{len(prod)} production files, {len(test_files)} test files, {len(cands)} candidates; top {a.top}:")
for c in cands[:a.top]: print(f"{c['score']:>3} {c['file']}:{c['line']} {c['ret']} {c['name']}({c['params'][:60]}) body={c['body_lines']} loops={c['loops']} tests={c['test_refs']} calls={c['prod_call_sites']} decls={c['same_name_decls']} cls={c['class_lines']} words={','.join(c['contract_words'][:6])}")
