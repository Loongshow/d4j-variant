#!/opt/miniconda3/bin/python
"""Static structural audit of a five-hop treatment on a PATCHED checkout (e.g. the treatment reproduction state), complementing the validator's
gates O/P/Q and the dynamic evidence (trigger fails only through hop 5). Checks: exactly five hops; each hop declared exactly once in the
production tree; each hop's call to the next occurs once in the whole production tree and inside the caller; the gold is referenced only by
hop 4 (no alternative path bypasses it); the facade calls hop 1 and no other hop; statement counts per hop; dataflow continuity (every
identifier passed by a hop to the next is a parameter or a local of that hop). Usage: structural_audit.py <config.json> <patched_checkout> <out.json>"""
import json, os, re, sys
cfg, co, out = json.load(open(sys.argv[1])), sys.argv[2], sys.argv[3]
T = cfg["treatment"]; HOPS = T["hops"]; SRC = os.path.join(co, cfg["src_dir"])
def text(p): return open(os.path.join(co, p), "rb").read().decode("utf-8").replace("\r\n", "\n")
def span(p, decl):
    L = text(p).split("\n"); s = next((i for i, l in enumerate(L) if decl in l), None)
    if s is None: return None
    d = 0; st = False
    for j in range(s, len(L)):
        d += L[j].count("{") - L[j].count("}"); st = st or "{" in L[j]
        if st and d == 0: return (s, j)
def grep_all(needle):
    hits = []
    for dp, _, fs in os.walk(SRC):
        for f in fs:
            if f.endswith(".java"):
                p = os.path.join(dp, f); t = open(p, "rb").read().decode("utf-8", "replace")
                for i, l in enumerate(t.split("\n")):
                    if needle in l: hits.append((os.path.relpath(p, co), i + 1))
    return hits
R = {"schema_version": "core-benchmark-scaleup-v1/structural-audit/v1", "pair_id": cfg["pair_id"], "checks": []}
def check(name, ok, detail): R["checks"].append({"check": name, "status": "pass" if ok else "FAIL", "detail": detail}); print(name, "pass" if ok else "FAIL")
check("exactly five synthetic hops in the design", len(HOPS) == 5 and HOPS[-1].get("holds_bug") is True, f"{len(HOPS)} hops; hop5 holds_bug={HOPS[-1].get('holds_bug')}")
spans = {}
for h in HOPS:
    sp = span(h["file"], h["decl"]); spans[h["n"]] = sp; decls = grep_all(h["decl"]); check(f"hop{h['n']} {h['class'].split('.')[-1]}.{h['method']} declared exactly once in production", bool(sp) and len(decls) == 1, f"span {sp}, declarations {decls}")
for h in HOPS[:-1]:
    hits = grep_all(h["calls_next"]); sp = spans[h["n"]]; inside = [x for x in hits if x[0] == h["file"] and sp and sp[0] + 1 <= x[1] <= sp[1] + 1]
    check(f"hop{h['n']} -> hop{h['n'] + 1} call occurs once in production and inside hop{h['n']}", len(hits) == 1 and len(inside) == 1, f"hits {hits}")
gold = HOPS[-1]; gname = gold["class"].split(".")[-1] + "." + gold["method"] + "("; refs = grep_all(gname); hop4 = HOPS[-2]; sp4 = spans[4]; ref_in_hop4 = [x for x in refs if x[0] == hop4["file"] and sp4 and sp4[0] + 1 <= x[1] <= sp4[1] + 1]
check("gold referenced only from hop 4 (no alternative path bypasses hop 5)", len(refs) == 1 and len(ref_in_hop4) == 1, f"references to {gname}: {refs}")
fsp = span(cfg["facade_file"], cfg["facade_decl"]); ftxt = "\n".join(text(cfg["facade_file"]).split("\n")[fsp[0]:fsp[1] + 1]) if fsp else ""
calls_in_facade = [h["n"] for h in HOPS if (h["class"].split(".")[-1] + "." + h["method"] + "(") in ftxt]
check("facade calls hop 1 and no other hop directly", calls_in_facade == [1] and T["facade_call"] in ftxt, f"chain methods called in facade: {calls_in_facade}")
stmts = {}
for h in HOPS:
    sp = spans[h["n"]]; body = text(h["file"]).split("\n")[sp[0] + 1:sp[1]]; n = len([l for l in body if l.strip() and not l.strip().startswith(("/", "*", "@"))]); stmts[f"hop{h['n']}"] = n
check("no hop is a bare pass-through (>= 3 body lines in hops 1-4, >= 2 in hop 5)", all(stmts[f"hop{i}"] >= 3 for i in range(1, 5)) and stmts["hop5"] >= 2, json.dumps(stmts))
flow = {}
ok_flow = True
for h in HOPS[:-1]:
    sp = spans[h["n"]]; L = text(h["file"]).split("\n"); head = " ".join(L[sp[0]:sp[0] + 8]); body = "\n".join(L[sp[0]:sp[1] + 1])
    k = body.find(h["calls_next"]); j = body.find(";", k); call = body[k:j]
    nxt = HOPS[h["n"]]; m = re.search(re.escape(nxt["class"].split(".")[-1] + "." + nxt["method"]) + r"\s*\(", body[k:])
    if m:  # the argument list of the actual call expression (balanced parentheses), not the whole statement
        i = k + m.end(); depth = 1; start = i
        while depth and i < len(body): depth += (body[i] == "(") - (body[i] == ")"); i += 1
        args = re.findall(r"\b([A-Za-z_]\w*)\b", body[start:i - 1])
    else:
        args = re.findall(r"\b([A-Za-z_]\w*)\b", call.split("(", 1)[1]) if "(" in call else []
    params = set(re.findall(r"\b([A-Za-z_]\w*)\s*[,)]", head.split("{")[0])); locals_ = set(re.findall(r"^\s*(?:final\s+)?[\w\[\]<>.]+\s+(\w+)\s*=", body, re.M))
    unknown = [a for a in set(args) if a not in params and a not in locals_ and not re.match(r"^(get|is|new|Math|FastMath|Arc2D|OPEN|MARGIN|[A-Z]\w+)$", a) and not a[0].isupper()]
    flow[f"hop{h['n']}"] = {"passes": sorted(set(args)), "unexplained": unknown}; ok_flow &= not unknown
check("dataflow continuity: every identifier passed down is a parameter or local of the passing hop", ok_flow, json.dumps(flow))
R["statement_counts"] = stmts; R["overall"] = "pass" if all(c["status"] == "pass" for c in R["checks"]) else "FAIL"; json.dump(R, open(out, "w"), indent=1); print("overall", R["overall"])
