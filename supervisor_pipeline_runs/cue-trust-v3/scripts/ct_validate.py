"""cue-trust-v3 instance validator. Usage: ct_validate.py <spec.json>
Gates (all must pass for READY):
  G0   work checkout clean; baseline compiles
  G1   CORRECT configuration (cue C0, no fault): compiles, trigger passes
  G2   trigger-blind: the test names no gold/decoy method; added lines carry no fault vocabulary
  per cue level L in C0, CG1, CG2, CD1, CD2:
  G3   patches apply; compiles; trigger fails x3 with one byte-identical failure output; expected signature present
  G4   bytecode equivalence with C0 (javap -c -p of every class compiled from a changed file; constant-pool indices
       stripped; declared field renames undone): code behaviour identical across cue levels
  G7   fresh reproduction on a pristine checkout (apply, compile, same failure)
  on C0 only (behaviour is shared by G4):
  G5   full suite: the trigger is the only failing test
  G6   gold and decoy both execute under the trigger (instrumented markers)
  G8   gold repair: restoring the original line fixes the trigger and leaves the full suite at 0 failures
  G9   owner invariance: every declared one-line decoy edit leaves the trigger failing or breaks the suite (no absorb)
  G10  the faulty line occurs exactly once across production and test sources
  X    identical failure signature across all cue levels (payload identity)"""
import json, os, re, sys, time, shutil, hashlib, subprocess, difflib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ct_lib as C
L = C.L
spec = json.load(open(sys.argv[1])); IID = spec["instance_id"]; work, fresh = spec["work"], spec["fresh"]
B = f"{C.V3}/instances/{IID}/build"; OUT = f"{C.V3}/instances/{IID}/validation.json"
T = spec["trigger"]; TRIG = f"{T['test_class']}::{T['test_method']}"
R = {"schema_version": "cue-trust-v3/validation/v1", "instance_id": IID, "started_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "gates": [], "levels": {}}
FORBID = re.compile(r"\b(bug|bugs|buggy|fault|faulty|wrong|wrongly|incorrect|incorrectly|broken|gold|decoy|cue|fixme|todo|xxx|hack|mistake|erroneous|should be|inverted|reversed)\b", re.I)

def save(): json.dump(R, open(OUT, "w"), indent=1)
def gate(gid, name, ok, key, level=None):
    R["gates"].append({"gate": gid, "level": level, "name": name, "status": "pass" if ok else "FAIL", "key_output": str(key)[-1500:]}); save()
    print(f"{gid:4s} {level or '':8s} {'pass' if ok else 'FAIL'}  {name}", flush=True); return ok
def sh(cmd, cwd=None, timeout=1800): return C.sh(cmd, cwd or work, timeout)
def reset(cwd=None):
    c = cwd or work; sh(["git", "reset", "-q", "--", "."], c); sh(["git", "checkout", "--", "."], c); sh(["git", "clean", "-fdq", "--", "src", "tests", "source"], c)
    return [l for l in sh(["git", "status", "--short"], c)[1].splitlines() if not l.startswith("??")]
def compile_(cwd=None):
    c = cwd or work
    for d in ("target", "build", "build-tests"): shutil.rmtree(os.path.join(c, d), ignore_errors=True)
    rc, o = sh(["defects4j", "compile"], c, 1200); return rc == 0 and "BUILD FAILED" not in o, o
def d4j_test(tid=None, cwd=None):
    c = cwd or work; rc, o = sh(["defects4j", "test"] + (["-t", tid] if tid else []), c, 3600)
    m = re.search(r"Failing tests:\s*(\d+)", o); n = int(m.group(1)) if m else None
    fp = os.path.join(c, "failing_tests"); ft = open(fp).read().strip() if os.path.exists(fp) else ""
    return n, ft, sorted(set(re.findall(r"^\s*-\s+(\S+::\S+)", o, re.M))), o
def sig(ft): return "\n".join(ft.splitlines()[:2])
def apply(level, cwd=None):
    d = f"{B}/{level}"; r1 = sh(["git", "apply", f"{d}/test.patch"], cwd); r2 = sh(["git", "apply", f"{d}/variant.patch"], cwd)
    return r1[0] == 0 and r2[0] == 0, r1[1] + r2[1]

def class_files(cwd):
    root = os.path.join(cwd, spec["classes_dir"]); out = []
    for rel in spec["prod_files"]:
        internal = os.path.relpath(rel, spec["src_root"])[:-5]; d = os.path.join(root, os.path.dirname(internal)); base = os.path.basename(internal)
        out += sorted(os.path.join(d, f) for f in os.listdir(d) if f == base + ".class" or (f.startswith(base + "$") and f.endswith(".class")))
    return out
def javap_text(cwd, level):
    lv = spec["levels"][level]; inv = {}
    for r in lv.get("renames", []):
        if r["scope"] == "fields": inv[r["class"]] = {v: k for k, v in r["map"].items()}
    texts = {}
    for cf in class_files(cwd):
        rc, o = sh(["javap", "-c", "-p", cf], cwd); o = re.sub(r"#\d+", "#", o)
        o = "\n".join(l for l in o.splitlines() if not l.startswith("Compiled from"))
        internal = os.path.relpath(cf, os.path.join(cwd, spec["classes_dir"]))[:-6]
        if internal in inv:
            m = inv[internal]; names = "|".join(re.escape(k) for k in m)
            o = re.sub(r"(// Field )(%s)(:)" % names, lambda x: x.group(1) + m[x.group(2)] + x.group(3), o)
            o = re.sub(r"^(\s*(?:private|protected|public)?\s*(?:static\s+)?(?:transient\s+)?(?:final\s+)?[\w.$\[\]<>]+\s+)(%s)(;)$" % names,
                       lambda x: x.group(1) + m[x.group(2)] + x.group(3), o, flags=re.M)
        texts[internal] = o
    return texts

ok = True
ok = gate("G0a", "work checkout clean before start", not reset(), "clean") and ok
good, o = compile_(); ok = gate("G0b", "baseline compiles", good, o[-400:]) and ok
# G2 static checks
names = [spec["gold"]["method"]] + [d["method"] for d in spec["decoys"]]
leak = [n for n in names if re.search(r"\b%s\b" % re.escape(n), T["code"])]
ok = gate("G2a", "trigger-blind: test code names no gold or decoy method", not leak, leak or "clean") and ok
hits = []
for level in C.LEVELS + ["CORRECT"]:
    for p in ("variant.patch", "test.patch"):
        for l in open(f"{B}/{level}/{p}", errors="replace").read().splitlines():
            if l.startswith("+") and not l.startswith("+++"):
                hits += [(level, p, m.group(0), l.strip()[:100]) for m in FORBID.finditer(l)]
ok = gate("G2b", "no fault-identifying vocabulary in any added line", not hits, hits or "clean") and ok
# G1 correct configuration
if ok:
    reset(); good, o = apply("CORRECT"); good2, o2 = compile_(); n, ft, _, o3 = d4j_test(TRIG)
    ok = gate("G1", "CORRECT configuration compiles and the trigger passes", good and good2 and n == 0, o3[-500:]) and ok
sigs, javs = {}, {}
for level in C.LEVELS:
    if not ok: break
    LV = R["levels"].setdefault(level, {}); reset()
    good, o = apply(level); good2, o2 = compile_()
    ok = gate("G3a", "patches apply and compile", good and good2, (o + o2)[-500:], level) and ok
    if not ok: break
    runs = []
    for i in range(3):
        n, ft, _, _ = d4j_test(TRIG); runs.append({"n_fail": n, "signature": sig(ft), "sha": hashlib.sha256(ft.encode()).hexdigest()})
    LV["trigger_runs"] = runs; sigs[level] = runs[0]["signature"]
    ok = gate("G3b", "trigger fails x3 with one byte-identical failure output", all(r["n_fail"] == 1 for r in runs) and len({r["sha"] for r in runs}) == 1, json.dumps(runs), level) and ok
    ok = gate("G3c", "expected failure signature", bool(re.search(spec["assertion_class_regex"], sigs[level])) and spec["expected_signature"] in sigs[level], sigs[level], level) and ok
    javs[level] = javap_text(work, level)
    if level != "C0":
        diffs = {k: [l for l in difflib.unified_diff(javs["C0"].get(k, "").splitlines(), v.splitlines(), lineterm="", n=0) if l[:1] in "+-" and l[:3] not in ("+++", "---")][:6]
                 for k, v in javs[level].items()}
        diffs = {k: v for k, v in diffs.items() if v}; same_set = set(javs["C0"]) == set(javs[level])
        ok = gate("G4", "bytecode identical to C0 after undoing declared renames", same_set and not diffs, diffs or f"{len(javs[level])} classes identical", level) and ok
    if level == "C0" and ok:
        n, ft, fails, o = d4j_test(); LV["suite_failures"] = fails
        ok = gate("G5", "full suite: the trigger is the only failing test", fails == [TRIG], fails, level) and ok
        # G6 markers
        mark = f"/tmp/ct-mark-{IID}"; shutil.rmtree(mark, ignore_errors=True); os.makedirs(mark)
        for mm in spec["marker_methods"]:
            s, e = L.method_span(work, mm["file"], mm["method"], mm.get("decl")); t, eol = L.read(work, mm["file"]); lines = t.split("\n")
            body = "\n".join(lines[s:e]); k = body.index("{", body.index(mm["method"] + "("))
            body = body[:k + 1] + f' new java.io.File("{mark}/{mm["role"]}").mkdirs();' + body[k + 1:]
            L.write(work, mm["file"], "\n".join(lines[:s] + body.split("\n") + lines[e:]), eol)
        good, o = compile_(); n, ft, _, _ = d4j_test(TRIG); seen = sorted(os.listdir(mark))
        ok = gate("G6", "gold and decoy both execute under the trigger", good and {"gold", "decoy"} <= set(seen) and n == 1, {"seen": seen, "trigger_fail": n}, level) and ok
        shutil.rmtree(mark, ignore_errors=True); reset(); apply(level)
        # G8 gold repair
        G = spec["gold"]; L.replace_once(work, G["file"], G["bug_line"], G["orig_line"]); good, o = compile_(); n1, _, _, _ = d4j_test(TRIG); n2, _, fails2, _ = d4j_test()
        LV["gold_repair"] = {"compiles": good, "trigger_fail": n1, "suite_fail": n2, "suite_failures": fails2}
        ok = gate("G8", "gold repair fixes the trigger and leaves the full suite at 0 failures", good and n1 == 0 and n2 == 0, LV["gold_repair"], level) and ok
        # G9 owner invariance
        res = []
        for ce in spec["compensating"]:
            reset(); apply(level); L.replace_once(work, ce["file"], ce["old"], ce["new"]); good, o = compile_(); n1, ft1, _, _ = d4j_test(TRIG)
            n2, _, fails2, _ = d4j_test() if (good and n1 == 0) else (None, None, [], None)
            absorbed = good and n1 == 0 and n2 == 0
            res.append({"edit": ce["why"], "compiles": good, "trigger_fail": n1, "trigger_sig": sig(ft1), "suite_fail": n2, "absorbed": absorbed})
        LV["compensating"] = res
        ok = gate("G9", "owner invariance: no one-line decoy edit absorbs the fault", res and not any(r["absorbed"] for r in res), res, level) and ok
        reset(); apply(level)
        cnt = 0
        for d, _, fs in os.walk(work):
            if "/build" in d or "/target" in d or "/.git" in d: continue
            for f in fs:
                if f.endswith(".java"): cnt += open(os.path.join(d, f), errors="replace").read().replace("\r\n", "\n").count(G["bug_line"])
        ok = gate("G10", "faulty line occurs exactly once across sources", cnt == 1, cnt, level) and ok
    # G7 fresh reproduction
    mods = reset(fresh); good, o = apply(level, fresh); goodc, oc = compile_(fresh); n, ft, _, _ = d4j_test(TRIG, fresh); reset(fresh)
    ok = gate("G7", "fresh reproduction: apply, compile, same failure", not mods and good and goodc and n == 1 and sig(ft) == sigs[level], sig(ft), level) and ok
if ok:
    ok = gate("X", "identical failure signature across all cue levels", len(set(sigs.values())) == 1, sigs) and ok
gate("G0c", "work checkout clean after validation", not reset(), "clean")
R["overall"] = "READY" if ok and all(g["status"] == "pass" for g in R["gates"]) else "FAIL"; R["finished_at"] = time.strftime("%Y-%m-%dT%H:%M:%S%z"); save()
print(IID, "overall:", R["overall"])
