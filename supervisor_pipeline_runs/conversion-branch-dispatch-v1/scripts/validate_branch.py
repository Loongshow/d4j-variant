"""Config-driven local validation for one arm of the branch-dispatch pair. Usage: validate_branch.py <config.json> <control|treatment> <work> <pkg> <out_json>
Each gate is appended to the JSON only after it executes; no field is pre-filled as PASS. NON-CANONICAL / BRANCH-DISPATCH DIAGNOSTIC. Adds gates DI/DW (two-implementation dispatch integrity and wiring) and BP1/BP2 (two-branch Java probe on the correct and on the buggy build)."""
import json, os, re, subprocess, sys, time, hashlib, shutil
cfg, arm, work, pkg, out = json.load(open(sys.argv[1])), sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5]
A = cfg[arm]; TRIG = cfg["trigger"]; REL = cfg["related_test"]; HOPS = cfg["treatment"]["hops"]
env = dict(os.environ, PERL5LIB=os.path.expanduser("~/perl5/lib/perl5"))
R = {"schema_version": "conversion-branch-dispatch-v1/validation/v1", "label": cfg["label"], "arm": arm.upper(), "synthetic_call_hops": 5 if arm == "treatment" else 0, "work_checkout": work, "package": pkg, "trigger": TRIG, "started_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "gates": []}
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
    sh(["git", "reset", "-q", "--", "."]); sh(["git", "checkout", "--", "."]); sh(["git", "clean", "-fdq", "--", "src/main/java", "src/test/java"]); rc, o = sh(["git", "status", "--short"]); return [l for l in o.splitlines() if not l.startswith("??")]
def span(path, decl):
    L = open(os.path.join(work, path)).read().split("\n"); s = next((i for i, l in enumerate(L) if decl in l), None)
    if s is None: return None
    d = 0; st = False
    for j in range(s, len(L)):
        d += L[j].count("{") - L[j].count("}"); st = st or "{" in L[j]
        if st and d == 0: return (s + 1, j + 1)
def lines_with(path, text): return [i + 1 for i, l in enumerate(open(os.path.join(work, path)).read().split("\n")) if text in l]
PROBE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "BranchProbe.java")
def probe():
    pd = os.path.join(work, "target", "branch-probe"); shutil.rmtree(pd, ignore_errors=True); os.makedirs(pd)
    rc, o = sh(["javac", "-cp", os.path.join(work, "target", "classes"), "-d", pd, PROBE], timeout=300)
    if rc != 0: return rc, o, {}
    rc, o = sh(["java", "-cp", os.path.join(work, "target", "classes") + ":" + pd, "BranchProbe"], timeout=300)
    kv = dict(l.split("=", 1) for l in o.splitlines() if "=" in l and not l.startswith(" ")); return rc, o, kv
def probe_ok(kv, buggy):
    base = kv.get("sel32") == "StandardFolding" and kv.get("sel16") == "NarrowFolding" and kv.get("sel8") == "NarrowFolding" and kv.get("narrow16_matches_oracle", "").startswith("true") and kv.get("narrow8_matches_oracle", "").startswith("true") and kv.get("narrow_on_word") == "f12345600"
    if buggy: return base and kv.get("trigger1") == "f123456" and kv.get("standard_direct") == "f123456" and kv.get("widen32_selected") == "f123456"
    return base and kv.get("trigger1") == "f12345600" and kv.get("trigger2") == "1234cdf1f0c1def0" and kv.get("standard_direct") == "f12345600" and kv.get("widen32_selected") == "f12345600"
R["package_hashes"] = {f: hashlib.sha256(open(os.path.join(pkg, f), "rb").read()).hexdigest() for f in ("variant.patch", "test.patch")}; save()
ok = True
mods = reset(); ok = gate("A0", "clean tracked tree before start", ["git checkout -- .", "git status --short"], not mods, "\n".join(mods) or "clean") and ok
rc, o, good = compile_(); ok = gate("A", "baseline checkout compiles", ["defects4j compile"], good, o) and ok
if ok:
    rc, o, n, ft = d4j_test(REL); ok = gate("B1", f"baseline related test passes ({REL.split('::')[1]})", [f"defects4j test -t {REL}"], n == 0, o) and ok
    rc, o, n, fails = full_suite(); R["baseline_full_suite_failures"] = fails; R["baseline_full_suite_n"] = n; ok = gate("B2", "baseline full suite (records pre-existing failures)", ["defects4j test"], n is not None, f"Failing tests: {n}\n" + "\n".join(fails)) and ok
if ok:
    rc, o = sh(["git", "apply", os.path.join(pkg, "test.patch")]); ok = gate("C", "apply test.patch only", ["git apply test.patch"], rc == 0, o or "applied") and ok
if ok:
    rc, o, good = compile_(); ok = gate("C2", "compiles with new test", ["defects4j compile"], good, o) and ok
if ok:
    rc, o, n, ft = d4j_test(TRIG); ok = gate("D", "new trigger passes on the original (correct) implementation", [f"defects4j test -t {TRIG}"], n == 0, o) and ok
if ok:
    rc, o = sh(["git", "apply", os.path.join(pkg, "variant.patch")]); ok = gate("E", "apply variant.patch (bug)", ["git apply variant.patch"], rc == 0, o or "applied") and ok
if ok and arm == "treatment":
    p = os.path.join(work, A["gold_file"]); t = open(p).read(); assert t.count(A["bug_line"]) == 1; open(p, "w").write(t.replace(A["bug_line"], A["orig_line"], 1))
    rc, o, good = compile_(); ok = gate("M", "correct five-hop chain (gold with the original line) compiles", ["<revert buggy line in hop 5 only>", "defects4j compile"], good, o) and ok
    if ok:
        rc, o, n, ft = d4j_test(TRIG); ok = gate("N", "correct-logic trigger passes THROUGH the five-hop chain", [f"defects4j test -t {TRIG}"], n == 0, o) and ok
    if ok:
        rc, o, n, ft = d4j_test(REL); ok = gate("N1", "related sibling test passes through the chain", [f"defects4j test -t {REL}"], n == 0, o) and ok
    if ok:
        rc, o, n, fails = full_suite(); base = set(R.get("baseline_full_suite_failures", [])); new = [f for f in fails if f not in base]; R["correct_chain_full_suite_failures"] = fails
        ok = gate("N2", "FULL suite on the correct five-hop chain equals the baseline failure set (behavioural equivalence of the refactor)", ["defects4j test"], n is not None and not new and set(fails) == base, f"Failing tests: {n}\nnew vs baseline: {new or 'none'}") and ok
    if ok:
        rc, o, kv = probe(); ok = gate("BP1", "two-branch probe on the CORRECT build: forWidth(32)=StandardFolding, forWidth(16|8)=NarrowFolding; narrow branch equals the untouched shortArrayToLong/byteArrayToLong oracles (30 cases); trigger values correct; STANDARD and NARROW both correct on the word case", ["javac/java BranchProbe against target/classes"], rc == 0 and probe_ok(kv, buggy=False), o) and ok
    t = open(p).read(); assert t.count(A["orig_line"]) == 1; open(p, "w").write(t.replace(A["orig_line"], A["bug_line"], 1)); R["gold_bug_restored"] = open(p).read().count(A["bug_line"]) == 1; save()
if ok:
    rc, o, good = compile_(); ok = gate("F", "buggy implementation compiles", ["defects4j compile"], good, o) and ok
if ok:
    sigs = []
    for i in range(3):
        rc, o, n, ft = d4j_test(TRIG); sigs.append({"run": i + 1, "n_fail": n, "signature": "\n".join(ft.splitlines()[:2]), "failing_tests_sha256": hashlib.sha256(ft.encode()).hexdigest()})
    R["trigger_runs"] = sigs; save(); sig = sigs[0]["signature"]
    ok = gate("G", "trigger fails on the buggy implementation", [f"defects4j test -t {TRIG}"], sigs[0]["n_fail"] == 1, sig) and ok
    ok = gate("H", "trigger fails deterministically 3x with identical signature", [f"defects4j test -t {TRIG} (x3)"], all(s["n_fail"] == 1 for s in sigs) and len({s["signature"] for s in sigs}) == 1, json.dumps(sigs, indent=1)) and ok
    clean = ("AssertionFailedError" in sig) and (cfg["expected_signature"] in sig) and not re.search(r"\w+Exception", sig)
    ok = gate("I", "failure is a clean value mismatch with the expected signature, no exception", ["inspect failing_tests"], clean, sig) and ok
if ok and arm == "treatment":
    rc, o, kv = probe(); ok = gate("BP2", "two-branch probe on the BUGGY build: selector unchanged; narrow branch STILL equals the oracles (fault not on that path); trigger and STANDARD/widen(32) give the buggy value f123456; NARROW on the word case stays correct", ["javac/java BranchProbe against target/classes"], rc == 0 and probe_ok(kv, buggy=True), o) and ok
if ok:
    rc, o, n, fails = full_suite(); base = set(R.get("baseline_full_suite_failures", [])); new = [f for f in fails if f != TRIG and f not in base]
    R["buggy_full_suite_failures"] = fails; ok = gate("J", "full-suite collateral with bug + test", ["defects4j test"], n is not None and TRIG in fails, f"Failing tests: {n}\n" + "\n".join(fails)) and ok
    ok = gate("K", "collateral equals baseline + trigger only", ["compare J vs B2"], not new, "new non-baseline failures: " + (", ".join(new) or "none")) and ok
if arm == "treatment" and ok:
    gs = span(A["gold_file"], A["gold_decl"]); bl = lines_with(A["gold_file"], A["bug_line"])
    others = {h["file"]: lines_with(h["file"], A["bug_line"]) + lines_with(h["file"], cfg["control"]["bug_line"]) for h in HOPS[:-1]}; others[cfg["facade_file"]] = lines_with(cfg["facade_file"], A["bug_line"]) + lines_with(cfg["facade_file"], cfg["control"]["bug_line"])
    ok = gate("O", "buggy line is physically inside hop 5 (gold) and nowhere else (facade, hops 1-4)", ["static span check"], bool(gs and bl and all(gs[0] <= b <= gs[1] for b in bl) and not any(others.values())), f"gold span {gs}, buggy line at {bl}, elsewhere {others}") and ok
    wiring = []; good = True
    s0 = span(cfg["facade_file"], cfg["facade_decl"]); c0 = lines_with(cfg["facade_file"], A["facade_call"]); good &= bool(s0 and c0 and s0[0] <= c0[0] <= s0[1]); wiring.append(("facade", s0, c0))
    for h in HOPS:
        sp = span(h["file"], h["decl"]); cl = lines_with(h["file"], h["calls_next"]) if h["calls_next"] else []
        good &= bool(sp) and (not h["calls_next"] or bool(cl and sp[0] <= cl[0] <= sp[1])); wiring.append((f"hop{h['n']}", sp, cl))
    for imp in A["new_imports"]: il = lines_with(imp["file"], imp["line"]); good &= bool(il); wiring.append(("import", imp["line"], il))
    ok = gate("P", "facade -> hop1 -> hop2 -> hop3 -> hop4 -> hop5 wiring, each call inside the caller's span, import present", ["static wiring check"], bool(good), json.dumps(wiring)) and ok
    bodies = {h["method"]: open(os.path.join(work, h["file"])).read().split("\n")[span(h["file"], h["decl"])[0]:span(h["file"], h["decl"])[1] - 1] for h in HOPS}
    thin = {m: len([l for l in b if l.strip() and not l.strip().startswith(("/", "*"))]) for m, b in bodies.items()}
    delegating = {h["method"]: thin[h["method"]] for h in HOPS if h["calls_next"]}; terminal = {h["method"]: thin[h["method"]] for h in HOPS if not h["calls_next"]}
    gold_src = "\n".join(bodies[HOPS[-1]["method"]]); arith = all(t in gold_src for t in ("shift", "<<", "& ~", "|"))
    D = A["dispatch"]; ab, im, al, se = D["abstraction"], D["implementation"], D["alternate"], D["selector"]
    h3 = [h for h in HOPS if h["n"] == 3][0]; s3 = span(h3["file"], h3["decl"]); body3 = "\n".join(open(os.path.join(work, h3["file"])).read().split("\n")[s3[0]:s3[1]]) if s3 else ""
    leak = [t for t in D["caller_must_not_contain"] if t in body3]
    impls = sorted(p.replace(work + "/", "") for p in subprocess.run(["grep", "-rln", "extends Folding", os.path.join(work, "src/main/java")], capture_output=True, text=True).stdout.split())
    binds = [lines_with(ab["file"], b) for b in ab["binding_lines"]]; sel_decl = lines_with(se["file"], se["decl"]); cond = lines_with(se["file"], se["condition_line"]); ab_meth = lines_with(ab["file"], ab["abstract_method"])
    di_ok = not leak and impls == sorted([im["file"], al["file"]]) and all(len(b) == 1 for b in binds) and len(sel_decl) == 1 and len(cond) == 1 and len(ab_meth) == 1
    ok = gate("DI", "dispatch integrity: hop-3 body names neither implementation nor the next stage; exactly two implementations of Folding; selector, its condition and both bindings unique", ["static token/cardinality check"], di_ok, json.dumps({"caller_span": s3, "leaked_tokens_in_caller": leak, "implementations": impls, "bindings_at": binds, "selector_decl_at": sel_decl, "condition_at": cond, "abstract_method_at": ab_meth})) and ok
    sa = span(im["file"], im["override_decl"]); ci = lines_with(im["file"], im["calls_next"]); s_alt = span(al["file"], al["override_decl"]); alt_src = "\n".join(open(os.path.join(work, al["file"])).read().split("\n")[s_alt[0]:s_alt[1]]) if s_alt else ""
    alt_bad = [t for t in al["must_not_contain"] if t in alt_src]; alt_loop = al["own_loop_line"] in alt_src; h3call = lines_with(h3["file"], h3["calls_next"])
    dw_ok = bool(sa and ci and sa[0] <= ci[0] <= sa[1] and s_alt and alt_loop and not alt_bad and h3call and s3 and s3[0] <= h3call[0] <= s3[1])
    ok = gate("DW", "dispatch wiring: hop 3 calls Folding.forWidth(width).fold inside its span; StandardFolding.fold calls ObjectUtils.combine inside its span; NarrowFolding.fold has its own correct loop and no overlay/combine/faulty-form tokens", ["static wiring check"], dw_ok, json.dumps({"hop3_call_at": h3call, "impl_span": sa, "impl_calls_next_at": ci, "alternate_span": s_alt, "alternate_own_loop": alt_loop, "alternate_forbidden_tokens": alt_bad})) and ok
    ok = gate("Q", "no delegating hop is a bare pass-through (hops 1-4 have >= 3 statements incl. real work) and the terminal gold holds the shift/mask/merge arithmetic", ["static body check"], all(v >= 3 for v in delegating.values()) and all(v >= 2 for v in terminal.values()) and arith, json.dumps({"delegating_hops": delegating, "terminal_gold": terminal, "gold_has_shift_mask_merge_arithmetic": arith})) and ok
mods = reset(); gate("L", "source reset cleanliness (git checkout -- .)", ["git checkout -- .", "git status --short"], not mods, "\n".join(mods) or "tracked tree clean")
R["overall"] = "pass" if ok and all(g["status"] == "pass" for g in R["gates"]) else "FAIL"; R["finished_at"] = time.strftime("%Y-%m-%dT%H:%M:%S%z"); save()
print(arm, "overall:", R["overall"], [(g["gate"], g["status"]) for g in R["gates"]])
