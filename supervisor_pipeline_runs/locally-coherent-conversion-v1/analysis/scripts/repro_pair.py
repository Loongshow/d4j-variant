"""Config-driven fresh-checkout reproduction from packaged patches only. Usage: repro_pair.py <config.json> <control|treatment> <fresh_checkout> <pkg> <out_json>"""
import json, os, re, subprocess, sys, time, hashlib, shutil
cfg, arm, co, pkg, out = json.load(open(sys.argv[1])), sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5]
A = cfg[arm]; TRIG = cfg["trigger"]; env = dict(os.environ, PERL5LIB=os.path.expanduser("~/perl5/lib/perl5"))
R = {"schema_version": "locally-coherent-conversion-v1/reproduction/v1", "label": "NON-CANONICAL", "arm": arm.upper() + "-01", "fresh_checkout": co, "package": pkg, "steps": [], "started_at": time.strftime("%Y-%m-%dT%H:%M:%S%z")}
def save(): json.dump(R, open(out, "w"), indent=1)
def sh(cmd, timeout=900):
    p = subprocess.run(cmd, cwd=co, capture_output=True, text=True, env=env, timeout=timeout); return p.returncode, p.stdout + p.stderr
def step(sid, name, cmds, ok, key): R["steps"].append({"step": sid, "name": name, "commands": cmds, "status": "pass" if ok else "FAIL", "key_output": key[-1000:]}); save(); return ok
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
        ft = open(os.path.join(co, "failing_tests")).read() if os.path.exists(os.path.join(co, "failing_tests")) else ""; sigs.append({"run": i + 1, "n_fail": n, "signature": "\n".join(ft.splitlines()[:2])})
    R["trigger_runs"] = sigs
    ok = step("R3", "trigger fails deterministically 3x with the expected value-mismatch signature", [f"defects4j test -t {TRIG} (x3)"], all(s["n_fail"] == 1 for s in sigs) and len({s["signature"] for s in sigs}) == 1 and cfg["expected_signature"] in sigs[0]["signature"], json.dumps(sigs, indent=1))
if ok:
    if arm == "control":
        s = span(cfg["facade_file"], A["gold_decl"]); b = where(cfg["facade_file"], A["bug_line"]); R["gold_check"] = {"gold": f"{A['gold_class']}#{A['gold_method']}", "span": s, "buggy_line_at": b}
        ok = step("R4", "gold source exists where recorded and contains the buggy line", ["static span check"], bool(s and b and all(s[0] <= x <= s[1] for x in b)), json.dumps(R["gold_check"]))
    else:
        s2 = span(cfg["hop2_file"], A["gold_decl"]); b = where(cfg["hop2_file"], A["bug_line"]); s1 = span(cfg["hop1_file"], A["hop1_decl"]); s0 = span(cfg["facade_file"], cfg["control"]["gold_decl"]); c1 = where(cfg["facade_file"], A["facade_call"]); c2 = where(cfg["hop1_file"], A["hop1_call"])
        R["gold_check"] = {"gold": f"{A['gold_class']}#{A['gold_method']}", "hop2_span": s2, "buggy_line_at": b, "hop1_span": s1, "facade_span": s0, "facade_calls_hop1_at": c1, "hop1_calls_hop2_at": c2, "buggy_line_elsewhere": {"facade": where(cfg["facade_file"], A["bug_line"]) + where(cfg["facade_file"], cfg["control"]["bug_line"]), "hop1": where(cfg["hop1_file"], A["bug_line"])}}
        ok = step("R4", "hop1 exists, hop2 exists, chain intact, bug physically in declared gold only", ["static span check"], bool(s2 and b and all(s2[0] <= x <= s2[1] for x in b) and s1 and s0 and c1 and s0[0] <= c1[0] <= s0[1] and c2 and s1[0] <= c2[0] <= s1[1] and not any(R["gold_check"]["buggy_line_elsewhere"].values())), json.dumps(R["gold_check"]))
R["overall"] = "pass" if ok and all(s["status"] == "pass" for s in R["steps"]) else "FAIL"; R["finished_at"] = time.strftime("%Y-%m-%dT%H:%M:%S%z"); save()
print(arm, "reproduction overall:", R["overall"], [(s["step"], s["status"]) for s in R["steps"]])
