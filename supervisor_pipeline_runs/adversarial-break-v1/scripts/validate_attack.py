"""General validator for one adversarial attack variant (no chain assumptions).
Usage: validate_attack.py <attack.json> <work-checkout> <out.json>
attack.json: variant_id, project, trigger, related_tests[], test_file, expected_signature (substring that must appear in
the failure text; may be coarse), assertion_class_regex, gold{class,method,file,decl,bug_line,orig_line}, package_dir.
Gates: A0 clean, A baseline compile, B2 baseline suite, C test.patch applies, C2 compiles, D trigger passes on original,
E variant.patch applies, F buggy compiles, G/H trigger fails x3 with one signature, I signature matches, J/K collateral ==
baseline + trigger, S gold-line-restored build passes the trigger (the declared gold line is a sufficient fix), L reset."""
import json, os, re, subprocess, sys, time, hashlib, shutil
cfg, work, out = json.load(open(sys.argv[1])), sys.argv[2], sys.argv[3]
G = cfg["gold"]; TRIG = cfg["trigger"]; pkg = cfg["package_dir"]
env = dict(os.environ, PERL5LIB=os.path.expanduser("~/perl5/lib/perl5"))
R = {"schema_version": "adversarial-break-v1/validation/v1", "variant_id": cfg["variant_id"], "project": cfg["project"], "work": work, "trigger": TRIG,
     "started_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "gates": []}
def save(): json.dump(R, open(out, "w"), indent=1)
def sh(cmd, timeout=1800):
    p = subprocess.run(cmd, cwd=work, capture_output=True, text=True, env=env, timeout=timeout); return p.returncode, p.stdout + p.stderr
def gate(gid, name, ok, key, note=""):
    R["gates"].append({"gate": gid, "name": name, "status": "pass" if ok else "FAIL", "key_output": key[-1500:], "note": note}); save(); print(gid, "pass" if ok else "FAIL", flush=True); return ok
def d4j_test(tid):
    rc, o = sh(["defects4j", "test", "-t", tid], timeout=900); m = re.search(r"Failing tests:\s*(\d+)", o); n = int(m.group(1)) if m else None
    ft = open(os.path.join(work, "failing_tests")).read() if os.path.exists(os.path.join(work, "failing_tests")) else ""; return rc, o, n, ft
def full_suite():
    rc, o = sh(["defects4j", "test"], timeout=3000); m = re.search(r"Failing tests:\s*(\d+)", o); n = int(m.group(1)) if m else None
    return rc, o, n, sorted(set(re.findall(r"^\s*-\s+(\S+::\S+)", o, re.M)))
def compile_():
    for d in ("target", "build", "build-tests"): shutil.rmtree(os.path.join(work, d), ignore_errors=True)
    rc, o = sh(["defects4j", "compile"], timeout=1200); return rc, o, (rc == 0 and "BUILD FAILED" not in o)
def reset():
    sh(["git", "reset", "-q", "--", "."]); sh(["git", "checkout", "--", "."]); sh(["git", "clean", "-fdq", "--", "src", "tests", "source"]); rc, o = sh(["git", "status", "--short"]); return [l for l in o.splitlines() if not l.startswith("??")]
def text(path): return open(os.path.join(work, path), "rb").read().decode("utf-8").replace("\r\n", "\n")
def swap_line(path, old, new):
    raw = open(os.path.join(work, path), "rb").read().decode("utf-8"); eol = "\r\n" if "\r\n" in raw else "\n"; t = raw.replace("\r\n", "\n"); assert t.count(old) == 1, (path, old, t.count(old))
    open(os.path.join(work, path), "wb").write(t.replace(old, new, 1).replace("\n", eol).encode("utf-8"))
R["package_hashes"] = {f: hashlib.sha256(open(os.path.join(pkg, f), "rb").read()).hexdigest() for f in ("variant.patch", "test.patch")}; save()
ok = True
mods = reset(); ok = gate("A0", "clean tracked tree", not mods, "\n".join(mods) or "clean") and ok
rc, o, good = compile_(); ok = gate("A", "baseline compiles", good, o) and ok
if ok:
    rc, o, n, fails = full_suite(); R["baseline_full_suite_failures"] = fails; R["baseline_full_suite_n"] = n
    ok = gate("B2", "baseline full suite recorded", n is not None, f"Failing tests: {n}\n" + "\n".join(fails)) and ok
TRIG_PATCH = cfg.get("trigger_only_test_patch") or os.path.join(pkg, "test.patch")   # companion tests of NEW production code may live in test.patch; gates C/C2/D use the trigger-only part
if ok:
    rc, o = sh(["git", "apply", TRIG_PATCH]); ok = gate("C", "trigger test patch applies" + (" (trigger-only part; full test.patch carries companion tests of new production code)" if TRIG_PATCH != os.path.join(pkg, "test.patch") else ""), rc == 0, o or "applied") and ok
if ok:
    rc, o, good = compile_(); ok = gate("C2", "compiles with new test", good, o) and ok
if ok:
    rc, o, n, ft = d4j_test(TRIG); ok = gate("D", "trigger passes on the original implementation", n == 0, o) and ok
    for rel in cfg.get("related_tests") or []:
        rc, o, n, ft = d4j_test(rel); ok = gate("D1", f"related test passes on original ({rel.split('::')[-1]})", n == 0, o) and ok
if ok and TRIG_PATCH != os.path.join(pkg, "test.patch"):
    sh(["git", "checkout", "--", "."]); sh(["git", "clean", "-fdq", "--", "src", "tests", "source"])
    rc, o = sh(["git", "apply", os.path.join(pkg, "test.patch")]); ok = gate("C3", "full test.patch (trigger + companion tests) applies", rc == 0, o or "applied") and ok
if ok:
    rc, o = sh(["git", "apply", os.path.join(pkg, "variant.patch")]); ok = gate("E", "variant.patch applies", rc == 0, o or "applied") and ok
if ok:
    rc, o, good = compile_(); ok = gate("F", "buggy implementation compiles", good, o) and ok
if ok:
    sigs = []
    for i in range(3):
        rc, o, n, ft = d4j_test(TRIG); sigs.append({"run": i + 1, "n_fail": n, "signature": "\n".join(ft.splitlines()[:3]), "failing_tests_sha256": hashlib.sha256(ft.encode()).hexdigest()})
    R["trigger_runs"] = sigs; save(); sig = sigs[0]["signature"]
    ok = gate("G", "trigger fails on the buggy implementation", sigs[0]["n_fail"] == 1, sig) and ok
    ok = gate("H", "deterministic x3, identical signature", all(s["n_fail"] == 1 for s in sigs) and len({s["failing_tests_sha256"] for s in sigs}) == 1, json.dumps(sigs, indent=1)) and ok
    clean = bool(re.search(cfg["assertion_class_regex"], sig)) and (cfg["expected_signature"] in sig)
    ok = gate("I", "failure signature matches the pre-registered expectation", clean, sig) and ok
if ok:
    rc, o, n, fails = full_suite(); base = set(R.get("baseline_full_suite_failures", [])); new = [f for f in fails if f != TRIG and f not in base]
    R["buggy_full_suite_failures"] = fails
    ok = gate("J", "full suite with bug: trigger fails", n is not None and TRIG in fails, f"Failing tests: {n}\n" + "\n".join(fails)) and ok
    ok = gate("K", "collateral equals baseline + trigger only" + (" (declared extra collateral allowed)" if cfg.get("allowed_collateral") else ""),
              all(f in (cfg.get("allowed_collateral") or []) for f in new), "new non-baseline failures: " + (", ".join(new) or "none")) and ok
if ok:
    swap_line(G["file"], G["bug_line"], G["orig_line"]); rc, o, good = compile_()
    if good:
        rc, o, n, ft = d4j_test(TRIG); ok = gate("S", "restoring ONLY the declared gold line makes the trigger pass (gold is a sufficient fix)", n == 0, o) and ok
    else: ok = gate("S", "gold-restored build compiles", False, o) and ok
    swap_line(G["file"], G["orig_line"], G["bug_line"])
    gs = text(G["file"]); ok = gate("O", "declared buggy line present exactly once in the declared gold file", gs.count(G["bug_line"]) == 1, f"count={gs.count(G['bug_line'])}") and ok
mods = reset(); gate("L", "reset cleanliness", not mods, "\n".join(mods) or "clean")
R["overall"] = "pass" if ok and all(g["status"] == "pass" for g in R["gates"]) else "FAIL"; R["finished_at"] = time.strftime("%Y-%m-%dT%H:%M:%S%z"); save()
print(cfg["variant_id"], "overall:", R["overall"], [(g["gate"], g["status"]) for g in R["gates"]])
