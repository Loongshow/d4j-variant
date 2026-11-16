"""OCFLB pair validator. Usage: ocflb_validate.py <pair.json> <work-checkout> <fresh-checkout> [--focused]
Runs V1..V14 (+ matched-arms) for both arms and writes <pair_dir>/validation/validation.json plus per-arm validation.json."""
import json, os, re, subprocess, sys, time, hashlib, shutil, difflib
spec = json.load(open(sys.argv[1])); work, fresh = sys.argv[2], sys.argv[3]; FOCUSED = "--focused" in sys.argv
env = dict(os.environ, PERL5LIB=os.path.expanduser("~/perl5/lib/perl5"))
PD = spec["pair_dir"]; VD = f"{PD}/validation"; os.makedirs(VD, exist_ok=True); OUT = f"{VD}/validation.json"
TRIG, PIN = spec["trigger"], spec["pin_test"]; CH = spec["chain"]; ARMS = spec["arms"]
R = {"schema_version": "ocflb-v1/validation/v1", "pair_id": spec["pair_id"], "project": spec["project"], "started_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "gates": [], "arms": {a: {} for a in ARMS}}
def save(): json.dump(R, open(OUT, "w"), indent=1)
def sh(cmd, cwd=None, timeout=1800):
    p = subprocess.run(cmd, cwd=cwd or work, capture_output=True, text=True, env=env, timeout=timeout); return p.returncode, p.stdout + p.stderr
def gate(gid, name, ok, key, arm=None):
    R["gates"].append({"gate": gid, "arm": arm, "name": name, "status": "pass" if ok else "FAIL", "key_output": str(key)[-1500:]}); save(); print(gid, arm or "", "pass" if ok else "FAIL", flush=True); return ok
def d4j_test(tid, cwd=None):
    rc, o = sh(["defects4j", "test", "-t", tid], cwd, 900); m = re.search(r"Failing tests:\s*(\d+)", o); n = int(m.group(1)) if m else None
    fp = os.path.join(cwd or work, "failing_tests"); ft = open(fp).read() if os.path.exists(fp) else ""; return n, ft.strip(), o
def suite(cwd=None):
    if FOCUSED: return None, None, "focused mode: full suite skipped"
    rc, o = sh(["defects4j", "test"], cwd, 3600); m = re.search(r"Failing tests:\s*(\d+)", o); n = int(m.group(1)) if m else None
    return n, sorted(set(re.findall(r"^\s*-\s+(\S+::\S+)", o, re.M))), o
def compile_(cwd=None):
    c = cwd or work
    for d in ("target", "build", "build-tests"): shutil.rmtree(os.path.join(c, d), ignore_errors=True)
    rc, o = sh(["defects4j", "compile"], c, 1200); return (rc == 0 and "BUILD FAILED" not in o), o
def reset(cwd=None):
    c = cwd or work; sh(["git", "reset", "-q", "--", "."], c); sh(["git", "checkout", "--", "."], c); sh(["git", "clean", "-fdq", "--", "src", "tests", "source"], c)
    rc, o = sh(["git", "status", "--short"], c); return [l for l in o.splitlines() if not l.startswith("??")]
def text(rel, cwd=None): return open(os.path.join(cwd or work, rel), "rb").read().decode("utf-8").replace("\r\n", "\n")
def swap(rel, old, new, cwd=None):
    c = cwd or work; raw = open(os.path.join(c, rel), "rb").read().decode("utf-8"); eol = "\r\n" if "\r\n" in raw else "\n"; t = raw.replace("\r\n", "\n")
    assert t.count(old) == 1, (rel, old[:60], t.count(old)); open(os.path.join(c, rel), "wb").write(t.replace(old, new, 1).replace("\n", eol).encode("utf-8"))
def apply_arm(arm, cwd=None):
    d = ARMS[arm]["package_dir"]; rc1, o1 = sh(["git", "apply", f"{d}/test.patch"], cwd); rc2, o2 = sh(["git", "apply", f"{d}/variant.patch"], cwd); return rc1 == 0 and rc2 == 0, o1 + o2
def sig_of(ft): return "\n".join(ft.splitlines()[:2])
FORBID = re.compile(r"\b(bug|bugs|buggy|fault|faulty|wrong|wrongly|incorrect|incorrectly|broken|definer|adapter|gold|ocflb|fixme|todo|xxx|hack|mistake|erroneous|misappl\w*|should be|inverted|reversed)\b", re.I)
ROLES = ["H1", "H2", "H3", "H4", "H5"]
def body_of(rel, method, decl=None, cwd=None):
    """Return the method body text (between the first '{' after the declaration and the matching '}')."""
    t = text(rel, cwd); pat = re.compile(r"^[ \t]*(public|protected|private|static|final|\s)*[\w<>\[\], ]+\s+" + re.escape(method) + r"\s*\(", re.M)
    cands = [m for m in pat.finditer(t) if (decl is None or decl in t[m.start(): t.find("\n", m.start())])]
    assert cands, (rel, method, decl); m = cands[0]; i = t.index("{", m.end()); depth = 0
    for j in range(i, len(t)):
        if t[j] == "{": depth += 1
        elif t[j] == "}":
            depth -= 1
            if depth == 0: return t[i + 1:j]
    raise AssertionError("unbalanced")
ok = True
mods = reset(); ok = gate("V14a", "work checkout clean before start", not mods, mods or "clean") and ok
good, o = compile_(); ok = gate("V1a", "baseline compiles", good, o) and ok
if ok and not FOCUSED:
    n, fails, o = suite(); R["baseline_suite_failures"] = fails; ok = gate("V5a", "baseline suite recorded", n is not None, f"{n} failing: {fails}") and ok
if ok:
    rc, o = sh(["git", "apply", f"{ARMS['ADAPTER_FAULT']['package_dir']}/test.patch"]); ok = gate("V2a", "shared test.patch applies", rc == 0, o or "applied") and ok
    rc, o = sh(["git", "apply", f"{spec['correct_dir']}/variant.patch"]); ok = gate("V2a2", "CORRECT chain (H2 and H3 both right) applies", rc == 0, o or "applied") and ok
    good, o = compile_(); ok = gate("V1b", "CORRECT chain + tests compiles", good, o) and ok
    n, ft, o = d4j_test(TRIG); ok = gate("V2b", "trigger passes on the CORRECT chain", n == 0, o) and ok
    n, ft, o = d4j_test(PIN); ok = gate("V2c", "pin test passes on the CORRECT chain", n == 0, o) and ok
    reset()
# lexgate on the shared test patch (trigger + pin) and both variant patches
def lexgate(patch):
    hits = []
    for l in open(patch, errors="replace").read().splitlines():
        if l.startswith("+") and not l.startswith("+++"):
            for m in FORBID.finditer(l): hits.append((m.group(0), l.strip()[:120]))
    return hits
trig_name = TRIG.split("::")[1].lower(); hop_names = [CH[r]["method"].lower() for r in ROLES]
leak = [h for h in hop_names if h in trig_name]
ok = gate("V9a", "trigger name is neutral (no hop method name inside it)", not leak, leak or trig_name) and ok
hits = lexgate(f"{ARMS['ADAPTER_FAULT']['package_dir']}/test.patch"); ok = gate("V9b", "lexgate on test.patch (no fault-identifying vocabulary)", not hits, hits or "clean") and ok
sigs = {}
for arm in ("DEFINER_FAULT", "ADAPTER_FAULT"):
    if not ok: break
    A = ARMS[arm]; G = A["gold"]; AR = R["arms"][arm]; AR["variant_id"] = A["variant_id"]
    reset(); good, o = apply_arm(arm); ok = gate("V8", "packaged patches apply cleanly", good, o or "applied", arm) and ok
    hits = lexgate(f"{A['package_dir']}/variant.patch"); ok = gate("V9c", "lexgate on variant.patch", not hits, hits or "clean", arm) and ok
    good, o = compile_(); ok = gate("V1c", "arm compiles", good, o, arm) and ok
    if not ok: break
    runs = []
    for i in range(3):
        n, ft, o = d4j_test(TRIG); runs.append({"n_fail": n, "signature": sig_of(ft), "sha": hashlib.sha256(ft.encode()).hexdigest()})
    AR["trigger_runs"] = runs; sig = runs[0]["signature"]; sigs[arm] = sig
    ok = gate("V3a", "trigger fails on the arm", runs[0]["n_fail"] == 1, sig, arm) and ok
    ok = gate("V3b", "deterministic x3 with one signature", all(r["n_fail"] == 1 for r in runs) and len({r["sha"] for r in runs}) == 1, json.dumps(runs), arm) and ok
    ok = gate("V3c", "signature matches the pre-registered expectation", bool(re.search(spec["assertion_class_regex"], sig)) and spec["expected_signature"] in sig, sig, arm) and ok
    n, ft, o = d4j_test(PIN); AR["pin_on_buggy"] = {"n_fail": n, "signature": sig_of(ft)}
    if arm == "ADAPTER_FAULT": ok = gate("V12", "pin test passes on the ADAPTER arm (H2 independently correct)", n == 0, o, arm) and ok
    else: ok = gate("V12", "pin test exposes H2 on the DEFINER arm (declared collateral)", n == 1, sig_of(ft), arm) and ok
    # V10 logic chain (static): call edges and real work
    edges = [("facade", "H1"), ("H1", "H2"), ("H1", "H3"), ("H3", "H4"), ("H4", "H5")]; missing = []; thin = []
    for a, b in edges:
        ba = body_of(CH[a]["file"], CH[a]["method"], CH[a].get("decl"))
        if not re.search(r"\b" + re.escape(CH[b]["method"]) + r"\s*\(", ba): missing.append(f"{a}->{b}")
    for r in ROLES:
        b = body_of(CH[r]["file"], CH[r]["method"], CH[r].get("decl"))
        if b.count(";") < 2: thin.append(r)
    ok = gate("V10", "logic chain: facade->H1, H1->H2, H1->H3, H3->H4, H4->H5 present and every hop has >= 2 statements", not missing and not thin, {"missing": missing, "thin": thin}, arm) and ok
    # V6 dynamic participation: instrumented copy of the hops
    mark = f"/tmp/ocflb-mark-{spec['pair_id']}-{arm}"; shutil.rmtree(mark, ignore_errors=True); os.makedirs(mark)
    for r in ["facade"] + ROLES:
        rel, meth, decl = CH[r]["file"], CH[r]["method"], CH[r].get("decl"); t = text(rel)
        pat = re.compile(r"^[ \t]*(public|protected|private|static|final|\s)*[\w<>\[\], ]+\s+" + re.escape(meth) + r"\s*\(", re.M)
        cands = [m for m in pat.finditer(t) if (decl is None or decl in t[m.start(): t.find("\n", m.start())])]; m = cands[0]; i = t.index("{", m.end())
        t2 = t[:i + 1] + f' new java.io.File("{mark}/{r}").mkdirs();' + t[i + 1:]
        raw = open(os.path.join(work, rel), "rb").read().decode("utf-8"); eol = "\r\n" if "\r\n" in raw else "\n"; open(os.path.join(work, rel), "wb").write(t2.replace("\n", eol).encode("utf-8"))
    good, o = compile_(); n, ft, o2 = d4j_test(TRIG); seen = sorted(os.listdir(mark)) if os.path.isdir(mark) else []
    ok = gate("V6", "H1-H5 (and facade) all execute dynamically under the trigger", good and set(["facade"] + ROLES) <= set(seen) and n == 1, {"compiled": good, "seen": seen, "trigger_fail": n}, arm) and ok
    shutil.rmtree(mark, ignore_errors=True); reset(); apply_arm(arm); compile_()
    # V5/V13 collateral
    if not FOCUSED:
        n, fails, o = suite(); base = set(R.get("baseline_suite_failures") or []); new = sorted(f for f in fails if f != TRIG and f not in base); AR["suite_failures"] = fails
        declared = set(A.get("declared_collateral") or []); ok = gate("V5", "suite: trigger fails and every other new failure is declared", TRIG in fails and set(new) <= declared, {"new": new, "declared": sorted(declared)}, arm) and ok
        ok = gate("V13", "no undeclared second bug", set(new) <= declared, new, arm) and ok
    # V11 ownership proof
    swap(G["file"], G["bug_line"], G["orig_line"]); good, o = compile_(); nt, ftt, _ = d4j_test(TRIG); npn, ftp, _ = d4j_test(PIN)
    AR["gold_repair"] = {"compiles": good, "trigger_fail": nt, "pin_fail": npn}
    ok = gate("V11a", "repairing the declared gold fixes the trigger and leaves the pin passing", good and nt == 0 and npn == 0, AR["gold_repair"], arm) and ok
    swap(G["file"], G["orig_line"], G["bug_line"]); C = A["compensating"]
    swap(C["file"], C["old"], C["new"]); good, o = compile_(); nt2, ftt2, _ = d4j_test(TRIG); npn2, ftp2, _ = d4j_test(PIN)
    AR["compensating_repair"] = {"target_role": C["role"], "compiles": good, "trigger_fail": nt2, "pin_fail": npn2, "pin_signature": sig_of(ftp2)}
    swap(C["file"], C["new"], C["old"])
    cls = "PINNED_UNIQUE" if (good and nt2 == 0 and npn2 == 1) else ("MOSTLY_UNIQUE" if (not good or nt2 != 0) else "AMBIGUOUS")
    AR["ownership"] = cls
    ok = gate("V11b", "compensating repair at the other hop passes the trigger but breaks the pin (ownership PINNED_UNIQUE)", cls == "PINNED_UNIQUE", AR["compensating_repair"], arm) and ok
    gs = text(G["file"]); ok = gate("V11c", "declared buggy line present exactly once in the gold file", gs.count(G["bug_line"]) == 1, gs.count(G["bug_line"]), arm) and ok
    # V7 fresh reproduction on the pristine second checkout
    mods = reset(fresh); good, o = apply_arm(arm, fresh); goodc, oc = compile_(fresh); n, ft, o2 = d4j_test(TRIG, fresh); reset(fresh)
    ok = gate("V7", "fresh reproduction on a pristine checkout: patches apply, compile, trigger fails with the same signature", not mods and good and goodc and n == 1 and sig_of(ft) == sig, {"fresh_sig": sig_of(ft)}, arm) and ok
    reset()
if ok and len(sigs) == 2:
    ok = gate("V3d", "same observed failure in both arms (identical signature)", sigs["DEFINER_FAULT"] == sigs["ADAPTER_FAULT"], sigs) and ok
    # matched arms: only the declared lines differ
    snaps = {}
    for arm in ("DEFINER_FAULT", "ADAPTER_FAULT"):
        reset(); apply_arm(arm); snaps[arm] = {f: text(f) for f in spec["prod_files"]}
    reset(); diffl = []
    for f in spec["prod_files"]:
        for l in difflib.unified_diff(snaps["DEFINER_FAULT"][f].splitlines(), snaps["ADAPTER_FAULT"][f].splitlines(), lineterm="", n=0):
            if l.startswith(("+", "-")) and not l.startswith(("+++", "---")): diffl.append(l[1:].strip())
    allowed = set()
    for arm in ARMS:
        for k in ("bug_line", "orig_line"): allowed |= {x.strip() for x in ARMS[arm]["gold"][k].split("\n")}
    stray = [l for l in diffl if l and l not in allowed]
    ok = gate("V10b", "matched arms: the two variant patches differ only in the declared H2/H3 lines", not stray and diffl, {"diff_lines": len(diffl), "stray": stray}) and ok
mods = reset(); gate("V14", "work checkout clean after validation", not mods, mods or "clean")
R["overall"] = "READY" if ok and all(g["status"] == "pass" for g in R["gates"]) else "FAIL"; R["finished_at"] = time.strftime("%Y-%m-%dT%H:%M:%S%z"); save()
for arm in ARMS:
    json.dump({"schema_version": "d4j-validation/v1", "variant_id": ARMS[arm]["variant_id"], "pair_id": spec["pair_id"], "arm": arm, "status": "accepted" if R["overall"] == "READY" else "rejected", "accepted": R["overall"] == "READY",
               "non_canonical": True, "validator_version": "ocflb-v1/ocflb_validate.py", "validated_at": R["finished_at"], "gate": {(g["gate"] + ("" if not g["arm"] else "")): {"status": g["status"], "name": g["name"]} for g in R["gates"] if g["arm"] in (None, arm)},
               "trigger_runs": R["arms"][arm].get("trigger_runs"), "ownership": R["arms"][arm].get("ownership")}, open(f"{ARMS[arm]['package_dir']}/validation.json", "w"), indent=1)
print(spec["pair_id"], "overall:", R["overall"], [(g["gate"], g["arm"] or "", g["status"]) for g in R["gates"] if g["status"] != "pass"] or "all gates pass")
