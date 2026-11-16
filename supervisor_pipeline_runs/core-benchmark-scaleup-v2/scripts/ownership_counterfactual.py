"""Counterfactual repair analysis across H1-H5 (Phase 13, mandatory for v2). For each candidate alternate repair declared in pair_config.json
("ownership_candidates": [{"hop","file","old","new","rationale"}]), copies the TREATMENT reproduction checkout, applies that ONE alternate repair while
leaving the real H5 bug in place, recompiles and (a) runs the trigger, (b) runs the equivalence probe class and compares its output to the ORIGINAL
(correct) output recorded by equivalence_probe.sh. Verdicts per candidate:
  equivalent_repair  - trigger passes AND probe output identical to the original build  -> this hop is an equally valid fault owner
  compensating       - trigger passes but probe output differs from the original        -> fixes the test, changes semantics elsewhere
  not_a_repair       - trigger still fails
Classification: AMBIGUOUS if any equivalent_repair; MOSTLY_UNIQUE if only compensating repairs exist; UNIQUE if every candidate is not_a_repair.
Usage: ownership_counterfactual.py <proj> <bug> <D4J project>.  NON-CANONICAL / CORE BENCHMARK SCALE-UP V2."""
import json, os, shutil, subprocess, sys
S = "/Users/shawnli/Desktop/Honours/defects4j/supervisor_pipeline_runs/core-benchmark-scaleup-v2"
P, B, D4J = sys.argv[1], sys.argv[2], sys.argv[3]
root = f"{S}/{P}/{B}"; cfg = json.load(open(f"{root}/pair_config.json")); E = f"{root}/analysis/equivalence"
cands = cfg.get("ownership_candidates") or []
env = dict(os.environ, PERL5LIB=os.path.expanduser("~/perl5/lib/perl5"))
def sh(cmd, cwd, timeout=3000):
    r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, env=env, timeout=timeout); return r.returncode, r.stdout + r.stderr
def drop_classes(co, rel):
    name = os.path.basename(rel)[:-5]; d = os.path.dirname(rel).replace("source/", "").replace("src/main/java/", "").replace("src/java/", "")
    for bd in ("build", "target/classes", "build/classes"):
        p = os.path.join(co, bd, d)
        if os.path.isdir(p):
            for f in os.listdir(p):
                if f == name + ".class" or f.startswith(name + "$"): os.remove(os.path.join(p, f))
probe_cls = cfg.get("probe_class"); orig_out = f"{E}/out_original.txt"
results = []
for c in cands:
    co = f"{root}/repro/cf-{c['hop']}-checkout"; shutil.rmtree(co, ignore_errors=True); shutil.copytree(f"{root}/repro/treatment-checkout", co, symlinks=True)
    p = os.path.join(co, c["file"]); raw = open(p, "rb").read().decode(); eol = "\r\n" if "\r\n" in raw else "\n"; t = raw.replace("\r\n", "\n")
    rec = {"hop": c["hop"], "file": c["file"], "repair": c["new"].strip()[:120], "rationale": c.get("rationale", "")}
    if t.count(c["old"]) != 1: rec.update({"verdict": "anchor_error", "detail": f"old string occurs {t.count(c['old'])} times"}); results.append(rec); continue
    open(p, "wb").write(t.replace(c["old"], c["new"], 1).replace("\n", eol).encode()); drop_classes(co, c["file"])
    rc, out = sh(["defects4j", "compile"], co)
    if rc != 0: rec.update({"verdict": "compile_error", "detail": out[-300:]}); results.append(rec); continue
    rc, out = sh(["defects4j", "test", "-t", cfg["trigger"]], co, 900)
    import re as _re
    m = _re.search(r"Failing tests:\s*(\d+)", out); nfail = int(m.group(1)) if m else None
    rec["trigger_fails"] = (nfail or 0) > 0
    if rec["trigger_fails"]: rec["verdict"] = "not_a_repair"
    elif probe_cls and os.path.exists(orig_out):
        cp = sh(["defects4j", "export", "-p", "cp.test"], co)[1].strip().splitlines()[-1]
        bd = f"{E}/build_cf_{c['hop']}"; os.makedirs(bd, exist_ok=True)
        rc1, o1 = sh(["javac", "-cp", cp, "-d", bd, f"{E}/{probe_cls}.java"], co)
        rc2, o2 = sh(["java", "-cp", cp + ":" + bd, probe_cls], co)
        if rc1 or rc2: rec.update({"verdict": "probe_error", "detail": (o1 + o2)[-200:]})
        else:
            open(f"{E}/out_cf_{c['hop']}.txt", "w").write(o2)
            a = open(orig_out).read().splitlines(); b = o2.splitlines(); same = sum(1 for x, y in zip(a, b) if x == y)
            rec.update({"probe_cases": len(a), "probe_matches_original": same, "verdict": "equivalent_repair" if (same == len(a) and len(a) == len(b)) else "compensating"})
    else: rec["verdict"] = "trigger_repair_probe_unavailable"
    results.append(rec)
eq = [r for r in results if r["verdict"] == "equivalent_repair"]; comp = [r for r in results if r["verdict"] == "compensating"]
cls = "AMBIGUOUS" if eq else ("MOSTLY_UNIQUE" if comp else "UNIQUE")
out = {"schema_version": "core-benchmark-scaleup-v2/ownership/v1", "bug": f"{P}/{B}", "pair_id": cfg["pair_id"], "gold": cfg["treatment"]["gold_class"] + "#" + cfg["treatment"]["gold_method"],
       "candidates_tested": len(results), "equivalent_repair_sites": [r["hop"] for r in eq], "compensating_repair_sites": [r["hop"] for r in comp],
       "classification": cls, "results": results}
json.dump(out, open(f"{root}/analysis/ownership_counterfactual.json", "w"), indent=1)
for r in results: print(f"  {r['hop']}: {r['verdict']}" + (f" ({r.get('probe_matches_original')}/{r.get('probe_cases')} probe cases match the original)" if r.get("probe_cases") else ""))
print(f"ownership: {cls} (equivalent repair sites: {out['equivalent_repair_sites'] or 'none'}; compensating: {out['compensating_repair_sites'] or 'none'})")
