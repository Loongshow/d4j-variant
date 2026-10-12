"""Full-suite mutation screen (agentB copy adapted from core-benchmark-scaleup-v1/scripts/mutation_probe.py, mode=full).
Usage: screen.py <checkout> <muts.json> <out.json> <k> <n>   (processes mutations with index % n == k)"""
import json, os, re, subprocess, sys, time
co, mf, outf, k, n = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4]), int(sys.argv[5])
env = dict(os.environ, PERL5LIB=os.path.expanduser("~/perl5/lib/perl5"))
def sh(cmd, timeout=600):
    p = subprocess.run(cmd, cwd=co, capture_output=True, text=True, env=env, timeout=timeout); return p.returncode, p.stdout + p.stderr
def raw(p): return open(os.path.join(co, p), "rb").read().decode("utf-8")
def put(p, t, eol="\n"): open(os.path.join(co, p), "wb").write(t.replace("\n", eol).encode("utf-8"))
def drop(p):
    name = os.path.basename(p)[:-5]; rel = os.path.dirname(p)
    d = os.path.join(co, "build", rel[len("source/"):])
    if os.path.isdir(d):
        for f in os.listdir(d):
            if f == name + ".class" or f.startswith(name + "$"): os.remove(os.path.join(d, f))
muts = json.load(open(mf)); res = []
for i, m in enumerate(muts):
    if i % n != k: continue
    t0 = time.time(); r0 = raw(m["file"]); eol = "\r\n" if "\r\n" in r0 else "\n"; text = r0.replace("\r\n", "\n"); rec = {"id": m["id"], "bug_line": m["bug_line"]}
    if text.count(m["old"]) != 1: rec["status"] = "SKIP"; res.append(rec); continue
    put(m["file"], text.replace(m["old"], m["new"], 1), eol); drop(m["file"])
    rc, o = sh(["defects4j", "compile"])
    if rc != 0 or "BUILD FAILED" in o: rec["status"] = "COMPILE_FAIL"
    else:
        try:
            rc, o = sh(["defects4j", "test"], 300)
            mm = re.search(r"Failing tests:\s*(\d+)", o); nf = int(mm.group(1)) if mm else None
            rec["failing"] = nf; rec["failing_tests"] = sorted(set(re.findall(r"^\s*-\s+(\S+::\S+)", o, re.M)))[:30]
            rec["status"] = "SURVIVED" if nf == 0 else f"KILLED({nf})"
        except subprocess.TimeoutExpired: rec["status"] = "TIMEOUT"
    open(os.path.join(co, m["file"]), "wb").write(r0.encode("utf-8")); drop(m["file"]); rec["secs"] = round(time.time() - t0); res.append(rec)
    print(rec["id"], rec["status"], rec["secs"], flush=True); json.dump(res, open(outf, "w"), indent=1)
sh(["git", "checkout", "--", "."]); json.dump(res, open(outf, "w"), indent=1)
