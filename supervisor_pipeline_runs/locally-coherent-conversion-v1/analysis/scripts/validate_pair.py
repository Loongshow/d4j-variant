"""Config-driven local validation (gates A–P) for one arm. Usage: validate_pair.py <config.json> <control|treatment> <work> <pkg> <out_json>
Each gate is appended to the JSON only after it executes; no field is pre-filled as PASS."""
import json, os, re, subprocess, sys, time, hashlib, shutil
cfg, arm, work, pkg, out = json.load(open(sys.argv[1])), sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5]
A = cfg[arm]; TRIG = cfg["trigger"]; REL = cfg["related_test"]
env = dict(os.environ, PERL5LIB=os.path.expanduser("~/perl5/lib/perl5"))
R = {"schema_version": "locally-coherent-conversion-v1/validation/v1", "label": "NON-CANONICAL / CONSTRUCTION-VALIDATION ONLY", "arm": arm.upper() + "-01", "work_checkout": work, "package": pkg, "trigger": TRIG, "started_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "gates": []}
def save(): json.dump(R, open(out, "w"), indent=1)
def sh(cmd, timeout=1500):
    p = subprocess.run(cmd, cwd=work, capture_output=True, text=True, env=env, timeout=timeout); return p.returncode, p.stdout + p.stderr
def gate(gid, name, cmds, ok, key, note=""):
    R["gates"].append({"gate": gid, "name": name, "commands": cmds, "status": "pass" if ok else "FAIL", "key_output": key[-1200:], "note": note}); save(); return ok
def d4j_test(tid):
    rc, o = sh(["defects4j", "test", "-t", tid], timeout=600); m = re.search(r"Failing tests:\s*(\d+)", o); n = int(m.group(1)) if m else None
    ft = open(os.path.join(work, "failing_tests")).read() if os.path.exists(os.path.join(work, "failing_tests")) else ""; return rc, o, n, ft
def full_suite():
    rc, o = sh(["defects4j", "test"], timeout=1800); m = re.search(r"Failing tests:\s*(\d+)", o); n = int(m.group(1)) if m else None
    return rc, o, n, sorted(set(re.findall(r"^\s*-\s+(\S+::\S+)", o, re.M)))
def compile_():
    for d in ("target", "build", "build-tests"): shutil.rmtree(os.path.join(work, d), ignore_errors=True)
    rc, o = sh(["defects4j", "compile"], timeout=900); return rc, o, (rc == 0 and "BUILD FAILED" not in o)
def reset():
    sh(["git", "checkout", "--", "."]); rc, o = sh(["git", "status", "--short"]); return [l for l in o.splitlines() if not l.startswith("??")]
def span(path, decl):
    L = open(os.path.join(work, path)).read().split("\n"); s = next((i for i, l in enumerate(L) if decl in l), None)
    if s is None: return None
    d = 0; st = False
    for j in range(s, len(L)):
        d += L[j].count("{") - L[j].count("}"); st = st or "{" in L[j]
        if st and d == 0: return (s + 1, j + 1)
def lines_with(path, text): return [i + 1 for i, l in enumerate(open(os.path.join(work, path)).read().split("\n")) if text in l]
R["package_hashes"] = {f: hashlib.sha256(open(os.path.join(pkg, f), "rb").read()).hexdigest() for f in ("variant.patch", "test.patch")}; save()
ok = True
mods = reset(); ok = gate("A0", "clean tracked tree before start", ["git checkout -- .", "git status --short"], not mods, "\n".join(mods) or "clean") and ok
rc, o, good = compile_(); ok = gate("A", "baseline checkout compiles", ["defects4j compile"], good, o) and ok
if ok:
    rc, o, n, ft = d4j_test(REL); ok = gate("B1", f"baseline related test passes ({REL.split('::')[1]})", [f"defects4j test -t {REL}"], n == 0, o) and ok
    rc, o, n, fails = full_suite(); R["baseline_full_suite_failures"] = fails; ok = gate("B2", "baseline full suite (records pre-existing failures)", ["defects4j test"], n is not None, f"Failing tests: {n}\n" + "\n".join(fails)) and ok
if ok:
    rc, o = sh(["git", "apply", os.path.join(pkg, "test.patch")]); ok = gate("C", "apply test.patch only", ["git apply test.patch"], rc == 0, o or "applied") and ok
if ok:
    rc, o, good = compile_(); ok = gate("C2", "compiles with new test", ["defects4j compile"], good, o) and ok
if ok:
    rc, o, n, ft = d4j_test(TRIG); ok = gate("D", "new trigger passes on correct implementation", [f"defects4j test -t {TRIG}"], n == 0, o) and ok
if ok:
    rc, o = sh(["git", "apply", os.path.join(pkg, "variant.patch")]); ok = gate("E", "apply variant.patch (bug)", ["git apply variant.patch"], rc == 0, o or "applied") and ok
if ok and arm == "treatment":
    p = os.path.join(work, cfg["hop2_file"]); t = open(p).read(); assert t.count(A["bug_line"]) == 1; open(p, "w").write(t.replace(A["bug_line"], A["orig_line"], 1))
    rc, o, good = compile_(); ok = gate("M", "correct chain (hop2 with original line) compiles", ["<revert buggy line in hop2 only>", "defects4j compile"], good, o) and ok
    if ok:
        rc, o, n, ft = d4j_test(TRIG); ok = gate("N", "correct-logic trigger passes THROUGH the chain", [f"defects4j test -t {TRIG}"], n == 0, o) and ok
    t = open(p).read(); assert t.count(A["orig_line"]) == 1; open(p, "w").write(t.replace(A["orig_line"], A["bug_line"], 1)); R["hop2_bug_restored"] = open(p).read().count(A["bug_line"]) == 1; save()
if ok:
    rc, o, good = compile_(); ok = gate("F", "buggy implementation compiles", ["defects4j compile"], good, o) and ok
if ok:
    sigs = []
    for i in range(3):
        rc, o, n, ft = d4j_test(TRIG); sigs.append({"run": i + 1, "n_fail": n, "signature": "\n".join(ft.splitlines()[:2]), "failing_tests_sha256": hashlib.sha256(ft.encode()).hexdigest()})
    R["trigger_runs"] = sigs; save(); sig = sigs[0]["signature"]
    ok = gate("G", "trigger fails on buggy implementation", [f"defects4j test -t {TRIG}"], sigs[0]["n_fail"] == 1, sig) and ok
    ok = gate("H", "trigger fails deterministically 3x with identical signature", [f"defects4j test -t {TRIG} (x3)"], all(s["n_fail"] == 1 for s in sigs) and len({s["signature"] for s in sigs}) == 1, json.dumps(sigs, indent=1)) and ok
    clean = ("AssertionFailedError" in sig) and (cfg["expected_signature"] in sig) and not re.search(r"\w+Exception", sig)
    ok = gate("I", "failure is a clean value mismatch with the expected signature, no exception", ["inspect failing_tests"], clean, sig) and ok
if ok:
    rc, o, n, fails = full_suite(); base = set(R.get("baseline_full_suite_failures", [])); new = [f for f in fails if f != TRIG and f not in base]
    R["buggy_full_suite_failures"] = fails; ok = gate("J", "full-suite collateral with bug + test", ["defects4j test"], n is not None and TRIG in fails, f"Failing tests: {n}\n" + "\n".join(fails)) and ok
    ok = gate("K", "collateral equals baseline + trigger only", ["compare J vs B2"], not new, "new non-baseline failures: " + (", ".join(new) or "none")) and ok
if arm == "treatment" and ok:
    s2 = span(cfg["hop2_file"], A["gold_decl"]); bl = lines_with(cfg["hop2_file"], A["bug_line"])
    elsewhere = {f: lines_with(cfg[f], cfg["control"]["bug_line"]) + lines_with(cfg[f], A["bug_line"]) for f in ("facade_file", "hop1_file")}
    o_ok = bool(s2 and bl and all(s2[0] <= b <= s2[1] for b in bl) and not any(elsewhere.values()))
    ok = gate("O", "buggy line is physically inside hop2 (gold) and nowhere else", ["static span check"], o_ok, f"gold span {s2}, buggy line at {bl}, elsewhere {elsewhere}") and ok
    s0 = span(cfg["facade_file"], cfg["control"]["gold_decl"]); c1 = lines_with(cfg["facade_file"], A["facade_call"]); s1 = span(cfg["hop1_file"], A["hop1_decl"]); c2 = lines_with(cfg["hop1_file"], A["hop1_call"]); imp = lines_with(cfg["hop1_file"], A["hop2_import_in_hop1"])
    p_ok = bool(s0 and c1 and s0[0] <= c1[0] <= s0[1] and s1 and c2 and s1[0] <= c2[0] <= s1[1] and imp)
    ok = gate("P", "facade -> hop1 -> hop2 wiring and import correct", ["static wiring check"], p_ok, f"facade {s0} calls hop1 at {c1}; hop1 {s1} calls hop2 at {c2}; import at {imp}") and ok
mods = reset(); gate("L", "source reset cleanliness (git checkout -- .)", ["git checkout -- .", "git status --short"], not mods, "\n".join(mods) or "tracked tree clean")
R["overall"] = "pass" if ok and all(g["status"] == "pass" for g in R["gates"]) else "FAIL"; R["finished_at"] = time.strftime("%Y-%m-%dT%H:%M:%S%z"); save()
print(arm, "overall:", R["overall"], [(g["gate"], g["status"]) for g in R["gates"]])
