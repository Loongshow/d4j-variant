#!/usr/bin/env python
"""Behavioural ownership counterfactual for one camouflage arm.

For each pre-registered alternate one-line repair at another chain stage, copy that arm's
reproduction checkout, apply the single edit while LEAVING the real gold bug in place, recompile,
run the trigger, and (if the trigger now passes) run the pair's equivalence probe and compare its
output with the ORIGINAL (unpatched) output recorded by equivalence_probe_camo.sh.

  equivalent_repair - trigger passes AND probe output identical to the original build
  compensating      - trigger passes but probe output differs somewhere else
  not_a_repair      - trigger still fails
Classification: AMBIGUOUS if any equivalent_repair, MOSTLY_UNIQUE if only compensating, else UNIQUE.
Usage: ownership_counterfactual_camo.py <spec.json> <low|high>
"""
import json, os, re, shutil, subprocess, sys

spec = json.load(open(sys.argv[1])); arm = sys.argv[2]
R = "/Users/shawnli/Desktop/Honours/defects4j/supervisor_pipeline_runs/camouflage-model-comparison-v1"
A = f"{R}/experiment-a-camouflage"; sname = os.path.basename(sys.argv[1])[:-5]
cfg = json.load(open(f"{A}/construction/configs/{sname}/pair_config_{arm}.json"))
VID = cfg["treatment_id"]; E = f"{A}/equivalence/{sname}"
host = spec["arms"][arm]["gold_host_class"].split(".")[-1]
cands = [{k: (v.replace("{HOST}", host) if isinstance(v, str) else v) for k, v in c.items()}
         for c in spec["ownership_candidates"]]
env = dict(os.environ, PERL5LIB=os.path.expanduser("~/perl5/lib/perl5"))
probe = spec["probe_class"]; orig = f"{E}/out_original.txt"


def sh(cmd, cwd, timeout=3000):
    p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, env=env, timeout=timeout)
    return p.returncode, p.stdout + p.stderr


def drop_classes(co, rel):
    name = os.path.basename(rel)[:-5]; d = os.path.dirname(rel).replace("src/main/java/", "")
    for bd in ("build", "target/classes", "build/classes"):
        p = os.path.join(co, bd, d)
        if os.path.isdir(p):
            for f in os.listdir(p):
                if f == name + ".class" or f.startswith(name + "$"):
                    os.remove(os.path.join(p, f))


results = []
for c in cands:
    co = f"{A}/repro/cf-{VID}-{c['hop']}"; shutil.rmtree(co, ignore_errors=True)
    shutil.copytree(f"{A}/repro/{VID}-checkout", co, symlinks=True)
    p = os.path.join(co, c["file"]); raw = open(p, "rb").read().decode()
    eol = "\r\n" if "\r\n" in raw else "\n"; t = raw.replace("\r\n", "\n")
    rec = {"hop": c["hop"], "file": c["file"], "from": c["old"].strip(), "to": c["new"].strip(),
           "rationale": c.get("rationale", "")}
    if t.count(c["old"]) != 1:
        rec.update({"verdict": "anchor_error", "detail": f"old string occurs {t.count(c['old'])} times"})
        results.append(rec); print(rec["hop"], rec["verdict"], flush=True); continue
    open(p, "wb").write(t.replace(c["old"], c["new"], 1).replace("\n", eol).encode())
    drop_classes(co, c["file"])
    rc, out = sh(["defects4j", "compile"], co)
    if rc != 0 or "BUILD FAILED" in out:
        rec.update({"verdict": "compile_error", "detail": out[-300:]})
        results.append(rec); print(rec["hop"], rec["verdict"], flush=True); continue
    rc, out = sh(["defects4j", "test", "-t", cfg["trigger"]], co, 900)
    m = re.search(r"Failing tests:\s*(\d+)", out); nfail = int(m.group(1)) if m else None
    rec["trigger_fails"] = (nfail or 0) > 0
    if rec["trigger_fails"]:
        rec["verdict"] = "not_a_repair"
    elif os.path.exists(orig):
        cp = sh(["defects4j", "export", "-p", "cp.test"], co)[1].strip().splitlines()[-1]
        bd = f"{E}/build_cf_{VID}_{c['hop']}"; os.makedirs(bd, exist_ok=True)
        rc1, o1 = sh(["javac", "-cp", cp, "-d", bd, f"{A}/equivalence/{probe}.java"], co)
        rc2, o2 = sh(["java", "-cp", cp + ":" + bd, probe], co)
        if rc1 or rc2:
            rec.update({"verdict": "probe_error", "detail": (o1 + o2)[-200:]})
        else:
            open(f"{E}/out_cf_{VID}_{c['hop']}.txt", "w").write(o2)
            a = open(orig).read().splitlines(); b = o2.splitlines()
            same = sum(1 for x, y in zip(a, b) if x == y)
            rec.update({"probe_cases": len(a), "probe_matches_original": same,
                        "verdict": "equivalent_repair" if (same == len(a) and len(a) == len(b)) else "compensating"})
    else:
        rec["verdict"] = "probe_unavailable"
    results.append(rec); print(rec["hop"], rec["verdict"], rec.get("probe_matches_original", ""), flush=True)

eq = [r for r in results if r["verdict"] == "equivalent_repair"]
comp = [r for r in results if r["verdict"] == "compensating"]
cls = "AMBIGUOUS" if eq else ("MOSTLY_UNIQUE" if comp else "UNIQUE")
out = {"schema_version": "camouflage-v1/ownership/v1", "pair": cfg["pair_id"], "arm": arm.upper(),
       "variant_id": VID, "gold": cfg["treatment"]["gold_class"] + "#" + cfg["treatment"]["gold_method"],
       "candidates_tested": len(results), "equivalent_repair_sites": [r["hop"] for r in eq],
       "compensating_repair_sites": [r["hop"] for r in comp],
       "behavioural_classification": cls, "results": results}
os.makedirs(f"{A}/review/ownership", exist_ok=True)
json.dump(out, open(f"{A}/review/ownership/{VID}_ownership.json", "w"), indent=1)
print(f"{VID} behavioural ownership: {cls} (equivalent: {out['equivalent_repair_sites'] or 'none'}; compensating: {out['compensating_repair_sites'] or 'none'})")
