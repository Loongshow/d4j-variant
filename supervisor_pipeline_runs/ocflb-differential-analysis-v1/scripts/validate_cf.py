"""Compact validator for one counterfactual variant. Usage: validate_cf.py <cf.json> <work> -> <package_dir>/validation.json
Gates: A0 clean; A compile with patches; G/H trigger fails x3 with the expected signature; P pin + extra tests pass on the buggy variant;
S restoring the declared gold lines makes trigger and pin pass; X lexgate; L reset."""
import json, os, re, subprocess, sys, hashlib, shutil, time
cf, work = json.load(open(sys.argv[1])), sys.argv[2]; env = dict(os.environ, PERL5LIB=os.path.expanduser("~/perl5/lib/perl5")); pkg = cf["package_dir"]
R = {"variant_id": cf["variant_id"], "gates": [], "started": time.strftime("%FT%T")}
def sh(c, t=1800): p = subprocess.run(c, cwd=work, capture_output=True, text=True, env=env, timeout=t); return p.returncode, p.stdout + p.stderr
def gate(g, name, ok, key): R["gates"].append({"gate": g, "name": name, "status": "pass" if ok else "FAIL", "key": str(key)[-800:]}); print(g, "pass" if ok else "FAIL", flush=True); return ok
def test(tid): rc, o = sh(["defects4j", "test", "-t", tid], 900); m = re.search(r"Failing tests:\s*(\d+)", o); ft = open(f"{work}/failing_tests").read() if os.path.exists(f"{work}/failing_tests") else ""; return (int(m.group(1)) if m else None), ft.strip()
def compile_():
    for d in ("build", "build-tests"): shutil.rmtree(f"{work}/{d}", ignore_errors=True)
    rc, o = sh(["defects4j", "compile"], 1200); return rc == 0 and "BUILD FAILED" not in o, o
def reset(): sh(["git", "reset", "-q", "--", "."]); sh(["git", "checkout", "--", "."]); sh(["git", "clean", "-fdq", "--", "source", "tests"]); rc, o = sh(["git", "status", "--short"]); return [l for l in o.splitlines() if not l.startswith("??")]
def swap(rel, a, b): p = f"{work}/{rel}"; t = open(p).read(); assert t.count(a) == 1, (rel, t.count(a)); open(p, "w").write(t.replace(a, b, 1))
FORBID = re.compile(r"\b(bug|buggy|fault|faulty|wrong|incorrect|broken|definer|adapter|gold|ocflb|fixme|todo|hack|mistake|erroneous|inverted|reversed)\b", re.I)
ok = gate("A0", "clean", not reset(), "clean")
rc, o = sh(["git", "apply", f"{pkg}/test.patch"]); rc2, o2 = sh(["git", "apply", f"{pkg}/variant.patch"]); ok = gate("E", "patches apply", rc == 0 and rc2 == 0, o + o2) and ok
good, o = compile_(); ok = gate("A", "compiles", good, o) and ok
sigs = []
for i in range(3): n, ft = test(cf["trigger"]); sigs.append((n, "\n".join(ft.splitlines()[:2])))
ok = gate("G", "trigger fails x3 with expected signature", all(n == 1 for n, _ in sigs) and len({s for _, s in sigs}) == 1 and cf["expected_signature"] in sigs[0][1], sigs) and ok
for t in [cf["pin_test"]] + cf.get("extra_passing_tests", []): n, ft = test(t); ok = gate("P", f"passes on the buggy variant: {t.split('::')[1]}", n == 0, ft) and ok
G = cf["gold"]; swap(G["file"], G["bug_line"], G["orig_line"]); good, o = compile_(); n1, _ = test(cf["trigger"]); n2, _ = test(cf["pin_test"]); swap(G["file"], G["orig_line"], G["bug_line"])
ok = gate("S", "restoring the declared gold lines makes trigger and pin pass", good and n1 == 0 and n2 == 0, (n1, n2)) and ok
hits = [(m.group(0), l[:100]) for f in ("variant.patch", "test.patch") for l in open(f"{pkg}/{f}").read().splitlines() if l.startswith("+") and not l.startswith("+++") for m in FORBID.finditer(l)]
ok = gate("X", "lexgate", not hits, hits or "clean") and ok
gate("L", "reset", not reset(), "clean"); R["overall"] = "READY" if ok else "FAIL"; R["signature"] = sigs[0][1]; R["hashes"] = {f: hashlib.sha256(open(f"{pkg}/{f}", "rb").read()).hexdigest() for f in ("variant.patch", "test.patch")}
json.dump(R, open(f"{pkg}/validation.json", "w"), indent=1); print(cf["variant_id"], R["overall"])
