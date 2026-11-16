"""Fresh-checkout reproduction from packaged patches only (Phase 11). Usage: repro_ha.py <config.json> <low|high> <fresh_checkout> <pkg_dir> <out_json>"""
import json, os, re, subprocess, sys, time, hashlib, shutil
cfg, arm, co, pkg, out = json.load(open(sys.argv[1])), sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5]
A = cfg[arm]; TRIG = cfg["trigger"]; env = dict(os.environ, PERL5LIB=os.path.expanduser("~/perl5/lib/perl5"))
R = {"schema_version": "hypothesis-ambiguity-v1/reproduction/v1", "label": cfg["label"], "arm": arm.upper(), "variant_id": cfg["low_id" if arm == "low" else "high_id"], "fresh_checkout": co, "package": pkg, "steps": [], "started_at": time.strftime("%Y-%m-%dT%H:%M:%S%z")}
def save(): json.dump(R, open(out, "w"), indent=1)
def sh(cmd, timeout=900):
    p = subprocess.run(cmd, cwd=co, capture_output=True, text=True, env=env, timeout=timeout); return p.returncode, p.stdout + p.stderr
def step(sid, name, cmds, ok, key): R["steps"].append({"step": sid, "name": name, "commands": cmds, "status": "pass" if ok else "FAIL", "key_output": key[-1200:]}); save(); print(sid, "pass" if ok else "FAIL", flush=True); return ok
def L(path): return open(os.path.join(co, path)).read().split("\n")
def span(path, decl):
    Ls = L(path); s = next((i for i, l in enumerate(Ls) if decl in l), None)
    if s is None: return None
    d = 0; st = False
    for j in range(s, len(Ls)):
        d += Ls[j].count("{") - Ls[j].count("}"); st = st or "{" in Ls[j]
        if st and d == 0: return (s + 1, j + 1)
def where(path, text): return [i + 1 for i, l in enumerate(L(path)) if text in l]
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
        rc, o = sh(["defects4j", "test", "-t", TRIG], timeout=600); m = re.search(r"Failing tests:\s*(\d+)", o); n = int(m.group(1)) if m else None
        ft = open(os.path.join(co, "failing_tests")).read() if os.path.exists(os.path.join(co, "failing_tests")) else ""; sigs.append({"run": i + 1, "n_fail": n, "signature": "\n".join(ft.splitlines()[:2]), "failing_tests_sha256": hashlib.sha256(ft.encode()).hexdigest()})
    R["trigger_runs"] = sigs
    ok = step("R3", "trigger fails deterministically 3x with the expected value-mismatch signature", [f"defects4j test -t {TRIG} (x3)"], all(s["n_fail"] == 1 for s in sigs) and len({s["signature"] for s in sigs}) == 1 and cfg["expected_signature"] in sigs[0]["signature"], json.dumps(sigs, indent=1))
if ok:
    gs = span(cfg["gold_file"], cfg["gold_decl"]); b = where(cfg["gold_file"], cfg["bug_line"]); good = bool(gs and b and all(gs[0] <= x <= gs[1] for x in b))
    s0 = span(cfg["facade_file"], cfg["facade_decl"]); c0 = where(cfg["facade_file"], cfg["facade_call"]); good &= bool(s0 and c0 and s0[0] <= c0[0] <= s0[1])
    sp = span(cfg["hop1"]["file"], cfg["hop1"]["decl"]); cg = where(cfg["hop1"]["file"], cfg["hop1"]["calls_gold"]); good &= bool(sp and cg and sp[0] <= cg[0] <= sp[1])
    cands = []
    for c in A["candidates"]:
        cs = span(c["file"], c["decl"]); cl = where(cfg["hop1"]["file"], c["called_as"]); cands.append({"method": c["method"], "span": cs, "called_from_pack_at": cl}); good &= bool(cs and cl and sp[0] <= cl[0] <= sp[1])
    elsewhere = {f: where(f, cfg["bug_line"]) for f in (cfg["facade_file"], cfg["hop1"]["file"], "src/main/java/org/apache/commons/lang3/math/NumberUtils.java")}
    good &= not any(elsewhere.values()); imp = where(cfg["new_import"]["file"], cfg["new_import"]["line"]); good &= bool(imp)
    R["structure_check"] = {"gold_span": gs, "buggy_line_at": b, "facade_span": s0, "facade_call_at": c0, "pack_span": sp, "pack_calls_gold_at": cg, "candidates": cands, "buggy_line_elsewhere": elsewhere, "import_at": imp}
    ok = step("R4", "gold, buggy line, facade->pack->gold wiring, every candidate declared and called from pack, import present, bug nowhere else", ["static structure check"], good, json.dumps(R["structure_check"]))
R["overall"] = "pass" if ok and all(s["status"] == "pass" for s in R["steps"]) else "FAIL"; R["finished_at"] = time.strftime("%Y-%m-%dT%H:%M:%S%z"); save()
print(arm, "reproduction overall:", R["overall"], [(s["step"], s["status"]) for s in R["steps"]])
