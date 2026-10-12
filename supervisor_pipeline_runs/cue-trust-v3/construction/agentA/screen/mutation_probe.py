#!/opt/miniconda3/bin/python
"""Empirical untested-regime probe (no LLM): applies candidate single-line mutations one at a time to a checkout, compiles, runs either the full
Defects4J suite (mode=full) or selected JUnit classes via JUnitCore (mode=classes), records failures, reverts. A mutation that SURVIVES the
existing suite marks a regime the tests do not exercise. Usage: mutation_probe.py <checkout> <mutations.json> <out.json> [--mode full|classes]"""
import json, os, re, subprocess, sys, time, argparse
ap = argparse.ArgumentParser(); ap.add_argument("checkout"); ap.add_argument("muts"); ap.add_argument("out"); ap.add_argument("--mode", default="full"); a = ap.parse_args()
env = dict(os.environ, PERL5LIB=os.path.expanduser("~/perl5/lib/perl5")); co = a.checkout
def sh(cmd, timeout=3000):
    p = subprocess.run(cmd, cwd=co, capture_output=True, text=True, env=env, timeout=timeout); return p.returncode, p.stdout + p.stderr
def raw(path): return open(os.path.join(co, path), "rb").read().decode("utf-8")
def put(path, t):
    r = raw(path); eol = "\r\n" if "\r\n" in r else "\n"; open(os.path.join(co, path), "wb").write(t.replace("\r\n", "\n").replace("\n", eol).encode("utf-8"))
def drop_classes(path):
    """Delete the compiled classes of a source file so an incremental build cannot skip it (same-second mtime granularity)."""
    name = os.path.basename(path)[:-5]; rel = os.path.dirname(path)
    for root in ("target/classes", "build", "target/test-classes", "build-tests"):
        for src_root in ("src/main/java/", "source/", "src/java/", "src/test/java/", "tests/"):
            if rel.startswith(src_root):
                d = os.path.join(co, root, rel[len(src_root):])
                if os.path.isdir(d):
                    for f in os.listdir(d):
                        if f == name + ".class" or f.startswith(name + "$"): os.remove(os.path.join(d, f))
muts = json.load(open(a.muts)); results = []
cp = None
if a.mode == "classes":
    pp = subprocess.run(["defects4j", "export", "-p", "cp.test"], cwd=co, capture_output=True, text=True, env=env); cp = pp.stdout.strip().splitlines()[-1]
    baseline = {}
def run_class(cls):
    try: rc, o = sh(["java", "-cp", cp, "org.junit.runner.JUnitCore", cls], timeout=180)
    except subprocess.TimeoutExpired: return None, [], "TIMEOUT (180 s): the mutated code probably loops"
    mm = re.search(r"Tests run: (\d+),\s+Failures: (\d+)", o); okm = re.search(r"OK \((\d+) tests?\)", o)
    nf = int(mm.group(2)) if mm else (0 if okm else None); names = sorted(set(re.findall(r"^\d+\) (\S+)", o, re.M))); return nf, names, o[-300:]
for m in muts:
    t0 = time.time(); path = m["file"]; text = raw(path).replace("\r\n", "\n"); n = text.count(m["old"])
    rec = {"id": m["id"], "file": path, "old": m["old"], "new": m["new"], "occurrences": n}
    if n != 1: rec["status"] = "SKIP (anchor not unique)"; results.append(rec); print(rec["id"], rec["status"]); continue
    put(path, text.replace(m["old"], m["new"], 1)); drop_classes(path)
    rc, o = sh(["defects4j", "compile"], timeout=1200)
    if rc != 0 or "BUILD FAILED" in o: rec["status"] = "COMPILE_FAIL"; rec["detail"] = o[-600:]
    else:
        if a.mode == "full":
            try: rc, o = sh(["defects4j", "test"], timeout=int(os.environ.get("PROBE_SUITE_TIMEOUT", "300")))
            except subprocess.TimeoutExpired: subprocess.run(["pkill", "-f", co.rstrip("/") + "/"], capture_output=True); rc, o = 124, "TIMEOUT: the mutated code probably loops"
            mm = re.search(r"Failing tests:\s*(\d+)", o); nf = int(mm.group(1)) if mm else None
            fails = sorted(set(re.findall(r"^\s*-\s+(\S+::\S+)", o, re.M))); rec["failing"] = nf; rec["failing_tests"] = fails[:40]
            rec["status"] = "SURVIVED (no test fails)" if nf == 0 else ("TIMEOUT (loop)" if rc == 124 else f"KILLED by {nf} test(s)")
        else:
            fails = {}; new_total = 0; unknown = False
            for cls in m["tests"]:
                if cls not in baseline:
                    sh(["git", "checkout", "--", path]); drop_classes(path); sh(["defects4j", "compile"], timeout=1200); baseline[cls] = run_class(cls); put(path, text.replace(m["old"], m["new"], 1)); drop_classes(path); sh(["defects4j", "compile"], timeout=1200)
                nf, names, tail = run_class(cls); bnf, bnames, _ = baseline[cls]
                if nf is None: unknown = True
                new = [x for x in names if x not in bnames]; new_total += len(new); fails[cls] = {"failures": nf, "baseline_failures": bnf, "new_failures": new[:20], "tail": tail if nf is None else ""}
            rec["per_class"] = fails; rec["status"] = ("TIMEOUT/UNKNOWN (loop or unparsed junit output)" if unknown else ("SURVIVED (no new test fails)" if new_total == 0 else f"KILLED by {new_total} new failure(s)"))
    sh(["git", "checkout", "--", path]); drop_classes(path); rec["secs"] = round(time.time() - t0); results.append(rec); print(rec["id"], rec["status"], f"{rec['secs']}s", flush=True)
    json.dump(results, open(a.out, "w"), indent=1)
json.dump(results, open(a.out, "w"), indent=1)
