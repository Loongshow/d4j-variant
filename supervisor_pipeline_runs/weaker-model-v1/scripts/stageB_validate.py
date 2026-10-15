"""Stage B copy of mechanism-search-v1/scripts/mx_build_validate.py (weaker-model-v1). Changes, all marked SB:
  SB1 trigger.existing=true means the trigger is an EXISTING test method (no test code inserted); test.patch is then empty
  SB2 G7 applies test.patch only when it is non-empty (git apply rejects an empty patch; the harness uses patch, which accepts it)
  SB3 validation record carries the spec sha256 and the Stage B cell label
  SB4 G14 stages with this root's evaluation server (models/w55) via stageB_harness_check.py
  SB6 the build aborts if variant.patch is empty (a fixture without .git makes git diff silent; found in incident W12)
Build and validate one NEW instance (single variant). Usage: stageB_validate.py <spec.json>
Spec: iid, project, group, mechanism, tags, tier, src_root, test_root,
  gold {class, method, file, edits:[{old,new}]}, context_edits [{file, old, new, purpose}] (behaviour-preserving),
  decoys [{class, method, file, decl?}], entry_points [], evidence [Class::method], ownership_reason, ownership_tests [Class::method],
  trigger {test_file, test_class, test_method, code, imports[]}, extra_tests [{test_file, code, imports[]}],
  expected_signature, compensating [{file, old, new, why}].
Builds instances/<iid>/build/{variant.patch,test.patch,correct.patch} from a copy of construction/fresh/<project>, then gates:
  G0 baseline compiles; baseline full-suite failures recorded       G1 CORRECT (context + tests, no fault): trigger and ownership tests
  pass, full suite adds no failure (decoys correct; context edits behaviour-preserving; = gold repair)
  G2 test-method names name no gold/decoy method; no fault vocabulary in added lines
  G3 VARIANT compiles; trigger fails x3 byte-identical; expected signature     G5 full suite: only the trigger newly fails
  G6 gold and every decoy execute under the trigger (markers)     G7 fresh reproduction     G9 no declared decoy edit absorbs the fault
  G10 every gold edit's new text occurs once in the sources      G11 decoy methods identical to pristine unless changed by context edits
  G12 ownership tests pass on the variant     G13 gold and decoys submittable by the harness validator     G14 patches apply in the harness-staged workspace. Writes instances/<iid>/validation.json (READY only if every gate passes)."""
import json, os, re, sys, time, shutil, hashlib, subprocess, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ct_lib as C
L = C.L; MX = C.V3
spec = json.load(open(sys.argv[1])); IID = spec["iid"]; P = spec["project"]
FRESH = f"{MX}/construction/fresh/{P}"; B = f"{MX}/instances/{IID}/build"; os.makedirs(B, exist_ok=True)
OUT = f"{MX}/instances/{IID}/validation.json"; T = spec["trigger"]; TRIG = f"{T['test_class']}::{T['test_method']}"; G = spec["gold"]
R = {"schema_version": "weaker-model-v1/stageB/validation/v1", "iid": IID, "spec_sha256": hashlib.sha256(open(sys.argv[1], "rb").read()).hexdigest(), "stage_b": spec.get("stage_b"), "started_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "gates": []}
FORBID = re.compile(r"\b(bug|bugs|buggy|fault|faulty|wrong|wrongly|incorrect|incorrectly|broken|gold|decoy|cue|fixme|todo|xxx|hack|mistake|erroneous|should be|inverted|reversed)\b", re.I)
ENV = {**os.environ, "PERL5LIB": os.path.expanduser("~/perl5/lib/perl5")}


def save(): json.dump(R, open(OUT, "w"), indent=1)


def gate(gid, name, ok, key):
    R["gates"].append({"gate": gid, "name": name, "status": "pass" if ok else "FAIL", "key_output": str(key)[-1500:]}); save()
    print(f"{gid:4s} {'pass' if ok else 'FAIL'}  {name}", flush=True); return ok


def sh(cmd, cwd, timeout=3600):
    p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout, env=ENV); return p.returncode, p.stdout + p.stderr


def copy_fresh(tag):
    d = tempfile.mkdtemp(prefix="mxb-", dir="/private/tmp"); shutil.copytree(FRESH, f"{d}/w", symlinks=True); return f"{d}/w"


def compile_(w):
    for d in ("target", "build", "build-tests"): shutil.rmtree(os.path.join(w, d), ignore_errors=True)
    rc, o = sh(["defects4j", "compile"], w, 1800); return rc == 0 and "BUILD FAILED" not in o, o


def d4j_test(w, tid=None):
    rc, o = sh(["defects4j", "test"] + (["-t", tid] if tid else []), w, 5400)
    m = re.search(r"Failing tests:\s*(\d+)", o); n = int(m.group(1)) if m else None
    fp = os.path.join(w, "failing_tests"); ft = open(fp, errors="replace").read().strip() if os.path.exists(fp) else ""
    return n, ft, sorted(set(re.findall(r"^\s*-\s+(\S+::\S+)", o, re.M))), o


def sig(ft): return "\n".join(ft.splitlines()[:2])


def add_tests(w):
    for t in ([] if T.get("existing") else [T]) + spec.get("extra_tests", []):  # SB1
        for imp in t.get("imports", []):
            txt, _ = L.read(w, t["test_file"])
            if imp not in txt: L.add_import(w, t["test_file"], imp)
        L.insert_before_class_end(w, t["test_file"], t["code"])


def configure(w, fault=True):
    for e in spec.get("context_edits", []): L.replace_once(w, e["file"], e["old"], e["new"])
    if fault:
        for e in G["edits"]: L.replace_once(w, G["file"], e["old"], e["new"])
    add_tests(w)


def method_src(w, d): return L.method_text(w, d["file"], d["method"], d.get("decl"))


ok = True
prod_files = sorted({G["file"]} | {e["file"] for e in spec.get("context_edits", [])})
test_files = sorted((set() if T.get("existing") else {T["test_file"]}) | {t["test_file"] for t in spec.get("extra_tests", [])})  # SB1
# build patches
w = copy_fresh("build"); configure(w, True); L.diff_to(w, f"{B}/variant.patch", prod_files); (L.diff_to(w, f"{B}/test.patch", test_files) if test_files else open(f"{B}/test.patch", "wb").close())  # SB1
assert os.path.getsize(f"{B}/variant.patch") > 0, "empty variant.patch: git diff produced nothing (fixture without .git?)"   # SB6
w2 = copy_fresh("correct"); configure(w2, False); L.diff_to(w2, f"{B}/correct.patch", prod_files + test_files)
# G2 static
names = [G["method"]] + [d["method"] for d in spec["decoys"]]
tnames = [T["test_method"]] + re.findall(r"public void (\w+)\s*\(", " ".join(t["code"] for t in spec.get("extra_tests", [])))
leak = [(tn, n) for tn in tnames for n in names if n.lower() in tn.lower()]
ok = gate("G2a", "no test-method name contains a gold or decoy method name", not leak, leak or tnames) and ok
hits = [(p, m.group(0), l.strip()[:90]) for p in ("variant.patch", "test.patch") for l in open(f"{B}/{p}", errors="replace").read().splitlines()
        if l.startswith("+") and not l.startswith("+++") for m in FORBID.finditer(l)]
ok = gate("G2b", "no fault vocabulary in added lines", not hits, hits or "clean") and ok
# G0 baseline
w0 = copy_fresh("base"); good, o = compile_(w0)
n0, _, base_fails, _ = d4j_test(w0) if good else (None, "", [], "")
R["baseline_failures"] = base_fails
ok = gate("G0", "baseline compiles; baseline full-suite failures recorded", good, base_fails) and ok
# G1 correct configuration (= gold repair of the variant)
good, o = compile_(w2)
n, ft, _, _ = d4j_test(w2, TRIG) if good else (None, "", [], "")
own_ok = all(d4j_test(w2, t)[0] == 0 for t in spec.get("ownership_tests", [])) if good else False
nS, _, fails_c, _ = d4j_test(w2) if good else (None, "", [], "")
ok = gate("G1", "CORRECT config: trigger + ownership tests pass; full suite adds no failure", good and n == 0 and own_ok and set(fails_c) <= set(base_fails),
          {"trigger_fail": n, "ownership_ok": own_ok, "new_failures": sorted(set(fails_c) - set(base_fails))}) and ok
# G3 variant
good, o = compile_(w); ok = gate("G3a", "variant compiles", good, o[-400:]) and ok
runs = [d4j_test(w, TRIG) for _ in range(3)] if good else []
shas = {hashlib.sha256(r[1].encode()).hexdigest() for r in runs}
ok = gate("G3b", "trigger fails x3, byte-identical", bool(runs) and all(r[0] == 1 for r in runs) and len(shas) == 1, [r[0] for r in runs]) and ok
S0 = sig(runs[0][1]) if runs else ""; R["signature"] = S0
ok = gate("G3c", "expected failure signature", bool(spec["expected_signature"]) and spec["expected_signature"] in (runs[0][1] if runs else ""), S0) and ok
if ok:
    nV, _, fails_v, _ = d4j_test(w); new_v = sorted(set(fails_v) - set(base_fails))
    ok = gate("G5", "full suite: only the trigger newly fails", new_v == [TRIG], new_v) and ok
    own_v = all(d4j_test(w, t)[0] == 0 for t in spec.get("ownership_tests", []))
    ok = gate("G12", "ownership tests pass on the variant", own_v, spec.get("ownership_tests", [])) and ok
    # G6 execution markers
    wm = copy_fresh("mark"); configure(wm, True); mark = tempfile.mkdtemp(prefix="mxm-", dir="/private/tmp")
    for role, mm in [("gold", G)] + [(f"decoy{i}", d) for i, d in enumerate(spec["decoys"])]:
        s, e = L.method_span(wm, mm["file"], mm["method"], mm.get("decl")); t, eol = L.read(wm, mm["file"]); lines = t.split("\n")
        body = "\n".join(lines[s:e]); k = body.index("{", body.index(mm["method"] + "("))
        body = body[:k + 1] + f' new java.io.File("{mark}/{role}").mkdirs();' + body[k + 1:]
        L.write(wm, mm["file"], "\n".join(lines[:s] + body.split("\n") + lines[e:]), eol)
    gm, _ = compile_(wm); d4j_test(wm, TRIG); seen = sorted(os.listdir(mark))
    need = {"gold"} | {f"decoy{i}" for i in range(len(spec["decoys"]))}
    ok = gate("G6", "gold and every decoy execute under the trigger", gm and need <= set(seen), {"seen": seen, "need": sorted(need)}) and ok
    # G9 owner invariance
    res = []
    for ce in spec.get("compensating", []):
        wc = copy_fresh("comp"); configure(wc, True); L.replace_once(wc, ce["file"], ce["old"], ce["new"]); gc, _ = compile_(wc)
        n1, ft1, _, _ = d4j_test(wc, TRIG) if gc else (None, "", [], "")
        n2, _, f2, _ = d4j_test(wc) if (gc and n1 == 0) else (None, "", [], "")
        absorbed = gc and n1 == 0 and set(f2) <= set(base_fails)
        res.append({"why": ce.get("why"), "compiles": gc, "trigger_fail": n1, "absorbed": absorbed}); shutil.rmtree(os.path.dirname(wc), ignore_errors=True)
    ok = gate("G9", "no declared one-line decoy edit absorbs the fault", bool(res) and not any(r["absorbed"] for r in res), res) and ok
    # G10 uniqueness of each gold edit's new text
    cnts = []
    for e in G["edits"]:
        needle = e["new"].strip(); c = 0
        for dpath, _, fs in os.walk(w):
            if any(x in dpath for x in ("/build", "/target", "/.git")): continue
            c += sum(open(os.path.join(dpath, f), errors="replace").read().replace("\r\n", "\n").count(needle) for f in fs if f.endswith(".java"))
        cnts.append(c)
    ok = gate("G10", "each gold edit's new text occurs once in the sources", all(c == 1 for c in cnts), cnts) and ok
    # G11 decoys unchanged unless by context edits (which G1 proved behaviour-preserving)
    # files touched by context edits are skipped first: their methods may not exist in pristine (new helpers), and G1 validated them
    changed = [d["method"] for d in spec["decoys"] if not any(ce["file"] == d["file"] for ce in spec.get("context_edits", [])) and method_src(w, d) != method_src(w0, d)]
    ok = gate("G11", "decoy methods identical to pristine unless changed by validated context edits", not changed, changed or "unchanged") and ok
    # G13 harness submittability: the submission validator rejects any method whose class ends with Test/Tests, whose package
    # contains .junit./.test., or whose name starts with "test" (agents/mini_swe_fault_localization.py::_looks_like_test_method);
    # a gold or decoy matching it can never be ranked (found after NEW-R4-M4, MannWhitneyUTest).
    def _unsub(c, m): return c.endswith("Test") or c.endswith("Tests") or ".junit." in c or ".test." in c or m.startswith("test")
    blocked = [f"{x['class']}::{x['method']}" for x in [G] + spec["decoys"] if _unsub(x["class"], x["method"])]
    ok = gate("G13", "gold and decoys are submittable (not rejected as test methods by the harness validator)", not blocked, blocked or "submittable") and ok
    # G14 harness compatibility (AMENDMENTS X10): the server stages the agent workspace with its own filtered copy (drops *.bak,
    # *.orig, *.rej, *.patch, private metadata, VCS/IDE/build dirs) and applies the patches with `patch -p1 --forward --batch`.
    hc = subprocess.run([sys.executable, os.path.join(os.path.dirname(os.path.abspath(__file__)), "stageB_harness_check.py"), P,
                         f"{B}/variant.patch", f"{B}/test.patch"], capture_output=True, text=True, timeout=1800)
    ok = gate("G14", "patches apply in the harness-staged workspace (server copy filter + patch -p1 --forward --batch)",
              hc.returncode == 0, hc.stdout[-1200:]) and ok
    # G7 fresh reproduction
    wf = copy_fresh("fresh")
    a1 = sh(["git", "apply", f"{B}/variant.patch"], wf)[0] == 0 and (os.path.getsize(f"{B}/test.patch") == 0 or sh(["git", "apply", f"{B}/test.patch"], wf)[0] == 0)  # SB2
    gf, _ = compile_(wf)
    nf, ftf, _, _ = d4j_test(wf, TRIG) if gf else (None, "", [], "")
    ok = gate("G7", "fresh reproduction: apply, compile, same failure", a1 and gf and nf == 1 and sig(ftf) == S0, sig(ftf)) and ok
    for x in (wm, wf): shutil.rmtree(os.path.dirname(x), ignore_errors=True)
    shutil.rmtree(mark, ignore_errors=True)   # this build's own marker dir (agents can list /private/tmp)
for x in (w, w2, w0): shutil.rmtree(os.path.dirname(x), ignore_errors=True)
R["overall"] = "READY" if ok and all(g["status"] == "pass" for g in R["gates"]) else "FAIL"
R["finished_at"] = time.strftime("%Y-%m-%dT%H:%M:%S%z"); save()
print(IID, "overall:", R["overall"])
