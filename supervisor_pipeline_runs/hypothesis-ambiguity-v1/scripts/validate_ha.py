"""Config-driven local validation for one arm of the HA pair (Phase 10). Usage: validate_ha.py <config.json> <low|high> <work> <pkg> <out_json>
Every gate is appended only after it executes. NON-CANONICAL / HYPOTHESIS-AMBIGUITY EXPERIMENT."""
import json, os, re, subprocess, sys, time, hashlib, shutil, tempfile
cfg, arm, work, pkg, out = json.load(open(sys.argv[1])), sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5]
A = cfg[arm]; TRIG = cfg["trigger"]; REL = cfg["related_test"]; VID = cfg["low_id" if arm == "low" else "high_id"]
env = dict(os.environ, PERL5LIB=os.path.expanduser("~/perl5/lib/perl5"))
R = {"schema_version": "hypothesis-ambiguity-v1/validation/v1", "label": cfg["label"], "arm": arm.upper(), "variant_id": VID, "work_checkout": work, "package": pkg, "trigger": TRIG, "started_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "gates": []}
def save(): json.dump(R, open(out, "w"), indent=1)
def sh(cmd, timeout=1500):
    p = subprocess.run(cmd, cwd=work, capture_output=True, text=True, env=env, timeout=timeout); return p.returncode, p.stdout + p.stderr
def gate(gid, name, cmds, ok, key, note=""):
    R["gates"].append({"gate": gid, "name": name, "commands": cmds, "status": "pass" if ok else "FAIL", "key_output": key[-1500:], "note": note}); save(); print(gid, "pass" if ok else "FAIL", flush=True); return ok
def d4j_test(tid):
    rc, o = sh(["defects4j", "test", "-t", tid], timeout=600); m = re.search(r"Failing tests:\s*(\d+)", o); n = int(m.group(1)) if m else None
    ft = open(os.path.join(work, "failing_tests")).read() if os.path.exists(os.path.join(work, "failing_tests")) else ""; return rc, o, n, ft
def full_suite():
    rc, o = sh(["defects4j", "test"], timeout=2400); m = re.search(r"Failing tests:\s*(\d+)", o); n = int(m.group(1)) if m else None
    return rc, o, n, sorted(set(re.findall(r"^\s*-\s+(\S+::\S+)", o, re.M)))
def compile_():
    for d in ("target", "build", "build-tests"): shutil.rmtree(os.path.join(work, d), ignore_errors=True)
    rc, o = sh(["defects4j", "compile"], timeout=900); return rc, o, (rc == 0 and "BUILD FAILED" not in o)
def reset():
    sh(["git", "reset", "--", "."]); sh(["git", "checkout", "--", "."]); sh(["git", "clean", "-fdq", "--", "src/main/java", "src/test/java"]); rc, o = sh(["git", "status", "--short"]); return [l for l in o.splitlines() if not l.startswith("??")]
def text(path): return open(os.path.join(work, path)).read()
def span(path, decl):
    L = text(path).split("\n"); s = next((i for i, l in enumerate(L) if decl in l), None)
    if s is None: return None
    d = 0; st = False
    for j in range(s, len(L)):
        d += L[j].count("{") - L[j].count("}"); st = st or "{" in L[j]
        if st and d == 0: return (s + 1, j + 1)
def lines_with(path, t): return [i + 1 for i, l in enumerate(text(path).split("\n")) if t in l]
def swap_line(path, old, new):
    t = text(path); assert t.count(old) == 1, (path, old, t.count(old)); open(os.path.join(work, path), "w").write(t.replace(old, new, 1))
R["package_hashes"] = {f: hashlib.sha256(open(os.path.join(pkg, f), "rb").read()).hexdigest() for f in ("variant.patch", "test.patch")}; save()
ok = True
mods = reset(); ok = gate("A0", "clean tracked tree before start", ["git reset -- .", "git checkout -- .", "git clean -fdq src", "git status --short"], not mods, "\n".join(mods) or "clean") and ok
rc, o, good = compile_(); ok = gate("A", "baseline checkout compiles", ["defects4j compile"], good, o) and ok
if ok:
    rc, o, n, ft = d4j_test(REL); ok = gate("B1", f"baseline related test passes ({REL.split('::')[1]})", [f"defects4j test -t {REL}"], n == 0, o) and ok
    rc, o, n, fails = full_suite(); R["baseline_full_suite_failures"] = fails; R["baseline_full_suite_n"] = n; R["baseline_tests_executed"] = (re.search(r"Tests run:\s*(\d+)", o) or [None, None])[1]
    ok = gate("B2", "baseline full suite (records pre-existing failures)", ["defects4j test"], n is not None, f"Failing tests: {n}\n" + "\n".join(fails)) and ok
if ok:
    rc, o = sh(["git", "apply", os.path.join(pkg, "test.patch")]); ok = gate("C", "apply test.patch only", ["git apply test.patch"], rc == 0, o or "applied") and ok
if ok:
    rc, o, good = compile_(); ok = gate("C2", "compiles with new test", ["defects4j compile"], good, o) and ok
if ok:
    rc, o, n, ft = d4j_test(TRIG); ok = gate("D", "new trigger passes on the original (correct) implementation", [f"defects4j test -t {TRIG}"], n == 0, o) and ok
if ok:
    rc, o = sh(["git", "apply", os.path.join(pkg, "variant.patch")]); ok = gate("E", "apply variant.patch (chain + bug)", ["git apply variant.patch"], rc == 0, o or "applied") and ok
if ok:
    swap_line(cfg["gold_file"], cfg["bug_line"], cfg["orig_line"])
    rc, o, good = compile_(); ok = gate("M", "correct chain (gold with the original floor line) compiles", ["<swap buggy line for the correct line in the gold only>", "defects4j compile"], good, o) and ok
    if ok:
        rc, o, n, ft = d4j_test(TRIG); ok = gate("N", "correct-logic trigger passes THROUGH the chain (both assertions)", [f"defects4j test -t {TRIG}"], n == 0, o) and ok
    if ok:
        rc, o, n, ft = d4j_test(REL); ok = gate("N1", "related sibling test passes through the chain", [f"defects4j test -t {REL}"], n == 0, o) and ok
    if ok:
        rc, o, n, fails = full_suite(); base = set(R.get("baseline_full_suite_failures", [])); new = [f for f in fails if f not in base]; R["correct_chain_full_suite_failures"] = fails
        ok = gate("N2", "FULL suite on the correct chain equals the baseline failure set (behavioural equivalence of the refactor)", ["defects4j test"], n is not None and not new and set(fails) == base, f"Failing tests: {n}\nnew vs baseline: {new or 'none'}") and ok
    swap_line(cfg["gold_file"], cfg["orig_line"], cfg["bug_line"]); R["gold_bug_restored"] = text(cfg["gold_file"]).count(cfg["bug_line"]) == 1; save()
if ok:
    rc, o, good = compile_(); ok = gate("F", "buggy implementation compiles", ["defects4j compile"], good, o) and ok
if ok:
    sigs = []
    for i in range(3):
        rc, o, n, ft = d4j_test(TRIG); sigs.append({"run": i + 1, "n_fail": n, "signature": "\n".join(ft.splitlines()[:2]), "failing_tests_sha256": hashlib.sha256(ft.encode()).hexdigest()})
    R["trigger_runs"] = sigs; save(); sig = sigs[0]["signature"]
    ok = gate("G", "trigger fails on the buggy implementation", [f"defects4j test -t {TRIG}"], sigs[0]["n_fail"] == 1, sig) and ok
    ok = gate("H", "trigger fails deterministically 3x with identical signature", [f"defects4j test -t {TRIG} (x3)"], all(s["n_fail"] == 1 for s in sigs) and len({s["signature"] for s in sigs}) == 1, json.dumps(sigs, indent=1)) and ok
    clean = ("AssertionFailedError" in sig or "AssertionError" in sig) and (cfg["expected_signature"] in sig) and not re.search(r"\w+Exception", sig)
    ok = gate("I", "failure is a clean value mismatch with the expected signature, no exception", ["inspect failing_tests"], clean, sig) and ok
if ok:
    rc, o, n, fails = full_suite(); base = set(R.get("baseline_full_suite_failures", [])); new = [f for f in fails if f != TRIG and f not in base]
    R["buggy_full_suite_failures"] = fails; ok = gate("J", "full-suite collateral with bug + test", ["defects4j test"], n is not None and TRIG in fails, f"Failing tests: {n}\n" + "\n".join(fails)) and ok
    ok = gate("K", "collateral equals baseline + trigger only", ["compare J vs B2"], not new, "new non-baseline failures: " + (", ".join(new) or "none")) and ok
if ok:
    gs = span(cfg["gold_file"], cfg["gold_decl"]); bl = lines_with(cfg["gold_file"], cfg["bug_line"])
    others = {f: lines_with(f, cfg["bug_line"]) for f in (cfg["facade_file"], cfg["hop1"]["file"], "src/main/java/org/apache/commons/lang3/math/NumberUtils.java")}
    ok = gate("O", "buggy line is physically inside the gold and nowhere else", ["static span check"], bool(gs and bl and all(gs[0] <= b <= gs[1] for b in bl) and not any(others.values())), f"gold span {gs}, buggy line at {bl}, elsewhere {others}") and ok
    s0 = span(cfg["facade_file"], cfg["facade_decl"]); c0 = lines_with(cfg["facade_file"], cfg["facade_call"]); sp = span(cfg["hop1"]["file"], cfg["hop1"]["decl"]); cg = lines_with(cfg["hop1"]["file"], cfg["hop1"]["calls_gold"])
    wiring = {"facade_span": s0, "facade_call": c0, "pack_span": sp, "pack_calls_gold": cg, "candidates": []}; good = bool(s0 and c0 and s0[0] <= c0[0] <= s0[1] and sp and cg and sp[0] <= cg[0] <= sp[1])
    for c in A["candidates"]:
        cs = span(c["file"], c["decl"]); cl = lines_with(cfg["hop1"]["file"], c["called_as"]); good &= bool(cs and cl and sp[0] <= cl[0] <= sp[1]); wiring["candidates"].append({"method": c["method"], "span": cs, "called_from_pack_at": cl})
    il = lines_with(cfg["new_import"]["file"], cfg["new_import"]["line"]); good &= bool(il); wiring["import_at"] = il
    ok = gate("P", "wiring: facade -> pack -> gold; every candidate declared and called from inside pack; import present", ["static wiring check"], good, json.dumps(wiring)) and ok
    def body(f, decl): s = span(f, decl); return [l.strip() for l in text(f).split("\n")[s[0]:s[1] - 1] if l.strip() and not l.strip().startswith(("/", "*", "}"))]
    def params(decl): return set(re.findall(r"final \w+(?:\[\])? (\w+)", decl))
    pb = body(cfg["hop1"]["file"], cfg["hop1"]["decl"]); cb = {c["method"]: (body(c["file"], c["decl"]), params(c["decl"])) for c in A["candidates"]}; gb = body(cfg["gold_file"], cfg["gold_decl"])
    # real work = at least one operator or call in the body, and the body is not a bare return of one of the method's own parameters
    real = lambda b, ps: any(re.search(r"[-+*/%&|<>]|\w+\(", l) for l in b) and not (len(b) == 1 and re.fullmatch(r"return (\w+);", b[0]) and re.fullmatch(r"return (\w+);", b[0]).group(1) in ps)
    ok = gate("Q", "pack has >= 3 statements; every candidate performs real work (operator or call, not a bare parameter return); gold holds the lane arithmetic", ["static body check"], len(pb) >= 3 and all(real(b, ps) for b, ps in cb.values()) and ("Integer.SIZE" in "\n".join(gb) and "/" in "\n".join(gb)), json.dumps({"pack": len(pb), "candidates": {k: {"statements": len(v[0]), "params": sorted(v[1]), "body": v[0]} for k, v in cb.items()}, "gold": gb})) and ok
    # R: dynamic participation probe compiled against target/classes
    probe_dir = tempfile.mkdtemp(prefix="haprobe_"); cands_expr = ("int off = BitField.offset(8); int w = ArrayUtils.advance(lane, 0); long viaCands = NumberUtils.deposit(0L, src[1], w, off);" if arm == "high" else "int[] run = ArrayUtils.gather(src, 1, 1); long viaCands = NumberUtils.merge(0L, BitField.widen(run[0]), (lane + 0) * Integer.SIZE + 8 % Integer.SIZE);")
    java = ("import org.apache.commons.lang3.*; import org.apache.commons.lang3.math.NumberUtils;\npublic class HAProbe { public static void main(String[] a) {\n int[] src = {0x1CDF1F0C, 0x00123456, 0x78000000};\n long viaFacade = Conversion.intArrayToLong(src, 1, 0L, 8, 1); long viaPack = ArrayUtils.pack(src, 1, 1, 0L, 8); int lane = BitField.lane(8);\n " + cands_expr + "\n System.out.println(viaFacade + \" \" + viaPack + \" \" + viaCands + \" \" + lane); } }\n")
    open(os.path.join(probe_dir, "HAProbe.java"), "w").write(java); cp = os.path.join(work, "target/classes")
    p1 = subprocess.run(["javac", "-cp", cp, "-d", probe_dir, os.path.join(probe_dir, "HAProbe.java")], capture_output=True, text=True); p2 = subprocess.run(["java", "-cp", cp + ":" + probe_dir, "HAProbe"], capture_output=True, text=True)
    vals = p2.stdout.split(); exp_buggy = "1311767949471645696"
    ok = gate("R", "dynamic participation: facade, pack and the candidate composition all reproduce the observed buggy value; lane(8) == 1", ["javac/java probe against target/classes"], p1.returncode == 0 and p2.returncode == 0 and len(vals) == 4 and vals[0] == vals[1] == vals[2] == exp_buggy and vals[3] == "1", p1.stderr + p2.stdout + p2.stderr) and ok
    shutil.rmtree(probe_dir, ignore_errors=True)
mods = reset(); gate("L", "source reset cleanliness", ["git reset -- .", "git checkout -- .", "git clean -fdq src", "git status --short"], not mods, "\n".join(mods) or "tracked tree clean")
R["overall"] = "pass" if ok and all(g["status"] == "pass" for g in R["gates"]) else "FAIL"; R["finished_at"] = time.strftime("%Y-%m-%dT%H:%M:%S%z"); save()
print(arm, "validation overall:", R["overall"], [(g["gate"], g["status"]) for g in R["gates"]])
