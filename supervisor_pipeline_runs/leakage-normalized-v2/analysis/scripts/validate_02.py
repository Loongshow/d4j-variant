"""Local validation gates A–P for one -02 arm, on a construction checkout, from the packaged patches.
Usage: validate_02.py <control|treatment> <work_checkout> <package_dir> <out_json>
Every gate is appended to the JSON only AFTER it has executed, with command, exit code and key output. No field is
pre-filled as PASS. Stops at the first hard failure (recorded) but always performs the reset gate L."""
import json, os, re, subprocess, sys, time, hashlib, shutil
arm, work, pkg, out = sys.argv[1:5]
TRIGGER = "org.apache.commons.lang3.math.NumberUtilsTest::testLang1106"
RELATED = "org.apache.commons.lang3.math.NumberUtilsTest::testCreateBigInteger"
BUG = 'str.startsWith("-") || str.startsWith("+")'; ORIG = 'str.startsWith("-")'
NU = "src/main/java/org/apache/commons/lang3/math/NumberUtils.java"; OU = "src/main/java/org/apache/commons/lang3/ObjectUtils.java"; CB = "src/main/java/org/apache/commons/lang3/builder/CompareToBuilder.java"
env = dict(os.environ, PERL5LIB=os.path.expanduser("~/perl5/lib/perl5"))
R = {"schema_version": "leakage-normalized-v2/validation/v1", "label": "NON-CANONICAL / CONSTRUCTION-VALIDATION ONLY", "arm": arm.upper() + "-02",
     "work_checkout": work, "package": pkg, "trigger": TRIGGER, "started_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "gates": []}
def save(): json.dump(R, open(out, "w"), indent=1)
def sh(cmd, timeout=1500):
    p = subprocess.run(cmd, cwd=work, capture_output=True, text=True, env=env, timeout=timeout); return p.returncode, (p.stdout + p.stderr)
def gate(gid, name, cmds, ok, key, note=""):
    R["gates"].append({"gate": gid, "name": name, "commands": cmds, "exit_codes": [], "status": "pass" if ok else "FAIL", "key_output": key[-1200:], "note": note}); save(); return ok
def d4j_test(test_id):
    rc, o = sh(["defects4j", "test", "-t", test_id], timeout=600); m = re.search(r"Failing tests:\s*(\d+)", o); n = int(m.group(1)) if m else None
    ft = open(os.path.join(work, "failing_tests")).read() if os.path.exists(os.path.join(work, "failing_tests")) else ""
    return rc, o, n, ft
def full_suite():
    rc, o = sh(["defects4j", "test"], timeout=1800); m = re.search(r"Failing tests:\s*(\d+)", o); n = int(m.group(1)) if m else None
    fails = sorted(set(re.findall(r"^\s*-\s+(\S+::\S+)", o, re.M))); return rc, o, n, fails
def compile_():
    for dname in ("target", "build", "build-tests"):
        shutil.rmtree(os.path.join(work, dname), ignore_errors=True)
    rc, o = sh(["defects4j", "compile"], timeout=900); return rc, o, (rc == 0 and "BUILD FAILED" not in o)
def reset():
    sh(["git", "checkout", "--", "."]); rc, o = sh(["git", "status", "--short"]); return [l for l in o.splitlines() if not l.startswith("??")]
def span(path, decl):
    lines = open(os.path.join(work, path)).read().split("\n"); s = next((i for i, l in enumerate(lines) if decl in l), None)
    if s is None: return None
    depth = 0; started = False
    for j in range(s, len(lines)):
        depth += lines[j].count("{") - lines[j].count("}"); started = started or "{" in lines[j]
        if started and depth == 0: return (s + 1, j + 1)
    return None
def line_of(path, text):
    lines = open(os.path.join(work, path)).read().split("\n"); return [i + 1 for i, l in enumerate(lines) if text in l]

R["package_hashes"] = {f: hashlib.sha256(open(os.path.join(pkg, f), "rb").read()).hexdigest() for f in ("variant.patch", "test.patch")}; save()
ok = True
mods = reset(); ok = gate("A0", "clean tracked tree before start", ["git checkout -- .", "git status --short"], not mods, "\n".join(mods) or "clean") and ok
rc, o, good = compile_(); ok = gate("A", "baseline checkout compiles", ["defects4j compile"], good, o) and ok
if ok:
    rc, o, n, ft = d4j_test(RELATED); ok = gate("B1", "baseline related test passes (testCreateBigInteger)", [f"defects4j test -t {RELATED}"], n == 0, o) and ok
    rc, o, n, fails = full_suite(); R["baseline_full_suite_failures"] = fails; ok = gate("B2", "baseline full suite (records pre-existing failures)", ["defects4j test"], n is not None, f"Failing tests: {n}\n" + "\n".join(fails), f"{n} pre-existing failures") and ok
if ok:
    rc, o = sh(["git", "apply", os.path.join(pkg, "test.patch")]); ok = gate("C", "apply test.patch only (correct implementation)", ["git apply test.patch"], rc == 0, o or "applied") and ok
if ok:
    rc, o, good = compile_(); ok = gate("C2", "compiles with new test", ["defects4j compile"], good, o) and ok
if ok:
    rc, o, n, ft = d4j_test(TRIGGER); ok = gate("D", "new trigger passes on correct implementation", [f"defects4j test -t {TRIGGER}"], n == 0, o) and ok
if ok:
    rc, o = sh(["git", "apply", os.path.join(pkg, "variant.patch")]); ok = gate("E", "apply variant.patch (bug)", ["git apply variant.patch"], rc == 0, o or "applied") and ok
if ok and arm == "treatment":
    # M/N: correct chain (bug reverted in hop2 only) must compile and pass the trigger through the chain
    p = os.path.join(work, CB); t = open(p).read(); assert t.count(BUG) == 1; open(p, "w").write(t.replace(BUG, ORIG, 1))
    rc, o, good = compile_(); ok = gate("M", "correct chain (hop2 with original line) compiles", ["<revert buggy line in hop2 only>", "defects4j compile"], good, o) and ok
    if ok:
        rc, o, n, ft = d4j_test(TRIGGER); ok = gate("N", "correct-logic trigger passes THROUGH the chain", [f"defects4j test -t {TRIGGER}"], n == 0, o) and ok
    t = open(p).read(); assert t.count(ORIG) == 1 and BUG not in t; open(p, "w").write(t.replace(ORIG, BUG, 1)); R["hop2_bug_restored"] = open(p).read().count(BUG) == 1; save()
if ok:
    rc, o, good = compile_(); ok = gate("F", "buggy implementation compiles", ["defects4j compile"], good, o) and ok
if ok:
    sigs = []
    for i in range(3):
        rc, o, n, ft = d4j_test(TRIGGER); first = "\n".join(ft.splitlines()[:2]); sigs.append({"run": i + 1, "n_fail": n, "signature": first, "failing_tests_sha256": hashlib.sha256(ft.encode()).hexdigest()})
    R["trigger_runs"] = sigs; save()
    ok = gate("G", "trigger fails on buggy implementation", [f"defects4j test -t {TRIGGER}"], sigs[0]["n_fail"] == 1, sigs[0]["signature"]) and ok
    ok = gate("H", "trigger fails deterministically 3x with identical signature", [f"defects4j test -t {TRIGGER} (x3)"], all(s["n_fail"] == 1 for s in sigs) and len({s["signature"] for s in sigs}) == 1, json.dumps(sigs, indent=1)) and ok
    sig = sigs[0]["signature"]; clean = ("AssertionFailedError" in sig) and ("expected:<1234> but was:<-1234>" in sig) and not re.search(r"\w+Exception", sig)
    ok = gate("I", "failure is a clean value mismatch, no exception", ["inspect failing_tests"], clean, sig) and ok
if ok:
    rc, o, n, fails = full_suite(); base = set(R.get("baseline_full_suite_failures", [])); new = [f for f in fails if f != TRIGGER and f not in base]
    R["buggy_full_suite_failures"] = fails; ok = gate("J", "full-suite collateral with bug + test", ["defects4j test"], n is not None and TRIGGER in fails, f"Failing tests: {n}\n" + "\n".join(fails)) and ok
    ok = gate("K", "collateral equals baseline + trigger only", ["compare J vs B2"], not new, "new non-baseline failures: " + (", ".join(new) or "none")) and ok
if arm == "treatment" and ok:
    s2 = span(CB, "public static BigInteger decodeMagnitude(final String str)"); bl = line_of(CB, BUG)
    o_ok = bool(s2 and bl and all(s2[0] <= b <= s2[1] for b in bl) and not line_of(NU, BUG) and not line_of(OU, BUG))
    ok = gate("O", "buggy line is physically inside hop2 (CompareToBuilder#decodeMagnitude) and nowhere else", ["static span check"], o_ok, f"decodeMagnitude span {s2}, buggy line(s) at {bl}; in NumberUtils {line_of(NU, BUG)}, in ObjectUtils {line_of(OU, BUG)}") and ok
    s0 = span(NU, "public static BigInteger createBigInteger(final String str)"); c1 = line_of(NU, "return ObjectUtils.resolveWholeValue(str);"); s1 = span(OU, "public static BigInteger resolveWholeValue(final String str)"); c2 = line_of(OU, "return CompareToBuilder.decodeMagnitude(str);")
    p_ok = bool(s0 and c1 and s0[0] <= c1[0] <= s0[1] and s1 and c2 and s1[0] <= c2[0] <= s1[1] and line_of(NU, "import org.apache.commons.lang3.ObjectUtils;") and line_of(OU, "import org.apache.commons.lang3.builder.CompareToBuilder;") and line_of(OU, "import java.math.BigInteger;") and line_of(CB, "import java.math.BigInteger;"))
    ok = gate("P", "facade -> hop1 -> hop2 wiring and imports correct", ["static wiring check"], p_ok, f"facade span {s0} calls hop1 at {c1}; hop1 span {s1} calls hop2 at {c2}") and ok
mods = reset(); gate("L", "source reset cleanliness (git checkout -- .)", ["git checkout -- .", "git status --short"], not mods, "\n".join(mods) or "tracked tree clean (untracked D4J build outputs may remain)")
R["overall"] = "pass" if ok and all(g["status"] == "pass" for g in R["gates"]) else "FAIL"; R["finished_at"] = time.strftime("%Y-%m-%dT%H:%M:%S%z"); save()
print(arm, "overall:", R["overall"], "|", [(g["gate"], g["status"]) for g in R["gates"]])
