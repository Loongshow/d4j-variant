"""Config-driven fresh-checkout reproduction from packaged patches only. Usage: repro_pair.py <config.json> <control|treatment> <fresh_checkout> <pkg> <out_json>"""
import json, os, re, subprocess, sys, time, hashlib, shutil
cfg, arm, co, pkg, out = json.load(open(sys.argv[1])), sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5]
A = cfg[arm]; TRIG = cfg["trigger"]; HOPS = cfg["treatment"]["hops"]; env = dict(os.environ, PERL5LIB=os.path.expanduser("~/perl5/lib/perl5"))
R = {"schema_version": "core-benchmark-scaleup-v1/reproduction/v1", "label": cfg["label"], "project": cfg["project"], "arm": arm.upper(), "variant_id": cfg[f"{arm}_id"], "fresh_checkout": co, "package": pkg, "steps": [], "started_at": time.strftime("%Y-%m-%dT%H:%M:%S%z")}
def save(): json.dump(R, open(out, "w"), indent=1)
def sh(cmd, timeout=1200):
    p = subprocess.run(cmd, cwd=co, capture_output=True, text=True, env=env, timeout=timeout); return p.returncode, p.stdout + p.stderr
def step(sid, name, cmds, ok, key): R["steps"].append({"step": sid, "name": name, "commands": cmds, "status": "pass" if ok else "FAIL", "key_output": key[-1200:]}); save(); print(sid, "pass" if ok else "FAIL", flush=True); return ok
def text(path): return open(os.path.join(co, path), "rb").read().decode("utf-8").replace("\r\n", "\n")
def span(path, decl):
    Ls = text(path).split("\n"); s = next((i for i, l in enumerate(Ls) if decl in l), None)
    if s is None: return None
    d = 0; st = False
    for j in range(s, len(Ls)):
        d += Ls[j].count("{") - Ls[j].count("}"); st = st or "{" in Ls[j]
        if st and d == 0: return (s + 1, j + 1)
def where(path, t):
    if "\n" in t:
        T = text(path); k = T.find(t)
        if k < 0 or T.count(t) != 1: return []
        start = T[:k].count("\n") + 1; return list(range(start, start + t.count("\n") + 1))
    return [i + 1 for i, l in enumerate(text(path).split("\n")) if t in l]
R["package_hashes"] = {f: hashlib.sha256(open(os.path.join(pkg, f), "rb").read()).hexdigest() for f in ("variant.patch", "test.patch")}
rc, o = sh(["git", "status", "--short"]); ok = step("R0", "fresh checkout has a clean tracked tree", ["git status --short"], not [l for l in o.splitlines() if not l.startswith("??")], o or "clean")
rc, o = sh(["git", "rev-parse", "HEAD"]); R["checkout_head"] = o.strip()
if ok:
    rc1, o1 = sh(["git", "apply", os.path.join(pkg, "variant.patch")]); rc2, o2 = sh(["git", "apply", os.path.join(pkg, "test.patch")])
    ok = step("R1", "apply packaged variant.patch + test.patch", ["git apply variant.patch", "git apply test.patch"], rc1 == 0 and rc2 == 0, (o1 + o2) or "both applied")
if ok:
    for d in ("target", "build", "build-tests"): shutil.rmtree(os.path.join(co, d), ignore_errors=True)
    rc, o = sh(["defects4j", "compile"]); ok = step("R2", "compile", ["defects4j compile"], rc == 0 and "BUILD FAILED" not in o, o)
if ok:
    sigs = []
    for i in range(3):
        rc, o = sh(["defects4j", "test", "-t", TRIG], timeout=900); m = re.search(r"Failing tests:\s*(\d+)", o); n = int(m.group(1)) if m else None
        ft = open(os.path.join(co, "failing_tests")).read() if os.path.exists(os.path.join(co, "failing_tests")) else ""; sigs.append({"run": i + 1, "n_fail": n, "signature": "\n".join(ft.splitlines()[:2])})
    R["trigger_runs"] = sigs
    ok = step("R3", "trigger fails deterministically 3x with the expected value-mismatch signature", [f"defects4j test -t {TRIG} (x3)"], all(s["n_fail"] == 1 for s in sigs) and len({s["signature"] for s in sigs}) == 1 and cfg["expected_signature"] in sigs[0]["signature"], json.dumps(sigs, indent=1))
if ok:
    if arm == "control":
        s = span(A["gold_file"], A["gold_decl"]); b = where(A["gold_file"], A["bug_line"]); R["gold_check"] = {"gold": f"{A['gold_class']}#{A['gold_method']}", "span": s, "buggy_line_at": b}
        ok = step("R4", "gold source exists where recorded and contains the buggy line", ["static span check"], bool(s and b and all(s[0] <= x <= s[1] for x in b)), json.dumps(R["gold_check"]))
    else:
        gs = span(A["gold_file"], A["gold_decl"]); b = where(A["gold_file"], A["bug_line"]); chain = []; good = bool(gs and b and all(gs[0] <= x <= gs[1] for x in b))
        s0 = span(cfg["facade_file"], cfg["facade_decl"]); c0 = where(cfg["facade_file"], A["facade_call"]); good &= bool(s0 and c0 and s0[0] <= c0[0] <= s0[1]); chain.append({"node": "facade", "span": s0, "calls_next_at": c0})
        for h in HOPS:
            sp = span(h["file"], h["decl"]); cl = where(h["file"], h["calls_next"]) if h["calls_next"] else []; good &= bool(sp) and (not h["calls_next"] or bool(cl and sp[0] <= cl[0] <= sp[1])); chain.append({"node": f"hop{h['n']}:{h['class'].split('.')[-1]}#{h['method']}", "span": sp, "calls_next_at": cl})
        elsewhere = {h["file"].split("/")[-1]: where(h["file"], A["bug_line"]) + where(h["file"], cfg["control"]["bug_line"]) for h in HOPS[:-1]}; elsewhere[cfg["facade_file"].split("/")[-1]] = where(cfg["facade_file"], A["bug_line"]) + where(cfg["facade_file"], cfg["control"]["bug_line"]); good &= not any(elsewhere.values())
        imp = [where(i["file"], i["line"]) for i in A["new_imports"]]; good &= all(imp)
        R["gold_check"] = {"gold": f"{A['gold_class']}#{A['gold_method']}", "gold_span": gs, "buggy_line_at": b, "chain": chain, "buggy_line_elsewhere": elsewhere, "imports_at": imp, "hop_count": len(HOPS)}
        ok = step("R4", "five hops exist in order, each call inside its caller, bug physically in hop 5 only, gold matches manifest", ["static chain check"], bool(good and len(HOPS) == 5), json.dumps(R["gold_check"]))
R["overall"] = "pass" if ok and all(s["status"] == "pass" for s in R["steps"]) else "FAIL"; R["finished_at"] = time.strftime("%Y-%m-%dT%H:%M:%S%z"); save()
print(arm, "reproduction overall:", R["overall"], [(s["step"], s["status"]) for s in R["steps"]])
